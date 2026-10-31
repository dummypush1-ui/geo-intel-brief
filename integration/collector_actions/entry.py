"""Nonroot bounded job entry. Secrets arrive on stdin, never argv/logs."""
import resource
LIMIT=512*1024*1024
resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
import sys,json,hashlib,time,re,os,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from integration.collector_actions.provider import ActionsProvider,source_digest
from integration.collector197_job import run_job,SAFE_INNER_CLASSES,INNER_JOB_STAGES,CONNECT_PREDICATES,CONNECT_UNDERLYING
from integration.collector197_job_runtime import read_job_facts,JobRefused
from integration.collector197_coordinator import supervised_candidates
from integration.collector197_http import create_writer_client
from integration.collector197_preflight import inspect_writer
from integration.geo_collector_contract import prepare_geo_documents
from collector130_prep.base_profile import compile_profile
from collector108_prep.durable_ledger import _valid_document

def ledger_key(ledger,n):
    return hashlib.sha256((ledger.profile+'\n'+n).encode()).hexdigest()

REPO='dummypush1-ui/geo-intel-brief'

_STAGE='start'
_STAGES=frozenset({'start','payload','config','facts','atlas_preflight','fixtures','fetch','prepare','feed_diagnostics','provider','status','job'})
_HELD_CLASSES=frozenset({'JobRefused','ParserRefused','SupervisorRefused','ProbeRefused','EvidenceRefused','HTTPRefused','ConfigRefused','ConnectorRefused','CoordinatorRefused','ProfileRefused','ValueError','KeyError','TypeError','OSError','TimeoutError','JSONDecodeError','ConnectionError','ConnectionFailure','ServerSelectionTimeoutError','OperationFailure','ConfigurationError','NetworkTimeout','AutoReconnect','ExecutionTimeout','HTTPError','URLError','SSLError','gaierror','TimeoutExpired','CalledProcessError','PreflightConnectRefused','PreflightRoleRefused','PreflightIndexRefused','PreflightLedgerRefused'})

def _held(stage,exc):
    # Bounded stage/exception-class marker on stderr only. Never str(exc),
    # traceback, values, env, paths or URLs. Stdout protocol unchanged.
    if stage not in _STAGES:stage='start'
    name=type(exc).__name__
    if name not in _HELD_CLASSES:name='other'
    rec={'error':'job_held_inspect_durable_state_no_blind_retry','stage':stage,'exception':name}
    inner=getattr(exc,'inner_class',None)
    if type(inner)is str and (inner in SAFE_INNER_CLASSES or inner=='other'):rec['inner']=inner
    istage=getattr(exc,'inner_stage',None)
    if type(istage)is str and (istage in INNER_JOB_STAGES or istage=='other'):rec['inner_stage']=istage
    pred=getattr(exc,'connect_predicate',None)
    if type(pred)is str and (pred in CONNECT_PREDICATES or pred=='other'):rec['predicate']=pred
    und=getattr(exc,'connect_underlying',None)
    if type(und)is str and (und in CONNECT_UNDERLYING or und=='other'):rec['underlying']=und
    sys.stderr.write(json.dumps(rec,sort_keys=True)+'\n')

def config(raw):
    if type(raw)is not dict or set(raw)!={'mode','repository','run_id','run_attempt','activation_reference','values'}:raise JobRefused('Exact launcher payload required')
    if raw['mode']not in ('measure','collect','status')or raw['repository']!=REPO:raise JobRefused('Scoped mode/repository required')
    for k in ('run_id','run_attempt'):
        if type(raw[k])is not str or not re.fullmatch('[1-9][0-9]{0,19}',raw[k]):raise JobRefused('Exact run identity')
    ref=raw['activation_reference']
    if type(ref)is not str or not 1<=len(ref)<=200 or any(ord(c)<33 or ord(c)>126 for c in ref):raise JobRefused('Owner activation source reference required')
    v=raw['values'];allowed={'GEO_WRITER_MONGODB_URI','COLLECTOR_PROFILE_FINGERPRINT'}
    if type(v)is not dict or not allowed<=set(v)<=allowed|{'COLLECTOR_ROLE_POLICY','ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP','TELEGRAM_BACKUP_BOT_TOKEN','TELEGRAM_BACKUP_CHAT_ID','TELEGRAM_BACKUP_APPROVAL'} or any(type(x)is not str for x in v.values()):raise JobRefused('Exact installation values')
    if any(v.get(k,'false')not in ('true','false')for k in ('ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP')):raise JobRefused('Exact feature switch')
    if 'COLLECTOR_ROLE_POLICY' in v and v['COLLECTOR_ROLE_POLICY'] not in ('exact','coverage_admin_accepted'):raise JobRefused('Exact role policy required')
    if v.get('ENABLE_TELEGRAM_BACKUP','false')!='true' and any(k in v for k in ('TELEGRAM_BACKUP_BOT_TOKEN','TELEGRAM_BACKUP_CHAT_ID','TELEGRAM_BACKUP_APPROVAL')):raise JobRefused('Telegram values without switch')
    if not v['GEO_WRITER_MONGODB_URI'] or len(v['GEO_WRITER_MONGODB_URI'])>4096 or not re.fullmatch('[0-9a-f]{64}',v['COLLECTOR_PROFILE_FINGERPRINT']):raise JobRefused('Writer/profile required')
    return {**v,'COLLECTION_ENABLED':'true','ENABLE_FULL_TEXT':v.get('ENABLE_FULL_TEXT','false'),'ENABLE_GNEWS':v.get('ENABLE_GNEWS','false'),'ENABLE_TELEGRAM_BACKUP':v.get('ENABLE_TELEGRAM_BACKUP','false')}

def nonce(repository,run_id):
    # Deliberately excludes run_attempt. Every GitHub rerun is the SAME job.
    return 'gha_'+hashlib.sha256((repository+'\n'+run_id).encode()).hexdigest()

def read_status(values,n):
    c=create_writer_client(values['GEO_WRITER_MONGODB_URI'])
    try:
        h=inspect_writer(c,values['COLLECTOR_PROFILE_FINGERPRINT'],values.get('COLLECTOR_ROLE_POLICY','exact'));ledger=h['ledger']
        d=ledger.c.find_one({'_id':'geo108'},max_time_ms=2000)
        _valid_document(d,'geo108',values['COLLECTOR_PROFILE_FINGERPRINT'])
        key=ledger_key(ledger,n)
        found=next((j for j in ([d['active']]if d['active']else[])+d['history']if j['key']==key),None)
        return {'job':key,'known':found is not None,'phase':found['phase']if found else None,
          'blocked':d['active']is not None,'history_count':len(d['history'])}
    finally:c.close()

def measure(values):
    global _STAGE
    start=time.monotonic();hard_end=start+74
    _STAGE='facts';facts=read_job_facts()
    if facts['supported']is not True:raise JobRefused('Measured containment unavailable')
    _STAGE='atlas_preflight'
    # Real dedicated Mongo preflight is read-only. No ledger init/claim here.
    c=create_writer_client(values['GEO_WRITER_MONGODB_URI'])
    try:inspect_writer(c,values['COLLECTOR_PROFILE_FINGERPRINT'],values.get('COLLECTOR_ROLE_POLICY','exact'))
    finally:c.close()
    _STAGE='fixtures'
    from integration.collector_actions.qualification import maximum_processing
    maximum=maximum_processing()
    p=compile_profile({'ENABLE_FULL_TEXT':'false','ENABLE_GNEWS':'false','ENABLE_TELEGRAM_BACKUP':'false'})
    _STAGE='fetch'
    out=supervised_candidates(deadline=start+80,per_feed_seconds=25,
      max_items=p['max_items'],lookback_hours=p['lookback_hours'],request_timeout=p['timeout'],job_mode=True)
    # No DB or writer. Includes decode, checkpoint-like capture and original
    # prepare path in the measured parent. Actual Mongo/write overhead remains
    # unmeasured and is an explicit separate qualification limit.
    _STAGE='prepare'
    docs=prepare_geo_documents(out['candidates'],p['active_categories'],p['threshold'])['documents']
    bad=[x['index']for x in out['source_states']if x['state']not in ('selected','parsed_bozo_unverified')]
    from integration.collector197_job import feed_diagnostics
    _STAGE='feed_diagnostics'
    diag=feed_diagnostics(bad,end=time.monotonic()+max(0,min(15,hard_end-time.monotonic()))) if bad else []
    return {'state':'measured_no_write','feed_diagnostics':diag,'fetched':len(out['candidates']),'prepared':len(docs),
      'coverage_states':[x['state']for x in out['source_states']],
      'writer_memory_proven':False,'driver_serialization_fixture':maximum,'readonly_mongo_preflight':True,'source_digest':source_digest(ROOT)}

def execute(raw):
    global _STAGE
    hard_deadline=time.monotonic()+80
    _STAGE='config';values=config(raw);n=nonce(raw['repository'],raw['run_id'])
    identity='gha:'+raw['repository']+':'+raw['run_id']+':'+raw['run_attempt']
    if raw['mode']=='measure':return measure(values)
    if raw['mode']=='status' or raw['run_attempt']!='1':
        _STAGE='status'
        if os.geteuid()==0 or read_job_facts()['supported']is not True:raise JobRefused('Readonly status containment unavailable')
        return {'state':'status_only_held','status':read_status(values,n)}
    _STAGE='provider'
    provider=ActionsProvider(ROOT,None,identity,raw['activation_reference'])
    provider() # Before even read-only Atlas preflight.
    _STAGE='status';s=read_status(values,n)
    if raw['mode']=='status' or raw['run_attempt']!='1' or s['known'] or s['blocked'] or s['history_count']>=64:
        # Never replay an accepted-but-unclaimed job or create new claim on rerun.
        # Reconciliation is read-only; held jobs require separately reviewed repair.
        return {'state':'status_only_held','status':s}
    _STAGE='job'
    return run_job(values,nonce=n,runtime_evidence=provider,hard_deadline=hard_deadline)

def soft_stop(*args):
    raise JobRefused('Graceful stop; durable state reconciliation required')

def main():
    signal.signal(signal.SIGTERM,soft_stop)
    signal.signal(signal.SIGALRM,soft_stop)
    signal.setitimer(signal.ITIMER_REAL,82)
    global _STAGE
    _STAGE='payload'
    try:
        raw=sys.stdin.buffer.read(8193)
        if len(raw)>8192:raise JobRefused('Payload bound')
        data=json.loads(raw)
        out=execute(data)
        sys.stdout.write(json.dumps(out,sort_keys=True)+'\n')
        return 0 if out.get('state')in ('measured_no_write','completed','status_only_held') else 3
    except Exception as e:
        _held(_STAGE,e)
        sys.stdout.write('{"error":"job_held_inspect_durable_state_no_blind_retry"}\n');return 2
    finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':raise SystemExit(main())
