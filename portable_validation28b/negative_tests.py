import pathlib,subprocess,json,shutil,hashlib,os
r=pathlib.Path(__file__).resolve().parents[1];out=r/'portable_validation28b';py=__import__('sys').executable;p=r/'integration/geospatial/response.py';base=p.read_bytes();dep=r/'tests/test_dependency_audit.py';d=dep.read_bytes();cases=[]
def run(name,mods,test):
 try:
  for f,t in mods:f.write_text(t)
  q=subprocess.run([py,'-m','unittest',test],cwd=r,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
  (out/(name+'.txt')).write_text(q.stdout+q.stderr);cases.append({'name':name,'exit_code':q.returncode,'test':test,'expected_failure_observed':q.returncode!=0})
  assert q.returncode!=0,name
 finally:p.write_bytes(base);dep.write_bytes(d)
run('negative-escaped-recursion',[(p,base.decode().replace('except (OSError, ValueError, RecursionError):','except (OSError, ValueError):'))],'tests.geospatial.test_map_route.MapLoaderBounds.test_decoder_recursion_refused')
run('negative-unsafe-shape',[(p,base.decode().replace('return [], {"ok": False, "reason": "bad_shape"}','return [], {"ok": True, "reason": "bad_shape"}'))],'tests.geospatial.test_map_route.MapLoaderBounds.test_decoder_nested_array_bad_shape_refused')
run('negative-ambient-marker',[(dep,d.decode().replace('q.marker.evaluate(historical_marker_environment(self.a))',"q.marker.evaluate({'extra':''})"))],'tests.test_dependency_audit.Tests.test_marker_declared_receipt_not_ambient')
(out/'negative-results.json').write_text(json.dumps(cases,indent=2)+'\n');print(json.dumps(cases,indent=2))
assert p.read_bytes()==base and dep.read_bytes()==d
