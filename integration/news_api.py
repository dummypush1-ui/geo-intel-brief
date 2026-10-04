"""Fixture-backed private staging API. Never imports a live legacy app."""
from flask import Flask,request,jsonify,send_from_directory,Response
from pathlib import Path
from collections import Counter
import re,hashlib,base64
from integration.news_view import views
from integration.relevance import match
from integration.story_links import groups
from integration.finder_links import finder_link
from integration.dashboard_model import loaded_stats
from integration.loaded_news import selection,sample_csv
from integration.loaded_charts import loaded_chart
from integration.critical_stories import critical_stories
from integration.country_page import country_page
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration.source_health import SourceHealthSnapshot
from datetime import datetime,timezone
from integration.dashboard_snapshots import DashboardSnapshots
from integration.branding_meta import brand_head,valid_origin

def create_app(reader=None,authorize=None,finder_context_reader=None,finder_base=None,finder_index_verified=False,allowed_origin=None,branding_public_base=None,dashboard_snapshot_reader=None,source_health_snapshot=None,tariff_evidence_snapshot=None):
 branding_public_base=valid_origin(branding_public_base)
 app=Flask(__name__)
 root=Path(__file__).resolve().parents[1]
 @app.after_request
 def private_response(response):
  response.headers['Cache-Control']='no-store'
  response.headers['X-Robots-Tag']='noindex, nofollow'
  if response.status_code==200 and response.mimetype=='text/html':
   response.direct_passthrough=False
   response.set_data(brand_head(response.get_data(as_text=True),branding_public_base))
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['Referrer-Policy']='same-origin'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  if request.path=='/workspace' and response.status_code==200:
   response.headers['Content-Security-Policy']+="; frame-src 'self' https://www.youtube-nocookie.com"
  if request.path.startswith('/workspace/finder/') and response.mimetype=='text/html' and response.status_code==200:
   response.direct_passthrough=False
   scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',response.get_data(as_text=True),flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
   hashes=['\'sha256-'+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+'\'' for s in scripts]
   response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' "+' '.join(hashes)+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  return response
 @app.get('/workspace')
 def workspace():return send_from_directory(root/'integration/ui','workspace.html')
 @app.get('/workspace/assets/<name>')
 def assets(name):
  if name not in ('workspace.js','workspace.css','live_news.js','live_channels.js','countries.js','countries.css','tariffs.js'):return jsonify(error='Not found'),404
  return send_from_directory(root/'integration/ui',name)
 @app.get('/workspace/branding/<name>')
 def branding(name):
  if name not in ('favicon.ico','icon-48.png','icon-192.png','icon-512.png','apple-touch-icon.png','og-image.png','logo.svg'):return jsonify(error='Not found'),404
  return send_from_directory(root/'integration/branding',name)
 @app.get('/workspace/manifest.webmanifest')
 def merged_manifest():return send_from_directory(root/'integration/branding','manifest.webmanifest')
 @app.get('/workspace/finder/<name>')
 def finder(name):
  import re
  if name not in ('index.html','offline.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png') and not re.fullmatch(r'data\.[0-9a-f]{12}\.js',name):return jsonify(error='Not found'),404
  return send_from_directory(root,name)
 source_reader=reader or (lambda:{'geo':[],'brics':[]})
 class ReadUnavailable(Exception):pass
 @app.errorhandler(ReadUnavailable)
 def read_unavailable(error):return jsonify(error='News storage temporarily unavailable'),503
 def public_row(row):return {k:v for k,v in row.items() if k not in ('mongo_id','legacy_id','emailed','original_url')}
 def reader():
  try:return source_reader()
  except Exception as error:
   app.logger.warning('Read-only news unavailable: %s',type(error).__name__)
   raise ReadUnavailable() from None
 authorize=authorize or (lambda req:False)
 @app.get('/health')
 def health():return jsonify(state='staging',collection=False,mail=False,scraper=False)
 @app.before_request
 def guard():
  if request.path=='/health':return None
  try:allowed=authorize(request)
  except Exception:allowed=False
  if not allowed:return jsonify(error='Private news unavailable until approved access control'),403
  if request.method=='POST' and request.headers.get('Origin')!=(allowed_origin or request.host_url.rstrip('/')):
   return jsonify(error='Same-origin request required'),403
 def selected_news():
  return selection(views(reader()),project=request.args.get('project',''),query=request.args.get('q',''),category=request.args.get('category',''),country=request.args.get('country',''),sort=request.args.get('sort','newest'))
 @app.get('/workspace/tariffs')
 def tariff_workspace():return send_from_directory(root/'integration/ui','tariffs.html')
 @app.get('/workspace/countries')
 def countries_workspace():return send_from_directory(root/'integration/ui','countries.html')
 @app.get('/api/tariff-evidence')
 def tariff_evidence_view():
  jurisdiction=request.args.get('jurisdiction','')
  if jurisdiction not in ('','IN','US','EU'):return jsonify(error='Known jurisdiction required'),400
  if tariff_evidence_snapshot is None:return jsonify(state='tariff_evidence_unwired',items=[],current_rates_verified=False,legal_effect_independently_verified=False,network=False,delivery=False,polling=False)
  if type(tariff_evidence_snapshot) is not TariffEvidenceSnapshot:return jsonify(error='Evidence unavailable'),503
  try:return jsonify(TariffEvidenceSnapshot.view(tariff_evidence_snapshot,datetime.now(timezone.utc),jurisdiction))
  except Exception:return jsonify(error='Evidence unavailable'),503
 @app.get('/api/country-page')
 def countries_read_view():
  try:return jsonify(country_page(views(reader()),request.args.get('country',''),request.args.get('project','')))
  except ValueError:return jsonify(error='Invalid country or project'),400
 @app.get('/api/news')
 def news():
  try:result=selected_news()
  except ValueError:return jsonify(error='Invalid project or sort'),400
  result['items']=[public_row(r) for r in result['items']]
  return jsonify(result)
 @app.get('/api/news-export.csv')
 def news_export():
  try:result=selected_news()
  except ValueError:return jsonify(error='Invalid project or sort'),400
  response=Response(sample_csv(result),mimetype='text/csv')
  response.headers['Content-Disposition']='attachment; filename="loaded-news-sample.csv"'
  response.headers['X-Export-Scope']='loaded_read_view_not_full_database'
  response.headers['X-Export-Limit']='100'
  response.headers['X-Export-Truncated']=str(result['truncated']).lower()
  return response
 @app.get('/api/sample-volume')
 def sample_volume():
  project=request.args.get('project','')
  if project not in ('geo','brics'):return jsonify(error='Exact project required'),400
  try:result=selected_news()
  except ValueError:return jsonify(error='Invalid project or sort'),400
  unique={}
  for row in result['items']:unique.setdefault(row['article_key'],row)
  chart=loaded_chart(list(unique.values()),project,datetime.now(timezone.utc))
  chart['outside_window_count']=len(unique)-sum(day['count'] for day in chart['daily_volume'])-chart['missing_time_count']-chart['future_time_count']
  chart.update(sample_count=len(unique),limit=result['limit'],truncated=result['truncated'],sort=result['sort'],duplicates_omitted=len(result['items'])-len(unique),selection='current_filtered_sorted_first_100')
  return jsonify(chart)
 @app.get('/api/source-health')
 def source_health():
  if source_health_snapshot is None:return jsonify(state='source_health_unwired',not_live_status=True,items=[]),200
  if type(source_health_snapshot) is not SourceHealthSnapshot:return jsonify(error='Source observations unavailable'),503
  try:return jsonify(SourceHealthSnapshot.view(source_health_snapshot,datetime.now(timezone.utc)))
  except Exception:return jsonify(error='Source observations unavailable'),503
 @app.get('/api/critical-stories')
 def critical_story_panel():
  return jsonify(critical_stories(views(reader()),datetime.now(timezone.utc)))
 @app.get('/api/news-stats')
 def news_stats():
  project=request.args.get('project','')
  if project and project not in ('geo','brics'):return jsonify(error='Invalid project'),400
  rows=[r for r in views(reader()) if not project or r['project']==project]
  counts=lambda key:[{'label':k,'count':v} for k,v in sorted(Counter(r[key] for r in rows if r[key]).items(),key=lambda x:(-x[1],x[0]))]
  dates=[r['collected_at'] for r in rows if r['collected_at']]
  return jsonify(count=len(rows),categories=counts('category'),countries=counts('original_country'),latest_collected=max(dates) if dates else None,scope='loaded_read_view',not_total_database=True)
 @app.get('/api/dashboard-snapshots')
 def dashboard_snapshots():
  project=request.args.get('project','')
  if project not in ('geo','brics'):return jsonify(error='Exact project required'),400
  if dashboard_snapshot_reader is None:return jsonify(project=project,state='snapshot_readers_unwired',not_live_status=True)
  if type(dashboard_snapshot_reader) is not DashboardSnapshots:return jsonify(error='Dashboard snapshots unavailable'),503
  try:return jsonify(dashboard_snapshot_reader(project))
  except Exception:return jsonify(error='Dashboard snapshots unavailable'),503
 @app.get('/api/dashboard-signals')
 def dashboard_signals():
  project=request.args.get('project','')
  if project not in ('geo','brics'):return jsonify(error='Exact project required'),400
  return jsonify(loaded_stats(views(reader()),project))
 @app.post('/api/related-news')
 def related():
  context=request.get_json(silent=True)
  if not isinstance(context,dict) or not isinstance(context.get('product_terms',[]),list) or len(context.get('product_terms',[]))>20 or any(not isinstance(t,str) or len(t)>200 for t in context.get('product_terms',[])):return jsonify(error='Invalid context'),400
  out=[]
  for row in views(reader()):
   evidence=match(context,row)
   if evidence['reasons']:out.append({'article':public_row(row),'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/api/story-groups')
 def story_groups():return jsonify(items=groups([public_row(r) for r in views(reader())]))
 @app.post('/api/finder-context')
 def finder_context():
  data=request.get_json(silent=True)
  if not isinstance(data,dict) or data.get('project') not in ('geo','brics') or not isinstance(data.get('article_key'),str):return jsonify(error='Exact project and article key required'),400
  articles=[r for r in views(reader()) if r['project']==data['project'] and r['article_key']==data['article_key']]
  if len(articles)!=1:return jsonify(error='Article identity not unique or unavailable'),404
  if finder_context_reader is None or not finder_base or not finder_index_verified:return jsonify(items=[],state='verified_finder_index_unwired')
  out=[]
  for context in finder_context_reader(articles[0]):
   evidence=match(context,articles[0])
   if not evidence['reasons']:continue
   link=finder_link(finder_base,context.get('system_index'),context.get('code'),verified=True)
   out.append({'context':{k:context.get(k) for k in ('code','system','edition','country','system_name')},'finder_url':link,'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/dashboard')
 def dashboard():return jsonify(state='Private dashboard UI requires Phase 2 login'),503
 return app
app=create_app()
