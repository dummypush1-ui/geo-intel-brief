import unittest,copy
from datetime import datetime,timezone,tzinfo
from integration.tariff_evidence import TariffEvidenceSnapshot
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row():return {'id':'fixture-1','jurisdiction':'IN','nomenclature':'HSN','edition':'fixture-2026','codes':['21069051'],'document_id':'Fixture notification, not live duty','source_url':'https://www.indiabudget.gov.in/doc/cen/cus0326.pdf','published_date':'2026-02-01','effective_dates':['2026-04-01','2026-05-01'],'excerpt':'Fixture excerpt <script>bad</script>','conditions':'Fixture only, not real legal interpretation','review_state':'candidate','reviewed_at':None}
class PlainTests(unittest.TestCase):
 def test_no_copy_hook(self):
  calls=[]
  class Hook:
   def __deepcopy__(self,memo):calls.append('copy');return 'valid text'
   def __str__(self):calls.append('str');return 'valid text'
  for field in row():
   r=row();r[field]=Hook()
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
  self.assertEqual(calls,[])
 def test_no_datetime_hook(self):
  calls=[]
  class Zone(tzinfo):
   def utcoffset(self,dt):calls.append('offset');raise AssertionError('hook')
  s=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row()])
  with self.assertRaises(ValueError):s.view(datetime(2026,10,5,tzinfo=Zone()))
  self.assertEqual(calls,[])
 def test_mutation_and_valid_shape(self):
  r=row();before=copy.deepcopy(r);s=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r]);r['codes'].append('99')
  d=s.view(NOW);self.assertEqual(d['items'][0]['codes'],before['codes']);d['items'][0]['codes'].append('88');self.assertEqual(s.view(NOW)['items'][0]['codes'],before['codes'])
 def test_timestamp_bounds_and_bad_scalars(self):
  for stamp in ['x'*65,'1969-01-01T00:00:00Z','2101-01-01T00:00:00Z','2026-01-01','2026-01-01T00:00:00+24:00']:
   with self.assertRaises(ValueError):TariffEvidenceSnapshot(stamp,[row()])
  for key,v in [('codes',[True]),('effective_dates',[12]),('excerpt','x\ud800'),('id',True)]:
   r=row();r[key]=v
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_aggregate_bytes_before_retention(self):
  rows=[dict(row(),id=str(n),excerpt='界'*2000,conditions='界'*1000) for n in range(1000)]
  with self.assertRaisesRegex(ValueError,'snapshot bytes'):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',rows)
 def test_post_normalization_budget_boundary(self):
  import json
  rows=[dict(row(),id=str(i),review_state='document_reviewed',reviewed_at='2026-10-03T00:00:00Z',excerpt='x',conditions='x') for i in range(700)]
  size=lambda rows:sum(len(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode()) for r in rows)
  remaining=2_000_000-size(rows)
  for r in rows:
   for key,cap in [('excerpt',2000),('conditions',1000)]:
    add=min(remaining,cap-len(r[key]));r[key]+='x'*add;remaining-=add
  self.assertEqual(remaining,0)
  with self.assertRaisesRegex(ValueError,'snapshot bytes'):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',rows)
  # Remove exact canonicalization expansion: retained SUM rows = limit.
  need=3500
  for r in rows:
   cut=min(need,len(r['excerpt'])-1);r['excerpt']=r['excerpt'][:-cut] if cut else r['excerpt'];need-=cut
  self.assertEqual(need,0)
  s=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',rows);self.assertEqual(size(s._items),2_000_000)
 def test_list_surrogates_coarse_error_before_copy(self):
  for field in ['codes','effective_dates']:
   r=row();r[field]=['\ud800']
   with self.assertRaisesRegex(ValueError,'list text'):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_huge_wrong_field_count_rejects_before_set_allocation(self):
  import tracemalloc
  huge={str(n):'x' for n in range(1_000_000)}
  tracemalloc.start()
  try:
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[huge])
   _,peak=tracemalloc.get_traced_memory()
  finally:tracemalloc.stop()
  self.assertLess(peak,64*1024)
