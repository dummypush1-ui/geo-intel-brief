"""D3a dormant UI fixtures only. No API, source/model or builder wiring."""
from pathlib import Path
PATHS=frozenset(('/workspace/code-news-coverage','/workspace/assets/code_news_coverage.js','/workspace/assets/code_news_coverage.css','/workspace/assets/code_news_contract.js'))
def enabled(env):
 value=env.get('PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED','false')
 if value not in ('true','false'):raise ValueError('Exact coverage UI flag')
 return value=='true'
def install(app,env=None,*,coverage_available=False):
 if not enabled(env or {}):return
 from flask import Response,request
 root=Path(__file__).resolve().parent/'ui'
 @app.get('/workspace/code-news-coverage')
 def coverage_shell():
  if request.method=='HEAD':return Response(status=200)
  html=(root/'code_news_coverage.html').read_text().replace('data-coverage-available="false"','data-coverage-available="true"'if coverage_available else'data-coverage-available="false"')
  from integration.news_finder_navigation_prep import enabled as finder_links_enabled
  if finder_links_enabled(env or {}):
   html=html.replace('<main data-coverage-available=', '<main data-finder-links="true" data-coverage-available=',1).replace('<span class="badge">Finder link unavailable</span>','<span id="finder-navigation" class="badge">Finder link unavailable</span>',1)
  return Response(html,mimetype='text/html')
 @app.get('/workspace/assets/code_news_coverage.js')
 def coverage_js():
  if request.method=='HEAD':return Response(status=200)
  from integration.news_finder_navigation_prep import enabled as finder_links_enabled
  name='code_news_finder_navigation.js' if finder_links_enabled(env or {}) else 'code_news_coverage.js'
  return Response((root/name).read_text(),mimetype='application/javascript')
 @app.get('/workspace/assets/code_news_coverage.css')
 def coverage_css():
  if request.method=='HEAD':return Response(status=200)
  return Response((root/'code_news_coverage.css').read_text(),mimetype='text/css')
 @app.get('/workspace/assets/code_news_contract.js')
 def coverage_contract():
  if request.method=='HEAD':return Response(status=200)
  from integration.code_news_coverage_contract_prep import script
  return Response(script(),mimetype='application/javascript')
 @app.after_request
 def coverage_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='no-referrer'
   response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; object-src 'none'"
  return response
 hooks=app.after_request_funcs[None];hooks.remove(coverage_headers);hooks.insert(0,coverage_headers)
