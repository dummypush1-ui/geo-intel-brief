# Copyright (c) 2026 Push. All rights reserved.
import unittest,csv,io
from .export import to_csv
from .model import snapshot
from .filters import apply_filters
from .fixtures import RAW,INDEX
from .fixtures import app

class ExportTests(unittest.TestCase):
 def test_same_filters_and_codes(self):
  data=apply_filters(snapshot(RAW,INDEX),{'code':'090111'})
  rows=list(csv.DictReader(io.StringIO(to_csv(data))))
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['exact_trade_codes'],'IN 090111')
  self.assertEqual(rows[0]['tariff_verified'],'false')
  self.assertEqual(len(list(csv.DictReader(io.StringIO(to_csv(apply_filters(snapshot(RAW),{'q':'absent'})))))),0)
 def test_formula_and_csv_quotes(self):
  raw={'geo':[dict(RAW['geo'][0],title='\u200b=HYPERLINK("x")',summary='a,b\n"c"')]}
  rows=list(csv.DictReader(io.StringIO(to_csv(snapshot(raw)))))
  self.assertTrue(rows[0]['title'].startswith("'"));self.assertEqual(rows[0]['summary'],'a,b\n"c"')
 def test_all_formula_prefixes(self):
  from integration.loaded_news import csv_cell
  for prefix in ('=','+','-','@','\t','\r','\n','\u200b=','\u202e+','\ufeff@'):
   self.assertTrue(csv_cell(prefix+'x').startswith("'"),repr(prefix))
 def test_route_and_scope(self):
  c=app();r=c.get('/workspace/world/export.csv?country=India')
  self.assertEqual(r.status_code,200);self.assertEqual(r.mimetype,'text/csv')
  self.assertIn('not_full_database',r.headers['X-Export-Scope'])
  self.assertEqual(c.get('/workspace/world/export.csv?unknown=x').status_code,400)
  self.assertEqual(c.post('/workspace/world/export.csv').status_code,405)
