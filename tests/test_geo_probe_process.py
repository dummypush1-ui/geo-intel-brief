import unittest,sys,subprocess,json,os,time
from unittest.mock import patch
from integration.geo_sample_probe import _result
from integration.geo_probe_process import execute_probe,validate_result
SECRET='mongodb://sentinel-private'
GOOD=_result('empty',0,{k:{'compatible':0,'incompatible':0,'missing':0} for k in ('created_at','published','score')})
class Tests(unittest.TestCase):
 def child(self,code):
  real=subprocess.Popen;children=[]
  def factory(args,**kwargs):
   self.assertEqual(args,[sys.executable,'-m','integration.geo_sample_probe_child']);self.assertNotIn(SECRET,' '.join(args));self.assertEqual(kwargs['env'],{'GEO_MONGODB_URI':SECRET,'LANG':'C.UTF-8'});self.assertEqual(kwargs['stderr'],subprocess.DEVNULL);self.assertTrue(kwargs['start_new_session'])
   p=real([sys.executable,'-c',code],**kwargs);children.append(p);return p
  with patch('integration.geo_probe_process.subprocess.Popen',side_effect=factory):r=execute_probe(SECRET)
  self.assertIsNotNone(children[0].poll());self.assertTrue(children[0].stdout.closed);self.assertNotIn(SECRET,json.dumps(r));return r
 def test_real_exec_success(self):self.assertEqual(self.child('import sys;sys.stdout.write('+repr(json.dumps(GOOD))+')'),GOOD)
 def test_real_malformed_large_nonzero(self):
  for code in ['print("sentinel-private")','print("x"*5000)','raise SystemExit(2)']:
   self.assertEqual(self.child(code)['state'],'unavailable')
 def test_real_timeout(self):
  # Clock makes budget expire immediately after exec; actual child killed/waited.
  with patch('integration.geo_probe_process.time.monotonic',side_effect=[0,11]):r=self.child('import time;time.sleep(60)')
  self.assertEqual(r['unavailable_reason'],'io_timeout')
 def test_no_secret_driver_stderr(self):
  r=self.child('import sys;sys.stderr.write("sentinel-private");sys.stdout.write('+repr(json.dumps(GOOD))+')');self.assertEqual(r,GOOD)
 def test_validate_strict(self):
  for bad in [None,{},dict(GOOD,extra=SECRET),dict(GOOD,sampled_rows=True),dict(GOOD,state='sample'),dict(GOOD,unavailable_reason=SECRET),dict(GOOD,compatibility={})]:
   with self.assertRaises((ValueError,TypeError)):validate_result(bad)
 def test_invalid_uri_no_exec(self):
  with patch('subprocess.Popen',side_effect=AssertionError('effect')):
   for uri in ['',None,'x'*8193]:self.assertEqual(execute_probe(uri)['state'],'unavailable')
 def test_control_kills_child(self):
  real=subprocess.Popen;children=[]
  def factory(*a,**kw):
   p=real([sys.executable,'-c','import time;time.sleep(60)'],**kw);children.append(p);return p
  with patch('subprocess.Popen',side_effect=factory),patch('integration.geo_probe_process.time.monotonic',side_effect=KeyboardInterrupt):
   with self.assertRaises(KeyboardInterrupt):execute_probe(SECRET)
  self.assertIsNotNone(children[0].poll());self.assertTrue(children[0].stdout.closed)
 def test_child_drops_uri_env_and_fixed_output(self):
  import io
  from contextlib import redirect_stdout
  from integration.geo_sample_probe_child import main
  def probe(uri,**kwargs):
   self.assertEqual(uri,SECRET);self.assertNotIn('GEO_MONGODB_URI',os.environ);return GOOD
  with patch.dict(os.environ,{'GEO_MONGODB_URI':SECRET},clear=True),patch('integration.geo_sample_probe.probe_geo_sample',side_effect=probe),redirect_stdout(io.StringIO()) as out:
   main()
  self.assertEqual(json.loads(out.getvalue()),GOOD)
