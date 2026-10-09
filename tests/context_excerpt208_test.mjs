import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../integration/ui/context_excerpt208.js',import.meta.url),'utf8');
const {descriptionContext:select} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
for(const n of [0,2,3,199,200,201,2850]) {
  const text='x'.repeat(n),v=select(text);
  assert.equal(Array.from(v.excerpt).length,Math.min(n,200));assert.equal(v.length,n);
  assert.equal(v.shortened,n>200);assert.deepEqual(v.terms,n>=3?[v.excerpt]:[]);
}
const emoji=select('x'.repeat(199)+'😀'+'tail');assert.equal(Array.from(emoji.excerpt).length,200);assert.ok(emoji.excerpt.endsWith('😀'));assert.equal(emoji.excerpt.length,201);
const short=select('😀'.repeat(150));assert.equal(short.shortened,false);assert.equal(short.length,150);assert.equal(short.excerpt.length,300);
for(const text of ['a\r\n\t\u00a0b','<script>&lt; synthetic text','a\x7fb','a\x85b','a\ud800b'])assert.equal(select(text).excerpt,text);
console.log('context_excerpt208: all boundaries and preservation PASS');
