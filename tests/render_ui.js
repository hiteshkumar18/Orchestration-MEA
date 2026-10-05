// Render index.html the way a browser does, and fail if it comes out blank.
//
//   cd tests && npm install && npm run build
//   node render_ui.js [path/to/app.js] [--running]
//
// The UI is one compiled script (app.js, built from app.jsx), so a
// runtime error anywhere in it blanks the whole page with nothing in the
// server log. Parsing the JSX is not enough: the bug this was written for
// parsed perfectly and still broke every screen. A useEffect had been added
// below App's early returns, so the first render (before config loads)
// skipped it and later renders ran it — "rendered more hooks than during the
// previous render" — and React unmounted everything.
//
// Fetch is stubbed, so this checks that the page mounts and renders, not that
// it talks to the server correctly.

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

// The compiled bundle the browser actually loads (built from app.jsx).
const file = process.argv.find(a => a.endsWith('.js') && !a.endsWith('render_ui.js')) ||
  path.join(__dirname, '..', 'orchestration', 'static', 'app.js');
const code = fs.readFileSync(file, 'utf8');

const RUNNING = process.argv.includes('--running');

const dom = new JSDOM('<!DOCTYPE html><div id="root"></div>',
  { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost:8000/' });
const w = dom.window;

// react-dom reads these at require time.
global.window = w; global.document = w.document; global.navigator = w.navigator;
global.HTMLElement = w.HTMLElement; global.Element = w.Element;
global.requestAnimationFrame = w.requestAnimationFrame;
global.cancelAnimationFrame = w.cancelAnimationFrame;

const data = {
  '/api/status': { running: RUNNING, runs: [], counts: {}, events: [], candidates: [],
                   scanning: false, resumable: 3, watch_dir: '/in', output_dir: '/out',
                   enabled_jobs: ['network'], limits: {} },
  '/api/config': { env: {}, watch_dir: '/in', driver_options: { output_dir: '/out' },
                   run_network: true, run_activity: true, max_concurrent_network: 2,
                   max_concurrent_activity: 2, gpu_cooldown_seconds: 5, queue_poll_seconds: 2,
                   settle_seconds: 600, poll_seconds: 30, logs_in_output: true,
                   stage_locally: false, scratch_dir: '', stage_min_free_gb: 200,
                   activity_active_hz: 0.05, h5_glob: 'data.raw.h5', driver_python: '' },
  '/api/schema': { groups: [] }, '/api/env': {}, '/api/queue': { batches: [] },
  '/api/handoff': { state: 'idle' }, '/api/logs': { lines: [] }, '/api/picker': {},
};
w.fetch = (url) => {
  const body = data[String(url).split('?')[0]] ?? {};
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body),
                           text: () => Promise.resolve(JSON.stringify(body)) });
};
w.React = require('react');
w.ReactDOM = require('react-dom/client');

const errors = [];
w.addEventListener('error', e => errors.push('window error: ' + (e.error?.stack || e.message)));
const origErr = console.error;
console.error = (...a) => { const s = a.join(' ');
  if (!/not wrapped in act|^Warning:/.test(s)) errors.push(s.slice(0, 500)); };

const el = w.document.createElement('script');
el.textContent = code;
w.document.body.appendChild(el);

setTimeout(() => {
  console.error = origErr;
  const text = (w.document.getElementById('root').textContent || '').trim();
  console.log('rendered characters:', text.length);
  console.log('first 140:', JSON.stringify(text.slice(0, 140)));
  if (errors.length) { console.log('\nERRORS:'); errors.slice(0, 3).forEach(e => console.log('  ' + e)); }
  // The AI report panel only shows once config has loaded; its absence means
  // the main view never got past loading.
  if (!RUNNING && !text.includes('AI report')) errors.push('AI report panel missing');
  const ok = text.length > 50 && errors.length === 0;
  console.log(ok ? '\nPASS: UI renders' : '\nFAIL: UI did not render');
  process.exit(ok ? 0 : 1);
}, 2000);
