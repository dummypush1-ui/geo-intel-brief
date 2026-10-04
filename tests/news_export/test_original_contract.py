import ast,csv,hashlib,io,unittest
from pathlib import Path
from types import SimpleNamespace
from integration.news_export.original_contract import original_snapshot,SOURCE_PINS,ExportRequestError
ROOT=Path(__file__).resolve().parents[2]
class OriginalContracts(unittest.TestCase):
 def oracle(self,project,rows,args):
  source=(ROOT/('intelligence/'+project+'/web.py')).read_text();tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='export_csv');node.decorator_list=[]
  class Response:
   def __init__(self,body,**kw):self.body=body
  scope={'request':SimpleNamespace(args=args),'csv':csv,'io':io,'Response':Response,'_authorized':lambda:True,'_db_check':lambda:None,'recent_articles':lambda limit:rows[:limit], 'get_store':lambda:SimpleNamespace(recent=lambda limit:rows[:limit]),'is_critical':lambda r:any(k in (r.get('title','')+' '+r.get('summary','')).lower() for k in ('attack','explosion','resign','coup','ceasefire','sanctions')),'datetime':__import__('datetime')}
  if project=='brics':
   predicate=next(n for n in ast.parse((ROOT/'intelligence/brics/processing/classifier.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='is_critical');scope['C']=SimpleNamespace(CRITICAL_KEYWORDS=['attack','explosion','resign','coup','ceasefire','sanctions']);exec(compile(ast.Module(body=[predicate],type_ignores=[]),'original critical predicate','exec'),scope)
  exec(compile(ast.Module(body=[node],type_ignores=[]),'original reviewed export','exec'),scope)
  return scope['export_csv']().body.encode()
 def test_source_pins(self):
  for p,h in SOURCE_PINS.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
 def test_geo_differential(self):
  rows=[{'title':'alpha, "beta"\nnewline','category':'TRADE','country':'India','score':4,'summary':'test','_id':'PRIVATE'},{'title':'Other','source':'S','category':'RISK'}]
  for args in ({},{'category':'TRADE'},{'category':'trade'},{'category':'GENERAL'}):
   body,h,m=original_snapshot(rows,'geo',args);self.assertEqual(body,self.oracle('geo',rows,args));self.assertNotIn(b'PRIVATE',body)
 def test_brics_differential(self):
  rows=[{'title':'sanctions today','summary':'brief','country':'India','category':'TRADE','corroborated_by':['A','B'],'source':'S,news'}, {'title':'Other','country':'Brazil','category':'RISK'}]
  for args in ({},{'category':' trade '},{'q':'india'},{'country':'BRAZIL'},{'critical_only':'yes'},{'critical_only':'YES'},{'limit':'bad'},{'limit':'1'}):
   body,_,_=original_snapshot(rows,'brics',args);self.assertEqual(body,self.oracle('brics',rows,args))
 def test_bounds_and_safety(self):
  for args in ({'limit':'0'},{'limit':'-1'},{'q':['x']},{'key':'secret'}):
   with self.assertRaises(ExportRequestError):original_snapshot([],'brics',args)
  with self.assertRaises(ValueError):original_snapshot([{}]*10001,'geo')
  b,_,_=original_snapshot([{'title':'=1+2','_id':'PRIVATE','emailed':'PRIVATE'}],'geo');self.assertIn(b"'=1+2",b);self.assertNotIn(b'PRIVATE',b)
 def test_cap_before_filter_and_exact_predicate(self):
  rows=[{'title':'plain','country':'Brazil'},{'title':'sanctions','country':'India'}]
  b,h,m=original_snapshot(rows,'brics',{'country':'India','limit':'1'});self.assertEqual(m['rows'],0);self.assertEqual(h['X-Export-Truncated'],'true')
  b,_,m=original_snapshot(rows,'brics',{'critical_only':'1'},critical_keywords=['plain']);self.assertEqual(m['rows'],1);self.assertIn(b'plain',b)

 def test_formula_prefixes_negative_numbers(self):
  for value in ('=SUM(1)','+1','-1','@foo','\tfoo','\rfoo','\nfoo','  =1','\u200b=1'):
   b,_,_=original_snapshot([{'title':value,'score':-3}],'geo')
   row=list(csv.DictReader(io.StringIO(b.decode())))[0]
   self.assertTrue(row['title'].startswith("'"),repr(value));self.assertEqual(row['score'],"'-3")
 def test_long_cells_report_truncation(self):
  b,h,m=original_snapshot([{'title':'x'*8001}],'geo');self.assertEqual(len(list(csv.DictReader(io.StringIO(b.decode())))[0]['title']),8000);self.assertEqual(h['X-Export-Truncated'],'true');self.assertTrue(m['cells_truncated'])
 def test_surrogates_and_geo_list_fail_closed(self):
  for row in ({'title':'bad\ud800'},{'title':'t','corroborated_by':['bad\udfff']}):
   with self.assertRaises(ExportRequestError):original_snapshot([row],'brics')
  with self.assertRaises(ValueError):original_snapshot([{'title':'t','corroboration':['A']}],'geo')
 def test_budget_and_stamp_fail_fast(self):
  with self.assertRaises(ExportRequestError):original_snapshot([{'title':'x'*1000}]*10,'geo',max_bytes=1024)
  with self.assertRaises(ExportRequestError):original_snapshot([object()],'brics',stamp='bad')
  with self.assertRaises(ValueError):original_snapshot([],'geo',max_bytes=True)
