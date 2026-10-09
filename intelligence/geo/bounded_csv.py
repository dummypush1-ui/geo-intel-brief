"""Bounded legacy CSV chunks. Failure marker means export is incomplete."""
import csv,io,time
from intelligence.geo.bounded_reads import EXPORT_FIELDS,MAX_BYTES,MAX_SECONDS
from integration.news_export.export import csv_cell

def csv_chunks(pages,clock=time.monotonic):
 start=clock();size=0
 def encode(values):
  buf=io.StringIO();csv.writer(buf,lineterminator='\r\n').writerow(values);return buf.getvalue()
 header=encode(EXPORT_FIELDS);size+=len(header.encode());yield header
 try:
  for page in pages:
   for row in page:
    if clock()-start>MAX_SECONDS:raise TimeoutError()
    line=encode([csv_cell(row.get(k)) for k in EXPORT_FIELDS]);size+=len(line.encode('utf-8'))
    if size>MAX_BYTES:raise ValueError()
    yield line
 except Exception:
  yield encode(['EXPORT_INCOMPLETE: source failure or reviewed limit reached; not a recovery backup']+['']*(len(EXPORT_FIELDS)-1))
 finally:
  close=getattr(pages,'close',None)
  if close:close()
