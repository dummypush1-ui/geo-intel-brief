/* INACTIVE fixture polling companion. Do not install triggers.
 * Reuses COLLECTION_PENDING108 submitted by reviewed companion.
 * Does not clear pending, create nonce, enable fetch/writer, or send mail.
 */
function _collectionPending109() {
  const raw = PropertiesService.getScriptProperties().getProperty('COLLECTION_PENDING108');
  if (!raw) throw new Error('No pending collection job');
  const b = JSON.parse(raw);
  if (!b || Object.keys(b).sort().join(',') !== 'created_at,nonce,profile' ||
      b.profile !== 'geo108' || typeof b.nonce !== 'string' || !/^[A-Za-z0-9_-]{20,80}$/.test(b.nonce) ||
      !Number.isSafeInteger(b.created_at) || b.created_at < 0) throw new Error('Invalid pending collection');
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, b.profile+'\n'+b.nonce, Utilities.Charset.UTF_8);
  const key = bytes.map(x => ('0'+((x+256)%256).toString(16)).slice(-2)).join('');
  return {body:b, key:key};
}
function _collectionStatus109(c,key) {
  const r = UrlFetchApp.fetch(c.base+'/internal/collector109/jobs/'+key, {
    headers:{Authorization:'Bearer '+c.token}, muteHttpExceptions:true, followRedirects:false
  });
  if (r.getResponseCode() !== 200) throw new Error('Collection status unavailable');
  const s = JSON.parse(r.getContentText('UTF-8'));
  if (!s || Object.keys(s).sort().join(',') !== 'counts,job,phase' || s.job !== key ||
      typeof s.phase !== 'string' || !/^(accepted|running|fetch_complete|prepare_complete|write_started|completed|failed_before_write|uncertain_after_write)$/.test(s.phase) ||
      !s.counts || typeof s.counts !== 'object' || Array.isArray(s.counts)) throw new Error('Invalid collection status');
  Object.keys(s.counts).forEach(k => {
    if (!/^(fetched|prepared|attempted|inserted|duplicate|failed|uncertain)$/.test(k) ||
        !Number.isSafeInteger(s.counts[k]) || s.counts[k] < 0 || s.counts[k] > 1000) throw new Error('Invalid collection counts');
  });
  return s;
}
function pollDriveCollection109() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('Collection drive busy');
  try {
    const c = _collectionConfig108();
    const pending = _collectionPending109();
    const before = _collectionStatus109(c,pending.key);
    // Never drive uncertain/write_started or terminal jobs; no blind replay.
    if (!/^(accepted|running|fetch_complete|prepare_complete)$/.test(before.phase)) return before;
    const r = UrlFetchApp.fetch(c.base+'/internal/collector109/jobs/'+pending.key+'/drive', {
      method:'post', contentType:'application/json', payload:'{}',
      headers:{Authorization:'Bearer '+c.token}, muteHttpExceptions:true, followRedirects:false
    });
    if (r.getResponseCode() !== 200) throw new Error('Collection drive refused or uncertain');
    const receipt = JSON.parse(r.getContentText('UTF-8'));
    if (!receipt || Object.keys(receipt).sort().join(',') !== 'job,phase,state' || receipt.job !== pending.key ||
        receipt.state !== 'held_before_write' || receipt.phase !== 'prepare_complete') throw new Error('Invalid inactive drive receipt');
    // Status is authoritative; acceptance/hold is not completed collection.
    const after = _collectionStatus109(c,pending.key);
    if (after.phase !== 'prepare_complete') throw new Error('Inactive drive status changed');
    return after;
  } finally {lock.releaseLock();}
}
