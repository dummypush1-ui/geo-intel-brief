import assert from 'node:assert/strict';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {pathToFileURL} from 'node:url';
const root=process.cwd(),tmp=fs.mkdtempSync(path.join(os.tmpdir(),'comtrade178-'));process.chdir(tmp);process.env.RENDER_DRY='1';process.env.COMTRADE_KEY='fake';globalThis.fetch=()=>{throw new Error('no dry network');};
for(const [name,fn]of [['market','bakeMarket'],['marketx','bakeMarketX'],['partners','bakePartners'],['mirror','bakeMirror']]){const m=await import(pathToFileURL(path.join(root,'comtrade-'+name+'.mjs')));assert.deepEqual(await m[fn](),{dry:true,network:false,writes:false,published:false});}
assert.deepEqual(fs.readdirSync(tmp),[]);process.chdir(root);fs.rmSync(tmp,{recursive:true});console.log('4 dry bakes: zero network/files');
