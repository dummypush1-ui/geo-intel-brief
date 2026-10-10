from scripts.doc_lookup import source_bytes, source_text
"""28a spec + LOCAL CPython3.10.12 Linuxx86_64 harness only; item28 OPEN."""
import pathlib,sys,json,hashlib,io,os,socket,subprocess,signal,time,ctypes,importlib.metadata as md,resource
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from packaging.markers import Marker
HERE=pathlib.Path(__file__).resolve().parent
FIXTURE_DEPTH_PROBE=64  # TEST ONLY; existing production MAX_DEPTH=8 unchanged.
STATUSES={'PASS','FAIL','SKIP','BLOCKED','NOT RUN'}
def totals(rows):
 return {s:sum(r['status']==s for r in rows)for s in sorted(STATUSES)}
def declared(version):
 return {'implementation_name':'cpython','implementation_version':version+'.0','os_name':'posix','platform_machine':'x86_64','platform_release':'declared-fixture','platform_system':'Linux','platform_version':'declared-fixture','python_full_version':version+'.0','platform_python_implementation':'CPython','python_version':version,'sys_platform':'linux','extra':''}
MARKERS=[('python_version < "3.12"',True,False),('python_version >= "3.12"',False,True),('sys_platform == "linux" and platform_machine == "x86_64"',True,True),('extra == "test"',False,False)]
def markers(version):return [Marker(text).evaluate(declared(version))for text,_,_ in MARKERS]
def depth(text):
 # Only syntactically generated nested-array fixture language, NOT a general JSON validator.
 n=0;maxdepth=0
 for ch in text:
  if ch=='[':n+=1;maxdepth=max(maxdepth,n)
  elif ch==']':n-=1
  elif ch!='0':return {'outcome':'refused','error':'fixture_syntax'}
  if n<0:return {'outcome':'refused','error':'fixture_syntax'}
 if n:return {'outcome':'refused','error':'fixture_syntax'}
 if maxdepth>FIXTURE_DEPTH_PROBE:return {'outcome':'refused','error':'fixture_depth_probe'}
 json.loads(text)
 return {'outcome':'accepted','error':None}
def tz_rows(resolver=ZoneInfo):
 instants=['2026-01-01T00:00:00+00:00','2026-01-01T18:29:59+00:00','2026-01-01T18:30:00+00:00','2026-06-30T18:30:00+00:00']
 try:a=resolver('Asia/Kolkata');b=resolver('Asia/Calcutta')
 except ZoneInfoNotFoundError:return {'status':'BLOCKED','reason':'one or both required zone names unavailable; no alias/UTC fallback'}
 for t in instants:
  d=datetime.fromisoformat(t);x=d.astimezone(a);y=d.astimezone(b)
  assert x.utcoffset()==y.utcoffset()==timedelta(hours=5,minutes=30)and x.date()==y.date()
 assert datetime.fromisoformat(instants[1]).astimezone(a).date().isoformat()=='2026-01-01'
 assert datetime.fromisoformat(instants[2]).astimezone(a).date().isoformat()=='2026-01-02'
 return {'status':'PASS','reason':'both zone names same +05:30/local dates for4fixedinstants including18:30UTCboundary','resolved_keys':[a.key,b.key]}
def sources(root):
 manifest=json.loads((HERE/'source-allowlist.json').read_text())
 for n,h in manifest['files'].items():
  p=pathlib.Path(root)/n
  if p.is_symlink()or hashlib.sha256(source_bytes(p)).hexdigest()!=h:raise ValueError('source_drift:'+n)
 return manifest['files']
def group_reap():
 # Harmless descendant-only test, no host processes targeted. Subreaper applies to this harness.
 libc=ctypes.CDLL(None,use_errno=True)
 if libc.prctl(36,1,0,0,0)!=0:raise RuntimeError('subreaper unavailable')
 code='import subprocess,time,os; p=subprocess.Popen(["/usr/bin/sleep","30"]);print(p.pid,flush=True);time.sleep(30)'
 child=None
 p=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,text=True,start_new_session=True)
 try:
  import selectors
  sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
  if not sel.select(2):raise RuntimeError('child PID timeout')
  child=int(p.stdout.readline().strip());sel.close()
  assert p.poll()is None
  os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
  end=time.monotonic()+2;reaped=False
  while time.monotonic()<end:
   n,status=os.waitpid(child,os.WNOHANG)
   if n==child:reaped=True;break
   time.sleep(.01)
  assert reaped,'descendant not reaped'
  for pid in [p.pid,child]:
   try:os.kill(pid,0)
   except ProcessLookupError:continue
   raise AssertionError('created process remains')
 finally:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  p.wait(timeout=2);p.stdout.close()
  if child is not None:
   try:os.waitpid(child,0)
   except ChildProcessError:pass
 return 'harmlesssleepgroup killed; leader and descendantwaited/reaped; no created PID remains'
def main(root):
 assert sys.version_info[:3]==(3,10,12)
 ident={'version':sys.version.split()[0],'implementation':sys.implementation.name,'machine':'x86_64','binary_sha256':hashlib.sha256(source_bytes(pathlib.Path('/usr/bin/python3.10'))).hexdigest()}
 rows=[]
 def row(name,status,reason,**extra):
  assert status in STATUSES;rows.append({'case':name,'status':status,'reason':reason,'interpreter':ident,**extra})
 src=sources(root);row('source_allowlist','PASS','exact immutable read-source hashes match')
 for v,idx in [('3.10',1),('3.12',2)]:
  actual=markers(v);expected=[t[idx]for t in MARKERS];assert actual==expected
  row('declared_marker_env_'+v,'PASS','fixture evaluated against all12declaredkeys, independentliteralexpectedtable; NOT interpreterexecutionofdeclaredversion',outcomes=actual)
 assert sys.version_info[:2]==(3,10)and markers('3.12')[0]is False
 row('declared_env_switch','PASS','actualpython3.10 differsfromdeclared3.12, result followsdeclaredenv')
 for n in [FIXTURE_DEPTH_PROBE-1,FIXTURE_DEPTH_PROBE,FIXTURE_DEPTH_PROBE+1]:
  text='['*n+'0'+']'*n;out=depth(text);expected={'outcome':'accepted','error':None}if n<=FIXTURE_DEPTH_PROBE else{'outcome':'refused','error':'fixture_depth_probe'};assert out==expected
  row('fixture_depth_'+str(n),'PASS','syntacticiterativefixtureonly, NOTproductionlimit; namedstructuredoutcome',outcome=out)
 tz=tz_rows();row('tz_alias_semantics',tz.pop('status'),tz.pop('reason'),**tz)
 def absent(key):raise ZoneInfoNotFoundError(key)
 assert tz_rows(absent)['status']=='BLOCKED';row('tz_absent_negative','PASS','injectedzone-unavailablebranch returnsBLOCKED, noUTCfallback')
 import pypdf
 assert md.version('pypdf')=='6.19.0'
 writer=pypdf.PdfWriter();writer.add_blank_page(width=72,height=72);writer.add_metadata({'/Title':'28a harmless fixture'});b=io.BytesIO();writer.write(b)
 reader=pypdf.PdfReader(io.BytesIO(b.getvalue()),strict=True);assert len(reader.pages)==1and reader.metadata.title=='28a harmless fixture'
 row('pypdf_structural_fixture','PASS','strictreaderopens,1page,metadata; NOTequivalenttopikepdf.pdf.check()',version=md.version('pypdf'))
 try:pikever=md.version('pikepdf')
 except md.PackageNotFoundError:pikever=None
 row('pikepdf_pdf_check','BLOCKED'if pikever is None else'NOT RUN','optionalvalidatornotinstalled; no dependencyadded'if pikever is None else'notselectedprofile,no validatorrun',version=pikever)
 assert not pathlib.Path('/home/sandbox').exists()and not pathlib.Path('/downloads').exists()
 s=socket.socket();assert s.connect_ex(('1.1.1.1',443))!=0;s.close()
 row('bwrap_namespace_probe','PASS','existing unshare-all pattern; hosthome/downloadsabsent, externalconnectrefused; no userdata')
 row('process_group_reap','PASS',group_reap())
 row('combined512MB_acceptance','NOT RUN','RLIMITceilingperprocess1GiB, NOT512MBcombinedtarget; noOOMstress')
 row('CP312_execution_matrix','NOT RUN','noCP312executor; declaredmarkertable isfixtureonly;27bsgmlCP312anchoropen')
 # Actual observed JSON interpreter fact, informational SKIP not semanticpass.
 text='['*2000+'0'+']'*2000
 try:json.loads(text);observation='local json.loads accepted depth2000'
 except RecursionError:observation='local json.loads raises RecursionError at depth2000; historicaltestdependsambientthreshold'
 row('historical_deep_json_observation','SKIP','nooriginaltestfix/productionlimitclaim; '+observation,recursion_limit_metadata=sys.getrecursionlimit())
 accounting=[{'status':'PASS'},{'status':'SKIP'},{'status':'BLOCKED'},{'status':'NOT RUN'}];assert totals(accounting)['PASS']==1and totals(accounting)['SKIP']==1
 row('skip_not_pass_accounting','PASS','literal4-rownegativeaccounting case countsonepass only')
 package_probe=subprocess.run(['dpkg-query','-W','-f=${Version}','tzdata'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 tzmeta={'system_tzdata_header':pathlib.Path('/usr/share/zoneinfo/tzdata.zi').read_text().splitlines()[0],'zone_hashes':{k:hashlib.sha256(source_bytes(pathlib.Path('/usr/share/zoneinfo')/k)).hexdigest()if (pathlib.Path('/usr/share/zoneinfo')/k).is_file()else 'BLOCKED:zonefileabsent'for k in ['Asia/Kolkata','Asia/Calcutta']},'tzdata_package_version':package_probe.stdout.strip()if package_probe.returncode==0 else 'BLOCKED:dpkgpackageDBnotmounted; systemtzdataheader/hashavailable'}
 print(json.dumps({'scope':'28a SPEC+LOCALCPython3.10.12Linuxx86_64harness;28OPEN,no targetvalidationclaim','rows':rows,'totals':totals(rows),'source_sha256':src,'tzdata':tzmeta,'no_full_environment_reproducibility_claim':True},sort_keys=True,separators=(',',':')))
if __name__=='__main__':main(sys.argv[1])
