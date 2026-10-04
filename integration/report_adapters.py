"""Call preserved report builders with isolated dependencies and no live stores.

Only reviewed renderer AST definitions are compiled in a minimal explicit scope.
Original modules/config/database are never imported by these factories.
"""
from integration.renderer_scope import renderer
from integration.html_safety import sanitize_html
from html import escape
from integration.news_view import safe_url

def geo_report_builder(articles_reader,events_reader):
 # Legacy HTML puts a trigger secret into dashboard links; never forward that
 # link into merged mail. Authenticated workspace links will be added separately.
 fn=renderer('geo_digest',{'unemailed_articles':articles_reader,'upcoming_events':events_reader})
 def build():
  html,critical,ids=fn();return {'html':sanitize_html(html),'critical_count':critical,'ids':ids}
 return build

def brics_report_builder(articles_reader,streams_reader):
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
 fn=renderer('brics_digest',{'load_streams':lambda:escape_fields(streams_reader(),('name',))})
 def build():
  rows=escape_fields(articles_reader(),('title','source','country'))
  html,ids=fn(rows);return {'html':sanitize_html(html or ''), 'ids':ids}
 return build
