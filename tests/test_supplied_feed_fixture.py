from integration.html_text209 import strip_html_once
from integration.publication_dates.policy import publication_date
import unittest,copy,ast,sys
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from dateutil import parser
from integration.supplied_feed_fixture import *
D=datetime(2026,1,2,12,tzinfo=timezone.utc);C=D-timedelta(days=2);SPEC=('Fixture','https://example.invalid/feed','HIGH')
def entry(**kw):return {'title':' Trade tariff news ','link':' https://example.invalid/story ','summary':'<p>Tariff &amp; trade</p>','published':D.isoformat()}|kw
class Tests(unittest.TestCase):
 def run_case(self,rows=None,**kw):return prepare_supplied_feed(SPEC,rows if rows is not None else [entry()],cutoff=C,fallback_clock=D,**kw)
 def test_slice_before_filter_equality_and_isolation(self):
  rows=[entry(title=''),entry(published=C.isoformat()),entry()];old=copy.deepcopy(rows);r=self.run_case(rows,max_items=2)
  self.assertEqual(len(r['candidates']),1);self.assertEqual(r['candidates'][0]['published'],C);self.assertEqual(rows,old)
  r['candidates'][0]['title']='changed';self.assertEqual(rows,old)
 def test_missing_present_empty_precedence(self):
  a=entry(summary='',description='description',published='',updated=C.isoformat());r=self.run_case([a]);self.assertFalse(r['candidates']);self.assertEqual(r['publication_date_holds'],{'missing':1})
  a.pop('summary');a.pop('published');r=self.run_case([a]);self.assertEqual(r['candidates'][0]['summary'],'description');self.assertEqual(r['candidates'][0]['published'],C)
  self.assertFalse(self.run_case([{},entry(link='')])['candidates'])
 def test_html_strip_entities(self):self.assertEqual(self.run_case()['candidates'][0]['summary'],'Tariff & trade')
 def test_dates_full_partial_naive_offsets(self):
  for date in ('2026-01-02T12:00:00Z','2026-01-02 12:00:00 GMT','2026-01-02 17:30:00 +0530'):
   r=self.run_case([entry(published=date)]);self.assertTrue(r['candidates']);self.assertIs(type(r['candidates'][0]['published'].tzinfo),timezone)
  self.assertFalse(self.run_case([entry(published='12:00')])['candidates'])
 def test_malformed_unknown_zone_unverified_fallback(self):
  for v in ('bad date','2026-01-02 12:00 XYZ'):
   r=self.run_case([entry(published=v)]);self.assertEqual(r['date_fallback_count'],0);self.assertFalse(r['candidates']);self.assertEqual(sum(r['publication_date_holds'].values()),1);self.assertEqual(r['declared_source_mode'],'ok')
 def test_declared_http_parser_failure_not_health(self):
  for kw in ({'http_mode':'error'},{'parser_mode':'error'}):
   r=self.run_case(**kw);self.assertEqual(r['declared_source_mode'],'error');self.assertFalse(r['candidates']);self.assertEqual(r['coarse_errors'],['supplied_source_error'])
  self.assertEqual(self.run_case(http_mode='error')['parser_calls'],0)
 def test_bad_input_before_source_no_hooks(self):
  class Text(str):
   def __len__(self):raise AssertionError('hook')
  for rows in ([entry(summary=Text('x'))],[entry(extra='x')],[entry(summary='\ud800')],[entry(summary='x'*10001)]):
   with patch('integration.supplied_feed_fixture._source',side_effect=AssertionError('executed')):
    with self.assertRaises(FeedRefused):self.run_case(rows)
  for v in (True,0,101,10**1000):
   with self.assertRaises(FeedRefused):self.run_case(max_items=v)
 def test_budget_selected_date_boundary(self):
  with self.assertRaises(FeedRefused):self.run_case([entry(summary='😀'*10000) for i in range(30)])
  for value in ('2101-01-01','9999-01-01'):
   self.assertFalse(self.run_case([entry(published=value)])['candidates'])
 def test_drift_effects_fields(self):
  with patch.dict(PINS,{'intelligence/geo/collectors/rss.py':'0'*64}):
   with self.assertRaises(FeedRefused):self.run_case()
  before=set(sys.modules);r=self.run_case()
  for m in ('requests','feedparser','intelligence.geo.collectors.rss','intelligence.geo.config'):self.assertNotIn(m,set(sys.modules)-before)
  self.assertEqual(set(r['candidates'][0]),{'title','url','source','credibility','summary','published'});self.assertFalse(r['network'])
 def test_independent_original_oracle(self):
  rows=[entry(),entry(summary='',description='desc',published='12:00')]
  class Resp:
   content=b'fixture'
   def raise_for_status(self):pass
  class Requests:
   def get(self,*a,**k):return Resp()
  class Feed:
   def parse(self,*a):return type('Parsed',(),{'entries':copy.deepcopy(rows)})()
  class DateParser:
   def parse(self,v):return parser.parse(v,default=D.replace(tzinfo=None))
  class Clock:
   @staticmethod
   def now(tz):return D
  defs=[];scope={'strip_html_once':strip_html_once,'requests':Requests(),'feedparser':Feed(),'REQUEST_TIMEOUT':20,'MAX_ITEMS_PER_FEED':50,'publication_date':publication_date,'record_date_hold':lambda state:None,'dateparser':DateParser(),'datetime':Clock,'timezone':timezone,'re':re}
  for p,names in [('intelligence/geo/collectors/rss.py',('_fetch_feed',)),('intelligence/geo/processing/classifier.py',('strip_html','parse_date'))]:
   tree=ast.parse((ROOT/p).read_bytes());defs.extend(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
   for n in tree.body:
    if isinstance(n,ast.Assign):
     for t in n.targets:
      if isinstance(t,ast.Name) and t.id in ('_HEADERS','_ENTITY_MAP'):scope[t.id]=ast.literal_eval(n.value)
      if isinstance(t,ast.Name) and t.id=='_TAG_RE':scope[t.id]=re.compile(ast.literal_eval(n.value.args[0]))
  exec(compile(ast.Module(body=defs,type_ignores=[]),'independent-original-feed','exec'),scope)
  self.assertEqual(self.run_case(rows)['candidates'],scope['_fetch_feed'](SPEC,C))
