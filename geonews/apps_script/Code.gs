/**
 * Geo Intel: combined BRICS + Geo collection and Gmail delivery on free Render.
 * Script Properties: RENDER_BASE_URL, TRIGGER_SECRET, EMAIL_TO.
 * Optional DIGEST_TIMES=10:00,22:00; TIME_ZONE=Asia/Kolkata;
 * KEEPALIVE_MINUTES=10 (0 disables); COLLECT_MINUTES=30.
 * No deployment as a Web App is required. See docs/FREE_RENDER_SETUP.md.
 */
function config_() {
  const p = PropertiesService.getScriptProperties();
  const base = (p.getProperty('RENDER_BASE_URL') || '').trim().replace(/\/+$/, '');
  const secret = (p.getProperty('TRIGGER_SECRET') || '').trim();
  const email = (p.getProperty('EMAIL_TO') || '').trim();
  if (!/^https:\/\/[^/]+$/.test(base) || !secret || !email) {
    throw new Error('Set RENDER_BASE_URL, TRIGGER_SECRET and EMAIL_TO in Script Properties.');
  }
  return {base:base, secret:secret, email:email};
}
function request_(path, method, body) {
  const c = config_();
  const options = {method:method || 'get', muteHttpExceptions:true, followRedirects:false,
                   headers:{'X-Trigger-Key':c.secret}};
  if (body !== undefined) {options.contentType='application/json'; options.payload=JSON.stringify(body);}
  const response = UrlFetchApp.fetch(c.base+path, options);
  const status = response.getResponseCode();
  if (status<200 || status>=300) throw new Error(path+' returned HTTP '+status+'. Check Render logs and the matching secret.');
  return JSON.parse(response.getContentText('UTF-8'));
}
function wakeRender() {
  const c=config_();
  for(let n=0;n<3;n++) {
    try {
      const r=UrlFetchApp.fetch(c.base+'/health',{muteHttpExceptions:true,followRedirects:false});
      if(r.getResponseCode()===200){console.log('Render is awake.');return;}
    } catch(e) {console.log('Wake attempt '+(n+1)+' did not complete.');}
    if(n<2) Utilities.sleep(10000);
  }
  throw new Error('Render did not become ready. Check its service status and logs.');
}
function keepAlive(){wakeRender();}
function runCollect(){wakeRender();const r=request_('/api/trigger/collect','post');console.log('Both feeds: '+r.status);}
function checkCollection(){wakeRender();const r=request_('/api/status');console.log(JSON.stringify({collecting:r.collecting,jobs:r.scheduler.jobs,apps:r.apps}));}
function sendTestEmail(){GmailApp.sendEmail(config_().email,'Geo Intel — email setup test','Success: Apps Script can send your combined news brief.');}
function sendDigest(){
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(1000)){console.log('Another digest is running; skipped.');return;}
  try {
    wakeRender();
    const p=PropertiesService.getScriptProperties();
    // Finish acknowledgement from the old Geo-only script when upgrading.
    const legacy=p.getProperty('PENDING_EMAIL_IDS');
    if(legacy){request_('/geo/mark-emailed','post',{article_ids:JSON.parse(legacy)});p.deleteProperty('PENDING_EMAIL_IDS');}
    const pending=p.getProperty('PENDING_COMBINED_IDS');
    if(pending){request_('/api/intel/mark-emailed','post',{article_ids:JSON.parse(pending)});p.deleteProperty('PENDING_COMBINED_IDS');}
    const data=request_('/api/intel/digest');
    if(typeof data.html!=='string'||!data.article_ids||!Array.isArray(data.article_ids.brics)||!Array.isArray(data.article_ids.geo))throw new Error('Invalid combined digest response.');
    if(!data.count){console.log('No new stories. Source status: '+JSON.stringify(data.errors||{}));return;}
    const stamp=Utilities.formatDate(new Date(),p.getProperty('TIME_ZONE')||'Asia/Kolkata','dd MMM yyyy HH:mm');
    GmailApp.sendEmail(config_().email,'Geo Intel · BRICS + Geo — '+stamp,'View the HTML email for your combined intelligence brief.',{htmlBody:data.html});
    p.setProperty('PENDING_COMBINED_IDS',JSON.stringify(data.article_ids));
    request_('/api/intel/mark-emailed','post',{article_ids:data.article_ids});
    p.deleteProperty('PENDING_COMBINED_IDS');
    console.log('Sent '+data.count+' stories. Source status: '+JSON.stringify(data.errors||{}));
  } finally {lock.releaseLock();}
}
function setupTriggers(){
  config_();
  const p=PropertiesService.getScriptProperties();
  const wake=Number(p.getProperty('KEEPALIVE_MINUTES')||10);
  const collect=Number(p.getProperty('COLLECT_MINUTES')||30);
  const minutes=[1,5,10,15,30];
  if(wake!==0&&!minutes.includes(wake))throw new Error('KEEPALIVE_MINUTES must be 0, 1, 5, 10, 15 or 30.');
  if(!minutes.includes(collect))throw new Error('COLLECT_MINUTES must be 1, 5, 10, 15 or 30.');
  const zone=p.getProperty('TIME_ZONE')||'Asia/Kolkata';
  Utilities.formatDate(new Date(),zone,'yyyy-MM-dd');
  const raw=(p.getProperty('DIGEST_TIMES')||'10:00,22:00').split(',').map(s=>s.trim());
  if(raw.length>8||raw.some(t=>!/^([01]\d|2[0-3]):[0-5]\d$/.test(t)))throw new Error('DIGEST_TIMES needs up to eight HH:MM times, for example 10:00,22:00.');
  // Remove only this app's current/legacy triggers, not unrelated project triggers.
  const owned=['keepAlive','runCollect','sendDigest','checkCritical','sendWeekly','cleanupOld'];
  ScriptApp.getProjectTriggers().forEach(t=>{if(owned.includes(t.getHandlerFunction()))ScriptApp.deleteTrigger(t);});
  if(wake)ScriptApp.newTrigger('keepAlive').timeBased().everyMinutes(wake).create();
  ScriptApp.newTrigger('runCollect').timeBased().everyMinutes(collect).create();
  [...new Set(raw)].forEach(t=>{const parts=t.split(':').map(Number);ScriptApp.newTrigger('sendDigest').timeBased().atHour(parts[0]).nearMinute(parts[1]).everyDays(1).inTimezone(zone).create();});
  console.log('Installed combined collection, wake-up and Gmail schedules. Times are approximate.');
}
