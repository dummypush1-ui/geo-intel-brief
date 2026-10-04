"""Loopback HTTPS browser using fixture credentials only; no outbound traffic."""
import sys,threading,json,tempfile,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from integration.accounts import AccountService,MemoryStore,Hasher
from integration.accounts.http_fixture import create_fixture_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
O='https://localhost:8781';svc=AccountService(MemoryStore(),b'f'*48,lambda:1800000000,hasher=Hasher(n=1024),signup_mode='open',allowed_origins=[O]);p=svc.issue_preauth();svc.signup('fixture-user','correct horse battery','',p['csrf'],p['nonce'],'seed',O)
svc.mode='closed';app=create_fixture_app(svc,O,lambda r:'browser-fixture');tmp=Path(tempfile.mkdtemp());cert=tmp/'cert.pem';key=tmp/'key.pem';subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
server=make_server('127.0.0.1',8781,app,ssl_context=(str(cert),str(key)));threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},ignore_https_errors=True,accept_downloads=True);errors=[];outside=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(O+'/') else (outside.append(r.request.url),r.abort()))
 page.goto(O+'/account/preview');page.locator('#status').filter(has_text='Ready for a test account').wait_for();page.fill('#username','fixture-user');page.fill('#password','correct horse battery');page.locator('#sign-in').click();page.locator('#settings').wait_for(state='visible');page.fill('#channels','Fixture news | abcdefghijk');page.fill('#watchlist','India');page.locator('#save').click();page.locator('#status').filter(has_text='Saved to the memory-only fixture').wait_for();assert 'Republic' not in page.input_value('#channels');page.screenshot(path='/downloads/account-settings-fixture-mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 with page.expect_download() as d:page.locator('#export').click()
 d.value.save_as('/downloads/fixture-account.json');export=json.loads(Path('/downloads/fixture-account.json').read_text());assert export['username']=='fixture-user';assert 'password' not in export;page.locator('#logout').click();page.locator('#status').filter(has_text='Signed out').wait_for();page.screenshot(path='/downloads/account-signin-fixture-mobile.png',full_page=True);assert not errors and not outside;print(json.dumps({'fixture_login_save_export_logout':True,'mobile_no_overflow':True,'external_requests':outside,'errors':errors}));b.close()
server.shutdown()
