import unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class WatchUpdateTests(unittest.TestCase):
 def check(self,body):
  r=subprocess.run(['node','--input-type=module','-e',(ROOT/'integration/ui/watch_updates.js').read_text()+'\n'+body],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_first_load_not_alert(self):self.check("const d=compareUpdate([],baselineKey('India',''),[{article_key:'a'.repeat(64)}]);if(d.state!=='baseline'||d.items.length)throw Error('first alert')")
 def test_new_deduped_old_not_repeated(self):self.check("const k=baselineKey('India',''),a={article_key:'a'.repeat(64)},b={article_key:'b'.repeat(64)};const x=compareUpdate([],k,[a]);const y=compareUpdate(x.next,k,[a,b,b]);if(y.items.length!==1)throw Error('dedupe');if(compareUpdate(y.next,k,[a,b]).items.length)throw Error('repeat')")
 def test_project_scope_separate(self):self.check("const x=compareUpdate([],baselineKey('India','geo'),[{article_key:'a'.repeat(64)}]);if(compareUpdate(x.next,baselineKey('India','brics'),[{article_key:'b'.repeat(64)}]).state!=='baseline')throw Error('scope')")
 def test_bounded_history(self):self.check("let s=[],k=baselineKey('India','');for(let j=0;j<6;j++){const rows=Array.from({length:100},(_,i)=>({article_key:(j*100+i).toString(16).padStart(64,'0')}));const d=compareUpdate(s,k,rows);s=d.next;if(j===5&&!d.memory_trimmed)throw Error('eviction invisible')}if(s[0].seen.length!==500)throw Error('unbounded')")
 def test_tampered_history(self):self.check("for(const v of [{},[{key:'{}',seen:[]}],[{key:baselineKey('India',''),seen:['wrong']}],Array(61).fill({key:baselineKey('India',''),seen:[]})]){let bad=false;try{validateBaselines(v)}catch{bad=true}if(!bad)throw Error('invalid accepted')}")
 def test_no_mutation_and_no_timer(self):
  self.check("const k=baselineKey('India',''),saved=[{key:k,seen:['a'.repeat(64)]}];compareUpdate(saved,k,[{article_key:'b'.repeat(64)}]);if(saved[0].seen.length!==1)throw Error('mutated')")
  s=(ROOT/'integration/ui/watch_updates.js').read_text();self.assertNotIn('setInterval(',s);self.assertNotIn('setTimeout(',s);self.assertNotIn('fetch(',s)
