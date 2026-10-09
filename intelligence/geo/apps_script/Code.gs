/**
 * Geo Intel Monitor — Apps Script companion.
 *
 * SETUP:
 *  1. In Google Apps Script (script.google.com), create a new project,
 *     paste this file in as Code.gs.
 *  2. Go to Project Settings (gear icon) > Script Properties and add
 *     the REQUIRED rows:
 *       RENDER_BASE_URL   -> https://your-app-name.onrender.com
 *       TRIGGER_SECRET    -> (same value as TRIGGER_SECRET in Render)
 *       EMAIL_TO          -> yourgmail@gmail.com (comma-separate for
 *                             multiple recipients)
 *
 *     Optional — customize the schedule. SET THESE YOURSELF, however you
 *     like — nothing is hardcoded to 10:00/22:00 anymore:
 *       DIGEST_TIMES               -> comma-separated "HH:MM" list, e.g.
 *                                      "08:00,13:30,20:00" — as many as
 *                                      you want, any times you want.
 *                                      Default if unset: "10:00,22:00".
 *                                      IGNORED if DIGEST_INTERVAL_HOURS is set.
 *       DIGEST_INTERVAL_HOURS       -> send the digest every N hours instead
 *                                      of at fixed clock times, e.g. "1" for
 *                                      hourly. Allowed values: 1, 2, 4, 6, 8,
 *                                      12 (Apps Script's own restriction on
 *                                      hourly triggers). Uses ONE trigger
 *                                      instead of one-per-time, so this is
 *                                      the right way to do "every hour" --
 *                                      listing 24 DIGEST_TIMES entries would
 *                                      blow past Apps Script's 20-triggersper-project limit once combined with keepAlive/runCollect/etc. Unset
 *                                      by default -- DIGEST_TIMES is used
 *                                      unless you set this.
 *       WEEKLY_DAY                 -> default MONDAY (MONDAY..SUNDAY)
 *       WEEKLY_TIME                -> default 09:00
 *       KEEPALIVE_INTERVAL_MIN     -> default 10
 *       COLLECT_INTERVAL_MIN       -> default 30
 *       CRITICAL_CHECK_INTERVAL_MIN -> default 30
 *
 *  3. Run setupTriggers() once (function dropdown > setupTriggers >
 *     Run) and approve the permissions it asks for.
 *  4. To CHANGE any time later: update the Script Property's value, then
 *     run setupTriggers() again (validates and stages replacements before removing
 *     known managed triggers; unrelated triggers are preserved). This is
 *     the only step needed to change your schedule yourself, any time.
 *
 * DASHBOARD AS AN APPS SCRIPT WEB PAGE (optional):
 *  If you'd rather open your dashboard at a script.google.com URL instead
 *  of remembering your Render URL, deploy this same project as a Web App:
 *    Deploy > New deployment > select type "Web app" >
 *    Execute as: Me > Who has access: Only myself (or "Anyone with the
 *    link" if you want to share it) > Deploy.
 *  Copy the Web App URL it gives you and open it in a browser — doGet()
 *  below fetches your Render dashboard and serves it through that URL.
 */

function _props() {
  return PropertiesService.getScriptProperties();
}

// Strict schedule parsing: invalid configured values fail before trigger changes.
function _parseTime(raw) {
  if (typeof raw !== 'string' || !/^([01]\d|2[0-3]):[0-5]\d$/.test(raw)) return null;
  const parts = raw.split(':');
  return {hour: Number(parts[0]), minute: Number(parts[1])};
}
function _readDigestTimes() {
  const raw = _props().getProperty('DIGEST_TIMES');
  const values = (raw === null ? '10:00,22:00' : raw).split(',').map(s => s.trim());
  const times = values.map(_parseTime);
  if (!times.length || times.some(t => !t) || new Set(values).size !== values.length)
    throw new Error('Invalid digest times');
  return times;
}
function _readTime(propName, fallback) {
  const raw = _props().getProperty(propName);
  const time = _parseTime(raw === null ? fallback : raw);
  if (!time) throw new Error('Invalid schedule time');
  return time;
}
function _readInt(propName, fallback) {
  const raw = _props().getProperty(propName);
  if (raw === null) return fallback;
  if (typeof raw !== 'string' || !/^(0|[1-9]\d*)$/.test(raw)) throw new Error('Invalid schedule interval');
  const n = Number(raw);
  if (!Number.isSafeInteger(n)) throw new Error('Invalid schedule interval');
  return n;
}
function _readWeekDay(propName, fallback) {
  const raw = _props().getProperty(propName);
  const day = raw === null ? fallback : raw;
  if (!/^(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)$/.test(day) || ScriptApp.WeekDay[day] === undefined)
    throw new Error('Invalid weekly day');
  return ScriptApp.WeekDay[day];
}

// Query credentials are no longer supported. No secrets in URLs or HTML.
function _renderFetch(path, options) {
  const base = _props().getProperty('RENDER_BASE_URL');
  const secret = _props().getProperty('TRIGGER_SECRET');
  if (typeof base !== 'string' || !/^https:\/\/[a-z0-9.-]+(?::443)?\/?$/.test(base))
    throw new Error('Canonical HTTPS Render origin required');
  if (typeof secret !== 'string' || !secret.trim())
    throw new Error('Non-empty trigger credential required');
  if (typeof path !== 'string' || !/^\/[a-z-]+$/.test(path))
    throw new Error('Fixed Render route required');
  const opts = Object.assign({}, options || {});
  opts.headers = Object.assign({}, opts.headers || {}, {'X-Trigger-Secret': secret});
  // Never follow a redirect carrying the credential to another origin.
  opts.followRedirects = false;
  return UrlFetchApp.fetch(base.replace(/\/$/, '') + path, opts);
}

// HTTP response bodies and transport exceptions may contain private data.
// Only fixed status labels are logged. Held 403 is never treated as success.
function _checkedRender(path, options) {
  let resp;
  try { resp = _renderFetch(path, options); }
  catch (e) { Logger.log('Render transport failed'); throw new Error('Render transport failed'); }
  const code = resp.getResponseCode();
  if (code === 403) { Logger.log('Render route held: HTTP 403'); throw new Error('Render route held: HTTP 403'); }
  if (code !== 200) { Logger.log('Render request failed: HTTP non-200'); throw new Error('Render request failed'); }
  return resp;
}

/** Cheap ping, just to stop the free Render instance from sleeping. */
function keepAlive() {
  _checkedRender('/health', {muteHttpExceptions: true});
}

/** Collection remains controlled by the Render installation gates. */
function runCollect() {
  _checkedRender('/collect', {method: 'post', muteHttpExceptions: true});
}

/** Fetches the digest from Render and emails it via Gmail. Runs at every
 * time listed in DIGEST_TIMES. */
function sendDigest() {
  const emailTo = _props().getProperty('EMAIL_TO');
  const resp = _checkedRender('/digest-data', {
    method: 'get',
    muteHttpExceptions: true,
  });

  // Explicit UTF-8 decode — without this, emoji and other multi-byte
  // characters in the digest get corrupted into "������" garbage text.
  const data = JSON.parse(resp.getContentText('UTF-8'));

  // At an hourly (or otherwise frequent) cadence, most cycles will have
  // nothing new. Skip sending an empty "No items this cycle" email rather
  // than filling the inbox — only skip if there's also nothing critical to
  // flag. Remove this block if you'd rather always get a "still nothing new"
  // email as a heartbeat.
  if ((!data.article_ids || data.article_ids.length === 0) && !(data.critical_count > 0)) {
    Logger.log('sendDigest: nothing new this cycle, skipped sending.');
    return;
  }

  const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd MMM yyyy HH:mm');
  const subject = '🌍 Geo Intel Brief — ' + today +
      (data.critical_count > 0 ? '  ⚠️ ' + data.critical_count + ' CRITICAL' : '');

  GmailApp.sendEmail(emailTo, subject, 'This email requires HTML support.', {
    htmlBody: data.html,
  });

  // Only tell Render to mark these articles as "sent" AFTER the Gmail send
  // above did not throw. An acknowledgement failure leaves unknown receipt
  // state and requires manual review, not another send. This legacy companion
  // has no durable receipt fence and remains uninstalled while routes are held.
  if (data.article_ids && data.article_ids.length) {
    try {
      _checkedRender('/mark-emailed', {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({ article_ids: data.article_ids }),
        muteHttpExceptions: true,
      });
    } catch (e) {
      Logger.log('Digest acknowledgement failed: receipt state unknown; manual review required');
      throw new Error('Digest acknowledgement failed: receipt state unknown');
    }
  }
}

/** Checks for CRITICAL items and sends an instant alert if found. Runs every
 * CRITICAL_CHECK_INTERVAL_MIN minutes. */
function checkCritical() {
  _checkedRender('/critical', {method: 'post', muteHttpExceptions: true});
}

/** Sends the weekly report only if the server accepts the route. */
function sendWeekly() {
  _checkedRender('/weekly', {method: 'post', muteHttpExceptions: true});
}

/** Cleanup is held. No requests or deletion until retention is implemented. */
function cleanupOld() {
  Logger.log('cleanupOld held: retention policy not implemented');
}

/** Explicit installation only. Validate the complete schedule before staging
 * replacements; inspect partial failures before retrying. Apps Script
 * nearMinute timers are approximate, not exact-minute delivery. Capacity or
 * partial failures require inspecting project triggers before retrying. */
function setupTriggers() {
  const keepAliveMin = _readInt('KEEPALIVE_INTERVAL_MIN', 10);
  const collectMin = _readInt('COLLECT_INTERVAL_MIN', 30);
  const criticalMin = _readInt('CRITICAL_CHECK_INTERVAL_MIN', 30);
  const intervalRaw = _props().getProperty('DIGEST_INTERVAL_HOURS');
  const digestIntervalHours = intervalRaw === null ? 0 : _readInt('DIGEST_INTERVAL_HOURS', 0);
  if (![1,5,10,15,30].includes(keepAliveMin) || ![1,5,10,15,30].includes(collectMin) || ![1,5,10,15,30].includes(criticalMin))
    throw new Error('Unsupported minute interval');
  if (intervalRaw !== null && ![1,2,4,6,8,12].includes(digestIntervalHours))
    throw new Error('Unsupported digest interval');
  const digestTimes = digestIntervalHours ? [] : _readDigestTimes();
  const weeklyDay = _readWeekDay('WEEKLY_DAY', 'MONDAY');
  const weeklyTime = _readTime('WEEKLY_TIME', '09:00');
  const existing = ScriptApp.getProjectTriggers();
  const handlers = ['keepAlive','runCollect','sendDigest','checkCritical','sendWeekly','cleanupOld'];
  const old = existing.filter(t => handlers.includes(t.getHandlerFunction()));
  const count = 4 + (digestIntervalHours ? 1 : digestTimes.length);
  // Stage replacements before deleting anything. Old triggers count against
  // Google's project quota too. Refuse if staging cannot fit; do not destroy
  // the old schedule to make room. Unrelated handlers are never touched.
  if (count > 20 || existing.length + count > 20)
    throw new Error('Trigger staging capacity exceeded; existing schedule unchanged');
  const created = [];
  try {
    created.push(ScriptApp.newTrigger('keepAlive').timeBased().everyMinutes(keepAliveMin).create());
    created.push(ScriptApp.newTrigger('runCollect').timeBased().everyMinutes(collectMin).create());
    if (digestIntervalHours) {
      created.push(ScriptApp.newTrigger('sendDigest').timeBased().everyHours(digestIntervalHours).create());
    } else {
      digestTimes.forEach(t => created.push(ScriptApp.newTrigger('sendDigest').timeBased().atHour(t.hour).nearMinute(t.minute).everyDays(1).create()));
    }
    created.push(ScriptApp.newTrigger('checkCritical').timeBased().everyMinutes(criticalMin).create());
    created.push(ScriptApp.newTrigger('sendWeekly').timeBased().onWeekDay(weeklyDay).atHour(weeklyTime.hour).nearMinute(weeklyTime.minute).create());
  } catch (e) {
    let cleanupFailed = false;
    created.forEach(t => {try {ScriptApp.deleteTrigger(t);} catch (ignored) {cleanupFailed = true;}});
    Logger.log(cleanupFailed ? 'Trigger creation failed; staged cleanup incomplete; manual review required' : 'Trigger creation failed; staged triggers removed; existing schedule unchanged');
    throw new Error('Trigger creation failed; inspect project triggers before retry');
  }
  try { old.forEach(t => ScriptApp.deleteTrigger(t)); }
  catch (e) {
    // Deletion is not transactional. Keep complete replacement schedule,
    // report duplicates/partial deletion rather than claim rollback.
    Logger.log('Trigger replacement incomplete; old triggers may remain; manual review required');
    throw new Error('Trigger replacement incomplete; inspect duplicates before retry');
  }
  Logger.log('Managed schedule replaced; unrelated triggers preserved; cleanup disabled');
}

/**
 * Serves your Render dashboard through this Apps Script's own Web App URL,
 * so you have a script.google.com link for it instead of only the Render
 * URL. Requires deploying this project as a Web App (see setup notes at
 * the top of this file). Just proxies/fetches — all the actual data still
 * comes from Render/MongoDB/Telegram; this changes nothing about the data.
 */
function doGet(e) {
  const resp = _renderFetch('/dashboard', { muteHttpExceptions: true });
  if (resp.getResponseCode() !== 200) {
    return HtmlService.createHtmlOutput(
      '<p>Could not load dashboard from Render (HTTP ' + resp.getResponseCode() + '). ' +
      'Check RENDER_BASE_URL and TRIGGER_SECRET in Script Properties.</p>'
    );
  }
  return HtmlService.createHtmlOutput(resp.getContentText('UTF-8'))
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
