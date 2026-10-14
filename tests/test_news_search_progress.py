import unittest,hashlib
from unittest.mock import Mock,patch
from integration import news_search_progress as s
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import LIVE,Client
from tests.test_news_pages185 import F,Store,rows
from integration.news_pages import WholeGeoPages,PageExpired
from integration.public_live_builder import sanitize_public_geo_rows
class Tests(unittest.TestCase):
 def app(self,on=True):
  env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED='true' if on else 'false')
  app=build_public_live_preview(env,client_factory=lambda *a,**k:Client());self.addCleanup(app.extensions['whole_news_pages'].close);return app
 def test_OFF_bytes(self):
  a=self.app(False);env=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false');b=build_public_live_preview(env,client_factory=lambda *a,**k:Client());self.addCleanup(b.extensions['whole_news_pages'].close)
  for path in ['/workspace',s.PATH,s.WORKSPACE]:
   for method in ['get','head']:
    x=getattr(a.test_client(),method)(path,base_url=LIVE['PREVIEW_ORIGIN']);y=getattr(b.test_client(),method)(path,base_url=LIVE['PREVIEW_ORIGIN']);self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
 def test_enabled_served_copy_only(self):
  c=self.app().test_client();base=LIVE['PREVIEW_ORIGIN']
  self.assertIn('120-second idle',c.get('/workspace',base_url=base).text)
  self.assertIn('Scanned ',c.get(s.PATH,base_url=base).text);self.assertIn('1250000',c.get(s.WORKSPACE,base_url=base).text)
  for name,pin in s.PINS.items():self.assertEqual(hashlib.sha256((s.ROOT/name).read_bytes()).hexdigest(),pin)
  self.assertNotIn('close',str([r.rule for r in self.app().url_map.iter_rules()]))
 def test_gates_before_factory(self):
  for extra in [{'PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED':'TRUE'},{'PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED':'true','PUBLIC_NEWS_FULL_PAGES_ENABLED':'false'}]:
   with self.assertRaises(ValueError):build_public_live_preview(dict(LIVE,**extra),client_factory=lambda *a,**k:self.fail('factory'))
 def test_mounted_type_required(self):
  from integration.news_api import create_app
  with self.assertRaises(ValueError):s.install(create_app())
 def test_all_continuation_bindings(self):
  p=WholeGeoPages(Store(rows(150)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(p.close);d=p.page(F)
  for key,value in [('query','different'),('category','TRADE'),('country','IN'),('sort','title')]:
   with self.assertRaises(PageExpired):p.page(dict(F,**{key:value}),25,d['next_cursor'])
  with self.assertRaises(PageExpired):p.page(F,26,d['next_cursor'])
 def test_old_history(self):
  rr=rows(2025);rr[-1]['title']='Unique old needle';store=Store(rr);p=WholeGeoPages(store,sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(p.close);f=dict(F,query='needle');d=p.page(f);self.assertEqual((d['scanned_this_page'],d['items']),(1000,[]));d=p.page(f,25,d['next_cursor']);self.assertEqual(d['items'],[]);d=p.page(f,25,d['next_cursor']);self.assertTrue(d['exhausted']);self.assertEqual(len(d['items']),1);self.assertEqual(len(store.calls),1)

 def test_combined_transforms_order(self):
  flags=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED='true',PUBLIC_CODE_NEWS_ENABLED='true',PUBLIC_CODE_NEWS_SCOPE_REVIEWED='true',PUBLIC_RELATIONSHIP_NAV_ENABLED='true',PUBLIC_TARIFF_EVIDENCE_ENABLED='true',PUBLIC_WEEKLY_PDF_ENABLED='true',PUBLIC_WEEKLY_FULL_STORE_ENABLED='true',PUBLIC_AI_ANSWERS_ENABLED='true',PUBLIC_MAP_ENABLED='true',PUBLIC_MAP_M2_ENABLED='true',PUBLIC_BRICS_STREAMS_ENABLED='true')
  a=build_public_live_preview(flags,client_factory=lambda *a,**k:Client());self.addCleanup(a.extensions['whole_news_pages'].close);c=a.test_client();x=c.get(s.WORKSPACE,base_url=LIVE['PREVIEW_ORIGIN']);y=c.get(s.WORKSPACE,base_url=LIVE['PREVIEW_ORIGIN']);self.assertEqual(x.data,y.data);self.assertIn('attachReportedCodes',x.text);self.assertIn('1250000',x.text);self.assertNotIn('/api/related-news',x.text);self.assertEqual(x.headers['Cache-Control'],'no-store')
 def test_startup_seam_drift(self):
  with patch.object(s,'PINS',{}),patch.object(s.Path,'read_text',return_value='changed'),self.assertRaises(ValueError):s.prepare({s.FLAG:'true','PUBLIC_NEWS_FULL_PAGES_ENABLED':'true'})
 def test_mutants(self):
  from pathlib import Path
  source=Path(s.__file__).read_text()
  mutants=[("r.headers['Cache-Control']='no-store'","r.headers['Cache-Control']='public'","cache"),("hooks.insert(0,served)","hooks.append(served)","order"),("if text.count(SEAM)!=1:raise ValueError('Search byte-bound seam drift')","if False:raise ValueError('Search byte-bound seam drift')","request"),("if (ROOT/'integration/ui/workspace.js').read_text().count(SEAM)!=1:raise ValueError('Search byte-bound seam drift')","if False:raise ValueError('Search byte-bound seam drift')","prepare"),("and env.get('PUBLIC_NEWS_FULL_PAGES_ENABLED')!='true'","and False","dependency"),("if value not in ('true','false'):","if False:","exact")]
  for old,new,kind in mutants:
   self.assertIn(old,source);ns={'__name__':'s1mutant','__file__':s.__file__};exec(compile(source.replace(old,new),kind,'exec'),ns)
   if kind=='dependency':self.assertTrue(ns['enabled']({s.FLAG:'true'}));continue
   if kind=='exact':self.assertFalse(ns['enabled']({s.FLAG:'TRUE'}));continue
   if kind=='prepare':
    # isolate seam validator from the independent pin gate
    ns['PINS']={}
    with patch.object(s.Path,'read_text',return_value='drift'):self.assertTrue(ns['prepare']({s.FLAG:'true','PUBLIC_NEWS_FULL_PAGES_ENABLED':'true'}))
    continue
   from integration.news_api import create_app
   from integration.news_pages import WholeGeoPages
   pages=WholeGeoPages(Store(rows(1)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(pages.close);a=create_app(authorize=lambda _:True,full_news_pages=pages);a.extensions['whole_news_pages']=pages
   # Preexisting rewriting hook models a protected server-side transform.
   from flask import request
   @a.after_request
   def rewrite(r):
    if request.path==s.WORKSPACE:r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace(s.SEAM,'  return null;'))
    return r
   ns['install'](a)
   a.testing=True;c=a.test_client()
   if kind=='request':self.assertEqual(c.get(s.WORKSPACE).status_code,200)
   elif kind=='order':self.assertEqual(c.get(s.WORKSPACE).status_code,200)
   else:self.assertEqual(c.get(s.PATH).headers['Cache-Control'],'public')
  # Production refuses response seam drift rather than silently bypassing the cap.
  a=self.app();a.testing=True
  @a.after_request
  def drift(r):
   from flask import request
   if request.path==s.WORKSPACE:r.direct_passthrough=False;r.set_data(r.get_data(as_text=True).replace(s.SEAM,'  return null;'))
   return r
  with self.assertRaises(ValueError):a.test_client().get(s.WORKSPACE,base_url=LIVE['PREVIEW_ORIGIN'])
