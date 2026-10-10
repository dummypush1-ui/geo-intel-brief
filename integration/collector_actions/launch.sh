#!/bin/bash
# Candidate Actions containment launcher. Root runs fixed setup, never collector.
# Explicit entry. No source/sudo shell content comes from payload or external data.
set -euo pipefail
[[ $# == 1 && $1 == --candidate && $EUID == 0 ]] || exit 2
root=$(pwd -P)
[[ ${SUDO_UID:-} =~ ^[0-9]+$ && ${SUDO_GID:-} =~ ^[0-9]+$ && $SUDO_UID -ne 0 ]]
python=$root/.collector-job-env/bin/python
[[ -x $python && -f $root/integration/collector_actions/entry.py ]]
base=$(mktemp -d /tmp/collector197-actions.XXXXXXXX)
chmod 700 "$base"
cg=/sys/fs/cgroup/geo197-actions-$$
mkdir "$cg"
cleanup() {
 for group in "$cg"/measure "$cg"/run; do
  if [[ -d $group ]]; then
   [[ ! -f $group/cgroup.kill ]] || echo 1 > "$group/cgroup.kill"
   for i in {1..20}; do [[ -z $(cat "$group/cgroup.procs") ]] && break; sleep .1; done
   rmdir "$group" || true
  fi
 done
 rmdir "$cg" || true
 rm -rf -- "$base"
}
trap cleanup EXIT
[[ -r /sys/fs/cgroup/cgroup.controllers ]]
grep -qw memory /sys/fs/cgroup/cgroup.subtree_control
echo +memory > "$cg/cgroup.subtree_control"
for name in measure run; do
 group=$cg/$name; mkdir "$group"
 echo 3221225472 > "$group/memory.max"
 echo 0 > "$group/memory.swap.max"
 echo 1 > "$group/memory.oom.group"
 chmod 755 "$group"
 chmod 644 "$group"/{cgroup.procs,memory.max,memory.swap.max,memory.oom.group}
done
# Secret payload stays root-readable tmp, only bounded plaintext stdin crosses
# into dropped process. Not in argv or stdout; no shell xtrace.
/usr/bin/head -c 8193 > "$base/payload.json"
chmod 600 "$base/payload.json"
/usr/bin/python3 -I -S - "$base/payload.json" <<'PY'
import pathlib,json,sys
p=pathlib.Path(sys.argv[1]);assert p.stat().st_size<=8192
x=json.loads(p.read_text());assert x['mode']in ('measure','collect','status')
PY
launch() {
 group=$1
 /usr/bin/timeout --kill-after=2s 90s /bin/bash -c '
  echo $$ > "$1/cgroup.procs"; shift
  exec /usr/bin/setpriv --reuid="$1" --regid="$2" --clear-groups --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs /usr/bin/env -i LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC "$3" -I "$4"
 ' guarded "$group" "$SUDO_UID" "$SUDO_GID" "$python" "$root/integration/collector_actions/entry.py"
}
mode=$(/usr/bin/python3 -I -S -c 'import json,sys;print(json.load(open(sys.argv[1]))["mode"])' "$base/payload.json")
attempt=$(/usr/bin/python3 -I -S -c 'import json,sys;print(json.load(open(sys.argv[1]))["run_attempt"])' "$base/payload.json")
if [[ $mode == status || $attempt != 1 ]]; then
 launch "$cg/run" < "$base/payload.json"
 exit 0
fi
# Fixed diagnostic independently checks actual aggregate OOM-group kill.
/usr/bin/env -i PATH=/usr/bin:/bin SUDO_UID="$SUDO_UID" SUDO_GID="$SUDO_GID" /bin/bash "$root/integration/collector197_job_diagnostic.sh" --diagnose > "$base/adversary.log"
mode=$(/usr/bin/python3 -I -S -c 'import json,sys;print(json.load(open(sys.argv[1]))["mode"])' "$base/payload.json")
/usr/bin/python3 -I -S - "$base/payload.json" "$base/measure.json" <<'PY'
import json,pathlib,sys
x=json.loads(pathlib.Path(sys.argv[1]).read_text());x['mode']='measure'
pathlib.Path(sys.argv[2]).write_text(json.dumps(x));pathlib.Path(sys.argv[2]).chmod(0o600)
PY
launch "$cg/measure" < "$base/measure.json" > "$base/measured-result.json"
[[ $(wc -c < "$base/measured-result.json") -le 8192 ]]
/usr/bin/python3 -I -S "$root/integration/collector_actions/receipt.py" "$base/payload.json" "$base/measured-result.json" "$cg/measure" "$base/adversary.log" "$base/qualification.json"
printf 'measurement_memory_peak_bytes=';cat "$cg/measure/memory.peak"
cat "$cg/measure/memory.events"
if [[ $mode == measure ]]; then
 printf 'qualification_no_write_complete=true\n'
 exit 0
fi
launch "$cg/run" 3< "$base/qualification.json" < "$base/payload.json"
printf 'run_memory_peak_bytes=';cat "$cg/run/memory.peak"
cat "$cg/run/memory.events"
