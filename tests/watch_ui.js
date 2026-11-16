// Watched projects on the page: what is watched is shown plainly, the wrong
// folder is caught with the right one offered, someone else's project asks
// before it is paused, and a waiting date says where it is in line.
//
//   node watch_ui.js

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
  {path:IPN+'/260825::network',folder:IPN+'/260825',run:'260825',job:'network',status:'dispatched',line_position:1,
   detail:'queued — waiting for a free network slot',started_by:'Test Person'},
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
   '/api/schema':{groups:[]},'/api/queue':{batches:[]},'/api/handoff':{state:'idle'},
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

  // Settings: the list, plainly.
  const s=page('settings'); await wait(1500);
  const t=s.txt();
  check(t.includes('Watched projects'), 'settings has a Watched projects section');
  check(t.includes('B6J 09092026 PVS')&&t.includes('IPN Organoids 08142026 PVS')&&t.includes('Old 2025'), 'every project is listed by name');
  check(t.includes(B6J)&&t.includes(IPN), 'with its full folder');
  check(t.includes('added by Ana')&&t.includes('added by Test Person (you)'), 'and who added it');
  check(t.includes('13 dates found')&&t.includes('1 analysing')&&t.includes('1 in line'), 'and what is happening in it');
  check((t.match(/Paused/g)||[]).length>=1&&(t.match(/Watching/g)||[]).length>=2, 'paused and watching are told apart');
  check(!t.includes('Recordings come from'), 'the single folder field is gone');

  // The lab folder is caught, and its projects offered.
  const inp=s.w.document.getElementById('wp-in');
  const setter=Object.getOwnPropertyDescriptor(s.w.HTMLInputElement.prototype,'value').set;
  setter.call(inp,LAB); inp.dispatchEvent(new s.w.Event('input',{bubbles:true})); await wait(100);
  s.click(s.btn(/^Check$/)); await wait(500);
  check(s.txt().includes('not recording dates'), 'picking the lab folder says it is not a project');
  check(s.txt().includes('already watched'), 'a suggestion already watched says so');
  const watchOne=s.btn(/Watch this one/);
  check(!!watchOne, 'the other project is offered');
  if(watchOne){ s.click(watchOne); await wait(500); }
  const add=s.posts.find(x=>x.p==='/api/projects/add');
  check(add&&add.body.path===LAB+'/New_11012026/New_11012026', 'one click adds the right folder');

  // Someone else's project asks first, then pauses.
  const pauses=[...s.w.document.querySelectorAll('.wp')].map(r=>[r,r.textContent]);
  const anaRow=pauses.find(([,x])=>x.includes('B6J'))[0];
  s.click([...anaRow.querySelectorAll('button')].find(b=>/Pause/.test(b.textContent))); await wait(300);
  check(s.txt().includes('Ana added this project'), 'pausing Ana’s project says whose it is');
  s.click(s.btn(/Pause watching it/)); await wait(500);
  const pz=s.posts.find(x=>x.p==='/api/projects/pause');
  check(pz&&pz.body.path===B6J&&pz.body.paused===true, 'and pauses it when confirmed');

  const ipnRow=[...s.w.document.querySelectorAll('.wp')].find(r=>r.textContent.includes('IPN'));
  s.click([...ipnRow.querySelectorAll('button')].find(b=>/Remove/.test(b.textContent))); await wait(300);
  check(s.txt().includes('Nothing is deleted'), 'removing says nothing is deleted');
  s.click(s.btn(/^Cancel$/)); await wait(200);
  check(!s.posts.some(x=>x.p==='/api/projects/remove'), 'cancel removes nothing');

  // Header and dashboard say what is watched.
  check(s.txt().includes('analysing now'), 'header shows the running analysis');
  const d=page('dashboard'); await wait(1500);
  check(d.txt().includes('Watching 2 projects for new recordings'), 'dashboard counts the active projects');
  check(d.txt().includes('Watched projects')&&d.txt().includes('added by Ana'), 'dashboard lists them with their owners');

  // Progress: a waiting date says where it is in line.
  const p=page('progress'); await wait(1500);
  check(p.txt().includes('Next in line for a free slot'), 'a waiting date says it is next in line');

  // Add recordings starts in a watched project and can switch between them.
  const a=page('add'); await wait(1500);
  check(a.txt().includes(B6J), 'Add recordings starts in a watched project');
  const sel=a.w.document.querySelector('select[aria-label="Watched project"]');
  check(sel&&[...sel.options].map(o=>o.textContent).includes('IPN Organoids 08142026 PVS'), 'and offers the others');

  // Saving settings never sends the projects (they have their own calls).
  const sv=page('settings',true); await wait(1500);
  check(!sv.btn(/Save settings/).disabled, 'Save is open when nothing runs');
  sv.click(sv.btn(/Save settings/)); await wait(500);
  const cfgPost=sv.posts.find(x=>x.p==='/api/config');
  check(cfgPost&&!('watch_dir' in cfgPost.body)&&!('watch_dirs' in cfgPost.body), 'Save settings does not send folders');

  check(![s,d,p,a,sv].some(x=>x.errors.length), 'no page errors');
  console.error=orig;
  console.log(fails.length?`\n${fails.length} FAILED`:'\nall passed');
  process.exit(fails.length?1:0);
})();
