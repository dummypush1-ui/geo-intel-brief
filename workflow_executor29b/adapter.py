"""29b1 Stage A plan only. Hosted execution NOT RUN; items 27/28/29 OPEN."""
import ctypes
import hashlib
import json
import os
import pathlib
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCOPE = '29b1 Stage A discovery only; items 27/28/29 OPEN'
IMAGE = 'ubuntu@sha256:f610ab94648195aa356059f5b41d6085c9d4d903c072430cdd1af7bdb646106b'
NAME = 'reviewed-stage-a-29b1'
EVIDENCE = ROOT / 'stage-a-evidence'
WORK = ROOT / 'stage-a-reviewed-inputs'
CAP = 1048576
TOTAL_CAP = 4194304
BAD = re.compile(r'(?i)(github_pat_|gh[pousr]_[a-z0-9]|mongodb(?:\+srv)?://|bearer\s|authorization:|-----BEGIN .*PRIVATE KEY|(?:token|password|secret)\s*[=:])')

class Stop(ValueError):
    pass


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe_json(data):
    raw = json.dumps(data, indent=2, sort_keys=True) + '\n'
    if BAD.search(raw) or len(raw.encode()) > TOTAL_CAP:
        raise Stop('receipt redaction or size check failed')
    return raw


def receipt(state='NOT RUN', reason='technical gate OFF', **extra):
    return dict(scope=SCOPE, state=state, reason=reason,
                hosted_execution='NOT RUN', install_permitted=False,
                stage_b='REFUSED', runtime_ready=False, **extra)


def parse_plan(text, expected, expected_base):
    """Strict apt simulation parse, no fixture plan promoted to target evidence."""
    if not text or len(text.encode()) > CAP or text.count('PLAN_BEGIN\n') != 1 or text.count('PLAN_END\n') != 1:
        raise Stop('zero-byte, malformed or oversized plan')
    if BAD.search(text):
        raise Stop('plan redaction check failed')
    tools = [x for x in text.splitlines() if x.startswith('TOOL\t')]
    if tools != ['TOOL\tapt\t2.8.3']:
        raise Stop('observed apt differs from 2.8.3 anchor')
    base = {}
    for line in text.splitlines():
        if line.startswith('BASE\t'):
            parts = line.split('\t')
            if len(parts) != 5:
                raise Stop('base row shape')
            _, n, v, arch, status = parts
            if status != 'installed' or n in base or not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*', n) or arch not in ('amd64', 'all'):
                raise Stop('base identity/status/architecture')
            base[n] = (v, arch)
    if base != expected_base:
        raise Stop('actual base installed set differs from reviewed 92-pair anchor')
    pockets = {}
    for line in text.splitlines():
        if line.startswith('POCKET\t'):
            _, suite, date = line.split('\t')
            if suite in pockets or suite not in ('noble', 'noble-updates', 'noble-security') or not date:
                raise Stop('pocket date shape')
            pockets[suite] = date
    if len(pockets) != 3:
        raise Stop('missing pocket dates')
    plan = text.split('PLAN_BEGIN\n')[1].split('PLAN_END\n')[0]
    actual = dict(base)
    changed = []
    for line in plan.splitlines():
        if line.startswith('Remv '):
            raise Stop('package removal refused')
        if line.startswith('Inst '):
            m = re.fullmatch(r'Inst ([a-z0-9][a-z0-9+.-]*)(?::(amd64))?(?: \[([^\]]+)\])? \(([^\s()]+) [^\r\n]* \[(amd64|all)\]\)', line)
            if not m:
                raise Stop('unparsed Inst row')
            name, qualifier, old, version, arch = m.groups()
            if name in changed or name not in expected or (version, arch) != expected[name]:
                raise Stop('added, changed or unreviewed package identity')
            if qualifier and qualifier != arch:
                raise Stop('architecture qualifier drift')
            if old is not None and (name not in base or base[name][0] != old):
                raise Stop('old package version mismatch')
            actual[name] = (version, arch)
            changed.append(name)
        elif line.startswith('Conf '):
            if not re.fullmatch(r'Conf [a-z0-9][a-z0-9+.-]*(?::amd64)? \([^\r\n]+\)', line):
                raise Stop('unparsed Conf row')
        elif line.startswith(('E:', 'W:')):
            raise Stop('apt plan diagnostic')
    if len(changed) != 54 or actual != expected:
        raise Stop('entire proposed post-set differs from reviewed 146-pair anchor')
    return {'outcome': 'MATCH', 'install_permitted': False,
            'base_packages': len(base), 'planned_changes': len(changed),
            'post_packages': [{'package': n, 'version': v, 'architecture': a} for n, (v, a) in sorted(actual.items())],
            'pocket_dates': pockets, 'apt_version': '2.8.3'}


def commands():
    """Only fixed argv. Paths resolved from reviewed code, never dispatch inputs."""
    return {
        'info': ['docker', 'info', '--format', '{{json .}}'],
        'pull': ['docker', 'pull', '--platform', 'linux/amd64', IMAGE],
        'run': ['docker', 'run', '--name', NAME, '--platform', 'linux/amd64',
                '--pull', 'never', '--network', 'bridge', '--read-only',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--pids-limit', '64', '--memory', '768m', '--cpus', '1',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=96m',
                '--tmpfs', '/etc/apt:rw,nosuid,nodev,size=8m',
                '--tmpfs', '/var/lib/apt/lists:rw,nosuid,nodev,size=256m',
                '--tmpfs', '/var/cache/apt:rw,nosuid,nodev,size=8m',
                '--tmpfs', '/bootstrap-ca:rw,nosuid,nodev,size=4m',
                '--tmpfs', '/usr/share/keyrings:rw,nosuid,nodev,size=2m',
                '--mount', 'type=bind,src=' + str(WORK) + ',dst=/reviewed,readonly',
                IMAGE, '/bin/sh', '/reviewed/discover.sh'],
        'rm': ['docker', 'rm', '--force', '--volumes', NAME],
        'inspect': ['docker', 'container', 'inspect', NAME],
    }


def execute_reviewed(kind, *, timeout=120, cap=CAP, _test_argv=None):
    """Single subprocess entry. Test-only fixed fixture commands require explicit injection."""
    if kind not in commands():
        raise Stop('unknown process kind')
    argv = commands()[kind] if _test_argv is None else _test_argv
    # Injection is a private unit-test seam, absent from env/CLI dispatch.
    # Adopt only our descendants, then wait only the new process group.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise Stop('process descendant subreaper unavailable')
    started = time.monotonic()
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True, env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'})
    sel = selectors.DefaultSelector()
    for stream in (p.stdout, p.stderr):
        os.set_blocking(stream.fileno(), False)
        sel.register(stream, selectors.EVENT_READ)
    outputs = {p.stdout: bytearray(), p.stderr: bytearray()}
    total = 0
    stop_reason = None
    killed = False
    try:
        while sel.get_map():
            if time.monotonic() - started >= timeout:
                stop_reason = 'wall timeout'
                break
            for key, _ in sel.select(min(0.05, max(0, timeout - (time.monotonic() - started)))):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    sel.unregister(key.fileobj)
                    continue
                keep = data[:max(0, cap - total)]
                outputs[key.fileobj].extend(keep)
                total += len(keep)
                if len(keep) < len(data):
                    stop_reason = 'output cap exceeded; retained prefix truncated'
                    break
            if stop_reason:
                break
        if stop_reason:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            time.sleep(0.05)
            # Kill whole group even if leader already exited; children may hold pipes.
            try:
                os.killpg(p.pid, signal.SIGKILL)
                killed = True
            except ProcessLookupError:
                pass
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            stop_reason = 'leader wait timeout'
            os.killpg(p.pid, signal.SIGKILL)
            killed = True
            p.wait(timeout=5)
    finally:
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
                killed = True
            except ProcessLookupError:
                pass
            p.wait(timeout=5)
        sel.close()
        p.stdout.close()
        p.stderr.close()
    descendant_count = 0
    end = time.monotonic() + 2
    while True:
        try:
            child, status = os.waitpid(-p.pid, os.WNOHANG)
        except ChildProcessError:
            break
        if child:
            descendant_count += 1
        elif time.monotonic() >= end:
            stop_reason = stop_reason or 'descendant reap timeout'
            break
        else:
            time.sleep(0.01)
    try:
        os.killpg(p.pid, 0)
        group_absent = False
        stop_reason = stop_reason or 'process group remains'
    except ProcessLookupError:
        group_absent = True
    return {'exit_code': p.returncode, 'stop_reason': stop_reason,
            'stdout': bytes(outputs[p.stdout]).decode(errors='replace'),
            'stderr': bytes(outputs[p.stderr]).decode(errors='replace'),
            'group_kill_sent': killed, 'leader_waited': True,
            'descendants_waited': descendant_count, 'process_group_absent': group_absent,
            'container_removal': 'separate Docker inspect required'}


def confirmed_absent(result):
    return (result['exit_code'] != 0 and result['stop_reason'] is None and
            result['stderr'].rstrip('\n') == 'Error response from daemon: No such container: ' + NAME)


def cleanup():
    removed = execute_reviewed('rm', timeout=30)
    inspected = execute_reviewed('inspect', timeout=30)
    ok = confirmed_absent(inspected)
    return {'state': 'inspect-confirmed absent' if ok else 'not confirmed',
            'rm_exit_code': removed['exit_code'], 'inspect_exit_code': inspected['exit_code'],
            'inspect_stop_reason': inspected['stop_reason']}


def verify_inputs():
    a = json.loads((HERE / 'source-allowlist.json').read_text())
    for n, h in a['files'].items():
        p = ROOT / n
        if p.is_symlink() or not p.is_file() or digest(p) != h:
            raise Stop('source input drift: ' + n)
    m = json.loads((HERE / 'manifest.json').read_text())
    actual = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    if actual != set(m['files']) or any(p.is_symlink() for p in HERE.rglob('*')):
        raise Stop('adapter exact file set')
    for n, h in m['files'].items():
        if digest(HERE / n) != h:
            raise Stop('adapter file hash drift: ' + n)
    expected = {x['package']: (x['version'], x['architecture']) for x in json.loads((ROOT / 'runtime_build/inputs/post-install-anchor.json').read_text())['post_install']}
    # Reviewed base identities from pinned dpkg status, not a local apt simulation.
    base = {}
    for block in (ROOT / 'runtime_build/inputs/base-dpkg-status').read_text().split('\n\n'):
        d = dict(x.split(': ', 1) for x in block.splitlines() if ': ' in x and not x.startswith(' '))
        if d.get('Status') == 'install ok installed':
            base[d['Package']] = (d['Version'], d['Architecture'])
    if len(base) != 92 or len(expected) != 146:
        raise Stop('reviewed pair count')
    return expected, base


def prepare_work():
    if WORK.exists() or WORK.is_symlink():
        raise Stop('fresh work directory required')
    WORK.mkdir(mode=0o700)
    names = ['apt.sources', 'ubuntu-archive-keyring.gpg', 'ca-certificates-bootstrap.deb']
    for n in names:
        shutil.copyfile(ROOT / 'runtime_build/inputs' / n, WORK / n)
    shutil.copyfile(HERE / 'discover.sh', WORK / 'discover.sh')
    (WORK / 'inputs.sha256').write_text(''.join(digest(WORK / n) + '  ' + n + '\n' for n in names + ['discover.sh']))


def run(gate, install_gate, stage):
    if EVIDENCE.is_symlink():
        raise Stop('evidence directory symlink')
    EVIDENCE.mkdir(exist_ok=True)
    initial = receipt()
    target = EVIDENCE / 'receipt.json'
    target.write_text(safe_json(initial))
    if gate != 'true':
        if gate != 'false':
            initial.update(state='REFUSED', reason='exact boolean gate required')
        target.write_text(safe_json(initial))
        return 0 if gate == 'false' else 1
    if stage != 'A' or install_gate != 'false':
        initial.update(state='REFUSED', reason='Stage B and install paths absent')
        target.write_text(safe_json(initial))
        return 1
    began = False
    state = receipt('BLOCKED', 'discovery incomplete', hosted_attempted=True)
    try:
        expected, base = verify_inputs()
        if sys.platform != 'linux' or os.uname().machine != 'x86_64':
            raise Stop('required Linux x86_64 runner unavailable')
        info = execute_reviewed('info', timeout=30)
        state['docker_probe_process'] = {k: v for k, v in info.items() if k not in ('stdout', 'stderr')}
        if info['exit_code'] or info['stop_reason']:
            raise Stop('Docker capability unavailable')
        d = json.loads(info['stdout'])
        if d.get('OSType') != 'linux' or d.get('Architecture') not in ('x86_64', 'amd64'):
            raise Stop('Docker architecture/platform mismatch')
        state['docker_version'] = str(d.get('ServerVersion', 'unknown'))[:80]
        prepare_work()
        pull = execute_reviewed('pull', timeout=300)
        state['pull_process'] = {k: v for k, v in pull.items() if k not in ('stdout', 'stderr')}
        if pull['exit_code'] or pull['stop_reason']:
            raise Stop('registry pull blocked, unavailable or rate limited')
        began = True
        actual = execute_reviewed('run', timeout=900)
        state['process'] = {k: v for k, v in actual.items() if k not in ('stdout', 'stderr')}
        retained = [line for line in actual['stdout'].splitlines() if line.startswith(('TOOL\t', 'BASE\t', 'POCKET\t', 'Inst ', 'Remv ', 'PLAN_BEGIN', 'PLAN_END'))]
        prefix = '\n'.join(retained)[:CAP]
        if BAD.search(prefix):
            raise Stop('public evidence redaction check failed')
        (EVIDENCE / 'plan-prefix.txt').write_text(prefix + '\n')
        if actual['exit_code'] or actual['stop_reason']:
            raise Stop('container discovery failed or timed out')
        plan = parse_plan(actual['stdout'], expected, base)
        state.update(state='MATCH', reason='actual plan identity only; independent anchor review required', plan=plan,
                     hosted_execution='Stage A plan observed; application/CP312 execution NOT RUN')
    except (Stop, OSError, ValueError, KeyError) as e:
        state.update(state='BLOCKED', reason=str(e)[:300] if isinstance(e, Stop) else 'source, capability or evidence parsing unavailable')
    finally:
        if began:
            try:
                state['cleanup'] = cleanup()
                if state['cleanup']['state'] != 'inspect-confirmed absent':
                    state.update(state='BLOCKED', reason='container removal not confirmed')
            except (OSError, ValueError) as e:
                state.update(state='BLOCKED', reason='container cleanup unavailable', cleanup={'state': 'not confirmed'})
        target.write_text(safe_json(state))
    return 0 if state['state'] == 'MATCH' else 1


if __name__ == '__main__':
    # Dispatch data is never argv or code. No CLI dynamic subprocess input accepted.
    if os.environ.get('CLEANUP_ONLY', 'false') == 'true':
        if os.environ.get('DISCOVERY_GATE', 'false') != 'true':
            raise SystemExit(0)
        result = cleanup()
        EVIDENCE.mkdir(exist_ok=True)
        target = EVIDENCE / 'receipt.json'
        state = json.loads(target.read_text()) if target.is_file() else receipt('BLOCKED', 'discovery receipt unavailable')
        state['cleanup'] = result
        if result['state'] != 'inspect-confirmed absent':
            state.update(state='BLOCKED', reason='container removal not confirmed')
        target.write_text(safe_json(state))
        raise SystemExit(0 if result['state'] == 'inspect-confirmed absent' else 1)
    raise SystemExit(run(os.environ.get('DISCOVERY_GATE', 'false'),
                         os.environ.get('INSTALL_GATE', 'false'),
                         os.environ.get('DISCOVERY_STAGE', 'A')))
