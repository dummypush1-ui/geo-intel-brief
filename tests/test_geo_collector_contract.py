import unittest,ast,hashlib
from datetime import datetime,timezone
from copy import deepcopy
from unittest.mock import patch
from integration.geo_collector_contract import prepare_geo_documents,run_geo_fixture_cycle,GeoFixtureStore,ROOT,RSS_PIN
from intelligence.geo.processing.classifier import classify
from intelligence.geo.processing.dedupe import dedupe_articles
D=datetime(2026,1,1,tzinfo=timezone.utc)
def row(title='Trade tariff new order',url='https://example.com/news'):
 return {'title':title,'url':url,'source':'Fixture','summary':'Supply chain tariff '+'x'*500,'published':D,'credibility':'HIGH'}
class Tests(unittest.TestCase):
 def test_original_collect_differential_docs_storeclock(self):
  candidates=[row(),row(url='https://other.example/story')];captured=[]
  class Executor:
   def __init__(self,**kw):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def map(self,fn,feeds):return [deepcopy(candidates)]
  source=(ROOT/'intelligence/geo/collectors/rss.py').read_bytes();self.assertEqual(hashlib.sha256(source).hexdigest(),RSS_PIN)
  collect=next(n for n in ast.parse(source).body if type(n) is ast.FunctionDef and n.name=='collect')
  scope={'__builtins__':{'min':min,'len':len},'DEFAULT_FEEDS':[('Fixture','https://example.com/rss','HIGH')],'datetime':type('Clock',(),{'now':staticmethod(lambda tz:D)}),'timezone':timezone,'timedelta':__import__('datetime').timedelta,'LOOKBACK_HOURS':48,'ThreadPoolExecutor':Executor,'_enrich_with_full_text':lambda x:x,'classify':classify,'dedupe_articles':dedupe_articles,'DEDUPE_THRESHOLD':.85,'ACTIVE_CATEGORIES':['TRADE'],'save_articles_bulk':lambda docs:captured.extend(deepcopy(docs)) or len(docs),'ENABLE_TELEGRAM_BACKUP':False}
  exec(compile(ast.Module(body=[collect],type_ignores=[]),'original-offline-oracle','exec'),scope);scope['collect']()
  result=prepare_geo_documents(candidates,['TRADE'],.85);self.assertEqual(result['documents'],captured);self.assertEqual(result['prepared_count'],1);self.assertEqual(captured[0]['corroboration'],2);self.assertEqual(len(captured[0]['summary']),300);self.assertNotIn('emailed',captured[0]);self.assertIsNone(captured[0]['telegram_message_id']);self.assertEqual(candidates[0]['summary'],row()['summary'])
  store=GeoFixtureStore();run_geo_fixture_cycle(candidates,['TRADE'],.85,D,store);expected=deepcopy(captured[0]);expected['created_at']=D.isoformat();self.assertEqual(store.snapshot()[expected['url']],expected)
 def test_duplicate_vs_failed_and_insert(self):
  s=GeoFixtureStore();r=run_geo_fixture_cycle([row()],['TRADE'],.85,D,s);self.assertEqual(r['inserted_count'],1)
  self.assertEqual(run_geo_fixture_cycle([row()],['TRADE'],.85,D,s)['duplicate_count'],1)
  self.assertEqual(run_geo_fixture_cycle([row()],['TRADE'],.85,D,s,[row()['url']])['failed_count'],1);self.assertFalse(r['live_writes']);self.assertEqual(r['telegram_backup'],'unwired_not_dropped')
 def test_unknown_overrides_stripped(self):
  a=row();a.update(_id='x',emailed=True,created_at='override',telegram_url='https://evil.example');s=GeoFixtureStore();run_geo_fixture_cycle([a],['TRADE'],.85,D,s);d=s.snapshot()[a['url']];self.assertNotIn('_id',d);self.assertNotIn('emailed',d);self.assertEqual(d['telegram_url'],'');self.assertEqual(d['created_at'],D.isoformat())
 def test_inputs_rejected_before_store_change(self):
  for a in (dict(row(),published='2026-01-01'),dict(row(),summary=object()),dict(row(),credibility='other'),dict(row(),title='')):
   s=GeoFixtureStore()
   with self.assertRaises(ValueError):run_geo_fixture_cycle([a],['TRADE'],.85,D,s)
   self.assertEqual(s.snapshot(),{})
 def test_hash_refusal(self):
  with patch('integration.geo_collector_contract.RSS_PIN','0'*64):
   with self.assertRaises(ValueError):prepare_geo_documents([row()],['TRADE'],.85)
 def test_empty_and_category_filter(self):
  s=GeoFixtureStore();self.assertEqual(run_geo_fixture_cycle([],['TRADE'],.85,D,s)['prepared_count'],0)
  self.assertEqual(run_geo_fixture_cycle([row()],['GENERAL'],.85,D,s)['prepared_count'],0);self.assertEqual(s.snapshot(),{})
 def test_callback_writer_not_accepted(self):
  with self.assertRaises(ValueError):run_geo_fixture_cycle([row()],['TRADE'],.85,D,lambda x:x)

 def test_original_parsed_date_offset_differential(self):
  from intelligence.geo.processing.classifier import parse_date
  for value in ('Mon, 05 Oct 2026 12:00:00 GMT','Mon, 05 Oct 2026 12:00:00 +0530','2026-10-05T12:00:00Z'):
   parsed=parse_date(value);a=row();a['published']=parsed
   d=prepare_geo_documents([a],['TRADE'],.85)['documents'][0]
   self.assertEqual(d['published'],parsed.isoformat())
   self.assertEqual(datetime.fromisoformat(d['published']).timestamp(),parsed.timestamp())
 def test_processing_source_pin_refusal(self):
  with patch('integration.geo_collector_contract.PROCESSING_PINS',{'intelligence/geo/processing/classifier.py':'0'*64}):
   with self.assertRaises(ValueError):prepare_geo_documents([row()],['TRADE'],.85)
