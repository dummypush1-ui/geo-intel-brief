import unittest,sys,time,json
from pathlib import Path
from unittest.mock import patch
from integration.collector197_coordinator import supervised_candidates,CoordinatorRefused
class Tests(unittest.TestCase):
 def test_complete_envelope(self):
  from collector113_prep.feed_composition import original_catalog
  n=len(original_catalog())
  out={'candidates':[],'source_states':[{'index':i,'state':'unstarted'}for i in range(n)],'wire_bytes':0,'decoded_bytes':0,'all_sources_healthy':False}
  script='import sys,json;json.load(sys.stdin);print('+repr(json.dumps(out))+')'
  with patch('integration.collector197_coordinator._command',return_value=[sys.executable,'-c',script]):
   self.assertEqual(supervised_candidates(deadline=time.monotonic()+20,per_feed_seconds=25)['source_states'],out['source_states'])
 def test_invalid_envelope_refused(self):
  with patch('integration.collector197_coordinator._command',return_value=[sys.executable,'-c','import sys;sys.stdin.read();print("{}")']):
   with self.assertRaises(CoordinatorRefused):supervised_candidates(deadline=time.monotonic()+20,per_feed_seconds=25)
 def test_forced_coordinator_kill_no_namespace_descendants(self):
  root=Path(__file__).resolve().parents[1];fixture=root/'integration/_collector197_coord_fixture.py'
  fixture.write_text('''import sys,os,json,subprocess,time
sys.path.insert(0,''' + repr(str(root)) + ''')
from integration.collector197_supervisor import _namespace_command
json.load(sys.stdin)
cmd=[sys.executable,'-c','import time;marker="collector197_forced_death_proof";time.sleep(60)']
subprocess.Popen(_namespace_command(cmd),start_new_session=False)
import signal
signal.signal(signal.SIGTERM,signal.SIG_IGN)
time.sleep(60)
''')
  try:
   with patch('integration.collector197_coordinator._command',return_value=[sys.executable,str(fixture)]):
    with self.assertRaises(CoordinatorRefused):supervised_candidates(deadline=time.monotonic()+15.2,per_feed_seconds=25)
   time.sleep(.1)
   for proc in Path('/proc').glob('[0-9]*/cmdline'):
    try:cmd=proc.read_bytes()
    except (FileNotFoundError,PermissionError):continue
    if b'collector197_forced_death_proof' in cmd and b'python' in cmd and b'-c' in cmd:
     self.fail('Feed namespace survived forced coordinator kill')
  finally:fixture.unlink(missing_ok=True)
