import hashlib
import unittest
from unittest.mock import Mock,patch
from flask import Flask
from integration import news_finder_navigation_prep as nav
from integration.finder_identity_proof_prep import FinderProof,normalized_description
from integration.code_news_coverage_broker_prep import CoverageBroker
from integration.code_news_parent_prep import ResolveQuota
from integration.code_news_disk import DiskLinks
from integration.code_news_links import Links
from integration.news_api import create_app,offline_finder_snapshot
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows,build_public_live_preview
from tests.test_news_pages185 import Store,rows
from tests.test_code_news_coverage_binding_prep import LIVE,Client,ORIGIN,Binding
from integration.code_news_coverage_route_prep import install
from integration.code_news_coverage_contract_prep import serialize
from pathlib import Path
T={'system':'HS','edition':'2022','code':'090121','description':'Coffee; roasted, not decaffeinated'}
P={k:T[k]for k in ('system','edition','code')}
HEADERS={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
class Tests(unittest.TestCase):
 def proof(self,target=T):
  return Mock(bound=Mock(return_value=dict(target,state='bound_preserved_snapshot',edition_verified=False,normalized_description_sha256=hashlib.sha256(normalized_description(target['description']).encode()).hexdigest())))
 def make(self,proof=True,n=60):
  self.now=0;data=rows(n)
  for r in data:r.update(title='HS090121; '*32,summary='')
  self.pages=WholeGeoPages(Store(data),sanitize_public_geo_rows,verified=True,clock=lambda:self.now,start_cleaner=False);self.addCleanup(self.pages.close)
  self.quota=ResolveQuota();self.fake=self.proof() if proof is True else proof
  self.b=CoverageBroker(self.pages,Links([T],[]),'a'*64,'v1',resolve_quota=self.quota,finder_proof=self.fake)
  return self.b
 def next(self,r):return self.b.page(scope=r['next_cursor'],manifest='a'*64,matcher_version='v1')
 def test_once_per_start_continuation_replay_and_empty(self):
  b=self.make();a,status=b.page(P);self.assertEqual(status,200);self.assertEqual(len(a['items']),25);self.assertEqual(len(a['items'][0]['relationships']),32)
  second,_=self.next(a);replay,_=self.next(a);last,_=self.next(second)
  self.fake.bound.assert_called_once_with('HS','2022','090121');self.assertEqual(self.quota.attempts,1)
  self.assertEqual(second,replay);self.assertEqual(last['finder_navigation']['state'],'bound')
  b=self.make();self.pages.store.rows=[];a,_=b.page(P);self.assertEqual(a['items'],[]);self.fake.bound.assert_called_once()
 def test_failed_resolve_and_off(self):
  b=self.make();b.page(dict(P,code='000000'));self.fake.bound.assert_not_called();self.assertEqual(self.quota.attempts,1)
  b=self.make(proof=None)
  with patch('integration.news_finder_navigation_prep.prepare',side_effect=AssertionError('OFF proof')):
   result,status=b.page(P)
  self.assertEqual(status,200);self.assertNotIn('finder_navigation',result);self.assertEqual(self.quota.attempts,1)
 def test_hook_failure_never_scan_failure(self):
  for failure in [RuntimeError('private'),TimeoutError(),None,'bad',{},dict(T,code='1006',state='bound_preserved_snapshot',edition_verified=False,normalized_description_sha256=hashlib.sha256(normalized_description(T['description']).encode()).hexdigest())]:
   fake=self.proof()
   if isinstance(failure,Exception):fake.bound.side_effect=failure
   else:fake.bound.return_value=failure
   b=self.make(proof=fake);r,status=b.page(P)
   self.assertEqual(status,200);self.assertEqual(r['finder_navigation']['state'],'unavailable');self.assertEqual(self.quota.attempts,1);self.assertEqual(len(b.ledger.rows),1)
 def test_hook_outside_Newslock_reserve_refusal_no_store(self):
  fake=self.proof();b=self.make(proof=fake)
  original=fake.bound.side_effect
  def bound(*args):self.assertFalse(self.pages.lock.locked());return fake.bound.return_value
  fake.bound.side_effect=bound
  for _ in range(4):self.assertEqual(b.page(P)[1],200)
  self.assertEqual(b.page(P)[1],429);self.assertEqual(len(b.ledger.rows),4);self.assertEqual(len(b.contexts),4);self.assertEqual(fake.bound.call_count,5);self.assertEqual(self.quota.attempts,5)
  self.assertFalse(hasattr(b,'prepared'))
  for _ in range(5):b.page(P)
  self.assertEqual(b.page(P)[1],429);self.assertEqual(fake.bound.call_count,10)
 def test_release_prune(self):
  b=self.make();b.page(P);key=next(iter(b.ledger.rows));b.ledger.drop(key);b._prune_locked();self.assertEqual(b.contexts,{});self.assertEqual(b.replies,{})
 def test_release_TTL(self):
  b=self.make();a,_=b.page(P);self.now=121;self.assertEqual(self.next(a)[1],410);self.assertEqual(b.ledger.rows,{});self.assertEqual(b.contexts,{})
 def test_release_hardTTL(self):
  b=self.make();a,_=b.page(P);self.now=1799
  for row in b.ledger.rows.values():row['used']=1799
  for row in self.pages.streams.values():row['used']=1799
  self.now=1800;self.assertEqual(self.next(a)[1],410);self.assertEqual(b.ledger.rows,{})
 def test_release_close_and_browser_abort_TTL(self):
  b=self.make();a,_=b.page(P)
  # Browser abort has no remote-cancel effect. Server binding remains until TTL.
  self.assertEqual(len(b.ledger.rows),1);self.now=121;self.pages._expire();b._prune_locked();self.assertEqual(b.ledger.rows,{})
  b=self.make();b.page(P);self.pages.close();self.assertEqual(b.ledger.rows,{})
  self.assertTrue(all('finder_navigation' not in reply['body']for reply in b.replies.values()))
 def test_mounted_real_view_gethead_private_and_tampered(self):
  app=create_app(authorize=lambda r:True);self.assertFalse(nav.mounted(app));nav.install_mount(app);self.assertTrue(nav.mounted(app))
  for method in ('get','head'):self.assertEqual(getattr(app.test_client(),method)(nav.PATH).status_code,200)
  r=app.test_client().get(nav.PATH);self.assertIn("connect-src 'none'",r.headers['Content-Security-Policy'])
  app.view_functions['offline_finder_snapshot']=lambda: 'dummy';self.assertFalse(nav.mounted(app))
  app.view_functions['offline_finder_snapshot']=offline_finder_snapshot
  app.extensions[nav.MARKER]=nav.OfflineMount(offline_finder_snapshot,'offline_finder_snapshot',nav.PATH,False);self.assertFalse(nav.mounted(app))
  app.extensions[nav.MARKER]={'path':nav.PATH};self.assertFalse(nav.mounted(app))
  app=Flask('post');app.add_url_rule(nav.PATH,'offline_finder_snapshot',offline_finder_snapshot,methods=['POST']);nav.install_mount(app);self.assertFalse(nav.mounted(app))
 def test_route_replay_mount_removed_nohref(self):
  b=self.make();app=create_app(authorize=lambda r:True);nav.install_mount(app);install(app,ORIGIN,b,{'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true',nav.FLAG:'true'})
  c=app.test_client();a=c.post('/api/code-news-coverage',json=P,base_url=ORIGIN,headers=HEADERS);self.assertEqual(a.status_code,200);self.assertEqual(a.json['finder_navigation']['url'],nav.PATH+'#code=0:090121')
  req={k:a.json[k]for k in ('scope','manifest','matcher_version')};r=c.post('/api/code-news-coverage',json=req,base_url=ORIGIN,headers=HEADERS);self.assertEqual(r.json['finder_navigation']['state'],'ready')
  app.extensions.pop(nav.MARKER);r=c.post('/api/code-news-coverage',json=req,base_url=ORIGIN,headers=HEADERS);self.assertIsNone(r.json['finder_navigation']['url']);self.assertEqual(r.json['finder_navigation']['label'],'Finder link unavailable');self.fake.bound.assert_called_once()
 def test_real_excluded_and_wrong_edition(self):
  root=Path(__file__).resolve().parents[1];proof=FinderProof();index=DiskLinks(root/'integration/code_news_index');self.addCleanup(proof.close);self.addCleanup(index.close)
  for system,edition,code in [('HS','2022','TOTAL'),('IN',nav.EDITIONS['IN'],'2307 00'),('IN',nav.EDITIONS['IN'],'2514 00'),('HS','2022','09'),('HS','2017','090121')]:
   self.assertIsNone(proof.bound(system,edition,code));self.assertEqual(nav.prepare(proof,dict(system=system,edition=edition,code=code,description='x'))['state'],'unavailable')
 def test_max_cap_includes_navigation(self):
  b=self.make();app=create_app(authorize=lambda r:True);nav.install_mount(app);install(app,ORIGIN,b,{'PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED':'true',nav.FLAG:'true'})
  r=app.test_client().post('/api/code-news-coverage',json=P,base_url=ORIGIN,headers=HEADERS);self.assertLessEqual(len(r.data),524288);self.assertEqual(len(r.json['items']),25)
  body,status=b.page(P)
  # Valid near-limit contract: 30 legal evidence strings share the fill, not
  # an overlong coverage_message that an earlier validator would reject.
  body['items']=body['items'][:1];body['items'][0]['relationships']=body['items'][0]['relationships'][:30]
  for relationship in body['items'][0]['relationships']:relationship['evidence']=''
  base=len(serialize(body));fill=524288-base-10
  for i,relationship in enumerate(body['items'][0]['relationships']):relationship['evidence']='x'*(fill//30+(1 if i<fill%30 else 0))
  self.assertLessEqual(max(len(x['evidence'])for x in body['items'][0]['relationships']),18001)
  with patch.object(b,'page',return_value=(body,200)):
   self.assertEqual(app.test_client().post('/api/code-news-coverage',json=P,base_url=ORIGIN,headers=HEADERS).status_code,503)
 def test_builder_ON_actual_proof_and_shutdown(self):
  client=Client()
  for r in client.store.rows:r.update(title='HS090121;',summary='')
  app=build_public_live_preview(dict(LIVE,**{nav.FLAG:'true'}),client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:Binding(True,True,True,True,'fixture-owner','fixture-deployment'))
  broker=app.extensions['code_news_coverage_broker'];self.addCleanup(app.extensions['coverage_close'])
  r=app.test_client().post('/api/code-news-coverage',base_url=ORIGIN,json=P,headers=HEADERS)
  self.assertEqual(r.status_code,200);self.assertEqual(r.json['finder_navigation']['state'],'ready')
  app.extensions['coverage_close']();self.assertTrue(broker.finder_proof.closed);self.assertEqual(broker.ledger.rows,{})
 def test_OFF_wire_equals_prior_broker_byte_for_byte(self):
  b=self.make(proof=None);body,status=b.page(P)
  self.assertNotIn('finder_navigation',body)
  self.assertNotIn('finder_evidence',next(iter(b.ledger.rows.values()))['binding'])
  from integration.code_news_coverage_route_prep import validate
  self.assertEqual(serialize(body),serialize(validate(body,status)[0]))
 def test_marker_route_removed_or_missing_HEAD_and_pin_drift(self):
  app=create_app(authorize=lambda r:True);nav.install_mount(app)
  with patch.object(nav,'VIEW_SHA','0'*64):self.assertFalse(nav.mounted(app))
  for rule in app.url_map.iter_rules():
   if rule.rule==nav.PATH:rule.methods.discard('HEAD')
  self.assertFalse(nav.mounted(app))
 def test_unverified_edition_required(self):
  fake=self.proof();fake.bound.return_value['edition_verified']=True
  self.assertEqual(nav.prepare(fake,T)['state'],'unavailable')
 def test_exact_server_labels_and_public_allow_scope(self):
  from integration.public_preview_builder import READ_PATHS
  self.assertIn(nav.PATH,READ_PATHS)
  app=create_app(authorize=lambda r:True);nav.install_mount(app)
  expected={'HS':'Open in the preserved Finder snapshot (labeled HS 2022)',
            'IN':'Open in the preserved Finder snapshot (India HSN label)'}
  for system,label in expected.items():
   t=dict(P,system=system,edition=nav.EDITIONS[system])
   decorated=nav.decorate(app,dict(state='bound',target=t))
   self.assertEqual(decorated['state'],'ready');self.assertEqual(decorated['label'],label)
   self.assertNotIn('same',decorated['label'].lower());self.assertNotIn('verified',decorated['label'].lower())
 def test_description_drift(self):
  fake=self.proof();self.assertEqual(nav.prepare(fake,dict(T,description='Other'))['state'],'unavailable')
 def test_strict_flags_and_evidence(self):
  self.assertFalse(nav.enabled({}));self.assertTrue(nav.enabled({nav.FLAG:'true'}))
  for flag in ['yes','1',True]:
   with self.assertRaises(ValueError):nav.enabled({nav.FLAG:flag})
  for evidence in [None,{},dict(state='bound',target=None),dict(state='bound',target=dict(P,edition='2012'))]:self.assertFalse(nav.valid_evidence(evidence))
 def test_builder_OFF_no_proof_import_bytes_and_on_close(self):
  client=Client();env=dict(LIVE)
  with patch('integration.finder_identity_proof_prep.FinderProof',side_effect=AssertionError('OFF')):
   app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:Binding(True,True,True,True,'fixture-owner','fixture-deployment'))
  self.addCleanup(app.extensions['coverage_close']);self.assertTrue(nav.mounted(app))
  c=app.test_client();self.assertEqual(c.get('/workspace/assets/code_news_coverage.js',base_url=ORIGIN).data,(Path(__file__).resolve().parents[1]/'integration/ui/code_news_coverage.js').read_bytes())
  self.assertNotIn('data-finder-links',c.get('/workspace/code-news-coverage',base_url=ORIGIN).text)

if __name__=='__main__':unittest.main()
