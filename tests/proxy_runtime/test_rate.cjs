'use strict';
const assert=require('node:assert/strict');const {peerIdentity,createLimiter}=require('../../proxy_runtime/rate-policy.cjs');
let tests=0;function test(n,f){f();tests++;console.log('PASS',n);}
test('CF/XFF ignored, direct peer only',()=>{assert.equal(peerIdentity({headers:{'cf-connecting-ip':'attacker','x-forwarded-for':'fake1,fake2'},socket:{remoteAddress:'192.0.2.1'}}),'192.0.2.1');assert.equal(peerIdentity({socket:{remoteAddress:'::ffff:192.0.2.1'}}),'192.0.2.1');assert.equal(peerIdentity({socket:{remoteAddress:'not-ip'}}),'unknown-peer');});
test('61 denied and identity flood cannot reset',()=>{const l=createLimiter();for(let i=0;i<60;i++)assert(l.allow('target'));assert(!l.allow('target'));for(let i=0;i<5001;i++)l.allow('peer'+i);assert.equal(l.size(),5000);assert(!l.allow('target'));assert(!l.allow('new'));});
test('expiry admits without erasing active counts',()=>{let now=0;const l=createLimiter({windowMs:10,max:1,capacity:2,clock:()=>now});assert(l.allow('a'));now=5;assert(l.allow('b'));now=10;assert(l.allow('c'));assert(!l.allow('b'));assert.equal(l.size(),2);});
test('invalid and backward clocks deny',()=>{let now=5;const l=createLimiter({clock:()=>now});assert(l.allow('a'));now=4;assert(!l.allow('b'));now=NaN;assert(!l.allow('a'));assert(!l.allow(''));});
test('no counter overflow after repeated denial',()=>{const l=createLimiter({max:1});assert(l.allow('a'));for(let i=0;i<10000;i++)assert(!l.allow('a'));assert.equal(l.size(),1);});
console.log(tests+' tests passed');
