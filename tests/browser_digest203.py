import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_digest_render203 import row,render
from playwright.sync_api import sync_playwright
x=render([row(title='Tariff review changes the outlook for exporters',summary='A supplied fixture for checking mobile wrapping and section counts. No message has been sent.'),row(title='Unknown category stays visible',category='NEW')]);# Supplied fixture only; no hosted app/network source.
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome-stable',headless=True,args=['--no-sandbox'])
 results=[]
 for width in (390,1280):
  page=b.new_page(viewport={'width':width,'height':900});requests=[];page.on('request',lambda r:requests.append(r.url));page.route('**/*',lambda r:r.abort());page.set_content(x['html']);page.screenshot(path=f'/downloads/digest203-{width}.png',full_page=True)
  assert page.locator('body').evaluate('(e)=>e.scrollWidth')<=width
  assert not requests
  results.append({'width':width,'external_requests':len(requests),'horizontal_overflow':False});page.close()
 b.close();print(json.dumps(results))
