from pathlib import Path
import subprocess,json,sys,os
root=Path(__file__).resolve().parents[1];src=root/'source'if(root/'source').is_dir()else root;p=src/'integration/public_map_prep/__init__.py';original=p.read_text();out=[]
mutants=[('payloadcap','if len(raw)>262144:','if False:','test_payload_cap_direct'),('duplicate','if key in seen:','if False:','test_duplicate_and_project'),('project',"r.get('project')!='geo'","False",'test_duplicate_and_project'),('https',"p.scheme!='https'","False",'test_https_only'),('allowlist','if name not in ASSETS:','if False:','test_asset_allowlist_and_method'),('loopback',"p.hostname not in ('127.0.0.1','localhost')","False",'test_loopback_same_scheme_wrong_host'),('assetpins',"if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:","if False:",'test_startup_pins_and_dependency'),('basepin',"if hashlib.sha256(Path(source).read_bytes()).hexdigest()!=BASE_PIN:","if False:",'test_startup_pins_and_dependency'),('publicdependency',"if env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':","if False:",'test_startup_pins_and_dependency'),('ruleshape','len(rules)!=1','False','test_route_rule_shape'),('method',"request.method not in ('GET','HEAD')","False",'test_asset_allowlist_and_method')]
try:
 for name,old,new,test in mutants:
  assert old in original;p.write_text(original.replace(old,new,1));r=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('test_map_m1.py')),'Tests.'+test],capture_output=True);out.append({'mutant':name,'killed':r.returncode!=0})
finally:p.write_text(original)
print(json.dumps(out,indent=2));assert all(x['killed']for x in out)
