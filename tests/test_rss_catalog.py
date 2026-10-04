import unittest,json
from copy import deepcopy
from pathlib import Path
from integration.rss_catalog.catalog import validate_catalog
ROOT=Path(__file__).resolve().parents[1]
class RSSCandidateTests(unittest.TestCase):
 def data(self):return json.loads((ROOT/'integration/rss_catalog/candidates.json').read_text())
 def test_disabled_unknown_terms_distinct_candidate_counts(self):
  d=validate_catalog(self.data());self.assertEqual(len(d['items']),143);self.assertEqual(sum(r['candidate_validation']=='reachable_parseable' for r in d['items']),133);self.assertTrue(all(r['enabled'] is False and r['terms_state']=='unverified' for r in d['items']))
 def test_no_mutation(self):
  d=self.data();out=validate_catalog(d);out['items'][0]['publisher']='change';self.assertNotEqual(d['items'][0]['publisher'],'change')
 def test_activation_and_terms_not_promoted(self):
  for key,value in [('enabled',True),('terms_state','allowed')]:
   d=self.data();d['items'][0][key]=value
   with self.assertRaises(ValueError):validate_catalog(d)
 def test_duplicate_private_and_unsafe_url(self):
  for variant in ['duplicate','private','url']:
   d=self.data()
   if variant=='duplicate':d['items'].append(deepcopy(d['items'][0]))
   if variant=='private':d['items'][0]['telegram_url']='secret'
   if variant=='url':d['items'][0]['feed_url']='https://user:secret@example.com/rss'
   with self.assertRaises(ValueError):validate_catalog(d)
 def test_bool_observation_unknown_key(self):
  d=self.data();d['items'][0]['captured_item_count']=True
  with self.assertRaises(ValueError):validate_catalog(d)
  d=self.data();d['anything']='secret'
  with self.assertRaises(ValueError):validate_catalog(d)
 def test_url_regressions(self):
  for url in ['https://@example.com/rss','https://example.com:abc/rss','https://example.com:0/rss','https://example.com:65536/rss','https://exаmple.com/rss','https://127.0.0.1/rss','https://10.0.0.1/rss','https://169.254.1.1/rss','https://[::1]/rss','https://[fc00::1]/rss']:
   d=self.data();d['items'][0]['feed_url']=url
   with self.assertRaises(ValueError,msg=url):validate_catalog(d)
 def test_identity_schema_date_status_regressions(self):
  for where,key,value in [('root','schema_version',True),('root','schema_version',1.0),('root','captured_date','2026-02-30'),('root','captured_date','2026-10-05\n'),('row','id',[]),('row','id',{}),('row','captured_http_status',99),('row','captured_http_status',600)]:
   d=self.data();target=d if where=='root' else d['items'][0];target[key]=value
   with self.assertRaises(ValueError):validate_catalog(d)
 def test_mutable_copy_requires_revalidation(self):
  d=validate_catalog(self.data());d['items'][0]['enabled']=True
  with self.assertRaises(ValueError):validate_catalog(d)
 def test_legacy_ip_local_suffix_query_and_latest(self):
  for host in ['127.1','127.0.1','0x7f.0.0.1','0x7f.1','0177.0.0.1','10.1','192.168.1','169.254.1','0.0','localhost','a.localhost','a.local','a.internal','a.lan','[::127.0.0.1]','[64:ff9b::127.0.0.1]']:
   d=self.data();d['items'][0]['feed_url']='https://'+host+'/'
   with self.assertRaises(ValueError,msg=host):validate_catalog(d)
  for query in ['token=a','api_key=b','KEY=c','secret=x','password=x']:
   d=self.data();d['items'][0]['feed_url']='https://example.com/rss?'+query
   with self.assertRaises(ValueError):validate_catalog(d)
  for latest in ['9999-99-99','2026-10-05\n']:
   d=self.data();d['items'][0]['captured_latest_date']=latest
   with self.assertRaises(ValueError):validate_catalog(d)
 def test_casefold_host_duplicate_and_empty_hint(self):
  d=self.data();r=deepcopy(d['items'][0]);r['id']='a'*16;r['feed_url']=r['feed_url'].replace('www.aljazeera.com','WWW.ALJAZEERA.COM');d['items'].append(r)
  with self.assertRaises(ValueError):validate_catalog(d)
  for k in ['category_hint','country_hint','language_hint','discovery']:
   d=self.data();d['items'][0][k]=''
   with self.assertRaises(ValueError):validate_catalog(d)
