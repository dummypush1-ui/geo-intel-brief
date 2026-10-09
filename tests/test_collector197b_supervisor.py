import unittest,time,sys,os,json,tempfile
from pathlib import Path
from unittest.mock import patch
from integration.collector197_supervisor import collect_catalog,SupervisorRefused
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.child=Path(self.t.name)/'fixture.py'
 def tearDown(self):self.t.cleanup()
 def call(self,script,seconds=2):
  self.child.write_text(script)
  from integration.collector197_supervisor import _namespace_command
  # Fixture is mounted at an installation-owned path, not caller-request code.
  target=Path(__file__).resolve().parents[1]/'integration/_collector197_test_child.py'
  target.write_text(script)
  self.addCleanup(lambda:target.unlink(missing_ok=True))
  with patch('integration.collector197_supervisor._command',return_value=_namespace_command([sys.executable,str(target)])[: -3]+['--bind',str(target.parent),str(target.parent),'--',sys.executable,str(target)]):
   return collect_catalog(deadline=time.monotonic()+20+seconds,per_feed_seconds=25)
 def test_complete_bounded_empty_source_envelopes(self):
  out=self.call("import sys,json\nv=json.load(sys.stdin)\nprint(json.dumps({'type':'wire','bytes':1}));print(json.dumps({'type':'result','envelope':{'index':v['index'],'state':'selected','wire_bytes':1,'decoded_bytes':1,'candidates':[]}}))")
  self.assertTrue(all(r['state']=='selected'for r in out['source_states']))
  self.assertFalse(out['all_sources_healthy']);self.assertEqual(out['candidates'],[])
 def test_global_cutoff_kills_and_reaps_group(self):
  log=Path(__file__).resolve().parents[1]/'integration/_collector197_test_pids'
  log.unlink(missing_ok=True);self.addCleanup(lambda:log.unlink(missing_ok=True))
  script=f"import sys,json,os,time,subprocess\nv=json.load(sys.stdin)\np=subprocess.Popen([sys.executable,'-c','import time;marker=\"collector197_namespace_sleep_proof\";time.sleep(60)'])\nopen({str(log)!r},'a').write(str(os.getpid())+','+str(p.pid)+'\\n')\ntime.sleep(60)"
  start=time.monotonic();out=self.call(script,.2)
  self.assertLess(time.monotonic()-start,1.5)
  self.assertTrue(any(r['state']=='unstarted'for r in out['source_states']))
  self.assertTrue(log.read_text())
  # Namespace PID 2/3 are NOT host PIDs. Inspect host process command lines
  # for the unique sleeping descendant marker instead of checking /proc/2.
  for proc in Path('/proc').glob('[0-9]*/cmdline'):
   try:cmd=proc.read_bytes()
   except (FileNotFoundError,PermissionError):continue
   if b'collector197_namespace_sleep_proof' in cmd and b'python' in cmd and b'-c' in cmd:
    self.fail('Namespace descendant survived cutoff')
 def test_partial_json_never_accepted(self):
  out=self.call("import sys\nsys.stdin.read()\nprint('{')")
  self.assertEqual(out['candidates'],[]);self.assertTrue(all(r['state']=='refused_envelope'for r in out['source_states']))
 def test_output_budget_killed(self):
  out=self.call("import sys,time\nsys.stdin.read()\nsys.stdout.write('x'*1200000);sys.stdout.flush();time.sleep(60)")
  self.assertEqual(out['candidates'],[])
  self.assertTrue(any(r['state']=='refused_timeout_or_budget'for r in out['source_states']))
 def test_four_at_once_only(self):
  log=Path(__file__).resolve().parents[1]/'integration/_collector197_test_live'
  log.unlink(missing_ok=True);self.addCleanup(lambda:log.unlink(missing_ok=True))
  script=f"import json,sys,time,os\nv=json.load(sys.stdin)\nopen({str(log)!r},'a').write(str(os.getpid())+'\\n')\ntime.sleep(60)"
  out=self.call(script,.2);self.assertEqual(len(log.read_text().splitlines()),4)
 def test_pin_drift_before_spawn(self):
  with patch('integration.collector197_supervisor._pins',side_effect=SupervisorRefused('drift')):
   with self.assertRaises(SupervisorRefused):self.call('print(1)')
 def test_parser_remains_feed_group(self):
  p=Path(__file__).resolve().parents[1]/'integration/collector197_parser.py'
  self.assertIn('start_new_session=False',p.read_text());self.assertIn('--die-with-parent',p.read_text());self.assertNotIn('--new-session',p.read_text())

 def test_real_isolated_parser_works_without_new_group(self):
  from integration.collector197_parser import parse_supplied_bytes
  blob=b'<rss version="2.0"><channel><title>Fixture</title></channel></rss>'
  out=parse_supplied_bytes(blob)
  self.assertEqual(out['entries'],[]);self.assertEqual(out['network_namespace'],'loopback_only')

 def test_refused_feed_telemetry_still_counted(self):
  out=self.call("import sys,json;json.load(sys.stdin);print(json.dumps({'type':'wire','bytes':123}));sys.exit(1)")
  from collector113_prep.feed_composition import original_catalog
  self.assertEqual(out['wire_bytes'],123*len(original_catalog()))
  self.assertEqual(out['candidates'],[])
