import assert from 'node:assert/strict';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import crypto from 'node:crypto';import zlib from 'node:zlib';
import {buildBundle,commitBundle,readBase,validateBundle} from '../../updater_runtime/refresh-bundle.mjs';
const root=fs.mkdtempSync(path.join(os.tmpdir(),'refresh-test-'));
const old='data.111111111111.js';
const snapshot=dir=>Object.fromEntries(fs.readdirSync(dir,{recursive:true}).filter(p=>fs.statSync(path.join(dir,p)).isFile()).map(p=>[p,fs.readFileSync(path.join(dir,p)).toString('base64')]));
try {
 fs.mkdirSync(path.join(root,'src'));fs.mkdirSync(path.join(root,'vendor'));
 fs.writeFileSync(path.join(root,'build.mjs'),'fixture');fs.writeFileSync(path.join(root,'src/app.js'),'const TRADE_YEAR = 2024;');fs.writeFileSync(path.join(root,'src/tradevalues.ts'),'prior');
 const chunk=zlib.gzipSync(Buffer.from(JSON.stringify([['IN','123456','<b>trade</b>']]))).toString('base64');fs.writeFileSync(path.join(root,'src/datachunk0.ts'),`export const CHUNK0 = "${chunk}";`);
 fs.writeFileSync(path.join(root,old),'prior data');fs.writeFileSync(path.join(root,'keep.js'),'keep');
 const before=snapshot(root);
 const fakeBuild=dir=>{assert.equal(fs.readFileSync(path.join(dir,'src/tradevalues.ts'),'utf8'),'next');const data='var DATA_B64 = "fixture";\n';const v=crypto.createHash('sha256').update(data).digest('hex').slice(0,12);const n=`data.${v}.js`;fs.writeFileSync(path.join(dir,n),data);fs.writeFileSync(path.join(dir,'index.html'),`data.src = './${n}'`);fs.writeFileSync(path.join(dir,'sw.js'),`hsn-data-${v} ./`+n);fs.writeFileSync(path.join(dir,'offline.html'),data);};
 const files=buildBundle(root,[{path:'src/tradevalues.ts',content:'next'}],[old],fakeBuild);
 assert.deepEqual(snapshot(root),before);assert.deepEqual(files.filter(f=>f.content===null),[{path:old,content:null}]);assert.ok(files.some(f=>f.path==='sw.js'));assert.ok(files.some(f=>f.path==='offline.html'));
 for (const p of ['../secret','keep.js','src/app.js']) assert.throws(()=>validateBundle([{path:p,content:null}]));
 assert.throws(()=>buildBundle(root,[{path:'src/tradevalues.ts',content:'next'}],[old],()=>{throw Error('build failed')}),/build failed/);assert.deepEqual(snapshot(root),before);
 assert.throws(()=>buildBundle(root,[{path:'src/tradevalues.ts',content:'next'}],[old],dir=>{fakeBuild(dir);fs.writeFileSync(path.join(dir,'sw.js'),'wrong')}),/identity mismatch/);
 const A='a'.repeat(40),B='b'.repeat(40),C='c'.repeat(40),D='d'.repeat(40);const base={sha:A,treeSha:B,oldData:[old]};
 let calls=[];const gh=async(method,url,body)=>{calls.push({method,url,body});if(method==='GET')return{object:{sha:A}};if(url.endsWith('/blobs'))return{sha:B};if(url.endsWith('/trees'))return{sha:C};if(url.endsWith('/commits'))return{sha:D};return{object:{sha:D}};};
 assert.equal(await commitBundle(gh,'u/r','main',base,files,'fixture'),D);const tree=calls.find(c=>c.url.endsWith('/trees')).body;assert.equal(tree.base_tree,B);assert.equal(tree.tree.find(r=>r.path===old).sha,null);assert.deepEqual(calls.find(c=>c.url.endsWith('/commits')).body.parents,[A]);assert.equal(calls.at(-1).body.force,false);
 let posts=0;await assert.rejects(commitBundle(async()=>{posts++;return{object:{sha:B}}},'u/r','main',base,files,'fixture'),/Branch moved/);assert.equal(posts,1);
 calls=[];await assert.rejects(commitBundle(async(m,u,b)=>{if(u.endsWith('/commits'))throw Error('commit failed');return gh(m,u,b)},'u/r','main',base,files,'fixture'),/commit failed/);assert.equal(calls.filter(c=>c.method==='PATCH').length,0);
 calls=[];await assert.rejects(commitBundle(async(m,u,b)=>{if(m==='PATCH')throw Error('concurrent move HTTP422');return gh(m,u,b)},'u/r','main',base,files,'fixture'),/Ref publication uncertain/);
 await assert.rejects(commitBundle(gh,'u/r','main',base,[{path:'data.222222222222.js',content:null}],'fixture'),/not in prior tree/);
 await assert.rejects(readBase(async(m,u)=>u.includes('/ref/')?{object:{sha:A}}:u.includes('/commits/')?{tree:{sha:B}}:{truncated:true,tree:[]},'u/r','main'),/Complete prior tree/);
 process.env.COMTRADE_KEY='fixture';process.env.RENDER_DRY='1';delete process.env.GITHUB_TOKEN;delete process.env.GEMINI_API_KEY;
 let fetches=0;globalThis.fetch=async()=>{fetches++;return{ok:true,json:async()=>({data:Array.from({length:3001},(_,i)=>({cmdCode:String(i+100000),primaryValue:i+1}))})}};
 const {runRefresh}=await import('../../refresh.mjs');const dry=await runRefresh({root,build:()=>{throw Error('DRY must not build')}});assert.equal(dry.dry,true);assert.equal(fetches,2);assert.deepEqual(snapshot(root),before);
 console.log('refresh bundle: isolated build/SW/hash/orphan deletion/base fencing/commit failure/concurrent move/DRY byte snapshot PASS; all fetches mocked');
} finally {fs.rmSync(root,{recursive:true,force:true});}
// Real build in disposable snapshot, identical source input. No provider calls.
const actual=process.cwd();const prior=fs.readdirSync(actual).filter(p=>/^data\.[0-9a-f]{12}\.js$/.test(p));
const source='src/tradevalues.ts';const bytes=fs.readFileSync(source,'utf8');
const built=buildBundle(actual,[{path:source,content:bytes}],prior);
assert.ok(built.find(f=>f.path==='sw.js'));assert.equal(fs.readFileSync(source,'utf8'),bytes);
console.log('actual build isolated snapshot consistency PASS; source unchanged');
