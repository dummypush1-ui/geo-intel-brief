import unittest,os
from unittest.mock import patch
from .parser_runner import parse_supplied_bytes,ParserRefused
RSS=b'<rss version="2.0"><channel><title>Fixture</title><item><title>Trade</title><link>https://example.com/a</link><description>Tariff</description></item></channel></rss>'
class Tests(unittest.TestCase):
 def test_real_supplied_rss_os_isolated(self):
  r=parse_supplied_bytes(RSS);self.assertEqual(r['entries'][0]['title'],'Trade');self.assertEqual(r['network_namespace'],'loopback_only')
 def test_secret_environment_not_inherited(self):
  os.environ['UNRELATED_SECRET']='must-not-inherit'
  try:self.assertEqual(parse_supplied_bytes(RSS)['entry_count'],1)
  finally:del os.environ['UNRELATED_SECRET']
 def test_dtd_entity_and_non_utf8_refused(self):
  for b in (b'<!DOCTYPE rss SYSTEM "https://example.com/x">'+RSS,b'<!ENTITY a "x">'+RSS,RSS.decode().encode('utf-16')):
   with self.assertRaises(ParserRefused):parse_supplied_bytes(b)
 def test_bytes_budget(self):
  for b in ('text',b'',b'x'*1048577):
   with self.assertRaises(ParserRefused):parse_supplied_bytes(b)
 def test_atom_projection(self):
  b=b'<feed xmlns="http://www.w3.org/2005/Atom"><title>x</title><entry><title>Trade</title><link href="https://example.com/a"/><summary>Tariff</summary></entry></feed>'
  self.assertEqual(parse_supplied_bytes(b)['entries'][0]['link'],'https://example.com/a')
 def test_source_drift_refuses_before_spawn(self):
  with patch('collector112_prep.parser_runner.FILE_PINS',{'parser_child.py':'0'*64}):
   with self.assertRaises(ParserRefused):parse_supplied_bytes(RSS)
 def test_unavailable_isolation_no_fallback(self):
  with patch('collector112_prep.parser_runner.BWRAP','/missing/bwrap'):
   with self.assertRaises(OSError):parse_supplied_bytes(RSS)
 def test_entry_text_budget(self):
  b=b'<rss><channel><item><title>'+b'x'*10001+b'</title></item></channel></rss>'
  with self.assertRaises(ParserRefused):parse_supplied_bytes(b)
 def test_bozoflag_not_fabricated_health(self):
  r=parse_supplied_bytes(b'<rss><channel><item><title>Trade</title><link>https://example.com/a</link></item>')
  self.assertTrue(r['bozo']);self.assertNotIn('healthy',r)

if __name__=='__main__':unittest.main(verbosity=2)
