import gzip
import zlib
import unittest
from .transport_policy import endpoint_plan, decode_response, TransportRefused, MAX_DECODED
F = (('Fixture', 'https://example.com/rss?q=1', 'HIGH'),)
class Tests(unittest.TestCase):
    def decode(self, chunks, **kw):
        return decode_response(kw.pop('status', 200), kw.pop('headers', {}), chunks,
                               deadline=10, clock=kw.pop('clock', lambda: 1), **kw)
    def test_endpoint_plan_retains_hostname(self):
        r = endpoint_plan(F, F[0][1], ('8.8.8.8',), '8.8.8.8')
        self.assertEqual(r['tls_server_name'], 'example.com')
        self.assertEqual(r['request_target'], '/rss?q=1')
        self.assertFalse(r['network_proof'])
    def test_private_mixed_and_special_dns_refused(self):
        for ip in ('127.0.0.1','10.0.0.1','169.254.169.254','192.168.1.1','0.0.0.0',
                   '224.0.0.1','192.88.99.1','192.88.99.254','::1','fc00::1','fe80::1','ff02::1','::ffff:8.8.8.8',
                   '64:ff9b::808:808','fe80::1%eth0','2002:0808:0808::1'):
            with self.subTest(ip=ip), self.assertRaises(TransportRefused):
                endpoint_plan(F, F[0][1], ('8.8.8.8', ip), '8.8.8.8')
    def test_rebinding_peer_refused(self):
        for peer in ('1.1.1.1', '127.0.0.1'):
            with self.assertRaises(TransportRefused):
                endpoint_plan(F, F[0][1], ('8.8.8.8',), peer)
    def test_unlisted_and_nonstandard_origin_refused(self):
        with self.assertRaises(TransportRefused):
            endpoint_plan(F, 'https://example.com/other', ('8.8.8.8',), '8.8.8.8')
        for url in ('https://example.com:444/rss','https://example.com/rss#x',
                    'https://example..com/rss'):
            with self.assertRaises(TransportRefused):
                endpoint_plan((('F',url,'HIGH'),),url,('8.8.8.8',),'8.8.8.8')
    def test_identity_and_split_compression(self):
        data = b'x' * 10000
        for encoding, raw in [('identity',data),('gzip',gzip.compress(data)),('deflate',zlib.compress(data))]:
            r = self.decode([raw[:3],raw[3:]], headers={'Content-Encoding':encoding,'Content-Length':str(len(raw))})
            self.assertEqual(r['bytes'],data)
            self.assertEqual(r['wire_bytes'],len(raw))
    def test_bomb_at_cap_and_over_cap(self):
        for n in (MAX_DECODED, MAX_DECODED+1):
            raw = gzip.compress(b'x'*n)
            if n == MAX_DECODED:
                self.assertEqual(self.decode([raw], headers={'content-encoding':'gzip'})['decoded_bytes'],n)
            else:
                with self.assertRaises(TransportRefused):
                    self.decode([raw],headers={'content-encoding':'gzip'})
    def test_wire_and_chunk_limits(self):
        for chunks in ([b'x'*65537], [b'x'*65536]*17, [b'']*4097):
            with self.assertRaises(TransportRefused): self.decode(chunks)
    def test_bad_compression_no_partial_success(self):
        raw = gzip.compress(b'feed')
        for blob in (raw[:-1],raw+b'extra',raw+raw,b'bad gzip'):
            with self.assertRaises(TransportRefused):
                self.decode([blob],headers={'content-encoding':'gzip'})
    def test_status_redirect_and_header_rules(self):
        for status in (True,201,301,302,303,307,308,403,500):
            with self.assertRaises(TransportRefused): self.decode([b'x'],status=status)
        for headers in ({'Content-Length':'1','content-length':'1'}, {'content-length':'2'},
                        {'content-length':'99999999'}, {'content-length':'-1'},
                        {'content-encoding':'br'},{'content-encoding':'gzip, deflate'},
                        {'transfer-encoding':'chunked'}, {'x':'a\nb'}, {'x':1}):
            with self.assertRaises(TransportRefused): self.decode([b'x'],headers=headers)
    def test_expired_mid_stream_and_empty(self):
        values=iter([1,2,10])
        with self.assertRaises(TransportRefused): self.decode([b'x',b'y'],clock=lambda:next(values))
        for chunks in ([],[b''],['not bytes']):
            with self.assertRaises(TransportRefused): self.decode(chunks)
if __name__ == '__main__': unittest.main()
