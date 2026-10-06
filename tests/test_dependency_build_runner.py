import unittest,sys,os,time,json,hashlib
from pathlib import Path
from integration.dependency_build.runner import capture
class RunnerTests(unittest.TestCase):
 def run_case(self,code,**kw):return capture([sys.executable,'-I','-c',code],env={'PATH':'/usr/bin'},**kw)
 def test_stdout_closed_then_sleep_is_reaped(self):
  r=self.run_case('import os,time;os.close(1);os.close(2);time.sleep(30)',wall=.15);self.assertEqual(r['stop_reason'],'wall_deadline');self.assertLess(r['wall_seconds'],3);self.assertIsNotNone(r['exit_code'])
 def test_crash(self):
  r=self.run_case('raise RuntimeError("fixture")');self.assertEqual(r['status'],'blocked');self.assertEqual(r['stop_reason'],'nonzero_exit')
 def test_output_cap(self):
  r=self.run_case('import os;os.write(1,b"x"*100000)',cap=1000);self.assertEqual(r['stop_reason'],'output_cap');self.assertEqual(len(r['output']),1000)
 def test_wall(self):
  r=self.run_case('import time;time.sleep(30)',wall=.1);self.assertEqual(r['stop_reason'],'wall_deadline');self.assertIsNotNone(r['exit_code'])
 def test_success(self):
  r=self.run_case('print("fixed")');self.assertEqual(r['status'],'passed');self.assertEqual(r['output'],b'fixed\n')
 def test_fallback_provenance(self):
  b=Path(__file__).resolve().parents[1]/'integration/dependency_build';a=json.loads((b/'receipt.json').read_text());self.assertEqual(hashlib.sha256((b/'tool-hash-fallback.txt').read_bytes()).hexdigest(),a['fallback_evidence']['script_sha256']);self.assertIn('post-build',a['fallback_evidence']['timing'])
