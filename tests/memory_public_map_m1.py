import sys,resource,json,gc,tracemalloc
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(os.environ.get('MAP_BASE_ROOT',ROOT))
if (ROOT/'source').is_dir():sys.path[:0]=[str(ROOT/'source'),str(BASE)]
else:sys.path.insert(0,str(ROOT))
from integration.news_api import create_app
from integration import public_map_prep as m
from pathlib import Path
tracemalloc.start();base=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
raw={'geo':[{'title':'SIMULATED news'+str(i),'country':'India','url':'https://news.example.com/'+str(i),'source':'Local fixture','created_at':'2026-10-12T00:00:00Z'}for i in range(100)]}
a=create_app(authorize=lambda r:True);m.install(a,'http://localhost',m.FakeMap(lambda:raw));c=a.test_client();samples=[]
for i in range(20):
 r=c.get(m.API);assert r.status_code==200;assert len(r.data)<262144;gc.collect();samples.append(tracemalloc.get_traced_memory()[0])
out={'fixture_only':True,'baseline_peakRSS_KiB':base,'final_peakRSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'tracemalloc_current_samples':samples,'not_proof':'No realports/countries, nofullcomposition/cgroup/browsergraphics capacity measured.'};print(json.dumps(out,indent=2))
