"""local CPython3.10.12 Linuxx86_64 venv build/import proof, offline runner."""
import pathlib,subprocess,sys,json,resource,hashlib
s=pathlib.Path(sys.argv[1]).resolve();reports=[]
provenance=json.loads((s/'tree/runtime_build/interpreter.json').read_text())
assert hashlib.sha256(pathlib.Path('/usr/bin/python3.10').read_bytes()).hexdigest()==provenance['sha256'], 'exact observed interpreter bytes required'
def run(args,cwd='/tree'):
 cmd=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--ro-bind',str(s/'tree'),'/tree','--ro-bind',str(s/'artifacts'),'/artifacts','--bind',str(s),'/work','--clearenv','--setenv','PATH','/usr/bin','--setenv','HOME','/work/home','--setenv','TMPDIR','/work/tmp','--setenv','PIP_CONFIG_FILE','/dev/null','--setenv','PIP_NO_INDEX','1','--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','PYTHONHASHSEED','0','--setenv','TZ','UTC','--chdir',cwd]+args
 def limit():
  resource.setrlimit(resource.RLIMIT_CPU,(120,120));resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,67108864))
 r=subprocess.run(cmd,env={'PATH':'/usr/bin'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,preexec_fn=limit);reports.append({'command':args,'exit_code':r.returncode,'output':r.stdout.decode(errors='replace')});(s/'run-log.json').write_text(json.dumps(reports,indent=2)+'\n');print(r.stdout.decode(errors='replace')[-1800:]);assert r.returncode==0
 return r.stdout.decode()
input_receipts=[]
run(['/usr/bin/python3','/tree/runtime_build/test_verify27.py'])
for i in (1,2):
 input_receipts.append(run(['/usr/bin/python3','-I','/tree/runtime_build/verify27.py','/artifacts','/tree']))
 py=f'/work/venv{i}/bin/python';run(['/usr/bin/python3','-I','-m','venv',f'/work/venv{i}'])
 for lock in ['bootstrap27.lock','app27.lock']:
  run([py,'-I','-m','pip','install','--no-index','--no-cache-dir','--only-binary=:all:','--find-links','/artifacts','--require-hashes','-r','/tree/runtime_build/'+lock])
 run([py,'-I','-m','pip','check']);raw=run([py,'-I','/tree/runtime_build/smoke27.py']);line=next(l for l in raw.splitlines() if l.startswith('RECEIPT='));(s/f'receipt{i}.json').write_text(line[8:]+'\n')
assert input_receipts[0]==input_receipts[1]
(s/'input-receipt.json').write_text(input_receipts[0])
assert (s/'receipt1.json').read_bytes()==(s/'receipt2.json').read_bytes();print('Two clean runs identical deterministic receipt SHA',hashlib.sha256((s/'receipt1.json').read_bytes()).hexdigest())
