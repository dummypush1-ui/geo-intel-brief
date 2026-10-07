/* INACTIVE additive companion: do not install any triggers yet.
 * Existing Code.gs functions/properties remain unchanged.
 * COLLECTION_BASE_URL and COLLECTION_HEADER_SECRET are separate properties.
 * Only submission implemented. No job execution or automatic recovery here.
 */
function _collectionConfig108() {
  const p = PropertiesService.getScriptProperties();
  const base = p.getProperty('COLLECTION_BASE_URL');
  const token = p.getProperty('COLLECTION_HEADER_SECRET');
  if (!base || !/^https:\/\/[a-z0-9-]+\.onrender\.com$/.test(base) ||
      !token || token.length < 48 || !/^[\x21-\x7e]+$/.test(token)) {
    throw new Error('Collection configuration missing or invalid');
  }
  return {base:base, token:token};
}
function keepAliveCollection108() {
  const c = _collectionConfig108();
  const r = UrlFetchApp.fetch(c.base + '/health', {muteHttpExceptions:true, followRedirects:false});
  if (r.getResponseCode() !== 200) throw new Error('Collection keepAlive failed');
}
function submitCollection108() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) throw new Error('Collection submission busy');
  try {
    const c = _collectionConfig108();
    const p = PropertiesService.getScriptProperties();
    // Persist nonce before HTTP; retry same request after uncertain response.
    // Its stale timestamp intentionally blocks automatic blind new submission.
    const raw = p.getProperty('COLLECTION_PENDING108');
    const b = raw ? JSON.parse(raw) : {profile:'geo108', nonce:Utilities.getUuid(), created_at:Math.floor(Date.now()/1000)};
    if (!raw) p.setProperty('COLLECTION_PENDING108',JSON.stringify(b));
    const r = UrlFetchApp.fetch(c.base + '/internal/collector108/jobs', {
      method:'post', contentType:'application/json', payload:JSON.stringify(b),
      headers:{Authorization:'Bearer '+c.token}, muteHttpExceptions:true, followRedirects:false
    });
    if (r.getResponseCode() !== 202) throw new Error('Collection submission refused or uncertain');
    const receipt = JSON.parse(r.getContentText('UTF-8'));
    const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, b.profile+'\n'+b.nonce, Utilities.Charset.UTF_8);
    const expected = bytes.map(x => ('0'+((x+256)%256).toString(16)).slice(-2)).join('');
    if (!receipt || receipt.job !== expected || typeof receipt.phase !== 'string' || !/^(accepted|running|fetch_complete|prepare_complete|write_started|completed|failed_before_write|uncertain_after_write)$/.test(receipt.phase)) {
      throw new Error('Collection receipt invalid');
    }
    // DO NOT clear pending until authenticated terminal status/reconciliation
    // is implemented; acceptance != completed collection.
    return {job:receipt.job, phase:receipt.phase};
  } finally {lock.releaseLock();}
}
