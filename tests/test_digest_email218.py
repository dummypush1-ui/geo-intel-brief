import copy,json,re,sys,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from bson import ObjectId
from integration import digest_email218 as seam
N=datetime(2026,10,10,23,30,tzinfo=timezone.utc)
R={'email':(),'telegram':(),'whatsapp':()}
def row(i=1,**kw):
 d={'_id':ObjectId(f'{i:024x}'),'title':'Fixture story','summary':'Supply chains and trade update.','source':'Fixture source','category':'TRADE','url':'https://example.invalid/story','score':5,'published':N.isoformat(),'created_at':N.isoformat()};d.update(kw);return d
def render(rows,**kw):
 args={'rows':rows,'now':N,'date_field':'published','displayed_receipts':R,'offset_minutes':330,'offset_label':'+05:30','limit':60};args.update(kw);return seam.render_candidate(enabled=True,**args)
class Tests(unittest.TestCase):
 def test_off_hostile_no_dependencies(self):
  class Hostile:
   def __getattribute__(self,k):raise AssertionError('touch')
  self.assertEqual(seam.render_candidate(rows=Hostile())['state'],'disabled')
  for v in (1,None,'true'):
   with self.assertRaises(ValueError):seam.render_candidate(enabled=v)
 def test_boundaries_overlap_union_order(self):
  rows=[row(1,published=(N-timedelta(hours=24)).isoformat()),row(2,published=(N-timedelta(days=7)).isoformat()),row(3,published=(N-timedelta(days=7,seconds=1)).isoformat()),row(4,published=(N+timedelta(seconds=1)).isoformat()),row(5)]
  x=render(rows)['candidate'];self.assertEqual(x['sections'][0]['ids'],[f'{5:024x}',f'{1:024x}']);self.assertEqual(x['sections'][1]['ids'],[f'{5:024x}',f'{1:024x}',f'{2:024x}']);self.assertEqual(x['sorted_union_ids'],[f'{i:024x}'for i in (1,2,5)])
  self.assertIn('includes last 24 hours',x['html'])
 def test_ties_and_exclusions_input_copy(self):
  rows=[row(1),row(2),row(3)];before=copy.deepcopy(rows);x=render(rows,displayed_receipts={**R,'email':(rows[1]['_id'],)})
  self.assertEqual(rows,before);self.assertEqual(x['candidate']['sections'][0]['ids'],[f'{3:024x}',f'{1:024x}']);y=render(rows);z=render(rows);self.assertEqual(y,z);y['candidate']['sections'][0]['ids'].clear();self.assertTrue(z['candidate']['sections'][0]['ids'])
 def test_fixed_shift_midnight_subject_utc(self):
  x=render([row(title='TITLE\r\nHEADER')])['candidate'];self.assertIn('2026-10-11T05:00:00.000000+05:30',x['html']);self.assertIn('2026-10-10T23:30:00.000000+00:00',x['subject']);self.assertNotIn('TITLE',x['subject'])
  for v in ('IST','+5:30','+05:31','-00:00','+05:30\n'):
   with self.assertRaises(ValueError):render([row()],offset_label=v)
 def test_text_html_same_order_escape_control_policy(self):
  x=render([row(1,title='&<>\"\'\x00A\u202eB\u200bC\x85D',summary='<script>bad</script>',url='https://example.invalid/?q="&x=1'),row(2)])['candidate']
  htmlids=re.findall(r'data-article-id="([a-f0-9]{24})"',x['html']);textids=re.findall(r'^Article ID: ([a-f0-9]{24})$',x['text'],re.M);self.assertEqual(htmlids,textids)
  for s in ('\x00','\u202e','\u200b','\x85'):self.assertNotIn(s,x['html']);self.assertNotIn(s,x['text'])
  for s in ('&amp;','&lt;','&gt;','&quot;','&#x27;'):self.assertIn(s,x['html'])
  self.assertNotIn('<script>',x['html']);self.assertIn('&quot;&amp;',x['html']);self.assertNotRegex(x['html'],r'<(?:style|script|img|link)\b')
 def test_unsafe_urls_refuse_whole_even_excluded(self):
  for url in ('javascript:x','data:text/plain,x','mailto:a@b.invalid','https://u:p@example.invalid','https://example.invalid/a b','https://example.invalid/x\n','https://example.invalid/\u202e','https://example.invalid:99999'):
   a=row(url=url,published=(N-timedelta(days=30)).isoformat())
   with self.assertRaises(ValueError):render([a],displayed_receipts={**R,'email':(a['_id'],)})
 def test_skip_has_no_sendable_fields(self):
  p=render([]);self.assertTrue(p['skip']);self.assertEqual(set(p),{'state','skip','send_allowed','ready','archive_proof'});self.assertFalse(p['send_allowed']);self.assertFalse(p['ready']);self.assertFalse(p['archive_proof'])
  for k in ('candidate','html','text','subject','content_digest'):self.assertNotIn(k,p)
 def test_invalid_types_dates_duplicates_cap(self):
  class S(str):
   def encode(self,*a):raise AssertionError()
  class DT(datetime):pass
  for a in [row(title=S('x')),row(score=True),row(score=float('nan')),row(published=DT(2026,10,10,tzinfo=timezone.utc)),row(title='\ud800')]:
   with self.assertRaises(ValueError):render([a])
  for kw in ({'now':N.replace(tzinfo=None)},{'now':DT(2026,10,10,tzinfo=timezone.utc)},{'limit':True},{'offset_minutes':True},{'date_field':S('published')}):
   with self.assertRaises(ValueError):render([row()],**kw)
  a=row()
  with self.assertRaises(ValueError):render([a,a])
  with self.assertRaises(ValueError):render([row(i+1)for i in range(1001)])
 def test_digest_every_field_and_order(self):
  p=render([row(1),row(2)]);c=p['candidate'];self.assertEqual(seam._digest(c),p['content_digest'])
  for k in c:
   changed=copy.deepcopy(c)
   if type(changed[k])is str:changed[k]+='X'
   elif type(changed[k])is bool:changed[k]=not changed[k]
   elif type(changed[k])is int:changed[k]+=1
   else:changed[k].reverse()
   self.assertNotEqual(seam._digest(changed),p['content_digest'],k)
  changed=copy.deepcopy(c);changed['sections'][0]['ids'].reverse();self.assertNotEqual(seam._digest(changed),p['content_digest'])
  changed=copy.deepcopy(c);changed['sorted_union_ids'][0]='f'*24;self.assertNotEqual(seam._digest(changed),p['content_digest'])
 def test_caps_multibyte_exact(self):
  # Exact combined boundary independent of rendered markup overhead.
  for delta in (-1,0,1):
   n=seam.COMBINED_CAP+delta;subject='€'*(n//3)+'a'*(n%3)
   if delta<=0:self.assertEqual(sum(seam._bytes(subject,'','')),n)
   else:
    with self.assertRaises(ValueError):seam._bytes(subject,'','')
  for delta in (-1,0,1):
   n=seam.HTML_CAP+delta;h='€'*(n//3)+'a'*(n%3)
   if delta<=0:self.assertEqual(seam._bytes('',h,'')[1],n)
   else:
    with self.assertRaises(ValueError):seam._bytes('',h,'')
  with self.assertRaises(ValueError):render([row(i+1,summary='€'*16000)for i in range(10)])
 def test_union_bound_and_static_flags(self):
  rows=[row(i+1,published=(N-timedelta(days=2)).isoformat() if i>=60 else N.isoformat())for i in range(120)]
  x=render(rows);self.assertLessEqual(len(x['candidate']['sorted_union_ids']),120)
  for k in ('send_allowed','ready','archive_proof'):self.assertIs(x[k],False)
 def test_failure_fixed_no_chain_no_current_import(self):
  with self.assertRaises(ValueError)as c:render([row(url='SECRET_CANARY')])
  self.assertEqual(str(c.exception),'Email candidate held');self.assertIsNone(c.exception.__cause__);self.assertIsNone(c.exception.__context__)
  root=Path(seam.__file__).parents[1]
  for p in (root/'production_entry.py',root/'integration/mail_surface217.py',root/'feature_mail_mount/bridge.gs'):
   self.assertNotIn('digest_email218',p.read_text())
