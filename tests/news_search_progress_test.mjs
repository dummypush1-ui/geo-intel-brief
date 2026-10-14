import assert from 'node:assert/strict';import {newsScrollController} from '../integration/ui/news_search_progress.js';
const a='a'.repeat(43),b='b'.repeat(43);
const data=(items=[],cursor=a,offset=0,scan=1000)=>({items,scope:'whole_geo_store_cursor',consistency:'mutable_read_not_snapshot',sort_semantics:'raw_mongo_source_fields_with_id_tiebreak',limit:25,offset,next_cursor:cursor,exhausted:cursor===null,scanned_this_page:scan,total_count:null});
let calls=[],pending=[],pages=[],states=[];
const c=newsScrollController({fetchPage:(f,t,s)=>{calls.push({f,t,s});return new Promise((resolve,reject)=>pending.push({resolve,reject}));},onPage:(p,s)=>pages.push({p,s}),onState:(t,s)=>{if(t)states.push(t);}});
let job=c.reset({q:'old',category:'TRADE',country:'IN',sort:'newest',project:'geo'});pending.shift().resolve(data());await job;
assert.match(states.at(-1),/Scanned 1 pages \/ 1000 source rows; 0 matching/);assert.match(states.at(-1),/keep searching/);assert.equal(pages[0].s.ended,false);
job=c.more();assert.equal(calls.at(-1).f.q,'old');pending.shift().resolve(data([{title:'old match'}],null,0,25));await job;assert.match(states.at(-1),/Scanned 2 pages \/ 1025 source rows; 1 matching/);assert.match(states.at(-1),/exhausted without error/);assert.equal(await c.more(),false);
let old=c.reset({q:'stale'}),newer=c.reset({q:'new'});assert.equal(calls.at(-2).s.aborted,true);pending.shift().resolve(data([{title:'stale'}],null,0,1));await old;assert.equal(pages.length,2);pending.shift().resolve(data([],null,0,0));await newer;assert.equal(pages.length,3);
for(const mutation of [{exhausted:true},{offset:1},{total_count:0},{scanned_this_page:1001},{limit:100},{secret:'bad'},{sort_semantics:'wrong'},{scanned_this_page:-1},{next_cursor:'short'}]){job=c.reset({q:'bad'});pending.shift().resolve({...data(),...mutation});await job;assert.equal(await c.more(),false);assert.match(states.at(-1),/Invalid search page/);}
job=c.reset({q:'429'});pending.shift().reject(Error('429 busy. Not complete.'));await job;let n=calls.length;assert.equal(await c.more(),false);assert.equal(calls.length,n);
job=c.reset({q:'cancel'});c.cancel();pending.shift().resolve(data());await job;assert.match(states.at(-1),/not immediately/);
console.log('S1 progress, EOF, empty continuation, schema mutants, stale reset, cancel, no retry PASS');
