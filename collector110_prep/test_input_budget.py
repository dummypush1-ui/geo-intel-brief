import unittest
from datetime import datetime,timezone
from .input_budget import capture,InputRefused
class Tests(unittest.TestCase):
 def test_exact_capture_and_independence(self):
  v={'candidates':[{'title':'News','published':datetime(2026,1,1,tzinfo=timezone.utc)}],'categories':['TRADE'],'threshold':.85}
  out=capture(v);v['candidates'][0]['title']='Changed';self.assertEqual(out['captured']['candidates'][0]['title'],'News');self.assertGreater(out['nodes'],0)
 def test_depth(self):
  v=[]
  for _ in range(9):v=[v]
  with self.assertRaises(InputRefused):capture(v)
 def test_cycles(self):
  v=[];v.append(v)
  with self.assertRaises(InputRefused):capture(v)
 def test_aggregate_nodes(self):
  with self.assertRaises(InputRefused):capture([list(range(1000)) for _ in range(21)])
 def test_aggregate_bytes(self):
  with self.assertRaises(InputRefused):capture(['x'*10000 for _ in range(220)])
 def test_repeated_shared_subtree_charged(self):
  row=['x'*10000 for _ in range(100)]
  with self.assertRaises(InputRefused):capture([row,row,row])
 def test_scalar_types_and_surrogate(self):
  for v in (float('inf'),float('nan'),2**100,'\ud800',object(),(1,2)):
   with self.assertRaises(InputRefused):capture(v)
 def test_invalid_keys(self):
  for v in ({1:2},{'a'*101:1}):
   with self.assertRaises(InputRefused):capture(v)
 def test_date_bounds(self):
  for v in (datetime(2026,1,1),datetime(1900,1,1,tzinfo=timezone.utc)):
   with self.assertRaises(InputRefused):capture(v)
 def test_container_and_text_bounds(self):
  for v in ([1]*1001,{str(x):1 for x in range(101)},'x'*10001):
   with self.assertRaises(InputRefused):capture(v)
if __name__=='__main__':unittest.main(verbosity=2)
