"""Separate pagewatch preview report. Never inserts rows into legacy articles.

No delivery or marking. Caller supplies a diff result for a reviewed source;
mail enablement and recipients are separate decisions.
"""
from html import escape
import unicodedata
from integration.page_watch import _url

def _plain(value,depth=0,budget=None):
 if budget is None:budget=[0]
 if depth>4:raise ValueError("Report nesting")
 if type(value) is dict:
  if len(value)>24 or any(type(k) is not str or len(k)>64 for k in value):raise ValueError("Report fields")
  for v in value.values():_plain(v,depth+1,budget)
 elif type(value) is list:
  if len(value)>1:raise ValueError("Report rows")
  for v in value:_plain(v,depth+1,budget)
 elif type(value) is str:
  if len(value)>2_000_000:raise ValueError("Report string")
  try:
   size=len(value.encode("utf-8"));budget[0]+=size
   if size>2_000_000 or budget[0]>4_000_000:raise ValueError("Report bytes")
  except UnicodeError:raise ValueError("Report text") from None
 elif type(value) is not bool:raise ValueError("Plain report values")

def _field(value,limit,controls=True):
 if type(value) is not str or len(value)>limit:raise ValueError("Bounded report field")
 try:
  if len(value.encode("utf-8"))>limit*4:raise ValueError("Report field bytes")
 except UnicodeError:raise ValueError("Report field text") from None
 if any((unicodedata.category(c) in ("Cc","Cf","Zl","Zp")) and (controls or c not in "\n\r\t") for c in value):raise ValueError("Report field controls")
 return value

def build_pagewatch_report(result):
 _plain(result)
 if type(result) is not dict or set(result)-{'state','items','snapshot','diff_truncated','diff_omitted'} or type(result.get('state')) is not str or result['state'] not in ('baseline','unchanged','changed'):raise ValueError('Valid pagewatch result required')
 if 'snapshot' in result:
  from integration.page_watch import validate_snapshot
  validate_snapshot(result['snapshot'])
 for key in ('diff_truncated','diff_omitted'):
  if key in result and type(result[key]) is not bool:raise ValueError('Report flags')
 rows=result.get('items',[])
 if type(rows) is not list or len(rows)>1:raise ValueError('One page-change row required')
 if result['state']!='changed':
  if rows:raise ValueError('No rows for unchanged baseline')
  return {'html':'','ids':[],'kind':'pagewatch_preview','mail':False,'marking':False}
 if len(rows)!=1:raise ValueError('One page-change row required')
 row=rows[0]
 allowed={'id','title','url','source','country','category','summary','summary_html','summary_format','published','created_at','method','previous_sha256','current_sha256','emailed'}
 if type(row) is not dict or set(row)-allowed:raise ValueError('Report row fields')
 identity=_field(row.get('id'),128);url=_url(row.get('url'));summary=_field(row.get('summary'),12100,False);title=_field(row.get('title','Page changed'),200)
 if not identity:raise ValueError('Safe page change identity required')
 for key in set(row)-{'id','title','url','summary'}:
  if key=='emailed':
   if type(row[key]) is not bool:raise ValueError('Report flag')
  else:_field(row[key],80000 if key=='summary_html' else 256,False)
 content='<section><h2>'+escape(title)+' </h2><p><a href="'+escape(url,quote=True)+'">Review source page</a></p><p>Observed page-text change, not independently verified event information.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(summary)+'</pre></section>'
 return {'html':content,'ids':[identity],'kind':'pagewatch_preview','mail':False,'marking':False}
