"""Scratch synthetic UTF16 packing, not real send/provider limit assertion."""
import hashlib,math
from collector110_prep.input_budget import capture
from integration.telegram_format_audit import _functions
import ast
class PackingRefused(ValueError):pass

def units(text):return len(text.encode('utf-16-le'))//2

def _split(text,budget):
 chunks=[];current=[];used=0
 for char in text:
  cost=2 if ord(char)>65535 else 1
  if used+cost>budget:
   chunks.append(''.join(current));current=[];used=0
  current.append(char);used+=cost
 if current:chunks.append(''.join(current))
 return chunks or ['']

def pack_synthetic(records,*,synthetic=False,unit_limit=3500):
 if synthetic is not True or type(unit_limit)is not int or not 256<=unit_limit<=3500 or type(records)is not list or len(records)>1000:raise PackingRefused('Bounded explicit synthetic inputs')
 rows=capture({'records':records})['captured']['records']
 fields={'title','url','source','category','summary','score','risk_level','country','credibility','corroboration','published'}
 for r in rows:
  if type(r)is not dict or set(r)-fields or any(type(r.get(k,''))is not str for k in ('title','url','source','category','summary','risk_level','country','credibility','published')):raise PackingRefused('Synthetic record shape')
 for r in rows:
  if 'score'in r and (type(r['score'])not in (int,float) or not math.isfinite(r['score']) or not 0<=r['score']<=100):raise PackingRefused('Bounded numeric score')
  if 'corroboration'in r and (type(r['corroboration'])is not int or not 1<=r['corroboration']<=100):raise PackingRefused('Bounded corroboration')
 definitions,_=_functions();scope={'__builtins__':{'len':len,'enumerate':enumerate},'TELEGRAM_MSG_LIMIT':3500}
 exec(compile(ast.Module(body=definitions,type_ignores=[]),'reviewed-original-formatter','exec'),scope)
 pieces=[];manifest=[]
 for index,row in enumerate(rows):
  text=scope['_format_full_record'](row)
  # Keep each article independent, avoiding shared-batch duplicate attribution.
  # A fixed128 UTF16 reserve covers header incl.index/count<=10000.
  chunks=_split(text,unit_limit-128);required=[]
  for n,chunk in enumerate(chunks,1):
   header='[SYNTHETIC NOT FOR DELIVERY] Article '+str(index+1)+' piece '+str(n)+'/'+str(len(chunks))+'\n'
   wire=header+chunk
   if units(wire)>unit_limit:raise PackingRefused('Packing overflow')
   piece={'article_index':index,'part':n,'total':len(chunks),'text':wire,'payload':chunk,
          'payload_sha256':hashlib.sha256(chunk.encode()).hexdigest(),'utf16_units':units(wire)}
   required.append(len(pieces));pieces.append(piece)
  manifest.append({'article_index':index,'required_piece_indices':required,'record_sha256':hashlib.sha256(text.encode()).hexdigest(),'record_utf16_units':units(text)})
 capture({'pieces':pieces,'manifest':manifest})
 return {'scope':'inactive_synthetic_full_record_packing','pieces':pieces,'manifest':manifest,
         'provider_limit_verified':False,'sent':False,'delivery':False,'production_ready':False}
