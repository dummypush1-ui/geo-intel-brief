import sys,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.news_api import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
app=create_app(authorize=lambda r:True);server=make_server('127.0.0.1',8776,app);threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith('http://127.0.0.1:8776/') else r.abort())
 page.goto('http://127.0.0.1:8776/workspace/finder/index.html#code=0:090121');page.locator('#d-fav').wait_for();assert 'Coffee; roasted, not decaffeinated' in page.inner_text('body');page.locator('#d-fav').click();assert 'Saved' in page.locator('#d-fav').inner_text();page.locator('#d-short').click();page.get_by_text('Your note',exact=True).click();page.locator('#d-note').fill('Local fixture note only');page.locator('#d-note').dispatch_event('change');page.reload();page.locator('#d-fav').wait_for();assert 'Saved' in page.locator('#d-fav').inner_text()
 headings=page.locator('summary').all_text_contents();assert any('Compare everywhere' in h for h in headings);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.locator('#d-back').click();page.locator('#open-sl').click()
 with page.expect_download() as d:page.locator('#sl-csv').click()
 d.value.save_as('/downloads/finder-shortlist-fixture.csv');assert '090121' in Path('/downloads/finder-shortlist-fixture.csv').read_text();assert not errors;print(json.dumps({'core_code_details':True,'favourites_persist':True,'shortlist_csv':True,'section_inventory':headings,'errors':errors,'fixture_only':True}));b.close()
server.shutdown()
