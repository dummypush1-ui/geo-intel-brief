import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from integration.report_adapters import geo_report_builder
from integration.html_safety import sanitize_html
from playwright.sync_api import sync_playwright
row={'_id':'fixture','title':'Trade update','url':'https://example.com/story','summary':'Supplied design preview. No mail sent.','score':80,'category':'TRADE','risk_level':'HIGH','source':'Source','country':'India'}
html=geo_report_builder(lambda:[row],lambda days:[])()['html']
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1000,'height':900});requests=[];page.on('request',lambda r:requests.append(r.url));page.route('**/*',lambda r:r.abort());page.set_content(html)
 td=page.locator('td[style*="linear-gradient"]').first
 assert 'linear-gradient' in td.evaluate('(e)=>getComputedStyle(e).backgroundImage');assert td.evaluate('(e)=>getComputedStyle(e).color')=='rgb(255, 255, 255)'
 page.screenshot(path='/downloads/mail-design-colors-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/downloads/mail-design-colors-mobile.png',full_page=True)
 hostile=sanitize_html('<div style="background:url(https://evil.invalid/track);color:red;position:fixed">Unsafe CSS withheld</div>');page.set_content(hostile);assert not requests;assert page.locator('div').evaluate('(e)=>getComputedStyle(e).backgroundImage')=='none'
 print(json.dumps({'gradient_and_white_text':True,'hostile_no_resource_load':True,'mail_sent':False,'email_client_render_unverified':True}));b.close()
