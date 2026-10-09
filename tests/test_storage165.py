import unittest
from intelligence.geo.bounded_reads import article_pages,cursor_rows,bounded_limit
from integration.db_contract.query_plan import query_plan,explain_review
class Cursor:
 def __init__(self,rows):self.rows=rows;self.closed=False;self.calls=[]
 def sort(self,x):self.calls.append(('sort',x));self.rows=sorted(self.rows,key=lambda r:r['_id'],reverse=x[0][1]<0);return self
 def limit(self,n):self.calls.append(('limit',n));self.rows=self.rows[:n];return self
 def max_time_ms(self,n):self.calls.append(('time',n));return self
 def batch_size(self,n):self.calls.append(('batch',n));return self
 def __iter__(self):return iter(self.rows)
 def close(self):self.closed=True
class Collection:
 def __init__(self,rows):self.rows=rows;self.cursors=[];self.queries=[]
 def find(self,q,projection):
  self.queries.append((q,projection));rows=[]
  for r in self.rows:
   if 'category' in q and r.get('category')!=q['category']:continue
   if '$or' in q and r.get('category') not in ('GENERAL',None):continue
   b=q.get('_id',{})
   if '$lt' in b and r['_id']>=b['$lt']:continue
   if '$gte' in b and r['_id']<b['$gte']:continue
   rows.append({k:v for k,v in r.items() if k in projection})
  c=Cursor(rows);self.cursors.append(c);return c
class StorageReadTests(unittest.TestCase):
 def test_plan_no_effects_or_provision(self):
  p=query_plan();self.assertFalse(p['provision_allowed']);self.assertFalse(p['ttl_allowed']);self.assertTrue(any(x['keys']==[('category',1),('_id',1)] for x in p['indexes']))
 def test_supplied_explain_not_live_grant(self):
  r=explain_review({'query_id':'fixture','executionStats':{'executionSuccess':True,'nReturned':2,'totalKeysExamined':3,'totalDocsExamined':3}});self.assertTrue(r['within_review_bound']);self.assertFalse(r['provision_allowed']);self.assertEqual(r['scope'],'supplied_not_live_verified')
  with self.assertRaises(ValueError):explain_review({'query_id':'fixture','executionStats':{'executionSuccess':False}})
 def test_page_order_projection_category_and_close(self):
  c=Collection([{'_id':i,'title':str(i),'category':'A' if i%2 else 'B','secret':'no'} for i in range(600)])
  pages=list(article_pages(c,category='A'));self.assertEqual([len(x) for x in pages],[250,50]);self.assertEqual(sum(map(len,pages)),300);self.assertNotIn('secret',str(pages));self.assertTrue(all(x.closed for x in c.cursors));self.assertTrue(all('time' in dict(x.calls) for x in c.cursors))
 def test_empty_and_caps_raise_close(self):
  self.assertEqual(list(article_pages(Collection([]))),[])
  c=Collection([{'_id':i,'title':'a'} for i in range(3)])
  with self.assertRaises(ValueError):list(article_pages(c,max_rows=2))
  self.assertTrue(all(x.closed for x in c.cursors))
 def test_wall_limit_and_cell_limit(self):
  times=iter([0,31]);c=Collection([{'_id':1}])
  with self.assertRaises(TimeoutError):list(article_pages(c,clock=lambda:next(times)))
  c=Collection([{'_id':1,'title':'x'*8001}])
  with self.assertRaises(ValueError):list(article_pages(c))
  self.assertTrue(all(x.closed for x in c.cursors))
 def test_read_limit_closed_and_cursor_bounds(self):
  for v in [0,-1,2001,True,'3']:
   with self.assertRaises(ValueError):bounded_limit(v)
  c=Cursor([{'_id':1}]);self.assertEqual(cursor_rows(c,1),[{'_id':1}]);self.assertTrue(c.closed)

class CsvTests(unittest.TestCase):
 def test_formula_and_incomplete_marker(self):
  from intelligence.geo.bounded_csv import csv_chunks
  def pages():
   yield [{'title':' =SUM(A1)','url':'fixture'}]
   raise RuntimeError('secret-uri')
  out=''.join(csv_chunks(pages()));self.assertIn("' =SUM(A1)",out);self.assertIn('EXPORT_INCOMPLETE',out);self.assertNotIn('secret-uri',out)
 def test_http_authorization_prefetch_and_stream(self):
  from intelligence.geo import web
  from unittest.mock import patch
  def pages(*args,**kw):yield [{'title':'safe'}]
  with patch.object(web,'TRIGGER_SECRET','known'),patch.object(web,'_db_check',return_value=None),patch.object(web,'_service',side_effect=pages):
   c=web.app.test_client();self.assertEqual(c.get('/export.csv').status_code,401)
   r=c.get('/export.csv',headers={'X-Trigger-Secret':'known'});self.assertEqual(r.status_code,200);self.assertIn('safe',r.text);self.assertEqual(r.headers['X-Export-Scope'],'bounded-not-snapshot-not-recovery-backup')
   self.assertEqual(c.get('/export.csv?category=A&category=B',headers={'X-Trigger-Secret':'known'}).status_code,400)

class MoreBounds(unittest.TestCase):
 def test_general_includes_null_missing_and_newest(self):
  c=Collection([{'_id':1,'title':'old'},{'_id':3,'category':'GENERAL','title':'new'},{'_id':2,'category':None,'title':'middle'},{'_id':4,'category':'OTHER'}])
  rows=sum(list(article_pages(c,category='GENERAL')),[]);self.assertEqual([r['title'] for r in rows],['new','middle','old'])
 def test_exact2000_and2001(self):
  self.assertEqual(sum(map(len,article_pages(Collection([{'_id':i} for i in range(2000)])))),2000)
  with self.assertRaises(ValueError):list(article_pages(Collection([{'_id':i} for i in range(2001)])))
 def test_byte_limit_and_unstable_order(self):
  c=Collection([{'_id':i,'title':'x'*8000} for i in range(2000)])
  from unittest.mock import patch
  with patch('intelligence.geo.bounded_reads.MAX_BYTES',1000):
   with self.assertRaises(ValueError):list(article_pages(c))
  class Bad(Collection):
   def find(self,q,projection):
    c=super().find(q,projection)
    if '_id' in q:c.rows=[{'_id':2},{'_id':2}];c.sort=lambda x:c
    return c
  with self.assertRaises(ValueError):list(article_pages(Bad([{'_id':1},{'_id':2}])))
 def test_actual16mib_source_cap(self):
  c=Collection([{'_id':i,'title':'x'*8000,'summary':'x'*8000} for i in range(1100)])
  with self.assertRaises(ValueError):list(article_pages(c))
 def test_http_midstream_redacted_marker(self):
  from intelligence.geo import web
  from unittest.mock import patch
  def pages(*args,**kw):
   yield [{'title':'newest'}]
   raise RuntimeError('secret-uri')
  with patch.object(web,'TRIGGER_SECRET','known'),patch.object(web,'_db_check',return_value=None),patch.object(web,'_service',side_effect=pages):
   r=web.app.test_client().get('/export.csv',headers={'X-Trigger-Secret':'known'});self.assertEqual(r.status_code,200);self.assertIn('EXPORT_INCOMPLETE',r.text);self.assertNotIn('secret-uri',r.text);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertIn('not-recovery-backup',r.headers['X-Export-Scope'])

class ListBounds(unittest.TestCase):
 def test2001_list_fails_instead_of_silent_send_slice(self):
  c=Cursor([{'_id':i} for i in range(2001)])
  with self.assertRaises(ValueError):cursor_rows(c,2000,require_complete=True)
  self.assertTrue(c.closed)
 def test2000_list_complete(self):
  c=Cursor([{'_id':i} for i in range(2000)]);self.assertEqual(len(cursor_rows(c,2000,require_complete=True)),2000);self.assertTrue(c.closed)
