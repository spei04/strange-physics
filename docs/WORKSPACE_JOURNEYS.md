# Researcher workspace journeys

SP-22.a design draft for product and producer/consumer review. Source baseline:
`f6cead9c09272e98bdacdeb8d8f687368f2fac3f`. This specifies behavior before client
implementation; it does not demonstrate a working UI or accessibility conformance.

The [inventory](workspace-journeys.inventory.json) assigns stable scenario IDs,
states, accessibility checks and real producer tasks. Its tests check consistency
with the repository contracts and backlog, not browser behavior.

## Contract and review boundary

- The first [identity/run subset](IDENTITY_RUN_CONTRACT.md) defines run states,
  scoped operations, cancellation and canonical request semantics. SP-01.b remains
  incomplete: browser sessions, membership/invitation and credential management
  still need their public contracts and review.
- C-WEB/SP-01.d still owns world projections, events, replay chunks, cursor expiry
  and archive resynchronization. C-ART/SP-01.c owns artifact/visibility envelopes.
  No paths, operation IDs, field names, cursor lifetimes or export grants below
  are new frozen API definitions.
- SP-22.a may be designed after SP-00.b. Client work still waits for its actual
  SP-22.c/d/e and SP-23/24 prerequisites. Draft fixtures are not deployed evidence.
- Product, frontend, backend and security review must accept the journeys before
  client code. Research reviews information boundaries. Automated and manual
  browser evidence belongs to SP-24.d and SP-30.a.
- Remaining decisions: management-role matrix; invitation recipient binding;
  browser session/CSRF lifecycle; exact resync transport; author-preview and
  post-run truth grants; export creation/retrieval authority. Default deny applies
  until the relevant contract explicitly grants an operation.

## Permissions and information

| Actor | Design behavior | Boundary still requiring contract review |
| --- | --- | --- |
| Owner | Manage membership, provider connections, quotas, publication and deletion; perform authorized study actions | Administrative role never grants blind truth or provider-secret reads |
| Researcher | Create/version authorized worlds; start and cancel authorized studies; inspect permitted results | Run-read does not grant every artifact or export |
| Viewer | Read permitted runs and artifacts | No world/run/membership mutation |
| Anonymous visitor | Inspect intentionally published releases | No private lookup or hosted arbitrary-code execution |
| Removed/revoked principal | No further authorized private activity | Previously downloaded files cannot be retracted |

The roadmap assigns owner intent to export/publication/deletion. Full-export
creation is therefore owner-only in this draft; researcher export authority is
unresolved, not silently granted. Retrieval of an existing export needs its own
current artifact authorization. Workspace creation and initial ownership must
come from the eventual identity contract, not a client-selected role.

World-author preview is a separately authorized projection. An author can know
their own law; a human author steering a strategy is not a blinded condition.
Changing the displayed projection cannot erase that knowledge. Switching views
clears inappropriate rendered/cached content as defense in depth, while the
server, agent process, API responses, SSE, errors and exports must enforce the
actual information boundary.

The active-agent view receives public structure and purchased observations.
Authorized learned coefficients, model provenance and predictions may be shown;
hidden true coefficients, held-out labels/scores and concealed change markers
must not appear. Official blind worlds have no author or owner bypass.
Post-run truth is a separately authorized artifact: a terminal run alone does
not release it.

## Shared behavior

| UI condition | Required behavior |
| --- | --- |
| Loading | Name what is loading; retain focus; do not render an empty success state |
| Empty | Explain what is absent and offer only actions the current role permits |
| Ready | Display current workspace, role and resource/version identity |
| Submitting | Prevent accidental duplicate action while keeping status accessible |
| Outcome unknown | Preserve the logical operation identity; reconcile before repeating; do not assume failure or create a new key |
| Retryable error | Show safe explanation, correlation reference and an explicit retry; respect server retry instructions |
| Permanent error | Explain the permitted next step; preserve relevant nonsensitive form input |
| Private/unavailable | Use non-enumerating resource messaging; disclose no foreign names or metadata |
| Session expired | Reauthenticate without automatically replaying mutations |
| Revoked | Stop streams/requests, clear private view and cache, and move focus to an access-status message |

Use server state and committed sequences for progress, counters and outcomes.
Budget exhaustion, connectivity loss and uncertain submission are conditions,
not additional backend run states. Distinguish billed, estimated and unknown
provider usage. Never replace missing values with zero or imply a retry is free.
Do not put credentials, private payloads or author truth in diagnostics.

<a id="j01"></a>
## J01 — Workspace and invitation

**Entry:** signed-out visitor, authenticated account without memberships, or an
existing member. Authenticate through the configured identity flow, then load
current authorized workspaces and roles. A new workspace is private; initial
owner assignment is server controlled. Owners manage invitations and roles.
Invitation acceptance authenticates the intended recipient under the frozen
recipient-binding policy and consumes a single-use, unexpired invitation.

**States:** loading/bootstrap failure; no memberships; pending invitation;
expired/revoked/used invitation; account mismatch; successful acceptance; role
change; sole-owner removal denied; cross-workspace denial; session expiry and
revocation. No email-domain auto-join or email-only identity linking. Concurrent
acceptance and same-person retries follow the frozen identity contract.

**Accessible path:** labeled authentication/invitation actions, visible current
role, error summary and focus on the resulting workspace heading. Keep secrets
out of live announcements and diagnostics.

**Producers:** SP-08.a/b/d, SP-11.c, SP-22.c. **Scenarios:** F01–F05.

<a id="j02"></a>
## J02 — Author and version a world

**Entry:** owner/researcher with author permission. Choose an approved law
implementation, edit supported particle/anchor/topology and parameter fields,
validate, save an immutable version, and reopen that exact version. The initial
builder remains within the accepted three-family, 2D/eight-particle domain.
It does not execute arbitrary uploaded law code.

**States:** empty catalog; valid form; invalid bounds/topology; saving; uncertain
save result; stale-version conflict. Preserve the draft on a recoverable failure.
Resolve an uncertain save through the eventual catalog operation/version contract
before creating another version. Existing runs keep their original world version.

**Accessible path:** every canvas edit has labeled numeric/list controls.
Selection, add/remove and position changes work without dragging. Author preview
and agent view have persistent text labels and different authorized data.
Switching to agent view never sends author data to the agent.

**Producers:** SP-01.d, SP-22.b/d. **Scenarios:** F06–F09.

<a id="j03"></a>
## J03 — Start a run

**Entry:** authorized owner/researcher with a saved world and approved package.
Review exact world/package versions, research track, experiment budget and
resource limits before submitting. Keep experiment allowance distinct from
CPU/provider/artifact limits. Label controlled-selection and complete-agent
tracks distinctly. Missing prerequisites have explanatory disabled actions.

**States:** review; submitting; unknown submission outcome; accepted operation;
queued/preparing; changed-payload conflict; schema rejection; quota/admission
rejection; temporary platform outage. Use the same logical request identity for
reconciliation/retry. Acknowledgement is not execution completion. Switching
workspace while waiting must not apply a response to the new workspace.

**Accessible path:** review summary before the start control; field-linked
validation errors; status announcement without unexpected focus movement.

**Producers:** SP-09.b/c, SP-12.b/c, SP-16.a, SP-22.e.
**Scenarios:** F10–F13.

<a id="j04"></a>
## J04 — Cancel or observe expiry

**Entry:** authorized owner/researcher viewing a nonterminal run. Explain that
cancellation stops further work and preserves already committed results; it does
not erase accepted experiment charges. On submission show request pending, then
the server's cancelling/cancelled state.

Cancellation acceptance atomically fences new launch, broker, result and
checkpoint authority. A real result committed before acceptance remains; a later
result is rejected even before resource settlement. The UI must not claim worker
termination or refunds from a 202 acknowledgement. Queued work with no active
resources can become cancelled directly.

**States:** pending acknowledgement; cancelling; cancelled; completion winning
the race; expiry; explicit termination/reconciliation fault. Keep authoritative
state and unfinished resource settlement visible. Do not invent a successful
retry or reopen a terminal run.

**Accessible path:** confirmation names the run and consequences; focus remains
predictable and returns to the run status after acknowledgement.

**Producers:** SP-09.c, SP-16.c/e, SP-23.d. **Scenarios:** F14–F16.

<a id="j05"></a>
## J05 — Inspect live investigation

**Entry:** an authorized read role. Display committed observations, logical
operation outcomes, accepted/remaining experiment counts and recorded costs.
Show the last committed sequence/lag through the eventual WEB projection.
Event timestamps do not establish ordering.

**States:** no observations yet; live updates; recovering; reconnecting;
duplicate/reordered events; detected gap; expired cursor; archive resynchronizing;
failed resync; revoked membership. Deduplicate committed events and resynchronize
from the authoritative snapshot/archive on expiry. Do not silently skip history
or double-count a budget. If resync fails, retain a clearly stale permitted
snapshot and disable claims of current completeness. Revocation clears it.

Ambiguous provider calls retain unknown outcome/cost until reconciled; no silent
paid retry. Active surfaces contain no evaluator feedback. A diagnostic can show
a learned model without exposing hidden true parameters.

**Accessible path:** meaningful progress announcements are bounded; avoid reading
every animation frame. Updates do not move keyboard focus or steal scroll.
A textual event/observation table provides the same essential information.

**Producers:** SP-23.a/b/c/d, SP-12.c, SP-20.d. **Scenarios:** F17–F21.

<a id="j06"></a>
## J06 — Replay and compare

**Entry:** authorized recorded data, including failed/cancelled/expired runs.
Choose an experiment and recorded timestamp, then play/pause, step or scrub.
Reference frames come from stored data. Visual interpolation is labeled and does
not become a scientific observation or browser-side simulation.

Label series separately: recorded observation (which may include observation
noise), model prediction with snapshot/purchased-history provenance, and
noiseless ground truth only when separately authorized. Optional model intervals
state their declared level and calibration status; absent intervals remain
unavailable.

**States:** loading chunks; missing/corrupt/unsupported artifact; partial replay;
missing/invalid prediction; absent uncertainty; withheld truth. Partial/truncated
frames remain incomplete/unverified and cannot be fabricated into a completed
ExperimentRecord or a valid scorable prefix. The committed record prefix may
include terminal failed simulations; fitted evidence is the separately declared
subset of completed observations.

Show the SCI development report as a development report. Under its current
policy any failed prediction makes primary MSE unavailable/unscorable; retain
the counts and reasons. Official benchmark scoring still requires a separate freeze.

Comparisons require compatible track, protocol, budgets and conditions for
pooled rankings or aggregate claims. If incompatible, disable those claims;
clearly labeled exploratory juxtaposition is permitted. Retain failed outcomes.

**Accessible path:** play/pause, previous/next-frame buttons, a named keyboard
slider with timestamp text, numeric values and text/table alternatives.
Start paused; honor reduced-motion preferences.

**Producers:** SP-24.a/b/c/d, SP-21.c. **Scenarios:** F22–F25.

<a id="j07"></a>
## J07 — Export for verification

**Entry:** currently authorized export creator or reader. Request a private
export under the eventual ID/ART authority policy, observe the asynchronous
operation and retrieve its manifest/artifacts. Export is separate from explicit
sanitized publication.

**States:** pending; complete; incomplete; failed; expired retrieval grant;
revoked access; missing content or checksum mismatch during offline verification.
A failed/cancelled run can have a complete account of an incomplete investigation;
label manifest completeness separately from scientific success. Preserve
accepted-slot audit and failed outcomes alongside the real contiguous CORE
prefix. Do not relabel truncated data as a valid observation bundle.

Distinguish raw artifact-byte SHA-256 from the SCI canonical typed-message
digest. Follow the manifest's declared codec and verifier; browser
JSON.stringify is not the SCI canonicalization algorithm. Offline replay makes
no provider calls. Missing bytes, changed hashes and unsupported versions fail
explicitly. Terminal status/export ownership does not expose blind truth.

**Accessible path:** named download/status actions, text completeness summary
and verifiable manifest identity. Expired access reauthorizes, never redirects
to arbitrary user-controlled storage URLs.

**Producers:** SP-25.c/e, SP-13.d, SP-11.b/c. **Scenarios:** F26–F28.

## Accessibility checklist

These are acceptance checks to exercise in real browsers, not completed audits.
The target is WCAG 2.2 AA. The design emphasizes keyboard access, visible focus,
labels and errors, non-color distinctions, text alternatives, and restrained
status updates. [W3C WCAG reference](https://www.w3.org/WAI/WCAG22/quickref/)


<a id="a11y-01"></a>

- **A11Y-01:** Complete each essential journey with semantic labeled controls,
  logical tab order, visible unobscured focus and no pointer-only action.

<a id="a11y-02"></a>

- **A11Y-02:** Form errors have a summary and field association; focus reaches
  correction; nonsensitive input survives recoverable failures.

<a id="a11y-03"></a>

- **A11Y-03:** Navigation, role/access changes and asynchronous results have a
  predictable focus target; background updates do not move it.

<a id="a11y-04"></a>

- **A11Y-04:** Announce meaningful loading/progress/error/access states without
  reading every frame or leaking secrets.

<a id="a11y-05"></a>

- **A11Y-05:** Essential canvas/chart information is available as text/tables;
  observation, prediction, uncertainty and failure do not rely only on color.

<a id="a11y-06"></a>

- **A11Y-06:** Modal confirmation contains focus, closes with Escape where
  cancellable and returns focus to the trigger or logical successor.
  [W3C dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

<a id="a11y-07"></a>

- **A11Y-07:** Replay supports named play/pause, frame buttons and keyboard
  slider with human-readable timestamps; reduced motion starts with static data.
  [W3C slider pattern](https://www.w3.org/WAI/ARIA/apg/patterns/slider/)

<a id="a11y-08"></a>

- **A11Y-08:** Check zoom/reflow, contrast, target sizes and supported
  screen-reader/browser combinations on the actual implementation.

## Acceptance scenario index

Detailed conditions, expected outcomes and producer references are in the JSON
inventory. A fixture entry names work to execute; its presence is not a passing
integration test.

| ID | Scenario |
| --- | --- |
| F01 | Session bootstrap, private workspace and no memberships |
| F02 | Invitation acceptance and current role |
| F03 | Expired, revoked, replayed or wrong-account invitation |
| F04 | Membership changes and sole-owner protection |
| F05 | Session expiry, revocation and cross-workspace denial |
| F06 | Empty catalog and permitted authoring |
| F07 | Keyboard editing and invalid bounds/topology |
| F08 | Immutable save, uncertain response and stale version |
| F09 | Author/agent separation and blind-suite denial |
| F10 | Start prerequisites and explicit review |
| F11 | Unknown submission and idempotent retry |
| F12 | Invalid/conflicting/quota/unavailable start |
| F13 | Authoritative run progress |
| F14 | Cancellation acceptance and settlement |
| F15 | Cancellation/completion race |
| F16 | Failed/expired run with retained accepted slots |
| F17 | Empty/live purchased-observation timeline |
| F18 | Duplicate, reordered and gapped events |
| F19 | Expired cursor and archive resync failure |
| F20 | Live membership revocation |
| F21 | Provider ambiguity and learned-model visibility |
| F22 | Exact indexed replay and keyboard navigation |
| F23 | Missing/invalid prediction and unavailable uncertainty |
| F24 | Partial data, scoring validity and withheld truth |
| F25 | Incompatible comparisons and failed outcomes |
| F26 | Complete/incomplete private export |
| F27 | Expired/revoked export retrieval |
| F28 | Offline integrity, canonical identities and separate publication |

SP-30.a supplies authenticated browser/SDK/CLI end-to-end evidence after the
listed producers integrate. SP-24.d supplies real accessibility and supported
browser evidence. Public release claims must use those results rather than this
specification or screenshots.
