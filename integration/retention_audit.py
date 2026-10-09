"""Pure supplied-fixture retention audit. No deletion safety or send readiness.

Original identities forbidden in supplied contract and never emitted. Ordinals
are fixture-local only. Original pure formatters loaded with exact source pins.
"""
import ast,hashlib,json,math
from pathlib import Path
from integration.news_view import safe_url
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
PINS={'backup': ('intelligence/geo/reports/telegram_backup.py', '0a0f7f0dcf7955e8e8a7cf1981f8669fc63180f0f2c18152131c9dc211de0b0c', ('_format_full_record', '_split_into_batches')), 'summary': ('intelligence/geo/reports/telegram_archive.py', '643bc27e2bfc65210fa3f3f065835269951e0e7ff69e6266e5c8b35e8994f684', ('_format_article_line', '_build_batches'))}
FIELDS={'title','summary','source','category','published','url','country','risk_level','score','credibility','corroboration','created_at','telegram_url'}

def _functions(kind):
 path,pin,names=PINS[kind];source=(ROOT/path).read_bytes()
 if hashlib.sha256(source).hexdigest()!=pin:raise ValueError('Original formatter changed')
 tree=ast.parse(source);selected=[n for n in tree.body if type(n) is ast.FunctionDef and n.name in names]
 if {n.name for n in selected}!=set(names) or any(type(n) in (ast.Import,ast.ImportFrom) for f in selected for n in ast.walk(f)):raise ValueError('Pure formatter required')
 scope={'safe_url':safe_url,'__builtins__':{'len':len,'enumerate':enumerate},'TELEGRAM_MSG_LIMIT':3500}
 exec(compile(ast.Module(body=selected,type_ignores=[]),path,'exec'),scope)
 return scope

def audit(rows,now,*,days=60):
 if type(rows) is not list or len(rows)>1000:raise ValueError('Bounded inert fixture required')
 if type(now) is not datetime or type(now.tzinfo) is not timezone or type(days) is not int or not 1<=days<=3650:raise ValueError('Fixed clock and days required')
 now=now.astimezone(timezone.utc);cutoff=now-timedelta(days=days)
 clean=[];budget=0
 for row in rows:
  if type(row) is not dict or any(type(k) is not str or k not in FIELDS for k in row):raise ValueError('Closed inert fixture fields')
  copied={}
  for k,v in row.items():
   if v is None:copied[k]='' # explicit fixture normalization, timestamp still unclassifiable
   elif type(v) is str and len(v)<=16000 and not any(0xD800<=ord(c)<=0xDFFF for c in v):copied[k]=v
   elif type(v) in (int,float) and math.isfinite(v) and abs(v)<=10**12:copied[k]=v
   else:raise ValueError('Bounded inert fixture scalar')
  # Original formatters slice/string-interpolate specific fields. Require text there.
  if any(k in copied and type(copied[k]) is not str for k in FIELDS-{'score','corroboration'}) or any(k in copied and type(copied[k]) not in (int,float) for k in ('score','corroboration')):raise ValueError('Formatter text schema')
  budget+=len(json.dumps(copied,ensure_ascii=False,separators=(',',':')).encode())+1
  if budget>2*1024*1024:raise ValueError('Fixture byte budget')
  clean.append(copied)
 backup=_functions('backup');summary=_functions('summary')
 records=[backup['_format_full_record'](r) for r in clean]
 lines=[summary['_format_article_line'](r) for r in clean]
 batches=backup['_split_into_batches'](clean)
 counts=[0]*len(clean);batch_info=[]
 for n,(span,text) in enumerate(batches,1):
  start,end=span
  for i in range(start,end):counts[i]+=1
  batch_info.append({'ordinal':n,'input_count':end-start,'actual_chars':len(text),'estimator_chars':sum(len(records[i])+2 for i in range(start,end)),'over3500':len(text)>3500,'empty':not text,'send_state':'not_executed'})
 summary_batches=summary['_build_batches'](clean)
 details=[]
 for i,r in enumerate(clean):
  raw=r.get('created_at','');state='unclassifiable';missing_or_null='created_at' not in rows[i] or rows[i]['created_at'] is None
  lexical=False if missing_or_null else raw<cutoff.isoformat();discrepancy=None
  try:
   stamp=datetime.fromisoformat(raw.replace('Z','+00:00'))
   if stamp.tzinfo is None:raise ValueError()
   old=stamp.astimezone(timezone.utc)<cutoff;state='before_cutoff' if old else 'at_or_after_cutoff'
   lexical=raw<cutoff.isoformat();discrepancy=lexical!=old
  except (ValueError,OverflowError,AttributeError):pass
  title=r.get('title','');text=r.get('summary','')
  details.append({'ordinal':i+1,'missing_or_null':missing_or_null,'age_classification':state,'source_lexical_selected':lexical,'lexical_time_discrepancy':discrepancy,'missing_backup_hint':not r.get('telegram_url'),'backup_hint_verified':False,'input_accounting_count':counts[i],'full_record_empty':not records[i],'single_record_over3500':len(records[i])>3500,'summary_title_chars_omitted':max(0,len(title)-120),'summary_text_chars_not_found':len(text) if text and text not in lines[i] else 0,'full_record_title_substring_found':title in records[i] if title else True,'full_record_summary_substring_found':text in records[i] if text else True,'summary_title_prefix_found':title[:120] in lines[i] if title else True,'send_state':'not_executed'})
 return {'scope':'supplied_fixture_original_fidelity_audit','deletion_safety':'not_established','delivery':'not_executed','backup_losslessness':'not_established','cutoff':cutoff.isoformat(),'counts':{'inputs':len(clean),'source_would_select':sum(x['source_lexical_selected'] for x in details),'unclassifiable_missing_or_null':sum(x['missing_or_null'] for x in details),'unclassifiable':sum(x['age_classification']=='unclassifiable' for x in details),'unclassifiable_source_would_select':sum(x['age_classification']=='unclassifiable' and x['source_lexical_selected'] for x in details),'before_cutoff':sum(x['age_classification']=='before_cutoff' for x in details),'at_or_after_cutoff':sum(x['age_classification']=='at_or_after_cutoff' for x in details),'lexical_time_discrepancy':sum(x['lexical_time_discrepancy'] is True for x in details),'missing_backup_hint':sum(x['missing_backup_hint'] for x in details),'single_record_over3500':sum(x['single_record_over3500'] for x in details),'summary_title_chars_omitted':sum(x['summary_title_chars_omitted'] for x in details),'summary_text_chars_not_found':sum(x['summary_text_chars_not_found'] for x in details)},'selection_is_eligibility':False,'cutoff_source_format_match':'unverified_database_now_clock','value_checks':'structural_substring_only_not_fidelity_proof','backup_batches':batch_info,'summary_batch_info':[{'chars':len(t),'over3500':len(t)>3500,'empty':not t} for t in summary_batches],'dropped_input_count':sum(c==0 for c in counts),'duplicated_input_count':sum(c>1 for c in counts),'failed_input_count':None,'partial_input_count':None,'delivery_accounting_scope':'no_send_or_receipt_evidence','html_archive_name':now.strftime('%Y-%m-%d')+'.html','html_archive_clock_scope':'UTC_fixture_not_original_server_local','html_archive_collision':'original_same_local_day_overwrites','apps_script_archive':'original_digest_data_does_not_call_archive'}
