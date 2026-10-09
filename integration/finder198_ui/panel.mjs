import {createBrokerClient} from './client.mjs';
import {addPortOptions226,renderShips226} from './ships226.mjs';
export function mountBrokerPanel(root,{enabled=false,fetcher,nonceFactory}={}) {
 if(!(root instanceof Element))throw Error('Explicit panel root required');
 // Fixed authored markup only. Server/user strings use textContent exclusively.
 root.innerHTML=`<section class="broker-panel" aria-labelledby="broker-title"><p class="eyebrow">Finder account</p><h2 id="broker-title">Built-in AI and ships</h2><p class="broker-note">Owner-provisioned accounts only. No signup or password reset. Own-provider keys are unchanged.</p><form data-login><label>Username<input data-username name="username" autocomplete="username" maxlength="32" required></label><label>Password<input data-password name="password" type="password" autocomplete="current-password" maxlength="128" required></label><button type="submit" data-signin>Sign in</button></form><div class="broker-actions"><button type="button" data-check>Check session</button><button type="button" data-logout>Sign out</button></div><p data-identity></p><p data-status role="status" aria-live="polite"></p><div class="broker-controls"><label>Ship port<select data-port><option value="ALL">All supported ports</option><option value="INNSA">Nhava Sheva (JNPT)</option><option value="INMAA">Chennai</option></select></label><button type="button" data-ships>Read ships once</button><button type="button" data-ai disabled>Built-in AI is off</button></div><div data-ship-view hidden></div><pre data-answer hidden aria-label="Ship response"></pre><p class="broker-note">An unknown or held request needs an owner check. Signing in or reloading does not reconcile it. Never resubmit it automatically.</p></section>`;
 const q=s=>root.querySelector(s);
 addPortOptions226(q('[data-port]'));
 const client=createBrokerClient({enabled,fetcher,nonceFactory,onChange:render});
 function render(s){
  q('[data-status]').textContent=s.message;q('[data-status]').dataset.state=s.request;q('[data-answer]').textContent=s.answer;q('[data-answer]').hidden=!s.answer;renderShips226(q('[data-ship-view]'),s.answer,{complete:s.request==='complete'});
  q('[data-identity]').textContent=s.username?'Signed in as '+s.username:'';
  q('[data-password]').disabled=!enabled||s.busy;q('[data-username]').disabled=!enabled||s.busy;
  q('[data-signin]').disabled=!enabled||s.busy;q('[data-check]').disabled=!enabled||s.busy;
  q('[data-logout]').disabled=!enabled||s.busy||s.session!=='signed_in';
  q('[data-ships]').disabled=!enabled||s.busy||s.blocked||s.session!=='signed_in';
  q('[data-port]').disabled=!enabled||s.busy||s.blocked||s.session!=='signed_in';
 }
 q('[data-login]').addEventListener('submit',e=>{e.preventDefault();const password=q('[data-password]').value;q('[data-password]').value='';client.login(q('[data-username]').value,password);});
 q('[data-check]').addEventListener('click',()=>client.checkSession());q('[data-logout]').addEventListener('click',()=>client.logout());
 q('[data-ships]').addEventListener('click',()=>client.request('ships',{port:q('[data-port]').value}));
 render(client.view());return client;
}
