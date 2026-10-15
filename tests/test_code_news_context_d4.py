import unittest,copy,json,hashlib
from pathlib import Path
from unittest.mock import Mock,patch
from flask import Flask
from integration import code_news_context_d4 as m
from integration.code_news_coverage_binding_prep import Binding
from integration.code_news_links import Links
from integration.code_news_parent_prep import ResolveQuota
from integration.news_pages import WholeGeoPages
from integration.public_live_builder import sanitize_public_geo_rows,build_public_live_preview
from tests.test_news_pages185 import Store,rows
from tests.test_code_news_coverage_binding_prep import LIVE,ORIGIN,Client
from integration.code_news_coverage_route_prep import install as route_install,Invalid
ENV={**LIVE,m.FLAG:'true'}
TARGET={'system':'HS','edition':'2022','code':'8517','description':'Phones'}
ARTICLE={'project':'geo','article_key':'a'*64,'title':'HS 8517; phone news','summary':'Trade mention','source':'Fixture source','url':'https://news.example/article','secret':'PRIVATE'}
class Tests(unittest.TestCase):
 def broker(self,values):
  p=WholeGeoPages(Store(values),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(p.close)
  return m.ContextBroker(p,Links([TARGET],[]),'a'*64,'fixture',resolve_quota=ResolveQuota())
 def bind(self):return Binding(True,True,True,True,'fixture-owner','fixture-deployment')
 def test_flags_pins_no_factory(self):
  self.assertFalse(m.prepare({}));self.assertTrue(m.prepare(ENV))
  for v in ['TRUE','yes','1','']:
   with self.assertRaises(ValueError):m.prepare({**ENV,m.FLAG:v})
  for k in ['PUBLIC_NEWS_READ_ENABLED','PUBLIC_NEWS_FULL_PAGES_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED']:
   f=Mock()
   with self.assertRaises(ValueError):build_public_live_preview({**ENV,k:'false'},client_factory=f)
   f.assert_not_called()
 def test_safe_closed_source_context(self):
  x=m.article_context(ARTICLE);self.assertEqual(x['title'],ARTICLE['title']);self.assertEqual(set(x),m.FIELDS);self.assertNotIn('secret',x)
  for u in ['javascript:alert(1)','http://news.example/a','https://user:pass@news.example/a','https://news.example:444/a','https://news.example/\nprivate','https://news.example/\\private','https://news.example/a b',None]:
   self.assertEqual(m.article_context({**ARTICLE,'url':u})['state'],'unavailable')
  for row in [{**ARTICLE,'project':'brics'},{**ARTICLE,'title':'x'*2001},{**ARTICLE,'source':{}},{**ARTICLE,'title':'\x00x'}]:self.assertEqual(m.article_context(row)['state'],'unavailable')
  for x in [{**m.article_context(ARTICLE),'secret':'PRIVATE'},{**m.article_context(ARTICLE),'url':'https://user@evil.test/a'},{'state':'unavailable','project':'geo','title':'x','source':'','url':None}]:
   with self.assertRaises(Invalid):m.check_context(x)
 def test_same_page_context_no_extra_read_and_wire_validation(self):
  source=rows(1);source[0].update(title=ARTICLE['title'],summary='',source=ARTICLE['source'],url=ARTICLE['url']);b=self.broker(source);body,status=b.page({k:TARGET[k]for k in ('system','edition','code')})
  self.assertEqual(status,200);self.assertEqual(len(b.pages.store.calls),1);self.assertEqual(len(body['items']),1);c=body['items'][0]['article_context'];self.assertEqual(c['title'],ARTICLE['title']);self.assertEqual(c['url'],ARTICLE['url']);self.assertEqual(m.validate(body,status)[0],body)
  bad=copy.deepcopy(body);bad['items'][0]['article_context']['private']='SECRET'
  with self.assertRaises(Invalid):m.validate(bad,status)
  bad=copy.deepcopy(body);del bad['items'][0]['article_context']
  with self.assertRaises(Invalid):m.validate(bad,status)
 def test_carry_replay_context_matches_article(self):
  source=rows(60)
  for n,r in enumerate(source):r.update(title=f'HS 8517; Article {n}',source='Fixture',url=f'https://news.example/{n}',summary='')
  b=self.broker(source);r,status=b.page({k:TARGET[k]for k in ('system','edition','code')});first=r;allitems=list(r['items'])
  args={k:r[k]for k in ('scope','manifest','matcher_version')};r,status=b.page(**args);repeat,status=b.page(**args);self.assertEqual(r,repeat);allitems+=r['items'];r,status=b.page(**{k:r[k]for k in ('scope','manifest','matcher_version')});allitems+=r['items'];self.assertEqual(len(allitems),60);self.assertEqual(len(b.pages.store.calls),1)
  for i in allitems:
   self.assertTrue(i['article_context']['title'].startswith('HS 8517; Article '));self.assertTrue(i['article_context']['url'].startswith('https://news.example/'));m.check_context(i['article_context'])
 def test_invalid_url_does_not_remove_reported_relationship(self):
  b=self.broker([]);b._initialize_locked('unit');b.ledger.rows['unit']={'binding':{'target':TARGET},'parent':None}
  r,done=b._finish_locked('unit',{'items':[{**ARTICLE,'url':'javascript:alert(1)'}],'exhausted':True});self.assertEqual(r['items'][0]['article_context']['state'],'unavailable');self.assertTrue(r['items'][0]['relationships'])
 def test_UI_both_variants_and_no_unsafe_html(self):
  root=Path(__file__).resolve().parents[1]
  for n in ['code_news_coverage.js','code_news_finder_navigation.js']:
   s=m.transform((root/'integration/ui'/n).read_text());self.assertIn("a.rel='noopener noreferrer'",s);self.assertIn("a.target='_blank'",s);self.assertIn("a=node('a',context.title)",s);self.assertIn('n.textContent=text',s);self.assertIn("u.protocol!=='https:'",s);self.assertIn(r'/[\s\\]/.test(c.url)',s);self.assertIn('c.url.length>2048',s);self.assertNotIn('.innerHTML',s)
  with self.assertRaises(ValueError):m.transform('unknown JS')
 def test_builder_uses_context_broker_only_when_flag_on(self):
  for flag in ['false','true']:
   c=Client()
   for r in c.store.rows:r.update(title='HS8517;',summary='',source='Fixture',url='https://news.example/story')
   a=build_public_live_preview({**ENV,m.FLAG:flag},client_factory=lambda *a,**k:c,coverage_binding_provider=self.bind);self.addCleanup(a.extensions['coverage_close']);b=a.extensions['code_news_coverage_broker'];self.assertEqual(type(b)is m.ContextBroker,flag=='true')
   t=a.test_client();h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'};r=t.post('/api/code-news-coverage',base_url=ORIGIN,headers=h,json={'system':'HS','edition':'2022','code':'8517'});self.assertEqual(r.status_code,200);self.assertEqual('article_context'in r.json['items'][0],flag=='true');s=t.get('/workspace/assets/code_news_coverage.js',base_url=ORIGIN).text;self.assertEqual('const context=item.article_context'in s,flag=='true')
 def test_pins_extra_missing_drift_and_preview_rejection(self):
  from integration.public_preview_builder import build_public_preview
  pins=json.loads((m.ROOT/'integration/code_news_context_d4/pins.json').read_text())
  for q in [{**pins,'extra':'a'*64},{k:v for k,v in pins.items()if k!=next(iter(pins))},{**pins,next(iter(pins)):'0'*64}]:
   with patch.object(m.json,'loads',return_value=q),self.assertRaises(ValueError):m.prepare(ENV)
  f=Mock()
  from tests.test_code_news_coverage_binding_prep import SAMPLE
  valid_preview={**SAMPLE,**{k:'true'for k in ('PUBLIC_NEWS_READ_ENABLED','PUBLIC_NEWS_FULL_PAGES_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED','PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED')},m.FLAG:'true'}
  with self.assertRaisesRegex(ValueError,'^Source context requires reviewed live composition$'):build_public_preview(valid_preview,client_factory=f)
  f.assert_not_called()
 def test_ambiguous_missing_and_payload_cap(self):
  for values in [[ARTICLE,{**ARTICLE,'title':'Another title'}],[{'article_key':'a'*64,'title':'HS 8517;','summary':''}]]:
   b=self.broker([]);b._initialize_locked('unit');b.ledger.rows['unit']={'binding':{'target':TARGET},'parent':None}
   r,done=b._finish_locked('unit',{'items':values,'exhausted':True});self.assertTrue(r['items']);self.assertTrue(all(i['article_context']['state']=='unavailable'for i in r['items']))
  b=self.broker([]);b._initialize_locked('unit');b.ledger.rows['unit']={'binding':{'target':TARGET},'parent':None}
  with patch.object(m.CoverageBroker,'_finish_locked',return_value=({'items':[{'article_key':'a'*64,'relationships':[],'extra':'x'*520000}]},True)),self.assertRaises(ValueError):b._finish_locked('unit',{'items':[ARTICLE],'exhausted':True})
 def test_context_overcap_returns_unavailable_and_cleans(self):
  source=rows(1);source[0].update(title='HS 8517;',summary='',source='Fixture',url='https://news.example/story');b=self.broker(source)
  real=m.json.dumps
  def expanded(obj,*a,**k):
   if type(obj)is dict and 'items'in obj and any('article_context'in x for x in obj['items']):return 'x'*520001
   return real(obj,*a,**k)
  with patch.object(m.json,'dumps',side_effect=expanded):body,status=b.page({k:TARGET[k]for k in ('system','edition','code')})
  self.assertEqual((body,status),({'state':'source_unavailable'},503));self.assertEqual(b.contexts,{});self.assertEqual(b.replies,{});self.assertEqual(b.ledger.rows,{});self.assertEqual(b.pages.streams,{})
 def test_actual_finder_variant_heads_headers_and_private_boundary(self):
  env={**ENV,'PUBLIC_NEWS_FINDER_LINKS_ENABLED':'true','PUBLIC_NEWS_FINDER_ENABLED':'true','PUBLIC_FINDER_IDENTITY_PROOF_PREP_ENABLED':'true'}
  # The Finder navigation uses its reviewed actual mount and identity proof.
  a=build_public_live_preview(env,client_factory=lambda *a,**k:Client(),coverage_binding_provider=self.bind);self.addCleanup(a.extensions['coverage_close']);t=a.test_client()
  r=t.get('/workspace/assets/code_news_coverage.js',base_url=ORIGIN);self.assertEqual(r.status_code,200);self.assertIn('const context=item.article_context',r.text);self.assertIn('finder_navigation',r.text);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertIn("script-src 'self'",r.headers['Content-Security-Policy'])
  for k in ('ETag','Last-Modified','Accept-Ranges'):self.assertNotIn(k,r.headers)
  h=t.head('/workspace/assets/code_news_coverage.js',base_url=ORIGIN);self.assertEqual(h.data,b'');self.assertEqual(h.status_code,200)
  self.assertNotIn('article_context',t.get('/api/geo-news',base_url=ORIGIN).text)
 def test_default_off_against_actual_parent_builder(self):
  import types
  baseline=types.ModuleType('baseline_public_live_builder')
  raw=(m.ROOT/'tests/fixtures/context_d4_base_live.txt').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),'4567df1e3b43bef70bd2460aecc157a31c91a0f6cedb562a7cf7db0c2fe296d5');exec(compile(raw,'actual-parent','exec'),baseline.__dict__)
  old=baseline.build_public_live_preview(LIVE,client_factory=lambda *a,**k:Client(),coverage_binding_provider=self.bind)
  new=build_public_live_preview({**LIVE,m.FLAG:'false'},client_factory=lambda *a,**k:Client(),coverage_binding_provider=self.bind)
  for a in (old,new):self.addCleanup(a.extensions['coverage_close'])
  self.assertEqual(sorted(str(x)for x in old.url_map.iter_rules()),sorted(str(x)for x in new.url_map.iter_rules()))
  for path in ['/workspace/code-news-coverage','/workspace/assets/code_news_coverage.js','/workspace/assets/code_news_coverage.css','/workspace/assets/code_news_contract.js','/api/news-health','/api/geo-news']:
   left,right=[a.test_client().get(path,base_url=ORIGIN)for a in (old,new)];self.assertEqual(left.status_code,right.status_code);self.assertEqual(left.data,right.data);self.assertEqual(dict(left.headers),dict(right.headers));left.close();right.close()
if __name__=='__main__':unittest.main()
