import unittest,hashlib
from datetime import datetime,timezone
from integration.news_api import create_app
from integration.critical_stories import critical_stories
from integration.news_view import views
from integration.storage_reader import ReadOnlyNewsReader
from integration.public_news import public_news_row,PUBLIC_NEWS_FIELDS,READ_STORE_FIELDS
PRIVATE='private-marker-telemetry'
class PrivateNewsFieldTests(unittest.TestCase):
 def test_all_api_news_boundaries_case_variants(self):
  raw={'title':'Fixture HSN090121 India coffee','url':'https://example.com/a','country':'India','risk_level':'CRITICAL','created_at':datetime.now(timezone.utc).isoformat(),'score':16,'category':'TRADE'}
  private_keys=['_id','id','mongo_id','legacy_id','original_url','backup_url','telegram_url','telegram_message_id','telegram_secret','emailed']
  for k in private_keys:
   for variant in [k,k.upper(),k.title()]:raw[variant]=PRIVATE
  raw['telegram_url']='https://t.me/c/123456/99';rows={'geo':[raw],'brics':[]}
  context=lambda article:[{'code':'090121','system':'HS','system_index':0,'country':'India','telegram_url':PRIVATE,'emailed':PRIVATE}]
  c=create_app(reader=lambda:rows,authorize=lambda req:True,finder_context_reader=context,finder_base='http://localhost/workspace/finder/index.html',finder_index_verified=True).test_client()
  paths=['/health','/api/news','/api/critical-stories','/api/story-groups','/api/country-page?country=India','/api/news-export.csv','/api/sample-volume?project=geo','/api/sample-volume?project=brics','/api/dashboard-signals?project=geo','/api/dashboard-signals?project=brics','/api/news-stats','/api/dashboard-snapshots?project=geo','/api/source-health','/api/tariff-evidence','/dashboard']
  for path in paths:
   response=c.get(path);body=response.get_data(as_text=True).casefold();self.assertNotIn(PRIVATE,body,path);self.assertNotIn('https://t.me/c/',body,path)
   for k in private_keys:self.assertNotIn('"'+k.casefold()+'"',body,path)
  for path,body in [('/api/related-news',{'country':'India'}),('/api/finder-context',{'project':'geo','article_key':hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()})]:
   response=c.post(path,json=body,headers={'Origin':'http://localhost'});out=response.get_data(as_text=True).casefold();self.assertEqual(response.status_code,200);self.assertNotIn(PRIVATE,out,path);self.assertNotIn('https://t.me/c/',out,path)
   for k in private_keys:self.assertNotIn('"'+k.casefold()+'"',out,path)
  self.assertEqual(raw['emailed'],PRIVATE);self.assertEqual(raw['telegram_url'],'https://t.me/c/123456/99')
 def test_critical_direct_boundary(self):
  rows=views({'geo':[{'title':'fixture','url':'https://example.com/a','risk_level':'CRITICAL','created_at':datetime.now(timezone.utc).isoformat(),'telegram_url':'https://t.me/c/123456/99'}]});self.assertIn('backup_url',rows[0]);self.assertNotIn('backup_url',critical_stories(rows,datetime.now(timezone.utc))['items'][0])
 def test_projection_full_pinned_allowlist(self):
  class Store:
   def find(self,q,p):self.projection=p;return self
   def sort(self,*args):return self
   def limit(self,*args):return self
   def __iter__(self):return iter([])
  expected=('_id','id','url','title','summary','source','country','category','published','created_at','collected_at','risk_level','credibility','score','corroborated_by')
  self.assertEqual(READ_STORE_FIELDS,expected);store=Store();ReadOnlyNewsReader({'geo':store},True)();self.assertEqual(store.projection,{k:1 for k in expected})
 def test_allowlist_case_collisions_deep_copy_and_unknown(self):
  self.assertEqual(PUBLIC_NEWS_FIELDS,('article_key','project','url','title','summary','source','original_country','category','published_at','collected_at','risk_level','credibility','score','corroboration_count'))
  row={'title':'safe','TITLE':'ambiguous','Telegram_URL':PRIVATE,'extra':PRIVATE,'score':1,'summary':{'a':['b']}}
  out=public_news_row(row);self.assertNotIn('title',out);self.assertNotIn('Telegram_URL',out);self.assertNotIn('extra',out);out['summary']['a'].append('c');self.assertEqual(row['summary']['a'],['b'])
 def test_no_private_fallback_for_identity(self):
  raw={'geo':[{'title':'fixture','telegram_url':'https://t.me/c/123456/99','backup_url':'https://example.com/private'}]};self.assertEqual(views(raw),[])
