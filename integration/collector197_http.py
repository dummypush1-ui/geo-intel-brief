"""Explicit default-OFF owner collector factory, unselected by production entry.
No clients/work on import. OFF needs no credentials or adapters. Source approval
is not permission to instantiate this with live clients or enable collection.
"""
import hmac,json,time,atexit
from flask import Flask,request,jsonify
from integration.collector197_config import configure,GATES
from integration.collector197_preflight import inspect_writer
from integration.collector197_orchestrator import run_cycle,CycleRefused
from integration.collector197_coordinator import supervised_candidates
from collector110_prep.durable_checkpoint import DurableCheckpoints
from integration.geo_article_writer import GeoArticleWriter

class HTTPRefused(ValueError):pass

def create_writer_client(uri):
    try:
        from pymongo import MongoClient
        return MongoClient(uri,connect=False,tls=True,tz_aware=True,retryWrites=False,
            serverSelectionTimeoutMS=2000,connectTimeoutMS=2000,socketTimeoutMS=5000,
            timeoutMS=8000,waitQueueTimeoutMS=1000,maxPoolSize=4,minPoolSize=0,
            tlsAllowInvalidCertificates=False,tlsAllowInvalidHostnames=False)
    except Exception:raise HTTPRefused('Dedicated writer client unavailable')from None

class _Database:
    def __init__(self,c):self.c=c
    def __getitem__(self,name):
        if name!='articles':raise ValueError()
        return self.c
class _Client:
    def __init__(self,c):self.c=c
    def __getitem__(self,name):
        if name!='geo_intel':raise ValueError()
        return _Database(self.c)


def build_collector_app(values, *, runtime_preflight=None, client_factory=None, clock=time.time):
    if type(values)is not dict or any(type(k)is not str or type(v)is not str for k,v in values.items()):
        raise HTTPRefused('Exact environment strings required')
    # First validate exact flags independent of proof/client callbacks.
    off=dict(values);off['COLLECTION_ENABLED']='false'
    configure(off,{})
    switch=values.get('COLLECTION_ENABLED','false')
    if switch not in ('false','true'):raise HTTPRefused('Exact collector switch required')
    app=Flask(__name__,static_folder=None);app.config['MAX_CONTENT_LENGTH']=4096
    app.logger.disabled=True
    if switch=='false':
        @app.get('/health')
        def disabled_health():return jsonify(collection=False,ready=False,source_contract='197b'),200
        @app.route('/api/collect',methods=['POST'])
        def disabled():return jsonify(error='collector_disabled'),503
        return app
    from collector130_prep.base_profile import compile_profile
    setting_keys={'MAX_ITEMS_PER_FEED','REQUEST_TIMEOUT','LOOKBACK_HOURS','ACTIVE_CATEGORIES','DEDUPE_THRESHOLD','ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'}
    profile=compile_profile({k:v for k,v in values.items() if k in setting_keys})
    secret=values.get('COLLECTOR_TRIGGER_SECRET','')
    fp=values.get('COLLECTOR_PROFILE_FINGERPRINT','')
    uri=values.get('GEO_WRITER_MONGODB_URI','')
    if (len(secret)<48 or len(secret)>256 or any(ord(c)<33 or ord(c)>126 for c in secret)
            or not callable(runtime_preflight) or type(fp)is not str or len(fp)!=64
            or any(c not in '0123456789abcdef' for c in fp) or not uri or uri in (values.get('GEO_MONGODB_URI'),values.get('MONGODB_URI'))):
        raise HTTPRefused('Complete startup prerequisites required before client access')
    # This callback must independently probe bwrap/kernel, source installation,
    # actual free service capacity and source-grounded activation record.
    # There is no built-in boolean environment shortcut or live-ready default.
    try:
        proof=runtime_preflight()
        if type(proof)is not dict or set(proof)!={'runtime_bwrap','free_capacity','source_catalog','owner_activation'} or any(v is not True for v in proof.values()):raise ValueError()
    except Exception:raise HTTPRefused('Verified runtime preflight unavailable')from None
    client=None
    try:
        client=(client_factory or create_writer_client)(uri)
        handles=inspect_writer(client,fp)
        allproof=dict.fromkeys(GATES,True)
        config=configure(values,allproof)
        ledger=handles['ledger'];cp=DurableCheckpoints(handles['checkpoints'])
        writer=GeoArticleWriter(_Client(handles['articles']),review={'mapping':('geo_intel','articles'),'write_permission':True,'unique_url_index_verified':True,'source_contract_verified':True})
    except Exception:
        if client is not None:
            try:client.close()
            except Exception:pass
        raise HTTPRefused('Writer startup preflight unavailable')from None
    atexit.register(client.close)
    app.extensions['collector_close']=client.close
    @app.before_request
    def boundary():
        if request.path=='/health' and request.method=='GET':return None
        supplied=request.headers.get('Authorization','')
        if len(supplied)>300 or not hmac.compare_digest(supplied.encode(),('Bearer '+secret).encode()):return jsonify(error='unauthorized'),401
        if request.headers.get('Origin') is not None or request.query_string:return jsonify(error='invalid_request'),400
        if request.method=='POST' and request.path=='/api/collect':return None
        if request.method=='GET' and request.path.startswith('/api/collect/status/'):return None
        return jsonify(error='route_unavailable'),404
    @app.get('/health')
    def health():return jsonify(collection=True,ready=True,source_contract='197b_unselected_factory'),200
    @app.post('/api/collect')
    def collect():
        if request.mimetype!='application/json' or request.content_length is None or request.content_length>4096:return jsonify(error='invalid_request'),400
        try:
            def pairs(rows):
                out={}
                for k,v in rows:
                    if k in out:raise ValueError()
                    out[k]=v
                return out
            body=json.loads(request.get_data(),object_pairs_hook=pairs)
            stamp=clock()
            if (type(body)is not dict or set(body)!={'nonce','timestamp'} or type(body['timestamp'])is not int
                    or type(stamp)not in (int,float) or abs(stamp-body['timestamp'])>300):raise ValueError()
        except Exception:return jsonify(error='invalid_request'),400
        coverage={}
        def fetch(**kw):
            out=supervised_candidates(**kw,max_items=profile['max_items'],lookback_hours=profile['lookback_hours'],request_timeout=profile['timeout'])
            coverage.update({'source_states':out['source_states'],'all_sources_healthy':False})
            return out['candidates']
        try:
            out=run_cycle(config,ledger=ledger,checkpoints=cp,nonce=body['nonce'],fetch=fetch,
                categories=profile['active_categories'],
                threshold=profile['threshold'],clock=lambda:int(clock()),writer=writer)
            # Explicit coverage is returned on completed/held successful requests,
            # never inferred from absence of errors or health endpoint.
            return jsonify(**out,**coverage),200
        except Exception:return jsonify(error='collector_held_reconciliation_required'),409
    @app.get('/api/collect/status/<key>')
    def status(key):
        try:return jsonify(ledger.status(key)),200
        except Exception:return jsonify(error='status_unavailable'),503
    @app.errorhandler(413)
    def big(_):return jsonify(error='request_too_large'),413
    return app
