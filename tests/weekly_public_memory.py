"""Offline combined public app stress; process-AS is not container memory."""
import sys,resource,time,json,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
from integration.public_live_builder import build_public_live_preview
from tests.test_code_news_coverage_binding_prep import LIVE,Client,Binding,ORIGIN
from integration import public_weekly_pdf as w
from integration import news_finder_navigation_prep as nav
from unittest.mock import patch
from integration.weekly_report import build_weekly_report
start=time.monotonic();client=Client()
for row in client.store.rows:row.update(title='HS090121;',summary='')
# Actual reviewed live mode limits100geo. Worst valid public row strings before
# report sanitizer further caps to200/400etc; unique URL keeps100 accepted.
raw={'geo':[dict(url='https://example.com/'+str(i),title=('T '*1024)[:2048],summary=('S '*4000)[:8000],source='X'*200,country='Y'*200,category='Z'*200,published='2026-10-02T00:00:00Z',score=i)for i in range(100)]}
env=dict(LIVE,**{w.FLAG:'true',nav.FLAG:'true','PUBLIC_WEATHER_UI_ENABLED':'true'})
barrier=threading.Barrier(3);results=[];errors=[]
def build(*a,**kw):barrier.wait(timeout=10);return build_weekly_report(*a,**kw)
with patch('integration.public_live_builder.ReadOnlyNewsReader',return_value=lambda:raw),patch('integration.weekly_report.build_weekly_report',side_effect=build):
 app=build_public_live_preview(env,client_factory=lambda *a,**k:client,coverage_binding_provider=lambda:Binding(True,True,True,True,'fixture-owner','fixture-deployment'))
 def worker():
  try:results.append(app.test_client().get(w.PATH+'?start=2026-10-01&end=2026-10-05',base_url=ORIGIN))
  except Exception as e:errors.append(str(e))
 threads=[threading.Thread(target=worker)for _ in range(2)]
 for t in threads:t.start()
 barrier.wait(timeout=10)
 # Actual E1 proof manual start hashes~92MB with two real public PDF builds,
 # pinned Finder/index/coverage objects resident. Retain both responses.
 h={'Origin':ORIGIN,'Sec-Fetch-Site':'same-origin','Sec-Fetch-Mode':'cors','Sec-Fetch-Dest':'empty'}
 r=app.test_client().post('/api/code-news-coverage',base_url=ORIGIN,headers=h,json={'system':'HS','edition':'2022','code':'090121'})
 for t in threads:t.join()
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
 report=dict(process_as_limit_MiB=512,peak_RSS_MiB=peak,wall_seconds=time.monotonic()-start,pdf_status=[r.status_code for r in results],retained_pdf_bytes=[len(r.data)for r in results],coverage_status=r.status_code,finder_state=r.json.get('finder_navigation',{}).get('state'),errors=errors,target_MiB=384,whole_container_certified=False,combined_actual_public_app=True,source='injected100geo-worststrings-noDB',reader_calls='public cache returns2copies; underlying1read')
 print(json.dumps(report,indent=2));app.extensions['coverage_close']()
 assert peak<=384 and len(results)==2 and all(r.status_code==200 for r in results)and report['finder_state']=='ready'and not errors
