// The lab cluster on the page: choosing where analyses run, each computer's
// paths, checking the cluster, saving, and a date that waits in the cluster
// queue or runs on one of its computers saying so.
//
//   node slurm_ui.js

const fs=require('fs'); const path=require('path'); const {JSDOM}=require('jsdom');
const code=fs.readFileSync(path.join(__dirname,'..','orchestration','static','app.js'),'utf8');
const P='/mnt/benshalom-nas/raw/Lab/IPN/IPN';

function page(hash,{cfg={},runs=[],idle=true,checkOk=true}={}){
  const dom=new JSDOM('<!DOCTYPE html><div id="root"></div>',{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost:8000/#'+hash});
  const w=dom.window;
  global.window=w; global.document=w.document; global.navigator=w.navigator;
  global.HTMLElement=w.HTMLElement; global.Element=w.Element;
  global.requestAnimationFrame=w.requestAnimationFrame; global.cancelAnimationFrame=w.cancelAnimationFrame;
  const posts=[];
  const base={env:{},watch_dirs:[],driver_options:{output_dir:'/out',skip_spikesorting:true,clean_up:true},run_network:true,
    run_activity:false,max_concurrent_network:1,max_concurrent_activity:2,settle_seconds:600,poll_seconds:30,stage_locally:true,
    scratch_dir:'/ssd',stage_min_free_gb:200,executor:'local',slurm_nodes:[],slurm_nas_here:'',slurm_cpus:8,slurm_mem_gb:32,
    slurm_hours:24,slurm_max_jobs:3,slurm_gpu_node:'',slurm_client:'/usr/local/bin/mea-slurm',cluster_ready:true};
  const data={
   '/api/status':{running:true,runs:idle?[]:runs,counts:{},events:[],candidates:[],scanning:false,resumable:0,projects:[],
     output_dir:'/out',enabled_jobs:['network'],limits:{network:3},active_jobs:{network:idle?0:runs.length},executor:'slurm'},
   '/api/config':Object.fromEntries(Object.entries({...base,...cfg}).filter(([,v])=>v!==undefined)),
   '/api/schema':{groups:[]},'/api/queue':{batches:[]},'/api/handoff':{state:'idle'},
   '/api/overview':{running:[],attention:[],recent:[],counts:{},limits:{network:3},active_jobs:{network:1},watching:true,projects:[],executor:'slurm'},
   '/api/system':{ready:false},'/api/history':{total:0,runs:[],projects:[]},'/api/reports':{reports:[]},'/api/logs':{lines:[]},
   '/api/audit':{entries:[]},'/api/me':{user:{id:1,name:'Test Person',email:'test@lab.org'}},
   '/api/cluster/check':checkOk
     ?{ok:true,server:[{what:'Cluster client',ok:true,say:'installed'}],nodes:[
        {node:'benshalom-labtower1',ok:true,state:'COMPLETED',steps:[{what:'identity',ok:true,say:'lab-jobs on benshalom-labtower1'},{what:'recording',ok:true,say:'decoded 260821'}]},
        {node:'benshalom-labtower2',ok:true,state:'COMPLETED',steps:[{what:'hdf5-plugin',ok:true,say:''}]}]}
     :{ok:false,server:[{what:'Shared results folder',ok:false,say:'This server cannot write to /mnt/mea-cluster/results. It must run in the lab-jobs group'}],nodes:[]},
  };
  w.fetch=(u,opt)=>{const p=String(u).split('?')[0];
    if(opt&&opt.method==='POST') posts.push({p,body:JSON.parse(opt.body||'{}')});
    const body=(opt&&opt.method==='POST'&&!data[p])?{ok:true}:(data[p]??{});
    return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(body),text:()=>Promise.resolve(JSON.stringify(body))});};
  w.React=require('react'); w.ReactDOM=require('react-dom/client');
  const errors=[];
  w.addEventListener('error',e=>errors.push(e.error?.stack||e.message));
  const el=w.document.createElement('script'); el.textContent=code; w.document.body.appendChild(el);
  const txt=()=>(w.document.getElementById('root').textContent||'');
  const btn=re=>[...w.document.querySelectorAll('button')].find(b=>re.test((b.textContent||'').trim()));
  const click=el=>el.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
  const radio=v=>w.document.querySelector(`input[name="executor"][value="${v}"]`);
  return {w,posts,errors,txt,btn,click,radio};
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const fails=[];
const check=(ok,what)=>{console.log((ok?'  ok   ':'  FAIL ')+what); if(!ok) fails.push(what);};

(async()=>{
  const orig=console.error;
  console.error=(...a)=>{const s=a.join(' '); if(!/not wrapped in act|^Warning:/.test(s)) orig(s.slice(0,300));};

  const s=page('settings'); await wait(1500);
  check(s.txt().includes('Where analyses run'), 'settings has a Where analyses run section');
  check(s.radio('local').checked&&!s.txt().includes('The cluster’s computers'), 'it starts on this computer, cluster fields hidden');
  s.click(s.radio('slurm')); await wait(200);
  check(s.txt().includes('The cluster’s computers')&&s.txt().includes('No computers listed'), 'choosing the cluster shows its computers');
  s.click(s.btn(/Use the lab’s three computers/)); await wait(200);
  const rows=[...s.w.document.querySelectorAll('.cl-node')];
  check(rows.length===3&&rows[2].querySelector('input[aria-label="NAS on it"]').value==='/mnt/ben-shalom_nas', 'the lab’s computers fill in with their own paths');
  s.click(s.w.document.getElementById('cl-check')); await wait(500);
  const ck=s.posts.find(x=>x.p==='/api/cluster/check');
  check(ck&&ck.body.slurm_nodes.length===3, 'Check sends the computers as they are on the page');
  check(s.txt().includes('benshalom-labtower1 Ready')&&s.txt().includes('decoded 260821')&&s.txt().includes('Every computer is ready'), 'each computer’s check is shown');
  s.click(s.btn(/Save settings/)); await wait(500);
  const sv=s.posts.find(x=>x.p==='/api/config');
  check(sv&&sv.body.executor==='slurm'&&sv.body.slurm_nodes.length===3&&sv.body.slurm_max_jobs===3, 'saving sends where analyses run and the computers');

  const f=page('settings',{cfg:{executor:'slurm',slurm_nodes:[{node:'benshalom-labtower1',python:'/p',mea_repo:'/r',nas:'/n'}]},checkOk:false}); await wait(1500);
  f.click(f.w.document.getElementById('cl-check')); await wait(500);
  check(f.txt().includes('It must run in the lab-jobs group')&&!f.txt().includes('Every computer is ready'), 'a failed check says what to fix');

  const n=page('settings',{cfg:{cluster_ready:false}}); await wait(1500);
  check(n.radio('slurm').disabled&&n.txt().includes('is not installed on this computer'), 'without the cluster client the cluster cannot be chosen');

  // An older server that knows nothing of the cluster: nothing extra is saved.
  const o=page('settings'); await wait(200);
  const old=page('settings',{cfg:{executor:undefined}}); await wait(1500);
  old.click(old.btn(/Save settings/)); await wait(500);
  const os_=old.posts.find(x=>x.p==='/api/config');
  check(os_&&!('executor' in os_.body)&&!('slurm_nodes' in os_.body), 'a server without the cluster gets no cluster settings');
  const runs=[
    {path:P+'/260821::network',folder:P+'/260821',run:'260821',job:'network',status:'queued',detail:'waiting in the cluster queue (Resources)',slurm_job_id:'31'},
    {path:P+'/260825::network',folder:P+'/260825',run:'260825',job:'network',status:'running',worker:'benshalom-labtower2',
     detail:'running 3m 2s · last log output 4s ago',slurm_job_id:'30'},
  ];
  const p=page('progress',{runs,idle:false}); await wait(1500);
  check(p.txt().includes('Waiting for a free computer in the lab cluster (all busy)'), 'a date waiting in the cluster queue says so');
  check(p.txt().includes('on benshalom-labtower2'), 'a running date says which computer it is on');
  const d=page('dashboard'); await wait(1500);
  check(d.txt().includes('Network analyses on the lab cluster 1 of 3'), 'the dashboard says analyses run on the cluster');

  check(![s,f,n,o,old,p,d].some(x=>x.errors.length), 'no page errors');
  console.error=orig;
  console.log(fails.length?`\n${fails.length} FAILED`:'\nall passed');
  process.exit(fails.length?1:0);
})();
