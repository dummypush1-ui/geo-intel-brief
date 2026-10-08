"""Private boundary and loopback checks; synthetic fixtures, network blocked."""
import unittest
from unittest.mock import patch, Mock
from contextlib import ExitStack
from copy import deepcopy
from tests.test_carrier_core import CARRIER, PORTS, ROUTE, EVENT, EVIDENCE, NOW, deny_network


def snapshot():
    return deepcopy({'carriers': [CARRIER], 'locations': PORTS, 'routes': [ROUTE],
                     'events': [EVENT], 'evidence': [EVIDENCE], 'as_of': NOW,
                     'articles': [{'article_key': 'fixture:article', 'title': 'Synthetic Fleet schedule update',
                                   'summary': 'Synthetic context only.'}]})


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for target in ('socket.socket', 'socket.create_connection', 'socket.getaddrinfo'):
            self.stack.enter_context(patch(target, side_effect=deny_network))
        from integration.news_api import create_app
        from feature_carrier_prep.api import mount_private
        from feature_carrier_prep import preview, news_context
        self.preview, self.context = preview, news_context
        self.mount, self.create = mount_private, create_app

    def test_existing_guard_denies_before_reader_all_paths(self):
        reader = Mock(side_effect=AssertionError('Denied reader called'))
        client = self.mount(self.create(), reader).test_client()
        for path in ('/', '/api/carriers', '/api/events', '/assets/carrier.js', '/assets/carrier.css'):
            self.assertEqual(client.get('/carrier-preview'+path).status_code, 403)
        reader.assert_not_called()

    def test_injected_fixture_guard_get_only_no_raw_errors(self):
        client = self.mount(self.create(authorize=lambda req: True), snapshot).test_client()
        for kind in ('carriers', 'routes', 'events', 'sources', 'context'):
            out = client.get('/carrier-preview/api/'+kind)
            self.assertEqual(out.status_code, 200)
            self.assertFalse(out.json['live_tracking'])
            self.assertEqual(out.headers['Cache-Control'], 'no-store')
        self.assertEqual(client.post('/carrier-preview/api/events', headers={'Origin': 'http://localhost'}).status_code, 405)
        for query in ('page=0', 'page=101', 'page=1&page=2', 'page='+'9'*5000, 'url=http://evil.invalid'):
            self.assertEqual(client.get('/carrier-preview/api/events?'+query).status_code, 400)
        self.assertEqual(client.get('/carrier-preview/assets/../api.py').status_code, 404)
        bad = self.mount(self.create(authorize=lambda req: True), lambda: {'secret': 'never display'}).test_client()
        response=bad.get('/carrier-preview/api/events')
        self.assertEqual(response.status_code, 503);self.assertNotIn('secret',response.text)

    def test_context_cap_cannot_break_other_endpoints(self):
        supplied=snapshot()
        supplied['carriers'].append({**CARRIER,'carrier_id':'fixture:second','name':'Other Synthetic Carrier','aliases':['Synthetic context']})
        supplied['articles']=[{'article_key':'fixture:article_'+str(n),'title':'Synthetic Fleet and Synthetic context','summary':''} for n in range(100)]
        client=self.mount(self.create(authorize=lambda req:True),lambda:supplied).test_client()
        for kind in ('carriers','routes','events','sources','context'):
            result=client.get('/carrier-preview/api/'+kind)
            self.assertEqual(result.status_code,200)
            if kind=='context':
                self.assertEqual(len(result.json['items']),100)
                self.assertTrue(result.json['truncated']);self.assertTrue(result.json['context_capped'])
            else:self.assertFalse(result.json['context_capped'])
        supplied['articles']=[{'_id':'private'}]
        self.assertEqual(client.get('/carrier-preview/api/carriers').status_code,200)
        self.assertEqual(client.get('/carrier-preview/api/context').status_code,503)

    def test_blueprint_requires_existing_guard(self):
        from flask import Flask
        with self.assertRaises(ValueError): self.mount(Flask('untrusted'), snapshot)

    def test_serve_rejects_before_binding(self):
        app=Mock()
        for host in ('0.0.0.0', '::', '192.168.1.1', 'localhost'):
            with self.assertRaises(ValueError): self.preview.serve(app, host=host, ssl_context='adhoc')
        app.run.assert_not_called()
        for host in ('127.0.0.1', '::1'):
            self.preview.serve(app, host=host, ssl_context='adhoc')
            self.assertEqual(app.run.call_args.kwargs['host'],host)
            self.assertFalse(app.run.call_args.kwargs['debug'])
        with self.assertRaises(ValueError): self.preview.serve(app,ssl_context=None)

    def test_preview_requires_real_private_access(self):
        for env in ({}, {'PREVIEW_ACCESS_ENABLED':'false'}, {'PREVIEW_ACCESS_ENABLED':'true'}):
            with self.assertRaises(ValueError): self.preview.build(env,snapshot)
        from werkzeug.security import generate_password_hash
        env={'PREVIEW_ACCESS_ENABLED':'true','PREVIEW_ORIGIN':'https://preview.invalid',
             'PREVIEW_PASSWORD_HASH':generate_password_hash('synthetic-test-only'),
             'PREVIEW_SESSION_KEY':'synthetic-key-for-test-not-a-real-secret-'*2}
        client=self.preview.build(env,snapshot).test_client()
        self.assertEqual(client.get('/carrier-preview/',base_url='https://preview.invalid').status_code,403)
        response=client.get('/login',base_url='https://preview.invalid')
        self.assertEqual(response.status_code,200)
        import re; token=re.search(r'name="csrf" value="([^"]+)"',response.text).group(1)
        response=client.post('/login',base_url='https://preview.invalid',headers={'Origin':'https://preview.invalid'},
                             data={'csrf':token,'password':'synthetic-test-only'})
        self.assertEqual(response.status_code,303)
        self.assertEqual(client.get('/carrier-preview/',base_url='https://preview.invalid').status_code,200)
        self.assertEqual(client.get('/carrier-preview/',base_url='https://other.invalid').status_code,403)

    def test_sanitized_news_contract_and_exact_matching(self):
        rows=snapshot()['articles']
        result=self.context.prepare(rows,CARRIER)
        self.assertEqual(len(result['items']),1)
        self.assertTrue(result['not_total_database'])
        for name in ('_id','emailed','mongo_id','TITLE'):
            with self.assertRaises(ValueError):self.context.prepare([{**rows[0],name:'private'}],CARRIER)
        for title in ('synthetic fleet update','PreSynthetic Fleetwood update'):
            self.assertEqual(self.context.prepare([{**rows[0],'title':title}],CARRIER)['items'],[])

if __name__=='__main__': unittest.main()
