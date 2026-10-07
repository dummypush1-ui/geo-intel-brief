import unittest,hashlib
from datetime import datetime,timezone
from .fulltext_composition import prepare_enriched_cycle,EnrichmentRefused
from collector115_prep.profile import compile_profile
D=datetime(2026,1,1,tzinfo=timezone.utc)
F=compile_profile({})['feeds']
RSS=b'<rss><channel><item><title>Tariff trade</title><link>https://example.com/a</link><description>short</description></item></channel></rss>'
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
