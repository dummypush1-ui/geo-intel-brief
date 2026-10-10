"""local CPython3.10.12 Linuxx86_64 venv build/import proof, stage exact inputs."""
import pathlib,json,sys,shutil,hashlib
root=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(sys.argv[1]).resolve();repo=pathlib.Path(sys.argv[2]).resolve();artifacts=pathlib.Path(sys.argv[3]).resolve()
sys.path.insert(0,str(root));from verify27 import verify,source
manifest=json.loads((root/'source-allowlist.json').read_text());source(repo,manifest);verify(artifacts,json.loads((root/'artifacts.json').read_text())['artifacts'])
out.mkdir();(out/'tree').mkdir();(out/'home').mkdir();(out/'tmp').mkdir();shutil.copytree(artifacts,out/'artifacts')
for name in manifest['files']:
 target=out/'tree'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,target)
shutil.copytree(root,out/'tree/runtime_build',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
print('local CPython3.10.12 Linuxx86_64 venv build/import proof inputs prepared')
