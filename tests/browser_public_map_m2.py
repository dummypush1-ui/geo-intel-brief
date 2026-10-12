import os
import sys,threading,json,random,time,base64,os,importlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path(os.environ.get('M2_BASE',str(ROOT)));sys.path.insert(0,str(BASE))
import integration
integration.__path__.insert(0,str(ROOT/'integration'))
from integration.news_api import create_app
from integration import public_map_m2 as m
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from flask import Response
out=Path(os.environ.get('MAP_EVIDENCE_DIR','/tmp/public-map-m2-evidence'));out.mkdir(parents=True,exist_ok=True);seed=int(sys.argv[1])if len(sys.argv)>1 else 11;steps=int(sys.argv[2])if len(sys.argv)>2 else 60
raw={'geo':[{'title':'India <img src=x onerror=alert(1)>','country':'India','source':'Fixture','url':'https://news.example.com/a'},{'title':'Congo ambiguous','country':'Congo','source':'Fixture','url':'https://news.example.com/b'}]}
app=create_app(authorize=lambda _:True);origin='http://127.0.0.1:8789';m.install(app,origin,lambda:raw,local_provider=m.LocalProvider());mode=['ok'];png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==')
@app.get('/workspace/map-fixture/tiles/<int:z>/<int:x>/<int:y>.png')
def tile(z,x,y):
 if mode[0]=='error':return Response('localerror',status=503)
 if mode[0]=='timeout':time.sleep(.4)
 return Response(png,mimetype='image/png',headers={'Cache-Control':'public,max-age=604800'})
server=make_server('127.0.0.1',8789,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start();rng=random.Random(seed);history=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=b.new_page(viewport={'width':1100,'height':844});csp=[];errors=[];external=[]
 page.on('console',lambda v:csp.append(v.text)if'violates'in v.text or'Content Security Policy'in v.text else None);page.on('pageerror',lambda v:errors.append(str(v)));page.on('request',lambda r:external.append(r.url)if not r.url.startswith(origin)else None)
 page.add_init_script("window.__timeouts=[];const original=window.setTimeout;window.setTimeout=(fn,n,...args)=>{if(n===10000){__timeouts.push(fn);return original(fn,n,...args);}return original(fn,n,...args);};")
 page.goto(origin+'/workspace/map');page.locator('#load').click();page.wait_for_function('()=>window.__map');page.wait_for_function('()=>document.querySelectorAll("#articles article").length===2');assert page.locator('#articles img').count()==0
 for width in [390,1100]:
  page.set_viewport_size({'width':width,'height':844});page.evaluate('__map.invalidateSize();__map.setView([20,80],2,{animate:false});void 0');page.wait_for_timeout(400);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'm2-reference-{width}.png'),full_page=True)
 page.evaluate('window.__testNow=0;__gate.clock=()=>__testNow')
 def audit():
  v=page.evaluate('__audit()');assert v['dom']<=64 and v['dom']==v['tiles']==v['jobs']==v['levels'],v;assert v['active']==v['activeJobs']<=4 and v['queue']<=64 and not v['outside']and not v['detached']and not v['srcOutside'],v
  starts=v['starts']; groups={}
  for x in starts:groups[x['at']]=groups.get(x['at'],0)+1
  assert all(n<=4 for n in groups.values()),groups
  times=sorted(groups);assert all(b-a>=1000 for a,b in zip(times,times[1:])),times
  if v['hidden']or v['paused']:assert v['jobs']==v['active']==v['queue']==0,v
  model=page.evaluate('(()=>{const t=__layer?Object.values(__layer._tiles):[];return t.map(x=>({key:x.coords.z+"/"+x.coords.x+"/"+x.coords.y,state:x.el._record?.state,same:__gate.jobs.get(x.el._record?.key)===x.el._record,src:x.el.getAttribute("src"),handlers:!!(x.el.onload||x.el.onerror)}))})()')
  assert len({x['key']for x in model})==len(model)and all(x['same']for x in model),model
  for x in model:
   assert x['state']in ['queued','active','loaded','failed'],x
   assert x['handlers']==(x['state']=='active'),x
   if x['state']in ['queued','failed']:assert x['src']is None,x
   else:assert x['src']=='/workspace/map-fixture/tiles/'+x['key']+'.png',x
  return v
 def settle():
  for _ in range(80):
   page.evaluate('__testNow+=1001;__gate.pump()');page.wait_for_timeout(40);v=audit()
   if v['active']==0 and v['queue']==0:break
  assert not v['active']and not v['queue'],{k:v[k]for k in v if k!='starts'}
  assert all(s in('loaded','failed')for s in v['states']),v
  return v
 page.locator('#tiles').click();settle()
 for action in ['__map.zoomIn()','__map.zoomIn()','__map.zoomIn()','__map.panBy([500,0],{animate:false})','__map.panBy([-500,0],{animate:false})']:
  page.evaluate(action+";void 0");audit();page.wait_for_timeout(510);settle()
 for i in range(steps):
  action=rng.choice(['pan','zoom','resize','hide','show','error','timeout'])
  if action=='pan':page.evaluate(f'__map.panBy([{rng.choice([-400,400])},0],{{animate:false}});void 0')
  elif action=='zoom':page.evaluate(f'__map.setZoom({rng.randint(2,8)});void 0')
  elif action=='resize':page.set_viewport_size({'width':rng.choice([390,1100,1600]),'height':844});page.evaluate('__map.invalidateSize();void 0')
  elif action=='hide':page.evaluate('__visibility(false)')
  elif action=='show':page.evaluate('__visibility(true);__testNow+=61000;__activate()')
  else:
   mode[0]=action;page.evaluate('__testNow+=61000;__activate()')
   if action=='timeout':page.evaluate('__gate.pump();for(const f of __timeouts.splice(0))f()')
  audit();page.wait_for_timeout(510);v=settle();history.append({'step':i,'action':action,**{k:v[k]for k in ['dom','active','queue','jobs','paused','hidden']}});mode[0]='ok'
  if v['paused']:page.evaluate('__testNow+=61000;__activate()');settle()
 page.evaluate('__visibility(false)');page.wait_for_timeout(450);audit();assert not csp,csp;assert not errors,errors;assert not external,external
 page.screenshot(path=str(out/f'm2-{seed}.png'),full_page=True);b.close()
server.shutdown();(out/f'fuzz-{seed}.json').write_text(json.dumps({'seed':seed,'steps':steps,'history':history,'csp':csp,'errors':errors,'external':external,'m1_repro':True},indent=2));print('PASS',seed,steps)
