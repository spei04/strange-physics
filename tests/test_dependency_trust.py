"""Portable fixtures for the CI guard; no installed CI extras are required."""

from __future__ import annotations

import ssl
from importlib.metadata import Distribution, PackageNotFoundError, PathDistribution
from pathlib import Path

import pytest

from scripts import check_certificate_trust as trust

# Public root certificates from the pinned certifi/pip bundles, not private keys.
_ALLOWED = """-----BEGIN CERTIFICATE-----
MIICiTCCAg+gAwIBAgIQH0evqmIAcFBUTAGem2OZKjAKBggqhkjOPQQDAzCBhTEL
MAkGA1UEBhMCR0IxGzAZBgNVBAgTEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UE
BxMHU2FsZm9yZDEaMBgGA1UEChMRQ09NT0RPIENBIExpbWl0ZWQxKzApBgNVBAMT
IkNPTU9ETyBFQ0MgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMDgwMzA2MDAw
MDAwWhcNMzgwMTE4MjM1OTU5WjCBhTELMAkGA1UEBhMCR0IxGzAZBgNVBAgTEkdy
ZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UEBxMHU2FsZm9yZDEaMBgGA1UEChMRQ09N
T0RPIENBIExpbWl0ZWQxKzApBgNVBAMTIkNPTU9ETyBFQ0MgQ2VydGlmaWNhdGlv
biBBdXRob3JpdHkwdjAQBgcqhkjOPQIBBgUrgQQAIgNiAAQDR3svdcmCFYX7deSR
FtSrYpn1PlILBs5BAH+X4QokPB0BBO490o0JlwzgdeT6+3eKKvUDYEs2ixYjFq0J
cfRK9ChQtP6IHG4/bC8vCVlbpVsLM5niwz2J+Wos77LTBumjQjBAMB0GA1UdDgQW
BBR1cacZSBm8nZ3qQUfflMRId5nTeTAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/
BAUwAwEB/zAKBggqhkjOPQQDAwNoADBlAjEA7wNbeqy3eApyt4jf/7VGFAkK+qDm
fQjGGoe9GKhzvSbKYAydzpmfz1wPMOG+FDHqAjAU9JM8SaczepBGR7NjfRObTrdv
GDeAU/7dIOA1mjbRxwG55tzd8/8dLDoWV9mSOdY=
-----END CERTIFICATE-----"""
_COMPROMISED = """-----BEGIN CERTIFICATE-----
MIICTjCCAdOgAwIBAgIKPPYHqWhwDtqLhDAKBggqhkjOPQQDAzBrMQswCQYDVQQG
EwJJTjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhyYSBUZWNo
bm9sb2dpZXMgTGltaXRlZDEgMB4GA1UEAxMXZW1TaWduIEVDQyBSb290IENBIC0g
RzMwHhcNMTgwMjE4MTgzMDAwWhcNNDMwMjE4MTgzMDAwWjBrMQswCQYDVQQGEwJJ
TjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhyYSBUZWNobm9s
b2dpZXMgTGltaXRlZDEgMB4GA1UEAxMXZW1TaWduIEVDQyBSb290IENBIC0gRzMw
djAQBgcqhkjOPQIBBgUrgQQAIgNiAAQjpQy4LRL1KPOxst3iAhKAnjlfSU2fySU0
WXTsuwYc58Byr+iuL+FBVIcUqEqy6HyC5ltqtdyzdc6LBtCGI79G1Y4PPwT01xyS
fvalY8L1X44uT6EYGQIrMgqCZH0Wk9GjQjBAMB0GA1UdDgQWBBR8XQKEE9TMipuB
zhccLikenEhjQjAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAKBggq
hkjOPQQDAwNpADBmAjEAvvNhzwIQHWSVB7gYboiFBS+DCBeQyh+KTOgNG3qxrdWB
CUfvO6wIBHxcmbHtRwfSAjEAnbpV/KlK6O3t5nYBQnvI+GDZjVGLVTv7jHvrZQnD
+JbNR6iC8hZVdyR+EhCVBCyj
-----END CERTIFICATE-----"""


def test_parseable_unaffected_root_is_allowed() -> None:
    assert trust.check_bundle(_ALLOWED) == 1


@pytest.mark.parametrize("prefix", ["", "# Harmless label does not change DER identity\n"])
def test_compromised_root_rejected_even_with_different_label(prefix: str) -> None:
    with pytest.raises(ValueError, match="compromised emSign"):
        trust.check_bundle(prefix + _COMPROMISED)


@pytest.mark.parametrize(
    "bundle",
    [
        "",
        "# Only comments",
        _ALLOWED + "\n-----BEGIN CERTIFICATE-----",
        _ALLOWED + "\n-----END CERTIFICATE-----",
        "-----BEGIN CERTIFICATE-----\nnot-a-certificate\n-----END CERTIFICATE-----",
        _ALLOWED + "\n" + _ALLOWED,
    ],
)
def test_empty_incomplete_malformed_or_duplicate_bundle_rejected(bundle: str) -> None:
    with pytest.raises((ValueError, ssl.SSLError)):
        trust.check_bundle(bundle)


@pytest.mark.parametrize("missing", ["certifi", "pip"])
def test_missing_ci_distribution_is_not_skipped(
    missing: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def installed(name: str) -> Distribution:
        if name == missing:
            raise PackageNotFoundError(name)
        return make_distribution(tmp_path, name, _ALLOWED)

    monkeypatch.setattr(trust, "distribution", installed)
    with pytest.raises(PackageNotFoundError):
        trust.check_installed()


def make_distribution(root: Path, name: str, bundle: str) -> Distribution:
    info = root / f"{name}-1.dist-info"
    info.mkdir(exist_ok=True)
    (info / "METADATA").write_text(f"Name: {name}\nVersion: 1\n")
    relative = "certifi/cacert.pem" if name == "certifi" else "pip/_vendor/certifi/cacert.pem"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bundle)
    return PathDistribution(info)


def test_standalone_update_does_not_hide_vendored_compromise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    distributions = {
        "certifi": make_distribution(tmp_path, "certifi", _ALLOWED),
        "pip": make_distribution(tmp_path, "pip", _COMPROMISED),
    }
    monkeypatch.setattr(trust, "distribution", distributions.__getitem__)
    with pytest.raises(ValueError, match="compromised emSign"):
        trust.check_installed()
    make_distribution(tmp_path, "pip", _ALLOWED)
    checked = trust.check_installed()
    assert [item["package"] for item in checked] == ["certifi", "pip"]
    assert all(item["certificates"] == 1 for item in checked)


def test_missing_bundle_is_not_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    distributions = {
        name: make_distribution(tmp_path, name, _ALLOWED) for name in ("certifi", "pip")
    }
    (tmp_path / "pip/_vendor/certifi/cacert.pem").unlink()
    monkeypatch.setattr(trust, "distribution", distributions.__getitem__)
    with pytest.raises(FileNotFoundError):
        trust.check_installed()
