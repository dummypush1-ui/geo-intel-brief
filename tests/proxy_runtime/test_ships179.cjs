'use strict';const assert=require('node:assert/strict');const {shipsReads}=require('../../proxy_runtime/ships-read.cjs');let t=0,builds=0;const p=shipsReads({clock:()=>t,maxKeys:2});
for(let i=0;i<20;i++)assert(p.allow('peer1'));assert(!p.allow('peer1'));assert(p.allow('peer2'));
assert.equal(p.snapshot('ALL',()=>++builds),1);assert.equal(p.snapshot('ALL',()=>++builds),1);assert.equal(p.snapshot('PORT',()=>++builds),2);assert.throws(()=>p.snapshot('EXTRA',()=>++builds));t=30001;assert.equal(p.snapshot('ALL',()=>++builds),3);assert.equal(p.size(),1);t=600001;assert(p.allow('peer1'));console.log('ships179 separatequota/cachettl/cap/expiry PASS');

const shared=shipsReads({clock:()=>t});for(let i=0;i<60;i++)assert(shared.allow(`peer${i}`));assert(!shared.allow("peer61"));t+=600001;assert(shared.allow("peer61"));console.log("ships179 independent shared60 cap/reset PASS");
