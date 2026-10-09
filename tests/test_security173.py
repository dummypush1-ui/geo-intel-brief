import unittest,json,re,hashlib
from pathlib import Path
from packaging.requirements import Requirement
ROOT=Path(__file__).resolve().parents[1]
class SecurityProfiles(unittest.TestCase):
 def test_exact_current_security_profile_pins(self):
  for file,req in [('requirements-offline-reviewed.candidate.txt','2.34.2'),('integration/dependency_build/requirements-offline-built.txt','2.33.0')]:
   text=(ROOT/file).read_text();pins={n.lower():v for n,v in re.findall(r'^([A-Za-z0-9_-]+)==([^\s]+)',text,re.M)}
   for name,value in {'flask':'3.1.3','werkzeug':'3.1.9','pymongo':'4.18.2','python-dotenv':'1.2.2','requests':req,'feedparser':'6.0.11','gunicorn':'22.0.0'}.items():self.assertEqual(pins[name],value)
  self.assertIn('python-dotenv==1.2.4',(ROOT/'requirements-staging.txt').read_text())
 def test_changed_hashes_and_no_historical_receipt_rewrite(self):
  artifacts=json.loads((ROOT/'integration/dependabot_security173/artifacts.json').read_text())
  for file in ['requirements-offline-reviewed.candidate.txt','integration/dependency_build/requirements-offline-built.txt']:
   text=(ROOT/file).read_text()
   for row in artifacts:
    if row['name'].lower()=='sgmllib3k' and 'candidate' in file:continue
    line=next((l for l in text.splitlines() if l.lower().startswith(row['name'].lower().replace('_','-')+'=='+row['version']+' ')),None)
    if line:self.assertIn('--hash=sha256:'+row['sha256'],line)
  snap=json.loads((ROOT/'integration/pypdf_remediation105/historical-locks.json').read_text())
  for row in snap['locks'].values():self.assertEqual(hashlib.sha256(row['text'].encode()).hexdigest(),row['sha256'])
 def test_new_default_extra_edges_satisfied(self):
  x=json.loads((ROOT/'integration/dependabot_security173/installed.json').read_text());ds={r['name'].lower().replace('_','-'):r for r in x['packages']}
  for row in x['packages']:
   for s in row['requires_dist']:
    q=Requirement(s)
    if q.marker and not q.marker.evaluate({'extra':''}):continue
    self.assertIn(q.name.lower().replace('_','-'),ds);self.assertIn(ds[q.name.lower().replace('_','-')]['version'],q.specifier)
