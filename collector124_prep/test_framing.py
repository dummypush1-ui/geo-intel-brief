import io,unittest,socket,ssl,gzip,zlib
from unittest.mock import patch,MagicMock
from .connector import fetch_one,ConnectorRefused
from collector113_prep.transport_policy import TransportRefused
import http.client
F=(('Fixture','https://example.com/rss','HIGH'),)
DNS=[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('8.8.8.8',443))]
class Tests(unittest.TestCase):
 def fetch(self,wire):
  raw=MagicMock();raw.getpeername.return_value=('8.8.8.8',443)
  tls=MagicMock();tls.getpeername.return_value=('8.8.8.8',443);tls.makefile.return_value=io.BytesIO(wire)
  ctx=MagicMock();ctx.check_hostname=True;ctx.verify_mode=ssl.CERT_REQUIRED;ctx.wrap_socket.return_value=tls
  with patch('collector124_prep.connector.socket.getaddrinfo',return_value=DNS),patch('collector124_prep.connector.socket.socket',return_value=raw),patch('collector124_prep.connector.ssl.create_default_context',return_value=ctx):
   try:return fetch_one(F,F[0][1])
   finally:self.assertTrue(raw.close.called);self.assertTrue(tls.close.called)
 def refused(self,wire):
  with self.assertRaises((ConnectorRefused,TransportRefused,http.client.HTTPException,ValueError)):self.fetch(wire)
 def test_complete_cl(self):self.assertEqual(self.fetch(b'HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nfeed')['decoded_bytes'],4)
 def test_truncated_cl_identity(self):self.refused(b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nfeed')
 def test_unframed_identity_refused_complete_or_truncated(self):
  for b in (b'<rss/>',b'<rss><channel>',b''):
   self.refused(b'HTTP/1.1 200 OK\r\n\r\n'+b)
 def test_unframed_gzip_complete(self):
  self.assertEqual(self.fetch(b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n\r\n'+gzip.compress(b'feed'))['decoded_bytes'],4)
 def test_unframed_compressed_truncation_refused(self):
  for encoding,body in ((b'gzip',gzip.compress(b'feed')),(b'deflate',zlib.compress(b'feed'))):
   for cut in (1,4,8):self.refused(b'HTTP/1.1 200 OK\r\nContent-Encoding: '+encoding+b'\r\n\r\n'+body[:-cut])
 def test_chunked_complete(self):self.assertEqual(self.fetch(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n4\r\nfeed\r\n0\r\n\r\n')['decoded_bytes'],4)
 def test_chunked_missing_termination(self):
  for b in (b'4\r\nfeed\r\n',b'4\r\nfee',b'Z\r\nfeed\r\n0\r\n\r\n'):self.refused(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'+b)
 def test_invalid_headers(self):
  for h in (b'Bad header\r\n',b'Content-Length: 4\r\nContent-Length: 4\r\n',b'Transfer-Encoding: chunked\r\nContent-Length: 4\r\n',b'Content-Length: -1\r\n',b'Content-Length: x\r\n',b'Content-Length: 1048577\r\n',b'Content-Encoding: br\r\n',b'Transfer-Encoding: gzip, chunked\r\n'):
   self.refused(b'HTTP/1.1 200 OK\r\n'+h+b'\r\nfeed')
 def test_redirect_refused(self):self.refused(b'HTTP/1.1 302 Found\r\nContent-Length: 4\r\n\r\nfeed')
