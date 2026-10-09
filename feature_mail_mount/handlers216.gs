// Copyright (c) 2026 Push. All rights reserved.
// Manual-only, OFF from editor Run. Never deploy as an API executable.
function mailV1Digest216(enabled) {
  if (enabled === false || enabled === undefined) return Object.freeze({state:'off',scope:'no_send_attempt'});
  if (typeof enabled !== 'boolean' || enabled !== true) throw Error('mail216_refused');
  let result;
  try { result = runMailV1('digest'); }
  catch (ignored) { throw Error('mail216_possibly_sent'); }
  return mail216Result(result);
}
function mailV1Critical216(enabled) {
  if (enabled === false || enabled === undefined) return Object.freeze({state:'off',scope:'no_send_attempt'});
  if (typeof enabled !== 'boolean' || enabled !== true) throw Error('mail216_refused');
  let result;
  try { result = runMailV1('critical'); }
  catch (ignored) { throw Error('mail216_possibly_sent'); }
  return mail216Result(result);
}
function mailV1Weekly216(enabled) {
  if (enabled === false || enabled === undefined) return Object.freeze({state:'off',scope:'no_send_attempt'});
  if (typeof enabled !== 'boolean' || enabled !== true) throw Error('mail216_refused');
  let result;
  try { result = runMailV1('weekly'); }
  catch (ignored) { throw Error('mail216_possibly_sent'); }
  return mail216Result(result);
}
function mail216Result(result) {
  let state;
  try {
    if (!result || typeof result !== 'object' || Array.isArray(result)) throw Error();
    state = result.state;
  } catch (ignored) { throw Error('mail216_unknown'); }
  if (state === 'off' || state === 'skipped') return Object.freeze({state:state,scope:'no_send_attempt'});
  if (state === 'acknowledged') return Object.freeze({state:'acknowledged',scope:'send_returned_not_delivery'});
  throw Error('mail216_unknown');
}
