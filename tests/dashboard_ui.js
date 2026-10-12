// Drive the Dashboard and a run's detail page under jsdom; fail on any error or
// missing section.
//
//   node dashboard_ui.js
//
// Covers: overview (running card with progress and time left, needs attention,
// system health with a GPU fault, processes, history), opening a run from the
// history table, every section of the run page, Back, the Progress tab's
// Details button, and an unknown run id.

const fs = require('fs'); const path = require('path'); const { JSDOM } = require('jsdom');
const code = fs.readFileSync(path.join(__dirname, '..', 'orchestration', 'static', 'app.js'), 'utf8');
const dom = new JSDOM('<!DOCTYPE html><div id="root"></div>',
  { runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://localhost:8000/#dashboard' });
const w = dom.window;
w.scrollTo = () => {};                    // jsdom does not implement it; the app scrolls to top on page change
global.window = w; global.document = w.document; global.navigator = w.navigator;
global.HTMLElement = w.HTMLElement; global.Element = w.Element;
global.requestAnimationFrame = w.requestAnimationFrame; global.cancelAnimationFrame = w.cancelAnimationFrame;

const F = '/in/IPN/260821';
const runRow = { path: F + '::network', folder: F, run: '260821', job: 'network', job_label: 'Network',
  status: 'running', run_id: 'r1', log: '/out/l.log', started_at: new Date(Date.now() - 600e3).toISOString() };
const detail = {
  id: 'r1', key: F + '::network', folder: F, project: 'IPN', date: '260821', job: 'network', status: 'running',
  started_at: new Date(Date.now() - 600e3).toISOString(), elapsed_s: 600, attempt: 2, imported: 0,
  live_detail: 'staged on local disk: /scratch/IPN/260821', last_output_age_s: 12,
  progress: { done: 9, total: 27, fraction: 0.333, seconds_left: 1200, expected_known: true },
  events: [{ time: new Date().toISOString(), status: 'dispatched', message: 'queued by hand' },
           { time: new Date().toISOString(), status: 'running', message: null },
           { time: new Date().toISOString(), status: null, message: 'running 1h 2m · last log output 0s ago' }],
  log: '/out/l.log', command: 'python nwb_job.py /in/IPN/260821 --output-dir /out',
  settings: { spike_sorting: false, nwb_convert: true, nwb_compression: 'gzip', stage_locally: true,
              scratch_dir: '/scratch', max_concurrent_network: 2, max_concurrent_activity: 2,
              watch_dir: '/in/IPN', output_dir: '/out' },
  log_summary: { route: 'nwb', counts: { complete: 8, not_recorded: 1 },
    conversion: [{ chip: 'M07036', run: '000023', well: 'well002', outcome: 'converted', seconds: 8 },
                 { chip: 'M07036', run: '000023', well: 'well003', outcome: 'not_recorded', reason: 'stream_id well003 is not in' }],
    conversion_summary: { seconds: 300, converted: 20, reused: 0, failed: 1 }, driver_seconds: null,
    wells: [{ chip: 'M07036', run: '000023', well: 'well002', outcome: 'complete', phase: 'Spike Detection',
              spikes: 1016958, seconds: 30, reason: null },
            { chip: 'M07036', run: '000023', well: 'well003', outcome: 'not_recorded', phase: 'Preprocessing',
              spikes: null, seconds: 3, reason: "stream_id well003 is not in ['well002']" }] },
  outputs: [{ label: 'Network results', path: '/out/IPN/260821', count: 8, unit: 'wells', bytes: 123456789 },
            { label: 'Log', path: '/out/l.log', count: 1, unit: 'file', bytes: 2048, log: true }],
};
const data = {
  '/api/status': { running: true, runs: [runRow], counts: { running: 1 }, events: [], candidates: [], scanning: false,
                   resumable: 0, watch_dir: '/in/IPN', output_dir: '/out', enabled_jobs: ['network'], limits: {} },
  '/api/config': { env: {}, watch_dir: '/in/IPN', driver_options: { output_dir: '/out' }, run_network: true,
                   run_activity: true, max_concurrent_network: 2, max_concurrent_activity: 2, settle_seconds: 600,
                   poll_seconds: 30, logs_in_output: true, h5_glob: 'data.raw.h5', driver_python: '' },
  '/api/schema': { groups: [] }, '/api/queue': { batches: [] }, '/api/handoff': { state: 'idle' },
  '/api/reports': { reports: [] }, '/api/logs': { lines: [] }, '/api/picker': {},
  '/api/runs/log': { lines: ['[2026-10-05 17:03:52,183] INFO: Processing : x well_id : well002', 'ERROR: boom'] },
  '/api/overview': { watching: true, active_jobs: { network: 1, activity: 0 }, limits: { network: 2, activity: 2 },
    running: [{ ...detail, conversion_summary: detail.log_summary.conversion_summary, counts: detail.log_summary.counts }],
    attention: [{ level: 'bad', kind: 'system', text: 'The graphics card driver needs a restart of the computer.' },
                { level: 'bad', kind: 'failed', run_id: 'r9', project: 'B6J', date: '261003', job: 'network', text: 'killed' }],
    recent: [], counts: { running: 1 } },
  '/api/system': { ready: true, cpu: { cores: 32, percent: 41, iowait_percent: 12, load: [9.1, 8, 7] },
    memory: { total: 64e9, available: 20e9, used: 44e9 }, gpu: { ok: false, error: 'Driver/library version mismatch' },
    disks: { 'Output disk': { path: '/out', total: 22e12, used: 4e12, free: 18e12 },
             'Recordings (NAS)': { path: '/in', error: 'did not answer within 5 s' } },
    processes: [{ pid: 1, kind: 'Network well (NWB)', user: 'me', mine: true, cpu_percent: 300, rss: 4e9, elapsed_s: 90, target: '260821/M07036/000023' },
                { pid: 2, kind: 'Network well', user: 'someone', mine: false, cpu_percent: 10, rss: 1e9, elapsed_s: 9, target: '' }],
    warnings: [] },
  '/api/history': { total: 2, projects: ['IPN', 'B6J'], runs: [
    { id: 'r1', project: 'IPN', date: '260821', job: 'network', status: 'running', duration_s: null },
    { id: 'r9', project: 'B6J', date: '261003', job: 'network', status: 'failed', duration_s: 55153, completed_at: new Date().toISOString() }] },
  '/api/history/r1': detail,
};
w.fetch = u => {
  const p = String(u).split('?')[0];
  if (p === '/api/history/missing')
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({ detail: 'No such run' }) });
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data[p] ?? {}),
                           text: () => Promise.resolve(JSON.stringify(data[p] ?? {})) });
};
w.React = require('react'); w.ReactDOM = require('react-dom/client');
const errors = [];
w.addEventListener('error', e => errors.push(e.error?.stack || e.message));
const orig = console.error;
console.error = (...a) => { const s = a.join(' '); if (!/not wrapped in act|^Warning:/.test(s)) errors.push(s.slice(0, 600)); };
const el = w.document.createElement('script'); el.textContent = code; w.document.body.appendChild(el);

const txt = () => (w.document.getElementById('root').textContent || '');
const wait = ms => new Promise(r => setTimeout(r, ms));
const failures = [];
const expect = (what, cond) => { console.log((cond ? '  ok   ' : '  FAIL ') + what); if (!cond) failures.push(what); };
const click = el => el && el.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
const button = label => [...w.document.querySelectorAll('button')].find(b => (b.textContent || '').includes(label));

(async () => {
  await wait(1500);
  console.log('Dashboard:');
  const t = txt();
  expect('needs attention lists the GPU fault', t.includes('graphics card driver needs a restart'));
  expect('needs attention lists the failed run', t.includes('killed'));
  expect('running card shows progress', t.includes('9 of 27 wells'));
  expect('running card shows time left', t.includes('20 min left'));
  expect('slots line', t.includes('Network analyses running 1 of 2'));
  expect('system: processors', t.includes('41%') && t.includes('32 cores'));
  expect('system: GPU not usable', t.includes('Not usable'));
  expect('system: NAS disk error shown', t.includes('did not answer within 5 s'));
  expect('system: my processes listed', t.includes('Network well (NWB)') && t.includes('260821/M07036/000023'));
  expect('system: other users summarised', t.includes('1 analysis program of someone'));
  expect('history lists runs', t.includes('Run history') && t.includes('3 Oct'));

  console.log('Open a run from history:');
  const row = [...w.document.querySelectorAll('table.tbl.hover tbody tr')][0];
  click(row);
  await wait(900);
  const d = txt();
  expect('address is #run/r1', w.location.hash === '#run/r1');
  expect('run page title', d.includes('21 Aug 2026'));
  expect('attempt shown', d.includes('run 2 for this date'));
  expect('live detail shown', d.includes('staged on local disk'));
  expect('progress section', d.includes('9 of 27 wells done') && d.includes('20 min left'));
  expect('steps timeline', d.includes('Steps') && d.includes('queued by hand') && d.includes('Converted to NWB'));
  expect('heartbeat is not a step', !d.includes('last log output'));
  expect('wells table', d.includes('1,016,958') && d.includes('not in the recording file'));
  expect('NWB conversion table', d.includes('NWB conversion') && d.includes('not in the file'));
  expect('outputs listed', d.includes('Network results') && d.includes('118 MB'));
  expect('settings it ran with', d.includes('Off (spike detection only)') && d.includes('standard compression'));
  expect('no tab is selected on a run page', ![...w.document.querySelectorAll('[role=tab]')].some(b => b.getAttribute('aria-selected') === 'true'));

  console.log('Log from the run page:');
  click(button(' Log'));
  await wait(600);
  expect('log drawer opens', !!w.document.querySelector('.drawer'));
  click(w.document.querySelector('.drawer [aria-label=Close]'));
  await wait(300);

  console.log('Back:');
  click(button('Back'));
  await wait(700);
  expect('back to the dashboard', w.location.hash === '#dashboard' && txt().includes('Needs attention'));

  console.log('Progress tab Details button:');
  click([...w.document.querySelectorAll('[role=tab]')].find(b => b.textContent.includes('Progress')));
  await wait(700);
  click(button('Details'));
  await wait(700);
  expect('Details opens the run page', w.location.hash === '#run/r1' && txt().includes('Settings it ran with'));

  console.log('Unknown run:');
  w.location.hash = 'run/missing';
  await wait(700);
  expect('unknown run shows a message', txt().includes('No such run'));

  console.error = orig;
  if (errors.length) { console.log('\nERRORS:'); errors.slice(0, 3).forEach(e => console.log('  ' + e.split('\n').slice(0, 6).join('\n  '))); }
  const ok = !errors.length && !failures.length;
  console.log(ok ? '\nPASS: dashboard and run page' : `\nFAIL: ${failures.length} check(s), ${errors.length} error(s)`);
  process.exit(ok ? 0 : 1);
})();
