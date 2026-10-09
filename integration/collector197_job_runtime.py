"""197e-a job-only runtime contract. No WSGI field, writes or activation grant.
3GiB is a design allocation, not measured consumption or guaranteed overhead.
The owner-operated runner establishes containment; this module only observes it.
"""
import os,resource,time
from pathlib import Path
from dataclasses import dataclass
from integration.collector197_coverage import catalog_fingerprint
from integration.collector197_host_probe import isolation_probe
from integration.collector197_supervisor import _pins
MiB=1024*1024
JOB_BYTES=3072*MiB
PARENT_BYTES=512*MiB
COORDINATOR_BYTES=256*MiB
class JobRefused(ValueError):pass

@dataclass(frozen=True)
class JobRuntimeEvidence:
    catalog:str
    activation_reference:str
    host_reference:str
    observed_at:int
    expires_at:int
    available_memory_bytes:int
    aggregate_memory_max:int
    aggregate_swap_max:int
    aggregate_oom_group:int
    parent_as_limit:int
    coordinator_as_limit:int
    job_deadline_seconds:int
    pid_namespace:bool
    nested_isolation:bool
    source_pins:bool
    aggregate_guard_verified:bool
    def validate(self,now):
        if type(now)is not int or now<0 or self.catalog!=catalog_fingerprint():raise JobRefused('Exact job evidence required')
        for ref in (self.activation_reference,self.host_reference):
            if type(ref)is not str or not 1<=len(ref)<=200 or any(ord(c)<33 or ord(c)>126 for c in ref):raise JobRefused('Bounded job references required')
        numbers=(self.observed_at,self.expires_at,self.available_memory_bytes,self.aggregate_memory_max,self.aggregate_swap_max,self.aggregate_oom_group,self.parent_as_limit,self.coordinator_as_limit,self.job_deadline_seconds)
        if any(type(v)is not int for v in numbers):raise JobRefused('Exact job counts required')
        if not 0<=self.observed_at<=now<self.expires_at<=self.observed_at+120 or self.available_memory_bytes<JOB_BYTES:raise JobRefused('Fresh job capacity required')
        if (self.aggregate_memory_max,self.aggregate_swap_max,self.aggregate_oom_group,self.parent_as_limit,self.coordinator_as_limit,self.job_deadline_seconds)!=(JOB_BYTES,0,1,PARENT_BYTES,COORDINATOR_BYTES,90):raise JobRefused('Fixed job containment required')
        if any(v is not True for v in (self.pid_namespace,self.nested_isolation,self.source_pins,self.aggregate_guard_verified)):raise JobRefused('Observed job isolation required')
        return self

def _guard():
    """Fixed current cgroup-v2 membership. No caller-controlled file paths.
    Refuse root/shared/writable guard; caller cannot move itself out of it.
    A later owner-operated setup creates it before launching this process.
    """
    lines=Path('/proc/self/cgroup').read_text().splitlines()
    if len(lines)!=1 or not lines[0].startswith('0::/'):raise JobRefused('Cgroup v2 required')
    rel=lines[0][3:]
    if rel=='/' or '..'in rel.split('/'):raise JobRefused('Dedicated job cgroup required')
    root=Path('/sys/fs/cgroup').resolve();group=(root/rel.lstrip('/')).resolve()
    if root not in group.parents:raise JobRefused('Fixed current cgroup required')
    # Refuse any writable ancestor membership target that could escape the guard.
    for ancestor in (root,*group.parents):
        if ancestor==root or root in ancestor.parents:
            if os.access(ancestor/'cgroup.procs',os.W_OK):raise JobRefused('Ancestor escape refused')
    for p in (group,group/'cgroup.procs',group/'memory.max',group/'memory.swap.max',group/'memory.oom.group'):
        if p.stat().st_uid!=0 or os.access(p,os.W_OK):raise JobRefused('Protected aggregate guard required')
    count=lambda name:int((group/name).read_text().strip())
    result=(count('memory.max'),count('memory.swap.max'),count('memory.oom.group'))
    if result!=(JOB_BYTES,0,1):raise JobRefused('Fixed aggregate guard required')
    members=[int(v)for v in (group/'cgroup.procs').read_text().split()]
    if members!=[os.getpid()]:raise JobRefused('Exclusive initial job membership required')
    events=dict(line.split()for line in (group/'memory.events').read_text().splitlines())
    if any(int(events.get(k,'-1'))!=0 for k in ('max','oom','oom_kill')):raise JobRefused('Clean aggregate guard required')
    return result

def read_job_facts():
    """Read-only/local fixed probes, never DB, network or cgroup configuration."""
    out={'supported':False,'available_memory_bytes':None,'aggregate_memory_max':None,
         'aggregate_swap_max':None,'aggregate_oom_group':None,'parent_as_limit':None,
         'pid_namespace':False,'nested_isolation':False,'source_pins':False,
         'design_accounting_bytes':JOB_BYTES,'activation_authority':False}
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):out['available_memory_bytes']=int(line.split()[1])*1024
        soft,hard=resource.getrlimit(resource.RLIMIT_AS)
        out['parent_as_limit']=soft if soft==hard else None
        a,b,c=_guard();out.update(aggregate_memory_max=a,aggregate_swap_max=b,aggregate_oom_group=c)
        _pins();out['source_pins']=True
        out['pid_namespace']=isolation_probe();out['nested_isolation']=isolation_probe(True)
        out['supported']=(out['available_memory_bytes']is not None and out['available_memory_bytes']>=JOB_BYTES and out['parent_as_limit']==PARENT_BYTES and out['pid_namespace']and out['nested_isolation'])
    except Exception:pass
    return out

def require_job_provider(provider,clock):
    if not callable(provider):raise JobRefused('Independent job evidence provider required')
    record=provider()
    if type(record)is not JobRuntimeEvidence:raise JobRefused('Exact job evidence record required')
    return record.validate(clock())
