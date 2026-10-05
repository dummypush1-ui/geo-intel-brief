import unittest
import csv,io
from datetime import datetime
from integration.news_export.original_contract import original_snapshot
from bson import ObjectId
from integration.news_export.keyset_plan import query_plan,resume,page_resume,Resume,KeysetPlanError
from integration.news_export.original_contract import GEO_FIELDS,BRICS_FIELDS
I=ObjectId('000000000000000000000003')
def geo(score=5,published='2026-10-04T00:00:00+00:00',identity=I):return {'score':score,'published':published,'_id':identity,'title':'fixture','private':'never projected'}
class KeysetPlanTests(unittest.TestCase):
 def test_original_orders_and_closed_projection(self):
  g=query_plan('geo');self.assertEqual(g['sort'],[('score',-1),('published',-1),('_id',-1)]);self.assertEqual(set(g['projection']),set(GEO_FIELDS)|{'_id'});self.assertEqual(g['query'],{});self.assertEqual(g['max_time_ms'],2000)
  b=query_plan('brics');self.assertEqual(b['sort'],[('collected_at',-1),('_id',-1)]);self.assertEqual(set(b['projection']),set(BRICS_FIELDS)|{'_id','summary'})
 def test_geo_lexicographic_continuation(self):
  q=query_plan('geo',resume('geo',geo()))['query'];self.assertEqual(q,{'$or':[{'score':{'$lt':5}},{'score':5,'published':{'$lt':'2026-10-04T00:00:00+00:00'}},{'score':5,'published':'2026-10-04T00:00:00+00:00','_id':{'$lt':I}}]})
 def test_duplicates_and_reordering_refused(self):
  rows=[geo(identity=ObjectId('000000000000000000000003')),geo(identity=ObjectId('000000000000000000000002')),geo(score=4)]
  last=page_resume('geo',rows);self.assertEqual(last.values[0],4)
  for bad in ([rows[0],rows[0]],list(reversed(rows))):
   with self.assertRaises(KeysetPlanError):page_resume('geo',bad)
  with self.assertRaises(KeysetPlanError):page_resume('geo',[rows[0]],last)
 def test_mixed_missing_and_invalid_values_refused(self):
  for patch in ({'score':None},{'score':True},{'score':float('nan')},{'published':None},{'published':'naive'},{'published':'2026-10-04'},{'_id':str(I)}):
   with self.assertRaises(KeysetPlanError):resume('geo',{**geo(),**patch})
  for limit in (True,0,1001):
   with self.assertRaises(KeysetPlanError):query_plan('geo',limit=limit)
  for after in ({'score':5},Resume('brics',(1,)),Resume('geo',(5,'bad',I))):
   with self.assertRaises(KeysetPlanError):query_plan('geo',after)
 def test_brics_page_and_empty_continuation(self):
  r={'collected_at':'2026-10-04T00:00:00.000001','_id':I};last=page_resume('brics',[r]);self.assertEqual(page_resume('brics',[],last),last);self.assertEqual(query_plan('brics',last)['query']['$or'][0],{'collected_at':{'$lt':r['collected_at']}})

 def test_real_producer_format_and_brics_id_tie(self):
  stamp=datetime.utcnow().isoformat()
  r={'collected_at':stamp,'_id':I}
  smaller={**r,'_id':ObjectId('000000000000000000000002')}
  last=page_resume('brics',[r,smaller],limit=2)
  self.assertEqual(last.values,(stamp,smaller['_id']))
  self.assertEqual(query_plan('brics',resume('brics',r))['query']['$or'][1],{'collected_at':stamp,'_id':{'$lt':I}})
  for value in (stamp+'Z',stamp+'+00:00','2026-10-04','2026-10-04T00:00:00.1'):
   with self.assertRaises(KeysetPlanError):resume('brics',{**r,'collected_at':value})
 def test_page_limit_and_numeric_equality(self):
  with self.assertRaises(KeysetPlanError):page_resume('geo',[geo(),geo(score=4)],limit=1)
  self.assertEqual(resume('geo',geo(5)).values,resume('geo',geo(5.0)).values)
  with self.assertRaises(KeysetPlanError):page_resume('geo',[geo(5),geo(5.0)],limit=2)
  self.assertEqual(page_resume('geo',[geo(5),geo(4.9)],limit=2).values[0],4.9)
 def test_raw_page_to_original_serializer_closed_columns(self):
  # Fixture handoff only, no production database adapter exists.
  rows=[{'collected_at':'2026-10-04T00:00:00.000001','_id':I,'summary':'PRIVATE PREDICATE TEXT','title':'fixture'}]
  page_resume('brics',rows,limit=1)
  data,headers,meta=original_snapshot(rows,'brics')
  decoded=list(csv.reader(io.StringIO(data.decode())))
  self.assertEqual(tuple(decoded[0]),BRICS_FIELDS)
  self.assertNotIn(str(I),data.decode());self.assertNotIn('PRIVATE PREDICATE TEXT',data.decode())
