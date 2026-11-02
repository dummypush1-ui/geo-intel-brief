from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from pymongo.errors import BulkWriteError, DuplicateKeyError, OperationFailure

from app import app, create_app

@pytest.fixture
def client():
    return app.test_client()

@pytest.mark.parametrize('path', ['/', '/health', '/hsn/', '/brics/', '/brics/api/articles', '/brics/api/sources', '/brics/api/streams', '/hsn/api/health'])
def test_public_routes(client, path):
    assert client.get(path).status_code == 200

@pytest.mark.parametrize('secret', ['', 'changeme', 'password', 'secret'])
def test_auth_fails_closed(client, monkeypatch, secret):
    monkeypatch.setenv('TRIGGER_SECRET', secret)
    monkeypatch.setenv('ALLOW_INSECURE_LOCAL', 'false')
    assert client.post('/api/trigger/collect').status_code == 503

def test_auth_valid_and_wrong(client, monkeypatch):
    monkeypatch.setenv('TRIGGER_SECRET', 'regression-test-key')
    assert client.get('/api/status').status_code == 401
    assert client.get('/api/status', headers={'X-Trigger-Key': 'regression-test-key'}).status_code == 200

def test_geo_missing_db_is_degraded(client, monkeypatch):
    monkeypatch.setenv('TRIGGER_SECRET', 'regression-test-key')
    assert not app.config['MODULES']['geo']['ok']
    assert client.get('/geo/health').status_code == 503
    assert client.get('/geo/?key=regression-test-key').status_code == 503

@pytest.mark.parametrize('raw', ['2026-11-02T11:30:00+05:30', '2026-11-02T06:00:00Z', '2026-11-02T06:00:00'])
def test_critical_window_timezone(raw):
    from brics.web import _is_within_window
    assert _is_within_window({'collected_at': raw}, datetime(2026, 11, 2, 7), timedelta(hours=24))

@pytest.mark.parametrize('raw', [None, 123, 'bad', '2026-11-03T06:00:00', '2026-10-01T06:00:00'])
def test_invalid_stale_future_dates(raw):
    from brics.web import _is_within_window
    assert not _is_within_window({'collected_at': raw}, datetime(2026, 11, 2, 7, tzinfo=timezone.utc), timedelta(hours=24))

def test_cleanup_preserves_unarchived(monkeypatch):
    from geonews.reports import metadata_cleanup as cleanup
    rows = [{'_id': 1}, {'_id': 2, 'telegram_url': 'https://t.me/c/1/2'},
            {'_id': 3, 'telegram_url': 'https://t.me/c/1/3', 'telegram_message_id': 3}]
    delete = Mock(return_value=1)
    monkeypatch.setattr(cleanup, 'get_articles_older_than', lambda days: rows)
    monkeypatch.setattr(cleanup, 'delete_articles', delete)
    result = cleanup.cleanup()
    delete.assert_called_once_with([3])
    assert result['deleted'] == 1 and result['skipped_unarchived'] == 2

def test_cleanup_no_backup_never_deletes(monkeypatch):
    from geonews.reports import metadata_cleanup as cleanup
    delete = Mock()
    monkeypatch.setattr(cleanup, 'get_articles_older_than', lambda days: [{'_id': 1}])
    monkeypatch.setattr(cleanup, 'delete_articles', delete)
    assert cleanup.cleanup()['deleted'] == 0
    delete.assert_not_called()

def test_bulk_duplicate_count_and_real_errors(monkeypatch):
    from geonews import database as db
    collection = Mock()
    monkeypatch.setattr(db, 'connect', lambda: Mock(articles=collection))
    collection.insert_many.side_effect = BulkWriteError({'nInserted': 1, 'writeErrors': [{'code': 11000}], 'writeConcernErrors': []})
    assert db.save_articles_bulk([{'url':'a'}, {'url':'a'}]) == 1
    collection.insert_many.side_effect = BulkWriteError({'nInserted': 0, 'writeErrors': [{'code': 121}], 'writeConcernErrors': []})
    with pytest.raises(BulkWriteError):
        db.save_articles_bulk([{'url':'b'}])

def test_mongo_does_not_hide_storage_errors():
    from brics.database import MongoStore
    store = MongoStore.__new__(MongoStore)
    store.col = Mock()
    store.col.insert_one.side_effect = DuplicateKeyError('duplicate')
    assert not store.insert({'url': 'https://test'})
    store.col.insert_one.side_effect = OperationFailure('denied')
    with pytest.raises(OperationFailure):
        store.insert({'url': 'https://test'})

def test_sqlite_concurrent_batches(tmp_path):
    from brics.database import SQLiteStore
    store = SQLiteStore(str(tmp_path/'test.sqlite'))
    def write(n):
        rows = [{'url':f'https://test/{n}/{i}', 'title':str(i), 'source':'test'} for i in range(20)]
        assert len(store.insert_many(rows)) == 20
        store.recent()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write, range(20)))
    assert len(store.recent(1000)) == 400
    store.conn.close()

@pytest.mark.parametrize('payload', [[1], {'article_ids':'abcdef'}, {'article_ids':[None]}, {'article_ids':['x']}, {'article_ids':[123]}])
def test_mark_emailed_rejects_bad_payload(client, monkeypatch, payload):
    from geonews import web
    monkeypatch.setenv('TRIGGER_SECRET', 'regression-test-key')
    monkeypatch.setattr(web, '_db_ready', True)
    response = client.post('/geo/mark-emailed?key=regression-test-key', json=payload)
    assert response.status_code == 400

def test_compressed_assets_concurrent_and_negotiated(client):
    from hsn.routes import STATIC, _gz_variant
    path = STATIC/'index.html'
    with ThreadPoolExecutor(max_workers=8) as pool:
        variants = list(pool.map(lambda _: _gz_variant(path), range(16)))
    assert len(set(variants)) == 1
    r = client.get('/hsn/', headers={'Accept-Encoding':'gzip;q=0'})
    assert 'Content-Encoding' not in r.headers
    assert 'Accept-Encoding' in r.vary
    r = client.get('/hsn/', headers={'Accept-Encoding':'gzip'})
    assert r.headers['Content-Encoding'] == 'gzip'
    import gzip
    assert gzip.decompress(r.data) == path.read_bytes()

def test_ais_capacity_keeps_new_ship(monkeypatch):
    from hsn import ais
    monkeypatch.setattr(ais, 'MAX_SHIPS', 2)
    feed = ais.AisFeed('')
    for i in range(3):
        feed.upsert({'MetaData': {'MMSI':str(100000001+i)}, 'MessageType':'PositionReport',
                     'Message': {'PositionReport': {'Latitude':19, 'Longitude':73}}})
    assert len(feed.ships) == 2
    assert '100000003' in feed.ships
    assert '100000001' not in feed.ships

def test_disabled_apps_are_not_collected(client, monkeypatch):
    from core import scheduler
    calls = []
    class ImmediateThread:
        def __init__(self, target, **kwargs): self.target = target
        def start(self): self.target()
    monkeypatch.setattr(scheduler.threading, 'Thread', ImmediateThread)
    monkeypatch.setattr(scheduler, 'brics_tier1', lambda: calls.append('brics'))
    monkeypatch.setattr(scheduler, 'brics_tier2', lambda: calls.append('brics'))
    monkeypatch.setattr(scheduler, 'geo_collect', lambda: calls.append('geo'))
    assert scheduler.collect_all_async(enable_brics=False, enable_geo=False)
    assert calls == [] and not scheduler.is_collecting()
    assert scheduler.collect_all_async(enable_brics=True, enable_geo=False)
    assert calls == ['brics', 'brics']

def test_crosslink_requests_newest(monkeypatch):
    from core import crosslink
    from geonews import database
    recent = Mock(return_value=[])
    monkeypatch.setattr(database, 'recent_articles', recent)
    crosslink._recent_articles()
    recent.assert_called_once_with(limit=400, sort_by='newest')

def test_hsn_crosslink(client):
    result = client.get('/api/links/codes-for-article?text=semiconductors').get_json()
    assert result['ok'] and any(t['code'] == '8542' for t in result['codes'])

def test_cors_preflight_and_vary(client, monkeypatch):
    from hsn import routes
    monkeypatch.setattr(routes, 'ALLOWED_ORIGINS', {'https://example.test'})
    headers = {'Origin': 'https://example.test', 'Access-Control-Request-Method': 'POST',
               'Access-Control-Request-Headers': 'Content-Type,x-app-token'}
    response = client.options('/hsn/api/groq/openai/v1/chat/completions', headers=headers)
    assert response.headers.get('Access-Control-Allow-Headers') == 'Content-Type, x-app-token'
    response = client.get('/hsn/', headers={'Origin':'https://example.test', 'Accept-Encoding':'gzip'})
    assert 'Origin' in response.vary and 'Accept-Encoding' in response.vary

def test_dashboard_links_encode_inputs_and_preserve_filter(monkeypatch):
    from geonews.reports import dashboard
    from html.parser import HTMLParser
    from urllib.parse import parse_qs, urlsplit
    for name, value in {'total_article_count':2, 'latest_collection_time':None,
                        'upcoming_events':[], 'critical_since':[], 'category_counts':[], 'top_countries':[]}.items():
        monkeypatch.setattr(dashboard, name, lambda *args, value=value: value)
    monkeypatch.setattr(dashboard, 'recent_articles', lambda **kwargs: [{'title':'test', 'category':'TRADE'}])
    rendered = dashboard.build_dashboard_html(trigger_key='key&"value', category='TRADE')
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.urls = []
        def handle_starttag(self, tag, attrs):
            if tag == 'a': self.urls.append(dict(attrs).get('href', ''))
    links = Links(); links.feed(rendered)
    export = next(u for u in links.urls if '/geo/export.csv' in u)
    assert parse_qs(urlsplit(export).query)['key'] == ['key&"value']
    assert 'for category TRADE' in rendered
    assert 'for category TRADE' not in dashboard.build_dashboard_html()

@pytest.mark.parametrize('secret', ['', 'changeme', 'password', 'secret'])
def test_dashboard_weak_secret_rejected(client, monkeypatch, secret):
    from brics import config
    monkeypatch.setattr(config, 'DASHBOARD_KEY', '')
    monkeypatch.setattr(config, 'TRIGGER_SECRET', secret)
    response = client.post('/brics/api/streams', json={'key':secret, 'name':'test', 'link':'bad'})
    assert response.status_code == 401

def test_health_all_disabled(monkeypatch):
    for name in ('HSN', 'BRICS', 'GEO'):
        monkeypatch.setenv(f'ENABLE_{name}_APP', 'false')
    other = create_app()
    assert other.test_client().get('/health').status_code == 503

def test_mark_emailed_valid(client, monkeypatch):
    from geonews import web
    from bson import ObjectId
    monkeypatch.setenv('TRIGGER_SECRET', 'regression-test-key')
    monkeypatch.setattr(web, '_db_ready', True)
    sent = Mock()
    monkeypatch.setattr(web, 'mark_sent', sent)
    oid = ObjectId()
    r = client.post('/geo/mark-emailed?key=regression-test-key', json={'article_ids':[str(oid)]})
    assert r.status_code == 200 and r.get_json()['marked'] == 1
    sent.assert_called_once_with([oid])



def test_crosslink_normalizes_feed_dates():
    from core.crosslink import _norm_date
    assert _norm_date({'published': 'Tue, 02 Nov 2026 10:00:00 GMT'}) == '2026-11-02'
    assert _norm_date({'published': 'Tue, 02 Nov 2026 23:30:00 -0500'}) == '2026-11-03'
    assert _norm_date({'published': '2026-11-02T06:00:00+00:00'}) == '2026-11-02'
    assert _norm_date({'published': '', 'collected_at': '2026-11-01T01:02:03'}) == '2026-11-01'
    assert _norm_date({'published': 'not a date', 'collected_at': '2026-11-01T01:02:03'}) == '2026-11-01'
    assert _norm_date({}) == ''


def test_news_for_code_applies_cutoff_to_rss_dated_brics(monkeypatch):
    from core import crosslink
    old = 'Mon, 01 Jan 2024 10:00:00 GMT'
    fresh = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    rows = [{'title': 'Crude oil exports old', 'url': 'https://x.test/old', 'source': 's', 'published': old,
             'collected_at': '2026-11-02T00:00:00'},
            {'title': 'Crude oil exports fresh', 'url': 'https://x.test/new', 'source': 's', 'published': fresh,
             'collected_at': '2026-11-02T00:00:00'}]
    store = Mock()
    store.recent.return_value = rows
    monkeypatch.setattr('brics.database.get_store', lambda: store)
    monkeypatch.setattr('brics.processing.classifier.filter_brics', lambda a: a)
    monkeypatch.setattr('geonews.database.recent_articles', lambda **k: [])
    monkeypatch.setattr(crosslink, '_cache', {'t': 0.0, 'rows': []})
    res = crosslink.news_for_code('2709', days=30)
    assert [i['url'] for i in res['items']] == ['https://x.test/new']
    assert res['items'][0]['date'] == datetime.now(timezone.utc).strftime('%Y-%m-%d')
