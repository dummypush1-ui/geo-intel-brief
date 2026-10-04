import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
raw={'geo':[dict(url='https://example.com/a',title='Fixture publication',country='India',published='2026-10-01T00:00:00Z')]}
a=create_app(reader=lambda:raw,authorize=lambda r:True);server=make_server('127.0.0.1',8773,a);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8773/') else r.abort());page.goto('http://127.0.0.1:8773/workspace/weekly');page.locator('#weekly-start').fill('2026-09-28');page.locator('#weekly-end').fill('2026-10-05')
 with page.expect_download() as d:page.get_by_role('button',name='Download supplied-news PDF').click()
 d.value.save_as('/downloads/weekly-route-FIXTURE.pdf');page.get_by_text('PDF download prepared. It covers supplied rows only, not complete weekly history.',exact=True).wait_for();page.screenshot(path='/downloads/weekly-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors
 page.route('**/api/weekly-report.pdf?*',lambda r:r.fulfill(status=503,json={'error':'Unavailable'}));page.get_by_role('button',name='Download supplied-news PDF').click();page.get_by_text('PDF unavailable. Check the date period or try a manual download later. No report saved or sent.',exact=True).wait_for();assert not errors;print(json.dumps(dict(download=True,errors=errors,mobile_no_overflow=True,failure_visible=True)));b.close()
server.shutdown()
