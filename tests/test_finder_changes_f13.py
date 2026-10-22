import unittest,json
from unittest.mock import patch
from pathlib import Path
from integration import finder_changes_f13 as m,finder_composition_f9 as f9
from integration.public_preview_builder import build_public_preview
from integration.public_ai_answers import Refused
from tests import test_finder_composition_f9 as fixture
from tests.test_code_news_coverage_binding_prep import ORIGIN
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  fixture.Tests.setUpClass();cls.binding=fixture.Tests.binding;cls.env=dict(fixture.Tests.env,**{m.FLAG:'true'});cls.selection=f9.prepare(cls.env,cls.binding)
 @classmethod
 def tearDownClass(cls):fixture.Tests.tearDownClass()
 def test_off_before_inputs_exact_flags(self):
  with patch.object(m.Snapshot,'__init__',side_effect=AssertionError):self.assertIsNone(m.prepare({},None))
  for v in ('TRUE','1',''):
   with self.assertRaises(Refused):m.prepare({m.FLAG:v},None)
  with self.assertRaises(Refused):m.prepare({m.FLAG:'true'},None)
  with self.assertRaises(Refused):m.prepare({},None,self.binding)
 def test_explicit_composition_dependency_true_flag(self):
  for env in ({m.FLAG:'true'},{m.FLAG:'true',f9.FLAG:'false'},{m.FLAG:'true',f9.FLAG:'TRUE'}):
   with self.assertRaisesRegex(Refused,'Selected Finder required'):m.enabled(env)
  self.assertTrue(m.enabled({m.FLAG:'true',f9.FLAG:'true'}))
 def test_identical_and_distinct_identity_not_chronology(self):
  before=m.Snapshot(self.binding);after=m.Snapshot(self.binding)
  result=m.compare(before,after,'HS','090121');self.assertEqual(result['snapshot_relationship'],'identical_artifact');self.assertFalse(result['baseline_chronology_verified'])
  # Synthetic metadata diagnostic only, does not mint a source artifact.
  after.meta=dict(after.meta,package_sha256='a'*64);result=m.compare(before,after,'HS','090121');self.assertEqual(result['snapshot_relationship'],'distinct_supplied_artifacts_chronology_unverified');self.assertFalse(result['baseline_chronology_verified'])
 def test_same_snapshot_no_change_and_dates_hashes(self):
  s=m.Snapshot(self.binding);result=m.compare(s,s,'HS','090121');self.assertFalse(any(result['changes'].values()));self.assertEqual(result['link_changes'],[]);self.assertFalse(result['currentness_verified']);self.assertEqual(result['official_refreshes'],0);self.assertIn('dataset_build_label',result['before_snapshot']);self.assertEqual(result['before_snapshot']['package_sha256'],self.binding.package_sha256)
 def test_exact_fields_and_missing_is_not_deletion(self):
  before={'state':'present','wording':'A','listed_duty':'10%','gst':['5%','source'],'duplicate_identity':False};after={**before,'wording':'B','listed_duty':'20%','gst':['12%','source']};self.assertEqual(m.compare_values(before,after),dict(wording_changed=True,listed_duty_changed=True,gst_changed=True,presence_changed=False))
  s=m.Snapshot(self.binding);absent=m.compare(s,s,'HS','999999999999');self.assertEqual(absent['before']['state'],'not_present_in_snapshot');self.assertIn('absence is not deletion',absent['notice'])
 def test_original_linkage_targets_bounded_sample(self):
  s=m.Snapshot(self.binding);links=s.links('IN','090121');self.assertEqual(len(links),22)
  for row in links:self.assertLessEqual(len(row['extension_sample']),8);self.assertEqual(row['sample_complete'],row['extension_count']<=8)
  self.assertEqual(next(r['target']for r in s.links('IN','09012110')if r['system']=='IN'),'09012110');self.assertEqual(next(r['target']for r in s.links('IN','09012110')if r['system']=='US'),'090121')
 def test_synthetic_changed_link_and_presence_projection(self):
  # Test-only mutated projection, not an F8 source or publishable artifact.
  before=m.Snapshot(self.binding);after=m.Snapshot(self.binding)
  after.rows[('HS','090121')]=tuple([0,'090121','SYNTHETIC CHANGED WORDING','0901','09','15%'])
  after.rows[('US','0901219999')]=(2,'0901219999','SYNTHETIC LINK',None,'09','')
  after.sorted['US']=sorted(after.sorted['US']+['0901219999'])
  result=m.compare(before,after,'HS','090121');self.assertTrue(result['changes']['wording_changed']);self.assertTrue(result['changes']['listed_duty_changed']);self.assertIn('US',[r['system']for r in result['link_changes']])
  del after.rows[('HS','090121')];result=m.compare(before,after,'HS','090121');self.assertTrue(result['changes']['presence_changed']);self.assertEqual(result['after']['state'],'not_present_in_snapshot');self.assertIn('not deletion',result['notice'])
 def test_same_count_beyond_sample_link_digest_detects_change(self):
  before=m.Snapshot(self.binding);after=m.Snapshot(self.binding)
  # Fixed synthetic prefix with >8 national extensions and same sample/count.
  before.sorted['US']=[f'999999{i:04d}'for i in range(12)];after.sorted['US']=before.sorted['US'][:-1]+['9999999999']
  a=next(r for r in before.links('HS','999999')if r['system']=='US');b=next(r for r in after.links('HS','999999')if r['system']=='US')
  self.assertEqual(a['extension_sample'],b['extension_sample']);self.assertEqual(a['extension_count'],b['extension_count']);self.assertNotEqual(a['extension_membership_sha256'],b['extension_membership_sha256'])
 def test_no_baseline_no_comparison(self):
  c=m.prepare(self.env,self.selection);result=c.read('HS','090121');self.assertEqual(result['state'],'baseline_unavailable');self.assertNotIn('changes',result)
 def test_missing_baseline_never_builds_dataset_projection(self):
  with patch.object(m.Snapshot,'__init__',side_effect=AssertionError('unused dataset projection')):
   c=m.Comparison(self.selection);result=c.read('HS','090121')
  self.assertIsNone(c.after);self.assertIsNone(c.before);self.assertEqual(result['state'],'baseline_unavailable');self.assertEqual(result['after_snapshot']['package_sha256'],self.binding.package_sha256)
 def test_same_binding_reuses_one_projection_but_still_checks_drift(self):
  original=m.Snapshot
  with patch.object(m,'Snapshot',wraps=original)as construct:
   c=m.Comparison(self.selection,self.binding)
   self.assertEqual(construct.call_count,1);self.assertIs(c.before,c.after)
  self.assertEqual(c.read('HS','090121')['snapshot_relationship'],'identical_artifact')
  with patch.object(type(self.binding),'verify',side_effect=ValueError('drift')):
   with self.assertRaises(ValueError):c.read('HS','090121')
 def test_distinct_binding_object_never_shares_projection(self):
  from dataclasses import replace
  other=replace(self.binding);self.assertIsNot(other,self.binding)
  c=m.Comparison(self.selection,other);self.assertIsNot(c.before,c.after)
  with patch.object(type(other),'verify',side_effect=lambda:None)as verify:
   c.read('HS','090121');self.assertGreaterEqual(verify.call_count,3)
 def test_wrong_inputs_and_drift_fail_closed(self):
  with self.assertRaises(Refused):m.Snapshot(object())
  c=m.Comparison(self.selection,self.binding)
  for system,code in [('evil','090121'),('HS','<script>'),('HS','090121.00')]:
   with self.assertRaises(Refused):c.read(system,code)
  with patch.object(type(self.binding),'verify',side_effect=ValueError('drift')):
   with self.assertRaises(ValueError):c.read('HS','090121')
 def test_mount_closed_read_only_routes_and_off_page(self):
  app=build_public_preview(self.env,finder_candidate_binding=self.binding,finder_comparison_baseline=self.binding);self.addCleanup(app.extensions['finder_composition_close_f9']);client=app.test_client()
  for path in (m.PAGE,m.BASE+'view.js',m.BASE+'view.css',m.API+'?system=HS&code=090121'):
   r=client.get(path,base_url=ORIGIN);self.assertEqual(r.status_code,200,path);self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertEqual(client.get(path,base_url='https://evil.test').status_code,403)
  self.assertEqual(client.post(m.API,base_url=ORIGIN,headers={'Origin':ORIGIN}).status_code,403)
  for query in ('?system=HS&code=090121&code=1','?system=HS','?system=HS&code=090121&url=x'):self.assertEqual(client.get(m.API+query,base_url=ORIGIN).status_code,400)
  self.assertEqual(client.get(m.API+'?system=HS&code=090121',base_url=ORIGIN).json['state'],'compared');self.assertIn('Snapshot changes',client.get('/workspace',base_url=ORIGIN).text)
  off=build_public_preview(dict(self.env,**{m.FLAG:'false'}),finder_candidate_binding=self.binding);self.addCleanup(off.extensions['finder_composition_close_f9']);self.assertEqual(off.test_client().get(m.PAGE,base_url=ORIGIN).status_code,403)
 def test_no_JS_storage_AI_or_auto_fetch(self):
  text=(m.ROOT/'view.js').read_text();self.assertNotIn('innerHTML',text);self.assertNotIn('localStorage',text);self.assertNotIn('setInterval',text);self.assertNotIn('setTimeout',text);self.assertEqual(text.count('fetch('),1);self.assertIn("addEventListener('submit'",text)
