"""Dedicated supervised coordinator. No DB, URI, credentials or HTTP.
Linux parent-death SIGTERM invokes cleanup of all tracked feed groups/reaping.
"""
import os,sys,json,ctypes,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
parent=os.getppid()
def terminate(*args):raise SystemExit(70)
signal.signal(signal.SIGTERM,terminate)
libc=ctypes.CDLL(None,use_errno=True)
assert libc.prctl(1,signal.SIGTERM,0,0,0)==0
assert os.getppid()==parent and parent!=1
raw=sys.stdin.buffer.read(4097);assert len(raw)<=4096
v=json.loads(raw);assert type(v)is dict and set(v)in ({'deadline','per_feed_seconds','max_items','lookback_hours','request_timeout','observed_at'},{'deadline','per_feed_seconds','max_items','lookback_hours','request_timeout','observed_at','job_mode'})
if 'job_mode'in v:
    assert v['job_mode']is True
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
from integration.collector197_supervisor import collect_catalog
from datetime import datetime
out=collect_catalog(deadline=v['deadline'],per_feed_seconds=v['per_feed_seconds'],max_items=v['max_items'],lookback_hours=v['lookback_hours'],request_timeout=v['request_timeout'],clock=datetime.fromisoformat(v['observed_at']))
for row in out['candidates']:row['published']=row['published'].isoformat()
wire=json.dumps(out,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
assert len(wire)<=2097152
sys.stdout.buffer.write(wire)
