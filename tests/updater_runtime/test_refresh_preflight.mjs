import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
process.env.COMTRADE_KEY='fixture';process.env.GITHUB_TOKEN='fixture';process.env.GITHUB_REPO='u/r';delete process.env.RENDER_DRY;
let calls=0;globalThis.fetch=()=>{calls++;throw Error('No network allowed')};
const {runRefresh}=await import('../../refresh.mjs');const root=fs.mkdtempSync(path.join(os.tmpdir(),'missing-checkout-'));
try {await assert.rejects(runRefresh({root}),/requires a Git checkout with HEAD/);assert.equal(calls,0);console.log('missing checkout preflight before provider/Git network PASS');}finally{fs.rmSync(root,{recursive:true,force:true});}
