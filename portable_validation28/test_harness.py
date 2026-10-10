"""Independent negative probes, LOCAL3.10.12 only."""
import unittest,sys,pathlib,tempfile,json,hashlib
from zoneinfo import ZoneInfoNotFoundError
from unittest.mock import patch
import harness as h
class Negatives(unittest.TestCase):
 def test_declared_env_switch(self):
  self.assertEqual(h.markers('3.10'),[True,False,True,False]);self.assertEqual(h.markers('3.12'),[False,True,True,False]);self.assertEqual(len(h.declared('3.12')),12)
 def test_depth_structured(self):
  for n in (63,64):self.assertEqual(h.depth('['*n+'0'+']'*n),{'outcome':'accepted','error':None})
  self.assertEqual(h.depth('['*65+'0'+']'*65),{'outcome':'refused','error':'fixture_depth_probe'})
 def test_missing_tz(self):
  def absent(k):raise ZoneInfoNotFoundError(k)
  self.assertEqual(h.tz_rows(absent)['status'],'BLOCKED')
 def test_skip_not_pass(self):
  r=[{'status':s}for s in ['PASS','FAIL','SKIP','BLOCKED','NOT RUN']];self.assertEqual(h.totals(r),{'PASS':1,'FAIL':1,'SKIP':1,'BLOCKED':1,'NOT RUN':1})
 def test_source_drift(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);(p/'x.py').write_text('changed');manifest={'files':{'x.py':'0'*64}}
   with patch.object(pathlib.Path,'read_text',return_value=json.dumps(manifest)):
    with self.assertRaises(ValueError):h.sources(p)
if __name__=='__main__':unittest.main()
