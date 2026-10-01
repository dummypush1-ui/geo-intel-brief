import unittest
from integration.news_api import create_app
from test_bridges import ROWS
class WorkspaceTests(unittest.TestCase):
 def test_workspace_private(self):
  c=create_app().test_client()
  for path in ['/workspace','/workspace/assets/workspace.js','/workspace/finder/index.html']:
   self.assertEqual(c.get(path).status_code,403)
 def test_authorized_static_allowlist(self):
  c=create_app(lambda:ROWS,lambda r:True).test_client()
  for path in ['/workspace','/workspace/assets/workspace.js','/workspace/assets/workspace.css','/workspace/finder/index.html']:
   r=c.get(path);self.assertEqual(r.status_code,200);self.assertEqual(r.headers['Cache-Control'],'no-store');r.close()
  for path in ['/workspace/finder/proxy.js','/workspace/finder/.env','/workspace/assets/news_api.py']:
   self.assertEqual(c.get(path).status_code,404)
 def test_filtered_news(self):
  c=create_app(lambda:ROWS,lambda r:True).test_client()
  for project in ['geo','brics']:
   rows=c.get('/api/news?project='+project).json['items'];self.assertEqual(len(rows),1);self.assertEqual(rows[0]['project'],project)
  self.assertEqual(c.get('/api/news?project=wrong').status_code,400)
 def test_no_live_mutation_routes(self):
  c=create_app(lambda:ROWS,lambda r:True).test_client()
  for path in ['/collect','/mark-emailed','/cleanup-old','/send-digest']:
   self.assertEqual(c.post(path,headers={'Origin':'http://localhost'}).status_code,404)
