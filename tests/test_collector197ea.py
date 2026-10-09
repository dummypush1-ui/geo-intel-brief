import unittest,io
from dataclasses import replace
from unittest.mock import patch
from integration.collector197_job_runtime import JobRuntimeEvidence,JobRefused,JOB_BYTES,PARENT_BYTES,COORDINATOR_BYTES,read_job_facts,require_job_provider
from integration.collector197_coverage import catalog_fingerprint
from integration.collector197_job import run_job,main

def evidence():return JobRuntimeEvidence(catalog_fingerprint(),'owner-original-reference','runner-probe-reference',100,200,JOB_BYTES,JOB_BYTES,0,1,PARENT_BYTES,COORDINATOR_BYTES,90,True,True,True,True)
class Tests(unittest.TestCase):
 def test_exact_job_record_no_wsgi(self):
  self.assertEqual(evidence().validate(101),evidence());self.assertNotIn('wsgi',evidence().__dict__)
 def test_memory_freshness_guards(self):
  for v in (replace(evidence(),available_memory_bytes=JOB_BYTES-1),replace(evidence(),expires_at=101),replace(evidence(),expires_at=221),replace(evidence(),aggregate_memory_max=JOB_BYTES+1),replace(evidence(),parent_as_limit=PARENT_BYTES+1),replace(evidence(),coordinator_as_limit=COORDINATOR_BYTES+1),replace(evidence(),aggregate_swap_max=1),replace(evidence(),aggregate_oom_group=0),replace(evidence(),job_deadline_seconds=91),replace(evidence(),pid_namespace=1),replace(evidence(),activation_reference='')):
   with self.assertRaises(JobRefused):v.validate(101)
 def test_web_record_cannot_pass(self):
  from tests.test_collector197c import evidence as web
  with self.assertRaises(JobRefused):require_job_provider(web,lambda:101)
 def test_default_off_no_reads_clients(self):
  with patch('integration.collector197_job.read_job_facts',side_effect=AssertionError):
   self.assertEqual(run_job({},nonce=None,client_factory=lambda u:(_ for _ in ()).throw(AssertionError()))['state'],'disabled')
 def test_true_without_provider_before_client(self):
  with self.assertRaises(JobRefused):run_job({'COLLECTION_ENABLED':'true'},nonce='n'*24,client_factory=lambda u:(_ for _ in ()).throw(AssertionError()))
 def test_environment_booleans_no_shortcut(self):
  with self.assertRaises(JobRefused):run_job({'COLLECTION_ENABLED':'true','JOB_RUNTIME_READY':'true'},nonce='n'*24)
 def test_unsupported_facts_before_client(self):
  with patch('integration.collector197_job.read_job_facts',return_value={'supported':False}):
   with self.assertRaises(JobRefused):run_job({'COLLECTION_ENABLED':'true'},nonce='n'*24,runtime_evidence=evidence,clock=lambda:101,client_factory=lambda u:(_ for _ in ()).throw(AssertionError()))
 def test_diagnostic_only_cli(self):
  out=io.StringIO();self.assertEqual(main(['--run'],output=out),2);self.assertNotIn('secret',out.getvalue())
 def test_diagnostic_sanitized_guard_failure(self):
  with patch('integration.collector197_job_runtime._guard',side_effect=ValueError('PRIVATE-URI')):
   result=read_job_facts()
  self.assertFalse(result['supported']);self.assertNotIn('PRIVATE',str(result));self.assertFalse(result['activation_authority'])
 def test_invalid_env_and_alias_refused(self):
  for env in ({'COLLECTION_ENABLED':True},{'ENABLE_FULL_TEXT':'true'},{'COLLECTION_ENABLED':'TRUE'}):
   with self.assertRaises(ValueError):run_job(env,nonce=None)

class RealLimits(unittest.TestCase):
 def test_parent_and_coordinator_allocation_refused(self):
  import subprocess,sys
  for limit in (PARENT_BYTES,COORDINATOR_BYTES):
   code='import resource;resource.setrlimit(resource.RLIMIT_AS,('+str(limit)+','+str(limit)+'));\ntry: x=bytearray('+str(limit)+')\nexcept MemoryError: raise SystemExit(0)\nraise SystemExit(9)'
   result=subprocess.run([sys.executable,'-I','-c',code],capture_output=True,timeout=5)
   self.assertEqual(result.returncode,0)
 def test_coordinator_job_guard_before_import(self):
  import ast
  from pathlib import Path
  tree=ast.parse((Path(__file__).resolve().parents[1]/'integration/collector197_coordinator_child.py').read_text())
  bound=next(i for i,n in enumerate(tree.body)if isinstance(n,ast.If)and "job_mode"in ast.unparse(n))
  imp=next(i for i,n in enumerate(tree.body)if isinstance(n,ast.ImportFrom)and n.module=='integration.collector197_supervisor')
  self.assertLess(bound,imp)
 def test_cli_real_bound_diagnostic_no_db(self):
  import subprocess,sys,json
  from pathlib import Path
  p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'collector197_job_cli.py'),'--diagnose'],capture_output=True,timeout=10)
  self.assertEqual(p.returncode,0);out=json.loads(p.stdout)
  self.assertEqual(out['parent_as_limit'],PARENT_BYTES);self.assertFalse(out['activation_authority'])
  # Shared local cgroup isn't a usable runner guard. No readiness shortcut.
  self.assertFalse(out['supported'])

class GuardValidation(unittest.TestCase):
 def test_closed_cgroup_read_and_mutations(self):
  from pathlib import Path
  from types import SimpleNamespace
  from integration.collector197_job_runtime import _guard
  import os
  group='/sys/fs/cgroup/unit'
  data={'/proc/self/cgroup':'0::/unit\n',group+'/memory.max':str(JOB_BYTES),group+'/memory.swap.max':'0',group+'/memory.oom.group':'1',group+'/cgroup.procs':str(os.getpid()),group+'/memory.events':'max 0\noom 0\noom_kill 0\n'}
  with patch.object(Path,'read_text',lambda p:data[str(p)]),patch.object(Path,'resolve',lambda p:p),patch.object(Path,'stat',lambda p:SimpleNamespace(st_uid=0)),patch('os.access',return_value=False):
   self.assertEqual(_guard(),(JOB_BYTES,0,1))
   for key,val in ((group+'/memory.max','max'),(group+'/memory.swap.max','1'),(group+'/memory.oom.group','0'),(group+'/cgroup.procs',str(os.getpid())+' 123'),(group+'/memory.events','max 0\noom 1\noom_kill 0\n'),('/proc/self/cgroup','0::/\n')):
    old=data[key];data[key]=val
    with self.assertRaises((ValueError,JobRefused)):_guard()
    data[key]=old
 def test_writable_guard_refused(self):
  from pathlib import Path
  from types import SimpleNamespace
  from integration.collector197_job_runtime import _guard
  with patch.object(Path,'read_text',return_value='0::/unit\n'),patch.object(Path,'resolve',lambda p:p),patch.object(Path,'stat',lambda p:SimpleNamespace(st_uid=0)),patch('os.access',return_value=True):
   with self.assertRaises(JobRefused):_guard()

class CompositionTests(unittest.TestCase):
 def test_same_durable_orchestration_client_cleanup(self):
  from tests.test_collector197a import Tests as Fixture
  from types import SimpleNamespace
  b=Fixture();b.setUp();closed=[]
  c=SimpleNamespace(close=lambda:closed.append(True))
  env={'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'fixture-writer','COLLECTOR_PROFILE_FINGERPRINT':'a'*64}
  handles={'ledger':b.ledger,'articles':object(),'checkpoints':b.pc}
  with patch('integration.collector197_job.read_job_facts',return_value={'supported':True}),patch('integration.collector197_job.inspect_writer',return_value=handles),patch('integration.collector197_job.run_cycle',return_value={'state':'completed'})as run:
   out=run_job(env,nonce='n'*24,runtime_evidence=evidence,clock=lambda:101,client_factory=lambda u:c)
  self.assertEqual(out['state'],'completed');self.assertEqual(closed,[True])
  kw=run.call_args.kwargs;self.assertIs(kw['ledger'],b.ledger)
  from integration.collector197_coverage import CoverageCheckpoints
  self.assertIs(type(kw['checkpoints']),CoverageCheckpoints);self.assertIs(kw['checkpoints'].c,b.pc)
 def test_changed_evidence_closes_before_cycle(self):
  from types import SimpleNamespace
  env={'COLLECTION_ENABLED':'true','GEO_WRITER_MONGODB_URI':'fixture','COLLECTOR_PROFILE_FINGERPRINT':'a'*64}
  closed=[];records=iter([evidence(),replace(evidence(),nested_isolation=False)])
  with patch('integration.collector197_job.read_job_facts',return_value={'supported':True}),patch('integration.collector197_job.inspect_writer',return_value={}):
   with self.assertRaises(JobRefused):run_job(env,nonce='n'*24,runtime_evidence=lambda:next(records),clock=lambda:101,client_factory=lambda u:SimpleNamespace(close=lambda:closed.append(True)))
  self.assertEqual(closed,[True])
