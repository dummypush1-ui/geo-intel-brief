"""198a default-OFF narrow account gate. No env/client/provision/UI/AI transport.
Public read/own-key routes pass unchanged. Protected broker remains held503.
Worker evidence is a source-grounded contract, not owner disclosure/write grant.
"""
import json,hashlib,weakref,threading
from dataclasses import dataclass
from werkzeug.wrappers import Request,Response
from integration.accounts.wired_http import validate,_account_app
from integration.accounts.service import AccountService,COOKIE_NAME
from integration.accounts import csrf
class AuthRefused(ValueError):pass

@dataclass(frozen=True)
class SingleWorkerEvidence:
    workers:int
    observed_at:int
    expires_at:int
    host_reference:str
    activation_reference:str
    def validate(self,now):
        if any(type(v)is not int for v in (self.workers,self.observed_at,self.expires_at,now))or self.workers!=1 or not 0<=self.observed_at<=now<self.expires_at<=self.observed_at+120:raise AuthRefused('Observed single worker required')
        for ref in (self.host_reference,self.activation_reference):
            if type(ref)is not str or not 1<=len(ref)<=200 or any(ord(c)<33 or ord(c)>126 for c in ref):raise AuthRefused('Bounded owner host references required')
        return self

def _evidence(provider,clock):
    if not callable(provider)or not callable(clock):raise AuthRefused('Independent worker evidence required')
    record=provider()
    if type(record)is not SingleWorkerEvidence:raise AuthRefused('Exact worker evidence required')
    return record.validate(clock())

_services=weakref.WeakKeyDictionary()
_registry_lock=threading.Lock()
def _register(service):
    # Enforce one registered service/limiter per store in this factory only.
    # Other unselected constructors remain a deployment invariant, not proven.
    with _registry_lock:
        prior=_services.get(service.store)
        if prior is not None and prior()is not None and prior()is not service:raise AuthRefused('One account service per store required')
        _services[service.store]=weakref.ref(service)

ACCOUNT_ROUTES={('/account/preauth','GET'),('/account/login','POST'),('/account/logout','POST'),('/account/whoami','GET')}
def create_finder_auth(public,*,enabled=False,service=None,origin=None,client_identity=None,worker_evidence=None,clock=None,broker_handler=None):
    """Unselected injected WSGI factory. Serving an enabled real store can write.
    OFF uses no collaborators and delegates byte-for-byte to public callable.
    No automatic provider, Mongo service construction or production mounting.
    """
    if type(enabled)is not bool or not callable(public):raise AuthRefused('Exact narrow gate selection required')
    if not enabled:return public
    if broker_handler is not None and not callable(broker_handler):raise AuthRefused('Exact broker handler required')
    _evidence(worker_evidence,clock)
    validate(service,origin,client_identity);_register(service)
    bound_limiter=service.limiter
    account=_account_app(service,origin,client_identity)
    def response(error,status):
        return Response(json.dumps({'ok':False,'error':error}),status=status,mimetype='application/json',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Robots-Tag':'noindex, nofollow'})
    def dispatch(environ,start_response):
        req=Request(environ);path=req.path
        protected=path=='/account' or path.startswith('/account/')or path=='/api/finder-broker'or path.startswith('/api/finder-broker/')
        if not protected:return public(environ,start_response)
        try:
            _evidence(worker_evidence,clock);validate(service,origin,client_identity)
            if service.limiter is not bound_limiter:raise AuthRefused('Bound limiter changed')
        except Exception:return response('auth_runtime_unavailable',503)(environ,start_response)
        raw=environ.get('RAW_URI',environ.get('REQUEST_URI',path)).split('?',1)[0]
        if req.host_url.rstrip('/')!=origin or '%'in raw or '\\'in path or '//'in path or any(x in ('.','..')for x in path.split('/'))or req.query_string:return response('forbidden',403)(environ,start_response)
        if path=='/account'or path.startswith('/account/'):
            if (path,req.method)not in ACCOUNT_ROUTES:return response('not_found',404)(environ,start_response)
            if req.method=='POST'and req.headers.get('Origin')!=origin:return response('forbidden',403)(environ,start_response)
            # whoami returns protocol CSRF only after touch_session checks live UID.
            return account(environ,start_response)
        if req.method not in ('GET','POST'):return response('method_not_allowed',405)(environ,start_response)
        # All broker requests, even GET, need exact origin and session CSRF.
        if req.headers.get('Origin')!=origin:return response('forbidden',403)(environ,start_response)
        try:
            token=req.cookies.get(COOKIE_NAME,'')
            session,session_hash,error=service._authed(token,req.headers.get('X-CSRF-Token'),origin)
            if error:return response('unauthenticated'if error=='unauthenticated'else'forbidden',401 if error=='unauthenticated'else 403)(environ,start_response)
            if type(session)is not dict or type(session.get('uid'))is not str or not 1<=len(session['uid'])<=512:raise AuthRefused('Live UID session required')
            principal_hash=hashlib.sha256(('finder198-principal:'+session['uid']).encode('utf-8')).hexdigest()
        except Exception:return response('account_unavailable',503)(environ,start_response)
        if broker_handler is not None:
            try:return broker_handler(req,principal_hash)(environ,start_response)
            except Exception:return response('broker_unavailable',503)(environ,start_response)
        return response('broker_not_wired',503)(environ,start_response)
    dispatch.route_contract={'accounts':sorted(ACCOUNT_ROUTES),'broker_prefix':'/api/finder-broker/','broker_transport':broker_handler is not None,'public':'unchanged','signup':False,'worker_requirement':1,'ui':False}
    return dispatch
