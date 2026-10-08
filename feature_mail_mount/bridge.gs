// Copyright (c) 2026 Push. All rights reserved.
// New manual entry point only. No triggers, deployment or legacy edits.
// OFF unless MAIL_V1_ENABLED is exactly true. Recipient/sender scope must be
// reviewed outside this code; channel is a fingerprint, not authentication.
// Gmail return is acceptance only, not independently verified delivery.
function runMailV1(kind) {
  if (!['digest', 'critical', 'weekly'].includes(kind)) throw Error('Invalid kind');
  const props = PropertiesService.getScriptProperties();
  if (props.getProperty('MAIL_V1_ENABLED') !== 'true') return {state:'off'};
  const base = props.getProperty('MAIL_V1_BASE');
  const secret = props.getProperty('MAIL_V1_HEADER_SECRET');
  const to = props.getProperty('MAIL_V1_EMAIL_TO');
  const channel = props.getProperty('MAIL_V1_CHANNEL');
  if (!/^https:\/\/[a-z0-9]+(?:[.-][a-z0-9]+)*$/.test(base || '') || !/^[\x21-\x7e]{48,256}$/.test(secret || '') || !/^[0-9a-f]{64}$/.test(channel || '')) throw Error('Reviewed configuration required');
  const recipients = (to || '').split(',').map(x=>x.trim());
  if (!recipients.length || recipients.length > 20 || recipients.some(x=>! /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(x))) throw Error('Reviewed recipients required');
  const sender = Session.getEffectiveUser().getEmail().trim().toLowerCase();
  if (!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(sender)) throw Error('Effective sender required');
  const normalized = recipients.map(x=>x.toLowerCase()).sort();
  if (new Set(normalized).size !== normalized.length) throw Error('Duplicate recipients');
  const scope = JSON.stringify({sender:sender,recipients:normalized});
  const actualChannel = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,scope,Utilities.Charset.UTF_8).map(b=>('0'+((b+256)%256).toString(16)).slice(-2)).join('');
  if (actualChannel !== channel) throw Error('Sender/recipient scope changed');
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw Error('Mail busy');
  const name = 'MAIL_V1_PENDING_' + kind.toUpperCase();
  function post(action, body) {
    const r = UrlFetchApp.fetch(base + '/internal/mail/v1/' + action, {method:'post', contentType:'application/json', headers:{Authorization:'Bearer ' + secret}, payload:JSON.stringify(body), muteHttpExceptions:true, followRedirects:false});
    if (r.getResponseCode() !== 200) throw Error('Mail operation uncertain; no resend');
    const raw = r.getContentText('UTF-8');
    if (raw.length > 1100000) throw Error('Response cap');
    return JSON.parse(raw);
  }
  function write(s) { props.setProperty(name, JSON.stringify(s)); }
  function binding(r,s) {return r && r.receipt===s.receipt && /^[0-9a-f]{64}$/.test(r.receipt) && r.hash===s.hash;}
  try {
    let raw = props.getProperty(name), s;
    if (raw) {
      if (raw.length > 2048) throw Error('Pending record cap');
      s = JSON.parse(raw);
      if (!s || s.channel!==channel || s.kind!==kind || !['pending','bound','claiming','sending','send_returned'].includes(s.phase) || !/^[A-Za-z0-9_-]{20,80}$/.test(s.nonce) || !/^[A-Za-z0-9_-]{20,80}$/.test(s.attempt)) throw Error('Pending record invalid');
    } else {
      s={kind,channel,nonce:Utilities.getUuid(),attempt:Utilities.getUuid(),phase:'pending'};
      write(s); // Persist nonce before first request. Never generate another on uncertain outcome.
    }
    if (s.phase==='send_returned') {
      const r=post('ack',{receipt:s.receipt,hash:s.hash,attempt:s.attempt});
      if (!r || r.receipt!==s.receipt || r.state!=='acknowledged' || r.scope!=='bridge_send_returned_not_delivery') throw Error('Ack refused');
      props.deleteProperty(name);return {state:'acknowledged'};
    }
    if (s.phase==='claiming' || s.phase==='sending') throw Error('Send outcome held for manual reconciliation; no resend');
    const r=post('prepare',{kind,nonce:s.nonce});
    if (!r || !/^[0-9a-f]{64}$/.test(r.receipt) || !/^[0-9a-f]{64}$/.test(r.hash) || r.channel_id!==channel || !r.payload || r.payload.kind!==kind) throw Error('Prepare binding refused');
    if (s.phase==='bound' && !binding(r,s)) throw Error('Changed receipt');
    if (r.state==='skipped' && r.payload.skip===true) {props.deleteProperty(name);return {state:'skipped'};}
    if (r.state!=='prepared' || r.payload.skip!==false || typeof r.payload.subject!=='string' || /[\r\n]/.test(r.payload.subject) || r.payload.subject.length>200 || typeof r.payload.html!=='string' || r.payload.html.length>1048576) throw Error('Prepared content refused');
    s.receipt=r.receipt;s.hash=r.hash;s.phase='claiming';write(s); // Lost claim response never retries send.
    const claim=post('claim',{receipt:s.receipt,hash:s.hash,attempt:s.attempt});
    if (!claim || claim.receipt!==s.receipt || claim.state!=='started' || claim.permit!==true) throw Error('No send permit');
    s.phase='sending';write(s);
    GmailApp.sendEmail(recipients.join(','),r.payload.subject,'This email requires HTML support.',{htmlBody:r.payload.html});
    s.phase='send_returned';write(s); // If this write fails, hold. Never blindly resend.
    const ack=post('ack',{receipt:s.receipt,hash:s.hash,attempt:s.attempt});
    if (!ack || ack.receipt!==s.receipt || ack.state!=='acknowledged' || ack.scope!=='bridge_send_returned_not_delivery') throw Error('Ack refused');
    props.deleteProperty(name);return {state:'acknowledged'};
  } finally {lock.releaseLock();}
}
