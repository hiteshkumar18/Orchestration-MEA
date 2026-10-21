// Source for app.js. Edit this, then: cd tests && npm run build
//
// MEA Bench — the lab-notebook front end for Orchestration-MEA.
// Written for people who run experiments, not software: every label says what
// happens in plain words, and the technical knobs live behind "Advanced".
//
// RULE: every hook sits above App's early returns (see docs/FIELD-NOTES.md §8).
const {useState,useEffect,useCallback,useRef,useMemo} = React;

/* ── Icons ─────────────────────────────────────────────────────────────── */
const I=({d,s=16,f="none",w=1.8})=>(
  <svg width={s} height={s} viewBox="0 0 24 24" fill={f} stroke="currentColor" strokeWidth={w}
       strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>);
const Play =p=><I {...p} f="currentColor" d={<polygon points="7 4 20 12 7 20"/>}/>;
const Pause=p=><I {...p} d={<><line x1="9" y1="5" x2="9" y2="19"/><line x1="15" y1="5" x2="15" y2="19"/></>}/>;
const Stop =p=><I {...p} f="currentColor" d={<rect x="6" y="6" width="12" height="12" rx="2"/>}/>;
const Check=p=><I {...p} d={<polyline points="20 6 9 17 4 12"/>}/>;
const X    =p=><I {...p} d={<><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>}/>;
const Chev =p=><I {...p} d={<polyline points="9 18 15 12 9 6"/>}/>;
const Doc  =p=><I {...p} d={<><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><polyline points="14 3 14 8 19 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></>}/>;
const Grid =p=><I {...p} d={<><circle cx="6" cy="6" r="2"/><circle cx="12" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="18" cy="12" r="2"/></>}/>;
const Lines=p=><I {...p} d={<><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="14" y2="18"/></>}/>;
const Again=p=><I {...p} d={<><polyline points="1 4 1 10 7 10"/><path d="M3.5 15a9 9 0 1 0 2.1-9.4L1 10"/></>}/>;
const Folder=p=><I {...p} d={<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>}/>;
const Alert=p=><I {...p} d={<><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13.5"/><line x1="12" y1="17.2" x2="12.01" y2="17.2"/></>}/>;
const Info =p=><I {...p} d={<><circle cx="12" cy="12" r="9.5"/><line x1="12" y1="16.5" x2="12" y2="11.5"/><line x1="12" y1="7.8" x2="12.01" y2="7.8"/></>}/>;
const Ext  =p=><I {...p} d={<><path d="M14 4h6v6"/><line x1="20" y1="4" x2="11" y2="13"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/></>}/>;

/* ── API ───────────────────────────────────────────────────────────────── */
async function api(path,opts){
  if(location.protocol==="file:")
    throw new Error("Open this page through the server (http://localhost:8000), not as a file.");
  let r;
  try{ r=await fetch(path,{headers:{"Content-Type":"application/json"},...opts}); }
  catch(e){ throw new Error("The analysis server is not answering. It may be restarting — try again in a minute."); }
  const b=await r.json().catch(()=>({}));
  // Signed out (or the session ended): back to the sign-in form.
  if(r.status===401&&path!=="/api/login"){window.dispatchEvent(new Event("mea-signed-out"));
    throw new Error("Please sign in again.");}
  if(!r.ok){const d=b.detail;
    throw new Error(d?.errors?d.errors.join("\n"):(typeof d==="string"?d:`Request failed (${r.status})`));}
  return b;
}

/* ── Plain-language helpers ────────────────────────────────────────────── */
const MONTHS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
// MaxWell date folders are YYMMDD.
const prettyDate=code=>{const m=/^(\d{2})(\d{2})(\d{2})$/.exec(code||"");
  if(!m) return {big:code,year:""};
  const mo=+m[2]-1; return mo>=0&&mo<12?{big:`${+m[3]} ${MONTHS[mo]}`,year:`20${m[1]}`}:{big:code,year:""};};
const projectOf=folder=>{const p=(folder||"").replace(/\/+$/,"").split("/");return p[p.length-2]||"";};
const prettyProject=s=>(s||"").replace(/_/g," ");
const ago=iso=>{if(!iso)return"";const t=new Date(iso);if(isNaN(t))return"";
  const s=Math.max(0,(Date.now()-t)/1e3);
  return s<60?"just now":s<3600?`${s/60|0} min ago`:s<86400?`${s/3600|0} h ago`:`${s/86400|0} days ago`;};
const dur=s=>{if(s==null)return"";if(s<60)return`${Math.round(s)} s`;const m=s/60|0;
  return m<60?`${m} min`:`${m/60|0} h ${m%60} min`;};

// One status word per job, in the operator's language.
const JOB={
  running:   {say:"Analysing",          k:"run"},
  dispatched:{say:"In line",            k:"queue"},
  queued:    {say:"In line",            k:"queue"},
  waiting:   {say:"Waiting for copy",   k:"wait"},
  detected:  {say:"Found (test mode)",  k:"wait"},
  interrupted:{say:"Paused — will resume",k:"wait"},
  held:      {say:"On hold",            k:"wait"},
  done:      {say:"Done",               k:"ok"},
  failed:    {say:"Needs attention",    k:"bad"},
};
const jobInfo=st=>JOB[st]||{say:st||"Not started",k:"wait"};

// A date folder's overall state, from its Network and Activity-scan jobs.
function folderState(jobs){
  const sts=jobs.map(j=>j.status);
  if(sts.includes("running"))return"running";
  if(sts.some(s=>s==="dispatched"||s==="queued"))return"dispatched";
  if(sts.includes("failed"))return"failed";
  if(sts.length&&sts.every(s=>s==="done"))return"done";
  if(sts.includes("interrupted"))return"interrupted";
  if(sts.includes("held"))return"held";
  return sts[0]||"waiting";
}

// What the pipeline's notes mean, said simply.
function plainNote(job){
  const d=job.detail||"", e=job.error||"";
  let m=/(\d+) of (\d+) well subprocess\(es\) failed/.exec(d);
  if(m) return {t:`${m[2]-m[1]} of ${m[2]} wells finished · ${m[1]} had problems`,k:"warn"};
  if(job.status==="held")return{t:"Taken off the queue — press Resume to analyse it",k:""};
  if(job.status==="failed"){
    if(/cancelled/i.test(e))return{t:"Stopped by hand — press “Analyse again” to redo it.",k:"bad"};
    if(/GPU is not usable/i.test(e))return{t:"The graphics card was not available.",k:"bad"};
    if(/could not be copied from local scratch/i.test(e))return{t:"Results could not be copied back from the fast disk.",k:"bad"};
    return {t:(e.split("\n")[0]||"Something went wrong — open the log.").slice(0,160),k:"bad"};
  }
  if(/settling \((\d+)s remaining\)/.test(d)){const s=+/settling \((\d+)s/.exec(d)[1];
    return {t:`Copy looks finished — confirming for ${Math.ceil(s/60)} more min`,k:""};}
  if(/waiting for MaxWell 'finished' marker/i.test(d))return{t:"Waiting for the recording to be marked finished",k:""};
  if(/queued — waiting/i.test(d))return{t:"Waiting for a free slot",k:""};
  m=/^running (.+?) · last log output (.+)$/.exec(d);
  if(m)return{t:`Running for ${m[1].replace(/(\d+)h/,"$1 h ").replace(/(\d+)m/,"$1 min")} · last activity ${m[2].replace(/(\d+)m ago/,"$1 min ago").replace(/(\d+)s ago/,"$1 s ago")}`,k:""};
  if(/staged on local disk/i.test(d))return{t:"Working on the fast local disk",k:""};
  if(/copying results/i.test(d))return{t:"Copying results back…",k:""};
  return d?{t:d.slice(0,160),k:""}:null;
}

function plainWellError(r,note){
  const e=String(r.error||note?.fail||"");
  if(/stream_id well\d+ is not in/.test(e))return"Not in this recording file — nothing to analyse.";
  if(/n_samples=\d+ should be >= n_clusters/.test(e))return"Almost no activity in this well.";
  if(/out of memory/i.test(e))return"Ran out of memory.";
  if(r.status!=="complete"&&!e)return"Stopped without an error message.";
  return (e.split("\n").find(Boolean)||"Unknown problem").slice(0,180);
}

// What the driver log says about each well: failures and silent wells are
// only recorded there, not in the checkpoint files. Key: chip|recording|well.
function parseWellNotes(lines){
  const notes={};let cur=null;
  for(const l of lines){
    let m=/Processing : (\S+) recording : \S+ well_id : (well\d+)/.exec(l);
    if(m){const p=m[1].split("/");cur=`${p[p.length-4]}|${p[p.length-2]}|${m[2]}`;continue;}
    if(!cur)continue;
    m=/CRITICAL FAILURE in (well\d+): (.*)/.exec(l);
    if(m&&cur.endsWith("|"+m[1])){notes[cur]={...notes[cur],fail:m[2].trim()};continue;}
    if(/Detected 0 total spikes|returned error: no_spikes/.test(l))notes[cur]={...notes[cur],silent:true};
  }
  return notes;
}
// complete | silent | absent | failed | running
function wellClass(r,note,finished){
  if(r.status==="complete")return note?.silent?"silent":"complete";
  if(note?.fail&&/stream_id well\d+ is not in/.test(note.fail))return"absent";
  if(note?.silent)return"silent";
  if(r.status==="failed"||note?.fail||finished)return"failed";
  return"running";
}
function wellCounts(data,finished){
  const c={complete:0,silent:0,absent:0,failed:0,running:0};
  (data?.wells||[]).forEach(r=>{c[wellClass(r,data.notes?.[`${r.chip_id}|${r.run_id}|${r.well}`],finished)]++;});
  return c;
}

// Log lines worth reading: drop progress bars, keep the story.
function cleanLog(lines){
  return lines.filter(l=>l&&!/\d+%\|/.test(l)&&!/it\/s\]/.test(l)&&!/^\s*write_binary_recording\s*$/.test(l)
    &&!/^engine=process/.test(l)&&!/libcompression\.so/.test(l)&&!/UserWarning|warnings\.warn\(/.test(l));
}
const logKind=l=>/ERROR|CRITICAL|Traceback|Error:|FAILED/.test(l)?"err":/WARNING/.test(l)?"warn"
  :/Processing Complete|completed in|Checkpoint Saved: REPORTS_COMPLETE/.test(l)?"ok":"";

/* ── Small components ─────────────────────────────────────────────────── */
function Switch({checked,onChange,label,hint,id,disabled}){
  return (
    <div className="sw-row">
      <button type="button" role="switch" aria-checked={!!checked} id={id} disabled={disabled}
              className="sw" onClick={()=>!disabled&&onChange(!checked)}/>
      <label htmlFor={id} style={{cursor:disabled?"not-allowed":"pointer"}}>
        <div className="sw-l">{label}</div>
        {hint&&<div className="sw-h">{hint}</div>}
      </label>
    </div>);
}

function Code({text}){
  const [c,setC]=useState(false);
  return (
    <pre className="code">{text}
      <button className="cp" onClick={()=>navigator.clipboard?.writeText(text)
        .then(()=>{setC(true);setTimeout(()=>setC(false),1500);})}>{c?"Copied":"Copy"}</button>
    </pre>);
}

function Callout({kind="",icon,children}){
  return <div className={"callout "+kind}><span className="ic">{icon||<Info s={17}/>}</span><div>{children}</div></div>;
}

function Toasts({items,close}){
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map(t=>(
        <div key={t.id} className={"toast"+(t.k==="error"?" err":"")}>
          <span style={{flex:"none",marginTop:2}}>{t.k==="error"?<Alert s={16}/>:<Check s={16}/>}</span>
          <div style={{flex:1,minWidth:0}}>
            <div className="toast-t">{t.t}</div>{t.m&&<div className="toast-m">{t.m}</div>}
          </div>
          <button className="btn ghost sm" style={{color:"inherit"}} onClick={()=>close(t.id)} aria-label="Dismiss"><X s={13}/></button>
        </div>))}
    </div>);
}

function Confirm({ask,onClose}){
  if(!ask) return null;
  return (<>
    <div className="scrim m" onClick={()=>onClose(false)}/>
    <div className="modal" role="dialog" aria-modal="true" aria-labelledby="cf-t">
      <h3 id="cf-t">{ask.title}</h3>
      <div className="hint" style={{whiteSpace:"pre-wrap"}}>{ask.body}</div>
      <div className="acts">
        <button className="btn ghost" onClick={()=>onClose(false)}>Cancel</button>
        {ask.alt&&<button className="btn" onClick={()=>onClose("alt")}>{ask.alt}</button>}
        <button className={"btn "+(ask.danger?"red":"ink")} autoFocus onClick={()=>onClose(true)}>{ask.ok||"Continue"}</button>
      </div>
    </div></>);
}

function Browser({initial,onPick,onClose}){
  const [d,setD]=useState(null),[p,setP]=useState(initial||""),[e,setE]=useState("");
  const load=useCallback(async q=>{
    try{setE("");const r=await api("/api/browse",{method:"POST",body:JSON.stringify({path:q})});
        setD(r);setP(r.path);}catch(x){setE(x.message);}},[]);
  useEffect(()=>{load(initial||"");},[load,initial]);
  return (
    <div className="br">
      <div className="br-p">
        <input className="inp mono" value={p} onChange={ev=>setP(ev.target.value)}
               onKeyDown={ev=>ev.key==="Enter"&&load(p)} aria-label="Folder path"/>
        <button className="btn sm" onClick={()=>load(p)}>Go</button>
        <button className="btn ink sm" onClick={()=>{onPick(p);onClose();}}>Use this folder</button>
      </div>
      {e&&<div style={{padding:"10px 14px",color:"var(--red)",fontSize:13.5}}>{e}</div>}
      <div className="br-l">
        {d?.parent&&<div className="br-i" onClick={()=>load(d.parent)}><Folder s={15}/><span className="n">.. (up one level)</span></div>}
        {d?.entries?.length===0&&<div className="hint" style={{padding:14}}>No folders inside.</div>}
        {d?.entries?.map(x=>(
          <div key={x.path} className="br-i" onClick={()=>load(x.path)} onDoubleClick={()=>{onPick(x.path);onClose();}}>
            <Folder s={15}/><span className="n">{x.name}</span>
            {x.is_run&&<span className="hint-s">{x.recordings} recording{x.recordings===1?"":"s"}</span>}
          </div>))}
      </div>
    </div>);
}

/* ── Wells: a plate map per chip ──────────────────────────────────────── */
function Plates({data,finished}){
  if(!data) return <div className="hint" style={{paddingTop:10,display:"flex",gap:10,alignItems:"center"}}>
    <span className="spin"/> Reading well results… While analyses are running the results disk is busy,
    so this can take a minute or two. You can keep using the page.</div>;
  if(data.error) return <div className="hint" style={{paddingTop:10,color:"var(--red)"}}>{data.error}</div>;
  const rows=data.wells||[];
  if(!rows.length) return <div className="hint" style={{paddingTop:10}}>
    No wells have started yet. They appear here as the analysis reaches them.</div>;
  const note=r=>data.notes?.[`${r.chip_id}|${r.run_id}|${r.well}`];
  const chips={};
  rows.forEach(r=>{const k=`${r.chip_id||"?"}·${r.run_id||""}`;(chips[k]=chips[k]||{chip:r.chip_id,run:r.run_id,wells:{}}).wells[r.well]=r;});
  const c=wellCounts(data,finished);
  const probs=rows.filter(r=>wellClass(r,note(r),finished)==="failed");
  const tips={complete:"finished",silent:"finished, but no spikes were detected",
    absent:"not in this recording file — nothing to analyse",running:"in progress"};
  let i=0;
  return (<>
    <div className="legend">
      <span><b>{c.complete}</b>&nbsp;finished</span>
      {c.silent>0&&<span><b>{c.silent}</b>&nbsp;no activity</span>}
      {c.absent>0&&<span><b>{c.absent}</b>&nbsp;not in the recording file</span>}
      {c.running>0&&<span><b>{c.running}</b>&nbsp;in progress</span>}
      {c.failed>0&&<span style={{color:"var(--red)"}}><b>{c.failed}</b>&nbsp;problem{c.failed===1?"":"s"}</span>}
    </div>
    <div className="legend" style={{marginTop:6}}>
      <span><i className="well-k complete"/>finished</span><span><i className="well-k silent"/>no activity</span>
      {!finished&&<span><i className="well-k running"/>in progress</span>}
      <span><i className="well-k failed"/>problem</span><span><i className="well-k absent"/>not in the recording file</span>
      <span><i className="well-k none"/>not recorded</span>
    </div>
    <div className="plates">
      {Object.values(chips).map(ch=>{
        const ids=Object.keys(ch.wells).map(w=>+w.replace(/\D/g,""));
        const n=Math.max(6,Math.ceil((Math.max(...ids)+1)/6)*6);
        return (
          <div className="plate" key={ch.chip+ch.run}>
            <div className="plate-h">Chip <b>{ch.chip||"?"}</b><span className="hint-s">recording {ch.run}</span></div>
            <div className="wells">
              {Array.from({length:n},(_,k)=>{
                const r=ch.wells[`well${String(k).padStart(3,"0")}`];
                const cls=r?wellClass(r,note(r),finished):"none";
                const tip=!r?`Well ${k+1}: not recorded in this run`
                  :cls==="failed"?`Well ${k+1}: ${plainWellError(r,note(r))}`
                  :cls==="running"?`Well ${k+1}: ${r.stage_name||"in progress"}`:`Well ${k+1}: ${tips[cls]}`;
                return <div key={k} className={"well "+cls} style={{"--i":i++}} title={tip}>{k+1}</div>;
              })}
            </div>
          </div>);})}
    </div>
    {probs.length>0&&<div className="probs">
      {probs.map((r,j)=><div className="prob" key={j}><span className="w">{r.chip_id} · well {+r.well.replace(/\D/g,"")+1}</span>
        <span>{plainWellError(r,note(r))}</span></div>)}
    </div>}
  </>);
}

/* ── Log drawer ───────────────────────────────────────────────────────── */
function LogDrawer({log,onClose,live}){
  const [raw,setRaw]=useState(false);
  const ref=useRef(null);
  const lines=raw?log.lines:cleanLog(log.lines);
  useEffect(()=>{if(ref.current)ref.current.scrollTop=ref.current.scrollHeight;},[log.lines,raw]);
  useEffect(()=>{const k=e=>e.key==="Escape"&&onClose();addEventListener("keydown",k);return()=>removeEventListener("keydown",k);},[onClose]);
  return (<>
    <div className="scrim" onClick={onClose}/>
    <aside className="drawer" role="dialog" aria-label="Log">
      <div className="dr-h">
        <div style={{flex:1,minWidth:0}}>
          <div className="dr-t">{log.title}</div>
          <div className="hint">{live?<><span className="dot run" style={{display:"inline-block",marginRight:7}}/>Updating live</>:"Last 600 lines"}
            {" · "}{lines.length} shown</div>
        </div>
        <button className="btn sm" onClick={()=>setRaw(r=>!r)}>{raw?"Hide progress noise":"Show everything"}</button>
        <button className="btn ghost sm" onClick={onClose} aria-label="Close"><X s={15}/></button>
      </div>
      <div className="dr-b" ref={ref}>
        {log.error&&<div className="lg err">{log.error}</div>}
        {!log.lines.length&&!log.error&&<div className="lg">Loading…</div>}
        {lines.map((l,i)=><div key={i} className={"lg "+logKind(l)}>{l}</div>)}
      </div>
    </aside></>);
}

/* ── Progress tab ─────────────────────────────────────────────────────── */
// Not finished, and not already on hold: what "Hold" and "Reset queue" act on.
const HOLDABLE=["dispatched","queued","running","interrupted","waiting"];

function Line({f,report,wells,open,onWells,onLog,onAgain,onHold,onResume,i}){
  const st=folderState(f.jobs), ji=jobInfo(st);
  const dt=prettyDate(f.date);
  const net=f.jobs.find(j=>j.job==="network"), scan=f.jobs.find(j=>j.job==="activity");
  const note=net?plainNote(net):null;
  const busy=st==="running";
  const sum=wells?.summary;
  const netDone=net&&(net.status==="done"||net.status==="failed");
  const wc=netDone&&wells?.wells&&wells.notes?wellCounts(wells,true):null;
  const refined=wc&&{t:[`${wc.complete} wells finished`,wc.silent&&`${wc.silent} with no activity`,
    wc.absent&&`${wc.absent} not in the recording file`,wc.failed&&`${wc.failed} with problems`].filter(Boolean).join(" · "),
    k:wc.failed?"bad":""};
  return (<>
    <div className="line rise" style={{"--i":i}}>
      <div>
        <div className="d-big">{dt.big}</div>
        <div className="d-code">{dt.year} · {f.date}</div>
      </div>
      <div className="mid">
        <div className="say">
          <span className={"stamp "+ji.k}>{ji.say}</span>
          {busy&&sum?.wells>0&&<span className="note-l">{sum.complete} wells finished so far</span>}
          {(refined||note)&&<span className={"note-l "+(refined||note).k}>{(refined||note).t}</span>}
        </div>
        {startedBy(net||scan)&&<div className="hint-s who">{startedBy(net||scan)}
          {net&&scan&&scan.started_by&&scan.started_by!==net.started_by?` · activity scan ${startedBy(scan)}`:""}</div>}
        <div className="lanes">
          {[["Network",net],["Activity scan",scan]].filter(x=>x[1]).map(([n,j])=>{
            const x=jobInfo(j.status);
            return <span className="lane" key={n}><i className={"dot "+(x.k==="ok"?"ok":x.k==="bad"?"bad":x.k==="run"?"run":x.k==="queue"?"queue":"wait")}/>
              {n} <span className="lk">{x.say.toLowerCase()}{j.status==="done"&&j.duration_s?` · took ${dur(j.duration_s)}`:""}</span></span>;})}
        </div>
        {busy&&<div className="flow"><i/></div>}
      </div>
      <div className="acts">
        {report&&<a className="btn ink sm" href={`/api/reports/view?path=${encodeURIComponent(report.path)}`}
                    target="_blank" rel="noopener"><Doc s={14}/> Report</a>}
        {net&&<button className="btn sm" aria-expanded={open} onClick={()=>onWells(f)}><Grid s={14}/> Wells</button>}
        {(net?.log||scan?.log)&&<button className="btn sm" onClick={()=>onLog(f)}><Lines s={14}/> Log</button>}
        {(net?.run_id||scan?.run_id)&&<button className="btn sm" title="Steps, wells, outputs and settings of this run"
          onClick={()=>goRun(net?.run_id||scan?.run_id)}><Chev s={14}/> Details</button>}
        {f.jobs.some(j=>HOLDABLE.includes(j.status))&&<button className="btn sm"
          title={busy?"Stop this date and keep it for later":"Take this date off the queue and keep it for later"}
          onClick={()=>onHold(f)}><Pause s={14}/> Hold</button>}
        {f.jobs.some(j=>j.status==="held")&&<button className="btn sm" title="Put this date back in the queue"
          onClick={()=>onResume(f)}><Play s={11}/> Resume</button>}
        <button className="btn ghost sm" title="Analyse this date again" aria-label="Analyse again" onClick={()=>onAgain(f)}><Again s={14}/></button>
      </div>
    </div>
    {open&&<div className="plate-wrap"><Plates data={wells} finished={!!netDone}/></div>}
  </>);
}

function Progress({folders,reports,wells,openW,onWells,onLog,onAgain,onHold,onResume,feed,goAdd}){
  const byProj={};
  folders.forEach(f=>{(byProj[f.project]=byProj[f.project]||[]).push(f);});
  if(!folders.length) return (
    <div className="ledger rise"><div className="empty">
      <div className="empty-t">Nothing in the notebook yet</div>
      <div className="empty-d">Choose recording dates to analyse and they will appear here, one line per date.</div>
      <div style={{marginTop:18}}><button className="btn ink" onClick={goAdd}><Play s={12}/> Add recordings</button></div>
    </div></div>);
  let i=0;
  return (<>
    {Object.entries(byProj).map(([p,fs])=>(
      <div className="sec" key={p}>
        <div className="ledger">
          <div className="proj"><span className="proj-n">{prettyProject(p)}</span>
            <span className="proj-c">{fs.length} date{fs.length===1?"":"s"} · {fs.filter(f=>folderState(f.jobs)==="done").length} done</span></div>
          {fs.map(f=><Line key={f.folder} f={f} i={i++} report={reports[`${p}/${f.date}`]}
                           wells={wells[f.folder]} open={!!openW[f.folder]}
                           onWells={onWells} onLog={onLog} onAgain={onAgain}
                           onHold={onHold} onResume={onResume}/>)}
        </div>
      </div>))}
    {feed.some(l=>!/^=+$|Open this in your browser|do not open index\.html|^Work dir:/.test(l.message))&&<div className="sec">
      <div className="sec-h"><div className="sec-t">Today’s entries</div><div className="sec-d">What the system has been doing, newest first</div></div>
      <div className="card"><div className="card-b feed">
        {feed.filter(l=>!/^=+$|Open this in your browser|do not open index\.html|^Work dir:/.test(l.message))
             .slice(-14).reverse().map(l=>(
          <div className={"feed-i"+(l.level==="ERROR"?" err":"")} key={l.seq}>
            <span className="feed-t">{l.time.slice(0,5)}</span><span className="feed-m">{l.message}</span></div>))}
      </div></div>
    </div>}
  </>);
}

/* ── Add recordings tab ───────────────────────────────────────────────── */
function AddRecordings({cfg,toast,ask,onQueued}){
  const [dir,setDir]=useState(cfg.watch_dir||"");
  const [entries,setEntries]=useState(null);
  const [info,setInfo]=useState({});
  const [sel,setSel]=useState({});
  const [again,setAgain]=useState(false);
  const [busy,setBusy]=useState(false);
  const [browse,setBrowse]=useState(false);
  const [checking,setChecking]=useState(false);

  const load=useCallback(async path=>{
    setEntries(null);setSel({});
    try{
      const r=await api("/api/browse",{method:"POST",body:JSON.stringify({path})});
      setDir(r.path);
      const runs=(r.entries||[]).filter(x=>x.is_run);
      setEntries(runs);
      setInfo({});
      if(runs.length){
        setChecking(true);
        try{const ins=await api("/api/queue/inspect",{method:"POST",body:JSON.stringify({folders:runs.map(x=>x.path)})});
            const by={};(ins.folders||[]).forEach(f=>{by[f.path]=f;});setInfo(by);}
        finally{setChecking(false);}
      }
    }catch(e){setEntries([]);setChecking(false);toast("Could not read that folder",e.message,"error");}
  },[toast]);
  useEffect(()=>{if(cfg.watch_dir)load(cfg.watch_dir);},[cfg.watch_dir,load]);

  // "Analysed" only when every analysis for the date is finished and its
  // results are still there (whoever ran it).
  const done=p=>{const j=info[p]?.jobs||[];return j.length>0&&j.every(x=>x.analysed);};
  const partly=p=>!done(p)&&(info[p]?.jobs||[]).some(x=>x.analysed);
  const busyBy=p=>(info[p]?.jobs||[]).find(x=>x.in_flight);
  const gone=p=>(info[p]?.jobs||[]).some(x=>x.previous&&!x.previous.output_exists);
  const byWhom=p=>[...new Set((info[p]?.jobs||[]).filter(x=>x.analysed&&x.previous.by).map(x=>x.previous.by))].join(", ");
  const prevLines=p=>(info[p]?.jobs||[]).filter(x=>x.analysed).map(x=>{const v=x.previous;
    return `${x.label}: analysed${v.by?` by ${v.by}`:""}${v.finished?` on ${whenStarted(v.finished)}`:""}. Results: ${v.output}`;});
  const chosen=Object.keys(sel).filter(k=>sel[k]);
  const chosenDone=chosen.filter(done).length;
  const fresh=(entries||[]).filter(x=>!done(x.path)&&x.finished!==false);

  const go=async()=>{
    if(chosenDone&&again&&!(await ask({title:"Analyse again?",ok:"Analyse again",
      body:`${chosenDone} of these dates were already analysed. Their results will be computed again and replaced.\n\n`+
        chosen.filter(done).map(p=>`${prettyDate(p.split("/").pop()).big} ${prettyDate(p.split("/").pop()).year}\n`+
          prevLines(p).map(l=>"  • "+l).join("\n")).join("\n\n")})))return;
    setBusy(true);
    try{
      const r=await api("/api/queue",{method:"POST",body:JSON.stringify({folders:chosen,rerun:again})});
      const n=new Set(r.queued.map(q=>q.path)).size;
      const sk=(r.skipped||[]).filter(x=>x.job);
      toast(`${n} date${n===1?"":"s"} added`,"They will be analysed in order. Follow them under Progress."+
        (sk.length?`\n\nNot added:\n`+sk.map(x=>`${x.path.split("/").pop()}: ${x.reason}`).join("\n"):""));
      setSel({});onQueued();
    }catch(e){toast("Nothing was added",e.message,"error");}
    finally{setBusy(false);}
  };

  return (<div className="rise">
    <div className="sec-h"><div className="sec-t">Add recordings</div>
      <div className="sec-d">Tick the recording dates you want analysed, then press the button at the bottom.</div></div>
    <div className="card" style={{marginBottom:18}}><div className="card-b" style={{display:"flex",gap:12,alignItems:"center",flexWrap:"wrap"}}>
      <Folder s={18}/><div style={{flex:1,minWidth:0}}>
        <div className="hint-s">Looking in</div>
        <div className="mono" style={{wordBreak:"break-all"}}>{dir||"—"}</div></div>
      <button className="btn sm" onClick={()=>setBrowse(b=>!b)}>{browse?"Close":"Look somewhere else"}</button>
      <button className="btn sm" onClick={()=>load(dir)}>Refresh</button>
      {browse&&<div style={{flexBasis:"100%"}}><Browser initial={dir} onClose={()=>setBrowse(false)} onPick={p=>load(p)}/></div>}
    </div></div>

    {entries===null
      ? <div className="tiles">{[0,1,2,3,4,5].map(k=><div key={k} className="skel" style={{height:96}}/>)}</div>
      : entries.length===0
        ? <Callout kind="amber" icon={<Alert s={17}/>}>No recording dates were found in this folder. Choose the folder that
            <b> contains</b> the date folders (like <span className="mono">260818</span>).</Callout>
        : <>
            <div style={{display:"flex",gap:8,marginBottom:12,flexWrap:"wrap"}}>
              {checking&&<span className="hint" style={{display:"flex",gap:8,alignItems:"center"}}>
                <span className="spin"/> Checking which dates were already analysed…</span>}
              <button className="btn sm" disabled={checking||!fresh.length}
                      onClick={()=>setSel(Object.fromEntries(fresh.map(x=>[x.path,true])))}>Select all new ({fresh.length})</button>
              {chosen.length>0&&<button className="btn ghost sm" onClick={()=>setSel({})}>Clear selection</button>}
            </div>
            <div className="tiles">
              {entries.map((x,k)=>{
                const dt=prettyDate(x.name), on=!!sel[x.path], dn=done(x.path), fl=busyBy(x.path)?.in_flight;
                const jobs=(info[x.path]?.jobs||[]).map(j=>j.label).join(" + ");
                const who=dn?byWhom(x.path):"";
                return (
                  <label key={x.path} className="tile" data-on={on} data-done={dn} style={{"--i":k}}>
                    <input type="checkbox" checked={on} onChange={()=>setSel(v=>({...v,[x.path]:!v[x.path]}))}/>
                    {fl?<span className="t-tag copy">{fl.status==="running"?"analysing":"in queue"}</span>
                      :dn?<span className="t-tag done">analysed</span>:partly(x.path)?<span className="t-tag copy">partly done</span>
                      :x.finished===false?<span className="t-tag copy">copying</span>:null}
                    <div className="t-date">{dt.big}</div>
                    <div className="t-code">{dt.year} · {x.name}</div>
                    <div className="t-what">{jobs||info[x.path]?.note||" "}</div>
                    {fl&&fl.by&&<div className="t-who">started by {fl.by}</div>}
                    {!fl&&who&&<div className="t-who">by {who}</div>}
                    {!fl&&!dn&&gone(x.path)&&<div className="t-who">earlier results were deleted</div>}
                    <span className="t-tick">{on&&<Check s={13} w={3}/>}</span>
                  </label>);})}
            </div>
          </>}

    {chosen.length>0&&<div className="sticky">
      <div style={{flex:1,minWidth:200}}>
        <b>{chosen.length} date{chosen.length===1?"":"s"} selected</b>
        {chosenDone>0&&<div className="dup">
          <div className="dup-t"><Info s={14}/> {chosenDone===1?"This date was":`${chosenDone} of these dates were`} already analysed — the results exist:</div>
          {chosen.filter(done).map(p=><div key={p} className="dup-i">
            <b>{prettyDate(p.split("/").pop()).big} {prettyDate(p.split("/").pop()).year}</b>
            {prevLines(p).map((l,i)=><div key={i} className="mono-s">{l}</div>)}</div>)}
          <label style={{display:"flex",gap:8,alignItems:"center",marginTop:6,fontSize:13,cursor:"pointer"}}>
            <input type="checkbox" checked={again} onChange={e=>setAgain(e.target.checked)}/>
            Run {chosenDone===1?"it":"them"} again anyway (otherwise {chosenDone===1?"it is":"they are"} skipped)</label></div>}
      </div>
      <button className="btn lite" disabled={busy} onClick={go}>
        {busy?<span className="spin"/>:<Play s={12}/>} Analyse {chosen.length} date{chosen.length===1?"":"s"}</button>
    </div>}
  </div>);
}

/* ── AI report tab ────────────────────────────────────────────────────── */
function AiReport({cfg,reports,toast}){
  const [text,setText]=useState(cfg.ai_requirements||"");
  const [saved,setSaved]=useState(cfg.ai_requirements||"");
  const [auto,setAuto]=useState(cfg.auto_handoff!==false);
  const [busy,setBusy]=useState(false);
  const [last,setLast]=useState(null);
  const building=last?.state==="running";
  // Reports are made in the background (about a minute per date): follow along.
  useEffect(()=>{
    let t=null,stop=false;
    const poll=()=>api("/api/handoff").then(d=>{if(stop)return;
      if(d?.state&&d.state!=="idle")setLast(d);
      if(d?.state==="running")t=setTimeout(poll,2500);}).catch(()=>{});
    poll();return()=>{stop=true;clearTimeout(t);};
  },[busy]);
  const save=async(a=auto)=>{
    try{await api("/api/requirements",{method:"POST",body:JSON.stringify({text,auto_handoff:a})});
        setSaved(text);toast("Saved","Every new report will follow these instructions.");return true;}
    catch(e){toast("Not saved",e.message,"error");return false;}
  };
  const prepare=async()=>{
    setBusy(true);
    try{if(text!==saved&&!(await save()))return;
        await api("/api/handoff",{method:"POST",body:JSON.stringify({folders:[]})});}
    catch(e){toast("Could not make the report",e.message,"error");}
    finally{setBusy(false);}
  };
  const list=Object.values(reports);
  const byP={};list.forEach(r=>{(byP[r.project]=byP[r.project]||[]).push(r);});
  return (<div className="rise">
    <div className="sec">
      <div className="sec-h"><div className="sec-t">Finished reports</div>
        <div className="sec-d">One report per recording date. It opens in a new tab.</div></div>
      {list.length===0
        ? <div className="card"><div className="empty"><div className="empty-t">No reports yet</div>
            <div className="empty-d">{auto?"A report is made automatically when analysed dates finish. You can also make them below.":
              "Switch on automatic reports below, or press “Make reports” to make them now."}</div></div></div>
        : Object.entries(byP).map(([p,rs])=>(
          <div className="ledger" key={p} style={{marginBottom:16}}>
            <div className="proj"><span className="proj-n">{prettyProject(p)||"Reports"}</span><span className="proj-c">{rs.length} report{rs.length===1?"":"s"}</span></div>
            {rs.map((r,k)=>{const dt=prettyDate(r.label);return(
              <div className="line rise" key={r.path} style={{"--i":k}}>
                <div><div className="d-big">{dt.big}</div><div className="d-code">{dt.year} · {r.label}</div></div>
                <div className="hint">Written {ago(r.built)}</div>
                <div className="acts"><a className="btn ink sm" target="_blank" rel="noopener"
                  href={`/api/reports/view?path=${encodeURIComponent(r.path)}`}><Ext s={14}/> Open report</a></div>
              </div>);})}
          </div>))}
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">What reports should cover</div>
        <div className="sec-d">Write it the way you would brief a colleague. Applies to every new report.</div></div>
      <div className="card"><div className="card-b">
        <textarea className="inp" rows={8} value={text} onChange={e=>setText(e.target.value)}
          placeholder={"For example:\n• Compare burst rate between the two lines at each age\n• Leave out wells that failed quality control\n• One figure per measurement"}/>
        <div style={{display:"flex",gap:10,marginTop:12,flexWrap:"wrap",alignItems:"center"}}>
          <button className="btn ink" disabled={text===saved} onClick={()=>save()}>{text===saved?"Saved":"Save instructions"}</button>
          <span className="hint-s">Anything you leave out follows the lab’s standard report.</span>
        </div>
        <details className="adv">
          <summary><span className="chev"><Chev s={14}/></span>Making reports</summary>
          <Switch id="ai-auto" checked={auto} onChange={v=>{setAuto(v);save(v);}}
                  label="Make the report automatically when dates finish"
                  hint="Builds the lab's standard report for each finished date — Network analysis, Activity scan, or both, whichever was run — and lists it above."/>
          <div className="hint" style={{margin:"6px 0 12px"}}>Every report folder also holds a short note for Claude. To have Claude
            add what your instructions above ask for and explain the results, run the command shown when a report is ready.</div>
          <button className="btn" disabled={busy||building} onClick={prepare}>{busy||building?<span className="spin"/>:<Doc s={14}/>} Make reports for every finished date</button>
          {building&&<div className="hint" style={{marginTop:10}}>Making the report{last.projects?.length>1?"s":""}… about a minute per date. You can leave this page.</div>}
          {last?.state==="done"&&last.prompt&&<div style={{marginTop:12}}>
            <Callout kind="green" icon={<Check s={17}/>}>Report ready — {last.network_wells} wells, {last.activity_runs} scans
              {last.packages?.length>1?` in ${last.packages.length} projects`:""}. It is listed above.
              For Claude, in a terminal on the analysis computer, run:</Callout>
            <div style={{marginTop:8}}><Code text={last.instruction}/></div>
            {last.errors?.length>0&&<div style={{marginTop:8}}><Callout kind="amber" icon={<Alert s={17}/>}>{last.errors.join(" · ")}</Callout></div>}</div>}
          {last?.state==="error"&&<div style={{marginTop:12}}><Callout kind="red" icon={<Alert s={17}/>}>{last.error}</Callout></div>}
        </details>
      </div></div>
    </div>
  </div>);
}

/* ── Settings tab ─────────────────────────────────────────────────────── */
function Field({spec,value,onChange}){
  const set=v=>onChange(spec.key,v);
  if(spec.type==="flag")return <Switch id={"o-"+spec.key} checked={!!value} onChange={set} label={spec.flag} hint={spec.help}/>;
  const L=<span className="f-l mono" style={{fontWeight:500}}>{spec.flag}</span>;
  const H=<span className="hint-s">{spec.help}</span>;
  if(spec.type==="tristate")return <div className="f">{L}
    <select className="sel" value={value==null?"":String(value)} onChange={e=>set(e.target.value===""?null:e.target.value==="true")}>
      <option value="">Default</option><option value="true">On</option><option value="false">Off</option></select>{H}</div>;
  if(spec.type==="choice")return <div className="f">{L}
    <select className="sel" value={value??""} onChange={e=>set(e.target.value||null)}>
      <option value="">Default</option>{spec.choices.map(c=><option key={c} value={c}>{c}</option>)}</select>{H}</div>;
  if(spec.type==="list")return <div className="f">{L}
    <input className="inp mono" placeholder="comma separated" value={Array.isArray(value)?value.join(", "):(value??"")}
           onChange={e=>set(e.target.value.split(",").map(s=>s.trim()).filter(Boolean))}/>{H}</div>;
  const num=spec.type==="int"||spec.type==="float";
  return <div className="f">{L}
    <input className={"inp"+(spec.type==="path"?" mono":"")} type={num?"number":"text"} step={spec.type==="float"?"0.01":"1"}
           placeholder="Default" value={value??""}
           onChange={e=>set(e.target.value===""?null:(num?Number(e.target.value):e.target.value))}/>{H}</div>;
}

function Settings({cfg,setCfg,schema,locked,onSave,busy,toast}){
  const [br,setBr]=useState(null);
  const [q,setQ]=useState("");
  const [openG,setOpenG]=useState({});
  const [preview,setPreview]=useState(null);
  const [py,setPy]=useState(null);
  const setT=(k,v)=>setCfg(c=>({...c,[k]:v}));
  const setO=(k,v)=>setCfg(c=>({...c,driver_options:{...c.driver_options,[k]:v}}));
  const sorting=!cfg.driver_options.skip_spikesorting;
  const ql=q.trim().toLowerCase();
  const groups=schema.groups.map(g=>({...g,fields:g.fields.filter(f=>!ql||f.key.includes(ql)||f.flag.includes(ql)||(f.help||"").toLowerCase().includes(ql))})).filter(g=>g.fields.length);
  const doPreview=async()=>{try{setPreview(await api("/api/preview",{method:"POST",body:JSON.stringify(onSave.payload())}));}
    catch(e){toast("No preview",e.message,"error");}};
  const testPy=async()=>{try{setPy(await api("/api/driver-python",{method:"POST",body:JSON.stringify({python:cfg.driver_python||""})}));}
    catch(e){toast("Test failed",e.message,"error");}};

  return (<div className="rise">
    {locked&&<div style={{marginBottom:18}}><Callout kind="amber" icon={<Alert s={17}/>}>
      <b>Settings are locked while analyses are running.</b> Changing them now could disturb the running work.
      They unlock as soon as the current analyses finish.</Callout></div>}

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Where things are</div></div>
      <div className="card"><div className="card-b">
        <div className="f"><label className="f-l" htmlFor="in">Recordings come from</label>
          <div className="f-row"><input id="in" className="inp mono" value={cfg.watch_dir} disabled={locked} onChange={e=>setT("watch_dir",e.target.value)}/>
            <button className="btn" disabled={locked} onClick={()=>setBr(br==="in"?null:"in")}><Folder s={15}/> Choose</button></div>
          <span className="hint-s">The project folder that contains the date folders. It is only ever read, never changed.</span>
          {br==="in"&&<Browser initial={cfg.watch_dir} onClose={()=>setBr(null)} onPick={p=>setT("watch_dir",p)}/>}
        </div>
        <div className="f" style={{marginBottom:0}}><label className="f-l" htmlFor="out">Results go to</label>
          <div className="f-row"><input id="out" className="inp mono" value={cfg.driver_options.output_dir??""} disabled={locked}
                 onChange={e=>setO("output_dir",e.target.value||null)}/>
            <button className="btn" disabled={locked} onClick={()=>setBr(br==="out"?null:"out")}><Folder s={15}/> Choose</button></div>
          <span className="hint-s">Each project gets its own folder here, with its results, scans, logs and reports.</span>
          {br==="out"&&<Browser initial={cfg.driver_options.output_dir||""} onClose={()=>setBr(null)} onPick={p=>setO("output_dir",p)}/>}
        </div>
      </div></div>
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">What to analyse</div></div>
      <div className="card"><div className="card-b">
        <Switch id="net" checked={cfg.run_network} disabled={locked} onChange={v=>setT("run_network",v)}
                label="Network analysis" hint="Spikes and network bursts from each well's network recording."/>
        <Switch id="sort" checked={sorting} disabled={locked||!cfg.run_network} onChange={v=>setO("skip_spikesorting",!v)}
                label="Spike sorting (slow — about an hour per well)"
                hint={sorting?"On: separates individual neurons with the graphics card. Much slower.":
                  "Off (recommended): counts spikes on each electrode. A few minutes per well, no graphics card needed."}/>
        <Switch id="nwb" checked={!!cfg.nwb_convert} disabled={locked||!cfg.run_network} onChange={v=>setT("nwb_convert",v)}
                label="Convert to NWB first (for sharing on DANDI)"
                hint={cfg.nwb_convert?"On: each well is saved as an NWB file in the results folder, and the analysis reads it from there. Conversion adds a few seconds per well and about one more copy of the data on disk.":
                  "Off: the analysis reads the original recordings directly. Turn on to also keep a standard NWB copy of every well."}/>
        <Switch id="act" checked={cfg.run_activity} disabled={locked} onChange={v=>setT("run_activity",v)}
                label="Activity scan" hint="Whole-chip activity maps and quality checks. Takes seconds."/>
        <Switch id="stg" checked={!!cfg.stage_locally} disabled={locked} onChange={v=>setT("stage_locally",v)}
                label="Use the fast local disk while working"
                hint="Keeps big temporary files on the computer's fast disk and deletes them afterwards. Several times faster."/>
        {cfg.stage_locally&&<Switch id="cln" checked={!!cfg.driver_options.clean_up} disabled={locked} onChange={v=>setO("clean_up",v)}
                label="Delete each well's working files as soon as it finishes"
                hint={cfg.driver_options.clean_up?"On (recommended): only one well's working files, up to about 150 GB, are on the fast disk at a time.":
                  "Off: every well's working files stay until the whole date has finished. A big date can need several TB, the fast disk can fill up, and the remaining wells then fail."}/>}
      </div></div>
    </div>

    <details className="adv">
      <summary><span className="chev"><Chev s={14}/></span>Advanced settings — for whoever maintains the pipeline</summary>
      <div className="card" style={{marginTop:8}}><div className="card-b">
        <div className="row2">
          <div className="f"><label className="f-l">Confirm a copy has finished after (seconds)</label>
            <input className="inp tnum" type="number" min="1" value={cfg.settle_seconds} disabled={locked} onChange={e=>setT("settle_seconds",e.target.value)}/></div>
          <div className="f"><label className="f-l">Check for new recordings every (seconds)</label>
            <input className="inp tnum" type="number" min="1" value={cfg.poll_seconds} disabled={locked} onChange={e=>setT("poll_seconds",e.target.value)}/></div>
          <div className="f"><label className="f-l">Network analyses at once</label>
            <input className="inp tnum" type="number" min="1" max="8" value={cfg.max_concurrent_network??1} disabled={locked} onChange={e=>setT("max_concurrent_network",e.target.value)}/></div>
          <div className="f"><label className="f-l">Activity scans at once</label>
            <input className="inp tnum" type="number" min="1" max="16" value={cfg.max_concurrent_activity??2} disabled={locked} onChange={e=>setT("max_concurrent_activity",e.target.value)}/></div>
          <div className="f"><label className="f-l">Fast-disk folder</label>
            <input className="inp mono" value={cfg.scratch_dir||""} disabled={locked} onChange={e=>setT("scratch_dir",e.target.value)}/></div>
          <div className="f"><label className="f-l">NWB compression</label>
            <select className="sel" value={cfg.nwb_compression||"gzip"} disabled={locked} onChange={e=>setT("nwb_compression",e.target.value)}>
              <option value="gzip">Standard (gzip) — any reader and DANDI can open it</option>
              <option value="maxwell">MaxWell's own — smaller, needs MaxWell's plugin to read</option>
            </select></div>
          <div className="f"><label className="f-l">Always keep this much free on it (GB)</label>
            <input className="inp tnum" type="number" min="0" value={cfg.stage_min_free_gb??200} disabled={locked} onChange={e=>setT("stage_min_free_gb",e.target.value)}/></div>
        </div>
        <Switch id="mk" checked={cfg.require_finished_marker} disabled={locked} onChange={v=>setT("require_finished_marker",v)}
                label="Wait for MaxWell's 'finished' mark" hint="Also require the recording software to have marked the recording complete."/>
        <Switch id="ex" checked={cfg.skip_settle_for_existing} disabled={locked} onChange={v=>setT("skip_settle_for_existing",v)}
                label="Folders already here are ready" hint="Skip the copy check for folders present when watching starts."/>
        <Switch id="dry" checked={cfg.dry_run} disabled={locked} onChange={v=>setT("dry_run",v)}
                label="Test mode" hint="Find recordings and show what would run, without running anything."/>
        <Switch id="lio" checked={cfg.logs_in_output!==false} disabled={locked} onChange={v=>setT("logs_in_output",v)}
                label="Keep logs beside the results"/>
        <div className="f" style={{marginTop:12}}><label className="f-l">Pipeline Python</label>
          <div className="f-row"><input className="inp mono" placeholder="(detected automatically)" value={cfg.driver_python??""} disabled={locked}
                 onChange={e=>setT("driver_python",e.target.value)}/><button className="btn" onClick={testPy}>Test</button></div>
          {py&&<Callout kind={py.ok?"green":"red"} icon={py.ok?<Check s={17}/>:<Alert s={17}/>}>
            <span className="mono">{py.python}</span> — {py.ok?"has everything the pipeline needs.":`missing ${(py.missing||[]).join(", ")||py.error}.`}</Callout>}
        </div>

        <div className="sec-h" style={{marginTop:22}}><div className="sec-t" style={{fontSize:20}}>Pipeline options</div>
          <div className="sec-d">Passed to MEA-Analysis</div></div>
        <input className="inp" placeholder="Search options…" value={q} onChange={e=>setQ(e.target.value)} aria-label="Search options"/>
        {groups.map(g=>{const o=!!ql||!!openG[g.group];return(
          <div className="grp" key={g.group}>
            <button className="grp-h" aria-expanded={o} onClick={()=>setOpenG(x=>({...x,[g.group]:!x[g.group]}))}>
              <span style={{display:"inline-flex",transform:o?"rotate(90deg)":"none",transition:"transform .2s"}}><Chev s={13}/></span>
              {g.group}<span className="hint-s" style={{marginLeft:"auto"}}>{g.fields.length}</span></button>
            {o&&<div className="grp-b">{g.fields.map(f=><Field key={f.key} spec={f} value={cfg.driver_options[f.key]} onChange={locked?()=>{}:setO}/>)}</div>}
          </div>);})}
        <div style={{marginTop:16}}><button className="btn" onClick={doPreview}><Lines s={14}/> Show the exact command</button></div>
        {preview&&(preview.commands||[]).map(c=><div key={c.job} style={{marginTop:10}}>
          <div className="hint-s" style={{marginBottom:4}}>{c.job_label}{preview.example_run?` · for ${preview.example_run}`:""}</div><Code text={c.command}/></div>)}
      </div></div>
    </details>

    <div className="sticky" style={{background:"var(--sheet)",color:"var(--ink)",border:"1px solid var(--rule-2)"}}>
      <div style={{flex:1}} className="hint">Changes apply to analyses started after you save.</div>
      <button className="btn ink" disabled={locked||busy} onClick={()=>onSave()}>{busy?<span className="spin"/>:<Check s={14}/>} Save settings</button>
    </div>
  </div>);
}


/* ── Dashboard ────────────────────────────────────────────────────────── */
const fmtBytes=b=>{if(b==null)return"—";const u=["B","KB","MB","GB","TB"];let i=0,v=b;
  while(v>=1024&&i<u.length-1){v/=1024;i++;}return`${v<10&&i?v.toFixed(1):Math.round(v)} ${u[i]}`;};
const pct=(a,b)=>b?Math.round(100*a/b):0;
const WELL_OUT={complete:["finished","ok"],silent:["no activity","queue"],not_recorded:["not in the recording file","wait"],
  failed:["problem","bad"],stopped:["stopped","bad"],running:["in progress","run"]};
const RUN_SAY={done:["Done","ok"],failed:["Failed","bad"],interrupted:["Interrupted","wait"],held:["On hold","wait"],running:["Analysing","run"],
  dispatched:["Starting","queue"],queued:["In line","queue"],detected:["Found (test mode)","wait"]};
const runSay=st=>RUN_SAY[st]||[st||"—","wait"];
const jobName=j=>j==="activity"?"Activity scan":"Network analysis";
// The watcher's once-a-minute "still running" note; not a step.
const HEARTBEAT=/^running .+ · last log output .+ ago$/;
const goRun=id=>{if(id)location.hash="run/"+id;};
const whenStarted=iso=>{if(!iso)return"";const t=new Date(iso);if(isNaN(t))return"";
  return t.toLocaleString([], {day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"});};
// "started by Ana · 14 Oct, 09:12" for a run that names who started it.
const startedBy=r=>r&&r.started_by?`started by ${r.started_by}${r.dispatched_at||r.created?` · ${whenStarted(r.dispatched_at||r.created)}`:""}`:"";

function Meter({value,max,label,sub,danger}){
  const f=max?Math.min(100,100*value/max):0;
  return (<div className="meter-row">
    <div className="meter-top"><span>{label}</span><span className="hint-s">{sub}</span></div>
    <div className="meter"><i style={{width:`${f}%`}} data-k={danger?"bad":f>85?"warn":"ok"}/></div>
  </div>);
}

function SysHealth({sys}){
  if(!sys?.ready) return <div className="card"><div className="card-b hint" style={{display:"flex",gap:10,alignItems:"center"}}>
    <span className="spin"/> Measuring the computer…</div></div>;
  const c=sys.cpu||{}, m=sys.memory||{}, g=sys.gpu||{};
  const mine=(sys.processes||[]).filter(p=>p.mine), others=(sys.processes||[]).filter(p=>!p.mine);
  const byUser={};others.forEach(p=>{byUser[p.user]=(byUser[p.user]||0)+1;});
  return (<div className="card"><div className="card-b">
    <div className="health">
      <div className="hcell">
        <div className="h-k">Processors</div>
        <div className="h-v tnum">{c.percent==null?"…":`${Math.round(c.percent)}%`}</div>
        <div className="hint-s">{c.cores} cores · load {(c.load||[])[0]}{c.iowait_percent?` · waiting on disks ${Math.round(c.iowait_percent)}%`:""}</div>
      </div>
      <div className="hcell">
        <div className="h-k">Memory</div>
        <div className="h-v tnum">{m.total?`${pct(m.used,m.total)}%`:"—"}</div>
        <div className="hint-s">{fmtBytes(m.available)} free of {fmtBytes(m.total)}</div>
      </div>
      <div className="hcell">
        <div className="h-k">Graphics card</div>
        {g.ok?(g.gpus||[]).map((x,i)=>(<React.Fragment key={i}>
          <div className="h-v tnum">{Math.round(x.util)}%</div>
          <div className="hint-s">{x.name} · {Math.round(x.mem_used_mb/1024)} of {Math.round(x.mem_total_mb/1024)} GB · {Math.round(x.temp_c)}°C</div></React.Fragment>))
          :<><div className="h-v" style={{color:"var(--red)",fontSize:22}}>Not usable</div>
            <div className="hint-s" style={{color:"var(--red)"}}>{g.error}</div></>}
      </div>
    </div>
    <div className="disks">
      <Meter label="Memory in use" value={m.used||0} max={m.total} sub={`${fmtBytes(m.used)} / ${fmtBytes(m.total)}`}/>
      {Object.entries(sys.disks||{}).map(([k,d])=>d.error
        ?<div className="meter-row" key={k}><div className="meter-top"><span>{k}</span><span className="hint-s" style={{color:"var(--red)"}}>{d.error}</span></div></div>
        :<Meter key={k} label={k} value={d.used} max={d.total} sub={`${fmtBytes(d.free)} free of ${fmtBytes(d.total)}`}/>)}
    </div>
    <div className="sub-h">Analysis programs running now</div>
    {mine.length===0?<div className="hint">None of yours.</div>:
      <div className="tw"><table className="tbl"><thead><tr><th>What</th><th>Working on</th><th className="n">Processor</th>
        <th className="n">Memory</th><th className="n">Running for</th></tr></thead><tbody>
        {mine.map(p=><tr key={p.pid}><td>{p.kind}</td><td className="mono">{p.target||"—"}</td>
          <td className="n">{p.cpu_percent==null?"…":`${Math.round(p.cpu_percent)}%`}</td><td className="n">{fmtBytes(p.rss)}</td>
          <td className="n">{dur(p.elapsed_s)}</td></tr>)}
      </tbody></table></div>}
    {others.length>0&&<div className="hint-s" style={{marginTop:8}}>Also on this computer: {Object.entries(byUser).map(([u,n])=>`${n} analysis program${n===1?"":"s"} of ${u}`).join(", ")}.</div>}
  </div></div>);
}

function RunCard({r}){
  const p=r.progress||{}, [say,k]=runSay(r.status), dt=prettyDate(r.date);
  return (<button className="runcard rise" onClick={()=>goRun(r.id)}>
    <div className="rc-top"><span className="rc-date">{dt.big} {dt.year}</span><span className={"stamp "+k}>{say}</span></div>
    <div className="hint-s">{prettyProject(r.project)} · {jobName(r.job)}</div>
    {r.started_by&&<div className="hint-s">{startedBy(r)}</div>}
    {r.job==="network"&&<>
      <div className="bar"><i style={{width:`${p.fraction?Math.round(100*p.fraction):3}%`}}/></div>
      <div className="rc-meta">{p.total?<b>{p.done} of {p.total} wells</b>:<b>{p.done||0} wells finished</b>}
        {p.seconds_left!=null&&<span> · about {dur(p.seconds_left)} left</span>}</div>
    </>}
    <div className="hint-s">Running for {dur(r.elapsed_s)}{r.last_output_age_s!=null&&` · last activity ${dur(r.last_output_age_s)} ago`}</div>
    {r.conversion_summary&&<div className="hint-s">NWB: {r.conversion_summary.converted} converted, {r.conversion_summary.reused} reused</div>}
  </button>);
}

function HistoryTable({fixedLimit}){
  const [f,setF]=useState({project:"",job:"",status:""});
  const [data,setData]=useState(null);
  const [limit,setLimit]=useState(fixedLimit||25);
  const load=useCallback(()=>{
    const q=new URLSearchParams({...f,limit:String(limit)}).toString();
    api("/api/history?"+q).then(setData).catch(()=>setData({runs:[],total:0,projects:[]}));},[f,limit]);
  useEffect(()=>{load();const t=setInterval(()=>{if(!document.hidden)load();},15000);return()=>clearInterval(t);},[load]);
  if(!data) return <div className="skel" style={{height:120}}/>;
  return (<>
    {!fixedLimit&&<div className="filters">
      <select className="sel" value={f.project} onChange={e=>setF({...f,project:e.target.value})} aria-label="Project">
        <option value="">All projects</option>{(data.projects||[]).map(p=><option key={p} value={p}>{prettyProject(p)}</option>)}</select>
      <select className="sel" value={f.job} onChange={e=>setF({...f,job:e.target.value})} aria-label="Analysis">
        <option value="">Both analyses</option><option value="network">Network analysis</option><option value="activity">Activity scan</option></select>
      <select className="sel" value={f.status} onChange={e=>setF({...f,status:e.target.value})} aria-label="Outcome">
        <option value="">Any outcome</option><option value="done">Done</option><option value="failed">Failed</option>
        <option value="interrupted">Interrupted</option><option value="held">On hold</option><option value="running,dispatched,queued">Running or starting</option></select>
      <span className="hint-s">{data.total} run{data.total===1?"":"s"}</span>
    </div>}
    {data.runs.length===0?<div className="hint" style={{padding:"10px 2px"}}>No runs match.</div>:
    <div className="tw"><table className="tbl hover"><thead><tr><th>Recording date</th><th>Project</th><th>Analysis</th>
      <th>Outcome</th><th>Started by</th><th className="n">Took</th><th>Finished</th></tr></thead><tbody>
      {data.runs.map(r=>{const [say,k]=runSay(r.status),dt=prettyDate(r.date);return(
        <tr key={r.id} onClick={()=>goRun(r.id)} tabIndex={0} onKeyDown={e=>e.key==="Enter"&&goRun(r.id)}>
          <td><b>{dt.big}</b> <span className="hint-s">{dt.year}</span></td><td>{prettyProject(r.project)}</td>
          <td>{jobName(r.job)}</td><td><span className={"stamp "+k}>{say}</span></td>
          <td>{r.started_by||<span className="hint-s">—</span>}{r.started_by&&<div className="hint-s">{whenStarted(r.created)}</div>}</td>
          <td className="n">{r.duration_s!=null?dur(r.duration_s):"—"}</td><td className="hint-s">{r.completed_at?ago(r.completed_at):"—"}</td></tr>);})}
    </tbody></table></div>}
    {!fixedLimit&&data.total>data.runs.length&&<div style={{marginTop:10}}>
      <button className="btn sm" onClick={()=>setLimit(l=>l+50)}>Show more</button></div>}
  </>);
}

function Dashboard(){
  const [ov,setOv]=useState(null);
  const [sys,setSys]=useState(null);
  useEffect(()=>{
    const load=()=>{if(document.hidden)return;
      api("/api/overview").then(setOv).catch(()=>{});api("/api/system").then(setSys).catch(()=>{});};
    load();const t=setInterval(load,5000);return()=>clearInterval(t);},[]);
  if(!ov) return <div className="skel" style={{height:240}}/>;
  const lim=ov.limits||{}, act=ov.active_jobs||{};
  return (<div className="rise">
    <div className="slots">
      <span className={"dot "+(ov.watching?"ok":"wait")}/>{ov.watching?"Watching for new recordings":"Not watching for new recordings"}
      <span className="hint-s">· Network analyses running {act.network||0} of {lim.network||1} · Activity scans {act.activity||0} of {lim.activity||1}</span>
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Needs attention</div></div>
      {ov.attention.length===0
        ?<Callout kind="green" icon={<Check s={17}/>}>Nothing needs attention.</Callout>
        :<div className="att">{ov.attention.map((a,i)=>(
          <div key={i} className={"att-i "+(a.level||"warn")} onClick={()=>a.run_id&&goRun(a.run_id)} style={{cursor:a.run_id?"pointer":"default"}}>
            <span className="ic">{a.level==="bad"?<Alert s={17}/>:<Info s={17}/>}</span>
            <div style={{flex:1,minWidth:0}}>
              {a.date&&<b>{prettyDate(a.date).big} {prettyDate(a.date).year} · {jobName(a.job)} — </b>}{a.text}</div>
            {a.run_id&&<Chev s={15}/>}
          </div>))}</div>}
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Running now</div>
        <div className="sec-d">{ov.running.length?"Click a run for its wells, steps and log":"Nothing is analysing at the moment"}</div></div>
      {ov.running.length>0&&<div className="runcards">{ov.running.map(r=><RunCard key={r.id} r={r}/>)}</div>}
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">The computer</div><div className="sec-d">Updates every few seconds</div></div>
      <SysHealth sys={sys}/>
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Run history</div><div className="sec-d">Every analysis run, newest first</div></div>
      <div className="card"><div className="card-b"><HistoryTable/></div></div>
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Who did what</div><div className="sec-d">Sign-ins, queueing, holds, stops and settings changes</div></div>
      <div className="card"><div className="card-b"><Audit/></div></div>
    </div>
  </div>);
}

function Audit(){
  const [d,setD]=useState(null);
  const [n,setN]=useState(15);
  useEffect(()=>{const load=()=>{if(!document.hidden)api(`/api/audit?limit=${n}`).then(setD).catch(()=>{});};
    load();const t=setInterval(load,15000);return()=>clearInterval(t);},[n]);
  if(!d) return <div className="skel" style={{height:80}}/>;
  if(!(d.entries||[]).length) return <div className="hint">Nothing yet.</div>;
  return (<>
    <div className="tw"><table className="tbl"><thead><tr><th>When</th><th>Who</th><th>What</th></tr></thead><tbody>
      {d.entries.map((e,i)=><tr key={i}><td className="hint-s" style={{whiteSpace:"nowrap"}}>{whenStarted(e.time)}</td>
        <td title={e.email||""}>{e.name||"—"}</td>
        <td style={{whiteSpace:"normal"}}>{e.action}{e.detail?<span className="hint-s"> — {e.detail}</span>:null}</td></tr>)}
    </tbody></table></div>
    {d.entries.length>=n&&<button className="btn sm" style={{marginTop:10}} onClick={()=>setN(x=>x+50)}>Show more</button>}
  </>);
}

/* ── Run detail ───────────────────────────────────────────────────────── */
function RunDetail({id,onLog,onBack}){
  const [d,setD]=useState(null);
  const [err,setErr]=useState("");
  const [showAll,setShowAll]=useState(false);
  useEffect(()=>{let t;setD(null);setErr("");
    const load=()=>api("/api/history/"+id).then(x=>{setD(x);
      if(!["done","failed","interrupted","detected","held"].includes(x.status)&&!t)t=setInterval(()=>{if(!document.hidden)load();},5000);
      else if(["done","failed","interrupted","detected","held"].includes(x.status)&&t){clearInterval(t);t=null;}})
      .catch(e=>setErr(e.message));
    load();return()=>t&&clearInterval(t);},[id]);
  if(err) return <div className="rise"><button className="btn sm" onClick={onBack}>← Back</button>
    <div style={{marginTop:16}}><Callout kind="red" icon={<Alert s={17}/>}>{err}</Callout></div></div>;
  if(!d) return <div className="skel" style={{height:300}}/>;
  const [say,k]=runSay(d.status), dt=prettyDate(d.date), ls=d.log_summary||{}, p=d.progress||{};
  const wells=ls.wells||[], conv=ls.conversion||[];
  const probs=wells.filter(w=>["failed","stopped"].includes(w.outcome));
  const shown=showAll?wells:wells.slice(0,60);
  const st=d.settings||{};
  const report=(d.outputs||[]).find(o=>o.report);
  return (<div className="rise">
    <button className="btn sm" onClick={onBack}>← Back</button>
    <div className="rd-h">
      <div><div className="rd-t">{dt.big} {dt.year}</div>
        <div className="hint">{prettyProject(d.project)} · {jobName(d.job)} · folder <span className="mono">{d.date}</span>
          {d.attempt>1&&` · run ${d.attempt} for this date`}{d.imported?" · imported from before history was kept":""}</div></div>
      <div className="acts" style={{alignItems:"center"}}>
        <span className={"stamp "+k} style={{fontSize:13}}>{say}</span>
        {report&&<a className="btn ink sm" target="_blank" rel="noopener" href={`/api/reports/view?path=${encodeURIComponent(report.path)}`}><Doc s={14}/> Report</a>}
        {d.log&&<button className="btn sm" onClick={()=>onLog(d.log,`${dt.big} ${dt.year} · ${jobName(d.job)}`)}><Lines s={14}/> Log</button>}
      </div>
    </div>

    <div className="tally" style={{marginBottom:22}}>
      <div className="tal"><div className="tal-k">Started by</div><div className="rd-v">{d.started_by||"—"}</div>
        {d.created&&<div className="hint-s">{whenStarted(d.created)}{d.started_by_email?` · ${d.started_by_email}`:""}</div>}</div>
      <div className="tal"><div className="tal-k">Started</div><div className="rd-v">{d.started_at?ago(d.started_at):"—"}</div></div>
      <div className="tal"><div className="tal-k">{["done","failed","interrupted","held"].includes(d.status)?"Took":"Running for"}</div><div className="rd-v">{d.elapsed_s!=null?dur(d.elapsed_s):"—"}</div></div>
      <div className="tal"><div className="tal-k">Finished</div><div className="rd-v">{d.completed_at?ago(d.completed_at):"not yet"}</div></div>
      <div className="tal"><div className="tal-k">Wells</div><div className="rd-v">{d.job==="network"?
        `${(ls.counts||{}).complete||0} finished${probs.length?` · ${probs.length} problem${probs.length===1?"":"s"}`:""}`:((ls.summary||{}).wells??"—")}</div></div>
    </div>

    {d.error&&<div style={{marginBottom:18}}><Callout kind="red" icon={<Alert s={17}/>}><b>What went wrong:</b> {d.error}</Callout></div>}
    {d.live_detail&&<div style={{marginBottom:18}}><Callout kind="blue">{d.live_detail}</Callout></div>}

    {d.job==="network"&&!["done","failed","interrupted","held"].includes(d.status)&&<div className="sec">
      <div className="sec-h"><div className="sec-t">Progress</div></div>
      <div className="card"><div className="card-b">
        <div className="bar" style={{height:10}}><i style={{width:`${p.fraction?Math.round(100*p.fraction):3}%`}}/></div>
        <div style={{marginTop:8}}>{p.total?<b>{p.done} of {p.total} wells done</b>:<b>{p.done||0} wells done</b>}
          {p.seconds_left!=null&&<span> · about {dur(p.seconds_left)} left</span>}
          {!p.expected_known&&<span className="hint-s"> · counting this date's wells…</span>}
          {d.last_output_age_s!=null&&<span className="hint-s"> · last activity {dur(d.last_output_age_s)} ago</span>}</div>
      </div></div></div>}

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Steps</div><div className="sec-d">What happened, in order</div></div>
      <div className="card"><div className="card-b"><ol className="tl">
        {(d.events||[]).length===0&&<li className="hint">No step record — this run happened before history was kept.</li>}
        {(d.events||[]).filter(e=>e.status||!HEARTBEAT.test(e.message||"")).map((e,i)=><li key={i} data-k={runSay(e.status)[1]}>
          <span className="tl-t">{e.time?new Date(e.time).toLocaleString():""}</span>
          <span>{e.status?<b>{runSay(e.status)[0]}</b>:null}{e.status&&e.message?" — ":""}{e.message}</span></li>)}
        {ls.conversion_summary&&<li data-k="ok"><span className="tl-t">NWB</span><span><b>Converted to NWB</b> — {ls.conversion_summary.converted} converted,
          {" "}{ls.conversion_summary.reused} reused, {ls.conversion_summary.failed} failed in {dur(ls.conversion_summary.seconds)}</span></li>}
        {ls.driver_seconds!=null&&<li data-k="ok"><span className="tl-t">Analysis</span><span><b>All wells analysed</b> in {dur(ls.driver_seconds)}</span></li>}
      </ol></div></div>
    </div>

    {d.job==="network"&&<div className="sec">
      <div className="sec-h"><div className="sec-t">Wells</div><div className="sec-d">{wells.length} well{wells.length===1?"":"s"} in the log</div></div>
      {wells.length===0?<div className="card"><div className="card-b hint">No wells started yet.</div></div>:
      <div className="card"><div className="card-b"><div className="tw"><table className="tbl"><thead><tr><th>Chip</th><th>Recording</th><th>Well</th>
        <th>Outcome</th><th>Step reached</th><th className="n">Spikes</th><th className="n">Took</th><th>Why</th></tr></thead><tbody>
        {shown.map((w,i)=>{const [s2,k2]=WELL_OUT[w.outcome]||[w.outcome,"wait"];return(
          <tr key={i}><td className="mono">{w.chip}</td><td className="mono">{w.run}</td><td>{+String(w.well).replace(/\D/g,"")+1}</td>
            <td><span className={"stamp "+k2}>{s2}</span></td><td className="hint-s">{w.phase}</td>
            <td className="n">{w.spikes!=null?w.spikes.toLocaleString():"—"}</td><td className="n">{w.seconds!=null?dur(w.seconds):"—"}</td>
            <td className="hint-s" style={{whiteSpace:"normal",maxWidth:320}}>{w.reason?plainWellError({error:w.reason,status:"failed"}):""}</td></tr>);})}
      </tbody></table></div>
      {wells.length>60&&<button className="btn sm" style={{marginTop:10}} onClick={()=>setShowAll(x=>!x)}>{showAll?"Show fewer":`Show all ${wells.length}`}</button>}
      </div></div>}
    </div>}

    {conv.length>0&&<div className="sec">
      <div className="sec-h"><div className="sec-t">NWB conversion</div></div>
      <div className="card"><div className="card-b"><div className="tw"><table className="tbl"><thead><tr><th>Chip</th><th>Recording</th><th>Well</th><th>Result</th><th className="n">Took</th><th>Why</th></tr></thead><tbody>
        {conv.map((c,i)=><tr key={i}><td className="mono">{c.chip}</td><td className="mono">{c.run}</td><td>{+String(c.well).replace(/\D/g,"")+1}</td>
          <td><span className={"stamp "+(c.outcome==="failed"?"bad":c.outcome==="not_recorded"?"wait":"ok")}>{c.outcome==="not_recorded"?"not in the file":c.outcome}</span></td>
          <td className="n">{c.seconds?dur(c.seconds):"—"}</td><td className="hint-s">{c.reason||""}</td></tr>)}
      </tbody></table></div></div></div></div>}

    <div className="sec">
      <div className="sec-h"><div className="sec-t">What it produced</div></div>
      <div className="card"><div className="card-b">{(d.outputs||[]).length===0?<div className="hint">Nothing yet.</div>:
        <div className="outs">{d.outputs.map((o,i)=><div className="out" key={i}>
          <div><b>{o.label}</b> <span className="hint-s">{o.count} {o.unit}{o.bytes!=null?` · ${fmtBytes(o.bytes)}`:""}</span></div>
          <div className="mono hint-s" style={{wordBreak:"break-all"}}>{o.path}</div>
          {o.report&&<a className="btn sm" target="_blank" rel="noopener" href={`/api/reports/view?path=${encodeURIComponent(o.path)}`}><Ext s={13}/> Open</a>}
          {o.log&&<button className="btn sm" onClick={()=>onLog(o.path,`${dt.big} ${dt.year} · ${jobName(d.job)}`)}><Lines s={13}/> Open</button>}
        </div>)}</div>}</div></div>
    </div>

    <div className="sec">
      <div className="sec-h"><div className="sec-t">Settings it ran with</div></div>
      <div className="card"><div className="card-b">
        {Object.keys(st).length===0?<div className="hint">Not recorded for this run (it happened before history was kept).</div>:
        <dl className="kv">
          <dt>Spike sorting</dt><dd>{st.spike_sorting?"On":"Off (spike detection only)"}</dd>
          <dt>Converted to NWB first</dt><dd>{st.nwb_convert?`Yes (${st.nwb_compression==="maxwell"?"MaxWell compression":"standard compression"})`:"No"}</dd>
          <dt>Fast local disk</dt><dd>{st.stage_locally?`Yes — ${st.scratch_dir||"default folder"}`:"No"}</dd>
          <dt>Analyses at once</dt><dd>Network {st.max_concurrent_network} · Activity scan {st.max_concurrent_activity}</dd>
          <dt>Recordings from</dt><dd className="mono">{st.watch_dir}</dd>
          <dt>Results to</dt><dd className="mono">{st.output_dir}</dd>
        </dl>}
        {d.command&&<details className="adv"><summary><span className="chev"><Chev s={14}/></span>Exact command</summary><Code text={d.command}/></details>}
      </div></div>
    </div>
  </div>);
}

/* ── App ──────────────────────────────────────────────────────────────── */
function App({user,onSignOut}){
  const [schema,setSchema]=useState(null);
  const [cfg,setCfg]=useState(null);
  const [status,setStatus]=useState(null);
  const [fatal,setFatal]=useState("");
  const VIEWS=["dashboard","progress","add","reports","settings"];
  const [tab,setTab]=useState(()=>{const h=location.hash.slice(1);
    if(VIEWS.includes(h))return h;
    try{const t=localStorage.getItem("mea-tab");return VIEWS.includes(t)?t:"dashboard";}catch(e){return"dashboard";}});
  // A run's detail page has its own address (#run/<id>) so Back works.
  const [runId,setRunId]=useState(()=>location.hash.startsWith("#run/")?location.hash.slice(5):null);
  const [reports,setReports]=useState({});
  const [wells,setWells]=useState({});
  const [openW,setOpenW]=useState({});
  const [log,setLog]=useState(null);
  const [feed,setFeed]=useState([]);
  const [toasts,setToasts]=useState([]);
  const [busy,setBusy]=useState(false);
  const [confirmAsk,setConfirmAsk]=useState(null);
  const tid=useRef(0),seq=useRef(0),polling=useRef(false),openWRef=useRef({}),confirmRes=useRef(null);

  const toast=useCallback((t,m,k="ok")=>{const id=++tid.current;setToasts(x=>[...x,{id,t,m,k}]);
    setTimeout(()=>setToasts(x=>x.filter(y=>y.id!==id)),k==="error"?9000:4500);},[]);
  const ask=useCallback(a=>new Promise(res=>{confirmRes.current=res;setConfirmAsk(a);}),[]);
  const closeAsk=v=>{setConfirmAsk(null);confirmRes.current&&confirmRes.current(v);};

  useEffect(()=>{try{localStorage.setItem("mea-tab",tab);}catch(e){}
    if(!runId&&location.hash.slice(1)!==tab)history.replaceState(null,"","#"+tab);},[tab,runId]);
  useEffect(()=>{const h=()=>{const t=location.hash.slice(1);
    if(t.startsWith("run/")){setRunId(t.slice(4));window.scrollTo(0,0);return;}
    setRunId(null);if(VIEWS.includes(t))setTab(t);};
    addEventListener("hashchange",h);addEventListener("popstate",h);
    return()=>{removeEventListener("hashchange",h);removeEventListener("popstate",h);};},[]);
  useEffect(()=>{openWRef.current=openW;},[openW]);

  useEffect(()=>{(async()=>{try{
    const [s,c]=await Promise.all([api("/api/schema"),api("/api/config")]);setSchema(s);setCfg(c);
  }catch(e){setFatal(e.message);}})();},[]);

  const loadReports=useCallback(()=>api("/api/reports").then(d=>{
    const m={};(d.reports||[]).forEach(r=>{m[`${r.project}/${r.label}`]=r;});setReports(m);}).catch(()=>{}),[]);

  // Status every 3 s, one request at a time, never while the tab is hidden.
  const refresh=useCallback(async force=>{
    if(polling.current||(!force&&document.hidden))return;
    polling.current=true;
    try{
      await Promise.all([
        api("/api/status").then(setStatus).catch(()=>{}),
        api(`/api/logs?since=${seq.current}`).then(d=>{if(d.lines?.length){seq.current=d.last_seq;
          setFeed(a=>[...a,...d.lines].slice(-60));}}).catch(()=>{}),
      ]);
    }finally{polling.current=false;}
  },[]);
  useEffect(()=>{
    refresh(true);loadReports();
    const t=setInterval(()=>refresh(false),3000), r=setInterval(loadReports,60000);
    const v=()=>{if(!document.hidden){refresh(true);loadReports();}};
    document.addEventListener("visibilitychange",v);
    return()=>{clearInterval(t);clearInterval(r);document.removeEventListener("visibilitychange",v);};
  },[refresh,loadReports]);

  // Wells: fetched when opened; refreshed every 20 s only while that date is running.
  // One read per date at a time: on a busy results disk a read can take a
  // minute, and stacking more behind it only makes every one slower.
  const inFlight=useRef({});
  const fetchWells=useCallback(async(folder,logPath)=>{
    if(inFlight.current[folder])return;
    inFlight.current[folder]=true;
    try{
      const [d,lg]=await Promise.all([
        api(`/api/runs/checkpoints?path=${encodeURIComponent(folder)}`),
        logPath?api(`/api/runs/log?path=${encodeURIComponent(logPath)}&tail=1000000`).catch(()=>null):null]);
      setWells(w=>({...w,[folder]:{...d,notes:lg?parseWellNotes(lg.lines||[]):{}}}));}
    catch(e){setWells(w=>({...w,[folder]:{error:e.message}}));}
    finally{delete inFlight.current[folder];}
  },[]);
  const runningNet=useMemo(()=>(status?.runs||[]).filter(r=>r.job==="network"&&r.status==="running")
    .map(r=>[r.folder,r.log]),[status]);
  useEffect(()=>{
    runningNet.forEach(([f,l])=>fetchWells(f,l));
    const t=setInterval(()=>{if(!document.hidden)runningNet.forEach(([f,l])=>fetchWells(f,l));},20000);
    return()=>clearInterval(t);
  },[runningNet.map(x=>x[0]).join("|"),fetchWells]);

  // Log drawer: follows live while that job runs.
  const loadLog=useCallback(async(l)=>{
    try{const d=await api(`/api/runs/log?path=${encodeURIComponent(l.path)}&tail=600`);
        setLog(x=>x&&x.path===l.path?{...x,lines:d.lines,error:null}:x);}
    catch(e){setLog(x=>x&&x.path===l.path?{...x,error:e.message}:x);}
  },[]);
  const logLive=!!log&&(status?.runs||[]).some(r=>r.log===log.path&&r.status==="running");
  useEffect(()=>{if(!log||!logLive)return;const t=setInterval(()=>loadLog(log),4000);return()=>clearInterval(t);},[log?.path,logLive,loadLog]);

  const folders=useMemo(()=>{
    const m={};
    (status?.runs||[]).forEach(r=>{(m[r.folder]=m[r.folder]||{folder:r.folder,date:r.run,project:projectOf(r.folder),jobs:[]}).jobs.push(r);});
    return Object.values(m).sort((a,b)=>a.project.localeCompare(b.project)||b.date.localeCompare(a.date));
  },[status]);

  /* ------- early returns: every hook is above this line ------- */
  if(fatal) return (
    <div className="wrap"><div className="card rise" style={{maxWidth:560,margin:"12vh auto"}}><div className="card-b">
      <div className="sec-t" style={{color:"var(--red)"}}>Can’t reach the analysis server</div>
      <p className="hint">{fatal}</p><button className="btn ink" onClick={()=>location.reload()}>Try again</button>
    </div></div></div>);
  if(!schema||!cfg) return (
    <div className="wrap"><div className="skel" style={{height:50,width:300}}/>
      <div className="skel" style={{height:96,marginTop:30}}/><div className="skel" style={{height:260,marginTop:20}}/></div>);

  const runs=status?.runs||[];
  const active=(status?.active_jobs?.network||0)+(status?.active_jobs?.activity||0);
  const watching=!!status?.running;
  const tally={
    wait:folders.filter(f=>["dispatched","waiting","interrupted","detected","held"].includes(folderState(f.jobs))).length,
    run:folders.filter(f=>folderState(f.jobs)==="running").length,
    done:folders.filter(f=>folderState(f.jobs)==="done").length,
    bad:folders.filter(f=>folderState(f.jobs)==="failed").length,
  };

  const payload=()=>({
    watch_dir:cfg.watch_dir,driver_options:cfg.driver_options,h5_glob:cfg.h5_glob,assay_subfolder:cfg.assay_subfolder,
    run_network:!!cfg.run_network,run_activity:!!cfg.run_activity,activity_subfolder:cfg.activity_subfolder,
    activity_output_dir:cfg.activity_output_dir||"",activity_active_hz:Number(cfg.activity_active_hz),
    activity_figures:!!cfg.activity_figures,max_concurrent_network:Number(cfg.max_concurrent_network)||1,
    max_concurrent_activity:Number(cfg.max_concurrent_activity)||1,gpu_cooldown_seconds:Number(cfg.gpu_cooldown_seconds)||0,
    queue_poll_seconds:Number(cfg.queue_poll_seconds)||1,settle_seconds:Number(cfg.settle_seconds),
    poll_seconds:Number(cfg.poll_seconds),require_finished_marker:!!cfg.require_finished_marker,
    skip_settle_for_existing:!!cfg.skip_settle_for_existing,driver_python:cfg.driver_python||"",
    logs_in_output:cfg.logs_in_output!==false,stage_locally:!!cfg.stage_locally,scratch_dir:cfg.scratch_dir||"",
    stage_min_free_gb:Number(cfg.stage_min_free_gb)||200,dry_run:!!cfg.dry_run,
    ai_requirements:cfg.ai_requirements||"",auto_handoff:cfg.auto_handoff!==false,
    nwb_convert:!!cfg.nwb_convert,nwb_python:cfg.nwb_python||"",nwb_compression:cfg.nwb_compression||"gzip",
  });
  const run_=async(fn,ok,m)=>{setBusy(true);try{await fn();if(ok)toast(ok,m);refresh(true);}
    catch(e){toast("That didn’t work",e.message,"error");}finally{setBusy(false);}};

  // Saving replaces the server's scheduler, so never while work is running.
  const save=()=>run_(()=>api("/api/config",{method:"POST",body:JSON.stringify(payload())}),"Settings saved");
  save.payload=payload;
  // Saving settings is refused while anything is in line or running.
  const inLine=runs.some(r=>["dispatched","queued","running"].includes(r.status));
  const dateList=fs=>fs.map(f=>{const d=prettyDate(f.date);return `${d.big} ${d.year}`;}).join(", ");
  const startWatch=async()=>{
    // Starting picks interrupted dates up again; say which, and let them wait.
    const intr=folders.filter(f=>f.jobs.some(j=>j.status==="interrupted"));
    let hold=false;
    if(intr.length){
      const n=intr.length, s=n===1?"":"s";
      const a=await ask({title:`Continue ${n} interrupted date${s}?`,ok:n===1?"Continue it":"Continue them",
        alt:"Keep on hold",
        body:`${n===1?"This date was":"These dates were"} stopped before ${n===1?"it":"they"} finished: ${dateList(intr)}.\n\n`+
          `Continue ${n===1?"it":"them"} now, or keep ${n===1?"it":"them"} on hold and only watch for new dates. `+
          `Dates on hold can be resumed later from Progress.`});
      if(!a)return;
      hold=a==="alt";
    }
    run_(async()=>{
      if(!active&&!inLine) await api("/api/config",{method:"POST",body:JSON.stringify(payload())});
      await api("/api/watcher/start"+(hold?"?hold_interrupted=true":""),{method:"POST"});},
      "Watching for new recordings",hold?"Interrupted dates are on hold. New dates are picked up once copied.":
        "New dates are picked up automatically once copied.");
  };
  const onHold=async f=>{
    const dt=prettyDate(f.date), running=f.jobs.some(j=>j.status==="running");
    const paths=f.jobs.filter(j=>HOLDABLE.includes(j.status)).map(j=>j.path);
    if(!(await ask({title:`Put ${dt.big} on hold?`,danger:running,ok:running?"Stop and hold":"Put on hold",
      body:running?"Its analysis is running and will be stopped now. Wells that already finished keep their results, "+
        "so resuming it later repeats only the well that was in progress.":
        "It will be taken off the queue and kept for later. Nothing is deleted. Press Resume on it when you want it analysed."})))return;
    run_(()=>api("/api/runs/hold",{method:"POST",body:JSON.stringify({paths})}),
      "On hold",`${dt.big} will not be analysed until you resume it.`);
  };
  const onResume=f=>{const dt=prettyDate(f.date);
    run_(()=>api("/api/queue",{method:"POST",body:JSON.stringify({folders:[f.folder]})}),
      "Resumed",`${dt.big} is back in the queue.`);};
  const holdable=runs.filter(r=>HOLDABLE.includes(r.status));
  const resetQueue=async()=>{
    const c=sts=>holdable.filter(r=>sts.includes(r.status)).length, pl=n=>n===1?"":"s";
    const nRun=c(["running"]), nWait=c(["dispatched","queued"]), nInt=c(["interrupted","waiting"]);
    const lines=[nRun&&`• ${nRun} running analysis job${pl(nRun)} will be stopped now`,
      nWait&&`• ${nWait} waiting job${pl(nWait)} will be taken out of the queue`,
      nInt&&`• ${nInt} interrupted job${pl(nInt)} will be kept from resuming`,
      watching&&"• Watching for new recordings will be paused"].filter(Boolean);
    if(!(await ask({title:"Reset the queue?",danger:nRun>0,ok:"Reset queue",
      body:lines.join("\n")+"\n\nThese dates are put “On hold”: nothing starts them until you press Resume on them — "+
        "for example after switching off Network analysis in Settings to run only the activity scan.\n\n"+
        "Finished results are kept. Wells that already finished keep theirs too, so resuming repeats only the well in progress."})))return;
    run_(()=>api("/api/queue/reset",{method:"POST"}),"Queue reset",
      "Nothing will start until you resume a date or add recordings.");
  };
  const pauseWatch=()=>run_(()=>api("/api/watcher/stop",{method:"POST"}),
    "Paused","No new dates will be started. Analyses already running carry on.");
  const stopAll=async()=>{
    if(!(await ask({title:"Stop all analyses?",danger:true,ok:"Stop everything",
      body:`${active} analysis job${active===1?"":"s"} will be stopped now. Dates that were in progress will need to be analysed again.`})))return;
    run_(()=>api("/api/watcher/stop?cancel_running=true",{method:"POST"}),"Stopped","All analyses were stopped.");
  };
  const onWells=f=>{const o=!openW[f.folder];setOpenW(x=>({...x,[f.folder]:o}));
    const settled=folderState(f.jobs)==="done"&&wells[f.folder]&&!wells[f.folder].error;
    if(o&&!settled)fetchWells(f.folder,f.jobs.find(j=>j.job==="network")?.log);};
  const onLog=f=>{const j=f.jobs.find(x=>x.job==="network"&&x.log)||f.jobs.find(x=>x.log);if(!j)return;
    const dt=prettyDate(f.date);const l={path:j.log,title:`${dt.big} ${dt.year} · ${j.job_label||j.job}`,lines:[]};
    setLog(l);loadLog(l);};
  const onAgain=async f=>{
    const dt=prettyDate(f.date);
    if(!(await ask({title:`Analyse ${dt.big} again?`,ok:"Analyse again",
      body:"Its results will be computed again from the recordings and replaced. This can take a while."})))return;
    run_(async()=>{for(const j of f.jobs)await api("/api/runs/reset",{method:"POST",body:JSON.stringify({path:j.path})});
      await api("/api/queue",{method:"POST",body:JSON.stringify({folders:[f.folder],rerun:true})});},
      "Added again",`${dt.big} will be analysed again.`);
  };

  const openLogPath=(path,title)=>{const l={path,title,lines:[]};setLog(l);loadLog(l);};
  const pickTab=k=>{setRunId(null);setTab(k);history.pushState(null,"","#"+k);};
  const TABS=[["dashboard","Dashboard"],["progress","Progress",folders.length],["add","Add recordings"],["reports","AI report",Object.keys(reports).length],["settings","Settings"]];
  return (
    <div className="wrap">
      <h1 className="sr">MEA Bench — analysis control</h1>
      <header className="top rise" style={{"--i":0}}>
        <div>
          <div className="brand">MEA <i>Bench</i></div>
          <div className="brand-sub">Ben-Shalom Lab · recordings in, reports out</div>
        </div>
        <div className="grow"/>
        <div className="ctrl">
          <span className="livechip">
            <i className={"dot "+(active?"run":watching?"ok":"wait")}/>
            {active?<><b>{active}</b> analysing now</>:watching?"Watching for new recordings":"Idle"}
          </span>
          {watching
            ? <button className="btn" disabled={busy} onClick={pauseWatch}><Pause s={14}/> Pause watching</button>
            : <button className="btn" disabled={busy} onClick={startWatch} title="Automatically analyse new dates as they are copied in"><Play s={12}/> Watch for new</button>}
          {active>0&&<button className="btn red" disabled={busy} onClick={stopAll}><Stop s={12}/> Stop all</button>}
          <span className="me" title={user.email}>{user.name}
            <button className="btn ghost sm" onClick={onSignOut}>Sign out</button></span>
        </div>
      </header>

      <nav className="tabs" role="tablist">
        {TABS.map(([k,l,n])=>(
          <button key={k} role="tab" className="tab" aria-selected={!runId&&tab===k} onClick={()=>pickTab(k)}>
            {l}{n?<span className="n">{n}</span>:null}</button>))}
      </nav>
      <div className="tabline"/>

      {runId&&<RunDetail id={runId} onLog={openLogPath} onBack={()=>{location.hash=tab;}}/>}
      {!runId&&tab==="dashboard"&&<Dashboard/>}
      {!runId&&tab==="progress"&&<>
        <div className="tally rise" style={{"--i":1}}>
          {[["wait","Waiting"],["run","Analysing"],["done","Done"],["bad","Need attention"]].map(([k,l])=>(
            <div className="tal" key={k} data-k={k} data-on={tally[k]>0}>
              <div className="tal-v">{status?tally[k]:"–"}</div><div className="tal-k">{l} <span className="hint-s">dates</span></div>
            </div>))}
        </div>
        {holdable.length>0&&<div className="qbar rise" style={{"--i":1}}>
          <button className="btn sm" disabled={busy} onClick={resetQueue}
            title="Stop and hold everything that has not finished, so you can decide what to run"><Again s={13}/> Reset queue</button>
        </div>}
        <Progress folders={folders} reports={reports} wells={wells} openW={openW}
                  onWells={onWells} onLog={onLog} onAgain={onAgain} onHold={onHold} onResume={onResume}
                  feed={feed} goAdd={()=>setTab("add")}/>
      </>}
      {!runId&&tab==="add"&&<AddRecordings cfg={cfg} toast={toast} ask={ask} onQueued={()=>{refresh(true);setTab("progress");}}/>}
      {!runId&&tab==="reports"&&<AiReport cfg={cfg} reports={reports} toast={toast}/>}
      {!runId&&tab==="settings"&&<Settings cfg={cfg} setCfg={setCfg} schema={schema} locked={active>0} onSave={save} busy={busy} toast={toast}/>}

      <div className="foot"><span>Orchestration-MEA</span><span>·</span><span>recordings are only ever read, never changed</span></div>

      {log&&<LogDrawer log={log} live={logLive} onClose={()=>setLog(null)}/>}
      <Confirm ask={confirmAsk} onClose={closeAsk}/>
      <Toasts items={toasts} close={id=>setToasts(t=>t.filter(x=>x.id!==id))}/>
    </div>);
}

/* ── Signing in ───────────────────────────────────────────────────────── */
function Login({onIn}){
  const [name,setName]=useState(()=>{try{return localStorage.getItem("mea-name")||"";}catch(e){return"";}});
  const [email,setEmail]=useState(()=>{try{return localStorage.getItem("mea-email")||"";}catch(e){return"";}});
  const [err,setErr]=useState("");
  const [busy,setBusy]=useState(false);
  const go=async e=>{e.preventDefault();setErr("");setBusy(true);
    try{const r=await api("/api/login",{method:"POST",body:JSON.stringify({name,email})});
      try{localStorage.setItem("mea-name",name);localStorage.setItem("mea-email",email);}catch(x){}
      onIn(r.user);}
    catch(x){setErr(x.message);}finally{setBusy(false);}};
  return (<div className="wrap"><div className="card rise login" style={{maxWidth:440,margin:"12vh auto"}}><div className="card-b">
    <div className="brand">MEA <i>Bench</i></div>
    <div className="brand-sub" style={{marginBottom:20}}>Ben-Shalom Lab · recordings in, reports out</div>
    <form onSubmit={go} noValidate>
      <label className="f"><span className="f-l">Your name</span>
        <input className="inp" name="name" autoComplete="name" value={name} onChange={e=>setName(e.target.value)} autoFocus/></label>
      <label className="f"><span className="f-l">Email</span>
        <input className="inp" name="email" type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)}/></label>
      <div className="hint-s" style={{margin:"4px 0 14px"}}>No password. Your name is shown on every analysis you start, so others know whose it is.</div>
      {err&&<div style={{marginBottom:12}}><Callout kind="red" icon={<Alert s={16}/>}>{err}</Callout></div>}
      <button className="btn ink" type="submit" disabled={busy}>{busy?<span className="spin"/>:null} Sign in</button>
    </form>
  </div></div></div>);
}

function Root(){
  const [user,setUser]=useState(undefined);          // undefined: still asking
  const [err,setErr]=useState("");
  useEffect(()=>{api("/api/me").then(r=>setUser(r.user||null)).catch(e=>setErr(e.message));
    const out=()=>setUser(null);addEventListener("mea-signed-out",out);
    return()=>removeEventListener("mea-signed-out",out);},[]);
  const signOut=async()=>{try{await api("/api/logout",{method:"POST"});}catch(e){}setUser(null);};
  if(err) return (<div className="wrap"><div className="card rise" style={{maxWidth:560,margin:"12vh auto"}}><div className="card-b">
      <div className="sec-t" style={{color:"var(--red)"}}>Can’t reach the analysis server</div>
      <p className="hint">{err}</p><button className="btn ink" onClick={()=>location.reload()}>Try again</button></div></div></div>);
  if(user===undefined) return <div className="wrap"><div className="skel" style={{height:50,width:300}}/></div>;
  if(!user) return <Login onIn={setUser}/>;
  return <App key={user.email} user={user} onSignOut={signOut}/>;
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root/>);
