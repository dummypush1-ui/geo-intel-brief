"""Pure offline serializers for original CSV contracts, not a live export.

Input is a supplied raw public-field snapshot in ORIGINAL reader order. Geo:
score DESC, published DESC; BRICS: collected_at DESC. This module does not sort
or fetch. At most10000 snapshot rows are accepted; full-history paging remains
separate. Source pins and differential tests document the original contract.
"""
import csv
import io
import re
from .export import csv_cell, ExportRequestError, CELL_LIMIT

GEO_FIELDS=('title','source','category','risk_level','score','credibility','country',
            'corroboration','published','created_at','url','summary')
BRICS_FIELDS=('title','url','source','country','category','published','collected_at','corroborated_by')
DEFAULT_CRITICAL=('attack','explosion','resign','coup','ceasefire','sanctions')
# No original modules are imported, and no environment config is read.
# Geo HTTP auth/deletion changed in P0; export_csv body remains unchanged.
SOURCE_PINS={
 'intelligence/geo/web.py':'3d83ca84984f5c01c0a8c53d02ae5a92e976e53f19f87f8b238a31d9c42a2cb3',
 'intelligence/brics/web.py':'1adebf8baaea16ee305afb16fd21717c5abf0635279a7dbedfa985ff21fe5997',
 'intelligence/brics/processing/classifier.py':'349a322ecc525671617bcdeaa60d5c3fb6547988fb736e361d74d673f27ba76a'}

def original_snapshot(rows,project,args=None,*,stamp='20000101_000000',critical_keywords=DEFAULT_CRITICAL,max_bytes=20*1024*1024):
 """Return bytes, headers and metadata. No live source or production activation.

 Columns, original filtering and cap-before-filter behavior are preserved.
 Intentional safety differences: strict query names/scalars, nonpositive BRICS
 limits rejected, spreadsheet formula defense/8k cell cap, unknown fields never
 read, private no-store scope header. These are documented, not full parity.
 """
 if project not in ('geo','brics'):raise ExportRequestError('project')
 if type(max_bytes) is not int or not 128<=max_bytes<=20*1024*1024:raise ValueError('byte budget')
 if project=='brics' and (type(stamp) is not str or not re.fullmatch(r'\d{8}_\d{6}',stamp)):raise ExportRequestError('stamp')
 if type(rows) not in (list,tuple) or len(rows)>10000:raise ValueError('snapshot bound')
 args={} if args is None else args
 allowed={'category'} if project=='geo' else {'category','country','q','critical_only','limit'}
 if type(args) is not dict or any(type(k) is not str or k not in allowed for k in args):raise ExportRequestError('arguments')
 for v in args.values():
  if type(v) is not str or len(v)>200 or any(ord(c)<32 for c in v):raise ExportRequestError('scalar')
 if type(critical_keywords) not in (list,tuple) or len(critical_keywords)>100 or any(type(k) is not str or not k.strip() or len(k)>100 for k in critical_keywords):raise ValueError('critical keywords')
 fields=GEO_FIELDS if project=='geo' else BRICS_FIELDS
 limit=1000000
 if project=='brics':
  try:limit=min(int(args.get('limit','1000')),5000)
  except ValueError:limit=1000
  if limit<1:raise ExportRequestError('limit')
 category=args.get('category','')
 selected=[]
 for r in rows[:limit]:
  if type(r) is not dict or len(r)>100 or any(type(k) is not str for k in r):raise ValueError('plain bounded row')
  # Copy only contract fields plus summary, used by original critical predicate.
  clean={k:r.get(k) for k in set(fields)|{'summary'}}
  for k,v in clean.items():
   if k=='corroborated_by' and type(v) is list:
    if len(v)>100 or any(type(x) is not str or len(x)>8000 for x in v):raise ValueError('corroboration list')
   elif v is not None and type(v) not in (str,int,float,bool):raise ValueError('scalar fields')
   strings=v if type(v) is list else [v]
   for text_value in strings:
    if type(text_value) is str:
     if any(0xD800<=ord(c)<=0xDFFF for c in text_value):raise ExportRequestError('unencodable field')
     if len(text_value)>32000:raise ValueError('field bound')
  if project=='geo':
   if category and (clean['category'] or 'GENERAL')!=category:continue
  else:
   def text(k):return str(clean.get(k) or '')
   if category.strip() and text('category').lower()!=category.strip().lower():continue
   if args.get('country','').strip() and text('country').lower()!=args['country'].strip().lower():continue
   q=args.get('q','').strip().lower()
   if q and q not in (text('title')+' '+text('source')+' '+text('country')).lower():continue
   if args.get('critical_only') in ('1','true','yes') and not any(k.strip().lower() in (text('title')+' '+text('summary')).lower() for k in critical_keywords):continue
  selected.append(clean)
 buf=io.StringIO(newline='');writer=csv.writer(buf);writer.writerow(fields)
 output=bytearray(buf.getvalue().encode());cell_cut=False
 if len(output)>max_bytes:raise ExportRequestError('output budget')
 for r in selected:
  values=[]
  for k in fields:
   v=r.get(k)
   if project=='brics' and k=='corroborated_by':v='; '.join(v) if type(v) is list else v or ''
   if v is not None and len(str(v))>CELL_LIMIT:cell_cut=True
   values.append(csv_cell(v))
  buf.seek(0);buf.truncate(0);writer.writerow(values)
  try:part=buf.getvalue().encode('utf-8')
  except UnicodeEncodeError:raise ExportRequestError('unencodable field') from None
  if len(output)+len(part)>max_bytes:raise ExportRequestError('output budget')
  output.extend(part)
 if project=='geo':
  # Category filename uses a bounded safe slug, rather than original raw value.
  slug=re.sub('[^A-Za-z0-9_-]','_',category)
  filename='geonews_export'+('_'+slug if category else '')+'.csv'
 else:
  filename='brics_articles_'+stamp+'.csv'
 return bytes(output),{'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="'+filename+'"','Cache-Control':'no-store','X-Export-Scope':'supplied_snapshot_not_full_database','X-Export-Truncated':'true' if len(rows)>limit or cell_cut else 'false'}, {'read':min(len(rows),limit),'rows':len(selected),'source_order_required':True,'cells_truncated':cell_cut,'bytes':len(output)}
