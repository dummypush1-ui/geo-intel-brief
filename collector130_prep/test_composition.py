from scripts.doc_lookup import source_bytes, source_text
import unittest,hashlib
from unittest.mock import patch
from datetime import datetime,timezone
from .network_selection import select_installed_source
from .extra_profile import compile_installed_profile,ProfileRefused
D=datetime(2026,1,1,tzinfo=timezone.utc);U=compile_installed_profile({})['feeds'][0][1]
def blob(n):return b'<rss><channel>'+b''.join(b'<item><title>Trade'+str(i).encode()+b'</title><link>https://example.com/'+str(i).encode()+b'</link><description>Tariff</description><pubDate>Thu, 01 Jan 2026 00:00:00 GMT</pubDate></item>'for i in range(n))+b'</channel></rss>'
def result(b,u=U):return {'bytes':b,'input_sha256':hashlib.sha256(b).hexdigest(),'wire_bytes':len(b),'url':u,'peer':'8.8.8.8','tls_hostname_verified':True,'delivery':False}
class Tests(unittest.TestCase):
 def run_n(self,cap,n=200,u=U,extras=()):
  settings={'MAX_ITEMS_PER_FEED':str(cap)}
  if extras:settings['EXTRA_RSS_FEEDS']=u
  with patch('collector130_prep.network_selection.run_fetch',return_value=result(blob(n),u)):
   return select_installed_source(settings,u,clock=D,reviewed_extra_urls=extras)
 def test_150_full_actual_parser_selection(self):
  r=self.run_n(150);self.assertEqual(len(r['candidates']),150);self.assertEqual(r['candidates'][-1]['title'],'Trade149');self.assertFalse(r['live_write_ready'])
 def test_200_full(self):self.assertEqual(len(self.run_n(200)['candidates']),200)
 def test_default40(self):
  with patch('collector130_prep.network_selection.run_fetch',return_value=result(blob(150))):self.assertEqual(len(select_installed_source({},U,clock=D)['candidates']),40)
 def test_extra150(self):
  u='https://example.com/custom';r=self.run_n(150,u=u,extras=(u,));self.assertEqual(r['source'],'Custom');self.assertEqual(len(r['candidates']),150);self.assertIn('installation_allowlist_owner_review',r['pending_gates'])
 def test_no_silent_above200(self):
  with patch('collector130_prep.network_selection.run_fetch')as f:
   with self.assertRaises(ProfileRefused):select_installed_source({'MAX_ITEMS_PER_FEED':'201'},U,clock=D)
   f.assert_not_called()
 def test_budget_same25_projection_agrees(self):
  with patch('collector130_prep.network_selection.time.monotonic',side_effect=[0,1,20,21]),patch('collector130_prep.network_selection.run_fetch',return_value=result(blob(1))),patch('collector130_prep.network_selection.parse_supplied_bytes',return_value={'entries':[],'entry_count':0,'bozo':False})as p:
   select_installed_source({'MAX_ITEMS_PER_FEED':'150'},U,clock=D);self.assertEqual(p.call_args.kwargs,{'timeout':5,'projection_limit':150})
 def test_missing_base_source_fails_loud(self):
  from tempfile import TemporaryDirectory
  from pathlib import Path
  with TemporaryDirectory()as d,patch('collector130_prep.base_profile.ROOT',Path(d)),patch('collector130_prep.network_selection.run_fetch')as f:
   with self.assertRaises(FileNotFoundError):select_installed_source({},U,clock=D)
   f.assert_not_called()
 def test_missing_selector_source_fails_loud(self):
  from tempfile import TemporaryDirectory
  from pathlib import Path
  with TemporaryDirectory()as d,patch('collector129_prep.supplied_feed.ROOT',Path(d)),patch('collector130_prep.network_selection.run_fetch',return_value=result(blob(1))):
   with self.assertRaises(FileNotFoundError):select_installed_source({},U,clock=D)
 def test_selection_budget_error_propagates(self):
  from collector129_prep.supplied_feed import FeedRefused
  with patch('collector130_prep.network_selection.run_fetch',return_value=result(blob(1))),patch('collector130_prep.network_selection.prepare_supplied_feed',side_effect=FeedRefused('fixture input budget')):
   with self.assertRaises(FeedRefused):select_installed_source({},U,clock=D)
 def test_exact_inventory(self):
  import json,hashlib
  from pathlib import Path
  b=Path(__file__).resolve().parent;j=json.loads((b/'inventory.json').read_text());expected={'base_profile.py','extra_profile.py','network_selection.py','__init__.py','BOUNDED-COMPOSITION.md'};self.assertEqual(set(j['files']),expected)
  for n,h in j['files'].items():self.assertEqual(h,hashlib.sha256(source_bytes(b/n)).hexdigest())
