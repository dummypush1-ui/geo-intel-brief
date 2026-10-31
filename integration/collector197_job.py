"""Default-OFF one-shot job composition. No HTTP, schedule or automatic recovery.
Injected evidence is mandatory and does not itself grant owner write authority.
No builtin production provider; owner-operated containment/binding is separate.
"""
import time,json,sys,resource
from integration.collector197_job_runtime import (JobRefused,require_job_provider,
    read_job_facts,PARENT_BYTES)
from integration.collector197_config import configure,GATES
from integration.collector197_http import create_writer_client,_Client
from integration.collector197_preflight import inspect_writer
from integration.collector197_coverage import CoverageCheckpoints
from integration.collector197_orchestrator import run_cycle
from integration.collector197_coordinator import supervised_candidates
from integration.geo_article_writer import GeoArticleWriter

_FT_CHILD = r"""
import sys,os,json,resource
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
sys.path.insert(0,%r)
assert set(os.environ)<={'LANG','LC_ALL','TZ','PWD'}
raw=sys.stdin.buffer.read(2200);assert len(raw)<=2100
v=json.loads(raw);assert type(v)is dict and set(v)=={'url','timeout','max_chars'}
url,timeout,mx=v['url'],v['timeout'],v['max_chars']
assert type(url)is str and url.startswith('https://') and type(timeout)in(int,float)and 0<timeout<=15 and type(mx)is int and 1<=mx<=9997
import base64,html.parser
from integration.collector197_connector import fetch_one
from integration.html_text209 import strip_html_once
got=fetch_one((('article',url,'LOW'),),url,timeout=timeout,account=lambda n:None)
body=base64.b64decode(got['body_b64'],validate=True)
try:text=body.decode('utf-8')
except UnicodeDecodeError:text=body.decode('utf-8','replace')
SKIP={'script','style','nav','footer','header','aside','form','noscript','template','svg','iframe','button','select'}
class P(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True);s.skip=0;s.inp=0;s.cur=[];s.out=[];s.size=0
    def handle_starttag(s,t,a):
        if t in SKIP:s.skip+=1
        elif t=='p' and not s.skip:s.inp+=1;s.cur=[]
    def handle_endtag(s,t):
        if t in SKIP and s.skip:s.skip-=1
        elif t=='p' and s.inp:
            s.inp=0;para=' '.join(''.join(s.cur).split());s.cur=[]
            if len(para)>=40:s.out.append(para);s.size+=len(para)
    def handle_data(s,d):
        if s.inp and not s.skip and len(s.cur)<2000:s.cur.append(d)
p=P()
for i in range(0,len(text),16384):
    p.feed(text[i:i+16384])
    if p.size>mx*3:break
joined=strip_html_once(' '.join(p.out))
joined=''.join(c for c in joined if c>=' ' and not 0xD800<=ord(c)<=0xDFFF)
joined=joined[:mx]+'...' if len(joined)>mx else joined
sys.stdout.write(json.dumps({'text':joined},ensure_ascii=False)[:40000]+'\n')
"""

def _ft_spawn(url, timeout, max_chars):
    """One article in a secret-free bubblewrap child: empty environment, no DB URI,
    own PID namespace, rlimits, whole-process wall kill. Any problem returns ''."""
    import subprocess,os,signal
    from pathlib import Path
    from integration.collector197_supervisor import _namespace_command
    root=Path(__file__).resolve().parents[1]
    cmd=_namespace_command([sys.executable,'-I','-c',_FT_CHILD%str(root)])
    payload=json.dumps({'url':url,'timeout':timeout,'max_chars':max_chars}).encode()
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},cwd=str(root),start_new_session=True)
    try:
        out,_=p.communicate(payload,timeout=timeout+3)
    except Exception:
        try:os.killpg(p.pid,signal.SIGKILL)
        except Exception:pass
        try:p.kill()
        except Exception:pass
        p.wait();return ''
    if p.returncode!=0 or len(out)>45000:return ''
    try:v=json.loads(out)
    except ValueError:return ''
    return v.get('text','') if type(v)is dict and set(v)=={'text'} else ''

def fulltext_enrich(candidates, *, end, max_chars=700, max_articles=15, workers=3, per_article=8, spawn=None, monotonic=time.monotonic):
    """Original behaviour: when a feed summary is under 200 characters, replace it
    with extracted article text. Bounded: https only, at most max_articles per run,
    stops starting new fetches at `end`, no redirects, one failure never fails the run.
    The text is a stdlib paragraph extraction, not trafilatura, so wording can differ."""
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime
    spawn=spawn or _ft_spawn
    if type(max_chars)is not int or not 1<=max_chars<=9997:raise JobRefused('Bounded full text size')
    rows=[dict(c) for c in candidates]
    todo=[i for i,c in enumerate(rows) if type(c.get('summary'))is str and len(c['summary'])<200
          and type(c.get('url'))is str and c['url'].startswith('https://') and len(c['url'])<=2000][:max_articles]
    stats={'attempted':0,'replaced':0,'skipped_no_time':0}
    def one(i):
        left=end-monotonic()
        if left<2:stats['skipped_no_time']+=1;return
        stats['attempted']+=1
        try:text=spawn(rows[i]['url'],min(per_article,left-1),max_chars)
        except Exception:return
        if type(text)is str and 0<len(text.strip())<=max_chars+3 and all(c>=' ' for c in text):
            rows[i]['summary']=text.strip();stats['replaced']+=1
    with ThreadPoolExecutor(max_workers=workers) as ex:list(ex.map(one,todo))
    return rows,stats

_GN_CHILD = r"""
import sys,os,json,resource
resource.setrlimit(resource.RLIMIT_CPU,(12,12))
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_FSIZE,(2097152,2097152))
sys.path.insert(0,%r)
assert set(os.environ)<={'LANG','LC_ALL','TZ','PWD'}
raw=sys.stdin.buffer.read(4200);assert len(raw)<=4100
v=json.loads(raw);assert type(v)is dict and set(v)=={'url','timeout','max_items','lookback_hours','observed_at'}
url=v['url'];assert type(url)is str and url.startswith('https://news.google.com/rss/search?q=') and len(url)<=1500
assert type(v['timeout'])in(int,float)and 0<v['timeout']<=20 and type(v['max_items'])is int and 1<=v['max_items']<=100 and type(v['lookback_hours'])is int and 1<=v['lookback_hours']<=168
import base64,time
from datetime import datetime,timezone,timedelta
from integration.collector197_connector import fetch_one
from integration.collector197_parser import parse_supplied_bytes
from collector129_prep.supplied_feed import prepare_supplied_feed
observed=datetime.fromisoformat(v['observed_at']);assert type(observed.tzinfo)is timezone
spec=('Google News',url,'MEDIUM')
start=time.monotonic()
got=fetch_one((spec,),url,timeout=v['timeout'],account=lambda n:None)
blob=base64.b64decode(got['body_b64'],validate=True)
parsed=parse_supplied_bytes(blob,timeout=min(10,max(1,v['timeout']-(time.monotonic()-start))),projection_limit=v['max_items'])
sel=prepare_supplied_feed(spec,parsed['entries'],cutoff=observed-timedelta(hours=v['lookback_hours']),fallback_clock=observed,max_items=v['max_items'],timeout=v['timeout'])
rows=sel['candidates']
for r in rows:r['published']=r['published'].isoformat()
sys.stdout.write(json.dumps({'candidates':rows},ensure_ascii=False,allow_nan=False,separators=(',',':'))[:900000]+'\n')
"""

def _run_child(source, payload, timeout, limit):
    import subprocess,os,signal
    from pathlib import Path
    from integration.collector197_supervisor import _namespace_command
    root=Path(__file__).resolve().parents[1]
    p=subprocess.Popen(_namespace_command([sys.executable,'-I','-c',source%str(root)]),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},cwd=str(root),start_new_session=True)
    try:out,_=p.communicate(json.dumps(payload).encode(),timeout=timeout+3)
    except Exception:
        try:os.killpg(p.pid,signal.SIGKILL)
        except Exception:pass
        try:p.kill()
        except Exception:pass
        p.wait();return None
    if p.returncode!=0 or len(out)>limit:return None
    try:return json.loads(out)
    except ValueError:return None

def _gn_spawn(url, timeout, max_items, lookback_hours, observed_at):
    v=_run_child(_GN_CHILD,{'url':url,'timeout':timeout,'max_items':max_items,'lookback_hours':lookback_hours,'observed_at':observed_at},timeout,1000000)
    return v['candidates'] if type(v)is dict and set(v)=={'candidates'} and type(v['candidates'])is list else []

def gnews_collect(*, end, groups=None, language=None, country=None, period=None, max_results=None, spawn=None, monotonic=time.monotonic):
    """Original Google News keyword search over the public RSS search endpoint
    (the same https://news.google.com/rss/search URL the gnews package builds),
    one secret-free child per query, fixed host, no redirects, no new dependency.
    Differences from the gnews package: article links stay as the Google News
    links (the package fetches each link to resolve it) and the source name is
    'Google News'. One failed query never fails the run."""
    import re
    from datetime import datetime,timezone
    from urllib.parse import quote
    from intelligence.geo import config as gc
    groups=gc.GNEWS_QUERY_GROUPS if groups is None else groups
    language=gc.GNEWS_LANGUAGE if language is None else language
    country=gc.GNEWS_COUNTRY if country is None else country
    period=gc.GNEWS_PERIOD if period is None else period
    max_results=gc.GNEWS_MAX_RESULTS if max_results is None else max_results
    if (type(groups)is not list or not 1<=len(groups)<=10 or any(type(g)is not list or not 1<=len(g)<=20 or any(type(t)is not str or not 1<=len(t)<=60 for t in g) for g in groups)
        or not re.fullmatch(r'[a-z]{2}',language or '') or not re.fullmatch(r'[A-Z]{2}',country or '')
        or not re.fullmatch(r'[1-9][0-9]{0,2}[hd]',period or '') or type(max_results)is not int or not 1<=max_results<=100):
        raise JobRefused('Bounded Google News settings required')
    hours=int(period[:-1])*(24 if period[-1]=='d' else 1)
    if hours>168:raise JobRefused('Bounded Google News period')
    spawn=spawn or _gn_spawn
    out=[];seen=set();stats={'queries':0,'failed':0,'skipped_no_time':0}
    for group in groups:
        left=end-monotonic()
        if left<3:stats['skipped_no_time']+=1;continue
        q=' OR '.join(group)
        url='https://news.google.com/rss/search?q='+quote(q,safe='')+'%20when%3A'+period+'&hl='+language+'&gl='+country+'&ceid='+country+':'+language
        stats['queries']+=1
        try:rows=spawn(url,min(15,left-1),max_results,hours,datetime.now(timezone.utc).isoformat())
        except Exception:rows=None
        if type(rows)is not list:stats['failed']+=1;continue
        for r in rows:
            if type(r)is not dict or type(r.get('title'))is not str or type(r.get('url'))is not str:continue
            if r['title'] in seen:continue  # original: one title once across queries
            seen.add(r['title'])
            # Google titles end with " - Publisher"; the original used the publisher name.
            pub=r['title'].rsplit(' - ',1)[1].strip() if ' - ' in r['title'] else ''
            r=dict(r,source=pub[:200] if pub else 'Google News');out.append(r)
    return out,stats

_TG_CHILD = r"""
import sys,os,json,resource,re,base64
resource.setrlimit(resource.RLIMIT_CPU,(8,8))
resource.setrlimit(resource.RLIMIT_AS,(192*1024*1024,192*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
resource.setrlimit(resource.RLIMIT_FSIZE,(262144,262144))
sys.path.insert(0,%r)
assert set(os.environ)<={'LANG','LC_ALL','TZ','PWD'}
raw=sys.stdin.buffer.read(9000);assert len(raw)<=8500
v=json.loads(raw);assert type(v)is dict and set(v)=={'token','chat_id','text','timeout'}
t,c,x,to=v['token'],v['chat_id'],v['text'],v['timeout']
assert type(t)is str and re.fullmatch(r'[0-9]{5,15}:[A-Za-z0-9_-]{20,80}',t)
assert type(c)is str and re.fullmatch(r'@[A-Za-z0-9_]{5,32}|-?[0-9]{1,20}',c)
assert type(x)is str and 1<=len(x)<=3600 and type(to)in(int,float) and 0<to<=20
from integration.collector197_connector import post_form_once
got=post_form_once('https://api.telegram.org/bot'+t+'/sendMessage',{'chat_id':c,'text':x,'disable_web_page_preview':'True'},timeout=to)
d=json.loads(base64.b64decode(got['body_b64'],validate=True))
assert type(d)is dict and d.get('ok')is True and type(d['result']['message_id'])is int
sys.stdout.write(json.dumps({'message_id':d['result']['message_id']})+'\n')
"""

def telegram_sender(token, chat_id, *, run=None, timeout=15):
    """Real transport for telegram_backup_attach. Token and chat id travel only on the
    child's stdin (never argv or env); the child has no DB URI. Returns message id or
    raises. Nothing builds this unless the owner gate in run_job passes."""
    run=run or _run_child
    def send(text):
        v=run(_TG_CHILD,{'token':token,'chat_id':chat_id,'text':text,'timeout':timeout},timeout,4000)
        if type(v)is not dict or set(v)!={'message_id'} or type(v['message_id'])is not int:raise JobRefused('Telegram send failed')
        return v['message_id']
    return send

TELEGRAM_MSG_LIMIT = 3500

def telegram_backup_format(a):
    return ("\U0001F4CC "+str(a.get('title',''))+"\n"
        "Source: "+str(a.get('source',''))+" | Credibility: "+str(a.get('credibility','MEDIUM'))+"\n"
        "Category: "+str(a.get('category',''))+" | Risk: "+str(a.get('risk_level',''))+" | Score: "+str(a.get('score',0))+"/100\n"
        "Country: "+str(a.get('country','') or '\u2014')+" | Corroborated by: "+str(a.get('corroboration',1))+" source(s)\n"
        "Published: "+str(a.get('published',''))+"\n"
        "URL: "+str(a.get('url',''))+"\n--\n"+str(a.get('summary','')))

def telegram_backup_batches(articles):
    """Same grouping as the original reports/telegram_backup.py."""
    batches=[];recs=[];ln=0;start=0
    for i,a in enumerate(articles):
        r=telegram_backup_format(a);rl=len(r)+2
        if ln+rl>TELEGRAM_MSG_LIMIT and recs:
            batches.append(((start,i),"\n\n====\n\n".join(recs)));recs=[];ln=0;start=i
        recs.append(r);ln+=rl
    if recs:batches.append(((start,len(articles)),"\n\n====\n\n".join(recs)))
    return batches

def telegram_permalink(chat_id, message_id):
    if chat_id.startswith("@"):return "https://t.me/"+chat_id.lstrip("@")+"/"+str(message_id)
    if chat_id.startswith("-100"):return "https://t.me/c/"+chat_id[4:]+"/"+str(message_id)
    return ""

def telegram_backup_attach(articles, *, token, chat_id, sender=None):
    """GATED, NOT WIRED. Original backup behaviour over an injected sender:
    batch the full records, send each batch, and attach message id and link to the
    articles of that batch. A failed batch leaves its articles with empty refs and
    never fails the run. With no token or chat id nothing is sent (as the original).
    There is no built-in transport: without a reviewed sender it refuses, so this
    cannot send anything by itself. Nothing calls it and config still refuses
    ENABLE_TELEGRAM_BACKUP until the owner approves recipient, content and credentials."""
    out=[dict(a) for a in articles]
    for a in out:a.setdefault('telegram_message_id',None);a.setdefault('telegram_url','')
    if not out or not token or not chat_id:return out
    if sender is None:raise JobRefused('Telegram transport not installed')
    for (a0,a1),text in telegram_backup_batches(out):
        try:mid=sender(text)
        except Exception:continue
        if type(mid)is not int:continue
        link=telegram_permalink(chat_id,mid)
        for a in out[a0:a1]:a['telegram_message_id']=mid;a['telegram_url']=link
    return out

_DIAG_REASONS = ('Duplicate HTTP header','Response header budget','HTTP header shape','Ambiguous HTTP framing','Content encoding',
    'Declared wire budget','Unverifiable close-delimited identity','Body cap without complete framing','Wire budget',
    'Truncated Content-Length body','Redirect target shape','Redirect must stay https','Redirect loop','Too many redirects',
    'Fetch wall budget','Public unicast address required','Empty response','Feed host policy','DNS set budget','TLS peer changed','Pinned peer changed')

def feed_diagnostics(indices, *, end, workers=4, monotonic=time.monotonic, runner=None):
    """Bounded, sanitized root-cause codes for feeds that did not return items.
    Each entry: index, public feed host, and one reason from a fixed vocabulary or
    'HTTP status NNN'. Never any response body, header value, URL path or secret.
    Read only; runs the same secret-free feed child once per listed feed."""
    import re,subprocess,os,signal
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime,timezone
    from urllib.parse import urlsplit
    from collector113_prep.feed_composition import original_catalog
    from integration.collector197_supervisor import _command
    feeds=original_catalog();observed=datetime.now(timezone.utc).isoformat()
    def code(text):
        m=re.search(r'HTTP status refused: ([1-5][0-9]{2})',text)
        if m:return 'HTTP status '+m.group(1)
        for r in _DIAG_REASONS:
            if r in text:return r
        if 'Timeout' in text or 'timed out' in text:return 'Timeout'
        if 'gaierror' in text or 'Name or service' in text:return 'DNS failure'
        if 'SSLError' in text or 'CERTIFICATE' in text:return 'TLS verification failed'
        return 'other'
    def one(i):
        left=end-monotonic()
        host=urlsplit(feeds[i][1]).hostname
        if left<2:return {'index':i,'host':host,'reason':'not_diagnosed_no_time'}
        t=min(15,left-1)
        payload=json.dumps({'index':i,'timeout':min(t,25),'max_items':1,'lookback_hours':1,'request_timeout':int(max(1,min(t,20))),'observed_at':observed}).encode()
        if runner is not None:return {'index':i,'host':host,'reason':runner(i)}
        try:
            p=subprocess.Popen(_command(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'},start_new_session=True)
            try:out,err=p.communicate(payload,timeout=t+3)
            except Exception:
                try:os.killpg(p.pid,signal.SIGKILL)
                except Exception:pass
                p.kill();p.wait();return {'index':i,'host':host,'reason':'Timeout'}
        except Exception:return {'index':i,'host':host,'reason':'other'}
        if p.returncode==0:return {'index':i,'host':host,'reason':'ok'}
        return {'index':i,'host':host,'reason':code(err.decode('utf-8','replace')[-600:])}
    with ThreadPoolExecutor(max_workers=workers) as ex:return list(ex.map(one,list(indices)[:64]))

def telegram_post_write(token, chat_id, sender=None):
    """post_write_hook for run_cycle: at-most-once Telegram backup AFTER the durable
    write, for the NEWLY INSERTED documents only. The writer proves which batch
    indices were inserted (all others were duplicates or failures and are never
    sent). If that proof is missing or inconsistent nothing is sent. The reviewed
    writer stores telegram_message_id=None and telegram_url='', so refs are not
    written to the DB. Sends the full records, within a 20 s cap."""
    sender=sender or telegram_sender(token,chat_id)
    def hook(docs, candidates, receipt, inserted=None, monotonic=time.monotonic):
        n=len(docs)
        if not n:return {'state':'nothing_to_send'}
        if type(inserted)is not list or len(inserted)!=receipt.get('inserted'):
            return {'state':'skipped_no_insert_proof','documents':n}
        if not inserted:return {'state':'nothing_new','documents':n}
        limit=monotonic()+20
        def capped(text):
            if monotonic()>=limit:raise JobRefused('Telegram time cap')
            return sender(text)
        full={c.get('url'):c.get('summary','') for c in candidates if type(c)is dict}
        send=[dict(docs[i],summary=full.get(docs[i]['url'],docs[i]['summary'])) for i in sorted(inserted)]
        done=telegram_backup_attach(send,token=token,chat_id=chat_id,sender=capped)
        sent=sum(1 for d in done if d.get('telegram_message_id') is not None)
        m=len(send)
        return {'state':'sent' if sent==m else ('partial' if sent else 'not_sent'),'documents':n,'new_documents':m,'sent_documents':sent}
    return hook

def phase_plan(now, outer, full, gnews):
    """Explicit end times so extras never starve the feeds and never eat the write phase.
    supervised_candidates reserves 20 s inside the deadline it is given, so the feed
    deadline is outer-25 (feeds end at outer-45, about 35 s of an 80 s job). Full text
    ends at outer-30 (outer-20 when Google News is off), Google News at outer-18, which
    leaves at least 18 s for checkpoint, prepare and write. Under 60 s total the extras
    are skipped and the feeds keep the original budget."""
    if not (full or gnews) or outer-now<60:
        return {'start':now,'feed_deadline':outer,'feed_end':min(outer-20,now+70),'extras':False,'fulltext_end':now,'gnews_end':now}
    plan={'start':now,'feed_deadline':outer-25,'extras':True,'fulltext_end':outer-(30 if gnews else 20),'gnews_end':outer-18}
    plan['feed_end']=min(plan['feed_deadline']-20,now+70)
    if not (now+25<=plan['feed_end']<plan['fulltext_end']<=plan['gnews_end']<=outer-18):raise JobRefused('Phase budget invalid')
    return plan

def run_job(values,*,nonce,runtime_evidence=None,client_factory=None,clock=None,fetch=None,hard_deadline=None):
    clock=clock or(lambda:int(time.time()))
    if type(values)is not dict or any(type(k)is not str or type(v)is not str for k,v in values.items()):raise JobRefused('Exact job configuration required')
    off={**values,'COLLECTION_ENABLED':'false'};configure(off,{})
    switch=values.get('COLLECTION_ENABLED','false')
    if switch not in ('false','true'):raise JobRefused('Exact job switch required')
    if switch=='false':return {'state':'disabled','activation_authority':False}
    # Must already be launched with bounds; do not pretend an observation sets them.
    require_job_provider(runtime_evidence,clock)
    facts=read_job_facts()
    if facts['supported']is not True:raise JobRefused('Observed job containment unavailable')
    from collector130_prep.base_profile import compile_profile
    keys={'MAX_ITEMS_PER_FEED','REQUEST_TIMEOUT','LOOKBACK_HOURS','ACTIVE_CATEGORIES','DEDUPE_THRESHOLD','ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'}
    profile=compile_profile({k:v for k,v in values.items()if k in keys})
    fp=values.get('COLLECTOR_PROFILE_FINGERPRINT','')
    if type(fp)is not str or len(fp)!=64 or any(c not in '0123456789abcdef'for c in fp):raise JobRefused('Exact profile fingerprint required')
    if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce):raise JobRefused('Exact job nonce required')
    config=configure(values,dict.fromkeys(GATES,True))
    client=None
    try:
        client=(client_factory or create_writer_client)(values['GEO_WRITER_MONGODB_URI'])
        handles=inspect_writer(client,fp,values.get('COLLECTOR_ROLE_POLICY','exact'))
        # Refresh before claim; no evidence from an earlier run can drive this one.
        require_job_provider(runtime_evidence,clock)
        if read_job_facts()['supported']is not True:raise JobRefused('Job guard changed')
        writer=GeoArticleWriter(_Client(handles['articles']),review={'mapping':('geo_intel','articles'),'write_permission':True,'unique_url_index_verified':True,'source_contract_verified':True})
        def bounded_fetch(**kw):
            require_job_provider(runtime_evidence,clock)
            full=profile['source_flags']['ENABLE_FULL_TEXT'];gnews=profile['source_flags']['ENABLE_GNEWS']
            outer=kw['deadline'];plan=phase_plan(time.monotonic(),outer,full,gnews)
            out=supervised_candidates(**dict(kw,deadline=plan['feed_deadline']),max_items=profile['max_items'],lookback_hours=profile['lookback_hours'],request_timeout=profile['timeout'],job_mode=True)
            stats={'plan_feed_window_s':round(plan['feed_end']-plan['start'],1),'extras':plan['extras']}
            if plan['extras'] and full:
                from collector115_prep.profile import defaults
                rows,stats['fulltext']=fulltext_enrich(out['candidates'],end=plan['fulltext_end'],max_chars=int(defaults()['FULL_TEXT_MAX_CHARS']))
                out=dict(out,candidates=rows)
            if plan['extras'] and gnews:
                from datetime import datetime
                extra,stats['gnews']=gnews_collect(end=plan['gnews_end'])
                for r in extra:r['published']=datetime.fromisoformat(r['published'])
                out=dict(out,candidates=out['candidates']+extra)
            stats['feeds_selected']=sum(1 for x in out['source_states'] if x['state'] in ('selected','parsed_bozo_unverified'))
            stats['feeds_total']=len(out['source_states'])
            sys.stderr.write('collector_phase_stats '+json.dumps(stats,sort_keys=True)+'\n') # no secrets, counts only
            return out
        hook=None
        if profile['source_flags']['ENABLE_TELEGRAM_BACKUP']:
            hook=telegram_post_write(values['TELEGRAM_BACKUP_BOT_TOKEN'],values['TELEGRAM_BACKUP_CHAT_ID'])
        return run_cycle(config,ledger=handles['ledger'],checkpoints=CoverageCheckpoints(handles['checkpoints']),nonce=nonce,fetch=fetch or bounded_fetch,categories=profile['active_categories'],threshold=profile['threshold'],clock=clock,writer=writer,**({'hard_deadline':hard_deadline}if hard_deadline is not None else{}),**({'post_write_hook':hook}if hook is not None else{}))
    except Exception:raise JobRefused('Job held; inspect durable state, never retry blindly')from None
    finally:
        if client is not None:
            try:client.close()
            except Exception:pass

def main(argv=None,*,values=None,runtime_evidence=None,output=None):
    """Owner-controlled launcher injects scoped provider; no env-ready shortcut.
    Direct CLI is read-only diagnostics. No URI, nonce or activation from argv.
    """
    argv=sys.argv[1:]if argv is None else argv
    output=output or sys.stdout
    if argv!=['--diagnose']:
        output.write(json.dumps({'error':'explicit_read_only_diagnostic_required'})+'\n');return 2
    output.write(json.dumps(read_job_facts(),sort_keys=True)+'\n');return 0

if __name__=='__main__':raise SystemExit(main())
