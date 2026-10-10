"""Read actual protected runner facts. No booleans from workflow env as proof."""
import hashlib,json,os,time,resource
from pathlib import Path
from integration.collector197_job_runtime import (JobRuntimeEvidence,JobRefused,
    read_job_facts,JOB_BYTES,PARENT_BYTES,COORDINATOR_BYTES)
from integration.collector197_coverage import catalog_fingerprint
MAX_PEAK=JOB_BYTES-512*1024*1024

def source_digest(root):
    root=Path(root)
    manifest=json.loads((root/'integration/collector_actions/source-files.json').read_text())
    from importlib.metadata import distributions
    package_bytes={}
    for d in distributions():
        for f in d.files or []:
            if str(f).endswith(('.py','.so','.pyd','.dist-info/METADATA')):
                p=Path(d.locate_file(f))
                if p.is_file():package_bytes[d.metadata['Name'].lower()+':'+str(f)]=hashlib.sha256(p.read_bytes()).hexdigest()
    values={p:hashlib.sha256((root/p).read_bytes()).hexdigest()for p in manifest}
    return hashlib.sha256(json.dumps({'source':values,'packages':package_bytes},sort_keys=True,separators=(',',':')).encode()).hexdigest()

def protected_receipt(path,root,run_identity,activation_reference,now):
    # Fixed inherited read-only FD3 opened by the root launcher. No path from
    # environment, payload or caller. File lives in root0700 fresh directory.
    st=os.fstat(3)
    import stat
    if not stat.S_ISREG(st.st_mode)or st.st_uid!=0 or st.st_mode&0o222 or st.st_size>16384:
        raise JobRefused('Root-owned immutable qualification fd required')
    import fcntl
    if fcntl.fcntl(3,fcntl.F_GETFL)&os.O_ACCMODE!=os.O_RDONLY:raise JobRefused('Readonly qualification fd')
    raw=os.pread(3,16385,0)
    bundle=json.loads(raw)
    q=bundle['receipt']; evidence=bundle['evidence']
    if hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=bundle['evidence_hash']:raise JobRefused('Raw qualification evidence hash mismatch')
    if evidence['measurement_peak']!=q['measurement_peak'] or evidence['measurement_events']!=q['measurement_events'] or evidence['adversary_exit']!=0 or 'aggregate_fixture_oom_group_kill_verified=true'not in evidence['adversary_log']:raise JobRefused('Derived qualification mismatch')
    expected={'version','run_identity','activation_reference','source_digest','observed_at',
      'measurement_peak','measurement_events','aggregate_adversary_verified','measurement_completed'}
    if type(q)is not dict or set(q)!=expected or q['version']!=1:raise JobRefused('Exact qualification schema')
    if (q['run_identity']!=run_identity or q['activation_reference']!=activation_reference
      or q['source_digest']!=source_digest(root)):raise JobRefused('Qualification source binding')
    if type(q['observed_at'])is not int or not 0<=q['observed_at']<=now<=q['observed_at']+120:
        raise JobRefused('Fresh qualification required')
    if type(q['measurement_peak'])is not int or not 0<q['measurement_peak']<=MAX_PEAK:
        raise JobRefused('Measured headroom refused')
    if q['measurement_completed']is not True or q['aggregate_adversary_verified']is not True:
        raise JobRefused('Independent aggregate qualification required')
    e=q['measurement_events']
    if type(e)is not dict or set(e)!={'max','oom','oom_kill','oom_group_kill'} or any(type(v)is not int or v!=0 for v in e.values()):
        raise JobRefused('Clean measured workload required')
    return q

class ActionsProvider:
    def __init__(self,root,receipt,run_identity,activation_reference,clock=lambda:int(time.time())):
        self.root=Path(root);self.receipt=receipt;self.run_identity=run_identity
        self.activation_reference=activation_reference;self.clock=clock
    def __call__(self):
        now=self.clock()
        if os.geteuid()==0:raise JobRefused('Nonroot required')
        status=dict(x.split(':',1)for x in Path('/proc/self/status').read_text().splitlines()if ':'in x)
        if any(int(status[k].strip(),16)!=0 for k in ('CapEff','CapPrm','CapInh','CapAmb')) or status['NoNewPrivs'].strip()!='1':
            raise JobRefused('Privilege drop required')
        if not hasattr(self,'qualified_at'):
            protected_receipt(None,self.root,self.run_identity,self.activation_reference,now)
            self.qualified_at=now
        if not self.qualified_at<=now<=self.qualified_at+90:raise JobRefused('Qualified run window elapsed')
        f=read_job_facts()
        if f['supported']is not True:raise JobRefused('Actual Actions job facts refused')
        # Existing job coordinator sets its AS limit before worker imports. Source
        # identity above and worker pins bind that code, not an env assertion.
        return JobRuntimeEvidence(catalog_fingerprint(),self.activation_reference,
          self.run_identity,now,now+110,f['available_memory_bytes'],
          f['aggregate_memory_max'],f['aggregate_swap_max'],f['aggregate_oom_group'],
          f['parent_as_limit'],COORDINATOR_BYTES,90,f['pid_namespace'],f['nested_isolation'],
          f['source_pins'],True)
