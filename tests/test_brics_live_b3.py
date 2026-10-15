import json,sqlite3,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import Mock,patch
from integration import brics_live_b3 as m
from integration.geo_read_factory import ReadClient
from integration.news_api import create_app
from integration import public_brics_news as base
from integration.public_live_builder import build_public_live_preview
from integration.public_preview_builder import build_public_preview
from tests.test_code_news_coverage_binding_prep import LIVE,Client,ORIGIN
NOW=datetime(2026,10,15,23,tzinfo=timezone.utc)
ROW=dict(url='https://fixture.invalid/brics',title='BRICS sanctions summit',summary='Synthetic stored row',source='Synthetic',country='IN',category='SANCTIONS',published='',collected_at='2026-10-15T22:00:00',password='SECRET')
ENV=dict(LIVE,PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_BRICS_NEWS_ENABLED='true',PUBLIC_BRICS_LIVE_READ_ENABLED='true',BRICS_STORE_MAPPING_VERIFIED='true',BRICS_PUBLIC_DISCLOSURE_VERIFIED='true',BRICS_READONLY_CREDENTIAL_VERIFIED='true')
class Tests(unittest.TestCase):
 def binding(self):
  r=m.SQLiteReader('/synthetic/not-opened.sqlite');return m.Binding(r,m.Review(r.identity,'fixture mapping','fixture disclosure','fixture readonly'),('sanctions','coup'))
 def service(self,rows,clock=lambda:0):
  b=self.binding();s=m.Service(b,clock=clock,now=lambda:NOW)
  patcher=patch.object(b.reader,'read',return_value=rows);mock=patcher.start();self.addCleanup(patcher.stop);self.addCleanup(s.close);return s,mock
 def test_off_and_evidence_gate_before_effect(self):
  with patch.object(Path,'read_bytes',side_effect=AssertionError),patch.object(m.SQLiteReader,'read',side_effect=AssertionError):self.assertIsNone(m.prepare({}))
  for k in (m.FLAG,'BRICS_STORE_MAPPING_VERIFIED','BRICS_PUBLIC_DISCLOSURE_VERIFIED','BRICS_READONLY_CREDENTIAL_VERIFIED'):
   with self.assertRaises(ValueError):m.prepare(dict(ENV,**{k:'yes'}),self.binding())
  with self.assertRaises(ValueError):m.prepare({},self.binding())
  with self.assertRaises(ValueError):m.prepare(ENV)
  b=self.binding()
  with self.assertRaises(ValueError):m.Binding(b.reader,m.Review(('sqlite','wrong'),'x','y','z'),('coup',)).validate()
  with self.assertRaises(ValueError):m.Binding(b.reader,m.Review(b.reader.identity,'','y','z'),('coup',)).validate()
  with patch.object(m,'PINS',{**m.PINS,'integration/brics_live_b3/page.js':'0'*64}),self.assertRaises(ValueError):m.prepare(ENV,b)
 def test_projection_separate_meaning_dates_filter_no_private(self):
  s,read=self.service([ROW,dict(ROW,title='Domestic football',url='https://fixture.invalid/other')]);out,status=s.run();self.assertEqual(status,200);self.assertEqual(len(out['items']),1);self.assertEqual(len(out['critical_24h_keys']),1);self.assertNotIn('SECRET',str(out));self.assertIsNone(out['items'][0]['published_at']);self.assertIsNone(out['items'][0]['corroboration_count']);self.assertNotIn('risk_level',str(out));self.assertNotIn('fixture',out['state']);read.assert_called_once()
 def test_cache_60s_future_old_and_missing_critical(self):
  s,read=self.service([dict(ROW,collected_at='2026-10-16T00:00:00Z'),dict(ROW,url='https://fixture.invalid/old',collected_at='2026-10-14T23:00:00Z'),dict(ROW,url='https://fixture.invalid/missing',collected_at=None)])
  first,status=s.run();s.run();self.assertEqual(read.call_count,1);self.assertEqual(first['critical_24h_keys'],[]);self.assertEqual(first['critical_time_unknown_count'],1)
  s.clock=lambda:61;s.run();self.assertEqual(read.call_count,2)
 def test_fail_latched_and_shutdown(self):
  for rows in ([ROW]*101,[dict(ROW,summary='x'*8000)]*100):
   s,read=self.service(rows);self.assertEqual(s.run()[1],503);self.assertEqual(s.run()[1],503);self.assertEqual(read.call_count,1);self.assertTrue(s.binding.reader.closed)
  s,read=self.service([]);s.close();s.close();self.assertEqual(s.run()[1],503);read.assert_not_called()
 def test_skip_count_unsafe_rows_and_cache_deepcopy(self):
  rows=[ROW,dict(ROW,summary=None),dict(ROW,category=None),dict(ROW,url='http://fixture.invalid'),dict(ROW,published='bad'),['bad']]
  s,read=self.service(rows);out,status=s.run();self.assertEqual(status,200);self.assertEqual(len(out['items']),1);self.assertEqual(out['skipped_rows'],5);self.assertFalse(s.failed)
  out['items'][0]['title']='MUTATED';again,status=s.run();self.assertEqual(again['items'][0]['title'],ROW['title']);self.assertEqual(again['skipped_rows'],5);read.assert_called_once()
  s,read=self.service([dict(ROW,summary=None)]);out,status=s.run();self.assertEqual(status,200);self.assertEqual(out['items'],[]);self.assertEqual(out['skipped_rows'],1)
 def test_sqlite_connection_write_refused_and_limit101(self):
  real=sqlite3.connect;seen=[]
  with tempfile.TemporaryDirectory()as tmp:
   path=Path(tmp)/'test.db';conn=real(path);conn.execute('CREATE TABLE articles(id TEXT,title TEXT,url TEXT,source TEXT,country TEXT,category TEXT,summary TEXT,published TEXT,collected_at TEXT)');conn.commit();conn.close()
   class Wrapped:
    def __init__(self,conn):self.conn=conn
    def execute(self,sql,*args):
     seen.append(sql)
     if sql.startswith('SELECT'):
      with selftest.assertRaises(sqlite3.OperationalError):self.conn.execute("INSERT INTO articles(id)VALUES('bad')")
     return self.conn.execute(sql,*args)
    def set_progress_handler(self,*args):return self.conn.set_progress_handler(*args)
    def close(self):return self.conn.close()
   selftest=self
   def connect(*args,**kwargs):
    self.assertIn('mode=ro',args[0]);self.assertTrue(kwargs['uri']);return Wrapped(real(*args,**kwargs))
   with patch.object(m.sqlite3,'connect',side_effect=connect):self.assertEqual(m.SQLiteReader(path).read(),[])
   self.assertTrue(any(sql.endswith('LIMIT 101')for sql in seen));self.assertIn('PRAGMA query_only=ON',seen)
 def test_sqlite_actual_mode_ro_no_creation_or_article_changes(self):
  with tempfile.TemporaryDirectory()as tmp:
   path=Path(tmp)/'news.db';r=m.SQLiteReader(path)
   with self.assertRaises(ValueError):r.read()
   self.assertFalse(path.exists())
   conn=sqlite3.connect(path);conn.execute('CREATE TABLE articles (id TEXT,title TEXT,url TEXT,source TEXT,country TEXT,category TEXT,summary TEXT,published TEXT,collected_at TEXT,password TEXT)')
   for i in range(105):conn.execute('INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?)',(str(i),ROW['title'],ROW['url'],ROW['source'],ROW['country'],ROW['category'],ROW['summary'],'',ROW['collected_at'],'SECRET'))
   conn.commit();conn.close();before=path.read_bytes();rows=r.read();self.assertEqual(len(rows),100);self.assertNotIn('password',rows[0]);self.assertEqual(before,path.read_bytes());r.close()
   with self.assertRaises(ValueError):r.read()
   link=Path(tmp)/'link';link.symlink_to(path)
   with self.assertRaises(ValueError):m.SQLiteReader(link).read()
 def test_mongo_projection_sort_caps_cursor_close_and_noGeo_mapping(self):
  class Cursor:
   def __init__(self):self.calls=[];self.closed=0;self.iterator=iter([ROW])
   def sort(self,*a):self.calls.append(('sort',a));return self
   def limit(self,n):self.calls.append(('limit',n));return self
   def batch_size(self,n):self.calls.append(('batch',n));return self
   def max_time_ms(self,n):self.calls.append(('time',n));return self
   def close(self):self.closed+=1
   def __iter__(self):return self
   def __next__(self):return next(self.iterator)
  cursor=Cursor();col=Mock();col.find.return_value=cursor;db=Mock();db.__getitem__=Mock(return_value=col);client=Mock();client.__getitem__=Mock(return_value=db)
  r=m.MongoReader(ReadClient(client),deployment='fixture',database='newsbot');self.assertEqual(r.read(),[ROW]);query,projection=col.find.call_args.args;self.assertEqual(query,{});self.assertEqual(projection['_id'],0);self.assertNotIn('password',projection);self.assertIn(('limit',100),cursor.calls);self.assertIn(('time',2000),cursor.calls);self.assertEqual(cursor.closed,1);r.close();r.close();client.close.assert_called_once()
  with self.assertRaises(ValueError):m.MongoReader(ReadClient(client),deployment='fixture',database='geo_intel')
 def test_builder_route_guards_head_noIO_separate_streams_and_off_parity(self):
  b=self.binding();app=build_public_live_preview(ENV,client_factory=lambda *a,**k:Client(),brics_live_binding=b);self.addCleanup(app.extensions['brics_live_close']);self.addCleanup(app.extensions['whole_news_pages'].close);c=app.test_client()
  with patch.object(b.reader,'read',return_value=[ROW])as read:
   self.assertEqual(c.head(base.API,base_url=ORIGIN).status_code,200);read.assert_not_called();self.assertEqual(c.get(base.API,base_url=ORIGIN).json['state'],'reviewed_brics_read');read.assert_called_once()
   for path in base.PATHS:
    self.assertEqual(c.post(path,base_url=ORIGIN).status_code,403);self.assertEqual(c.get(path+'?x=1',base_url=ORIGIN).status_code,400);self.assertEqual(c.get(path,base_url='https://evil.invalid').status_code,403)
  self.assertIn('BRICS stored news',c.get(base.PAGE,base_url=ORIGIN).text);self.assertIn('BRICS news</a>',c.get('/workspace',base_url=ORIGIN).text)
  with self.assertRaises(ValueError):build_public_preview(ENV)
  # New default flag explicitly false preserves exact old responses.
  flags={k:v for k,v in ENV.items()if k not in (m.FLAG,'BRICS_STORE_MAPPING_VERIFIED','BRICS_PUBLIC_DISCLOSURE_VERIFIED','BRICS_READONLY_CREDENTIAL_VERIFIED')}
  apps=[build_public_live_preview(e,client_factory=lambda *a,**k:Client())for e in (flags,dict(flags,**{m.FLAG:'false'}))]
  for a in apps:self.addCleanup(a.extensions['whole_news_pages'].close)
  for path in ['/workspace',base.PAGE,base.API,base.ASSET,'/api/brics/streams']:
   x,y=[a.test_client().get(path,base_url=ORIGIN)for a in apps];self.assertEqual((x.status_code,x.data,dict(x.headers)),(y.status_code,y.data,dict(y.headers)))
if __name__=='__main__':unittest.main()
