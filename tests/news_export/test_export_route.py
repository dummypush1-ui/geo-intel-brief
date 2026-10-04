# Copyright (c) 2026 Push
"""Route tests for A's venv after PATCH_EXPORT.md is applied; skips where news_api is not importable.
  /tmp/phase1-venv/bin/python -m unittest tests.news_export.test_export_route"""
import csv, io, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from integration.news_api import create_app
except Exception:
    create_app = None
ROWS = {'geo': [{'_id': 'private', 'url': 'https://example.com/%d' % i, 'title': t, 'source': 'S, "q"', 'country': 'India', 'category': c, 'created_at': '2026-10-02T00:00:00Z', 'summary': 'a\nb', 'telegram_url': 'https://t.me/x'}
                for i, (t, c) in enumerate([('=bad', 'TRADE'), ('ok', 'RISK')])],
        'brics': [{'id': 'secret', 'url': 'https://example.com/b', 'title': 'B', 'country': 'Brazil'}]}

@unittest.skipIf(create_app is None, 'news_api not importable here')
class ExportRoutes(unittest.TestCase):
    def client(self, rows=ROWS, allow=True, **kw): return create_app(reader=lambda: rows, authorize=lambda r: allow, **kw).test_client()
    def test_403_and_args(self):
        self.assertEqual(self.client(allow=False).get('/api/export.csv').status_code, 403)
        c = self.client()
        for q in ('project=x', 'category=../x', 'foo=1', 'project=geo&project=brics', 'file=x.csv'): self.assertEqual(c.get('/api/export.csv?' + q).status_code, 400, q)
        self.assertEqual(c.post('/api/export.csv',headers={'Origin':'http://localhost'}).status_code, 405)
    def test_snapshot_csv(self):
        r = self.client().get('/api/export.csv?project=geo')
        self.assertEqual(r.status_code, 200); self.assertTrue(r.headers['Content-Type'].startswith('text/csv'))
        self.assertIn('attachment; filename="geo-intel-news-snapshot-geo.csv"', r.headers['Content-Disposition'])
        self.assertEqual(r.headers['X-Export-Scope'], 'loaded_read_view_not_full_database'); self.assertEqual(r.headers['Cache-Control'], 'no-store')
        parsed = list(csv.DictReader(io.StringIO(r.text)))
        self.assertEqual(len(parsed), 2); self.assertTrue(any(p['title'] == "'=bad" for p in parsed))
        for bad in ('private', 'secret', 't.me', '_id'): self.assertNotIn(bad, r.text)
    def test_store_failure_503(self):
        def boom(): raise RuntimeError('db')
        self.assertEqual(create_app(reader=boom, authorize=lambda r: True).test_client().get('/api/export.csv').status_code, 503)
    def test_full_route_unwired_is_503(self):
        self.assertEqual(self.client().get('/api/export-full.csv').status_code, 503)
    def test_full_route_with_fixture_pager(self):
        def pager(project, cursor, limit):
            rows = [{'project': project, 'title': 'T%d' % i, 'article_key': '%s%d' % (project, i)} for i in range(5)]
            s = cursor or 0; ch = rows[s:s + limit]; e = s + len(ch); return ch, (e if e < 5 else None)
        r = self.client(full_export_pager=pager).get('/api/export-full.csv?project=brics')
        self.assertEqual(r.status_code, 200); self.assertEqual(len(list(csv.DictReader(io.StringIO(r.text)))), 5)
        self.assertEqual(r.headers['X-Export-Scope'], 'paged_read_view_capped')

if __name__ == '__main__': unittest.main()

class ExportLifecycle(unittest.TestCase):
    def test_head_and_early_close_release(self):
        def pager(project,cursor,limit):return ([{'project':project,'title':'x','article_key':'k'}],None)
        app=create_app(authorize=lambda r:True,full_export_pager=pager);c=app.test_client()
        r=c.head('/api/export-full.csv?project=geo');self.assertEqual(r.status_code,200);r.close()
        r=c.get('/api/export-full.csv?project=geo',buffered=False);self.assertEqual(r.status_code,200);r.close()
        r=c.get('/api/export-full.csv?project=geo');self.assertEqual(r.status_code,200);r.close()
    def test_snapshot_cut_flag(self):
        rows={'geo':[{'url':'https://example.com/'+str(i),'title':'t'} for i in range(101)]}
        r=create_app(reader=lambda:rows,authorize=lambda r:True).test_client().get('/api/export.csv')
        self.assertEqual(r.headers['X-Export-Truncated'],'true');self.assertEqual(r.headers['X-Export-Input-Limit'],'100 per project')

    def test_category_before_cut(self):
        rows={'geo':[{'url':'https://example.com/'+str(i),'title':'other','category':'RISK'} for i in range(100)]+[{'url':'https://example.com/trade','title':'late trade','category':'TRADE'}]}
        r=create_app(reader=lambda:rows,authorize=lambda r:True).test_client().get('/api/export.csv?project=geo&category=TRADE')
        self.assertEqual(r.status_code,200);self.assertIn('late trade',r.text);self.assertEqual(r.headers['X-Export-Truncated'],'false')
