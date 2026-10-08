import unittest,ast
from pathlib import Path
from datetime import datetime,timezone
from .gnews_supplied import prepare_supplied_gnews,GNewsRefused
D=datetime(2026,1,1,tzinfo=timezone.utc)
T=ast.parse((Path(__file__).resolve().parents[1]/'intelligence/geo/config.py').read_text())
G=ast.literal_eval(next(n.value for n in T.body if type(n)is ast.Assign and any(type(t)is ast.Name and t.id=='GNEWS_QUERY_GROUPS'for t in n.targets)))
Q=[' OR '.join(g)for g in G]
def outcomes():return {q:{'state':'ok','results':[{'title':'Trade tariff','url':'https://example.com/a','description':'<b>trade tariff</b>','publisher':{'title':'Fixture'}}]}for q in Q}
class Tests(unittest.TestCase):
 def test_default_disabled(self):self.assertEqual(prepare_supplied_gnews({}, {},clock=D)['state'],'disabled_by_config')
 def test_enabled_backup_held_not_fake_sent(self):
  r=prepare_supplied_gnews({'ENABLE_GNEWS':'true'},outcomes(),clock=D);self.assertEqual(r['state'],'prepared');self.assertEqual(len(r['documents']),1);self.assertEqual(r['backup'],'held_pending_durable_adapter');self.assertNotIn('held_candidates',r)
 def test_original_queries_seen_title_and_docs(self):
  r=prepare_supplied_gnews({'ENABLE_GNEWS':'true','ENABLE_TELEGRAM_BACKUP':'false'},outcomes(),clock=D)
  self.assertEqual(r['query_trace'],Q);self.assertEqual(len(r['documents']),1);self.assertEqual(r['documents'][0]['credibility'],'MEDIUM');self.assertEqual(r['documents'][0]['summary'],'trade tariff')
 def test_source_error_continues(self):
  o=outcomes();o[Q[0]]={'state':'error','results':[]};r=prepare_supplied_gnews({'ENABLE_GNEWS':'true','ENABLE_TELEGRAM_BACKUP':'false'},o,clock=D)
  self.assertEqual(len(r['query_trace']),3);self.assertEqual(r['coarse_source_error_count'],1)
 def test_unavailable_original_skip(self):self.assertEqual(prepare_supplied_gnews({'ENABLE_GNEWS':'true'}, {},clock=D,available=False)['state'],'sdk_unavailable')
 def test_missing_outcomes_refused(self):
  with self.assertRaises(GNewsRefused):prepare_supplied_gnews({'ENABLE_GNEWS':'true'}, {},clock=D)
if __name__=='__main__':unittest.main()
