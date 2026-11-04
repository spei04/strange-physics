# D1 cycle-6 transport failure and closeout status

**Status: validation stopped; the authorized failure closeout is complete.** On 2026-11-03 Pacific, the single approved cycle-6 rebind invocation ended with SSH exit 255 during banner exchange. It returned no remote outer record. No dependent phase, CI, installation or runtime command was dispatched. The source review passed, but this attempt provides no new test or runtime qualification result.

## Original observation and evidence custody

The local transport closed after **45.935 seconds**, with no signal, zero stdout bytes and 89 stderr bytes. Its input pipe reported EPIPE. The original remote exit, elapsed time, execution and usage remain **unknown**. Local connection time is not a remote-duration measurement. Later absence of cycle-6 operational files does not prove zero remote work.

The interrupted turn lost its volatile tool stores. The exact input was recovered from the unchanged 305-row baseline and 27-row append inventory; its 83,395-byte length and SHA-256 match the original sent-input observation. The exact error text was recovered from the retained tool output and matches its original length and digest. This recovery is explicitly recorded, rather than described as a surviving original memory buffer.

Private evidence remains outside disposable checkouts:

| Record | Bytes | SHA-256 |
| --- | ---: | --- |
| repair-cycle6-original-transport-observation-20261104.json | 3,473 | dac39010d9119f2923d317cd2781de59506331541db1552856a59cdbc3aae010 |
| repair-cycle6-recovered-original-input-20261104.json | 83,395 | 926a1ba0b81b9e9362ae147131d6d536a23a26e05be1d18e6e70cd712b8b2270 |
| Original empty stdout | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| Original stderr | 89 | 5cb0c1231d33323ce235f9f008691e9d3289a9f68bba908efbb9e27d3d565890 |
| Final independent source review | 12,146 | e5afa4c64011ac0177294d090589319443a5b66748c9ee9e17b1b5959936321c |

The incident record is an administrative preservation record. It does not replace a metered operational receipt or the retained cycle-5 index. Its recovery provenance and accounting were independently reviewed. One administrative preservation script initially failed Python parsing before executing its body; the corrected script saved both records exclusively with owner-only permissions and verified their hashes. Neither administrative command invoked a validation candidate.

## Closeout defect

The frozen handoff source, SHA-256 8078800d2265cbefad4e75905490d65c3146d6603d625eda9ba3c4e43b29dcc7, accepts an incomplete outer observation but requires its remote elapsed field to be a finite number. It rejects the truthful null duration from this transport failure. It would also label a supplied number as an original remote observation. Substituting zero or the 45.935-second local duration would misstate the evidence.

The independent source review missed this unobserved-duration path. The sole failure handoff was withheld while a narrowly versioned correction was prepared and independently reviewed. That corrected closeout has now completed within the original allowance; the frozen sources, original input and all earlier failed evidence remain unchanged. No seventh cycle or automatic retry is authorized.

## Failure closeout — completed within the original allowance

The approved decision explicitly permits routine pre-invocation source corrections within fixed scopes. The handoff had not been invoked, so its narrow correction used the existing 2 CPU / 6 wall slot without a new allocation or retry. The original dispatcher, transport, deadlines, output bounds and no-retry rules stayed unchanged.

The successor preserves the original 332-row input exactly and separately appends the incident, recovered input, successor source, recipe and review. Its final inventory contained 338 rows. The reader accepts only this pinned initial-rebind failure, records local connection timing separately and emits no fabricated remote-duration charge. The original producer and handoff files remain retained.

The one failure handoff returned zero with complete original streams, no children, known descriptor closure and no handoff failure. Its measured self CPU was 0.557021 seconds, active wall 0.5537898712791502 seconds, and original remote outer duration 0.5772429062053561 seconds. These measurements describe the **closeout only**; the failed rebind's remote duration and usage remain unknown. The full 2/6 closeout charge is retained. Independent review accepted the original observations and exact receipt/index readbacks.

| Closeout evidence | Bytes | SHA-256 |
| --- | ---: | --- |
| Enabled unknown-time handoff source | 50,324 | b7df27dcdf5b5b195464660a55baa2795349315897e583d23756abfbe544ad9b |
| Independent successor source review | 6,131 | 07e88a36a4f259939e24c7694cae58fad14e38bc0545cfb3af6a31075a7a995a |
| repair-cycle6-closeout-original-execution-record-20261104.json | 4,658 | 162ccb508249ee85faa97935099809274d007392d488b89bdb75e158f1fab827 |
| repair-cycle6-closeout-original-input-20261104.json | 84,277 | a3b9ff76d9d23cb31db488692b52d7692c2563ebc5127acd5bc03d2ef9216539 |
| E2-cycle6-handoff-receipt.json | 4,305 | f516541950628b89a852c82571ac2ebaf600d0fceba1a6910e9319212b1e3f52 |
| cycle6-software-index.json | 4,451 | d2d1b1e9de9791dbaa7d9f16659d58a00e741db78dbd24fad35e2ee65b42e899 |

The stopped index preserves unknown original usage, no retry, no new admission and qualified_test_success=false. All final original closeout buffers are saved privately; no reconstruction was needed for this closeout's buffers. Source additions including final evidence total 1,438,717 bytes within the unchanged 2 MiB allowance.

## Accounting and storage

Retain the full new cycle allocation of **225 CPU / 675 active-wall seconds** once, plus the prior **592.445086 / 1538.1534917629324** hold: **817.445086 / 2213.1534917629324** in unresolved retained B accounting. These are reserved charges, not measured remote usage or a proven actual-cost upper bound. Larger genuine observations would still have to be retained without double counting.

E2 now retains **48 CPU / 144 wall seconds**, including its sole original **2 / 6** failure-handoff slot once. All historical failures, unknowns and package ceilings remain intact. The unused control/outcome allowances do not authorize another attempt.

Before invocation, the complete census contained 332 external rows, including all 305 original rows and 1,147,387 bytes of additions. Retained package bytes were 11,633,549; the remaining 1 GiB envelope was 1,062,108,275 bytes. Software and review forecasts fit their unchanged pools. Filesystem availability was 41,021,693,952 bytes. Rewind's active 256 MiB allowance was considered separately; other-owner and transient demand remained unknown. High local host load was observed but is not an established cause of this SSH failure.

After incident preservation, additions were 1,234,255 bytes within the same 2 MiB source allowance. Later correction/review artifacts must also be counted. No storage allowance was reset.

## Assignments and remaining boundary

| Engineer | Work | Status |
| --- | --- | --- |
| Platform | Rebind producer, consumers and source activation | Completed; original attempt failed in transport |
| Research | Seven-case harness and E2 source graph | Source completed; no new runtime result |
| Quality | Source review, actual admission arithmetic and incident evidence | Reviewed; unknown-duration defect acknowledged |
| Lead | Original dispatch, evidence recovery and public checkpoint | Failure recorded; dependent work stopped |
| Closeout engineer / independent reviewer | Minimal versioned unknown-duration correction and actual closeout evidence | Source and final evidence accepted; sole failure handoff completed |

Both cloud checkouts remain clean at the reconciliation point: documentation at 0644a3b7f0a86a8688a55be5ba041a76c2457299 and application/test source at ae0eea284132c4ca67815b29ba4cadfc5a6d2891. Both remain needed; none was removed or duplicated. Private evidence remains outside them. Protected local computer-use work was untouched.

No recovery decision remains for this failure closeout. A further validation attempt requires a separately scoped proposal and approval; none is admitted here. The original downstream CI/install/runtime gates remain unmet; scientific execution and production-readiness claims remain excluded.
