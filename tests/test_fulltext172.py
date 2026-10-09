import unittest,gzip
from integration.fulltext_policy import plan,prepare_body,FulltextHeld
U='https://example.org/article'
class Fulltext(unittest.TestCase):
 def test_default_off_never_reads_supplied_inputs(self):
  self.assertEqual(plan(object(),object(),object(),object())['state'],'disabled')
 def test_installed_exact_url_and_public_dns_peer(self):
  self.assertFalse(plan((U,),U,('8.8.8.8',),'8.8.8.8',enabled=True)['network'])
  cases=[((U,),U,('127.0.0.1',),'127.0.0.1'),((U,),U,('8.8.8.8','10.0.0.1'),'8.8.8.8'),((U,),U,('8.8.8.8',),'1.1.1.1'),((U,),U+'?other',('8.8.8.8',),'8.8.8.8')]
  for args in cases:
   with self.assertRaises(FulltextHeld):plan(*args,enabled=True)
  for url in ['http://example.org/x','https://u:p@example.org/x','https://127.0.0.1/x','https://localhost/x','https://example.org/x#secret','https://example.org/\rx','https://example.org/\\x']:
   with self.assertRaises(FulltextHeld):plan((url,),url,('8.8.8.8',),'8.8.8.8',enabled=True)
 def body(self,status=200,headers=None,chunks=(b'<html>data</html>',),clock=lambda:0):
  return prepare_body((U,),U,('8.8.8.8',),'8.8.8.8',status,headers or {},chunks,deadline=1,clock=clock,enabled=True)
 def test_bytes_no_extract_and_redirection_refused(self):
  self.assertEqual(self.body()['state'],'supplied_bytes_pending_isolated_extractor')
  for status in [301,302,307,308,404,500]:
   with self.assertRaises(FulltextHeld):self.body(status)
 def test_compressed_and_wire_header_deadline_caps(self):
  for headers,chunks in [({'Content-Encoding':'gzip'},(gzip.compress(b'x'*1048577),)),({},(b'x'*65537,)),({'Content-Length':'99999999'},(b'x',)),({'X-Test':'x'*2001},(b'x',)),({'Transfer-Encoding':'chunked'},(b'x',)),({'Content-Encoding':'gzip'},(b'bad',))]:
   with self.assertRaises(FulltextHeld):self.body(headers=headers,chunks=chunks)
  with self.assertRaises(FulltextHeld):self.body(clock=lambda:1)
