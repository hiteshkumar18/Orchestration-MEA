#!/usr/bin/env python3
"""
The standard MEA report: one self-contained HTML file with two pages
(Network analysis, Activity scan), plus every table as CSV in tables/.

Reads only the result files listed in a MANIFEST.json (written by
orchestration/handoff.py). Writes only into the output folder.

    python build_report.py                       # MANIFEST at ../MANIFEST.json, output here
    python build_report.py --manifest M.json --out DIR

Usually run through make_report.py, which prepares the manifest.
"""

from __future__ import annotations

import base64
import html
import io
import json
import math
from datetime import date, datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

import argparse  # noqa: E402

_ap = argparse.ArgumentParser(description="Build the standard MEA report")
_ap.add_argument("--manifest", type=Path, help="MANIFEST.json (default: ../MANIFEST.json)")
_ap.add_argument("--out", type=Path, help="Folder to write report.html and tables/ into (default: here)")
_args, _ = _ap.parse_known_args()
HERE = (_args.out or Path(__file__).resolve().parent).resolve()
HERE.mkdir(parents=True, exist_ok=True)
HANDOFF = HERE.parent
TABLES = HERE / "tables"
TABLES.mkdir(exist_ok=True)
MANIFEST = json.loads((_args.manifest or (HANDOFF / "MANIFEST.json")).read_text())
SOURCES: dict[str, set[str]] = {"network": set(), "activity": set()}

ARTIFACT_HZ = 100.0          # report-side flag: mean rate above this over the whole recording
NOISE_BURST_PER_MIN = 60.0   # report-side flag: more than one network burst per second
CHIP_COLOURS = ["#2563eb", "#d97706", "#059669", "#dc2626", "#7c3aed", "#0891b2",
                "#db2777", "#65a30d"]

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e5e7eb", "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.dpi": 110, "savefig.bbox": "tight",
    "legend.frameon": False, "legend.fontsize": 8,
})


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def src(kind: str, path) -> Path:
    SOURCES[kind].add(str(path))
    return Path(path)


def fig_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def img(fig, alt: str) -> str:
    return f'<img class="fig" alt="{html.escape(alt)}" src="data:image/png;base64,{fig_b64(fig)}">'


def file_img(path: Path, alt: str, kind: str, max_w: int = 1100) -> str:
    """Embed an existing figure, re-encoded as JPEG to keep the file small."""
    src(kind, path)
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=80, optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    return (f'<img class="fig" loading="lazy" alt="{html.escape(alt)}" '
            f'src="data:image/jpeg;base64,{data}">')


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}"
    if isinstance(v, (float, np.floating)):
        a = abs(v)
        if a == 0:
            return "0"
        if a >= 1 and float(v).is_integer():
            return f"{int(v):,}"
        if a >= 1000:
            return f"{v:,.0f}"
        if a >= 100:
            return f"{v:.1f}"
        if a >= 1:
            return f"{v:.2f}"
        return f"{v:.{nd}g}"
    return html.escape(str(v))


def table(df: pd.DataFrame, name: str, caption: str, index=False) -> str:
    """HTML table (sortable) and the same table as tables/<name>.csv."""
    df.to_csv(TABLES / f"{name}.csv", index=index)
    d = df.reset_index() if index else df
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
    rows = []
    for _, r in d.iterrows():
        cells = []
        for c in d.columns:
            v = r[c]
            num = isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
            sort = f' data-v="{v}"' if num and not (isinstance(v, float) and math.isnan(v)) else ""
            cells.append(f'<td class="{"n" if num else ""}"{sort}>{fmt(v)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="tw"><table class="sortable"><caption>{html.escape(caption)} '
            f'<a class="csv" title="Also saved as CSV">tables/{name}.csv</a></caption>'
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def chip_colour_map(chips) -> dict:
    return {c: CHIP_COLOURS[i % len(CHIP_COLOURS)] for i, c in enumerate(sorted(chips))}


def strip_by_chip(ax, df, col, colours, flag_col=None, ylabel="", log=False):
    """One point per well, grouped by chip; mean line per chip."""
    chips = sorted(df["chip"].unique())
    for i, c in enumerate(chips):
        sub = df[df["chip"] == c]
        y = sub[col].astype(float).values
        x = i + np.linspace(-0.12, 0.12, len(y)) if len(y) > 1 else np.array([i])
        flagged = sub[flag_col].values if flag_col else np.zeros(len(y), bool)
        ok = ~np.isnan(y)
        ax.scatter(x[ok & ~flagged], y[ok & ~flagged], s=26, color=colours[c], zorder=3)
        ax.scatter(x[ok & flagged], y[ok & flagged], s=34, facecolors="none",
                   edgecolors=colours[c], linewidths=1.3, zorder=3, marker="o")
        if ok.any():
            ax.hlines(np.nanmean(y), i - 0.25, i + 0.25, color="#374151", lw=1.2, zorder=2)
    ax.set_xticks(range(len(chips)))
    ax.set_xticklabels(chips, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")


def spearman_heatmap(df: pd.DataFrame, cols: dict, title: str):
    sub = df[list(cols)].astype(float)
    n = len(cols)
    rho = np.full((n, n), np.nan)
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if a == b:
                rho[i, j] = 1.0 if sub[a].notna().sum() >= 5 else np.nan
                continue
            ok = sub[[a, b]].dropna()
            if len(ok) >= 5 and ok[a].nunique() > 1 and ok[b].nunique() > 1:
                rho[i, j] = spearmanr(ok[a], ok[b]).statistic
    fig, ax = plt.subplots(figsize=(0.55 * n + 2.5, 0.5 * n + 1.8))
    ax.grid(False)
    im = ax.imshow(rho, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = list(cols.values())
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(n)); ax.set_yticklabels(labels)
    for i in range(n):
        for j in range(n):
            if not np.isnan(rho[i, j]):
                ax.text(j, i, f"{rho[i, j]:.2f}", ha="center", va="center", fontsize=7,
                        color="white" if abs(rho[i, j]) > 0.6 else "#111827")
    fig.colorbar(im, ax=ax, shrink=0.7, label="Spearman ρ")
    ax.set_title(title)
    return fig, pd.DataFrame(rho, index=labels, columns=labels)


def downsample_max(t, y, n=2000):
    """Max-pool to n points so peaks survive plotting."""
    if len(y) <= n:
        return t, y
    k = len(y) // n
    m = len(y) // k * k
    return t[:m].reshape(-1, k).mean(1), y[:m].reshape(-1, k).max(1)


# --------------------------------------------------------------------------- #
# Load: Network
# --------------------------------------------------------------------------- #
METRIC_KEYS = ["burst_duration_s", "ibi_s", "ifbi_s", "spike_count_per_burst",
               "participation_fraction", "peak_participation_fraction",
               "peak_population_firing_rate_hz", "burst_area"]

net_rows, unit_frames, event_frames, diag_rows, pop = [], [], [], [], {}


def driver_errors() -> dict:
    """(recording, well) -> the driver's one-line reason a well failed.

    Read from the date's network log in <output>/<project>/orchestration_logs,
    so a failed well is reported with its cause (skills.md §3a).
    """
    found: dict = {}
    roots = {Path(w["output_dir"]).parents[4] for w in MANIFEST["network_wells"] if w.get("output_dir")}
    dates = {w["date"] for w in MANIFEST["network_wells"]}
    import re as _re
    for root in roots:
        for d in dates:
            logs = sorted((root / "orchestration_logs").glob(f"{d}_network_*.log"))
            if not logs:
                continue
            cur = None
            for line in src("network", logs[-1]).read_text(errors="ignore").splitlines():
                m = _re.search(r"Processing : (\S+) recording : \S+ well_id : (well\d+)", line)
                if m:
                    cur = (m.group(1), m.group(2))
                m = _re.search(r"CRITICAL FAILURE in (well\d+): (.*)", line)
                if m and cur and cur[1] == m.group(1):
                    found[cur] = m.group(2).strip()[:220]
                elif cur and cur not in found and _re.search(r"Detected 0 total spikes|returned error: no_spikes", line):
                    found[cur] = "no spikes detected"
    return found


def outcome(status: str, why: str | None) -> str:
    """complete / silent / not_recorded / failed — same reading as the control UI."""
    if status == "complete":
        return "complete"
    if why and "is not in [" in why and "stream_id" in why:
        return "not_recorded"
    if why == "no spikes detected":
        return "silent"
    return "failed"


DRIVER_ERR = driver_errors()
for w in sorted(MANIFEST["network_wells"], key=lambda x: (x["chip_id"], x["well"])):
    o = Path(w["output_dir"])
    key = f'{w["chip_id"]} {w["well"]}'
    if not (o / "network_results.json").exists():
        # A well that failed in the pipeline has no results: keep it in every
        # table with its error (skills.md rule 3), with no metrics.
        err = (w.get("error") or "no network_results.json written").strip().splitlines()
        why = DRIVER_ERR.get((w.get("recording") or "", w["well"]))
        net_rows.append({"chip": w["chip_id"], "run": w["run_id"], "well": w["well"],
                         "plate_label": int(w["well"][-3:]) + 1, "status": w["status"],
                         "mode": w.get("mode"), "channels": np.nan, "spiking_channels": np.nan,
                         "total_spikes": np.nan, "artifact_channels": np.nan, "artifact_spike_pct": np.nan,
                         "nb_count": np.nan, "nb_rate_per_min": np.nan, "detection_valid": None,
                         "burst_flag": True, "artifact_dominated": False,
                         "outcome": outcome(w["status"], why),
                         "flags": ("not in the recording file — MaxWell's file has no data for this well"
                                   if outcome(w["status"], why) == "not_recorded" else
                                   "no spikes detected — a silent well, nothing to analyse"
                                   if outcome(w["status"], why) == "silent" else
                                   f"failed in the pipeline: {err[-1][:200] if err else ''}"
                                   if w["status"] == "failed" else
                                   f"did not finish: {why}" if why else
                                   f"did not finish: stopped at '{w.get('stage')}' with no error recorded "
                                   "— see the driver log")})
        continue
    res = json.loads(src("network", o / "network_results.json").read_text())
    us = pd.read_csv(src("network", o / "unit_stats.csv"))
    st = np.load(src("network", o / "spike_times.npy"), allow_pickle=True).item()
    pinfo = json.loads(src("network", o / "processing_info.json").read_text())
    npz = np.load(src("network", o / "network_plot_data.npz"))
    bad_path = o / "bad_channels.json"
    bad = (len(json.loads(src("network", bad_path).read_text()).get("bad_channel_ids", []))
           if bad_path.exists() else None)

    counts = {str(k): len(v) for k, v in st.items()}
    us["unit_id"] = us["unit_id"].astype(str)
    us["spikes"] = us["unit_id"].map(counts).fillna(0).astype(int)
    # Recording length from the files themselves: spikes / mean rate per unit.
    with np.errstate(divide="ignore", invalid="ignore"):
        dur_est = (us["spikes"] / us["mean_firing_rate_hz"]).replace([np.inf], np.nan)
    duration = float(np.nanmedian(dur_est)) if dur_est.notna().any() else float(npz["time_s"][-1])
    us["artifact"] = us["mean_firing_rate_hz"] > ARTIFACT_HZ
    us.insert(0, "chip", w["chip_id"]); us.insert(1, "run", w["run_id"]); us.insert(2, "well", w["well"])
    unit_frames.append(us)

    spiking = us[us["spikes"] > 0]
    total = int(us["spikes"].sum())
    art_spikes = int(us.loc[us["artifact"], "spikes"].sum())

    nb = res["network_bursts"]["metrics"]
    fr = res["burst_fragments"]["metrics"]
    sb = res["superbursts"]
    diag = res.get("diagnostics", {})
    row = {
        "chip": w["chip_id"], "run": w["run_id"], "well": w["well"],
        "plate_label": int(w["well"][-3:]) + 1,
        "status": w["status"], "mode": pinfo.get("processing_mode"),
        "duration_s": duration,
        "channels": int(res.get("n_units") or len(us)),
        "spiking_channels": int(len(spiking)),
        "channels_ge_0.1Hz": int((us["mean_firing_rate_hz"] >= 0.1).sum()),
        "total_spikes": total,
        "artifact_channels": int(us["artifact"].sum()),
        "artifact_spike_pct": 100.0 * art_spikes / total if total else np.nan,
        "bad_channels": bad,
        "fr_median_hz": float(spiking["mean_firing_rate_hz"].median()) if len(spiking) else np.nan,
        "fr_q25_hz": float(spiking["mean_firing_rate_hz"].quantile(.25)) if len(spiking) else np.nan,
        "fr_q75_hz": float(spiking["mean_firing_rate_hz"].quantile(.75)) if len(spiking) else np.nan,
        "bursty_channels": int(us["is_bursty"].sum()),
        "bursty_pct": 100.0 * us["is_bursty"].mean() if len(us) else np.nan,
        "cv_isi_median": float(spiking["cv_isi"].median()) if len(spiking) else np.nan,
        "cv2_median": float(spiking["cv2"].median()) if len(spiking) else np.nan,
        "lv_median": float(spiking["lv"].median()) if len(spiking) else np.nan,
        "bimodality_median": float(spiking["bimodality_coefficient"].median()) if len(spiking) else np.nan,
        "nb_count": nb.get("burst_count", 0) or 0,
        "nb_rate_per_min": 60.0 * (nb.get("burst_rate_hz") or 0.0),
        "frag_count": fr.get("burst_count", 0) or 0,
        "frag_rate_per_min": 60.0 * (fr.get("burst_rate_hz") or 0.0),
        "superbursts": len(sb.get("events", [])),
        "detection_valid": diag.get("burst_detection_valid"),
    }
    for prefix, m in (("nb", nb), ("frag", fr)):
        for k in METRIC_KEYS:
            v = m.get(k)
            if isinstance(v, dict):
                for s in ("mean", "std", "cv"):
                    row[f"{prefix}_{k}_{s}"] = v.get(s)
    flags = []
    if not row["nb_count"]:
        flags.append("no network bursts")
    if row["spiking_channels"] < 10:
        flags.append(f"only {row['spiking_channels']} spiking channels")
    if row["nb_rate_per_min"] > NOISE_BURST_PER_MIN:
        flags.append(f"{row['nb_rate_per_min']:.0f} bursts/min — likely detecting noise fluctuations")
    # Burst metrics are unreliable when any of the above holds.
    row["burst_flag"] = bool(flags)
    if row["artifact_spike_pct"] > 50:
        flags.append(f"{row['artifact_spike_pct']:.0f}% of spikes on channels >{ARTIFACT_HZ:.0f} Hz "
                     "(inflates spike counts and population rate)")
    row["flags"] = "; ".join(flags)
    row["artifact_dominated"] = row["artifact_spike_pct"] > 50
    net_rows.append(row)

    diag_rows.append({"chip": w["chip_id"], "well": w["well"],
                      **{k: v for k, v in diag.items() if not isinstance(v, (dict, list))}})
    for kind, block in (("network_burst", res["network_bursts"]), ("fragment", res["burst_fragments"]),
                        ("superburst", res["superbursts"])):
        ev = pd.DataFrame(block.get("events", []))
        if len(ev):
            ev.insert(0, "event_type", kind); ev.insert(0, "well", w["well"]); ev.insert(0, "chip", w["chip_id"])
            event_frames.append(ev)
    pop[key] = {k: npz[k] for k in npz.files}

net = pd.DataFrame(net_rows, columns=None if net_rows else ["chip", "well", "flags", "burst_flag", "artifact_dominated"])
if len(net):
    net["outcome"] = net["outcome"].fillna("complete") if "outcome" in net else "complete"
oc = net["outcome"] if "outcome" in net else pd.Series(dtype=str)
units = pd.concat(unit_frames, ignore_index=True)
events = pd.concat(event_frames, ignore_index=True) if event_frames else pd.DataFrame()
diag_df = pd.DataFrame(diag_rows)
nb_ev = events[events["event_type"] == "network_burst"].copy() if len(events) else pd.DataFrame()
if len(nb_ev):
    nb_ev = nb_ev.sort_values(["chip", "well", "start_time_s"])
    nb_ev["ibi_s"] = nb_ev.groupby(["chip", "well"])["start_time_s"].diff()

# --------------------------------------------------------------------------- #
# Load: Activity scan
# --------------------------------------------------------------------------- #
act_rows, elec_frames, run_meta = [], [], []
for r in sorted(MANIFEST["activity_runs"], key=lambda x: x["chip_id"]):
    s = json.loads(src("activity", r["summary"]).read_text())
    run_meta.append({k: v for k, v in s.items() if k != "wells"} | {"summary": r["summary"]})
    for wl in s["wells"]:
        row = {"chip": s["chip_id"], "run": s["run_id"], "well": f'well{int(wl["well_id"]):03d}'}
        for k, v in wl.items():
            if k == "centroid_um" and isinstance(v, list) and len(v) == 2:
                row["centroid_x_um"], row["centroid_y_um"] = v
            elif k == "qc_reasons":
                row[k] = "; ".join(v)
            else:
                row[k] = v
        act_rows.append(row)
    if r.get("per_electrode"):
        pe = pd.read_csv(src("activity", r["per_electrode"]))
        pe.insert(0, "chip", s["chip_id"])
        elec_frames.append(pe)
act = pd.DataFrame(act_rows, columns=None if act_rows else ["chip", "run", "well", "qc"])
elec = pd.concat(elec_frames, ignore_index=True) if elec_frames else pd.DataFrame()
act_thr = float(run_meta[0].get("active_threshold_hz", 0.05)) if run_meta else 0.05

# Selection metrics are valid only against a Network recording on the same
# chip; summary.json records which one was used (skills.md §3b).
def _sel_ok(meta: dict) -> bool:
    srcp = meta.get("selection_source")
    return bool(srcp) and meta.get("chip_id") in Path(srcp).parts
SEL_VALID = {m["chip_id"]: _sel_ok(m) for m in run_meta}
SEL_SOURCE = {m["chip_id"]: m.get("selection_source") for m in run_meta}
act["selection_valid"] = act["chip"].map(SEL_VALID).fillna(False) if len(act) else []

all_chips = sorted(set(net["chip"]) | set(act["chip"]))
COL = chip_colour_map(all_chips)

# Session facts
rec_dates = sorted({w["date"] for w in MANIFEST["network_wells"]} |
                   {r["date"] for r in MANIFEST["activity_runs"]})
rec_date = datetime.strptime(rec_dates[0], "%y%m%d").date() if rec_dates else None
plating = sorted(set(act["plating_date"].dropna())) if "plating_date" in act else []
div = None
if rec_date and len(plating) == 1:
    d, m, y = (int(x) for x in plating[0].split("."))
    div = (rec_date - date(y, m, d)).days
groups = sorted(set(act["group"].dropna())) if "group" in act else []
project = (MANIFEST["network_wells"][0]["project"] if MANIFEST["network_wells"]
           else Path(MANIFEST["folders_in_scope"][0]).parent.name if MANIFEST.get("folders_in_scope") else "")


# --------------------------------------------------------------------------- #
# Page 1: Network
# --------------------------------------------------------------------------- #
def network_page() -> str:
    P = []
    ok = net[~net["burst_flag"]]
    flagged = net[net["burst_flag"]]
    art_wells = net[net["artifact_dominated"]]

    P.append("<h2>Summary</h2><ul class='sum'>")
    P.append(f"<li><b>{len(net)}</b> wells on <b>{net['chip'].nunique()}</b> chips analysed, "
             f"<b>{(net['status'] == 'complete').sum()}</b> complete"
             f"{', <b>' + str((net['status'] == 'failed').sum()) + '</b> failed' if (net['status'] == 'failed').any() else ''}"
             + "".join(f", <b>{n}</b> {label}" for n, label in (
                 (int((oc == "silent").sum()), "with no spikes (silent)"),
                 (int((oc == "not_recorded").sum()), "not in the recording file"),
                 (int(net["status"].isin(["running", "pending"]).sum() - (oc.isin(["silent", "not_recorded"]) & net["status"].isin(["running", "pending"])).sum()),
                  "did not finish (listed under QC)")) if n) + ", in "
             f"<b>detection-only</b> mode: a unit here is an electrode channel, not a neuron.</li>")
    P.append(f"<li>Burst metrics are usable in <b>{len(ok)}</b> of {len(net)} wells. The other {len(flagged)} "
             f"have no network bursts, fewer than 10 spiking channels, or more than "
             f"{NOISE_BURST_PER_MIN:.0f} bursts per minute (detection riding on noise): "
             f"{', '.join(flagged['chip'] + ' ' + flagged['well'])}.</li>")
    if len(ok):
        P.append(f"<li>In the usable wells, network bursts occur at a median <b>{fmt(ok['nb_rate_per_min'].median())}</b> "
                 f"per minute (range {fmt(ok['nb_rate_per_min'].min())}–{fmt(ok['nb_rate_per_min'].max())}), last "
                 f"{fmt(ok['nb_burst_duration_s_mean'].median())} s and recruit "
                 f"{fmt(100 * ok['nb_participation_fraction_mean'].median())}% of channels (medians across "
                 f"n = {len(ok)} wells).</li>")
    P.append(f"<li>Spiking channels per well: median <b>{fmt(net['spiking_channels'].median())}</b> "
             f"(range {fmt(net['spiking_channels'].min())}–{fmt(net['spiking_channels'].max())}); "
             f"median channel firing rate {fmt(net['fr_median_hz'].median())} Hz "
             f"(n = {int(net['spiking_channels'].notna().sum())} wells with results).</li>")
    P.append(f"<li>In <b>{len(art_wells)}</b> wells, more than half of all spikes come from a few channels firing "
             f"above {ARTIFACT_HZ:.0f} Hz on average ({fmt(art_wells['artifact_channels'].median())} such channels "
             f"per well, median) — implausible for neurons, most likely noise. They inflate spike counts and "
             f"population rates; burst detection works on participation (fraction of channels active) and is "
             f"much less affected.</li></ul>")

    P.append("<h2>Dataset</h2>")
    P.append(f"<p>Project <b>{html.escape(project)}</b>, recorded <b>{rec_date}</b>"
             f"{f', plated {plating[0]} — <b>{div} days in vitro</b>' if div is not None else ''}. "
             f"Recording length {fmt(net['duration_s'].median())} s per well (derived as spikes ÷ mean rate "
             f"in unit_stats.csv). No experimental groups were entered in MaxWell (group labels: "
             f"{', '.join(html.escape(g) for g in groups) or 'none'}), so wells are compared by chip only.</p>")
    per_chip = net.groupby("chip").agg(wells=("well", "count"), complete=("status", lambda s: (s == "complete").sum()),
                                       with_bursts=("nb_count", lambda s: (s > 0).sum()),
                                       burst_metrics_usable=("burst_flag", lambda s: (~s).sum())).reset_index()
    P.append(table(per_chip, "network_wells_per_chip", "Wells per chip"))

    P.append("<h2>Quality control</h2>")
    nfail = int((oc == "failed").sum())
    P.append("<p>Report-side checks, applied identically to every well. "
             + (f"<b>{nfail} well(s) failed or stopped without results</b>; the reason is in "
                "the flags column and they have no metrics. " if nfail else "No well failed in the pipeline. ") +
             "<b>Burst metrics unreliable</b> (hollow points; left out of correlations and pooled event plots, "
             f"kept in every table): no network bursts; fewer than 10 spiking channels; more than "
             f"{NOISE_BURST_PER_MIN:.0f} network bursts per minute. <b>Noisy channels</b> (reported, not excluded): "
             f"channels whose mean rate over the recording exceeds {ARTIFACT_HZ:.0f} Hz. "
             "bad_channels.json was not written in this mode, so pipeline-excluded channels are not reported.</p>")
    qc = net[["chip", "well", "status", "channels", "spiking_channels", "total_spikes", "artifact_channels",
              "artifact_spike_pct", "nb_count", "nb_rate_per_min", "burst_flag", "detection_valid", "flags"]]
    P.append(table(qc, "network_qc", "Per-well QC"))

    P.append("<h2>Per-well network metrics</h2>")
    key_cols = ["chip", "well", "spiking_channels", "fr_median_hz", "bursty_pct", "nb_count", "nb_rate_per_min",
                "nb_burst_duration_s_mean", "nb_ibi_s_mean", "nb_ibi_s_cv", "nb_spike_count_per_burst_mean",
                "nb_participation_fraction_mean", "nb_peak_population_firing_rate_hz_mean", "frag_rate_per_min",
                "superbursts", "flags"]
    P.append(table(net[[c for c in key_cols if c in net]], "network_key_metrics",
                   "Key metrics (nb = network bursts; mean across bursts within the well)"))
    P.append("<details><summary>All per-well values (every metric, mean / std / CV)</summary>"
             + table(net, "network_all_metrics", "All per-well network values") + "</details>")

    # Strip plots
    panels = [("spiking_channels", "Spiking channels", False), ("fr_median_hz", "Median channel rate (Hz)", True),
              ("bursty_pct", "Bursty channels (%)", False), ("nb_rate_per_min", "Network bursts / min", False),
              ("nb_burst_duration_s_mean", "Burst duration (s)", False), ("nb_ibi_s_mean", "Inter-burst interval (s)", False),
              ("nb_ibi_s_cv", "IBI CV (regularity)", False), ("nb_participation_fraction_mean", "Participation (fraction)", False),
              ("nb_spike_count_per_burst_mean", "Spikes per burst", True),
              ("nb_peak_population_firing_rate_hz_mean", "Peak population rate (Hz)", True),
              ("frag_rate_per_min", "Burst fragments / min", False), ("lv_median", "Median LV", False)]
    fig, axes = plt.subplots(3, 4, figsize=(13, 9))
    for ax, (c, lab, lg) in zip(axes.flat, panels):
        strip_by_chip(ax, net, c, COL, "burst_flag", lab, log=lg and (net[c] > 0).any())
        ax.set_title(lab)
    fig.suptitle("Per-well metrics by chip — each point a well; bar = chip mean of all wells; "
                 "hollow = burst metrics unreliable (see QC)",
                 y=1.01)
    fig.tight_layout()
    P.append("<h2>Comparison across chips</h2><p>Descriptive only: without experimental groups and with 2–5 wells "
             "per chip, no hypothesis tests are applied (skills.md rule 6).</p>" + img(fig, "metrics by chip"))

    # Correlations
    corr_cols = {"spiking_channels": "Spiking ch.", "fr_median_hz": "Median rate", "bursty_pct": "% bursty",
                 "cv_isi_median": "CV ISI", "lv_median": "LV", "nb_rate_per_min": "NB/min",
                 "nb_burst_duration_s_mean": "NB dur.", "nb_ibi_s_mean": "IBI", "nb_ibi_s_cv": "IBI CV",
                 "nb_participation_fraction_mean": "Particip.", "nb_spike_count_per_burst_mean": "Spk/burst",
                 "frag_rate_per_min": "Frag/min"}
    fig, rho = spearman_heatmap(ok, corr_cols, f"Spearman correlation between per-well metrics "
                                               f"(n = {len(ok)} wells with usable burst metrics)")
    rho.to_csv(TABLES / "network_metric_correlations.csv")
    P.append("<h3>How the metrics relate</h3>" + img(fig, "correlation heatmap") +
             "<p class='note'>Cells blank where fewer than 5 wells had both values. tables/network_metric_correlations.csv</p>")

    # Units
    P.append("<h2>Channels (units)</h2><p>From unit_stats.csv: one row per electrode channel. "
             f"{len(units):,} channels in total, {int((units['spikes'] > 0).sum()):,} with at least one spike, "
             f"{int(units['artifact'].sum()):,} above {ARTIFACT_HZ:.0f} Hz.</p>")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    sp = units[units["spikes"] > 0]
    for (c, well), g in sp.groupby(["chip", "well"]):
        x = np.sort(g["mean_firing_rate_hz"].values)
        axes[0].plot(x, np.arange(1, len(x) + 1) / len(x), color=COL[c], lw=1, alpha=0.8)
    axes[0].set_xscale("log"); axes[0].axvline(ARTIFACT_HZ, color="#9ca3af", ls="--", lw=1)
    axes[0].set_xlabel("Mean firing rate (Hz)"); axes[0].set_ylabel("Cumulative fraction of channels")
    axes[0].set_title("Firing-rate distribution per well")
    good = sp[~sp["artifact"]]
    for c in sorted(good["chip"].unique()):
        g = good[good["chip"] == c]
        axes[1].scatter(g["cv_isi"], g["lv"], s=6, alpha=0.4, color=COL[c], label=c)
    axes[1].axhline(1, color="#9ca3af", lw=0.8); axes[1].set_xlabel("CV of ISI"); axes[1].set_ylabel("LV")
    axes[1].set_title("Firing regularity (LV ≈ 1 Poisson, > 1 bursty)"); axes[1].legend(markerscale=3)
    bc = good["bimodality_coefficient"].dropna()
    axes[2].hist(bc, bins=40, color="#6b7280"); axes[2].axvline(5 / 9, color="#dc2626", ls="--", lw=1)
    axes[2].set_xlabel("Bimodality coefficient"); axes[2].set_ylabel("Channels")
    axes[2].set_title("ISI bimodality (dashed = 5/9)")
    fig.tight_layout()
    P.append(img(fig, "channel distributions"))
    per_well_units = units.groupby(["chip", "well"]).agg(
        channels=("unit_id", "count"), spiking=("spikes", lambda s: (s > 0).sum()),
        rate_mean_hz=("mean_firing_rate_hz", "mean"), rate_median_hz=("mean_firing_rate_hz", "median"),
        rate_max_hz=("mean_firing_rate_hz", "max"), cv_isi_median=("cv_isi", "median"),
        cv2_median=("cv2", "median"), lv_median=("lv", "median"),
        bimodality_median=("bimodality_coefficient", "median"), bursty=("is_bursty", "sum"),
        artifact=("artifact", "sum")).reset_index()
    P.append(table(per_well_units, "network_unit_summary", "Per-well channel statistics (all channels)"))
    units.to_csv(TABLES / "network_units_all.csv", index=False)
    P.append("<p class='note'>Every channel of every well: tables/network_units_all.csv</p>")

    # Burst events
    usable = set(ok["chip"] + " " + ok["well"])
    if len(nb_ev):
        ev_ok = nb_ev[(nb_ev["chip"] + " " + nb_ev["well"]).isin(usable)]
        P.append(f"<h2>Burst events</h2><p>{len(nb_ev):,} network bursts and "
                 f"{int((events['event_type'] == 'fragment').sum()):,} burst fragments across all wells. "
                 "Every event is in tables/network_burst_events.csv. The pooled plots below use the "
                 f"{len(usable)} wells with usable burst metrics ({len(ev_ok):,} bursts); the per-well plots "
                 "and the timeline show every well.</p>")
        events.to_csv(TABLES / "network_burst_events.csv", index=False)
        order = [k for k in (net["chip"] + " " + net["well"])]
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))
        for c in sorted(ev_ok["chip"].unique()):
            g = ev_ok[ev_ok["chip"] == c]
            axes[0].scatter(g["burst_duration_s"], g["spike_count"], s=5, alpha=0.4, color=COL[c], label=c)
        axes[0].set_xscale("log"); axes[0].set_yscale("log")
        axes[0].set_xlabel("Burst duration (s)"); axes[0].set_ylabel("Spikes in burst")
        axes[0].set_title("Each network burst"); axes[0].legend(markerscale=3)
        for c in sorted(ev_ok["chip"].unique()):
            g = ev_ok[ev_ok["chip"] == c]
            axes[1].scatter(g["participation_fraction"], g["peak_population_firing_rate_hz"], s=5,
                            alpha=0.4, color=COL[c])
        axes[1].set_yscale("log"); axes[1].set_xlabel("Participation fraction")
        axes[1].set_ylabel("Peak population rate (Hz)"); axes[1].set_title("Burst size vs recruitment")
        ib = ev_ok["ibi_s"].dropna()
        axes[2].hist(np.log10(ib[ib > 0]), bins=50, color="#6b7280")
        axes[2].set_xlabel("log10 inter-burst interval (s)"); axes[2].set_ylabel("Intervals")
        axes[2].set_title("Inter-burst intervals, usable wells")
        fig.tight_layout()
        P.append(img(fig, "burst events"))

        fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
        data_d, data_i, labels, colours = [], [], [], []
        for k in order:
            c, wl = k.split(" ")
            g = nb_ev[(nb_ev["chip"] == c) & (nb_ev["well"] == wl)]
            data_d.append(g["burst_duration_s"].values if len(g) else [np.nan])
            data_i.append(g["ibi_s"].dropna().values if g["ibi_s"].notna().any() else [np.nan])
            labels.append(k); colours.append(COL[c])
        for ax, data, lab in ((axes[0], data_d, "Burst duration (s)"), (axes[1], data_i, "Inter-burst interval (s)")):
            bp = ax.boxplot(data, showfliers=False, patch_artist=True, widths=0.6)
            for patch, colr in zip(bp["boxes"], colours):
                patch.set_facecolor(colr); patch.set_alpha(0.55)
            ax.set_yscale("log"); ax.set_ylabel(lab)
        axes[1].set_xticks(range(1, len(labels) + 1)); axes[1].set_xticklabels(labels, rotation=60, ha="right")
        axes[0].set_title("Within-well distributions (box = IQR, whiskers 1.5 × IQR)")
        fig.tight_layout()
        P.append(img(fig, "per-well burst distributions"))

        fig, ax = plt.subplots(figsize=(13, 0.32 * len(order) + 1.2))
        for i, k in enumerate(order):
            c, wl = k.split(" ")
            g = nb_ev[(nb_ev["chip"] == c) & (nb_ev["well"] == wl)]
            ax.vlines(g["start_time_s"], i - 0.38, i + 0.38, color=COL[c], lw=0.6)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.invert_yaxis()
        ax.set_xlabel("Time in recording (s)"); ax.grid(False)
        ax.set_title("Network burst timeline — one tick per burst onset")
        fig.tight_layout()
        P.append(img(fig, "burst timeline"))

    # Population activity
    keys = list(pop)
    ncol = 3
    nrow = math.ceil(len(keys) / ncol)
    for sig, ylab, title, fname in (
            ("population_firing_rate_hz", "Population rate (Hz)", "Population firing rate", "pop"),
            ("participation_fraction_signal", "Participation", "Participation signal (burst detection input)", "part")):
        fig, axes = plt.subplots(nrow, ncol, figsize=(13, 1.75 * nrow), sharex=True)
        for ax, k in zip(axes.flat, keys):
            d = pop[k]; c = k.split(" ")[0]
            t, y = downsample_max(d["time_s"], d[sig])
            ax.plot(t, y, color=COL[c], lw=0.6)
            if sig == "participation_fraction_signal":
                if len(d["nb_peak_times_s"]):
                    ax.plot(d["nb_peak_times_s"], d["nb_peak_participation_fraction"], ".", ms=2, color="#111827")
            fl = " ⚑" if k in set(net.loc[net["burst_flag"], "chip"] + " " + net.loc[net["burst_flag"], "well"]) else ""
            ax.set_title(k + fl, fontsize=8, pad=2); ax.tick_params(labelsize=7); ax.grid(False)
        for ax in list(axes.flat)[len(keys):]:
            ax.axis("off")
        fig.supxlabel("Time (s)"); fig.supylabel(ylab)
        fig.suptitle(title + (" — dots: network-burst peaks found by the pipeline"
                              if fname == "part" else ""), y=1.0)
        fig.tight_layout()
        P.append(("<h2>Population activity</h2><p>Full-length traces from network_plot_data.npz "
                  "(max-pooled for display, so peaks are preserved). ⚑ = burst metrics unreliable.</p>" if fname == "pop" else "")
                 + img(fig, title))

    P.append("<h2>Burst-detection diagnostics</h2><p>Parameters the pipeline chose per well "
             "(adaptive thresholds and merge gaps).</p>")
    P.append(table(diag_df, "network_diagnostics", "Detection diagnostics per well"))

    P.append("<h2>Pipeline raster plots</h2><p>raster_burst_plot_60s.png from each well, as produced by "
             "MEA-Analysis.</p><div class='gal'>")
    for w in sorted(MANIFEST["network_wells"], key=lambda x: (x["chip_id"], x["well"])):
        p = Path(w["output_dir"]) / "raster_burst_plot_60s.png"
        if p.exists():
            flag = net[(net.chip == w["chip_id"]) & (net.well == w["well"])]["flags"].iloc[0]
            P.append(f"<details><summary>{w['chip_id']} {w['well']}"
                     f"{' — ' + html.escape(flag) if flag else ''}</summary>"
                     f"{file_img(p, w['chip_id'] + ' ' + w['well'], 'network')}</details>")
    P.append("</div>")

    P.append("<h2>Methods</h2><ul>"
             "<li>MEA-Analysis pipeline, <code>--skip-spikesorting</code>: per-channel threshold detection "
             "(negative peaks, 5 × MAD noise, 0.1 ms exclusion), then network-burst analysis on all channels. "
             "No spike sorting, waveforms or curation.</li>"
             "<li>Burst metrics: as computed by the pipeline (network_results.json); thresholds per well in the "
             "diagnostics table. Rates per minute = burst_rate_hz × 60.</li>"
             f"<li>Report-side: channel firing-rate summaries over channels with ≥ 1 spike; artifact flag at mean "
             f"rate &gt; {ARTIFACT_HZ:.0f} Hz; inter-burst intervals from consecutive network-burst onsets; "
             "Spearman correlations across wells. Statistics are per well (n = wells).</li></ul>")
    return "\n".join(P)


# --------------------------------------------------------------------------- #
# Page 2: Activity scan
# --------------------------------------------------------------------------- #
def activity_page() -> str:
    P = []
    qc_counts = act["qc"].value_counts().to_dict()
    P.append("<h2>Summary</h2><ul class='sum'>")
    P.append(f"<li><b>{len(act)}</b> wells on <b>{act['chip'].nunique()}</b> chips scanned across the whole "
             f"array ({fmt(act['electrodes_scanned'].median())} electrodes per well, "
             f"{fmt(act['array_coverage_pct'].median())}% coverage).</li>")
    P.append(f"<li>QC: <b>{qc_counts.get('pass', 0)}</b> pass, <b>{qc_counts.get('warn', 0)}</b> warn, "
             f"<b>{qc_counts.get('fail', 0)}</b> fail.</li>")
    P.append(f"<li>Active electrodes (≥ {act_thr} Hz) per well: median <b>{fmt(act['electrodes_active'].median())}</b> "
             f"(range {fmt(act['electrodes_active'].min())}–{fmt(act['electrodes_active'].max())}), i.e. "
             f"{fmt(100 * act['active_fraction'].median())}% of the array.</li>")
    P.append(f"<li>Mean firing rate of active electrodes: median {fmt(act['rate_mean_hz'].median())} Hz across wells; "
             f"median spike amplitude {fmt(act['amplitude_median_uv'].median())} µV.</li>")
    sv = act[act["selection_valid"]]
    if len(sv) and "captured_activity_fraction" in sv:
        q = sv["selection_quality"].value_counts()
        P.append(f"<li>The electrodes chosen for each chip's Network recording captured a median "
                 f"<b>{fmt(100 * sv['captured_activity_fraction'].median())}%</b> of the activity the scan found "
                 f"(range {fmt(100 * sv['captured_activity_fraction'].min())}–"
                 f"{fmt(100 * sv['captured_activity_fraction'].max())}%, n = {len(sv)} wells); selection quality: "
                 f"{', '.join(f'{k} {v}' for k, v in q.items())}.</li>")
    bad = sorted(c for c, ok in SEL_VALID.items() if not ok)
    if bad:
        P.append(f"<li>Selection metrics not shown for {', '.join(bad)}: no same-chip Network recording recorded.</li>")
    P.append("</ul>")

    P.append("<h2>Dataset</h2>")
    meta = pd.DataFrame(run_meta)[["chip_id", "run_id", "script_id", "active_threshold_hz", "array_electrodes",
                                   "extracted_at"]]
    P.append(table(meta, "activity_runs", "ActivityScan runs"))

    P.append("<h2>Quality control</h2><p>Verdicts from the activity scan: warn/fail when fewer than 50 active "
             "electrodes, mean rate below 0.1 Hz, or active fraction below 1% (fail when fewer than 25 active).</p>")
    P.append(table(act[["chip", "well", "well_label", "qc", "qc_reasons", "electrodes_active", "rate_mean_hz",
                        "active_fraction"]], "activity_qc", "QC per well"))

    P.append("<h2>Per-well metrics</h2>")
    key = ["chip", "well", "qc", "electrodes_active", "active_fraction", "total_spikes", "rate_mean_hz",
           "rate_median_hz", "rate_p90_hz", "amplitude_median_uv", "occupied_area_mm2", "clustering_index",
           "isi_cv_median", "burst_fraction_mean", "population_rate_hz", "synchrony_fano", "network_burst_rate_hz",
           "pct_spikes_in_bursts"]
    P.append(table(act[[c for c in key if c in act]], "activity_key_metrics", "Key metrics per well"))
    P.append("<details><summary>All per-well values (every field in summary.json)</summary>"
             + table(act, "activity_all_metrics", "All ActivityScan values") + "</details>")

    panels = [("electrodes_active", "Active electrodes", True), ("active_fraction", "Active fraction", False),
              ("rate_mean_hz", "Mean rate (Hz)", False), ("amplitude_median_uv", "Median amplitude (µV)", False),
              ("occupied_area_mm2", "Occupied area (mm²)", False), ("clustering_index", "Clustering index", False),
              ("isi_cv_median", "Median ISI CV", False), ("burst_fraction_mean", "Burst fraction", False),
              ("population_rate_hz", "Population rate (Hz)", False), ("synchrony_fano", "Synchrony (Fano)", False),
              ("network_burst_rate_hz", "Block burst rate (Hz)", False), ("pct_spikes_in_bursts", "% spikes in bursts", False)]
    panels = [p for p in panels if p[0] in act]
    act["_qc_not_pass"] = act["qc"] != "pass"
    fig, axes = plt.subplots(3, 4, figsize=(13, 9))
    for ax, (c, lab, lg) in zip(axes.flat, panels):
        strip_by_chip(ax, act, c, COL, "_qc_not_pass", lab, log=lg)
        ax.set_title(lab)
    for ax in list(axes.flat)[len(panels):]:
        ax.axis("off")
    fig.suptitle("Per-well ActivityScan metrics by chip — hollow = QC warn/fail", y=1.01)
    fig.tight_layout()
    P.append("<h2>Comparison across chips</h2><p>Descriptive only (no groups entered; 2–5 wells per chip).</p>"
             + img(fig, "activity by chip"))

    corr = {"electrodes_active": "Active el.", "rate_mean_hz": "Mean rate", "amplitude_median_uv": "Amplitude",
            "occupied_area_mm2": "Area", "clustering_index": "Clustering", "isi_cv_median": "ISI CV",
            "burst_fraction_mean": "Burst frac.", "population_rate_hz": "Pop. rate",
            "synchrony_fano": "Fano", "network_burst_rate_hz": "Burst rate", "pct_spikes_in_bursts": "% in bursts"}
    fig, rho = spearman_heatmap(act, {k: v for k, v in corr.items() if k in act},
                                f"Spearman correlation between per-well ActivityScan metrics (n = {len(act)} wells)")
    rho.to_csv(TABLES / "activity_metric_correlations.csv")
    P.append("<h3>How the metrics relate</h3>" + img(fig, "activity correlation"))

    if len(elec):
        active = elec[elec["rate_hz"] >= act_thr]
        P.append(f"<h2>Electrodes</h2><p>From per_electrode.csv: {len(elec):,} electrodes scanned, "
                 f"{len(active):,} active (≥ {act_thr} Hz).</p>")
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
        for (c, wid), g in active.groupby(["chip", "well_id"]):
            x = np.sort(g["rate_hz"].values)
            axes[0].plot(x, np.arange(1, len(x) + 1) / len(x), color=COL[c], lw=1, alpha=0.8)
            a = np.sort(g["mean_amplitude_uv"].dropna().values)
            if len(a):
                axes[1].plot(a, np.arange(1, len(a) + 1) / len(a), color=COL[c], lw=1, alpha=0.8)
        axes[0].set_xscale("log"); axes[0].set_xlabel("Firing rate (Hz)")
        axes[0].set_ylabel("Cumulative fraction"); axes[0].set_title("Rate of active electrodes, per well")
        axes[1].set_xlabel("Mean amplitude (µV)"); axes[1].set_title("Amplitude of active electrodes, per well")
        hb = axes[2].hexbin(np.log10(active["rate_hz"]), active["mean_amplitude_uv"], gridsize=40,
                            cmap="Greys", bins="log", mincnt=1)
        axes[2].set_xlabel("log10 rate (Hz)"); axes[2].set_ylabel("Amplitude (µV)")
        axes[2].set_title("Rate vs amplitude, all active electrodes"); axes[2].grid(False)
        fig.colorbar(hb, ax=axes[2], label="electrodes")
        handles = [plt.Line2D([], [], color=COL[c], label=c) for c in sorted(active["chip"].unique())]
        axes[0].legend(handles=handles)
        fig.tight_layout()
        P.append(img(fig, "electrode distributions"))

        wells = act[["chip", "well_id", "well"]].values.tolist()
        ncol = 6
        nrow = math.ceil(len(wells) / ncol)
        fig, axes = plt.subplots(nrow, ncol, figsize=(13, 1.35 * nrow + 0.6))
        vmax = np.log10(max(active["rate_hz"].quantile(0.99), act_thr * 10))
        for ax, (c, wid, wl) in zip(axes.flat, wells):
            g = elec[(elec["chip"] == c) & (elec["well_id"] == wid)]
            a = g[g["rate_hz"] >= act_thr]
            ax.scatter(g["x_um"], g["y_um"], s=0.2, color="#f3f4f6", rasterized=True)
            sc = ax.scatter(a["x_um"], a["y_um"], c=np.log10(a["rate_hz"]), s=1.5, cmap="magma_r",
                            vmin=np.log10(act_thr), vmax=vmax, rasterized=True)
            ax.set_title(f"{c} {wl}", fontsize=7, pad=2)
            ax.set_aspect("equal"); ax.axis("off"); ax.invert_yaxis()
        for ax in list(axes.flat)[len(wells):]:
            ax.axis("off")
        fig.colorbar(sc, ax=axes, shrink=0.6, label="log10 rate (Hz)")
        fig.suptitle("Where the activity is — active electrodes on the full array, common colour scale")
        P.append("<h3>Activity maps</h3>" + img(fig, "activity maps"))

        per_well_e = active.groupby(["chip", "well_id"]).agg(
            active=("electrode", "count"), rate_median_hz=("rate_hz", "median"),
            rate_max_hz=("rate_hz", "max"), amp_median_uv=("mean_amplitude_uv", "median"),
            amp_max_uv=("mean_amplitude_uv", "max")).reset_index()
        P.append(table(per_well_e, "activity_electrode_summary", "Active-electrode statistics per well"))

    sv = act[act["selection_valid"]]
    if len(sv) and "selection_efficiency" in sv:
        P.append("<h2>Network electrode selection</h2><p>How well the ~1,020 electrodes chosen for each chip's Network "
                 "recording cover the activity this scan found across the whole array. Enrichment = selected mean "
                 "rate ÷ array mean rate; captured = share of all scanned spikes on selected electrodes; recall and "
                 "efficiency compare with taking the busiest electrodes (quality: good ≥ 0.8, fair ≥ 0.5 "
                 "efficiency). Each scan is compared with the Network recording on its own chip:</p>")
        src_tbl = pd.DataFrame([{"chip": c, "network_recording": SEL_SOURCE[c]} for c in sorted(SEL_SOURCE)
                                if SEL_VALID.get(c)])
        P.append(table(src_tbl, "activity_selection_sources", "Network recording used per chip"))
        sel = ["chip", "well", "selected_electrodes", "selected_active_fraction", "selected_rate_mean_hz",
               "selection_enrichment", "captured_activity_fraction", "selection_recall", "selection_efficiency",
               "selection_quality"]
        P.append(table(sv[[c for c in sel if c in sv]], "activity_selection", "Selection quality per well"))
        fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
        for ax, (c, lab, lg) in zip(axes, (("selection_enrichment", "Enrichment (×)", True),
                                           ("captured_activity_fraction", "Captured activity fraction", False),
                                           ("selection_recall", "Selection recall", False),
                                           ("selection_efficiency", "Selection efficiency", False))):
            strip_by_chip(ax, sv, c, COL, "_qc_not_pass", lab, log=lg); ax.set_title(lab)
        fig.suptitle("Electrode selection by chip — hollow = scan QC warn/fail", y=1.03)
        fig.tight_layout()
        P.append(img(fig, "selection quality"))

    # Cross-assay
    m = act.merge(net, on=["chip", "well"], suffixes=("_scan", "_net"))
    if len(m):
        P.append(f"<h2>Activity scan vs Network recording</h2><p>The same {len(m)} wells, matched by chip and well. "
                 "The scan covers the whole array in ~30 s blocks; the Network recording covers the selected "
                 "electrodes simultaneously for ~10 minutes, so absolute values differ by design. Spearman ρ, "
                 "n = wells; the burst comparison uses only wells with usable burst metrics.</p>")
        pairs = [("electrodes_active", "spiking_channels", "Active electrodes (scan)", "Spiking channels (network)", False),
                 ("rate_median_hz", "fr_median_hz", "Median rate, scan (Hz)", "Median channel rate, network (Hz)", False),
                 ("network_burst_rate_hz", "nb_rate_per_min", "Block burst rate, scan (Hz)", "Network bursts / min", True),
                 ("captured_activity_fraction", "spiking_channels", "Captured activity fraction (scan)",
                  "Spiking channels (network)", False)]
        pairs = [p for p in pairs if p[0] in m and p[1] in m]
        fig, axes = plt.subplots(1, len(pairs), figsize=(14, 3.8))
        rows = []
        for ax, (a, b, la, lb, bursts) in zip(np.atleast_1d(axes), pairs):
            mm = m[~m["burst_flag"]] if bursts else m
            if a == "captured_activity_fraction":
                mm = mm[mm["selection_valid"]]
            for c in sorted(mm["chip"].unique()):
                g = mm[mm["chip"] == c]
                ax.scatter(g[a], g[b], s=26, color=COL[c], label=c)
            ok = mm[[a, b]].dropna()
            r = spearmanr(ok[a], ok[b]) if len(ok) >= 5 else None
            ax.set_xlabel(la); ax.set_ylabel(lb)
            if a in ("rate_median_hz",):
                ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_title((f"ρ = {r.statistic:.2f}, p = {r.pvalue:.2g}, n = {len(ok)}" if r else f"n = {len(ok)}")
                         + (" (usable burst wells)" if bursts else ""))
            rows.append({"scan_metric": a, "network_metric": b, "wells": "usable burst wells" if bursts else "all",
                         "n_wells": len(ok), "spearman_rho": r.statistic if r else np.nan,
                         "p_value": r.pvalue if r else np.nan})
        np.atleast_1d(axes)[0].legend()
        fig.tight_layout()
        P.append(img(fig, "cross assay"))
        P.append(table(pd.DataFrame(rows), "cross_assay_correlations", "Scan vs Network, per-well Spearman correlations"))

    P.append("<h2>Activity-scan figures</h2><p>Figures written by the activity scan: plate overviews, then per-well "
             "activity, network and functional maps.</p><div class='gal'>")
    for r in sorted(MANIFEST["activity_runs"], key=lambda x: x["chip_id"]):
        d = Path(r["summary"]).parent
        pngs = sorted(d.glob("*.png"))
        if not pngs:
            continue
        inner = "".join(f"<p class='cap'>{p.name}</p>{file_img(p, p.name, 'activity')}" for p in pngs)
        P.append(f"<details><summary>{r['chip_id']} · run {r['run_id']} · {len(pngs)} figures</summary>{inner}</details>")
    P.append("</div>")

    P.append("<h2>Methods</h2><ul>"
             "<li>Orchestration-MEA ActivityScan v1.0: on-chip threshold-crossing spikes read from the "
             "ActivityScan recording; each electrode recorded in one ~30 s block.</li>"
             f"<li>Active electrode: mean rate ≥ {act_thr} Hz. Bursts, synchrony and correlations are computed "
             "within a block only (electrodes in different blocks were never recorded together).</li>"
             "<li>Report-side: per-well summaries from per_electrode.csv over active electrodes; Spearman "
             "correlations across wells (n = wells); no hypothesis tests between chips.</li></ul>")
    return "\n".join(P)


# --------------------------------------------------------------------------- #
# Assemble
# --------------------------------------------------------------------------- #
def sources_html(kind: str) -> str:
    files = sorted(SOURCES[kind])
    roots = sorted({str(Path(f).parent) for f in files})
    return (f"<h2>Data sources</h2><p>{len(files)} files read, in {len(roots)} folders. Full list:</p>"
            f"<details><summary>Show files</summary><pre>{html.escape(chr(10).join(files))}</pre></details>")


NONE = ("<h2>No {k} results</h2><p>This recording folder has no {k} results in MANIFEST.json "
        "(no recording of that type was made, or its analysis produced no output).</p>")
net_html = (network_page() + sources_html("network")) if len(net) else NONE.format(k="Network")
act_html = (activity_page() + sources_html("activity")) if len(act) else NONE.format(k="ActivityScan")

CSS = """
:root{--ink:#111827;--ink2:#4b5563;--line:#e5e7eb;--bg:#f9fafb;--card:#fff;--acc:#2563eb}
*{box-sizing:border-box}body{margin:0;font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
color:var(--ink);background:var(--bg)}
header{background:var(--card);border-bottom:1px solid var(--line);padding:18px 24px 0;position:sticky;top:0;z-index:5}
h1{font-size:20px;margin:0 0 4px}.meta{color:var(--ink2);font-size:13px;margin-bottom:12px}
nav{display:flex;gap:4px}nav button{border:0;background:none;padding:10px 16px;font:600 14px system-ui;
color:var(--ink2);border-bottom:3px solid transparent;cursor:pointer}
nav button.on{color:var(--acc);border-bottom-color:var(--acc)}
main{max-width:1180px;margin:0 auto;padding:8px 24px 60px}section[hidden]{display:none}
h2{font-size:17px;margin:34px 0 10px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:14px;margin:22px 0 8px}
ul.sum{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 18px 14px 34px}
ul.sum li{margin:4px 0}.note{color:var(--ink2);font-size:12px}
.warn{background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:10px 14px}
.fig{max-width:100%;display:block;margin:10px 0;background:#fff;border-radius:6px}
.tw{overflow-x:auto;margin:10px 0;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;font-size:12px;width:100%}caption{text-align:left;padding:8px 10px;font-weight:600}
.csv{font-weight:400;color:var(--ink2);font-size:11px;margin-left:8px}
th,td{padding:5px 9px;border-top:1px solid var(--line);white-space:nowrap;text-align:left}
th{background:#f3f4f6;cursor:pointer;position:sticky;top:0;user-select:none}th:hover{background:#e5e7eb}
td.n{text-align:right;font-variant-numeric:tabular-nums}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:8px 0;padding:8px 12px}
summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;font-size:11px;color:var(--ink2)}
.cap{font-size:12px;color:var(--ink2);margin:14px 0 0}code{background:#f3f4f6;padding:1px 4px;border-radius:3px}
"""
JS = """
function show(id){document.querySelectorAll('main>section').forEach(s=>s.hidden=s.id!=='page-'+id);
document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===id));
history.replaceState(null,'','#'+id);window.scrollTo(0,0);}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.t));
show(location.hash==='#activity'?'activity':'network');
document.querySelectorAll('table.sortable th').forEach((th,i)=>th.onclick=()=>{
const tb=th.closest('table').tBodies[0],rows=[...tb.rows],asc=th.dataset.s!=='a';
th.closest('tr').querySelectorAll('th').forEach(x=>delete x.dataset.s);th.dataset.s=asc?'a':'d';
rows.sort((a,b)=>{const x=a.cells[i],y=b.cells[i],xv=x.dataset.v,yv=y.dataset.v;
let r=(xv!==undefined&&yv!==undefined)?(+xv-+yv):x.textContent.localeCompare(y.textContent,undefined,{numeric:true});
return asc?r:-r;});rows.forEach(r=>tb.appendChild(r));});
"""

title = f"MEA report — {project} · {rec_date}"
doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body>
<header><h1>{html.escape(title)}</h1>
<div class="meta">{len(net)} Network wells · {len(act)} ActivityScan wells · {len(all_chips)} chips ·
{f'{div} days in vitro · ' if div is not None else ''}spike detection only (no sorting) ·
generated {datetime.now():%Y-%m-%d %H:%M} from {html.escape(str(HANDOFF))}</div>
<nav><button data-t="network">Network analysis</button><button data-t="activity">Activity scan</button></nav></header>
<main><section id="page-network">{net_html}</section><section id="page-activity" hidden>{act_html}</section></main>
<script>{JS}</script></body></html>"""
out = HERE / "report.html"
out.write_text(doc)
print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB), {len(list(TABLES.glob('*.csv')))} tables")
