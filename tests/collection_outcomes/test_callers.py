"""Execute ONLY extracted write branch with fake writer, no collector imports."""
import ast
from pathlib import Path
import unittest
class OutcomeError(Exception):
 def __init__(self,state):
  super().__init__('PRIVATE URI MUST NOT SURFACE')
  self.outcome={'state':state,'attempted':3,'inserted_count':1 if state=='partial' else None,'duplicate_count':0 if state=='partial' else None,'failed_count':2 if state=='partial' else None,'uncertain_count':0 if state=='partial' else 3,'retry_safe':False,'PRIVATE':'secret'}
class Tests(unittest.TestCase):
 def branch(self,name,writer):
  root=Path(__file__).parents[2];tree=ast.parse((root/f'intelligence/geo/collectors/{name}.py').read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='collect');branch=fn.body[-1]
  self.assertIsInstance(branch,ast.Try)
  node=ast.FunctionDef(name='write_only',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[branch],decorator_list=[])
  scope={'save_articles_bulk':writer,'ArticleWriteOutcomeError':OutcomeError,'docs':[{}]};exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'fakebranch','exec'),scope);return scope['write_only']()
 def test_success_int(self):
  for name in ['rss','gnews_search']:self.assertEqual(self.branch(name,lambda _:2),2)
 def test_partial_and_unknown_closed(self):
  for name in ['rss','gnews_search']:
   for state in ['partial','uncertain']:
    def writer(_):raise OutcomeError(state)
    out=self.branch(name,writer);self.assertEqual(out['state'],state);self.assertIs(type(out),dict);self.assertNotIn('PRIVATE',out);self.assertNotIn('URI',str(out));self.assertFalse(out['retry_safe'])
 def test_other_exception_not_swallowed(self):
  def writer(_):raise RuntimeError('fixture')
  for name in ['rss','gnews_search']:
   with self.assertRaises(RuntimeError):self.branch(name,writer)
 def test_no_backup_calls_or_threads(self):
  for name in ['rss','gnews_search']:
   tree=ast.parse((Path(__file__).parents[2]/f'intelligence/geo/collectors/{name}.py').read_text())
   names=[n.id for n in ast.walk(tree) if isinstance(n,ast.Name)]
   self.assertNotIn('attach_backup_refs',names);self.assertNotIn('threading',names);self.assertNotIn('update_telegram_refs',names)
if __name__=='__main__':unittest.main()
