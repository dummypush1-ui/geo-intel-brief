"""Fixed trusted feed worker: no URI, credentials, DB or delivery modules.
Network connector runs IN this supervised group, including blocking DNS.
Parser bwrap shares group and has die-with-parent, no orphan session fallback.
"""
import sys, os, resource, json, hashlib, time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU, (12,12))
resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (64,64))
resource.setrlimit(resource.RLIMIT_FSIZE, (2097152,2097152))
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from integration.collector197_connector import fetch_one
from collector113_prep.feed_composition import original_catalog
from integration.collector197_parser import parse_supplied_bytes
from collector129_prep.supplied_feed import prepare_supplied_feed
from datetime import datetime, timezone, timedelta
assert set(os.environ) <= {'LANG','LC_ALL','TZ'}
raw=sys.stdin.buffer.read(4097);assert len(raw)<=4096
v=json.loads(raw);assert type(v)is dict and set(v)=={'index','timeout','max_items','lookback_hours','request_timeout','observed_at'}
feeds=original_catalog();index=v['index'];assert type(index)is int and 0<=index<len(feeds)
assert type(v['timeout'])in (int,float) and 0<v['timeout']<=25
assert type(v['max_items'])is int and 1<=v['max_items']<=200
assert type(v['lookback_hours'])is int and 1<=v['lookback_hours']<=168
observed=datetime.fromisoformat(v['observed_at']);assert type(observed.tzinfo)is timezone
assert type(v['request_timeout'])is int and 1<=v['request_timeout']<=30
start=time.monotonic();deadline=start+v['timeout'];spec=feeds[index]
def account(n):
    sys.stdout.write(json.dumps({'type':'wire','bytes':n})+'\n');sys.stdout.flush()
fetched=fetch_one(feeds,spec[1],timeout=min(v['request_timeout'],v['timeout']),account=account)
import base64
blob=base64.b64decode(fetched['body_b64'],validate=True)
remaining=deadline-time.monotonic();assert remaining>0
parsed=parse_supplied_bytes(blob,timeout=min(10,remaining),projection_limit=v['max_items'])
selected=prepare_supplied_feed(spec,parsed['entries'],cutoff=observed-timedelta(hours=v['lookback_hours']),fallback_clock=observed,max_items=v['max_items'],timeout=min(v['request_timeout'],v['timeout']))
assert time.monotonic()<deadline
rows=selected['candidates']
for row in rows:row['published']=row['published'].isoformat()
out={'index':index,'state':'parsed_bozo_unverified'if parsed['bozo']else'selected',
     'wire_bytes':fetched['wire_bytes'],'decoded_bytes':len(blob),'candidates':rows}
wire=json.dumps(out,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
assert len(wire)<=1048576
sys.stdout.buffer.write(json.dumps({'type':'result','envelope':out},ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n');sys.stdout.flush()
