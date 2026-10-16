import fs from 'node:fs';import assert from 'node:assert/strict';
const source=fs.readFileSync('integration/brics_recovery_b4/recovery.js','utf8');const {failureState,PROVIDER_ORIGIN}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
assert.equal(PROVIDER_ORIGIN,'https://www.youtube-nocookie.com');
for(const value of [null,{},0,'null','[]','{','x'.repeat(4097),JSON.stringify({event:'infoDelivery',info:[]}),JSON.stringify({event:'infoDelivery',info:{playerState:'0'}}),JSON.stringify({event:'infoDelivery',info:{playerState:1}}),JSON.stringify({event:'onError',info:'100'}),JSON.stringify({event:'onError',info:999}),JSON.stringify({event:'other',info:0})])assert.equal(failureState(value),null);
for(const value of [{event:'infoDelivery',info:{playerState:0}},{event:'onStateChange',info:0}])assert.equal(failureState(JSON.stringify(value)),'ended');
for(const info of [2,5,100,101,150])assert.equal(failureState(JSON.stringify({event:'onError',info})),'error');
console.log('bounded provider-event parser passed');
