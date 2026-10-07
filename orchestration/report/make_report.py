#!/usr/bin/env python3
"""
Make the standard MEA report for any set of recording dates.

    PY=/mnt/Vol20tb1/user_workspaces/hitesh/MEA-Analysis/.venv/bin/python
    $PY make_report.py --project-dir <results>/<project> --list
    $PY make_report.py --project-dir <results>/<project> --dates 260818
    $PY make_report.py --project-dir <results>/<project> --dates 260818 260821 260825
    $PY make_report.py --project-dir <results>/<project> --all

One date   -> report/report.html: the standard two-page report (Network, Activity scan).
Many dates -> the same standard report for each date in report/dates/<date>/, plus
              report/report.html: an overview with trends across the dates and links.

Read-only with respect to the results. Writes only a new folder:
    <project-dir>/AI_HANDOFF/<timestamp>_<label>/   (or --out)
which the control UI lists under "AI report".
"""

from __future__ import annotations

import argparse
import html
import io
import base64
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import handoff  # noqa: E402

BUILD = HERE / "build_report.py"
DATE_RE = re.compile(r"^\d{6}$")


def available_dates(pdir: Path) -> dict[str, dict]:
    """Dates with any Network or ActivityScan results in this project folder."""
    out: dict[str, dict] = {}
    for d in sorted(p for p in pdir.iterdir() if p.is_dir() and DATE_RE.match(p.name)):
        n = sum(1 for _ in d.glob("*/Network/*/well*/network_results.json"))
        out.setdefault(d.name, {})["network_wells_with_results"] = n
    act = pdir / "ActivityScan"
    if act.is_dir():
        for d in sorted(p for p in act.iterdir() if p.is_dir() and DATE_RE.match(p.name)):
            out.setdefault(d.name, {})["activity_runs"] = sum(1 for _ in d.glob("*/*/summary.json"))
    return dict(sorted(out.items()))


def analysis_state(project: str) -> dict[str, str]:
    """date -> finished / running / waiting / failed, from the control server.

    Empty when the server cannot be reached (then nothing is refused)."""
    import urllib.request
    try:
        runs = json.load(urllib.request.urlopen("http://localhost:8000/api/status", timeout=15))["runs"]
    except Exception:  # noqa: BLE001
        return {}
    by: dict[str, list[str]] = {}
    for r in runs:
        f = Path(r["folder"])
        if f.parent.name == project:
            by.setdefault(f.name, []).append(r.get("status") or "")
    out = {}
    for d, sts in by.items():
        out[d] = ("running" if "running" in sts else
                  "waiting" if any(x in sts for x in ("dispatched", "queued", "waiting", "interrupted")) else
                  "failed" if "failed" in sts else
                  "finished" if all(x == "done" for x in sts) else "unknown")
    return out


def pretty(code: str) -> str:
    try:
        return datetime.strptime(code, "%y%m%d").strftime("%-d %b %Y")
    except ValueError:
        return code


def manifest_for(pdir: Path, dates: list[str], watch_dir: str) -> dict:
    """The same MANIFEST.json shape handoff.py writes, for these dates."""
    net, act = [], []
    for d in dates:
        if (pdir / d).is_dir():
            net += handoff.collect_network(pdir / d, [])
    act_dir = pdir / "ActivityScan"
    if act_dir.is_dir():
        act = [r for r in handoff.collect_activity(act_dir, []) if r["date"] in dates]
    return {"created": datetime.now().isoformat(timespec="seconds"), "output_dir": str(pdir),
            "activity_dir": str(act_dir) if act_dir.is_dir() else None,
            "input_dir_read_only": watch_dir or None, "dates": dates,
            "network_wells": net, "activity_runs": act}


def build(manifest_path: Path, out: Path, py: str) -> tuple[bool, str]:
    r = subprocess.run([py, str(BUILD), "--manifest", str(manifest_path), "--out", str(out)],
                       capture_output=True, text=True)
    ok = (out / "report.html").exists()
    return ok, (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ""


# --------------------------------------------------------------------------- #
# Multi-date overview: trends from the per-date tables
# --------------------------------------------------------------------------- #
NET_TRENDS = [("spiking_channels", "Spiking channels"), ("fr_median_hz", "Median channel rate (Hz)"),
              ("bursty_pct", "Bursty channels (%)"), ("nb_rate_per_min", "Network bursts / min"),
              ("nb_burst_duration_s_mean", "Burst duration (s)"),
              ("nb_participation_fraction_mean", "Burst participation")]
ACT_TRENDS = [("electrodes_active", "Active electrodes"), ("active_fraction", "Active fraction"),
              ("rate_mean_hz", "Mean rate (Hz)"), ("amplitude_median_uv", "Median amplitude (µV)"),
              ("network_burst_rate_hz", "Block burst rate (Hz)"), ("synchrony_fano", "Synchrony (Fano)")]
COLOURS = ["#2563eb", "#d97706", "#059669", "#dc2626", "#7c3aed", "#0891b2", "#db2777", "#65a30d"]


def overview(report_dir: Path, dates: list[str], built: dict[str, bool], project: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": "#e5e7eb", "figure.dpi": 110,
                         "savefig.bbox": "tight", "legend.frameon": False})

    def b64(fig):
        buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode()

    net, act, rows = [], [], []
    for d in dates:
        t = report_dir / "dates" / d / "tables"
        n = pd.read_csv(t / "network_all_metrics.csv") if (t / "network_all_metrics.csv").exists() else None
        a = pd.read_csv(t / "activity_all_metrics.csv") if (t / "activity_all_metrics.csv").exists() else None
        if n is not None:
            n["date"] = d; net.append(n)
        if a is not None:
            a["date"] = d; act.append(a)
        rows.append({"date": d, "recorded": pretty(d),
                     "network_wells": 0 if n is None else len(n),
                     "complete": 0 if n is None else int((n["status"] == "complete").sum()),
                     "burst_metrics_usable": 0 if n is None or "burst_flag" not in n else int((~n["burst_flag"].astype(bool)).sum()),
                     "scan_wells": 0 if a is None else len(a),
                     "scan_qc_pass": 0 if a is None or "qc" not in a else int((a["qc"] == "pass").sum()),
                     "report": f"dates/{d}/report.html" if built.get(d) else ""})
    net = pd.concat(net, ignore_index=True) if net else pd.DataFrame()
    act = pd.concat(act, ignore_index=True) if act else pd.DataFrame()

    # Days in vitro, when one plating date covers everything.
    xs = {d: datetime.strptime(d, "%y%m%d").date() for d in dates}
    xlabel = "Recording date"
    if len(act) and "plating_date" in act and act["plating_date"].nunique() == 1:
        dd, mm, yy = (int(v) for v in str(act["plating_date"].iloc[0]).split("."))
        plated = date(yy, mm, dd)
        xs = {d: (v - plated).days for d, v in xs.items()}
        xlabel = f"Days in vitro (plated {plated:%-d %b %Y})"

    def trend(df, metrics, title, usable=None):
        if not len(df):
            return f"<p class='note'>No {title.lower()} results for these dates.</p>"
        d = df if usable is None else df[usable(df)]
        chips = sorted(d["chip"].dropna().unique())
        col = {c: COLOURS[i % len(COLOURS)] for i, c in enumerate(chips)}
        fig, axes = plt.subplots(2, 3, figsize=(13, 7))
        for ax, (m, lab) in zip(axes.flat, metrics):
            if m not in d:
                ax.axis("off"); continue
            for c in chips:
                g = d[d["chip"] == c].groupby("date")[m].median()
                if len(g):
                    ax.plot([xs[x] for x in g.index], g.values, "-o", ms=3.5, lw=1.2, color=col[c], label=c, alpha=.85)
            allm = d.groupby("date")[m].median()
            ax.plot([xs[x] for x in allm.index], allm.values, "-", lw=3, color="#151b36", label="all wells", alpha=.8)
            ax.set_title(lab); ax.set_xlabel(xlabel)
            if not isinstance(next(iter(xs.values())), int):
                ax.tick_params(axis="x", rotation=30)
        axes.flat[0].legend(fontsize=7.5)
        fig.suptitle(f"{title} — median per chip (thin) and across all wells (thick)", y=1.01)
        fig.tight_layout()
        return f"<img class='fig' src='data:image/png;base64,{b64(fig)}'>"

    usable = (lambda df: ~df["burst_flag"].astype(bool)) if "burst_flag" in net else None
    summary = pd.DataFrame(rows)
    summary.to_csv(report_dir / "overview_dates.csv", index=False)
    if len(net):
        net.to_csv(report_dir / "network_all_dates.csv", index=False)
    if len(act):
        act.to_csv(report_dir / "activity_all_dates.csv", index=False)

    def link(href):
        return f'<a href="{href}">Open the full report →</a>' if href else "not built"

    trs = "".join(
        f"<tr><td>{r['recorded']}</td><td class='m'>{r['date']}</td><td class='n'>{r['network_wells']}</td>"
        f"<td class='n'>{r['complete']}</td><td class='n'>{r['burst_metrics_usable']}</td>"
        f"<td class='n'>{r['scan_wells']}</td><td class='n'>{r['scan_qc_pass']}</td>"
        f"<td>{link(r['report'])}</td></tr>"
        for r in rows)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MEA overview — {html.escape(project)}</title><style>
body{{margin:0;font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#111827;background:#f9fafb}}
header{{background:#fff;border-bottom:1px solid #e5e7eb;padding:18px 24px}} h1{{font-size:20px;margin:0 0 4px}}
.meta{{color:#4b5563;font-size:13px}} main{{max-width:1180px;margin:0 auto;padding:8px 24px 60px}}
h2{{font-size:17px;margin:34px 0 10px;padding-top:8px;border-top:1px solid #e5e7eb}}
table{{border-collapse:collapse;width:100%;font-size:13px;background:#fff;border:1px solid #e5e7eb}}
th,td{{padding:7px 10px;border-top:1px solid #e5e7eb;text-align:left}} th{{background:#f3f4f6}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}} td.m{{font-family:monospace;color:#6b7280}}
a{{color:#2563eb}} .fig{{max-width:100%;background:#fff;border-radius:6px;margin:10px 0}} .note{{color:#4b5563}}
</style></head><body><header><h1>MEA overview — {html.escape(project.replace('_', ' '))}</h1>
<div class="meta">{len(dates)} recording dates · {pretty(dates[0])} to {pretty(dates[-1])} ·
spike detection only (no sorting) · generated {datetime.now():%Y-%m-%d %H:%M}</div></header><main>
<h2>Dates in this report</h2><p class="note">Each date has the full standard report (Network analysis and
Activity scan). Trends below use per-well values: medians per chip and across all wells; network-burst
trends use only wells whose burst metrics are usable (see each date's quality-control section).</p>
<table><thead><tr><th>Recorded</th><th>Folder</th><th>Network wells</th><th>Complete</th>
<th>Burst metrics usable</th><th>Scan wells</th><th>Scan QC pass</th><th>Report</th></tr></thead><tbody>{trs}</tbody></table>
<h2>Network analysis over time</h2>{trend(net, NET_TRENDS, "Network analysis", usable)}
<h2>Activity scan over time</h2>{trend(act, ACT_TRENDS, "Activity scan")}
<h2>Data</h2><p class="note">All per-well values for these dates: network_all_dates.csv, activity_all_dates.csv,
overview_dates.csv (in this folder). Chips are matched by chip id across dates; the same chip id on two
dates is the same plate.</p></main></body></html>"""
    (report_dir / "report.html").write_text(doc)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", type=Path, required=True,
                    help="Results folder of one project, e.g. .../spike_detection/IPN_Organoids_08142026_PVS")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="List the dates that have results, then stop")
    g.add_argument("--dates", nargs="+", help="Recording dates (YYMMDD folder names)")
    g.add_argument("--all", action="store_true", help="Every date with results")
    ap.add_argument("--requirements", default="", help="Extra instructions to record with the report (text or @file)")
    ap.add_argument("--label", default="", help="Name for the report folder (default: the dates)")
    ap.add_argument("--out", type=Path, help="Write here instead of <project-dir>/AI_HANDOFF/<stamp>_<label>")
    ap.add_argument("--python", default=sys.executable, help="Interpreter with pandas/matplotlib/scipy/PIL")
    ap.add_argument("--allow-unfinished", action="store_true",
                    help="Also report dates whose analysis has not finished (the report will be partial)")
    a = ap.parse_args()

    pdir = a.project_dir.expanduser().resolve()
    if not pdir.is_dir():
        sys.exit(f"Not a folder: {pdir}")
    have = available_dates(pdir)
    state = analysis_state(pdir.name)
    if a.list:
        print(f"Project: {pdir.name}")
        if not state:
            print("(control server not reachable: analysis status unknown)")
        print(f"{'date':<8} {'recorded':<13} {'analysis':<9} network wells  activity runs")
        for d, v in have.items():
            print(f"{d:<8} {pretty(d):<13} {state.get(d, 'unknown'):<9} "
                  f"{v.get('network_wells_with_results', 0):>13}  {v.get('activity_runs', 0):>13}")
        return

    dates = sorted(have) if a.all else sorted(set(a.dates))
    missing = [d for d in dates if d not in have]
    if missing:
        sys.exit(f"No results for {', '.join(missing)} in {pdir}. Run with --list to see the dates that have results.")
    unfinished = [d for d in dates if state.get(d) not in (None, "finished")]
    if a.all and not a.allow_unfinished:
        dates = [d for d in dates if d not in unfinished]
        if unfinished:
            print(f"Leaving out dates still being analysed or not finished: {', '.join(unfinished)}")
        if not dates:
            sys.exit("No finished dates to report.")
    elif unfinished and not a.allow_unfinished:
        sys.exit("Not finished yet: " + ", ".join(f"{d} ({state[d]})" for d in unfinished) +
                 ". Wait for the analysis to finish, or add --allow-unfinished for a partial report.")

    label = re.sub(r"[^A-Za-z0-9_-]", "", a.label) or (dates[0] if len(dates) == 1 else f"{dates[0]}-{dates[-1]}_{len(dates)}dates")
    hdir = a.out.resolve() if a.out else pdir / handoff.HANDOFF_DIRNAME / f"{datetime.now():%Y%m%d_%H%M%S}_{label}"
    report = hdir / "report"
    report.mkdir(parents=True, exist_ok=False)

    # The input folder the results came from, for the record (read-only).
    watch = ""
    for w in handoff.collect_network(pdir / dates[0], []) if (pdir / dates[0]).is_dir() else []:
        if w.get("recording"):
            watch = str(Path(w["recording"]).parents[4]); break

    req = a.requirements[1:] if a.requirements.startswith("@") else ""
    req_text = Path(req).read_text() if req else a.requirements
    shutil.copyfile(handoff.DEFAULT_SKILLS, hdir / "skills.md")
    (hdir / "REQUIREMENTS.md").write_text("# Requirements\n\n" + (req_text.strip() or
                                          "Standard report (Network analysis + Activity scan).") + "\n")
    full = manifest_for(pdir, dates, watch)
    (hdir / "MANIFEST.json").write_text(json.dumps(full, indent=2))

    built: dict[str, bool] = {}
    if len(dates) == 1:
        ok, msg = build(hdir / "MANIFEST.json", report, a.python)
        built[dates[0]] = ok
        print(("built " if ok else "FAILED ") + f"{dates[0]}: {msg}")
    else:
        for d in dates:
            out = report / "dates" / d
            out.mkdir(parents=True)
            m = manifest_for(pdir, [d], watch)
            (out / "MANIFEST.json").write_text(json.dumps(m, indent=2))
            ok, msg = build(out / "MANIFEST.json", out, a.python)
            built[d] = ok
            print(("built " if ok else "FAILED ") + f"{d}: {msg}")
        overview(report, dates, built, pdir.name)
        print(f"overview: {report / 'report.html'}")

    print(json.dumps({"report": str(report / "report.html"), "folder": str(hdir), "dates": dates,
                      "built": built, "network_wells": len(full["network_wells"]),
                      "activity_runs": len(full["activity_runs"])}, indent=2))
    if not all(built.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
