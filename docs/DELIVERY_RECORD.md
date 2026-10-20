# Verified CI delivery record

Recorded 2026-10-20 UTC. Owner: project lead. Task: CI-01 / [#54](https://github.com/spei04/strange-physics/issues/54).
Purpose: preserve acceptance evidence for an unpublished package candidate. This is not a product release, hosted deployment, signature or production-readiness claim.

## Reviewed source and executed evidence

- [PR #56](https://github.com/spei04/strange-physics/pull/56), reviewed head `55137eb82ca233816c1f7635b41c3844fbc59de7`.
- Protected-main source `256b409240a2fe50720f2181cc4f8602e15bdaf2`; its tree `8ed8ef624ce0f9e2e201dc3cdce0888f01a37906` equals the reviewed head.
- [PR CI](https://github.com/spei04/strange-physics/actions/runs/39346906168): Python 3.12/3.14 each passed 292 tests, 152 external schema cases, Ruff, strict mypy, offline wheel/sdist inspection and scientific CLI smoke. Dependency/static security and CI gate passed. The PR produced zero artifacts.
- [Protected-main CI and delivery](https://github.com/spei04/strange-physics/actions/runs/39347053265): all required checks passed again; a fresh environment containing only locked runtime dependencies installed and exercised the wheel outside the checkout, then the candidate was delivered.
- Research and Platform independently reviewed the source; bounded build/metadata repairs received peer review. The lead integrated the exact reviewed head without an administrative bypass.
- The coordination owner independently inspected archive members and the bundle; the lead independently verified the four-file bundle, listed checksums, source commit and lock checksum in memory.

## Candidate identity

Artifact ID: `12231636153`. Name: `release-candidate-256b409240a2fe50720f2181cc4f8602e15bdaf2-1`.
GitHub-reported artifact digest: `sha256:6dcb4463303bd43af365c23db7baaf6a08b393ccd194f6280bb09737b52ad7f0`.
Temporary artifact expiry: **2026-10-27T00:21:27Z**.

| File | Bytes / purpose | SHA-256 |
| --- | --- | --- |
| strange_physics-0.1.0a1-py3-none-any.whl | 31571 | `58c991c57b8f17da89d1b1bf9e5a9869004188e73d8c85b477e7f0c0603af864` |
| strange_physics-0.1.0a1.tar.gz | 25216 | `68d383732e838e545ed3dbab755832c68b3cf83a65a551f3c1ab1f49710f6a53` |
| provenance.json | Source, lock, tools and run identity | `2620cbb54459983c557b8f59c35971d267333d38b013678c6d0e8b94ed431c4a` |
| SHA256SUMS | Verified checksums for the other three files | Included in the four-file bundle |

Lock checksum: `b83593cf033d0459848ceb699b1067706566ac09e23d864733698a5077b04b85`.
Exported runtime-requirements checksum: `3769228e5fd9efe6038aec94d335553f55ca9bd659f60d15fe0bd69a81fb25f9`.
Tools: uv 0.11.21; delivery Python 3.12.15.

The wheel and sdist have exact allowlists and byte comparisons against reviewed source. The tracked public source `.gitignore` is an explicit sdist entry with a byte check; other dotfiles, run outputs and evidence are excluded. The distribution output directory itself rejects a `.gitignore` marker.

## Repository policy read-back

Before merge, main required PR updates and an up-to-date successful **CI gate** from GitHub Actions app 15368, with admin enforcement, resolved conversations, no force pushes and no deletion. Full-SHA action policy was separately verified. No settings mutation was part of the code PR.

GitHub approval count is zero because only one collaborator is configured. Independent engineering reviews are recorded above; they are not separate-account GitHub approvals. Add an authorized independent human reviewer before claiming that control.

## Retention and limitations

This public record is retained in Git history. An owner-readable metadata copy and indexed checksum are also stored outside the working checkout; that local copy is not an off-device backup. No package bytes were copied to local project storage.

The candidate bytes expire after seven days. This metadata record does not preserve those bytes or create permanent release storage. An approved promotion must retain its required candidate bytes and records in approved durable storage before expiry. No package publication, paid resource, model call or deployment was performed. CI-01 does not complete SP-27.a or waive SP-02.b/c.

For maintenance, promotion and rollback boundaries, see [CI_CD.md](CI_CD.md).
