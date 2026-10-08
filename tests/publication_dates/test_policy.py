import unittest
from datetime import datetime,timezone,timedelta
from integration.publication_dates.policy import publication_date
D=datetime(2026,10,8,12,tzinfo=timezone.utc)
class Tests(unittest.TestCase):
 def test_missing_invalid(self):
  for x,state in [('', 'missing'),(None,'missing'),('bad','invalid'),('x'*257,'invalid')]:self.assertEqual(publication_date(x,D),(None,state))
 def test_naive(self):self.assertEqual(publication_date('2026-10-08T11:00:00',D),(None,'naive_timezone'))
 def test_partial(self):
  for x in ['October 8 11:00 UTC','2026-10 11:00 UTC','2026 11:00 UTC']:
   self.assertEqual(publication_date(x,D),(None,'incomplete'))
 def test_unknown_zone(self):self.assertEqual(publication_date('2026-10-08 11:00 XYZ',D),(None,'unknown_timezone'))
 def test_future_strict(self):self.assertEqual(publication_date('2026-10-08T12:00:01Z',D),(None,'future'))
 def test_complete_rfc_iso_offsets(self):
  for x in ['2026-10-08T12:00:00Z','Thu, 08 Oct 2026 12:00:00 GMT','2026-10-08T17:30:00+05:30']:
   self.assertEqual(publication_date(x,D),(D,'verified'))
 def test_old_not_replaced_now(self):
  result,state=publication_date('2000-01-01T00:00:00Z',D);self.assertEqual(result.year,2000);self.assertEqual(state,'verified')
 def test_leap(self):self.assertEqual(publication_date('2024-02-29T00:00:00Z',D)[1],'verified')
 def test_host_tz_independent(self):
  import subprocess,os,sys,json
  script="from integration.publication_dates.policy import publication_date;from datetime import datetime,timezone;import json;D=datetime(2026,10,9,tzinfo=timezone.utc);print(json.dumps([publication_date('2026-10-08 11:00 '+z,D)[1] for z in ['IST','EST','EDT','PDT','UTC','GMT']]))"
  for zone in ['UTC','Asia/Kolkata','America/New_York']:
   result=subprocess.check_output([sys.executable,'-c',script],env={**os.environ,'TZ':zone},text=True)
   self.assertEqual(json.loads(result),['unknown_timezone']*4+['verified']*2)
 def test_offset_bound(self):
  self.assertEqual(publication_date('2026-10-08T00:00:00+14:01',D)[1],'invalid')
  self.assertEqual(publication_date('2026-10-08T00:00:00+14:00',D)[1],'verified')
 def test_named_offset_rejected(self):
  for v in ['2026-10-01 12:00 UTC+5','2026-10-01 12:00 GMT+3','2026-10-08T11:00:00UTC+0100','2026-10-08T11:00:00Z+01:00','2026-10-08T11:00:00Z-05:00','2026-10-08T11:00:00Z +0100']:
   self.assertEqual(publication_date(v,D)[1],'invalid')
 def test_web_counter_schema(self):
  import ast
  from pathlib import Path
  tree=ast.parse((Path(__file__).parents[2]/'intelligence/geo/web.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_publication_holds');scope={}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'counter-only','exec'),scope)
  valid={k:0 for k in ['missing','invalid','incomplete','naive_timezone','unknown_timezone','future']}
  self.assertEqual(scope['_publication_holds'](valid)['scope'],'cumulative_since_process_start')
  with self.assertRaises(ValueError):scope['_publication_holds']({**valid,'raw':'secret'})
 def test_fake_job_success_diagnostics_and_failed_collection(self):
  import ast
  from pathlib import Path
  tree=ast.parse((Path(__file__).parents[2]/'intelligence/geo/web.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_collection_outcome','_publication_holds','_run_collect_job')]
  counts={k:0 for k in ['missing','invalid','incomplete','naive_timezone','unknown_timezone','future']};counts['missing']=2
  for value in [2,True]:
   scope={'collect_rss':lambda x:value,'EXTRA_RSS_FEEDS':[],'ENABLE_GNEWS':False,'seed_events':lambda:0,'_service':lambda *a:dict(counts),'_collect_status':{},'datetime':datetime,'timezone':timezone,'log':type('Log',(),{'error':lambda *a:None})()}
   exec(compile(ast.Module(body=defs,type_ignores=[]),'fakejob','exec'),scope);scope['_run_collect_job']()
   result=scope['_collect_status']['last_result'];self.assertEqual(result['state'],'failed' if value is True else 'confirmed');self.assertEqual(result['publication_date_holds'],{'scope':'cumulative_since_process_start','counts':counts})
 def test_fake_job_diagnostic_failure_preserves_write(self):
  import ast
  from pathlib import Path
  tree=ast.parse((Path(__file__).parents[2]/'intelligence/geo/web.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_collection_outcome','_publication_holds','_run_collect_job')]
  def unavailable(*a):raise RuntimeError('private diagnostic')
  partial={'state':'partial','attempted':3,'inserted_count':1,'duplicate_count':0,'failed_count':2,'uncertain_count':0,'retry_safe':False}
  for value in [2,partial]:
   scope={'collect_rss':lambda x:value,'EXTRA_RSS_FEEDS':[], 'ENABLE_GNEWS':False,'seed_events':lambda:0,'_service':unavailable,'_collect_status':{},'datetime':datetime,'timezone':timezone,'log':type('Log',(),{'error':lambda *a:None})()}
   exec(compile(ast.Module(body=defs,type_ignores=[]),'fakejob','exec'),scope);scope['_run_collect_job']()
   result=scope['_collect_status']['last_result'];self.assertEqual(result['state'],'partial' if type(value)is dict else 'confirmed');self.assertEqual(result['publication_date_holds'],{'scope':'unavailable'})
   self.assertEqual(result['rss']['inserted_count'],1 if type(value)is dict else 2)
if __name__=='__main__':unittest.main()
