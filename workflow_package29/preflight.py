from scripts.doc_lookup import source_bytes, source_text
"""local workflow preflight/package inventory; Docker NOT RUN; item 29 OPEN"""
import pathlib,hashlib,json,re,sys
SCOPE='local workflow preflight/package inventory; Docker NOT RUN; item 29 OPEN'
HERE=pathlib.Path(__file__).resolve().parent
class Refused(ValueError):pass
def check(condition,reason):
 if not condition:raise Refused(reason)
def sha(p):return hashlib.sha256(source_bytes(p)).hexdigest()
def json_read(p):
 def unique(pairs):
  out={}
  for k,v in pairs:
   check(k not in out,'duplicate JSON key');out[k]=v
  return out
 return json.loads(source_bytes(p),object_pairs_hook=unique)
def source_check(root):
 m=json_read(HERE/'source-allowlist.json')
 for name,h in m['files'].items():
  p=root/name;check(not p.is_symlink()and sha(p)==h,'source drift:'+name)
 return m

def inspect(root):
 root=pathlib.Path(root);r=root/'runtime_build';wf=root/'.github/workflows/runtime-build-review.yml';text=wf.read_text();anchors=json_read(HERE/'workflow-anchors.json')
 # Exact reviewed workflow bytes enforce trigger/steps/order/permissions/concurrency shape.
 check(sha(wf)==anchors['workflow_sha256'],'workflow shape/check drift')
 check(text.count("python3 - <<'PY'")==2,'heredoc shape')
 block=text.split("python3 - <<'PY'",1)[1].split('\n          PY',1)[0]
 check(hashlib.sha256(block.encode()).hexdigest()==anchors['input_check_block_sha256'],'embedded input check drift')
 raw=source_bytes(r/'inputs-manifest.json');anchor=(r/'inputs.sha256').read_text().strip()
 check(re.fullmatch('[0-9a-f]{64}',anchor)is not None and sha(r/'inputs-manifest.json')==anchor,'input manifest anchor mismatch')
 check(len(raw)<=1048576,'manifest bound');m=json_read(r/'inputs-manifest.json');check(type(m)is dict and set(m)=={'scope','files'}and m['scope']=='reviewed_build_inputs','manifest shape/scope');f=m['files'];check(type(f)is dict and 1<=len(f)<=10000,'file count bound');actual=set();total=0
 for p in r.rglob('*'):
  check(not p.is_symlink(),'input symlink')
  if p.is_file()and p.relative_to(r).as_posix()not in('inputs.sha256','inputs-manifest.json'):actual.add(p.relative_to(r).as_posix())
 check(actual==set(f),'exact input file set mismatch')
 for name,h in f.items():
  check(type(name)is str and not name.startswith('/')and '\\'not in name and all(x not in('','.','..')for x in name.split('/')),'input path shape')
  check(type(h)is str and re.fullmatch('[0-9a-f]{64}',h)is not None,'hash shape')
  p=r/name;size=p.stat().st_size;total+=size;check(size<=67108864and total<=268435456,'input size bound');check(sha(p)==h,'input bytes changed:'+name)
 # Source provenance is checked in addition to generic manifest integrity.
 sources=source_check(root)
 check('inputs/application.lock'not in f and not(r/'inputs/application.lock').exists(),'unreviewed application.lock refused; oldhash/placeholder never permitted')
 pending=(r/'inputs/application.pending.lock').read_text();check('PENDING'in pending and 'sgmllib3k==1.0.0'in pending,'pending lock marker changed')
 docker=(r/'Dockerfile.candidate').read_text();check('RUN test -f /reviewed-inputs/application.lock'in docker,'Dockerfile missing refusal gate')
 required=['Dockerfile.candidate','network-launcher.c','build-args.json','inputs/apt.sources','inputs/application.lock'];missing=[n for n in required if n not in actual];check(missing==['inputs/application.lock'],'unexpected required-file set')
 args=json_read(r/'build-args.json');keys={'REVIEWED_APT_SOURCES_SHA256','GCC_VERSION','LIBC6_DEV_VERSION','BWRAP_VERSION'};check(set(args)==keys,'build args key set');check(set(re.findall(r'^ARG (\w+)$',docker,re.M))==keys,'Dockerfile ARG set');check(all(type(v)is str and re.fullmatch('[A-Za-z0-9.+:~_-]{1,128}',v)for v in args.values()),'args value shape');check(args['REVIEWED_APT_SOURCES_SHA256']==sha(r/'inputs/apt.sources'),'apt.sources pin mismatch')
 for key in ['GCC_VERSION','LIBC6_DEV_VERSION','BWRAP_VERSION']:
  matches=re.findall(r'\$'+key+r'" = \'([^\']+)\'',docker);check(matches==[args[key]],'Dockerfile expected arg drift:'+key)
 # Build-context observations extracted, never execute commands/heredocs.
 copies=re.findall(r'^COPY (\S+) (\S+)$',docker,re.M);check(copies==[('inputs','/reviewed-inputs'),('network-launcher.c','/reviewed/network-launcher.c')],'COPY shape')
 refs=set(re.findall(r'/reviewed-inputs/([A-Za-z0-9_.-]+)',docker))
 supplied={p.name for p in(r/'inputs').iterdir()if p.is_file()};generated={'bootstrap-ca.pem'}
 missingrefs=sorted(refs-supplied-generated)
 check(missingrefs==['application.lock'],'unresolved build-context file reference')
 script=(r/'inputs/apt_verify.sh').read_text();fetch=(r/'inputs/fetch_verify.py').read_text()
 script_files=set(re.findall(r'\b([A-Za-z0-9_.-]+\.(?:tsv|json|txt))\b',script))
 fetch_files=set(re.findall(r"root/'([^']+)'",fetch))
 generated_script={'before-dpkg.tsv','installed-dpkg.tsv','apt-plan.txt','changes.tsv'}
 check(not(script_files-supplied-generated_script),'unresolved shell inputreference')
 check(fetch_files<=supplied,'unresolved fetch inputreference')
 shell_commands=sorted(set(re.findall(r'^(?:  )?([a-z][a-z0-9_-]+)(?: |$)',script,re.M)))
 ledger=json_read(r/'inputs/deb-ledger.json');post=json_read(r/'inputs/post-install-anchor.json');check(len(ledger['packages'])==119 and len(post['post_install'])==146,'ledger count drift')
 binaries=[{'path':'inputs/ubuntu-archive-keyring.gpg','bytes':(r/'inputs/ubuntu-archive-keyring.gpg').stat().st_size,'sha256':sha(r/'inputs/ubuntu-archive-keyring.gpg')},{'path':'inputs/ca-certificates-bootstrap.deb','bytes':(r/'inputs/ca-certificates-bootstrap.deb').stat().st_size,'sha256':sha(r/'inputs/ca-certificates-bootstrap.deb')}];check([b['bytes']for b in binaries]==[7399,139430],'binary identity')
 # Each row has explicit local scope; blocked/NOT RUN never build readiness PASS.
 def row(name,status,reason):return {'scope':SCOPE,'case':name,'status':status,'reason':reason}
 rows=[row('manifest_integrity','PASS','exact52file set/hash/limits+anchoredworkflow/sourcebytes match'),row('required_input_closure','BLOCKED','inputs/application.lock absent'),row('target_application_artifact_closure','BLOCKED','ownCP312sgmllibwheelanchor+appsourcepackage absent'),row('Docker_capability','NOT RUN','harness no executor/network/subprocess; no capability probe'),row('target_build_import','NOT RUN','noDocker/CP312build/importexecuted'),row('dispatch_permission','BLOCKED','HELD: separate ownerper-taskdispatchpermission+capableexecutorhandoff required')]
 facts=anchors['observed_facts'];gaps=[{'scope':SCOPE,'gap':'application source not copied','evidence':copies},{'scope':SCOPE,'gap':'integration/html_text209.py and tests/test_html209.py not in image','evidence':'COPY only inputs and network-launcher.c, noappsource COPY'},{'scope':SCOPE,'gap':'build NOT offline','evidence':'workflow --network default; fetch_verify usesfiles.pythonhosted.org; apt usessnapshot.ubuntu.com'},{'scope':SCOPE,'gap':'failed build evidence upload normally skipped','evidence':facts['upload_failure_finding']},{'scope':SCOPE,'gap':'CP312sgmlbuildanchor missing','evidence':'application.pending.lock notpromoted; application.lock absent'}]
 return {'scope':SCOPE,'summary':'preflight: 1 blocked input, build not attempted','rows':rows,'totals':{s:sum(x['status']==s for x in rows)for s in ['PASS','FAIL','SKIP','BLOCKED','NOT RUN']},'input_count':len(f),'input_total_bytes':total,'input_max_file_bytes':max((r/n).stat().st_size for n in f),'size_limits':{'per_file':67108864,'total':268435456},'binaries':binaries,'ledger_counts':{'download_debs':119,'post_install_pairs':146},'build_context_inventory':{'copy_paths':copies,'reviewed_input_references':sorted(refs),'generated_files':sorted(generated),'missing_references':missingrefs,'shell_commands_observed':shell_commands,'shell_file_references':sorted(script_files),'shell_generated_evidence':sorted(generated_script),'fetch_python_reads':sorted(fetch_files),'network_hosts_observed':['snapshot.ubuntu.com','files.pythonhosted.org']},'workflow_facts':facts,'gap_list':gaps,'source_sha256':sources['files'],'remaining':['27bCP312sgmlanchor externalexecutor','28bactualtestfixes separatecontract/pinreview','29breadyapplicationlock/appsource/workflowfailure-evidence separatecontract'],'no_build_readiness_claim':True}
def main(root):
 try:result=inspect(pathlib.Path(root))
 except(Exception)as e:
  print(json.dumps({'scope':SCOPE,'status':'FAIL','reason':str(e)},sort_keys=True));raise SystemExit(1)
 print(json.dumps(result,sort_keys=True,separators=(',',':')))
if __name__=='__main__':main(sys.argv[1])
