"""232 cached-local served-copy CSV/shortlist probe, synthetic session data only."""
import sys,threading,json,os,csv,io,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server,WSGIRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('OFFLINE232_OUT','/tmp/offline232-review'));OUT.mkdir(parents=True,exist_ok=True);BEFORE=os.environ.get('OFFLINE232_BEFORE')=='1'
class Quiet(WSGIRequestHandler):
 def log_request(self,*a,**k):pass
server=make_server('127.0.0.1',0,create_app(authorize=lambda r:True),request_handler=Quiet);O='http://127.0.0.1:'+str(server.server_port);threading.Thread(target=server.serve_forever,daemon=True).start()
notes=['ordinary','="formula"','+1','-3','@foo','\tfoo','\rfoo','\nfoo','\u200b=1','nul\0value','bad\ud800','astral 😀 quote " comma,\nline'];result={'phase':'BEFORE232'if BEFORE else'AFTER232','started_at':datetime.now(timezone.utc).isoformat(),'synthetic_only':True,'captures':[],'outbound_successes':0};failures=[]
try:
 with sync_playwright()as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);result['chromium']=b.version
  c=b.new_context(viewport={'width':1100,'height':900},accept_downloads=True,timezone_id='Asia/Kolkata');c.add_init_script("{const D=Date;window.Date=class extends D{constructor(...a){super(...(a.length?a:[1791576000000]));}static now(){return 1791576000000;}};Math.random=()=>0.25;window.__writes=[];for(const n of ['setItem','removeItem','clear']){const f=Storage.prototype[n];Storage.prototype[n]=function(...a){window.__writes.push(n);return f.apply(this,a)}}}")
  outside=[];errors=[];violations=[];c.route('**/*',lambda r:r.continue_()if r.request.url.startswith(O+'/')else(outside.append({'method':r.request.method,'host':r.request.url.split('/')[2]}),r.abort()));page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:violations.append(m.text)if'Content Security Policy'in m.text else None)
  page.goto(O+'/workspace/finder/index.html#code=0:090121');page.locator('#d-short').wait_for();page.evaluate("async()=>{await caches.open('geo-public-finder-c100d1017b7c-v1');await caches.open('geo-public-finder-TEST-old');await caches.open('unrelated-TEST');}")
  page.locator('#finder-offline-save').click();page.locator('#finder-offline-status').filter(has_text='Public snapshot stored').wait_for(timeout=40000);page.wait_for_function('navigator.serviceWorker.controller!==null')
  result['cache_keys']=page.evaluate('caches.keys()');expected='geo-public-finder-'+hashlib.sha256(create_app(authorize=lambda r:True).test_client().get('/workspace/finder/offline.html').data).hexdigest()[:12]+'-v1';result['cache_id_derivation_matches']=expected in result['cache_keys']
  if not BEFORE:assert result['cache_id_derivation_matches'] and set(result['cache_keys'])=={expected,'unrelated-TEST'}
  c.set_offline(True);page.goto(O+'/workspace/finder/offline.html#code=0:090121');page.locator('#d-short').wait_for(timeout=40000);assert page.evaluate('V.apiKey===""&&S.shortlist.length===0&&Object.keys(S.notes).length===0')
  # Only synthetic in-memory fixture entries/notes; all rendering and downloads use original handlers.
  keys=page.evaluate('Array.from(S.db.keyToIdx.keys()).slice(0,12)');page.evaluate('(x)=>{S.shortlist=x.keys;S.notes=Object.fromEntries(x.keys.map((k,i)=>[k,x.notes[i]]));paintShortlist();}',{'keys':keys,'notes':notes})
  with page.expect_download()as d:page.locator('#sl-csv').click()
  assert d.value.suggested_filename=='hsn-shortlist.csv';d.value.save_as(str(OUT/'offline.csv'));rows=list(csv.reader(io.StringIO((OUT/'offline.csv').read_bytes().decode('utf-8-sig').replace('\0','NUL_FIXTURE'))));assert rows[0]==['System','Code','Description','Open duty / rate','Note','Source']and len(rows)==13
  for r in rows:r[4]=r[4].replace('NUL_FIXTURE','\0')
  result['export_notes']=[r[4]for r in rows[1:]];result['filename']=d.value.suggested_filename;result['csv_sha256']=hashlib.sha256((OUT/'offline.csv').read_bytes()).hexdigest()
  expected_notes=['ordinary','\'="formula"',"'+1","'-3","'@foo","'\tfoo","'\rfoo","'\nfoo","'\u200b=1",'nulvalue','bad�','astral 😀 quote " comma,\nline']
  for i,(got,want)in enumerate(zip(result['export_notes'],expected_notes)):
   if got!=want:failures.append({'kind':'CSV','row':i,'actual':got,'expected':want})
  for width in [320,390,1100]:
   page.set_viewport_size({'width':width,'height':900})
   for theme in ['light','dark']:
    page.evaluate('(t)=>{S.theme=t;V.dark=t==="dark";document.documentElement.classList.toggle("dark-mode",V.dark);}',theme)
    region=page.locator('.finder-shortlist-scroll');has=region.count()==1
    page.locator('#sl-print').focus();page.keyboard.press('Tab');focused=has and region.evaluate('e=>document.activeElement===e')
    if has:
     region.evaluate('e=>e.scrollLeft=0');region.press('ArrowRight')
     if region.evaluate('e=>e.scrollWidth>e.clientWidth'):page.wait_for_function('()=>document.querySelector(".finder-shortlist-scroll").scrollLeft>0')
    geom=page.evaluate('()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,region:!!document.querySelector(".finder-shortlist-scroll"),focused:document.activeElement?.className,accessible:document.querySelector(".finder-shortlist-scroll")?.getAttribute("aria-label"),keyboardScroll:document.querySelector(".finder-shortlist-scroll")?.scrollLeft||0})');result['captures'].append({'width':width,'theme':theme,'geometry':geom,'tab_focus':focused});page.screenshot(path=str(OUT/f'shortlist-{width}-{theme}.png'),full_page=True)
    if has and region.evaluate('e=>e.scrollWidth>e.clientWidth'):
     region.press('End');page.wait_for_function('()=>{const e=document.querySelector(".finder-shortlist-scroll");return e.scrollLeft>=e.scrollWidth-e.clientWidth-1}');page.screenshot(path=str(OUT/f'shortlist-{width}-{theme}-end.png'),full_page=True)
    if not has or not focused or geom['scroll']>width:failures.append({'kind':'geometry','width':width,'theme':theme})
  assert page.evaluate('window.__writes.length')==0
  page.reload();page.locator('#d-short').wait_for();assert page.evaluate('S.shortlist.length===0&&Object.keys(S.notes).length===0&&V.apiKey===""');assert page.evaluate('window.__writes.length')==0;result['fresh_page_reset']=True
  c.set_offline(False);page.goto(O+'/workspace/finder/index.html#code=0:090121');page.locator('#d-short').wait_for();page.evaluate('(x)=>{S.shortlist=x.keys;S.notes=Object.fromEntries(x.keys.map((k,i)=>[k,x.notes[i]]));paintShortlist();}',{'keys':keys,'notes':['ordinary']*12})
  with page.expect_download()as d:page.locator('#sl-csv').click()
  d.value.save_as(str(OUT/'online-normal.csv'));online=list(csv.reader(io.StringIO((OUT/'online-normal.csv').read_bytes().decode('utf-8-sig'))));assert online[0]==rows[0]and online[1]==rows[1];assert all(a[:4]+a[5:]==z[:4]+z[5:]for a,z in zip(rows[1:],online[1:]));result['normal_online_differential']=True
  page.locator('#finder-offline-clear').click();page.locator('#finder-offline-status').filter(has_text='cleared').wait_for();assert page.evaluate('caches.keys()')==['unrelated-TEST'];assert page.evaluate('navigator.serviceWorker.getRegistrations().then(x=>x.length)')==0
  result['errors']=errors;result['violations']=violations;result['unexpected_external']=outside;assert not errors and not outside;assert all(('connect-src'in x or 'Refused to connect'in x)and('frankfurter'in x.lower())for x in violations),violations;b.close()
finally:server.shutdown()
result['failures']=failures;result['finished_at']=datetime.now(timezone.utc).isoformat();(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'phase':result['phase'],'failures':len(failures)}));assert not failures,failures
