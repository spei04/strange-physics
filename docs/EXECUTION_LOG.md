# Execution assignment log

## Approval and execution capacity

2026-10-19 — Product owner approved execution baseline `2d78e3598252e211110883b164854b64c356eeda` and requested independent engineer subagents, reassignment on completion and this short log.

SP-00.a is complete for the amended execution mode: one project lead plus at most three concurrent engineers. Lead owns TL and unassigned BE/FE lanes; Platform covers PL1/PL2 sequentially; Research covers RS1/RS2 sequentially; Quality covers QE. Lead obtains peer review before integration. The nine-human-team schedule remains a reference and will be reforecast; these assignments do not establish human operations, external assessor availability or partner commitments. D01–D05 recommendations accepted as scope/provisional targets; D06 retains concrete paid and release approvals.

## Assignments

| UTC start | Engineer | Task / scope | State / next handoff |
| --- | --- | --- | --- |
| 2026-10-19 23:22 | Quality | SP-00.b — journal, session, SDK recovery review and existing checks at 2d78e35 | Review passed: 55 tests, Ruff and strict mypy; matching CI includes Python 3.12/3.14 build and CLI smoke |
| 2026-10-19 23:22 | Platform | SP-02.a — cloud preflight; read-only disk inventory to prepare SP-02.b | Audit complete with deployment NO-GO; credit/target-project gaps retained |
| 2026-10-19 23:24 | Research | SP-00.b — independent physics, observations and scientific-boundary review at 2d78e35 | Review passed: 26 physics/contract tests and small analytic checks; not SP-03 domain ratification |
| 2026-10-19 23:25 | Project lead | SP-00.a — approval/roster; integration and dependency coordination | Completed; actual assignment log maintained here |
| 2026-10-19 23:23 | Research | SP-00.b — repair factual law/change-timing documentation | Committed 9833e6f; Quality peer review passed; writer ownership relinquished |
| 2026-10-19 23:24 | Quality | SP-00.a/b — review approval/roster and documentation repair | Peer review passed; 168 Markdown/JSON task states and prerequisites agree |
| 2026-10-19 23:24 | Research | SP-01.a — read-only SCI preparation | Draft only; freeze waits for baseline integration and safe write capacity |
| 2026-10-19 23:24 | Quality | SP-01.b — read-only HTTP/identity/SQL preparation | Six concrete gaps identified; implementation/freeze not started |
| 2026-10-19 23:25 | Platform | SP-02.b — concrete capacity remediation proposal | Ready: 200→300 GiB boot disk plus regional recovery snapshot; explicit approval pending |

## Review evidence and management checkpoint

- Outcome: an enterprise research product that measures discovery and adaptation. Next evidence-producing milestone is the approved noiseless spring path: purchased observations → fit → unseen-condition predictions → independently scored report.
- Baseline delta: research and recovery reviews at 2d78e35; 55 tests, lint/format and strict mypy pass; same-head CI covers Python 3.12/3.14, packaging and eight-particle CLI smoke. Two factual documentation corrections committed as 9833e6f and peer reviewed. PR #1 integration is still pending.
- Preparatory analysis is not implementation: no SCI/HTTP subset frozen, fitter built, hosted service deployed or benchmark result established.
- Cloud audit: current shared project/billing accessible; target projects/IAM/quota and credit eligibility/expiry unknown. Deployment NO-GO, Platform owns remediation; product/billing owner supplies private credit evidence. Private raw records remain outside the checkout; no account IDs published.
- Shared storage: free space fell to 57.7 MiB and fluctuates near 100 MiB. Only ~18 MB is project-owned disposable cache. Other projects, active consumers and migration archives are excluded from cleanup.
- Exact pending action: existing balanced boot disk 200→300 GiB (~+$10/month) with a regional recovery snapshot (up to roughly +$10/month while retained), before credits/tax. No reboot, detach or formatting; verify snapshot READY, exact disk/partition layout, running consumers and >=20 GiB free. Snapshot retention review after seven days; effective recycle retention remains to be verified. Official [pricing](https://cloud.google.com/compute/disks-image-pricing) and [resize procedure](https://docs.cloud.google.com/compute/docs/disks/resize-persistent-disk).
- Budget: no new cloud/provider spend incurred or reserved. Disk/snapshot proposal remains unapproved. Existing VM billing is outside this new-work spend record.
- Tracking: SP-00.a [#44](https://github.com/spei04/strange-physics/issues/44), SP-00.b [#45](https://github.com/spei04/strange-physics/issues/45), SP-02.a [#46](https://github.com/spei04/strange-physics/issues/46).

## Current blockers and rules

- Cloud filesystem had 215 MiB free at execution start. SP-02.b gates installs/builds; preserve migration archives and other active projects.
- Baseline integration must pass both review scopes and required checks before SP-01 consumers begin.
- Root coordinates every checkout write; independent writers get separate cloud checkouts. No local project copies.
- Partner/assessor/human operations availability is unconfirmed. No outreach or contractual commitment is implied.
- No priced staging, provider trial, official sweep or production release is approved yet.
- A completed assignment includes source identity, tests, reviewer outcome and limitations. Review findings become bounded repair assignments before acceptance.
