"""Literal independent contract oracle, not copied from implementation."""
import unittest,sys
from integration.html_text209 import strip_html_once,decode_once
VECTORS=[
 ('AT&T','AT&T'),('&amp 5','&amp 5'),('&#65 x','&#65 x'),('&#x41','&#x41'),('&;','&;'),('&#;','&#;'),('&foo;','&foo;'),
 ('&amp;amp;lt;','&amp;lt;'),('&amp;lt;','&lt;'),('&lt;','<'),('&amp;','&'),('&quot;&#39;','"\''),
 ('&eacute; &NotEqualTilde;','é ≂̸'),('&#73;ndia &#x49;ndia','India India'),('&#X000041; &#00065;','A A'),('&#128512;','😀'),
 ('&#0; &#1; &#8; &#127; &#128; &#159;','&#0; &#1; &#8; &#127; &#128; &#159;'),
 ('&#9;x&#10;y&#13;z','x y z'),('&nbsp;x&#160;y','x y'),
 ('&#xD800; &#55296; &#x110000; &#xFDD0; &#xFFFF; &#x10FFFF;','&#xD800; &#55296; &#x110000; &#xFDD0; &#xFFFF; &#x10FFFF;'),
 ('&#-1; &#+65; &#١; &#xＧ;','&#-1; &#+65; &#١; &#xＧ;'),
 ('<p>India</p><p>tariff</p>','India tariff'),('<p title="a > b">India</p> tariff','India tariff'),
 ('&lt;b&gt;India&lt;/b&gt; tariff','India tariff'),('&amp;lt;b&amp;gt;India&amp;lt;/b&amp;gt;','&lt;b&gt;India&lt;/b&gt;'),
 ('&lt;script&gt;alert&lt;/script&gt;',''),('&amp;lt;script&amp;gt;','&lt;script&gt;'),
 ('a<script>bad<b>x</b></script>b','a b'),('x <script>y','x'),('x <style>y','x'),
 ('<div','<div'),('a <b','a <b'),('a < b','a < b'),('x <3 y','x <3 y'),('if a<b and c>d','if a<b and c>d'),
 ('a<!--bad-->b','a b'),('<!--broken','<!--broken'),('<![wat','<![wat'),('<![CDATA[bad]]>ok','ok'),
 ('<!wat>hi','hi'),('<!DOCTYPE x>hi','hi'),('a <!doctype q ">"> b','a b'),('<?pi >hi','hi'),
 ('<iframe allowfullscreen></iframe>t','t'),('<a href="u" download rel=x>l</a>','l'),
 ('<img src="a" async/>p','p'),('<p itemscope>t</p>','t'),('<td nowrap>t</td>','t'),
 ('<video playsinline>t</video>','t'),('<br clear>t','t'),
 ('<script defer>alert(1)</script>ok','ok'),('<script nomodule>var a=1</script>z','z'),
 ('<script async>x</script>ok','ok'),('<style anything>x</style>ok','ok'),
 ('a <b c>d','a <b c>d'),('<custom disabled>t</custom>','<custom disabled>t'),
 ('',''),('plain café','plain café'),('a\n\t b','a b'),('A&amp;B&copy;','A&B©'),
]
class HTML209(unittest.TestCase):
 def test_golden(self):
  print('HTML209 golden interpreter:',sys.version.split()[0])
  for raw,expected in VECTORS:
   with self.subTest(raw=raw):self.assertEqual(strip_html_once(raw),expected)
 def test_oversized_digits(self):
  s='&#'+'0'*10000+'65;';self.assertEqual(strip_html_once(s),s)
 def test_scalar_control_range(self):
  for n in list(range(0,32))+list(range(127,160)):
   s='&#%d;'%n;expected=chr(n) if n in (9,10,13) else s
   self.assertEqual(decode_once(s),expected)
 def test_unknown_and_all_known_named(self):
  from html.entities import html5
  for k,v in html5.items():
   if k.endswith(';'):self.assertEqual(decode_once('&'+k),v)
 def test_no_downstream_redecode(self):
  from intelligence.geo.processing.classifier import classify,strip_html
  s=strip_html('&amp;#73;ndia tariff');self.assertEqual(s,'&#73;ndia tariff');self.assertEqual(classify('',s)[3],'')
  self.assertEqual(classify('AT&amp;T','')[0],'GENERAL')
 def test_no_runtime_version_gate(self):
  from unittest.mock import patch
  with patch.object(sys,'version_info',(3,99,99)):
   self.assertEqual(strip_html_once('<b>&amp;</b>'),'&')
 def test_punctuation_fuzz_total(self):
  import random
  r=random.Random(209)
  for i in range(2000):
   s=''.join(r.choice('<>![]?;/&\'"abc012\n') for _ in range(r.randrange(100)))
   self.assertIsInstance(strip_html_once(s),str)
 def test_real_supplied_rss_once(self):
  from integration.supplied_feed_fixture import prepare_supplied_feed
  from datetime import datetime,timezone
  d=datetime(2026,10,9,tzinfo=timezone.utc)
  rows=[{'title':'AT&amp;T','link':'https://example.invalid/a','summary':'&amp;#73;ndia tariff','published':'2026-10-08T12:00:00Z'}]
  out=prepare_supplied_feed(('Fixture','https://example.invalid/rss','HIGH'),rows,cutoff=d.replace(day=1),fallback_clock=d)
  self.assertEqual(out['candidates'][0]['summary'],'&#73;ndia tariff');self.assertEqual(out['candidates'][0]['title'],'AT&amp;T')
 def test_real_gnews_ast_once(self):
  import ast
  from pathlib import Path
  from datetime import datetime,timezone
  from integration.publication_dates.policy import publication_date
  from intelligence.geo.processing.classifier import classify,strip_html
  from unittest.mock import MagicMock
  tree=ast.parse((Path(__file__).parents[1]/'intelligence/geo/collectors/gnews_search.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='collect')
  client=MagicMock();client.get_news.return_value=[{'title':'AT&amp;T tariff','url':'https://example.invalid/a','description':'&amp;#73;ndia tariff','published date':'2026-10-08T12:00:00Z','publisher':'Fixture'}];captured=[]
  scope={'HAS_GNEWS':True,'GNews':lambda **k:client,'GNEWS_LANGUAGE':'en','GNEWS_COUNTRY':'IN','GNEWS_MAX_RESULTS':10,'GNEWS_PERIOD':'1d','_build_queries':lambda:['fixture'],'datetime':type('Clock',(),{'now':staticmethod(lambda tz:datetime(2026,10,9,tzinfo=timezone.utc))}),'timezone':timezone,'publication_date':publication_date,'strip_html':strip_html,'classify':classify,'ACTIVE_CATEGORIES':['TRADE'],'dedupe_articles':lambda x,**k:x,'DEDUPE_THRESHOLD':.85,'save_articles_bulk':lambda docs:captured.extend(docs)or len(docs),'ArticleWriteOutcomeError':RuntimeError}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'gnews-html209-fixture','exec'),scope);self.assertEqual(scope['collect'](),1);self.assertEqual(captured[0]['summary'],'&#73;ndia tariff');self.assertEqual(captured[0]['country'],'');self.assertEqual(captured[0]['title'],'AT&amp;T tariff')
 def test_both_wrappers_old_shape_refused(self):
  from unittest.mock import patch
  import integration.supplied_feed_fixture as a
  import collector129_prep.supplied_feed as b
  old=b'\ndef strip_html(text):\n return text\n_ENTITY_MAP={}\n_TAG_RE=None\n'
  from pathlib import Path
  original=Path.read_bytes
  def read(p):return old if str(p).endswith('processing/classifier.py') else original(p)
  for m in (a,b):
   with patch.object(Path,'read_bytes',read):
    with self.assertRaises(m.FeedRefused):m._source()
 def test_both_wrappers_vectors(self):
  from integration.supplied_feed_fixture import prepare_supplied_feed as a
  from collector129_prep.supplied_feed import prepare_supplied_feed as b
  from datetime import datetime,timezone
  d=datetime(2026,10,9,tzinfo=timezone.utc)
  for s in ('&amp;lt;','&lt;b&gt;India&lt;/b&gt; tariff','<p title="a > b">India</p> tariff','&#73;ndia tariff'):
   row={'title':'AT&amp;T','summary':s,'link':'https://example.invalid/a','published':'2026-10-08T12:00:00Z'}
   for fn in (a,b):
    out=fn(('Fixture','https://example.invalid/rss','HIGH'),[row],cutoff=d.replace(day=1),fallback_clock=d)
    self.assertEqual(out['candidates'][0]['summary'],strip_html_once(s));self.assertEqual(out['candidates'][0]['title'],'AT&amp;T')
