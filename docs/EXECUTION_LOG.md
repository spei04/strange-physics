# Execution assignment log

## Approval and execution capacity

2026-10-19 — Product owner approved execution baseline `2d78e3598252e211110883b164854b64c356eeda` and requested independent engineer subagents, reassignment on completion and this short log.

SP-00.a is complete for the amended execution mode: one project lead plus at most three concurrent engineers. Lead owns TL and unassigned BE/FE lanes; Platform covers PL1/PL2 sequentially; Research covers RS1/RS2 sequentially; Quality covers QE. Lead obtains peer review before integration. The nine-human-team schedule remains a reference and will be reforecast; these assignments do not establish human operations, external assessor availability or partner commitments. D01–D05 recommendations accepted as scope/provisional targets; D06 retains concrete paid and release approvals.

## Current assignment board

| Engineer | Current / next work | Review and gate |
| --- | --- | --- |
| Platform | SP-02.b complete; independent SP-03.a review; B3 identity linking (#63) queued | Infrastructure ownership released; Research owns the source writer slot |
| Research | SP-03.a analytic physics fixtures (#73), in progress | Exclusive writer in the existing cloud checkout; Quality/Platform independently review |
| Quality | SP-02.b independently accepted; progress and SP-03.a reviews next | ID-C/#64 remains dependent on accepted B3; independent SP-06.a scorer follows SP-04.b |
| Project lead | Capacity acceptance, checkout reconciliation and scientific integration | Existing checkout reconciled to main 89a44ed; review and exact-head CI precede integration |

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
| 2026-10-20 00:42 | Research | ID-A/#57 — browser-session contract and review repairs | PR #65 merged cc576da; 413 tests, 207 independent schema cases; writer released |
| 2026-10-20 00:42 | Quality + Platform | ID-A — independent immutable-source security/interface review | Accepted 34d26d9 after response/path schema, error mapping and cross-alias proof replay repairs |
| 2026-10-20 00:42 | Project lead | ID-A integration and assignment checkpoint | Reviewed/merge tree cd1f0ff matches; PR CI39348959056 and main CI39349126536 passed; parent #52 remains open |
| Next handoff | Platform | ID-B/B1 — workspace creation, membership, last-owner and quarantine contracts | Approved bounded plan; #63; Research/Quality review before B2 invitations and B3 linking |
| Queued after ID-B | Quality | ID-C/#64 — service/run credential lifecycle | Prepared threat model; dependencies not yet accepted |
| 2026-10-20 00:57 | Platform | ID-B/B1 — private workspace and human membership contracts | PR #67 merged 1ec45aa; 474 tests, 61 focused; writer released |
| 2026-10-20 00:57 | Research + Quality | B1 — independent source/security/HTTP review | Accepted b9c4754 after owner-status, pending security-fence and human-owner boundary repairs |
| 2026-10-20 00:57 | Project lead | B1 integration and next assignment | Merge/review tree 0e9c0a4 matches; PR CI39350544354 passed; #63 and #52 remain open |
| Next handoff | Platform | ID-B/B2 — invitations and safe redemption/recovery | Bounded plan preparation; Research/Quality review before B3 linking |
| 2026-10-20 01:02 | Quality | B3 linking threat-boundary preparation | Read-only; purpose-separated proof claims and tenant-aware identity namespace; no implementation |
| 2026-10-20 01:03 | Research + Quality | B2 independent source review | Found tenant/profile and issuing-owner revision gaps; Platform repaired both |
| 2026-10-20 01:07 | Research | Final SP-01.b integration checklist | Authority composition, global proof claims, secret retries, schemas and current stream delivery; parent remains open |
| 2026-10-20 01:09 | Platform | B2 authoring handoff and capacity stop | Clean committed c773946; 86 focused tests/static checks passed; writer released below 100 MiB floor |
| 2026-10-20 01:12 | Project lead + reviewers | B2 remote integration after capacity stop | PR #69 merged 89e6117; exact reviewed tree f51c487 matches 8267865; 560 tests and all PR/main checks passed |
| Next after capacity recovery | Platform | ID-B/B3 explicit identity linking | Assigned, blocked; Quality owns ID-C after accepted B3; no source writes or new checkout |
| 2026-10-20 01:21 | Research | Read-only I1 dependency and scientific gap review | Complete; SP-03.a queued on SP-02.b, then six existing scientific PR tasks; Quality owns SP-06.a after SP-04.b |
| 2026-10-20 01:48 | Platform | SP-02.b/#72 — approved recovery snapshot and online disk expansion | Completed 01:57; disk 200→300 GiB, partition/ext4 expanded, source and consumers preserved |
| 2026-10-20 01:58 | Quality | SP-02.b — independent control-plane, filesystem and integrity acceptance | Accepted; 104,113,758,208 bytes free; archive, uv and all 3,414 venv entries independently rehashed |
| 2026-10-20 01:59 | Project lead | Reconcile preserved checkout with reviewed main | Clean main 89a44ed; dependency manifests unchanged; no new checkout or local project copy |
| 2026-10-20 01:59 | Research | SP-03.a/#73 — independent analytic fixtures | In progress, exclusive source writer; Quality and Platform review immutable commits |

## Review evidence and management checkpoint

- Outcome: an enterprise research product that measures discovery and adaptation. Next evidence-producing milestone is the approved noiseless spring path: purchased observations → fit → unseen-condition predictions → independently scored report.
- Baseline delta: research and recovery reviews at 2d78e35; 55 tests, lint/format and strict mypy pass; same-head CI covers Python 3.12/3.14, packaging and eight-particle CLI smoke. Two factual documentation corrections committed as 9833e6f and peer reviewed. PR #1 merged as 7117060d03d4e0f843d7dddc53c3e5b580b8ef3f; git diff verified its tree matches reviewed head 5cb1895c280af1ac0ad16bdc954d596089e91b70. All four GitHub CI checks at that head passed on Python 3.12/3.14. [Merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39341809891) also passed at 7117060. SP-00.b is complete; this is not a product release.
- Forecast repair: adding the DB-to-artifact freeze edge changes R0 to W6–7 and first spring integration to W11–13; R1 reserve becomes W26. GA remains W52–67. These remain nine-human-team reference estimates; actual engineer assignments are separate.
- SCI delta: SP-01.a complete via [PR #51](https://github.com/spei04/strange-physics/pull/51), merge cc24aef tree equals reviewed 6e72415; all four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39343441273) pass. 147 tests and independent schema checks passed after three repairs. No fitter, hosted service or benchmark result is claimed.
- Control delta: part 1 integrated via [PR #53](https://github.com/spei04/strange-physics/pull/53), merge d6204aa matching reviewed f6cead9. Four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39344813113) passed after four review fixes at a9fa8cb. 252 total tests, Ruff, strict mypy, 67 external schema/header cases and 47 reference resolutions pass. Full SP-01.b remains incomplete: ID-A sessions are now integrated; identity linking and credential lifecycle contracts still need reviewed PRs. Their consumers remain blocked; four-day reference effort needs re-estimation.
- Session delta: [PR #65](https://github.com/spei04/strange-physics/pull/65) merged cc576da9f7ce43f7bc497289a3e02efa9c74f9d0 with tree cd1f0ff73adb1ca41cbf87a5d4d39802d16d3357 matching independently accepted 34d26d9343c63747e520351d0a99f154596248f0. 413 tests, Ruff, strict mypy and 207 independent schema cases passed; required PR CI39348959056 and protected-main CI39349126536 succeeded. Session policy, one-use proof, bootstrap, renewal/logout and safe errors are contracts only; actual verifier/HTTP/SQL behavior remains later work. ID-B is three PRs: B1 workspace/membership, B2 invitations, B3 explicit identity linking.
- Membership delta: [PR #67](https://github.com/spei04/strange-physics/pull/67) merged 1ec45aabb02b3d4fff98de91fc09bffb0e9c7daf with tree 0e9c0a40c187b417550f5ef601de8e073cca4561 matching independently accepted b9c4754af1ffa5dc2ca18a0d44ddbfa72cc57d5a. 474 full tests (61 focused), Ruff/format/strict mypy and 135 independent offline structural cases/67 reference checks passed. PR CI39350544354 passed the pinned external schema validator and all required checks; protected-main CI39350659100 also succeeded. At that checkpoint B2 invitations, B3 linking and ID-C remained; B2 is now integrated below. Trusted producer obligations cover owner eligibility, pending security-event fences, actual SQL serialization and recovery; those are not deployed implementation claims. Available cloud storage was about 140 MiB at that checkpoint; the later recovery below resolves that capacity block.
- Invitation delta: [PR #69](https://github.com/spei04/strange-physics/pull/69) merged 89e6117f1b5394acd70968b3505c4770fbc9315e; tree f51c4876b460e83799427cdaf19c16e314b4b9dd matches independently accepted 8267865bfbb8b953970dd3ba9f76fd410311ee67. Hosted PR CI39351960120 and protected-main CI39352075786 passed with 560 tests, pinned schema validation, lint/type/security, archive and CLI checks. 86 focused tests and static checks passed locally before the disk stop; no local full-suite claim. Research independently checked 43 runtime/schema plus 128 external cases; Quality checked 9 repair negatives plus 238 external cases. The remote final head adds only reviewed progress documents and the redemption-retry prose clarification to c773946. No HTTP/SQL/provider/rate-limiter implementation is claimed; B3 and ID-C remain open.
- Cloud audit: current shared project/billing accessible; target projects/IAM/quota and credit eligibility/expiry unknown. Deployment NO-GO, Platform owns remediation; product/billing owner supplies private credit evidence. Private raw records remain outside the checkout; no account IDs published.
- Shared storage: cloud free space measured 101,232,640 bytes (~96.5 MiB), then 103,305,216 bytes (~98.5 MiB), on 2026-10-20; checkout mutations stopped below the 100 MiB no-write floor. Mac read-back was 323 MiB after a transient no-space warning. Only ~18 MB is project-owned disposable cloud cache; other projects and migration archives are excluded. This historical stop was resolved by the approved SP-02.b recovery below; no unrelated cleanup occurred.
- Capacity recovery: the product owner approved the concrete 200→300 GiB balanced boot-disk expansion and recovery snapshot on 2026-10-20. Platform completed the globally scoped STANDARD snapshot, stored in us-central1, before expanding the same attached disk and its root partition/ext4 filesystem online. Snapshot completion was 01:54:35 UTC; resize and filesystem growth completed by 01:56:22 UTC. No reboot, stop, detach, formatting, cleanup, dependency install or IAM change occurred. Platform measured 104,103,600,128 bytes free; Quality independently measured 104,113,758,208 bytes (~96.96 GiB), above the 20 GiB gate. The filesystem totals 310,911,414,272 bytes. Both reviewers fully rehashed the protected archive, pinned uv and all 3,414 venv entries; source, manifest/runtime fingerprints, directory metadata, recorded long-lived consumers, boot identity and service state were preserved. Private evidence and its hash index remain outside the checkout with owner-only 0700/0600 permissions. Snapshot review is 2026-10-27, with no automatic deletion; the three-day recycle period begins only after a future deletion. This is a crash-consistent snapshot, not a restore rehearsal or application-health proof. Ordinary diagnostics are reviewed 2026-11-19; unique recovery records remain until superseded. Official [pricing](https://cloud.google.com/compute/disks-image-pricing) and [resize procedure](https://docs.cloud.google.com/compute/docs/disks/resize-persistent-disk).
- CI/CD complete for this package: PR #56 merged 256b409 with a matching reviewed tree. Main run 39347053265 passed all checks and delivered artifact 12231636153; independent in-memory bundle/checksum/source review passed, and the PR produced zero artifacts. DELIVERY_RECORD.md preserves exact hashes and policy read-back. This is unpublished candidate delivery, not deployment or production readiness. One-account GitHub approval limitation remains explicit.
- Budget: the approved expansion adds an estimated ~$10/month and the snapshot up to roughly ~$10/month while retained, before credits/tax; actual billing is not yet measured. Only this capacity action was approved. Staging, provider trials, official sweeps and releases retain their concrete approval gates. Existing VM billing is outside this incremental estimate.
- Tracking: SP-00.a [#44](https://github.com/spei04/strange-physics/issues/44), SP-00.b [#45](https://github.com/spei04/strange-physics/issues/45), SP-02.a [#46](https://github.com/spei04/strange-physics/issues/46), SP-02.b [#72](https://github.com/spei04/strange-physics/issues/72), SP-03.a [#73](https://github.com/spei04/strange-physics/issues/73).

## Next scientific acceptance checkpoint — I1

Research owns the local spring proof; Quality independently authors its development
scorer. SP-02.b is accepted, the checkout is reconciled, and Research now owns
SP-03.a as the first source writer. Platform retains queued B3 linking and Quality retains ID-C after
accepted ID-B; neither enterprise stream is removed.

The approved dependency path is SP-02.b → SP-03.a → SP-03.b → SP-04.a → SP-04.b →
SP-06.a → SP-04.e/I1. SP-03.a also requires completed SP-00.b; SP-03.b requires
completed SP-01.a; SP-04.a also requires SP-02.b; SP-04.e requires both SP-04.b and
SP-06.a. Their transitive predecessors APPROVAL, SP-00.a/b and SP-02.a are complete.
These six scientific PR tasks total 19 reference engineering days plus 4.75 reserve,
not a subagent delivery forecast. Preserve SP-03.a's full analytic fixture scope.

I1 must demonstrate a documented SDK/CLI sequence: buy and retain an exact public
spring observation prefix, fit only that prefix, predict initial conditions or
impulses absent from it within the ratified domain, and produce an independently
scored development report. Labels come from independent analytic references,
not the predictor or simulator under validation. Retain source/environment,
purchased indices, model/configuration/protocol/report hashes, unseen-input
manifest, analytic derivation, counts, errors, timings and CLI round-trip evidence.

SP-03.b must ratify coefficient and trajectory bounds before acceptance; existing
provisional targets are <=1% coefficient error and <=0.001 position RMSE over two
seconds. SCI reports retain MSE and normalized MSE; derive sqrt(position_mse) for
the RMSE acceptance check and document averaging dimensions and normalization.
Insufficient excitation, mass/order mismatch, tampering, divergence and missing
outputs require explicit failures. Any failed probe makes primary MSE fields null
and the report unscorable; never average only surviving probes. A correctly
reported negative result is valid evidence, not permission to relax tolerances.

The accepted simulation/journal/random-investigation CLI and 560 passing tests
do not yet supply a fitter, predictor, independent scorer, generalization result
or recovery result. I1 is a local development proof, not the full held-out
benchmark, hosted execution or a product release.

Unfinished SP-01.b/c/d/e, B3, ID-C, SP-08 identity implementation, staging and whole
R0 exit are not prerequisites in this local path. They remain prerequisites for
their hosted/later consumers (for example SP-06.b requires SP-01.c). Use the leaf
DAG; do not turn their schedule order into a new scientific dependency. With one
checkout, parallel work means independent preparation/review and sequential
writer handoffs. Scorer implementation waits for SP-04.b. The concrete capacity
action is approved and complete; it grants no additional staging or release authority.

## Current blockers and rules

- Capacity stop resolved: the preserved clean c773946 checkout was fetched and fast-forwarded to reviewed main 89a44ed after independent SP-02.b acceptance. Dependency manifests are unchanged. Research received the exclusive SP-03.a writer slot at 01:59 UTC; Platform retains queued B3. The sole authoritative cloud checkout remains in use and must not be archived or removed. No additional checkout or local project copy was created. Writers remain sequential unless separate safe checkouts are available; maintain the >=20 GiB readiness gate separately from the 100 MiB emergency stop floor.
- Final identity review must reconcile issuer + verified tenant/null + subject, global purpose-bound proof ownership, composed human/service/run authority and current authorization before every streamed delivery batch. The <=30-second check applies only to idle connections. B3/ID-C remain implementation assignments, not completed interfaces.
- Cloud filesystem had 215 MiB free at execution start; accepted SP-02.b recovery now permits scoped development. Continue preserving migration archives and other active projects.
- Baseline integration passed both review scopes and required checks at 7117060. Specific contract freezes remain prerequisites; SP-01.c additionally waits for SP-01.b DB acceptance.
- Root coordinates every checkout write; independent writers get separate cloud checkouts. No local project copies.
- Partner/assessor/human operations availability is unconfirmed. No outreach or contractual commitment is implied.
- No priced staging, provider trial, official sweep or production release is approved yet.
- A completed assignment includes source identity, tests, reviewer outcome and limitations. Review findings become bounded repair assignments before acceptance.
