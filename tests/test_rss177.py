import unittest,hashlib,ast,io,contextlib
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from integration.bounded_rss.driver import BoundedRSSDriver,RSSRefused
FEEDS=(('Fixed','https://example.com/feed','HIGH'),);HEAD={'User-Agent':'fixture'}
def fetched(blob=b'<rss/>'):
 return {'bytes':blob,'input_sha256':hashlib.sha256(blob).hexdigest(),'wire_bytes':len(blob),'url':FEEDS[0][1],'peer':'8.8.8.8','tls_hostname_verified':True,'delivery':False}
class Tests(unittest.TestCase):
 def test_default_held_before_network(self):
  with patch('integration.bounded_rss.driver.run_fetch',side_effect=AssertionError('network')):
   with self.assertRaises(RSSRefused):BoundedRSSDriver(FEEDS).get(FEEDS[0][1],timeout=20,headers=HEAD)
 def test_exact_installation_before_fetch(self):
  d=BoundedRSSDriver(FEEDS,enabled=True)
  with patch('integration.bounded_rss.driver.run_fetch',side_effect=AssertionError('network')):
   for u in ['https://evil.com/feed','https://example.com/other','https://user:secret@example.com/feed']:
    with self.assertRaises(RSSRefused):d.get(u,timeout=20,headers=HEAD)
 def test_opaque_handle_once(self):
  d=BoundedRSSDriver(FEEDS,enabled=True,projection_limit=150)
  with patch('integration.bounded_rss.driver.run_fetch',return_value=fetched()),patch('integration.bounded_rss.driver.parse_supplied_bytes',return_value={'bozo':False,'entries':[]}) as parser:
   r=d.get(FEEDS[0][1],timeout=20,headers=HEAD);self.assertIs(r.content,r);self.assertEqual(d.parse(r).entries,[]);self.assertEqual(parser.call_args.kwargs['projection_limit'],150)
   with self.assertRaises(RSSRefused):d.parse(r)
   with self.assertRaises(RSSRefused):d.parse(FEEDS[0][1])
 def test_overflow_hash_peer_malformed_closed(self):
  variants=[dict(fetched(),bytes=b'x'*1048577),dict(fetched(),input_sha256='wrong'),dict(fetched(),peer='127.0.0.1'),dict(fetched(),wire_bytes=1048577)]
  d=BoundedRSSDriver(FEEDS,enabled=True)
  for r in variants:
   with patch('integration.bounded_rss.driver.run_fetch',return_value=r),patch('integration.bounded_rss.driver.parse_supplied_bytes',side_effect=AssertionError('parser')):
    with self.assertRaises(RSSRefused):d.get(FEEDS[0][1],timeout=20,headers=HEAD)
  with patch('integration.bounded_rss.driver.run_fetch',return_value=fetched()),patch('integration.bounded_rss.driver.parse_supplied_bytes',return_value={'bozo':True,'entries':[]}):
   with self.assertRaises(RSSRefused):d.get(FEEDS[0][1],timeout=20,headers=HEAD)
 def test_remaining_phase_budget(self):
  d=BoundedRSSDriver(FEEDS,enabled=True)
  with patch('integration.bounded_rss.driver.time.monotonic',side_effect=[0,19,19]),patch('integration.bounded_rss.driver.run_fetch',return_value=fetched()),patch('integration.bounded_rss.driver.parse_supplied_bytes',return_value={'bozo':False,'entries':[]}) as p:
   d.get(FEEDS[0][1],timeout=20,headers=HEAD);self.assertEqual(p.call_args.kwargs['timeout'],1)
 def test_original_safe_label_no_untrusted_values(self):
  root=Path(__file__).resolve().parents[1];tree=ast.parse((root/'intelligence/geo/collectors/rss.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_fetch_feed')
  class Refuse:
   def get(self,*a,**k):raise ValueError('https://secret.invalid/?token=SECRET')
  scope={'requests':Refuse(),'REQUEST_TIMEOUT':20,'_HEADERS':HEAD,'datetime':datetime,'timezone':timezone};exec(compile(ast.Module(body=[node],type_ignores=[]),'rss177','exec'),scope)
  out=io.StringIO()
  with contextlib.redirect_stdout(out):self.assertEqual(scope['_fetch_feed'](('RAWSECRET','https://secret.invalid','HIGH'),datetime.now(timezone.utc)),[])
  self.assertEqual(out.getvalue(),'[RSS] source_refused\n')
 def test_no_unsafe_import_fallback(self):
  root=Path(__file__).resolve().parents[1];s=(root/'intelligence/geo/collectors/rss.py').read_text();self.assertNotIn('import requests',s);self.assertNotIn('import feedparser',s)
 def test_real_contained_parser_projection(self):
  blob=b'<rss version="2.0"><channel><title>Fixture</title><item><title>Trade</title><link>https://example.com/a</link><pubDate>Fri, 09 Oct 2026 00:00:00 GMT</pubDate></item></channel></rss>'
  with patch('integration.bounded_rss.driver.run_fetch',return_value=fetched(blob)):
   d=BoundedRSSDriver(FEEDS,enabled=True);r=d.get(FEEDS[0][1],timeout=20,headers=HEAD);self.assertEqual(d.parse(r).entries[0]['title'],'Trade')
 def test_isolation_missing_refuses_no_fallback(self):
  d=BoundedRSSDriver(FEEDS,enabled=True)
  with patch('integration.bounded_rss.driver.run_fetch',return_value=fetched()),patch('collector128_prep.parser_runner.BWRAP','/no-bwrap'):
   with self.assertRaises(RSSRefused):d.get(FEEDS[0][1],timeout=20,headers=HEAD)
