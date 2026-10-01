"""Separate pagewatch preview report. Never inserts rows into legacy articles.

No delivery or marking. Caller supplies a diff result for a reviewed source;
mail enablement and recipients are separate decisions.
"""
from html import escape
from integration.news_view import safe_url

def build_pagewatch_report(result):
 if not isinstance(result,dict) or result.get('state') not in ('baseline','unchanged','changed'):raise ValueError('Valid pagewatch result required')
 if result['state']!='changed':return {'html':'','ids':[],'kind':'pagewatch_preview','mail':False,'marking':False}
 rows=result.get('items')
 if not isinstance(rows,list) or len(rows)!=1:raise ValueError('One page-change row required')
 row=rows[0];url=safe_url(row.get('url'))
 if not url or not isinstance(row.get('id'),str) or not row['id'] or not isinstance(row.get('summary'),str):raise ValueError('Safe page change identity required')
 content='<section><h2>'+escape(str(row.get('title','Page changed')))+' </h2><p><a href="'+escape(url,quote=True)+'">Review source page</a></p><p>Observed page-text change, not independently verified event information.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(row['summary'])+'</pre></section>'
 return {'html':content,'ids':[row['id']],'kind':'pagewatch_preview','mail':False,'marking':False}
