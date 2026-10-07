import unittest,gzip,socket,ssl
from unittest.mock import patch,MagicMock
from .connector import fetch_one,ConnectorRefused
from collector113_prep.transport_policy import TransportRefused
F=(('Fixture','https://example.com/rss','HIGH'),)
DNS=[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('8.8.8.8',443))]
class Tests(unittest.TestCase):
 def run_fetch(self,*,dns=DNS,peer='8.8.8.8',status=200,headers=None,chunks=None):
  raw=MagicMock();raw.getpeername.return_value=(peer,443)
  tls=MagicMock();tls.getpeername.return_value=(peer,443)
  ctx=MagicMock();ctx.check_hostname=True;ctx.verify_mode=ssl.CERT_REQUIRED;ctx.wrap_socket.return_value=tls
  resp=MagicMock();resp.status=status;resp.chunked=any(k.lower()=='transfer-encoding' for k,v in (headers or []));resp.getheaders.return_value=headers or [];resp.read.side_effect=(chunks or [b'feed'])+[b'']
  with patch('collector114_prep.connector.socket.getaddrinfo',return_value=dns),patch('collector114_prep.connector.socket.socket',return_value=raw),patch('collector114_prep.connector.ssl.create_default_context',return_value=ctx),patch('collector114_prep.connector.http.client.HTTPResponse',return_value=resp):
   out=fetch_one(F,F[0][1]);self.assertTrue(raw.close.called);self.assertTrue(tls.close.called);self.assertTrue(resp.close.called)
   return out,raw,tls,ctx
 def test_pinned_connect_and_sni(self):
  out,raw,tls,ctx=self.run_fetch()
  raw.connect.assert_called_once_with(('8.8.8.8',443));ctx.wrap_socket.assert_called_once_with(raw,server_hostname='example.com')
  self.assertIn(b'Host: example.com\r\n',tls.sendall.call_args[0][0]);self.assertTrue(out['tls_hostname_verified'])
 def test_gzip_and_chunked(self):
  blob=gzip.compress(b'feed')
  out,*_=self.run_fetch(headers=[('Transfer-Encoding','chunked'),('Content-Encoding','gzip')],chunks=[blob])
  self.assertEqual(out['decoded_bytes'],4)
 def test_mixed_dns_no_socket(self):
  dns=DNS+[(socket.AF_INET,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',('127.0.0.1',443))]
  with patch('collector114_prep.connector.socket.getaddrinfo',return_value=dns),patch('collector114_prep.connector.socket.socket')as s:
   with self.assertRaises(TransportRefused):fetch_one(F,F[0][1])
   s.assert_not_called()
 def test_redirects_and_headers(self):
  with self.assertRaises(ConnectorRefused):self.run_fetch(status=302)
  for h in ([('Content-Length','1'),('content-length','1')],[('Transfer-Encoding','chunked'),('Content-Length','4')],[('Transfer-Encoding','gzip, chunked')]):
   with self.assertRaises(ConnectorRefused):self.run_fetch(headers=h)
 def test_actual_peer_rebinding(self):
  with self.assertRaises(ConnectorRefused):self.run_fetch(peer='1.1.1.1')
 def test_invalid_url_before_dns(self):
  with patch('collector114_prep.connector.socket.getaddrinfo')as d:
   with self.assertRaises(TransportRefused):fetch_one(F,'https://example.com/other')
   d.assert_not_called()
if __name__=='__main__':unittest.main()

class WireTests(unittest.TestCase):
 """Real stdlib HTTP framing parser over supplied bytes, no network."""
 def fetch_wire(self,wire):
  import io
  raw=MagicMock();raw.getpeername.return_value=('8.8.8.8',443)
  tls=MagicMock();tls.getpeername.return_value=('8.8.8.8',443);tls.makefile.return_value=io.BytesIO(wire)
  ctx=MagicMock();ctx.check_hostname=True;ctx.verify_mode=ssl.CERT_REQUIRED;ctx.wrap_socket.return_value=tls
  with patch('collector114_prep.connector.socket.getaddrinfo',return_value=DNS),patch('collector114_prep.connector.socket.socket',return_value=raw),patch('collector114_prep.connector.ssl.create_default_context',return_value=ctx):
   return fetch_one(F,F[0][1])
 def test_chunked_real_parser(self):
  self.assertEqual(self.fetch_wire(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n4\r\nfeed\r\n0\r\n\r\n')['decoded_bytes'],4)
 def test_content_length_real_parser(self):
  self.assertEqual(self.fetch_wire(b'HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nfeed')['decoded_bytes'],4)
 def test_eof_framed_gzip(self):
  wire=b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n\r\n'+gzip.compress(b'feed')
  self.assertEqual(self.fetch_wire(wire)['decoded_bytes'],4)
 def test_malformed_framing(self):
  import http.client
  for wire in (b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nfeed',
               b'HTTP/1.1 200 OK\r\nContent-Length: 4\r\nContent-Length: 4\r\n\r\nfeed',
               b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\nZ\r\nfeed\r\n',
               b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Length: 4\r\n\r\n4\r\nfeed\r\n0\r\n\r\n'):
   with self.subTest(wire=wire),self.assertRaises((ConnectorRefused,TransportRefused,http.client.HTTPException,ValueError)):
    self.fetch_wire(wire)

class FaultTests(unittest.TestCase):
 def test_tls_failure_closes_raw(self):
  raw=MagicMock();raw.getpeername.return_value=('8.8.8.8',443)
  ctx=MagicMock();ctx.check_hostname=True;ctx.verify_mode=ssl.CERT_REQUIRED;ctx.wrap_socket.side_effect=ssl.SSLError('fixture')
  with patch('collector114_prep.connector.socket.getaddrinfo',return_value=DNS),patch('collector114_prep.connector.socket.socket',return_value=raw),patch('collector114_prep.connector.ssl.create_default_context',return_value=ctx):
   with self.assertRaises(ssl.SSLError):fetch_one(F,F[0][1])
   raw.close.assert_called_once()
 def test_dns_empty_refused(self):
  with patch('collector114_prep.connector.socket.getaddrinfo',return_value=[]),patch('collector114_prep.connector.socket.socket')as s:
   with self.assertRaises(ConnectorRefused):fetch_one(F,F[0][1])
   s.assert_not_called()
 def test_timeout_before_dns(self):
  with patch('collector114_prep.connector.socket.getaddrinfo')as d:
   for n in (False,0,31,float('nan')):
    with self.assertRaises(ConnectorRefused):fetch_one(F,F[0][1],timeout=n)
   d.assert_not_called()
