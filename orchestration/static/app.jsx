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
  return sts[0]||"waiting";
}

// What the pipeline's notes mean, said simply.
function plainNote(job){
  const d=job.detail||"", e=job.error||"";
  let m=/(\d+) of (\d+) well subprocess\(es\) failed/.exec(d);
  if(m) return {t:`${m[2]-m[1]} of ${m[2]} wells finished · ${m[1]} had problems`,k:"warn"};
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

function plainWellError(r){
  const e=String(r.error||"");
  if(/stream_id well\d+ is not in/.test(e))return"Not in this recording file — nothing to analyse.";
  if(/n_samples=\d+ should be >= n_clusters/.test(e))return"Almost no activity in this well.";
  if(/out of memory/i.test(e))return"Ran out of memory.";
  if(r.status!=="complete"&&!e)return"Stopped without an error message.";
  return (e.split("\n").find(Boolean)||"Unknown problem").slice(0,180);
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
function Plates({data}){
  if(!data) return <div className="hint" style={{paddingTop:10,display:"flex",gap:10,alignItems:"center"}}>
    <span className="spin"/> Reading well results… While analyses are running the results disk is busy,
    so this can take a minute or two. You can keep using the page.</div>;
  if(data.error) return <div className="hint" style={{paddingTop:10,color:"var(--red)"}}>{data.error}</div>;
  const rows=data.wells||[];
  if(!rows.length) return <div className="hint" style={{paddingTop:10}}>
    No wells have started yet. They appear here as the analysis reaches them.</div>;
  const chips={};
  rows.forEach(r=>{const k=`${r.chip_id||"?"}·${r.run_id||""}`;(chips[k]=chips[k]||{chip:r.chip_id,run:r.run_id,wells:{}}).wells[r.well]=r;});
  const s=data.summary||{};
  const probs=rows.filter(r=>r.status==="failed"||(r.status!=="complete"&&r.error));
  let i=0;
  return (<>
    <div className="legend">
      <span><b>{s.complete||0}</b>&nbsp;of {s.wells||rows.length} wells finished</span>
      <span><i className="dot ok"/> finished</span><span><i className="dot run"/> in progress</span>
      <span><i className="dot bad"/> problem</span>
    </div>
    <div className="plates">
      {Object.values(chips).map(c=>{
        const ids=Object.keys(c.wells).map(w=>+w.replace(/\D/g,""));
        const n=Math.max(6,Math.ceil((Math.max(...ids)+1)/6)*6);
        return (
          <div className="plate" key={c.chip+c.run}>
            <div className="plate-h">Chip <b>{c.chip||"?"}</b><span className="hint-s">recording {c.run}</span></div>
            <div className="wells">
              {Array.from({length:n},(_,k)=>{
                const r=c.wells[`well${String(k).padStart(3,"0")}`];
                const cls=!r?"none":r.status==="complete"?"complete":r.status==="failed"?"failed":"running";
                const tip=!r?"Not part of this recording":r.status==="complete"?`Well ${k+1}: finished`
                  :r.status==="failed"?`Well ${k+1}: ${plainWellError(r)}`:`Well ${k+1}: ${r.stage_name||"in progress"}`;
                return <div key={k} className={"well "+cls} style={{"--i":i++}} title={tip}>{k+1}</div>;
              })}
            </div>
          </div>);})}
    </div>
    {probs.length>0&&<div className="probs">
      {probs.map((r,j)=><div className="prob" key={j}><span className="w">{r.chip_id} · well {+r.well.replace(/\D/g,"")+1}</span>
        <span>{plainWellError(r)}</span></div>)}
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
function Line({f,report,wells,open,onWells,onLog,onAgain,i}){
  const st=folderState(f.jobs), ji=jobInfo(st);
  const dt=prettyDate(f.date);
  const net=f.jobs.find(j=>j.job==="network"), scan=f.jobs.find(j=>j.job==="activity");
  const note=net?plainNote(net):null;
  const busy=st==="running";
  const sum=wells?.summary;
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
          {note&&<span className={"note-l "+note.k}>{note.t}</span>}
        </div>
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
        <button className="btn ghost sm" title="Analyse this date again" aria-label="Analyse again" onClick={()=>onAgain(f)}><Again s={14}/></button>
      </div>
    </div>
    {open&&<div className="plate-wrap"><Plates data={wells}/></div>}
  </>);
}

function Progress({folders,reports,wells,openW,onWells,onLog,onAgain,feed,goAdd}){
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
                           onWells={onWells} onLog={onLog} onAgain={onAgain}/>)}
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

  // "Analysed" only when every analysis for the date is finished.
  const done=p=>{const j=info[p]?.jobs||[];return j.length>0&&j.every(x=>x.status==="done");};
  const partly=p=>!done(p)&&(info[p]?.jobs||[]).some(x=>x.status==="done");
  const chosen=Object.keys(sel).filter(k=>sel[k]);
  const chosenDone=chosen.filter(done).length;
  const fresh=(entries||[]).filter(x=>!done(x.path)&&x.finished!==false);

  const go=async()=>{
    if(chosenDone&&again&&!(await ask({title:"Analyse again?",ok:"Analyse again",
      body:`${chosenDone} of these dates were already analysed. Their results will be computed again and replaced.`})))return;
    setBusy(true);
    try{
      const r=await api("/api/queue",{method:"POST",body:JSON.stringify({folders:chosen,rerun:again})});
      const n=new Set(r.queued.map(q=>q.path)).size;
      toast(`${n} date${n===1?"":"s"} added`,"They will be analysed in order. Follow them under Progress.");
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
                const dt=prettyDate(x.name), on=!!sel[x.path], dn=done(x.path);
                const jobs=(info[x.path]?.jobs||[]).map(j=>j.label).join(" + ");
                return (
                  <label key={x.path} className="tile" data-on={on} data-done={dn} style={{"--i":k}}>
                    <input type="checkbox" checked={on} onChange={()=>setSel(v=>({...v,[x.path]:!v[x.path]}))}/>
                    {dn?<span className="t-tag done">analysed</span>:partly(x.path)?<span className="t-tag copy">partly done</span>
                      :x.finished===false?<span className="t-tag copy">copying</span>:null}
                    <div className="t-date">{dt.big}</div>
                    <div className="t-code">{dt.year} · {x.name}</div>
                    <div className="t-what">{jobs||info[x.path]?.note||" "}</div>
                    <span className="t-tick">{on&&<Check s={13} w={3}/>}</span>
                  </label>);})}
            </div>
          </>}

    {chosen.length>0&&<div className="sticky">
      <div style={{flex:1,minWidth:200}}>
        <b>{chosen.length} date{chosen.length===1?"":"s"} selected</b>
        {chosenDone>0&&<label style={{display:"flex",gap:8,alignItems:"center",marginTop:4,fontSize:13,cursor:"pointer"}}>
          <input type="checkbox" checked={again} onChange={e=>setAgain(e.target.checked)}/>
          Also redo the {chosenDone} already analysed</label>}
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
  useEffect(()=>{api("/api/handoff").then(d=>d?.state&&d.state!=="idle"&&setLast(d)).catch(()=>{});},[]);
  const save=async(a=auto)=>{
    try{await api("/api/requirements",{method:"POST",body:JSON.stringify({text,auto_handoff:a})});
        setSaved(text);toast("Saved","Every new report will follow these instructions.");return true;}
    catch(e){toast("Not saved",e.message,"error");return false;}
  };
  const prepare=async()=>{
    setBusy(true);
    try{if(text!==saved&&!(await save()))return;
        const r=await api("/api/handoff",{method:"POST",body:JSON.stringify({folders:[]})});
        setLast({state:"done",...r});}
    catch(e){toast("Could not prepare",e.message,"error");}
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
            <div className="empty-d">Reports appear here as each recording date finishes, a few minutes after its analyses complete.</div></div></div>
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
          <summary><span className="chev"><Chev s={14}/></span>Report packages for Claude</summary>
          <Switch id="ai-auto" checked={auto} onChange={v=>{setAuto(v);save(v);}}
                  label="Make a package when a batch of added dates finishes"
                  hint="Leave this off while the lab's report service is writing a report for each date — otherwise every batch gets two packages."/>
          <div className="hint" style={{margin:"6px 0 12px"}}>Bundles all results with these instructions into one folder that
            Claude can turn into a report covering every date.</div>
          <button className="btn" disabled={busy} onClick={prepare}>{busy?<span className="spin"/>:<Doc s={14}/>} Prepare package for all results</button>
          {last?.state==="done"&&last.prompt&&<div style={{marginTop:12}}>
            <Callout kind="green" icon={<Check s={17}/>}>Package ready — {last.network_wells} wells, {last.activity_runs} scans.
              In a terminal on the analysis computer, run:</Callout>
            <div style={{marginTop:8}}><Code text={last.instruction}/></div></div>}
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
        <Switch id="act" checked={cfg.run_activity} disabled={locked} onChange={v=>setT("run_activity",v)}
                label="Activity scan" hint="Whole-chip activity maps and quality checks. Takes seconds."/>
        <Switch id="stg" checked={!!cfg.stage_locally} disabled={locked} onChange={v=>setT("stage_locally",v)}
                label="Use the fast local disk while working"
                hint="Keeps big temporary files on the computer's fast disk and deletes them afterwards. Several times faster."/>
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

/* ── App ──────────────────────────────────────────────────────────────── */
function App(){
  const [schema,setSchema]=useState(null);
  const [cfg,setCfg]=useState(null);
  const [status,setStatus]=useState(null);
  const [fatal,setFatal]=useState("");
  const [tab,setTab]=useState(()=>{const h=location.hash.slice(1);
    if(["progress","add","reports","settings"].includes(h))return h;
    try{return localStorage.getItem("mea-tab")||"progress";}catch(e){return"progress";}});
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
    if(location.hash.slice(1)!==tab)history.replaceState(null,"","#"+tab);},[tab]);
  useEffect(()=>{const h=()=>{const t=location.hash.slice(1);
    if(["progress","add","reports","settings"].includes(t))setTab(t);};
    addEventListener("hashchange",h);return()=>removeEventListener("hashchange",h);},[]);
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
  const fetchWells=useCallback(async folder=>{
    if(inFlight.current[folder])return;
    inFlight.current[folder]=true;
    try{const d=await api(`/api/runs/checkpoints?path=${encodeURIComponent(folder)}`);setWells(w=>({...w,[folder]:d}));}
    catch(e){setWells(w=>({...w,[folder]:{error:e.message}}));}
    finally{delete inFlight.current[folder];}
  },[]);
  const runningFolders=useMemo(()=>[...new Set((status?.runs||[]).filter(r=>r.job==="network"&&r.status==="running").map(r=>r.folder))],[status]);
  useEffect(()=>{
    runningFolders.forEach(fetchWells);
    const t=setInterval(()=>{if(!document.hidden)runningFolders.forEach(fetchWells);},20000);
    return()=>clearInterval(t);
  },[runningFolders.join("|"),fetchWells]);

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
    wait:folders.filter(f=>["dispatched","waiting","interrupted","detected"].includes(folderState(f.jobs))).length,
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
  });
  const run_=async(fn,ok,m)=>{setBusy(true);try{await fn();if(ok)toast(ok,m);refresh(true);}
    catch(e){toast("That didn’t work",e.message,"error");}finally{setBusy(false);}};

  // Saving replaces the server's scheduler, so never while work is running.
  const save=()=>run_(()=>api("/api/config",{method:"POST",body:JSON.stringify(payload())}),"Settings saved");
  save.payload=payload;
  const startWatch=()=>run_(async()=>{
    if(!active) await api("/api/config",{method:"POST",body:JSON.stringify(payload())});
    await api("/api/watcher/start",{method:"POST"});},
    "Watching for new recordings","New dates are picked up automatically once copied.");
  const pauseWatch=()=>run_(()=>api("/api/watcher/stop",{method:"POST"}),
    "Paused","No new dates will be started. Analyses already running carry on.");
  const stopAll=async()=>{
    if(!(await ask({title:"Stop all analyses?",danger:true,ok:"Stop everything",
      body:`${active} analysis job${active===1?"":"s"} will be stopped now. Dates that were in progress will need to be analysed again.`})))return;
    run_(()=>api("/api/watcher/stop?cancel_running=true",{method:"POST"}),"Stopped","All analyses were stopped.");
  };
  const onWells=f=>{const o=!openW[f.folder];setOpenW(x=>({...x,[f.folder]:o}));
    const settled=folderState(f.jobs)==="done"&&wells[f.folder]&&!wells[f.folder].error;
    if(o&&!settled)fetchWells(f.folder);};
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

  const TABS=[["progress","Progress",folders.length],["add","Add recordings"],["reports","AI report",Object.keys(reports).length],["settings","Settings"]];
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
        </div>
      </header>

      <nav className="tabs" role="tablist">
        {TABS.map(([k,l,n])=>(
          <button key={k} role="tab" className="tab" aria-selected={tab===k} onClick={()=>setTab(k)}>
            {l}{n?<span className="n">{n}</span>:null}</button>))}
      </nav>
      <div className="tabline"/>

      {tab==="progress"&&<>
        <div className="tally rise" style={{"--i":1}}>
          {[["wait","Waiting"],["run","Analysing"],["done","Done"],["bad","Need attention"]].map(([k,l])=>(
            <div className="tal" key={k} data-k={k} data-on={tally[k]>0}>
              <div className="tal-v">{status?tally[k]:"–"}</div><div className="tal-k">{l} <span className="hint-s">dates</span></div>
            </div>))}
        </div>
        <Progress folders={folders} reports={reports} wells={wells} openW={openW}
                  onWells={onWells} onLog={onLog} onAgain={onAgain} feed={feed} goAdd={()=>setTab("add")}/>
      </>}
      {tab==="add"&&<AddRecordings cfg={cfg} toast={toast} ask={ask} onQueued={()=>{refresh(true);setTab("progress");}}/>}
      {tab==="reports"&&<AiReport cfg={cfg} reports={reports} toast={toast}/>}
      {tab==="settings"&&<Settings cfg={cfg} setCfg={setCfg} schema={schema} locked={active>0} onSave={save} busy={busy} toast={toast}/>}

      <div className="foot"><span>Orchestration-MEA</span><span>·</span><span>recordings are only ever read, never changed</span></div>

      {log&&<LogDrawer log={log} live={logLive} onClose={()=>setLog(null)}/>}
      <Confirm ask={confirmAsk} onClose={closeAsk}/>
      <Toasts items={toasts} close={id=>setToasts(t=>t.filter(x=>x.id!==id))}/>
    </div>);
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
