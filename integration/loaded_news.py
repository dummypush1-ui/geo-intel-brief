"""Filter/sort/export the supplied news view only, never a full-store export.

CSV cells are bounded and formula-like leading values are prefixed with an
apostrophe, including operators hidden behind whitespace/format characters.
The same selection drives JSON and CSV. No clients, writes or live lookups.
"""
import csv,io,unicodedata
SORTS={'':'newest','newest':'newest','title':'title','country':'country','score':'score','corroboration':'corroboration'}
LIMIT=100
FIELDS=('project','title','source','original_country','category','published_at','collected_at','risk_level','credibility','score','corroboration_count','url','summary')
def selection(rows,project='',query='',category='',country='',sort='newest'):
 if project not in ('','geo','brics') or sort not in SORTS:raise ValueError('Invalid project or sort')
 sort=SORTS[sort]
 if (sort=='score' and project!='geo') or (sort=='corroboration' and project!='brics'):raise ValueError('Project-specific sort required')
 q=query[:200].casefold();country=country[:100].casefold();category=category[:100]
 matched=[r for r in rows if (not project or r['project']==project) and (not category or r['category']==category) and (not country or r['original_country'].casefold()==country) and (not q or q in (r['title']+' '+r['summary']+' '+r['source']+' '+r['original_country']).casefold())]
 # First establish deterministic newest ordering for tie breaks and defaults.
 matched.sort(key=lambda r:(r['title'].casefold(),r['article_key']))
 matched.sort(key=lambda r:r['collected_at'] or '',reverse=True)
 if sort in ('title','country'):matched.sort(key=lambda r:(r['title'] if sort=='title' else r['original_country']).casefold())
 if sort in ('score','corroboration'):
  key='score' if sort=='score' else 'corroboration_count'
  matched.sort(key=lambda r:(r.get(key) is not None,r.get(key) if r.get(key) is not None else 0),reverse=True)
 return {'items':matched[:LIMIT],'scope':'loaded_read_view','limit':LIMIT,'sort':sort,'truncated':len(matched)>LIMIT,'not_full_database_export':True}

def csv_cell(value):
 if value is None:return ''
 text=str(value)[:8000].replace('\x00','')
 text=''.join('\ufffd' if unicodedata.category(c)=='Cs' else c for c in text)
 probe=text.lstrip()
 while probe and unicodedata.category(probe[0])[0] in ('Z','C'):probe=probe[1:]
 if text.startswith(('\t','\r','\n')) or probe.startswith(('=','+','-','@')):text="'"+text
 return text

def sample_csv(result):
 buf=io.StringIO(newline='');writer=csv.writer(buf,lineterminator='\r\n');writer.writerow(FIELDS)
 for row in result['items']:writer.writerow([csv_cell(row.get(key)) for key in FIELDS])
 return buf.getvalue()
