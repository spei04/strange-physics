# RA-01 source, license and reproduction admission

Audited **2026-10-21**; review due **2026-11-20**. This is the full RA-01
source-admission unit for the methods in the research decision record. It
executes no external method, installs no dependency, contacts no provider,
downloads no restricted data/model weights, and runs no native comparison.

The result is **GO for self-authored native implementation**, with the existing
I1 implementation as its licensed, locked foundation. This is not permission
to run an unfinished producer or skip its acceptance gates. The first
36-episode study still needs accepted candidate/predictor provenance,
finite-grid inference and independent checks, calibration and discrepancy/prior
sensitivity, the fixed action bank/selectors, independent scoring, and the
final frozen manifest/cost/failure accounting. Its run recipe and future
configuration hashes remain unresolved until those artifacts exist. Later
Laplace implementation and the transferred approximation-versus-grid audit
remain separate retained work.

## Records and validation

[source-admission.json](source-admission.json) records all eight required SOURCE
fields for each method: publication/version, repository commit, license grant,
runtime/dependencies, recipe, expected artifacts, reproduction status, and
dated review. It also records the decision, available code/data/weights, and
information-access boundary. Publication versions, source commits, dependency
manifests and runtime identities are different things.

[source-admission.schema.json](source-admission.schema.json) describes the
strict shapes. The script additionally checks reference ownership, dates,
complete method coverage, license evidence and admission implications:

~~~sh
.venv/bin/python scripts/research_sources.py --check-schema
.venv/bin/python scripts/research_sources.py --method mda
.venv/bin/python -m pytest -p no:cacheprovider tests/test_research_sources.py
~~~

These commands are offline. The script never executes recipe argv, fetches
a URL, imports an external source, or resolves dependencies. Its fixed 512 KiB,
depth-16 and 50,000-node envelope rejects excess before typed decoding;
the shared strict loader rejects duplicate keys, invalid UTF-8 and nonfinite
numbers. JSON Schema checks shapes; cross-record joins require the validator.
The output `canonical_manifest_sha256` hashes the complete validated model
serialized as JSON with sorted keys, compact separators, finite numbers and
ASCII escaping. It is a typed canonical identity, distinct from the SHA-256 of
the inspected manifest file bytes. Permitted whitespace changes do not change it.
Validation does not prove that a supplied license exists or a claimed hash
came from its publisher: the dated primary-source review and retained raw
evidence supply that trust boundary. The exact historical uv.lock identity and
complete observed Linux runtime notice coverage were independently reviewed against the
retained files; metadata shape and reference checks do not attest an environment
or prove that coherently edited claims remain true. RA-02 and the final run
manifest must bind the actual post-integration source and lock before execution.

Every file evidence entry joins a repository and its exact commit. Its raw
SHA-256 and byte count identify the inspected file. Append
/blob/{commit}/{path} to the repository URL to locate it. Full license text
was read, rather than inferring permission from a badge, paper license or
GitHub classifier. The private evidence retains fetched text and lookup
failures; public records contain no credentials or private run data.

## Admission decisions

| Method | Current source/license result | Native execution admission |
| --- | --- | --- |
| Self-authored spring | Existing I1 at 33ddfbf, MIT; exact uv.lock and runtime notices | Implementation GO only; future run recipe unresolved |
| NewtonBench | 912a4ba, MIT source and benchmark modules | Deferred; provider runner/adapter not admitted |
| MDA solver | Checked candidate location returned 404; no official solver revision verified | No-go reuse/reproduction; paper inspiration only |
| LLM-AutoSciLab | New 467fa184 MIT grant, third-party notices; truth-conditioned loop unchanged | Deferred; licensing does not repair leakage |
| LLM-ACES | 34ceeb9 README MIT claim, no license grant | No-go reuse pending actual grant |
| PySR + SymbolicRegression.jl | 72a9ab9 +83ca176, Apache-2.0 | Deferred; full Python/Julia lock/notices and adapter required |
| PySINDy weak/SBR | c4421fc actual MIT despite metadata NOASSERTION | Deferred; optional stack/error model need review |
| ZSINDy | c31039d, no repository grant | No-go reuse; paper access does not license code |
| NeuronBench | c354622, MIT benchmark and baseline | Deferred; not MDA solver |
| GlucoseBench | 6bb0ff6, MIT wrapper and simglucose notice/provenance | Deferred; persistence is not MDA |

Deferred does not mean approved to install or execute. Missing external source
or unresolved licensing does not block independent native implementation. No
external method is labelled reproduced; author scores are not our results.

## Dated source and scientific boundaries

[MDA v5](https://arxiv.org/abs/2608.09696v5) was first submitted 2026-08-10 and
revised 2026-09-27. Appendix A.9/equation 59 describe a noise-whitened weighted
model-disagreement surrogate, not exact mutual information. All three native
selectors must share the same finite-grid candidate representation and
inference engine. A renamed equivalent disagreement score is not an
independent advance. The previously recorded
[candidate solver location](https://github.com/murphyk/MDA) returned 404 on the
audit date. The paper links the two benchmark repositories; an official
full-solver link/revision was not verified. No reason for the 404 or universal
absence claim is inferred. Benchmarks do not establish full solver availability.

[AutoSciLab v1](https://arxiv.org/abs/2605.24043v1),2026-05-21, combines LLM
hypotheses, experiment selection and refinement. The official
[351aae73→467fa184 comparison](https://github.com/scientific-discovery/LLM-AutoSciLab/compare/351aae73e6c6c279e67943b77143b0f118d1e289...467fa184ba537d26b2228ee3f3a8c052d9bfca58)
is one 2026-10-20 commit adding LICENSE/THIRD_PARTY_LICENSES and editing README,
with no method-code change. The earlier no-license observation is historical.
The [new MIT grant](https://github.com/scientific-discovery/LLM-AutoSciLab/blob/467fa184ba537d26b2228ee3f3a8c052d9bfca58/LICENSE)
is verified. Third-party notices list permissive components alongside
GPL-2.0-or-later GENIE3/GIES and separately governed hosted models; that is not
blanket approval of every dependency/data/model path.

The pinned [discovery loop](https://github.com/scientific-discovery/LLM-AutoSciLab/blob/467fa184ba537d26b2228ee3f3a8c052d9bfca58/autoscilab/loop/discovery.py)
calls evaluate_law for intermediate and final candidate selection, including
lines 1928/1971/2182. Its
[memory](https://github.com/scientific-discovery/LLM-AutoSciLab/blob/467fa184ba537d26b2228ee3f3a8c052d9bfca58/autoscilab/llm/memory.py)
exposes GT_RMSLE at 384/401. This violates our sealed-evaluator design.
Removing those paths creates an adaptation, not a faithful reproduction.
Appendix C also uses an LLM symbolic judge, unlike our independent numeric
scorer. Static inspection does not establish a safe flag combination.

[ACES v1](https://arxiv.org/abs/2606.25039v1),2026-06-23, combines operator
guidance, symbolic regression and active initial conditions. Section 3.1
reports one run per system, held-out initial conditions and longer horizons;
it does not establish replicated uncertainty or within-run unannounced
law-change adaptation. The
[pinned README](https://github.com/scientific-discovery/LLM-ACES/blob/34ceeb99f57fb679763ed3ec3fb27b5115d03a18/README.md)
claims MIT and links a missing LICENSE; its placeholder clone URL is not the
official identity. The complete tree and requirements/environment files were
read. A badge or another package's license cannot repair the missing grant.

[NewtonBench v3](https://arxiv.org/abs/2510.07172v3),2026-02-24
(first 2025-10-08), describes 324 tasks/12 domains. Its
[official source](https://github.com/HKUST-KnowComp/NewtonBench/tree/912a4ba5f4356ddd06acc16e44460ca30be4abc2)
contains interactive modules and provider runners. Task-level law variants are
not evidence for our change-adaptation protocol. Lower-bound requirements
and author result tables are not a fully pinned, executed reproduction.

[PySR v3 paper](https://arxiv.org/abs/2305.01582v3),2023-05-05
(first 2023-05-02), accompanies the separate Python/Julia projects. Audited
sources are version 2.7.2, but
[juliapkg.json](https://github.com/astroautomata/PySR/blob/72a9ab982e72eb1c80a063b8fcc4b551daf9660e/pysr/juliapkg.json)
and Project.toml ranges are not a resolved Julia manifest. Future offline use
must pin Julia runtime/artifacts and preserve Apache notices; implicit
network bootstrap is excluded. Evolutionary fitting alone is not calibrated
posterior evidence.

[PySINDy's paper](https://joss.theoj.org/papers/10.21105/joss.02104) was published
2020-05-18. Its [weak/integral documentation](https://pysindy.readthedocs.io/en/stable/examples/12_weakform_SINDy_examples/example.html)
supports avoiding noisy pointwise derivatives, while quadrature and boundary
errors still need checking. Actual MIT text includes sparsereg and PySINDy
notices. The pinned [SBR implementation](https://github.com/dynamicslab/pysindy/blob/c4421fcec275c8f4cc5c1e93bebb961b212067ae/pysindy/optimizers/sbr.py)
explicitly uses derivative residuals, unlike the state likelihood in
[UQ-SINDy](https://arxiv.org/abs/2107.02107v1).
Do not label that implementation a faithful state-space reproduction.
Optional JAX/NumPyro or Gurobi paths are not currently admitted.

[ZSINDy's article](https://doi.org/10.1103/4d98-tdlp) was published 2025-08-21;
its [repository](https://github.com/josephbakarji/zsindy/tree/c31039d826039e62fdf4cbcf71b8423bb1282a54)
is a 2024 snapshot without a license file or full replay lock. Article CC-BY
does not grant software permission. Conditional linear-library posterior
calculations do not establish arbitrary nonlinear-model evidence.

[NeuronBench](https://github.com/murphyk/neuronbench/blob/c354622458c460b419cab821d482c879f0578377/README.md)
explicitly describes a benchmark, not a solver. Its diagnostic/truth helpers
are not learner capabilities; the README's world.discriminator() example must
not enter acquisition.
[GlucoseBench](https://github.com/murphyk/glucosebench/blob/6bb0ff6f44513e1e816ac3f0827531a366e8d7a0/README.md)
includes persistence, fixed protocols and vendored simglucose. NOTICE, MIT
text and PROVENANCE pin upstream 2e897f10f333c76ad383e44a5f98b2586e4aa9ac.
Its Python 3.11 constraints pin NumPy/SciPy/pandas, not all test/tool artifacts.
It supplies within-patient forecasting, not clinical validation or MDA's
selected histories.

## Recipes, dependencies and retained failures

Each available method has explicit argv, inputs, prerequisites and expected
outputs in the manifest. These are **unexecuted instructions**, not execution
permissions or verified results. Deferred recipes are upstream entrypoints
or clearly labelled API/import smokes. A smoke is never called a whole-paper,
weak-form or Bayesian reproduction. MDA has an unavailable recipe instead
of a fabricated command.

The admitted native foundation has a real test recipe using the existing
pinned environment and actual repository files. It validates existing I1 only.
The [I1 CLI sequence](../LOCAL_SCIENTIFIC_WORKFLOW.md) exists but was not rerun
as an RA-01 study. Future producer/run commands belong to their own reviewed
work; no configuration hash or expected score is guessed.

The six transitive runtime distributions are pinned in unchanged uv.lock.
The 22 actual distributed license/notice files are indexed. NumPy includes
component notices and runtime exceptions, so one BSD label is insufficient
for the complete binary distribution. Preserve complete distributed texts
on later redistribution. Existing development/security tools remain in the
same lock. This audit installs nothing and redistributes no binaries,
datasets or weights.

Missing grants, unavailable URLs, unresolved locks, unexecuted recipes and
evaluator contamination remain distinct outcomes. Reconsideration requires
new dated evidence/review. Source availability does not silently revise this
manifest. RA-01 completion certifies no future numerical accuracy, simulator
fidelity, isolation, provider replay, study power or population generalization.

The native lock and 22 notices describe the observed Linux/CPython 3.12 runtime
at the historical baseline, not every platform or any future environment.
A separately identified CI-only certifi lock repair is being integrated by
the lead; this audit does not silently replace its original lock digest.
The eventual study must pin the actual post-integration source and lock, and
recheck notices for any changed selected runtime distributions. Historical
source admission is not an environment attestation for that future run.
