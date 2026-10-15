// GENERATED from app.jsx by tests/build_ui.js — do not edit by hand.
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo
} = React;
const I = ({
  d,
  s = 16,
  f = "none",
  w = 1.8
}) => React.createElement("svg", {
  width: s,
  height: s,
  viewBox: "0 0 24 24",
  fill: f,
  stroke: "currentColor",
  strokeWidth: w,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": "true"
}, d);
const Play = p => React.createElement(I, _extends({}, p, {
  f: "currentColor",
  d: React.createElement("polygon", {
    points: "7 4 20 12 7 20"
  })
}));
const Pause = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("line", {
    x1: "9",
    y1: "5",
    x2: "9",
    y2: "19"
  }), React.createElement("line", {
    x1: "15",
    y1: "5",
    x2: "15",
    y2: "19"
  }))
}));
const Stop = p => React.createElement(I, _extends({}, p, {
  f: "currentColor",
  d: React.createElement("rect", {
    x: "6",
    y: "6",
    width: "12",
    height: "12",
    rx: "2"
  })
}));
const Check = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("polyline", {
    points: "20 6 9 17 4 12"
  })
}));
const X = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("line", {
    x1: "18",
    y1: "6",
    x2: "6",
    y2: "18"
  }), React.createElement("line", {
    x1: "6",
    y1: "6",
    x2: "18",
    y2: "18"
  }))
}));
const Chev = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("polyline", {
    points: "9 18 15 12 9 6"
  })
}));
const Doc = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("path", {
    d: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"
  }), React.createElement("polyline", {
    points: "14 3 14 8 19 8"
  }), React.createElement("line", {
    x1: "9",
    y1: "13",
    x2: "15",
    y2: "13"
  }), React.createElement("line", {
    x1: "9",
    y1: "17",
    x2: "13",
    y2: "17"
  }))
}));
const Grid = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("circle", {
    cx: "6",
    cy: "6",
    r: "2"
  }), React.createElement("circle", {
    cx: "12",
    cy: "6",
    r: "2"
  }), React.createElement("circle", {
    cx: "18",
    cy: "6",
    r: "2"
  }), React.createElement("circle", {
    cx: "6",
    cy: "12",
    r: "2"
  }), React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "2"
  }), React.createElement("circle", {
    cx: "18",
    cy: "12",
    r: "2"
  }))
}));
const Lines = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("line", {
    x1: "4",
    y1: "6",
    x2: "20",
    y2: "6"
  }), React.createElement("line", {
    x1: "4",
    y1: "12",
    x2: "20",
    y2: "12"
  }), React.createElement("line", {
    x1: "4",
    y1: "18",
    x2: "14",
    y2: "18"
  }))
}));
const Again = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("polyline", {
    points: "1 4 1 10 7 10"
  }), React.createElement("path", {
    d: "M3.5 15a9 9 0 1 0 2.1-9.4L1 10"
  }))
}));
const Folder = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("path", {
    d: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
  })
}));
const Alert = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("path", {
    d: "M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"
  }), React.createElement("line", {
    x1: "12",
    y1: "9",
    x2: "12",
    y2: "13.5"
  }), React.createElement("line", {
    x1: "12",
    y1: "17.2",
    x2: "12.01",
    y2: "17.2"
  }))
}));
const Info = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9.5"
  }), React.createElement("line", {
    x1: "12",
    y1: "16.5",
    x2: "12",
    y2: "11.5"
  }), React.createElement("line", {
    x1: "12",
    y1: "7.8",
    x2: "12.01",
    y2: "7.8"
  }))
}));
const Ext = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("path", {
    d: "M14 4h6v6"
  }), React.createElement("line", {
    x1: "20",
    y1: "4",
    x2: "11",
    y2: "13"
  }), React.createElement("path", {
    d: "M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"
  }))
}));
async function api(path, opts) {
  if (location.protocol === "file:") throw new Error("Open this page through the server (http://localhost:8000), not as a file.");
  let r;
  try {
    r = await fetch(path, {
      headers: {
        "Content-Type": "application/json"
      },
      ...opts
    });
  } catch (e) {
    throw new Error("The analysis server is not answering. It may be restarting — try again in a minute.");
  }
  const b = await r.json().catch(() => ({}));
  if (r.status === 401 && path !== "/api/login") {
    window.dispatchEvent(new Event("mea-signed-out"));
    throw new Error("Please sign in again.");
  }
  if (!r.ok) {
    const d = b.detail;
    throw new Error(d?.errors ? d.errors.join("\n") : typeof d === "string" ? d : `Request failed (${r.status})`);
  }
  return b;
}
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const prettyDate = code => {
  const m = /^(\d{2})(\d{2})(\d{2})$/.exec(code || "");
  if (!m) return {
    big: code,
    year: ""
  };
  const mo = +m[2] - 1;
  return mo >= 0 && mo < 12 ? {
    big: `${+m[3]} ${MONTHS[mo]}`,
    year: `20${m[1]}`
  } : {
    big: code,
    year: ""
  };
};
const projectOf = folder => {
  const p = (folder || "").replace(/\/+$/, "").split("/");
  return p[p.length - 2] || "";
};
const prettyProject = s => (s || "").replace(/_/g, " ");
const ago = iso => {
  if (!iso) return "";
  const t = new Date(iso);
  if (isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1e3);
  return s < 60 ? "just now" : s < 3600 ? `${s / 60 | 0} min ago` : s < 86400 ? `${s / 3600 | 0} h ago` : `${s / 86400 | 0} days ago`;
};
const dur = s => {
  if (s == null) return "";
  if (s < 60) return `${Math.round(s)} s`;
  const m = s / 60 | 0;
  return m < 60 ? `${m} min` : `${m / 60 | 0} h ${m % 60} min`;
};
const JOB = {
  running: {
    say: "Analysing",
    k: "run"
  },
  dispatched: {
    say: "In line",
    k: "queue"
  },
  queued: {
    say: "In line",
    k: "queue"
  },
  waiting: {
    say: "Waiting for copy",
    k: "wait"
  },
  detected: {
    say: "Found (test mode)",
    k: "wait"
  },
  interrupted: {
    say: "Paused — will resume",
    k: "wait"
  },
  held: {
    say: "On hold",
    k: "wait"
  },
  done: {
    say: "Done",
    k: "ok"
  },
  failed: {
    say: "Needs attention",
    k: "bad"
  }
};
const jobInfo = st => JOB[st] || {
  say: st || "Not started",
  k: "wait"
};
function folderState(jobs) {
  const sts = jobs.map(j => j.status);
  if (sts.includes("running")) return "running";
  if (sts.some(s => s === "dispatched" || s === "queued")) return "dispatched";
  if (sts.includes("failed")) return "failed";
  if (sts.length && sts.every(s => s === "done")) return "done";
  if (sts.includes("interrupted")) return "interrupted";
  if (sts.includes("held")) return "held";
  return sts[0] || "waiting";
}
function plainNote(job) {
  const d = job.detail || "",
    e = job.error || "";
  let m = /(\d+) of (\d+) well subprocess\(es\) failed/.exec(d);
  if (m) return {
    t: `${m[2] - m[1]} of ${m[2]} wells finished · ${m[1]} had problems`,
    k: "warn"
  };
  if (job.status === "held") return {
    t: "Taken off the queue — press Resume to analyse it",
    k: ""
  };
  if (job.status === "failed") {
    if (/cancelled/i.test(e)) return {
      t: "Stopped by hand — press “Analyse again” to redo it.",
      k: "bad"
    };
    if (/GPU is not usable/i.test(e)) return {
      t: "The graphics card was not available.",
      k: "bad"
    };
    if (/could not be copied from local scratch/i.test(e)) return {
      t: "Results could not be copied back from the fast disk.",
      k: "bad"
    };
    return {
      t: (e.split("\n")[0] || "Something went wrong — open the log.").slice(0, 160),
      k: "bad"
    };
  }
  if (/settling \((\d+)s remaining\)/.test(d)) {
    const s = +/settling \((\d+)s/.exec(d)[1];
    return {
      t: `Copy looks finished — confirming for ${Math.ceil(s / 60)} more min`,
      k: ""
    };
  }
  if (/waiting for MaxWell 'finished' marker/i.test(d)) return {
    t: "Waiting for the recording to be marked finished",
    k: ""
  };
  if (/queued — waiting/i.test(d)) return {
    t: "Waiting for a free slot",
    k: ""
  };
  m = /^running (.+?) · last log output (.+)$/.exec(d);
  if (m) return {
    t: `Running for ${m[1].replace(/(\d+)h/, "$1 h ").replace(/(\d+)m/, "$1 min")} · last activity ${m[2].replace(/(\d+)m ago/, "$1 min ago").replace(/(\d+)s ago/, "$1 s ago")}`,
    k: ""
  };
  if (/staged on local disk/i.test(d)) return {
    t: "Working on the fast local disk",
    k: ""
  };
  if (/copying results/i.test(d)) return {
    t: "Copying results back…",
    k: ""
  };
  return d ? {
    t: d.slice(0, 160),
    k: ""
  } : null;
}
function plainWellError(r, note) {
  const e = String(r.error || note?.fail || "");
  if (/stream_id well\d+ is not in/.test(e)) return "Not in this recording file — nothing to analyse.";
  if (/n_samples=\d+ should be >= n_clusters/.test(e)) return "Almost no activity in this well.";
  if (/out of memory/i.test(e)) return "Ran out of memory.";
  if (r.status !== "complete" && !e) return "Stopped without an error message.";
  return (e.split("\n").find(Boolean) || "Unknown problem").slice(0, 180);
}
function parseWellNotes(lines) {
  const notes = {};
  let cur = null;
  for (const l of lines) {
    let m = /Processing : (\S+) recording : \S+ well_id : (well\d+)/.exec(l);
    if (m) {
      const p = m[1].split("/");
      cur = `${p[p.length - 4]}|${p[p.length - 2]}|${m[2]}`;
      continue;
    }
    if (!cur) continue;
    m = /CRITICAL FAILURE in (well\d+): (.*)/.exec(l);
    if (m && cur.endsWith("|" + m[1])) {
      notes[cur] = {
        ...notes[cur],
        fail: m[2].trim()
      };
      continue;
    }
    if (/Detected 0 total spikes|returned error: no_spikes/.test(l)) notes[cur] = {
      ...notes[cur],
      silent: true
    };
  }
  return notes;
}
function wellClass(r, note, finished) {
  if (r.status === "complete") return note?.silent ? "silent" : "complete";
  if (note?.fail && /stream_id well\d+ is not in/.test(note.fail)) return "absent";
  if (note?.silent) return "silent";
  if (r.status === "failed" || note?.fail || finished) return "failed";
  return "running";
}
function wellCounts(data, finished) {
  const c = {
    complete: 0,
    silent: 0,
    absent: 0,
    failed: 0,
    running: 0
  };
  (data?.wells || []).forEach(r => {
    c[wellClass(r, data.notes?.[`${r.chip_id}|${r.run_id}|${r.well}`], finished)]++;
  });
  return c;
}
function cleanLog(lines) {
  return lines.filter(l => l && !/\d+%\|/.test(l) && !/it\/s\]/.test(l) && !/^\s*write_binary_recording\s*$/.test(l) && !/^engine=process/.test(l) && !/libcompression\.so/.test(l) && !/UserWarning|warnings\.warn\(/.test(l));
}
const logKind = l => /ERROR|CRITICAL|Traceback|Error:|FAILED/.test(l) ? "err" : /WARNING/.test(l) ? "warn" : /Processing Complete|completed in|Checkpoint Saved: REPORTS_COMPLETE/.test(l) ? "ok" : "";
function Switch({
  checked,
  onChange,
  label,
  hint,
  id,
  disabled
}) {
  return React.createElement("div", {
    className: "sw-row"
  }, React.createElement("button", {
    type: "button",
    role: "switch",
    "aria-checked": !!checked,
    id: id,
    disabled: disabled,
    className: "sw",
    onClick: () => !disabled && onChange(!checked)
  }), React.createElement("label", {
    htmlFor: id,
    style: {
      cursor: disabled ? "not-allowed" : "pointer"
    }
  }, React.createElement("div", {
    className: "sw-l"
  }, label), hint && React.createElement("div", {
    className: "sw-h"
  }, hint)));
}
function Code({
  text
}) {
  const [c, setC] = useState(false);
  return React.createElement("pre", {
    className: "code"
  }, text, React.createElement("button", {
    className: "cp",
    onClick: () => navigator.clipboard?.writeText(text).then(() => {
      setC(true);
      setTimeout(() => setC(false), 1500);
    })
  }, c ? "Copied" : "Copy"));
}
function Callout({
  kind = "",
  icon,
  children
}) {
  return React.createElement("div", {
    className: "callout " + kind
  }, React.createElement("span", {
    className: "ic"
  }, icon || React.createElement(Info, {
    s: 17
  })), React.createElement("div", null, children));
}
function Toasts({
  items,
  close
}) {
  return React.createElement("div", {
    className: "toasts",
    role: "status",
    "aria-live": "polite"
  }, items.map(t => React.createElement("div", {
    key: t.id,
    className: "toast" + (t.k === "error" ? " err" : "")
  }, React.createElement("span", {
    style: {
      flex: "none",
      marginTop: 2
    }
  }, t.k === "error" ? React.createElement(Alert, {
    s: 16
  }) : React.createElement(Check, {
    s: 16
  })), React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, React.createElement("div", {
    className: "toast-t"
  }, t.t), t.m && React.createElement("div", {
    className: "toast-m"
  }, t.m)), React.createElement("button", {
    className: "btn ghost sm",
    style: {
      color: "inherit"
    },
    onClick: () => close(t.id),
    "aria-label": "Dismiss"
  }, React.createElement(X, {
    s: 13
  })))));
}
function Confirm({
  ask,
  onClose
}) {
  if (!ask) return null;
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "scrim m",
    onClick: () => onClose(false)
  }), React.createElement("div", {
    className: "modal",
    role: "dialog",
    "aria-modal": "true",
    "aria-labelledby": "cf-t"
  }, React.createElement("h3", {
    id: "cf-t"
  }, ask.title), React.createElement("div", {
    className: "hint",
    style: {
      whiteSpace: "pre-wrap"
    }
  }, ask.body), React.createElement("div", {
    className: "acts"
  }, React.createElement("button", {
    className: "btn ghost",
    onClick: () => onClose(false)
  }, "Cancel"), ask.alt && React.createElement("button", {
    className: "btn",
    onClick: () => onClose("alt")
  }, ask.alt), React.createElement("button", {
    className: "btn " + (ask.danger ? "red" : "ink"),
    autoFocus: true,
    onClick: () => onClose(true)
  }, ask.ok || "Continue"))));
}
function Browser({
  initial,
  onPick,
  onClose
}) {
  const [d, setD] = useState(null),
    [p, setP] = useState(initial || ""),
    [e, setE] = useState("");
  const load = useCallback(async q => {
    try {
      setE("");
      const r = await api("/api/browse", {
        method: "POST",
        body: JSON.stringify({
          path: q
        })
      });
      setD(r);
      setP(r.path);
    } catch (x) {
      setE(x.message);
    }
  }, []);
  useEffect(() => {
    load(initial || "");
  }, [load, initial]);
  return React.createElement("div", {
    className: "br"
  }, React.createElement("div", {
    className: "br-p"
  }, React.createElement("input", {
    className: "inp mono",
    value: p,
    onChange: ev => setP(ev.target.value),
    onKeyDown: ev => ev.key === "Enter" && load(p),
    "aria-label": "Folder path"
  }), React.createElement("button", {
    className: "btn sm",
    onClick: () => load(p)
  }, "Go"), React.createElement("button", {
    className: "btn ink sm",
    onClick: () => {
      onPick(p);
      onClose();
    }
  }, "Use this folder")), e && React.createElement("div", {
    style: {
      padding: "10px 14px",
      color: "var(--red)",
      fontSize: 13.5
    }
  }, e), React.createElement("div", {
    className: "br-l"
  }, d?.parent && React.createElement("div", {
    className: "br-i",
    onClick: () => load(d.parent)
  }, React.createElement(Folder, {
    s: 15
  }), React.createElement("span", {
    className: "n"
  }, ".. (up one level)")), d?.entries?.length === 0 && React.createElement("div", {
    className: "hint",
    style: {
      padding: 14
    }
  }, "No folders inside."), d?.entries?.map(x => React.createElement("div", {
    key: x.path,
    className: "br-i",
    onClick: () => load(x.path),
    onDoubleClick: () => {
      onPick(x.path);
      onClose();
    }
  }, React.createElement(Folder, {
    s: 15
  }), React.createElement("span", {
    className: "n"
  }, x.name), x.is_run && React.createElement("span", {
    className: "hint-s"
  }, x.recordings, " recording", x.recordings === 1 ? "" : "s")))));
}
function Plates({
  data,
  finished
}) {
  if (!data) return React.createElement("div", {
    className: "hint",
    style: {
      paddingTop: 10,
      display: "flex",
      gap: 10,
      alignItems: "center"
    }
  }, React.createElement("span", {
    className: "spin"
  }), " Reading well results\u2026 While analyses are running the results disk is busy, so this can take a minute or two. You can keep using the page.");
  if (data.error) return React.createElement("div", {
    className: "hint",
    style: {
      paddingTop: 10,
      color: "var(--red)"
    }
  }, data.error);
  const rows = data.wells || [];
  if (!rows.length) return React.createElement("div", {
    className: "hint",
    style: {
      paddingTop: 10
    }
  }, "No wells have started yet. They appear here as the analysis reaches them.");
  const note = r => data.notes?.[`${r.chip_id}|${r.run_id}|${r.well}`];
  const chips = {};
  rows.forEach(r => {
    const k = `${r.chip_id || "?"}·${r.run_id || ""}`;
    (chips[k] = chips[k] || {
      chip: r.chip_id,
      run: r.run_id,
      wells: {}
    }).wells[r.well] = r;
  });
  const c = wellCounts(data, finished);
  const probs = rows.filter(r => wellClass(r, note(r), finished) === "failed");
  const tips = {
    complete: "finished",
    silent: "finished, but no spikes were detected",
    absent: "not in this recording file — nothing to analyse",
    running: "in progress"
  };
  let i = 0;
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "legend"
  }, React.createElement("span", null, React.createElement("b", null, c.complete), "\xA0finished"), c.silent > 0 && React.createElement("span", null, React.createElement("b", null, c.silent), "\xA0no activity"), c.absent > 0 && React.createElement("span", null, React.createElement("b", null, c.absent), "\xA0not in the recording file"), c.running > 0 && React.createElement("span", null, React.createElement("b", null, c.running), "\xA0in progress"), c.failed > 0 && React.createElement("span", {
    style: {
      color: "var(--red)"
    }
  }, React.createElement("b", null, c.failed), "\xA0problem", c.failed === 1 ? "" : "s")), React.createElement("div", {
    className: "legend",
    style: {
      marginTop: 6
    }
  }, React.createElement("span", null, React.createElement("i", {
    className: "well-k complete"
  }), "finished"), React.createElement("span", null, React.createElement("i", {
    className: "well-k silent"
  }), "no activity"), !finished && React.createElement("span", null, React.createElement("i", {
    className: "well-k running"
  }), "in progress"), React.createElement("span", null, React.createElement("i", {
    className: "well-k failed"
  }), "problem"), React.createElement("span", null, React.createElement("i", {
    className: "well-k absent"
  }), "not in the recording file"), React.createElement("span", null, React.createElement("i", {
    className: "well-k none"
  }), "not recorded")), React.createElement("div", {
    className: "plates"
  }, Object.values(chips).map(ch => {
    const ids = Object.keys(ch.wells).map(w => +w.replace(/\D/g, ""));
    const n = Math.max(6, Math.ceil((Math.max(...ids) + 1) / 6) * 6);
    return React.createElement("div", {
      className: "plate",
      key: ch.chip + ch.run
    }, React.createElement("div", {
      className: "plate-h"
    }, "Chip ", React.createElement("b", null, ch.chip || "?"), React.createElement("span", {
      className: "hint-s"
    }, "recording ", ch.run)), React.createElement("div", {
      className: "wells"
    }, Array.from({
      length: n
    }, (_, k) => {
      const r = ch.wells[`well${String(k).padStart(3, "0")}`];
      const cls = r ? wellClass(r, note(r), finished) : "none";
      const tip = !r ? `Well ${k + 1}: not recorded in this run` : cls === "failed" ? `Well ${k + 1}: ${plainWellError(r, note(r))}` : cls === "running" ? `Well ${k + 1}: ${r.stage_name || "in progress"}` : `Well ${k + 1}: ${tips[cls]}`;
      return React.createElement("div", {
        key: k,
        className: "well " + cls,
        style: {
          "--i": i++
        },
        title: tip
      }, k + 1);
    })));
  })), probs.length > 0 && React.createElement("div", {
    className: "probs"
  }, probs.map((r, j) => React.createElement("div", {
    className: "prob",
    key: j
  }, React.createElement("span", {
    className: "w"
  }, r.chip_id, " \xB7 well ", +r.well.replace(/\D/g, "") + 1), React.createElement("span", null, plainWellError(r, note(r)))))));
}
function LogDrawer({
  log,
  onClose,
  live
}) {
  const [raw, setRaw] = useState(false);
  const ref = useRef(null);
  const lines = raw ? log.lines : cleanLog(log.lines);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [log.lines, raw]);
  useEffect(() => {
    const k = e => e.key === "Escape" && onClose();
    addEventListener("keydown", k);
    return () => removeEventListener("keydown", k);
  }, [onClose]);
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "scrim",
    onClick: onClose
  }), React.createElement("aside", {
    className: "drawer",
    role: "dialog",
    "aria-label": "Log"
  }, React.createElement("div", {
    className: "dr-h"
  }, React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, React.createElement("div", {
    className: "dr-t"
  }, log.title), React.createElement("div", {
    className: "hint"
  }, live ? React.createElement(React.Fragment, null, React.createElement("span", {
    className: "dot run",
    style: {
      display: "inline-block",
      marginRight: 7
    }
  }), "Updating live") : "Last 600 lines", " · ", lines.length, " shown")), React.createElement("button", {
    className: "btn sm",
    onClick: () => setRaw(r => !r)
  }, raw ? "Hide progress noise" : "Show everything"), React.createElement("button", {
    className: "btn ghost sm",
    onClick: onClose,
    "aria-label": "Close"
  }, React.createElement(X, {
    s: 15
  }))), React.createElement("div", {
    className: "dr-b",
    ref: ref
  }, log.error && React.createElement("div", {
    className: "lg err"
  }, log.error), !log.lines.length && !log.error && React.createElement("div", {
    className: "lg"
  }, "Loading\u2026"), lines.map((l, i) => React.createElement("div", {
    key: i,
    className: "lg " + logKind(l)
  }, l)))));
}
const HOLDABLE = ["dispatched", "queued", "running", "interrupted", "waiting"];
function Line({
  f,
  report,
  wells,
  open,
  onWells,
  onLog,
  onAgain,
  onHold,
  onResume,
  i
}) {
  const st = folderState(f.jobs),
    ji = jobInfo(st);
  const dt = prettyDate(f.date);
  const net = f.jobs.find(j => j.job === "network"),
    scan = f.jobs.find(j => j.job === "activity");
  const note = net ? plainNote(net) : null;
  const busy = st === "running";
  const sum = wells?.summary;
  const netDone = net && (net.status === "done" || net.status === "failed");
  const wc = netDone && wells?.wells && wells.notes ? wellCounts(wells, true) : null;
  const refined = wc && {
    t: [`${wc.complete} wells finished`, wc.silent && `${wc.silent} with no activity`, wc.absent && `${wc.absent} not in the recording file`, wc.failed && `${wc.failed} with problems`].filter(Boolean).join(" · "),
    k: wc.failed ? "bad" : ""
  };
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "line rise",
    style: {
      "--i": i
    }
  }, React.createElement("div", null, React.createElement("div", {
    className: "d-big"
  }, dt.big), React.createElement("div", {
    className: "d-code"
  }, dt.year, " \xB7 ", f.date)), React.createElement("div", {
    className: "mid"
  }, React.createElement("div", {
    className: "say"
  }, React.createElement("span", {
    className: "stamp " + ji.k
  }, ji.say), busy && sum?.wells > 0 && React.createElement("span", {
    className: "note-l"
  }, sum.complete, " wells finished so far"), (refined || note) && React.createElement("span", {
    className: "note-l " + (refined || note).k
  }, (refined || note).t)), startedBy(net || scan) && React.createElement("div", {
    className: "hint-s who"
  }, startedBy(net || scan), net && scan && scan.started_by && scan.started_by !== net.started_by ? ` · activity scan ${startedBy(scan)}` : ""), React.createElement("div", {
    className: "lanes"
  }, [["Network", net], ["Activity scan", scan]].filter(x => x[1]).map(([n, j]) => {
    const x = jobInfo(j.status);
    return React.createElement("span", {
      className: "lane",
      key: n
    }, React.createElement("i", {
      className: "dot " + (x.k === "ok" ? "ok" : x.k === "bad" ? "bad" : x.k === "run" ? "run" : x.k === "queue" ? "queue" : "wait")
    }), n, " ", React.createElement("span", {
      className: "lk"
    }, x.say.toLowerCase(), j.status === "done" && j.duration_s ? ` · took ${dur(j.duration_s)}` : ""));
  })), busy && React.createElement("div", {
    className: "flow"
  }, React.createElement("i", null))), React.createElement("div", {
    className: "acts"
  }, report && React.createElement("a", {
    className: "btn ink sm",
    href: `/api/reports/view?path=${encodeURIComponent(report.path)}`,
    target: "_blank",
    rel: "noopener"
  }, React.createElement(Doc, {
    s: 14
  }), " Report"), net && React.createElement("button", {
    className: "btn sm",
    "aria-expanded": open,
    onClick: () => onWells(f)
  }, React.createElement(Grid, {
    s: 14
  }), " Wells"), (net?.log || scan?.log) && React.createElement("button", {
    className: "btn sm",
    onClick: () => onLog(f)
  }, React.createElement(Lines, {
    s: 14
  }), " Log"), (net?.run_id || scan?.run_id) && React.createElement("button", {
    className: "btn sm",
    title: "Steps, wells, outputs and settings of this run",
    onClick: () => goRun(net?.run_id || scan?.run_id)
  }, React.createElement(Chev, {
    s: 14
  }), " Details"), f.jobs.some(j => HOLDABLE.includes(j.status)) && React.createElement("button", {
    className: "btn sm",
    title: busy ? "Stop this date and keep it for later" : "Take this date off the queue and keep it for later",
    onClick: () => onHold(f)
  }, React.createElement(Pause, {
    s: 14
  }), " Hold"), f.jobs.some(j => j.status === "held") && React.createElement("button", {
    className: "btn sm",
    title: "Put this date back in the queue",
    onClick: () => onResume(f)
  }, React.createElement(Play, {
    s: 11
  }), " Resume"), React.createElement("button", {
    className: "btn ghost sm",
    title: "Analyse this date again",
    "aria-label": "Analyse again",
    onClick: () => onAgain(f)
  }, React.createElement(Again, {
    s: 14
  })))), open && React.createElement("div", {
    className: "plate-wrap"
  }, React.createElement(Plates, {
    data: wells,
    finished: !!netDone
  })));
}
function Progress({
  folders,
  reports,
  wells,
  openW,
  onWells,
  onLog,
  onAgain,
  onHold,
  onResume,
  feed,
  goAdd
}) {
  const byProj = {};
  folders.forEach(f => {
    (byProj[f.project] = byProj[f.project] || []).push(f);
  });
  if (!folders.length) return React.createElement("div", {
    className: "ledger rise"
  }, React.createElement("div", {
    className: "empty"
  }, React.createElement("div", {
    className: "empty-t"
  }, "Nothing in the notebook yet"), React.createElement("div", {
    className: "empty-d"
  }, "Choose recording dates to analyse and they will appear here, one line per date."), React.createElement("div", {
    style: {
      marginTop: 18
    }
  }, React.createElement("button", {
    className: "btn ink",
    onClick: goAdd
  }, React.createElement(Play, {
    s: 12
  }), " Add recordings"))));
  let i = 0;
  return React.createElement(React.Fragment, null, Object.entries(byProj).map(([p, fs]) => React.createElement("div", {
    className: "sec",
    key: p
  }, React.createElement("div", {
    className: "ledger"
  }, React.createElement("div", {
    className: "proj"
  }, React.createElement("span", {
    className: "proj-n"
  }, prettyProject(p)), React.createElement("span", {
    className: "proj-c"
  }, fs.length, " date", fs.length === 1 ? "" : "s", " \xB7 ", fs.filter(f => folderState(f.jobs) === "done").length, " done")), fs.map(f => React.createElement(Line, {
    key: f.folder,
    f: f,
    i: i++,
    report: reports[`${p}/${f.date}`],
    wells: wells[f.folder],
    open: !!openW[f.folder],
    onWells: onWells,
    onLog: onLog,
    onAgain: onAgain,
    onHold: onHold,
    onResume: onResume
  }))))), feed.some(l => !/^=+$|Open this in your browser|do not open index\.html|^Work dir:/.test(l.message)) && React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Today\u2019s entries"), React.createElement("div", {
    className: "sec-d"
  }, "What the system has been doing, newest first")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b feed"
  }, feed.filter(l => !/^=+$|Open this in your browser|do not open index\.html|^Work dir:/.test(l.message)).slice(-14).reverse().map(l => React.createElement("div", {
    className: "feed-i" + (l.level === "ERROR" ? " err" : ""),
    key: l.seq
  }, React.createElement("span", {
    className: "feed-t"
  }, l.time.slice(0, 5)), React.createElement("span", {
    className: "feed-m"
  }, l.message)))))));
}
function AddRecordings({
  cfg,
  toast,
  ask,
  onQueued
}) {
  const [dir, setDir] = useState(cfg.watch_dir || "");
  const [entries, setEntries] = useState(null);
  const [info, setInfo] = useState({});
  const [sel, setSel] = useState({});
  const [again, setAgain] = useState(false);
  const [busy, setBusy] = useState(false);
  const [browse, setBrowse] = useState(false);
  const [checking, setChecking] = useState(false);
  const load = useCallback(async path => {
    setEntries(null);
    setSel({});
    try {
      const r = await api("/api/browse", {
        method: "POST",
        body: JSON.stringify({
          path
        })
      });
      setDir(r.path);
      const runs = (r.entries || []).filter(x => x.is_run);
      setEntries(runs);
      setInfo({});
      if (runs.length) {
        setChecking(true);
        try {
          const ins = await api("/api/queue/inspect", {
            method: "POST",
            body: JSON.stringify({
              folders: runs.map(x => x.path)
            })
          });
          const by = {};
          (ins.folders || []).forEach(f => {
            by[f.path] = f;
          });
          setInfo(by);
        } finally {
          setChecking(false);
        }
      }
    } catch (e) {
      setEntries([]);
      setChecking(false);
      toast("Could not read that folder", e.message, "error");
    }
  }, [toast]);
  useEffect(() => {
    if (cfg.watch_dir) load(cfg.watch_dir);
  }, [cfg.watch_dir, load]);
  const done = p => {
    const j = info[p]?.jobs || [];
    return j.length > 0 && j.every(x => x.analysed);
  };
  const partly = p => !done(p) && (info[p]?.jobs || []).some(x => x.analysed);
  const busyBy = p => (info[p]?.jobs || []).find(x => x.in_flight);
  const gone = p => (info[p]?.jobs || []).some(x => x.previous && !x.previous.output_exists);
  const byWhom = p => [...new Set((info[p]?.jobs || []).filter(x => x.analysed && x.previous.by).map(x => x.previous.by))].join(", ");
  const prevLines = p => (info[p]?.jobs || []).filter(x => x.analysed).map(x => {
    const v = x.previous;
    return `${x.label}: analysed${v.by ? ` by ${v.by}` : ""}${v.finished ? ` on ${whenStarted(v.finished)}` : ""}. Results: ${v.output}`;
  });
  const chosen = Object.keys(sel).filter(k => sel[k]);
  const chosenDone = chosen.filter(done).length;
  const fresh = (entries || []).filter(x => !done(x.path) && x.finished !== false);
  const go = async () => {
    if (chosenDone && again && !(await ask({
      title: "Analyse again?",
      ok: "Analyse again",
      body: `${chosenDone} of these dates were already analysed. Their results will be computed again and replaced.\n\n` + chosen.filter(done).map(p => `${prettyDate(p.split("/").pop()).big} ${prettyDate(p.split("/").pop()).year}\n` + prevLines(p).map(l => "  • " + l).join("\n")).join("\n\n")
    }))) return;
    setBusy(true);
    try {
      const r = await api("/api/queue", {
        method: "POST",
        body: JSON.stringify({
          folders: chosen,
          rerun: again
        })
      });
      const n = new Set(r.queued.map(q => q.path)).size;
      const sk = (r.skipped || []).filter(x => x.job);
      toast(`${n} date${n === 1 ? "" : "s"} added`, "They will be analysed in order. Follow them under Progress." + (sk.length ? `\n\nNot added:\n` + sk.map(x => `${x.path.split("/").pop()}: ${x.reason}`).join("\n") : ""));
      setSel({});
      onQueued();
    } catch (e) {
      toast("Nothing was added", e.message, "error");
    } finally {
      setBusy(false);
    }
  };
  return React.createElement("div", {
    className: "rise"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Add recordings"), React.createElement("div", {
    className: "sec-d"
  }, "Tick the recording dates you want analysed, then press the button at the bottom.")), React.createElement("div", {
    className: "card",
    style: {
      marginBottom: 18
    }
  }, React.createElement("div", {
    className: "card-b",
    style: {
      display: "flex",
      gap: 12,
      alignItems: "center",
      flexWrap: "wrap"
    }
  }, React.createElement(Folder, {
    s: 18
  }), React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, React.createElement("div", {
    className: "hint-s"
  }, "Looking in"), React.createElement("div", {
    className: "mono",
    style: {
      wordBreak: "break-all"
    }
  }, dir || "—")), React.createElement("button", {
    className: "btn sm",
    onClick: () => setBrowse(b => !b)
  }, browse ? "Close" : "Look somewhere else"), React.createElement("button", {
    className: "btn sm",
    onClick: () => load(dir)
  }, "Refresh"), browse && React.createElement("div", {
    style: {
      flexBasis: "100%"
    }
  }, React.createElement(Browser, {
    initial: dir,
    onClose: () => setBrowse(false),
    onPick: p => load(p)
  })))), entries === null ? React.createElement("div", {
    className: "tiles"
  }, [0, 1, 2, 3, 4, 5].map(k => React.createElement("div", {
    key: k,
    className: "skel",
    style: {
      height: 96
    }
  }))) : entries.length === 0 ? React.createElement(Callout, {
    kind: "amber",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, "No recording dates were found in this folder. Choose the folder that", React.createElement("b", null, " contains"), " the date folders (like ", React.createElement("span", {
    className: "mono"
  }, "260818"), ").") : React.createElement(React.Fragment, null, React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginBottom: 12,
      flexWrap: "wrap"
    }
  }, checking && React.createElement("span", {
    className: "hint",
    style: {
      display: "flex",
      gap: 8,
      alignItems: "center"
    }
  }, React.createElement("span", {
    className: "spin"
  }), " Checking which dates were already analysed\u2026"), React.createElement("button", {
    className: "btn sm",
    disabled: checking || !fresh.length,
    onClick: () => setSel(Object.fromEntries(fresh.map(x => [x.path, true])))
  }, "Select all new (", fresh.length, ")"), chosen.length > 0 && React.createElement("button", {
    className: "btn ghost sm",
    onClick: () => setSel({})
  }, "Clear selection")), React.createElement("div", {
    className: "tiles"
  }, entries.map((x, k) => {
    const dt = prettyDate(x.name),
      on = !!sel[x.path],
      dn = done(x.path),
      fl = busyBy(x.path)?.in_flight;
    const jobs = (info[x.path]?.jobs || []).map(j => j.label).join(" + ");
    const who = dn ? byWhom(x.path) : "";
    return React.createElement("label", {
      key: x.path,
      className: "tile",
      "data-on": on,
      "data-done": dn,
      style: {
        "--i": k
      }
    }, React.createElement("input", {
      type: "checkbox",
      checked: on,
      onChange: () => setSel(v => ({
        ...v,
        [x.path]: !v[x.path]
      }))
    }), fl ? React.createElement("span", {
      className: "t-tag copy"
    }, fl.status === "running" ? "analysing" : "in queue") : dn ? React.createElement("span", {
      className: "t-tag done"
    }, "analysed") : partly(x.path) ? React.createElement("span", {
      className: "t-tag copy"
    }, "partly done") : x.finished === false ? React.createElement("span", {
      className: "t-tag copy"
    }, "copying") : null, React.createElement("div", {
      className: "t-date"
    }, dt.big), React.createElement("div", {
      className: "t-code"
    }, dt.year, " \xB7 ", x.name), React.createElement("div", {
      className: "t-what"
    }, jobs || info[x.path]?.note || " "), fl && fl.by && React.createElement("div", {
      className: "t-who"
    }, "started by ", fl.by), !fl && who && React.createElement("div", {
      className: "t-who"
    }, "by ", who), !fl && !dn && gone(x.path) && React.createElement("div", {
      className: "t-who"
    }, "earlier results were deleted"), React.createElement("span", {
      className: "t-tick"
    }, on && React.createElement(Check, {
      s: 13,
      w: 3
    })));
  }))), chosen.length > 0 && React.createElement("div", {
    className: "sticky"
  }, React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 200
    }
  }, React.createElement("b", null, chosen.length, " date", chosen.length === 1 ? "" : "s", " selected"), chosenDone > 0 && React.createElement("div", {
    className: "dup"
  }, React.createElement("div", {
    className: "dup-t"
  }, React.createElement(Info, {
    s: 14
  }), " ", chosenDone === 1 ? "This date was" : `${chosenDone} of these dates were`, " already analysed \u2014 the results exist:"), chosen.filter(done).map(p => React.createElement("div", {
    key: p,
    className: "dup-i"
  }, React.createElement("b", null, prettyDate(p.split("/").pop()).big, " ", prettyDate(p.split("/").pop()).year), prevLines(p).map((l, i) => React.createElement("div", {
    key: i,
    className: "mono-s"
  }, l)))), React.createElement("label", {
    style: {
      display: "flex",
      gap: 8,
      alignItems: "center",
      marginTop: 6,
      fontSize: 13,
      cursor: "pointer"
    }
  }, React.createElement("input", {
    type: "checkbox",
    checked: again,
    onChange: e => setAgain(e.target.checked)
  }), "Run ", chosenDone === 1 ? "it" : "them", " again anyway (otherwise ", chosenDone === 1 ? "it is" : "they are", " skipped)"))), React.createElement("button", {
    className: "btn lite",
    disabled: busy,
    onClick: go
  }, busy ? React.createElement("span", {
    className: "spin"
  }) : React.createElement(Play, {
    s: 12
  }), " Analyse ", chosen.length, " date", chosen.length === 1 ? "" : "s")));
}
function AiReport({
  cfg,
  reports,
  toast
}) {
  const [text, setText] = useState(cfg.ai_requirements || "");
  const [saved, setSaved] = useState(cfg.ai_requirements || "");
  const [auto, setAuto] = useState(cfg.auto_handoff !== false);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState(null);
  const building = last?.state === "running";
  useEffect(() => {
    let t = null,
      stop = false;
    const poll = () => api("/api/handoff").then(d => {
      if (stop) return;
      if (d?.state && d.state !== "idle") setLast(d);
      if (d?.state === "running") t = setTimeout(poll, 2500);
    }).catch(() => {});
    poll();
    return () => {
      stop = true;
      clearTimeout(t);
    };
  }, [busy]);
  const save = async (a = auto) => {
    try {
      await api("/api/requirements", {
        method: "POST",
        body: JSON.stringify({
          text,
          auto_handoff: a
        })
      });
      setSaved(text);
      toast("Saved", "Every new report will follow these instructions.");
      return true;
    } catch (e) {
      toast("Not saved", e.message, "error");
      return false;
    }
  };
  const prepare = async () => {
    setBusy(true);
    try {
      if (text !== saved && !(await save())) return;
      await api("/api/handoff", {
        method: "POST",
        body: JSON.stringify({
          folders: []
        })
      });
    } catch (e) {
      toast("Could not make the report", e.message, "error");
    } finally {
      setBusy(false);
    }
  };
  const list = Object.values(reports);
  const byP = {};
  list.forEach(r => {
    (byP[r.project] = byP[r.project] || []).push(r);
  });
  return React.createElement("div", {
    className: "rise"
  }, React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Finished reports"), React.createElement("div", {
    className: "sec-d"
  }, "One report per recording date. It opens in a new tab.")), list.length === 0 ? React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "empty"
  }, React.createElement("div", {
    className: "empty-t"
  }, "No reports yet"), React.createElement("div", {
    className: "empty-d"
  }, auto ? "A report is made automatically when analysed dates finish. You can also make them below." : "Switch on automatic reports below, or press “Make reports” to make them now."))) : Object.entries(byP).map(([p, rs]) => React.createElement("div", {
    className: "ledger",
    key: p,
    style: {
      marginBottom: 16
    }
  }, React.createElement("div", {
    className: "proj"
  }, React.createElement("span", {
    className: "proj-n"
  }, prettyProject(p) || "Reports"), React.createElement("span", {
    className: "proj-c"
  }, rs.length, " report", rs.length === 1 ? "" : "s")), rs.map((r, k) => {
    const dt = prettyDate(r.label);
    return React.createElement("div", {
      className: "line rise",
      key: r.path,
      style: {
        "--i": k
      }
    }, React.createElement("div", null, React.createElement("div", {
      className: "d-big"
    }, dt.big), React.createElement("div", {
      className: "d-code"
    }, dt.year, " \xB7 ", r.label)), React.createElement("div", {
      className: "hint"
    }, "Written ", ago(r.built)), React.createElement("div", {
      className: "acts"
    }, React.createElement("a", {
      className: "btn ink sm",
      target: "_blank",
      rel: "noopener",
      href: `/api/reports/view?path=${encodeURIComponent(r.path)}`
    }, React.createElement(Ext, {
      s: 14
    }), " Open report")));
  })))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "What reports should cover"), React.createElement("div", {
    className: "sec-d"
  }, "Write it the way you would brief a colleague. Applies to every new report.")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("textarea", {
    className: "inp",
    rows: 8,
    value: text,
    onChange: e => setText(e.target.value),
    placeholder: "For example:\n• Compare burst rate between the two lines at each age\n• Leave out wells that failed quality control\n• One figure per measurement"
  }), React.createElement("div", {
    style: {
      display: "flex",
      gap: 10,
      marginTop: 12,
      flexWrap: "wrap",
      alignItems: "center"
    }
  }, React.createElement("button", {
    className: "btn ink",
    disabled: text === saved,
    onClick: () => save()
  }, text === saved ? "Saved" : "Save instructions"), React.createElement("span", {
    className: "hint-s"
  }, "Anything you leave out follows the lab\u2019s standard report.")), React.createElement("details", {
    className: "adv"
  }, React.createElement("summary", null, React.createElement("span", {
    className: "chev"
  }, React.createElement(Chev, {
    s: 14
  })), "Making reports"), React.createElement(Switch, {
    id: "ai-auto",
    checked: auto,
    onChange: v => {
      setAuto(v);
      save(v);
    },
    label: "Make the report automatically when dates finish",
    hint: "Builds the lab's standard report for each finished date \u2014 Network analysis, Activity scan, or both, whichever was run \u2014 and lists it above."
  }), React.createElement("div", {
    className: "hint",
    style: {
      margin: "6px 0 12px"
    }
  }, "Every report folder also holds a short note for Claude. To have Claude add what your instructions above ask for and explain the results, run the command shown when a report is ready."), React.createElement("button", {
    className: "btn",
    disabled: busy || building,
    onClick: prepare
  }, busy || building ? React.createElement("span", {
    className: "spin"
  }) : React.createElement(Doc, {
    s: 14
  }), " Make reports for every finished date"), building && React.createElement("div", {
    className: "hint",
    style: {
      marginTop: 10
    }
  }, "Making the report", last.projects?.length > 1 ? "s" : "", "\u2026 about a minute per date. You can leave this page."), last?.state === "done" && last.prompt && React.createElement("div", {
    style: {
      marginTop: 12
    }
  }, React.createElement(Callout, {
    kind: "green",
    icon: React.createElement(Check, {
      s: 17
    })
  }, "Report ready \u2014 ", last.network_wells, " wells, ", last.activity_runs, " scans", last.packages?.length > 1 ? ` in ${last.packages.length} projects` : "", ". It is listed above. For Claude, in a terminal on the analysis computer, run:"), React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, React.createElement(Code, {
    text: last.instruction
  })), last.errors?.length > 0 && React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, React.createElement(Callout, {
    kind: "amber",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, last.errors.join(" · ")))), last?.state === "error" && React.createElement("div", {
    style: {
      marginTop: 12
    }
  }, React.createElement(Callout, {
    kind: "red",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, last.error)))))));
}
function Field({
  spec,
  value,
  onChange
}) {
  const set = v => onChange(spec.key, v);
  if (spec.type === "flag") return React.createElement(Switch, {
    id: "o-" + spec.key,
    checked: !!value,
    onChange: set,
    label: spec.flag,
    hint: spec.help
  });
  const L = React.createElement("span", {
    className: "f-l mono",
    style: {
      fontWeight: 500
    }
  }, spec.flag);
  const H = React.createElement("span", {
    className: "hint-s"
  }, spec.help);
  if (spec.type === "tristate") return React.createElement("div", {
    className: "f"
  }, L, React.createElement("select", {
    className: "sel",
    value: value == null ? "" : String(value),
    onChange: e => set(e.target.value === "" ? null : e.target.value === "true")
  }, React.createElement("option", {
    value: ""
  }, "Default"), React.createElement("option", {
    value: "true"
  }, "On"), React.createElement("option", {
    value: "false"
  }, "Off")), H);
  if (spec.type === "choice") return React.createElement("div", {
    className: "f"
  }, L, React.createElement("select", {
    className: "sel",
    value: value ?? "",
    onChange: e => set(e.target.value || null)
  }, React.createElement("option", {
    value: ""
  }, "Default"), spec.choices.map(c => React.createElement("option", {
    key: c,
    value: c
  }, c))), H);
  if (spec.type === "list") return React.createElement("div", {
    className: "f"
  }, L, React.createElement("input", {
    className: "inp mono",
    placeholder: "comma separated",
    value: Array.isArray(value) ? value.join(", ") : value ?? "",
    onChange: e => set(e.target.value.split(",").map(s => s.trim()).filter(Boolean))
  }), H);
  const num = spec.type === "int" || spec.type === "float";
  return React.createElement("div", {
    className: "f"
  }, L, React.createElement("input", {
    className: "inp" + (spec.type === "path" ? " mono" : ""),
    type: num ? "number" : "text",
    step: spec.type === "float" ? "0.01" : "1",
    placeholder: "Default",
    value: value ?? "",
    onChange: e => set(e.target.value === "" ? null : num ? Number(e.target.value) : e.target.value)
  }), H);
}
function Settings({
  cfg,
  setCfg,
  schema,
  locked,
  onSave,
  busy,
  toast
}) {
  const [br, setBr] = useState(null);
  const [q, setQ] = useState("");
  const [openG, setOpenG] = useState({});
  const [preview, setPreview] = useState(null);
  const [py, setPy] = useState(null);
  const setT = (k, v) => setCfg(c => ({
    ...c,
    [k]: v
  }));
  const setO = (k, v) => setCfg(c => ({
    ...c,
    driver_options: {
      ...c.driver_options,
      [k]: v
    }
  }));
  const sorting = !cfg.driver_options.skip_spikesorting;
  const ql = q.trim().toLowerCase();
  const groups = schema.groups.map(g => ({
    ...g,
    fields: g.fields.filter(f => !ql || f.key.includes(ql) || f.flag.includes(ql) || (f.help || "").toLowerCase().includes(ql))
  })).filter(g => g.fields.length);
  const doPreview = async () => {
    try {
      setPreview(await api("/api/preview", {
        method: "POST",
        body: JSON.stringify(onSave.payload())
      }));
    } catch (e) {
      toast("No preview", e.message, "error");
    }
  };
  const testPy = async () => {
    try {
      setPy(await api("/api/driver-python", {
        method: "POST",
        body: JSON.stringify({
          python: cfg.driver_python || ""
        })
      }));
    } catch (e) {
      toast("Test failed", e.message, "error");
    }
  };
  return React.createElement("div", {
    className: "rise"
  }, locked && React.createElement("div", {
    style: {
      marginBottom: 18
    }
  }, React.createElement(Callout, {
    kind: "amber",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, React.createElement("b", null, "Settings are locked while analyses are running."), " Changing them now could disturb the running work. They unlock as soon as the current analyses finish.")), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Where things are")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "in"
  }, "Recordings come from"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    id: "in",
    className: "inp mono",
    value: cfg.watch_dir,
    disabled: locked,
    onChange: e => setT("watch_dir", e.target.value)
  }), React.createElement("button", {
    className: "btn",
    disabled: locked,
    onClick: () => setBr(br === "in" ? null : "in")
  }, React.createElement(Folder, {
    s: 15
  }), " Choose")), React.createElement("span", {
    className: "hint-s"
  }, "The project folder that contains the date folders. It is only ever read, never changed."), br === "in" && React.createElement(Browser, {
    initial: cfg.watch_dir,
    onClose: () => setBr(null),
    onPick: p => setT("watch_dir", p)
  })), React.createElement("div", {
    className: "f",
    style: {
      marginBottom: 0
    }
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "out"
  }, "Results go to"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    id: "out",
    className: "inp mono",
    value: cfg.driver_options.output_dir ?? "",
    disabled: locked,
    onChange: e => setO("output_dir", e.target.value || null)
  }), React.createElement("button", {
    className: "btn",
    disabled: locked,
    onClick: () => setBr(br === "out" ? null : "out")
  }, React.createElement(Folder, {
    s: 15
  }), " Choose")), React.createElement("span", {
    className: "hint-s"
  }, "Each project gets its own folder here, with its results, scans, logs and reports."), br === "out" && React.createElement(Browser, {
    initial: cfg.driver_options.output_dir || "",
    onClose: () => setBr(null),
    onPick: p => setO("output_dir", p)
  }))))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "What to analyse")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement(Switch, {
    id: "net",
    checked: cfg.run_network,
    disabled: locked,
    onChange: v => setT("run_network", v),
    label: "Network analysis",
    hint: "Spikes and network bursts from each well's network recording."
  }), React.createElement(Switch, {
    id: "sort",
    checked: sorting,
    disabled: locked || !cfg.run_network,
    onChange: v => setO("skip_spikesorting", !v),
    label: "Spike sorting (slow \u2014 about an hour per well)",
    hint: sorting ? "On: separates individual neurons with the graphics card. Much slower." : "Off (recommended): counts spikes on each electrode. A few minutes per well, no graphics card needed."
  }), React.createElement(Switch, {
    id: "nwb",
    checked: !!cfg.nwb_convert,
    disabled: locked || !cfg.run_network,
    onChange: v => setT("nwb_convert", v),
    label: "Convert to NWB first (for sharing on DANDI)",
    hint: cfg.nwb_convert ? "On: each well is saved as an NWB file in the results folder, and the analysis reads it from there. Conversion adds a few seconds per well and about one more copy of the data on disk." : "Off: the analysis reads the original recordings directly. Turn on to also keep a standard NWB copy of every well."
  }), React.createElement(Switch, {
    id: "act",
    checked: cfg.run_activity,
    disabled: locked,
    onChange: v => setT("run_activity", v),
    label: "Activity scan",
    hint: "Whole-chip activity maps and quality checks. Takes seconds."
  }), React.createElement(Switch, {
    id: "stg",
    checked: !!cfg.stage_locally,
    disabled: locked,
    onChange: v => setT("stage_locally", v),
    label: "Use the fast local disk while working",
    hint: "Keeps big temporary files on the computer's fast disk and deletes them afterwards. Several times faster."
  })))), React.createElement("details", {
    className: "adv"
  }, React.createElement("summary", null, React.createElement("span", {
    className: "chev"
  }, React.createElement(Chev, {
    s: 14
  })), "Advanced settings \u2014 for whoever maintains the pipeline"), React.createElement("div", {
    className: "card",
    style: {
      marginTop: 8
    }
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "row2"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Confirm a copy has finished after (seconds)"), React.createElement("input", {
    className: "inp tnum",
    type: "number",
    min: "1",
    value: cfg.settle_seconds,
    disabled: locked,
    onChange: e => setT("settle_seconds", e.target.value)
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Check for new recordings every (seconds)"), React.createElement("input", {
    className: "inp tnum",
    type: "number",
    min: "1",
    value: cfg.poll_seconds,
    disabled: locked,
    onChange: e => setT("poll_seconds", e.target.value)
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Network analyses at once"), React.createElement("input", {
    className: "inp tnum",
    type: "number",
    min: "1",
    max: "8",
    value: cfg.max_concurrent_network ?? 1,
    disabled: locked,
    onChange: e => setT("max_concurrent_network", e.target.value)
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Activity scans at once"), React.createElement("input", {
    className: "inp tnum",
    type: "number",
    min: "1",
    max: "16",
    value: cfg.max_concurrent_activity ?? 2,
    disabled: locked,
    onChange: e => setT("max_concurrent_activity", e.target.value)
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Fast-disk folder"), React.createElement("input", {
    className: "inp mono",
    value: cfg.scratch_dir || "",
    disabled: locked,
    onChange: e => setT("scratch_dir", e.target.value)
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "NWB compression"), React.createElement("select", {
    className: "sel",
    value: cfg.nwb_compression || "gzip",
    disabled: locked,
    onChange: e => setT("nwb_compression", e.target.value)
  }, React.createElement("option", {
    value: "gzip"
  }, "Standard (gzip) \u2014 any reader and DANDI can open it"), React.createElement("option", {
    value: "maxwell"
  }, "MaxWell's own \u2014 smaller, needs MaxWell's plugin to read"))), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l"
  }, "Always keep this much free on it (GB)"), React.createElement("input", {
    className: "inp tnum",
    type: "number",
    min: "0",
    value: cfg.stage_min_free_gb ?? 200,
    disabled: locked,
    onChange: e => setT("stage_min_free_gb", e.target.value)
  }))), React.createElement(Switch, {
    id: "mk",
    checked: cfg.require_finished_marker,
    disabled: locked,
    onChange: v => setT("require_finished_marker", v),
    label: "Wait for MaxWell's 'finished' mark",
    hint: "Also require the recording software to have marked the recording complete."
  }), React.createElement(Switch, {
    id: "ex",
    checked: cfg.skip_settle_for_existing,
    disabled: locked,
    onChange: v => setT("skip_settle_for_existing", v),
    label: "Folders already here are ready",
    hint: "Skip the copy check for folders present when watching starts."
  }), React.createElement(Switch, {
    id: "dry",
    checked: cfg.dry_run,
    disabled: locked,
    onChange: v => setT("dry_run", v),
    label: "Test mode",
    hint: "Find recordings and show what would run, without running anything."
  }), React.createElement(Switch, {
    id: "lio",
    checked: cfg.logs_in_output !== false,
    disabled: locked,
    onChange: v => setT("logs_in_output", v),
    label: "Keep logs beside the results"
  }), React.createElement("div", {
    className: "f",
    style: {
      marginTop: 12
    }
  }, React.createElement("label", {
    className: "f-l"
  }, "Pipeline Python"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    className: "inp mono",
    placeholder: "(detected automatically)",
    value: cfg.driver_python ?? "",
    disabled: locked,
    onChange: e => setT("driver_python", e.target.value)
  }), React.createElement("button", {
    className: "btn",
    onClick: testPy
  }, "Test")), py && React.createElement(Callout, {
    kind: py.ok ? "green" : "red",
    icon: py.ok ? React.createElement(Check, {
      s: 17
    }) : React.createElement(Alert, {
      s: 17
    })
  }, React.createElement("span", {
    className: "mono"
  }, py.python), " \u2014 ", py.ok ? "has everything the pipeline needs." : `missing ${(py.missing || []).join(", ") || py.error}.`)), React.createElement("div", {
    className: "sec-h",
    style: {
      marginTop: 22
    }
  }, React.createElement("div", {
    className: "sec-t",
    style: {
      fontSize: 20
    }
  }, "Pipeline options"), React.createElement("div", {
    className: "sec-d"
  }, "Passed to MEA-Analysis")), React.createElement("input", {
    className: "inp",
    placeholder: "Search options\u2026",
    value: q,
    onChange: e => setQ(e.target.value),
    "aria-label": "Search options"
  }), groups.map(g => {
    const o = !!ql || !!openG[g.group];
    return React.createElement("div", {
      className: "grp",
      key: g.group
    }, React.createElement("button", {
      className: "grp-h",
      "aria-expanded": o,
      onClick: () => setOpenG(x => ({
        ...x,
        [g.group]: !x[g.group]
      }))
    }, React.createElement("span", {
      style: {
        display: "inline-flex",
        transform: o ? "rotate(90deg)" : "none",
        transition: "transform .2s"
      }
    }, React.createElement(Chev, {
      s: 13
    })), g.group, React.createElement("span", {
      className: "hint-s",
      style: {
        marginLeft: "auto"
      }
    }, g.fields.length)), o && React.createElement("div", {
      className: "grp-b"
    }, g.fields.map(f => React.createElement(Field, {
      key: f.key,
      spec: f,
      value: cfg.driver_options[f.key],
      onChange: locked ? () => {} : setO
    }))));
  }), React.createElement("div", {
    style: {
      marginTop: 16
    }
  }, React.createElement("button", {
    className: "btn",
    onClick: doPreview
  }, React.createElement(Lines, {
    s: 14
  }), " Show the exact command")), preview && (preview.commands || []).map(c => React.createElement("div", {
    key: c.job,
    style: {
      marginTop: 10
    }
  }, React.createElement("div", {
    className: "hint-s",
    style: {
      marginBottom: 4
    }
  }, c.job_label, preview.example_run ? ` · for ${preview.example_run}` : ""), React.createElement(Code, {
    text: c.command
  })))))), React.createElement("div", {
    className: "sticky",
    style: {
      background: "var(--sheet)",
      color: "var(--ink)",
      border: "1px solid var(--rule-2)"
    }
  }, React.createElement("div", {
    style: {
      flex: 1
    },
    className: "hint"
  }, "Changes apply to analyses started after you save."), React.createElement("button", {
    className: "btn ink",
    disabled: locked || busy,
    onClick: () => onSave()
  }, busy ? React.createElement("span", {
    className: "spin"
  }) : React.createElement(Check, {
    s: 14
  }), " Save settings")));
}
const fmtBytes = b => {
  if (b == null) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0,
    v = b;
  while (v >= 1024 && i < u.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v < 10 && i ? v.toFixed(1) : Math.round(v)} ${u[i]}`;
};
const pct = (a, b) => b ? Math.round(100 * a / b) : 0;
const WELL_OUT = {
  complete: ["finished", "ok"],
  silent: ["no activity", "queue"],
  not_recorded: ["not in the recording file", "wait"],
  failed: ["problem", "bad"],
  stopped: ["stopped", "bad"],
  running: ["in progress", "run"]
};
const RUN_SAY = {
  done: ["Done", "ok"],
  failed: ["Failed", "bad"],
  interrupted: ["Interrupted", "wait"],
  held: ["On hold", "wait"],
  running: ["Analysing", "run"],
  dispatched: ["Starting", "queue"],
  queued: ["In line", "queue"],
  detected: ["Found (test mode)", "wait"]
};
const runSay = st => RUN_SAY[st] || [st || "—", "wait"];
const jobName = j => j === "activity" ? "Activity scan" : "Network analysis";
const HEARTBEAT = /^running .+ · last log output .+ ago$/;
const goRun = id => {
  if (id) location.hash = "run/" + id;
};
const whenStarted = iso => {
  if (!iso) return "";
  const t = new Date(iso);
  if (isNaN(t)) return "";
  return t.toLocaleString([], {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  });
};
const startedBy = r => r && r.started_by ? `started by ${r.started_by}${r.dispatched_at || r.created ? ` · ${whenStarted(r.dispatched_at || r.created)}` : ""}` : "";
function Meter({
  value,
  max,
  label,
  sub,
  danger
}) {
  const f = max ? Math.min(100, 100 * value / max) : 0;
  return React.createElement("div", {
    className: "meter-row"
  }, React.createElement("div", {
    className: "meter-top"
  }, React.createElement("span", null, label), React.createElement("span", {
    className: "hint-s"
  }, sub)), React.createElement("div", {
    className: "meter"
  }, React.createElement("i", {
    style: {
      width: `${f}%`
    },
    "data-k": danger ? "bad" : f > 85 ? "warn" : "ok"
  })));
}
function SysHealth({
  sys
}) {
  if (!sys?.ready) return React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b hint",
    style: {
      display: "flex",
      gap: 10,
      alignItems: "center"
    }
  }, React.createElement("span", {
    className: "spin"
  }), " Measuring the computer\u2026"));
  const c = sys.cpu || {},
    m = sys.memory || {},
    g = sys.gpu || {};
  const mine = (sys.processes || []).filter(p => p.mine),
    others = (sys.processes || []).filter(p => !p.mine);
  const byUser = {};
  others.forEach(p => {
    byUser[p.user] = (byUser[p.user] || 0) + 1;
  });
  return React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "health"
  }, React.createElement("div", {
    className: "hcell"
  }, React.createElement("div", {
    className: "h-k"
  }, "Processors"), React.createElement("div", {
    className: "h-v tnum"
  }, c.percent == null ? "…" : `${Math.round(c.percent)}%`), React.createElement("div", {
    className: "hint-s"
  }, c.cores, " cores \xB7 load ", (c.load || [])[0], c.iowait_percent ? ` · waiting on disks ${Math.round(c.iowait_percent)}%` : "")), React.createElement("div", {
    className: "hcell"
  }, React.createElement("div", {
    className: "h-k"
  }, "Memory"), React.createElement("div", {
    className: "h-v tnum"
  }, m.total ? `${pct(m.used, m.total)}%` : "—"), React.createElement("div", {
    className: "hint-s"
  }, fmtBytes(m.available), " free of ", fmtBytes(m.total))), React.createElement("div", {
    className: "hcell"
  }, React.createElement("div", {
    className: "h-k"
  }, "Graphics card"), g.ok ? (g.gpus || []).map((x, i) => React.createElement(React.Fragment, {
    key: i
  }, React.createElement("div", {
    className: "h-v tnum"
  }, Math.round(x.util), "%"), React.createElement("div", {
    className: "hint-s"
  }, x.name, " \xB7 ", Math.round(x.mem_used_mb / 1024), " of ", Math.round(x.mem_total_mb / 1024), " GB \xB7 ", Math.round(x.temp_c), "\xB0C"))) : React.createElement(React.Fragment, null, React.createElement("div", {
    className: "h-v",
    style: {
      color: "var(--red)",
      fontSize: 22
    }
  }, "Not usable"), React.createElement("div", {
    className: "hint-s",
    style: {
      color: "var(--red)"
    }
  }, g.error)))), React.createElement("div", {
    className: "disks"
  }, React.createElement(Meter, {
    label: "Memory in use",
    value: m.used || 0,
    max: m.total,
    sub: `${fmtBytes(m.used)} / ${fmtBytes(m.total)}`
  }), Object.entries(sys.disks || {}).map(([k, d]) => d.error ? React.createElement("div", {
    className: "meter-row",
    key: k
  }, React.createElement("div", {
    className: "meter-top"
  }, React.createElement("span", null, k), React.createElement("span", {
    className: "hint-s",
    style: {
      color: "var(--red)"
    }
  }, d.error))) : React.createElement(Meter, {
    key: k,
    label: k,
    value: d.used,
    max: d.total,
    sub: `${fmtBytes(d.free)} free of ${fmtBytes(d.total)}`
  }))), React.createElement("div", {
    className: "sub-h"
  }, "Analysis programs running now"), mine.length === 0 ? React.createElement("div", {
    className: "hint"
  }, "None of yours.") : React.createElement("div", {
    className: "tw"
  }, React.createElement("table", {
    className: "tbl"
  }, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "What"), React.createElement("th", null, "Working on"), React.createElement("th", {
    className: "n"
  }, "Processor"), React.createElement("th", {
    className: "n"
  }, "Memory"), React.createElement("th", {
    className: "n"
  }, "Running for"))), React.createElement("tbody", null, mine.map(p => React.createElement("tr", {
    key: p.pid
  }, React.createElement("td", null, p.kind), React.createElement("td", {
    className: "mono"
  }, p.target || "—"), React.createElement("td", {
    className: "n"
  }, p.cpu_percent == null ? "…" : `${Math.round(p.cpu_percent)}%`), React.createElement("td", {
    className: "n"
  }, fmtBytes(p.rss)), React.createElement("td", {
    className: "n"
  }, dur(p.elapsed_s))))))), others.length > 0 && React.createElement("div", {
    className: "hint-s",
    style: {
      marginTop: 8
    }
  }, "Also on this computer: ", Object.entries(byUser).map(([u, n]) => `${n} analysis program${n === 1 ? "" : "s"} of ${u}`).join(", "), ".")));
}
function RunCard({
  r
}) {
  const p = r.progress || {},
    [say, k] = runSay(r.status),
    dt = prettyDate(r.date);
  return React.createElement("button", {
    className: "runcard rise",
    onClick: () => goRun(r.id)
  }, React.createElement("div", {
    className: "rc-top"
  }, React.createElement("span", {
    className: "rc-date"
  }, dt.big, " ", dt.year), React.createElement("span", {
    className: "stamp " + k
  }, say)), React.createElement("div", {
    className: "hint-s"
  }, prettyProject(r.project), " \xB7 ", jobName(r.job)), r.started_by && React.createElement("div", {
    className: "hint-s"
  }, startedBy(r)), r.job === "network" && React.createElement(React.Fragment, null, React.createElement("div", {
    className: "bar"
  }, React.createElement("i", {
    style: {
      width: `${p.fraction ? Math.round(100 * p.fraction) : 3}%`
    }
  })), React.createElement("div", {
    className: "rc-meta"
  }, p.total ? React.createElement("b", null, p.done, " of ", p.total, " wells") : React.createElement("b", null, p.done || 0, " wells finished"), p.seconds_left != null && React.createElement("span", null, " \xB7 about ", dur(p.seconds_left), " left"))), React.createElement("div", {
    className: "hint-s"
  }, "Running for ", dur(r.elapsed_s), r.last_output_age_s != null && ` · last activity ${dur(r.last_output_age_s)} ago`), r.conversion_summary && React.createElement("div", {
    className: "hint-s"
  }, "NWB: ", r.conversion_summary.converted, " converted, ", r.conversion_summary.reused, " reused"));
}
function HistoryTable({
  fixedLimit
}) {
  const [f, setF] = useState({
    project: "",
    job: "",
    status: ""
  });
  const [data, setData] = useState(null);
  const [limit, setLimit] = useState(fixedLimit || 25);
  const load = useCallback(() => {
    const q = new URLSearchParams({
      ...f,
      limit: String(limit)
    }).toString();
    api("/api/history?" + q).then(setData).catch(() => setData({
      runs: [],
      total: 0,
      projects: []
    }));
  }, [f, limit]);
  useEffect(() => {
    load();
    const t = setInterval(() => {
      if (!document.hidden) load();
    }, 15000);
    return () => clearInterval(t);
  }, [load]);
  if (!data) return React.createElement("div", {
    className: "skel",
    style: {
      height: 120
    }
  });
  return React.createElement(React.Fragment, null, !fixedLimit && React.createElement("div", {
    className: "filters"
  }, React.createElement("select", {
    className: "sel",
    value: f.project,
    onChange: e => setF({
      ...f,
      project: e.target.value
    }),
    "aria-label": "Project"
  }, React.createElement("option", {
    value: ""
  }, "All projects"), (data.projects || []).map(p => React.createElement("option", {
    key: p,
    value: p
  }, prettyProject(p)))), React.createElement("select", {
    className: "sel",
    value: f.job,
    onChange: e => setF({
      ...f,
      job: e.target.value
    }),
    "aria-label": "Analysis"
  }, React.createElement("option", {
    value: ""
  }, "Both analyses"), React.createElement("option", {
    value: "network"
  }, "Network analysis"), React.createElement("option", {
    value: "activity"
  }, "Activity scan")), React.createElement("select", {
    className: "sel",
    value: f.status,
    onChange: e => setF({
      ...f,
      status: e.target.value
    }),
    "aria-label": "Outcome"
  }, React.createElement("option", {
    value: ""
  }, "Any outcome"), React.createElement("option", {
    value: "done"
  }, "Done"), React.createElement("option", {
    value: "failed"
  }, "Failed"), React.createElement("option", {
    value: "interrupted"
  }, "Interrupted"), React.createElement("option", {
    value: "held"
  }, "On hold"), React.createElement("option", {
    value: "running,dispatched,queued"
  }, "Running or starting")), React.createElement("span", {
    className: "hint-s"
  }, data.total, " run", data.total === 1 ? "" : "s")), data.runs.length === 0 ? React.createElement("div", {
    className: "hint",
    style: {
      padding: "10px 2px"
    }
  }, "No runs match.") : React.createElement("div", {
    className: "tw"
  }, React.createElement("table", {
    className: "tbl hover"
  }, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "Recording date"), React.createElement("th", null, "Project"), React.createElement("th", null, "Analysis"), React.createElement("th", null, "Outcome"), React.createElement("th", null, "Started by"), React.createElement("th", {
    className: "n"
  }, "Took"), React.createElement("th", null, "Finished"))), React.createElement("tbody", null, data.runs.map(r => {
    const [say, k] = runSay(r.status),
      dt = prettyDate(r.date);
    return React.createElement("tr", {
      key: r.id,
      onClick: () => goRun(r.id),
      tabIndex: 0,
      onKeyDown: e => e.key === "Enter" && goRun(r.id)
    }, React.createElement("td", null, React.createElement("b", null, dt.big), " ", React.createElement("span", {
      className: "hint-s"
    }, dt.year)), React.createElement("td", null, prettyProject(r.project)), React.createElement("td", null, jobName(r.job)), React.createElement("td", null, React.createElement("span", {
      className: "stamp " + k
    }, say)), React.createElement("td", null, r.started_by || React.createElement("span", {
      className: "hint-s"
    }, "\u2014"), r.started_by && React.createElement("div", {
      className: "hint-s"
    }, whenStarted(r.created))), React.createElement("td", {
      className: "n"
    }, r.duration_s != null ? dur(r.duration_s) : "—"), React.createElement("td", {
      className: "hint-s"
    }, r.completed_at ? ago(r.completed_at) : "—"));
  })))), !fixedLimit && data.total > data.runs.length && React.createElement("div", {
    style: {
      marginTop: 10
    }
  }, React.createElement("button", {
    className: "btn sm",
    onClick: () => setLimit(l => l + 50)
  }, "Show more")));
}
function Dashboard() {
  const [ov, setOv] = useState(null);
  const [sys, setSys] = useState(null);
  useEffect(() => {
    const load = () => {
      if (document.hidden) return;
      api("/api/overview").then(setOv).catch(() => {});
      api("/api/system").then(setSys).catch(() => {});
    };
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);
  if (!ov) return React.createElement("div", {
    className: "skel",
    style: {
      height: 240
    }
  });
  const lim = ov.limits || {},
    act = ov.active_jobs || {};
  return React.createElement("div", {
    className: "rise"
  }, React.createElement("div", {
    className: "slots"
  }, React.createElement("span", {
    className: "dot " + (ov.watching ? "ok" : "wait")
  }), ov.watching ? "Watching for new recordings" : "Not watching for new recordings", React.createElement("span", {
    className: "hint-s"
  }, "\xB7 Network analyses running ", act.network || 0, " of ", lim.network || 1, " \xB7 Activity scans ", act.activity || 0, " of ", lim.activity || 1)), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Needs attention")), ov.attention.length === 0 ? React.createElement(Callout, {
    kind: "green",
    icon: React.createElement(Check, {
      s: 17
    })
  }, "Nothing needs attention.") : React.createElement("div", {
    className: "att"
  }, ov.attention.map((a, i) => React.createElement("div", {
    key: i,
    className: "att-i " + (a.level || "warn"),
    onClick: () => a.run_id && goRun(a.run_id),
    style: {
      cursor: a.run_id ? "pointer" : "default"
    }
  }, React.createElement("span", {
    className: "ic"
  }, a.level === "bad" ? React.createElement(Alert, {
    s: 17
  }) : React.createElement(Info, {
    s: 17
  })), React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, a.date && React.createElement("b", null, prettyDate(a.date).big, " ", prettyDate(a.date).year, " \xB7 ", jobName(a.job), " \u2014 "), a.text), a.run_id && React.createElement(Chev, {
    s: 15
  }))))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Running now"), React.createElement("div", {
    className: "sec-d"
  }, ov.running.length ? "Click a run for its wells, steps and log" : "Nothing is analysing at the moment")), ov.running.length > 0 && React.createElement("div", {
    className: "runcards"
  }, ov.running.map(r => React.createElement(RunCard, {
    key: r.id,
    r: r
  })))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "The computer"), React.createElement("div", {
    className: "sec-d"
  }, "Updates every few seconds")), React.createElement(SysHealth, {
    sys: sys
  })), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Run history"), React.createElement("div", {
    className: "sec-d"
  }, "Every analysis run, newest first")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement(HistoryTable, null)))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Who did what"), React.createElement("div", {
    className: "sec-d"
  }, "Sign-ins, queueing, holds, stops and settings changes")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement(Audit, null)))));
}
function Audit() {
  const [d, setD] = useState(null);
  const [n, setN] = useState(15);
  useEffect(() => {
    const load = () => {
      if (!document.hidden) api(`/api/audit?limit=${n}`).then(setD).catch(() => {});
    };
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [n]);
  if (!d) return React.createElement("div", {
    className: "skel",
    style: {
      height: 80
    }
  });
  if (!(d.entries || []).length) return React.createElement("div", {
    className: "hint"
  }, "Nothing yet.");
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "tw"
  }, React.createElement("table", {
    className: "tbl"
  }, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "When"), React.createElement("th", null, "Who"), React.createElement("th", null, "What"))), React.createElement("tbody", null, d.entries.map((e, i) => React.createElement("tr", {
    key: i
  }, React.createElement("td", {
    className: "hint-s",
    style: {
      whiteSpace: "nowrap"
    }
  }, whenStarted(e.time)), React.createElement("td", {
    title: e.email || ""
  }, e.name || "—"), React.createElement("td", {
    style: {
      whiteSpace: "normal"
    }
  }, e.action, e.detail ? React.createElement("span", {
    className: "hint-s"
  }, " \u2014 ", e.detail) : null)))))), d.entries.length >= n && React.createElement("button", {
    className: "btn sm",
    style: {
      marginTop: 10
    },
    onClick: () => setN(x => x + 50)
  }, "Show more"));
}
function RunDetail({
  id,
  onLog,
  onBack
}) {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  const [showAll, setShowAll] = useState(false);
  useEffect(() => {
    let t;
    setD(null);
    setErr("");
    const load = () => api("/api/history/" + id).then(x => {
      setD(x);
      if (!["done", "failed", "interrupted", "detected", "held"].includes(x.status) && !t) t = setInterval(() => {
        if (!document.hidden) load();
      }, 5000);else if (["done", "failed", "interrupted", "detected", "held"].includes(x.status) && t) {
        clearInterval(t);
        t = null;
      }
    }).catch(e => setErr(e.message));
    load();
    return () => t && clearInterval(t);
  }, [id]);
  if (err) return React.createElement("div", {
    className: "rise"
  }, React.createElement("button", {
    className: "btn sm",
    onClick: onBack
  }, "\u2190 Back"), React.createElement("div", {
    style: {
      marginTop: 16
    }
  }, React.createElement(Callout, {
    kind: "red",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, err)));
  if (!d) return React.createElement("div", {
    className: "skel",
    style: {
      height: 300
    }
  });
  const [say, k] = runSay(d.status),
    dt = prettyDate(d.date),
    ls = d.log_summary || {},
    p = d.progress || {};
  const wells = ls.wells || [],
    conv = ls.conversion || [];
  const probs = wells.filter(w => ["failed", "stopped"].includes(w.outcome));
  const shown = showAll ? wells : wells.slice(0, 60);
  const st = d.settings || {};
  const report = (d.outputs || []).find(o => o.report);
  return React.createElement("div", {
    className: "rise"
  }, React.createElement("button", {
    className: "btn sm",
    onClick: onBack
  }, "\u2190 Back"), React.createElement("div", {
    className: "rd-h"
  }, React.createElement("div", null, React.createElement("div", {
    className: "rd-t"
  }, dt.big, " ", dt.year), React.createElement("div", {
    className: "hint"
  }, prettyProject(d.project), " \xB7 ", jobName(d.job), " \xB7 folder ", React.createElement("span", {
    className: "mono"
  }, d.date), d.attempt > 1 && ` · run ${d.attempt} for this date`, d.imported ? " · imported from before history was kept" : "")), React.createElement("div", {
    className: "acts",
    style: {
      alignItems: "center"
    }
  }, React.createElement("span", {
    className: "stamp " + k,
    style: {
      fontSize: 13
    }
  }, say), report && React.createElement("a", {
    className: "btn ink sm",
    target: "_blank",
    rel: "noopener",
    href: `/api/reports/view?path=${encodeURIComponent(report.path)}`
  }, React.createElement(Doc, {
    s: 14
  }), " Report"), d.log && React.createElement("button", {
    className: "btn sm",
    onClick: () => onLog(d.log, `${dt.big} ${dt.year} · ${jobName(d.job)}`)
  }, React.createElement(Lines, {
    s: 14
  }), " Log"))), React.createElement("div", {
    className: "tally",
    style: {
      marginBottom: 22
    }
  }, React.createElement("div", {
    className: "tal"
  }, React.createElement("div", {
    className: "tal-k"
  }, "Started by"), React.createElement("div", {
    className: "rd-v"
  }, d.started_by || "—"), d.created && React.createElement("div", {
    className: "hint-s"
  }, whenStarted(d.created), d.started_by_email ? ` · ${d.started_by_email}` : "")), React.createElement("div", {
    className: "tal"
  }, React.createElement("div", {
    className: "tal-k"
  }, "Started"), React.createElement("div", {
    className: "rd-v"
  }, d.started_at ? ago(d.started_at) : "—")), React.createElement("div", {
    className: "tal"
  }, React.createElement("div", {
    className: "tal-k"
  }, ["done", "failed", "interrupted", "held"].includes(d.status) ? "Took" : "Running for"), React.createElement("div", {
    className: "rd-v"
  }, d.elapsed_s != null ? dur(d.elapsed_s) : "—")), React.createElement("div", {
    className: "tal"
  }, React.createElement("div", {
    className: "tal-k"
  }, "Finished"), React.createElement("div", {
    className: "rd-v"
  }, d.completed_at ? ago(d.completed_at) : "not yet")), React.createElement("div", {
    className: "tal"
  }, React.createElement("div", {
    className: "tal-k"
  }, "Wells"), React.createElement("div", {
    className: "rd-v"
  }, d.job === "network" ? `${(ls.counts || {}).complete || 0} finished${probs.length ? ` · ${probs.length} problem${probs.length === 1 ? "" : "s"}` : ""}` : (ls.summary || {}).wells ?? "—"))), d.error && React.createElement("div", {
    style: {
      marginBottom: 18
    }
  }, React.createElement(Callout, {
    kind: "red",
    icon: React.createElement(Alert, {
      s: 17
    })
  }, React.createElement("b", null, "What went wrong:"), " ", d.error)), d.live_detail && React.createElement("div", {
    style: {
      marginBottom: 18
    }
  }, React.createElement(Callout, {
    kind: "blue"
  }, d.live_detail)), d.job === "network" && !["done", "failed", "interrupted", "held"].includes(d.status) && React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Progress")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "bar",
    style: {
      height: 10
    }
  }, React.createElement("i", {
    style: {
      width: `${p.fraction ? Math.round(100 * p.fraction) : 3}%`
    }
  })), React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, p.total ? React.createElement("b", null, p.done, " of ", p.total, " wells done") : React.createElement("b", null, p.done || 0, " wells done"), p.seconds_left != null && React.createElement("span", null, " \xB7 about ", dur(p.seconds_left), " left"), !p.expected_known && React.createElement("span", {
    className: "hint-s"
  }, " \xB7 counting this date's wells\u2026"), d.last_output_age_s != null && React.createElement("span", {
    className: "hint-s"
  }, " \xB7 last activity ", dur(d.last_output_age_s), " ago"))))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Steps"), React.createElement("div", {
    className: "sec-d"
  }, "What happened, in order")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("ol", {
    className: "tl"
  }, (d.events || []).length === 0 && React.createElement("li", {
    className: "hint"
  }, "No step record \u2014 this run happened before history was kept."), (d.events || []).filter(e => e.status || !HEARTBEAT.test(e.message || "")).map((e, i) => React.createElement("li", {
    key: i,
    "data-k": runSay(e.status)[1]
  }, React.createElement("span", {
    className: "tl-t"
  }, e.time ? new Date(e.time).toLocaleString() : ""), React.createElement("span", null, e.status ? React.createElement("b", null, runSay(e.status)[0]) : null, e.status && e.message ? " — " : "", e.message))), ls.conversion_summary && React.createElement("li", {
    "data-k": "ok"
  }, React.createElement("span", {
    className: "tl-t"
  }, "NWB"), React.createElement("span", null, React.createElement("b", null, "Converted to NWB"), " \u2014 ", ls.conversion_summary.converted, " converted,", " ", ls.conversion_summary.reused, " reused, ", ls.conversion_summary.failed, " failed in ", dur(ls.conversion_summary.seconds))), ls.driver_seconds != null && React.createElement("li", {
    "data-k": "ok"
  }, React.createElement("span", {
    className: "tl-t"
  }, "Analysis"), React.createElement("span", null, React.createElement("b", null, "All wells analysed"), " in ", dur(ls.driver_seconds))))))), d.job === "network" && React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Wells"), React.createElement("div", {
    className: "sec-d"
  }, wells.length, " well", wells.length === 1 ? "" : "s", " in the log")), wells.length === 0 ? React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b hint"
  }, "No wells started yet.")) : React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "tw"
  }, React.createElement("table", {
    className: "tbl"
  }, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "Chip"), React.createElement("th", null, "Recording"), React.createElement("th", null, "Well"), React.createElement("th", null, "Outcome"), React.createElement("th", null, "Step reached"), React.createElement("th", {
    className: "n"
  }, "Spikes"), React.createElement("th", {
    className: "n"
  }, "Took"), React.createElement("th", null, "Why"))), React.createElement("tbody", null, shown.map((w, i) => {
    const [s2, k2] = WELL_OUT[w.outcome] || [w.outcome, "wait"];
    return React.createElement("tr", {
      key: i
    }, React.createElement("td", {
      className: "mono"
    }, w.chip), React.createElement("td", {
      className: "mono"
    }, w.run), React.createElement("td", null, +String(w.well).replace(/\D/g, "") + 1), React.createElement("td", null, React.createElement("span", {
      className: "stamp " + k2
    }, s2)), React.createElement("td", {
      className: "hint-s"
    }, w.phase), React.createElement("td", {
      className: "n"
    }, w.spikes != null ? w.spikes.toLocaleString() : "—"), React.createElement("td", {
      className: "n"
    }, w.seconds != null ? dur(w.seconds) : "—"), React.createElement("td", {
      className: "hint-s",
      style: {
        whiteSpace: "normal",
        maxWidth: 320
      }
    }, w.reason ? plainWellError({
      error: w.reason,
      status: "failed"
    }) : ""));
  })))), wells.length > 60 && React.createElement("button", {
    className: "btn sm",
    style: {
      marginTop: 10
    },
    onClick: () => setShowAll(x => !x)
  }, showAll ? "Show fewer" : `Show all ${wells.length}`)))), conv.length > 0 && React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "NWB conversion")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "tw"
  }, React.createElement("table", {
    className: "tbl"
  }, React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "Chip"), React.createElement("th", null, "Recording"), React.createElement("th", null, "Well"), React.createElement("th", null, "Result"), React.createElement("th", {
    className: "n"
  }, "Took"), React.createElement("th", null, "Why"))), React.createElement("tbody", null, conv.map((c, i) => React.createElement("tr", {
    key: i
  }, React.createElement("td", {
    className: "mono"
  }, c.chip), React.createElement("td", {
    className: "mono"
  }, c.run), React.createElement("td", null, +String(c.well).replace(/\D/g, "") + 1), React.createElement("td", null, React.createElement("span", {
    className: "stamp " + (c.outcome === "failed" ? "bad" : c.outcome === "not_recorded" ? "wait" : "ok")
  }, c.outcome === "not_recorded" ? "not in the file" : c.outcome)), React.createElement("td", {
    className: "n"
  }, c.seconds ? dur(c.seconds) : "—"), React.createElement("td", {
    className: "hint-s"
  }, c.reason || ""))))))))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "What it produced")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, (d.outputs || []).length === 0 ? React.createElement("div", {
    className: "hint"
  }, "Nothing yet.") : React.createElement("div", {
    className: "outs"
  }, d.outputs.map((o, i) => React.createElement("div", {
    className: "out",
    key: i
  }, React.createElement("div", null, React.createElement("b", null, o.label), " ", React.createElement("span", {
    className: "hint-s"
  }, o.count, " ", o.unit, o.bytes != null ? ` · ${fmtBytes(o.bytes)}` : "")), React.createElement("div", {
    className: "mono hint-s",
    style: {
      wordBreak: "break-all"
    }
  }, o.path), o.report && React.createElement("a", {
    className: "btn sm",
    target: "_blank",
    rel: "noopener",
    href: `/api/reports/view?path=${encodeURIComponent(o.path)}`
  }, React.createElement(Ext, {
    s: 13
  }), " Open"), o.log && React.createElement("button", {
    className: "btn sm",
    onClick: () => onLog(o.path, `${dt.big} ${dt.year} · ${jobName(d.job)}`)
  }, React.createElement(Lines, {
    s: 13
  }), " Open"))))))), React.createElement("div", {
    className: "sec"
  }, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Settings it ran with")), React.createElement("div", {
    className: "card"
  }, React.createElement("div", {
    className: "card-b"
  }, Object.keys(st).length === 0 ? React.createElement("div", {
    className: "hint"
  }, "Not recorded for this run (it happened before history was kept).") : React.createElement("dl", {
    className: "kv"
  }, React.createElement("dt", null, "Spike sorting"), React.createElement("dd", null, st.spike_sorting ? "On" : "Off (spike detection only)"), React.createElement("dt", null, "Converted to NWB first"), React.createElement("dd", null, st.nwb_convert ? `Yes (${st.nwb_compression === "maxwell" ? "MaxWell compression" : "standard compression"})` : "No"), React.createElement("dt", null, "Fast local disk"), React.createElement("dd", null, st.stage_locally ? `Yes — ${st.scratch_dir || "default folder"}` : "No"), React.createElement("dt", null, "Analyses at once"), React.createElement("dd", null, "Network ", st.max_concurrent_network, " \xB7 Activity scan ", st.max_concurrent_activity), React.createElement("dt", null, "Recordings from"), React.createElement("dd", {
    className: "mono"
  }, st.watch_dir), React.createElement("dt", null, "Results to"), React.createElement("dd", {
    className: "mono"
  }, st.output_dir)), d.command && React.createElement("details", {
    className: "adv"
  }, React.createElement("summary", null, React.createElement("span", {
    className: "chev"
  }, React.createElement(Chev, {
    s: 14
  })), "Exact command"), React.createElement(Code, {
    text: d.command
  }))))));
}
function App({
  user,
  onSignOut
}) {
  const [schema, setSchema] = useState(null);
  const [cfg, setCfg] = useState(null);
  const [status, setStatus] = useState(null);
  const [fatal, setFatal] = useState("");
  const VIEWS = ["dashboard", "progress", "add", "reports", "settings"];
  const [tab, setTab] = useState(() => {
    const h = location.hash.slice(1);
    if (VIEWS.includes(h)) return h;
    try {
      const t = localStorage.getItem("mea-tab");
      return VIEWS.includes(t) ? t : "dashboard";
    } catch (e) {
      return "dashboard";
    }
  });
  const [runId, setRunId] = useState(() => location.hash.startsWith("#run/") ? location.hash.slice(5) : null);
  const [reports, setReports] = useState({});
  const [wells, setWells] = useState({});
  const [openW, setOpenW] = useState({});
  const [log, setLog] = useState(null);
  const [feed, setFeed] = useState([]);
  const [toasts, setToasts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [confirmAsk, setConfirmAsk] = useState(null);
  const tid = useRef(0),
    seq = useRef(0),
    polling = useRef(false),
    openWRef = useRef({}),
    confirmRes = useRef(null);
  const toast = useCallback((t, m, k = "ok") => {
    const id = ++tid.current;
    setToasts(x => [...x, {
      id,
      t,
      m,
      k
    }]);
    setTimeout(() => setToasts(x => x.filter(y => y.id !== id)), k === "error" ? 9000 : 4500);
  }, []);
  const ask = useCallback(a => new Promise(res => {
    confirmRes.current = res;
    setConfirmAsk(a);
  }), []);
  const closeAsk = v => {
    setConfirmAsk(null);
    confirmRes.current && confirmRes.current(v);
  };
  useEffect(() => {
    try {
      localStorage.setItem("mea-tab", tab);
    } catch (e) {}
    if (!runId && location.hash.slice(1) !== tab) history.replaceState(null, "", "#" + tab);
  }, [tab, runId]);
  useEffect(() => {
    const h = () => {
      const t = location.hash.slice(1);
      if (t.startsWith("run/")) {
        setRunId(t.slice(4));
        window.scrollTo(0, 0);
        return;
      }
      setRunId(null);
      if (VIEWS.includes(t)) setTab(t);
    };
    addEventListener("hashchange", h);
    addEventListener("popstate", h);
    return () => {
      removeEventListener("hashchange", h);
      removeEventListener("popstate", h);
    };
  }, []);
  useEffect(() => {
    openWRef.current = openW;
  }, [openW]);
  useEffect(() => {
    (async () => {
      try {
        const [s, c] = await Promise.all([api("/api/schema"), api("/api/config")]);
        setSchema(s);
        setCfg(c);
      } catch (e) {
        setFatal(e.message);
      }
    })();
  }, []);
  const loadReports = useCallback(() => api("/api/reports").then(d => {
    const m = {};
    (d.reports || []).forEach(r => {
      m[`${r.project}/${r.label}`] = r;
    });
    setReports(m);
  }).catch(() => {}), []);
  const refresh = useCallback(async force => {
    if (polling.current || !force && document.hidden) return;
    polling.current = true;
    try {
      await Promise.all([api("/api/status").then(setStatus).catch(() => {}), api(`/api/logs?since=${seq.current}`).then(d => {
        if (d.lines?.length) {
          seq.current = d.last_seq;
          setFeed(a => [...a, ...d.lines].slice(-60));
        }
      }).catch(() => {})]);
    } finally {
      polling.current = false;
    }
  }, []);
  useEffect(() => {
    refresh(true);
    loadReports();
    const t = setInterval(() => refresh(false), 3000),
      r = setInterval(loadReports, 60000);
    const v = () => {
      if (!document.hidden) {
        refresh(true);
        loadReports();
      }
    };
    document.addEventListener("visibilitychange", v);
    return () => {
      clearInterval(t);
      clearInterval(r);
      document.removeEventListener("visibilitychange", v);
    };
  }, [refresh, loadReports]);
  const inFlight = useRef({});
  const fetchWells = useCallback(async (folder, logPath) => {
    if (inFlight.current[folder]) return;
    inFlight.current[folder] = true;
    try {
      const [d, lg] = await Promise.all([api(`/api/runs/checkpoints?path=${encodeURIComponent(folder)}`), logPath ? api(`/api/runs/log?path=${encodeURIComponent(logPath)}&tail=1000000`).catch(() => null) : null]);
      setWells(w => ({
        ...w,
        [folder]: {
          ...d,
          notes: lg ? parseWellNotes(lg.lines || []) : {}
        }
      }));
    } catch (e) {
      setWells(w => ({
        ...w,
        [folder]: {
          error: e.message
        }
      }));
    } finally {
      delete inFlight.current[folder];
    }
  }, []);
  const runningNet = useMemo(() => (status?.runs || []).filter(r => r.job === "network" && r.status === "running").map(r => [r.folder, r.log]), [status]);
  useEffect(() => {
    runningNet.forEach(([f, l]) => fetchWells(f, l));
    const t = setInterval(() => {
      if (!document.hidden) runningNet.forEach(([f, l]) => fetchWells(f, l));
    }, 20000);
    return () => clearInterval(t);
  }, [runningNet.map(x => x[0]).join("|"), fetchWells]);
  const loadLog = useCallback(async l => {
    try {
      const d = await api(`/api/runs/log?path=${encodeURIComponent(l.path)}&tail=600`);
      setLog(x => x && x.path === l.path ? {
        ...x,
        lines: d.lines,
        error: null
      } : x);
    } catch (e) {
      setLog(x => x && x.path === l.path ? {
        ...x,
        error: e.message
      } : x);
    }
  }, []);
  const logLive = !!log && (status?.runs || []).some(r => r.log === log.path && r.status === "running");
  useEffect(() => {
    if (!log || !logLive) return;
    const t = setInterval(() => loadLog(log), 4000);
    return () => clearInterval(t);
  }, [log?.path, logLive, loadLog]);
  const folders = useMemo(() => {
    const m = {};
    (status?.runs || []).forEach(r => {
      (m[r.folder] = m[r.folder] || {
        folder: r.folder,
        date: r.run,
        project: projectOf(r.folder),
        jobs: []
      }).jobs.push(r);
    });
    return Object.values(m).sort((a, b) => a.project.localeCompare(b.project) || b.date.localeCompare(a.date));
  }, [status]);
  if (fatal) return React.createElement("div", {
    className: "wrap"
  }, React.createElement("div", {
    className: "card rise",
    style: {
      maxWidth: 560,
      margin: "12vh auto"
    }
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "sec-t",
    style: {
      color: "var(--red)"
    }
  }, "Can\u2019t reach the analysis server"), React.createElement("p", {
    className: "hint"
  }, fatal), React.createElement("button", {
    className: "btn ink",
    onClick: () => location.reload()
  }, "Try again"))));
  if (!schema || !cfg) return React.createElement("div", {
    className: "wrap"
  }, React.createElement("div", {
    className: "skel",
    style: {
      height: 50,
      width: 300
    }
  }), React.createElement("div", {
    className: "skel",
    style: {
      height: 96,
      marginTop: 30
    }
  }), React.createElement("div", {
    className: "skel",
    style: {
      height: 260,
      marginTop: 20
    }
  }));
  const runs = status?.runs || [];
  const active = (status?.active_jobs?.network || 0) + (status?.active_jobs?.activity || 0);
  const watching = !!status?.running;
  const tally = {
    wait: folders.filter(f => ["dispatched", "waiting", "interrupted", "detected", "held"].includes(folderState(f.jobs))).length,
    run: folders.filter(f => folderState(f.jobs) === "running").length,
    done: folders.filter(f => folderState(f.jobs) === "done").length,
    bad: folders.filter(f => folderState(f.jobs) === "failed").length
  };
  const payload = () => ({
    watch_dir: cfg.watch_dir,
    driver_options: cfg.driver_options,
    h5_glob: cfg.h5_glob,
    assay_subfolder: cfg.assay_subfolder,
    run_network: !!cfg.run_network,
    run_activity: !!cfg.run_activity,
    activity_subfolder: cfg.activity_subfolder,
    activity_output_dir: cfg.activity_output_dir || "",
    activity_active_hz: Number(cfg.activity_active_hz),
    activity_figures: !!cfg.activity_figures,
    max_concurrent_network: Number(cfg.max_concurrent_network) || 1,
    max_concurrent_activity: Number(cfg.max_concurrent_activity) || 1,
    gpu_cooldown_seconds: Number(cfg.gpu_cooldown_seconds) || 0,
    queue_poll_seconds: Number(cfg.queue_poll_seconds) || 1,
    settle_seconds: Number(cfg.settle_seconds),
    poll_seconds: Number(cfg.poll_seconds),
    require_finished_marker: !!cfg.require_finished_marker,
    skip_settle_for_existing: !!cfg.skip_settle_for_existing,
    driver_python: cfg.driver_python || "",
    logs_in_output: cfg.logs_in_output !== false,
    stage_locally: !!cfg.stage_locally,
    scratch_dir: cfg.scratch_dir || "",
    stage_min_free_gb: Number(cfg.stage_min_free_gb) || 200,
    dry_run: !!cfg.dry_run,
    ai_requirements: cfg.ai_requirements || "",
    auto_handoff: cfg.auto_handoff !== false,
    nwb_convert: !!cfg.nwb_convert,
    nwb_python: cfg.nwb_python || "",
    nwb_compression: cfg.nwb_compression || "gzip"
  });
  const run_ = async (fn, ok, m) => {
    setBusy(true);
    try {
      await fn();
      if (ok) toast(ok, m);
      refresh(true);
    } catch (e) {
      toast("That didn’t work", e.message, "error");
    } finally {
      setBusy(false);
    }
  };
  const save = () => run_(() => api("/api/config", {
    method: "POST",
    body: JSON.stringify(payload())
  }), "Settings saved");
  save.payload = payload;
  const inLine = runs.some(r => ["dispatched", "queued", "running"].includes(r.status));
  const dateList = fs => fs.map(f => {
    const d = prettyDate(f.date);
    return `${d.big} ${d.year}`;
  }).join(", ");
  const startWatch = async () => {
    const intr = folders.filter(f => f.jobs.some(j => j.status === "interrupted"));
    let hold = false;
    if (intr.length) {
      const n = intr.length,
        s = n === 1 ? "" : "s";
      const a = await ask({
        title: `Continue ${n} interrupted date${s}?`,
        ok: n === 1 ? "Continue it" : "Continue them",
        alt: "Keep on hold",
        body: `${n === 1 ? "This date was" : "These dates were"} stopped before ${n === 1 ? "it" : "they"} finished: ${dateList(intr)}.\n\n` + `Continue ${n === 1 ? "it" : "them"} now, or keep ${n === 1 ? "it" : "them"} on hold and only watch for new dates. ` + `Dates on hold can be resumed later from Progress.`
      });
      if (!a) return;
      hold = a === "alt";
    }
    run_(async () => {
      if (!active && !inLine) await api("/api/config", {
        method: "POST",
        body: JSON.stringify(payload())
      });
      await api("/api/watcher/start" + (hold ? "?hold_interrupted=true" : ""), {
        method: "POST"
      });
    }, "Watching for new recordings", hold ? "Interrupted dates are on hold. New dates are picked up once copied." : "New dates are picked up automatically once copied.");
  };
  const onHold = async f => {
    const dt = prettyDate(f.date),
      running = f.jobs.some(j => j.status === "running");
    const paths = f.jobs.filter(j => HOLDABLE.includes(j.status)).map(j => j.path);
    if (!(await ask({
      title: `Put ${dt.big} on hold?`,
      danger: running,
      ok: running ? "Stop and hold" : "Put on hold",
      body: running ? "Its analysis is running and will be stopped now. Wells that already finished keep their results, " + "so resuming it later repeats only the well that was in progress." : "It will be taken off the queue and kept for later. Nothing is deleted. Press Resume on it when you want it analysed."
    }))) return;
    run_(() => api("/api/runs/hold", {
      method: "POST",
      body: JSON.stringify({
        paths
      })
    }), "On hold", `${dt.big} will not be analysed until you resume it.`);
  };
  const onResume = f => {
    const dt = prettyDate(f.date);
    run_(() => api("/api/queue", {
      method: "POST",
      body: JSON.stringify({
        folders: [f.folder]
      })
    }), "Resumed", `${dt.big} is back in the queue.`);
  };
  const holdable = runs.filter(r => HOLDABLE.includes(r.status));
  const resetQueue = async () => {
    const c = sts => holdable.filter(r => sts.includes(r.status)).length,
      pl = n => n === 1 ? "" : "s";
    const nRun = c(["running"]),
      nWait = c(["dispatched", "queued"]),
      nInt = c(["interrupted", "waiting"]);
    const lines = [nRun && `• ${nRun} running analysis job${pl(nRun)} will be stopped now`, nWait && `• ${nWait} waiting job${pl(nWait)} will be taken out of the queue`, nInt && `• ${nInt} interrupted job${pl(nInt)} will be kept from resuming`, watching && "• Watching for new recordings will be paused"].filter(Boolean);
    if (!(await ask({
      title: "Reset the queue?",
      danger: nRun > 0,
      ok: "Reset queue",
      body: lines.join("\n") + "\n\nThese dates are put “On hold”: nothing starts them until you press Resume on them — " + "for example after switching off Network analysis in Settings to run only the activity scan.\n\n" + "Finished results are kept. Wells that already finished keep theirs too, so resuming repeats only the well in progress."
    }))) return;
    run_(() => api("/api/queue/reset", {
      method: "POST"
    }), "Queue reset", "Nothing will start until you resume a date or add recordings.");
  };
  const pauseWatch = () => run_(() => api("/api/watcher/stop", {
    method: "POST"
  }), "Paused", "No new dates will be started. Analyses already running carry on.");
  const stopAll = async () => {
    if (!(await ask({
      title: "Stop all analyses?",
      danger: true,
      ok: "Stop everything",
      body: `${active} analysis job${active === 1 ? "" : "s"} will be stopped now. Dates that were in progress will need to be analysed again.`
    }))) return;
    run_(() => api("/api/watcher/stop?cancel_running=true", {
      method: "POST"
    }), "Stopped", "All analyses were stopped.");
  };
  const onWells = f => {
    const o = !openW[f.folder];
    setOpenW(x => ({
      ...x,
      [f.folder]: o
    }));
    const settled = folderState(f.jobs) === "done" && wells[f.folder] && !wells[f.folder].error;
    if (o && !settled) fetchWells(f.folder, f.jobs.find(j => j.job === "network")?.log);
  };
  const onLog = f => {
    const j = f.jobs.find(x => x.job === "network" && x.log) || f.jobs.find(x => x.log);
    if (!j) return;
    const dt = prettyDate(f.date);
    const l = {
      path: j.log,
      title: `${dt.big} ${dt.year} · ${j.job_label || j.job}`,
      lines: []
    };
    setLog(l);
    loadLog(l);
  };
  const onAgain = async f => {
    const dt = prettyDate(f.date);
    if (!(await ask({
      title: `Analyse ${dt.big} again?`,
      ok: "Analyse again",
      body: "Its results will be computed again from the recordings and replaced. This can take a while."
    }))) return;
    run_(async () => {
      for (const j of f.jobs) await api("/api/runs/reset", {
        method: "POST",
        body: JSON.stringify({
          path: j.path
        })
      });
      await api("/api/queue", {
        method: "POST",
        body: JSON.stringify({
          folders: [f.folder],
          rerun: true
        })
      });
    }, "Added again", `${dt.big} will be analysed again.`);
  };
  const openLogPath = (path, title) => {
    const l = {
      path,
      title,
      lines: []
    };
    setLog(l);
    loadLog(l);
  };
  const pickTab = k => {
    setRunId(null);
    setTab(k);
    history.pushState(null, "", "#" + k);
  };
  const TABS = [["dashboard", "Dashboard"], ["progress", "Progress", folders.length], ["add", "Add recordings"], ["reports", "AI report", Object.keys(reports).length], ["settings", "Settings"]];
  return React.createElement("div", {
    className: "wrap"
  }, React.createElement("h1", {
    className: "sr"
  }, "MEA Bench \u2014 analysis control"), React.createElement("header", {
    className: "top rise",
    style: {
      "--i": 0
    }
  }, React.createElement("div", null, React.createElement("div", {
    className: "brand"
  }, "MEA ", React.createElement("i", null, "Bench")), React.createElement("div", {
    className: "brand-sub"
  }, "Ben-Shalom Lab \xB7 recordings in, reports out")), React.createElement("div", {
    className: "grow"
  }), React.createElement("div", {
    className: "ctrl"
  }, React.createElement("span", {
    className: "livechip"
  }, React.createElement("i", {
    className: "dot " + (active ? "run" : watching ? "ok" : "wait")
  }), active ? React.createElement(React.Fragment, null, React.createElement("b", null, active), " analysing now") : watching ? "Watching for new recordings" : "Idle"), watching ? React.createElement("button", {
    className: "btn",
    disabled: busy,
    onClick: pauseWatch
  }, React.createElement(Pause, {
    s: 14
  }), " Pause watching") : React.createElement("button", {
    className: "btn",
    disabled: busy,
    onClick: startWatch,
    title: "Automatically analyse new dates as they are copied in"
  }, React.createElement(Play, {
    s: 12
  }), " Watch for new"), active > 0 && React.createElement("button", {
    className: "btn red",
    disabled: busy,
    onClick: stopAll
  }, React.createElement(Stop, {
    s: 12
  }), " Stop all"), React.createElement("span", {
    className: "me",
    title: user.email
  }, user.name, React.createElement("button", {
    className: "btn ghost sm",
    onClick: onSignOut
  }, "Sign out")))), React.createElement("nav", {
    className: "tabs",
    role: "tablist"
  }, TABS.map(([k, l, n]) => React.createElement("button", {
    key: k,
    role: "tab",
    className: "tab",
    "aria-selected": !runId && tab === k,
    onClick: () => pickTab(k)
  }, l, n ? React.createElement("span", {
    className: "n"
  }, n) : null))), React.createElement("div", {
    className: "tabline"
  }), runId && React.createElement(RunDetail, {
    id: runId,
    onLog: openLogPath,
    onBack: () => {
      location.hash = tab;
    }
  }), !runId && tab === "dashboard" && React.createElement(Dashboard, null), !runId && tab === "progress" && React.createElement(React.Fragment, null, React.createElement("div", {
    className: "tally rise",
    style: {
      "--i": 1
    }
  }, [["wait", "Waiting"], ["run", "Analysing"], ["done", "Done"], ["bad", "Need attention"]].map(([k, l]) => React.createElement("div", {
    className: "tal",
    key: k,
    "data-k": k,
    "data-on": tally[k] > 0
  }, React.createElement("div", {
    className: "tal-v"
  }, status ? tally[k] : "–"), React.createElement("div", {
    className: "tal-k"
  }, l, " ", React.createElement("span", {
    className: "hint-s"
  }, "dates"))))), holdable.length > 0 && React.createElement("div", {
    className: "qbar rise",
    style: {
      "--i": 1
    }
  }, React.createElement("button", {
    className: "btn sm",
    disabled: busy,
    onClick: resetQueue,
    title: "Stop and hold everything that has not finished, so you can decide what to run"
  }, React.createElement(Again, {
    s: 13
  }), " Reset queue")), React.createElement(Progress, {
    folders: folders,
    reports: reports,
    wells: wells,
    openW: openW,
    onWells: onWells,
    onLog: onLog,
    onAgain: onAgain,
    onHold: onHold,
    onResume: onResume,
    feed: feed,
    goAdd: () => setTab("add")
  })), !runId && tab === "add" && React.createElement(AddRecordings, {
    cfg: cfg,
    toast: toast,
    ask: ask,
    onQueued: () => {
      refresh(true);
      setTab("progress");
    }
  }), !runId && tab === "reports" && React.createElement(AiReport, {
    cfg: cfg,
    reports: reports,
    toast: toast
  }), !runId && tab === "settings" && React.createElement(Settings, {
    cfg: cfg,
    setCfg: setCfg,
    schema: schema,
    locked: active > 0,
    onSave: save,
    busy: busy,
    toast: toast
  }), React.createElement("div", {
    className: "foot"
  }, React.createElement("span", null, "Orchestration-MEA"), React.createElement("span", null, "\xB7"), React.createElement("span", null, "recordings are only ever read, never changed")), log && React.createElement(LogDrawer, {
    log: log,
    live: logLive,
    onClose: () => setLog(null)
  }), React.createElement(Confirm, {
    ask: confirmAsk,
    onClose: closeAsk
  }), React.createElement(Toasts, {
    items: toasts,
    close: id => setToasts(t => t.filter(x => x.id !== id))
  }));
}
function Login({
  onIn
}) {
  const [name, setName] = useState(() => {
    try {
      return localStorage.getItem("mea-name") || "";
    } catch (e) {
      return "";
    }
  });
  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem("mea-email") || "";
    } catch (e) {
      return "";
    }
  });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const go = async e => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const r = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({
          name,
          email
        })
      });
      try {
        localStorage.setItem("mea-name", name);
        localStorage.setItem("mea-email", email);
      } catch (x) {}
      onIn(r.user);
    } catch (x) {
      setErr(x.message);
    } finally {
      setBusy(false);
    }
  };
  return React.createElement("div", {
    className: "wrap"
  }, React.createElement("div", {
    className: "card rise login",
    style: {
      maxWidth: 440,
      margin: "12vh auto"
    }
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "brand"
  }, "MEA ", React.createElement("i", null, "Bench")), React.createElement("div", {
    className: "brand-sub",
    style: {
      marginBottom: 20
    }
  }, "Ben-Shalom Lab \xB7 recordings in, reports out"), React.createElement("form", {
    onSubmit: go,
    noValidate: true
  }, React.createElement("label", {
    className: "f"
  }, React.createElement("span", {
    className: "f-l"
  }, "Your name"), React.createElement("input", {
    className: "inp",
    name: "name",
    autoComplete: "name",
    value: name,
    onChange: e => setName(e.target.value),
    autoFocus: true
  })), React.createElement("label", {
    className: "f"
  }, React.createElement("span", {
    className: "f-l"
  }, "Email"), React.createElement("input", {
    className: "inp",
    name: "email",
    type: "email",
    autoComplete: "email",
    value: email,
    onChange: e => setEmail(e.target.value)
  })), React.createElement("div", {
    className: "hint-s",
    style: {
      margin: "4px 0 14px"
    }
  }, "No password. Your name is shown on every analysis you start, so others know whose it is."), err && React.createElement("div", {
    style: {
      marginBottom: 12
    }
  }, React.createElement(Callout, {
    kind: "red",
    icon: React.createElement(Alert, {
      s: 16
    })
  }, err)), React.createElement("button", {
    className: "btn ink",
    type: "submit",
    disabled: busy
  }, busy ? React.createElement("span", {
    className: "spin"
  }) : null, " Sign in")))));
}
function Root() {
  const [user, setUser] = useState(undefined);
  const [err, setErr] = useState("");
  useEffect(() => {
    api("/api/me").then(r => setUser(r.user || null)).catch(e => setErr(e.message));
    const out = () => setUser(null);
    addEventListener("mea-signed-out", out);
    return () => removeEventListener("mea-signed-out", out);
  }, []);
  const signOut = async () => {
    try {
      await api("/api/logout", {
        method: "POST"
      });
    } catch (e) {}
    setUser(null);
  };
  if (err) return React.createElement("div", {
    className: "wrap"
  }, React.createElement("div", {
    className: "card rise",
    style: {
      maxWidth: 560,
      margin: "12vh auto"
    }
  }, React.createElement("div", {
    className: "card-b"
  }, React.createElement("div", {
    className: "sec-t",
    style: {
      color: "var(--red)"
    }
  }, "Can\u2019t reach the analysis server"), React.createElement("p", {
    className: "hint"
  }, err), React.createElement("button", {
    className: "btn ink",
    onClick: () => location.reload()
  }, "Try again"))));
  if (user === undefined) return React.createElement("div", {
    className: "wrap"
  }, React.createElement("div", {
    className: "skel",
    style: {
      height: 50,
      width: 300
    }
  }));
  if (!user) return React.createElement(Login, {
    onIn: setUser
  });
  return React.createElement(App, {
    key: user.email,
    user: user,
    onSignOut: signOut
  });
}
ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(Root, null));
