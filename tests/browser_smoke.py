"""Browser integration smoke test using local seeded data and mocked AI; no notifications.
Run: pip install playwright; python tests/browser_smoke.py
Requires Chromium at CHROMIUM_PATH (default /usr/bin/chromium).
"""
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(DATA_DIR=tempfile.mkdtemp(prefix='geo-browser-'), RUN_SCHEDULER='false',
                  STORAGE_BACKEND='sqlite', DEPLOY_MODE='local', MONGODB_URI='',
                  GEO_ENABLE_TELEGRAM_BACKUP='false', TRIGGER_SECRET='browser-test-secret-12345')
import mongomock
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from app import app
from core import intelligence, scheduler
from brics import database as B
from geonews import database as G, web as W
from hsn import routes

mongo=mongomock.MongoClient().geo
G.connect=lambda:mongo
W._db_ready=True
app.config['MODULES']['geo']['ok']=True
store=B.get_store()
store.insert(dict(title='BRICS semiconductor trade agreement',url='https://example.test/brics',source='Test Wire',
                  country='India',category='TRADE',summary='Semiconductors and supply chains',published='2026-11-02T10:00:00Z'))
G.save_article(dict(title='Semiconductor export restrictions',url='https://example.test/geo',source='Test Bulletin',
                    country='China',category='SANCTIONS',risk_level='HIGH',score=70,credibility='HIGH',
                    summary='Reported semiconductor trade restrictions',published='2026-11-02T09:00:00Z'))
routes.POOLS={'groq':['fake-test-key']}
response=Mock();response.json.return_value={'choices':[{'message':{'content':'Reported facts\nTrade talks were reported [1].\nPossible impacts\nSupply chains may change; verify details.'}}]}
intelligence.requests.post=Mock(return_value=response)
scheduler.collect_all_async=lambda **kwargs:True
server=make_server('127.0.0.1',0,app,threaded=True)
threading.Thread(target=server.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(server.server_port)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1000})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
  page.goto(base);page.locator('#secret').fill(os.environ['TRIGGER_SECRET']);page.locator('#login-form button').click()
  page.locator('.story').first.wait_for();assert page.locator('.story').count()==2
  page.locator('#country').select_option('India');assert page.locator('.story').count()==1
  page.locator('#save-watch').click();assert page.locator('[data-watch]').count()==1
  page.locator('#country').select_option('');page.locator('[data-select]').first.check()
  page.locator('#analyze').click();page.locator('#analysis-result').wait_for();assert '[1]' in page.locator('#analysis-text').inner_text()
  with page.expect_download() as download:page.locator('#download-brief').click()
  assert download.value.suggested_filename=='geo-intel-brief.txt'
  # The same cookie opens protected Geo and stream controls without a secret URL.
  page.goto(base+'/geo/');assert 'Recent Articles' in page.content();assert os.environ['TRIGGER_SECRET'] not in page.content()
  page.goto(base+'/brics/');assert page.locator('#dashboardKey').count()==1
  result=page.evaluate("""async () => {const r=await fetch('/brics/api/streams',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Browser test',country:'India',link:'https://youtu.be/abcdefghijk'})});return r.status;}""")
  assert result==200
  page.goto(base+'/hsn/#code=0:8542');page.wait_for_function("document.body.innerText.includes('8542') && !document.body.innerText.includes('Loading trade codes...')",timeout=30000)
  assert not page.locator('#jserr-bar').count()
  page.goto(base);page.locator('.story').first.wait_for()
  page.screenshot(path='/workspace/work/unified-desktop.png',full_page=True)
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/workspace/work/unified-mobile.png',full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
  page.locator('#logout').click();page.locator('#login-panel').wait_for()
  assert not errors, errors
  browser.close()
 print('Browser passed: login, feed/filter, saved view, AI brief/download, shared Geo session, stream write, HSN deep link, mobile layout, logout.')
finally:server.shutdown()
