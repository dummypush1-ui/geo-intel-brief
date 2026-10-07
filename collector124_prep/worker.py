"""Fixed-code candidate worker. No command/paths accepted from its input."""
import sys,resource,json
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(5,5))
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_FSIZE,(2097152,2097152))
# Installation-owned paths only. Scratch location must be replaced/pinned before
# deployment. -I means no cwd/PYTHONPATH/user-site import influence.
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connector import fetch_one
raw=sys.stdin.buffer.read(131073)
try:
 if len(raw)>131072:raise ValueError()
 data=json.loads(raw)
 if type(data)is not dict or set(data)!={'feeds','url','timeout'}:raise ValueError()
 if type(data['feeds'])is not list or len(data['feeds'])>64:raise ValueError()
 feeds=tuple(tuple(f)for f in data['feeds'])
 result=fetch_one(feeds,data['url'],timeout=data['timeout'])
 wire=json.dumps({'ok':True,'result':result},separators=(',',':')).encode()
 if len(wire)>2097152:raise ValueError()
 sys.stdout.buffer.write(wire)
except Exception:
 sys.stdout.buffer.write(b'{"ok":false,"error":"fetch_refused"}')
 sys.exit(1)
