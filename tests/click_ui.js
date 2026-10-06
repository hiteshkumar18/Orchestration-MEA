// Open a run's Wells and Log panels and fail if either blanks the page.
//
//   node click_ui.js
//
// render_ui.js only covers the first paint. These two buttons were broken
// anyway: RunBlock rendered <Wells>, but no such component existed, so
// clicking Wells threw a ReferenceError and React unmounted the whole app.
// The initial render was perfect, which is exactly why it went unnoticed.

const fs=require('fs'); const path=require('path'); const {JSDOM}=require('jsdom');
const code=fs.readFileSync(path.join(__dirname,'..','orchestration','static','app.js'),'utf8');
const dom=new JSDOM('<!DOCTYPE html><div id="root"></div>',{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost:8000/'});
const w=dom.window;
global.window=w; global.document=w.document; global.navigator=w.navigator;
global.HTMLElement=w.HTMLElement; global.Element=w.Element;
global.requestAnimationFrame=w.requestAnimationFrame; global.cancelAnimationFrame=w.cancelAnimationFrame;

const run={path:'/in/260828::network',folder:'/in/260828',run:'260828',job:'network',
  job_label:'Network',status:'done',returncode:0,duration_s:56,
  detail:'1 of 19 well subprocess(es) failed — see the driver log',
  log:'/out/orchestration_logs/260828_network.log',completed_at:new Date().toISOString()};
const data={
 '/api/status':{running:false,runs:[run],counts:{done:1},events:[],candidates:[],scanning:false,
   resumable:0,watch_dir:'/in',output_dir:'/out',enabled_jobs:['network'],limits:{}},
 '/api/config':{env:{},watch_dir:'/in',driver_options:{output_dir:'/out'},run_network:true,
   run_activity:true,max_concurrent_network:2,max_concurrent_activity:2,gpu_cooldown_seconds:5,
   queue_poll_seconds:2,settle_seconds:600,poll_seconds:30,logs_in_output:true,stage_locally:false,
   scratch_dir:'',stage_min_free_gb:200,activity_active_hz:0.05,h5_glob:'data.raw.h5',driver_python:''},
 '/api/schema':{groups:[]},'/api/env':{},'/api/queue':{batches:[]},'/api/handoff':{state:'idle'},
 '/api/logs':{lines:[]},'/api/picker':{},
 '/api/runs/checkpoints':{summary:{wells:19,complete:18,failed:1},
   wells:[{well:'well001',run_id:'000061',chip_id:'M07036',stage:10,stage_name:'Reports complete',
           progress:1,status:'complete',failed_stage:null,error:null,
           last_updated:'2026-10-05 10:00:00',data_dir:'/in/260828',output_dir:'/out/w1'}]},
 '/api/runs/log':{lines:['line one','line two'],path:run.log},
};
w.fetch=u=>{const p=String(u).split('?')[0];
  return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(data[p]??{}),
                          text:()=>Promise.resolve(JSON.stringify(data[p]??{}))});};
w.React=require('react'); w.ReactDOM=require('react-dom/client');
const errors=[];
w.addEventListener('error',e=>errors.push(e.error?.stack||e.message));
const orig=console.error;
console.error=(...a)=>{const s=a.join(' '); if(!/not wrapped in act|^Warning:/.test(s)) errors.push(s.slice(0,600));};
const el=w.document.createElement('script'); el.textContent=code; w.document.body.appendChild(el);

const txt=()=>(w.document.getElementById('root').textContent||'').trim();
const click=label=>{
  const b=[...w.document.querySelectorAll('button')].find(x=>(x.textContent||'').includes(label));
  if(!b){console.log(`  [no "${label}" button found]`); return false;}
  b.dispatchEvent(new w.MouseEvent('click',{bubbles:true})); return true;
};
setTimeout(()=>{
  console.log('after load:', txt().length, 'chars');
  click('Wells');
  setTimeout(()=>{
    console.log('after Wells click:', txt().length, 'chars');
    click('Log');
    setTimeout(()=>{
      console.error=orig;
      console.log('after Log click:', txt().length, 'chars');
      if(errors.length){console.log('\nERRORS:'); errors.slice(0,3).forEach(e=>console.log('  '+e.split('\n').slice(0,6).join('\n  ')));}
      else console.log('\nno errors');
      process.exit(errors.length?1:0);
    },700);
  },700);
},1500);
