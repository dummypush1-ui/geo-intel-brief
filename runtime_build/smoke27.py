"""local CPython3.10.12 Linuxx86_64 venv build/import proof, no client creation."""
import importlib,importlib.metadata as md,json,pathlib,sys,unittest,hashlib,socket
sys.path.insert(0,'/tree')
# No socket client/server allowed even within the network namespace.
def denied(*args,**kwargs):raise RuntimeError('27a no network/client/server')
socket.socket.connect=denied;socket.socket.connect_ex=denied;socket.socket.bind=denied;socket.socket.listen=denied
assert sys.version_info[:3]==(3,10,12)
assert sys.prefix!=sys.base_prefix and not any('dist-packages'in p for p in sys.path)
expected=json.loads(pathlib.Path('/tree/runtime_build/packages.json').read_text())
canon=lambda n:n.lower().replace('_','-').replace('.','-')
found={canon(d.metadata['Name']):d.version for d in md.distributions()}
assert found==expected,(found,expected)
# Explicit import allowlist. Never import app/server/collectors/providers with live effects.
for name in ['flask','gunicorn','yaml','dotenv','requests','feedparser','sgmllib','pymongo','integration.html_text209','intelligence.geo.processing.classifier','integration.supplied_feed_fixture','collector129_prep.supplied_feed']:
 importlib.import_module(name)
# Constructor refusal catches accidental DB/client creation by source under test.
import pymongo
pymongo.MongoClient.__init__=denied
from integration.native200_transactions import verify_native_pins
assert verify_native_pins()=='4.18.2'
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_html209');result=unittest.TextTestRunner(verbosity=2).run(suite)
assert result.wasSuccessful()
# Exact installed Python/native bytes, no pyc/absolute paths included in stable receipt.
files={}
for d in md.distributions():
 for f in d.files or []:
  if str(f).endswith(('.py','.so','METADATA','WHEEL')):
   p=d.locate_file(f)
   assert p.is_file()
   files[canon(d.metadata['Name'])+'/'+str(f)]=hashlib.sha256(p.read_bytes()).hexdigest()
print('RECEIPT='+json.dumps({'scope':'local CPython3.10.12 Linuxx86_64 venv build/import proof','packages':found,'selected_imports':'bounded explicit allowlist','native_source_pin_count':11,'html209_tests_run':result.testsRun,'installed_selected_file_sha256':dict(sorted(files.items())),'no_target_claim':True},sort_keys=True,separators=(',',':')))
