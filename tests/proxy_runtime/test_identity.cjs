'use strict';
const assert=require('node:assert/strict'),{identityPolicy,quotaPolicy}=require('../../proxy_runtime/identity-policy.cjs');
let tests=0;function test(n,f){f();tests++;console.log('PASS',n);}
const req=(peer,xff,raw=['X-Forwarded-For',xff])=>({socket:{remoteAddress:peer},headers:{'x-forwarded-for':xff,'cf-connecting-ip':'203.0.113.99'},rawHeaders:raw});
test('default ignores all spoofed headers',()=>{const p=identityPolicy();assert.equal(p(req('192.0.2.1','203.0.113.1')),'192.0.2.1');assert.equal(p(req('::ffff:192.0.2.1','203.0.113.1')),'192.0.2.1');assert.equal(p(req('bad','203.0.113.1')),'unknown-peer');});
test('trust requires explicit topology and exact valid peers',()=>{assert.throws(()=>identityPolicy({PROXY_TRUSTED_PEERS:'192.0.2.1'}));for(const v of ['bad','192.0.2.1,192.0.2.1','0.0.0.0/0'])assert.throws(()=>identityPolicy({PROXY_TRUSTED_PEERS:v,PROXY_XFF_TOPOLOGY_VERIFIED:'single_appended_hop'}));});
const p=identityPolicy({PROXY_TRUSTED_PEERS:'192.0.2.1',PROXY_XFF_TOPOLOGY_VERIFIED:'single_appended_hop'});
test('only verified direct peer uses appended hop',()=>{assert.equal(p(req('192.0.2.1','203.0.113.99, 198.51.100.2')),'198.51.100.2');assert.equal(p(req('192.0.2.2','198.51.100.2')),'192.0.2.2');});
test('duplicate malformed overlong and invalid chains fall back',()=>{for(const x of ['bad','198.51.100.2,','127.0.0.1:3','x'.repeat(1025),Array(17).fill('198.51.100.2').join(',')])assert.equal(p(req('192.0.2.1',x)),'192.0.2.1');assert.equal(p(req('192.0.2.1','198.51.100.2',['X-Forwarded-For','198.51.100.2','x-forwarded-for','203.0.113.1'])),'192.0.2.1');});
test('mapped IPv6 case and bounded env quotas',()=>{assert.equal(identityPolicy()(req('::FFFF:192.0.2.1','203.0.113.1')),'192.0.2.1');assert.equal(quotaPolicy().perPeer,20);assert.equal(quotaPolicy({PROXY_PER_PEER_LIMIT:'10',PROXY_SHARED_LIMIT:'30'}).shared,30);for(const v of ['0','-1','1001','2.5',' 20','abc'])assert.throws(()=>quotaPolicy({PROXY_PER_PEER_LIMIT:v}));assert.throws(()=>quotaPolicy({PROXY_PER_PEER_LIMIT:'61'}));});
console.log(tests+' tests passed');
