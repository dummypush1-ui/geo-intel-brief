"""Pinned immutable flat-file lookup, no DB/network/gzip runtime catalogue.
Format v1: index records are >12sQI (24 bytes): padded ASCII code, offset,length.
Only the small offset index is mapped; one bounded JSON row group read per lookup.
"""
import mmap,json,struct,hashlib,re
from pathlib import Path
from integration.code_news_links import Links,Refused
RECORD=struct.Struct('>12sQI');MAX_GROUP=65536
class DiskLinks(Links):
 def __init__(self,folder):
  self.folder=Path(folder);meta=json.loads((self.folder/'manifest.json').read_text())
  if meta.get('format')!='code_news_flat_v1':raise Refused('Unsupported index format')
  # Complete verification once, streaming bounded chunks. No file payload retained.
  for name in ('codes.idx','rows.jsonl'):
   p=self.folder/name
   if p.stat().st_size!=meta['files'][name]['bytes']:raise Refused('Index length mismatch')
   h=hashlib.sha256()
   with p.open('rb')as f:
    while chunk:=f.read(65536):h.update(chunk)
   if h.hexdigest()!=meta['files'][name]['sha256']:raise Refused('Pinned index mismatch')
  self.index_file=(self.folder/'codes.idx').open('rb');self.index=mmap.mmap(self.index_file.fileno(),0,access=mmap.ACCESS_READ)
  self.rows_file=(self.folder/'rows.jsonl').open('rb');self.count=len(self.index)//RECORD.size
  if len(self.index)%RECORD.size or self.count!=meta['code_count']:self.close();raise Refused('Malformed index')
  previous=b'';end=0
  for i in range(self.count):
   code,offset,length=RECORD.unpack_from(self.index,i*RECORD.size)
   key=code.rstrip(b' ')
   if not re.fullmatch(rb'[0-9]{2,12}',key)or code!=key.ljust(12,b' ')or code<=previous or offset!=end or not 1<=length<=MAX_GROUP:self.close();raise Refused('Invalid offset record')
   previous=code;end=offset+length
  if end!=meta['files']['rows.jsonl']['bytes']:self.close();raise Refused('Offset bounds')
  self.rules=[];self.catalogue={};self.omissions={};self.by_code={}
 def close(self):
  for name in ('index','index_file','rows_file'):
   item=getattr(self,name,None)
   if item:item.close()
 def resolve(self,code,system=None,edition=None):
  if type(code)is not str or not re.fullmatch('[0-9]{2,12}',code):return {'state':'invalid_code','items':[]}
  needle=code.encode().ljust(12,b' ');lo=0;hi=self.count
  while lo<hi:
   mid=(lo+hi)//2;key,offset,length=RECORD.unpack_from(self.index,mid*RECORD.size)
   if key<needle:lo=mid+1
   else:hi=mid
  if lo>=self.count:return {'state':'not_in_link_model'if len(code)in (2,7,9,11)else'unknown_code','items':[]}
  key,offset,length=RECORD.unpack_from(self.index,lo*RECORD.size)
  if key!=needle:return {'state':'not_in_link_model'if len(code)in (2,7,9,11)else'unknown_code','items':[]}
  self.rows_file.seek(offset);raw=self.rows_file.read(length)
  if len(raw)!=length:raise Refused('Short rowgroup')
  rows=json.loads(raw)
  if type(rows)is not list or len(rows)>100:raise Refused('Bounded rowgroup')
  candidates=[]
  for row in rows:
   if type(row)is not dict or row.get('code')!=code or row.get('state')not in ('resolved','conflicting_source_rows','not_in_link_model','unusable_description'):raise Refused('Bad rowgroup')
   if(system is None or row['system']==system)and(edition is None or row['edition']==edition):candidates.append(row)
  if len(candidates)>1:return {'state':'ambiguous','items':candidates}
  if candidates:return {'state':candidates[0]['state'],'items':candidates}
  return {'state':'unknown_code','items':[]}
