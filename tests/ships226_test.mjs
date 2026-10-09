import assert from 'node:assert/strict';
import {PORT_OPTIONS226,parseShips226} from '../integration/finder198_ui/ships226.mjs';
export const fixture=(count=1)=>({ok:true,warming:false,stalled:false,updated:'2026-10-10T01:00:00.000Z',count,ports:PORT_OPTIONS226.map(([code,name])=>({code,name,count:99})),vessels:Array.from({length:Math.min(150,count)},(_,i)=>({mmsi:String(100000000+i),name:'Supplied vessel',type:'Cargo',flag:'India',sog:10,dest:'Chennai',eta:'2026-10-11 08:00 UTC',lat:13,lon:80,port:'INMAA',seenAgoSec:50}))});
assert.equal(PORT_OPTIONS226.length,42);
for(const count of [0,1,150,200])assert.ok(parseShips226(JSON.stringify(fixture(count))));
const bad=(change)=>{const d=fixture();change(d);assert.equal(parseShips226(JSON.stringify(d)),null);};
for(const key of ['ok','warming','stalled','updated','count','ports','vessels'])bad(d=>delete d[key]);
bad(d=>d.extra=true);bad(d=>d.ok=false);bad(d=>d.count=true);bad(d=>d.count=6001);bad(d=>d.updated='2026-02-30T01:00:00.000Z');bad(d=>d.updated='2026-10-10T01:00:00+00:00');bad(d=>d.ports.pop());bad(d=>d.ports.push(d.ports[0]));bad(d=>d.ports[1]=d.ports[0]);bad(d=>d.ports[0].name='fake');bad(d=>d.ports[0].count=true);bad(d=>d.ports[0].code='javascript:x');
for(const [key,value]of [['sog',true],['sog',102.4],['lat',null],['lat',91],['lon',-181],['seenAgoSec',-1],['seenAgoSec',1.5],['seenAgoSec',31536001],['mmsi',100000001],['mmsi','１２３４５６７８９'],['port','javascript:x']])bad(d=>d.vessels[0][key]=value);
for(const key of ['name','type','flag','dest','eta']){
 bad(d=>d.vessels[0][key]='x'.repeat(121));bad(d=>d.vessels[0][key]='a\u202eb');bad(d=>d.vessels[0][key]='a\u200bb');
 const d=fixture();d.vessels[0][key]='<img src=https://attack.invalid/x onerror=alert(1)> javascript:x';assert.ok(parseShips226(JSON.stringify(d)));
}
bad(d=>{d.vessels.push(d.vessels[0]);d.count=2;});
assert.equal(parseShips226('x'.repeat(1048577)),null);assert.equal(parseShips226('{}'),null);
console.log('226 supplied ship shape: PASS');
