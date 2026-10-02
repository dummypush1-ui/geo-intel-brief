"""Common read view over supplied rows. No database client or legacy imports."""
from datetime import datetime,timezone
from integration.dashboard_model import signals
from copy import deepcopy
import hashlib
from urllib.parse import urlsplit,urlunsplit

def safe_url(value):
 try:
  u=urlsplit(str(value or ''))
  if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or any(c.isspace() or ord(c)<32 for c in str(value)):return None
  return urlunsplit((u.scheme,u.netloc.lower(),u.path or '/',u.query,''))
 except ValueError:return None

def date_view(value):
 try:
  d=value if isinstance(value,datetime) else datetime.fromisoformat(str(value).replace('Z','+00:00'))
  if d.tzinfo is None:return None
  return d.astimezone(timezone.utc).isoformat()
 except (ValueError,TypeError,OverflowError):return None

def normalize_row(row,project):
 if project not in ('geo','brics'):raise ValueError('Unknown project')
 url=safe_url(row.get('url'))
 if not url or not str(row.get('title','')).strip():return None
 return {'article_key':hashlib.sha256((project+'\n'+url).encode()).hexdigest(),'project':project,'legacy_id':str(row.get('id',row.get('_id','')) if project=='brics' else row.get('_id',row.get('id',''))),'mongo_id':str(row.get('_id','')),'url':url,'original_url':row['url'],
  'title':str(row['title']),'summary':str(row.get('summary') or ''),'source':str(row.get('source') or ''),
  'original_country':str(row.get('country') or ''),'category':str(row.get('category') or 'GENERAL'),
  'published_at':date_view(row.get('published')),'collected_at':date_view(row.get('created_at') or row.get('collected_at')),
  **signals(row,project),'backup_url':safe_url(row.get('telegram_url')),'emailed':deepcopy(row.get('emailed'))}

def views(rows_by_project):
 return [view for project,rows in rows_by_project.items() for row in rows if (view:=normalize_row(row,project))]
