import unittest
from integration.news_api import create_app
class WeeklyRoutes(unittest.TestCase):
 def test_guard_validation_and_no_post(self):
  c=create_app().test_client()
  for p in ['/workspace/weekly','/api/weekly-report.pdf?start=2026-09-28&end=2026-10-05','/workspace/assets/weekly.js']:self.assertEqual(c.get(p).status_code,403)
  c=create_app(authorize=lambda r:True).test_client()
  for q in ['', '?start=2026-09-28&end=2026-09-28','?start=0001-01-01&end=0001-01-02','?start=2026-01-01&end=2026-12-31','?start=2026-02-30&end=2026-03-02']:
   self.assertEqual(c.get('/api/weekly-report.pdf'+q).status_code,400)
  self.assertEqual(c.post('/api/weekly-report.pdf',headers={'Origin':'http://localhost'}).status_code,405)
 def test_pdf_private_fields_and_no_side_effects(self):
  from pypdf import PdfReader
  import io
  raw={'geo':[dict(url='https://example.com/a',title='Fixture publication',country='India',published='2026-10-01T00:00:00Z',created_at='2026-10-01T01:00:00Z',telegram_url='secret-field',emailed=True,_id='secret-field')]}
  c=create_app(reader=lambda:raw,authorize=lambda r:True).test_client();r=c.get('/api/weekly-report.pdf?start=2026-09-28&end=2026-10-05');self.assertEqual(r.status_code,200);self.assertEqual(r.mimetype,'application/pdf');self.assertEqual(r.headers['Cache-Control'],'no-store');text=''.join(p.extract_text() for p in PdfReader(io.BytesIO(r.data)).pages);self.assertIn('Fixture publication',text);self.assertNotIn('secret-field',text);self.assertTrue(raw['geo'][0]['emailed'])
 def test_reader_failure503(self):
  def fail():raise RuntimeError('private')
  r=create_app(reader=fail,authorize=lambda r:True).test_client().get('/api/weekly-report.pdf?start=2026-09-28&end=2026-10-05');self.assertEqual(r.status_code,503);self.assertNotIn('private',r.get_data(as_text=True))

 def test_boundary_and_malformed_snapshots(self):
  path='/api/weekly-report.pdf?start=1970-01-02&end=1970-01-03'
  c=create_app(authorize=lambda r:True).test_client()
  self.assertEqual(c.get(path).status_code,200)
  self.assertEqual(c.get(path.replace('start=1970-01-02','start=1970-01-01')).status_code,400)
  for q in ['&start=1970-01-02','&end=1970-01-03']:
   self.assertEqual(c.get(path+q).status_code,400)
  for raw in [None,{'geo':[None]},{'unknown':[]},{'geo':[{}]*2001}]:
   r=create_app(reader=lambda:raw,authorize=lambda r:True).test_client().get(path)
   self.assertEqual(r.status_code,503);self.assertEqual(r.mimetype,'application/json')
 def test_reader_rows_capped_before_normalization(self):
  raw={'geo':[{}]*100+[None]}
  self.assertEqual(create_app(reader=lambda:raw,authorize=lambda r:True).test_client().get('/api/weekly-report.pdf?start=2026-09-28&end=2026-10-05').status_code,200)
 def test_concurrency_guard(self):
  from unittest.mock import patch
  from threading import Event,Thread
  entered=Event();release=Event();count=[]
  def build(*a,**k):
   count.append(1)
   if len(count)==2:entered.set()
   release.wait(10);return b'%PDF-1.4'
  app=create_app(authorize=lambda r:True);path='/api/weekly-report.pdf?start=2026-09-28&end=2026-10-05'
  with patch('integration.news_api.build_weekly_report',side_effect=build):
   ts=[Thread(target=lambda:app.test_client().get(path)) for _ in range(2)]
   for t in ts:t.start()
   try:
    self.assertTrue(entered.wait(5));self.assertEqual(app.test_client().get(path).status_code,429)
   finally:
    release.set()
    for t in ts:t.join()
  self.assertEqual(app.test_client().get(path).status_code,200)
 def test_period_cap_and_gate_release_on_exception(self):
  from unittest.mock import patch
  app=create_app(authorize=lambda r:True);c=app.test_client()
  base='/api/weekly-report.pdf?start=2026-09-01&end='
  self.assertEqual(c.get(base+'2026-10-02').status_code,200)
  self.assertEqual(c.get(base+'2026-10-03').status_code,400)
  with patch('integration.news_api.build_weekly_report',side_effect=ValueError('private')):
   for _ in range(3):self.assertEqual(c.get(base+'2026-10-02').status_code,503)
  self.assertEqual(c.get(base+'2026-10-02').status_code,200)
