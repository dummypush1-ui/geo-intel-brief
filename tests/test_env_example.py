import unittest,re,ast,subprocess,tempfile
from pathlib import Path
from integration.storage_settings import StorageSettings
ROOT=Path(__file__).resolve().parents[1]
class EnvExampleTests(unittest.TestCase):
 def test_settings_valid(self):
  values=dict(line.split('=',1) for line in (ROOT/'.env.example').read_text().splitlines() if line and not line.startswith('#'))
  s=StorageSettings.from_env(values);self.assertEqual(s.geo_database,'geo_intel');self.assertFalse(s.read_enabled);self.assertEqual(s.brics_backend,'mongodb')
 def test_credential_values_blank(self):
  for line in (ROOT/'.env.example').read_text().splitlines():
   if not line or line.startswith('#'):continue
   name,value=line.split('=',1)
   if re.search(r'URI|PASSWORD|SECRET|KEYS?$|TOKEN',name) and name!='CRITICAL_KEYWORDS':self.assertEqual(value,'',name)
 def test_ignore_real_env_allow_example(self):
  with tempfile.TemporaryDirectory() as d:
   subprocess.run(['git','init','-q',d],check=True);Path(d,'.gitignore').write_text((ROOT/'.gitignore').read_text())
   for path in ['.env','.env.production']:
    self.assertEqual(subprocess.run(['git','-C',d,'check-ignore',path],capture_output=True).returncode,0)
   self.assertEqual(subprocess.run(['git','-C',d,'check-ignore','.env.example'],capture_output=True).returncode,1)
 def test_documented_python_variables(self):
  text=(ROOT/'.env.example').read_text()
  for p in [ROOT/'intelligence/geo/config.py',ROOT/'intelligence/brics/config.py',ROOT/'integration/storage_settings.py']:
   for n in ast.walk(ast.parse(p.read_text())):
    if not isinstance(n,ast.Call) or not n.args or not isinstance(n.args[0],ast.Constant) or not isinstance(n.args[0].value,str):continue
    name=n.args[0].value
    if not re.fullmatch('[A-Z][A-Z0-9_]*',name):continue
    recognized=isinstance(n.func,ast.Attribute) and n.func.attr in ('get','getenv') or isinstance(n.func,ast.Name) and n.func.id in ('_bool','_list')
    if recognized:self.assertRegex(text,r'(?m)^'+name+r'=')
