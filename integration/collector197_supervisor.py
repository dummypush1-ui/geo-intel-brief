"""Hard bounded four-worker fetch supervisor candidate. Explicit calls only.
Trusted fixed code resource containment, not a filesystem-confidential sandbox.
No credentials passed to children, no network or worker launch at import time.
"""
import os, sys, time, json, signal, selectors, subprocess, hashlib, ctypes
from pathlib import Path
from datetime import datetime, timezone
from collector113_prep.feed_composition import original_catalog
from collector110_prep.input_budget import capture

ROOT=Path(__file__).resolve().parents[1]
class SupervisorRefused(ValueError):pass

def _namespace_command(command):
    env=Path(sys.executable).parent.parent
    # PID namespace teardown kills all namespace members, including descendants
    # in nested sessions. Network intentionally stays host-side for pinned TLS.
    return ['/usr/bin/bwrap','--unshare-pid','--die-with-parent','--clearenv',
        '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
        '--tmpfs','/tmp','--ro-bind',str(env),str(env),'--ro-bind',str(ROOT),str(ROOT),
        '--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev',
        '--setenv','LANG','C.UTF-8','--setenv','LC_ALL','C.UTF-8','--setenv','TZ','UTC',
        '--chdir',str(ROOT),'--']+command

def _command():
    return _namespace_command([sys.executable,'-I',str(ROOT/'integration/collector197_feed_child.py')])

def _pins():
    rows=json.loads((ROOT/'integration/collector197_worker_pins.json').read_text())
    for p,h in rows.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:
            raise SupervisorRefused('Worker installation drift')

def _subreaper():
    # This supervisor must run in its dedicated coordinator process, not the
    # WSGI process. Orphans stay in feed groups and are explicitly reaped.
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0:
        raise SupervisorRefused('Linux child subreaper required')

def collect_catalog(*, deadline, per_feed_seconds, max_items=50, lookback_hours=24, request_timeout=20, clock=None):
    _pins()
    _subreaper()
    start=time.monotonic()
    if type(deadline)not in (int,float) or not start<deadline<=start+90 or type(per_feed_seconds)is not int or per_feed_seconds!=25:
        raise SupervisorRefused('Fixed wall budgets required')
    if type(max_items)is not int or not 1<=max_items<=200 or type(lookback_hours)is not int or not 1<=lookback_hours<=168:
        raise SupervisorRefused('Fixed selection limits required')
    observed=clock or datetime.now(timezone.utc)
    if type(observed)is not datetime or type(observed.tzinfo)is not timezone:
        raise SupervisorRefused('Exact observed clock required')
    # Reserve 20s for checkpoint/prepare/write. Worker cutoff never extends the
    # whole-cycle deadline and is not a guarantee every source can finish.
    end=min(deadline-20,start+70)
    feeds=original_catalog();states=['unstarted']*len(feeds);pending=list(range(len(feeds)))
    active={};all_processes=[];sel=selectors.DefaultSelector();candidates=[];wire=decoded=0;reserved=0
    def cleanup(p):
        # Kill this PID namespace supervisor; kernel destroys all members.
        if p.poll() is None:
            p.kill()
        p.wait()
        for f in (p.stdin,p.stdout,p.stderr):
            if f and not f.closed:
                try:sel.unregister(f)
                except KeyError:pass
                f.close()
    try:
        while (pending or active) and time.monotonic()<end:
            while pending and len(active)<4 and reserved+1048576<=26*1048576:
                i=pending.pop(0);remaining=min(per_feed_seconds,end-time.monotonic())
                if remaining<=0:break
                p=subprocess.Popen(_command(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    cwd=str(ROOT),env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},start_new_session=False)
                all_processes.append(p);reserved+=1048576
                raw=json.dumps({'index':i,'timeout':remaining,'max_items':max_items,
                    'lookback_hours':lookback_hours,'request_timeout':request_timeout,'observed_at':observed.isoformat()}).encode()
                # Tiny bounded input to child; nonblocking like output to avoid
                # an uninterruptible pipe write if fixed worker installation breaks.
                for f in (p.stdin,p.stdout,p.stderr):os.set_blocking(f.fileno(),False)
                active[p.pid]={'p':p,'i':i,'until':time.monotonic()+remaining,'out':bytearray(),'err':bytearray(),'raw':raw,'sent':0,'open':2,'wire':0,'result':None,'protocol_bad':False}
                for f,k in ((p.stdin,'in'),(p.stdout,'out'),(p.stderr,'err')):sel.register(f,selectors.EVENT_WRITE if k=='in'else selectors.EVENT_READ,(p.pid,k))
                states[i]='running'
            for key,_ in sel.select(.05):
                pid,k=key.data
                if pid not in active:continue
                row=active[pid];f=key.fileobj
                if k=='in':
                    try:n=os.write(f.fileno(),row['raw'][row['sent']:])
                    except BrokenPipeError:n=0;row['sent']=len(row['raw'])
                    row['sent']+=n
                    if row['sent']>=len(row['raw']):sel.unregister(f);f.close()
                else:
                    chunk=os.read(f.fileno(),65536)
                    if not chunk:sel.unregister(f);row['open']-=1
                    else:
                        row[k].extend(chunk)
                        if k=='out':
                            while b'\n' in row['out']:
                                line,_,rest=row['out'].partition(b'\n');row['out']=bytearray(rest)
                                try:
                                    event=json.loads(line)
                                    if type(event)is not dict:raise ValueError()
                                    if set(event)=={'type','bytes'} and event['type']=='wire':
                                        n=event['bytes']
                                        if type(n)is not int or not 1<=n<=65536 or row['result']is not None:raise ValueError()
                                        row['wire']+=n;wire+=n
                                        if row['wire']>1048576 or wire>26*1048576:raise ValueError()
                                    elif set(event)=={'type','envelope'} and event['type']=='result' and row['result']is None:
                                        row['result']=event['envelope']
                                    else:raise ValueError()
                                except Exception:row['protocol_bad']=True

            for pid,row in list(active.items()):
                p=row['p'];i=row['i'];now=time.monotonic()
                if now>=row['until'] or row['protocol_bad'] or len(row['out'])+len(row['err'])>1048576:
                    states[i]='refused_envelope' if row['protocol_bad'] else 'refused_timeout_or_budget';cleanup(p);del active[pid];continue
                if p.poll()is None or row['open']:continue
                try:
                    if p.returncode!=0 or row['err']:raise ValueError()
                    if row['out']:raise ValueError()
                    v=row['result']
                    if type(v)is not dict or set(v)!={'index','state','wire_bytes','decoded_bytes','candidates'}or v['index']!=i or v['state']not in ('selected','parsed_bozo_unverified'):raise ValueError()
                    if any(type(v[k])is not int or not 1<=v[k]<=1048576 for k in ('wire_bytes','decoded_bytes')):raise ValueError()
                    if v['wire_bytes']!=row['wire']:raise ValueError()
                    decoded+=v['decoded_bytes']
                    if wire>26*1048576 or decoded>26*1048576:raise SupervisorRefused('Aggregate network budget')
                    rows=v['candidates']
                    if type(rows)is not list or len(rows)>max_items:raise ValueError()
                    for r in rows:
                        if type(r)is not dict or set(r)!={'title','url','source','summary','published','credibility'} or r['source']!=feeds[i][0] or r['credibility']!=feeds[i][2]:raise ValueError()
                        r['published']=datetime.fromisoformat(r['published'])
                    captured=capture({'candidates':candidates+rows})['captured']['candidates']
                    if len(captured)>1000 or time.monotonic()>=end:raise ValueError()
                    candidates=captured;states[i]=v['state']
                except SupervisorRefused:raise
                except Exception:states[i]='refused_envelope'
                cleanup(p);del active[pid]
        for row in active.values():states[row['i']]='refused_global_cutoff'
        return {'candidates':candidates,'source_states':[{'index':i,'state':s}for i,s in enumerate(states)],
                'wire_bytes':wire,'decoded_bytes':decoded,'all_sources_healthy':False}
    except Exception:
        raise SupervisorRefused('Supervised cycle refused')from None
    finally:
        for p in all_processes:cleanup(p)
        sel.close()
