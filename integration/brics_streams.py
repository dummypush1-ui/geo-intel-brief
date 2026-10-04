"""Original BRICS stream CRUD contract over an injected fixture-only store.

No YAML writes, DB clients, timers or live imports. Stricter YouTube grammar
retains watch/short/live/embed input forms; arbitrary original bare IDs fail.
"""
import re,threading,unicodedata
from urllib.parse import urlsplit,parse_qs
from copy import deepcopy
from integration.youtube_links import VIDEO,CHANNEL

def video_id(value):
 if not isinstance(value,str) or len(value)>200:return None
 if any(c.isspace() or unicodedata.category(c).startswith('C') for c in value):return None
 if VIDEO.fullmatch(value):return value
 if any(c in value for c in ('\\','%','#')):return None
 try:u=urlsplit(value)
 except ValueError:return None
 if u.scheme!='https' or u.netloc not in ('www.youtube.com','youtube.com','youtu.be'):return None
 if u.netloc=='youtu.be' and not u.query:vid=u.path[1:]
 elif u.netloc in ('www.youtube.com','youtube.com') and u.path=='/watch':
  if not re.fullmatch(r'v=[A-Za-z0-9_-]{11}',u.query):return None
  args=parse_qs(u.query,keep_blank_values=True)
  if set(args)!={'v'} or len(args['v'])!=1:return None
  vid=args['v'][0]
 elif u.netloc in ('www.youtube.com','youtube.com') and not u.query and re.fullmatch(r'/(?:live|embed)/[A-Za-z0-9_-]{11}',u.path):vid=u.path.split('/')[-1]
 else:return None
 return vid if VIDEO.fullmatch(vid) else None

def label(value,default=None):
 if value is None and default is not None:value=default
 if not isinstance(value,str) or not value.strip() or len(value)>80 or any(unicodedata.category(c).startswith('C') for c in value) or not any(unicodedata.category(c)[0] in 'LNPS' for c in value if c not in 'ᅟᅠ⠀ㅤﾠ'):raise ValueError('Visible short label required')
 return value.strip()

def country(value):
 if value is None:return 'Custom'
 if not isinstance(value,str):raise ValueError('Country must be a string')
 return label(value) if value.strip() else 'Custom'

def name_key(value):return label(value).casefold()

def enrich(raw):
 if type(raw) is not dict:raise ValueError('Plain stream object required')
 s={k:raw[k] for k in ('name','country','type','video_id','channel_id') if k in raw}
 s['name']=label(s.get('name'));s['country']=country(s.get('country'))
 if s.get('type')=='video':
  vid=video_id(s.get('video_id')); 
  if not vid:raise ValueError('Valid YouTube video required')
  s.pop('channel_id',None);s['video_id']=vid;s['watch_url']='https://www.youtube.com/watch?v='+vid;s['embed_url']='https://www.youtube-nocookie.com/embed/'+vid
 elif s.get('type')=='channel' and isinstance(s.get('channel_id'),str) and CHANNEL.fullmatch(s['channel_id']):
  s.pop('video_id',None);cid=s['channel_id'];s['watch_url']='https://www.youtube.com/channel/'+cid+'/live';s['embed_url']='https://www.youtube-nocookie.com/embed/live_stream?channel='+cid
 else:raise ValueError('Valid stream type required')
 return deepcopy(s)

class FixtureStreams:
 fixture_only=True
 def __init__(self,rows):
  if type(rows) is not list or len(rows)>20:raise ValueError('Up to20 fixture streams')
  self._lock=threading.Lock();self._rows=[enrich(r) for r in rows]
  if len({name_key(r['name']) for r in self._rows})!=len(rows):raise ValueError('Unique names required')
 def load(self):
  with self._lock:return deepcopy(self._rows)
 def add(self,name,country,link):
  row=enrich({'name':name,'country':country,'type':'video','video_id':link})
  with self._lock:
   if len(self._rows)>=20:raise ValueError('Up to20 streams')
   if any(name_key(s['name'])==name_key(row['name']) for s in self._rows):raise ValueError('Stream name already exists')
   self._rows.append(row)
  return deepcopy(row)
 def remove(self,name):
  name=name_key(name)
  with self._lock:
   kept=[r for r in self._rows if name_key(r['name'])!=name]
   removed=len(kept)!=len(self._rows);self._rows=kept;return removed
