import tempfile,unittest
from pathlib import Path
from integration.finder_index import FinderIndex,load_bundled_index
from integration.finder_links import finder_link
from integration.news_api import create_app
ROOT=Path(__file__).resolve().parents[1]
class FinderIndexTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.index=load_bundled_index(ROOT)
 def test_real_leading_zero_and_supplement(self):
  rows=self.index.for_article({'title':'HS 090121; HSN 97051000'})
  self.assertTrue(any(r['code']=='090121' and r['system']=='HS' for r in rows))
  self.assertTrue(any(r['code']=='97051000' and r['system']=='US' for r in rows))
  self.assertEqual(finder_link('https://preview.example/workspace/finder/index.html',0,'090121',True),'https://preview.example/workspace/finder/index.html#code=0:090121')
 def test_no_country_or_numeric_guess(self):
  for title in ['India coffee news','Order 090121','HS 090121abc','HS 0901210000000','HS 090121.00','HS 090121-99','HS 090121/00','HS 090121,00','HS 090121. 00','HS 090121 .00','HS 090121 - 00','HS 090121 00']:
   self.assertEqual(self.index.for_article({'title':title}),[])
 def test_duplicate_mentions_unique(self):
  rows=self.index.for_article({'title':'HS 090121 HSN 090121'})
  self.assertEqual(len(rows),len({(r['system_index'],r['code']) for r in rows}))
 def test_unknown_exact_code(self):self.assertEqual(self.index.for_article({'title':'HS 999999999999'}),[])
 def test_repeated_keys_follow_finder_map(self):
  x=FinderIndex([[0,'090121','first',None,'09',''],[0,'090121','last',None,'09',''],[0,'TOTAL','total',None,'TO','']], [{'tag':'HS','name':'World'}])
  self.assertEqual(len(x.for_article({'title':'HS 090121'})),1)
 def test_bad_rows_fail(self):
  for row in [[True,'090121','x',None,'09',''],[0,90121,'x',None,'09',''],[0,'090121',None,None,'09','']]:
   with self.assertRaises(ValueError):FinderIndex([row],[{'tag':'HS','name':'World'}])
 def test_integer_code_refused(self):
  with self.assertRaises(ValueError):finder_link('https://preview.example',0,90121,True)
 def test_tampered_bundle_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'index.html').write_text("data.000000000000.js");(p/'data.000000000000.js').write_text('not trusted')
   with self.assertRaises(ValueError):load_bundled_index(p)
 def test_route_uses_verified_exact_code(self):
  rows={'geo':[{'_id':'article','url':'https://example.com/a','title':'HS 090121 coffee'}]}
  c=create_app(reader=lambda:rows,authorize=lambda r:True,finder_context_reader=self.index.for_article,finder_index_verified=True,finder_base='http://localhost/workspace/finder/index.html').test_client()
  d=c.post('/api/finder-context',json={'project':'geo','legacy_id':'article'},headers={'Origin':'http://localhost'}).json
  self.assertTrue(d['items']);self.assertTrue(all(x['finder_url'].endswith(':090121') for x in d['items']))
  self.assertTrue(all(x['match']['precise'] and not x['match']['duty_change_verified'] for x in d['items']))

 def test_punctuated_prefix_is_not_precise(self):
  from integration.relevance import match
  for title in ['HS 090121.00','HS 090121-99','HS 090121/00','HS 090121,00','HS 090121. 00','HS 090121 .00','HS 090121 - 00','HS 090121 00']:
   self.assertFalse(match({'code':'090121'},{'title':title})['precise'])
 def test_shell_size_checked_before_read(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'index.html'
   with p.open('wb') as f:f.truncate(2_000_001)
   with self.assertRaisesRegex(ValueError,'shell too large'):load_bundled_index(d)
 def test_bundle_size_checked_before_read(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'index.html').write_text('data.000000000000.js')
   with (p/'data.000000000000.js').open('wb') as f:f.truncate(30_000_001)
   with self.assertRaisesRegex(ValueError,'bundle too large'):load_bundled_index(p)
