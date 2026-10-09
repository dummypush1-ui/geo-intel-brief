"""Hard whole-fetch coordinator wrapper candidate; no launch on import.
SIGTERM allows tracked descendant cleanup; failure to exit after cleanup grace
is a hard refusal, never returns candidates or authorizes write.
"""
import os,sys,json,time,signal,selectors,subprocess
from pathlib import Path
from datetime import datetime,timezone
from collector110_prep.input_budget import capture
from integration.collector197_supervisor import _pins
ROOT=Path(__file__).resolve().parents[1]
class CoordinatorRefused(ValueError):pass

def _command():return [sys.executable,'-I',str(ROOT/'integration/collector197_coordinator_child.py')]

def supervised_candidates(*, deadline, per_feed_seconds, max_items=50, lookback_hours=24, request_timeout=20, job_mode=False):
    if type(job_mode)is not bool:raise CoordinatorRefused('Exact job selection required')
    _pins()
    now=time.monotonic()
    if type(deadline)not in (int,float) or not now<deadline<=now+90 or per_feed_seconds!=25:
        raise CoordinatorRefused('Fixed coordinator budgets required')
    end=deadline-15
    raw=json.dumps({'deadline':deadline,'per_feed_seconds':per_feed_seconds,
        'max_items':max_items,'lookback_hours':lookback_hours,'request_timeout':request_timeout,
        'observed_at':datetime.now(timezone.utc).isoformat(),**({'job_mode':True}if job_mode else{})}).encode()
    p=None;sel=selectors.DefaultSelector();sent=0;buffers={}
    try:
        p=subprocess.Popen(_command(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},cwd=str(ROOT),start_new_session=True)
        buffers={p.stdout:bytearray(),p.stderr:bytearray()}
        for f in (p.stdin,p.stdout,p.stderr):os.set_blocking(f.fileno(),False)
        sel.register(p.stdin,selectors.EVENT_WRITE)
        for f in buffers:sel.register(f,selectors.EVENT_READ)
        while sel.get_map():
            if time.monotonic()>=end:raise CoordinatorRefused('Coordinator wall budget')
            for key,_ in sel.select(.05):
                f=key.fileobj
                if f is p.stdin:
                    try:n=os.write(f.fileno(),raw[sent:])
                    except BrokenPipeError:n=0;sent=len(raw)
                    sent+=n
                    if sent>=len(raw):sel.unregister(f);f.close()
                else:
                    chunk=os.read(f.fileno(),65536)
                    if not chunk:sel.unregister(f)
                    else:buffers[f].extend(chunk)
                if sum(len(b)for b in buffers.values())>2097152:raise CoordinatorRefused('Coordinator output budget')
        p.wait(timeout=max(.001,end-time.monotonic()))
        if p.returncode!=0 or buffers[p.stderr]:raise CoordinatorRefused('Coordinator refused')
        out=json.loads(buffers[p.stdout])
        if type(out)is not dict or set(out)!={'candidates','source_states','wire_bytes','decoded_bytes','all_sources_healthy'} or out['all_sources_healthy']is not False:raise ValueError()
        from collector113_prep.feed_composition import original_catalog
        states=out['source_states'];n=len(original_catalog())
        allowed={'unstarted','selected','parsed_bozo_unverified','refused_timeout_or_budget','refused_global_cutoff','refused_envelope'}
        if type(states)is not list or len(states)!=n or any(type(r)is not dict or set(r)!={'index','state'}or type(r['index'])is not int or r['index']!=i or r['state']not in allowed for i,r in enumerate(states)):raise ValueError()
        if any(type(out[k])is not int or not 0<=out[k]<=26*1048576 for k in ('wire_bytes','decoded_bytes')):raise ValueError()
        rows=out['candidates']
        if type(rows)is not list or len(rows)>1000:raise ValueError()
        for row in rows:row['published']=datetime.fromisoformat(row['published'])
        rows=capture({'candidates':rows})['captured']['candidates']
        if time.monotonic()>=end:raise CoordinatorRefused('Coordinator late envelope')
        # Source coverage is retained as metadata, not silently labelled healthy.
        return {'candidates':rows,'source_states':states,'all_sources_healthy':False}
    except Exception:
        raise CoordinatorRefused('Supervised fetch unavailable')from None
    finally:
        if p is not None:
            if p.poll()is None:
                try:os.kill(p.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:os.killpg(p.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    p.wait()
            for f in (p.stdin,p.stdout,p.stderr):
                if not f.closed:f.close()
        sel.close()
