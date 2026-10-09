"""Single production entry point (factory). Additive; nothing imports or mounts it yet.

Use as `gunicorn production_entry:create_app()`. No app is built at import time.
It delegates unchanged to the reviewed public read-only builder and records which
merge components are wired, so one place shows the composition. Collector dispatch is default OFF and requires real injected runtime evidence.
Mail and scraper are NOT wired here: asking for them fails closed instead of silently
running a partial path. Enabling any of them is a separate, explicitly approved step.
"""
import os

COMPONENTS = {
    'geo_news_read': {'wired': True, 'via': 'integration.public_live_builder.guarded_public_app', 'gate': 'PUBLIC_NEWS_READ_ENABLED'},
    'finder_offline': {'wired': True, 'via': 'public_live107 (offline finder frame)', 'gate': None},
    'brics_streams': {'wired': False, 'via': 'integration.brics_streams (private preview only)', 'gate': None},
    'collector': {'wired': True, 'via': 'integration.collector197_http (default-OFF dispatcher)', 'gate': 'COLLECTION_ENABLED'},
    'mail': {'wired': False, 'via': 'Apps Script bridge (inactive)', 'gate': 'MERGED_MAIL_ENABLED'},
    'scraper': {'wired': False, 'via': 'none', 'gate': 'SCRAPER_ENABLED'},
}
_UNWIRED_SWITCHES = ('MERGED_MAIL_ENABLED', 'SCRAPER_ENABLED')


def build_production_app(environ, public_builder=None, *, runtime_evidence=None, collector_client_factory=None, clock=None):
    if type(environ) is not dict or any(type(k) is not str or type(v) is not str for k, v in environ.items()):
        raise ValueError('Plain environment strings required')
    bad = [k for k in _UNWIRED_SWITCHES if environ.get(k, 'false') != 'false']
    if bad:
        raise ValueError('Component not wired in production entry: ' + ', '.join(bad))
    probe_flag=environ.get('COLLECTOR_HOST_PROBE_ENABLED','false')
    if probe_flag not in ('false','true'):raise ValueError('Exact host probe switch required')
    probe_app=None
    if probe_flag=='true':
        from integration.collector197_host_probe import create_host_probe
        probe_app=create_host_probe(environ)
    flag=environ.get('COLLECTION_ENABLED','false')
    if flag not in ('false','true'):raise ValueError('Exact collection switch required')
    collector=None
    if flag=='true':
        import time
        from integration.collector197_runtime_evidence import evidence_provider
        from integration.collector197_http import build_collector_app
        liveclock=clock or (lambda:int(time.time()))
        record=evidence_provider(runtime_evidence,liveclock)
        collector=build_collector_app(environ,runtime_preflight=lambda:evidence_provider(runtime_evidence,liveclock).validate(liveclock()),client_factory=collector_client_factory,clock=liveclock,durable_coverage=True)
    if public_builder is None:
        from integration.public_live_builder import guarded_public_app as public_builder
    public_env=environ if flag=='false' else {**environ,'COLLECTION_ENABLED':'false'}
    try:app = public_builder(public_env)
    except Exception:
        if collector is not None:collector.extensions['collector_close']()
        raise
    if collector is not None:
        from integration.collector197_dispatcher import CollectorDispatcher
        app.wsgi_app=CollectorDispatcher(app.wsgi_app,collector.wsgi_app)
        app.extensions['collector_close']=collector.extensions['collector_close']
    if probe_app is not None:
        original=app.wsgi_app
        def probe_dispatch(env,start_response):
            if env.get('PATH_INFO')=='/api/collector-host-probe':return probe_app.wsgi_app(env,start_response)
            return original(env,start_response)
        app.wsgi_app=probe_dispatch
    comps = {k: dict(v) for k, v in COMPONENTS.items()}
    for v in comps.values():
        # 'wired' = code path exists in this entry; gate_state = actual env switch (default 'false').
        v['gate_state'] = environ.get(v['gate'], 'false') if v['gate'] else None
    app.extensions['production_components'] = comps
    return app


def create_app():
    return build_production_app(dict(os.environ))
