"""Injected read-only original-dashboard snapshots. No clients or live imports.

Source status is reported as a captured observation, never a current health
claim. Stream URLs are outbound links only; this adapter does not embed video.
Unavailable differs from an empty verified snapshot.
"""
from datetime import date
from integration.news_view import safe_url,date_view

class DashboardSnapshots:
 def __init__(self,readers,verified=False):
  if verified is not True:raise ValueError('Reviewed snapshot readers required')
  if not isinstance(readers,dict) or any(k not in ('geo_events','brics_sources','brics_streams') or not callable(v) for k,v in readers.items()):raise ValueError('Exact read-only snapshot readers required')
  self.readers=dict(readers)
 def __call__(self,project):
  if project not in ('geo','brics'):raise ValueError('Exact project required')
  keys=('geo_events',) if project=='geo' else ('brics_sources','brics_streams')
  result={'project':project,'scope':'supplied_read_only_snapshot','not_live_status':True,'panels':{}}
  for key in keys:
   if key not in self.readers:result['panels'][key]={'state':'unavailable','items':[]};continue
   try:
    snapshot=self.readers[key]()
    if not isinstance(snapshot,dict) or not date_view(snapshot.get('observed_at')) or not isinstance(snapshot.get('items'),list) or len(snapshot['items'])>1000:raise ValueError('Bounded zoned snapshot required')
    items=[];rejected=0
    for row in snapshot['items']:
     item=self.normalize(key,row)
     if item is None:rejected+=1
     else:items.append(item)
    result['panels'][key]={'state':'supplied_snapshot','observed_at':date_view(snapshot['observed_at']),'items':items[:100],'rejected_count':rejected,'truncated':len(items)>100}
   except Exception:result['panels'][key]={'state':'unavailable','items':[]}
  return result
 @staticmethod
 def normalize(key,row):
  if not isinstance(row,dict):return None
  def text(k):
   v=row.get(k);return v[:2000] if isinstance(v,str) else ''
  if key=='geo_events':
   try:day=date.fromisoformat(text('event_date')).isoformat()
   except ValueError:return None
   url=safe_url(row.get('source_url'));name=text('name')
   if not name or not url:return None
   return {'name':name,'event_date':day,'source_url':url,'description':text('description')}
  if key=='brics_sources':
   name=text('name');url=safe_url(row.get('url'))
   if not name or not url:return None
   status=row.get('last_status');count=row.get('last_count')
   return {'name':name,'url':url,'country':text('country'),'last_status':status if isinstance(status,str) and status in ('ok','warning','error','disabled') else None,'last_count':count if type(count) is int and 0<=count<=1000000 else None,'last_checked':date_view(row.get('last_checked'))}
  url=safe_url(row.get('watch_url'));name=text('name')
  if not url or not name:return None
  return {'name':name,'country':text('country'),'watch_url':url,'availability':'not_checked'}
