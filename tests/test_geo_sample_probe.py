import unittest,importlib,os,json
from datetime import datetime,timezone
from unittest.mock import patch
from integration.geo_sample_probe import probe_geo_sample,LABEL
SECRET='mongodb://sentinel-secret'
class Cursor:
 def __init__(self,rows,stage=None,error=RuntimeError):self.rows=rows;self.stage=stage;self.error=error;self.calls=[];self.closes=0
 def step(self,name,*args):
  self.calls.append((name,args))
  if self.stage==name:raise self.error(SECRET)
  return self
 def sort(self,*a):return self.step('sort',*a)
 def limit(self,*a):return self.step('limit',*a)
 def max_time_ms(self,*a):return self.step('max_time_ms',*a)
 def __iter__(self):self.step('iteration');return iter(self.rows)
 def close(self):self.closes+=1;self.step('cursor_close')
class Client:
 def __init__(self,cur):self.cur=cur;self.paths=[];self.closes=0;self.finds=[]
 def __getitem__(self,k):self.paths.append(k);return self
 def find(self,*a):self.finds.append(a);self.cur.step('find');return self.cur
 def close(self):self.closes+=1;self.cur.step('client_close')
class Tests(unittest.TestCase):
 def runprobe(self,rows,stage=None,error=RuntimeError):
  cur=Cursor(rows,stage,error);client=Client(cur)
  with patch('builtins.print') as pr:
   with patch('logging.Logger._log') as log:
    factory=unittest.mock.Mock(return_value=client);r=probe_geo_sample(SECRET,client_factory=factory)
    pr.assert_not_called();log.assert_not_called()
  factory.assert_called_once_with(SECRET,serverSelectionTimeoutMS=5000,connect=False)
  self.assertNotIn(SECRET,json.dumps(r));self.assertEqual(client.closes,1)
  self.assertEqual(cur.closes,0 if stage=='find' else 1)
  return r,client,cur
 def test_exact_boundary_success20(self):
  row={'created_at':'2026-10-06T00:00:00Z','published':'2026-10-06T00:00:00+00:00','score':50}
  r,c,u=self.runprobe([row]*20);self.assertEqual(r['state'],'sample');self.assertEqual(r['sampled_rows'],20);self.assertEqual(c.paths,['geo_intel','articles']);self.assertEqual(c.finds,[({}, {'created_at':1,'published':1,'score':1,'_id':0})]);self.assertEqual(u.calls[:4],[('find',()),('sort',('created_at',-1)),('limit',(20,)),('max_time_ms',(2000,))]);self.assertEqual(r['credential_scope'],LABEL);self.assertTrue(r['probe_issues_no_writes']);self.assertFalse(r['read_only_privileges_verified']);self.assertEqual(r['compatibility']['score']['compatible'],20)
 def test_empty_distinct(self):
  r,_,_=self.runprobe([]);self.assertEqual(r['state'],'empty');self.assertEqual(r['sampled_rows'],0)
 def test_type_counts_not_filter(self):
  r,_,_=self.runprobe([{}, {'score':float('nan'),'published':'not date','created_at':datetime(2026,10,6)}, {'score':True,'published':'2026-10-06','created_at':None}]);self.assertEqual(r['sampled_rows'],3);self.assertEqual(r['compatibility']['score'],{'compatible':0,'incompatible':2,'missing':1});self.assertEqual(r['compatibility']['created_at']['compatible'],0)
 def test_malformed_and_hooks(self):
  class Evil:
   def __str__(self):raise AssertionError('hook')
  class Row(dict):pass
  for rows in [[None],[Row()],[{'score':Evil()}],[{'unknown':1}],[{'published':'x'*101}],[{}]*21]:
   r,_,_=self.runprobe(rows);self.assertEqual(r['state'],'unavailable');self.assertEqual(r['sampled_rows'],0);self.assertEqual(r['compatibility'],{})
 def test_driver_and_cleanup_errors(self):
  for stage in ['find','sort','limit','max_time_ms','iteration','cursor_close','client_close']:
   r,_,_=self.runprobe([],stage);self.assertEqual(r['state'],'unavailable')
 def test_control_cleanup(self):
  for error in [KeyboardInterrupt,SystemExit]:
   for stage in ['sort','iteration','cursor_close','client_close']:
    cur=Cursor([],stage,error);c=Client(cur)
    with self.assertRaises(error):probe_geo_sample(SECRET,client_factory=lambda *a,**k:c)
    self.assertEqual(c.closes,1);self.assertEqual(cur.closes,1)
 def test_constructor_redaction_and_invalid(self):
  def bad(*a,**k):raise RuntimeError(SECRET)
  self.assertEqual(probe_geo_sample(SECRET,client_factory=bad)['state'],'unavailable')
  for uri in [None,'',object(),'x'*8193]:self.assertEqual(probe_geo_sample(uri,client_factory=bad)['state'],'unavailable')
 def test_import_and_existing_gate_untouched(self):
  import integration.geo_sample_probe as m
  with patch.dict(os.environ,{'GEO_MONGODB_URI':SECRET},clear=True),patch('pymongo.MongoClient',side_effect=AssertionError('client')):
   importlib.reload(m)
  from tests.test_geo_only_runtime import env
  from integration.preview_launcher import build_preview
  e=env();e['PREVIEW_GEO_ONLY_ENABLED']='true';e['NEWS_STORE_MAPPING_VERIFIED']='false'
  with self.assertRaises(ValueError):build_preview(e,client_factory=lambda *a,**k:None)

 def test_timeout_vs_connection(self):
  from pymongo.errors import ExecutionTimeout,NetworkTimeout,ServerSelectionTimeoutError
  for error,reason in [(ExecutionTimeout,'query_timeout'),(NetworkTimeout,'io_timeout'),(ServerSelectionTimeoutError,'connection_unavailable')]:
   r,_,_=self.runprobe([],'iteration',error);self.assertEqual(r['unavailable_reason'],reason)
