// Preparation only. No true caller, live installer, timer or mail run here.
function scheduledMailV1Weekly217(enable,event) { return mailSchedule217Run_(enable,event,'weekly'); }
function scheduledMailV1Critical217(enable,event) { return mailSchedule217Run_(enable,event,'critical'); }
function mailSchedule217Gate_(enable) {
  if (enable !== true) return null;
  const p=PropertiesService.getScriptProperties();
  if (p.getProperty('MAIL_V1_SCHEDULER_ENABLED') !== 'true' || p.getProperty('MAIL_V1_ENABLED') !== 'true') return null;
  return p;
}
function mailSchedule217Read_(p) {
  const day=p.getProperty('MAIL217_WEEKLY_DAY'),time=p.getProperty('MAIL217_WEEKLY_TIME');
  const minutes=p.getProperty('MAIL217_CRITICAL_MINUTES'),zone=p.getProperty('MAIL217_TIMEZONE');
  if (!['MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY'].includes(day) ||
      typeof time !== 'string' || !/^([01]\d|2[0-3]):[0-5]\d$/.test(time) || !['1','5','10','15','30'].includes(minutes) ||
      typeof zone !== 'string' || !/^[A-Za-z_]+(?:\/[A-Za-z0-9_+-]+)+$/.test(zone)) throw Error('mail217_schedule_refused');
  // Validates actual timezone before any trigger mutation. No owner defaults.
  Utilities.formatDate(new Date(0),zone,'yyyy-MM-dd');
  return {day,time,minutes:Number(minutes),zone};
}
function mailSchedule217State_(p) {
  const raw=p.getProperty('MAIL217_OWNED');
  if (raw === null) return {active:[],inactive:[],staged:[]};
  if (raw.length>4096) throw Error('mail217_state_refused');
  const s=JSON.parse(raw);
  if (!s || Object.keys(s).sort().join(',')!=='active,inactive,staged' || ['active','inactive','staged'].some(k=>!Array.isArray(s[k])||s[k].length>20||s[k].some(x=>typeof x!=='string'||!/^[A-Za-z0-9_-]{1,100}$/.test(x))) || new Set([...s.active,...s.inactive,...s.staged]).size!==s.active.length+s.inactive.length+s.staged.length) throw Error('mail217_state_refused');
  return s;
}
function mailSchedule217Write_(p,key,value) {
  const raw=JSON.stringify(value);p.setProperty(key,raw);
  if (p.getProperty(key)!==raw) throw Error('mail217_readback_held');
}
function installMailV1Schedules217(enable) {
  const p=mailSchedule217Gate_(enable);if (!p) return Object.freeze({state:'off'});
  const lock=LockService.getScriptLock();if(!lock.tryLock(1000))throw Error('mail217_busy');
  try {
    if(p.getProperty('MAIL217_OPERATION')!==null)throw Error('mail217_operation_held');
    const config=mailSchedule217Read_(p),s=mailSchedule217State_(p),triggers=ScriptApp.getProjectTriggers();
    const names=['scheduledMailV1Weekly217','scheduledMailV1Critical217'];
    const known=new Set([...s.active,...s.inactive,...s.staged]);
    if(s.staged.length||s.inactive.length)throw Error('mail217_recovery_held');
    if(triggers.some(t=>names.includes(t.getHandlerFunction())&&!known.has(t.getUniqueId())))throw Error('mail217_adoption_held');
    if(s.active.some(id=>!triggers.some(t=>t.getUniqueId()===id&&names.includes(t.getHandlerFunction()))))throw Error('mail217_missing_owned_held');
    if(triggers.length+2>20)throw Error('mail217_quota_held');
    const operation={state:'creating',old:s.active.slice(),created:[]};
    mailSchedule217Write_(p,'MAIL217_OPERATION',operation); // Before possible creation.
    const [hour,minute]=config.time.split(':').map(Number);
    const weekly=ScriptApp.newTrigger(names[0]).timeBased().onWeekDay(ScriptApp.WeekDay[config.day]).atHour(hour).nearMinute(minute).inTimezone(config.zone).create();
    operation.created.push(weekly.getUniqueId());mailSchedule217Write_(p,'MAIL217_OPERATION',operation);
    const critical=ScriptApp.newTrigger(names[1]).timeBased().everyMinutes(config.minutes).create();
    operation.created.push(critical.getUniqueId());mailSchedule217Write_(p,'MAIL217_OPERATION',operation);
    s.staged=operation.created.slice();mailSchedule217Write_(p,'MAIL217_OWNED',s);
    s.inactive=s.active.slice();s.active=s.staged.slice();s.staged=[];mailSchedule217Write_(p,'MAIL217_OWNED',s);
    operation.state='retiring';mailSchedule217Write_(p,'MAIL217_OPERATION',operation);
    for(const t of triggers)if(s.inactive.includes(t.getUniqueId()))ScriptApp.deleteTrigger(t);
    s.inactive=[];mailSchedule217Write_(p,'MAIL217_OWNED',s);p.deleteProperty('MAIL217_OPERATION');
    return Object.freeze({state:'installed_not_live_proven'});
  } catch(e) { throw Error('mail217_install_held_manual_recovery'); }
  finally {lock.releaseLock();}
}
function removeMailV1Schedules217(enable) {
  const p=mailSchedule217Gate_(enable);if(!p)return Object.freeze({state:'off'});
  const lock=LockService.getScriptLock();if(!lock.tryLock(1000))throw Error('mail217_busy');
  try {
    if(p.getProperty('MAIL217_OPERATION')!==null)throw Error('mail217_operation_held');
    const s=mailSchedule217State_(p),ids=[...s.active,...s.inactive,...s.staged];
    mailSchedule217Write_(p,'MAIL217_OPERATION',{state:'removing',owned:ids});
    mailSchedule217Write_(p,'MAIL217_OWNED',{active:[],inactive:ids,staged:[]});
    for(const t of ScriptApp.getProjectTriggers())if(ids.includes(t.getUniqueId()))ScriptApp.deleteTrigger(t);
    mailSchedule217Write_(p,'MAIL217_OWNED',{active:[],inactive:[],staged:[]});p.deleteProperty('MAIL217_OPERATION');
    return Object.freeze({state:'removed'});
  }catch(e){throw Error('mail217_remove_held_manual_recovery');}
  finally{lock.releaseLock();}
}
function mailSchedule217Run_(enable,event,kind) {
  const p=mailSchedule217Gate_(enable);if(!p)return Object.freeze({state:'off'});
  if(!event || typeof event.triggerUid!=='string')return Object.freeze({state:'unowned_event'});
  const lock=LockService.getScriptLock();if(!lock.tryLock(1000))throw Error('mail217_busy');
  let send=false;
  try {
    const s=mailSchedule217State_(p);
    if(p.getProperty('MAIL217_OPERATION')!==null||!s.active.includes(event.triggerUid))return Object.freeze({state:'held_event'});
    const c=mailSchedule217Read_(p),stamp=new Date();
    let occurrence;
    if(kind==='weekly'){
      const local=Utilities.formatDate(stamp,c.zone,'yyyy-MM-dd'),d=new Date(local+'T00:00:00Z');
      d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7));occurrence='weekly:'+d.toISOString().slice(0,10);
    }else if(kind==='critical')occurrence='critical:'+Math.floor(stamp.getTime()/(c.minutes*60000));
    else throw Error('mail217_kind_refused');
    const raw=p.getProperty('MAIL217_OCCURRENCES'),seen=raw===null?[]:JSON.parse(raw);
    if(!Array.isArray(seen)||seen.length>128||seen.some(x=>typeof x!=='string'||x.length>80)||new Set(seen).size!==seen.length)throw Error('mail217_occurrence_refused');
    if(seen.includes(occurrence))return Object.freeze({state:'occurrence_held_no_retry'});
    if(seen.length>=128)throw Error('mail217_occurrence_capacity_held');
    seen.push(occurrence);mailSchedule217Write_(p,'MAIL217_OCCURRENCES',seen);send=true;
  }finally{lock.releaseLock();} // 216/bridge obtains same lock; never nest it.
  if(send){if(kind==='weekly')return mailV1Weekly216(true);return mailV1Critical216(true);}
}
