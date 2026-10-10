from scripts.doc_lookup import source_bytes, source_text
"""27c executor-discovery preparation; Docker/CP312 NOT RUN; 27/28/29 OPEN"""
import pathlib,json,hashlib,sys,argparse,subprocess
SCOPE='27c executor-discovery preparation; Docker/CP312 NOT RUN; 27/28/29 OPEN'
HERE=pathlib.Path(__file__).resolve().parent
class Refused(ValueError):pass
def report(state,reason,**extra):return {'scope':SCOPE,'state':state,'reason':reason,'unimplemented':['execution','failure capture','Stage B'],'future_adapter':'requires separate contract and review',**extra}
def sha(p):return hashlib.sha256(source_bytes(p)).hexdigest()
def pairs(rows):
 out={}
 for r in rows:
  n=r['package'];v=r['version']
  if type(n)is not str or type(v)is not str or n in out:raise Refused('pair shape/duplicate')
  out[n]=v
 return out
def compare(expected,actual):
 # Fixture or future-plan pair identity; no claim of target apt execution.
 a=pairs(expected);b=pairs(actual);added=sorted(set(b)-set(a));removed=sorted(set(a)-set(b));changed=sorted(n for n in set(a)&set(b)if a[n]!=b[n])
 return {'outcome':'MATCH'if not(added or removed or changed)else'STOP','added':added,'removed':removed,'changed':changed,'install_permitted':False}
def preflight(root):
 root=pathlib.Path(root);m=json.loads((HERE/'source-allowlist.json').read_text())
 for n,h in m['files'].items():
  p=root/n
  if p.is_symlink()or sha(p)!=h:raise Refused('source drift:'+n)
 anchor=json.loads((root/'runtime_build/inputs/post-install-anchor.json').read_text());expected=anchor['post_install']
 return report('NOT RUN','discovery not executed; base image anchor records apt 2.8.3; target executor behaviour and CP312 execution unobserved; local apt 2.4.14 not reused',expected_pairs=len(expected),source_sha256=m['files'],open_dependencies=['no app source copied','no209helper/goldens','Gunicorn22vs23','bcrypt5','extras','nativeprivateinternals','historicalwheel','ownCP312sgmloutputanchor','realapt/Dockerdiscovery','29bworkflowfailureevidencewrapper','executionadapter','failurecapture','StageBimplementation'])
def execute_reviewed(command,output_dir):
 # ONLY subprocess entry. This package NEVER invokes it: executable discovery adapter
 # is deliberately withheld until a separate executor-specific contract/permission.
 # Keeping bounded-capture specification as data avoids pretending a local opt-in
 # is authorization or a capable executor. Any accidental call fails BEFORE subprocess.
 raise Refused('executor adapter absent; discovery not executed; no subprocess allowed')
def dispatch(argv):
 # No args/default returns without even reading pins, writing files or subprocess.
 if not argv:return report('NOT RUN','default gate OFF; discovery not executed; zero side effects')
 allowed={'--stage','--gate','--source','--stage-a-anchor'};values={};i=0
 while i<len(argv):
  k=argv[i]
  if k not in allowed or k in values or i+1>=len(argv):return report('REFUSED','unknown/duplicate/missing argument; discovery not executed')
  values[k]=argv[i+1];i+=2
 if values.get('--stage')not in('A','B'):return report('REFUSED','wrong stage; discovery not executed')
 if values.get('--gate','off')!='on':return report('NOT RUN','technical gate OFF; discovery not executed; zero side effects')
 if values['--stage']=='B':
  anchor=values.get('--stage-a-anchor')
  if not anchor:return report('REFUSED','stageB needs separately accepted stageAanchor; discovery not executed')
  # A supplied file is not approval. No source can authenticate its own authority.
  return report('REFUSED','stageB execution adapter and separately reviewed anchor binding absent; discovery not executed')
 if '--source'not in values:return report('REFUSED','source required; discovery not executed')
 try:r=preflight(values['--source'])
 except(OSError,ValueError,KeyError)as e:return report('REFUSED',str(e)+'; discovery not executed')
 r['reason']='source pins inspected only; StageA plan-only adapter intentionally absent; separate executor handoff required; discovery not executed'
 return r
def main():print(json.dumps(dispatch(sys.argv[1:]),sort_keys=True,separators=(',',':')))
if __name__=='__main__':main()
