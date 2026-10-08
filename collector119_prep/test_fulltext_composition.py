import unittest,hashlib
from datetime import datetime,timezone
from .fulltext_composition import prepare_enriched_cycle,EnrichmentRefused
from collector115_prep.profile import compile_profile
D=datetime(2026,1,1,tzinfo=timezone.utc)
F=compile_profile({})['feeds']
RSS=b'<rss><channel><item><title>Tariff trade</title><link>https://example.com/a</link><description>short</description><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item></channel></rss>'
def proof(blob):return {'bytes':blob,'input_sha256':hashlib.sha256(blob).hexdigest(),'wire_bytes':len(blob)}
class Tests(unittest.TestCase):
 def test_disabled_original_default(self):
  r=prepare_enriched_cycle({}, {F[0][1]:proof(RSS)}, {},clock=D)
  self.assertEqual(r['fulltext_state'],'disabled_by_config');self.assertEqual(r['enriched_candidates'][0]['summary'],'short');self.assertFalse(r['full_article_verified'])
 def test_original_enrichment_truncation(self):
  r=prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},{F[0][1]:proof(RSS)}, {'https://example.com/a':{'download':'text','extract':'text','text':'x'*1000}},clock=D)
  self.assertEqual(r['enriched_candidates'][0]['summary'],'x'*700+'...');self.assertEqual(len(r['documents'][0]['summary']),300)
 def test_unavailable_preserves_rss(self):
  r=prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},{F[0][1]:proof(RSS)}, {},clock=D,available=False)
  self.assertEqual(r['fulltext_state'],'unavailable_supplied');self.assertEqual(r['enriched_candidates'][0]['summary'],'short')
 def test_provider_failure_preserves_rss(self):
  r=prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},{F[0][1]:proof(RSS)}, {'https://example.com/a':{'download':'error','extract':'empty','text':''}},clock=D)
  self.assertEqual(r['enriched_candidates'][0]['summary'],'short')
 def test_missing_outcome_refused(self):
  with self.assertRaises(EnrichmentRefused):prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},{F[0][1]:proof(RSS)}, {},clock=D)
 def test_whole_run_dedupe_after_enrichment(self):
  r=prepare_enriched_cycle({}, {F[0][1]:proof(RSS),F[1][1]:proof(RSS)}, {},clock=D)
  self.assertEqual(len(r['enriched_candidates']),2);self.assertEqual(len(r['documents']),1)
if __name__=='__main__':unittest.main()

class OutcomeBudgetTests(unittest.TestCase):
 def evidence(self,count=120):
  feeds=compile_profile({})['feeds'];evidence={};outcomes={}
  for group in range((count+39)//40):
   items=[]
   for n in range(group*40,min(count,(group+1)*40)):
    u='https://example.com/a'+str(n)
    items.append('<item><title>Trade '+str(n)+'</title><link>'+u+'</link><description>short</description><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item>')
    outcomes[u]={'download':'text','extract':'text','text':'fulltext trade '+str(n)}
   blob=('<rss><channel>'+''.join(items)+'</channel></rss>').encode()
   evidence[feeds[group][1]]=proof(blob)
  return evidence,outcomes
 def test120_eligible_over100_dict_cap_now_supported(self):
  evidence,outcomes=self.evidence()
  r=prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},evidence,outcomes,clock=D)
  self.assertEqual(len(r['enriched_candidates']),120)
  self.assertTrue(all(a['summary'].startswith('fulltext trade')for a in r['enriched_candidates']))
  self.assertFalse(r['production_ready'])
 def test_aggregate_budget_not_relaxed(self):
  from collector110_prep.input_budget import InputRefused
  evidence,outcomes=self.evidence(240)
  for o in outcomes.values():o['text']='x'*10000
  with self.assertRaises(InputRefused):prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},evidence,outcomes,clock=D)
 def test_custom_outcome_object_rejected_before_ast(self):
  from collector110_prep.input_budget import InputRefused
  from unittest.mock import patch
  evidence,outcomes=self.evidence(1);outcomes['https://example.com/a0']=object()
  with patch('collector119_prep.fulltext_composition.prepare_supplied_fulltext')as adapter:
   with self.assertRaises(InputRefused):prepare_enriched_cycle({'ENABLE_FULL_TEXT':'true'},evidence,outcomes,clock=D)
   adapter.assert_not_called()
