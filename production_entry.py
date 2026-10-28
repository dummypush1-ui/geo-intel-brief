"""Single production entry point (factory). No app is built at import time.

Use as `gunicorn production_entry:create_app()`. Finder candidate and comparison
bindings can be injected into the factory by a trusted Python deployment wrapper;
paths, hashes and evidence are never accepted from environment strings. With
MERGED_FINDER_BINDING_PREP_ENABLED, PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED
and the fixed build directory below, the held Finder package built at deploy time
is bound only after every pinned payload file matches.
Collector dispatch is default OFF and requires real injected runtime evidence.
Mail has an injected default-OFF private receipt mount; no builtin provider, DB
creation or sender. Scraper is not wired. Enabling components is a separately
reviewed owner-scoped step.
"""
import os

COMPONENTS = {
    'geo_news_read': {'wired': True, 'via': 'integration.public_live_builder.guarded_public_app', 'gate': 'PUBLIC_NEWS_READ_ENABLED'},
    'finder_offline': {'wired': True, 'via': 'public_live107 (offline finder frame)', 'gate': None},
    'brics_streams': {'wired': False, 'via': 'integration.brics_streams (private preview only)', 'gate': None},
    'collector': {'wired': True, 'via': 'integration.collector197_http (default-OFF dispatcher)', 'gate': 'COLLECTION_ENABLED'},
    'mail': {'wired': True, 'via': 'injected private receipt mount (default OFF, no sender)', 'gate': 'MERGED_MAIL_ENABLED'},
    'scraper': {'wired': False, 'via': 'none', 'gate': 'SCRAPER_ENABLED'},
}
_UNWIRED_SWITCHES = ('SCRAPER_ENABLED',)


_FINDER_BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.finder-candidate')
# Exact sha256 of the 13 payload files of the held Finder package. manifest.json and
# provenance/source-chain.json embed the build commit, so they are checked by F8.
_FINDER_PAYLOAD_SHA256 = {
    'data.aa056ad4e0cf.js': 'aa056ad4e0cf8e0c12ccff4474425c700c27f4b3387484c02c77121c889d40d3',
    'index.html': 'fd839e43e397e50043bf5e365b80d76ca1f582c81f3e69d8332d281d1faf1d73',
    'integration/code_news_index/codes.idx': '4f6487562fd144ef42f75724581fc4d206bf2f0df7b78ce6c66270bffff3fb03',
    'integration/code_news_index/manifest.json': '9dde33202076e4eb08b8589878f5fd26d1d89e2de4edb1bc0b227947458a1aaf',
    'integration/code_news_index/rows.jsonl': '1bf6201069537c58c7dd5ee287d9b3b990b88e3884c10fd3febcd726f2c0f92a',
    'integration/finder_identity_proof.bin': 'bfbea25e82ffaddadae5b8e6175ce27d1872477c96d31e085d1a0056fb6e6fc2',
    'offline.html': '5f21235e1454dc7470c5020d40f22ce3eca083386dfc46eb3fab24161fef490b',
    'review/public-offline.html': '30d8055442b84a9005475ff651a53c9d2981332146fb6299186ae21d3327f78e',
    'src/sanctions.ts': '198ad67256387dd86ba7a7147005cfef0d2ce82c6efb73190eecf7a5e835ba9f',
    'src/tradepartners.ts': '61d36205a98506009752ef42adff11f84f63071962c17c08ff07b2739bca8c39',
    'sw.js': '18f9be15a710ae55fcbfe374861a856ac69c1dd8067d7ab151154bc5f22da17a',
    'upstream/src/sanctions.ts': '03d33e43c46dc79235c18be1d3c750c04eeffc70e34460ba048040b395fb702e',
    'upstream/src/tradepartners.ts': '1a2c819224371e783bdfe70b8c9b247f7410415db2b74e60fcd73ceb58611334',
}


def _load_finder_binding(environ):
    import hashlib
    from integration import finder_binding_f8 as f8
    archive = os.path.join(_FINDER_BUILD_DIR, 'finder-candidate.zip')
    root = os.path.join(_FINDER_BUILD_DIR, 'root')
    try:
        for name, pin in _FINDER_PAYLOAD_SHA256.items():
            digest = hashlib.sha256()
            with open(os.path.join(root, name), 'rb') as stream:
                for chunk in iter(lambda: stream.read(65536), b''):
                    digest.update(chunk)
            if digest.hexdigest() != pin:
                raise f8.Held('Finder payload hash mismatch')
        digest = hashlib.sha256()
        with open(archive, 'rb') as stream:
            for chunk in iter(lambda: stream.read(65536), b''):
                digest.update(chunk)
    except OSError as exc:
        raise f8.Held('Finder candidate package not present') from exc
    binding = f8.prepare(environ, archive=archive, expected_sha256=digest.hexdigest(), root=root)
    if binding is None:
        raise f8.Held('Finder composition requires MERGED_FINDER_BINDING_PREP_ENABLED=true')
    return binding


def build_production_app(environ, public_builder=None, *, runtime_evidence=None, collector_client_factory=None, clock=None, mail_binding_provider=None, coverage_binding_provider=None, finder_candidate_binding=None, finder_comparison_baseline=None):
    if type(environ) is not dict or any(type(k) is not str or type(v) is not str for k, v in environ.items()):
        raise ValueError('Plain environment strings required')
    bad = [k for k in _UNWIRED_SWITCHES if environ.get(k, 'false') != 'false']
    if bad:
        raise ValueError('Component not wired in production entry: ' + ', '.join(bad))
    if finder_candidate_binding is None and environ.get('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED', 'false') == 'true':
        finder_candidate_binding = _load_finder_binding(environ)
    probe_flag=environ.get('COLLECTOR_HOST_PROBE_ENABLED','false')
    if probe_flag not in ('false','true'):raise ValueError('Exact host probe switch required')
    probe_app=None
    if probe_flag=='true':
        from integration.collector197_host_probe import create_host_probe
        probe_app=create_host_probe(environ)
    flag=environ.get('COLLECTION_ENABLED','false')
    if flag not in ('false','true'):raise ValueError('Exact collection switch required')
    # Do not import the Flask collector stack merely to reject an incomplete
    # activation request.  This keeps the production entry fail-closed in a
    # minimal runtime and makes the required evidence explicit at its boundary.
    if flag == 'true' and runtime_evidence is None:
        from integration.collector197_runtime_evidence import EvidenceRefused
        raise EvidenceRefused('Verified runtime evidence required before enabling collection')
    mail_flag=environ.get('MERGED_MAIL_ENABLED','false')
    if mail_flag not in ('false','true'):raise ValueError('Exact merged mail switch required')
    mail_binding=None
    if mail_flag=='true':
        if environ.get('MAIL_V1_ENABLED','false')!='true':raise ValueError('Exact private mail gate required')
        import time
        from integration.mail_mount_binding import resolve_binding
        live_mail_clock=clock or (lambda:int(time.time()))
        mail_binding=resolve_binding(mail_binding_provider,live_mail_clock)
    collector=None
    try:
        if flag=='true':
            import time
            from integration.collector197_runtime_evidence import evidence_provider
            from integration.collector197_http import build_collector_app
            liveclock=clock or (lambda:int(time.time()))
            record=evidence_provider(runtime_evidence,liveclock)
            collector=build_collector_app(environ,runtime_preflight=lambda:evidence_provider(runtime_evidence,liveclock).validate(liveclock()),client_factory=collector_client_factory,clock=liveclock,durable_coverage=True)
    except Exception:
        if mail_binding is not None:mail_binding.close()
        raise
    if public_builder is None:
        from integration.public_live_builder import guarded_public_app, build_public_live_preview
        def public_builder(public_environ, **builder_bindings):
            if not builder_bindings:
                return guarded_public_app(public_environ)
            return guarded_public_app(
                public_environ,
                build=lambda selected_environ: build_public_live_preview(selected_environ, **builder_bindings),
            )
    public_env=environ if flag=='false' and mail_flag=='false' else {**environ,'COLLECTION_ENABLED':'false','MERGED_MAIL_ENABLED':'false','MAIL_V1_ENABLED':'false'}
    if 'PUBLIC_NEWS_FULL_PAGES_ENABLED' not in public_env:
        public_env={**public_env,'PUBLIC_NEWS_FULL_PAGES_ENABLED':'true' if public_env.get('PUBLIC_NEWS_READ_ENABLED')=='true' else 'false'}
    if 'PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED' not in public_env:
        public_env={**public_env,'PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED':'true' if public_env.get('PUBLIC_NEWS_FULL_PAGES_ENABLED')=='true' else 'false'}
    builder_bindings={}
    if coverage_binding_provider is not None:builder_bindings['coverage_binding_provider']=coverage_binding_provider
    if finder_candidate_binding is not None:builder_bindings['finder_candidate_binding']=finder_candidate_binding
    if finder_comparison_baseline is not None:builder_bindings['finder_comparison_baseline']=finder_comparison_baseline
    app=None
    try:
        app = public_builder(public_env,**builder_bindings) if builder_bindings else public_builder(public_env)
        if public_env.get('PUBLIC_NEWS_FULL_PAGES_ENABLED')=='true':
            from integration.public_news_keyset import install as install_public_news_keyset
            install_public_news_keyset(app,public_env.get('GEO_MONGODB_URI',''))
    except Exception:
        if app is not None:
            cleanup=app.extensions.get('coverage_close')
            if callable(cleanup):
                cleanup()
            else:
                for client in app.extensions.get('read_only_news_clients',[]):
                    try:client.close()
                    except Exception:pass
        if collector is not None:collector.extensions['collector_close']()
        if mail_binding is not None:mail_binding.close()
        raise
    if collector is not None:
        from integration.collector197_dispatcher import CollectorDispatcher
        app.wsgi_app=CollectorDispatcher(app.wsgi_app,collector.wsgi_app)
        app.extensions['collector_close']=collector.extensions['collector_close']
    if mail_binding is not None:
        try:
            from flask import Flask
            from feature_mail_mount.composition import compose_private_mail
            from integration.mail_mount_binding import MailDispatcher
            private=Flask('production_private_mail',static_folder=None)
            private.logger.disabled=True
            compose_private_mail(private,enabled=True,store=mail_binding.store,secret=mail_binding.secret,clock=mail_binding.clock)
            app.wsgi_app=MailDispatcher(app.wsgi_app,private.wsgi_app,mail_binding,live_mail_clock,mail_binding_provider)
            app.extensions['mail_close']=mail_binding.close
            app.extensions['mail_receipt_mode']='private_receipt_bridge_no_send'
        except Exception:
            mail_binding.close()
            if collector is not None:collector.extensions['collector_close']()
            raise
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


def create_app(**bindings):
    return build_production_app(dict(os.environ), **bindings)
