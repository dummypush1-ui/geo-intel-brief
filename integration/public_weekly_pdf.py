"""Manual supplied-view PDF, default OFF. Guards are per process, not deployment.
Startup pins do not continuously monitor drift. No source is fetched at install.
"""
from pathlib import Path
from threading import Lock, BoundedSemaphore
from collections import deque
from datetime import datetime, timezone, timedelta
import hashlib
import math
import re
import time

FLAG = 'PUBLIC_WEEKLY_PDF_ENABLED'
PATH = '/api/weekly-report.pdf'
PATHS = frozenset((PATH, '/workspace/weekly', '/workspace/assets/weekly.js',
                   '/workspace/assets/weekly.css'))
ROOT = Path(__file__).resolve().parents[1]
PINS = {'integration/news_api.py': '77137ebf1d8debef70bc49bdc0a253c9b4845429135431af9e8e46328217dff7', 'integration/query_validation.py': '6ba0e2bdc7c329fed02321e3fda5e622fd7686f677c1544d7dfec2f6a462d939', 'integration/news_view.py': 'd24256b4467b6acc81bbb4d9e0f689c42b52511443fe1fa0feb3725b06416b1f', 'integration/public_news.py': '08a002863831a1e7cf9336e10b2f9d61aa1ce0ecf4b4367027dd34ed1dbd8145', 'integration/dashboard_model.py': '2a771a65358b9f62bb014d614cf8c0dea07b048edd8c7be93e7d8c467209a4f0', 'integration/weekly_report/__init__.py': 'a29dae5559548f4364463ae45db9f70fde82707a16c41244ad6307ad4f1bba90', 'integration/weekly_report/report.py': '5efd22db000fc70763a9ce142f3b677b848a7053a3d97ccac27ccc21fb753d30', 'integration/weekly_report/_render.py': '9a8919f173e3b7b10ce1672a4d4c96f5b288c179b125cfef873d920adc6f49c4', 'integration/weekly_report/_pdf.py': 'f1bac997e22c9055cbcf1c9c71302cf67fe85a43caad73bc7f397156f05fb198', 'integration/weekly_report/_metrics.py': '3a71b4a248a223d5772d20ca6d26437659cc4f6435ee46698403cff79eb2921c', 'integration/ui/weekly.html': '18a7dac2b8854d3bd51146d9ac6ed55c9146d0ae6bc7b7d39c557c7519eb2faa', 'integration/ui/public_weekly.js': 'c5428c8b6149f8054f99f27ab6d48546a69f35448a19f4ec77084fc4030e25b1', 'integration/ui/public_weekly.css': 'fb08165dece27a65431557a168e32126d14cae10a324af2161cae4040f38f243'}
_SLOTS = BoundedSemaphore(2)
_RATE_LOCK = Lock()
_STARTS = deque()
MAX_PDF = 2 * 1024 * 1024


def enabled(env):
 value = env.get(FLAG, 'false')
 if value not in ('true', 'false'):
  raise ValueError('Exact public weekly PDF flag required')
 on = value == 'true'
 if on and env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED') != 'true':
  raise ValueError('Weekly PDF requires public composition')
 return on


def verify_pins():
 try:
  for name, expected in PINS.items():
   h = hashlib.sha256()
   with (ROOT / name).open('rb') as f:
    while chunk := f.read(65536):
     h.update(chunk)
   if h.hexdigest() != expected:
    raise ValueError()
 except Exception:
  raise ValueError('Public weekly PDF pins unavailable') from None


def prepare(env):
 on = enabled(env)
 if on:
  verify_pins()
 return on


def _admit(now):
 with _RATE_LOCK:
  while _STARTS and now - _STARTS[0] >= 60:
   _STARTS.popleft()
  if len(_STARTS) >= 10:
   return max(1, math.ceil(60 - (now - _STARTS[0])))
  _STARTS.append(now)
 return 0


def _dates(args):
 if set(args) != {'start', 'end'} or any(len(args.getlist(k)) != 1 for k in args):
  raise ValueError()
 start, end = args['start'], args['end']
 if any(not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', v) for v in (start, end)):
  raise ValueError()
 zone = timezone(timedelta(hours=5, minutes=30))
 ps, pe = (datetime.fromisoformat(v).replace(tzinfo=zone) for v in (start, end))
 if ps.date() < datetime(1970, 1, 2).date() or not 1970 <= ps.year <= 2100 or not 1970 <= pe.year <= 2100 or not timedelta(days=1) <= pe - ps <= timedelta(days=31):
  raise ValueError()
 return ps, pe


def _bounded_rows(raw):
 """Public mode fails on excess rows/invalid public values; never slices rows.
 Unknown/private fields are never copied/read as values. Missing dates excluded
 by the preserved report; invalid supplied dates fail instead of substitution.
 """
 from integration.weekly_report.report import _clean_url, _parse_dt
 from integration.news_view import views
 from integration.public_news import public_news_row
 if type(raw) is not dict or len(raw) > 2 or any(type(k) is not str or k not in ('geo', 'brics') for k in raw):
  raise ValueError()
 caps = {'url':500, 'title':2048, 'summary':8000, 'source':200,
         'country':200, 'category':200, 'risk_level':200, 'credibility':200}
 clean = {}
 for project, rows in raw.items():
  if type(rows) is not list or len(rows) > 100:
   raise ValueError()
  out = []
  for row in rows:
   if type(row) is not dict:
    raise ValueError()
   item = {}
   for k, cap in caps.items():
    if k not in row:
     continue
    v = row[k]
    if type(v) is not str or len(v) > cap:
     raise ValueError()
    v.encode('utf-8', 'strict')
    item[k] = v
   if not item.get('title', '').strip() or _clean_url(item.get('url')) is None:
    raise ValueError()
   for k in ('published', 'created_at', 'collected_at'):
    if k not in row or row[k] is None:
     continue
    v = row[k]
    if type(v) is datetime:
     if v.tzinfo is None or v.utcoffset() is None:
      raise ValueError()
     v = v.isoformat()
    if type(v) is not str or _parse_dt(v) is None:
     raise ValueError()
    item[k] = v
   if 'score' in row:
    v = row['score']
    if type(v) not in (int, float) or abs(v) > 10**12 or not math.isfinite(v):
     raise ValueError()
    item['score'] = v
   out.append(item)
  clean[project] = out
 return [public_news_row(r) for r in views(clean)]


def install(app, reader, *, period_reader=None):
 """Replace endpoints only on validated public apps. Private handlers unchanged."""
 from flask import request, Response, jsonify
 from integration.query_validation import valid
 from integration.weekly_report import build_weekly_report
 endpoints = {'weekly_workspace':'/workspace/weekly', 'weekly_download':PATH}
 for endpoint, path in endpoints.items():
  old = app.view_functions.get(endpoint)
  rules = [r for r in app.url_map.iter_rules() if r.endpoint == endpoint]
  # Exact function originates from the pinned create_app code, not a wrapped view.
  from integration.news_api import create_app
  code = next((c for c in create_app.__code__.co_consts
               if hasattr(c, 'co_name') and c.co_name == endpoint), None)
  if old is None or old.__code__ is not code or len(rules) != 1 or rules[0].rule != path or rules[0].methods != {'GET','HEAD','OPTIONS'} or not rules[0].provide_automatic_options:
   raise ValueError('Weekly endpoint mount unavailable')
 # Flask adds automatic OPTIONS; public allow policy rejects it. Assert exactly
 # GET/HEAD plus framework OPTIONS, not an extra supported public verb.
 html = (ROOT / 'integration/ui/weekly.html').read_text()
 if html.count('PRIVATE STAGING') != 1:
  raise ValueError('Weekly public label seam unavailable')
 html = html.replace('PRIVATE STAGING', 'PUBLIC SUPPLIED NEWS')
 seam = '<p id="weekly-status" role="status">'
 if html.count(seam) != 1:
  raise ValueError('Weekly public status seam unavailable')
 note = ('<p>Latest-100 sample per collection only. Empty means no supplied items, '
         'not no events. Global limit: 10 download starts per 60 seconds per process, '
         'shared by all visitors. Anyone can exhaust it; wait up to 60 seconds and '
         'retry manually. Stopping the browser wait does not stop server generation.</p>')
 html = html.replace(seam, note + seam)
 if period_reader is not None:
  html = html.replace('Latest-100 sample per collection only.', 'Bounded whole-store period read. Not a fixed snapshot. The scan must finish within 25,000 source rows, 2,000 dated period rows, 8 MiB retained text and 10 seconds; otherwise no PDF is returned.')
  html = html.replace('PUBLIC SUPPLIED NEWS', 'PUBLIC PERIOD NEWS')


 def shell():
  return Response('' if request.method == 'HEAD' else html, mimetype='text/html')

 def download():
  try:
   if not valid(PATH, request.args, request.query_string):
    raise ValueError()
   ps, pe = _dates(request.args)
  except (ValueError, OverflowError):
   return jsonify(error='Use exact start and exclusive end, a 1 to 31 day period in 1970 to 2100'), 400
  headers = {'Content-Disposition':'attachment; filename="weekly-supplied-news.pdf"'}
  if request.method == 'HEAD':
   return Response(status=200, mimetype='application/pdf', headers=headers)
  retry = _admit(time.monotonic())
  if retry:
   return jsonify(error='Global weekly PDF start limit; retry manually'), 429, {'Retry-After':str(retry)}
  if not _SLOTS.acquire(blocking=False):
   return jsonify(error='Weekly PDF busy; retry manually'), 429, {'Retry-After':'1'}
  try:
   if period_reader is None:
    rows = _bounded_rows(reader())
    pdf = build_weekly_report(rows, [], period_start=ps, period_end=pe,
          generated_at=datetime.now(timezone.utc), display_tz='Asia/Kolkata',
          title='Weekly supplied-news report')
   else:
    from integration.weekly_report.report import summarize_week
    from integration.weekly_report._render import render_pdf
    rows, scan = period_reader(ps, pe)
    summary = summarize_week(rows, [], ps, pe, datetime.now(timezone.utc),
                            display_tz='Asia/Kolkata', title='Weekly period-news report')
    summary['source_scan'] = scan
    pdf = render_pdf(summary)
   if type(pdf) is not bytes or not pdf.startswith(b'%PDF-1.4') or len(pdf) > MAX_PDF:
    raise ValueError()
   return Response(pdf, mimetype='application/pdf', headers=headers)
  except Exception as error:
   from integration.weekly_full_store import StoreTooLarge, PeriodTooLarge
   if isinstance(error, StoreTooLarge):
    return jsonify(error='Store too large for this report. No PDF returned. The report scans the store for every download; a narrower period does not reduce source scan work.'), 503
   if isinstance(error, PeriodTooLarge):
    return jsonify(error='Period too large for this report. No PDF returned. Try a narrower period manually.'), 503
   app.logger.warning('Public weekly PDF unavailable')
   return jsonify(error='Weekly PDF unavailable'), 503
  finally:
   _SLOTS.release()

 app.view_functions['weekly_workspace'] = shell
 app.view_functions['weekly_download'] = download
 # Preserve the original shared asset endpoint for every other path, replace only
 # these two named assets in public mode. No extra route registration.
 old_asset = app.view_functions['assets']
 def asset(name):
  if name in ('weekly.js','weekly.css'):
   kind = 'application/javascript' if name.endswith('.js') else 'text/css'
   data = '' if request.method == 'HEAD' else (ROOT / ('integration/ui/public_' + name)).read_text()
   if name == 'weekly.js' and period_reader is not None:
    data = data.replace('latest-100 supplied sample', 'bounded whole-store period read').replace('supplied sample rows only, not complete weekly history', 'a completed bounded period scan, not a fixed snapshot or complete world-event coverage')
    data = data.replace("if(r.status===503){status.textContent='Supplied-news PDF unavailable. Try manually later. No report saved or sent.';return;}", "if(r.status===503){const v=await r.json();status.textContent=typeof v.error==='string'&&v.error.startsWith('Store too large')?'Store too large for this report. No PDF returned. Every download scans the store; a narrower period does not reduce scan work.':typeof v.error==='string'&&v.error.startsWith('Period too large')?'Period too large for this report. No PDF returned. Try a narrower period manually.':'Period PDF unavailable. No report saved or sent. Retry manually later.';return;}")

   return Response(data, mimetype=kind)
  return old_asset(name)
 app.view_functions['assets'] = asset
 @app.before_request
 def weekly_query():
  if request.path in PATHS - {PATH} and request.query_string:
   return jsonify(error='No query parameters accepted'), 400
 @app.after_request
 def weekly_headers(response):
  if request.path in PATHS:
   response.headers['Cache-Control'] = 'no-store'
   response.headers['X-Content-Type-Options'] = 'nosniff'
   response.headers['Referrer-Policy'] = 'no-referrer'
   response.headers['Content-Security-Policy'] = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'"
  return response
 # Flask after-request functions run in reverse order; place feature policy first
 # in storage so it wins over the original generic policy.
 hooks = app.after_request_funcs[None]
 hooks.remove(weekly_headers)
 hooks.insert(0, weekly_headers)
 app.extensions['public_weekly_pdf'] = True
 app.extensions['public_weekly_full_store'] = period_reader is not None
