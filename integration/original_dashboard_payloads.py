"""Pure mapping of explicitly supplied original dashboard payloads.

No legacy imports, file reads, clients, scheduling or network. Capture timestamps
must be supplied and zoned. Naive source status timestamps can be mapped to UTC
only with the exact source_timezone='UTC' contract for original utcnow output.
Missing status map is unavailable, not a completed cycle with zero records.
Output feeds ONLY DashboardSnapshots, never direct rendering: status/count,
labels and links remain raw until that adapter applies its safety contract.
Duplicate source names share the supplied name-keyed status entry. Non-dict
rows are dropped here without a rejected count. UTC mapping assumes the exact
original utcnow timestamp format; do not supply date-only strings (the Python
parser would interpret them as midnight).
"""
from datetime import datetime,timezone
from integration.news_view import date_view
from integration.youtube_links import supplied_video_watch,supplied_channel_watch

def captured_snapshot(items,observed_at):
 stamp=date_view(observed_at)
 if not stamp or not isinstance(items,list) or len(items)>1000:raise ValueError('Bounded rows and explicit zoned capture required')
 return {'observed_at':stamp,'items':[dict(row) for row in items if isinstance(row,dict)]}

def geo_events(rows,observed_at):
 snapshot=captured_snapshot(rows,observed_at)
 snapshot['items']=[{key:row.get(key) for key in ('name','event_date','source_url','description','category','confidence')} for row in snapshot['items']]
 return snapshot

def brics_sources(config_rows,status_map,observed_at,source_timezone=None):
 if status_map is None:raise ValueError('Source status capture unavailable')
 if not isinstance(status_map,dict) or len(status_map)>1000 or source_timezone not in (None,'UTC'):raise ValueError('Reviewed status map/timezone required')
 snapshot=captured_snapshot(config_rows,observed_at);result=[]
 for row in snapshot['items']:
  out={key:row.get(key) for key in ('name','url','country')};name=row.get('name');status=status_map.get(name) if isinstance(name,str) else None
  if isinstance(status,dict):
   checked=status.get('checked_at');stamp=date_view(checked)
   if not stamp and source_timezone=='UTC' and isinstance(checked,str):
    try:
     d=datetime.fromisoformat(checked)
     if d.tzinfo is None:stamp=date_view(d.replace(tzinfo=timezone.utc))
    except (ValueError,OverflowError):pass
   out.update(last_status=status.get('status'),last_count=status.get('count'),last_checked=stamp)
  result.append(out)
 snapshot['items']=result
 return snapshot

def brics_video_streams(config_rows,observed_at):
 # Compatibility entry point: video-only supplied configuration mapper.
 snapshot=captured_snapshot(config_rows,observed_at);items=[]
 for row in snapshot['items']:
  if row.get('type')!='video':continue
  watch=supplied_video_watch(row.get('video_id'))
  if watch:items.append({'name':row.get('name'),'country':row.get('country'),'watch_url':watch})
 snapshot['items']=items
 return snapshot

def brics_streams(config_rows,observed_at):
 snapshot=captured_snapshot(config_rows,observed_at);items=[]
 for row in snapshot['items']:
  kind=row.get('type')
  watch=supplied_video_watch(row.get('video_id')) if kind=='video' else supplied_channel_watch(row.get('channel_id')) if kind=='channel' else None
  if watch:items.append({'name':row.get('name'),'country':row.get('country'),'watch_url':watch})
 snapshot['items']=items
 return snapshot
