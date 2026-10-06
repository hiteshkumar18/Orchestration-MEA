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
  f = "none"
}) => React.createElement("svg", {
  width: s,
  height: s,
  viewBox: "0 0 24 24",
  fill: f,
  stroke: "currentColor",
  strokeWidth: "1.7",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": "true"
}, d);
const Wave = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("polyline", {
    points: "22 12 18 12 15 21 9 3 6 12 2 12"
  })
}));
const Folder = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("path", {
    d: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
  })
}));
const Play = p => React.createElement(I, _extends({}, p, {
  f: "currentColor",
  d: React.createElement("polygon", {
    points: "6 4 20 12 6 20"
  })
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
const Ex = p => React.createElement(I, _extends({}, p, {
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
const Search = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("circle", {
    cx: "11",
    cy: "11",
    r: "7"
  }), React.createElement("line", {
    x1: "21",
    y1: "21",
    x2: "16.65",
    y2: "16.65"
  }))
}));
const Chev = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("polyline", {
    points: "9 18 15 12 9 6"
  })
}));
const Copy = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("rect", {
    x: "9",
    y: "9",
    width: "13",
    height: "13",
    rx: "2.5"
  }), React.createElement("path", {
    d: "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
  }))
}));
const Term = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("polyline", {
    points: "4 17 10 11 4 5"
  }), React.createElement("line", {
    x1: "12",
    y1: "19",
    x2: "20",
    y2: "19"
  }))
}));
const Sync = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("polyline", {
    points: "23 4 23 10 17 10"
  }), React.createElement("path", {
    d: "M20.49 15a9 9 0 1 1-2.12-9.36L23 10"
  }))
}));
const Moon = p => React.createElement(I, _extends({}, p, {
  d: React.createElement("path", {
    d: "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
  })
}));
const Sun = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "4.5"
  }), React.createElement("line", {
    x1: "12",
    y1: "1.5",
    x2: "12",
    y2: "3.5"
  }), React.createElement("line", {
    x1: "12",
    y1: "20.5",
    x2: "12",
    y2: "22.5"
  }), React.createElement("line", {
    x1: "4.2",
    y1: "4.2",
    x2: "5.7",
    y2: "5.7"
  }), React.createElement("line", {
    x1: "18.3",
    y1: "18.3",
    x2: "19.8",
    y2: "19.8"
  }), React.createElement("line", {
    x1: "1.5",
    y1: "12",
    x2: "3.5",
    y2: "12"
  }), React.createElement("line", {
    x1: "20.5",
    y1: "12",
    x2: "22.5",
    y2: "12"
  }), React.createElement("line", {
    x1: "4.2",
    y1: "19.8",
    x2: "5.7",
    y2: "18.3"
  }), React.createElement("line", {
    x1: "18.3",
    y1: "5.7",
    x2: "19.8",
    y2: "4.2"
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
const Alert = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("path", {
    d: "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
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
const Inbox = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("polyline", {
    points: "22 12 16 12 14 15 10 15 8 12 2 12"
  }), React.createElement("path", {
    d: "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
  }))
}));
const Clock = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9.5"
  }), React.createElement("polyline", {
    points: "12 6.5 12 12 16 14"
  }))
}));
const Slide = p => React.createElement(I, _extends({}, p, {
  d: React.createElement(React.Fragment, null, React.createElement("line", {
    x1: "4",
    y1: "8",
    x2: "20",
    y2: "8"
  }), React.createElement("line", {
    x1: "4",
    y1: "16",
    x2: "20",
    y2: "16"
  }), React.createElement("circle", {
    cx: "9",
    cy: "8",
    r: "2.4"
  }), React.createElement("circle", {
    cx: "15",
    cy: "16",
    r: "2.4"
  }))
}));
const IS_FILE = location.protocol === "file:";
const H_FILE = "This page is open as a local file, so it cannot reach the server.\n\n" + "Start the backend and open it through that instead:\n\n" + "    python orchestration/api.py --port 8000\n\nthen visit http://localhost:8000";
const H_DOWN = "Could not reach the API server.\n\nMake sure it is running:\n\n" + "    python orchestration/api.py --port 8000\n\n" + "and that this page is open at the same host and port.";
async function api(path, opts) {
  if (IS_FILE) throw new Error(H_FILE);
  let r;
  try {
    r = await fetch(path, {
      headers: {
        "Content-Type": "application/json"
      },
      ...opts
    });
  } catch (e) {
    throw new Error(H_DOWN);
  }
  const b = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = b.detail;
    throw new Error(d?.errors ? d.errors.join("\n") : typeof d === "string" ? d : "Request failed");
  }
  return b;
}
const ST = {
  waiting: {
    l: "Waiting",
    c: "p-n",
    i: 0
  },
  detected: {
    l: "Detected",
    c: "p-a",
    i: 1
  },
  dispatched: {
    l: "Queued",
    c: "p-a",
    i: 2
  },
  running: {
    l: "Analyzing",
    c: "p-a",
    i: 2
  },
  done: {
    l: "Complete",
    c: "p-o",
    i: 3
  },
  failed: {
    l: "Failed",
    c: "p-b",
    i: 3
  },
  interrupted: {
    l: "Interrupted",
    c: "p-n",
    i: 1
  }
};
const STAGES = ["Detected", "Settled", "Analyzing", "Complete"];
const settleLeft = d => {
  const m = /settling \((\d+)s remaining\)/.exec(d || "");
  return m ? +m[1] : null;
};
const ago = iso => {
  if (!iso) return "";
  const s = Math.max(0, (Date.now() - new Date(iso)) / 1e3);
  return s < 60 ? `${s | 0}s ago` : s < 3600 ? `${s / 60 | 0}m ago` : s < 86400 ? `${s / 3600 | 0}h ago` : `${s / 86400 | 0}d ago`;
};
const dur = s => {
  if (s == null) return "";
  if (s < 60) return `${Math.round(s)}s`;
  const m = s / 60 | 0;
  return m < 60 ? `${m}m ${Math.round(s % 60)}s` : `${m / 60 | 0}h ${m % 60}m`;
};
function Switch({
  checked,
  onChange,
  label,
  hint,
  id,
  disabled
}) {
  return React.createElement("div", {
    className: "sw-row",
    style: disabled ? {
      opacity: .5
    } : undefined
  }, React.createElement("button", {
    type: "button",
    role: "switch",
    "aria-checked": !!checked,
    id: id,
    disabled: disabled,
    className: "sw",
    "data-on": !!checked,
    onClick: () => !disabled && onChange(!checked)
  }, React.createElement("span", {
    className: "sw-k"
  })), React.createElement("label", {
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
  text,
  scroll
}) {
  const [c, setC] = useState(false);
  return React.createElement("div", {
    className: "code-w"
  }, React.createElement("pre", {
    className: "code" + (scroll ? " code-s" : "")
  }, text), React.createElement("button", {
    className: "btn btn-s code-c",
    onClick: () => navigator.clipboard?.writeText(text).then(() => {
      setC(true);
      setTimeout(() => setC(false), 1600);
    })
  }, c ? React.createElement(React.Fragment, null, React.createElement(Check, {
    s: 12
  }), " Copied") : React.createElement(React.Fragment, null, React.createElement(Copy, {
    s: 12
  }), " Copy")));
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
    className: "toast"
  }, React.createElement("span", {
    style: {
      color: `var(--${t.k === "error" ? "bad" : t.k === "success" ? "ok" : "accent"})`,
      flex: "none",
      marginTop: 1,
      display: "flex"
    }
  }, t.k === "error" ? React.createElement(Alert, {
    s: 15
  }) : t.k === "success" ? React.createElement(Check, {
    s: 15
  }) : React.createElement(Info, {
    s: 15
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
    className: "btn btn-q btn-s btn-i",
    onClick: () => close(t.id),
    "aria-label": "Dismiss"
  }, React.createElement(Ex, {
    s: 13
  })))));
}
function LiveLog({
  lines,
  follow,
  setFollow,
  onClear
}) {
  const ref = useRef(null);
  useEffect(() => {
    if (follow && ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines, follow]);
  return React.createElement(React.Fragment, null, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10,
      marginBottom: 10
    }
  }, React.createElement("span", {
    className: "pill p-o"
  }, React.createElement("span", {
    className: "dot dot-l"
  }), "Live"), React.createElement("span", {
    className: "f-h"
  }, lines.length, " line", lines.length === 1 ? "" : "s"), React.createElement("div", {
    className: "grow"
  }), React.createElement("label", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      fontSize: 12.5,
      cursor: "pointer",
      color: "var(--ink-2)"
    }
  }, React.createElement("input", {
    type: "checkbox",
    checked: follow,
    onChange: e => setFollow(e.target.checked),
    style: {
      accentColor: "var(--accent)"
    }
  }), "Auto-scroll"), lines.length > 0 && React.createElement("button", {
    className: "btn btn-q btn-s",
    onClick: onClear
  }, "Clear")), React.createElement("div", {
    className: "log",
    ref: ref
  }, lines.length === 0 ? React.createElement("div", {
    style: {
      color: "#6e6e78"
    }
  }, "Waiting for activity\u2026") : lines.map(l => React.createElement("div", {
    className: "ll",
    key: l.seq
  }, React.createElement("span", {
    className: "lt"
  }, l.time), React.createElement("span", {
    className: "lv l-" + l.level
  }, l.level), React.createElement("span", {
    className: "lm"
  }, l.message)))));
}
function Field({
  spec,
  value,
  onChange
}) {
  const set = v => onChange(spec.key, v);
  const mod = value !== spec.default && value !== null && value !== "" && value !== false;
  const L = React.createElement("span", {
    className: "f-l",
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6
    }
  }, mod && React.createElement("span", {
    className: "mod",
    title: "Changed"
  }), React.createElement("code", {
    className: "mono"
  }, spec.flag));
  if (spec.type === "flag") return React.createElement(Switch, {
    id: spec.key,
    checked: !!value,
    onChange: set,
    label: spec.flag,
    hint: spec.help
  });
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
  }, "Enabled"), React.createElement("option", {
    value: "false"
  }, "Disabled")), React.createElement("span", {
    className: "f-h"
  }, spec.help));
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
  }, c))), React.createElement("span", {
    className: "f-h"
  }, spec.help));
  if (spec.type === "list") return React.createElement("div", {
    className: "f"
  }, L, React.createElement("input", {
    className: "inp mono",
    placeholder: "comma separated",
    value: Array.isArray(value) ? value.join(", ") : value ?? "",
    onChange: e => set(e.target.value.split(",").map(s => s.trim()).filter(Boolean))
  }), React.createElement("span", {
    className: "f-h"
  }, spec.help));
  const num = spec.type === "int" || spec.type === "float";
  return React.createElement("div", {
    className: "f"
  }, L, React.createElement("input", {
    className: "inp" + (spec.type === "path" ? " mono" : ""),
    type: num ? "number" : "text",
    step: spec.type === "float" ? "0.01" : "1",
    placeholder: spec.type === "path" ? "/path/on/server" : "Default",
    value: value ?? "",
    onChange: e => set(e.target.value === "" ? null : num ? Number(e.target.value) : e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, spec.help));
}
function Browser({
  initial,
  onPick,
  onClose,
  picker,
  onNative,
  busyNative
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
  const crumbs = [];
  if (d?.path) {
    const parts = d.path.split("/").filter(Boolean);
    crumbs.push({
      name: "/",
      path: "/"
    });
    let acc = "";
    for (const seg of parts) {
      acc += "/" + seg;
      crumbs.push({
        name: seg,
        path: acc
      });
    }
  }
  return React.createElement("div", {
    className: "br"
  }, React.createElement("div", {
    className: "br-p"
  }, React.createElement("input", {
    className: "inp mono",
    value: p,
    onChange: e => setP(e.target.value),
    onKeyDown: e => e.key === "Enter" && load(p),
    "aria-label": "Path"
  }), React.createElement("button", {
    className: "btn btn-s",
    onClick: () => load(p)
  }, "Go"), picker?.available && React.createElement("button", {
    className: "btn btn-s",
    disabled: busyNative,
    onClick: onNative,
    title: `Open the ${picker.tool} folder chooser on the server`
  }, busyNative ? React.createElement(React.Fragment, null, React.createElement("span", {
    className: "spin"
  }), " Waiting\u2026") : React.createElement(React.Fragment, null, React.createElement(Folder, {
    s: 12
  }), " File manager")), React.createElement("button", {
    className: "btn btn-s btn-pri",
    onClick: () => {
      onPick(p);
      onClose();
    }
  }, "Select")), crumbs.length > 0 && React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      alignItems: "center",
      gap: 2,
      padding: "7px 12px",
      borderBottom: "1px solid var(--line)",
      background: "var(--raise)",
      fontSize: 12
    }
  }, crumbs.map((c, i) => React.createElement(React.Fragment, {
    key: c.path
  }, i > 0 && React.createElement("span", {
    style: {
      color: "var(--ink-3)"
    }
  }, "/"), React.createElement("button", {
    className: "btn btn-q btn-s",
    style: {
      height: 22,
      padding: "0 6px",
      fontFamily: "var(--mono)",
      fontSize: 11.5
    },
    onClick: () => load(c.path)
  }, c.name)))), e && React.createElement("div", {
    style: {
      padding: "10px 14px",
      fontSize: 12.5,
      color: "var(--bad)"
    }
  }, e), React.createElement("div", {
    className: "br-l"
  }, d?.parent && React.createElement("div", {
    className: "br-i",
    onClick: () => load(d.parent)
  }, React.createElement(Folder, {
    s: 14
  }), React.createElement("span", {
    className: "br-n",
    style: {
      color: "var(--ink-3)"
    }
  }, "..")), d?.entries?.length === 0 && React.createElement("div", {
    style: {
      padding: "14px",
      fontSize: 12.5,
      color: "var(--ink-3)"
    }
  }, "No subfolders"), d?.entries?.map(x => React.createElement("div", {
    key: x.path,
    className: "br-i",
    onClick: () => load(x.path),
    onDoubleClick: () => {
      onPick(x.path);
      onClose();
    }
  }, React.createElement(Folder, {
    s: 14
  }), React.createElement("span", {
    className: "br-n"
  }, x.name), x.recordings > 0 && React.createElement("span", {
    className: "f-h",
    style: {
      flex: "none"
    }
  }, x.recordings, " rec"), x.is_run && React.createElement("span", {
    className: "pill " + (x.finished ? "p-o" : "p-w")
  }, React.createElement("span", {
    className: "dot"
  }), x.finished ? "run · finished" : "run · in progress")))), picker && !picker.available && React.createElement("div", {
    style: {
      padding: "8px 12px",
      borderTop: "1px solid var(--line)"
    },
    className: "f-h"
  }, picker.reason));
}
function Row({
  run,
  onLog,
  onReset,
  wells,
  onWells,
  expanded
}) {
  const m = ST[run.status] || ST.waiting;
  const left = settleLeft(run.detail);
  const busy = run.status === "running" || run.status === "dispatched";
  const bad = run.status === "failed";
  const idx = bad ? 3 : m.i;
  return React.createElement("div", {
    className: "row"
  }, React.createElement("div", null, React.createElement("div", {
    className: "row-id"
  }, run.run), React.createElement("div", {
    className: "row-job"
  }, React.createElement("span", {
    className: "dot",
    style: {
      background: run.job === "activity" ? "var(--ok)" : "var(--accent)"
    }
  }), run.job_label || (run.job === "activity" ? "Activity scan" : "Network"))), React.createElement("div", {
    className: "row-mid"
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    className: "pill " + m.c
  }, busy ? React.createElement("span", {
    className: "spin"
  }) : React.createElement("span", {
    className: "dot" + (run.status === "waiting" ? " dot-l" : "")
  }), m.l), React.createElement("span", {
    className: "row-note" + (/\bfailed\b/i.test(run.detail || "") ? " warn" : ""),
    title: run.detail || ""
  }, run.detail || (run.returncode != null ? `exit code ${run.returncode}` : ""))), bad && run.error && React.createElement("div", {
    className: "row-why"
  }, run.error), busy && React.createElement("div", {
    className: "bar-t"
  }, React.createElement("div", {
    className: "bar-i"
  })), left != null && run.status === "waiting" && React.createElement("div", {
    className: "bar-t"
  }, React.createElement("div", {
    className: "bar-f",
    style: {
      width: `${Math.max(4, 100 - Math.min(100, left))}%`
    }
  }))), React.createElement("div", {
    className: "rail",
    "aria-label": m.l
  }, STAGES.map((s, i) => React.createElement(React.Fragment, {
    key: s
  }, i > 0 && React.createElement("span", {
    className: "st-l",
    "data-d": i <= idx
  }), React.createElement("span", {
    className: "st",
    "data-s": bad && i === 3 ? "failed" : i < idx ? "done" : i === idx ? "active" : "todo"
  }, React.createElement("span", {
    className: "st-d"
  }, bad && i === 3 ? React.createElement(Ex, {
    s: 9
  }) : i < idx ? React.createElement(Check, {
    s: 9
  }) : React.createElement("span", {
    style: {
      width: 4,
      height: 4,
      borderRadius: "50%",
      background: "currentColor"
    }
  })), React.createElement("span", {
    className: "st-n"
  }, s))))), React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--s4)"
    }
  }, React.createElement("div", {
    className: "row-time"
  }, React.createElement("div", {
    className: "row-dur tnum"
  }, dur(run.duration_s)), React.createElement("div", {
    className: "row-ago"
  }, ago(run.completed_at || run.started_at || run.dispatched_at || run.last_seen))), React.createElement("div", {
    className: "btns",
    style: {
      flexWrap: "nowrap"
    }
  }, run.job !== "activity" && React.createElement("button", {
    className: "btn btn-s",
    onClick: () => onWells(run),
    title: "Per-well status from checkpoints"
  }, React.createElement(Slide, {
    s: 12
  }), " Wells"), run.log && React.createElement("button", {
    className: "btn btn-s",
    onClick: () => onLog(run)
  }, React.createElement(Term, {
    s: 12
  }), " Log"), React.createElement("button", {
    className: "btn btn-q btn-s btn-i",
    onClick: () => onReset(run),
    title: "Reset this run"
  }, React.createElement(Sync, {
    s: 12
  })))));
}
function Wells({
  rows,
  summary
}) {
  if (!rows?.length) return null;
  const s = summary || {};
  const cls = r => r.status === "complete" ? "p-o" : r.status === "failed" ? "p-b" : r.status === "running" ? "p-a" : "p-n";
  const when = t => {
    if (!t) return "";
    const d = new Date(t.replace(" ", "T"));
    return isNaN(d) ? String(t).slice(0, 19) : ago(d.toISOString());
  };
  return React.createElement("div", {
    style: {
      padding: "0 24px 18px"
    }
  }, React.createElement("div", {
    className: "facts",
    style: {
      display: "flex",
      gap: 18,
      margin: "2px 0 10px",
      fontSize: 12.5,
      color: "var(--ink-2)",
      flexWrap: "wrap"
    }
  }, React.createElement("span", null, React.createElement("b", null, s.wells ?? rows.length), " wells"), s.complete != null && React.createElement("span", null, React.createElement("b", null, s.complete), " complete"), !!s.failed && React.createElement("span", {
    style: {
      color: "var(--bad)"
    }
  }, React.createElement("b", null, s.failed), " failed"), !!s.running && React.createElement("span", null, React.createElement("b", null, s.running), " running")), React.createElement("div", {
    className: "panel",
    style: {
      overflowX: "auto"
    }
  }, React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 12.5
    }
  }, React.createElement("thead", null, React.createElement("tr", null, ["Well", "Chip", "Recording", "Stage", "Status", "Updated"].map(h => React.createElement("th", {
    key: h,
    style: {
      textAlign: "left",
      padding: "7px 10px",
      fontSize: 10.5,
      textTransform: "uppercase",
      letterSpacing: ".05em",
      color: "var(--ink-3)",
      borderBottom: "1px solid var(--line)",
      whiteSpace: "nowrap"
    }
  }, h)))), React.createElement("tbody", null, rows.map((r, i) => React.createElement(React.Fragment, {
    key: (r.output_dir || "") + r.well + i
  }, React.createElement("tr", null, React.createElement("td", {
    style: {
      padding: "6px 10px"
    },
    className: "mono"
  }, r.well), React.createElement("td", {
    style: {
      padding: "6px 10px"
    },
    className: "mono"
  }, r.chip_id || "—"), React.createElement("td", {
    style: {
      padding: "6px 10px"
    },
    className: "mono"
  }, r.run_id || "—"), React.createElement("td", {
    style: {
      padding: "6px 10px",
      whiteSpace: "nowrap"
    }
  }, r.stage_name || r.stage), React.createElement("td", {
    style: {
      padding: "6px 10px"
    }
  }, React.createElement("span", {
    className: "pill " + cls(r)
  }, React.createElement("span", {
    className: "dot"
  }), r.status)), React.createElement("td", {
    style: {
      padding: "6px 10px",
      whiteSpace: "nowrap",
      color: "var(--ink-3)"
    }
  }, when(r.last_updated))), r.error && React.createElement("tr", null, React.createElement("td", {
    colSpan: 6,
    style: {
      padding: "0 10px 8px",
      color: "var(--bad)",
      fontSize: 12,
      whiteSpace: "pre-wrap",
      wordBreak: "break-word"
    }
  }, r.failed_stage ? `${r.failed_stage}: ` : "", String(r.error).slice(0, 400)))))))));
}
function RunBlock(props) {
  const {
    run,
    wells,
    expanded
  } = props;
  return React.createElement("div", {
    style: {
      borderTop: "1px solid var(--line)"
    }
  }, React.createElement(Row, props), expanded && wells && React.createElement(Wells, {
    rows: wells.wells,
    summary: wells.summary
  }), expanded && wells && !wells.wells?.length && React.createElement("div", {
    style: {
      padding: "0 24px 18px"
    },
    className: "f-h"
  }, "No checkpoint files found yet for this run", wells.searched?.length ? React.createElement(React.Fragment, null, " under ", React.createElement("span", {
    className: "mono"
  }, wells.searched.join(", "))) : null, "."));
}
function QueuePanel({
  cfg,
  toast
}) {
  const [dir, setDir] = useState(cfg?.watch_dir || "");
  const [entries, setEntries] = useState(null);
  const [sel, setSel] = useState({});
  const [info, setInfo] = useState({});
  const [rerun, setRerun] = useState(false);
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState(null);
  const timer = useRef(null);
  const load = useCallback(async path => {
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
      if (runs.length) {
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
      } else setInfo({});
    } catch (e) {
      setEntries([]);
      toast("Could not list folders", e.message, "error");
    }
  }, [toast]);
  useEffect(() => {
    if (cfg?.watch_dir) load(cfg.watch_dir);
  }, [cfg?.watch_dir, load]);
  const poll = useCallback(async () => {
    try {
      const d = await api("/api/queue");
      setQ(d);
      const live = (d.batches || []).some(b => !b.finished);
      if (!live && d.handoff?.state !== "running") {
        clearInterval(timer.current);
        timer.current = null;
      }
    } catch (e) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);
  useEffect(() => () => clearInterval(timer.current), []);
  const chosen = Object.keys(sel).filter(k => sel[k]);
  const doneCount = chosen.filter(p => (info[p]?.jobs || []).some(j => j.already_done)).length;
  const start = async () => {
    if (!chosen.length) return;
    setBusy(true);
    try {
      const r = await api("/api/queue", {
        method: "POST",
        body: JSON.stringify({
          folders: chosen,
          rerun
        })
      });
      toast("Queued", `${r.queued.length} job(s) started`, "ok");
      setSel({});
      if (!timer.current) timer.current = setInterval(poll, 2000);
      poll();
    } catch (e) {
      toast("Nothing queued", e.message, "error");
    } finally {
      setBusy(false);
    }
  };
  const batch = (q?.batches || []).slice(-1)[0];
  const rep = q?.handoff;
  return React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Queue"), React.createElement("div", {
    className: "sec-d"
  }, "Pick folders to analyse now \u2014 they run one at a time, in order")), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b",
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--s5)"
    }
  }, React.createElement("div", {
    className: "btns",
    style: {
      alignItems: "center"
    }
  }, React.createElement("span", {
    className: "f-h"
  }, "In"), React.createElement("code", {
    className: "mono f-h",
    style: {
      wordBreak: "break-all"
    }
  }, dir || "—"), React.createElement("div", {
    className: "grow"
  }), React.createElement("button", {
    className: "btn btn-q btn-s",
    onClick: () => load(dir)
  }, "Refresh")), entries === null ? React.createElement("div", {
    className: "f-h"
  }, "Loading\u2026") : entries.length === 0 ? React.createElement("div", {
    className: "note n-w"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Alert, {
    s: 15
  })), React.createElement("div", null, "No run folders with a recording were found here. Check the input folder under Folders.")) : React.createElement("div", {
    className: "qlist"
  }, entries.map(x => {
    const row = info[x.path] || {};
    const jobs = row.jobs || [];
    const already = jobs.some(j => j.already_done);
    const on = !!sel[x.path];
    return React.createElement("label", {
      key: x.path,
      className: "qrow" + (on ? " on" : "")
    }, React.createElement("input", {
      type: "checkbox",
      checked: on,
      onChange: () => setSel(v => ({
        ...v,
        [x.path]: !v[x.path]
      }))
    }), React.createElement("span", {
      className: "qname"
    }, x.name), React.createElement("span", {
      className: "qmeta"
    }, jobs.length ? jobs.map(j => j.label).join(" + ") : row.note || "no analysis applies"), already && React.createElement("span", {
      className: "pill p-w"
    }, "already analysed"), x.finished === false && React.createElement("span", {
      className: "pill p-w"
    }, "still copying"));
  })), React.createElement("div", {
    style: {
      borderTop: "1px solid var(--line)",
      paddingTop: "var(--s4)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--s3)"
    }
  }, doneCount > 0 && React.createElement(Switch, {
    id: "q-rerun",
    checked: rerun,
    onChange: setRerun,
    label: `Re-run ${doneCount} folder(s) already analysed`,
    hint: "Off by default \u2014 a Network analysis is a long GPU job."
  })), React.createElement("div", {
    className: "btns",
    style: {
      alignItems: "center"
    }
  }, React.createElement("button", {
    className: "btn btn-pri",
    disabled: busy || !chosen.length,
    onClick: start
  }, React.createElement(Play, {
    s: 13
  }), busy ? "Queueing…" : `Queue ${chosen.length || ""} folder${chosen.length === 1 ? "" : "s"}`), batch && !batch.finished && React.createElement("span", {
    className: "f-h"
  }, "Running \u2014 ", batch.keys.length, " job(s) in this batch"), batch && batch.finished && rep?.state === "running" && React.createElement("span", {
    className: "f-h"
  }, "Analysis done \u2014 preparing the AI handoff\u2026")), batch?.finished && rep?.state === "done" && rep.label === batch.id && React.createElement("div", {
    className: "note n-a"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Check, {
    s: 15
  })), React.createElement("div", {
    style: {
      minWidth: 0,
      flex: 1
    }
  }, "AI handoff for this batch is ready. Run:", React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, React.createElement(Code, {
    text: rep.instruction
  })))), batch?.finished && rep?.state === "error" && React.createElement("div", {
    className: "note n-b"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Alert, {
    s: 15
  })), React.createElement("div", null, "The analysis finished, but the AI handoff failed: ", rep.error)))));
}
function AiHandoff({
  cfg,
  toast
}) {
  const [text, setText] = useState(cfg?.ai_requirements || "");
  const [saved, setSaved] = useState(cfg?.ai_requirements || "");
  const [auto, setAuto] = useState(cfg?.auto_handoff !== false);
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState(null);
  useEffect(() => {
    (async () => {
      try {
        const d = await api("/api/handoff");
        if (d && d.state) setLast(d);
      } catch (e) {}
    })();
  }, []);
  const save = async (nextAuto = auto) => {
    try {
      await api("/api/requirements", {
        method: "POST",
        body: JSON.stringify({
          text,
          auto_handoff: nextAuto
        })
      });
      setSaved(text);
      return true;
    } catch (e) {
      toast("Requirements not saved", e.message, "error");
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
      toast("AI handoff ready", `${r.network_wells} network well(s), ${r.activity_runs} scan run(s)`, "ok");
    } catch (e) {
      toast("Handoff failed", e.message, "error");
    } finally {
      setBusy(false);
    }
  };
  const dirty = text !== saved;
  return React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "AI report"), React.createElement("div", {
    className: "sec-d"
  }, "Requirements for the report, and the handoff folder to give Claude")), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b",
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--s4)"
    }
  }, React.createElement("div", null, React.createElement("div", {
    className: "f-l",
    style: {
      marginBottom: 6
    }
  }, "Requirements"), React.createElement("textarea", {
    className: "inp",
    rows: 7,
    value: text,
    style: {
      height: "auto",
      padding: "10px 12px",
      resize: "vertical",
      lineHeight: 1.5
    },
    placeholder: "What should the report show? e.g.\n• Compare KO vs WT burst rate and IBI at each DIV\n• Exclude wells with QC fail\n• Word document with one figure per metric",
    onChange: e => setText(e.target.value)
  }), React.createElement("div", {
    className: "f-h",
    style: {
      marginTop: 6
    }
  }, "Saved with the configuration and copied into every handoff. Defaults for anything not stated here come from ", React.createElement("span", {
    className: "mono"
  }, "skills.md"), ".")), React.createElement(Switch, {
    id: "ai-auto",
    checked: auto,
    onChange: v => {
      setAuto(v);
      save(v);
    },
    label: "Prepare a handoff automatically when a queued batch finishes",
    hint: "Covers just the folders in that batch."
  }), React.createElement("div", {
    className: "btns",
    style: {
      alignItems: "center"
    }
  }, React.createElement("button", {
    className: "btn",
    disabled: !dirty,
    onClick: () => save()
  }, dirty ? "Save requirements" : "Saved"), React.createElement("button", {
    className: "btn btn-pri",
    disabled: busy,
    onClick: prepare
  }, busy ? "Preparing…" : "Prepare handoff for all results")), last?.state === "done" && last.prompt && React.createElement("div", {
    className: "note n-a"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Check, {
    s: 15
  })), React.createElement("div", {
    style: {
      minWidth: 0,
      flex: 1
    }
  }, React.createElement("div", null, "Handoff ready \u2014 ", last.network_wells, " network well(s), ", last.activity_runs, " scan run(s). In a terminal on this server, run:"), React.createElement("div", {
    style: {
      marginTop: 8
    }
  }, React.createElement(Code, {
    text: last.instruction
  })), React.createElement("div", {
    className: "f-h",
    style: {
      marginTop: 6
    }
  }, "The report will be written to", " ", React.createElement("span", {
    className: "mono",
    style: {
      wordBreak: "break-all"
    }
  }, last.report_dir)))), last?.state === "error" && React.createElement("div", {
    className: "note n-b"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Alert, {
    s: 15
  })), React.createElement("div", null, "The handoff could not be prepared: ", last.error)))));
}
function App() {
  const [schema, setSchema] = useState(null);
  const [cfg, setCfg] = useState(null);
  const [status, setStatus] = useState(null);
  const [fatal, setFatal] = useState("");
  const [preview, setPreview] = useState(null);
  const [browsing, setBrowsing] = useState(null);
  const [log, setLog] = useState(null);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState({});
  const [theme, setTheme] = useState(() => localStorage.getItem("mea-theme") || "auto");
  const [toasts, setToasts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [act, setAct] = useState([]);
  const [follow, setFollow] = useState(true);
  const [showCfg, setShowCfg] = useState(true);
  useEffect(() => {
    if (!status?.running) setShowCfg(true);
  }, [status?.running]);
  const [picker, setPicker] = useState(null);
  const [pyCheck, setPyCheck] = useState(null);
  const [busyNative, setBusyNative] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [wells, setWells] = useState({});
  const [openWells, setOpenWells] = useState({});
  const tid = useRef(0),
    seq = useRef(0),
    openWellsRef = useRef({});
  const toast = useCallback((t, m, k = "info") => {
    const id = ++tid.current;
    setToasts(x => [...x, {
      id,
      t,
      m,
      k
    }]);
    setTimeout(() => setToasts(x => x.filter(y => y.id !== id)), k === "error" ? 9000 : 4200);
  }, []);
  useEffect(() => {
    openWellsRef.current = openWells;
  }, [openWells]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("mea-theme", theme);
  }, [theme]);
  useEffect(() => {
    (async () => {
      try {
        const s = await api("/api/schema"),
          c = await api("/api/config");
        setSchema(s);
        setCfg(c);
        const o = {};
        s.groups.forEach((g, i) => o[g.group] = !g.group.toLowerCase().includes("advanced"));
        setOpen(o);
        try {
          setPicker(await api("/api/picker"));
        } catch (e) {
          setPicker({
            available: false
          });
        }
      } catch (e) {
        setFatal(e.message);
      }
    })();
  }, []);
  const polling = useRef(false),
    tick = useRef(0);
  const refresh = useCallback(async force => {
    if (polling.current) return;
    if (!force && typeof document !== "undefined" && document.hidden) return;
    polling.current = true;
    try {
      const wellsDue = force || tick.current++ % 5 === 0;
      const keys = wellsDue ? Object.keys(openWellsRef.current || {}).filter(k => openWellsRef.current[k]) : [];
      await Promise.all([api("/api/status").then(s => {
        setStatus(s);
        setShowCfg(v => s.running ? false : v);
      }).catch(() => {}), api(`/api/logs?since=${seq.current}`).then(d => {
        if (d.lines?.length) {
          seq.current = d.last_seq;
          setAct(a => [...a, ...d.lines].slice(-400));
        }
      }).catch(() => {}), ...keys.map(k => api(`/api/runs/checkpoints?path=${encodeURIComponent(k)}`).then(d => setWells(w => ({
        ...w,
        [k]: d
      }))).catch(() => {}))]);
    } finally {
      polling.current = false;
    }
  }, []);
  useEffect(() => {
    refresh(true);
    const t = setInterval(() => refresh(false), 2000);
    const vis = () => {
      if (!document.hidden) refresh(true);
    };
    document.addEventListener("visibilitychange", vis);
    return () => {
      clearInterval(t);
      document.removeEventListener("visibilitychange", vis);
    };
  }, [refresh]);
  useEffect(() => {
    if (!log?.path) return;
    const live = (status?.runs || []).some(r => r.log === log.path && (r.status === "running" || r.status === "dispatched"));
    if (!live) return;
    const t = setInterval(async () => {
      try {
        const d = await api(`/api/runs/log?path=${encodeURIComponent(log.path)}`);
        setLog(l => l && l.path === log.path ? {
          ...l,
          lines: d.lines
        } : l);
      } catch (e) {}
    }, 3000);
    return () => clearInterval(t);
  }, [log?.path, status]);
  const payload = useCallback(() => ({
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
  }), [cfg]);
  const act_ = useCallback(async (fn, t, m) => {
    setBusy(true);
    try {
      await fn();
      if (t) toast(t, m, "success");
      refresh();
    } catch (e) {
      toast("Something went wrong", e.message, "error");
    } finally {
      setBusy(false);
    }
  }, [toast, refresh]);
  if (fatal) return React.createElement("div", {
    className: "shell"
  }, React.createElement("div", {
    className: "page",
    style: {
      maxWidth: 640,
      paddingTop: 96
    }
  }, React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-h"
  }, React.createElement("div", null, React.createElement("div", {
    className: "panel-t",
    style: {
      color: "var(--bad)"
    }
  }, "Cannot reach the backend"), React.createElement("div", {
    className: "panel-d"
  }, "This page is the interface only \u2014 the Python server reads folders and runs the pipeline, so it must serve this page."))), React.createElement("div", {
    className: "panel-b"
  }, React.createElement(Code, {
    text: fatal
  })), React.createElement("div", {
    className: "panel-b",
    style: {
      paddingTop: 0
    }
  }, React.createElement("button", {
    className: "btn btn-pri",
    onClick: () => location.reload()
  }, React.createElement(Sync, {
    s: 13
  }), " Retry")))));
  if (!schema || !cfg) return React.createElement("div", {
    className: "shell"
  }, React.createElement("div", {
    className: "page"
  }, React.createElement("div", {
    className: "stack"
  }, React.createElement("div", {
    className: "skel",
    style: {
      height: 38,
      width: 280
    }
  }), React.createElement("div", {
    className: "metrics"
  }, [0, 1, 2, 3].map(i => React.createElement("div", {
    className: "metric",
    key: i
  }, React.createElement("div", {
    className: "skel",
    style: {
      height: 12,
      width: "55%"
    }
  }), React.createElement("div", {
    className: "skel",
    style: {
      height: 30,
      width: "38%",
      marginTop: 8
    }
  })))), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b"
  }, React.createElement("div", {
    className: "skel",
    style: {
      height: 16,
      width: 190
    }
  }), React.createElement("div", {
    className: "skel",
    style: {
      height: 38,
      marginTop: 16
    }
  }), React.createElement("div", {
    className: "skel",
    style: {
      height: 38,
      marginTop: 10
    }
  }))))));
  const running = !!status?.running;
  const setO = (k, v) => setCfg(c => ({
    ...c,
    driver_options: {
      ...c.driver_options,
      [k]: v
    }
  }));
  const setT = (k, v) => setCfg(c => ({
    ...c,
    [k]: v
  }));
  const counts = status?.counts || {},
    runs = status?.runs || [];
  const failedCount = runs.filter(r => r.status === "failed").length;
  const save = () => act_(async () => {
    await api("/api/config", {
      method: "POST",
      body: JSON.stringify(payload())
    });
  }, "Configuration saved");
  const start = () => {
    const n = status?.resumable || 0;
    if (n && !window.confirm(`${n} job(s) from a previous run were left unfinished ` + "and will be picked up again.\n\nFinished wells are skipped, so this repeats " + "only unfinished work. Clear them first if you want a fresh start.")) return;
    act_(async () => {
      await api("/api/config", {
        method: "POST",
        body: JSON.stringify(payload())
      });
      await api("/api/watcher/start", {
        method: "POST"
      });
    }, "Watcher started", cfg.dry_run ? "Dry run — nothing will be launched." : n ? `Resuming ${n} unfinished job(s); new folders will be analyzed too.` : "Completed runs will be analyzed automatically.");
  };
  const stop = () => act_(async () => {
    await api("/api/watcher/stop", {
      method: "POST"
    });
  }, "Stopped scanning", "Jobs already running carry on. Use Stop &amp; cancel to end them.");
  const cancel = () => {
    const n = (status?.counts?.running || 0) + (status?.counts?.dispatched || 0);
    if (!window.confirm(`Stop scanning and cancel ${n} job(s) in flight?\n\n` + "Wells already finished keep their checkpoints, so re-running repeats " + "only the well that was in progress.")) return;
    act_(async () => {
      await api("/api/watcher/stop?cancel_running=true", {
        method: "POST"
      });
    }, "Stopped", "Running jobs were cancelled.");
  };
  const doPrev = () => act_(async () => {
    setPreview(await api("/api/preview", {
      method: "POST",
      body: JSON.stringify(payload())
    }));
  });
  const onReset = r => act_(async () => {
    await api("/api/runs/reset", {
      method: "POST",
      body: JSON.stringify({
        path: r.path
      })
    });
  }, "Run reset", `${r.run} will be processed again.`);
  const onLog = r => act_(async () => {
    const d = await api(`/api/runs/log?path=${encodeURIComponent(r.log)}`);
    setLog({
      run: r.run,
      lines: d.lines,
      path: r.log
    });
  });
  const onClearAll = async which => {
    const all = status?.runs || [];
    const n = which === "failed" ? all.filter(r => r.status === "failed").length : all.length;
    if (which === "all" && n > 0 && !window.confirm(`Forget all ${n} run(s)?\n\nAnalysed output on disk is not touched — the ` + `watcher will simply treat these folders as unseen.`)) return;
    setClearing(true);
    try {
      const r = await api("/api/runs/reset-all", {
        method: "POST",
        body: JSON.stringify({
          which
        })
      });
      toast("Cleared", `${r.cleared} run(s) forgotten` + (r.skipped?.length ? ` · ${r.skipped.length} still running, left alone` : ""), "ok");
      refresh();
    } catch (e) {
      toast("Could not clear", e.message, "error");
    } finally {
      setClearing(false);
    }
  };
  const testPython = () => act_(async () => {
    setPyCheck(await api("/api/driver-python", {
      method: "POST",
      body: JSON.stringify({
        python: cfg.driver_python || ""
      })
    }));
  });
  const pickNative = (start, title, apply) => {
    setBusyNative(true);
    act_(async () => {
      try {
        const d = await api("/api/picker", {
          method: "POST",
          body: JSON.stringify({
            start: start || "",
            title
          })
        });
        if (!d.cancelled && d.path) apply(d.path);
      } finally {
        setBusyNative(false);
      }
    });
  };
  const onWells = r => {
    const isOpen = !!openWells[r.path];
    setOpenWells(o => ({
      ...o,
      [r.path]: !isOpen
    }));
    if (isOpen) return;
    act_(async () => {
      const d = await api(`/api/runs/checkpoints?path=${encodeURIComponent(r.path)}`);
      setWells(w => ({
        ...w,
        [r.path]: d
      }));
    });
  };
  const ql = q.trim().toLowerCase();
  const groups = schema.groups.map(g => ({
    ...g,
    fields: g.fields.filter(f => !ql || f.key.toLowerCase().includes(ql) || f.flag.toLowerCase().includes(ql) || (f.help || "").toLowerCase().includes(ql))
  })).filter(g => g.fields.length);
  const modified = Object.entries(cfg.driver_options).filter(([k, v]) => {
    const s = schema.groups.flatMap(g => g.fields).find(f => f.key === k);
    return s && v !== s.default && v !== null && v !== "" && v !== false;
  }).length;
  const active = (counts.running || 0) + (counts.dispatched || 0);
  const heroTitle = running ? active ? `Analyzing ${active} job${active > 1 ? "" : ""}` : "Watching for recordings" : runs.length ? "Watcher stopped" : "Ready to watch";
  const jobsOn = [cfg.run_network && "Network", cfg.run_activity && "Activity scan"].filter(Boolean);
  return React.createElement("div", {
    className: "shell"
  }, React.createElement("h1", {
    className: "sr"
  }, "MEA pipeline control"), React.createElement("div", {
    className: "bar"
  }, React.createElement("div", {
    className: "bar-in"
  }, React.createElement("div", {
    className: "mark"
  }, React.createElement(Wave, {
    s: 15
  })), React.createElement("div", {
    className: "wordmark"
  }, "MEA Pipeline"), React.createElement("div", {
    className: "grow"
  }), React.createElement("span", {
    className: "pill " + (running ? "p-o" : "p-n")
  }, React.createElement("span", {
    className: "dot" + (running ? " dot-l" : "")
  }), running ? cfg.dry_run ? "Dry run" : "Watching" : "Stopped"), React.createElement("button", {
    className: "btn btn-q btn-i",
    onClick: () => setTheme(t => t === "dark" ? "light" : "dark"),
    "aria-label": "Toggle theme"
  }, theme === "dark" ? React.createElement(Sun, {
    s: 15
  }) : React.createElement(Moon, {
    s: 15
  })), running ? React.createElement(React.Fragment, null, React.createElement("button", {
    className: "btn",
    onClick: stop,
    disabled: busy
  }, React.createElement(Stop, {
    s: 12
  }), " Stop scanning"), React.createElement("button", {
    className: "btn btn-dan",
    onClick: cancel,
    disabled: busy
  }, React.createElement(Stop, {
    s: 12
  }), " Stop & cancel")) : React.createElement("button", {
    className: "btn btn-pri",
    onClick: start,
    disabled: busy
  }, React.createElement(Play, {
    s: 12
  }), " Start watching"))), React.createElement("div", {
    className: "page"
  }, React.createElement("div", {
    className: "stack"
  }, React.createElement("div", {
    className: "hero"
  }, React.createElement("div", null, React.createElement("div", {
    className: "hero-h"
  }, heroTitle), React.createElement("div", {
    className: "hero-sub"
  }, cfg.watch_dir ? React.createElement(React.Fragment, null, "Monitoring ", React.createElement("span", {
    className: "mono"
  }, cfg.watch_dir), jobsOn.length ? React.createElement(React.Fragment, null, " \xB7 ", jobsOn.join(" + ")) : null) : "No input folder set yet")), React.createElement("div", {
    className: "btns"
  }, !running && React.createElement("button", {
    className: "btn",
    onClick: () => setShowCfg(s => !s)
  }, React.createElement(Slide, {
    s: 13
  }), " ", showCfg ? "Hide setup" : "Show setup"), React.createElement("button", {
    className: "btn",
    onClick: refresh
  }, React.createElement(Sync, {
    s: 13
  }), " Refresh"))), cfg.env?.in_container && React.createElement("div", {
    className: "note n-a"
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Info, {
    s: 15
  })), React.createElement("div", null, "Running in a container. Mounted paths are identical inside and out", cfg.env.suggested_input && React.createElement(React.Fragment, null, " \u2014 input ", React.createElement("code", null, cfg.env.suggested_input), " (read-only)"), cfg.env.suggested_output && React.createElement(React.Fragment, null, ", output ", React.createElement("code", null, cfg.env.suggested_output)), ". The input path must be the folder ", React.createElement("b", null, "containing"), " your run folders, not a single run.")), React.createElement("div", {
    className: "metrics"
  }, [{
    k: "waiting",
    l: "Waiting",
    i: React.createElement(Clock, {
      s: 12
    })
  }, {
    k: "running",
    l: "Analyzing",
    i: React.createElement(Wave, {
      s: 12
    })
  }, {
    k: "done",
    l: "Complete",
    i: React.createElement(Check, {
      s: 12
    })
  }, {
    k: "failed",
    l: "Failed",
    i: React.createElement(Alert, {
      s: 12
    })
  }].map(s => React.createElement("div", {
    className: "metric",
    key: s.k,
    "data-live": s.k === "running" && (counts.running || 0) > 0,
    "data-bad": s.k === "failed" && (counts.failed || 0) > 0
  }, React.createElement("div", {
    className: "metric-k"
  }, s.i, s.l), React.createElement("div", {
    className: "metric-v tnum"
  }, counts[s.k] || 0)))), React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Runs"), React.createElement("div", {
    className: "sec-d"
  }, running ? "Scanning for completed recordings" : "Watcher is stopped", status?.scanning ? " · reading the input folder…" : status?.candidates?.length ? ` · ${status.candidates.length} folder${status.candidates.length > 1 ? "s" : ""} in scope` : ""), React.createElement("div", {
    className: "grow"
  }), failedCount > 0 && React.createElement("button", {
    className: "btn btn-q btn-s",
    disabled: clearing,
    onClick: () => onClearAll("failed")
  }, "Clear ", failedCount, " failed"), runs.length > 0 && React.createElement("button", {
    className: "btn btn-q btn-s",
    disabled: clearing,
    onClick: () => onClearAll("all")
  }, "Clear all")), React.createElement("div", {
    className: "panel"
  }, runs.length === 0 ? React.createElement("div", {
    className: "empty"
  }, React.createElement("div", {
    className: "empty-i"
  }, React.createElement(Inbox, {
    s: 21
  })), React.createElement("div", {
    className: "empty-t"
  }, "No runs yet"), React.createElement("div", {
    className: "empty-d"
  }, status?.candidates?.length ? React.createElement(React.Fragment, null, "Found ", React.createElement("b", null, status.candidates.join(", ")), " in the input folder. Start the watcher to begin checking whether they have finished copying.") : React.createElement(React.Fragment, null, "Set an input folder below, then start the watcher. Run folders containing a recording will appear here as they are detected."))) : React.createElement("div", {
    className: "rows"
  }, runs.map(r => React.createElement(RunBlock, {
    key: r.path,
    run: r,
    onLog: onLog,
    onReset: onReset,
    onWells: onWells,
    wells: wells[r.path],
    expanded: !!openWells[r.path]
  }))))), React.createElement(QueuePanel, {
    cfg: cfg,
    toast: toast
  }), React.createElement(AiHandoff, {
    cfg: cfg,
    toast: toast
  }), log && React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Pipeline log"), React.createElement("div", {
    className: "sec-d"
  }, log.run, " \xB7 last ", log.lines.length, " lines", (status?.runs || []).some(r => r.log === log.path && (r.status === "running" || r.status === "dispatched")) && " · following live"), React.createElement("div", {
    className: "grow"
  }), React.createElement("button", {
    className: "btn btn-q btn-s btn-i",
    onClick: () => setLog(null),
    "aria-label": "Close"
  }, React.createElement(Ex, {
    s: 14
  }))), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b"
  }, React.createElement(Code, {
    text: log.lines.join("\n"),
    scroll: true
  })))), React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Activity"), React.createElement("div", {
    className: "sec-d"
  }, "Live watcher output \u2014 detection, settle windows, dispatches")), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b"
  }, React.createElement(LiveLog, {
    lines: act,
    follow: follow,
    setFollow: setFollow,
    onClear: () => setAct([])
  })))), running && React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "strip"
  }, React.createElement("span", null, "Settle ", React.createElement("b", {
    className: "tnum"
  }, cfg.settle_seconds, "s")), React.createElement("span", null, "Poll ", React.createElement("b", {
    className: "tnum"
  }, cfg.poll_seconds, "s")), React.createElement("span", null, "Analyses ", React.createElement("b", null, jobsOn.join(" + ") || "none")), React.createElement("span", null, "Output ", React.createElement("b", {
    className: "mono"
  }, cfg.driver_options.output_dir || "—")), React.createElement("div", {
    className: "grow"
  }), React.createElement("span", {
    style: {
      color: "var(--ink-3)"
    }
  }, "Stop the watcher to edit"))), showCfg && !running && React.createElement(React.Fragment, null, React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Setup"), React.createElement("div", {
    className: "sec-d"
  }, "Where recordings arrive, and what runs when they do")), React.createElement("div", {
    className: "grid2"
  }, React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-h"
  }, React.createElement("div", null, React.createElement("div", {
    className: "panel-t"
  }, "Folders"))), React.createElement("div", {
    className: "panel-b",
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--s5)"
    }
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "in"
  }, "Input"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    id: "in",
    className: "inp mono",
    value: cfg.watch_dir,
    placeholder: "/home/user/MEA",
    onChange: e => setT("watch_dir", e.target.value)
  }), React.createElement("button", {
    className: "btn",
    onClick: () => setBrowsing(browsing === "in" ? null : "in")
  }, React.createElement(Folder, {
    s: 13
  }))), React.createElement("span", {
    className: "f-h"
  }, "Folder containing run folders such as ", React.createElement("code", {
    className: "mono"
  }, "000041"), "."), browsing === "in" && React.createElement(Browser, {
    initial: cfg.watch_dir,
    onClose: () => setBrowsing(null),
    onPick: p => setT("watch_dir", p),
    picker: picker,
    busyNative: busyNative,
    onNative: () => pickNative(cfg.watch_dir, "Select input folder", p => setT("watch_dir", p))
  })), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "out"
  }, "Output"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    id: "out",
    className: "inp mono",
    value: cfg.driver_options.output_dir ?? "",
    placeholder: "/home/user/AnalyzedData",
    onChange: e => setO("output_dir", e.target.value || null)
  }), React.createElement("button", {
    className: "btn",
    onClick: () => setBrowsing(browsing === "out" ? null : "out")
  }, React.createElement(Folder, {
    s: 13
  }))), React.createElement("span", {
    className: "f-h"
  }, "Passed as ", React.createElement("code", {
    className: "mono"
  }, "--output-dir"), "."), browsing === "out" && React.createElement(Browser, {
    initial: cfg.driver_options.output_dir || "",
    onClose: () => setBrowsing(null),
    onPick: p => setO("output_dir", p),
    picker: picker,
    busyNative: busyNative,
    onNative: () => pickNative(cfg.driver_options.output_dir, "Select output folder", p => setO("output_dir", p))
  })))), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-h"
  }, React.createElement("div", null, React.createElement("div", {
    className: "panel-t"
  }, "Detection"))), React.createElement("div", {
    className: "panel-b"
  }, React.createElement("div", {
    className: "grid2"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "set"
  }, "Settle window"), React.createElement("input", {
    id: "set",
    className: "inp tnum",
    type: "number",
    min: "1",
    value: cfg.settle_seconds,
    onChange: e => setT("settle_seconds", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Seconds of no change before a run counts as complete.")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "pol"
  }, "Poll interval"), React.createElement("input", {
    id: "pol",
    className: "inp tnum",
    type: "number",
    min: "1",
    value: cfg.poll_seconds,
    onChange: e => setT("poll_seconds", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "How often the folder is checked."))), React.createElement("div", {
    className: "sep"
  }), React.createElement(Switch, {
    id: "mk",
    checked: cfg.require_finished_marker,
    onChange: v => setT("require_finished_marker", v),
    label: "Require MaxWell completion marker",
    hint: "Also wait for finished= in mxassay.metadata."
  }), React.createElement(Switch, {
    id: "skip",
    checked: cfg.skip_settle_for_existing,
    onChange: v => setT("skip_settle_for_existing", v),
    label: "Folders already here are ready",
    hint: "Start analyzing existing folders immediately, skipping the settle window. Use when the copy already finished. Folders arriving later still wait the full window."
  }), React.createElement(Switch, {
    id: "dry",
    checked: cfg.dry_run,
    onChange: v => setT("dry_run", v),
    label: "Dry run",
    hint: "Detect and record the command, but never launch."
  }), cfg.dry_run && React.createElement("div", {
    className: "note n-w",
    style: {
      marginTop: "var(--s3)"
    }
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Info, {
    s: 15
  })), React.createElement("div", null, "Runs will stop at ", React.createElement("b", null, "Detected"), ". Turn this off and save to run for real \u2014 already-detected runs are cleared automatically.")))))), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-h"
  }, React.createElement("div", null, React.createElement("div", {
    className: "panel-t"
  }, "Analyses"), React.createElement("div", {
    className: "panel-d"
  }, "Independent jobs \u2014 separate outputs, separate status"))), React.createElement("div", {
    className: "panel-b"
  }, React.createElement("div", {
    className: "grid2"
  }, React.createElement(Switch, {
    id: "net",
    checked: cfg.run_network,
    onChange: v => setT("run_network", v),
    label: "Network \u2014 spike sorting",
    hint: "Kilosort4, curation, burst analysis. Needs a GPU; hours per chip."
  }), React.createElement(Switch, {
    id: "ac",
    checked: cfg.run_activity,
    onChange: v => setT("run_activity", v),
    label: "Activity scan \u2014 whole-array maps",
    hint: "Activity maps, QC metrics, network bursts. CPU only; seconds per chip."
  })), cfg.run_network && React.createElement(React.Fragment, null, React.createElement("div", {
    className: "sep"
  }), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "dpy"
  }, "Pipeline interpreter"), React.createElement("div", {
    className: "f-row"
  }, React.createElement("input", {
    id: "dpy",
    className: "inp mono",
    placeholder: "(auto-detect \u2014 the environment MEA-Analysis is installed in)",
    value: cfg.driver_python ?? "",
    onChange: e => setT("driver_python", e.target.value)
  }), React.createElement("button", {
    className: "btn",
    onClick: testPython,
    disabled: busy
  }, "Test")), React.createElement("span", {
    className: "f-h"
  }, "Must have the pipeline's dependencies (pandas, spikeinterface, kilosort, torch). This tool's own virtualenv does not \u2014 launching the driver with it fails at", React.createElement("code", {
    className: "mono"
  }, " import pandas"), "."), pyCheck && React.createElement("div", {
    className: "note " + (pyCheck.ok ? "n-a" : "n-b"),
    style: {
      marginTop: 8
    }
  }, React.createElement("span", {
    className: "n-i"
  }, pyCheck.ok ? React.createElement(Check, {
    s: 15
  }) : React.createElement(Alert, {
    s: 15
  })), React.createElement("div", {
    style: {
      minWidth: 0
    }
  }, React.createElement("div", null, React.createElement("b", {
    className: "mono"
  }, pyCheck.python), pyCheck.version && React.createElement(React.Fragment, null, " \xB7 Python ", pyCheck.version), pyCheck.source && React.createElement(React.Fragment, null, " \xB7 ", pyCheck.source)), pyCheck.ok ? React.createElement("div", {
    style: {
      marginTop: 3
    }
  }, "All pipeline dependencies present.") : React.createElement("div", {
    style: {
      marginTop: 3
    }
  }, "Missing: ", React.createElement("b", null, (pyCheck.missing || []).join(", ") || pyCheck.error), ". Set the path to the environment MEA-Analysis runs in."))))), cfg.run_activity && React.createElement(React.Fragment, null, React.createElement("div", {
    className: "sep"
  }), React.createElement("div", {
    className: "grid2"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "ao"
  }, "Activity output"), React.createElement("input", {
    id: "ao",
    className: "inp mono",
    placeholder: "(defaults to <output>/ActivityScan)",
    value: cfg.activity_output_dir ?? "",
    onChange: e => setT("activity_output_dir", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Kept separate from spike-sorting output.")), React.createElement("div", {
    className: "grid2"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "ah"
  }, "Active threshold"), React.createElement("input", {
    id: "ah",
    className: "inp tnum",
    type: "number",
    step: "0.01",
    min: "0",
    value: cfg.activity_active_hz,
    onChange: e => setT("activity_active_hz", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Hz")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "as"
  }, "Assay folder"), React.createElement("input", {
    id: "as",
    className: "inp mono",
    value: cfg.activity_subfolder ?? "",
    onChange: e => setT("activity_subfolder", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Holds the scans")))), React.createElement(Switch, {
    id: "af",
    checked: cfg.activity_figures,
    onChange: v => setT("activity_figures", v),
    label: "Generate figures",
    hint: "Activity maps, rasters, connectivity, plate overview."
  })), React.createElement("div", {
    className: "sep"
  }), React.createElement("div", {
    className: "grid2"
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "cn"
  }, "Concurrent Network jobs"), React.createElement("input", {
    id: "cn",
    className: "inp tnum",
    type: "number",
    min: "1",
    max: "8",
    value: cfg.max_concurrent_network ?? 1,
    onChange: e => setT("max_concurrent_network", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Extra jobs queue rather than starting. Whether more than one fits depends on the card: measure peak VRAM during the sorting phase with", React.createElement("code", null, " nvidia-smi"), " and allow that much per job. Sorting also leaves the GPU idle much of the time while it waits on data, so a second job often fills those gaps rather than competing \u2014 and overlaps its own CPU-only analyzer stage with the first job's GPU work.")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "ca"
  }, "Concurrent Activity jobs"), React.createElement("input", {
    id: "ca",
    className: "inp tnum",
    type: "number",
    min: "1",
    max: "16",
    value: cfg.max_concurrent_activity ?? 2,
    onChange: e => setT("max_concurrent_activity", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "CPU only, so this can be higher. Never waits behind spike sorting.")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "cool"
  }, "GPU cooldown"), React.createElement("input", {
    id: "cool",
    className: "inp tnum",
    type: "number",
    min: "0",
    max: "600",
    value: cfg.gpu_cooldown_seconds ?? 5,
    onChange: e => setT("gpu_cooldown_seconds", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Seconds to wait before starting the next queued Network job. CUDA memory is not always released the moment a process exits.")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "qp"
  }, "Queue check interval"), React.createElement("input", {
    id: "qp",
    className: "inp tnum",
    type: "number",
    min: "1",
    max: "120",
    value: cfg.queue_poll_seconds ?? 2,
    onChange: e => setT("queue_poll_seconds", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "How often a queued job looks for a free slot."))), React.createElement("div", {
    className: "sep"
  }), React.createElement(Switch, {
    id: "lio",
    checked: cfg.logs_in_output !== false,
    onChange: v => setT("logs_in_output", v),
    label: "Write logs beside the results",
    hint: "Per-run logs go to <output>/orchestration_logs/ as well, so the log lives with the output it describes. Falls back to the work directory if that is not writable."
  }), React.createElement("div", {
    className: "sep"
  }), React.createElement(Switch, {
    id: "stg",
    checked: !!cfg.stage_locally,
    onChange: v => setT("stage_locally", v),
    label: "Run against local disk, then copy results",
    hint: "Spike sorting writes a float32 copy of each recording and reads it back many times \u2014 tens of GB per well. On a network output directory that traffic, not the GPU, decides how long a run takes. Input and final output paths are unchanged; only the working files move."
  }), cfg.stage_locally && React.createElement(React.Fragment, null, React.createElement("div", {
    className: "grid2",
    style: {
      marginTop: "var(--s3)"
    }
  }, React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "scr"
  }, "Scratch directory"), React.createElement("input", {
    id: "scr",
    className: "inp",
    type: "text",
    spellCheck: "false",
    placeholder: "<work dir>/scratch",
    value: cfg.scratch_dir || "",
    onChange: e => setT("scratch_dir", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "A local disk with room to spare. Leave blank to use the work directory \u2014 check that it is not the same volume you are short of space on.")), React.createElement("div", {
    className: "f"
  }, React.createElement("label", {
    className: "f-l",
    htmlFor: "smf"
  }, "Keep free (GB)"), React.createElement("input", {
    id: "smf",
    className: "inp tnum",
    type: "number",
    min: "0",
    max: "10000",
    value: cfg.stage_min_free_gb ?? 200,
    onChange: e => setT("stage_min_free_gb", e.target.value)
  }), React.createElement("span", {
    className: "f-h"
  }, "Staging is skipped, and the job runs against the output directory instead, if it would take the volume below this. Never fills a disk to run faster."))), React.createElement("div", {
    className: "note n-b",
    style: {
      marginTop: "var(--s3)"
    }
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Alert, {
    s: 15
  })), React.createElement("div", null, "Results for a folder appear in the output directory when that folder finishes, rather than well by well. Per-well progress and logs are unaffected."))), !cfg.run_network && !cfg.run_activity && React.createElement("div", {
    className: "note n-b",
    style: {
      marginTop: "var(--s3)"
    }
  }, React.createElement("span", {
    className: "n-i"
  }, React.createElement(Alert, {
    s: 15
  })), React.createElement("div", null, "Enable at least one analysis, or nothing will run.")))), React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Pipeline options"), React.createElement("div", {
    className: "sec-d"
  }, "Passed to run_pipeline_driver.py \xB7 ", modified, " changed from default")), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b"
  }, React.createElement("div", {
    className: "opt-bar"
  }, React.createElement("div", {
    className: "srch"
  }, React.createElement("span", {
    className: "srch-i"
  }, React.createElement(Search, {
    s: 14
  })), React.createElement("input", {
    className: "inp",
    placeholder: "Search options\u2026",
    value: q,
    onChange: e => setQ(e.target.value),
    "aria-label": "Search options"
  })), q && React.createElement("button", {
    className: "btn btn-q btn-s",
    onClick: () => setQ("")
  }, "Clear")), groups.length === 0 ? React.createElement("div", {
    className: "empty",
    style: {
      padding: "36px 0"
    }
  }, React.createElement("div", {
    className: "empty-t"
  }, "No matching options"), React.createElement("div", {
    className: "empty-d"
  }, "Try a different search term.")) : React.createElement("div", {
    className: "groups"
  }, groups.map(g => {
    const o = ql ? true : !!open[g.group];
    return React.createElement("div", {
      className: "grp",
      key: g.group
    }, React.createElement("button", {
      className: "grp-h",
      onClick: () => setOpen(x => ({
        ...x,
        [g.group]: !x[g.group]
      })),
      "aria-expanded": o
    }, React.createElement("span", {
      className: "chev",
      "data-o": o
    }, React.createElement(Chev, {
      s: 12
    })), React.createElement("span", {
      className: "grp-n"
    }, g.group), React.createElement("span", {
      className: "grp-c"
    }, g.fields.length)), o && React.createElement("div", {
      className: "grp-b"
    }, g.fields.map(f => React.createElement(Field, {
      key: f.key,
      spec: f,
      value: cfg.driver_options[f.key],
      onChange: setO
    }))));
  }))))), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b",
    style: {
      display: "flex",
      gap: "var(--s2)",
      flexWrap: "wrap",
      alignItems: "center"
    }
  }, React.createElement("button", {
    className: "btn btn-pri",
    onClick: start,
    disabled: busy
  }, React.createElement(Play, {
    s: 12
  }), " Start watching"), React.createElement("button", {
    className: "btn",
    onClick: save,
    disabled: busy
  }, "Save configuration"), React.createElement("button", {
    className: "btn",
    onClick: doPrev,
    disabled: busy
  }, React.createElement(Term, {
    s: 13
  }), " Preview command"))), preview && React.createElement("div", null, React.createElement("div", {
    className: "sec-h"
  }, React.createElement("div", {
    className: "sec-t"
  }, "Command preview"), React.createElement("div", {
    className: "sec-d"
  }, preview.detected_runs?.length ? React.createElement(React.Fragment, null, "For ", React.createElement("b", null, preview.example_run), " \xB7 detected: ", preview.detected_runs.join(", ")) : "No run folders detected yet")), React.createElement("div", {
    className: "panel"
  }, React.createElement("div", {
    className: "panel-b",
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--s5)"
    }
  }, (preview.commands?.length ? preview.commands : [{
    job: "network",
    job_label: "Command",
    command: preview.command
  }]).map(c => React.createElement("div", {
    key: c.job
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      marginBottom: 8
    }
  }, React.createElement("span", {
    className: "dot",
    style: {
      background: c.job === "activity" ? "var(--ok)" : "var(--accent)"
    }
  }), React.createElement("span", {
    style: {
      fontSize: 12.5,
      fontWeight: 600,
      letterSpacing: "-.01em"
    }
  }, c.job_label)), React.createElement(Code, {
    text: c.command
  }))), preview.commands && preview.commands.length === 0 && React.createElement("div", {
    className: "f-h"
  }, "No analyses enabled."))))))), React.createElement(Toasts, {
    items: toasts,
    close: id => setToasts(t => t.filter(x => x.id !== id))
  }));
}
ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App, null));
