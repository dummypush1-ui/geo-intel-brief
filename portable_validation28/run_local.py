"""28a LOCAL sandbox runner only. No existing workflow imports it."""
import pathlib,sys,subprocess,json,resource,hashlib
root=pathlib.Path(sys.argv[1]).resolve();work=pathlib.Path(sys.argv[2]).resolve();art=pathlib.Path(sys.argv[3]).resolve();work.mkdir();(work/'home').mkdir();(work/'tmp').mkdir();logs=[]
def run(args):
 cmd=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--ro-bind',str(root),'/tree','--ro-bind',str(art),'/artifacts','--bind',str(work),'/work','--clearenv','--setenv','PATH','/usr/bin','--setenv','HOME','/work/home','--setenv','TMPDIR','/work/tmp','--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','PIP_NO_INDEX','1','--setenv','PIP_CONFIG_FILE','/dev/null','--setenv','TZ','UTC','--chdir','/work']+args
 def limits():
  resource.setrlimit(resource.RLIMIT_CPU,(90,90));resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120,preexec_fn=limits,env={'PATH':'/usr/bin'});logs.append({'argv':args,'exit_code':r.returncode,'output':r.stdout.decode(errors='replace')});(work/'logs.json').write_text(json.dumps(logs,indent=2)+'\n');assert r.returncode==0,r.stdout.decode();return r.stdout
run(['/usr/bin/python3','-I','/tree/runtime_build/verify27.py','/artifacts','/tree'])
for n in [1,2]:
 py=f'/work/venv{n}/bin/python';run(['/usr/bin/python3','-I','-m','venv',f'/work/venv{n}'])
 for lock in ['bootstrap27.lock','app27.lock']:run([py,'-I','-m','pip','install','--no-index','--no-cache-dir','--only-binary=:all:','--find-links=/artifacts','--require-hashes','-r','/tree/runtime_build/'+lock])
 run([py,'-I','-m','pip','check']);receipt=run([py,'-I','/tree/portable_validation28/harness.py','/tree']);(work/f'receipt{n}.json').write_bytes(receipt)
assert(work/'receipt1.json').read_bytes()==(work/'receipt2.json').read_bytes();r=json.loads(receipt);print(json.dumps({'scope':r['scope'],'totals':r['totals'],'receipt_sha256':hashlib.sha256(receipt).hexdigest(),'two_clean_semantic_receipts_equal':True},indent=2))
