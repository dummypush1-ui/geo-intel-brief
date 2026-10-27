"""Default-OFF served-copy search progress. No new server route/cursor effect."""
from pathlib import Path
import hashlib
from flask import request
ROOT=Path(__file__).resolve().parents[1]
FLAG='PUBLIC_NEWS_SEARCH_PROGRESS_ENABLED'
PINS={'integration/ui/workspace.js':'d1c8893753936a8f8b6583ae591c33a9966b5f28cc13af7bf76e0b296f6fab32', 'integration/ui/news_search_progress.js': '7534389119161d9f5c425a50c91e532588160feec818aeaf8ae6b1480452b9ad', 'integration/ui/news_scroll.js': '1fe5950c718c4a7136e853565fc7ec2857ddb209c4ffa01d4278be2165936ea5', 'integration/ui/workspace.html': 'f0947e8b67b2c579f105ce3f24752d96e1d7633718a7ba0972be41b455a8324f', 'integration/news_pages.py': '24d25bb917c72f1601cfa7c1d667e6c6663e42f604a3e0f2db4de2c085cbb9f0'}
PATH='/workspace/assets/news_scroll.js'
WORKSPACE='/workspace/assets/workspace.js'
SEAM='  return r.json();'
REPLACEMENT="""  if(!(r.headers.get('Content-Type')||'').toLowerCase().startsWith('application/json'))throw Error('Invalid search response. Not complete.');
  const reader=r.body.getReader();let count=0,chunks=[];
  try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.byteLength;if(count>1250000)throw Error('Search response too large. Not complete.');chunks.push(value);}}finally{await reader.cancel().catch(()=>{});}
  const bytes=new Uint8Array(count);let pos=0;for(const chunk of chunks){bytes.set(chunk,pos);pos+=chunk.byteLength;}return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));"""

def enabled(env):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise ValueError('Exact search progress flag')
 if value=='true'and env.get('PUBLIC_NEWS_FULL_PAGES_ENABLED')!='true':raise ValueError('Search progress requires whole-store pages')
 return value=='true'
def prepare(env):
 if not enabled(env):return False
 try:
  for name,pin in PINS.items():
   if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin:raise ValueError()
 except Exception:raise ValueError('Search progress source unavailable')from None
 if (ROOT/'integration/ui/workspace.js').read_text().count(SEAM)!=1:raise ValueError('Search byte-bound seam drift')
 return True
def install(app):
 from integration.news_pages import WholeGeoPages
 if type(app.extensions.get('whole_news_pages'))is not WholeGeoPages:raise ValueError('Mounted whole-store pages required')
 if (ROOT/'integration/ui/workspace.js').read_text().count(SEAM)!=1:raise ValueError('Search byte-bound seam drift')
 module=(ROOT/'integration/ui/news_search_progress.js').read_bytes()
 @app.after_request
 def served(r):
  if request.path==PATH and r.status_code==200:
   if request.method=='HEAD':r.headers['Content-Length']=str(len(module))
   else:r.direct_passthrough=False;r.set_data(module)
   for name in ['ETag','Last-Modified','Accept-Ranges']:r.headers.pop(name,None)
  if request.path==WORKSPACE and r.status_code==200:
   r.direct_passthrough=False;text=r.get_data(as_text=True)
   if text.count(SEAM)!=1:raise ValueError('Search byte-bound seam drift')
   transformed=text.replace(SEAM,REPLACEMENT)
   if request.method=='HEAD':r.headers['Content-Length']=str(len(transformed.encode()))
   else:r.set_data(transformed)
   for name in ['ETag','Last-Modified','Accept-Ranges']:r.headers.pop(name,None)
  if request.path=='/workspace'and r.status_code==200 and request.method!='HEAD':
   r.direct_passthrough=False;text=r.get_data(as_text=True)
   text=text.replace('Whole-store read, not a fixed snapshot. Earlier cards leave the screen window as you continue. Refresh to start over. Summary charts and CSV still cover up to 100 stored articles in the selected summary view, not the whole feed.','Search covers the full stored Geo collection by title, summary, source and country text; it does not infer meaning. Results may change during a search. Empty batches can have later matches: keep loading until search says complete. Refresh to start over. Summary charts and CSV remain latest-100 only.')
   r.set_data(text)
  if request.path in (PATH,WORKSPACE,'/workspace'):r.headers['Cache-Control']='no-store'
  return r
 hooks=app.after_request_funcs[None];hooks.remove(served);hooks.insert(0,served)
 app.extensions['news_search_progress']=True
