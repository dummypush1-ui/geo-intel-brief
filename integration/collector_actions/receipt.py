"""Fixed root stdlib-only observed qualification writer, run with -I -S."""
import sys,os,json,time,hashlib
from pathlib import Path

def create(payload_path,result_path,group_path,adversary_path,receipt_path):
    if os.geteuid()!=0:raise ValueError('Root required')
    payload=json.loads(Path(payload_path).read_text());result=json.loads(Path(result_path).read_text())
    if (result.get('state')!='measured_no_write' or result.get('readonly_mongo_preflight')is not True
      or result.get('writer_memory_proven')is not False):raise ValueError('Exact scoped qualification required')
    if result.get('driver_serialization_fixture')!={'maximum_rows':1000,'checkpoint_fixture':True,'writer_bson_fixture':True,'aggregate_overbudget_refused':True,'real_db_writes':False}:raise ValueError('Maximum local fixture required')
    group=Path(group_path)
    if tuple(int((group/p).read_text())for p in ('memory.max','memory.swap.max','memory.oom.group'))!=(3221225472,0,1):raise ValueError('Guard changed')
    if (group/'cgroup.procs').read_text().strip():raise ValueError('Measurement orphans')
    events=dict(x.split()for x in (group/'memory.events').read_text().splitlines())
    e={k:int(events[k])for k in ('max','oom','oom_kill','oom_group_kill')}
    peak=int((group/'memory.peak').read_text());adversary=Path(adversary_path).read_text()
    if any(e.values())or not 0<peak<=2560*1024*1024:raise ValueError('Headroom refused')
    if 'aggregate_fixture_oom_group_kill_verified=true'not in adversary or len(adversary)>8192:raise ValueError('Actual aggregate adversary output required')
    evidence={'measurement_peak':peak,'measurement_events':e,'measurement_result':result,'adversary_exit':0,'adversary_log':adversary}
    receipt={'version':1,'run_identity':'gha:'+payload['repository']+':'+payload['run_id']+':'+payload['run_attempt'],
      'activation_reference':payload['activation_reference'],'source_digest':result['source_digest'],'observed_at':int(time.time()),
      'measurement_peak':peak,'measurement_events':e,'aggregate_adversary_verified':True,'measurement_completed':True}
    bundle={'receipt':receipt,'evidence':evidence,'evidence_hash':hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    p=Path(receipt_path)
    with p.open('x')as f:json.dump(bundle,f,sort_keys=True)
    p.chmod(0o400)
    # Root opens read-onlyFD before drop. Do not disclose this path to payload.
    p.chmod(0o444)
if __name__=='__main__':create(*sys.argv[1:])
