import unittest
from datetime import datetime,timezone
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration.news_api import create_app
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row():return {'id':'fixture-1','jurisdiction':'IN','nomenclature':'HSN','edition':'fixture-2026','codes':['21069051'],'document_id':'Fixture notification, not live duty','source_url':'https://www.indiabudget.gov.in/doc/cen/cus0326.pdf','published_date':'2026-02-01','effective_dates':['2026-04-01','2026-05-01'],'excerpt':'Fixture excerpt <script>bad</script>','conditions':'Fixture only, not real legal interpretation','review_state':'candidate','reviewed_at':None}
class TariffEvidenceTests(unittest.TestCase):
 def test_dates_separate_and_no_legal_or_current_claim(self):
  s=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[row()]);d=s.view(NOW);self.assertEqual(len(d['items'][0]['effective_dates']),2);self.assertFalse(d['current_rates_verified']);self.assertFalse(d['legal_effect_independently_verified']);self.assertFalse(d['network'])
 def test_official_exact_host_and_url_shape(self):
  for url in ['https://www.indiabudget.gov.in.evil/x','https://evil@www.indiabudget.gov.in/x','https://www.indiabudget.gov.in\\@evil/x','http://www.indiabudget.gov.in/x','https://www.indiabudget.gov.in/%2fsecret','https://www.indiabudget.gov.in:444/x']:
   r=row();r['source_url']=url
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_review_not_promoted_by_host(self):
  r=row();d=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r]).view(NOW);self.assertEqual(d['items'][0]['review_state'],'candidate')
  r['reviewed_at']='2026-10-03T00:00:00Z'
  with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
  r['review_state']='document_reviewed';self.assertEqual(TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r]).view(NOW)['items'][0]['review_state'],'document_reviewed')
 def test_future_capture_and_future_review(self):
  s=TariffEvidenceSnapshot('2026-10-06T00:00:00Z',[row()])
  with self.assertRaises(ValueError):s.view(NOW)
  r=row();r.update(review_state='document_reviewed',reviewed_at='2026-10-05T00:00:00Z')
  with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_exact_code_not_numeric_ranges_or_percent_guess(self):
  for codes in [[21069051],['2106-2208'],['21.06'],['21069051','21069051']]:
   r=row();r['codes']=codes
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_copy_cap_and_jurisdiction_filter(self):
  rows=[dict(row(),id='fixture-'+str(i)) for i in range(101)];s=TariffEvidenceSnapshot('2026-10-04T00:00:00Z',rows);rows[0]['codes'].append('9999');d=s.view(NOW);self.assertEqual(len(d['items']),100);self.assertTrue(d['truncated']);self.assertEqual(s.view(NOW,'US')['items'],[])
 def test_dates_invalid_and_schema_closed(self):
  for key,value in [('published_date','2026-02-30'),('effective_dates',['2026-13-01']),('codes','2106'),('excerpt','a'*2001)]:
   r=row();r[key]=value
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
  r=row();r['rate']='5%'
  with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
 def test_route_guard_unwired_failure_and_no_post(self):
  self.assertEqual(create_app().test_client().get('/api/tariff-evidence').status_code,403)
  c=create_app(authorize=lambda req:True).test_client();self.assertEqual(c.get('/api/tariff-evidence').json['state'],'tariff_evidence_unwired');self.assertEqual(c.get('/api/tariff-evidence?jurisdiction=XX').status_code,400)
  c=create_app(authorize=lambda req:True,tariff_evidence_snapshot=lambda:[]).test_client();self.assertEqual(c.get('/api/tariff-evidence').status_code,503)
 def test_non_ascii_code_and_date_digits_rejected(self):
  for key,value in [('codes',['٢١٠٦٩٠٥١']),('published_date','٢٠٢٦-٠٢-٠١'),('effective_dates',['٢٠٢٦-٠٤-٠١'])]:
   r=row();r[key]=value
   with self.assertRaises(ValueError):TariffEvidenceSnapshot('2026-10-04T00:00:00Z',[r])
