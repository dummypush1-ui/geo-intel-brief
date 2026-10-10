"""Dependency fakes only, not actual Flask/Mongo integration proof."""
import unittest,sys,types,importlib.util,pathlib,builtins
from unittest.mock import patch
from dataclasses import replace
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
binding=load('integration.mail_mount_binding',ROOT/'integration/mail_mount_binding.py');entry=load('proposed_entry',ROOT/'production_entry.py')
class Store:policy='displayed'
class App:
 def __init__(self,*a,**kw):self.extensions={};self.logger=types.SimpleNamespace(disabled=False);self.wsgi_app=lambda env,start:[b'PUBLIC']
def mod(**kw):m=types.ModuleType('fake');m.__dict__.update(kw);return m
class Tests(unittest.TestCase):
 def setUp(self):
  self.closed=[];self.mounted=[];self.now=100
  self.b=binding.MailBinding(Store(),'s'*48,lambda:None,lambda:self.closed.append(True),99,200,'owner-original','source-original',('geo_intel','articles','events','mail_control','mail_receipts','displayed','private_receipt_no_send'),(True,)*6)
  self.mods={'feature_mail_mount.store':mod(MongoMailStore=Store),'flask':mod(Flask=App),'feature_mail_mount.composition':mod(compose_private_mail=self.compose)}
 def compose(self,app,**kw):self.mounted.append(kw);app.wsgi_app=lambda env,start:[b'PRIVATE'];return app
 def runapp(self,env=None,provider=None,builder=App):
  with patch.dict(sys.modules,self.mods):app=entry.build_production_app(env or {},lambda e:builder(),mail_binding_provider=provider,clock=lambda:self.now)
  original=app.wsgi_app
  def request(env,start):
   with patch.dict(sys.modules,self.mods):return original(env,start)
  app.wsgi_app=request
  return app
 def test_off_does_not_invoke_provider_or_import_mail(self):
  original=builtins.__import__
  def trap(name,*a,**kw):
   if name.startswith('feature_mail_mount')or name=='integration.mail_mount_binding':raise AssertionError('OFF_IMPORT')
   return original(name,*a,**kw)
  with patch('builtins.__import__',side_effect=trap):app=self.runapp(provider=lambda:(_ for _ in ()).throw(AssertionError('OFF_PROVIDER')))
  self.assertEqual(app.wsgi_app({},None),[b'PUBLIC']);self.assertEqual(self.mounted,[])
 def test_true_no_provider_refuses_before_public(self):
  with self.assertRaises(binding.MailBindingRefused):self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},builder=lambda:(_ for _ in ()).throw(AssertionError('PUBLIC')))
 def test_mail_second_gate_before_provider(self):
  for v in [None,'false','TRUE']:
   env={'MERGED_MAIL_ENABLED':'true'}
   if v is not None:env['MAIL_V1_ENABLED']=v
   with self.assertRaises(ValueError):self.runapp(env,provider=lambda:(_ for _ in ()).throw(AssertionError()))
 def test_invalid_binding_refuses(self):
  for b in [True,replace(self.b,expires_at=100),replace(self.b,verified=(True,)*5+(1,)),replace(self.b,scope=('wrong',)),replace(self.b,secret='short')]:
   with self.assertRaises(ValueError):self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:b)
 def test_mount_private_only_and_expiry_preserves_public(self):
  app=self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:self.b)
  self.assertEqual(app.wsgi_app({'PATH_INFO':'/'},None),[b'PUBLIC']);self.assertEqual(app.wsgi_app({'PATH_INFO':'/internal/mail/v1/prepare'},None),[b'PRIVATE']);self.assertEqual(len(self.mounted),1)
  self.now=201;status=[];r=app.wsgi_app({'PATH_INFO':'/internal/mail/v1/prepare'},lambda s,h:status.append(s));self.assertEqual(status,['503 Service Unavailable']);self.assertIn(b'retry_send',r[0]);self.assertEqual(app.wsgi_app({'PATH_INFO':'/'},None),[b'PUBLIC'])
 def test_public_failure_closes_binding(self):
  with self.assertRaises(AssertionError):self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:self.b,builder=lambda:(_ for _ in ()).throw(AssertionError()))
  self.assertEqual(self.closed,[True])
 def test_mount_failure_closes_binding(self):
  self.mods['feature_mail_mount.composition']=mod(compose_private_mail=lambda *a,**kw:(_ for _ in ()).throw(ValueError()))
  with self.assertRaises(ValueError):self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:self.b)
  self.assertEqual(self.closed,[True])
 def test_collector_none_guard_exact_and_before_mailprovider(self):
  class EvidenceRefused(ValueError):pass
  self.mods['integration.collector197_runtime_evidence']=mod(EvidenceRefused=EvidenceRefused)
  with self.assertRaises(EvidenceRefused):self.runapp({'COLLECTION_ENABLED':'true','MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:(_ for _ in ()).throw(AssertionError('MAIL')))
 def test_provider_refreshes_expiry_same_capabilities(self):
  def provider():return replace(self.b,observed_at=self.now-1,expires_at=self.now+100)
  app=self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=provider)
  self.now=300;self.assertEqual(app.wsgi_app({'PATH_INFO':'/internal/mail/v1/prepare'},None),[b'PRIVATE'])
 def test_provider_changed_capability_refused(self):
  records=iter([self.b,replace(self.b,store=Store())]);app=self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:next(records))
  status=[];app.wsgi_app({'PATH_INFO':'/internal/mail/v1/prepare'},lambda s,h:status.append(s));self.assertEqual(status,['503 Service Unavailable'])
 def test_real_type_contract_and_policy_check(self):
  for store in [object(),type('WrongPolicy',(Store,),{'policy':'wrong'})()]:
   with self.assertRaises(binding.MailBindingRefused):self.runapp({'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},provider=lambda:replace(self.b,store=store))
 def test_collector_build_failure_closes_mail_binding(self):
  self.mods['integration.collector197_runtime_evidence']=mod(evidence_provider=lambda *a:object())
  self.mods['integration.collector197_http']=mod(build_collector_app=lambda *a,**kw:(_ for _ in ()).throw(ValueError('collector_failed')))
  with patch.dict(sys.modules,self.mods):
   with self.assertRaises(ValueError):entry.build_production_app({'COLLECTION_ENABLED':'true','MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'},lambda e:App(),runtime_evidence=lambda:None,mail_binding_provider=lambda:self.b,clock=lambda:100)
  self.assertEqual(self.closed,[True])
 def test_env_not_mutated_public_gets_mail_off(self):
  env={'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'};seen=[]
  with patch.dict(sys.modules,self.mods):entry.build_production_app(env,lambda e:(seen.append(e)or App()),mail_binding_provider=lambda:self.b,clock=lambda:100)
  self.assertEqual(env,{'MERGED_MAIL_ENABLED':'true','MAIL_V1_ENABLED':'true'});self.assertEqual(seen[0]['MERGED_MAIL_ENABLED'],'false')
if __name__=='__main__':unittest.main()
