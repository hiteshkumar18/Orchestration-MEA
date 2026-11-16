// The priority line on the page: adding dates as priority, and moving a
// waiting date into the priority line and back.
//
//   node priority_ui.js

const fs=require('fs'); const path=require('path'); const {JSDOM}=require('jsdom');
const code=fs.readFileSync(path.join(__dirname,'..','orchestration','static','app.js'),'utf8');

const LAB='/nas/BenShalomLab';
const B6J=LAB+'/B6J_09092026_PVS/B6J_09092026_PVS', IPN=LAB+'/IPN_Organoids_08142026_PVS/IPN_Organoids_08142026_PVS';
const OLD=LAB+'/Old_2025/Old_2025';
const PROJECTS=[
  {path:B6J,name:'B6J_09092026_PVS',added_by:'Ana',added_by_email:'ana@lab.org',added_at:'2026-11-01T10:00:00Z',paused:false,
   exists:true,dates_found:13,dates_tracked:3,counts:{done:2,running:1},last_checked:new Date().toISOString()},
  {path:IPN,name:'IPN_Organoids_08142026_PVS',added_by:'Test Person',added_by_email:'test@lab.org',added_at:'2026-11-02T10:00:00Z',
   paused:false,exists:true,dates_found:4,dates_tracked:1,counts:{dispatched:1},last_checked:new Date().toISOString()},
  {path:OLD,name:'Old_2025',added_by:'Ana',added_by_email:'ana@lab.org',added_at:'',paused:true,exists:true,
   dates_found:null,dates_tracked:0,counts:{}},
];
const RUNS=[
  {path:B6J+'/260929::network',folder:B6J+'/260929',run:'260929',job:'network',status:'running',started_by:'Ana'},
  {path:IPN+'/260825::network',folder:IPN+'/260825',run:'260825',job:'network',status:'dispatched',line_position:2,
   detail:'queued — waiting for a free network slot',started_by:'Test Person',priority:false},
  {path:IPN+'/260826::network',folder:IPN+'/260826',run:'260826',job:'network',status:'dispatched',line_position:1,
   detail:'queued — waiting for a free network slot',started_by:'Ana',priority:true},
];

function page(hash,idle){
  const dom=new JSDOM('<!DOCTYPE html><div id="root"></div>',{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost:8000/#'+hash});
  const w=dom.window;
  global.window=w; global.document=w.document; global.navigator=w.navigator;
  global.HTMLElement=w.HTMLElement; global.Element=w.Element;
  global.requestAnimationFrame=w.requestAnimationFrame; global.cancelAnimationFrame=w.cancelAnimationFrame;
  const posts=[];
  const data={
   '/api/status':{running:true,runs:idle?[]:RUNS,counts:{},events:[],candidates:[],scanning:false,resumable:0,projects:PROJECTS,
     output_dir:'/out',enabled_jobs:['network'],limits:{network:1},active_jobs:idle?{}:{network:1}},
   '/api/config':{env:{},watch_dirs:PROJECTS.map(({path,added_by,added_by_email,added_at,paused})=>({path,added_by,added_by_email,added_at,paused})),
     driver_options:{output_dir:'/out',skip_spikesorting:true},run_network:true,run_activity:false,max_concurrent_network:1,
     max_concurrent_activity:2,settle_seconds:600,poll_seconds:30,stage_locally:true,scratch_dir:'/ssd',stage_min_free_gb:200},
   '/api/schema':{groups:[]},'/api/queue':{batches:[],queued:[{path:B6J+'/260929',job:'network'}],skipped:[]},'/api/handoff':{state:'idle'},
   '/api/overview':{running:[],attention:[],recent:[],counts:{},limits:{network:1},active_jobs:{network:1},watching:true,projects:PROJECTS},
   '/api/system':{ready:false},'/api/history':{total:0,runs:[],projects:[]},'/api/reports':{reports:[]},'/api/logs':{lines:[]},
   '/api/audit':{entries:[]},'/api/me':{user:{id:1,name:'Test Person',email:'test@lab.org'}},
   '/api/browse':{path:B6J,parent:LAB,entries:[{name:'260929',path:B6J+'/260929',is_run:true,recordings:4,finished:true}]},
   '/api/queue/inspect':{folders:[]},
   '/api/projects/check':{ok:false,kind:'lab',path:LAB,dates:0,problems:[],
     say:'This folder holds 2 projects, not recording dates. Pick one project to watch.',suggestions:[B6J,LAB+'/New_11012026/New_11012026']},
  };
  w.fetch=(u,opt)=>{const p=String(u).split('?')[0];
    if(opt&&opt.method==='POST') posts.push({p,body:JSON.parse(opt.body||'{}')});
    const body=(opt&&opt.method==='POST'&&!data[p])?{ok:true}:(data[p]??{});
    return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(body),text:()=>Promise.resolve(JSON.stringify(body))});};
  w.React=require('react'); w.ReactDOM=require('react-dom/client');
  const errors=[];
  w.addEventListener('error',e=>errors.push(e.error?.stack||e.message));
  const el=w.document.createElement('script'); el.textContent=code; w.document.body.appendChild(el);
  const txt=()=>(w.document.getElementById('root').textContent||'')+(w.document.querySelector('.modal')?.textContent||'');
  const btn=re=>[...w.document.querySelectorAll('button')].find(b=>re.test((b.textContent||'').trim()));
  const click=el=>el.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
  return {w,posts,errors,txt,btn,click};
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const fails=[];
const check=(ok,what)=>{console.log((ok?'  ok   ':'  FAIL ')+what); if(!ok) fails.push(what);};

(async()=>{
  const orig=console.error;
  console.error=(...a)=>{const s=a.join(' '); if(!/not wrapped in act|^Warning:/.test(s)) orig(s.slice(0,300));};

  // Add recordings: tick a date, tick Priority, analyse.
  const a=page('add'); await wait(1500);
  a.click(a.w.document.querySelector('.tile input[type=checkbox]')); await wait(200);
  const pick=a.w.document.querySelector('.prio-pick input');
  check(!!pick&&!pick.checked, 'a Priority tick box, off by default');
  a.click(pick); await wait(100);
  a.click(a.btn(/Analyse 1 date/)); await wait(500);
  const q=a.posts.find(x=>x.p==='/api/queue');
  check(q&&q.body.priority===true&&q.body.folders.length===1, 'adding sends it as priority');
  const toasts=a.w.document.body.textContent;
  check(toasts.includes('added as priority')&&toasts.includes('ahead of every regular date'), 'and says so');

  const b=page('add'); await wait(1500);
  b.click(b.w.document.querySelector('.tile input[type=checkbox]')); await wait(200);
  b.click(b.btn(/Analyse 1 date/)); await wait(500);
  check(b.posts.find(x=>x.p==='/api/queue')?.body.priority===false, 'without the tick it is regular');

  // Progress: the priority date is marked; each waiting date can be moved.
  const p=page('progress'); await wait(1500);
  const rows=[...p.w.document.querySelectorAll('.line')];
  const row=n=>rows.find(r=>r.textContent.includes(n));
  check(row('260826')?.querySelector('.stamp.prio')&&!row('260825')?.querySelector('.stamp.prio'), 'only the priority date is marked priority');
  check(!row('260929')?.textContent.includes('Make priority'), 'a running date has no priority button');
  p.click([...row('260825').querySelectorAll('button')].find(x=>/Make priority/.test(x.textContent))); await wait(500);
  const mp=p.posts.find(x=>x.p==='/api/runs/priority');
  check(mp&&mp.body.priority===true&&mp.body.paths[0]===IPN+'/260825::network', 'Make priority moves that date up');
  p.click([...row('260826').querySelectorAll('button')].find(x=>/Make regular/.test(x.textContent))); await wait(500);
  const mr=p.posts.filter(x=>x.p==='/api/runs/priority')[1];
  check(mr&&mr.body.priority===false&&mr.body.paths[0]===IPN+'/260826::network', 'Make regular moves it back');

  check(![a,b,p].some(x=>x.errors.length), 'no page errors');
  console.error=orig;
  console.log(fails.length?`\n${fails.length} FAILED`:'\nall passed');
  process.exit(fails.length?1:0);
})();
