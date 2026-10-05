"""Offline strict-reject parser caps; subprocess timeout is harness only."""
import unittest,subprocess,sys,json,copy
from integration.page_watch import snapshot,compare
U='https://nilgiried.com/';T='2026-10-05T10:00:00Z'
class ParserBudgetTests(unittest.TestCase):
 def test_caps_and_baseline_not_mutated(self):
  baseline=snapshot(U,'<p>Sample visible event detail with enough text for baseline</p>',T);before=copy.deepcopy(baseline)
  for text in ['x'*(128*1024+1),'தமிழ்'*30000,'<a '+('x'*4097)+'>','<!--'+('x'*4097)+'-->','<br>'*4001,'<a>'*501+'<p>Long enough visible content text for baseline</p>','<a>'*500+'</b>'*3000]:
   with self.subTest(length=len(text)):
    with self.assertRaises(ValueError):snapshot(U,text,T)
   self.assertEqual(baseline,before)
 def test_normal_output_golden(self):
  a=snapshot(U,'<h1>Normal title</h1><p>Enough ordinary sample content for baseline</p>',T)
  self.assertEqual(a['text'],'Normal title\nEnough ordinary sample content for baseline')
 def test_direct_event_budget(self):
  from integration.page_watch import VisibleText
  parser=VisibleText()
  for _ in range(8000):parser.handle_comment('fixture')
  with self.assertRaises(ValueError):parser.handle_comment('last')
 def test_crafted_subprocess_measurements(self):
  script="""
import time,json
from integration.page_watch import snapshot
cases={'nested_unclosed':'<a>'*500+'</b>'*3000,'giant_attribute':'<a x="'+'x'*4097+'">','giant_comment':'<!--'+'x'*4097+'-->','many_tags':'<br>'*4001,'nearcap_attribute':'<a x="'+'x'*4000+'"><p>'+'enough visible content '*3+'</p>','nested_within':'<a>'*400+'</b>'*2500+'<p>'+'enough visible content '*3+'</p>'}
for name,html in cases.items():
 start=time.monotonic()
 try:snapshot('https://nilgiried.com/',html,'2026-10-05T10:00:00Z');state='accepted'
 except ValueError:state='rejected'
 print(json.dumps({'case':name,'state':state,'seconds':time.monotonic()-start}))
"""
  result=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True,timeout=2,check=True)
  rows=[json.loads(line) for line in result.stdout.splitlines()];self.assertEqual(len(rows),6);self.assertEqual(result.stderr,'')
  for row in rows:print('OFFLINE_PARSER_MEASURE',row)
