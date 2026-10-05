"""Fixed exec child with bounded output/time. No shell, URI argv or env dump."""
import json,os,selectors,subprocess,sys,time
from pathlib import Path
from integration.geo_sample_probe import _result,LABEL,FIELDS
ROOT=Path(__file__).resolve().parents[1]
REASONS={'query_timeout','io_timeout','connection_unavailable','source_unavailable','cleanup_unavailable',None}
def validate_result(result):
 expected=set(_result('unavailable'))
 if type(result) is not dict or set(result)!=expected:raise ValueError()
 if result['mapping']!=['geo_intel','articles'] or result['credential_scope']!=LABEL:raise ValueError()
 for key,value in [('sample_cap',20),('sample_only',True),('no_full_history_proof',True),('probe_issues_no_writes',True),('read_only_privileges_verified',False)]:
  if type(result[key]) is not type(value) or result[key]!=value:raise ValueError()
 state=result['state'];count=result['sampled_rows'];counts=result['compatibility'];reason=result['unavailable_reason']
 if reason is not None and type(reason) is not str:raise ValueError()
 if type(state) is not str or state not in ('sample','empty','unavailable') or type(count) is not int or not 0<=count<=20 or type(counts) is not dict or reason not in REASONS:raise ValueError()
 if state=='unavailable':
  if count!=0 or counts!={}:raise ValueError()
 else:
  if reason is not None or set(counts)!=set(FIELDS) or (state=='empty')!=(count==0):raise ValueError()
  for row in counts.values():
   if type(row) is not dict or set(row)!={'compatible','incompatible','missing'} or any(type(v) is not int or not 0<=v<=20 for v in row.values()) or sum(row.values())!=count:raise ValueError()
 return result

def execute_probe(uri):
 """10s sampled child deadline, 4096 byte stdout, kill+wait on every path.

Not a finite whole HTTP/ingress deadline. Child process env necessarily carries
URI; no privilege isolation from authorized OS/process inspection.
 """
 process=None;selector=None;result=_result('unavailable',reason='source_unavailable')
 try:
  if type(uri) is not str or not uri or len(uri)>8192:raise ValueError()
  process=subprocess.Popen([sys.executable,'-m','integration.geo_sample_probe_child'],cwd=ROOT,env={'GEO_MONGODB_URI':uri,'LANG':'C.UTF-8'},stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
  selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
  started=time.monotonic();data=bytearray()
  while True:
   remaining=10-(time.monotonic()-started)
   if remaining<=0:raise TimeoutError()
   events=selector.select(remaining)
   if not events:raise TimeoutError()
   chunk=os.read(process.stdout.fileno(),4097-len(data))
   if not chunk:break
   data.extend(chunk)
   if len(data)>4096:raise ValueError()
  remaining=10-(time.monotonic()-started)
  if remaining<=0:raise TimeoutError()
  if process.wait(timeout=remaining)!=0:raise ValueError()
  result=validate_result(json.loads(data.decode('utf-8')))
 except (TimeoutError,subprocess.TimeoutExpired):result=_result('unavailable',reason='io_timeout')
 except Exception:result=_result('unavailable',reason='source_unavailable')
 finally:
  if selector is not None:
   try:selector.close()
   except Exception:result=_result('unavailable',reason='cleanup_unavailable')
  if process is not None:
   try:
    if process.poll() is None:process.kill()
    process.wait()
   except Exception:result=_result('unavailable',reason='cleanup_unavailable')
   finally:
    if process.stdout is not None:
     try:process.stdout.close()
     except Exception:result=_result('unavailable',reason='cleanup_unavailable')
 return result
