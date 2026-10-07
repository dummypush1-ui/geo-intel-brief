"""Pure synthetic receipt fixture. No send, storage, retries or reconciliation.
Validation detects malformed fixtures, not hostile forgery or durable authority.
"""
import hashlib
from collector110_prep.input_budget import capture
from .packing import units
class ReceiptRefused(ValueError):pass

def _snap(value):
 try:return capture(value)['captured']
 except (ValueError,TypeError,OverflowError,UnicodeError) as e:raise ReceiptRefused('Bounded JSON fixture') from e

def _digest(x):
 return type(x)is str and len(x)==64 and all(c in '0123456789abcdef'for c in x)

def validate_plan(plan):
 p=_snap(plan)
 keys={'scope','pieces','manifest','provider_limit_verified','sent','delivery','production_ready'}
 if type(p)is not dict or set(p)!=keys or p['scope']!='inactive_synthetic_full_record_packing' or any(p[k] is not False for k in ('provider_limit_verified','sent','delivery','production_ready')):raise ReceiptRefused('Fixed inactive plan')
 pieces=p['pieces'];manifest=p['manifest']
 if type(pieces)is not list or type(manifest)is not list or len(manifest)>1000:raise ReceiptRefused('Bounded plan lists')
 cursor=0
 for ai,m in enumerate(manifest):
  if type(m)is not dict or set(m)!={'article_index','required_piece_indices','record_sha256','record_utf16_units'} or type(m['article_index'])is not int or m['article_index']!=ai or not _digest(m['record_sha256']):raise ReceiptRefused('Ordered manifest identity')
  req=m['required_piece_indices']
  if type(req)is not list or not req or any(type(n)is not int for n in req) or req!=list(range(cursor,cursor+len(req))) or cursor+len(req)>len(pieces):raise ReceiptRefused('Complete nonoverlapping manifest')
  texts=[]
  for part,idx in enumerate(req,1):
   x=pieces[idx]
   if type(x)is not dict or set(x)!={'article_index','part','total','text','payload','payload_sha256','utf16_units'}:raise ReceiptRefused('Fixed piece fields')
   if any(type(x[k])is not int for k in ('article_index','part','total','utf16_units')) or (x['article_index'],x['part'],x['total'])!=(ai,part,len(req)):raise ReceiptRefused('Ordered piece identity')
   if type(x['payload'])is not str or type(x['text'])is not str or not _digest(x['payload_sha256']):raise ReceiptRefused('Piece content')
   header='[SYNTHETIC NOT FOR DELIVERY] Article '+str(ai+1)+' piece '+str(part)+'/'+str(len(req))+'\n'
   try:
    ok=x['text']==header+x['payload'] and x['payload_sha256']==hashlib.sha256(x['payload'].encode()).hexdigest() and x['utf16_units']==units(x['text']) and 0<x['utf16_units']<=3500
   except UnicodeError as e:raise ReceiptRefused('Valid Unicode')from e
   if not ok:raise ReceiptRefused('Piece integrity and budget')
   texts.append(x['payload'])
  full=''.join(texts)
  if type(m['record_utf16_units'])is not int or m['record_utf16_units']!=units(full) or hashlib.sha256(full.encode()).hexdigest()!=m['record_sha256']:raise ReceiptRefused('Lossless full record')
  cursor+=len(req)
 if cursor!=len(pieces):raise ReceiptRefused('No unassigned pieces')
 return p

def prepare_state(plan):
 p=validate_plan(plan)
 states=[{'piece_index':n,'digest':x['payload_sha256'],'state':'planned','message_id':None}for n,x in enumerate(p['pieces'])]
 return {'scope':'inactive_synthetic_receipt_state','plan':p,'states':states,'delivery':False,'persistent':False}

def validate_state(state):
 s=_snap(state)
 if type(s)is not dict or set(s)!={'scope','plan','states','delivery','persistent'} or s['scope']!='inactive_synthetic_receipt_state' or s['delivery']is not False or s['persistent']is not False:raise ReceiptRefused('Fixed inactive state')
 p=validate_plan(s['plan']);rows=s['states'];ids=set()
 if type(rows)is not list or len(rows)!=len(p['pieces']):raise ReceiptRefused('State cardinality')
 for i,r in enumerate(rows):
  if type(r)is not dict or set(r)!={'piece_index','digest','state','message_id'} or type(r['piece_index'])is not int or r['piece_index']!=i or r['digest']!=p['pieces'][i]['payload_sha256'] or type(r['state'])is not str or r['state']not in ('planned','sending','acknowledged','failed','unknown'):raise ReceiptRefused('State identity')
  mid=r['message_id']
  if r['state']=='acknowledged':
   if type(mid)is not int or not 1<=mid<=2**31-1 or mid in ids:raise ReceiptRefused('Distinct confirmed fixture ids')
   ids.add(mid)
  elif mid is not None:raise ReceiptRefused('No id before ack')
 return s

def transition(state,index,event,*,message_id=None):
 out=validate_state(state)
 if type(index)is not int or not 0<=index<len(out['states']):raise ReceiptRefused('Synthetic piece index')
 row=out['states'][index];old=row['state']
 permitted={'planned':{'begin':'sending'},'sending':{'ack':'acknowledged','known_failure':'failed','uncertain':'unknown'}}
 if type(event)is not str or event not in permitted.get(old,{}):raise ReceiptRefused('No replay/retry/unlock')
 if event=='ack':
  if type(message_id)is not int or not 1<=message_id<=2**31-1:raise ReceiptRefused('Synthetic confirmed message id')
 elif message_id is not None:raise ReceiptRefused('No id without ack')
 row['state']=permitted[old][event];row['message_id']=message_id
 return validate_state(out)

def coverage(state):
 out=validate_state(state);rows=out['states'];articles=[]
 for m in out['plan']['manifest']:
  required=m['required_piece_indices'];done=sum(rows[n]['state']=='acknowledged'for n in required)
  articles.append({'article_index':m['article_index'],'required':len(required),'acknowledged':done,'complete':done==len(required),'unknown':any(rows[n]['state']=='unknown'for n in required)})
 return {'scope':'synthetic_coverage_not_delivery','articles':articles,'ready_for_live':False,'checkpoint_retention_required':any(not a['complete']for a in articles)}
