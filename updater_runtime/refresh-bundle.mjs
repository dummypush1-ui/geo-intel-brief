// Offline preparation and one non-force Git tree publication. No automatic retry.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const DATA = /^data\.[0-9a-f]{12}\.js$/;
const SOURCE = /^(src\/(tradevalues\.ts|app\.js|datachunk\d+\.ts))$/;
const GENERATED = new Set(['index.html', 'offline.html', 'sw.js']);
export function validateBundle(files) {
  if (!Array.isArray(files) || !files.length) throw new Error('Empty refresh bundle');
  const seen = new Set();
  for (const f of files) {
    if (!f || typeof f.path !== 'string' || seen.has(f.path) || !(SOURCE.test(f.path) || GENERATED.has(f.path) || DATA.test(f.path))) throw new Error('Invalid refresh path');
    seen.add(f.path);
    if (f.content === null) { if (!DATA.test(f.path)) throw new Error('Only orphan data can be deleted'); }
    else if (typeof f.content !== 'string') throw new Error('Invalid refresh content');
  }
  return files;
}
export function buildBundle(root, sourceFiles, oldData, build = (dir) => execFileSync(process.execPath, ['build.mjs'], {cwd:dir, stdio:'pipe'})) {
  if (!Array.isArray(oldData) || oldData.some(p => !DATA.test(p)) || new Set(oldData).size !== oldData.length) throw new Error('Invalid prior data paths');
  validateBundle(sourceFiles);
  if (sourceFiles.some(f => !SOURCE.test(f.path) || f.content === null)) throw new Error('Source changes only');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'finder-refresh-'));
  try {
    fs.cpSync(path.join(root, 'src'), path.join(dir, 'src'), {recursive:true});
    fs.cpSync(path.join(root, 'vendor'), path.join(dir, 'vendor'), {recursive:true});
    fs.copyFileSync(path.join(root, 'build.mjs'), path.join(dir, 'build.mjs'));
    for (const f of sourceFiles) fs.writeFileSync(path.join(dir, f.path), f.content);
    build(dir);
    const data = fs.readdirSync(dir).filter(f => DATA.test(f));
    if (data.length !== 1) throw new Error('Exactly one generated data file required');
    const name = data[0], version = name.slice(5,17);
    const generated = [...GENERATED, name].map(p => ({path:p, content:fs.readFileSync(path.join(dir,p),'utf8')}));
    const content = Object.fromEntries(generated.map(f => [f.path,f.content]));
    if (crypto.createHash("sha256").update(content[name]).digest("hex").slice(0,12) !== version) throw new Error("Data hash mismatch");
    if (!content['index.html'].includes(`data.src = './${name}'`) || !content['sw.js'].includes(`hsn-data-${version}`) || !content['sw.js'].includes(`./${name}`) || content['offline.html'].includes('data.src =')) throw new Error('Generated bundle identity mismatch');
    // Offline file must contain the exact generated data, not only a matching date.
    if (!content['offline.html'].includes(content[name])) throw new Error('Offline data mismatch');
    const files = [...sourceFiles, ...generated, ...oldData.filter(p => p !== name).map(p => ({path:p,content:null}))];
    validateBundle(files);
    return files;
  } finally { fs.rmSync(dir,{recursive:true,force:true}); }
}
export async function readBase(gh, repo, branch) {
  const ref = await gh('GET', `/repos/${repo}/git/ref/heads/${branch}`);
  const sha = ref?.object?.sha;
  if (!/^[a-f0-9]{40}$/.test(sha || '')) throw new Error('Invalid branch receipt');
  const commit = await gh('GET', `/repos/${repo}/git/commits/${sha}`);
  const treeSha = commit?.tree?.sha;
  if (!/^[a-f0-9]{40}$/.test(treeSha || '')) throw new Error('Invalid commit receipt');
  const tree = await gh('GET', `/repos/${repo}/git/trees/${treeSha}?recursive=1`);
  if (tree?.truncated !== false || !Array.isArray(tree.tree)) throw new Error('Complete prior tree required');
  const oldData = tree.tree.filter(r => r.type === 'blob' && DATA.test(r.path)).map(r => r.path);
  return {sha,treeSha,oldData};
}
export async function commitBundle(gh, repo, branch, base, files, message) {
  validateBundle(files);
  if (!base || !/^[a-f0-9]{40}$/.test(base.sha) || !/^[a-f0-9]{40}$/.test(base.treeSha) || !Array.isArray(base.oldData)) throw new Error('Verified base required');
  for (const f of files) if (f.content === null && !base.oldData.includes(f.path)) throw new Error('Deletion not in prior tree');
  const current = await gh('GET', `/repos/${repo}/git/ref/heads/${branch}`);
  if (current?.object?.sha !== base.sha) throw new Error('Branch moved; refresh held');
  const tree = [];
  for (const f of files) {
    let sha = null;
    if (f.content !== null) {
      const blob = await gh('POST', `/repos/${repo}/git/blobs`, {content:Buffer.from(f.content,'utf8').toString('base64'), encoding:'base64'});
      sha = blob?.sha;
      if (!/^[a-f0-9]{40}$/.test(sha || '')) throw new Error('Invalid blob receipt');
    }
    tree.push({path:f.path,mode:'100644',type:'blob',sha});
  }
  const next = await gh('POST', `/repos/${repo}/git/trees`, {base_tree:base.treeSha,tree});
  if (!/^[a-f0-9]{40}$/.test(next?.sha || '')) throw new Error('Invalid tree receipt');
  const commit = await gh('POST', `/repos/${repo}/git/commits`, {message,tree:next.sha,parents:[base.sha]});
  if (!/^[a-f0-9]{40}$/.test(commit?.sha || '')) throw new Error('Invalid new commit receipt');
  // A competing sibling commit cannot fast-forward to this parent-bound commit.
  let ref;
  try { ref = await gh('PATCH', `/repos/${repo}/git/refs/heads/${branch}`, {sha:commit.sha,force:false}); }
  catch { throw new Error('Ref publication uncertain; reconcile remote HEAD before any new refresh'); }
  if (ref?.object?.sha !== commit.sha) throw new Error('Ref publication uncertain; reconcile, do not retry');
  return commit.sha;
}
