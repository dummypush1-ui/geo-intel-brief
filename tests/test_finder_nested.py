import unittest,re,hashlib,base64
from pathlib import Path
from integration.finder_nested import shortlist_scroll,shortlist_csv_safe,TABLE,STYLE,REPLACEMENT,CSV_QUOTE,CSV_SAFE
from integration.finder_network import manual_ships_shell
from integration.news_api import create_app
class FinderNestedTests(unittest.TestCase):
 def test_exact_seam_and_first_real_head_only(self):
  s=(Path(__file__).resolve().parents[1]/'index.html').read_text();out=shortlist_scroll(s)
  self.assertNotIn(TABLE,out);self.assertEqual(out.count(STYLE),1);self.assertEqual(out.count('<style id="finder-nested-shortlist">'),1)
  self.assertFalse(any(m.start()<=out.index(STYLE)<m.end() for m in re.finditer(r'<script\b[^>]*>.*?</script>',out,re.S|re.I)))
  self.assertEqual(out.replace(STYLE,'',1).replace(REPLACEMENT,TABLE),s)
  self.assertLess(out.index(STYLE),out.index('</head>'));self.assertEqual(s.count('</head>'),out.count('</head>'))
 def test_seam_changes_fail_closed(self):
  for s in ('<head></head>',TABLE+TABLE+'</head>',TABLE):
   with self.assertRaises(ValueError):shortlist_scroll(s)
 def test_private_served_only_and_csp_hashes(self):
  self.assertEqual(create_app().test_client().get('/workspace/finder/index.html').status_code,403)
  c=create_app(authorize=lambda r:True).test_client();r=c.get('/workspace/finder/index.html');self.assertEqual(r.status_code,200);self.assertIn(STYLE,r.text);self.assertIn('sha256-',r.headers['Content-Security-Policy']);self.assertEqual(r.headers['Cache-Control'],'no-store')

 def test_served_pipeline_seam_and_exact_script_csp(self):
  s=(Path(__file__).resolve().parents[1]/'index.html').read_text();before=manual_ships_shell(s);after=shortlist_csv_safe(shortlist_scroll(before))
  def scripts(text):return [body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',text,flags=re.S|re.I) if body.strip() and not re.search(r'\bsrc\s*=',attrs,re.I)]
  def hashes(text):return {"'sha256-"+base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()+"'" for body in scripts(text)}
  # The seam port only adds markup in the one original UI script, so that
  # script hash necessarily changes; all other original scripts are unchanged.
  self.assertEqual(len(scripts(before)),len(scripts(after)))
  self.assertEqual(len(hashes(before)-hashes(after)),1)
  self.assertEqual(len(hashes(after)-hashes(before)),1)
  r=create_app(authorize=lambda r:True).test_client().get('/workspace/finder/index.html')
  directive=next(x.strip() for x in r.headers['Content-Security-Policy'].split(';') if x.strip().startswith('script-src'))
  self.assertNotIn("'unsafe-inline'",directive)
  self.assertEqual(set(re.findall(r"'sha256-[^']+'",directive)),hashes(r.text))
  self.assertEqual(len(scripts(r.text)),len(scripts(before)))
  with self.assertRaises(ValueError):shortlist_scroll(before.replace(TABLE,'seam changed'))
 def test_fake_head_inside_script_not_selected(self):
  with self.assertRaises(ValueError):shortlist_scroll('<script>"</head><body>"</script>'+TABLE)

 def test_two_real_head_boundaries_refused(self):
  with self.assertRaises(ValueError):shortlist_scroll('</head><body>'+TABLE+'</head><body>')

 def test_csv_seam_reversible_and_node_cells(self):
  import subprocess,json
  source=(Path(__file__).resolve().parents[1]/'index.html').read_text();safe=shortlist_csv_safe(source);self.assertEqual(safe.replace(CSV_SAFE,CSV_QUOTE),source)
  values=['normal','quote " comma,\nline','=1','+1','-3','@foo','\tfoo','\rfoo','\nfoo','  =1','\u200b=1','\ufeff+1','nul\0value','astral 😀','bad\ud800']
  run=CSV_SAFE+"\nconsole.log(JSON.stringify("+json.dumps(values)+".map(q)))"
  p=subprocess.run(['node','-e',run],capture_output=True,text=True,check=True);results=json.loads(p.stdout)
  for i in range(2,12):self.assertTrue(results[i].startswith('"\''),values[i])
  self.assertEqual(results[0],'"normal"');self.assertEqual(results[12],'"nulvalue"');self.assertEqual(results[13],'"astral 😀"');self.assertEqual(results[14],'"bad�"')
  for s in ('none',CSV_QUOTE+CSV_QUOTE):
   with self.assertRaises(ValueError):shortlist_csv_safe(s)

 def test_csv_no_lookbehind_controls_and_all_columns(self):
  import subprocess,json
  self.assertNotIn('(?<',CSV_SAFE)
  controls=['\x01=1','\x1f+1','\x7f-3','\x85@foo','\x9f=1']
  p=subprocess.run(['node','-e',CSV_SAFE+"\nconsole.log(JSON.stringify("+json.dumps(controls)+".map(q)))"],capture_output=True,text=True,check=True)
  for value in json.loads(p.stdout):self.assertTrue(value.startswith('"\''))
  source=(Path(__file__).resolve().parents[1]/'index.html').read_text()
  self.assertIn("['System', 'Code', 'Description', 'Open duty / rate', 'Note', 'Source'].map(q)",source)
  self.assertIn("S.notes[x.k] || '', SYS[e[0]].url].map(q)",source)
