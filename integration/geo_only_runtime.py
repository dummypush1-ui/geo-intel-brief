"""Explicit offline Geo-only read composition. Independently written (c)2026 Push.

No private_router selection, default client, migration, old-store access or
collector effects. A caller injects the client after separate live-read gates.
"""
from integration.preview_access import create_preview_from_env
from integration.finder_network import from_env as finder_network_from_env
from integration.storage_reader import ReadOnlyNewsReader
from integration.finder_index import load_bundled_index
from integration.single_db_plan import label
from pathlib import Path


def compose_geo_only(environ,client_factory=None):
    if type(environ) is not dict or any(type(k) is not str or type(v) is not str for k,v in environ.items()):raise ValueError('Plain environment strings required')
    # Validate private access before loading any client. Finder is local only.
    access=environ.get('PREVIEW_ACCESS_ENABLED','false').lower()=='true'
    opts={}
    if access:
        idx=load_bundled_index(Path(__file__).resolve().parents[1])
        opts={'finder_context_reader':idx.for_article,'finder_base':environ.get('PREVIEW_ORIGIN','').rstrip('/')+'/workspace/finder/index.html','finder_index_verified':True,'finder_network_preview_enabled':finder_network_from_env(environ)}
    app=create_preview_from_env(environ,**opts);clients=[]
    events_enabled=environ.get('NEWS_EVENTS_READ_ENABLED','false')
    events_verified=environ.get('NEWS_EVENTS_MAPPING_VERIFIED','false')
    if events_enabled not in ('true','false') or events_verified not in ('true','false'):raise ValueError('Exact event flags required')
    event_hosts=[]
    if events_enabled=='true':
        from integration.dashboard_snapshots import DashboardSnapshots
        raw_hosts=environ.get('GEO_EVENTS_ALLOWED_HOSTS','')
        if len(raw_hosts)>2048:raise ValueError('Bounded event host list required')
        event_hosts=raw_hosts.split(',')
        if not 1<=len(event_hosts)<=20 or len(set(event_hosts))!=len(event_hosts) or any(not DashboardSnapshots.public_host(h) for h in event_hosts):raise ValueError('Explicit public event hosts required')
        if events_verified!='true' or environ.get('NEWS_READ_ENABLED','false')!='true' or not access:raise ValueError('Separate event review and article reads required')
        if environ.get('GEO_DATABASE','geo_intel')!='geo_intel' or environ.get('GEO_EVENTS_COLLECTION','events')!='events':raise ValueError('Exact Geo events mapping required')
    if environ.get('NEWS_READ_ENABLED','false').lower()=='true':
        if not access or environ.get('NEWS_STORE_MAPPING_VERIFIED','false').lower()!='true':raise ValueError('Private access and Geo store review required')
        database=environ.get('GEO_DATABASE','geo_intel');collection=environ.get('GEO_ARTICLES_COLLECTION','articles')
        if (database,collection)!=('geo_intel','articles') and environ.get('GEO_MAPPING_OVERRIDE_VERIFIED','false').lower()!='true':raise ValueError('Nondefault Geo mapping requires separate review')
        if not label(database) or not label(collection) or collection.casefold() in ('events','oplog','oplog.rs','admin','local') or database.casefold() in ('admin','local','newsbot','events'):raise ValueError('Explicit article mapping required')
        if not environ.get('GEO_MONGODB_URI') or not callable(client_factory):raise ValueError('Explicit URI and injected client factory required')
        try:client=client_factory(environ['GEO_MONGODB_URI'],serverSelectionTimeoutMS=5000,connect=False)
        except Exception:raise ValueError('Read-only client unavailable') from None
        if client is None:raise ValueError('Read-only client unavailable')
        clients.append(client)
        try:
            reader=ReadOnlyNewsReader({'geo':client[database][collection]},verified=True,limit=100,query_timeout_ms=2000)
            from threading import Lock
            read_lock=Lock();failed=[False]
            def guarded_read():
                with read_lock:
                    if failed[0]:raise ValueError('Geo news read unavailable')
                    try:return reader()
                    except Exception:
                        failed[0]=True
                        try:client.close()
                        except Exception:pass
                        raise ValueError('Geo news read unavailable') from None
            if events_enabled=='true':
                from integration.event_reader import ReadOnlyEventsReader
                from integration.dashboard_snapshots import DashboardSnapshots
                from datetime import datetime,timezone
                event_reader=ReadOnlyEventsReader(client[database]['events'],lambda:datetime.now(timezone.utc),verified=True,days=90,limit=1000)
                # Isolate event failure from article latch: a failed events read
                # becomes unavailable in display adapter, never fabricated empty.
                opts['dashboard_snapshot_reader']=DashboardSnapshots({'geo_events':event_reader},verified=True,allowed_hosts={'geo_events':event_hosts})
            app=create_preview_from_env(environ,reader=guarded_read,**opts)
        except Exception:
            try:client.close()
            except Exception:pass
            raise ValueError('Geo article mapping unavailable') from None
    app.extensions['read_only_news_clients']=clients
    app.extensions['stored_news_projects']=('geo',)
    app.extensions['geo_events_read_enabled']=events_enabled=='true'
    return app
