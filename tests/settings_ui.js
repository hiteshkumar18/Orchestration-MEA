// The fast-disk switch brings its clean-up switch with it.
//
//   node settings_ui.js
//
// With "Use the fast local disk" on and clean-up off, every well's working
// files stayed on the SSD until the date finished; on 2026-10-20 that filled
// 3.6 TB. The clean-up option was buried in the advanced driver options under
// a technical name, so the page now puts it right below the fast-disk switch,
// says what happens when it is off, and saves it.

const fs=require('fs'); const path=require('path'); const {JSDOM}=require('jsdom');
const code=fs.readFileSync(path.join(__dirname,'..','orchestration','static','app.js'),'utf8');
const LABEL="Delete each well's working files as soon as it finishes";

function page(stageLocally){
  const dom=new JSDOM('<!DOCTYPE html><div id="root"></div>',{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost:8000/#settings'});
  const w=dom.window;
  global.window=w; global.document=w.document; global.navigator=w.navigator;
  global.HTMLElement=w.HTMLElement; global.Element=w.Element;
  global.requestAnimationFrame=w.requestAnimationFrame; global.cancelAnimationFrame=w.cancelAnimationFrame;
  const saved=[];
  const data={
   '/api/status':{running:false,runs:[],counts:{},events:[],candidates:[],scanning:false,
     resumable:0,watch_dir:'/in',output_dir:'/out',enabled_jobs:['network'],limits:{}},
   '/api/config':{env:{},watch_dir:'/in',driver_options:{output_dir:'/out',clean_up:false,skip_spikesorting:true},
     run_network:true,run_activity:false,max_concurrent_network:2,max_concurrent_activity:2,gpu_cooldown_seconds:5,
     queue_poll_seconds:2,settle_seconds:600,poll_seconds:30,logs_in_output:true,stage_locally:stageLocally,
     scratch_dir:'/ssd',stage_min_free_gb:200,activity_active_hz:0.05,h5_glob:'data.raw.h5',driver_python:''},
   '/api/schema':{groups:[]},'/api/env':{},'/api/queue':{batches:[]},'/api/handoff':{state:'idle'},
   '/api/overview':{running:[],attention:[],recent:[],counts:{},limits:{},active_jobs:{}},'/api/system':{ready:false},
   '/api/history':{total:0,runs:[],projects:[]},'/api/reports':{reports:[]},'/api/logs':{lines:[]},'/api/picker':{},
   '/api/me':{user:{id:1,name:'Test Person',email:'test@lab.org'}},
  };
  w.fetch=(u,opt)=>{const p=String(u).split('?')[0];
    if(opt&&opt.method==='POST'&&p==='/api/config') saved.push(JSON.parse(opt.body));
    const body=(opt&&opt.method==='POST')?{ok:true}:(data[p]??{});
    return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(body),text:()=>Promise.resolve(JSON.stringify(body))});};
  w.React=require('react'); w.ReactDOM=require('react-dom/client');
  const errors=[];
  w.addEventListener('error',e=>errors.push(e.error?.stack||e.message));
  const el=w.document.createElement('script'); el.textContent=code; w.document.body.appendChild(el);
  return {w,saved,errors,txt:()=>(w.document.getElementById('root').textContent||'')};
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const fails=[];
const check=(ok,what)=>{console.log((ok?'  ok   ':'  FAIL ')+what); if(!ok) fails.push(what);};

(async()=>{
  const orig=console.error;
  console.error=(...a)=>{const s=a.join(' '); if(!/not wrapped in act|^Warning:/.test(s)) orig(s.slice(0,300));};

  const off=page(false); await wait(1500);
  check(off.txt().includes('Use the fast local disk'), 'settings page renders');
  check(!off.txt().includes(LABEL), 'no clean-up switch while the fast disk is off');

  const on=page(true); await wait(1500);
  check(on.txt().includes(LABEL), 'clean-up switch shown with the fast disk on');
  check(on.txt().includes('the fast disk can fill up'), 'says what happens when it is off');
  const sw=on.w.document.getElementById('cln');
  check(sw&&sw.getAttribute('aria-checked')==='false', 'switch shows the saved value (off)');
  sw.dispatchEvent(new on.w.MouseEvent('click',{bubbles:true})); await wait(300);
  check(on.w.document.getElementById('cln').getAttribute('aria-checked')==='true', 'click turns it on');
  check(on.txt().includes('On (recommended)'), 'hint changes to the on text');
  const save=[...on.w.document.querySelectorAll('button')].find(b=>/^Save/.test((b.textContent||'').trim()));
  check(!!save, 'a Save button exists');
  if(save){ save.dispatchEvent(new on.w.MouseEvent('click',{bubbles:true})); await wait(800); }
  check(on.saved.length===1 && on.saved[0].driver_options.clean_up===true, 'Save sends clean_up: true');
  check(!off.errors.length && !on.errors.length, 'no page errors');

  console.error=orig;
  console.log(fails.length?`\n${fails.length} FAILED`:'\nall passed');
  process.exit(fails.length?1:0);
})();
