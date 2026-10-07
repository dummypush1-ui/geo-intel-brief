"""Real supervisor fault checks with fixed test commands, no network."""
import sys,time,unittest,base64,json,os
from unittest.mock import patch
from .runner import run_fetch,FetchRefused
F=(('Fixture','https://example.com/rss','HIGH'),)
class Tests(unittest.TestCase):
 def invoke(self,code,timeout=2):
  with patch('collector124_prep.runner._command',return_value=[sys.executable,'-I','-c',code]):return run_fetch(F,F[0][1],timeout=timeout)
 def test_hung_dns_analogue_killed_and_reaped(self):
  start=time.monotonic()
  with self.assertRaises(FetchRefused):self.invoke('import time;time.sleep(20)',timeout=.2)
  self.assertLess(time.monotonic()-start,1.5)
 def test_output_overflow(self):
  with self.assertRaises(FetchRefused):self.invoke('import sys;sys.stdout.buffer.write(b"x"*3000000)')
 def test_stderr_refused(self):
  with self.assertRaises(FetchRefused):self.invoke('import sys;sys.stderr.write("nope")')
 def test_malformed_envelope_refused(self):
  for wire in ('{}','{"ok":true,"result":{}}','null','{"ok":false,"error":"fetch_refused"}'):
   with self.assertRaises(FetchRefused):self.invoke('print('+repr(wire)+')')
 def test_environment_cleared(self):
  os.environ['UNRELATED_SECRET']='must-not-inherit'
  try:
   with self.assertRaises(FetchRefused):self.invoke('import os,sys;assert "UNRELATED_SECRET" not in os.environ;print("{}")')
  finally:del os.environ['UNRELATED_SECRET']
 def test_exact_success_protocol(self):
  r={'scope':'inactive_https_connector_candidate','url':F[0][1],'body_b64':base64.b64encode(b'feed').decode(),
     'wire_bytes':4,'decoded_bytes':4,'hostname':'example.com','peer':'8.8.8.8','tls_hostname_verified':True,'redirects':False,'delivery':False}
  out=self.invoke('print('+repr(json.dumps({'ok':True,'result':r}))+')')
  self.assertEqual(out['bytes'],b'feed');self.assertEqual(len(out['input_sha256']),64)
 def test_source_pin_drift_before_process(self):
  with patch('collector124_prep.runner.FILE_PINS',{'worker.py':'0'*64}),patch('collector124_prep.runner.subprocess.Popen')as p:
   with self.assertRaises(FetchRefused):run_fetch(F,F[0][1])
   p.assert_not_called()
 def test_unknown_url_before_process(self):
  with patch('collector124_prep.runner.subprocess.Popen')as p:
   with self.assertRaises(ValueError):run_fetch(F,'https://example.com/other')
   p.assert_not_called()
if __name__=='__main__':unittest.main()
