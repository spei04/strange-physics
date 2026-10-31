# D1 runtime record materialization

This recipe uses the existing TrustedInstallation and d1-protected-capture-v1
formats. The callable utility in scripts/d1_runtime_inventory.py performs
bounded file inspection and record construction. It contains no installer,
network client, process launcher, acceptance switch or scientific import.

The exact reviewed source must first reach protected main through normal
reviewed integration and pass that main revision's candidate workflow. Retain
the resulting commit M even when its tree equals an earlier feature tree.
Independently verify the actual run/attempt, branch protection, artifact digest,
four-file bundle, checksums, source/lock provenance and package bytes using the
existing delivery policy. Never relabel the old main artifact. Generating JSON
does not establish candidate acceptance, custody or production readiness.

## Installation prerequisite

Use one fresh owned cloud runtime outside disposable checkouts, private
ancestors, a restrictive umask and the existing approved pinned uv tool. Do not
repair or chmod the shared engineering environment. Prefer uv's Linux layout:
bin/python, lib/python3.12/site-packages, version_info in pyvenv.cfg and disabled
system site packages. Each mutable installation file must be independently
owned; no shared mutable environment or hard-link installation.

The candidate uses uv 0.13.4. Do not silently replace the separately pinned
cloud tool or assume cross-version export equivalence. Regenerate the exact
reviewed runtime requirements export and compare its complete byte hash with
runtime_requirements_sha256 in the actual provenance before installation.
Header command text is included. Mismatch stops preparation; do not normalize
headers, change provenance or install another tool implicitly. This change
does not alter workflow/artifact policy. If exact regeneration is impossible,
review the smallest candidate-artifact amendment before integration.

After that join, the one admitted preparation may install hashed runtime-only
dependencies and the exact candidate wheel offline without dependency
resolution. Preserve commands, tool identities, downloads, partial failures and
outputs within the whole-path envelope.

## Observe the real runtime

CaptureSpec.interpreter and plan.controller_interpreter identify the resolved
controller executable, normally /usr/bin/python3.12. The distinct target in
plan.interpreter is exactly <venv>/bin/python. The actual controller source is
scripts/d1_bootstrap_control.py and the target source is tests/d1_bootstrap.py.

Inspect startup files before running a benign target observation. One frozen,
bounded invocation of the target with -I -B may collect only standard-library
facts: sys.version_info[:3], sys.prefix, sys.executable, sys.path,
sys.builtin_module_names, _imp._frozen_module_names(), sysconfig's stdlib/purelib
paths and current module origins. Its script/argv/output and process accounting
must be frozen before execution. Reject project/D1 or apport_python_hook
imports; do not add checkout src/tests to lookup. Missing observation APIs or
unknown origins fail rather than becoming guessed fields.

Dependency membership is a bounded no-follow census of every actual
site-packages file, including distribution metadata and extension files.
It is not an imported-module list or a requested-dependency list. Package bytes
must equal the exact wheel and reviewed checkout. The materializer derives the
existing engine digest from literal package/registry metadata, observed Python
version, installed NumPy/Pydantic metadata and ordered source bytes without
importing laws. A metadata-only regression compares the existing implementation.

## Native and deferred closure

Enumerate ELF files by their magic bytes in the inventoried interpreter,
complete stdlib and installed extensions. Never execute these files or use
ldd. Use the existing pinned readelf once per distinct file:

    /usr/bin/readelf --file-header --program-headers --dynamic --wide <exact-file>

Inspect architecture, PT_INTERP, DT_NEEDED, DT_RPATH and DT_RUNPATH. Retain one
bounded loader-cache listing from the existing ldconfig -p, its tool identity,
the /etc/ld.so.cache hash and relevant loader configuration. Resolve every
needed soname recursively under the observed supported loader search order.
Expand only inspected literal $ORIGIN paths against the ELF's directory.
Reject empty/relative search directories, unknown tokens, architecture
mismatch, ambiguity or unresolved dependencies. Deduplicate canonical files;
record every literal symlink hop, owner/mode and final regular-file hash.
Recheck this external evidence before and after capture. Do not recursively
inventory unrelated library directories.

Prospective limits: 256 distinct ELF files, 64 dependency names per file,
64 KiB per readelf output, 1 MiB loader-cache listing, plus the existing
512 MiB/32,768-entry protected inventory limits. These are stop ceilings, not
a measured fit claim or permission to run the commands now. Static ELF work
does not discover arbitrary dlopen: review pinned extension startup/deferred
loading paths, including NumPy's bundled libraries. Any unresolved dynamic
edge blocks actual admission. Supply the resulting reviewed regular-file
closure to materialize_plan; an arbitrary nonempty list is not proof.

The service inherits user-manager environment, while the target clears its
environment. Recheck the actual controller environment and one successful,
bounded systemctl --user show-environment read immediately before admission.
Process values only in memory; never print or retain them. Reject LD_* and
PYTHON* names plus MALLOC_CONF, GLIBC_TUNABLES, GCONV_PATH and LOCPATH; retain only
checked names, presence results and command status. Failure to read is unknown.
Do not change shared manager state or the GRID Systemd adapter. Preliminary
clean observations must be repeated at the actual boundary.

## Reviewed Linux aliases and absence

Only explicit interpreter links and these runtime aliases are supported:

| Alias | Literal target |
| --- | --- |
| <venv>/lib64 | lib |
| <stdlib>/_sysconfigdata__linux_x86_64-linux-gnu.py | _sysconfigdata__x86_64-linux-gnu.py |
| <stdlib>/sitecustomize.py | /etc/python3.12/sitecustomize.py |
| /usr/lib/python3.12/config-3.12-x86_64-linux-gnu/libpython3.12.so | ../../x86_64-linux-gnu/libpython3.12.so.1 |
| /usr/lib/x86_64-linux-gnu/libpython3.12.so.1 | libpython3.12.so.1.0 |

Literal targets, owners and target types must match. Protected target files are
hashed and directory targets are closed; deduplicated targets are visited once.
The libpython build alias has an exact absolute source path: moving stdlib
cannot reinterpret its relative target. The observed final library is root-owned
0644, 9,061,000 bytes, SHA256
1021f236227334ded6d1bbbc4bb6f5d933f793d8397c969896cfbdf03ce96223.
Future acceptance requires the actual protected-plan hash.

The sysconfig target is 49,505 bytes, SHA256
ee5bb5493fa4575f7788e1b0e8a067b9c463f9705dcb36f5eb571d1c0812ea82:
one literal assignment, no imports/calls. Ubuntu sitecustomize is 155 bytes,
SHA256 43d81125d92376b1a69d53a71126a041cc9a18d8080e92dea0a2ae23be138b1e.
It conditionally imports apport_python_hook and calls its installer if found.
The supported profile rejects that dependency's package/source/bytecode/extension
candidates throughout startup roots, including lib-dynload, and builtin/frozen
or already-loaded occurrences. Other customization remains rejected. Child
source-alias recognition requires the exact module name, ordinary loader,
literal alias and pinned canonical target.

An absent /usr/lib/python312.zip requires no-follow ENOENT and protected
ancestor/parent identity checks. It does not require recursively closing
unrelated /usr/lib siblings. Dangling links, permission errors and changed
parent identity fail. These observations do not prevent hostile same-UID
writes between checks; the accepted exclusive-custody interval remains external.

## Materialization order

1. Verify candidate acceptance and actual M/checkout/lock joins independently.
   Use the existing archive checks before invoking the utility.
2. Call materialize_installation with actual checkout/site, resolved target
   executable, observed Python version, M, original wheel/provenance paths and
   provenance digest, and the exact hash-matching requirements file.
3. Call write_record once for installation.json. Its existing
   accepted_release_candidate value describes the independently verified premise;
   construction is not acceptance.
4. Assemble the existing launch binding fields from the real startup observation
   and fixed routes. Include both reviewed virtualenv hook files when present,
   and the exact sitecustomize alias/target when present. Supply the independently
   reviewed native/deferred regular files.
5. materialize_plan collects stdlib/venv membership, all fixed helper/native
   source joins, controller inputs, lock/archive/provenance and installation
   record, then invokes the existing preflight validator. Write exclusively;
   freeze the digest; have Lead/Quality inspect the actual records and external
   custody/acceptance evidence before capture.

No new record schema or accepted marker is produced. The launch plan is outside
its own input inventory; installation.json is written first and subsequently
pinned, avoiding a hash cycle. Existing source-disabled activation and all
scientific gates remain unchanged.

## Bounds and validation status

Existing ceilings remain: 64 MiB per protected file, 512 MiB payload per full
inventory, 32,768 entries, 10,000 dependency entries and 4 MiB per record.
The collector bounds queue/scandir work and uses no-follow reads. Installation
construction additionally reads the bounded wheel/provenance/export,
package/source bytes, metadata and engine inputs. Plan construction includes
one inventory read followed by the existing validator's full read; capture
validation passes are additional. Retained bytes are not read-volume or memory
measurements; parsing, copies and loader work still count.

Preparation, downloads, installation, inspections, subprocesses, failures,
records/logs and final closeout all belong to one prospective whole-path
engineering envelope. Existing historical charges and unknowns are unchanged.
Source authoring/static review alone does not qualify protected startup,
runtime instrumentation, owned descendants or any D1 scientific execution.
