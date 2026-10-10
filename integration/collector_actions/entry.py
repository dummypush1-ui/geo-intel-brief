"""Nonroot bounded job entry. Secrets arrive on stdin, never argv/logs."""
import resource
LIMIT=512*1024*1024
resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
import sys,json,hashlib,time,re,os,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from integration.collector_actions.provider import ActionsProvider,source_digest
from integration.collector197_job import run_job
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

def config(raw):
    if type(raw)is not dict or set(raw)!={'mode','repository','run_id','run_attempt','activation_reference','values'}:raise JobRefused('Exact launcher payload required')
    if raw['mode']not in ('measure','collect','status')or raw['repository']!=REPO:raise JobRefused('Scoped mode/repository required')
    for k in ('run_id','run_attempt'):
        if type(raw[k])is not str or not re.fullmatch('[1-9][0-9]{0,19}',raw[k]):raise JobRefused('Exact run identity')
    ref=raw['activation_reference']
    if type(ref)is not str or not 1<=len(ref)<=200 or any(ord(c)<33 or ord(c)>126 for c in ref):raise JobRefused('Owner activation source reference required')
    v=raw['values'];allowed={'GEO_WRITER_MONGODB_URI','COLLECTOR_PROFILE_FINGERPRINT'}
    if type(v)is not dict or set(v)!=allowed or any(type(x)is not str for x in v.values()):raise JobRefused('Exact installation values')
    if not v['GEO_WRITER_MONGODB_URI'] or len(v['GEO_WRITER_MONGODB_URI'])>4096 or not re.fullmatch('[0-9a-f]{64}',v['COLLECTOR_PROFILE_FINGERPRINT']):raise JobRefused('Writer/profile required')
    return {**v,'COLLECTION_ENABLED':'true','ENABLE_FULL_TEXT':'false','ENABLE_GNEWS':'false','ENABLE_TELEGRAM_BACKUP':'false'}

def nonce(repository,run_id):
    # Deliberately excludes run_attempt. Every GitHub rerun is the SAME job.
    return 'gha_'+hashlib.sha256((repository+'\n'+run_id).encode()).hexdigest()

def read_status(values,n):
    c=create_writer_client(values['GEO_WRITER_MONGODB_URI'])
    try:
        h=inspect_writer(c,values['COLLECTOR_PROFILE_FINGERPRINT']);ledger=h['ledger']
        d=ledger.c.find_one({'_id':'geo108'},max_time_ms=2000)
        _valid_document(d,'geo108',values['COLLECTOR_PROFILE_FINGERPRINT'])
        key=ledger_key(ledger,n)
        found=next((j for j in ([d['active']]if d['active']else[])+d['history']if j['key']==key),None)
        return {'job':key,'known':found is not None,'phase':found['phase']if found else None,
          'blocked':d['active']is not None,'history_count':len(d['history'])}
    finally:c.close()

def measure(values):
    start=time.monotonic()
    facts=read_job_facts()
    if facts['supported']is not True:raise JobRefused('Measured containment unavailable')
    # Real dedicated Mongo preflight is read-only. No ledger init/claim here.
    c=create_writer_client(values['GEO_WRITER_MONGODB_URI'])
    try:inspect_writer(c,values['COLLECTOR_PROFILE_FINGERPRINT'])
    finally:c.close()
    from integration.collector_actions.qualification import maximum_processing
    maximum=maximum_processing()
    p=compile_profile({'ENABLE_FULL_TEXT':'false','ENABLE_GNEWS':'false','ENABLE_TELEGRAM_BACKUP':'false'})
    out=supervised_candidates(deadline=start+80,per_feed_seconds=25,
      max_items=p['max_items'],lookback_hours=p['lookback_hours'],request_timeout=p['timeout'],job_mode=True)
    # No DB or writer. Includes decode, checkpoint-like capture and original
    # prepare path in the measured parent. Actual Mongo/write overhead remains
    # unmeasured and is an explicit separate qualification limit.
    docs=prepare_geo_documents(out['candidates'],p['active_categories'],p['threshold'])['documents']
    return {'state':'measured_no_write','fetched':len(out['candidates']),'prepared':len(docs),
      'coverage_states':[x['state']for x in out['source_states']],
      'writer_memory_proven':False,'driver_serialization_fixture':maximum,'readonly_mongo_preflight':True,'source_digest':source_digest(ROOT)}

def execute(raw):
    hard_deadline=time.monotonic()+80
    values=config(raw);n=nonce(raw['repository'],raw['run_id'])
    identity='gha:'+raw['repository']+':'+raw['run_id']+':'+raw['run_attempt']
    if raw['mode']=='measure':return measure(values)
    if raw['mode']=='status' or raw['run_attempt']!='1':
        if os.geteuid()==0 or read_job_facts()['supported']is not True:raise JobRefused('Readonly status containment unavailable')
        return {'state':'status_only_held','status':read_status(values,n)}
    provider=ActionsProvider(ROOT,None,identity,raw['activation_reference'])
    provider() # Before even read-only Atlas preflight.
    s=read_status(values,n)
    if raw['mode']=='status' or raw['run_attempt']!='1' or s['known'] or s['blocked'] or s['history_count']>=64:
        # Never replay an accepted-but-unclaimed job or create new claim on rerun.
        # Reconciliation is read-only; held jobs require separately reviewed repair.
        return {'state':'status_only_held','status':s}
    return run_job(values,nonce=n,runtime_evidence=provider,hard_deadline=hard_deadline)

def soft_stop(*args):
    raise JobRefused('Graceful stop; durable state reconciliation required')

def main():
    signal.signal(signal.SIGTERM,soft_stop)
    signal.signal(signal.SIGALRM,soft_stop)
    signal.setitimer(signal.ITIMER_REAL,82)
    try:
        raw=sys.stdin.buffer.read(8193)
        if len(raw)>8192:raise JobRefused('Payload bound')
        data=json.loads(raw)
        out=execute(data)
        sys.stdout.write(json.dumps(out,sort_keys=True)+'\n')
        return 0 if out.get('state')in ('measured_no_write','completed','status_only_held') else 3
    except Exception:
        sys.stdout.write('{"error":"job_held_inspect_durable_state_no_blind_retry"}\n');return 2
    finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':raise SystemExit(main())
