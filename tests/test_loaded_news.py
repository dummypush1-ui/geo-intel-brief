import csv,io,unittest
from integration.news_api import create_app
from integration.loaded_news import csv_cell
ROWS={'geo':[{'_id':'private','url':'https://example.com/'+str(i),'title':title,'source':'Source, "quoted"','country':country,'score':score,'created_at':'2026-10-02T00:00:00Z','summary':'line1\nline2'} for i,(title,country,score) in enumerate([('Z','India',2),('A','Brazil',9),('M','China',None)])],'brics':[{'id':'secret','url':'https://example.com/b','title':'B','country':'Brazil','corroborated_by':['one','two']}]}
class LoadedNewsTests(unittest.TestCase):
 def client(self,rows=ROWS):return create_app(reader=lambda:rows,authorize=lambda r:True).test_client()
 def test_explicit_sorts_and_project_contract(self):
  c=self.client()
  for sort,want in [('title',['A','M','Z']),('country',['A','M','Z']),('score',['A','Z','M'])]:self.assertEqual([r['title'] for r in c.get('/api/news?project=geo&sort='+sort).json['items']],want)
  for query in ['project=geo&sort=corroboration','project=brics&sort=score','sort=score','sort=weird','project=bad']:self.assertEqual(c.get('/api/news?'+query).status_code,400)
 def test_csv_matches_filtered_json_not_full_export(self):
  c=self.client();q='project=geo&sort=title&country=Brazil';rows=c.get('/api/news?'+q).json['items'];r=c.get('/api/news-export.csv?'+q)
  parsed=list(csv.DictReader(io.StringIO(r.text)));self.assertEqual([x['title'] for x in parsed],[x['title'] for x in rows]);self.assertEqual(parsed[0]['summary'],'line1\nline2');self.assertEqual(parsed[0]['source'],'Source, "quoted"');self.assertNotIn('_id',r.text);self.assertNotIn('private',r.text);self.assertEqual(r.headers['X-Export-Scope'],'loaded_read_view_not_full_database');self.assertIn('loaded-news-sample.csv',r.headers['Content-Disposition'])
 def test_formula_cells_hidden_prefixes_and_surrogates(self):
  for v in ['=1','+cmd','-1','@x','  =SUM(1)','\u200b=1','\x00=1','\ttext','\rtext','\ntext']:self.assertTrue(csv_cell(v).startswith("'"),repr(v))
  self.assertEqual(csv_cell('normal'),'normal');self.assertEqual(csv_cell('a\ud800'),'a\ufffd');self.assertEqual(len(csv_cell('a'*9000)),8000)
 def test_csv_formulas_not_raw(self):
  rows={'geo':[{'url':'https://example.com/x','title':'=HYPERLINK("x")','source':'\u200b@secret','summary':'  +cmd'}]};r=self.client(rows).get('/api/news-export.csv?project=geo');item=list(csv.DictReader(io.StringIO(r.text)))[0]
  for field in ['title','source','summary']:self.assertTrue(item[field].startswith("'"))
 def test_cap_truthful_and_guards_no_mutation(self):
  rows={'geo':[{'url':'https://example.com/'+str(i),'title':str(i)} for i in range(101)]};c=self.client(rows);d=c.get('/api/news?project=geo').json;self.assertEqual(len(d['items']),100);self.assertTrue(d['truncated']);self.assertTrue(d['not_full_database_export']);r=c.get('/api/news-export.csv?project=geo');self.assertEqual(len(list(csv.DictReader(io.StringIO(r.text)))),100);self.assertEqual(r.headers['X-Export-Truncated'],'true');self.assertEqual(len(rows['geo']),101)
  self.assertEqual(create_app().test_client().get('/api/news-export.csv').status_code,403);self.assertEqual(c.get('/api/news-export.csv?sort=bad').status_code,400)

 def test_embedded_nul_cannot_break_export(self):
  rows={'geo':[{'url':'https://example.com/x','title':'T\x00x','source':'mid\x00field'}]}
  r=self.client(rows).get('/api/news-export.csv?project=geo');self.assertEqual(r.status_code,200)
  parsed=list(csv.DictReader(io.StringIO(r.text)));self.assertEqual(parsed[0]['title'],'Tx');self.assertEqual(parsed[0]['source'],'midfield');self.assertNotIn('\x00',r.text)
