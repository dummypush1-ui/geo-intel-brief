"""A1 fake service + served20MBFinder only, NOT full512MiB/cgroup acceptance."""
import sys,resource,json,tracemalloc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration import public_ai_answers as a
from tests.test_public_ai_answers import RAW,V
from tests.test_code_news_coverage_binding_prep import SAMPLE,ORIGIN
from integration.public_preview_builder import build_public_preview
tracemalloc.start();app=build_public_preview(dict(SAMPLE,**{a.FLAG:'true'}))
r=app.test_client().get('/workspace/finder/offline.html',base_url=ORIGIN);shell=r.data
start=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
s=a.Service(lambda:RAW,lambda *a:None,a.FakeTransport(),a.FakeCatalog(),clock=lambda:1000)
for n in range(20):
 s.dispatches.clear();s.submit(V);s.thread.join(1)
current,peak=tracemalloc.get_traced_memory();rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
print("MEASURE",len(shell),start,rss,flush=True)
assert len(shell)>19000000 and rss<384
print(json.dumps({'fixture_only':True,'shell_bytes':len(shell),'maxrss_before_fake_jobs_MiB':start,'maxrss_after_fake_jobs_MiB':rss,'python_tracemalloc_peak_MiB':peak/1048576,'live_child_implemented':False,'container_cgroup_measured':False,'combined_features_capacity_verified':False},indent=2))
s.close()
