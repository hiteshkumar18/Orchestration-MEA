// Source for app.js. Edit this, then: cd tests && npm run build
const {useState,useEffect,useCallback,useRef,useMemo} = React;

/* ── Icons ─────────────────────────────────────────────────────────────── */
const I=({d,s=16,f="none"})=>(
  <svg width={s} height={s} viewBox="0 0 24 24" fill={f} stroke="currentColor"
       strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>);
const Wave =p=><I {...p} d={<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>}/>;
const Folder=p=><I {...p} d={<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>}/>;
const Play =p=><I {...p} f="currentColor" d={<polygon points="6 4 20 12 6 20"/>}/>;
const Stop =p=><I {...p} f="currentColor" d={<rect x="6" y="6" width="12" height="12" rx="2"/>}/>;
const Check=p=><I {...p} d={<polyline points="20 6 9 17 4 12"/>}/>;
const Ex   =p=><I {...p} d={<><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>}/>;
const Search=p=><I {...p} d={<><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>}/>;
const Chev =p=><I {...p} d={<polyline points="9 18 15 12 9 6"/>}/>;
const Copy =p=><I {...p} d={<><rect x="9" y="9" width="13" height="13" rx="2.5"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>}/>;
const Term =p=><I {...p} d={<><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></>}/>;
const Sync =p=><I {...p} d={<><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></>}/>;
const Moon =p=><I {...p} d={<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>}/>;
const Sun  =p=><I {...p} d={<><circle cx="12" cy="12" r="4.5"/><line x1="12" y1="1.5" x2="12" y2="3.5"/><line x1="12" y1="20.5" x2="12" y2="22.5"/><line x1="4.2" y1="4.2" x2="5.7" y2="5.7"/><line x1="18.3" y1="18.3" x2="19.8" y2="19.8"/><line x1="1.5" y1="12" x2="3.5" y2="12"/><line x1="20.5" y1="12" x2="22.5" y2="12"/><line x1="4.2" y1="19.8" x2="5.7" y2="18.3"/><line x1="18.3" y1="5.7" x2="19.8" y2="4.2"/></>}/>;
const Info =p=><I {...p} d={<><circle cx="12" cy="12" r="9.5"/><line x1="12" y1="16.5" x2="12" y2="11.5"/><line x1="12" y1="7.8" x2="12.01" y2="7.8"/></>}/>;
const Alert=p=><I {...p} d={<><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13.5"/><line x1="12" y1="17.2" x2="12.01" y2="17.2"/></>}/>;
const Inbox=p=><I {...p} d={<><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></>}/>;
const Clock=p=><I {...p} d={<><circle cx="12" cy="12" r="9.5"/><polyline points="12 6.5 12 12 16 14"/></>}/>;
const Slide=p=><I {...p} d={<><line x1="4" y1="8" x2="20" y2="8"/><line x1="4" y1="16" x2="20" y2="16"/><circle cx="9" cy="8" r="2.4"/><circle cx="15" cy="16" r="2.4"/></>}/>;

/* ── API ───────────────────────────────────────────────────────────────── */
const IS_FILE = location.protocol === "file:";
const H_FILE="This page is open as a local file, so it cannot reach the server.\n\n"+
  "Start the backend and open it through that instead:\n\n"+
  "    python orchestration/api.py --port 8000\n\nthen visit http://localhost:8000";
const H_DOWN="Could not reach the API server.\n\nMake sure it is running:\n\n"+
  "    python orchestration/api.py --port 8000\n\n"+
  "and that this page is open at the same host and port.";

async function api(path,opts){
  if(IS_FILE) throw new Error(H_FILE);
  let r;
  try{ r=await fetch(path,{headers:{"Content-Type":"application/json"},...opts}); }
  catch(e){ throw new Error(H_DOWN); }
  const b=await r.json().catch(()=>({}));
  if(!r.ok){const d=b.detail;
    throw new Error(d?.errors?d.errors.join("\n"):(typeof d==="string"?d:"Request failed"));}
  return b;
}

/* ── Helpers ───────────────────────────────────────────────────────────── */
const ST={
  waiting:{l:"Waiting",c:"p-n",i:0}, detected:{l:"Detected",c:"p-a",i:1},
  dispatched:{l:"Queued",c:"p-a",i:2}, running:{l:"Analyzing",c:"p-a",i:2},
  done:{l:"Complete",c:"p-o",i:3}, failed:{l:"Failed",c:"p-b",i:3},
  /* Cut short by a restart, not a failure: re-queued automatically. */
  interrupted:{l:"Interrupted",c:"p-n",i:1},
};
const STAGES=["Detected","Settled","Analyzing","Complete"];
const settleLeft=d=>{const m=/settling \((\d+)s remaining\)/.exec(d||"");return m?+m[1]:null;};
const ago=iso=>{if(!iso)return"";const s=Math.max(0,(Date.now()-new Date(iso))/1e3);
  return s<60?`${s|0}s ago`:s<3600?`${s/60|0}m ago`:s<86400?`${s/3600|0}h ago`:`${s/86400|0}d ago`;};
const dur=s=>{if(s==null)return"";if(s<60)return`${Math.round(s)}s`;
  const m=s/60|0;return m<60?`${m}m ${Math.round(s%60)}s`:`${m/60|0}h ${m%60}m`;};

/* ── Primitives ────────────────────────────────────────────────────────── */
function Switch({checked,onChange,label,hint,id,disabled}){
  return (
    <div className="sw-row" style={disabled?{opacity:.5}:undefined}>
      <button type="button" role="switch" aria-checked={!!checked} id={id} disabled={disabled}
              className="sw" data-on={!!checked} onClick={()=>!disabled&&onChange(!checked)}>
        <span className="sw-k"/>
      </button>
      <label htmlFor={id} style={{cursor:disabled?"not-allowed":"pointer"}}>
        <div className="sw-l">{label}</div>
        {hint&&<div className="sw-h">{hint}</div>}
      </label>
    </div>
  );
}

function Code({text,scroll}){
  const [c,setC]=useState(false);
  return (
    <div className="code-w">
      <pre className={"code"+(scroll?" code-s":"")}>{text}</pre>
      <button className="btn btn-s code-c"
              onClick={()=>navigator.clipboard?.writeText(text).then(()=>{setC(true);setTimeout(()=>setC(false),1600);})}>
        {c?<><Check s={12}/> Copied</>:<><Copy s={12}/> Copy</>}
      </button>
    </div>
  );
}

function Toasts({items,close}){
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map(t=>(
        <div key={t.id} className="toast">
          <span style={{color:`var(--${t.k==="error"?"bad":t.k==="success"?"ok":"accent"})`,
                        flex:"none",marginTop:1,display:"flex"}}>
            {t.k==="error"?<Alert s={15}/>:t.k==="success"?<Check s={15}/>:<Info s={15}/>}
          </span>
          <div style={{flex:1,minWidth:0}}>
            <div className="toast-t">{t.t}</div>
            {t.m&&<div className="toast-m">{t.m}</div>}
          </div>
          <button className="btn btn-q btn-s btn-i" onClick={()=>close(t.id)} aria-label="Dismiss">
            <Ex s={13}/></button>
        </div>
      ))}
    </div>
  );
}

function LiveLog({lines,follow,setFollow,onClear}){
  const ref=useRef(null);
  useEffect(()=>{if(follow&&ref.current)ref.current.scrollTop=ref.current.scrollHeight;},[lines,follow]);
  return (
    <>
      <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}>
        <span className="pill p-o"><span className="dot dot-l"/>Live</span>
        <span className="f-h">{lines.length} line{lines.length===1?"":"s"}</span>
        <div className="grow"/>
        <label style={{display:"flex",alignItems:"center",gap:6,fontSize:12.5,
                       cursor:"pointer",color:"var(--ink-2)"}}>
          <input type="checkbox" checked={follow} onChange={e=>setFollow(e.target.checked)}
                 style={{accentColor:"var(--accent)"}}/>Auto-scroll
        </label>
        {lines.length>0&&<button className="btn btn-q btn-s" onClick={onClear}>Clear</button>}
      </div>
      <div className="log" ref={ref}>
        {lines.length===0
          ? <div style={{color:"#6e6e78"}}>Waiting for activity…</div>
          : lines.map(l=>(
              <div className="ll" key={l.seq}>
                <span className="lt">{l.time}</span>
                <span className={"lv l-"+l.level}>{l.level}</span>
                <span className="lm">{l.message}</span>
              </div>))}
      </div>
    </>
  );
}

function Field({spec,value,onChange}){
  const set=v=>onChange(spec.key,v);
  const mod=value!==spec.default&&value!==null&&value!==""&&value!==false;
  const L=<span className="f-l" style={{display:"flex",alignItems:"center",gap:6}}>
    {mod&&<span className="mod" title="Changed"/>}<code className="mono">{spec.flag}</code></span>;

  if(spec.type==="flag")
    return <Switch id={spec.key} checked={!!value} onChange={set} label={spec.flag} hint={spec.help}/>;
  if(spec.type==="tristate")
    return <div className="f">{L}
      <select className="sel" value={value==null?"":String(value)}
              onChange={e=>set(e.target.value===""?null:e.target.value==="true")}>
        <option value="">Default</option><option value="true">Enabled</option><option value="false">Disabled</option>
      </select><span className="f-h">{spec.help}</span></div>;
  if(spec.type==="choice")
    return <div className="f">{L}
      <select className="sel" value={value??""} onChange={e=>set(e.target.value||null)}>
        <option value="">Default</option>
        {spec.choices.map(c=><option key={c} value={c}>{c}</option>)}
      </select><span className="f-h">{spec.help}</span></div>;
  if(spec.type==="list")
    return <div className="f">{L}
      <input className="inp mono" placeholder="comma separated"
             value={Array.isArray(value)?value.join(", "):(value??"")}
             onChange={e=>set(e.target.value.split(",").map(s=>s.trim()).filter(Boolean))}/>
      <span className="f-h">{spec.help}</span></div>;
  const num=spec.type==="int"||spec.type==="float";
  return <div className="f">{L}
    <input className={"inp"+(spec.type==="path"?" mono":"")} type={num?"number":"text"}
           step={spec.type==="float"?"0.01":"1"}
           placeholder={spec.type==="path"?"/path/on/server":"Default"} value={value??""}
           onChange={e=>set(e.target.value===""?null:(num?Number(e.target.value):e.target.value))}/>
    <span className="f-h">{spec.help}</span></div>;
}

function Browser({initial,onPick,onClose,picker,onNative,busyNative}){
  const [d,setD]=useState(null),[p,setP]=useState(initial||""),[e,setE]=useState("");
  const load=useCallback(async q=>{
    try{setE("");const r=await api("/api/browse",{method:"POST",body:JSON.stringify({path:q})});
        setD(r);setP(r.path);}catch(x){setE(x.message);}},[]);
  useEffect(()=>{load(initial||"");},[load,initial]);

  // Clickable path segments — faster than retyping a long path.
  const crumbs=[];
  if(d?.path){
    const parts=d.path.split("/").filter(Boolean);
    crumbs.push({name:"/",path:"/"});
    let acc="";
    for(const seg of parts){acc+="/"+seg;crumbs.push({name:seg,path:acc});}
  }

  return (
    <div className="br">
      <div className="br-p">
        <input className="inp mono" value={p} onChange={e=>setP(e.target.value)}
               onKeyDown={e=>e.key==="Enter"&&load(p)} aria-label="Path"/>
        <button className="btn btn-s" onClick={()=>load(p)}>Go</button>
        {picker?.available&&
          <button className="btn btn-s" disabled={busyNative} onClick={onNative}
                  title={`Open the ${picker.tool} folder chooser on the server`}>
            {busyNative?<><span className="spin"/> Waiting…</>:<><Folder s={12}/> File manager</>}
          </button>}
        <button className="btn btn-s btn-pri" onClick={()=>{onPick(p);onClose();}}>Select</button>
      </div>

      {crumbs.length>0&&(
        <div style={{display:"flex",flexWrap:"wrap",alignItems:"center",gap:2,
                     padding:"7px 12px",borderBottom:"1px solid var(--line)",
                     background:"var(--raise)",fontSize:12}}>
          {crumbs.map((c,i)=>(
            <React.Fragment key={c.path}>
              {i>0&&<span style={{color:"var(--ink-3)"}}>/</span>}
              <button className="btn btn-q btn-s" style={{height:22,padding:"0 6px",
                      fontFamily:"var(--mono)",fontSize:11.5}}
                      onClick={()=>load(c.path)}>{c.name}</button>
            </React.Fragment>))}
        </div>)}

      {e&&<div style={{padding:"10px 14px",fontSize:12.5,color:"var(--bad)"}}>{e}</div>}
      <div className="br-l">
        {d?.parent&&<div className="br-i" onClick={()=>load(d.parent)}>
          <Folder s={14}/><span className="br-n" style={{color:"var(--ink-3)"}}>..</span></div>}
        {d?.entries?.length===0&&<div style={{padding:"14px",fontSize:12.5,color:"var(--ink-3)"}}>No subfolders</div>}
        {d?.entries?.map(x=>(
          <div key={x.path} className="br-i" onClick={()=>load(x.path)}
               onDoubleClick={()=>{onPick(x.path);onClose();}}>
            <Folder s={14}/><span className="br-n">{x.name}</span>
            {x.recordings>0&&<span className="f-h" style={{flex:"none"}}>{x.recordings} rec</span>}
            {x.is_run&&<span className={"pill "+(x.finished?"p-o":"p-w")}>
              <span className="dot"/>{x.finished?"run · finished":"run · in progress"}</span>}
          </div>))}
      </div>
      {picker&&!picker.available&&(
        <div style={{padding:"8px 12px",borderTop:"1px solid var(--line)"}} className="f-h">
          {picker.reason}
        </div>)}
    </div>
  );
}

function Row({run,onLog,onReset,wells,onWells,expanded}){
  const m=ST[run.status]||ST.waiting;
  const left=settleLeft(run.detail);
  const busy=run.status==="running"||run.status==="dispatched";
  const bad=run.status==="failed";
  const idx=bad?3:m.i;
  return (
    <div className="row">
      <div>
        <div className="row-id">{run.run}</div>
        <div className="row-job">
          <span className="dot" style={{background:run.job==="activity"?"var(--ok)":"var(--accent)"}}/>
          {run.job_label||(run.job==="activity"?"Activity scan":"Network")}
        </div>
      </div>
      <div className="row-mid">
        <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
          <span className={"pill "+m.c}>
            {busy?<span className="spin"/>:<span className={"dot"+(run.status==="waiting"?" dot-l":"")}/>}
            {m.l}</span>
          {/* A run can finish with wells failed. The pill still says Complete,
              because the job did complete, so the count carries the warning. */}
          <span className={"row-note"+(/\bfailed\b/i.test(run.detail||"")?" warn":"")}
                title={run.detail||""}>
            {run.detail||(run.returncode!=null?`exit code ${run.returncode}`:"")}</span>
        </div>
        {bad&&run.error&&<div className="row-why">{run.error}</div>}
        {busy&&<div className="bar-t"><div className="bar-i"/></div>}
        {left!=null&&run.status==="waiting"&&
          <div className="bar-t"><div className="bar-f" style={{width:`${Math.max(4,100-Math.min(100,left))}%`}}/></div>}
      </div>
      <div className="rail" aria-label={m.l}>
        {STAGES.map((s,i)=>(
          <React.Fragment key={s}>
            {i>0&&<span className="st-l" data-d={i<=idx}/>}
            <span className="st" data-s={bad&&i===3?"failed":i<idx?"done":i===idx?"active":"todo"}>
              <span className="st-d">{bad&&i===3?<Ex s={9}/>:i<idx?<Check s={9}/>:
                <span style={{width:4,height:4,borderRadius:"50%",background:"currentColor"}}/>}</span>
              <span className="st-n">{s}</span>
            </span>
          </React.Fragment>))}
      </div>
      <div style={{display:"flex",alignItems:"center",gap:"var(--s4)"}}>
        <div className="row-time">
          <div className="row-dur tnum">{dur(run.duration_s)}</div>
          <div className="row-ago">{ago(run.completed_at||run.started_at||run.dispatched_at||run.last_seen)}</div>
        </div>
        <div className="btns" style={{flexWrap:"nowrap"}}>
          {run.job!=="activity"&&
            <button className="btn btn-s" onClick={()=>onWells(run)} title="Per-well status from checkpoints">
              <Slide s={12}/> Wells</button>}
          {run.log&&<button className="btn btn-s" onClick={()=>onLog(run)}><Term s={12}/> Log</button>}
          <button className="btn btn-q btn-s btn-i" onClick={()=>onReset(run)} title="Reset this run"><Sync s={12}/></button>
        </div>
      </div>
    </div>
  );
}

/* Per-well status from the pipeline's own checkpoints.
   RunBlock has always rendered <Wells>, but the component was never defined,
   so opening Wells threw a ReferenceError and blanked the page. */
function Wells({rows,summary}){
  if(!rows?.length) return null;
  const s=summary||{};
  const cls=r=>r.status==="complete"?"p-o":r.status==="failed"?"p-b"
           :r.status==="running"?"p-a":"p-n";
  const when=t=>{if(!t)return"";const d=new Date(t.replace(" ","T"));
    return isNaN(d)?String(t).slice(0,19):ago(d.toISOString());};
  return (
    <div style={{padding:"0 24px 18px"}}>
      <div className="facts" style={{display:"flex",gap:18,margin:"2px 0 10px",
           fontSize:12.5,color:"var(--ink-2)",flexWrap:"wrap"}}>
        <span><b>{s.wells??rows.length}</b> wells</span>
        {s.complete!=null&&<span><b>{s.complete}</b> complete</span>}
        {!!s.failed&&<span style={{color:"var(--bad)"}}><b>{s.failed}</b> failed</span>}
        {!!s.running&&<span><b>{s.running}</b> running</span>}
      </div>
      <div className="panel" style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:12.5}}>
          <thead><tr>
            {["Well","Chip","Recording","Stage","Status","Updated"].map(h=>
              <th key={h} style={{textAlign:"left",padding:"7px 10px",fontSize:10.5,
                  textTransform:"uppercase",letterSpacing:".05em",color:"var(--ink-3)",
                  borderBottom:"1px solid var(--line)",whiteSpace:"nowrap"}}>{h}</th>)}
          </tr></thead>
          <tbody>
            {rows.map((r,i)=>(
              <React.Fragment key={(r.output_dir||"")+r.well+i}>
                <tr>
                  <td style={{padding:"6px 10px"}} className="mono">{r.well}</td>
                  <td style={{padding:"6px 10px"}} className="mono">{r.chip_id||"—"}</td>
                  <td style={{padding:"6px 10px"}} className="mono">{r.run_id||"—"}</td>
                  <td style={{padding:"6px 10px",whiteSpace:"nowrap"}}>{r.stage_name||r.stage}</td>
                  <td style={{padding:"6px 10px"}}>
                    <span className={"pill "+cls(r)}><span className="dot"/>{r.status}</span></td>
                  <td style={{padding:"6px 10px",whiteSpace:"nowrap",color:"var(--ink-3)"}}>
                    {when(r.last_updated)}</td>
                </tr>
                {r.error&&<tr><td colSpan={6} style={{padding:"0 10px 8px",color:"var(--bad)",
                  fontSize:12,whiteSpace:"pre-wrap",wordBreak:"break-word"}}>
                  {r.failed_stage?`${r.failed_stage}: `:""}{String(r.error).slice(0,400)}</td></tr>}
              </React.Fragment>))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RunBlock(props){
  const {run,wells,expanded}=props;
  return (
    <div style={{borderTop:"1px solid var(--line)"}}>
      <Row {...props}/>
      {expanded&&wells&&<Wells rows={wells.wells} summary={wells.summary}/>}
      {expanded&&wells&&!wells.wells?.length&&
        <div style={{padding:"0 24px 18px"}} className="f-h">
          No checkpoint files found yet for this run{wells.searched?.length
            ? <> under <span className="mono">{wells.searched.join(", ")}</span></>:null}.
        </div>}
    </div>
  );
}


/* ── Queue ─────────────────────────────────────────────────────────────── */
function QueuePanel({cfg,toast}){
  const [dir,setDir]=useState(cfg?.watch_dir||"");
  const [entries,setEntries]=useState(null);
  const [sel,setSel]=useState({});          // path -> true
  const [info,setInfo]=useState({});        // path -> inspect row
  const [rerun,setRerun]=useState(false);
  const [busy,setBusy]=useState(false);
  const [q,setQ]=useState(null);            // {batches, report}
  const timer=useRef(null);

  const load=useCallback(async path=>{
    try{
      const r=await api("/api/browse",{method:"POST",body:JSON.stringify({path})});
      setDir(r.path);
      const runs=(r.entries||[]).filter(x=>x.is_run);
      setEntries(runs);
      if(runs.length){
        const ins=await api("/api/queue/inspect",{method:"POST",
          body:JSON.stringify({folders:runs.map(x=>x.path)})});
        const by={}; (ins.folders||[]).forEach(f=>{by[f.path]=f;});
        setInfo(by);
      } else setInfo({});
    }catch(e){ setEntries([]); toast("Could not list folders",e.message,"error"); }
  },[toast]);

  useEffect(()=>{ if(cfg?.watch_dir) load(cfg.watch_dir); },[cfg?.watch_dir,load]);

  const poll=useCallback(async()=>{
    try{
      const d=await api("/api/queue"); setQ(d);
      const live=(d.batches||[]).some(b=>!b.finished);
      if(!live&&d.handoff?.state!=="running"){
        clearInterval(timer.current); timer.current=null;
      }
    }catch(e){ clearInterval(timer.current); timer.current=null; }
  },[]);
  useEffect(()=>()=>clearInterval(timer.current),[]);

  const chosen=Object.keys(sel).filter(k=>sel[k]);
  const doneCount=chosen.filter(p=>(info[p]?.jobs||[]).some(j=>j.already_done)).length;

  const start=async()=>{
    if(!chosen.length) return;
    setBusy(true);
    try{
      const r=await api("/api/queue",{method:"POST",
        body:JSON.stringify({folders:chosen,rerun})});
      toast("Queued",`${r.queued.length} job(s) started`,"ok");
      setSel({});
      if(!timer.current) timer.current=setInterval(poll,2000);
      poll();
    }catch(e){ toast("Nothing queued",e.message,"error"); }
    finally{ setBusy(false); }
  };

  const batch=(q?.batches||[]).slice(-1)[0];
  const rep=q?.handoff;

  return (
    <div>
      <div className="sec-h">
        <div className="sec-t">Queue</div>
        <div className="sec-d">Pick folders to analyse now — they run one at a time, in order</div>
      </div>
      <div className="panel"><div className="panel-b"
           style={{display:"flex",flexDirection:"column",gap:"var(--s5)"}}>

        <div className="btns" style={{alignItems:"center"}}>
          <span className="f-h">In</span>
          <code className="mono f-h" style={{wordBreak:"break-all"}}>{dir||"—"}</code>
          <div className="grow"/>
          <button className="btn btn-q btn-s" onClick={()=>load(dir)}>Refresh</button>
        </div>

        {entries===null
          ? <div className="f-h">Loading…</div>
          : entries.length===0
            ? <div className="note n-w"><span className="n-i"><Alert s={15}/></span>
                <div>No run folders with a recording were found here. Check the input
                     folder under Folders.</div></div>
            : <div className="qlist">
                {entries.map(x=>{
                  const row=info[x.path]||{};
                  const jobs=row.jobs||[];
                  const already=jobs.some(j=>j.already_done);
                  const on=!!sel[x.path];
                  return (
                    <label key={x.path} className={"qrow"+(on?" on":"")}>
                      <input type="checkbox" checked={on}
                             onChange={()=>setSel(v=>({...v,[x.path]:!v[x.path]}))}/>
                      <span className="qname">{x.name}</span>
                      <span className="qmeta">
                        {jobs.length
                          ? jobs.map(j=>j.label).join(" + ")
                          : (row.note||"no analysis applies")}
                      </span>
                      {already&&<span className="pill p-w">already analysed</span>}
                      {x.finished===false&&<span className="pill p-w">still copying</span>}
                    </label>
                  );
                })}
              </div>}

        <div style={{borderTop:"1px solid var(--line)",paddingTop:"var(--s4)",
                     display:"flex",flexDirection:"column",gap:"var(--s3)"}}>
          {doneCount>0&&
            <Switch id="q-rerun" checked={rerun} onChange={setRerun}
                    label={`Re-run ${doneCount} folder(s) already analysed`}
                    hint="Off by default — a Network analysis is a long GPU job."/>}
        </div>

        <div className="btns" style={{alignItems:"center"}}>
          <button className="btn btn-pri" disabled={busy||!chosen.length} onClick={start}>
            <Play s={13}/>{busy?"Queueing…":`Queue ${chosen.length||""} folder${chosen.length===1?"":"s"}`}
          </button>
          {batch&&!batch.finished&&
            <span className="f-h">Running — {batch.keys.length} job(s) in this batch</span>}
          {batch&&batch.finished&&rep?.state==="running"&&
            <span className="f-h">Analysis done — preparing the AI handoff…</span>}
        </div>

        {batch?.finished&&rep?.state==="done"&&rep.label===batch.id&&
          <div className="note n-a"><span className="n-i"><Check s={15}/></span>
            <div style={{minWidth:0,flex:1}}>AI handoff for this batch is ready. Run:
              <div style={{marginTop:8}}><Code text={rep.instruction}/></div></div></div>}
        {batch?.finished&&rep?.state==="error"&&
          <div className="note n-b"><span className="n-i"><Alert s={15}/></span>
            <div>The analysis finished, but the AI handoff failed: {rep.error}</div></div>}
      </div></div>
    </div>
  );
}

/* ── AI report handoff ───────────────────────────────────────────────── */
// The report is written by an AI assistant, not by this tool. This panel keeps
// the study's requirements (saved with the configuration) and prepares a
// handoff folder — skills.md + requirements + the result paths — to give it.
function AiHandoff({cfg,toast}){
  const [text,setText]=useState(cfg?.ai_requirements||"");
  const [saved,setSaved]=useState(cfg?.ai_requirements||"");
  const [auto,setAuto]=useState(cfg?.auto_handoff!==false);
  const [busy,setBusy]=useState(false);
  const [last,setLast]=useState(null);

  useEffect(()=>{(async()=>{try{
    const d=await api("/api/handoff"); if(d&&d.state) setLast(d);}catch(e){}})();},[]);

  const save=async(nextAuto=auto)=>{
    try{ await api("/api/requirements",{method:"POST",
           body:JSON.stringify({text,auto_handoff:nextAuto})});
         setSaved(text); return true; }
    catch(e){ toast("Requirements not saved",e.message,"error"); return false; }
  };
  const prepare=async()=>{
    setBusy(true);
    try{
      if(text!==saved && !(await save())) return;
      const r=await api("/api/handoff",{method:"POST",body:JSON.stringify({folders:[]})});
      setLast({state:"done",...r});
      toast("AI handoff ready",`${r.network_wells} network well(s), ${r.activity_runs} scan run(s)`,"ok");
    }catch(e){ toast("Handoff failed",e.message,"error"); }
    finally{ setBusy(false); }
  };
  const dirty=text!==saved;

  return (
    <div>
      <div className="sec-h">
        <div className="sec-t">AI report</div>
        <div className="sec-d">Requirements for the report, and the handoff folder to give Claude</div>
      </div>
      <div className="panel"><div className="panel-b"
           style={{display:"flex",flexDirection:"column",gap:"var(--s4)"}}>
        <div>
          <div className="f-l" style={{marginBottom:6}}>Requirements</div>
          <textarea className="inp" rows={7} value={text}
                    style={{height:"auto",padding:"10px 12px",resize:"vertical",lineHeight:1.5}}
                    placeholder={"What should the report show? e.g.\n• Compare KO vs WT burst rate and IBI at each DIV\n• Exclude wells with QC fail\n• Word document with one figure per metric"}
                    onChange={e=>setText(e.target.value)}/>
          <div className="f-h" style={{marginTop:6}}>
            Saved with the configuration and copied into every handoff. Defaults for
            anything not stated here come from <span className="mono">skills.md</span>.
          </div>
        </div>
        <Switch id="ai-auto" checked={auto}
                onChange={v=>{setAuto(v); save(v);}}
                label="Prepare a handoff automatically when a queued batch finishes"
                hint="Covers just the folders in that batch."/>
        <div className="btns" style={{alignItems:"center"}}>
          <button className="btn" disabled={!dirty} onClick={()=>save()}>
            {dirty?"Save requirements":"Saved"}</button>
          <button className="btn btn-pri" disabled={busy} onClick={prepare}>
            {busy?"Preparing…":"Prepare handoff for all results"}</button>
        </div>
        {last?.state==="done"&&last.prompt&&
          <div className="note n-a"><span className="n-i"><Check s={15}/></span>
            <div style={{minWidth:0,flex:1}}>
              <div>Handoff ready — {last.network_wells} network well(s), {last.activity_runs} scan
                run(s). In a terminal on this server, run:</div>
              <div style={{marginTop:8}}><Code text={last.instruction}/></div>
              <div className="f-h" style={{marginTop:6}}>The report will be written to{" "}
                <span className="mono" style={{wordBreak:"break-all"}}>{last.report_dir}</span></div>
            </div></div>}
        {last?.state==="error"&&
          <div className="note n-b"><span className="n-i"><Alert s={15}/></span>
            <div>The handoff could not be prepared: {last.error}</div></div>}
      </div></div>
    </div>
  );
}

/* ── App ───────────────────────────────────────────────────────────────── */
function App(){
  const [schema,setSchema]=useState(null);
  const [cfg,setCfg]=useState(null);
  const [status,setStatus]=useState(null);
  const [fatal,setFatal]=useState("");
  const [preview,setPreview]=useState(null);
  const [browsing,setBrowsing]=useState(null);
  const [log,setLog]=useState(null);
  const [q,setQ]=useState("");
  const [open,setOpen]=useState({});
  const [theme,setTheme]=useState(()=>localStorage.getItem("mea-theme")||"auto");
  const [toasts,setToasts]=useState([]);
  const [busy,setBusy]=useState(false);
  const [act,setAct]=useState([]);
  const [follow,setFollow]=useState(true);
  const [showCfg,setShowCfg]=useState(true);
  /* Never leave the operator stopped with no way back to setup: the only
     control that reveals it is hidden while running, so a panel collapsed
     before a run could not be reopened after one.

     Must sit with the other hooks, above App's early returns. Placing it
     lower meant the first render (no config yet) bailed out before it and
     later renders ran it — "rendered more hooks than during the previous
     render", which blanks the page. Reads status directly because the
     `running` const is declared further down. */
  useEffect(()=>{if(!status?.running)setShowCfg(true);},[status?.running]);
  const [picker,setPicker]=useState(null);
  const [pyCheck,setPyCheck]=useState(null);
  const [busyNative,setBusyNative]=useState(false);
  const [clearing,setClearing]=useState(false);
  const [wells,setWells]=useState({});      // run key -> checkpoint payload
  const [openWells,setOpenWells]=useState({});
  const tid=useRef(0), seq=useRef(0), openWellsRef=useRef({});

  const toast=useCallback((t,m,k="info")=>{const id=++tid.current;
    setToasts(x=>[...x,{id,t,m,k}]);
    setTimeout(()=>setToasts(x=>x.filter(y=>y.id!==id)),k==="error"?9000:4200);},[]);

  useEffect(()=>{openWellsRef.current=openWells;},[openWells]);

  useEffect(()=>{document.documentElement.dataset.theme=theme;
    localStorage.setItem("mea-theme",theme);},[theme]);

  useEffect(()=>{(async()=>{try{
    const s=await api("/api/schema"),c=await api("/api/config");
    setSchema(s);setCfg(c);
    const o={};s.groups.forEach((g,i)=>o[g.group]=!g.group.toLowerCase().includes("advanced"));
    setOpen(o);
    try{ setPicker(await api("/api/picker")); }catch(e){ setPicker({available:false}); }
  }catch(e){setFatal(e.message);}})();},[]);

  // One poll at a time: a slow answer used to let polls pile up behind each
  // other. Nothing is polled while the tab is hidden, and the per-well
  // checkpoints (the expensive read) refresh every fifth tick, not every tick.
  const polling=useRef(false), tick=useRef(0);
  const refresh=useCallback(async(force)=>{
    if(polling.current) return;
    if(!force&&typeof document!=="undefined"&&document.hidden) return;
    polling.current=true;
    try{
      const wellsDue=force||(tick.current++%5===0);
      const keys=wellsDue?Object.keys(openWellsRef.current||{}).filter(k=>openWellsRef.current[k]):[];
      await Promise.all([
        api("/api/status").then(s=>{setStatus(s);setShowCfg(v=>s.running?false:v);}).catch(()=>{}),
        api(`/api/logs?since=${seq.current}`).then(d=>{
          if(d.lines?.length){seq.current=d.last_seq;setAct(a=>[...a,...d.lines].slice(-400));}}).catch(()=>{}),
        ...keys.map(k=>api(`/api/runs/checkpoints?path=${encodeURIComponent(k)}`)
          .then(d=>setWells(w=>({...w,[k]:d}))).catch(()=>{})),
      ]);
    }finally{ polling.current=false; }
  },[]);
  useEffect(()=>{
    refresh(true);
    const t=setInterval(()=>refresh(false),2000);
    const vis=()=>{ if(!document.hidden) refresh(true); };
    document.addEventListener("visibilitychange",vis);
    return()=>{clearInterval(t);document.removeEventListener("visibilitychange",vis);};
  },[refresh]);

  useEffect(()=>{
    if(!log?.path)return;
    const live=(status?.runs||[]).some(r=>r.log===log.path&&(r.status==="running"||r.status==="dispatched"));
    if(!live)return;
    const t=setInterval(async()=>{try{
      const d=await api(`/api/runs/log?path=${encodeURIComponent(log.path)}`);
      setLog(l=>l&&l.path===log.path?{...l,lines:d.lines}:l);}catch(e){}},3000);
    return()=>clearInterval(t);
  },[log?.path,status]);

  const payload=useCallback(()=>({
    watch_dir:cfg.watch_dir, driver_options:cfg.driver_options, h5_glob:cfg.h5_glob,
    assay_subfolder:cfg.assay_subfolder,
    run_network:!!cfg.run_network, run_activity:!!cfg.run_activity,
    activity_subfolder:cfg.activity_subfolder, activity_output_dir:cfg.activity_output_dir||"",
    activity_active_hz:Number(cfg.activity_active_hz), activity_figures:!!cfg.activity_figures,
    max_concurrent_network:Number(cfg.max_concurrent_network)||1,
    max_concurrent_activity:Number(cfg.max_concurrent_activity)||1,
    gpu_cooldown_seconds:Number(cfg.gpu_cooldown_seconds)||0,
    queue_poll_seconds:Number(cfg.queue_poll_seconds)||1,
    settle_seconds:Number(cfg.settle_seconds), poll_seconds:Number(cfg.poll_seconds),
    require_finished_marker:!!cfg.require_finished_marker,
    skip_settle_for_existing:!!cfg.skip_settle_for_existing,
    driver_python:cfg.driver_python||"", logs_in_output:cfg.logs_in_output!==false,
    stage_locally:!!cfg.stage_locally, scratch_dir:cfg.scratch_dir||"",
    stage_min_free_gb:Number(cfg.stage_min_free_gb)||200,
    dry_run:!!cfg.dry_run,
    ai_requirements:cfg.ai_requirements||"", auto_handoff:cfg.auto_handoff!==false,
  }),[cfg]);

  const act_=useCallback(async(fn,t,m)=>{setBusy(true);
    try{await fn();if(t)toast(t,m,"success");refresh();}
    catch(e){toast("Something went wrong",e.message,"error");}
    finally{setBusy(false);}},[toast,refresh]);

  if(fatal) return (
    <div className="shell"><div className="page" style={{maxWidth:640,paddingTop:96}}>
      <div className="panel">
        <div className="panel-h"><div>
          <div className="panel-t" style={{color:"var(--bad)"}}>Cannot reach the backend</div>
          <div className="panel-d">This page is the interface only — the Python server reads
            folders and runs the pipeline, so it must serve this page.</div>
        </div></div>
        <div className="panel-b"><Code text={fatal}/></div>
        <div className="panel-b" style={{paddingTop:0}}>
          <button className="btn btn-pri" onClick={()=>location.reload()}><Sync s={13}/> Retry</button>
        </div>
      </div>
    </div></div>);

  if(!schema||!cfg) return (
    <div className="shell"><div className="page"><div className="stack">
      <div className="skel" style={{height:38,width:280}}/>
      <div className="metrics">{[0,1,2,3].map(i=>(
        <div className="metric" key={i}>
          <div className="skel" style={{height:12,width:"55%"}}/>
          <div className="skel" style={{height:30,width:"38%",marginTop:8}}/>
        </div>))}</div>
      <div className="panel"><div className="panel-b">
        <div className="skel" style={{height:16,width:190}}/>
        <div className="skel" style={{height:38,marginTop:16}}/>
        <div className="skel" style={{height:38,marginTop:10}}/>
      </div></div>
    </div></div></div>);

  const running=!!status?.running;
  const setO=(k,v)=>setCfg(c=>({...c,driver_options:{...c.driver_options,[k]:v}}));
  const setT=(k,v)=>setCfg(c=>({...c,[k]:v}));
  const counts=status?.counts||{}, runs=status?.runs||[];
  const failedCount=runs.filter(r=>r.status==="failed").length;

  const save   =()=>act_(async()=>{await api("/api/config",{method:"POST",body:JSON.stringify(payload())});},"Configuration saved");
  /* A start resumes jobs a previous run left unfinished. Doing that
     silently made the whole previous queue reappear with no explanation,
     so it is stated and can be declined. */
  const start  =()=>{
    const n=status?.resumable||0;
    if(n&&!window.confirm(`${n} job(s) from a previous run were left unfinished `
      +"and will be picked up again.\n\nFinished wells are skipped, so this repeats "
      +"only unfinished work. Clear them first if you want a fresh start.")) return;
    act_(async()=>{
      await api("/api/config",{method:"POST",body:JSON.stringify(payload())});
      await api("/api/watcher/start",{method:"POST"});},
      "Watcher started",cfg.dry_run?"Dry run — nothing will be launched.":
        n?`Resuming ${n} unfinished job(s); new folders will be analyzed too.`
         :"Completed runs will be analyzed automatically.");
  };
  const stop   =()=>act_(async()=>{await api("/api/watcher/stop",{method:"POST"});},
                    "Stopped scanning","Jobs already running carry on. Use Stop &amp; cancel to end them.");
  /* Stop on its own leaves drivers running for hours, which left the
     terminal as the only way to actually stop work — and killing a
     driver by hand orphans its per-well subprocesses. */
  const cancel =()=>{
    const n=(status?.counts?.running||0)+(status?.counts?.dispatched||0);
    if(!window.confirm(`Stop scanning and cancel ${n} job(s) in flight?\n\n`
      +"Wells already finished keep their checkpoints, so re-running repeats "
      +"only the well that was in progress.")) return;
    act_(async()=>{await api("/api/watcher/stop?cancel_running=true",{method:"POST"});},
         "Stopped","Running jobs were cancelled.");
  };
  const doPrev =()=>act_(async()=>{setPreview(await api("/api/preview",{method:"POST",body:JSON.stringify(payload())}));});
  const onReset=r=>act_(async()=>{await api("/api/runs/reset",{method:"POST",body:JSON.stringify({path:r.path})});},
                    "Run reset",`${r.run} will be processed again.`);
  const onLog  =r=>act_(async()=>{const d=await api(`/api/runs/log?path=${encodeURIComponent(r.log)}`);
                    setLog({run:r.run,lines:d.lines,path:r.log});});

  // Clearing runs one at a time is unusable after a failed batch, so offer the
  // two cases that actually come up: forget the failures, or start fresh.
  const onClearAll=async which=>{
    const all=(status?.runs)||[];
    const n=which==="failed"?all.filter(r=>r.status==="failed").length:all.length;
    if(which==="all"&&n>0&&!window.confirm(
        `Forget all ${n} run(s)?\n\nAnalysed output on disk is not touched — the `
        +`watcher will simply treat these folders as unseen.`)) return;
    setClearing(true);
    try{
      const r=await api("/api/runs/reset-all",{method:"POST",
        body:JSON.stringify({which})});
      toast("Cleared",`${r.cleared} run(s) forgotten`
        +(r.skipped?.length?` · ${r.skipped.length} still running, left alone`:""),"ok");
      refresh();
    }catch(e){ toast("Could not clear",e.message,"error"); }
    finally{ setClearing(false); }
  };
  const testPython=()=>act_(async()=>{
    setPyCheck(await api("/api/driver-python",{method:"POST",
      body:JSON.stringify({python:cfg.driver_python||""})}));
  });

  const pickNative=(start,title,apply)=>{
    setBusyNative(true);
    act_(async()=>{
      try{
        const d=await api("/api/picker",{method:"POST",
          body:JSON.stringify({start:start||"",title})});
        if(!d.cancelled&&d.path) apply(d.path);
      } finally { setBusyNative(false); }
    });
  };

  const onWells=r=>{
    const isOpen=!!openWells[r.path];
    setOpenWells(o=>({...o,[r.path]:!isOpen}));
    if(isOpen) return;
    act_(async()=>{
      const d=await api(`/api/runs/checkpoints?path=${encodeURIComponent(r.path)}`);
      setWells(w=>({...w,[r.path]:d}));
    });
  };

  const ql=q.trim().toLowerCase();
  const groups=schema.groups.map(g=>({...g,fields:g.fields.filter(f=>!ql||
    f.key.toLowerCase().includes(ql)||f.flag.toLowerCase().includes(ql)||
    (f.help||"").toLowerCase().includes(ql))})).filter(g=>g.fields.length);
  const modified=Object.entries(cfg.driver_options).filter(([k,v])=>{
    const s=schema.groups.flatMap(g=>g.fields).find(f=>f.key===k);
    return s&&v!==s.default&&v!==null&&v!==""&&v!==false;}).length;

  const active=(counts.running||0)+(counts.dispatched||0);
  const heroTitle = running
    ? (active?`Analyzing ${active} job${active>1?"":""}`:"Watching for recordings")
    : (runs.length?"Watcher stopped":"Ready to watch");
  const jobsOn=[cfg.run_network&&"Network",cfg.run_activity&&"Activity scan"].filter(Boolean);

  return (
    <div className="shell">
      <h1 className="sr">MEA pipeline control</h1>

      <div className="bar"><div className="bar-in">
        <div className="mark"><Wave s={15}/></div>
        <div className="wordmark">MEA Pipeline</div>
        <div className="grow"/>
        <span className={"pill "+(running?"p-o":"p-n")}>
          <span className={"dot"+(running?" dot-l":"")}/>
          {running?(cfg.dry_run?"Dry run":"Watching"):"Stopped"}
        </span>
        <button className="btn btn-q btn-i" onClick={()=>setTheme(t=>t==="dark"?"light":"dark")}
                aria-label="Toggle theme">{theme==="dark"?<Sun s={15}/>:<Moon s={15}/>}</button>
        {running
          ? <><button className="btn" onClick={stop} disabled={busy}><Stop s={12}/> Stop scanning</button>
            <button className="btn btn-dan" onClick={cancel} disabled={busy}><Stop s={12}/> Stop &amp; cancel</button></>
          : <button className="btn btn-pri" onClick={start} disabled={busy}><Play s={12}/> Start watching</button>}
      </div></div>

      <div className="page"><div className="stack">

        <div className="hero">
          <div>
            <div className="hero-h">{heroTitle}</div>
            <div className="hero-sub">
              {cfg.watch_dir
                ? <>Monitoring <span className="mono">{cfg.watch_dir}</span>
                    {jobsOn.length?<> · {jobsOn.join(" + ")}</>:null}</>
                : "No input folder set yet"}
            </div>
          </div>
          <div className="btns">
            {!running&&<button className="btn" onClick={()=>setShowCfg(s=>!s)}>
              <Slide s={13}/> {showCfg?"Hide setup":"Show setup"}</button>}
            <button className="btn" onClick={refresh}><Sync s={13}/> Refresh</button>
          </div>
        </div>

        {cfg.env?.in_container&&(
          <div className="note n-a"><span className="n-i"><Info s={15}/></span>
            <div>Running in a container. Mounted paths are identical inside and out
              {cfg.env.suggested_input&&<> — input <code>{cfg.env.suggested_input}</code> (read-only)</>}
              {cfg.env.suggested_output&&<>, output <code>{cfg.env.suggested_output}</code></>}.
              The input path must be the folder <b>containing</b> your run folders, not a single run.
            </div></div>)}

        <div className="metrics">
          {[{k:"waiting",l:"Waiting",i:<Clock s={12}/>},
            {k:"running",l:"Analyzing",i:<Wave s={12}/>},
            {k:"done",l:"Complete",i:<Check s={12}/>},
            {k:"failed",l:"Failed",i:<Alert s={12}/>}].map(s=>(
            <div className="metric" key={s.k}
                 data-live={s.k==="running"&&(counts.running||0)>0}
                 data-bad={s.k==="failed"&&(counts.failed||0)>0}>
              <div className="metric-k">{s.i}{s.l}</div>
              <div className="metric-v tnum">{counts[s.k]||0}</div>
            </div>))}
        </div>

        <div>
          <div className="sec-h">
            <div className="sec-t">Runs</div>
            <div className="sec-d">
              {running?"Scanning for completed recordings":"Watcher is stopped"}
              {status?.scanning
                ? " · reading the input folder…"
                : (status?.candidates?.length?` · ${status.candidates.length} folder${status.candidates.length>1?"s":""} in scope`:"")}
            </div>
            <div className="grow"/>
            {failedCount>0&&
              <button className="btn btn-q btn-s" disabled={clearing}
                      onClick={()=>onClearAll("failed")}>
                Clear {failedCount} failed
              </button>}
            {runs.length>0&&
              <button className="btn btn-q btn-s" disabled={clearing}
                      onClick={()=>onClearAll("all")}>
                Clear all
              </button>}
          </div>
          <div className="panel">
            {runs.length===0
              ? <div className="empty">
                  <div className="empty-i"><Inbox s={21}/></div>
                  <div className="empty-t">No runs yet</div>
                  <div className="empty-d">
                    {status?.candidates?.length
                      ? <>Found <b>{status.candidates.join(", ")}</b> in the input folder.
                          Start the watcher to begin checking whether they have finished copying.</>
                      : <>Set an input folder below, then start the watcher. Run folders containing
                          a recording will appear here as they are detected.</>}
                  </div>
                </div>
              : <div className="rows">{runs.map(r=>
                  <RunBlock key={r.path} run={r} onLog={onLog} onReset={onReset}
                            onWells={onWells} wells={wells[r.path]}
                            expanded={!!openWells[r.path]}/>)}</div>}
          </div>
        </div>

        <QueuePanel cfg={cfg} toast={toast}/>

        <AiHandoff cfg={cfg} toast={toast}/>

        {log&&(
          <div>
            <div className="sec-h">
              <div className="sec-t">Pipeline log</div>
              <div className="sec-d">{log.run} · last {log.lines.length} lines
                {(status?.runs||[]).some(r=>r.log===log.path&&(r.status==="running"||r.status==="dispatched"))&&" · following live"}</div>
              <div className="grow"/>
              <button className="btn btn-q btn-s btn-i" onClick={()=>setLog(null)} aria-label="Close"><Ex s={14}/></button>
            </div>
            <div className="panel"><div className="panel-b"><Code text={log.lines.join("\n")} scroll/></div></div>
          </div>)}

        <div>
          <div className="sec-h">
            <div className="sec-t">Activity</div>
            <div className="sec-d">Live watcher output — detection, settle windows, dispatches</div>
          </div>
          <div className="panel"><div className="panel-b">
            <LiveLog lines={act} follow={follow} setFollow={setFollow} onClear={()=>setAct([])}/>
          </div></div>
        </div>

        {running&&(
          <div className="panel"><div className="strip">
            <span>Settle <b className="tnum">{cfg.settle_seconds}s</b></span>
            <span>Poll <b className="tnum">{cfg.poll_seconds}s</b></span>
            <span>Analyses <b>{jobsOn.join(" + ")||"none"}</b></span>
            <span>Output <b className="mono">{cfg.driver_options.output_dir||"—"}</b></span>
            <div className="grow"/>
            <span style={{color:"var(--ink-3)"}}>Stop the watcher to edit</span>
          </div></div>)}

        {showCfg&&!running&&(<>
          <div>
            <div className="sec-h">
              <div className="sec-t">Setup</div>
              <div className="sec-d">Where recordings arrive, and what runs when they do</div>
            </div>
            <div className="grid2">
              <div className="panel">
                <div className="panel-h"><div><div className="panel-t">Folders</div></div></div>
                <div className="panel-b" style={{display:"flex",flexDirection:"column",gap:"var(--s5)"}}>
                  <div className="f">
                    <label className="f-l" htmlFor="in">Input</label>
                    <div className="f-row">
                      <input id="in" className="inp mono" value={cfg.watch_dir}
                             placeholder="/home/user/MEA" onChange={e=>setT("watch_dir",e.target.value)}/>
                      <button className="btn" onClick={()=>setBrowsing(browsing==="in"?null:"in")}>
                        <Folder s={13}/></button>
                    </div>
                    <span className="f-h">Folder containing run folders such as <code className="mono">000041</code>.</span>
                    {browsing==="in"&&<Browser initial={cfg.watch_dir} onClose={()=>setBrowsing(null)}
                                               onPick={p=>setT("watch_dir",p)}
                                               picker={picker} busyNative={busyNative}
                                               onNative={()=>pickNative(cfg.watch_dir,"Select input folder",
                                                 p=>setT("watch_dir",p))}/>}
                  </div>
                  <div className="f">
                    <label className="f-l" htmlFor="out">Output</label>
                    <div className="f-row">
                      <input id="out" className="inp mono" value={cfg.driver_options.output_dir??""}
                             placeholder="/home/user/AnalyzedData"
                             onChange={e=>setO("output_dir",e.target.value||null)}/>
                      <button className="btn" onClick={()=>setBrowsing(browsing==="out"?null:"out")}>
                        <Folder s={13}/></button>
                    </div>
                    <span className="f-h">Passed as <code className="mono">--output-dir</code>.</span>
                    {browsing==="out"&&<Browser initial={cfg.driver_options.output_dir||""} onClose={()=>setBrowsing(null)}
                                                onPick={p=>setO("output_dir",p)}
                                                picker={picker} busyNative={busyNative}
                                                onNative={()=>pickNative(cfg.driver_options.output_dir,"Select output folder",
                                                  p=>setO("output_dir",p))}/>}
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-h"><div><div className="panel-t">Detection</div></div></div>
                <div className="panel-b">
                  <div className="grid2">
                    <div className="f">
                      <label className="f-l" htmlFor="set">Settle window</label>
                      <input id="set" className="inp tnum" type="number" min="1"
                             value={cfg.settle_seconds} onChange={e=>setT("settle_seconds",e.target.value)}/>
                      <span className="f-h">Seconds of no change before a run counts as complete.</span>
                    </div>
                    <div className="f">
                      <label className="f-l" htmlFor="pol">Poll interval</label>
                      <input id="pol" className="inp tnum" type="number" min="1"
                             value={cfg.poll_seconds} onChange={e=>setT("poll_seconds",e.target.value)}/>
                      <span className="f-h">How often the folder is checked.</span>
                    </div>
                  </div>
                  <div className="sep"/>
                  <Switch id="mk" checked={cfg.require_finished_marker}
                          onChange={v=>setT("require_finished_marker",v)}
                          label="Require MaxWell completion marker"
                          hint="Also wait for finished= in mxassay.metadata."/>
                  <Switch id="skip" checked={cfg.skip_settle_for_existing}
                          onChange={v=>setT("skip_settle_for_existing",v)}
                          label="Folders already here are ready"
                          hint="Start analyzing existing folders immediately, skipping the settle window. Use when the copy already finished. Folders arriving later still wait the full window."/>
                  <Switch id="dry" checked={cfg.dry_run} onChange={v=>setT("dry_run",v)}
                          label="Dry run"
                          hint="Detect and record the command, but never launch."/>
                  {cfg.dry_run&&<div className="note n-w" style={{marginTop:"var(--s3)"}}>
                    <span className="n-i"><Info s={15}/></span>
                    <div>Runs will stop at <b>Detected</b>. Turn this off and save to run for real —
                      already-detected runs are cleared automatically.</div></div>}
                </div>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-h"><div>
              <div className="panel-t">Analyses</div>
              <div className="panel-d">Independent jobs — separate outputs, separate status</div>
            </div></div>
            <div className="panel-b">
              <div className="grid2">
                <Switch id="net" checked={cfg.run_network} onChange={v=>setT("run_network",v)}
                        label="Network — spike sorting"
                        hint="Kilosort4, curation, burst analysis. Needs a GPU; hours per chip."/>
                <Switch id="ac" checked={cfg.run_activity} onChange={v=>setT("run_activity",v)}
                        label="Activity scan — whole-array maps"
                        hint="Activity maps, QC metrics, network bursts. CPU only; seconds per chip."/>
              </div>
              {cfg.run_network&&(<>
                <div className="sep"/>
                <div className="f">
                  <label className="f-l" htmlFor="dpy">Pipeline interpreter</label>
                  <div className="f-row">
                    <input id="dpy" className="inp mono"
                           placeholder="(auto-detect — the environment MEA-Analysis is installed in)"
                           value={cfg.driver_python??""}
                           onChange={e=>setT("driver_python",e.target.value)}/>
                    <button className="btn" onClick={testPython} disabled={busy}>Test</button>
                  </div>
                  <span className="f-h">
                    Must have the pipeline's dependencies (pandas, spikeinterface, kilosort, torch).
                    This tool's own virtualenv does not — launching the driver with it fails at
                    <code className="mono"> import pandas</code>.
                  </span>
                  {pyCheck&&(
                    <div className={"note "+(pyCheck.ok?"n-a":"n-b")} style={{marginTop:8}}>
                      <span className="n-i">{pyCheck.ok?<Check s={15}/>:<Alert s={15}/>}</span>
                      <div style={{minWidth:0}}>
                        <div><b className="mono">{pyCheck.python}</b>
                          {pyCheck.version&&<> · Python {pyCheck.version}</>}
                          {pyCheck.source&&<> · {pyCheck.source}</>}</div>
                        {pyCheck.ok
                          ? <div style={{marginTop:3}}>All pipeline dependencies present.</div>
                          : <div style={{marginTop:3}}>
                              Missing: <b>{(pyCheck.missing||[]).join(", ")||pyCheck.error}</b>.
                              Set the path to the environment MEA-Analysis runs in.
                            </div>}
                      </div>
                    </div>)}
                </div>
              </>)}

              {cfg.run_activity&&(<>
                <div className="sep"/>
                <div className="grid2">
                  <div className="f">
                    <label className="f-l" htmlFor="ao">Activity output</label>
                    <input id="ao" className="inp mono" placeholder="(defaults to <output>/ActivityScan)"
                           value={cfg.activity_output_dir??""}
                           onChange={e=>setT("activity_output_dir",e.target.value)}/>
                    <span className="f-h">Kept separate from spike-sorting output.</span>
                  </div>
                  <div className="grid2">
                    <div className="f">
                      <label className="f-l" htmlFor="ah">Active threshold</label>
                      <input id="ah" className="inp tnum" type="number" step="0.01" min="0"
                             value={cfg.activity_active_hz}
                             onChange={e=>setT("activity_active_hz",e.target.value)}/>
                      <span className="f-h">Hz</span>
                    </div>
                    <div className="f">
                      <label className="f-l" htmlFor="as">Assay folder</label>
                      <input id="as" className="inp mono" value={cfg.activity_subfolder??""}
                             onChange={e=>setT("activity_subfolder",e.target.value)}/>
                      <span className="f-h">Holds the scans</span>
                    </div>
                  </div>
                </div>
                <Switch id="af" checked={cfg.activity_figures} onChange={v=>setT("activity_figures",v)}
                        label="Generate figures"
                        hint="Activity maps, rasters, connectivity, plate overview."/>
              </>)}
              <div className="sep"/>
              <div className="grid2">
                <div className="f">
                  <label className="f-l" htmlFor="cn">Concurrent Network jobs</label>
                  <input id="cn" className="inp tnum" type="number" min="1" max="8"
                         value={cfg.max_concurrent_network??1}
                         onChange={e=>setT("max_concurrent_network",e.target.value)}/>
                  <span className="f-h">Extra jobs queue rather than starting. Whether more than
                    one fits depends on the card: measure peak VRAM during the sorting phase with
                    <code> nvidia-smi</code> and allow that much per job. Sorting also leaves the GPU
                    idle much of the time while it waits on data, so a second job often fills those
                    gaps rather than competing — and overlaps its own CPU-only analyzer stage with
                    the first job's GPU work.</span>
                </div>
                <div className="f">
                  <label className="f-l" htmlFor="ca">Concurrent Activity jobs</label>
                  <input id="ca" className="inp tnum" type="number" min="1" max="16"
                         value={cfg.max_concurrent_activity??2}
                         onChange={e=>setT("max_concurrent_activity",e.target.value)}/>
                  <span className="f-h">CPU only, so this can be higher. Never waits behind
                    spike sorting.</span>
                </div>
                <div className="f">
                  <label className="f-l" htmlFor="cool">GPU cooldown</label>
                  <input id="cool" className="inp tnum" type="number" min="0" max="600"
                         value={cfg.gpu_cooldown_seconds??5}
                         onChange={e=>setT("gpu_cooldown_seconds",e.target.value)}/>
                  <span className="f-h">Seconds to wait before starting the next queued Network
                    job. CUDA memory is not always released the moment a process exits.</span>
                </div>
                <div className="f">
                  <label className="f-l" htmlFor="qp">Queue check interval</label>
                  <input id="qp" className="inp tnum" type="number" min="1" max="120"
                         value={cfg.queue_poll_seconds??2}
                         onChange={e=>setT("queue_poll_seconds",e.target.value)}/>
                  <span className="f-h">How often a queued job looks for a free slot.</span>
                </div>
              </div>
              <div className="sep"/>
              <Switch id="lio" checked={cfg.logs_in_output!==false}
                      onChange={v=>setT("logs_in_output",v)}
                      label="Write logs beside the results"
                      hint="Per-run logs go to <output>/orchestration_logs/ as well, so the log lives with the output it describes. Falls back to the work directory if that is not writable."/>
              <div className="sep"/>
              <Switch id="stg" checked={!!cfg.stage_locally}
                      onChange={v=>setT("stage_locally",v)}
                      label="Run against local disk, then copy results"
                      hint="Spike sorting writes a float32 copy of each recording and reads it back many times — tens of GB per well. On a network output directory that traffic, not the GPU, decides how long a run takes. Input and final output paths are unchanged; only the working files move."/>
              {cfg.stage_locally&&<>
                <div className="grid2" style={{marginTop:"var(--s3)"}}>
                  <div className="f">
                    <label className="f-l" htmlFor="scr">Scratch directory</label>
                    <input id="scr" className="inp" type="text" spellCheck="false"
                           placeholder="<work dir>/scratch"
                           value={cfg.scratch_dir||""}
                           onChange={e=>setT("scratch_dir",e.target.value)}/>
                    <span className="f-h">A local disk with room to spare. Leave blank to use the
                      work directory — check that it is not the same volume you are short of space on.</span>
                  </div>
                  <div className="f">
                    <label className="f-l" htmlFor="smf">Keep free (GB)</label>
                    <input id="smf" className="inp tnum" type="number" min="0" max="10000"
                           value={cfg.stage_min_free_gb??200}
                           onChange={e=>setT("stage_min_free_gb",e.target.value)}/>
                    <span className="f-h">Staging is skipped, and the job runs against the output
                      directory instead, if it would take the volume below this. Never fills a disk
                      to run faster.</span>
                  </div>
                </div>
                <div className="note n-b" style={{marginTop:"var(--s3)"}}>
                  <span className="n-i"><Alert s={15}/></span>
                  <div>Results for a folder appear in the output directory when that folder
                    finishes, rather than well by well. Per-well progress and logs are unaffected.</div>
                </div>
              </>}
              {!cfg.run_network&&!cfg.run_activity&&
                <div className="note n-b" style={{marginTop:"var(--s3)"}}>
                  <span className="n-i"><Alert s={15}/></span>
                  <div>Enable at least one analysis, or nothing will run.</div></div>}
            </div>
          </div>

          <div>
            <div className="sec-h">
              <div className="sec-t">Pipeline options</div>
              <div className="sec-d">
                Passed to run_pipeline_driver.py · {modified} changed from default
              </div>
            </div>
            <div className="panel"><div className="panel-b">
              <div className="opt-bar">
                <div className="srch">
                  <span className="srch-i"><Search s={14}/></span>
                  <input className="inp" placeholder="Search options…" value={q}
                         onChange={e=>setQ(e.target.value)} aria-label="Search options"/>
                </div>
                {q&&<button className="btn btn-q btn-s" onClick={()=>setQ("")}>Clear</button>}
              </div>
              {groups.length===0
                ? <div className="empty" style={{padding:"36px 0"}}>
                    <div className="empty-t">No matching options</div>
                    <div className="empty-d">Try a different search term.</div></div>
                : <div className="groups">{groups.map(g=>{
                    const o=ql?true:!!open[g.group];
                    return (
                      <div className="grp" key={g.group}>
                        <button className="grp-h" onClick={()=>setOpen(x=>({...x,[g.group]:!x[g.group]}))}
                                aria-expanded={o}>
                          <span className="chev" data-o={o}><Chev s={12}/></span>
                          <span className="grp-n">{g.group}</span>
                          <span className="grp-c">{g.fields.length}</span>
                        </button>
                        {o&&<div className="grp-b">{g.fields.map(f=>
                          <Field key={f.key} spec={f} value={cfg.driver_options[f.key]} onChange={setO}/>)}</div>}
                      </div>);})}</div>}
            </div></div>
          </div>

          <div className="panel">
            <div className="panel-b" style={{display:"flex",gap:"var(--s2)",flexWrap:"wrap",alignItems:"center"}}>
              <button className="btn btn-pri" onClick={start} disabled={busy}>
                <Play s={12}/> Start watching</button>
              <button className="btn" onClick={save} disabled={busy}>Save configuration</button>
              <button className="btn" onClick={doPrev} disabled={busy}><Term s={13}/> Preview command</button>
            </div>
          </div>

          {preview&&(
            <div>
              <div className="sec-h">
                <div className="sec-t">Command preview</div>
                <div className="sec-d">
                  {preview.detected_runs?.length
                    ? <>For <b>{preview.example_run}</b> · detected: {preview.detected_runs.join(", ")}</>
                    : "No run folders detected yet"}
                </div>
              </div>
              <div className="panel"><div className="panel-b"
                   style={{display:"flex",flexDirection:"column",gap:"var(--s5)"}}>
                {(preview.commands?.length?preview.commands:
                  [{job:"network",job_label:"Command",command:preview.command}]).map(c=>(
                  <div key={c.job}>
                    <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:8}}>
                      <span className="dot" style={{background:c.job==="activity"?"var(--ok)":"var(--accent)"}}/>
                      <span style={{fontSize:12.5,fontWeight:600,letterSpacing:"-.01em"}}>{c.job_label}</span>
                    </div>
                    <Code text={c.command}/>
                  </div>))}
                {preview.commands&&preview.commands.length===0&&
                  <div className="f-h">No analyses enabled.</div>}
              </div></div>
            </div>)}
        </>)}
      </div></div>

      <Toasts items={toasts} close={id=>setToasts(t=>t.filter(x=>x.id!==id))}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
