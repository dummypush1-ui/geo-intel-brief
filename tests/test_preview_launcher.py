import unittest,importlib,sys,os
from unittest.mock import patch
from integration.preview_launcher import build_preview
from tests.test_geo_only_runtime import env,Client
class PreviewLauncherTests(unittest.TestCase):
 def test_default_off_preserves_legacy_no_client(self):
  a=build_preview({},lambda *a,**k:(_ for _ in ()).throw(AssertionError('client')));self.assertEqual(a.extensions['preview_launcher_mode'],'legacy_isolated');self.assertEqual(a.extensions['read_only_news_clients'],[])
 def test_geo_only_read_off_denied_private(self):
  a=build_preview({'PREVIEW_GEO_ONLY_ENABLED':'true'},lambda *a,**k:(_ for _ in ()).throw(AssertionError('client')));self.assertEqual(a.extensions['preview_launcher_mode'],'geo_only');self.assertEqual(a.extensions['stored_news_projects'],('geo',));self.assertEqual(a.test_client().get('/workspace').status_code,403)
 def test_geo_only_fake_factory_exact_mapping_and_no_brics(self):
  e=env();e['PREVIEW_GEO_ONLY_ENABLED']='true';calls=[];c=Client()
  a=build_preview(e,lambda *args,**kwargs:(calls.append(args),c)[1]);self.assertEqual(len(calls),1);self.assertEqual(c.paths,['geo_intel','articles']);self.assertEqual(a.extensions['stored_news_projects'],('geo',))
 def test_live_factory_missing_and_invalid_flag_fail_closed(self):
  e=env();e['PREVIEW_GEO_ONLY_ENABLED']='true'
  with self.assertRaises(ValueError):build_preview(e)
  for v in ('TRUE','1','',True):
   with self.assertRaises(ValueError):build_preview({'PREVIEW_GEO_ONLY_ENABLED':v})
  e=env();e.update(PREVIEW_GEO_ONLY_ENABLED='true',GEO_MONGODB_DB_NAME='different')
  with self.assertRaises(ValueError):build_preview(e,lambda *a,**k:(_ for _ in ()).throw(AssertionError('client')))
 def test_actual_router_import_read_off_no_client(self):
  sys.modules.pop('integration.private_router',None)
  with patch.dict(os.environ,{'PREVIEW_GEO_ONLY_ENABLED':'true'},clear=True),patch('pymongo.MongoClient',side_effect=AssertionError('network client')):
   m=importlib.import_module('integration.private_router');self.assertEqual(m.app.extensions['preview_launcher_mode'],'geo_only');self.assertEqual(m.app.extensions['read_only_news_clients'],[])
  sys.modules.pop('integration.private_router',None)

 def test_exact_geo_flags_and_no_external_dependency_calls(self):
  from pathlib import Path
  from integration.finder_index import load_bundled_index
  from integration.finder_network import from_env
  with patch('socket.socket',side_effect=AssertionError('network')),patch('pymongo.MongoClient',side_effect=AssertionError('client')),patch('requests.get',side_effect=AssertionError('fetch')):
   idx=load_bundled_index(Path(__file__).resolve().parents[1]);self.assertTrue(idx.by_code);self.assertFalse(from_env({}))
  for key in ('NEWS_READ_ENABLED','PREVIEW_ACCESS_ENABLED','NEWS_STORE_MAPPING_VERIFIED','PREVIEW_TRUST_ONE_PROXY'):
   with self.assertRaises(ValueError):build_preview({'PREVIEW_GEO_ONLY_ENABLED':'true',key:'TRUE'})
 def test_two_app_builds_isolated_no_global_registration(self):
  import integration.geo_only_runtime as module
  from integration.preview_access import create_preview_from_env
  built=[]
  def capture(*a,**kw):
   app=create_preview_from_env(*a,**kw);built.append(app);return app
  e=env();e['PREVIEW_GEO_ONLY_ENABLED']='true'
  with patch.object(module,'create_preview_from_env',capture),patch('socket.socket',side_effect=AssertionError('network')):
   app=build_preview(e,lambda *a,**kw:Client())
  self.assertEqual(len(built),2);self.assertIsNot(built[0],built[1]);self.assertIs(app,built[1]);self.assertEqual(len([r for r in app.url_map.iter_rules() if r.rule=='/login']),1)
