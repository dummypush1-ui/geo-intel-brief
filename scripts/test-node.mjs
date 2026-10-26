#!/usr/bin/env node
// Run the same standalone Node regression scripts locally and in CI.
import { readdirSync } from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const testRoot = path.resolve('tests');

function findTests(directory) {
  return readdirSync(directory, { withFileTypes: true })
    .sort((a, b) => a.name.localeCompare(b.name))
    .flatMap((entry) => {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) return findTests(fullPath);
      return entry.isFile() && entry.name.endsWith('.mjs') ? [fullPath] : [];
    });
}

let tests;
try {
  tests = findTests(testRoot).sort();
} catch (error) {
  console.error('Could not discover Node tests under tests/:', error.message);
  process.exit(1);
}

if (tests.length === 0) {
  console.error('No standalone Node regression tests found under tests/.');
  process.exit(1);
}

const failures = [];
for (const testPath of tests) {
  const label = path.relative(process.cwd(), testPath);
  console.log('\n> ' + label);
  const result = spawnSync(process.execPath, [testPath], { stdio: 'inherit' });
  if (result.error || result.status !== 0) {
    failures.push({ label, reason: result.error?.message ?? (result.signal ? 'signal ' + result.signal : 'exit ' + result.status) });
  }
}

console.log('\nNode regression summary: ' + (tests.length - failures.length) + '/' + tests.length + ' passed.');
if (failures.length) {
  for (const failure of failures) console.error('- ' + failure.label + ': ' + failure.reason);
  process.exitCode = 1;
}
