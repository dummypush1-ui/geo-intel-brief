"""Explicit device opt-in for one exact F9 safe render; default OFF."""
import hashlib,json,re,base64
from dataclasses import dataclass
from pathlib import Path
from flask import Response,request
from integration.finder_composition_f9 import Selection,selected
FLAG='PUBLIC_FINDER_DEVICE_CACHE_ENABLED';KEY='finder_device_f10'
ROOT=Path(__file__).resolve().parent
class Held(ValueError):pass
@dataclass(frozen=True)
class Device:
 selection:Selection
 digest:str
 size:int
 @property
 def base(self):return '/workspace/finder/device/'+self.digest+'/'
 @property
 def paths(self):return frozenset(self.base+n for n in ('','control.js','worker.js','snapshot.html','manifest.webmanifest'))
 @property
 def cache(self):return 'geo-finder-device-f10-'+self.digest
 def verify(self):
  self.selection.verify()
  expected=next(pin for name,size,pin in self.selection.binding.files if name=='review/public-offline.html')
  raw=self.selection.rendered.encode()
  if self.selection.report_enabled:expected=hashlib.sha256(self.selection.rendered.encode()).hexdigest()
  if len(raw)!=self.size or hashlib.sha256(raw).hexdigest()!=self.digest or self.digest!=expected:raise Held('Exact safe render required')
def prepare(env,selection=None):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise Held('Exact device-cache flag required')
 if flag=='false':return None
 if type(selection)is not Selection:raise Held('Exact selected Finder edition required')
 raw=selection.rendered.encode();device=Device(selection,hashlib.sha256(raw).hexdigest(),len(raw))
 if not 1<=device.size<=24*1024*1024:raise Held('Bounded public snapshot required')
 device.verify();return device

def config(device):return dict(base=device.base,digest=device.digest,size=device.size,cache=device.cache)
def script(name,device):
 text=(ROOT/name).read_text();seam='/*F10_CONFIG*/'
 if text.count(seam)!=1:raise Held('Device asset config seam drift')
 return text.replace(seam,'const CFG='+json.dumps(config(device),separators=(',',':'))+';',1)
def install(app,device):
 if type(device)is not Device or KEY in app.extensions or selected(app)is not device.selection:raise Held('One matching device selection per app required')
 device.verify()
 scripts={n:script(n,device)for n in ('control.js','worker.js')}
 app.extensions[KEY]=device
 def serve(name):
  if request.method=='HEAD':return Response(status=200,mimetype='text/html'if name in ('','snapshot.html')else'application/javascript'if name.endswith('.js')else'application/manifest+json')
  try:device.verify()
  except Exception:return Response('Public device snapshot unavailable.',503,mimetype='text/plain')
  if name in scripts:return Response(scripts[name],mimetype='application/javascript')
  if name=='snapshot.html':return Response(device.selection.rendered,mimetype='text/html')
  if name=='manifest.webmanifest':return Response(json.dumps(dict(name='Offline public Finder',short_name='Offline Finder',id=device.base,start_url=device.base+'snapshot.html',scope=device.base,display='standalone',icons=[])),mimetype='application/manifest+json')
  return Response('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Store public Finder</title><link rel="manifest" href="manifest.webmanifest"><style>body{font:17px system-ui;line-height:1.6;max-width:40rem;margin:2rem auto;padding:0 1rem;color:#17243a}button,a{font:inherit}button{padding:.7rem;margin:.3rem .3rem .3rem 0}code{overflow-wrap:anywhere}p{overflow-wrap:anywhere}</style></head><body><h1>Public Finder on this device</h1><p>This stores only the selected public, network-disabled Finder snapshot in this browser. It does not store private news, provider keys, notes or AI answers.</p><p>Save is optional. No worker or snapshot cache is created until you choose Save. Once saved, the browser may check the installed worker for updates. Storage may be cleared or evicted by the browser; this is not a permanent backup.</p><button id="save">Save public snapshot</button><button id="clear">Clear this snapshot</button><p id="status" role="status">Not saved by this page.</p><p><a href="snapshot.html">Open this public snapshot</a></p><p>Edition/render identity: <code>'''+device.digest+'''</code></p><p>Clear removes only this snapshot's worker and cache. Other editions, browser keys and notes are unchanged. To remove a different edition, open its own storage page.</p><script src="control.js"></script></body></html>''',mimetype='text/html')
 for name in ('','control.js','worker.js','snapshot.html','manifest.webmanifest'):
  app.add_url_rule(device.base+name,'finder_device_f10_'+(name or'home'),lambda name=name:serve(name),methods=['GET','HEAD'])
 @app.after_request
 def headers(response):
  if request.path=='/workspace'and response.status_code==200:
   response.direct_passthrough=False;text=response.get_data(as_text=True)
   if text.count('</nav>')!=1:raise Held('Workspace device-link seam drift')
   response.set_data(text.replace('</nav>','<a href="'+device.base+'">Store public Finder</a></nav>',1))
  if request.path not in device.paths:return response
  response.headers['Cache-Control']='no-store';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Content-Type-Options']='nosniff'
  if request.path==device.base+'worker.js':response.headers['Service-Worker-Allowed']=device.base
  if request.path==device.base+'snapshot.html'and response.status_code==200:
   if request.method!='HEAD':response.set_data(device.selection.rendered)
   hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in re.findall(r'<script>(.*?)</script>',device.selection.rendered,re.S|re.I))
   response.headers['Content-Security-Policy']="default-src 'none'; script-src "+hashes+"; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'none'"
   response.headers['X-Finder-Device-Snapshot']=device.digest
  else:response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; worker-src 'self'; manifest-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
  return response

 # Final snapshot headers must run after generic private_response hooks.
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
