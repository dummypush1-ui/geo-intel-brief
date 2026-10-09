import unittest
from datetime import datetime,timedelta,timezone,tzinfo
from bson import ObjectId
from integration.digest_dates202 import normalize_date,select_normalized
N=datetime(2026,10,9,12,tzinfo=timezone.utc)
R={'email':(),'telegram':(),'whatsapp':()}
def row(**kw):
 r={'_id':ObjectId(),'title':'Story','score':5,'published':N.isoformat(),'created_at':N.isoformat()};r.update(kw);return r
def select(rows,**kw):return select_normalized(rows,N,date_field=kw.pop('date_field','published'),channel=kw.pop('channel','email'),displayed_receipts=kw.pop('displayed_receipts',R),**kw)
class Tests(unittest.TestCase):
 def test_equivalent_offsets_datetime_and_microseconds(self):
  want='2026-10-09T12:00:00.123456+00:00'
  for v in ('2026-10-09T14:00:00.123456+02:00','2026-10-09T12:00:00.123456Z',N.replace(microsecond=123456)):
   self.assertEqual(normalize_date(v),want)
 def test_naive_missing_invalid_and_nonstandard_strings_refused(self):
  for v in (None,False,0,N.replace(tzinfo=None),'2026-10-09','2026-10-09T12:00:00',' 2026-10-09T12:00:00Z','20261009T120000Z','2026-10-09T12:00:00.1234567Z','2026-10-09T12:00:00.1Z','2026-10-09T12:00:00.12Z','2026-10-09T12:00:00.1234Z','2026-10-09T12:00:00.12345Z','2026-02-30T12:00:00Z','2026-10-09T12:00:00+99:00','2026-10-09T12:00:00+00:99','2026-10-09T12:00:00-00:00'):
   with self.subTest(v=v),self.assertRaises(ValueError):normalize_date(v)
 def test_datetime_overflow_and_custom_timezone_not_called(self):
  class Trap(tzinfo):
   def utcoffset(self,dt):raise AssertionError('custom callback')
  for v in (N.replace(tzinfo=Trap()),datetime(1,1,1,tzinfo=timezone(timedelta(hours=1)))):
   with self.assertRaises(ValueError):normalize_date(v)
 def test_normalized_chronological_order_not_lexical_order(self):
  a=row(published='2026-10-09T14:00:00+03:00');b=row(published='2026-10-09T11:30:00Z')
  x=select([a,b]);self.assertEqual([r['_id']for r in x['sections']['last_24h']['rows']],[b['_id'],a['_id']])
 def test_explicit_policy_two_dates_required_even_ignored(self):
  a=row(published=(N-timedelta(days=3)).isoformat(),created_at=N)
  self.assertEqual(select([a])['sections']['last_24h']['rows'],[])
  self.assertEqual(len(select([a],date_field='created_at')['sections']['last_24h']['rows']),1)
  for bad in (row(published=None),row(created_at=None),row(published='bad',score=0)):
   with self.assertRaises(ValueError):select([bad],displayed_receipts=dict(R,email=(bad['_id'],)))
 def test_boundaries_future_and_channels_remain_193_semantics(self):
  a=row(published=N-timedelta(days=1));b=row(published=N-timedelta(days=7));c=row(published=N+timedelta(microseconds=1))
  x=select([a,b,c]);self.assertEqual(set(x['displayed_union_ids']),{a['_id'],b['_id']})
  self.assertNotIn(a['_id'],select([a],displayed_receipts=dict(R,email=(a['_id'],)))['displayed_union_ids'])
  self.assertIn(a['_id'],select([a],channel='telegram',displayed_receipts=dict(R,email=(a['_id'],)))['displayed_union_ids'])
 def test_no_mutation_equivalent_snapshot_and_no_live_claim(self):
  a=row();b=dict(a,published=N,created_at=N);x=select([a]);y=select([b]);self.assertEqual(x['snapshot_id'],y['snapshot_id']);self.assertEqual(y['date_adapter']['input_kinds'],{'strings':0,'aware_datetimes':2})
  x['sections']['last_24h']['rows'][0]['title']='changed';self.assertEqual(a['title'],'Story');self.assertFalse(y['unsent_queue_verified']);self.assertFalse(y['writes']);self.assertFalse(y['network']);self.assertIsNone(y['date_adapter']['raw_mongo_query'])
 def test_closed_projection_bounds_full_193_validation(self):
  for rows in ([row()]*1001,[row(extra='secret')],[row(title='x'*16001)],[row(score=True)],[row(emailed=[])],[row(url='\ud800')]):
   with self.assertRaises(ValueError):select(rows)
  with self.assertRaises(ValueError):select([row(title='x'*16000)for _ in range(140)])
  a=row()
  with self.assertRaises(ValueError):select([a,a])
  with self.assertRaises(ValueError):select([row()],date_field='auto')
