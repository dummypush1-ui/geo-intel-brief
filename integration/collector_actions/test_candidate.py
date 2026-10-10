import unittest,hashlib,copy,io,json
from unittest.mock import patch
from integration.collector_actions import entry
from integration.collector_actions.provider import protected_receipt,MAX_PEAK
class Tests(unittest.TestCase):
 def payload(self):return dict(mode='collect',repository=entry.REPO,run_id='12345',run_attempt='1',activation_reference='owner-original-message-id',values={'GEO_WRITER_MONGODB_URI':'fixture-only','COLLECTOR_PROFILE_FINGERPRINT':'a'*64})
 def test_nonce_stable_and_scoped(self):
  self.assertEqual(entry.nonce(entry.REPO,'12345'),entry.nonce(entry.REPO,'12345'))
  self.assertNotEqual(entry.nonce(entry.REPO,'12345'),entry.nonce(entry.REPO,'12346'))
 def test_closed_config(self):
  x=self.payload();self.assertEqual(entry.config(x)['ENABLE_GNEWS'],'false')
  mutations=[('mode','run'),('repository','wrong'),('run_id','1;touch'),('run_attempt','0'),('activation_reference','has space')]
  for k,v in mutations:
   y=copy.deepcopy(x);y[k]=v
   with self.assertRaises(ValueError):entry.config(y)
  y=copy.deepcopy(x);y['values']['RUNTIME_READY']='true'
  with self.assertRaises(ValueError):entry.config(y)
 def test_rerun_never_calls_run(self):
  x=self.payload();x['run_attempt']='2'
  with patch('os.geteuid',return_value=1000),patch.object(entry,'read_job_facts',return_value={'supported':True}),patch.object(entry,'ActionsProvider')as p,patch.object(entry,'read_status',return_value={'known':False,'blocked':False,'history_count':0}),patch.object(entry,'run_job',side_effect=AssertionError):
   self.assertEqual(entry.execute(x)['state'],'status_only_held')
 def test_accepted_uncertain_any_active_full_hold(self):
  for s in [{'known':True,'blocked':False,'history_count':1},{'known':True,'blocked':True,'history_count':0},{'known':False,'blocked':True,'history_count':0},{'known':False,'blocked':False,'history_count':64}]:
   with patch.object(entry,'ActionsProvider'),patch.object(entry,'read_status',return_value=s),patch.object(entry,'run_job',side_effect=AssertionError):self.assertEqual(entry.execute(self.payload())['state'],'status_only_held')
 def test_fresh_claim_exact_provider(self):
  with patch.object(entry,'ActionsProvider')as p,patch.object(entry,'read_status',return_value={'known':False,'blocked':False,'history_count':0}),patch.object(entry,'run_job',return_value={'state':'completed'})as run:
   self.assertEqual(entry.execute(self.payload())['state'],'completed');self.assertIs(run.call_args.kwargs['runtime_evidence'],p.return_value)
 def test_provider_refuses_before_db(self):
  with patch.object(entry,'ActionsProvider')as p,patch.object(entry,'read_status',side_effect=AssertionError):
   p.return_value.side_effect=ValueError('private')
   with self.assertRaises(ValueError):entry.execute(self.payload())
 def test_status_no_write(self):
  x=self.payload();x['mode']='status'
  with patch('os.geteuid',return_value=1000),patch.object(entry,'read_job_facts',return_value={'supported':True}),patch.object(entry,'ActionsProvider'),patch.object(entry,'read_status',return_value={'known':False,'blocked':False,'history_count':0}),patch.object(entry,'run_job',side_effect=AssertionError):self.assertEqual(entry.execute(x)['state'],'status_only_held')
 def test_secret_errors_redacted(self):
  with patch('sys.stdin',type('S',(),{'buffer':io.BytesIO(json.dumps(self.payload()).encode())})()),patch('sys.stdout',new_callable=io.StringIO)as out,patch.object(entry,'execute',side_effect=ValueError('PRIVATE_URI')):
   self.assertEqual(entry.main(),2);self.assertNotIn('PRIVATE',out.getvalue())
 def test_root_receipt_refusal(self):
  import tempfile,pathlib
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'receipt';p.write_text('{}')
   with self.assertRaises(ValueError):protected_receipt(p,'.','identity','ref',100)
 def test_runtime_bounded_before_import(self):
  import ast,pathlib
  t=ast.parse(pathlib.Path(entry.__file__).read_text());bound=next(i for i,n in enumerate(t.body)if 'setrlimit'in ast.unparse(n));app=next(i for i,n in enumerate(t.body)if isinstance(n,ast.ImportFrom)and n.module=='integration.collector197_job');self.assertLess(bound,app)
 def test_shell_does_not_fake_ready(self):
  import pathlib
  s=pathlib.Path(entry.__file__).with_name('launch.sh').read_text();self.assertIn('collector197_job_diagnostic.sh',s);self.assertIn('receipt.py',s);self.assertNotIn('aggregate_adversary_verified=true',s)
if __name__=='__main__':unittest.main()

class QualificationRules(unittest.TestCase):
 def bundle(self):
  from integration.collector_actions.provider import MAX_PEAK
  q={'version':1,'run_identity':'run','activation_reference':'owner','source_digest':'digest','observed_at':100,'measurement_peak':1000,'measurement_events':dict.fromkeys(('max','oom','oom_kill','oom_group_kill'),0),'aggregate_adversary_verified':True,'measurement_completed':True}
  e={'measurement_peak':q['measurement_peak'],'measurement_events':q['measurement_events'],'adversary_exit':0,'adversary_log':'aggregate_fixture_oom_group_kill_verified=true'}
  return {'receipt':q,'evidence':e,'evidence_hash':hashlib.sha256(json.dumps(e,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 def call(self,b,now=101,owner=0,mode=0o100444):
  from types import SimpleNamespace
  from integration.collector_actions.provider import protected_receipt
  with patch('os.fstat',return_value=SimpleNamespace(st_uid=owner,st_mode=mode,st_size=1000)),patch('fcntl.fcntl',return_value=0),patch('os.pread',return_value=json.dumps(b).encode()),patch('integration.collector_actions.provider.source_digest',return_value='digest'):
   return protected_receipt(None,'.','run','owner',now)
 def test_positive_exact_qualification(self):self.assertEqual(self.call(self.bundle())['measurement_peak'],1000)
 def test_mutations_refuse(self):
  cases=[('observed_at',0),('measurement_peak',MAX_PEAK+1),('aggregate_adversary_verified',False),('source_digest','wrong'),('run_identity','wrong'),('activation_reference','wrong'),('measurement_completed',False)]
  for k,v in cases:
   b=self.bundle();b['receipt'][k]=v
   with self.assertRaises(ValueError):self.call(b,now=221 if k=='observed_at'else 101)
  for k in ('max','oom','oom_kill','oom_group_kill'):
   b=self.bundle();b['receipt']['measurement_events'][k]=1
   with self.assertRaises(ValueError):self.call(b)
  for owner,mode in ((1,0o100444),(0,0o100644),(0,0o120444)):
   with self.assertRaises(ValueError):self.call(self.bundle(),owner=owner,mode=mode)
  b=self.bundle();b['evidence_hash']='wrong'
  with self.assertRaises(ValueError):self.call(b)
 def test_privileges_and_window(self):
  from integration.collector_actions.provider import ActionsProvider
  from pathlib import Path
  p=ActionsProvider('.',None,'run','owner',clock=lambda:101)
  with patch('os.geteuid',return_value=0):
   with self.assertRaises(ValueError):p()
  for no_new,caps in [('0','0'),('1','1')]:
   text='NoNewPrivs: '+no_new+'\nCapEff: '+caps+'\nCapPrm: 0\nCapInh: 0\nCapAmb: 0\n'
   with patch('os.geteuid',return_value=1000),patch.object(Path,'read_text',return_value=text):
    with self.assertRaises(ValueError):p()

class PositiveProvider(unittest.TestCase):
 def test_actual_fact_binding_and_refresh(self):
  from integration.collector_actions.provider import ActionsProvider
  from integration.collector197_job_runtime import JOB_BYTES,PARENT_BYTES
  from pathlib import Path
  now=[100];p=ActionsProvider('.',None,'run','owner',clock=lambda:now[0])
  status='NoNewPrivs: 1\nCapEff: 0\nCapPrm: 0\nCapInh: 0\nCapAmb: 0\n'
  facts={'supported':True,'available_memory_bytes':JOB_BYTES+1,'aggregate_memory_max':JOB_BYTES,'aggregate_swap_max':0,'aggregate_oom_group':1,'parent_as_limit':PARENT_BYTES,'pid_namespace':True,'nested_isolation':True,'source_pins':True}
  with patch('os.geteuid',return_value=1000),patch.object(Path,'read_text',return_value=status),patch('integration.collector_actions.provider.protected_receipt')as qual,patch('integration.collector_actions.provider.read_job_facts',return_value=facts)as read:
   self.assertEqual(p().validate(100).available_memory_bytes,JOB_BYTES+1)
   now[0]=150;p();self.assertEqual(qual.call_count,1);self.assertEqual(read.call_count,2)
   now[0]=191
   with self.assertRaises(ValueError):p()
 def test_changed_actual_facts_refuse(self):
  from integration.collector_actions.provider import ActionsProvider
  from pathlib import Path
  p=ActionsProvider('.',None,'run','owner',clock=lambda:100)
  status='NoNewPrivs: 1\nCapEff: 0\nCapPrm: 0\nCapInh: 0\nCapAmb: 0\n'
  with patch('os.geteuid',return_value=1000),patch.object(Path,'read_text',return_value=status),patch('integration.collector_actions.provider.protected_receipt'),patch('integration.collector_actions.provider.read_job_facts',return_value={'supported':False}):
   with self.assertRaises(ValueError):p()

class SurvivorTests(QualificationRules):
 def evidence_update(self,b):b['evidence_hash']=hashlib.sha256(json.dumps(b['evidence'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def test_fd_readonly(self):
  with patch('fcntl.fcntl',return_value=1):
   from types import SimpleNamespace
   with patch('os.fstat',return_value=SimpleNamespace(st_uid=0,st_mode=0o100444,st_size=1000)):
    with self.assertRaises(ValueError):protected_receipt(None,'.','run','owner',101)
 def test_independent_peak_consistency(self):
  b=self.bundle();b['evidence']['measurement_peak']=999;self.evidence_update(b)
  with self.assertRaises(ValueError):self.call(b)
 def test_provider_adversary_log_consistency(self):
  b=self.bundle();b['evidence']['adversary_log']='notverified';self.evidence_update(b)
  with self.assertRaises(ValueError):self.call(b)
 def test_peak_cap_independently(self):
  b=self.bundle();b['receipt']['measurement_peak']=MAX_PEAK+1;b['evidence']['measurement_peak']=MAX_PEAK+1;self.evidence_update(b)
  with self.assertRaises(ValueError):self.call(b)
 def test_events_independently(self):
  for k in ('max','oom','oom_kill','oom_group_kill'):
   b=self.bundle();b['receipt']['measurement_events'][k]=1;b['evidence']['measurement_events'][k]=1;self.evidence_update(b)
   with self.assertRaises(ValueError):self.call(b)
 def test_early_status_requires_facts(self):
  x=Tests().payload();x['mode']='status'
  with patch('os.geteuid',return_value=1000),patch.object(entry,'read_job_facts',return_value={'supported':False}),patch.object(entry,'read_status',side_effect=AssertionError):
   with self.assertRaises(ValueError):entry.execute(x)
 def test_each_capability_refused(self):
  from integration.collector_actions.provider import ActionsProvider
  from pathlib import Path
  for cap in ('CapEff','CapPrm','CapInh','CapAmb'):
   status='NoNewPrivs: 1\n'+'\n'.join(k+': '+('1'if k==cap else'0')for k in ('CapEff','CapPrm','CapInh','CapAmb'))+'\n'
   with patch('os.geteuid',return_value=1000),patch.object(Path,'read_text',return_value=status):
    with self.assertRaises(ValueError):ActionsProvider('.',None,'run','owner',clock=lambda:100)()
 def test_shell_measure_exit_gate(self):
  from pathlib import Path
  s=Path(entry.__file__).with_name('launch.sh').read_text();self.assertLess(s.index('if [[ $mode == measure ]]'),s.index('launch "$cg/run" 3<'));self.assertIn('exit 0',s[s.index('if [[ $mode == measure ]]'):s.index('launch "$cg/run" 3<')])
 def test_fresh_claim_deadline_passed(self):
  with patch.object(entry,'ActionsProvider'),patch.object(entry,'read_status',return_value={'known':False,'blocked':False,'history_count':0}),patch.object(entry,'run_job',return_value={'state':'completed'})as run,patch('time.monotonic',return_value=100):
   entry.execute(Tests().payload());self.assertEqual(run.call_args.kwargs['hard_deadline'],180)

class ReceiptProducer(unittest.TestCase):
 def exercise(self,change=None):
  import tempfile,pathlib
  from integration.collector_actions.receipt import create
  with tempfile.TemporaryDirectory()as d:
   r=pathlib.Path(d);g=r/'group';g.mkdir()
   payload={'repository':entry.REPO,'run_id':'12345','run_attempt':'1','activation_reference':'owner'}
   fixture={'maximum_rows':1000,'checkpoint_fixture':True,'writer_bson_fixture':True,'aggregate_overbudget_refused':True,'real_db_writes':False}
   result={'state':'measured_no_write','readonly_mongo_preflight':True,'writer_memory_proven':False,'driver_serialization_fixture':fixture,'source_digest':'digest'}
   files={'memory.max':'3221225472','memory.swap.max':'0','memory.oom.group':'1','cgroup.procs':'','memory.events':'max 0\noom 0\noom_kill 0\noom_group_kill 0\n','memory.peak':'1000'}
   adversary='aggregate_fixture_oom_group_kill_verified=true'
   if change:result,files,adversary=change(result,files,adversary)
   (r/'payload').write_text(json.dumps(payload));(r/'result').write_text(json.dumps(result));(r/'adversary').write_text(adversary)
   for k,v in files.items():(g/k).write_text(v)
   with patch('os.geteuid',return_value=0):create(r/'payload',r/'result',g,r/'adversary',r/'receipt')
   return json.loads((r/'receipt').read_text())
 def test_positive_derived_raw_hash(self):
  q=self.exercise();self.assertEqual(q['receipt']['measurement_peak'],1000);self.assertEqual(q['evidence_hash'],hashlib.sha256(json.dumps(q['evidence'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
 def test_root_required(self):
  from integration.collector_actions.receipt import create
  with patch('os.geteuid',return_value=1000):
   with self.assertRaises(ValueError):create('a','b','c','d','e')
 def test_every_result_guard(self):
  for k,v in [('state','completed'),('readonly_mongo_preflight',False),('writer_memory_proven',True),('driver_serialization_fixture',{})]:
   def change(a,b,c):a[k]=v;return a,b,c
   with self.assertRaises(ValueError):self.exercise(change)
 def test_every_guard_file(self):
  for k,v in [('memory.max','1'),('memory.swap.max','1'),('memory.oom.group','0'),('cgroup.procs','123'),('memory.events','max 1\noom 0\noom_kill 0\noom_group_kill 0\n'),('memory.peak','0'),('memory.peak',str(MAX_PEAK+1))]:
   def change(a,b,c):b[k]=v;return a,b,c
   with self.assertRaises(ValueError):self.exercise(change)
 def test_adversary_and_size(self):
  for c in ('wrong','x'*8193):
   with self.assertRaises(ValueError):self.exercise(lambda a,b,d:(a,b,c))

class MainSignals(unittest.TestCase):
 def test_handlers_alarm_and_cleanup(self):
  import signal
  with patch('sys.stdin',type('S',(),{'buffer':io.BytesIO(json.dumps(Tests().payload()).encode())})()),patch('sys.stdout',new_callable=io.StringIO),patch.object(entry,'execute',return_value={'state':'completed'}),patch('signal.signal')as sig,patch('signal.setitimer')as timer:
   self.assertEqual(entry.main(),0)
   sig.assert_any_call(signal.SIGTERM,entry.soft_stop);sig.assert_any_call(signal.SIGALRM,entry.soft_stop)
   self.assertEqual(timer.call_args_list[0].args,(signal.ITIMER_REAL,82));self.assertEqual(timer.call_args_list[-1].args,(signal.ITIMER_REAL,0))
 def test_soft_stop_redacted_exit(self):
  with patch('sys.stdin',type('S',(),{'buffer':io.BytesIO(json.dumps(Tests().payload()).encode())})()),patch('sys.stdout',new_callable=io.StringIO)as out,patch.object(entry,'execute',side_effect=entry.soft_stop),patch('signal.signal'),patch('signal.setitimer'):
   self.assertEqual(entry.main(),2);self.assertEqual(out.getvalue(),'{"error":"job_held_inspect_durable_state_no_blind_retry"}\n')
 def test_launch_static_limits_and_exit_gates(self):
  from pathlib import Path
  s=Path(entry.__file__).with_name('launch.sh').read_text()
  self.assertIn('/usr/bin/timeout --kill-after=2s 90s',s)
  self.assertIn('if [[ $mode == status || $attempt != 1 ]]',s)
  self.assertIn('launch "$cg/run" < "$base/payload.json"\n exit 0',s)
  self.assertIn("printf 'qualification_no_write_complete=true\\n'\n exit 0",s)
 def test_measure_80_budget(self):
  from pathlib import Path
  s=Path(entry.__file__).read_text();self.assertIn('supervised_candidates(deadline=start+80',s)
