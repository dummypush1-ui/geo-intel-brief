"""Original-column CSV streaming over an exact injected RawPager fixture seam.

No routes or production adapter. Output differs intentionally on incomplete
exports: a fixed-cell-count final status with a digest of preceding CSV bytes.
Reserved EXPORT_ data-cell prefixes are escaped to distinguish status rows.
"""
import csv,io,math,time,hashlib
from .raw_pager import RawPager,RawPagerError
from .original_contract import original_snapshot,GEO_FIELDS,BRICS_FIELDS
from .export import ExportRequestError

class OriginalStream:
 def __init__(self,pager,project,args=None,*,stamp='20000101_000000',max_bytes=20*1024*1024,max_seconds=120,clock=time.monotonic):
  if type(pager) is not RawPager or pager._project!=project:raise ExportRequestError('exact project pager required')
  if type(max_bytes) is not int or not 1024<=max_bytes<=20*1024*1024:raise ExportRequestError('byte budget')
  if type(max_seconds) not in (int,float) or not math.isfinite(max_seconds) or not 0<max_seconds<=120 or not callable(clock):raise ExportRequestError('time budget')
  # Validate args/stamp and preserve original filename/header using empty snapshot.
  head,headers,_=original_snapshot([],project,args,stamp=stamp)
  self._args=dict(args or {});self._stamp=stamp;self._project=project;self._pager=pager
  self._header=head;self.headers=dict(headers)
  self.headers['X-Export-Trailer']='final EXPORT_COMPLETE/EXPORT_TRUNCATED/EXPORT_INCOMPLETE with SHA256 of preceding bytes'
  self.headers['X-Export-Scope']='injected_original_order_capped_not_live_database'
  self.headers.pop('X-Export-Truncated',None)
  self._cap=1000000
  if project=='brics':
   try:self._cap=min(int(self._args.get('limit','1000')),5000)
   except ValueError:self._cap=1000
  self._hard_cap=(project=='geo')
  if project=='brics':
   try:self._hard_cap=int(self._args.get('limit','1000'))>5000
   except ValueError:self._hard_cap=False
  if getattr(pager,'_stream_claimed',False):raise ExportRequestError('pager already claimed')
  if pager._last is not None or pager._eof or pager._verified or pager._closed:raise ExportRequestError('fresh pager required')
  pager._stream_claimed=True
  self._digest=hashlib.sha256()
  self._max=max_bytes;self._seconds=max_seconds;self._clock=clock
  self._total=0;self._closed=False;self.state={'read':0,'rows':0,'pages':0,'reason':None,'cells_truncated':False}
  self._generator=None
  try:
   self._start=clock()
   self._first=pager.fetch_page(limit=min(pager._size,self._cap))
  except BaseException:
   self.close();raise
 def __enter__(self):return self
 def __exit__(self,*exc):self.close()
 def close(self):
  if self._closed:return
  self._closed=True;RawPager._shutdown(self._pager)
  if self._generator is not None:self._generator.close()
 def __iter__(self):return self
 def __next__(self):
  if self._closed:raise StopIteration
  if self._generator is None:self._generator=self._chunks()
  try:return next(self._generator)
  except BaseException:
   self._closed=True;RawPager._shutdown(self._pager);raise
 def _trailer(self,kind,reason):
  self.state['reason']=reason
  buf=io.StringIO(newline='');n=len(GEO_FIELDS if self._project=='geo' else BRICS_FIELDS)
  csv.writer(buf).writerow([kind,reason,str(self.state['rows']),str(self.state['read']),self._digest.hexdigest(),str(int(self.state['cells_truncated']))]+['']*(n-6))
  return buf.getvalue().encode()
 def _expired(self):return self._clock()-self._start>self._seconds
 def _chunks(self):
  # Reserve 512 bytes for the fixed status trailer within the strict byte budget.
  try:
   self._total=len(self._header);self._digest.update(self._header);yield self._header
   page=self._first;self._first=None
   while True:
    if self._expired():yield self._trailer('EXPORT_TRUNCATED','time budget');return
    self.state['pages']+=1
    if not page:yield self._trailer('EXPORT_COMPLETE','source exhausted');return
    for row in page:
     if self.state['read']>=self._cap:yield self._trailer('EXPORT_TRUNCATED' if self._hard_cap else 'EXPORT_COMPLETE','hard source cap' if self._hard_cap else 'requested source limit');return
     if self._expired():yield self._trailer('EXPORT_TRUNCATED','time budget');return
     self.state['read']+=1
     try:
      data,_,meta=original_snapshot([row],self._project,self._args,stamp=self._stamp)
      part=data[len(self._header):]
      if part:
       values=next(csv.reader(io.StringIO(part.decode('utf-8'))))
       values=["'"+v if v.startswith('EXPORT_') else v for v in values]
       buf=io.StringIO(newline='');csv.writer(buf).writerow(values);part=buf.getvalue().encode('utf-8')
     except Exception:yield self._trailer('EXPORT_INCOMPLETE','invalid source row');return
     if self._total+len(part)>self._max-512:yield self._trailer('EXPORT_TRUNCATED','byte budget');return
     self._total+=len(part);self.state['rows']+=meta['rows'];self.state['cells_truncated']|=meta['cells_truncated']
     if part:self._digest.update(part);yield part
    if self.state['read']>=self._cap:
     # Conservative: no extra source read beyond cap to prove EOF.
     yield self._trailer('EXPORT_TRUNCATED' if self._hard_cap else 'EXPORT_COMPLETE','hard source cap' if self._hard_cap else 'requested source limit');return
    if self._expired():yield self._trailer('EXPORT_TRUNCATED','time budget');return
    try:page=self._pager.fetch_page(limit=min(self._pager._size,self._cap-self.state['read']))
    except Exception:yield self._trailer('EXPORT_INCOMPLETE','source unavailable');return
  finally:
   RawPager._shutdown(self._pager);self._closed=True
