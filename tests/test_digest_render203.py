import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from bson import ObjectId
from integration.digest_render203 import render_preview
N=datetime(2026,10,9,12,tzinfo=timezone.utc);R={'email':(),'telegram':(),'whatsapp':()}
def row(**kw):
 r={'_id':ObjectId(),'title':'Fixture story','summary':'Supplied preview, not sent.','url':'https://example.com/news','source':'Fixture','category':'TRADE','score':5,'published':N.isoformat(),'created_at':N.isoformat()};r.update(kw);return r
def render(rows,**kw):return render_preview(rows,N,date_field=kw.pop('date_field','published'),channel=kw.pop('channel','email'),displayed_receipts=kw.pop('displayed_receipts',R),offset_minutes=kw.pop('offset_minutes',330),zone_label=kw.pop('zone_label','IST'),**kw)
class Tests(unittest.TestCase):
 def test_overlap_distinct_counts_precap_and_deterministic_cut(self):
  rows=[row()for _ in range(65)];x=render(rows);self.assertEqual(x['sections']['last_24h'],{'shown':60,'eligible':65});self.assertEqual(x['selection_only_union_pre_cap_count'],65);self.assertEqual(len(x['selection_only_union_ids']),60);self.assertEqual(x['omitted_section_occurrences'],{'last_24h':5,'last_7days':5});self.assertEqual(x['html'].count('Showing 60 of 65'),2);self.assertIn('includes last 24 hours',x['html'])
 def test_no_mutation_no_selection_input_byte_determinism(self):
  rows=[row()];original=deepcopy(rows);a=render(rows);b=render(rows);self.assertEqual(rows,original);self.assertEqual(a['html'].encode(),b['html'].encode());self.assertEqual(a['text'],b['text']);self.assertFalse(a['delivery']);self.assertFalse(a['network'])
  with self.assertRaises(ValueError):render(a)
 def test_snapshot_integrity_timezone_and_no_ids_rendered(self):
  a=row();x=render([a]);self.assertIn(x['snapshot_id'],x['html']);self.assertIn('2026-10-09T17:30:00.000000+05:30 IST (UTC+05:30)',x['text']);self.assertIn('date policy and receipts unverified',x['html']);self.assertNotIn(str(a['_id']),x['html']);self.assertNotIn(str(a['_id']),x['text'])
  for kw in ({'offset_minutes':True},{'zone_label':'X\nY'},{'offset_minutes':1440}):
   with self.assertRaises(ValueError):render([a],**kw)
 def test_unknown_missing_empty_categories_visible_other(self):
  for cat in ('UNKNOWN','',None):
   a=row()
   if cat is None:a.pop('category')
   else:a['category']=cat
   x=render([a]);self.assertIn('<h3>Other</h3>',x['html']);self.assertEqual(x['sections']['last_24h']['shown'],1)
 def test_hostile_text_escape_bidi_controls_plain_line_safety(self):
  x=render([row(title='<script>\nA\u202eB\x00C',summary='x\r\nFake header:',source='<bad>',url='https://example.com/?x="bad"&y=1')]);self.assertNotIn('<script>',x['html']);self.assertIn('&lt;script&gt;',x['html']);self.assertNotIn('\u202e',x['html']);self.assertIn('rel="noopener noreferrer"',x['html']);self.assertIn('&quot;bad&quot;&amp;',x['html']);self.assertIn('x Fake header:',x['text']);self.assertNotIn('\r',x['text'])
 def test_invalid_url_whole_render_held_even_excluded(self):
  for url in ('javascript:alert(1)','data:text/html,x','https://u:p@example.com/x','https://example.com/a b','https://example.com/x\nY','https://example.com:99999','https://example.com/\u202ex','https://example.com/'+('x'*2048)):
   a=row(url=url,published=(N-timedelta(days=30)).isoformat())
   with self.subTest(url=url),self.assertRaises(ValueError):render([a],displayed_receipts=dict(R,email=(a['_id'],)))
  with self.assertRaises(ValueError):render([row(url='http://example.com/')])
 def test_bytecap_failclosed_no_reduced_rows(self):
  with self.assertRaisesRegex(ValueError,'byte cap'):render([row(summary='x'*16000)for _ in range(60)])
 def test_empty_and_category_order(self):
  x=render([]);self.assertIn('Showing 0 of 0',x['html']);self.assertIn('events not supplied',x['html']);self.assertEqual(x['selection_only_union_pre_cap_count'],0)
  x=render([row(category='UNKNOWN'),row(category='GENERAL'),row(category='TRADE'),row(category='GEOPOLITICS')]);self.assertLess(x['html'].index('<h3>Geopolitics'),x['html'].index('<h3>Trade Activity'));self.assertLess(x['html'].index('<h3>Trade Activity'),x['html'].index('<h3>Other'));self.assertEqual(x['html'].count('<h3>Other</h3>'),2)
