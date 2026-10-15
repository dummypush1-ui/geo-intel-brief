'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const js=fs.readFileSync(path.join(__dirname,'../integration/public_map_m3/streets.js'),'utf8');
const fn=js.slice(js.indexOf('function source('),js.indexOf('function stop('));
assert.ok(fn.startsWith('function source('));
const source=Function('HOST','PREFIX','location',`return (${fn.trim()});`)('tiles.openfreemap.org','/workspace/map-streets/',{href:'https://preview.example/workspace/map',origin:'https://preview.example'});
for(const u of ['https://tiles.openfreemap.org/planet','https://tiles.openfreemap.org/planet/release/3/2/1.pbf','https://tiles.openfreemap.org/fonts/Noto/0-255.pbf','https://tiles.openfreemap.org/sprites/a.png','https://tiles.openfreemap.org/natural_earth/ne2/0/0/0.png','/workspace/map-streets/liberty.json']){
 const r=source(u);assert.equal(r.credentials,'omit');assert.ok(r.url.startsWith('https://'));
}
for(const u of ['http://tiles.openfreemap.org/planet','https://evil.test/planet','https://tiles.openfreemap.org.evil.test/planet','https://tiles.openfreemap.org@evil.test/planet','https://user:pass@tiles.openfreemap.org/planet','https://tiles.openfreemap.org:444/planet','https://tiles.openfreemap.org/planet?q=secret','https://tiles.openfreemap.org/planet#fragment','https://tiles.openfreemap.org/private','https://tiles.openfreemap.org./planet','https://tile.openstreetmap.org/0/0/0.png','/api/news','/workspace/map-streets/liberty.json?x=1','data:application/json,{}','javascript:alert(1)'])assert.throws(()=>source(u),Error,u);
console.log('PASS source guard:6 accepted/15 rejected, independent of browser CSP');
