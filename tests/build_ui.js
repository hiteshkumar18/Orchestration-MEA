// Compile orchestration/static/app.jsx to app.js, so the browser never has to.
//
//   cd tests && npm install && npm run build
//
// The page used to load @babel/standalone (~3 MB) from a CDN and compile the
// whole UI on every load. Now it is compiled once, here, and the result is
// committed. Run this after every edit to app.jsx — `npm test` checks the two
// are in step and fails if app.js is stale.

const fs = require('fs');
const path = require('path');
const babel = require('@babel/standalone');

const dir = path.join(__dirname, '..', 'orchestration', 'static');
const src = fs.readFileSync(path.join(dir, 'app.jsx'), 'utf8');
const out = '// GENERATED from app.jsx by tests/build_ui.js — do not edit by hand.\n' +
  babel.transform(src, { presets: ['react'], comments: false, compact: false }).code + '\n';

if (process.argv.includes('--check')) {
  const cur = fs.existsSync(path.join(dir, 'app.js')) ? fs.readFileSync(path.join(dir, 'app.js'), 'utf8') : '';
  if (cur !== out) { console.error('FAIL: app.js is stale — run `npm run build` in tests/'); process.exit(1); }
  console.log('OK: app.js matches app.jsx');
} else {
  fs.writeFileSync(path.join(dir, 'app.js'), out);
  console.log(`wrote app.js (${out.length} bytes)`);
}
