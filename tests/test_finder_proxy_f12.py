import json,unittest,hashlib
from unittest.mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Response
from integration import finder_proxy_f12 as m,finder_composition_f9 as f9,finder_device_f10 as f10
from integration.finder_proxy_f12.evidence import Evidence
from integration.public_preview_builder import build_public_preview
from integration.finder198_receipts import ProxyReceiptBudget
from integration.finder198_transport import FixedProxyTransport
from integration.finder198_connector import ModelEntry
from integration.accounts.service import AccountService
from integration.accounts.store import MemoryStore
from tests import test_finder_composition_f9 as fixture
from tests.test_finder198ba import Collection,R
from tests.test_finder198a import evidence,O,PW
from tests.test_code_news_coverage_binding_prep import ORIGIN as SAMPLE_ORIGIN
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  fixture.Tests.setUpClass();cls.env=dict(fixture.Tests.env,**{m.FLAG:'true','PUBLIC_FINDER_DATA_REPORT_ENABLED':'true',f10.FLAG:'true'})
  cls.selection=f9.prepare(cls.env,fixture.Tests.binding);cls.e=Evidence(cls.selection)
 @classmethod
 def tearDownClass(cls):fixture.Tests.tearDownClass()
 def setUp(self):
  self.c=Collection();self.c.doc.update(schema=2,receipts=[]);self.b=ProxyReceiptBudget(self.c,review=R);self.t=FixedProxyTransport({'FINDER_PROXY_BASE_URL':'https://hsn-ai-proxy.onrender.com','FINDER_PROXY_SECRET':'x'*48},enabled=True)
  self.handler=m.FeatureBroker(self.e,self.b,self.t,lambda:101,provider='groq',model='fixture-reviewed',permission=m.FeaturePermission('fixture-disclosure','fixture-spend','fixture-retention','fixture-no-paid-fallback',100,200))
 def ids(self,code='090121',system='HS'):return {'system':system,'edition':dict(self.selection.editions)[system],'code':code}
 def data(self,feature='plain_words'):
  return {'nonce':'n'*24,'feature':feature,'question':'coffee'if feature=='classification_context'else'','candidates':[self.ids()]+([self.ids('090111')]if feature=='code_comparison'else[])}
 def request(self,data):
  from werkzeug.test import EnvironBuilder
  from werkzeug.wrappers import Request
  return self.handler(Request(EnvironBuilder(path=m.PATH,method='POST',json=data).get_environ()),'d'*64)
 def catalog(self):return patch('integration.finder198_connector.MODEL_CATALOG',(ModelEntry('groq','fixture-reviewed','fixture-owner','fixture-vendor','fixture-entitlement',100,200),))
 def wire(self):
  app=build_public_preview(self.env,finder_candidate_binding=fixture.Tests.binding);self.addCleanup(app.extensions['finder_composition_close_f9'])
  # Handler evidence must bind THIS installed selection, not an equal other app.
  h=m.FeatureBroker(Evidence(f9.selected(app)),self.b,self.t,lambda:101,provider='groq',model='fixture-reviewed',permission=m.FeaturePermission('fixture-disclosure','fixture-spend','fixture-retention','fixture-no-paid-fallback',100,200))
  store=MemoryStore();service=AccountService(store,b'x'*48,lambda:101,signup_mode='closed',allowed_origins=[O]);store.create_account('alice',{'uid':'alice','password':service.hasher.hash(PW),'created':100,'pwv':0},None,50)
  m.activate(app,handler=h,service=service,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,clock=lambda:101)
  return app,Client(app,Response),store
 def test_default_suite_javascript_client_panel_and_bridges(self):
  import subprocess
  from pathlib import Path
  for name in ('finder_proxy_f12_client.mjs','finder_proxy_f12_ui.mjs'):
   result=subprocess.run(['node',str(Path(__file__).with_name(name))],capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,0,name+'\n'+result.stdout+'\n'+result.stderr)
 def test_exact_flags_off_no_reads(self):
  with patch.object(f9.Selection,'verify',side_effect=AssertionError):self.assertFalse(m.enabled({}))
  for v in ('TRUE','1',''):
   with self.assertRaises(ValueError):m.enabled({m.FLAG:v})
  with self.assertRaises(ValueError):m.enabled({m.FLAG:'true'})
 def test_default_empty_catalog_no_budget_no_dispatch(self):
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(self.request(self.data()).status_code,409)
  self.assertEqual(self.c.writes,0)
 def test_permission_gap_or_expiry_precedes_budget_and_dispatch(self):
  for permission in (None,m.FeaturePermission('fixture-disclosure','fixture-spend','fixture-retention','fixture-no-paid',0,100)):
   handler=m.FeatureBroker(self.e,self.b,self.t,lambda:101,provider='groq',model='fixture-reviewed',permission=permission)
   from werkzeug.test import EnvironBuilder
   from werkzeug.wrappers import Request
   with self.catalog(),patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(handler(Request(EnvironBuilder(path=m.PATH,method='POST',json=self.data()).get_environ()),'d'*64).status_code,409)
  self.assertEqual(self.c.writes,0)
 def test_closed_payload_no_private_evidence_models_or_urls(self):
  for extra in ('prompt','evidence','provider','model','url','notes'):
   with self.assertRaises(ValueError):m.validate_feature(dict(self.data(),**{extra:'no'}))
  for data in (dict(self.data(),question='caller prompt'),dict(self.data(),candidates=[]),dict(self.data(),feature='unknown')):
   with self.assertRaises(ValueError):m.validate_feature(data)
 def test_server_owned_selected_source_all_features_and_one_request(self):
  raw=json.dumps({'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':json.dumps({'answer':'SIMULATED TEST TEXT','citations':['S1']})}}]}).encode()
  with self.catalog(),patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':raw})as call:
   r=self.request(self.data());self.assertEqual(r.status_code,200,r.get_data(as_text=True));self.assertEqual(r.json['answer'],'SIMULATED TEST TEXT');self.assertIn('not independently checked',r.json['source_notice']);self.assertEqual(call.call_count,1)
   plan,body=call.call_args.args;self.assertIn('hsn-ai-proxy',plan['base']);self.assertNotIn(b'notes',body);self.assertIn(b'preserved_snapshot',body)
   self.assertEqual(self.request(self.data()).status_code,409);self.assertEqual(call.call_count,1)
  for feature in m.FEATURES:
   data=self.data(feature);e=self.e.project(data['candidates'],feature);self.assertTrue(e);self.assertLessEqual(len(e),4);self.assertTrue(all(len(x['text'])<=2000 for x in e))
 def test_bad_output_and_unknown_hold_no_retry(self):
  with self.catalog(),patch.object(FixedProxyTransport,'execute',side_effect=ValueError)as call:
   self.assertEqual(self.request(self.data()).status_code,409);self.assertEqual(self.request(dict(self.data(),nonce='m'*24)).status_code,409);self.assertEqual(call.call_count,1)
  self.assertIsNotNone(self.c.doc['active'])
 def test_wrong_edition_or_absent_identity_no_budget(self):
  for data in (dict(self.ids(),edition='wrong'),self.ids('999999999999')):
   with self.catalog(),patch.object(FixedProxyTransport,'execute',side_effect=AssertionError):self.assertEqual(self.request(dict(self.data(),candidates=[data])).status_code,409)
  self.assertEqual(self.c.writes,0)
 def test_authenticated_origin_csrf_and_revoked_session_before_budget(self):
  app,c,store=self.wire()
  self.assertEqual(c.post(m.PATH,base_url=O,json=self.data(),headers={'Origin':O}).status_code,401)
  pre=c.get('/account/preauth',base_url=O).json['csrf'];r=c.post('/account/login',base_url=O,json={'username':'alice','password':PW,'csrf':pre},headers={'Origin':O});csrf=r.json['csrf']
  self.assertEqual(c.post(m.PATH,base_url=O,json=self.data(),headers={'Origin':O,'X-CSRF-Token':'wrong'}).status_code,403)
  self.assertEqual(c.post(m.PATH,base_url=O,json=self.data(),headers={'Origin':'https://evil.test','X-CSRF-Token':csrf}).status_code,403)
  store.sessions.clear();self.assertEqual(c.post(m.PATH,base_url=O,json=self.data(),headers={'Origin':O,'X-CSRF-Token':csrf}).status_code,401);self.assertEqual(self.c.writes,0)
 def test_enabled_held_mount_and_device_unchanged(self):
  app=build_public_preview(self.env,finder_candidate_binding=fixture.Tests.binding);self.addCleanup(app.extensions['finder_composition_close_f9']);c=app.test_client();s=f9.selected(app);d=app.extensions[f10.KEY]
  r=c.get('/workspace/finder/offline.html',base_url=SAMPLE_ORIGIN);self.assertEqual(r.status_code,200);self.assertIn('finder-proxy-f12-request',r.text);self.assertIn('Make the data PDF report',r.text);self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy'])
  cached=c.get(d.base+'snapshot.html',base_url=SAMPLE_ORIGIN);self.assertEqual(cached.data,s.rendered.encode());self.assertNotIn('finder-proxy-f12-request',cached.text)
  self.assertEqual(c.post(m.PATH,base_url=SAMPLE_ORIGIN,json=self.data(),headers={'Origin':SAMPLE_ORIGIN}).status_code,409)
  for path in m.ASSETS:self.assertEqual(c.get(path,base_url=SAMPLE_ORIGIN).status_code,200,path)
