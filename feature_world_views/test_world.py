# Copyright (c) 2026 Push. All rights reserved.
import unittest
from flask import Flask
from integration.finder_index import FinderIndex
from .model import snapshot
from .routes import create_blueprint

from .fixtures import RAW, INDEX, app

class WorldTests(unittest.TestCase):
    def test_combines_exact_context(self):
        result = snapshot(RAW, INDEX)
        self.assertEqual(result['items'][0]['trade_context'][0]['code'], '090111')
        self.assertFalse(result['tariff_verification'])
        self.assertNotIn('PRIVATE', str(result))

    def test_no_inferred_code(self):
        self.assertEqual(snapshot({'geo': [{'title': 'Coffee', 'url': 'https://example.com/a'}]}, INDEX)['items'][0]['trade_context'], [])

    def test_missing_index_explicit(self):
        self.assertEqual(snapshot(RAW)['trade_state'], 'not_supplied')

    def test_bounds(self):
        for raw in ({'unknown': []}, {'geo': 'rows'}, {'geo': [None]}):
            with self.assertRaises(ValueError): snapshot(raw)

    def test_cap_and_oversized_required_fields(self):
        rows=[dict(RAW['geo'][0], url='https://example.com/'+str(i)) for i in range(101)]
        result=snapshot({'geo':rows})
        self.assertEqual(result['count'],100);self.assertTrue(result['truncated'])
        for key in ('title','url'):
            raw={'geo':[dict(RAW['geo'][0], **{key:'x'*9000}),RAW['geo'][0]]}
            self.assertEqual(snapshot(raw)['count'],1)
            self.assertEqual(app(reader=lambda:raw).get('/workspace/world/data').status_code,200)

    def test_mongo_utc_date_and_url_boundary(self):
        from datetime import datetime, timezone
        raw={'geo':[dict(RAW['geo'][0],created_at=datetime(2026,10,8,tzinfo=timezone.utc))]}
        self.assertEqual(snapshot(raw)['items'][0]['collected_at'],'2026-10-08T00:00:00+00:00')
        for url in ('/relative','https://u:pass@example.com','data:text/plain,x'):
            self.assertEqual(snapshot({'geo':[dict(RAW['geo'][0],url=url)]})['count'],0)

    def test_duplicates(self):
        self.assertEqual(snapshot({'geo': RAW['geo'] * 2})['count'], 1)

    def test_unsafe_url_and_title(self):
        self.assertEqual(snapshot({'geo': [{'url': 'javascript:alert(1)', 'title': 'x'}]})['count'], 0)
        self.assertEqual(snapshot({'geo': [{'url': 'https://example.com', 'title': {'secret': 'x'}}]})['count'], 0)

    def test_denial_no_read(self):
        def fail(): raise AssertionError('Read attempted')
        self.assertEqual(app(fail, lambda r: False).get('/workspace/world/data').status_code, 403)

    def test_auth_exception_fail_closed(self):
        def fail(r): raise RuntimeError('Private error')
        self.assertEqual(app(authorize=fail).get('/workspace/world').status_code, 403)

    def test_errors_redacted(self):
        def fail(): raise RuntimeError('secret uri')
        response = app(fail).get('/workspace/world/data')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'secret', response.data)

    def test_read_only_assets_and_headers(self):
        client = app()
        for path in ('', '/assets/world.js', '/assets/world.css', '/data'):
            response = client.get('/workspace/world' + path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(client.get('/workspace/world/assets/other.js').status_code, 404)
        self.assertEqual(client.post('/workspace/world/data').status_code, 405)
        self.assertEqual(client.get('/workspace/world/data?unknown=x').status_code, 400)

    def test_requires_explicit_seams(self):
        with self.assertRaises(ValueError): create_blueprint(reader=None, authorize=lambda r: True)

if __name__ == '__main__': unittest.main()
