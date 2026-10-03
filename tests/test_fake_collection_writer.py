import unittest
from unittest.mock import patch
from hashlib import sha256
from integration.fake_collection_writer import FakeCollectionWriter
NOW='2026-10-03T18:00:00+05:30'
def row(url='https://example.com/x'):
 return {'url':url,'title':'BRICS summit','source':'Fixture','summary':'Text','_id':'provider','id':'wrong','emailed':True,'created_at':'wrong','collected_at':'wrong'}
class FakeWriterTests(unittest.TestCase):
 def test_separate_identities_time_and_strip(self):
  w=FakeCollectionWriter();r=row();before=dict(r)
  with patch('socket.socket',side_effect=AssertionError('No network')):
   w.write('geo',[r],NOW);w.write('brics',[r],NOW)
  g=w.snapshot('geo')[r['url']];identity=sha256(r['url'].encode()).hexdigest();b=w.snapshot('brics')[identity]
  self.assertEqual(g['created_at'],'2026-10-03T12:30:00+00:00');self.assertEqual(b['collected_at'],g['created_at']);self.assertEqual(b['id'],identity);self.assertFalse(g['emailed']);self.assertFalse(b['emailed']);self.assertNotIn('_id',g);self.assertNotIn('_id',b);self.assertNotIn('id',g);self.assertEqual(r,before)
 def test_duplicates_failures_no_update_and_snapshot_isolation(self):
  w=FakeCollectionWriter();d=w.write('geo',[row(),row(),row('https://example.com/fail')],NOW,['https://example.com/fail'])
  self.assertEqual([r['state'] for r in d['results']],['inserted','duplicate','failed']);self.assertEqual((d['inserted_count'],d['duplicate_count'],d['failed_count']),(1,1,1))
  s=w.snapshot('geo');s.clear();self.assertEqual(len(w.snapshot('geo')),1);changed=row();changed['title']='Changed';w.write('geo',[changed],NOW);self.assertEqual(w.snapshot('geo')[changed['url']]['title'],'BRICS summit')
 def test_batch_validation_no_partial_change(self):
  w=FakeCollectionWriter()
  for rows,clock in [([row(),{}],NOW),([row()],'2026-10-03'),([row()]*1001,NOW),([dict(row(),x=object())],NOW),([dict(row(),x=float('nan'))],NOW)]:
   with self.assertRaises(ValueError):w.write('geo',rows,clock)
   self.assertEqual(w.snapshot('geo'),{})
 def test_nested_copy_and_no_collection_naming(self):
  w=FakeCollectionWriter();r=dict(row(),corroborated_by=['a','b']);w.write('brics',[r],NOW);r['corroborated_by'].append('c');self.assertEqual(next(iter(w.snapshot('brics').values()))['corroborated_by'],['a','b'])
