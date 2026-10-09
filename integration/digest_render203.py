"""Articles-only supplied preview. Not a send/receipt; no selection input accepted."""
import html,unicodedata
from datetime import timezone,timedelta
from urllib.parse import urlsplit
from integration.digest_dates202 import select_normalized

PREVIEW_BYTE_CAP=512*1024 # Offline preview only. NOT an email budget.
ORDER=('GEOPOLITICS','CONFERENCE','TRADE','SANCTIONS','RISK','RESEARCH','GENERAL')
LABELS={'GEOPOLITICS':'Geopolitics','CONFERENCE':'Conferences & Meetings','TRADE':'Trade Activity','SANCTIONS':'Sanctions & Circulars','RISK':'Risk Signals','RESEARCH':'Research Papers & Documents','GENERAL':'Other'}

def plain(value):
 # New local helper: neutralize ALL Unicode controls/formats and whitespace.
 return ' '.join(''.join(' 'if unicodedata.category(c)in ('Cc','Cf')else c for c in value).split())

def link(value):
 # New local closed helper, inspired by news_view.safe_url, not a dependency.
 if type(value)is not str or not 1<=len(value)<=2048 or any(c.isspace()or unicodedata.category(c)in ('Cc','Cf')for c in value):raise ValueError('Whole preview held: unsafe link')
 try:
  u=urlsplit(value)
  if u.scheme!='https'or not u.hostname or u.username is not None or u.password is not None or '\\'in value:raise ValueError()
  _=u.port
 except ValueError:raise ValueError('Whole preview held: unsafe link')from None
 return value

def render_preview(rows,now,*,date_field,channel,displayed_receipts,offset_minutes,zone_label,limit=60):
 """Validate ORIGINAL rows via202; return HTML/text and selection-only identities.

Byte overflow refuses the entire preview, never silently drops a selected row.
No network, DB, events, send, mark, archive, timezone fallback or receipt proof.
"""
 if type(offset_minutes)is not int or not -1439<=offset_minutes<=1439 or type(zone_label)is not str or not 1<=len(zone_label)<=40 or plain(zone_label)!=zone_label:raise ValueError('Explicit fixed offset/label required')
 selected=select_normalized(rows,now,date_field=date_field,channel=channel,displayed_receipts=displayed_receipts,limit=limit)
 #202 already validates every row. Validate ALL links even excluded/old rows.
 for row in rows:link(row.get('url',''))
 zone=timezone(timedelta(minutes=offset_minutes));local=now.astimezone(zone)
 sign='+'if offset_minutes>=0 else'-';off=abs(offset_minutes)
 stamp=local.isoformat(timespec='microseconds')+' '+zone_label+' (UTC'+sign+f'{off//60:02d}:{off%60:02d}'+')'
 #193's7day eligible count equals pre-cap union:24h is a subset, same policy.
 preunion_count=selected['sections']['last_7days']['eligible_count']
 e=lambda s:html.escape(plain(s),quote=True)
 banner='PREVIEW, not sent; date policy and receipts unverified'
 text=[banner,'As of '+stamp,'Date field: '+date_field+'; channel: '+channel,'Snapshot: '+selected['snapshot_id'],f'Distinct articles before section caps: {preunion_count}; displayed distinct: {len(selected["displayed_union_ids"])}','Articles only; events not supplied.']
 body=['<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Digest preview</title><style>body{margin:0;background:#f1f4f8;color:#243247;font:16px Arial,sans-serif}main{max-width:760px;margin:auto;padding:20px}header,section{background:white;padding:20px;margin-bottom:18px;border-radius:10px}h1{font-size:24px}h2{font-size:21px}h3{font-size:16px}p{line-height:1.5;overflow-wrap:anywhere}a{color:#174b85;overflow-wrap:anywhere}.banner{background:#fff1ca;padding:12px;font-weight:bold}.card{border-left:4px solid #3973a6;padding:12px;margin:14px 0;background:#f6f8fb}small{color:#546278;overflow-wrap:anywhere}</style></head><body><main><header><div class="banner">'+e(banner)+'</div><h1>Digest preview</h1>'+''.join('<p>'+e(s)+'</p>'for s in text[1:])+'</header>']
 rendered=[];omitted={};counts={}
 for name,label in (('last_24h','Last 24 hours'),('last_7days','Last 7 days (includes last 24 hours)')):
  s=selected['sections'][name];items=s['rows'];n=len(items);m=s['eligible_count'];counts[name]={'shown':n,'eligible':m};omitted[name]=m-n
  body.append('<section><h2>'+label+'</h2><p>'+f'Showing {n} of {m}'+'</p>');text.extend([label,f'Showing {n} of {m}'])
  groups={}
  for row in items:
   category=row.get('category','');key=category if category in ORDER else'GENERAL';groups.setdefault(key,[]).append(row)
  if not items:body.append('<p>No eligible articles in this supplied snapshot.</p>');text.append('No eligible articles in this supplied snapshot.')
  for key in ORDER:
   if key not in groups:continue
   body.append('<h3>'+LABELS[key]+'</h3>');text.append(LABELS[key])
   for row in groups[key]:
    rendered.append(row['_id']);title=plain(row['title'])or'Untitled article';url=link(row['url']);summary=plain(row['summary']);meta=plain(row['source'])or'Source not supplied'
    body.append('<article class="card"><small>'+e(meta)+' | score '+e(str(row['score']))+'</small><h3><a href="'+html.escape(url,quote=True)+'" rel="noopener noreferrer">'+e(title)+'</a></h3><p>'+e(summary)+'</p></article>')
    text.extend([meta+' | score '+str(row['score']),title,summary,url])
  body.append('</section>')
 body.append('<footer><p>Offline browser preview only, not email-client compatibility. No dark-mode claim. 512 KiB whole-preview byte cap; overflow holds. Email delivery needs a lower independently tested size budget and inline CSS/table layout.</p></footer></main></body></html>')
 expected=[r['_id']for s in selected['sections'].values()for r in s['rows']]
 if sorted(rendered)!=sorted(expected)or set(rendered)!=set(selected['displayed_union_ids'])or sum(omitted.values())!=sum(s['eligible_count']-len(s['rows'])for s in selected['sections'].values()):raise ValueError('Preview identity self-check held')
 h=''.join(body);t='\n'.join(text)
 if len(h.encode())>PREVIEW_BYTE_CAP or len(t.encode())>PREVIEW_BYTE_CAP:raise ValueError('Whole preview byte cap held')
 return {'html':h,'text':t,'snapshot_id':selected['snapshot_id'],'selection_only_union_ids':selected['displayed_union_ids'],'selection_only_union_pre_cap_count':preunion_count,'sections':counts,'omitted_section_occurrences':omitted,'byte_cap':PREVIEW_BYTE_CAP,'delivery':False,'writes':False,'network':False,'events_supplied':False}
