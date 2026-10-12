import subprocess,json,tempfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];s=(root/'integration/public_map_m2/map.js').read_text();mutants=[('quiet','this.quietUntil=this.clock()+QUIET','this.quietUntil=this.clock()'),('batch','now<this.lastBatch+BATCH','false'),('slots','this.active===4','this.active===40'),('cancel','this.jobs.delete(item.key);',''),('poly','r.length>1024','r.length>10240'),('ids','ids.has(f.id)','false')];out=[]
for name,a,b in mutants:
 with tempfile.TemporaryDirectory(prefix='m2-mut-')as tmp:
  d=Path(tmp);(d/'integration/public_map_m2').mkdir(parents=True);(d/'tests').mkdir();(d/'integration/public_map_m2/map.js').write_text(s.replace(a,b));shutil.copy(root/'integration/public_map_m2/countries.json',d/'integration/public_map_m2/countries.json');shutil.copy(root/'tests/public_map_m2_gate.cjs',d/'tests/public_map_m2_gate.cjs');r=subprocess.run(['node',str(d/'tests/public_map_m2_gate.cjs')],capture_output=True,text=True);out.append({'mutant':name,'killed':r.returncode!=0})
print(json.dumps(out,indent=2));assert all(x['killed']for x in out)
