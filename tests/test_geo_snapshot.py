import unittest
from bson import ObjectId
from integration.news_export.geo_snapshot import create_geo_original_stream,SnapshotUnavailable,GeoSnapshot
R={'mapping':('geo_intel','articles'),'read_only':True,'snapshot_supported':True,'index':'geo_export_order','index_explain_verified':True}
def row(n):return {'score':10,'published':'2026-01-01T00:00:00+00:00','_id':ObjectId(f'{n:024x}'),'title':f'News{n}','url':'https://example.com'}
class Session:
 def __init__(self):self.ends=0
 def end_session(self):self.ends+=1
class Cursor:
 def __init__(self,rows,fail=False):self.rows=rows;self.closed=False;self.calls=[];self.fail=fail
 def sort(self,x):self.calls.append(('sort',x));return self
 def hint(self,x):self.calls.append(('hint',x));return self
 def max_time_ms(self,x):self.calls.append(('max_time_ms',x));return self
 def batch_size(self,x):self.calls.append(('batch_size',x));return self
 def limit(self,x):self.calls.append(('limit',x));self.rows=self.rows[:x];return self
 def __iter__(self):
  if self.fail:raise ValueError('secret-uri')
  return iter(self.rows)
 def close(self):self.closed=True
class Client:
 def __init__(self,rows,fail=False):self.rows=rows;self.session=Session();self.sessions=[];self.finds=[];self.cursors=[];self.fail=fail
 def start_session(self,**kw):self.sessions.append(kw);return self.session
 def __getitem__(self,x):return self
 def find(self,q,p,**kw):
  self.finds.append((q,p,kw));rows=[{k:v for k,v in r.items() if k in p} for r in self.rows]
  if q:
   def matches(r):
    return any(all((r[k]<v['$lt'] if type(v) is dict else r[k]==v) for k,v in term.items()) for term in q['$or'])
   rows=[r for r in rows if matches(r)]
  cur=Cursor(rows,self.fail);self.cursors.append(cur);return cur
class Tests(unittest.TestCase):
 def test_review_before_session(self):
  for key in R:
   r=dict(R);r.pop(key);c=Client([])
   with self.assertRaises(SnapshotUnavailable):create_geo_original_stream(c,review=r)
   self.assertEqual(c.sessions,[])
 def test_full_stream_and_snapshot_same_session(self):
  c=Client([row(3),row(2)]);s=create_geo_original_stream(c,review=R);data=b''.join(s)
  self.assertIn(b'News3',data);self.assertIn(b'EXPORT_COMPLETE',data);self.assertEqual(c.session.ends,1)
  self.assertEqual(c.sessions,[{'snapshot':True,'causal_consistency':False}]);self.assertEqual(len(c.finds),2)
  for q,p,k in c.finds:self.assertIs(k['session'],c.session);self.assertEqual(k['collation'],{'locale':'simple'})
  self.assertTrue(all(x.closed for x in c.cursors));self.assertEqual(c.cursors[0].calls,[('sort',[('score',-1),('published',-1),('_id',-1)]),('hint','geo_export_order'),('max_time_ms',2000),('batch_size',100)])
 def test_unstarted_and_idempotent_close(self):
  c=Client([]);s=create_geo_original_stream(c,review=R);s.close();s.close();self.assertEqual(c.session.ends,1);self.assertEqual(list(s),[])
 def test_unsupported_hidden_row_blocks_before_header(self):
  c=Client([row(3),dict(row(2),score=None)])
  with self.assertRaises(SnapshotUnavailable):create_geo_original_stream(c,review=R)
  self.assertEqual(len(c.finds),1);self.assertEqual(c.session.ends,1);self.assertTrue(c.cursors[0].closed)
 def test_failure_redacted_closed(self):
  c=Client([],True)
  with self.assertRaises(SnapshotUnavailable) as e:create_geo_original_stream(c,review=R)
  self.assertIsNone(e.exception.__context__);self.assertNotIn('secret',str(e.exception));self.assertEqual(c.session.ends,1);self.assertTrue(c.cursors[0].closed)
 def test_preflight_deadline_closes(self):
  c=Client([row(1)]);ticks=iter([0,0,0,0,0,121])
  with self.assertRaises(SnapshotUnavailable):create_geo_original_stream(c,review=R,clock=lambda:next(ticks))
  self.assertEqual(c.session.ends,1);self.assertTrue(c.cursors[0].closed)

 def test_501_rows_multiple_pages_same_snapshot(self):
  c=Client([row(n) for n in range(501,0,-1)]);s=create_geo_original_stream(c,review=R);data=b''.join(s)
  self.assertIn(b'EXPORT_COMPLETE',data);self.assertEqual(s.state['read'],501);self.assertEqual(s.state['rows'],501)
  self.assertEqual(len(c.finds),3);self.assertIn('$or',c.finds[-1][0]);self.assertEqual(c.session.ends,1);self.assertTrue(all(x.closed for x in c.cursors))
 def test_bad_source_order_before_header(self):
  c=Client([row(1),row(2)])
  with self.assertRaises(SnapshotUnavailable):create_geo_original_stream(c,review=R)
  self.assertEqual(len(c.finds),1);self.assertEqual(c.session.ends,1)
 def test_page_budget_before_append_closes(self):
  c=Client([dict(row(n),summary='x'*32000) for n in range(80,0,-1)])
  with self.assertRaises(SnapshotUnavailable):create_geo_original_stream(c,review=R)
  self.assertEqual(c.session.ends,1);self.assertTrue(all(x.closed for x in c.cursors))
 def test_late_page_failure_is_incomplete_and_session_closed(self):
  class Late(Client):
   def find(self,*a,**k):
    c=super().find(*a,**k)
    if len(self.finds)==3:c.fail=True
    return c
  c=Late([row(n) for n in range(501,0,-1)]);s=create_geo_original_stream(c,review=R);data=b''.join(s)
  self.assertIn(b'EXPORT_INCOMPLETE',data);self.assertNotIn(b'secret-uri',data);self.assertEqual(c.session.ends,1);self.assertTrue(all(x.closed for x in c.cursors))

 def test_query_injection_rejected_before_find(self):
  from integration.news_export.keyset_plan import query_plan
  for query in ({'$where':'1'},{'$or':[],'$where':'1'},{'score':{'$gt':1}}):
   c=Client([row(2)]);snap=GeoSnapshot(c,review=R);snap.verify_scope('geo',(('score',-1),('published',-1),('_id',-1)))
   p=query_plan('geo');p['query']=query
   with self.assertRaises(SnapshotUnavailable) as e:snap.execute(p)
   self.assertIsNone(e.exception.__context__);self.assertEqual(len(c.finds),1);self.assertEqual(c.session.ends,1)
 def test_exception_context_does_not_retain_source_error(self):
  class Bad(Client):
   def start_session(self,**kw):raise ValueError('secret-uri')
  with self.assertRaises(SnapshotUnavailable) as e:create_geo_original_stream(Bad([]),review=R)
  self.assertIsNone(e.exception.__context__)

 def test_all_initial_execute_guards_close_exactly_once(self):
  from integration.news_export.keyset_plan import query_plan
  class Impostor(dict):pass
  for p in (None,{},dict(query_plan('geo'),project='brics'),Impostor(query_plan('geo'))):
   c=Client([row(1)]);snap=GeoSnapshot(c,review=R);snap.verify_scope('geo',(('score',-1),('published',-1),('_id',-1)))
   with self.assertRaises(SnapshotUnavailable) as e:snap.execute(p)
   self.assertIsNone(e.exception.__context__);self.assertEqual(str(e.exception),'Geo export page unavailable');self.assertEqual(c.session.ends,1);self.assertTrue(snap._closed);snap.close();self.assertEqual(c.session.ends,1);self.assertEqual(len(c.finds),1)
 def test_all_initial_scope_guards_close_exactly_once(self):
  order=(('score',-1),('published',-1),('_id',-1))
  for project,ordering in ((None,order),('brics',order),('geo',None),('geo',()),('geo',list(order))):
   c=Client([]);snap=GeoSnapshot(c,review=R)
   with self.assertRaises(SnapshotUnavailable) as e:snap.verify_scope(project,ordering)
   self.assertIsNone(e.exception.__context__);self.assertEqual(str(e.exception),'Geo export schema snapshot unavailable');self.assertEqual(c.session.ends,1);self.assertTrue(snap._closed);snap.close();self.assertEqual(c.session.ends,1);self.assertEqual(c.finds,[])
