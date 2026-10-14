"""Default-OFF unconnected BRICS news page. Fixtures injected only in tests."""
from pathlib import Path
import hashlib,json
from flask import request,Response,jsonify
from integration.brics_news_boundary import Service
ROOT=Path(__file__).resolve().parents[1]
FLAG='PUBLIC_BRICS_NEWS_ENABLED'
PAGE='/workspace/brics-news';API='/api/brics/news';ASSET='/workspace/assets/public_brics_news.js';PATHS=frozenset((PAGE,API,ASSET))
PINS={'integration/brics_news_boundary.py': 'c206b85a9896b908a4fe0543417f86a6ebea4e14b99eb2d078e66da98a2ec700', 'integration/ui/public_brics_news.html': '56827dcb16eeeba407473fc6cea9f3a1e519d4c0c77c5bb4a5948213738eda86', 'integration/ui/public_brics_news.js': 'c8410f4d25ce695af366b67ea45c49976dce05d346b15d3cbcd9104fed72dacd', 'integration/brics_processing_offline.py': '049546d8e83a0db291b04b7741db09cd5468bd9dd2d2e9dc284b0bb1ffd73345', 'integration/text_matching/matcher.py': 'eb9bdc9b113d36da34702ed724ea857ebcfc9649131fdeafe7add3138d2db607', 'integration/ui/workspace.html': 'f0947e8b67b2c579f105ce3f24752d96e1d7633718a7ba0972be41b455a8324f'}
def prepare(env):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise ValueError('Exact BRICS news flag required')
 if value=='false':return False
 if env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise ValueError('Public BRICS composition required')
 try:
  if (ROOT/'integration/ui/workspace.html').read_text().count('</nav>')!=1:raise ValueError('BRICS news nav seam drift')
  for name,pin in PINS.items():
   if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin:raise ValueError()
 except Exception:raise ValueError('BRICS news source unavailable')from None
 return True
def install(app,origin,fixture=None,geo_identity=None):
 if any(r.rule in PATHS for r in app.url_map.iter_rules()):raise ValueError('Duplicate BRICS news mount')
 service=Service(fixture,geo_identity=geo_identity)
 def shell():return Response('' if request.method=='HEAD'else(ROOT/'integration/ui/public_brics_news.html').read_text(),mimetype='text/html')
 def listing():
  if request.method=='HEAD':return Response('',mimetype='application/json')
  value,status=service.run();return Response(json.dumps(value,ensure_ascii=True,separators=(',',':')),status=status,mimetype='application/json')
 def asset():return Response(''if request.method=='HEAD'else(ROOT/'integration/ui/public_brics_news.js').read_text(),mimetype='application/javascript')
 for path,endpoint,view in [(PAGE,'public_brics_news_page',shell),(API,'public_brics_news_get',listing),(ASSET,'public_brics_news_asset',asset)]:app.add_url_rule(path,endpoint,view,methods=['GET','HEAD'])
 @app.before_request
 def guard():
  if request.path not in PATHS:return
  if request.host_url.rstrip('/')!=origin or request.method not in ('GET','HEAD'):return jsonify(state='unavailable'),403
  if request.query_string:return jsonify(state='bad_request'),400
 @app.after_request
 def headers(r):
  if request.path in PATHS:
   r.headers['Cache-Control']='no-store';r.headers['Referrer-Policy']='no-referrer';r.headers['X-Content-Type-Options']='nosniff';r.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
  if request.path=='/workspace'and r.status_code==200 and request.method!='HEAD' and mounted(app):
   r.direct_passthrough=False;s=r.get_data(as_text=True)
   if s.count('</nav>')!=1:raise ValueError('BRICS news nav seam drift')
   r.set_data(s.replace('</nav>',f'<a href="{PAGE}">BRICS news</a></nav>'))
  return r
 hooks=app.after_request_funcs[None];hooks.remove(headers);hooks.insert(0,headers)
 app.extensions.update(public_brics_news=service,public_brics_news_view=shell)
def mounted(app):return type(app.extensions.get('public_brics_news'))is Service and app.view_functions.get('public_brics_news_page')is app.extensions.get('public_brics_news_view') and any(r.rule==PAGE and r.endpoint=='public_brics_news_page' and r.methods=={'GET','HEAD','OPTIONS'} for r in app.url_map.iter_rules())
