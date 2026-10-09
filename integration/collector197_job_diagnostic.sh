#!/bin/bash
# Owner-pasted diagnostic workflow ONLY. Explicit privileged fixed cgroup setup.
# Never source this. No Atlas credentials, repo settings, live collector or network.
set -euo pipefail
[[ $# == 1 && $1 == --diagnose && $EUID == 0 ]] || exit 2
root=$(pwd -P)
[[ -f $root/collector197_job_cli.py && -f $root/integration/collector197_job_adversary.py ]]
[[ -r /sys/fs/cgroup/cgroup.controllers ]]
grep -qw memory /sys/fs/cgroup/cgroup.controllers
[[ ${SUDO_UID:-} =~ ^[0-9]+$ && ${SUDO_GID:-} =~ ^[0-9]+$ && $SUDO_UID -ne 0 ]]
python=$root/.collector-job-env/bin/python
[[ -x $python ]]
base=/sys/fs/cgroup/geo197e-diagnostic-$$
mkdir "$base"
cleanup() {
 for group in "$base"/facts "$base"/below "$base"/overflow; do
  if [[ -d $group ]]; then
   [[ ! -f $group/cgroup.kill ]] || echo 1 > "$group/cgroup.kill"
   rmdir "$group" || true
  fi
 done
 rmdir "$base" || true
}
trap cleanup EXIT
# This changes only disposable fixture-owned subtree. If the parent lacks
# controller delegation, fail unsupported. Never weaken a running parent limit.
grep -qw memory /sys/fs/cgroup/cgroup.subtree_control
echo +memory > "$base/cgroup.subtree_control"
for name in facts below overflow; do
 group=$base/$name; mkdir "$group"
 echo 3221225472 > "$group/memory.max"
 echo 0 > "$group/memory.swap.max"
 echo 1 > "$group/memory.oom.group"
 chmod 755 "$group"
 chmod 644 "$group/cgroup.procs" "$group/memory.max" "$group/memory.swap.max" "$group/memory.oom.group"
done
# Enter before dropping all privileges; Python inherits group and can't move out.
launch() {
 group=$1; shift
 /usr/bin/timeout --kill-after=2s 35s /bin/bash -c '
  echo $$ > "$1/cgroup.procs"; shift
  exec /usr/bin/setpriv --reuid="$1" --regid="$2" --clear-groups --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs /usr/bin/env -i LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC "$3" "$4" "$5"
 ' guarded "$group" "$SUDO_UID" "$SUDO_GID" "$python" "$@"
}
launch "$base/facts" "$root/collector197_job_cli.py" --diagnose
launch "$base/below" "$root/integration/collector197_job_adversary.py" --below
[[ $(awk '$1=="oom_kill"{print $2}' "$base/below/memory.events") == 0 ]]
set +e
launch "$base/overflow" "$root/integration/collector197_job_adversary.py" --overflow
status=$?
set -e
[[ $status != 0 && $status != 124 ]]
[[ $(awk '$1=="oom_kill"{print $2}' "$base/overflow/memory.events") -gt 0 ]]
[[ $(awk '$1=="oom_group_kill"{print $2}' "$base/overflow/memory.events") -gt 0 ]]
[[ -z $(cat "$base/overflow/cgroup.procs") ]]
printf 'aggregate_fixture_oom_group_kill_verified=true\n'
for name in below overflow; do
 printf '%s_memory_peak_bytes=' "$name";cat "$base/$name/memory.peak"
 cat "$base/$name/memory.events"
done
# Synthetic test is NOT a provider or activation proof. Real workload peak and
# overhead remain separate before enabled production; only diagnostics ran.
