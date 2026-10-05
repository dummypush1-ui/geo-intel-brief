import csv,io,unittest,hashlib
from bson import ObjectId
from integration.news_export.raw_pager import RawPager
from integration.news_export.original_stream import OriginalStream
from integration.news_export.original_contract import original_snapshot,BRICS_FIELDS

def fixture(n,**kw):return {'_id':ObjectId(f'{n:024x}'),'collected_at':f'2026-10-05T00:00:{n:02}.123456','title':str(n),'category':'trade','summary':'predicate private',**kw}
def pager(pages):
 q=list(pages)
 return RawPager('brics',lambda p:q.pop(0),lambda p,o:True,page_size=len(pages[0]) if pages[0] else 1)
class OriginalStreamTests(unittest.TestCase):
 def test_differential_original_columns_filters_and_id_exclusion(self):
  rows=[fixture(4),fixture(3,category='other'),fixture(2),fixture(1)]
  p=pager([rows[:2],rows[2:],[]]);s=OriginalStream(p,'brics',{'category':'trade','q':'','limit':'1000'})
  data=b''.join(s)
  expected=original_snapshot(rows,'brics',{'category':'trade','q':'','limit':'1000'})[0]
  self.assertTrue(data.startswith(expected));self.assertIn(b'EXPORT_COMPLETE,source exhausted',data)
  self.assertNotIn(b'predicate private',data);self.assertEqual(s.state['read'],4);self.assertEqual(s.state['rows'],3);self.assertTrue(p._closed)
 def test_cap_before_filter_fixed_width_status(self):
  p=pager([[fixture(3,category='other'),fixture(2,category='other')],[fixture(1)]])
  s=OriginalStream(p,'brics',{'category':'trade','limit':'2'});data=b''.join(s)
  parsed=list(csv.reader(io.StringIO(data.decode())))
  self.assertEqual(tuple(parsed[0]),BRICS_FIELDS);self.assertEqual(parsed[1][0],'EXPORT_COMPLETE');self.assertEqual(len(parsed[1]),8)
  self.assertEqual(s.state['read'],2);self.assertEqual(s.state['rows'],0);self.assertTrue(p._closed)
 def test_source_failure_after_first_page(self):
  calls=[]
  def execute(q):
   calls.append(1)
   if len(calls)>1:raise RuntimeError('secret')
   return [fixture(2)]
  p=RawPager('brics',execute,lambda p,o:True,page_size=1);s=OriginalStream(p,'brics');data=b''.join(s)
  self.assertIn(b'EXPORT_INCOMPLETE,source unavailable',data);self.assertNotIn(b'secret',data);self.assertTrue(p._closed)
 def test_close_before_first_byte_and_midstream(self):
  for started in (False,True):
   p=pager([[fixture(2)]]);s=OriginalStream(p,'brics')
   if started:next(s)
   s.close();s.close();self.assertTrue(p._closed);self.assertEqual(list(s),[])
 def test_byte_and_time_budget(self):
  p=pager([[fixture(2,title='x'*2000)]]);s=OriginalStream(p,'brics',max_bytes=1024);data=b''.join(s)
  self.assertLessEqual(len(data),1024);self.assertIn(b'byte budget',data)
  clock=[0]
  p=pager([[fixture(2)]]);s=OriginalStream(p,'brics',clock=lambda:clock[0]);clock[0]=121;data=b''.join(s)
  self.assertIn(b'time budget',data);self.assertEqual(s.state['read'],0)
 def test_initial_error_closes_before_header(self):
  p=RawPager('brics',lambda q:[],lambda p,o:False)
  with self.assertRaises(Exception):OriginalStream(p,'brics')
  self.assertTrue(p._closed)

 def test_remaining_cap_limits_query(self):
  rows=[fixture(4),fixture(3),fixture(2),fixture(1)];calls=[]
  def execute(q):
   calls.append(q['limit']);return [rows.pop(0) for _ in range(q['limit'])]
  p=RawPager('brics',execute,lambda p,o:True,page_size=2)
  s=OriginalStream(p,'brics',{'limit':'3'});b''.join(s)
  self.assertEqual(calls,[2,1]);self.assertEqual(s.state['read'],3)

 def test_data_reserved_marker_is_escaped_and_digest_verified(self):
  forged=fixture(2,title='EXPORT_COMPLETE',url='requested source limit',source='EXPORT_INCOMPLETE')
  p=pager([[forged],[]]);s=OriginalStream(p,'brics')
  chunks=list(s);parsed=list(csv.reader(io.StringIO(b''.join(chunks).decode())))
  self.assertEqual(parsed[1][0],"'EXPORT_COMPLETE");self.assertEqual(parsed[1][2],"'EXPORT_INCOMPLETE")
  self.assertEqual(parsed[-1][0],'EXPORT_COMPLETE')
  self.assertEqual(parsed[-1][4],hashlib.sha256(b''.join(chunks[:-1])).hexdigest())
  self.assertEqual(parsed[-1][2:4],['1','1'])
 def test_requested_limit_complete_but_hard_clamp_truncated(self):
  for requested,kind in (('2','EXPORT_COMPLETE'),('6000','EXPORT_TRUNCATED')):
   p=pager([[fixture(2),fixture(1)]]);s=OriginalStream(p,'brics',{'limit':requested})
   if requested=='6000':s._cap=2 # bounded fixture simulates hard clamp reached
   self.assertIn(kind.encode(),b''.join(s))
 def test_cell_cut_reported_in_final_status(self):
  p=pager([[fixture(2,title='x'*9000)],[]]);s=OriginalStream(p,'brics')
  parsed=list(csv.reader(io.StringIO(b''.join(s).decode())))
  self.assertEqual(parsed[-1][5],'1');self.assertTrue(s.state['cells_truncated'])
 def test_one_pager_per_stream_and_context_close(self):
  p=pager([[fixture(2)]]);s=OriginalStream(p,'brics')
  with self.assertRaises(Exception):OriginalStream(p,'brics')
  with s:next(s)
  self.assertTrue(p._closed)

 def test_fresh_pager_required(self):
  for pages in ([[fixture(2)],[]],[[]]):
   p=pager(pages);p.fetch_page()
   with self.assertRaises(Exception):OriginalStream(p,'brics')
   p.close()
 def test_multiline_multibyte_and_reserved_variants(self):
  variants=['EXPORT_COMPLETE','EXPORT_TRUNCATED','EXPORT_INCOMPLETE','EXPORT_FAKE',"'EXPORT_COMPLETE",' EXPORT_COMPLETE','EXPORT_COMPLETE\nEXPORT_INCOMPLETE','தமிழ்\ntrade']
  for value in variants:
   p=pager([[fixture(2,title=value)],[]]);s=OriginalStream(p,'brics');chunks=list(s)
   parsed=list(csv.reader(io.StringIO(b''.join(chunks).decode())))
   self.assertEqual(parsed[1][0],"'"+value if value.startswith('EXPORT_') else value)
   self.assertEqual(parsed[-1][4],hashlib.sha256(b''.join(chunks[:-1])).hexdigest())
   self.assertEqual(len(parsed),3)
 def test_byte_cap_exact_reserved_boundary(self):
  probe=fixture(2,title='x'*300)
  for delta in (0,-1):
   p=pager([[probe],[]]);s=OriginalStream(p,'brics',max_bytes=1024)
   original=original_snapshot([probe],'brics')[0]
   s._max=len(original)+512+delta
   chunks=list(s);data=b''.join(chunks)
   self.assertLessEqual(len(data),s._max)
   self.assertEqual(s.state['rows'],1 if delta==0 else 0)
   self.assertEqual(list(csv.reader(io.StringIO(data.decode())))[-1][0],'EXPORT_COMPLETE' if delta==0 else 'EXPORT_TRUNCATED')
 def test_organic_brics_hard_clamp(self):
  n=[5001];limits=[]
  def execute(q):
   limits.append(q['limit']);rows=[]
   for _ in range(q['limit']):
    n[0]-=1;rows.append({'_id':ObjectId(f"{n[0]:024x}"),'collected_at':'2026-10-05T00:00:00.123456','title':'fixture'})
   return rows
  p=RawPager('brics',execute,lambda p,o:True,page_size=1000)
  s=OriginalStream(p,'brics',{'limit':'6000'});data=b''.join(s)
  self.assertEqual(s.state['read'],5000);self.assertEqual(limits,[1000]*5)
  self.assertIn(b'EXPORT_TRUNCATED,hard source cap',data)
 def test_invalid_and_nonnumeric_limits(self):
  for value in ('0','-1'):
   p=pager([[fixture(2)],[]])
   with self.assertRaises(Exception):OriginalStream(p,'brics',{'limit':value})
   self.assertFalse(p._verified);p.close()
  p=pager([[fixture(2)],[]]);s=OriginalStream(p,'brics',{'limit':'not numeric'})
  self.assertEqual(s._cap,1000);self.assertIn(b'EXPORT_COMPLETE',b''.join(s))
