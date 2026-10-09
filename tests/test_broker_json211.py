import io
import json
import unittest
from unittest.mock import patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from integration.broker_json211 import BodyRefused, parse, CAP
from integration.finder198_server import BrokerHandler
from integration.native201_broker import NativeBrokerHandler


class BodyTests(unittest.TestCase):
    def env(self, raw, length='auto', terminated=False, **extra):
        if type(raw) is str:
            raw = raw.encode('utf-8')
        env = EnvironBuilder(path='/api/finder-broker/ships', method='POST', content_type='application/json').get_environ()
        env['wsgi.input'] = io.BytesIO(raw)
        if length == 'auto':
            length = str(len(raw))
        if length is None:
            env.pop('CONTENT_LENGTH', None)
        else:
            env['CONTENT_LENGTH'] = length
        if terminated:
            env['wsgi.input_terminated'] = True
        env.update(extra)
        return Request(env)

    def ships(self, **kw):
        value = {'nonce': 'n' * 24, 'port': 'ALL'}
        value.update(kw)
        return json.dumps(value, ensure_ascii=False).encode('utf-8')

    def ai(self, prompt='hello', **kw):
        value = {'nonce': 'n' * 24, 'provider': 'groq', 'model': 'model-1', 'prompt': prompt}
        value.update(kw)
        return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    def reject(self, raw, status=400, kind='ships', **kw):
        with self.assertRaises(BodyRefused) as caught:
            parse(self.env(raw, **kw), kind)
        self.assertEqual(caught.exception.status, status)
        self.assertNotIn('PRIVATE', str(caught.exception))

    def test_framing_matches_207_vectors_without_import(self):
        for length in ['+2', '0x2', ' 2', '2 ', '1_0', '2,2', '02', '0', '-2', '２', 2]:
            self.reject(b'{}', length=length)
        for length in [None, '']:
            self.reject(b'{}', 411, length=length)
        self.reject(b'{}', length='2', HTTP_TRANSFER_ENCODING='chunked')
        self.reject(self.ships(), QUERY_STRING='x=1')
        for terminated in [False, True]:
            self.reject(b'{', length='2', terminated=terminated)
        raw = self.ships()
        self.assertEqual(parse(self.env(raw + b'EXTRA', length=str(len(raw))), 'ships')['port'], 'ALL')
        self.reject(raw + b'EXTRA', length=str(len(raw)), terminated=True)
        self.reject(b'x' * (CAP + 1), 413, length='2', terminated=True)
        with patch.object(Request, 'stream', property(lambda req: (_ for _ in ()).throw(AssertionError('read')))):
            self.reject(b'{}', 413, length=str(CAP + 1))
            self.reject(b'{}', 413, length='9' * 10000)

    def test_raw_media_not_mimetype(self):
        for media in ['text/json', 'application/problem+json', 'application/json;charset=latin1', 'application/json;charset=utf-8;charset=utf-8', 'application/json;other=x', 'application/json;', 'application/json;charset="utf-8"']:
            self.reject(self.ships(), 415, CONTENT_TYPE=media)
        for media in ['application/json', 'Application/JSON; charset=UTF-8']:
            self.assertEqual(parse(self.env(self.ships(), CONTENT_TYPE=media), 'ships')['port'], 'ALL')

    def test_hostile_json_and_exact_shape(self):
        for raw in [b'[]', b'null', b'{', b'\xef\xbb\xbf{}', b'{"nonce":"\xff"}', b'{"nonce":NaN}', b'{"nonce":Infinity}', b'{"nonce":-Infinity}', b'{"nonce":"PRIVATE","nonce":"PRIVATE"}', b'{"nonce":"PRIVATE","\\u006eonce":"PRIVATE"}', b'1' * 5000, b'[' * 100 + b']' * 100, b'[' * 1500 + b']' * 1500]:
            self.reject(raw)
        for changes in [{'url': 'https://evil.invalid'}, {'nonce': 1}, {'port': None}, {'port': 'x' * 101}, {'port': '\ud800'}, {'port': ''}]:
            # ensure_ascii needed for testing escaped lone surrogates.
            value = {'nonce': 'n' * 24, 'port': 'ALL'}; value.update(changes)
            self.reject(json.dumps(value))
        for prompt in ['', 'x' * 8001, '\x00', '\x0b', '\x7f', '\x85', '\ud800']:
            value = {'nonce': 'n' * 24, 'provider': 'groq', 'model': 'm', 'prompt': prompt}
            self.reject(json.dumps(value), kind='ai')
        for provider in ['nvidia', '', None]:
            self.reject(self.ai(provider=provider), kind='ai')
        for key in ['url', 'headers', 'tools', 'messages']:
            self.reject(self.ai(**{key: 'PRIVATE'}), kind='ai')
        self.assertEqual(parse(self.env(self.ai('\t\n\r\u00a0\U0001f600')), 'ai')['prompt'], '\t\n\r\u00a0\U0001f600')

    def test_raw_cap_vs_codepoints(self):
        self.assertEqual(len(parse(self.env(self.ai('x' * 8000)), 'ai')['prompt']), 8000)
        overhead = len(self.ai(''))
        n = (CAP - overhead) // 3
        raw = self.ai('界' * n)
        self.assertLessEqual(len(raw), CAP)
        self.assertEqual(len(parse(self.env(raw), 'ai')['prompt']), n)
        self.reject(self.ai('界' * (n + 1)), 413, kind='ai')
        escaped = json.dumps({'nonce': 'n'*24, 'provider': 'groq', 'model': 'm', 'prompt': '界'*3000})
        self.reject(escaped, 413, kind='ai')
        # Astral Unicode is one Python code point, four raw UTF-8 bytes.
        self.assertEqual(len(parse(self.env(self.ai('\U0001f600'*100)), 'ai')['prompt']), 100)

    def test_nonce_parity_with_engine_real_vectors(self):
        from integration.finder198_budget import ProxyCallBudget
        class NoIO:
            def _change(self, now, mutate): return 'admitted'
        for nonce in ['n'*19, 'n'*20, 'n'*80, 'n'*81, 'A_z-09'*4, '界'*24, 'n'*23+'/', '', None, 'n'*23+'\n']:
            try:
                ProxyCallBudget.reserve(NoIO(), nonce, 100); engine = True
            except ValueError:
                engine = False
            try:
                parse(self.env(self.ships(nonce=nonce)), 'ships'); shape = True
            except BodyRefused:
                shape = False
            self.assertEqual(shape, engine, repr(nonce))

    def test_model_identifier_parity_not_catalog_admission(self):
        from integration import finder198_connector as engine
        for model in ['a', 'a'*100, 'a'*101, '', 'a/b.c_-09', '界', 'a?b', 'a\n', None]:
            entry = engine.ModelEntry('groq', model, 'owner', 'vendor', 'free', 99, 101)
            with patch.object(engine, 'MODEL_CATALOG', (entry,)):
                try:
                    engine.plan_ai('groq', model, now=100); accepted = True
                except ValueError:
                    accepted = False
            try:
                parse(self.env(self.ai(model=model)), 'ai'); shape = True
            except BodyRefused:
                shape = False
            self.assertEqual(shape, accepted, repr(model))
        # Generic identifier '/' is valid shape; Gemini-specific path admission remains engine-only.
        self.assertEqual(parse(self.env(self.ai(model='a/b', provider='gemini')), 'ai')['model'], 'a/b')
        with self.assertRaises(ValueError): engine.plan_ai('groq', 'invented', now=100)

    def handler(self, cls):
        h = object.__new__(cls); h.budget = object(); h.transport = object(); h.clock = lambda: 100
        return h

    def test_both_handlers_same_errors_before_budget_and_payload_parity(self):
        for cls, module, name in [(BrokerHandler, 'integration.finder198_server', 'proxy_request'), (NativeBrokerHandler, 'integration.native201_broker', 'proxy_request_native')]:
            handler = self.handler(cls)
            with patch(module+'.'+name) as call:
                for raw, status, error in [(b'{"PRIVATE":NaN}', 400, 'invalid_request'), (self.ships(url='PRIVATE'), 400, 'invalid_request'), (b'x'*(CAP+1), 413, 'request_too_large')]:
                    r = handler(self.env(raw), 'e'*64)
                    self.assertEqual((r.status_code, r.json), (status, {'ok': False, 'error': error}))
                    self.assertNotIn('PRIVATE', r.get_data(as_text=True))
                r = handler(self.env(b'{}', length=None), 'e'*64); self.assertEqual(r.status_code, 411)
                r = handler(self.env(b'{}', CONTENT_TYPE='text/plain'), 'e'*64); self.assertEqual(r.status_code, 415)
                call.assert_not_called()
            with patch(module+'.'+name, return_value={'state': 'complete', 'status': 200, 'body': b'{}'}) as call:
                for provider in ['gemini', 'groq', 'mistral']:
                    req = self.env(self.ai('hi\n界', provider=provider), PATH_INFO='/api/finder-broker/ai')
                    self.assertEqual(handler(req, 'e'*64).status_code, 200)
                    payload = json.loads(call.call_args.kwargs['body'])
                    if provider == 'gemini':
                        self.assertEqual(payload, {'contents': [{'role': 'user', 'parts': [{'text': 'hi\n界'}]}], 'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 2048}})
                    else:
                        self.assertEqual(payload, {'model': 'model-1', 'messages': [{'role': 'user', 'content': 'hi\n界'}], 'temperature': 0.2, 'max_tokens': 2048})
            with patch.object(Request, 'stream', property(lambda r: (_ for _ in ()).throw(AssertionError('read')))):
                for extra in [{'REQUEST_METHOD': 'GET'}, {'PATH_INFO': '/api/finder-broker/unknown'}]:
                    self.assertEqual(handler(self.env(b'{', **extra), 'e'*64).status_code, 404)
            with patch(module+'.parse', side_effect=RuntimeError('PRIVATE')):
                self.assertEqual(handler(self.env(self.ships()), 'e'*64).json, {'ok': False, 'error': 'broker_unavailable'})
            for exception in [ValueError, UnicodeError, RecursionError]:
                with patch('integration.broker_json211.json.loads', side_effect=exception('PRIVATE')):
                    self.assertEqual(handler(self.env(self.ships()), 'e'*64).status_code, 400)

    def test_archive199_deliberately_unchanged(self):
        from integration.replay199_broker import ArchiveBrokerHandler
        handler = self.handler(ArchiveBrokerHandler)
        with patch('integration.replay199_broker.proxy_request_archive') as call:
            response = handler(self.env(self.ships(url='PRIVATE')), 'e'*64)
            self.assertEqual((response.status_code, response.json), (409, {'ok': False, 'error': 'broker_request_held'}))
            call.assert_not_called()

    def test_existing_auth_order_both_handlers_no_reads(self):
        from integration.finder198_auth import create_finder_auth
        from integration.accounts.service import AccountService
        from integration.accounts.store import MemoryStore
        from tests.test_finder198a import O, PW, evidence
        from werkzeug.test import Client
        from werkzeug.wrappers import Response
        for cls in [BrokerHandler, NativeBrokerHandler]:
            store = MemoryStore(); service = AccountService(store, b'x'*48, lambda: 101, signup_mode='closed', allowed_origins=[O])
            store.create_account('alice', {'uid': 'alice', 'password': service.hasher.hash(PW), 'created': 100, 'pwv': 0}, None, 50)
            app = create_finder_auth(lambda e,s: Response('PUBLIC')(e,s), enabled=True, service=service, origin=O, client_identity=lambda r:'trusted', worker_evidence=evidence, clock=lambda:101, broker_handler=self.handler(cls))
            client = Client(app, Response)
            csrf = client.get('/account/preauth', base_url=O).json['csrf']
            csrf = client.post('/account/login', base_url=O, json={'username':'alice','password':PW,'csrf':csrf}, headers={'Origin':O}).json['csrf']
            for target, headers, status in [(Client(app, Response), {'Origin':O, 'X-CSRF-Token':'bad'}, 401), (client, {'Origin':O, 'X-CSRF-Token':'bad'}, 403), (client, {'Origin':'https://wrong.invalid', 'X-CSRF-Token':csrf}, 403)]:
                with patch.object(Request, 'stream', property(lambda r: (_ for _ in ()).throw(AssertionError('stream')))), patch.object(Request, 'get_data', side_effect=AssertionError('get_data')), patch.object(Request, 'get_json', side_effect=AssertionError('get_json')):
                    response = target.post('/api/finder-broker/ai', base_url=O, data=b'{PRIVATE', content_type='application/json', headers=headers)
                self.assertEqual(response.status_code, status)
            headers = {'Origin':O, 'X-CSRF-Token':csrf}
            with patch.object(Request, 'stream', property(lambda r: (_ for _ in ()).throw(AssertionError('read')))):
                self.assertEqual(client.post('/api/finder-broker/ships?x=1', base_url=O, data=b'{', headers=headers).status_code, 403)
                self.assertEqual(client.put('/api/finder-broker/ships', base_url=O, data=b'{', headers=headers).status_code, 405)
                self.assertEqual(client.get('/api/finder-broker/ships', base_url=O, headers=headers).status_code, 404)
                self.assertEqual(client.post('/api/finder-broker/unknown', base_url=O, data=b'{', headers=headers).status_code, 404)


if __name__ == '__main__': unittest.main()
