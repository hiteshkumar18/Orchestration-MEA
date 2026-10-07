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
    k: "line"
  },
  queued: {
    say: "In line",
    k: "line"
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
function plainWellError(r) {
  const e = String(r.error || "");
  if (/stream_id well\d+ is not in/.test(e)) return "Not in this recording file — nothing to analyse.";
  if (/n_samples=\d+ should be >= n_clusters/.test(e)) return "Almost no activity in this well.";
  if (/out of memory/i.test(e)) return "Ran out of memory.";
  if (r.status !== "complete" && !e) return "Stopped without an error message.";
  return (e.split("\n").find(Boolean) || "Unknown problem").slice(0, 180);
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
  }, "Cancel"), React.createElement("button", {
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
  data
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
  const chips = {};
  rows.forEach(r => {
    const k = `${r.chip_id || "?"}·${r.run_id || ""}`;
    (chips[k] = chips[k] || {
      chip: r.chip_id,
      run: r.run_id,
      wells: {}
    }).wells[r.well] = r;
  });
  const s = data.summary || {};
  const probs = rows.filter(r => r.status === "failed" || r.status !== "complete" && r.error);
  let i = 0;
  return React.createElement(React.Fragment, null, React.createElement("div", {
    className: "legend"
  }, React.createElement("span", null, React.createElement("b", null, s.complete || 0), "\xA0of ", s.wells || rows.length, " wells finished"), React.createElement("span", null, React.createElement("i", {
    className: "dot ok"
  }), " finished"), React.createElement("span", null, React.createElement("i", {
    className: "dot run"
  }), " in progress"), React.createElement("span", null, React.createElement("i", {
    className: "dot bad"
  }), " problem")), React.createElement("div", {
    className: "plates"
  }, Object.values(chips).map(c => {
    const ids = Object.keys(c.wells).map(w => +w.replace(/\D/g, ""));
    const n = Math.max(6, Math.ceil((Math.max(...ids) + 1) / 6) * 6);
    return React.createElement("div", {
      className: "plate",
      key: c.chip + c.run
    }, React.createElement("div", {
      className: "plate-h"
    }, "Chip ", React.createElement("b", null, c.chip || "?"), React.createElement("span", {
      className: "hint-s"
    }, "recording ", c.run)), React.createElement("div", {
      className: "wells"
    }, Array.from({
      length: n
    }, (_, k) => {
      const r = c.wells[`well${String(k).padStart(3, "0")}`];
      const cls = !r ? "none" : r.status === "complete" ? "complete" : r.status === "failed" ? "failed" : "running";
      const tip = !r ? "Not part of this recording" : r.status === "complete" ? `Well ${k + 1}: finished` : r.status === "failed" ? `Well ${k + 1}: ${plainWellError(r)}` : `Well ${k + 1}: ${r.stage_name || "in progress"}`;
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
  }, r.chip_id, " \xB7 well ", +r.well.replace(/\D/g, "") + 1), React.createElement("span", null, plainWellError(r))))));
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
function Line({
  f,
  report,
  wells,
  open,
  onWells,
  onLog,
  onAgain,
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
  }, sum.complete, " wells finished so far"), note && React.createElement("span", {
    className: "note-l " + note.k
  }, note.t)), React.createElement("div", {
    className: "lanes"
  }, [["Network", net], ["Activity scan", scan]].filter(x => x[1]).map(([n, j]) => {
    const x = jobInfo(j.status);
    return React.createElement("span", {
      className: "lane",
      key: n
    }, React.createElement("i", {
      className: "dot " + (x.k === "ok" ? "ok" : x.k === "bad" ? "bad" : x.k === "run" ? "run" : x.k === "line" ? "line" : "wait")
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
  }), " Log"), React.createElement("button", {
    className: "btn ghost sm",
    title: "Analyse this date again",
    "aria-label": "Analyse again",
    onClick: () => onAgain(f)
  }, React.createElement(Again, {
    s: 14
  })))), open && React.createElement("div", {
    className: "plate-wrap"
  }, React.createElement(Plates, {
    data: wells
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
    onAgain: onAgain
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
    return j.length > 0 && j.every(x => x.status === "done");
  };
  const partly = p => !done(p) && (info[p]?.jobs || []).some(x => x.status === "done");
  const chosen = Object.keys(sel).filter(k => sel[k]);
  const chosenDone = chosen.filter(done).length;
  const fresh = (entries || []).filter(x => !done(x.path) && x.finished !== false);
  const go = async () => {
    if (chosenDone && again && !(await ask({
      title: "Analyse again?",
      ok: "Analyse again",
      body: `${chosenDone} of these dates were already analysed. Their results will be computed again and replaced.`
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
      toast(`${n} date${n === 1 ? "" : "s"} added`, "They will be analysed in order. Follow them under Progress.");
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
      dn = done(x.path);
    const jobs = (info[x.path]?.jobs || []).map(j => j.label).join(" + ");
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
    }), dn ? React.createElement("span", {
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
    }, jobs || info[x.path]?.note || " "), React.createElement("span", {
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
  }, React.createElement("b", null, chosen.length, " date", chosen.length === 1 ? "" : "s", " selected"), chosenDone > 0 && React.createElement("label", {
    style: {
      display: "flex",
      gap: 8,
      alignItems: "center",
      marginTop: 4,
      fontSize: 13,
      cursor: "pointer"
    }
  }, React.createElement("input", {
    type: "checkbox",
    checked: again,
    onChange: e => setAgain(e.target.checked)
  }), "Also redo the ", chosenDone, " already analysed")), React.createElement("button", {
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
  useEffect(() => {
    api("/api/handoff").then(d => d?.state && d.state !== "idle" && setLast(d)).catch(() => {});
  }, []);
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
      const r = await api("/api/handoff", {
        method: "POST",
        body: JSON.stringify({
          folders: []
        })
      });
      setLast({
        state: "done",
        ...r
      });
    } catch (e) {
      toast("Could not prepare", e.message, "error");
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
  }, "Reports appear here as each recording date finishes, a few minutes after its analyses complete."))) : Object.entries(byP).map(([p, rs]) => React.createElement("div", {
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
  })), "Report packages for Claude"), React.createElement(Switch, {
    id: "ai-auto",
    checked: auto,
    onChange: v => {
      setAuto(v);
      save(v);
    },
    label: "Make a package when a batch of added dates finishes",
    hint: "Leave this off while the lab's report service is writing a report for each date \u2014 otherwise every batch gets two packages."
  }), React.createElement("div", {
    className: "hint",
    style: {
      margin: "6px 0 12px"
    }
  }, "Bundles all results with these instructions into one folder that Claude can turn into a report covering every date."), React.createElement("button", {
    className: "btn",
    disabled: busy,
    onClick: prepare
  }, busy ? React.createElement("span", {
    className: "spin"
  }) : React.createElement(Doc, {
    s: 14
  }), " Prepare package for all results"), last?.state === "done" && last.prompt && React.createElement("div", {
    style: {
      marginTop: 12
    }
  }, React.createElement(Callout, {
    kind: "green",
    icon: React.createElement(Check, {
      s: 17
    })
  }, "Package ready \u2014 ", last.network_wells, " wells, ", last.activity_runs, " scans. In a terminal on the analysis computer, run:"), React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, React.createElement(Code, {
    text: last.instruction
  }))), last?.state === "error" && React.createElement("div", {
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
function App() {
  const [schema, setSchema] = useState(null);
  const [cfg, setCfg] = useState(null);
  const [status, setStatus] = useState(null);
  const [fatal, setFatal] = useState("");
  const [tab, setTab] = useState(() => {
    const h = location.hash.slice(1);
    if (["progress", "add", "reports", "settings"].includes(h)) return h;
    try {
      return localStorage.getItem("mea-tab") || "progress";
    } catch (e) {
      return "progress";
    }
  });
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
    if (location.hash.slice(1) !== tab) history.replaceState(null, "", "#" + tab);
  }, [tab]);
  useEffect(() => {
    const h = () => {
      const t = location.hash.slice(1);
      if (["progress", "add", "reports", "settings"].includes(t)) setTab(t);
    };
    addEventListener("hashchange", h);
    return () => removeEventListener("hashchange", h);
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
  const fetchWells = useCallback(async folder => {
    if (inFlight.current[folder]) return;
    inFlight.current[folder] = true;
    try {
      const d = await api(`/api/runs/checkpoints?path=${encodeURIComponent(folder)}`);
      setWells(w => ({
        ...w,
        [folder]: d
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
  const runningFolders = useMemo(() => [...new Set((status?.runs || []).filter(r => r.job === "network" && r.status === "running").map(r => r.folder))], [status]);
  useEffect(() => {
    runningFolders.forEach(fetchWells);
    const t = setInterval(() => {
      if (!document.hidden) runningFolders.forEach(fetchWells);
    }, 20000);
    return () => clearInterval(t);
  }, [runningFolders.join("|"), fetchWells]);
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
    wait: folders.filter(f => ["dispatched", "waiting", "interrupted", "detected"].includes(folderState(f.jobs))).length,
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
    auto_handoff: cfg.auto_handoff !== false
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
  const startWatch = () => run_(async () => {
    if (!active) await api("/api/config", {
      method: "POST",
      body: JSON.stringify(payload())
    });
    await api("/api/watcher/start", {
      method: "POST"
    });
  }, "Watching for new recordings", "New dates are picked up automatically once copied.");
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
    if (o && !settled) fetchWells(f.folder);
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
  const TABS = [["progress", "Progress", folders.length], ["add", "Add recordings"], ["reports", "AI report", Object.keys(reports).length], ["settings", "Settings"]];
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
  }), " Stop all"))), React.createElement("nav", {
    className: "tabs",
    role: "tablist"
  }, TABS.map(([k, l, n]) => React.createElement("button", {
    key: k,
    role: "tab",
    className: "tab",
    "aria-selected": tab === k,
    onClick: () => setTab(k)
  }, l, n ? React.createElement("span", {
    className: "n"
  }, n) : null))), React.createElement("div", {
    className: "tabline"
  }), tab === "progress" && React.createElement(React.Fragment, null, React.createElement("div", {
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
  }, "dates"))))), React.createElement(Progress, {
    folders: folders,
    reports: reports,
    wells: wells,
    openW: openW,
    onWells: onWells,
    onLog: onLog,
    onAgain: onAgain,
    feed: feed,
    goAdd: () => setTab("add")
  })), tab === "add" && React.createElement(AddRecordings, {
    cfg: cfg,
    toast: toast,
    ask: ask,
    onQueued: () => {
      refresh(true);
      setTab("progress");
    }
  }), tab === "reports" && React.createElement(AiReport, {
    cfg: cfg,
    reports: reports,
    toast: toast
  }), tab === "settings" && React.createElement(Settings, {
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
ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App, null));
