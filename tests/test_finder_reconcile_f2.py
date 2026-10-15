import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from integration import finder_reconcile_f2 as m
ENV={m.FLAG:'true',m.build.FLAG:'true'}
class Tests(unittest.TestCase):
 def partner(self,entries=None,year=2025):
  entries=entries or {'020230':{'x':[['A',12]],'m':[]}}
  return '// Synthetic fixture only.\nexport const TRADE_PARTNERS_YEAR = '+str(year)+';\n'+(m.ROOT/'integration/finder_reconcile_f2/partner-declaration.txt').read_text()+''.join("  '"+k+"': "+json.dumps(v)+',\n'for k,v in entries.items())+'};\n'
 def sanc(self,rows=None):return '// Synthetic fixture only.\nexport const SANCTIONS_META = {"checked":"2000-01-01"};\nexport const SANCTIONS: [string, string, string][] = '+json.dumps(rows or [['A','OFAC','SYNTHETIC']])+';\n'
 def snapshot(self,p=None,s=None):
  return {'state':'supplied_public_snapshot_not_official_proof','repository':'push2006/finder-hsn-codee','revision':'a'*40,'source_files':[{'path':n,'content':t,'sha256':m.digest(t.encode())}for n,t in zip(m.FILES,[p or self.partner(),s or self.sanc()])]}
 def run_fixture(self,*,p=None,s=None,oldp=None,olds=None):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'src').mkdir();(root/m.FILES[0]).write_text(oldp or self.partner());(root/m.FILES[1]).write_text(olds or self.sanc())
   def rebuild(env,**kw):
    self.assertEqual(env,ENV);return copy.deepcopy(kw['bundle'])
   with patch.object(m.build,'prepare',side_effect=rebuild):return m.prepare(ENV,snapshot=self.snapshot(p,s),root=root)
 def test_exact_off_before_any_file_or_build(self):
  with patch.object(m,'candidate',side_effect=AssertionError),patch.object(Path,'read_text',side_effect=AssertionError),patch.object(m.build,'prepare',side_effect=AssertionError):
   for env in ({},{m.FLAG:'false'}):self.assertEqual(m.prepare(env)['state'],'disabled')
  for value in ('TRUE','1','yes',''):
   with self.assertRaises(m.Held):m.prepare({m.FLAG:value})
  with self.assertRaises(m.Held):m.prepare({m.FLAG:'true'},snapshot=self.snapshot())
 def test_closed_snapshot_hash_cap_duplicate_and_utf8(self):
  cases=[];s=self.snapshot();s['x']=1;cases.append(s)
  s=self.snapshot();s['revision']='main';cases.append(s)
  s=self.snapshot();s['repository']='other/repo';cases.append(s)
  s=self.snapshot();s['source_files'][0]['sha256']='0'*64;cases.append(s)
  s=self.snapshot();s['source_files'][1]=s['source_files'][0];cases.append(s)
  s=self.snapshot();s['source_files'][0]['path']='../src/tradepartners.ts';cases.append(s)
  s=self.snapshot();s['source_files'][0]['content']='\ud800';cases.append(s)
  for s in cases:
   with self.subTest(s=str(s)[:120]),self.assertRaises(m.Held):m.candidate(s)
  with patch.object(m,'MAX_BYTES',10),self.assertRaises(m.Held):m.candidate(self.snapshot())
 def test_partner_data_parser_no_execution(self):
  for text in ('{x:process.exit(),m:[]}','{x:[],m:[],__proto__:{}}','{x:[],x:[],m:[]}','{x:[],m:[],constructor:[]}','{x:[],m:[],a:1}','{x:`a`,m:[]}','{x:[],m:[]};fetch("x")'):
   with self.assertRaises(m.Held):m.js_object(text)
  good=m.js_object('{x:[["x: true; process.exit()",12]],m:[],xn:[12,false]}');self.assertEqual(good['x'][0][0],'x: true; process.exit()');m.partner_value(good)
 def test_partner_schema(self):
  for row in ({'x':[]},{'x':[],'m':[],'bad':[]},{'x':[['A',True]],'m':[]},{'x':[['A',-1]],'m':[]},{'x':[['A',1e100]],'m':[]},{'x':[['A',1]]*6,'m':[]},{'x':[],'m':[],'xn':[1,'false']},{'x':[],'m':[],'xq':[1,'bad']}):
   with self.assertRaises(m.Held):m.partner_value(row)
 def test_partner_duplicate_year_and_declaration_drift(self):
  text=self.partner()
  for t in (text.replace("  '020230'", "  '020230': {\"x\":[],\"m\":[]},\n  '020230'"),text+'console.log(1)\n',text.replace('number?','number'),text.replace("  '020230'", "  'bad'")):
   with self.assertRaises(m.Held):m.partners(t)
  with self.assertRaises(m.Held):self.run_fixture(p=self.partner(year=2026))
 def test_last_good_retained_additions_only_and_no_cosmetic_noop(self):
  p=self.partner({'020230':{'x':[['CHANGED',99]],'m':[]},'030617':{'x':[],'m':[['B',20]]}})
  out=self.run_fixture(p=p,s=self.sanc([['B','OFAC','SYNTHETIC']]))
  self.assertEqual(out['partners']['added_codes'],['030617']);self.assertEqual(out['partners']['held_changed_codes'],['020230']);self.assertEqual(out['partners']['candidate_count'],2)
  self.assertEqual(out['sanctions']['retained_missing_rows'],1);self.assertEqual(out['sanctions']['removals_applied'],0)
  p,s=[r['content']for r in out['rebuild']['source_files']];self.assertIn('"A",12',p);self.assertNotIn('CHANGED',p);self.assertIn('"A","OFAC"',s);self.assertIn('"B","OFAC"',s);self.assertIn('2000-01-01',s)
  same=self.run_fixture();self.assertEqual(same['rebuild']['source_files'],[])
  missing=self.run_fixture(p=self.partner({'030617':{'x':[],'m':[]}}));self.assertEqual(missing['partners']['retained_missing_codes'],['020230'])
 def test_sanctions_schema_and_no_executable_tail(self):
  for t in (self.sanc()+'fetch("bad")',self.sanc().replace('OFAC','BAD'),self.sanc().replace('["A", "OFAC", "SYNTHETIC"]','[1, "OFAC", "SYNTHETIC"]')):
   with self.assertRaises(m.Held):m.sanctions(t)
 def test_lastgood_symlink_and_malformed_source_hold(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);(root/'src').mkdir();(root/m.FILES[0]).symlink_to(m.ROOT/m.FILES[0])
   with self.assertRaises(m.Held):m.prepare(ENV,root=root,snapshot=self.snapshot())
 def test_real_baseline_no_repo_write(self):
  before={n:m.digest((m.ROOT/n).read_bytes())for n in m.FILES}
  snapshot=self.snapshot(*[(m.ROOT/n).read_text()for n in m.FILES]);out=m.prepare(ENV,snapshot=snapshot)
  self.assertEqual(out['rebuild']['state'],'unchanged_rebuild_not_source_refresh');self.assertFalse(out['writes']);self.assertFalse(out['published']);self.assertFalse(out['sanctions']['legal_screening_ready'])
  self.assertEqual(before,{n:m.digest((m.ROOT/n).read_bytes())for n in m.FILES})
 def test_reserved_keys_and_unknown_token_explicit(self):
  for name in ('__proto__','constructor','prototype'):
   with self.subTest(name=name),self.assertRaisesRegex(m.Held,'reserved'):m.pairs([(name,[])])
   with self.assertRaises(m.Held):m.js_object('{"'+name+'":[]}')
  with self.assertRaisesRegex(m.Held,'unknown data token'):m.js_object('{x:[],m:[],other:[]}')
if __name__=='__main__':unittest.main()
