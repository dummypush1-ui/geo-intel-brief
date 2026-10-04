import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime,timezone
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
row={'url':'https://example.com/a','title':'FIXTURE preview only - no message sent','summary':'Original report renderer over a simulated public sample.','source':'Fixture','country':'India','risk_level':'CRITICAL','score':50,'category':'TRADE','created_at':datetime.now(timezone.utc).isoformat()}
app=create_app(reader=lambda:{'geo':[row]},authorize=lambda r:True);server=make_server('127.0.0.1',8777,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});requests=[];page.on('request',lambda r:requests.append(r.url));page.route('**/*',lambda r:r.abort())
 for endpoint,name in [('/digest-data','digest'),('/critical','critical'),('/weekly','weekly')]:
  d=app.test_client().get(endpoint).json;assert not d['delivery'] and not d['writes'];page.set_content(d['html']);page.screenshot(path='/downloads/'+name+'-original-preview-mobile.png',full_page=True);assert 'FIXTURE preview only' in page.inner_text('body')
 assert not requests;print(json.dumps({'three_original_renderers':True,'no_external_resource_requests':True,'delivery':False,'mobile_layout_inspection_required':True}));b.close()
server.shutdown()
