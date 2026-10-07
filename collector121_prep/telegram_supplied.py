"""Inactive original Telegram attach contract using synthetic response fixtures.
No actual send, credentials, clients or article-ref write. NOT FOR DELIVERY.
"""
import ast,hashlib
from pathlib import Path
from collector110_prep.input_budget import capture
ROOT=Path(__file__).resolve().parents[1]
PIN='0a0f7f0dcf7955e8e8a7cf1981f8669fc63180f0f2c18152131c9dc211de0b0c'
class BackupRefused(ValueError):pass

def prepare_supplied_backup(records,outcomes,*,synthetic=False,chat='@fixture_channel',configured=True):
 if synthetic is not True or type(chat)is not str or chat not in ('@fixture_channel','-1001234567890','unrecognized')or type(configured)is not bool:raise BackupRefused('Synthetic fixture only')
 if type(records)is not list or len(records)>1000 or type(outcomes)is not list or len(outcomes)>1000:raise BackupRefused('Bounded fixture records')
 snap=capture({'records':records,'outcomes':outcomes})['captured'];records=snap['records'];outcomes=snap['outcomes']
 allowed={'title','url','source','category','summary','score','risk_level','country','credibility','corroboration','published','telegram_message_id','telegram_url'}
 for r in records:
  if type(r)is not dict or set(r)-allowed:raise BackupRefused('Closed article fixture')
  if any(type(r.get(k,''))is not str for k in ('title','url','source','category','summary','risk_level','country','credibility','published')):raise BackupRefused('Exact fixture article strings')
  if 'telegram_message_id'in r and r['telegram_message_id']is not None or 'telegram_url'in r and r['telegram_url']!='':raise BackupRefused('No caller-seeded refs')
 for o in outcomes:
  if type(o)is not dict or set(o)!={'state','message_id'}or o['state']not in ('ok','http_error','exception','json_error')or type(o['message_id'])is not int or not 1<=o['message_id']<=2**31-1:raise BackupRefused('Exact fixture response')
 raw=(ROOT/'intelligence/geo/reports/telegram_backup.py').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=PIN:raise BackupRefused('Original Telegram drift')
 tree=ast.parse(raw);defs=[n for n in tree.body if type(n)is ast.FunctionDef]
 if {n.name for n in defs}!={'_api','_permalink','_format_full_record','_split_into_batches','attach_backup_refs'}:raise BackupRefused('Original definitions')
 for node in defs:
  if node.decorator_list or any(isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.With))for n in ast.walk(node)):raise BackupRefused('Original AST structure')
 trace=[];errors=[]
 class Response:
  text='synthetic HTTP failure'
  def __init__(self,o):self.o=o;self.status_code=200 if o['state']in ('ok','json_error')else 500
  def json(self):
   if self.o['state']=='json_error':raise ValueError('Synthetic JSON fault')
   return {'result':{'message_id':self.o['message_id']}}
 class Requests:
  def post(self,url,*,data,timeout):
   if len(trace)>=len(outcomes):raise BackupRefused('Missing supplied response')
   o=outcomes[len(trace)];trace.append({'span_index':len(trace),'fixture_api_method':url.rsplit('/',1)[1],'text':data['text'],'timeout':timeout,'chat':data['chat_id'],'utf16_units':len(data['text'].encode('utf-16-le'))//2})
   if o['state']=='exception':raise ValueError('Synthetic transport fault')
   return Response(o)
 scope={'__builtins__':{'len':len,'enumerate':enumerate,'print':lambda *a:errors.append(1),'Exception':Exception},'TELEGRAM_MSG_LIMIT':3500,'TELEGRAM_BACKUP_BOT_TOKEN':'FIXTURE_TOKEN'if configured else '', 'TELEGRAM_BACKUP_CHAT_ID':chat if configured else '', 'requests':Requests()}
 exec(compile(ast.Module(body=defs,type_ignores=[]),'original-synthetic-backup','exec'),scope)
 batches=scope['_split_into_batches'](records)
 expected=len(batches)if configured and records else 0
 if len(outcomes)!=expected:raise BackupRefused('Missing or unused synthetic response')
 mapped=scope['attach_backup_refs'](records)
 capture({'mapped':mapped,'trace':trace})
 return {'scope':'inactive_original_telegram_synthetic_NOT_FOR_DELIVERY','synthetic':True,
         'mapped_fixture_records':mapped,'fixture_send_trace':trace,'coarse_error_count':len(errors),
         'oversize_fixture_batches':sum(t['utf16_units']>4096 for t in trace),
         'refs_are_synthetic':True,'sent':False,'delivery':False,'writes':False,'network':False,'production_ready':False,
         'pending_gates':['real_telegram_permission_identity','durable_send_reconciliation','live_provider_limits','packing_overflow','article_ref_write']}
