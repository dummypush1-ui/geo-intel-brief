"""Call preserved report builders with isolated dependencies and no live stores.

Function globals are copied, never monkeypatched across threads/projects.
Imports are explicit factory work, not private-router import side effects.
"""
from types import FunctionType
from copy import deepcopy
from integration.html_safety import sanitize_html
from html import escape
from integration.news_view import safe_url

def isolated_function(fn,overrides):
 scope={k:deepcopy(v) if isinstance(v,(list,dict,set)) else v for k,v in fn.__globals__.items()}
 scope.update(overrides)
 for name,value in list(scope.items()):
  if isinstance(value,FunctionType) and value.__module__==fn.__module__:
   clone=FunctionType(value.__code__,scope,value.__name__,value.__defaults__,value.__closure__)
   clone.__kwdefaults__=deepcopy(value.__kwdefaults__)
   scope[name]=clone
 return scope.get(fn.__name__,FunctionType(fn.__code__,scope,fn.__name__,fn.__defaults__,fn.__closure__))

def geo_report_builder(articles_reader,events_reader):
 from intelligence.geo.reports.email_report import build_digest
 # Legacy HTML puts a trigger secret into dashboard links; never forward that
 # link into merged mail. Authenticated workspace links will be added separately.
 fn=isolated_function(build_digest,{'unemailed_articles':articles_reader,'upcoming_events':events_reader,'DASHBOARD_BASE_URL':'','TRIGGER_SECRET':''})
 def build():
  html,critical,ids=fn();return {'html':sanitize_html(html),'critical_count':critical,'ids':ids}
 return build

def brics_report_builder(articles_reader,streams_reader):
 from intelligence.brics.reports.email_report import build_digest
 def escape_fields(rows,keys):
  result=[]
  for row in rows:
   copy=dict(row)
   if 'category' in row:copy['category']=row.get('category') or 'GENERAL'
   if 'url' not in copy and 'id' in copy:copy['url']=''
   for key in keys:
    copy[key]=escape(str(row.get(key) or ''),quote=True)
   for key in ('url','watch_url'):
    if key in row:copy[key]=escape(safe_url(row[key]) or '',quote=True)
   result.append(copy)
  return result
 # Original BRICS builder interpolates strings directly. Escape untrusted fields
 # at the adapter boundary, while preserving category grouping/stream content.
 fn=isolated_function(build_digest,{'load_streams':lambda:escape_fields(streams_reader(),('name',))})
 def build():
  rows=escape_fields(articles_reader(),('title','source','country'))
  html,ids=fn(rows);return {'html':sanitize_html(html or ''), 'ids':ids}
 return build
