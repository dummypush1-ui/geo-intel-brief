import ast,copy,json,math,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
from integration import brics_feed_b5 as m
CATS=['GEOPOLITICS','TRADE','SANCTIONS','RISK','CONFERENCE','GENERAL']
def source(name='A',**kw):return dict(name=name,url='https://example.test/feed',country='India',tier=1,type='rss',**kw)
def entry(title='BRICS summit',**kw):return dict(dict(title=title,link='https://example.test/story',summary=''),**kw)
def outcome(entries=None,bozo=False,state='feed'):return dict(entries=[entry()]if entries is None else entries,bozo=bozo,state=state)
class Tests(unittest.TestCase):
 def runprep(self,**kw):
  args=dict(sources=[source()],outcomes={0:outcome()},categories=CATS,threshold=.85,checked_at='2026-10-16T00:00:00Z');args.update(kw);return m.prepare({m.FLAG:'true'},**args)
 def test_off_no_reads_or_input_hooks(self):
  with patch.object(Path,'read_bytes',side_effect=AssertionError):
   self.assertIsNone(m.prepare({},sources=object()));self.assertIsNone(m.prepare({m.FLAG:'false'}))
 def test_exact_flags(self):
  for value in ('TRUE','1','',True):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
 def test_parsed_order_cap_clean_dates_and_status_count(self):
  entries=[entry('<b>BRICS summit '+str(i)+'</b>',summary=' <i>'+('x'*600)+'</i> ',published='not a date')for i in range(40)]
  # Override summary after factory because it has a default summary.
  r=self.runprep(outcomes={0:outcome(entries)});self.assertEqual(len(r['parsed_candidates']),30);self.assertEqual(r['source_statuses'][0]['count'],40);row=r['parsed_candidates'][0];self.assertEqual(row['title'],'BRICS summit 0');self.assertEqual(len(row['summary']),500);self.assertEqual(row['published'],'not a date');self.assertNotIn('collected_at',row)
 def test_warning_error_empty_and_disabled_separate(self):
  sources=[source('A'),source('B'),source('C'),source('D',enabled=False),source('E')]
  r=self.runprep(sources=sources,outcomes={0:outcome(bozo=True),1:outcome([],True),2:outcome([],state='error'),4:outcome([])})
  self.assertEqual([s['status']for s in r['source_statuses']],['warning','error','error','disabled','ok']);self.assertEqual(len(r['parsed_candidates']),1)
 def test_tiers_and_duplicate_names_use_index(self):
  sources=[source('same'),dict(source('same'),tier=2),source('same',enabled=False)]
  r=self.runprep(sources=sources,outcomes={1:outcome()},tiers=(2,));self.assertEqual([s['source_index']for s in r['source_statuses']],[1,2])
  with self.assertRaises(m.Held):self.runprep(sources=sources,outcomes={0:outcome()},tiers=(2,))
 def test_dedupe_category_then_relevance_and_no_input_mutation(self):
  sources=[source('A'),source('B')];outcomes={0:outcome([entry()]),1:outcome([entry(),entry('Local sports final')])};before=copy.deepcopy(outcomes)
  r=self.runprep(sources=sources,outcomes=outcomes);p=r['processing'];self.assertEqual(p['candidate_count'],3);self.assertEqual(p['deduped_count'],2);self.assertEqual(p['prepared_count'],1);self.assertEqual(p['items'][0]['corroborated_by'],['A','B']);self.assertEqual(outcomes,before)
  self.assertEqual(self.runprep(categories=['TRADE'])['processing']['prepared_count'],0)
 def test_official_is_held_disposition_not_stub_news(self):
  sources=[source(),dict(source('official'),tier=3,type='scrape',enabled=False)]
  r=self.runprep(sources=sources,include_official=True);self.assertEqual(r['official_source_indexes'],[1]);self.assertIn('held',r['official_disposition']);self.assertEqual(len(r['parsed_candidates']),1)
 def test_plain_closed_shapes_and_exact_types(self):
  class D(dict):pass
  for kw in [dict(sources=D()),dict(outcomes={True:outcome()}),dict(sources=[dict(source(),extra=1)]),dict(outcomes={0:dict(outcome(),extra=1)}),dict(outcomes={0:outcome([{'title':object()}])}),dict(outcomes={0:outcome([],True,'error')}),dict(threshold=True),dict(threshold=math.nan),dict(tiers=(True,)),dict(categories=['GENERAL','GENERAL']),dict(checked_at='2026-10-16'),dict(checked_at='2026-10-16T00:00:00+05:30'),dict(include_official=1)]:
   with self.subTest(kw=repr(kw)),self.assertRaises(m.Held):self.runprep(**kw)
 def test_source_drift_fails_closed(self):
  original=Path.read_bytes
  with patch.object(Path,'read_bytes',lambda p:b'drift'if str(p).endswith('/brics/collectors/rss.py')else original(p)),self.assertRaisesRegex(m.Held,'source drift'):self.runprep()
 def test_no_network_delivery_store_or_production_mount(self):
  with patch('socket.socket',side_effect=AssertionError):r=self.runprep()
  for key in ('network','xml_parsed','writes','schedules','delivery','critical_alerts','production_mounted'):self.assertIs(r[key],False)
 def test_invalid_candidate_refused_not_silently_dropped(self):
  with self.assertRaisesRegex(m.Held,'processing boundary'):self.runprep(outcomes={0:outcome([entry('')])})
 def test_input_and_output_budgets(self):
  with self.assertRaises(m.Held):self.runprep(outcomes={0:outcome([entry()]*101)})
  sources=[source(str(i))for i in range(40)]
  with self.assertRaisesRegex(m.Held,'processing capacity'):self.runprep(sources=sources,outcomes={i:outcome([entry()]*30)for i in range(40)})
  with self.assertRaisesRegex(m.Held,'byte budget'):self.runprep(sources=[source(str(i))for i in range(3)],outcomes={i:outcome([dict(entry(),summary='x'*10000)]*100)for i in range(3)})
 def test_no_legacy_imports_or_config(self):
  code="""
import builtins
original=builtins.__import__
def guard(name,*a,**k):
 if name.startswith('intelligence.brics')or name in ('requests','feedparser','dotenv','schedule'):raise AssertionError(name)
 return original(name,*a,**k)
builtins.__import__=guard
from integration.brics_feed_b5 import prepare,FLAG
r=prepare({FLAG:'true'},sources=[dict(name='A',url='https://example.test/feed',type='rss',tier=1)],outcomes={0:dict(state='feed',bozo=False,entries=[])},categories=['GENERAL'],threshold=.8,checked_at='2026-10-16T00:00:00Z')
assert r['state']=='supplied_brics_feed_prepared_only'
"""
  subprocess.run([sys.executable,'-c',code],check=True)
 def test_original_pinned_process_feed_differential(self):
  # Execute only pinned pure extraction defs with inert record-status/print,
  # not the source module, its config imports or any collector.
  tree=ast.parse((m.ROOT/'intelligence/brics/collectors/rss.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ('_clean','_process_feed')];record=[]
  scope={'_TAG_RE':m.re.compile(r'<[^>]+>'),'_record_status':lambda *a:record.append(a),'print':lambda *a:None}
  exec(compile(ast.Module(body=defs,type_ignores=[]),'pinned-brics-pure-extraction','exec'),scope)
  class Feed(dict):
   @property
   def entries(self):return self['entries']
   @property
   def bozo(self):return self['bozo']
  for bozo,entries in [(False,[]),(True,[]),(True,[entry()]),(False,[dict(entry(),title='<b>BRICS summit</b>',summary='<i>'+('x'*600)+'</i>',updated='raw')]*35)]:
   expected=scope['_process_feed'](source(),Feed(bozo=bozo,entries=entries));actual=self.runprep(outcomes={0:outcome(entries,bozo)})
   self.assertEqual(actual['parsed_candidates'],expected);status=actual['source_statuses'][0];self.assertEqual((status['status'],status['count']),(record[-1][1],record[-1][2]))
 def test_invalid_flag_with_valid_dependencies(self):
  for value in ('TRUE','1',''):
   with self.subTest(value=value),self.assertRaisesRegex(m.Held,'Exact supplied-feed flag'):m.prepare({m.FLAG:value},sources=[source()],outcomes={0:outcome()},categories=CATS,threshold=.85,checked_at='2026-10-16T00:00:00Z')
 def test_environment_nonstring_values(self):
  with self.assertRaisesRegex(m.Held,'environment strings'):m.prepare({m.FLAG:'true','other':1})
 def test_source_and_outcome_counts(self):
  for count in (0,51):
   with self.subTest(count=count),self.assertRaisesRegex(m.Held,'Bounded supplied sources'):self.runprep(sources=[source()for _ in range(count)])
  with self.assertRaisesRegex(m.Held,'Bounded supplied sources'):self.runprep(outcomes={i:outcome()for i in range(51)})
 def test_duplicate_tiers(self):
  with self.assertRaisesRegex(m.Held,'tier selection'):self.runprep(tiers=(1,1))
 def test_missing_required_source_field(self):
  s=source();del s['url']
  with self.assertRaisesRegex(m.Held,'Closed source'):self.runprep(sources=[s])
 def test_extra_entry_field(self):
  with self.assertRaisesRegex(m.Held,'Closed parsed entry'):self.runprep(outcomes={0:outcome([dict(entry(),extra='x')])})
 def test_whitespace_identity_and_source_type_disagreement(self):
  for kw in ({'name':' '},{'url':' '},{'tier':3},{'type':'scrape'},{'enabled':'yes'}):
   with self.subTest(kw=kw),self.assertRaises(m.Held):self.runprep(sources=[dict(source(),**kw)])
 def test_boolean_outcome_key_and_bogus_state(self):
  with self.assertRaisesRegex(m.Held,'source index'):self.runprep(outcomes={True:outcome()})
  with self.assertRaisesRegex(m.Held,'parsed-feed outcome'):self.runprep(outcomes={0:outcome(state='bogus')})
 def test_incremental_raw_input_budget_alone(self):
  # Raw utf8 >2MiB; JSON deliberately tiny so only incremental budget can fail.
  entries=[dict(entry(),summary='x'*10000)]*100
  with patch.object(m.json,'dumps',return_value='small'),self.assertRaisesRegex(m.Held,'input byte budget'):self.runprep(sources=[source(str(i))for i in range(3)],outcomes={i:outcome(entries)for i in range(3)})
 def test_json_escaped_input_budget_alone(self):
  # Raw text <2MiB but ensure_ascii JSON escapes expand past2MiB.
  entries=[dict(entry(),summary='\x01'*10000)]*100
  with self.assertRaisesRegex(m.Held,'input byte budget'):self.runprep(outcomes={0:outcome(entries)})
 def test_output_byte_budget_alone(self):
  original=m.json.dumps;calls=[]
  def dump(value,*a,**kw):
   calls.append(1)
   return original(value,*a,**kw)if len(calls)==1 else'x'*(2*1024*1024+1)
  with patch.object(m.json,'dumps',dump),self.assertRaisesRegex(m.Held,'output byte budget'):self.runprep()
  self.assertEqual(len(calls),2)
 def test_link_whitespace_is_stripped(self):
  r=self.runprep(outcomes={0:outcome([dict(entry(),link='  https://example.test/trim  ')])});self.assertEqual(r['parsed_candidates'][0]['url'],'https://example.test/trim')
 def test_source_country_url_and_timestamp_caps(self):
  for kw in ({'country':'x'*201},{'url':'x'*2049}):
   with self.subTest(kw=next(iter(kw))),self.assertRaisesRegex(m.Held,'Bounded exact text'):self.runprep(sources=[dict(source(),**kw)])
  # Python accepts an arbitrary fractional precision, so a parse-only guard
  # does not substitute for the exact timestamp length cap.
  with self.assertRaisesRegex(m.Held,'Bounded exact text'):self.runprep(checked_at='2026-10-16T00:00:00.'+'0'*50+'Z')
if __name__=='__main__':unittest.main()
