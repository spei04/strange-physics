#!/usr/bin/env bash
# One fixed cloud operator; live activation requires the combined owner decision.
EXECUTION_ENABLED=false
if [ "$EXECUTION_ENABLED" != true ]; then
  printf '%s\n' 'Disabled pending combined owner/source/lease admission' >&2
  exit 64
fi
set -u
set -C
umask 077
if [ "$#" -ne 10 ]; then
  printf '%s\n' 'Expected fixture, manifest/hash, control root, and three spec/hash pairs' >&2
  exit 64
fi
Q=$1; M=$2; MSHA=$3; C=$4
NORMAL_SPEC=$5; NORMAL_SHA=$6
NONZERO_SPEC=$7; NONZERO_SHA=$8
TIMEOUT_SPEC=$9; TIMEOUT_SHA=${10}

# Inspect pinned inputs and consume authority inside the preparation deadline.
if /usr/bin/timeout --signal=TERM --kill-after=2s 10s /usr/bin/python3 -I -B - "$0" "$@" <<'PY'
import hashlib, importlib.util, json, os, sys, time
from pathlib import Path
self_path, fixture_path, manifest_path, expected, control_path = map(str, sys.argv[1:6])
def raw(path):
    p=Path(path)
    info=p.lstat()
    if not p.is_absolute() or p.resolve()!=p or not p.is_file() or info.st_uid!=os.getuid() or info.st_mode & 0o777 != 0o600 or info.st_nlink!=1:
        raise ValueError("Exact private input required")
    with p.open("rb") as stream: value=stream.read(131073)
    if len(value)>131072: raise ValueError("Input extent")
    return value
def sha(value): return hashlib.sha256(value).hexdigest()
manifest_raw=raw(manifest_path)
if sha(manifest_raw)!=expected: raise ValueError("Manifest digest")
manifest=json.loads(manifest_raw)
owner_ref=manifest["owner"]; owner_raw=raw(owner_ref["path"])
if sha(owner_raw)!=owner_ref["sha256"]: raise ValueError("Owner digest")
owner=json.loads(owner_raw)
if sha(raw(fixture_path))!=owner["fixture_active_sha256"]: raise ValueError("Fixture digest")
operator={"path":str(Path(self_path).resolve()),"sha256":sha(raw(self_path))}
if manifest["operator"]!=operator or owner["operator"]!=operator: raise ValueError("Operator digest")
if manifest["control_root"]!=control_path: raise ValueError("Control root")
spec=importlib.util.spec_from_file_location("fixed_fixture_operator",fixture_path)
if spec is None or spec.loader is None: raise ValueError("Fixture module")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.load(Path(manifest_path),expected)
entries=manifest["fixtures"]
if len(entries)!=3 or len(sys.argv[6:])!=6: raise ValueError("Three fixture pairs")
for entry,path,digest in zip(entries,sys.argv[6::2],sys.argv[7::2],strict=True):
    if entry!={"path":path,"sha256":digest}: raise ValueError("Exact ordered fixture pair")
module.stage_claim(manifest,"operator")
server_ref=manifest["leases"]["server"]; server_raw=raw(server_ref["path"])
if sha(server_raw)!=server_ref["sha256"]: raise ValueError("Pinned server lease")
start=json.loads(server_raw)
boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
possible=Path("/sys/devices/system/cpu/possible").read_text().strip()
now=time.monotonic_ns()
elapsed=(now-start["start_monotonic_ns"])/1e9
if start["closed"] is not False or start["source"]!=manifest["source"] or start["combined_id"]!=manifest["combined_id"]:
    raise ValueError("Open lease binding")
if boot!=start["boot_start"] or possible!="0-3" or start["maximum_cpu_count"]!=4:
    raise ValueError("Server identity or CPU assumption changed")
if not 0<=elapsed<=180 or 2400-elapsed<2170: raise ValueError("Preparation exhausted lease")
print("operator_preflight_admitted",flush=True)
PY
then
  :
else
  printf '%s\n' '{"kind":"preflight_failed","accepted":false,"attempt_consumed":true,"closure":"incomplete"}'
  exit 71
fi

operator_rc=1
# Independent sequential phase timeouts; no nested outer process-group claim.
if /usr/bin/env -u BASH_ENV /bin/bash --noprofile --norc -s -- "$@" <<'BODY'
set -u
set -C
umask 077
Q=$1; M=$2; MSHA=$3; C=$4
NORMAL_SPEC=$5; NORMAL_SHA=$6
NONZERO_SPEC=$7; NONZERO_SHA=$8
TIMEOUT_SPEC=$9; TIMEOUT_SHA=${10}
phase() {
  name=$1; seconds=$2; shift 2
  ( ulimit -f 512 || exit 70
    exec /usr/bin/timeout --signal=TERM --kill-after=5s "${seconds}s" "$@"
  ) >"$C/$name.log" 2>&1
}
qual_rc=1; grid_rc=125; close_rc=1
if phase qualification 175 /usr/bin/env -u BASH_ENV /bin/bash --noprofile --norc -c '
  set -u
  Q=$1; M=$2; MSHA=$3; shift 3
  op() { /usr/bin/python3 -I -B "$Q" "$1" --spec "$2" --sha256 "$3"; }
  while [ "$#" -gt 0 ]; do
    spec=$1; sha=$2; shift 2; stage=0; terminal=0
    if op start "$spec" "$sha" && op ready "$spec" "$sha" && op release "$spec" "$sha"; then stage=1; fi
    if op finish "$spec" "$sha"; then terminal=1; fi
    [ "$stage" -eq 1 ] && [ "$terminal" -eq 1 ] || exit 1
  done
  op barrier "$M" "$MSHA"
' grid-qualification "$Q" "$M" "$MSHA" "$NORMAL_SPEC" "$NORMAL_SHA" "$NONZERO_SPEC" "$NONZERO_SHA" "$TIMEOUT_SPEC" "$TIMEOUT_SHA"; then
  qual_rc=0
else
  qual_rc=$?
fi
if [ "$qual_rc" -eq 0 ]; then
  if phase grid 1735 /usr/bin/python3 -I -B "$Q" dispatch --spec "$M" --sha256 "$MSHA"; then
    grid_rc=0
  else
    grid_rc=$?
  fi
fi
phase_record_rc=0
/usr/bin/timeout --signal=TERM --kill-after=1s 4s /usr/bin/python3 -I -B - "$C" "$M" "$MSHA" "$qual_rc" "$grid_rc" <<'PY'
import hashlib,json,os,sys
from pathlib import Path
root=Path(sys.argv[1]); manifest_raw=Path(sys.argv[2]).read_bytes()
if hashlib.sha256(manifest_raw).hexdigest()!=sys.argv[3]: raise ValueError("Manifest changed")
manifest=json.loads(manifest_raw)
raw=(json.dumps({"combined_id":manifest["combined_id"],"source":manifest["source"],"qualification_exit":int(sys.argv[4]),"grid_exit":int(sys.argv[5]),"accepted":False},sort_keys=True)+"\n").encode()
if len(raw)>16384: raise ValueError("Phase record extent")
fd=os.open(root/"phase-status.json",os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,"wb") as out:
    out.write(raw); out.flush(); os.fsync(out.fileno())
fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
try: os.fsync(fd)
finally: os.close(fd)
PY
phase_record_rc=$?
# Never redirect closeout to a unit file that could grow after its census.
if /usr/bin/timeout --signal=TERM --kill-after=5s 235s \
  /usr/bin/python3 -I -B "$Q" closeout --spec "$M" --sha256 "$MSHA"; then
  close_rc=0
else
  close_rc=$?
fi
# From this point the operator writes only to the captured terminal.
printf 'operator_phase_exits qualification=%s grid=%s phase_record=%s closeout=%s\n' \
  "$qual_rc" "$grid_rc" "$phase_record_rc" "$close_rc"
[ "$qual_rc" -eq 0 ] && [ "$grid_rc" -eq 0 ] && [ "$phase_record_rc" -eq 0 ] && [ "$close_rc" -eq 0 ]
BODY
then
  operator_rc=0
else
  operator_rc=$?
fi
# Observed after the foreground driver has returned; this marker is not its own
# post-exit witness. The trusted tool handback and client observation finish that.
marker_rc=0
/usr/bin/timeout --signal=TERM --kill-after=1s 4s /usr/bin/python3 -I -B - "$M" "$MSHA" "$operator_rc" <<'PY'
import hashlib,json,sys,time
from pathlib import Path
raw=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(raw).hexdigest()!=sys.argv[2]: raise ValueError("Manifest changed")
manifest=json.loads(raw); ref=manifest["leases"]["server"]
start_raw=Path(ref["path"]).read_bytes()
if hashlib.sha256(start_raw).hexdigest()!=ref["sha256"]: raise ValueError("Lease changed")
start=json.loads(start_raw)
boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
possible=Path("/sys/devices/system/cpu/possible").read_text().strip()
now=time.monotonic_ns()
summary=Path(manifest["control_root"])/"combined-closeout.json"
summary_raw=summary.read_bytes() if summary.is_file() else None
summary_sha=hashlib.sha256(summary_raw).hexdigest() if summary_raw is not None else None
summary_value=json.loads(summary_raw) if summary_raw is not None else {}
provisional=summary_value.get("attempt_status")=="provisional_complete"
print(json.dumps({"kind":"server_post_driver_observation","combined_id":start["combined_id"],"source":start["source"],"manifest_sha256":sys.argv[2],"combined_closeout_sha256":summary_sha,"start_monotonic_ns":start["start_monotonic_ns"],"observed_monotonic_ns":now,"boot_start":start["boot_start"],"boot_observed":boot,"maximum_cpu_count":4 if possible=="0-3" else None,"operator_exit":int(sys.argv[3]),"ledger_provisional_complete":provisional,"observed_within_lease":0<=now-start["start_monotonic_ns"]<=2400000000000,"accepted":False,"transport_boundary":"owned_command_handback_shared_transport_retained"},sort_keys=True),flush=True)
raise SystemExit(0 if provisional and boot==start["boot_start"] and possible=="0-3" and 0<=now-start["start_monotonic_ns"]<=2400000000000 else 1)
PY
marker_rc=$?
[ "$operator_rc" -eq 0 ] && [ "$marker_rc" -eq 0 ]
