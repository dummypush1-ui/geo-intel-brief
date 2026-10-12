from pathlib import Path
import subprocess,json
root=Path(__file__).resolve().parents[1];p=(root/'source'if(root/'source').is_dir()else root)/'integration/public_map_prep/map.js';s=p.read_text();out=[]
try:
 for name,old,new in [('3-error-pause','this.errors>=3','this.errors>=4'),('60s-resume','<60000','<59999'),('4-active','this.active<4','this.active<5'),('failed-no-retry','||this.failed.has(key)',''),('release-cancel-slot','if(active)this.active--;if(item.abort)','if(false)this.active--;if(item.abort)'),('cancel-key-release','this.jobs.delete(item.key);this.queue=this.queue.filter','this.queue=this.queue.filter'),('hidden-cancel','if(!v)this.cancelAll();','if(!v)this.queue=[];'),('single-completion',"if(item.state==='ended')return;const active=item.state==='active';item.state='ended';this.jobs.delete(item.key);if(active)this.active--;", "const active=item.state==='active';item.state='ended';this.jobs.delete(item.key);if(active)this.active--;" )]:
  assert old in s,(name,old);p.write_text(s.replace(old,new,1));r=subprocess.run(['node',str(Path(__file__).with_name('tile_gate.cjs'))],capture_output=True);out.append({'mutant':name,'killed':r.returncode!=0})
finally:p.write_text(s)
print(json.dumps(out,indent=2));assert all(x['killed']for x in out)
