# Copyright (c) 2026 Push. All rights reserved.
import unittest
from unittest.mock import patch, MagicMock
from integration.india_open_data.transport import government_get, PullError


class TransportTests(unittest.TestCase):
    def response(self, status=200, body=b'{}', headers=None):
        r=MagicMock();r.status=status;r.read.return_value=body
        r.getheader.side_effect=lambda k, default=None: (headers or {}).get(k,default)
        return r

    def call(self, response, params=None):
        with patch('integration.india_open_data.transport.socket.getaddrinfo',
                   return_value=[(2,1,6,'',('8.8.8.8',443))]), \
             patch('integration.india_open_data.transport._PinnedHTTPS') as conn:
            conn.return_value.getresponse.return_value=response
            body=government_get('https://api.data.gov.in/resource/test',params or {})
            return body,conn

    def test_success_no_redirect_no_proxy(self):
        body,conn=self.call(self.response())
        self.assertEqual(body,b'{}')
        conn.assert_called_once_with('api.data.gov.in','8.8.8.8',20)
        conn.return_value.close.assert_called_once()

    def test_non_public_and_mixed_dns(self):
        for addresses in (['127.0.0.1'],['10.0.0.2'],['169.254.169.254'],['8.8.8.8','10.0.0.1'],[]):
            with patch('integration.india_open_data.transport.socket.getaddrinfo',
                       return_value=[(2,1,6,'',(a,443)) for a in addresses]), \
                 patch('integration.india_open_data.transport._PinnedHTTPS') as conn:
                with self.assertRaises(PullError): government_get('https://niti.gov.in/',{})
                conn.assert_not_called()

    def test_status_no_retries(self):
        for status in (301,302,401,403,429,500):
            with self.subTest(status=status),self.assertRaises(PullError):
                self.call(self.response(status=status))

    def test_compressed_oversize_empty_mismatch(self):
        for r in (self.response(headers={'Content-Encoding':'gzip'}),
                  self.response(headers={'Content-Length':'5000001'}),
                  self.response(headers={'Content-Length':'invalid'}),
                  self.response(body=b''),self.response(headers={'Content-Length':'3'})):
            with self.assertRaises(PullError): self.call(r)

    def test_no_key_other_host_or_extra_parameters(self):
        with self.assertRaises(ValueError):government_get('https://niti.gov.in/',{'api-key':'secret'})
        with self.assertRaises(ValueError):government_get('https://api.data.gov.in/',{'api-key':'secret','extra':'x'})
        with self.assertRaises(ValueError):government_get('https://niti.gov.in/?api-key=secret',{})

    def test_full_ogd_url_never_copied_to_provenance(self):
        params={'api-key':'test-secret','format':'json','offset':0,'limit':1}
        with patch('integration.india_open_data.transport.socket.getaddrinfo',
                   return_value=[(2,1,6,'',('8.8.8.8',443))]), \
             patch('integration.india_open_data.transport._PinnedHTTPS') as conn:
            conn.return_value.getresponse.return_value=self.response()
            body=government_get('https://api.data.gov.in/resource/2ed5b97a-d5bc-404b-a8f3-2a08f20c0b8f',params)
            self.assertEqual(body,b'{}')
            self.assertIn('api-key=test-secret',conn.return_value.request.call_args.args[1])
        with self.assertRaises(ValueError):
            government_get('https://api.data.gov.in/restricted/test',params)

    def test_connection_failure_closes_and_does_not_expose_params(self):
        with patch('integration.india_open_data.transport.socket.getaddrinfo',
                   return_value=[(2,1,6,'',('8.8.8.8',443))]), \
             patch('integration.india_open_data.transport._PinnedHTTPS') as conn:
            conn.return_value.request.side_effect=RuntimeError('secret')
            with self.assertRaises(PullError) as e:government_get('https://niti.gov.in/',{})
            self.assertNotIn('secret',str(e.exception))
            conn.return_value.close.assert_called_once()

    def test_dns_error_sanitized(self):
        with patch('integration.india_open_data.transport.socket.getaddrinfo', side_effect=RuntimeError('secret')):
            with self.assertRaises(PullError) as e:government_get('https://niti.gov.in/',{})
            self.assertNotIn('secret',str(e.exception))

if __name__ == '__main__':unittest.main()
