"""Inactive bounded RSS/Atom byte parser child, OS-isolated by fixed runner."""
import sys,resource,json,io,hashlib,socket,os
resource.setrlimit(resource.RLIMIT_CPU,(3,3))
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
# namespace must contain only loopback; environment must be the fixed contract.
assert set(os.environ)<={'LANG','LC_ALL','TZ','PATH','PYTHONPATH','PWD'}
assert all(name=='lo' for _,name in socket.if_nameindex())
import feedparser,feedparser.http,sgmllib
from pathlib import Path
assert feedparser.__version__=='6.0.11'
sdk=Path(feedparser.__file__).parent
pins=json.loads(Path('/app/sdk-pins.json').read_text())
assert {str(p.relative_to(sdk)) for p in sdk.rglob('*.py')}==set(pins)
for p,h in pins.items():assert hashlib.sha256((sdk/p).read_bytes()).hexdigest()==h
assert hashlib.sha256(Path(sgmllib.__file__).read_bytes()).hexdigest()=='9180791aa507111207d7c14f36db574a11fbedda257debfb9d030b273b773f44'
blob=sys.stdin.buffer.read(1048577)
assert len(blob)<=1048576
# For this first arbitrary-bytes stage accept ONLY UTF-8 with optional BOM.
# Fail closed on any DTD/entity declarations. No UTF16/32 obfuscation accepted.
text=blob.decode('utf-8-sig',errors='strict')
assert '\x00'not in text and '<!DOCTYPE'not in text.upper() and '<!ENTITY'not in text.upper()
parsed=feedparser.parse(io.BytesIO(blob))
assert type(parsed.entries)is list and len(parsed.entries)<=1000
assert len(sys.argv)==2
projection=int(sys.argv[1]);assert 1<=projection<=200
rows=[];size=0
for entry in parsed.entries[:projection]:
 row={}
 for k in ('title','link','summary','description','published','updated'):
  v=entry.get(k,None)
  if v is not None:
   assert type(v)is str and len(v)<=10000
   size+=len(v.encode('utf-8'));assert size<=524288
   row[k]=v
 rows.append(row)
wire=json.dumps({'scope':'inactive_arbitrary_utf8_bytes_parser','entries':rows,'entry_count':len(parsed.entries),'bozo':bool(parsed.get('bozo',False)),'input_sha256':hashlib.sha256(blob).hexdigest(),'network_namespace':'loopback_only','delivery':False},ensure_ascii=False).encode()
assert len(wire)<=1048576
sys.stdout.buffer.write(wire)
