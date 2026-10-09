import hashlib
import io
import json
import unittest
from unittest.mock import Mock, patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from integration.news_api import create_app
from integration.post_json207 import BodyRefused, parse, CAP
from integration.news_view import views
from integration.public_news import public_news_row
from integration.relevance import match

ROWS = {'geo': [{'_id': '1', 'url': 'https://example.com/a', 'title': 'HS 090121 India steel\nproducts'}], 'brics': []}
KEY = hashlib.sha256(b'geo\nhttps://example.com/a').hexdigest()


class Post207(unittest.TestCase):
    def setUp(self):
        self.reader = Mock(return_value=ROWS)
        self.app = create_app(reader=self.reader, authorize=lambda req: True)
        self.client = self.app.test_client()

    def send(self, raw, path='/api/related-news', content_type='application/json', **kw):
        return self.client.post(path, data=raw, content_type=content_type, headers={'Origin': 'http://localhost'}, **kw)

    def environ(self, raw, length, terminated=False, extra=None):
        env = EnvironBuilder(path='/api/related-news', method='POST', content_type='application/json').get_environ()
        env['wsgi.input'] = io.BytesIO(raw)
        if length is None:
            env.pop('CONTENT_LENGTH', None)
        else:
            env['CONTENT_LENGTH'] = length
        if terminated:
            env['wsgi.input_terminated'] = True
        if extra:
            env.update(extra)
        return Request(env)

    def refused(self, raw, status=400, **kw):
        response = self.send(raw, **kw)
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json, {'error': 'Invalid read context'})
        self.reader.assert_not_called()

    def test_valid_semantics_against_old_handler_loop(self):
        for context in [{}, {'code': '090121'}, {'country': 'India'}, {'product_terms': ['steel\nproducts']}, {'code': '01', 'system': 'IN', 'country': 'India', 'product_terms': []}]:
            expected = []
            for row in [public_news_row(r) for r in views(ROWS)]:
                evidence = match(context, row)
                if evidence['reasons']:
                    expected.append({'article': public_news_row(row), 'match': evidence})
            response = self.send(json.dumps(context))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {'items': expected[:100]})

    def test_exact_finder_identity_valid_and_invalid(self):
        self.assertEqual(self.send(json.dumps({'project': 'geo', 'article_key': KEY}), path='/api/finder-context').status_code, 200)
        self.reader.reset_mock()
        for value in [{'project': 'geo'}, {'project': 'geo', 'article_key': 'missing'}, {'project': 'geo', 'article_key': KEY.upper()}, {'project': 'geo', 'article_key': KEY, 'extra': 1}, {'project': [], 'article_key': KEY}]:
            self.refused(json.dumps(value), path='/api/finder-context')

    def test_duplicates_nonfinite_unknown_and_utf8_bom(self):
        for raw in [b'{"code":"1","code":"1"}', b'{"product_terms":[{"x":1,"x":1}]}', b'{"x":NaN}', b'{"country":Infinity}', b'{"x":1}', b'[]', b'null', b'{"country":"\xff"}', b'\xef\xbb\xbf{}', b'{']:
            self.refused(raw)

    def test_bounded_fields_controls_multiline_and_nbsp(self):
        valid = {'code': '001', 'system': 'SAC', 'edition': '', 'country': 'United Arab Emirates', 'product_terms': ['steel\nproducts\t\r\u00a0', 'x' * 200]}
        self.assertEqual(self.send(json.dumps(valid)).status_code, 200)
        self.reader.reset_mock()
        for value in [{'code': '１'}, {'code': '1' * 13}, {'code': 1}, {'system': 'x' * 33}, {'country': 'x' * 101}, {'edition': 'x' * 33}, {'product_terms': ['x' * 201]}, {'product_terms': ['x'] * 21}, {'product_terms': 'x'}, {'product_terms': [None]}, {'country': '\n'}, {'system': '\t'}]:
            self.refused(json.dumps(value))
        for char in ['\x00', '\x0b', '\x7f', '\x85', '\ud800']:
            self.refused(json.dumps({'product_terms': [char]}))

    def test_charset_exact_media_and_parameters(self):
        for media in ['text/json', 'application/problem+json', 'application/json;charset=latin1', 'application/json;charset=utf-8;charset=utf-8', 'application/json;other=x', 'application/json;']:
            self.refused('{}', 415, content_type=media)
        self.assertEqual(self.send('{}', content_type='application/json;charset=UTF-8').status_code, 200)

    def test_query_refusal_before_reader(self):
        self.refused('{}', path='/api/related-news?x=1')

    def test_raw_size_first_deep_and_huge_integer(self):
        for raw in ['[' * 100000 + ']' * 100000, '1' * 100000]:
            with patch('integration.post_json207.json.loads', side_effect=AssertionError('parsed')):
                response = self.send(raw)
                self.assertEqual(response.status_code, 413)
                self.reader.assert_not_called()
        for raw in ['[' * 1500 + ']' * 1500, '1' * 5000]:
            with patch.object(self.app.logger, 'error') as log_error:
                self.refused(raw)
                log_error.assert_not_called()

    def test_environ_content_length_hygiene(self):
        for length in ['+2', '0x2', ' 2', '2 ', '1_0', '2,2', '02', '0', '-2']:
            with self.assertRaises(BodyRefused) as error:
                parse(self.environ(b'{}', length), 'related')
            self.assertEqual(error.exception.status, 400)
        for length in [None, '']:
            with self.assertRaises(BodyRefused) as error:
                parse(self.environ(b'{}', length), 'related')
            self.assertEqual(error.exception.status, 411)
        with self.assertRaises(BodyRefused) as error:
            parse(self.environ(b'{}', '2', extra={'HTTP_TRANSFER_ENCODING': 'chunked'}), 'related')
        self.assertEqual(error.exception.status, 400)

    def test_environ_terminated_extras_short_and_cap(self):
        for terminated in [False, True]:
            with self.assertRaises(BodyRefused) as error:
                parse(self.environ(b'{', '2', terminated), 'related')
            self.assertEqual(error.exception.status, 400)
        # Nonterminated extra bytes cannot be observed through CL-limited stream.
        self.assertEqual(parse(self.environ(b'{}EXTRA', '2'), 'related'), {})
        with self.assertRaises(BodyRefused) as error:
            parse(self.environ(b'{}EXTRA', '2', True), 'related')
        self.assertEqual(error.exception.status, 400)
        with self.assertRaises(BodyRefused) as error:
            parse(self.environ(b'x' * (CAP + 1), '2', True), 'related')
        self.assertEqual(error.exception.status, 413)
        with patch.object(Request, 'stream', new_callable=lambda: property(lambda req: (_ for _ in ()).throw(AssertionError('read')))):
            with self.assertRaises(BodyRefused) as error:
                parse(self.environ(b'{}', str(CAP + 1)), 'related')
            self.assertEqual(error.exception.status, 413)

    def test_auth_then_origin_then_parser_and_reader(self):
        for authorized, origin in [(False, 'http://localhost'), (True, 'https://wrong.example')]:
            app = create_app(reader=self.reader, authorize=lambda req: authorized)
            with patch('integration.post_json207.parse', side_effect=AssertionError('parsed')), patch.object(Request, 'stream', new_callable=lambda: property(lambda req: (_ for _ in ()).throw(AssertionError('read')))):
                response = app.test_client().post('/api/related-news', data='x' * (CAP + 1), headers={'Origin': origin}, content_type='application/json')
            self.assertEqual(response.status_code, 403)
            self.reader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
