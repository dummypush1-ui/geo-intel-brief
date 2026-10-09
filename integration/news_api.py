"""Fixture-backed private staging API. Never imports a live legacy app."""
from flask import Flask,request,jsonify,send_from_directory,Response,stream_with_context
from pathlib import Path
from collections import Counter
import re,hashlib,base64,json
from threading import BoundedSemaphore,Lock
from integration.news_view import views
from integration.public_news import public_news_row
from integration.relevance import match
from integration.story_links import groups
from integration.finder_links import finder_link
from integration.dashboard_model import loaded_stats
from integration.loaded_news import selection,sample_csv
from integration.loaded_charts import loaded_chart
from integration.critical_stories import critical_stories
from integration.country_page import country_page
from integration.country_signals import country_signals
from integration.tariff_evidence import TariffEvidenceSnapshot
from integration.source_health import SourceHealthSnapshot
from datetime import datetime,timezone,timedelta
from integration.weekly_report import build_weekly_report
from integration.dashboard_snapshots import DashboardSnapshots
from integration.branding_meta import brand_head,valid_origin
from integration.geospatial.response import map_data_response
from integration.finder_nested import shortlist_scroll,shortlist_csv_safe
from integration.finder_network import connect_sources,manual_ships_shell
from integration.finder_offline import shell as offline_shell,opt_in as offline_opt_in
from integration.news_export import snapshot_export,stream_export,guarded,parse_args as parse_export_args,ExportRequestError,ExportUnavailable
from integration.digest_preview import preview as digest_preview

def create_app(reader=None,authorize=None,finder_context_reader=None,finder_base=None,finder_index_verified=False,allowed_origin=None,branding_public_base=None,dashboard_snapshot_reader=None,source_health_snapshot=None,tariff_evidence_snapshot=None,finder_network_preview_enabled=False,full_export_pager=None,brics_stream_fixture=None,full_news_pages=None):
 if brics_stream_fixture is not None:
  from integration.brics_streams import FixtureStreams
  if type(brics_stream_fixture) is not FixtureStreams:raise ValueError('Exact fixture-only store required')
  from urllib.parse import urlsplit
  u=urlsplit(allowed_origin or '')
  if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.path or u.query or u.fragment or u.netloc!=u.hostname+((':'+str(u.port)) if u.port else ''):raise ValueError('Canonical scheme authority Origin required')
  if u.scheme=='http' and u.hostname not in ('localhost','127.0.0.1'):raise ValueError('HTTP loopback only')
 finder_connect=connect_sources(finder_network_preview_enabled)
 branding_public_base=valid_origin(branding_public_base)
 app=Flask(__name__)
 root=Path(__file__).resolve().parents[1]
 @app.after_request
 def private_response(response):
  response.headers['Cache-Control']='no-store'
  response.headers['X-Robots-Tag']='noindex, nofollow'
  if response.status_code==200 and response.mimetype=='text/html' and request.path!='/workspace/finder/offline.html':
   response.direct_passthrough=False
   response.set_data(brand_head(response.get_data(as_text=True),branding_public_base))
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['Referrer-Policy']='same-origin'
  response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  if request.path=='/workspace' and response.status_code==200:
   response.headers['Content-Security-Policy']+="; frame-src 'self' https://www.youtube-nocookie.com"
  if request.path=='/workspace/finder/index.html' and response.mimetype=='text/html' and response.status_code==200:
   response.direct_passthrough=False
   response.set_data(offline_opt_in(shortlist_csv_safe(shortlist_scroll(manual_ships_shell(response.get_data(as_text=True))))))
   scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',response.get_data(as_text=True),flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
   hashes=['\'sha256-'+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+'\'' for s in scripts]
   response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' "+' '.join(hashes)+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src "+finder_connect+"; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
  if request.path=='/workspace/finder/offline.html' and response.status_code==200 and response.mimetype=='text/html':
   response.direct_passthrough=False
   # Use source original, not branding that adds protected external assets.
   # Memory route already supplies the transformed complete shell (Range ignored).
   scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',response.get_data(as_text=True),flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
   hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
   response.headers['Content-Security-Policy']="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'none'"
   response.headers['X-Finder-Public-Snapshot']='true'
  return response
 @app.get('/workspace')
 def workspace():
  html=(root/'integration/ui/workspace.html').read_text()
  if full_news_pages is not None:
   html=html.replace('data-full-news-pages="false"','data-full-news-pages="true"').replace('Loaded sample only. Database totals and unsupplied events are unavailable.','Summary metrics use up to the latest 100 stored articles, not the whole-store total. The feed can load more below.').replace('Export loaded sample CSV','Export latest-100 view CSV')
  return Response(html,mimetype='text/html')
 @app.get('/workspace/assets/<name>')
 def assets(name):
  if name not in ('workspace.js','news_scroll.js','workspace.css','live_news.js','live_channels.js','countries.js','countries.css','tariffs.js','watch_updates.js','weekly.js','weekly.css','map.js','map.css','geo_map_ui.js','geo_map.css','brics_streams.js','brics_streams.css'):return jsonify(error='Not found'),404
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
  if name=='offline.html':return Response(offline_shell((root/'offline.html').read_text(encoding='utf-8')),mimetype='text/html')
  if name=='offline-manifest.webmanifest':return jsonify(name='Public offline trade Finder',short_name='Offline Finder',id='/workspace/finder/offline.html',start_url='/workspace/finder/offline.html',scope='/workspace/finder/',display='standalone',icons=[])
  if name=='offline-sw.js':
   r=send_from_directory(root/'integration/ui','finder-offline-sw.js');r.headers['Service-Worker-Allowed']='/workspace/finder/';return r
  if name=='offline-control.js':return send_from_directory(root/'integration/ui','finder-offline-control.js')
  if name not in ('index.html','offline.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png') and not re.fullmatch(r'data\.[0-9a-f]{12}\.js',name):return jsonify(error='Not found'),404
  return send_from_directory(root,name)
 source_reader=reader or (lambda:{'geo':[],'brics':[]})
 class ReadUnavailable(Exception):pass
 @app.errorhandler(ReadUnavailable)
 def read_unavailable(error):return jsonify(error='News storage temporarily unavailable'),503
 def public_row(row):return public_news_row(row)
 def public_views(data):return [public_news_row(r) for r in views(data)]
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
  if request.method in ('POST','DELETE') and request.headers.get('Origin')!=(allowed_origin or request.host_url.rstrip('/')):
   return jsonify(error='Same-origin request required'),403
 @app.before_request
 def validate_read_query():
  from integration.query_validation import valid
  if request.method in ('GET','HEAD') and not valid(request.path,request.args,request.query_string):return jsonify(error='Invalid read query parameters'),400
 def selected_news():
  return selection(public_views(reader()),project=request.args.get('project',''),query=request.args.get('q',''),category=request.args.get('category',''),country=request.args.get('country',''),sort=request.args.get('sort','newest'))
 @app.get('/workspace/weekly')
 def weekly_workspace():return send_from_directory(root/'integration/ui','weekly.html')
 weekly_build_slots=BoundedSemaphore(2)
 @app.get('/api/weekly-report.pdf')
 def weekly_download():
  # Request supplies dates only; never HTML, rows, URLs or a caller summary.
  if any(len(request.args.getlist(k))!=1 for k in ('start','end')):return jsonify(error='Exactly one start and end required'),400
  start=request.args.get('start','');end=request.args.get('end','')
  if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',start) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',end):return jsonify(error='Exact start and exclusive end dates required'),400
  try:
   # Explicit India offset for user-entered calendar dates, no DST ambiguity.
   zone=timezone(timedelta(hours=5,minutes=30))
   ps=datetime.fromisoformat(start).replace(tzinfo=zone);pe=datetime.fromisoformat(end).replace(tzinfo=zone)
   if ps.date()<datetime(1970,1,2).date() or not 1970<=ps.year<=2100 or not 1970<=pe.year<=2100 or not timedelta(days=1)<=pe-ps<=timedelta(days=31):raise ValueError()
  except (ValueError,OverflowError):return jsonify(error='Use a 1 to31 day period between1970 and2100'),400
  if not weekly_build_slots.acquire(blocking=False):return jsonify(error='Weekly PDF busy'),429
  try:
   raw=reader()
   if type(raw) is not dict or len(raw)>2 or any(k not in ('geo','brics') for k in raw):raise ValueError('Invalid snapshot')
   if any(type(v) not in (list,tuple) for v in raw.values()) or sum(len(v) for v in raw.values())>2000:raise ValueError('Snapshot work bound')
   rows=public_views({k:v[:100] for k,v in raw.items()})
   pdf=build_weekly_report(rows,[],period_start=ps,period_end=pe,generated_at=datetime.now(timezone.utc),display_tz='Asia/Kolkata',title='Weekly supplied-news report')
   return Response(pdf,mimetype='application/pdf',headers={'Content-Disposition':'attachment; filename="weekly-supplied-news.pdf"'})
  except Exception:
   app.logger.warning('Weekly PDF unavailable')
   return jsonify(error='Weekly PDF unavailable'),503
  finally:weekly_build_slots.release()
 @app.get('/api/export.csv')
 def export_snapshot_csv():
  args={k:(v[0] if len(v)==1 else v) for k,v in request.args.lists()}
  try:
   raw=reader()
   if type(raw) is not dict or len(raw)>2 or any(k not in ('geo','brics') for k in raw) or any(type(v) not in (list,tuple) for v in raw.values()) or sum(len(v) for v in raw.values())>2000:raise ValueError('Snapshot bound')
   parsed=parse_export_args(args)
   chosen={}
   for project,values in raw.items():
    if parsed['project'] and project!=parsed['project']:continue
    selected=[v for v in values if not parsed['category'] or (type(v) is dict and (v.get('category') or 'GENERAL')==parsed['category'])]
    chosen[project]=selected
   cut=any(len(v)>100 for v in chosen.values())
   body,headers,meta=snapshot_export(public_views({k:v[:100] for k,v in chosen.items()}),args)
   headers['X-Export-Input-Limit']='100 per project'
   if cut:headers['X-Export-Truncated']='true'
  except ExportRequestError:return jsonify(error='Invalid export arguments'),400
  except ReadUnavailable:raise
  except Exception:
   app.logger.warning('Export unavailable');return jsonify(error='Export unavailable'),503
  return Response(body,headers=headers)
 export_slots=BoundedSemaphore(1)
 @app.get('/api/export-full.csv')
 def export_full_csv():
  if full_export_pager is None:return jsonify(error='Full export not wired',state='full_export_unwired'),503
  args={k:(v[0] if len(v)==1 else v) for k,v in request.args.lists()}
  if not export_slots.acquire(blocking=False):return jsonify(error='Export busy'),429,{'Retry-After':'5'}
  try:chunks,headers,state=stream_export(full_export_pager,args)
  except ExportRequestError:
   export_slots.release();return jsonify(error='Invalid export arguments'),400
  except Exception as error:
   export_slots.release();app.logger.warning('Full export unavailable: %s',type(error).__name__);return jsonify(error='Export unavailable'),503
  close_lock=Lock();released=[False]
  def release_once():
   with close_lock:
    if not released[0]:released[0]=True;export_slots.release()
  response=Response(stream_with_context(guarded(chunks,release_once)),headers=headers)
  response.call_on_close(release_once)
  return response
 def geo_digest_preview(kind):
  if request.args:return jsonify(error='No preview query parameters accepted'),400
  try:
   raw=reader()
   if type(raw) is not dict or len(raw)>2 or any(k not in ('geo','brics') for k in raw) or any(type(v) not in (list,tuple) for v in raw.values()) or sum(len(v) for v in raw.values())>2000:raise ValueError('Snapshot bound')
   rows=public_views({'geo':raw.get('geo',[])[:100]})
   return jsonify(digest_preview(rows,kind,datetime.now(timezone.utc),event_snapshots=dashboard_snapshot_reader))
  except Exception:
   app.logger.warning('Digest preview unavailable');return jsonify(error='Digest preview unavailable'),503
 @app.get('/digest-data')
 def digest_data_preview():return geo_digest_preview('digest')
 @app.post('/mark-emailed')
 def mark_emailed_disabled():return jsonify(error='Sent marking disabled',state='receipt_adapter_unwired',writes=False),503
 @app.route('/critical',methods=['GET','POST'])
 def critical_preview():return geo_digest_preview('critical')
 @app.route('/weekly',methods=['GET','POST'])
 def weekly_preview():return geo_digest_preview('weekly')
 @app.get('/workspace/brics-streams')
 def brics_stream_workspace():return send_from_directory(root/'integration/ui','brics_streams.html')
 @app.get('/api/brics/streams')
 def brics_stream_get():
  if brics_stream_fixture is None:return jsonify(error='Original stream persistence unwired',state='unwired'),503
  return jsonify(streams=brics_stream_fixture.load(),state='fixture_only',persistence=False,polling=False)
 def stream_json():
  if request.mimetype!='application/json':return None,415
  if request.content_length is None or not 0<request.content_length<=4096:return None,413
  def pairs(items):
   out={}
   for key,value in items:
    if key in out:raise ValueError('Duplicate field')
    out[key]=value
   return out
  raw=request.stream.read(4097)
  if len(raw)>4096:return None,413
  if len(raw)!=request.content_length:return None,400
  try:return json.loads(raw,object_pairs_hook=pairs),None
  except (ValueError,UnicodeError):return None,400
 @app.post('/api/brics/streams')
 def brics_stream_add():
  data,error=stream_json()
  if error:return jsonify(error='Invalid bounded JSON request'),error
  if brics_stream_fixture is None:return jsonify(error='Stream persistence unwired'),503
  if type(data) is not dict or set(data)-{'name','country','link','video_id'}:return jsonify(error='Invalid stream fields'),400
  try:row=brics_stream_fixture.add(data.get('name'),data.get('country'),data.get('link') or data.get('video_id'))
  except ValueError:return jsonify(error='Invalid or duplicate stream'),400
  return jsonify(status='added',stream=row,state='fixture_only',persistence=False)
 @app.delete('/api/brics/streams')
 def brics_stream_delete():
  data,error=stream_json()
  if error:return jsonify(error='Invalid bounded JSON request'),error
  if type(data) is not dict or set(data)!={'name'}:return jsonify(error='Exact name body required'),400
  name=data['name']
  if brics_stream_fixture is None:return jsonify(error='Stream persistence unwired'),503
  try:removed=brics_stream_fixture.remove(name)
  except ValueError:return jsonify(error='Invalid stream name'),400
  if not removed:return jsonify(error='No matching stream'),404
  return jsonify(status='removed',name=name,state='fixture_only',persistence=False)
 @app.get('/workspace/tariffs')
 def tariff_workspace():return send_from_directory(root/'integration/ui','tariffs.html')
 @app.get('/workspace/countries')
 def countries_workspace():return send_from_directory(root/'integration/ui','countries.html')
 @app.get('/workspace/map')
 def map_workspace():return send_from_directory(root/'integration/ui','map.html')
 @app.get('/api/map-data')
 def map_data():
  if request.args:return jsonify(error='No query parameters accepted'),400
  try:return jsonify(map_data_response(None,datetime.now(timezone.utc)))
  except Exception:
   app.logger.warning('Map data unavailable');return jsonify(error='Map data unavailable'),503
 @app.get('/api/tariff-evidence')
 def tariff_evidence_view():
  jurisdiction=request.args.get('jurisdiction','')
  if jurisdiction not in ('','IN','US','EU'):return jsonify(error='Known jurisdiction required'),400
  if tariff_evidence_snapshot is None:return jsonify(state='tariff_evidence_unwired',items=[],current_rates_verified=False,legal_effect_independently_verified=False,network=False,delivery=False,polling=False)
  if type(tariff_evidence_snapshot) is not TariffEvidenceSnapshot:return jsonify(error='Evidence unavailable'),503
  try:return jsonify(TariffEvidenceSnapshot.view(tariff_evidence_snapshot,datetime.now(timezone.utc),jurisdiction))
  except Exception:return jsonify(error='Evidence unavailable'),503
 @app.get('/api/country-signals')
 def countries_signal_view():
  country=request.args.get('country','')
  try:country_signals([],country,datetime.now(timezone.utc))
  except ValueError:return jsonify(error='Exact bounded country label required'),400
  rows=public_views(reader())
  # The normalized public read view has plain string fields. Isolate exact
  # country/project before strict signal validation; unrelated data can't fail it.
  selected=[r for r in rows if r.get('original_country')==country and r.get('project')=='geo']
  try:
   result=country_signals(selected,country,datetime.now(timezone.utc))
   result['supplied_read_view_rows']=len(rows)
   result['reader_scope_note']='Bounded supplied read view, not whole database; live reader uses newest up to100 rows per configured collection'
   return jsonify(result)
  except (ValueError,TypeError):return jsonify(error='Supplied signal snapshot unavailable'),503
 @app.get('/api/country-page')
 def countries_read_view():
  try:return jsonify(country_page(public_views(reader()),request.args.get('country',''),request.args.get('project','')))
  except ValueError:return jsonify(error='Invalid country or project'),400
 @app.get('/api/news')
 def news():
  try:result=selected_news()
  except ValueError:return jsonify(error='Invalid project or sort'),400
  result['items']=[public_row(r) for r in result['items']]
  return jsonify(result)
 @app.get('/api/news-page')
 def news_page():
  from integration.news_pages import validate,PageExpired,PageBusy,PageUnavailable
  allowed={'project','q','category','country','sort','limit','cursor'}
  if set(request.args)-allowed or any(len(request.args.getlist(k))!=1 for k in request.args):return jsonify(error='Exact single page parameters required'),400
  raw=request.args.get('limit','25')
  if not re.fullmatch(r'[1-9][0-9]{0,2}',raw):return jsonify(error='Limit 1 to100 required'),400
  filters={'project':request.args.get('project','geo'),'query':request.args.get('q',''),'category':request.args.get('category',''),'country':request.args.get('country',''),'sort':request.args.get('sort','newest')}
  token=request.args.get('cursor','')
  try:validate(filters,int(raw),token)
  except ValueError:return jsonify(error='Invalid news page request'),400
  if full_news_pages is None:return jsonify(error='Whole-store paging disabled',state='full_pages_unwired'),503
  try:return jsonify(full_news_pages.page(filters,int(raw),token))
  except PageExpired:return jsonify(error='News cursor expired or changed; refresh to restart'),409
  except PageBusy:return jsonify(error='News paging busy'),429,{'Retry-After':'5'}
  except (PageUnavailable,Exception):
   app.logger.warning('Whole-store page unavailable');return jsonify(error='Whole-store page unavailable'),503
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
  return jsonify(critical_stories(public_views(reader()),datetime.now(timezone.utc)))
 @app.get('/api/news-stats')
 def news_stats():
  project=request.args.get('project','')
  if project and project not in ('geo','brics'):return jsonify(error='Invalid project'),400
  rows=[r for r in public_views(reader()) if not project or r['project']==project]
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
  return jsonify(loaded_stats(public_views(reader()),project))
 @app.post('/api/related-news')
 def related():
  context=request.get_json(silent=True)
  if not isinstance(context,dict) or not isinstance(context.get('product_terms',[]),list) or len(context.get('product_terms',[]))>20 or any(not isinstance(t,str) or len(t)>200 for t in context.get('product_terms',[])):return jsonify(error='Invalid context'),400
  out=[]
  for row in public_views(reader()):
   evidence=match(context,row)
   if evidence['reasons']:out.append({'article':public_row(row),'match':evidence})
  return jsonify(items=out[:100])
 @app.get('/api/story-groups')
 def story_groups():return jsonify(items=groups([public_row(r) for r in public_views(reader())]))
 @app.post('/api/finder-context')
 def finder_context():
  data=request.get_json(silent=True)
  if not isinstance(data,dict) or data.get('project') not in ('geo','brics') or not isinstance(data.get('article_key'),str):return jsonify(error='Exact project and article key required'),400
  articles=[r for r in public_views(reader()) if r['project']==data['project'] and r['article_key']==data['article_key']]
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
 from integration.api_v1 import install as install_v1
 install_v1(app)
 return app

# Preserve integration.news_api:app without constructing a fixture during imports.
# Access by a WSGI loader creates and caches the compatibility application once.
from threading import Lock as _AppLock
_compat_app_lock=_AppLock()
def __getattr__(name):
 if name!='app':raise AttributeError(name)
 with _compat_app_lock:
  if 'app' not in globals():globals()['app']=create_app()
  return globals()['app']
