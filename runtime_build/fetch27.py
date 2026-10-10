"""local CPython3.10.12 Linuxx86_64 venv build/import proof, pinned public fetch stage."""
import pathlib,json,sys,hashlib,urllib.request,urllib.parse,datetime
here=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(sys.argv[1]).resolve();out.mkdir();ledger=[]
for row in json.loads((here/'artifacts.json').read_text())['artifacts']:
 if row['profile']=='local-candidate-reviewed-anchor':continue
 url=row['origin_url'];assert urllib.parse.urlparse(url).hostname=='files.pythonhosted.org'
 response=urllib.request.urlopen(url,timeout=30);assert urllib.parse.urlparse(response.url).hostname=='files.pythonhosted.org';raw=response.read();assert hashlib.sha256(raw).hexdigest()==row['sha256']
 (out/row['filename']).write_bytes(raw);ledger.append({'filename':row['filename'],'url':url,'sha256':row['sha256'],'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'scope':'local CPython3.10.12 Linuxx86_64 venv build/import proof','public_fetch_receipt':ledger,'remaining':'supply independently anchored local candidate wheel separately, never historical wheel'},sort_keys=True))
