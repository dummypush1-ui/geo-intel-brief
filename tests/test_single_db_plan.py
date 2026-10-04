import unittest
from integration.single_db_plan import SingleDatabasePlan
class SingleDBPlanTests(unittest.TestCase):
 def test_distinct_maps_one_db(self):
  p=SingleDatabasePlan('fixture_db','geo_rows','other_rows');g={};b={};m=p.fake_store_map({'geo_rows':g,'other_rows':b});self.assertIs(m['geo'],g);self.assertIs(m['brics'],b)
 def test_no_inferred_mapping(self):
  for args in [('fixture_db','articles','articles'),('','geo','other'),('fixture_db','geo.$','other')]:self.assertRaises(ValueError,SingleDatabasePlan,*args)
  p=SingleDatabasePlan('fixture_db','geo','other');self.assertRaises(ValueError,p.fake_store_map,{'geo':{},'other':{},'legacy':{}})
 def test_no_hook_objects_or_same_store(self):
  class Map(dict):pass
  p=SingleDatabasePlan('fixture_db','geo','other');self.assertRaises(ValueError,p.fake_store_map,Map(geo={},other={}))
  shared={};self.assertRaises(ValueError,p.fake_store_map,{'geo':shared,'other':shared})
