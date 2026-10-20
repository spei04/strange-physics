# Execution assignment log

## Approval and execution capacity

2026-10-19 — Product owner approved execution baseline `2d78e3598252e211110883b164854b64c356eeda` and requested independent engineer subagents, reassignment on completion and this short log.

SP-00.a is complete for the amended execution mode: one project lead plus at most three concurrent engineers. Lead owns TL and unassigned BE/FE lanes; Platform covers PL1/PL2 sequentially; Research covers RS1/RS2 sequentially; Quality covers QE. Lead obtains peer review before integration. The nine-human-team schedule remains a reference and will be reforecast; these assignments do not establish human operations, external assessor availability or partner commitments. D01–D05 recommendations accepted as scope/provisional targets; D06 retains concrete paid and release approvals.

## Current assignment board

| Engineer | Current / next work | Review and gate |
| --- | --- | --- |
| Quality | CI-01 complete; next independent ID-A security review | Authoring released; review Research source before integration |
| Research | ID-A/#57 browser-session contracts; next exclusive writer | Quality/Platform review; full SP-01.b remains open |
| Platform | CI-01 review complete; ID-B threat analysis prepared; next ID-A policy review | Journey acceptance, full identity freeze and concrete provisioning approval remain pending |
| Project lead | Integrate reviewed PRs, update evidence and manage exclusive writer handoffs | No repo-settings races or paid-resource approval inferred |

## Assignments

| UTC start | Engineer | Task / scope | State / next handoff |
| --- | --- | --- | --- |
| 2026-10-19 23:22 | Quality | SP-00.b — journal, session, SDK recovery review and existing checks at 2d78e35 | Review passed: 55 tests, Ruff and strict mypy; matching CI includes Python 3.12/3.14 build and CLI smoke |
| 2026-10-19 23:22 | Platform | SP-02.a — cloud preflight; read-only disk inventory to prepare SP-02.b | Audit complete with deployment NO-GO; credit/target-project gaps retained |
| 2026-10-19 23:24 | Research | SP-00.b — independent physics, observations and scientific-boundary review at 2d78e35 | Review passed: 26 physics/contract tests and small analytic checks; not SP-03 domain ratification |
| 2026-10-19 23:25 | Project lead | SP-00.a — approval/roster; integration and dependency coordination | Completed; actual assignment log maintained here |
| 2026-10-19 23:23 | Research | SP-00.b — repair factual law/change-timing documentation | Committed 9833e6f; Quality peer review passed; writer ownership relinquished |
| 2026-10-19 23:24 | Quality | SP-00.a/b — review approval/roster and documentation repair | Peer review passed; 168 Markdown/JSON task states and prerequisites agree |
| 2026-10-19 23:24 | Research | SP-01.a — read-only SCI preparation | Queued while engineer idle; actual design start recorded below |
| 2026-10-19 23:24 | Quality | SP-01.b — read-only HTTP/identity/SQL preparation | Six concrete gaps identified; implementation/freeze not started |
| 2026-10-19 23:25 | Platform | SP-02.b — concrete capacity remediation proposal | Ready: 200→300 GiB boot disk plus regional recovery snapshot; explicit approval pending |
| 2026-10-19 23:29 | Research | SP-01.a — SCI contract design | Design accepted; implementation awaits exclusive writer handoff; Quality/lead review required; [#47](https://github.com/spei04/strange-physics/issues/47) |
| 2026-10-19 23:28 | Project lead | SP-00.b — integrate reviewed baseline | Completed: PR #1 merge 7117060, tree-equivalent to reviewed 5cb1895; four CI checks pass |
| 2026-10-19 23:30 | Platform | SP-01.c preparation — audit ART/EXEC boundary and repair DB freeze dependency | Added SP-01.b prerequisite; 369 edges and both reference forecasts regenerated; Quality review queued |
| 2026-10-19 23:33 | Research | SP-01.a — implement local SCI subset | b4f8505; Quality review found grid aliasing and two schema/runtime gaps |
| 2026-10-19 23:38 | Research | SP-01.a — repair three review findings | 8c86e76; 147 tests, Ruff and strict mypy pass; Quality independently accepted; writer released |
| 2026-10-19 23:41 | Project lead | SP-01.a — accept repair and prepare integration | Accepted source 8c86e76; PR and matching CI next |
| 2026-10-19 23:34 | Platform | SP-02.c — prepare priced staging configuration | Proposal ready; configuration/credit evidence and approval pending; [#49](https://github.com/spei04/strange-physics/issues/49) |
| 2026-10-19 23:37 | Platform | SP-22.a — specify workspace journeys | Seven journeys prepared; bounded documentation writer slot pending; [#50](https://github.com/spei04/strange-physics/issues/50) |
| 2026-10-19 23:42 | Research | SP-22.a — independent truth-boundary review | Active, read-only; author preview, held-out access and prediction/failure semantics |
| 2026-10-19 23:44 | Quality | SP-01.b part 1 — control-contract authoring | a9fa8cb accepted by Research/Platform/lead after four repairs; 252 tests pass; full identity freeze remains open; [#52](https://github.com/spei04/strange-physics/issues/52) |
| 2026-10-19 23:44 | Project lead | SP-01.a — integrate reviewed subset | PR #51 merged cc24aef; tree equals 6e72415; four head checks and merge-main CI passed |
| 2026-10-19 23:45 | Platform | SP-02.a — private evidence index | Owner-readable index/hash/permissions verified; review 2026-11-18; no off-device backup claim |
| 2026-10-19 23:52 | Research + Platform | SP-01.b part 1 — independent review | Repaired action/request binding, HTTP key drift, cancellation fencing and completion-prefix gap; accepted a9fa8cb |
| 2026-10-19 23:55 | Research | SP-01.b remaining identity subset — PR decomposition | Read-only preparation; session, membership/invitation/linking and credential lifecycle; no consumer starts before full freeze |
| Next | Platform | SP-22.a journeys; SP-02.c cost proposal | Separate documentation commits after root handoff; Quality reviews; no UI or provisioning |
| 2026-10-20 00:04 | Project lead | SP-01.b part 1 — integrate reviewed subset | PR #53 merged d6204aa; reviewed tree equals f6cead9; four head checks and merge-main CI passed; parent remains incomplete |
| 2026-10-20 00:04 | Platform | SP-22.a / SP-02.c — save reviewable documents | 90c010c journeys and 0eba987 staging proposal; three consistency tests/static checks pass; no UI/provisioning approval |
| 2026-10-20 00:04 | Research | SP-01.b ID-A/B/C — remaining freeze preparation | Three units, estimated 6–8 engineer-days remaining; ID-A ready to author after CI priority; consumers remain blocked |
| 2026-10-20 00:04 | Quality | CI-01 — scoped CI/CD preparation | [#54](https://github.com/spei04/strange-physics/issues/54); writer next; pinned checks, exact CI gate, protected-main candidate artifact; Research/Platform review |
| 2026-10-20 00:07 | Quality | CI-01/#54 — workflow, security and candidate delivery | 55137eb accepted by Research/Platform; hosted build/metadata repairs preserved strict policy; 292 tests and final PR CI pass |
| 2026-10-20 00:09 | Platform | ID-B — independent membership/linking challenge | Last-owner serialization, recipient verification, fresh linking proof and broker/app recovery identified; no handlers |
| 2026-10-20 00:20 | Project lead | CI-01 — integrate reviewed source and verify delivery | PR #56 merged 256b409, matching reviewed tree; strict protection read-back; main run 39347053265 delivered artifact 12231636153 |
| 2026-10-20 00:23 | Project lead | Record delivery evidence; reassign engineer | DELIVERY_RECORD.md plus owner-readable copy/index outside checkout; Research assigned ID-A/#57, Quality/Platform reviewers |

## Review evidence and management checkpoint

- Outcome: an enterprise research product that measures discovery and adaptation. Next evidence-producing milestone is the approved noiseless spring path: purchased observations → fit → unseen-condition predictions → independently scored report.
- Baseline delta: research and recovery reviews at 2d78e35; 55 tests, lint/format and strict mypy pass; same-head CI covers Python 3.12/3.14, packaging and eight-particle CLI smoke. Two factual documentation corrections committed as 9833e6f and peer reviewed. PR #1 merged as 7117060d03d4e0f843d7dddc53c3e5b580b8ef3f; git diff verified its tree matches reviewed head 5cb1895c280af1ac0ad16bdc954d596089e91b70. All four GitHub CI checks at that head passed on Python 3.12/3.14. [Merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39341809891) also passed at 7117060. SP-00.b is complete; this is not a product release.
- Forecast repair: adding the DB-to-artifact freeze edge changes R0 to W6–7 and first spring integration to W11–13; R1 reserve becomes W26. GA remains W52–67. These remain nine-human-team reference estimates; actual engineer assignments are separate.
- SCI delta: SP-01.a complete via [PR #51](https://github.com/spei04/strange-physics/pull/51), merge cc24aef tree equals reviewed 6e72415; all four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39343441273) pass. 147 tests and independent schema checks passed after three repairs. No fitter, hosted service or benchmark result is claimed.
- Control delta: part 1 integrated via [PR #53](https://github.com/spei04/strange-physics/pull/53), merge d6204aa matching reviewed f6cead9. Four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39344813113) passed after four review fixes at a9fa8cb. 252 total tests, Ruff, strict mypy, 67 external schema/header cases and 47 reference resolutions pass. Full SP-01.b remains incomplete: public session, membership/invitation/linking and credential lifecycle contracts still need reviewed PRs. Their consumers remain blocked; four-day reference effort needs re-estimation.
- Cloud audit: current shared project/billing accessible; target projects/IAM/quota and credit eligibility/expiry unknown. Deployment NO-GO, Platform owns remediation; product/billing owner supplies private credit evidence. Private raw records remain outside the checkout; no account IDs published.
- Shared storage: free space fell to 57.7 MiB and was about 143 MiB at this checkpoint. Only ~18 MB is project-owned disposable cache. Other projects, active consumers and migration archives are excluded from cleanup; the >=20 GiB capacity gate remains closed.
- Exact pending action: existing balanced boot disk 200→300 GiB (~+$10/month) with a regional recovery snapshot (up to roughly +$10/month while retained), before credits/tax. No reboot, detach or formatting; verify snapshot READY, exact disk/partition layout, running consumers and >=20 GiB free. Snapshot retention review after seven days; effective recycle retention remains to be verified. Official [pricing](https://cloud.google.com/compute/disks-image-pricing) and [resize procedure](https://docs.cloud.google.com/compute/docs/disks/resize-persistent-disk).
- CI/CD complete for this package: PR #56 merged 256b409 with a matching reviewed tree. Main run 39347053265 passed all checks and delivered artifact 12231636153; independent in-memory bundle/checksum/source review passed, and the PR produced zero artifacts. DELIVERY_RECORD.md preserves exact hashes and policy read-back. This is unpublished candidate delivery, not deployment or production readiness. One-account GitHub approval limitation remains explicit.
- Budget: no new cloud/provider spend incurred or reserved. Disk/snapshot proposal remains unapproved. Existing VM billing is outside this new-work spend record.
- Tracking: SP-00.a [#44](https://github.com/spei04/strange-physics/issues/44), SP-00.b [#45](https://github.com/spei04/strange-physics/issues/45), SP-02.a [#46](https://github.com/spei04/strange-physics/issues/46).

## Current blockers and rules

- Cloud filesystem had 215 MiB free at execution start. SP-02.b gates installs/builds; preserve migration archives and other active projects.
- Baseline integration passed both review scopes and required checks at 7117060. Specific contract freezes remain prerequisites; SP-01.c additionally waits for SP-01.b DB acceptance.
- Root coordinates every checkout write; independent writers get separate cloud checkouts. No local project copies.
- Partner/assessor/human operations availability is unconfirmed. No outreach or contractual commitment is implied.
- No priced staging, provider trial, official sweep or production release is approved yet.
- A completed assignment includes source identity, tests, reviewer outcome and limitations. Review findings become bounded repair assignments before acceptance.
