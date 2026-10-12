import os
import sys,resource,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,os.environ.get('M2_BASE',str(r)));import integration;integration.__path__.insert(0,str(r/'integration'))
from integration.news_api import create_app
app=create_app(authorize=lambda _:True)
baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
from integration import public_map_m2 as m
m.install(app,'https://app.example.com',lambda:{'geo':[]})
c=app.test_client()
for _ in range(100):
 for path in ['/workspace/map','/api/map-data','/workspace/map-fixture/countries.json','/workspace/map-fixture/ports.json']:
  res=c.get(path,base_url='https://app.example.com');assert res.status_code==200
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
out={'full_create_app_baseline_rss_highwater_bytes':baseline,'map_plus_100_reference_request_cycles_peak_bytes':peak,'increment_bytes':peak-baseline,'headroom_bytes':512*1024*1024-peak,'fixture_reader_no_db':True,'production_live_store_worker_count_unverified':True};assert out['increment_bytes']<=32*1024*1024 and out['headroom_bytes']>=128*1024*1024
print(json.dumps(out,indent=2))
