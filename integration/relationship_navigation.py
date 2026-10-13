"""Manual public supplied-page relationship bridge. Private source stays intact.
Install validates exact assets and seams before exposing transformed controls.
"""
import hashlib
from pathlib import Path
from flask import request, Response

ROOT=Path(__file__).resolve().parents[1]
FLAG='PUBLIC_RELATIONSHIP_NAV_ENABLED'
ASSET='/workspace/assets/relationship_navigation.js'
PINS={'integration/ui/workspace.js':'d1c8893753936a8f8b6583ae591c33a9966b5f28cc13af7bf76e0b296f6fab32',
      'integration/ui/relationship_navigation.js':'cea24f932c418cf2b2c5a373784b438911b852977005a0a485be228b89447e4d'}


SHELLS={
 '/workspace/countries':('integration/ui/countries.html','</nav>'),
 '/workspace/weekly':('integration/ui/weekly.html','</nav>'),
 '/workspace/weather':('integration/ui/weather.html','</nav>'),
 '/workspace/brics-streams':('integration/ui/public_brics_streams.html','</main>'),
 '/workspace/ai-answers':('integration/ui/public_ai_answers.html','</main>'),
 '/workspace/code-news':('integration/ui/code_news.html','</main>'),
}
MAP_SHELLS=('integration/ui/map.html','integration/public_map_prep/map.html','integration/public_map_m2/map.html')
PINS['integration/ui/workspace.html']='f0947e8b67b2c579f105ce3f24752d96e1d7633718a7ba0972be41b455a8324f'
PINS.update({'integration/ui/countries.html': '510907a12cdc096394a4fa8ad4c167efedf88a7a3dcee517e9cee2fad42689c1', 'integration/ui/weekly.html': '18a7dac2b8854d3bd51146d9ac6ed55c9146d0ae6bc7b7d39c557c7519eb2faa', 'integration/ui/weather.html': 'bafaebe34da0eb46e8455b403543561aa64162768e5de6993784e580124dacda', 'integration/ui/public_brics_streams.html': 'a509bc1dbcfe91213550ad38a793b7b31032b083bba40eaa16a6dbd0400adcf5', 'integration/ui/public_ai_answers.html': 'bb202082ced19a2c252cfc86f04e785c6ad82ddedc242713c7ae5008a0d97109', 'integration/ui/code_news.html': 'fb54dec26cf025f62bf2bf3ed501dd1cd21c0e9ef09fbc7e7532a70c64d39f3f', 'integration/ui/map.html': 'fd07ccd0bb3d81a03e6f29e170c9b0ef411ab68b64b20689a9d29293c127a7dd', 'integration/public_map_prep/map.html': '121260e7aef529bcecbd6acaf646e7e682c25755b18c7975563779b5515db603', 'integration/public_map_m2/map.html': 'e683a88f437a2ca0c34ccb5337cba14ce9d93ca0fc2875c25f5204bb4f0e9e2b'})

def enabled(env):
    value=env.get(FLAG,'false')
    if value not in ('true','false'):raise ValueError('Exact relationship navigation flag')
    if value=='true' and env.get('PUBLIC_CODE_NEWS_ENABLED')!='true':
        raise ValueError('Relationship navigation requires public code-news')
    return value=='true'


def transform(source):
    start="    if(article.article_key && ['geo','brics'].includes(article.project)) {"
    end='    container.append(row);'
    begin='async function syncContext() {'
    finish="frame.addEventListener('load', () => {"
    for seam in (start,end,begin,finish):
        if source.count(seam)!=1:raise ValueError('Relationship asset seam drift')
    a=source.index(start);b=source.index(end,a)
    source=source[:a]+'''    if(article.article_key && article.project==='geo') {
      attachReportedCodes(row,article,frame);
    }
'''+source[b:]
    a=source.index(begin);b=source.index(finish,a)
    source=source[:a]+'''function syncContext() {
  manualFinderContext(frame,byId('related'),byId('related-status'),byId('context'));
}
'''+source[b:]
    if '/api/related-news' in source or '/api/finder-context' in source:
        raise ValueError('Private relationship path remains')
    load_start="frame.addEventListener('load', () => {"
    load_end='\nasync function readStats'
    if source.count(load_start)!=1 or source.count(load_end)!=1:raise ValueError('Frame lifecycle seam drift')
    a=source.index(load_start);b=source.index(load_end,a)
    lifecycle="""
let finderDetach=()=>{};
function bindFinderContext(){
 finderDetach();resetFinderContext();
 let doc,win;try{doc=frame.contentDocument;win=frame.contentWindow;if(!doc?.body)return;}catch{return;}
 let raf=0;const queue=()=>{if(!raf)raf=requestAnimationFrame(()=>{raf=0;syncContext();});};
 const observer=new MutationObserver(queue);observer.observe(doc.body,{childList:true,subtree:true});
 const input=e=>{if(e.target.id==='q-main')queue();};
 win.addEventListener('hashchange',queue);doc.addEventListener('input',input);
 const detach=()=>{observer.disconnect();cancelAnimationFrame(raf);win.removeEventListener('hashchange',queue);doc.removeEventListener('input',input);win.removeEventListener('pagehide',detach);resetFinderContext();};
 win.addEventListener('pagehide',detach,{once:true});finderDetach=detach;syncContext();
}
frame.addEventListener('load',bindFinderContext);
window.addEventListener('pagehide',()=>finderDetach(),{once:true});
if(frame.contentDocument?.readyState==='complete')bindFinderContext();
"""
    source=source[:a]+lifecycle+source[b:]
    return "import {attachReportedCodes,manualFinderContext,resetFinderContext} from './relationship_navigation.js';\n"+source



def prepare(env):
    if not enabled(env):return False
    try:
        for name,pin in PINS.items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin:raise ValueError()
        transform((ROOT/'integration/ui/workspace.js').read_text())
        if (ROOT/'integration/ui/workspace.html').read_text().count('</nav>')!=1:raise ValueError('Workspace seam drift')
        for name,seam in SHELLS.values():
            if (ROOT/name).read_text().count(seam)!=1:raise ValueError('Shell seam drift')
        for name in MAP_SHELLS:
            if (ROOT/name).read_text().count('</nav>')!=1:raise ValueError('Map seam drift')
    except Exception:raise ValueError('Relationship source unavailable')from None
    return True


def install(app,origin):
    from integration.news_finder_navigation_prep import mounted
    if 'code_news_public' not in app.extensions or not mounted(app):
        raise ValueError('Relationship navigation mounts unavailable')
    raw=(ROOT/'integration/ui/workspace.js').read_text()
    transformed=transform(raw)
    module=(ROOT/'integration/ui/relationship_navigation.js').read_text()
    @app.get(ASSET)
    def asset():
        return Response('' if request.method=='HEAD' else
                        module,
                        mimetype='application/javascript',headers={'Content-Length':str(len(module.encode('utf-8')))})
    @app.after_request
    def served_copy(response):
        if request.method=='HEAD' and response.status_code==200:
            if request.path==ASSET:response.headers['Content-Length']=str(len(module.encode('utf-8')))
            elif request.path=='/workspace/assets/workspace.js':response.headers['Content-Length']=str(len(transformed.encode('utf-8')))
            elif request.path in set(SHELLS)|{'/workspace','/workspace/map'}:response.headers.pop('Content-Length',None);response.automatically_set_content_length=False
        if request.path=='/workspace/assets/workspace.js' and response.status_code==200 and request.method!='HEAD':
            response.direct_passthrough=False;response.set_data(transformed)
        if request.path=='/workspace' and response.status_code==200 and request.method!='HEAD':
            response.direct_passthrough=False;text=response.get_data(as_text=True)
            if text.count('</nav>')!=1:raise ValueError('Workspace navigation seam drift')
            text=text.replace('Open a code in Finder to see matching news. A country or product mention is context, not proof of a tariff change.','Manual Geo latest-100 reported mentions only. BRICS rows have no relationship button. A reported mention is not proof of classification or a tariff change.')
            text=text.replace('</nav>','<a href="/workspace/code-news">Reported code-news</a></nav>',1)
            # API availability derives from mounted broker at request time.
            if app.extensions.get('code_news_coverage_broker') is not None:
                text=text.replace('</nav>','<a href="/workspace/code-news-coverage">Whole-store code coverage</a></nav>',1)
            response.set_data(text)
        if request.path in set(SHELLS)|{'/workspace/map'} and response.status_code==200 and request.method!='HEAD':
            response.direct_passthrough=False;text=response.get_data(as_text=True)
            seam=SHELLS[request.path][1] if request.path in SHELLS else '</nav>'
            if text.count(seam)!=1:raise ValueError('Feature navigation seam drift')
            text=text.replace(seam,'<a href="/workspace/code-news">Reported code-news</a>'+seam,1)
            response.set_data(text)
        if request.path in {ASSET,'/workspace/assets/workspace.js'}:
            for name in ['ETag','Last-Modified','Accept-Ranges']:response.headers.pop(name,None)
        if request.path==ASSET:
            response.headers['Cache-Control']='no-store'
            response.headers['Referrer-Policy']='no-referrer'
            response.headers['X-Content-Type-Options']='nosniff'
        return response
    # Run after builder served-copy disable seam has executed, and keep feature
    # policies installed earlier authoritative for their own routes.
    hooks=app.after_request_funcs[None];hooks.remove(served_copy);hooks.insert(0,served_copy)
    app.extensions['relationship_navigation']=True
