import unittest
from unittest.mock import patch
from .parser_runner import parse_supplied_bytes,ParserRefused
B=b'<rss><channel>'+b''.join(b'<item><title>Trade'+str(i).encode()+b'</title><link>https://example.com/'+str(i).encode()+b'</link></item>'for i in range(150))+b'</channel></rss>'
class Tests(unittest.TestCase):
 def test_default100_same(self):
  r=parse_supplied_bytes(B);self.assertEqual(r['entry_count'],150);self.assertEqual(len(r['entries']),100)
 def test_150_all_projected(self):
  r=parse_supplied_bytes(B,projection_limit=150);self.assertEqual(len(r['entries']),150);self.assertEqual(r['entries'][-1]['title'],'Trade149')
 def test_200_cap_with_less_entries(self):self.assertEqual(len(parse_supplied_bytes(B,projection_limit=200)['entries']),150)
 def test_low_cap(self):self.assertEqual(len(parse_supplied_bytes(B,projection_limit=1)['entries']),1)
 def test_invalid_pre_spawn(self):
  for n in (True,0,201,1.0,'100',None):
   with patch('collector128_prep.parser_runner.subprocess.Popen')as p:
    with self.assertRaises(ParserRefused):parse_supplied_bytes(B,projection_limit=n)
    p.assert_not_called()
 def test_aggregate_unchanged_refuses(self):
  b=b'<rss><channel>'+(b'<item><title>'+b'x'*4000+b'</title></item>')*150+b'</channel></rss>'
  with self.assertRaises(ParserRefused):parse_supplied_bytes(b,projection_limit=200)
 def test_dtd_unchanged(self):
  with self.assertRaises(ParserRefused):parse_supplied_bytes(b'<!DOCTYPE rss>'+B,projection_limit=200)
