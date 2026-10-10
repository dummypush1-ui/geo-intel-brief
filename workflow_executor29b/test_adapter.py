"""Local fixture QA only; hosted execution NOT RUN; items 27/28/29 OPEN."""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('adapter29b', HERE / 'adapter.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def fixture():
    base = {'p%03d' % n: ('1.0', 'amd64') for n in range(92)}
    post = dict(base)
    for n in range(92, 146):
        post['p%03d' % n] = ('2.0', 'amd64')
    text = 'TOOL\tapt\t2.8.3\n'
    text += ''.join('BASE\t%s\t%s\t%s\tinstalled\n' % (n, v, arch) for n, (v, arch) in base.items())
    text += ''.join('POCKET\t%s\tThu, 08 Oct 2026 00:00:00 UTC\n' % s for s in ('noble', 'noble-updates', 'noble-security'))
    text += 'PLAN_BEGIN\n' + ''.join('Inst %s (2.0 Ubuntu:24.04/noble [amd64])\n' % n for n in post if n not in base) + 'PLAN_END\n'
    return text, post, base


class Tests(unittest.TestCase):
    def test_fixture_match_not_install_permission(self):
        text, expected, base = fixture()
        self.assertFalse(a.parse_plan(text, expected, base)['install_permitted'])

    def test_zero_malformed_oversize(self):
        text, expected, base = fixture()
        for bad in ('', 'arbitrary text', text.replace('PLAN_END\n', ''), text + 'x' * a.CAP):
            with self.assertRaises(a.Stop):
                a.parse_plan(bad, expected, base)

    def test_added_changed_removed_downgraded_arch_wrong_apt(self):
        text, expected, base = fixture()
        bads = [text.replace('p092', 'extra'), text.replace('Inst p092 (2.0', 'Inst p092 (3.0'),
                text.replace('Inst p092 (2.0 Ubuntu:24.04/noble [amd64])\n', ''),
                text.replace('Inst p092 (2.0', 'Inst p092 (0.1'),
                text.replace('Inst p092 (2.0 Ubuntu:24.04/noble [amd64])', 'Remv p092'),
                text.replace(' [amd64])', ' [arm64])'), text.replace('2.8.3\n', '2.4.14\n')]
        for bad in bads:
            with self.assertRaises(a.Stop):
                a.parse_plan(bad, expected, base)

    def test_default_no_source_process_or_network(self):
        with tempfile.TemporaryDirectory() as d, patch.object(a, 'EVIDENCE', pathlib.Path(d)), patch.object(a, 'execute_reviewed', side_effect=AssertionError('process')), patch.object(a, 'verify_inputs', side_effect=AssertionError('read')):
            self.assertEqual(a.run('false', 'false', 'A'), 0)
            self.assertEqual(json.loads((pathlib.Path(d) / 'receipt.json').read_text())['hosted_execution'], 'NOT RUN')

    def test_hostile_inputs_and_stage_install_refused(self):
        with tempfile.TemporaryDirectory() as d, patch.object(a, 'EVIDENCE', pathlib.Path(d)), patch.object(a, 'execute_reviewed', side_effect=AssertionError('process')):
            for gate, install, stage in [('$(touch PWN)', 'false', 'A'), ('true', 'true', 'A'), ('true', 'false', 'B'), ('true', '; docker run evil', 'A')]:
                self.assertEqual(a.run(gate, install, stage), 1)
        self.assertFalse((HERE / 'PWN').exists())

    def test_historical_simulation_only_parser_fixture(self):
        root = HERE.parent
        expected = {x['package']: (x['version'], x['architecture']) for x in json.loads((root / 'runtime_build/inputs/post-install-anchor.json').read_text())['post_install']}
        base = {}
        for block in (root / 'runtime_build/inputs/base-dpkg-status').read_text().split('\n\n'):
            d = dict(x.split(': ', 1) for x in block.splitlines() if ': ' in x and not x.startswith(' '))
            if d.get('Status') == 'install ok installed':
                base[d['Package']] = (d['Version'], d['Architecture'])
        text = 'TOOL\tapt\t2.8.3\n'
        text += ''.join('BASE\t%s\t%s\t%s\tinstalled\n' % (n, v, arch) for n, (v, arch) in base.items())
        text += ''.join('POCKET\t%s\tfixture date\n' % s for s in ('noble', 'noble-updates', 'noble-security'))
        text += 'PLAN_BEGIN\n' + (root / 'runtime_build/inputs/base-status-simulate.txt').read_text() + 'PLAN_END\n'
        self.assertEqual(a.parse_plan(text, expected, base)['outcome'], 'MATCH')

    def test_workflow_template_semantics(self):
        text = (HERE / 'workflow.template.yml').read_text()
        self.assertIn('workflow_dispatch:', text)
        self.assertNotIn('schedule:', text)
        self.assertNotIn('pull_request:', text)
        self.assertIn('contents: read', text)
        self.assertIn('persist-credentials: false', text)
        self.assertIn('retention-days: 1', text)
        self.assertIn("steps.public_evidence.outcome == 'success'", text)
        self.assertIn('__LANDED_COMMIT__', text)
        self.assertIn('__MANIFEST_SHA256__', text)
        self.assertIn('__ADAPTER_SHA256__', text)
        import re
        uses = re.findall(r'uses: ([^\s]+)', text)
        self.assertEqual(len(uses), 2)
        for use in uses:
            self.assertRegex(use, r'^actions/(checkout|upload-artifact)@[0-9a-f]{40}$')
        # Inputs appear only in env or boolean step conditions, never run script bodies.
        for block in text.split('run: |')[1:]:
            script = block.split('      - name:')[0]
            self.assertNotIn('${{', script)
        self.assertEqual(text.count("if: inputs.discovery_gate == true"), 3)
        self.assertIn("if: always() && inputs.discovery_gate == true && steps.verify.outcome == 'success'", text)

    def test_public_work_permissions_restrictive_umask(self):
        import stat
        with tempfile.TemporaryDirectory() as d, patch.object(a, 'WORK', pathlib.Path(d) / 'work'):
            old = os.umask(0o077)
            try:
                a.prepare_work()
            finally:
                os.umask(old)
            self.assertEqual(stat.S_IMODE(a.WORK.stat().st_mode), 0o755)
            files = list(a.WORK.iterdir())
            self.assertEqual(len(files), 5)
            for p in files:
                self.assertTrue(p.is_file())
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o644)
            self.assertIn('type=bind,src=' + str(a.WORK) + ',dst=/reviewed,readonly', a.commands()['run'])

    def test_stderr_redaction_controls_and_caps(self):
        raw = 'safe first\nTOKEN=do-not-retain\nAuthorization: hidden\nhttps://user:pass@example.invalid/\nNAME=value\napi_key hidden\npassword hidden\n' + '\n'.join('plain ' + str(n) for n in range(25)) + '\nlast\x00\x1b\x7f line'
        d = a.diagnostics(dict(stdout='STAGE start\nSTAGE fake\nSTAGE inputs-ok\nSTAGE plan-begin\n', stderr=raw, stop_reason=None))
        self.assertEqual(d['stage_markers'], ['STAGE start', 'STAGE inputs-ok', 'STAGE plan-begin'])
        self.assertEqual(d['suppressed_lines'], 6)
        self.assertGreater(d['truncated_lines'], 0)
        self.assertFalse(d['stderr_empty'])
        self.assertLessEqual(len(d['stderr_tail'].splitlines()), a.STDERR_LINES)
        self.assertNotIn('hidden', d['stderr_tail'])
        self.assertNotIn('\x1b', d['stderr_tail'])
        a.safe_json(d)
        large = a.diagnostics(dict(stdout='', stderr='😀' * 10000, stop_reason='output cap exceeded'))
        self.assertLessEqual(len(large['stderr_tail'].encode()), a.STDERR_BYTES)
        self.assertTrue(large['byte_truncated'])
        self.assertTrue(large['capture_truncated'])
        a.safe_json(large)

    def test_exit2_empty_stdout_receipt_blocked_and_diagnostics_data_only(self):
        def fake(kind, **kwargs):
            base = dict(exit_code=0, stop_reason=None, stdout='', stderr='', leader_waited=True)
            if kind == 'info':
                base['stdout'] = json.dumps({'OSType': 'linux', 'Architecture': 'amd64', 'ServerVersion': 'fixture'})
            if kind == 'run':
                base.update(exit_code=2, stderr='/bin/sh: cannot open /reviewed/discover.sh: Permission denied\n')
            return base
        with tempfile.TemporaryDirectory() as d, patch.object(a, 'EVIDENCE', pathlib.Path(d)), patch.object(a, 'verify_inputs', return_value=({}, {})), patch.object(a, 'prepare_work'), patch.object(a, 'execute_reviewed', side_effect=fake), patch.object(a, 'cleanup', return_value={'state': 'inspect-confirmed absent'}):
            self.assertEqual(a.run('true', 'false', 'A'), 1)
            r = json.loads((pathlib.Path(d) / 'receipt.json').read_text())
            self.assertEqual(r['state'], 'BLOCKED')
            self.assertEqual(r['diagnostics']['stage_markers'], [])
            self.assertIn('Permission denied', r['diagnostics']['stderr_tail'])
            self.assertIn('untrusted', r['diagnostics']['label'])
            self.assertFalse(r['install_permitted'])

    def test_timeout_and_kill_diagnostics_retained(self):
        for reason in ('wall timeout', 'output cap exceeded'):
            d = a.diagnostics(dict(stdout='STAGE start\n', stderr='apt public diagnostic\n', stop_reason=reason))
            self.assertEqual(d['stage_markers'], ['STAGE start'])
            self.assertIn('public diagnostic', d['stderr_tail'])
        empty = a.diagnostics(dict(stdout='', stderr='', stop_reason=None))
        self.assertTrue(empty['stderr_empty'])

    def test_marker_first_command_and_exact_whitelist(self):
        text = (HERE / 'discover.sh').read_text()
        first = next(line for line in text.splitlines() if line.strip() and not line.startswith('#'))
        self.assertEqual(first, "printf '%s\\n' 'STAGE start'")
        for name in ('start', 'inputs-ok', 'dpkg-ok', 'ca-ok', 'apt-update-ok', 'plan-begin'):
            self.assertTrue(a.STAGE_LINE.fullmatch('STAGE ' + name))
        for line in ('STAGE start extra', 'STAGE unknown', ' STAGE start', 'STAGE TOKEN=value'):
            self.assertFalse(a.STAGE_LINE.fullmatch(line))

    def test_fixed_allowlist(self):
        cmds = a.commands()
        self.assertEqual(set(cmds), {'info', 'pull', 'run', 'rm', 'inspect'})
        self.assertEqual(cmds['pull'][-1], a.IMAGE)
        self.assertEqual(cmds['run'][cmds['run'].index('--name') + 1], a.NAME)
        self.assertEqual(cmds['rm'][-1], a.NAME)
        self.assertEqual(cmds['inspect'][-1], a.NAME)
        with self.assertRaises(a.Stop):
            a.execute_reviewed('build')

    def test_fake_docker_inspect_three_outcomes(self):
        # Fake shim does not invoke Docker, network or apt.
        for code, error, expected in [(1, 'Error response from daemon: No such container: ' + a.NAME + '\n', True), (0, '', False), (1, 'Cannot connect to the Docker daemon\n', False)]:
            argv = [sys.executable, '-c', 'import sys;sys.stderr.write(sys.argv[1]);sys.exit(int(sys.argv[2]))', error, str(code)]
            result = a.execute_reviewed('inspect', _test_argv=argv)
            self.assertEqual(a.confirmed_absent(result), expected)
        for err in ['Error response from daemon: No such container: other', ' Error response from daemon: No such container: ' + a.NAME]:
            self.assertFalse(a.confirmed_absent(dict(exit_code=1, stop_reason=None, stderr=err)))

    def test_harmless_timeout_leader_waited(self):
        r = a.execute_reviewed('info', timeout=0.1, _test_argv=[sys.executable, '-c', 'import time;time.sleep(30)'])
        self.assertEqual(r['stop_reason'], 'wall timeout')
        self.assertTrue(r['leader_waited'])

    def test_harmless_group_descendant_killed_and_reaped(self):
        code = 'import subprocess,time,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);print(p.pid,flush=True);time.sleep(30)'
        r = a.execute_reviewed('info', timeout=0.2, _test_argv=[sys.executable, '-c', code])
        child = int(r['stdout'].strip())
        self.assertEqual(r['stop_reason'], 'wall timeout')
        self.assertEqual(r['descendants_waited'], 1)
        self.assertTrue(r['process_group_absent'])
        with self.assertRaises(ProcessLookupError):
            os.kill(child, 0)

    def test_oversize_retains_bounded_prefix(self):
        r = a.execute_reviewed('info', cap=512, _test_argv=[sys.executable, '-c', 'import sys;sys.stdout.write("x"*10000);sys.stdout.flush()'])
        self.assertEqual(r['stdout'], 'x' * 512)
        self.assertIn('output cap exceeded', r['stop_reason'])
        self.assertTrue(r['leader_waited'])

    def test_redaction_size(self):
        for v in ['github_pat_example', 'mongodb+srv://anything', 'Bearer example', 'password=example']:
            with self.assertRaises(a.Stop):
                a.safe_json({'value': v})
        with self.assertRaises(a.Stop):
            a.safe_json({'value': 'x' * a.TOTAL_CAP})

    def test_hash_drift_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            here = root / 'workflow_executor29b'
            here.mkdir()
            (root / 'input').write_text('wrong')
            (here / 'source-allowlist.json').write_text(json.dumps({'files': {'input': '0' * 64}}))
            with patch.object(a, 'ROOT', root), patch.object(a, 'HERE', here), self.assertRaises(a.Stop):
                a.verify_inputs()
            (root / 'input').unlink()
            (root / 'input').symlink_to('/etc/passwd')
            with patch.object(a, 'ROOT', root), patch.object(a, 'HERE', here), self.assertRaises(a.Stop):
                a.verify_inputs()


if __name__ == '__main__':
    unittest.main()
