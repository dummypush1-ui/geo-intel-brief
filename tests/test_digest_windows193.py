import unittest
from datetime import datetime,timedelta,timezone
from bson import ObjectId
from integration.digest_windows193 import select_supplied,query_plan
N=datetime(2026,10,9,12,tzinfo=timezone.utc)
def row(days=0,score=5,**kw):
 r={'_id':ObjectId(),'title':'Story','score':score,'published':(N-timedelta(days=days)).isoformat(),'created_at':(N-timedelta(days=days)).isoformat()};r.update(kw);return r
R={'email':(),'telegram':(),'whatsapp':()}
def select(rows,**kw):return select_supplied(rows,N,date_field=kw.pop('date_field','published'),channel=kw.pop('channel','email'),displayed_receipts=kw.pop('displayed_receipts',R),**kw)
class Tests(unittest.TestCase):
 def test_one_digest_both_windows_future_old_high_score_excluded(self):
  a,b,c,d=row(),row(3),row(8,99),row(-1,90);x=select([c,d,b,a]);self.assertEqual([r['_id']for r in x['sections']['last_24h']['rows']],[a['_id']]);self.assertEqual(set(x['displayed_union_ids']),{a['_id'],b['_id']});self.assertEqual(len(x['sections']['last_7days']['rows']),2);self.assertIsNone(x['plan']['raw_mongo_query'])
 def test_all_time_displayed_receipt_per_channel_no_inferred_emailed(self):
  a=row(emailed=True);b=row();rec=dict(R,email=(a['_id'],));x=select([a,b],displayed_receipts=rec);self.assertEqual(x['displayed_union_ids'],(b['_id'],));y=select([a,b],channel='telegram',displayed_receipts=rec);self.assertIn(a['_id'],y['displayed_union_ids']);self.assertFalse(y['unsent_queue_verified']);self.assertFalse(y['writes'])
 def test_explicit_date_policy_missing_clock_and_bad_gate(self):
  a=row(3,created_at=N.isoformat());self.assertEqual(len(select([a])['sections']['last_24h']['rows']),0);self.assertEqual(len(select([a],date_field='created_at')['sections']['last_24h']['rows']),1)
  for kw in ({'date_field':'auto'},{'channel':'all'},{'limit':True},{'displayed_receipts':{}},{'displayed_receipts':dict(R,email=['bad'])}):
   with self.assertRaises(ValueError):select([a],**kw)
  with self.assertRaises(ValueError):query_plan(N.replace(tzinfo=None),date_field='published',channel='email')
 def test_full_validation_before_receipt_time_score_exclusion(self):
  for bad in (row(20,0,published='bad'),row(0,score=True),row(0,emailed=[]),row(0,title=None),row(0,private='no'),row(0,title='x'*16001)):
   with self.assertRaises(ValueError):select([bad],displayed_receipts=dict(R,email=(bad['_id'],)))
  with self.assertRaises(ValueError):select([row()]*2)
 def test_bounds_offsets_inclusive_and_deterministic_tie(self):
  a=row(1);b=row(7);x=select([a,b]);self.assertIn(a['_id'],x['displayed_union_ids']);self.assertIn(b['_id'],x['displayed_union_ids']);a['published']='2026-10-09T14:00:00+02:00';self.assertEqual(len(select([a])['sections']['last_24h']['rows']),1)
  rows=[row()for _ in range(65)]+[row(score=0)for _ in range(50)];x=select(rows);self.assertEqual(len(x['displayed_union_ids']),60);self.assertTrue(x['sections']['last_24h']['truncated']);self.assertEqual(x['snapshot_id'],select(rows)['snapshot_id'])
 def test_empty_input_copy_no_state_mutation_snapshot_bound_to_channel_date_receipts(self):
  self.assertEqual(select([])['displayed_union_ids'],());a=row();x=select([a]);x['sections']['last_24h']['rows'][0]['title']='Changed';self.assertEqual(a['title'],'Story');self.assertNotEqual(x['snapshot_id'],select([a],channel='telegram')['snapshot_id']);self.assertNotEqual(x['snapshot_id'],select([a],date_field='created_at')['snapshot_id']);self.assertNotEqual(x['snapshot_id'],select([a],displayed_receipts=dict(R,email=(a['_id'],)))['snapshot_id'])
