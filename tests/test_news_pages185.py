import unittest
from integration.news_pages import WholeGeoPages,PageExpired,PageBusy,PageUnavailable
from integration.public_live_builder import sanitize_public_geo_rows
from integration.news_api import create_app
class Cursor:
 def __init__(self,rows):self.rows=iter(rows);self.closed=0;self.settings=[]
 def sort(self,v):self.settings.append(('sort',v));return self
 def batch_size(self,v):self.settings.append(('batch',v));return self
 def max_time_ms(self,v):self.settings.append(('timeout',v));return self
 def __next__(self):return next(self.rows)
 def close(self):self.closed+=1
class Store:
 def __init__(self,rows):self.rows=rows;self.calls=[];self.cursors=[]
 def find(self,q,p):self.calls.append((q,p));c=Cursor(self.rows);self.cursors.append(c);return c
F={'project':'geo','query':'','category':'','country':'','sort':'newest'}
def rows(n):return [{'url':'https://fixture.invalid/'+str(i),'title':'Story '+str(i),'created_at':'2026-10-09T00:00:00Z','secret':'NO_PRIVATE_VALUE','_id':i}for i in range(n)]
class Tests(unittest.TestCase):
 def make(self,n):
  self.store=Store(rows(n));self.now=0;self.pages=WholeGeoPages(self.store,sanitize_public_geo_rows,verified=True,clock=lambda:self.now,start_cleaner=False);self.addCleanup(self.pages.close);return self.pages
 def test_whole21609_no100cap_no_keys_in_token_no_private(self):
  p=self.make(21609);d=p.page(F,100);seen=[]
  while True:
   seen+=d['items'];self.assertNotIn('NO_PRIVATE_VALUE',str(d));self.assertIsNone(d['total_count']);self.assertTrue(all('_id'not in r and 'mongo_id'not in r and 'legacy_id'not in r for r in d['items']));
   if not d['next_cursor']:break
   d=p.page(F,100,d['next_cursor'])
  self.assertEqual(len(seen),21609);self.assertEqual(len({r['article_key']for r in seen}),21609);self.assertEqual(len(self.store.calls),1);self.assertEqual(self.store.calls[0][0],{});self.assertGreater(self.store.cursors[0].closed,0)
 def test_retries_binding_expiry_limits(self):
  p=self.make(105);a=p.page(F);t=a['next_cursor'];b=p.page(F,25,t);self.assertEqual(b,p.page(F,25,t));self.assertEqual(len(b['items']),25)
  with self.assertRaises(PageExpired):p.page(dict(F,query='changed'),25,t)
  self.now=121
  with self.assertRaises(PageExpired):p.page(F,25,b['next_cursor'])
  self.assertEqual(len(p.streams),0);self.assertGreater(self.store.cursors[0].closed,0)
 def test_raw_sort_tiebreak_and_bounded_scans(self):
  p=self.make(2001);d=p.page(dict(F,query='never'));self.assertEqual(d['scanned_this_page'],1000);self.assertEqual(d['items'],[]);self.assertIsNotNone(d['next_cursor']);self.assertEqual(self.store.cursors[0].settings,[('sort',[('created_at',-1),('_id',-1)]),('batch',100),('timeout',2000)])
 def test_capacity_and_close(self):
  p=self.make(100)
  for _ in range(16):p.page(F)
  with self.assertRaises(PageBusy):p.page(F)
  p.close();self.assertEqual(len(p.streams),0)
  with self.assertRaises(PageUnavailable):p.page(F)
 def test_route_strict_auth_off_and_public_projection(self):
  p=self.make(105);c=create_app(full_news_pages=p,authorize=lambda _:True).test_client()
  for q in ['limit=0','limit=101','limit=01','limit=1.0','limit=2&limit=3','q='+'a'*201,'unknown=x','cursor=bad','q=a&q=b','project=brics','sort=no']:
   self.assertEqual(c.get('/api/news-page?'+q).status_code,400,q)
  self.assertEqual(c.get('/api/news-page').status_code,200);self.assertEqual(create_app().test_client().get('/api/news-page').status_code,403);self.assertEqual(create_app(authorize=lambda _:True).test_client().get('/api/news-page').status_code,503)
 def test_cursor_failure_closed_fixed_error(self):
  p=self.make(50);d=p.page(F)
  def bad():raise RuntimeError('SECRET')
  class Bad:
   def __next__(self):bad()
   def close(self):self.closed=True
  state=next(iter(p.streams.values()));bad_cursor=Bad();state['cursor']=bad_cursor
  with self.assertRaises(PageUnavailable)as caught:p.page(F,25,d['next_cursor'])
  self.assertNotIn('SECRET',str(caught.exception));self.assertTrue(bad_cursor.closed);self.assertEqual(len(p.streams),0)
 def test_live_builder_default_off_exact_flags_and_gated_reader(self):
  from integration.public_live_builder import build_public_live_preview
  base={'PUBLIC_NEWS_READ_ENABLED':'true','PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','NEWS_STORE_MAPPING_VERIFIED':'true','PUBLIC_NEWS_DISCLOSURE_VERIFIED':'true','GEO_READONLY_CREDENTIAL_VERIFIED':'true','GEO_MONGODB_URI':'mongodb://fixture','PREVIEW_ORIGIN':'https://example.org'}
  store=Store(rows(105))
  class Client:
   def __getitem__(self,key):return self
   def find(self,q,p):return store.find(q,p)
   def close(self):pass
  for flag,status in [('false',503),('true',200)]:
   app=build_public_live_preview(dict(base,PUBLIC_NEWS_FULL_PAGES_ENABLED=flag),client_factory=lambda *a,**k:Client())
   pages=app.extensions['whole_news_pages']
   if pages:self.addCleanup(pages.close)
   self.assertEqual(app.test_client().get('/api/news-page',base_url='https://example.org').status_code,status)
   self.assertEqual(app.test_client().get('/api/news-page',base_url='https://wrong.org').status_code,403)
  for extra in [{'PUBLIC_NEWS_FULL_PAGES_ENABLED':'yes'},{'PUBLIC_NEWS_FULL_PAGES_ENABLED':'true','PUBLIC_NEWS_READ_ENABLED':'false'},{'PUBLIC_NEWS_FULL_PAGES_ENABLED':'true','PUBLIC_NEWS_DISCLOSURE_VERIFIED':'false'}]:
   with self.assertRaises(ValueError):build_public_live_preview(dict(base,**extra),client_factory=lambda *a,**k:self.fail('client before gates'))
 def test_final_page_retry_and_absolute_expiry(self):
  p=self.make(30);a=p.page(F);t=a['next_cursor'];b=p.page(F,25,t);self.assertTrue(b['exhausted']);self.assertEqual(b,p.page(F,25,t));self.now=1800
  with self.assertRaises(PageExpired):p.page(F,25,t)
 def test_all_raw_orders_closed_projection_old_contract(self):
  p=self.make(105)
  for sort,field,direction in [('newest','created_at',-1),('title','title',1),('country','country',1),('score','score',-1)]:
   p.page(dict(F,sort=sort));self.assertEqual(self.store.cursors[-1].settings[0],('sort',[(field,direction),('_id',direction)]))
  from integration.public_news import READ_STORE_FIELDS
  self.assertEqual(self.store.calls[0][1],{k:1 for k in READ_STORE_FIELDS})
  c=create_app(reader=lambda:{'geo':rows(105)},authorize=lambda _:True).test_client();self.assertEqual(len(c.get('/api/news?project=geo').json['items']),100);self.assertEqual(c.get('/api/news-export.csv?project=geo').headers['X-Export-Limit'],'100')
