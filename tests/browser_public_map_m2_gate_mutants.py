import os,sys,threading,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,os.environ.get('M2_BASE',str(ROOT)));import integration;integration.__path__.insert(0,str(ROOT/'integration'))
from integration.news_api import create_app
from integration import public_map_m2 as m
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda _:True);origin='http://127.0.0.1:8789';m.install(app,origin,lambda:{'geo':[]},local_provider=m.LocalProvider());server=make_server('127.0.0.1',8789,app,threaded=True);threading.Thread(target=server.serve_forever,daemon=True).start()
src=(m.ROOT/'map.js').read_text();mutations={'MAX_ACTIVE':('MAX_ACTIVE=4','MAX_ACTIVE=40'),'pause_errors':('this.errors>=3','this.errors>=30'),'pause_window':('this.clock()-this.pauseAt<60000','this.clock()-this.pauseAt<6000'),'failed_skip':('this.failed.has(item.key)','false'),'generation':("item.state!=='active'||item.g!==this.generation","item.state!=='active'")}
# Each target is an isolated state transition; the Gate code is loaded into realChrome via normal map.js route.
cases={
'MAX_ACTIVE':"""let now=0,scheduled=[];const g=new M2Gate(()=>now,(f,n)=>{scheduled.push(n);return 1},()=>{});for(let i=0;i<8;i++)g.add('k'+i,{},()=>()=>{});g.timer=null;scheduled=[];g.pump();if(g.active!==4)throw Error('active cap');if(scheduled.length!==0)throw Error('slots schedule despite active4');""",
'pause_errors':"""let now=0,done=[];const g=new M2Gate(()=>now,()=>1,()=>{});for(let i=0;i<4;i++)g.add('k'+i,{},f=>{done.push(f);return()=>{}});g.pump();done.slice(0,3).forEach(f=>f(false));if(!g.paused||g.jobs.size||g.active)throw Error('third error did not dispose/pause');""",
'pause_window':"""let now=0;const g=new M2Gate(()=>now,()=>1,()=>{});g.pause();now=59999;if(g.resume()!==false||!g.paused)throw Error('early resume');now=60000;if(g.resume()!==true||g.paused)throw Error('boundary resume');""",
'failed_skip':"""let starts=0;const g=new M2Gate(()=>0,()=>1,()=>{});g.failed.add('same');g.add('same',{},()=>{starts++;return()=>{}});g.pump();if(starts||g.active||g.jobs.get('same').state!=='failed')throw Error('failed key retried');""",
'generation':"""let done;const g=new M2Gate(()=>0,()=>1,()=>{});const item=g.add('k',{},f=>{done=f;return()=>{}});g.pump();g.generation++;done(true);if(g.active!==1||item.state!=='active')throw Error('stale generation accepted');"""}
out=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
 for name in ['baseline']+list(mutations):
  script=src if name=='baseline'else src.replace(*mutations[name]);assert name=='baseline'or script!=src
  page=b.new_page();page.route('**/map-fixture/map.js',lambda route:route.fulfill(body=script,content_type='application/javascript'));page.goto(origin+'/workspace/map');page.locator('#load').click();page.wait_for_function('()=>window.__map&&window.M2Gate');assert page.locator('#status').inner_text().startswith('0 country-tagged')
  results={}
  for test,js in cases.items():
   results[test]=page.evaluate('(function(){try{'+js+"return {pass:true};}catch(e){return {pass:false,reason:e.message}}})()")
  if name=='baseline':assert all(x['pass']for x in results.values()),results
  else:assert not results[name]['pass'],(name,results)
  out.append({'variant':name,'map_started_pin_guard_passed':True,'injection':'route fulfillment after server validated unmodified pinned source','tests':results});page.close()
 b.close()
server.shutdown();(Path(os.environ.get('MAP_EVIDENCE_DIR','/tmp/public-map-m2-evidence'))/'browser-gate-mutants.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
