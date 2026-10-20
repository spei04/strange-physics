# Execution assignment log

## Approval and execution capacity

2026-10-19 — Product owner approved execution baseline `2d78e3598252e211110883b164854b64c356eeda` and requested independent engineer subagents, reassignment on completion and this short log.

SP-00.a is complete for the amended execution mode: one project lead plus at most three concurrent engineers. Lead owns TL and unassigned BE/FE lanes; Platform covers PL1/PL2 sequentially; Research covers RS1/RS2 sequentially; Quality covers QE. Lead obtains peer review before integration. The nine-human-team schedule remains a reference and will be reforecast; these assignments do not establish human operations, external assessor availability or partner commitments. D01–D05 recommendations accepted as scope/provisional targets; D06 retains concrete paid and release approvals.

## Current assignment board

| Engineer | Current / next work | Review and gate |
| --- | --- | --- |
| Platform | C2 run-credential preparation | C1 source independently accepted; implementation waits C1 integration and identity handoff |
| Research | SP-04.e/I1 SDK/CLI preparation and scorer review | Read-only preparation; SDK/CLI source waits accepted scorer |
| Quality | SP-06.a/#83 independent development scorer | Exclusive primary writer after accepted predictor; publish protocol/API for review before implementation |
| Project lead | C1 integration and scorer coordination | Owns identity integration; Quality owns primary; exact-head checks before each merge |

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
| 2026-10-20 02:05 | Research | SP-03.a/#73 — analytic fixtures and numerical evidence | Source 66016cf accepted; 613 full tests, 64 physics tests, Ruff/format and strict mypy passed; writer released |
| 2026-10-20 02:05 | Quality + Platform | SP-03.a — independent scientific/SDK review | Accepted immutable source/docs; Quality reproduced 53 cases and measurements, detected seven injected physics errors |
| Next after SP-03.a integration | Research | SP-03.b/#75 — first-spring domain, sampling bias and error bounds | Read-only preparation; authoring waits for dependency acceptance and lead handoff |
| 2026-10-20 02:09 | Project lead | SP-03.a integration and SP-03.b writer handoff | PR #76 merged 8510243; accepted tree e81fa2f matches reviewed 2c73c3c; PR/main CI passed; existing checkout reused |
| 2026-10-20 02:09 | Research | SP-03.b/#75 — calibration implementation | In progress; predeclared domain, quadrature/solver/prediction separation, zero/weak excitation and per-probe acceptance |
| 2026-10-20 02:13 | Platform | ID-B/B3/#63 — explicit identity linking | Active in one separate cloud worktree; primary checkout remains with Research; bounded plan accepted |
| 2026-10-20 02:20 | Quality | SP-03.b — independent reproduction and numerical failure review | Reproduced fixed matrices; found derived-arithmetic and propagation overflow paths; Research repaired explicit JSON-safe failure accounting |
| 2026-10-20 02:25 | Research | SP-03.b/#75 — noiseless domain calibration and noise sensitivity | 43e0589 accepted; 817 full tests, 204 focused; Ruff/format and strict mypy passed; primary writer released |
| 2026-10-20 02:25 | Project lead | SP-03.b integration; SP-04.a/#77 preparation assigned | Quality accepted immutable source; exact-head CI still required; production fitter authoring follows integration |
| 2026-10-20 02:29 | Project lead | SP-03.b integration and SP-04.a writer handoff | PR #78/main db182788 matches reviewed7b27bad/tree08efb975; PR CI39358928012 and main CI39359050024 passed; reused primary checkout |
| 2026-10-20 02:29 | Research | SP-04.a/#77 — versioned public-prefix spring fitter | Bounded config/result API accepted; no prediction/scoring claim; Quality and Platform independently review |
| 2026-10-20 02:31 | Platform | ID-B/B3/#63 — reviewed linking contract and repairs | Source051d8f7 accepted by Research/Quality/lead; 714 branch tests, 222 focused, static/schema/package checks passed; identity writer released |
| 2026-10-20 02:31 | Project lead | Integrate B3 with accepted scientific main and reconcile stream contracts | Exact integrated-head checks before merge; three stream acceptance statements clarified without changing graph/effort/gates |
| 2026-10-20 02:31 | Quality | ID-C/#64 — bounded credential API preparation | C1 service/key lifecycle then C2 run credentials/composition; read-only until B3 integration; Platform reviews fitter |
| 2026-10-20 02:39 | Project lead | B3 integration and C1 writer handoff | PR #79/main24c8796 matches reviewedc716ede/treeaedc6064; PR/main CI passed; same identity checkout reused |
| 2026-10-20 02:39 | Quality | ID-C/C1/#64 — service principal and key lifecycle | Accepted bounded route/model plan; no actual verifier/HTTP/SQL; C2 waits C1 and full parent freeze remains open |
| 2026-10-20 02:42 | Research | SP-04.a/#77 production fitter | c43cd801 independently accepted by Quality/Platform; 905 author tests and static/schema/package checks; primary writer released |
| 2026-10-20 02:42 | Project lead | SP-04.a integrated-source verification | Accepted B3/main and reviewed assignment progress reconciled; 1,006 tests and lint/format/type/schema checks passed; hosted CI next |
| 2026-10-20 02:43 | Research + Platform | SP-04.b bounded predictor design | Research prepares API/runtime/oracle plan; Platform challenges it; no implementation before accepted fitter integration |
| 2026-10-20 02:49 | Project lead | SP-04.a integration and SP-04.b writer handoff | PR #80 accepted with matching reviewed tree and PR/main CI; reused primary checkout |
| 2026-10-20 02:49 | Research | SP-04.b/#81 production predictor | Bounded analytic runtime and independent Decimal-oracle plan accepted; record preregistration before measurements |
| 2026-10-20 03:06 | Research | SP-04.b/#81 analytic predictor and evidence | ec959b5 accepted by lead/Platform; 1,320 full tests, 314 independent focused cases and package verification; primary writer released |
| 2026-10-20 03:06 | Project lead | SP-04.b integration; next assignments | Exact-head hosted checks next; Quality moves to SP-06.a after C1 release, Platform takes C2 after C1 acceptance, Research prepares SDK/CLI read-only |
| 2026-10-20 03:06 | Quality + Platform + lead | C1 adversarial review | Four repairs tracked: role-independent key counts, common referenced-record retention, creation workspace CAS and principal snapshot evolution |
| 2026-10-20 03:12 | Project lead | Predictor integrated; scorer writer handoff | PR #82 and protected main passed with matching reviewed tree; primary checkout reused |
| 2026-10-20 03:12 | Quality | SP-06.a/#83 independent scorer | C1 source released at 5009fdf; current protocol/API review precedes implementation; Research prepares SDK/CLI consumer |
| 2026-10-20 03:12 | Platform | C2 preparation | C1 source accepted; identity authoring begins after C1 integration and writer handoff |

## Review evidence and management checkpoint

- Outcome: an enterprise research product that measures discovery and adaptation. Next evidence-producing milestone is the approved noiseless spring path: purchased observations → fit → unseen-condition predictions → independently scored report.
- Baseline delta: research and recovery reviews at 2d78e35; 55 tests, lint/format and strict mypy pass; same-head CI covers Python 3.12/3.14, packaging and eight-particle CLI smoke. Two factual documentation corrections committed as 9833e6f and peer reviewed. PR #1 merged as 7117060d03d4e0f843d7dddc53c3e5b580b8ef3f; git diff verified its tree matches reviewed head 5cb1895c280af1ac0ad16bdc954d596089e91b70. All four GitHub CI checks at that head passed on Python 3.12/3.14. [Merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39341809891) also passed at 7117060. SP-00.b is complete; this is not a product release.
- Forecast repair: adding the DB-to-artifact freeze edge changes R0 to W6–7 and first spring integration to W11–13; R1 reserve becomes W26. GA remains W52–67. These remain nine-human-team reference estimates; actual engineer assignments are separate.
- SCI delta: SP-01.a complete via [PR #51](https://github.com/spei04/strange-physics/pull/51), merge cc24aef tree equals reviewed 6e72415; all four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39343441273) pass. 147 tests and independent schema checks passed after three repairs. No fitter, hosted service or benchmark result is claimed.
- Control delta: part 1 integrated via [PR #53](https://github.com/spei04/strange-physics/pull/53), merge d6204aa matching reviewed f6cead9. Four head checks and [merge-main CI](https://github.com/spei04/strange-physics/actions/runs/39344813113) passed after four review fixes at a9fa8cb. 252 total tests, Ruff, strict mypy, 67 external schema/header cases and 47 reference resolutions pass. Full SP-01.b remains incomplete: ID-A sessions are now integrated; identity linking and credential lifecycle contracts still need reviewed PRs. Their consumers remain blocked; four-day reference effort needs re-estimation.
- Session delta: [PR #65](https://github.com/spei04/strange-physics/pull/65) merged cc576da9f7ce43f7bc497289a3e02efa9c74f9d0 with tree cd1f0ff73adb1ca41cbf87a5d4d39802d16d3357 matching independently accepted 34d26d9343c63747e520351d0a99f154596248f0. 413 tests, Ruff, strict mypy and 207 independent schema cases passed; required PR CI39348959056 and protected-main CI39349126536 succeeded. Session policy, one-use proof, bootstrap, renewal/logout and safe errors are contracts only; actual verifier/HTTP/SQL behavior remains later work. ID-B is three PRs: B1 workspace/membership, B2 invitations, B3 explicit identity linking.
- Membership delta: [PR #67](https://github.com/spei04/strange-physics/pull/67) merged 1ec45aabb02b3d4fff98de91fc09bffb0e9c7daf with tree 0e9c0a40c187b417550f5ef601de8e073cca4561 matching independently accepted b9c4754af1ffa5dc2ca18a0d44ddbfa72cc57d5a. 474 full tests (61 focused), Ruff/format/strict mypy and 135 independent offline structural cases/67 reference checks passed. PR CI39350544354 passed the pinned external schema validator and all required checks; protected-main CI39350659100 also succeeded. At that checkpoint B2 invitations, B3 linking and ID-C remained; B2 is now integrated below. Trusted producer obligations cover owner eligibility, pending security-event fences, actual SQL serialization and recovery; those are not deployed implementation claims. Available cloud storage was about 140 MiB at that checkpoint; the later recovery below resolves that capacity block.
- Invitation delta: [PR #69](https://github.com/spei04/strange-physics/pull/69) merged 89e6117f1b5394acd70968b3505c4770fbc9315e; tree f51c4876b460e83799427cdaf19c16e314b4b9dd matches independently accepted 8267865bfbb8b953970dd3ba9f76fd410311ee67. Hosted PR CI39351960120 and protected-main CI39352075786 passed with 560 tests, pinned schema validation, lint/type/security, archive and CLI checks. 86 focused tests and static checks passed locally before the disk stop; no local full-suite claim. Research independently checked 43 runtime/schema plus 128 external cases; Quality checked 9 repair negatives plus 238 external cases. The remote final head adds only reviewed progress documents and the redemption-retry prose clarification to c773946. No HTTP/SQL/provider/rate-limiter implementation is claimed; B3 and ID-C remain open.
- Analytic fixture delta: SP-03.a source 66016cf6b5f3bcb74d98ace504e1e6b2db77d080 (tests ea3ebf12fa90ad415f970d5127dc1dc15a667ae8) was independently accepted by Quality and Platform. 53 new cases bring the full local suite to 613; 64 focused physics tests, repository Ruff/format (59 files) and strict mypy (32 source files) pass. Quality independently ran immutable cases, reproduced error/energy measurements and detected seven injected physics mistakes. Worst analytic position-or-velocity norm error was 6.5304e-8 against the predeclared 2e-7 component limit; timestep refinement reduced errors about sixteenfold. No tolerance, production source, study distribution, dependency or old assertion changed. [NUMERICAL_VALIDATION.md](NUMERICAL_VALIDATION.md) preserves equations, fixture limits, measured errors and reproduction. Required exact-head CI is enforced before integration. These are bounded synthetic fixtures; SP-03.b domain ratification and fit/predict/score remain unfinished.
- Analytic integration: [PR #76](https://github.com/spei04/strange-physics/pull/76) merged 8510243a029fc24a8ec4067c6737762fa2c7bc29 with tree e81fa2f030fd4326ad5716504302a934df2158d3 matching reviewed head 2c73c3cfc12487dadc0ca9cb850e44c464cb271e. PR CI39357113227 and protected-main CI39357223876 passed, including main candidate delivery. Issue #73 is closed; SP-03.b remains a separate calibration task.
- Capacity integration: [PR #74](https://github.com/spei04/strange-physics/pull/74) merged f197687cbf7327d29ef6bad06cc228dcbaf4a10a, tree b1bd3b926aba4a6a1e4a6d060ee9b9461e370405 matching accepted head 579907b1be757ee2fb1708b854dfe12196f6aefe. PR CI39356603093 and protected-main CI39356704081 succeeded, including main candidate delivery. Issue #72 is closed; this records capacity recovery, not staging approval.
- Cloud audit: current shared project/billing accessible; target projects/IAM/quota and credit eligibility/expiry unknown. Deployment NO-GO, Platform owns remediation; product/billing owner supplies private credit evidence. Private raw records remain outside the checkout; no account IDs published.
- Shared storage: cloud free space measured 101,232,640 bytes (~96.5 MiB), then 103,305,216 bytes (~98.5 MiB), on 2026-10-20; checkout mutations stopped below the 100 MiB no-write floor. Mac read-back was 323 MiB after a transient no-space warning. Only ~18 MB is project-owned disposable cloud cache; other projects and migration archives are excluded. This historical stop was resolved by the approved SP-02.b recovery below; no unrelated cleanup occurred.
- Capacity recovery: the product owner approved the concrete 200→300 GiB balanced boot-disk expansion and recovery snapshot on 2026-10-20. Platform completed the globally scoped STANDARD snapshot, stored in us-central1, before expanding the same attached disk and its root partition/ext4 filesystem online. Snapshot completion was 01:54:35 UTC; resize and filesystem growth completed by 01:56:22 UTC. No reboot, stop, detach, formatting, cleanup, dependency install or IAM change occurred. Platform measured 104,103,600,128 bytes free; Quality independently measured 104,113,758,208 bytes (~96.96 GiB), above the 20 GiB gate. The filesystem totals 310,911,414,272 bytes. Platform and Quality fully rehashed the protected archive, pinned uv and all 3,414 venv entries; source, manifest/runtime fingerprints, directory metadata, recorded long-lived consumers, boot identity and service state were preserved. Private evidence and its hash index remain outside the checkout with owner-only 0700/0600 permissions. Snapshot review is 2026-10-27, with no automatic deletion; the three-day recycle period begins only after a future deletion. This is a crash-consistent snapshot, not a restore rehearsal or application-health proof. Ordinary diagnostics are reviewed 2026-11-19; unique recovery records remain until superseded. Official [pricing](https://cloud.google.com/compute/disks-image-pricing) and [resize procedure](https://docs.cloud.google.com/compute/docs/disks/resize-persistent-disk).
- CI/CD complete for this package: PR #56 merged 256b409 with a matching reviewed tree. Main run 39347053265 passed all checks and delivered artifact 12231636153; independent in-memory bundle/checksum/source review passed, and the PR produced zero artifacts. DELIVERY_RECORD.md preserves exact hashes and policy read-back. This is unpublished candidate delivery, not deployment or production readiness. One-account GitHub approval limitation remains explicit.
- Linking integration: PR #79 merged24c879612c92913d04b7b54456515a69b46ee67b; treeaedc60646121d591eb593e0261e6a9c4a4abb808 matches reviewedc716ede7cad5b745ceb5d473d7f301c448107a0a. PR CI39359729686 and main CI39359864028 passed all applicable checks, including candidate build; 918 integrated tests, Ruff/format64, strict mypy35 and478 external schema checks passed.
- Credential planning: Provisional remaining ID-C human effort: C1 service/key lifecycle 3–5 engineer-days (medium); C2 run credentials/composition 2–4 (medium-low); shared final composition review/integration 1–2, counted once. Total6–11 engineer-days includes uncertainty; no additional reserve is added. This supersedes the original two-day ID-C expectation for current execution only; the nine-human reference forecast remains historical and agent elapsed time is not human effort evidence.
- Linking delta: ID-B/B3 source051d8f708a5f5cc1a9182448466eb6dbdeb10f55 passed Research, Quality and lead review. Platform passed 714 full branch tests, 222 focused session/link tests, Ruff/format (62 files), strict mypy (34), 478 external schema checks, configured Bandit severity gate and offline wheel/sdist allowlist validation. Research independently ran 100 linking cases; Quality ran all222 and confirmed repaired guard-mutation coverage. Fixes bind audit replay, expose public commit revision, reject invalid primary authority before freshness advice, prevent cross-provider login/link callback collisions and define safe429 responses. Shared trusted proof purpose/owner is an explicit internal producer amendment; public login HTTP is unchanged. Root integrated accepted scientific progress before exact-head checks. No real verifier, broker, HTTP, SQL or recovery enforcement is claimed; ID-C and final parent freeze remain open.
- Calibration integration: [PR #78](https://github.com/spei04/strange-physics/pull/78) merged as db18278821d72d3ba02336e45827d441af0a00b6; tree08efb97564ff99f7056551a04b93b27b5460f3eb matches independently accepted7b27bad5a6d947580d231b337df8836558a62131. PR CI39358928012 and protected-main CI39359050024 passed all applicable jobs, including the main candidate build. SP-03.b is complete for its bounded calibration scope; SP-04.a is now assigned.
- Calibration delta: SP-03.b source 43e05897587ba3b7e1a4266c2d40af7cbaa1b5b6 passed independent Quality and lead review. Preregistration 5e524a1 and proof clarification f55d38f preceded measurements. All 63 primary and seven mixed-mass noiseless prefixes meet the joint criteria; maximum per-probe RMSE 8.46960e-6. Weak excitation retains 34 unsupported / 48 cases. Noise retains all 64 prefixes: six negative estimates, 13 joint passes, 406 computed probes over the bound and 144 failed probes. Derived arithmetic/propagation failures remain JSON-safe and counted. 817 full tests and 204 focused cases, Ruff/format and strict mypy passed; exact-head hosted CI remains an integration gate. SPRING_DOMAIN.md documents reproduction, analytic bounds and finite-matrix limitations. This is test-only calibration, not a production fitter/predictor/scorer or I1 exit.
- Predictor integration: PR #82/main 9c341f8c282865387b2c562d15568a953d7bc7b5 matches reviewed d37118e35f8b7d970e9237a95bcf845322468110/tree 4d33a099fa47c18e6f4e78d1892f1005538adccc. PR CI39362603040 and protected-main CI39362758495 passed, including the installed candidate. SP-04.b is complete for its bounded runtime; independent scoring and SDK/CLI I1 evidence remain.
- Predictor delta: ec959b5e89ac1489ff8ba35c4fd431a928e89787 preserves accepted runtime 205b3fc and preregistration 9f30fa2. All 1,320 tests, lint/format, strict mypy (43 files), 506 external schema checks, configured Bandit gate and offline package verification passed. Lead reran both focused files from immutable source; Platform ran all 314 plus 27 boundary/varied-input checks and detected five deliberate numerical defects. All 168 direct oracle and 18 near-zero requests satisfy the fixed 1e-12 component threshold. All 70 fitted models generated all 1,680 probes; worst per-probe RMSE 8.4695975e-6, zero failed outcomes. Prediction uses exact timestamps and returns no partial response. Hosted exact-head checks remain; no scorer, official benchmark or I1 claim.
- Fitter integration: PR #80 merged e5a3c8d8b7d718be9be7d88e81fb4cad90e73f1a; tree cbe89e1d14646d3e9d77b96b97d8f267e6cfaafd matches reviewed 833d8c711ecdc97e3817ed744f9ff674331d0d1f. PR CI39360722931 and main CI39360858087 passed all applicable jobs, including the protected-main candidate build. SP-04.a is complete for its bounded fitting scope; SP-04.b is now assigned. No prediction/scoring/I1 result is claimed.
- Fitter delta: source c43cd8011efdb6fe2dc27ce251803eba4fe36597 independently accepted by Quality and Platform. Each reran all 88 focused cases; Quality detected five and Platform ten deliberate source defects. The fixed config binds the actual digest, consumes every eligible paired-Simpson window using public masses, retains failed-record provenance and zero rows, and reports finite/negative/weak failures explicitly. Author checks passed 905 tests, external schema validation and offline package allowlist. Reconciliation with B3 passed 1,006 tests, Ruff/format (69 files), strict mypy (39 files) and external schema validation. No frozen SCI bytes or dependency manifest changed. Exact-head hosted checks remain before merge; fitting success makes no accuracy, prediction, score or I1 claim.
- Budget: the approved expansion adds an estimated ~$10/month and the snapshot up to roughly ~$10/month while retained, before credits/tax; actual billing is not yet measured. Only this capacity action was approved. Staging, provider trials, official sweeps and releases retain their concrete approval gates. Existing VM billing is outside this incremental estimate.
- Tracking: SP-00.a [#44](https://github.com/spei04/strange-physics/issues/44), SP-00.b [#45](https://github.com/spei04/strange-physics/issues/45), SP-02.a [#46](https://github.com/spei04/strange-physics/issues/46), SP-02.b [#72](https://github.com/spei04/strange-physics/issues/72), SP-03.a [#73](https://github.com/spei04/strange-physics/issues/73).

## Next scientific acceptance checkpoint — I1

Research owns the local spring proof; Quality independently authors its development
scorer. SP-02.b is accepted and SP-03.a fixtures have passed independent review.
SP-03.a and SP-03.b are integrated, including exact-head PR/main checks.
SP-04.a/#77 is integrated with matching reviewed tree and PR/main CI.
SP-04.b/#81 is integrated with passing PR/main CI. Quality owns the primary
checkout for independent SP-06.a/#83 scoring. Research prepares SP-04.e read-only.
C1 source 5009fdf is independently accepted; the lead owns identity integration.
Platform takes C2 after C1 integration and identity writer handoff.

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

SP-03.b ratifies the bounded noiseless finite matrix with coefficient error
<=max(1e-8, 0.01*k_true) and <=0.001 coordinate position RMSE for every probe over
two seconds. The absolute floor handles zero/near-zero stiffness; see SPRING_DOMAIN.md
for exact-sample bounds, finite-grid evidence and the retained noisy failures.
SCI reports retain MSE and normalized MSE; derive sqrt(position_mse) for
the RMSE acceptance check and document averaging dimensions and normalization.
Insufficient excitation, mass/order mismatch, tampering, divergence and missing
outputs require explicit failures. Any failed probe makes primary MSE fields null
and the report unscorable; never average only surviving probes. A correctly
reported negative result is valid evidence, not permission to relax tolerances.

Simulation, purchased journals, calibration, fitting and bounded prediction are
integrated. Independent scoring, the SDK/CLI I1 exit and recovery evaluation
remain unfinished. I1 is a local development proof, not the full held-out
benchmark, hosted execution or a product release.

Unfinished SP-01.b/c/d/e, B3, ID-C, SP-08 identity implementation, staging and whole
R0 exit are not prerequisites in this local path. They remain prerequisites for
their hosted/later consumers (for example SP-06.b requires SP-01.c). Use the leaf
DAG; do not turn their schedule order into a new scientific dependency. Two cloud
checkouts support independent scientific and identity work; each checkout
has one writer and its own locked dependency installation. Reuse them sequentially
at handoff and retain independent review. Scorer implementation waits for SP-04.b.
The concrete capacity
action is approved and complete; it grants no additional staging or release authority.

## Current blockers and rules

- Capacity stop resolved: independent SP-02.b acceptance preserved source and dependencies; PR #74/main f197687 records recovery, and PR #76/main 8510243 records accepted SP-03.a. One additional ordinary cloud worktree was necessary for independent B3 authoring while Research owned the primary checkout. Its own locked copy-mode environment occupies about 179 MiB; 103,889,854,464 bytes remained free at creation. Managed creation cannot target this remote host from the local chat, so the remote worktree is unmanaged and indexed privately. Both checkouts remain active and must be reused, not archived or removed. No local project copy or shared mutable dependency links. Maintain >=20 GiB readiness separately from the 100 MiB emergency stop floor.
- Final identity review must reconcile issuer + verified tenant/null + subject, global purpose-bound proof ownership, composed human/service/run authority and current authorization before every streamed delivery batch. The <=30-second check applies only to idle connections. B3 is integrated; ID-C and final composition remain unfinished.
- Cloud filesystem had 215 MiB free at execution start; accepted SP-02.b recovery now permits scoped development. Continue preserving migration archives and other active projects.
- Baseline integration passed both review scopes and required checks at 7117060. Specific contract freezes remain prerequisites; SP-01.c additionally waits for SP-01.b DB acceptance.
- Root coordinates every checkout write; independent writers get separate cloud checkouts. No local project copies.
- Partner/assessor/human operations availability is unconfirmed. No outreach or contractual commitment is implied.
- No priced staging, provider trial, official sweep or production release is approved yet.
- A completed assignment includes source identity, tests, reviewer outcome and limitations. Review findings become bounded repair assignments before acceptance.
