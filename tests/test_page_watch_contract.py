"""Offline snapshot integrity contract, not source/time authenticity."""
import unittest,copy,hashlib
from integration.page_watch import snapshot,validate_snapshot,compare
U='https://nilgiried.com/'
H='<p>Sample visible event detail with enough text for baseline</p>'
class ContractTests(unittest.TestCase):
 def snap(self,text='Sample visible event detail with enough text for baseline',stamp='2026-10-05T10:00:00Z',url=U):
  return {'url':url,'observed_at':stamp,'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'method':'page_change_snapshot'}
 def test_utc_idempotence_and_fresh_copy(self):
  a=self.snap(stamp='2026-10-05T15:30:00+05:30',url='HTTPS://NILGIRIED.COM:443#one')
  b=validate_snapshot(a);self.assertEqual(b['observed_at'],'2026-10-05T10:00:00.000000+00:00');self.assertEqual(b['url'],U)
  self.assertEqual(validate_snapshot(b),b);self.assertIsNot(a,b);b['text']='mutated';self.assertNotEqual(a['text'],b['text'])
 def test_older_offset_and_equal_conflict(self):
  a=self.snap();b=self.snap(text='Changed visible content sufficiently long',stamp='2026-10-05T15:00:00+06:00')
  with self.assertRaises(ValueError):compare(a,b)
  with self.assertRaisesRegex(ValueError,'equal-time'):compare(a,self.snap(text=b['text']))
  self.assertEqual(compare(a,self.snap(stamp='2026-10-05T15:30:00+05:30'))['state'],'unchanged')
 def test_url_limited_equivalence_query_retained(self):
  a=self.snap(url='http://EXAMPLE.com:80?q=A%20B#one');b=validate_snapshot(a)
  self.assertEqual(b['url'],'http://example.com/?q=A%20B')
  for url in ['https://user@example.com','https://x:bad/','https://x:65536/','https://é.com/','https://x/\\evil','https://x/ space','https://x/\x7f','file:///x','https://x/'+('a'*2049),'https://x/\ud800']:
   with self.subTest(url=repr(url)):
    with self.assertRaises(ValueError):validate_snapshot(self.snap(url=url))
 def test_stamp_bounds(self):
  for stamp in ['2026-01-01','2026-01-01T10:00:00','1969-12-31T00:00:00Z','2101-01-01T00:00:00Z','2026-01-01T00:00:00+24:00','x'*65]:
   with self.assertRaises(ValueError):validate_snapshot(self.snap(stamp=stamp))
 def test_caps_before_hash_diff_and_plain_types(self):
  for text in ['x\n'*20001,'x'*100001,'தமிழ்'*200000,'x\ud800'*20]:
   a=self.snap() if '\ud800' in text else self.snap(text=text)
   if '\ud800' in text:a['text']=text
   with self.assertRaises(ValueError):validate_snapshot(a)
  a=self.snap();a['sha256']=a['sha256'].upper()
  with self.assertRaises(ValueError):validate_snapshot(a)
  for a in [dict(self.snap(),extra='x'),dict(self.snap(),text=True),dict(self.snap(),method='other')]:
   with self.assertRaises(ValueError):validate_snapshot(a)
  class Evil(str):pass
  a=self.snap();a['text']=Evil(a['text'])
  with self.assertRaises(ValueError):validate_snapshot(a)
 def test_diff_budget_short_and_identical_lines(self):
  for atext,btext in [('x\n'*2000,'y\n'*2000),('same\n'*2000,'same\n'*1999+'new line')]:
   a=self.snap(text=atext);b=self.snap(text=btext,stamp='2026-10-05T10:00:01Z');r=compare(a,b)
   self.assertEqual(r['state'],'changed');self.assertTrue(r['diff_omitted']);self.assertIn('diff omitted',r['items'][0]['summary'])
  a=self.snap(text='same\n'*2000);self.assertEqual(compare(a,a)['state'],'unchanged')
 def test_golden_diff_and_no_mutation(self):
  a=self.snap(text='Sample visible event detail\nOld value');b=self.snap(text='Sample visible event detail\nNew value',stamp='2026-10-05T10:00:01Z')
  before=copy.deepcopy((a,b));r=compare(a,b)
  self.assertEqual((a,b),before);self.assertEqual(r['items'][0]['summary'],'--- previous observation\n+++ current observation\n@@ -1,2 +1,2 @@\n Sample visible event detail\n-Old value\n+New value')
  self.assertFalse(r['diff_omitted']);self.assertFalse(r['diff_truncated']);self.assertEqual(r['items'][0]['published'],'')
