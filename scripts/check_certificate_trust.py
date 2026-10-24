"""Reject the compromised emSign CA in both trust stores used by CI tools."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
from importlib.metadata import distribution

# Standalone certifi upgrades do not replace pip's vendored trust store.
# https://discuss.python.org/t/109576
_COMPROMISED_ROOT_SHA256 = "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"
_BEGIN = "-----BEGIN CERTIFICATE-----"
_END = "-----END CERTIFICATE-----"


def check_bundle(bundle: str) -> int:
    """Require complete, parseable CA certificates and exclude the removed root."""
    certificates = re.findall(f"{_BEGIN}.*?{_END}", bundle, re.DOTALL)
    if not certificates or not (bundle.count(_BEGIN) == bundle.count(_END) == len(certificates)):
        raise ValueError("CA bundle is empty or has incomplete certificate blocks")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata=bundle)
    parsed = context.get_ca_certs(binary_form=True)
    if len(parsed) != len(certificates):
        raise ValueError("CA bundle contains duplicate or non-CA certificates")
    if any(
        hashlib.sha256(certificate).hexdigest() == _COMPROMISED_ROOT_SHA256
        for certificate in parsed
    ):
        raise ValueError("CA bundle still trusts the compromised emSign ECC Root CA - G3")
    return len(parsed)


def check_installed() -> list[dict[str, str | int]]:
    """Missing either required CI package or bundle is an error, never a skip."""
    result: list[dict[str, str | int]] = []
    for package, relative in (
        ("certifi", "certifi/cacert.pem"),
        ("pip", "pip/_vendor/certifi/cacert.pem"),
    ):
        installed = distribution(package)
        path = installed.locate_file(relative)
        raw = path.read_bytes()
        count = check_bundle(raw.decode("ascii"))
        result.append(
            {
                "package": package,
                "version": installed.version,
                "bundle": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "certificates": count,
            }
        )
    return result


if __name__ == "__main__":
    print(json.dumps(check_installed(), sort_keys=True))
