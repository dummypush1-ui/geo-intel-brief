"""Injected read-only original-dashboard snapshots. No clients or live imports.

Source status is reported as a captured observation, never a current health
claim. Stream URLs are outbound links only; this adapter does not embed video.
Unavailable differs from an empty verified snapshot.
"""
from datetime import date
from urllib.parse import urlsplit,urlunsplit
import ipaddress,re,json
from integration.news_view import safe_url,date_view

class DashboardSnapshots:
 def __init__(self,readers,verified=False,allowed_hosts=None):
  if verified is not True:raise ValueError('Reviewed snapshot readers required')
  if not isinstance(readers,dict) or any(k not in ('geo_events','brics_sources','brics_streams') or not callable(v) for k,v in readers.items()):raise ValueError('Exact read-only snapshot readers required')
  allowed_hosts=allowed_hosts or {}
  if not isinstance(allowed_hosts,dict) or any(k not in readers or not isinstance(v,(list,tuple)) or not v for k,v in allowed_hosts.items()):raise ValueError('Exact per-panel public host allowlists required')
  self.hosts={}
  for key in readers:
   hosts=allowed_hosts.get(key,[])
   if not hosts or any(not self.public_host(h) for h in hosts):raise ValueError('Reviewed public hosts required for each reader')
   self.hosts[key]=frozenset(hosts)
  self.readers=dict(readers)
 @staticmethod
 def public_host(host):
  if not isinstance(host,str) or len(host)>253 or host!=host.lower() or not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*',host) or '.' not in host or host.endswith(('.localhost','.local','.internal','.test','.invalid','.example')):return False
  # Browsers also interpret shortened, octal and hex IPv4 forms as IPs.
  if re.fullmatch(r'(?:[0-9]+|0x[0-9a-f]*)',host.split('.')[-1]):return False
  if all(re.fullmatch(r'(?:[0-9]+|0x[0-9a-f]+)',label) for label in host.split('.')):return False
  try:ipaddress.ip_address(host);return False
  except ValueError:pass
  return all(1<=len(label)<=63 and not label.startswith('-') and not label.endswith('-') for label in host.split('.'))
 def link(self,key,value):
  url=safe_url(value)
  if not url:return None
  u=urlsplit(url)
  try:port=u.port
  except ValueError:return None
  if u.hostname not in self.hosts[key] or port not in (None,443,80):return None
  # Query values can hold tokens or private context; do not silently rewrite
  # a watch link into a different resource. Query-bearing links are withheld.
  if re.search(r'%(?:e2%80%(?:8e|8f|aa|ab|ac|ad|ae)|e2%81%(?:a6|a7|a8|a9)|d8%9c)',u.path,re.I):return None
  if u.query or any(c in u.path for c in ('\u061c','\u200e','\u200f','\u202a','\u202b','\u202c','\u202d','\u202e','\u2066','\u2067','\u2068','\u2069')):return None
  netloc=u.hostname if port in (None,443 if u.scheme=='https' else 80) else u.hostname+':'+str(port)
  return urlunsplit((u.scheme,netloc,u.path,'',''))
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
    order=lambda r:(r.get('event_date',''),r['name'].casefold(),r.get('country','').casefold(),r.get('source_url',r.get('url',r.get('watch_url',''))),json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=True))
    items.sort(key=order)
    result['panels'][key]={'state':'supplied_snapshot','observed_at':date_view(snapshot['observed_at']),'items':items[:100],'rejected_count':rejected,'truncated':len(items)>100}
   except Exception:result['panels'][key]={'state':'unavailable','items':[]}
  return result
 def normalize(self,key,row):
  if not isinstance(row,dict):return None
  def text(k):
   v=row.get(k);return v[:2000] if isinstance(v,str) else ''
  if key=='geo_events':
   try:day=date.fromisoformat(text('event_date')).isoformat()
   except ValueError:return None
   url=self.link(key,row.get('source_url'));name=text('name')
   if not name or not url:return None
   return {'name':name,'event_date':day,'source_url':url,'description':text('description')}
  if key=='brics_sources':
   name=text('name');url=self.link(key,row.get('url'))
   if not name or not url:return None
   status=row.get('last_status');count=row.get('last_count')
   return {'name':name,'url':url,'country':text('country'),'last_status':status if isinstance(status,str) and status in ('ok','warning','error','disabled') else None,'last_count':count if type(count) is int and 0<=count<=1000000 else None,'last_checked':date_view(row.get('last_checked'))}
  url=self.link(key,row.get('watch_url'));name=text('name')
  if not url or not name:return None
  return {'name':name,'country':text('country'),'watch_url':url,'availability':'not_checked'}
