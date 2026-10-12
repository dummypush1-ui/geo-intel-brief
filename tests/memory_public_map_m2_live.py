import os,sys,resource,json
from pathlib import Path
from unittest.mock import patch
r=Path(__file__).resolve().parents[1];sys.path.insert(0,os.environ.get('M2_BASE',str(r)));import integration;integration.__path__.insert(0,str(r/'integration'))
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import LIVE,ORIGIN,Client
raw={'geo':[{'title':'Fixture article '+str(i)+' '+('x'*1900),'summary':'x'*7900,'country':'India','source':'Fixture','url':'https://news.example.com/'+str(i)}for i in range(100)]}
env=dict(LIVE,PUBLIC_MAP_ENABLED='true',PUBLIC_CODE_NEWS_COVERAGE_API_ENABLED='false',PUBLIC_CODE_NEWS_COVERAGE_UI_ENABLED='false',PUBLIC_NEWS_FULL_PAGES_ENABLED='false')
with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:raw):
 baseline_app=build_public_live_preview(env,client_factory=lambda *a,**k:Client());c=baseline_app.test_client();assert c.get('/api/news',base_url=ORIGIN).status_code==200
 baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
 app=build_public_live_preview(dict(env,PUBLIC_MAP_M2_ENABLED='true'),client_factory=lambda *a,**k:Client());c=app.test_client()
 for _ in range(100):
  for path in ['/workspace/map','/api/map-data','/workspace/map-fixture/countries.json','/workspace/map-fixture/ports.json','/api/news']:
   res=c.get(path,base_url=ORIGIN);assert res.status_code==200,(path,res.status_code)
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
out={'baseline_live_M1_latest100_highwater_bytes':baseline,'M2_live_builder_100cycles_peak_bytes':peak,'increment_bytes':peak-baseline,'headroom_bytes':512*1024*1024-peak,'fixture_100_large_rows_no_db':True,'two_apps_retained_conservative_local_only':True,'production_live_store_worker_count_unverified':True};assert out['increment_bytes']<=32*1024*1024 and out['headroom_bytes']>=128*1024*1024;print(json.dumps(out,indent=2))
