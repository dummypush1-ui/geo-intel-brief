// Local deterministic build/provenance only. No provider calls or source edits.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {buildBundle} from '../updater_runtime/refresh-bundle.mjs';
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
export function prepare(root) {
 const inputs=['build.mjs','vendor/pako-inflate.min.js',...fs.readdirSync(path.join(root,'src')).filter(n=>fs.statSync(path.join(root,'src',n)).isFile()).map(n=>'src/'+n)].sort();
 const sourceHashes=Object.fromEntries(inputs.map(p=>[p,hash(fs.readFileSync(path.join(root,p)))]));
 const seed={path:'src/tradevalues.ts',content:fs.readFileSync(path.join(root,'src/tradevalues.ts'),'utf8')};
 const build=()=>buildBundle(root,[seed],[]).filter(f=>f.path!==seed.path);
 const files=build(),again=build();
 if(JSON.stringify(files)!==JSON.stringify(again))throw Error('Build not deterministic');
 for(const p of inputs)if(hash(fs.readFileSync(path.join(root,p)))!==sourceHashes[p])throw Error('Build input changed');
 return {files,receipt:{scope:'local_source_build_not_live_refresh',inputs:sourceHashes,outputs:Object.fromEntries(files.map(f=>[f.path,hash(f.content)])),double_build_equal:true,source_bytes_unchanged:true}};
}
