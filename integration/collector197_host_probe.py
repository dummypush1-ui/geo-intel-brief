"""Default-OFF read-only host diagnostic. Not runtime evidence or authority.
No provider, client, secrets returned, writes, activation or automatic polling.
Fixed subprocess isolation probes only. Actual results may be unavailable.
"""
import os,json,hmac,platform,subprocess,signal
from pathlib import Path
from flask import Flask,request,jsonify

class ProbeRefused(ValueError):pass

def _integer_file(path):
    value=Path(path).read_text().strip()
    if value=='max':return None
    n=int(value)
    if n<0:raise ValueError()
    return n

def memory_available():
    """Cgroup allowance minus current use, bounded by host MemAvailable.
    This is a point-in-time observation, not reserved capacity or free quota.
    """
    try:
        mem={}
        for line in Path('/proc/meminfo').read_text().splitlines():
            k,_,v=line.partition(':')
            if k=='MemAvailable':mem[k]=int(v.split()[0])*1024
        host=mem['MemAvailable']
        try:
            maximum=_integer_file('/sys/fs/cgroup/memory.max')
            current=_integer_file('/sys/fs/cgroup/memory.current')
        except (OSError,ValueError):
            maximum=_integer_file('/sys/fs/cgroup/memory/memory.limit_in_bytes')
            current=_integer_file('/sys/fs/cgroup/memory/memory.usage_in_bytes')
        if current is None:raise ValueError()
        return {'available_memory_bytes':host if maximum is None else min(host,max(0,maximum-current)),
                'cgroup_limit_bytes':maximum,'cgroup_current_bytes':current,'state':'observed_not_reserved'}
    except Exception:return {'available_memory_bytes':None,'cgroup_limit_bytes':None,'cgroup_current_bytes':None,'state':'unavailable'}

def _isolation_command(nested=False):
    base=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--clearenv',
          '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
          '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--']
    return base+(base+['/usr/bin/true'] if nested else ['/usr/bin/true'])

def isolation_probe(nested=False):
    p=None
    try:
        p=subprocess.Popen(_isolation_command(nested),stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={},start_new_session=True)
        return p.wait(timeout=3)==0
    except Exception:return False
    finally:
        if p is not None:
            if p.poll()is None:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            p.wait()

def worker_timeout():
    """Only an actual gunicorn Worker object supplies a config observation.
    No environment or guessed command-line default can establish this value.
    Importing no gunicorn code here; inspect the current worker-owned objects.
    """
    try:
        import gc
        values=[]
        for obj in gc.get_objects():
            t=type(obj)
            if t.__module__.startswith('gunicorn.workers.') and hasattr(obj,'cfg'):
                cfg=obj.cfg
                n=cfg.timeout;workers=cfg.workers
                if type(n)is int and n>=0 and type(workers)is int and workers>0:values.append((n,workers))
        if len(set(values))!=1:return {'timeout_seconds':None,'workers':None,'state':'unavailable'}
        n,workers=values[0]
        return {'timeout_seconds':n,'workers':workers,'state':'observed_gunicorn_worker_config'}
    except Exception:return {'timeout_seconds':None,'workers':None,'state':'unavailable'}

def host_facts():
    exists=Path('/usr/bin/bwrap').is_file() and os.access('/usr/bin/bwrap',os.X_OK)
    return {'memory':memory_available(),'bwrap_present':bool(exists),
            'pid_namespace_works':isolation_probe() if exists else False,
            'nested_bwrap_works':isolation_probe(True) if exists else False,
            'kernel_release':platform.release()[:200],'wsgi':worker_timeout(),
            'activation_authority':False,'runtime_evidence_provider':False}

def create_host_probe(values,probe=host_facts):
    if type(values)is not dict or any(type(k)is not str or type(v)is not str for k,v in values.items()):raise ProbeRefused('Exact environment strings required')
    flag=values.get('COLLECTOR_HOST_PROBE_ENABLED','false')
    if flag not in ('false','true'):raise ProbeRefused('Exact host probe switch required')
    app=Flask(__name__,static_folder=None);app.logger.disabled=True
    secret=values.get('COLLECTOR_HOST_PROBE_SECRET','')
    if flag=='true' and (not 48<=len(secret)<=256 or any(ord(c)<33 or ord(c)>126 for c in secret)):raise ProbeRefused('Dedicated owner probe secret required')
    @app.get('/api/collector-host-probe')
    def diagnostic():
        if flag=='false':return jsonify(error='probe_disabled'),503
        supplied=request.headers.get('Authorization','')
        if len(supplied)>300 or not hmac.compare_digest(supplied.encode(),('Bearer '+secret).encode()):return jsonify(error='unauthorized'),401
        if request.headers.get('Origin') is not None or request.query_string:return jsonify(error='invalid_request'),400
        # One-at-a-time, best-effort process-local gate; no repeated monitoring.
        if not lock.acquire(blocking=False):return jsonify(error='probe_busy'),429
        try:
            facts=probe()
            facts=validate_facts(facts)
            return jsonify(facts),200
        except Exception:return jsonify(error='probe_unavailable'),503
        finally:lock.release()
    from threading import Lock
    lock=Lock()
    @app.after_request
    def safe(response):
        response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
        return response
    return app


def validate_facts(facts):
    # Closed response schema prevents an injected collaborator from turning
    # diagnostics into credential/environment disclosure.
    if type(facts)is not dict or set(facts)!={'memory','bwrap_present','pid_namespace_works','nested_bwrap_works','kernel_release','wsgi','activation_authority','runtime_evidence_provider'}:raise ProbeRefused('Closed host facts required')
    if any(type(facts[k])is not bool for k in ('bwrap_present','pid_namespace_works','nested_bwrap_works')) or facts['activation_authority']is not False or facts['runtime_evidence_provider']is not False:raise ProbeRefused('No authority in host facts')
    kernel=facts['kernel_release']
    if type(kernel)is not str or not 1<=len(kernel)<=200 or any(ord(c)<33 or ord(c)>126 for c in kernel):raise ProbeRefused('Bounded kernel facts')
    memory=facts['memory'];wsgi=facts['wsgi']
    if type(memory)is not dict or set(memory)!={'available_memory_bytes','cgroup_limit_bytes','cgroup_current_bytes','state'} or memory['state']not in ('observed_not_reserved','unavailable'):raise ProbeRefused('Closed memory facts')
    for k in ('available_memory_bytes','cgroup_limit_bytes','cgroup_current_bytes'):
        n=memory[k]
        if n is not None and (type(n)is not int or not 0<=n<=2**63-1):raise ProbeRefused('Bounded memory counts')
    if type(wsgi)is not dict or set(wsgi)!={'timeout_seconds','workers','state'} or wsgi['state']not in ('unavailable','observed_gunicorn_worker_config'):raise ProbeRefused('Closed WSGI facts')
    for k in ('timeout_seconds','workers'):
        n=wsgi[k]
        if n is not None and (type(n)is not int or not 0<=n<=100000):raise ProbeRefused('Bounded WSGI counts')
    return facts
