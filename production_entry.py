"""Single production entry point (factory). Additive; nothing imports or mounts it yet.

Use as `gunicorn production_entry:create_app()`. No app is built at import time.
It delegates unchanged to the reviewed public read-only builder and records which
merge components are wired, so one place shows the composition. Collector, mail and
scraper are NOT wired here: asking for them fails closed instead of silently
running a partial path. Enabling any of them is a separate, explicitly approved step.
"""
import os

COMPONENTS = {
    'geo_news_read': {'wired': True, 'via': 'integration.public_live_builder.guarded_public_app', 'gate': 'PUBLIC_NEWS_READ_ENABLED'},
    'finder_offline': {'wired': True, 'via': 'public_live107 (offline finder frame)', 'gate': None},
    'brics_streams': {'wired': False, 'via': 'integration.brics_streams (private preview only)', 'gate': None},
    'collector': {'wired': False, 'via': 'collector.select_installed_source (inactive)', 'gate': 'COLLECTION_ENABLED'},
    'mail': {'wired': False, 'via': 'Apps Script bridge (inactive)', 'gate': 'MERGED_MAIL_ENABLED'},
    'scraper': {'wired': False, 'via': 'none', 'gate': 'SCRAPER_ENABLED'},
}
_UNWIRED_SWITCHES = ('COLLECTION_ENABLED', 'MERGED_MAIL_ENABLED', 'SCRAPER_ENABLED')


def build_production_app(environ, public_builder=None):
    if type(environ) is not dict or any(type(k) is not str or type(v) is not str for k, v in environ.items()):
        raise ValueError('Plain environment strings required')
    bad = [k for k in _UNWIRED_SWITCHES if environ.get(k, 'false') != 'false']
    if bad:
        raise ValueError('Component not wired in production entry: ' + ', '.join(bad))
    if public_builder is None:
        from integration.public_live_builder import guarded_public_app as public_builder
    app = public_builder(environ)
    comps = {k: dict(v) for k, v in COMPONENTS.items()}
    for v in comps.values():
        # 'wired' = code path exists in this entry; gate_state = actual env switch (default 'false').
        v['gate_state'] = environ.get(v['gate'], 'false') if v['gate'] else None
    app.extensions['production_components'] = comps
    return app


def create_app():
    return build_production_app(dict(os.environ))
