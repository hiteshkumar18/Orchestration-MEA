#!/usr/bin/env python3
"""
One chip's recordings drawn the way MaxWell's own software shows them, as a
single HTML page that stands alone (figures embedded).

What is on the page
-------------------
Network Analysis   per well, from the chip's Network recording: the spike
                   raster (channels x time) over the network activity trace.
Active Area        per well, from the ActivityScan: the electrodes that are
                   active by both firing rate and amplitude, black and white.
Results View       per well (a picker chooses the well): mean firing rate,
                   spike amplitude and active electrodes over the whole
                   array, each beside its histogram.

Only the spikes MaxWell already detected while recording are read
(``spikes``: frame, channel, amplitude) with the electrode map; never the raw
traces, so no compression plugin and no GPU. Files are opened read only.

    python orchestration/maxwell_summary.py <date>/<chip> -o page.html

The activity scan (``activity_scan.py``) writes one beside each chip's
results as ``maxwell_summary.html``.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import logging
from pathlib import Path
from typing import Optional

import h5py
import numpy as np

from activity_scan import (_first, block_duration_s, find_chip_network, iter_blocks,
                           read_wellplate)

LOG = logging.getLogger("mea.maxwell_summary")

ROWS, COLS = 120, 220                 # the MaxOne/MaxTwo array: 26,400 electrodes
BLUE = "#1f9bde"                      # MaxWell's plot colour
NETWORK_WINDOW_S = 60.0               # MaxWell's summary shows the first minute
# An electrode is "active" when both hold (MaxWell's activity-scan defaults).
ACTIVE_HZ = 0.1
ACTIVE_UV = 20.0
ISI_MAX_MS = 150.0


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def _uv_per_unit(blk: h5py.Group) -> float:
    lsb = float(_first(blk["settings/lsb"]) or 0) if "settings/lsb" in blk else 0.0
    return lsb * 1e6 if lsb > 0 else 1.0


def _first_frame(blk: h5py.Group, spikes: np.ndarray) -> int:
    if "groups/routed/frame_nos" in blk and blk["groups/routed/frame_nos"].shape[0]:
        return int(blk["groups/routed/frame_nos"][0])
    return int(spikes["frameno"].min()) if spikes.size else 0


def _labels(f: h5py.File) -> dict[int, str]:
    out = {}
    for wid, m in read_wellplate(f).items():
        name = f"Well {m.label}" if m.label else f"Well {wid}"
        out[wid] = name + (f" · {m.group}" if m.group else "")
    return out


def read_network(path: Path, window_s: float = NETWORK_WINDOW_S) -> dict[int, dict]:
    """Per well: spike times and raster rows within the first ``window_s``."""
    wells: dict[int, dict] = {}
    with h5py.File(path, "r") as f:
        labels = _labels(f)
        for wid, blk in iter_blocks(f):
            if wid in wells or "settings/mapping" not in blk:
                continue
            fs = float(_first(blk["settings/sampling"]) or 10000) if "settings/sampling" in blk else 10000.0
            m = blk["settings/mapping"][:]
            sp = blk["spikes"][:]
            dur = block_duration_s(blk) or (float(np.ptp(sp["frameno"])) / fs if sp.size else 0.0)
            span = min(window_s, dur) if dur else window_s
            t = (sp["frameno"].astype(np.int64) - _first_frame(blk, sp)) / fs
            # Raster rows: the recorded channels, in channel order as MaxWell draws them.
            row_of = np.full(int(max(m["channel"].max(), sp["channel"].max() if sp.size else 0)) + 1, -1)
            row_of[np.sort(m["channel"])] = np.arange(m.size)
            ch = sp["channel"].astype(np.int64)
            keep = (t >= 0) & (t < span) & (ch >= 0) & (ch < row_of.size)
            keep &= row_of[np.clip(ch, 0, row_of.size - 1)] >= 0
            wells[wid] = {"label": labels.get(wid, f"Well {wid}"), "t": t[keep],
                          "row": row_of[ch[keep]], "channels": int(m.size), "span": span}
    return wells


def read_scan(path: Path) -> dict[int, dict]:
    """Per well, over all scan blocks: firing rate (Hz), mean |amplitude| (µV)
    and the interspike intervals below ``ISI_MAX_MS`` of every electrode."""
    acc: dict[int, dict] = {}
    with h5py.File(path, "r") as f:
        labels = _labels(f)
        for wid, blk in iter_blocks(f):
            if "settings/mapping" not in blk:
                continue
            a = acc.setdefault(wid, {"label": labels.get(wid, f"Well {wid}"),
                                     "n": np.zeros(ROWS * COLS), "amp": np.zeros(ROWS * COLS),
                                     "secs": np.zeros(ROWS * COLS), "isi": []})
            fs = float(_first(blk["settings/sampling"]) or 10000) if "settings/sampling" in blk else 10000.0
            m = blk["settings/mapping"][:]
            m = m[(m["electrode"] >= 0) & (m["electrode"] < ROWS * COLS)]
            a["secs"][m["electrode"]] += block_duration_s(blk)
            sp = blk["spikes"][:]
            if not sp.size or not m.size:
                continue
            e_of = np.full(int(max(m["channel"].max(), sp["channel"].max())) + 1, -1)
            e_of[m["channel"]] = m["electrode"]
            ch = sp["channel"].astype(np.int64)
            ok = (ch >= 0) & (ch < e_of.size)
            ok[ok] = e_of[ch[ok]] >= 0
            e = e_of[ch[ok]]
            np.add.at(a["n"], e, 1)
            np.add.at(a["amp"], e, np.abs(sp["amplitude"][ok].astype(np.float64)) * _uv_per_unit(blk))
            o = np.lexsort((sp["frameno"][ok], e))
            es, ts = e[o], sp["frameno"][ok][o] / fs * 1000.0
            d = np.diff(ts)[es[1:] == es[:-1]]
            a["isi"].append(d[(d > 0) & (d <= ISI_MAX_MS)])
    out = {}
    for wid, a in acc.items():
        with np.errstate(invalid="ignore", divide="ignore"):
            rate = np.where(a["secs"] > 0, a["n"] / a["secs"], np.nan)
            amp = np.where(a["n"] > 0, a["amp"] / a["n"], np.nan)
        active = (np.nan_to_num(rate) >= ACTIVE_HZ) & (np.nan_to_num(amp) >= ACTIVE_UV)
        out[wid] = {"label": a["label"], "rate": rate, "amp": amp, "active": active,
                    "firing": np.nan_to_num(rate) > 0,
                    "isi": np.concatenate(a["isi"]) if a["isi"] else np.empty(0)}
    return out


# --------------------------------------------------------------------------- #
# Figures, drawn like MaxWell's
# --------------------------------------------------------------------------- #
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.labelsize": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.labelweight": "normal"})
    return plt


def _png(fig) -> str:
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(
        "maxwell", ["#000000", "#0b2b4a", "#2a7ab8", "#a9d3f0", "#ffffff", "#ffb347", "#ff3b1f"])


def network_figure(w: dict) -> str:
    plt = _plt()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(4.6, 3.6), gridspec_kw={"hspace": 0.45})
    n, span = max(w["channels"], 1), w["span"]
    a1.plot(w["t"], w["row"], "|", ms=1.6, mew=0.5, c=BLUE, rasterized=True)
    a1.set_xlim(0, span); a1.set_ylim(0, 1024 if n <= 1024 else n)
    a1.set_yticks([0, 1024 if n <= 1024 else n]); a1.set_xticks([0, span])
    a1.set_xticklabels(["0.0", f"{span:.1f}"]); a1.set_ylabel("Channels")
    # Network activity: spikes per second across the array, smoothed by a
    # Gaussian (σ 100 ms) on 10 ms bins.
    bin_s, sigma = 0.01, 0.1
    edges = np.arange(0, span + bin_s, bin_s)
    counts = np.histogram(w["t"], edges)[0] / bin_s
    k = np.exp(-0.5 * (np.arange(-4 * sigma, 4 * sigma + bin_s, bin_s) / sigma) ** 2)
    act = np.convolve(counts, k / k.sum(), mode="same")
    a2.plot(edges[:-1], act, c=BLUE, lw=1)
    top = float(act.max()) if act.size else 1.0
    a2.set_xlim(0, span); a2.set_ylim(0, top * 1.05 or 1)
    a2.set_yticks([0, round(top)]); a2.set_xticks([0, span]); a2.set_xticklabels(["0.0", f"{span:.1f}"])
    a2.set_ylabel("Network Activity\n(spikes/s)"); a2.set_xlabel("Time [seconds]", fontweight="bold")
    return _png(fig)


def _grid(v: np.ndarray) -> np.ndarray:
    return v.reshape(ROWS, COLS)


def active_area_figure(s: dict) -> str:
    plt = _plt()
    fig = plt.figure(figsize=(4.4, 3.0))
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.68])
    ax.imshow(_grid(s["active"]), cmap="gray", vmin=0, vmax=1, interpolation="nearest", aspect="auto")
    ax.set_xticks([]); ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)
    bar = fig.add_axes([0.08, 0.17, 0.84, 0.06])
    bar.imshow([[0, 1]], cmap="gray", vmin=0, vmax=1, aspect="auto", extent=(0, 1, 0, 1),
               interpolation="nearest")
    bar.set_xticks([]); bar.set_yticks([])
    for side in bar.spines.values():
        side.set_visible(True); side.set_linewidth(0.8)
    fig.text(0.04, 0.20, "0.0", ha="right", va="center"); fig.text(0.96, 0.20, "1.0", ha="left", va="center")
    fig.text(0.5, 0.05, f"Active Area: {100 * s['active'].mean():.2f}%", ha="center", fontweight="bold")
    return _png(fig)


def results_figure(s: dict) -> str:
    plt = _plt()
    from matplotlib.colors import ListedColormap
    fig, ax = plt.subplots(3, 2, figsize=(12, 9.5), gridspec_kw={"width_ratios": [1.45, 1], "hspace": 0.45,
                                                                "wspace": 0.5})
    rate, amp, act = s["rate"], s["amp"], s["active"]

    def vmax(v):
        f = v[np.isfinite(v) & (v > 0)]
        return float(np.percentile(f, 99.5)) if f.size else 1.0

    for i, (title, v, unit) in enumerate((("Mean Firing Rate", rate, "Firing Rate [Hz]"),
                                          ("Spike Amplitude", amp, "Amplitude [µV]"))):
        im = ax[i, 0].imshow(np.nan_to_num(_grid(v)), cmap=_cmap(), vmin=0, vmax=vmax(v),
                             interpolation="nearest", aspect="equal")
        fig.colorbar(im, ax=ax[i, 0], fraction=0.03, pad=0.02).set_label(unit, fontsize=12)
        ax[i, 0].set_title(title, loc="left", fontweight="bold", fontsize=10)
    im = ax[2, 0].imshow(_grid(act), cmap=ListedColormap(["black", BLUE]), vmin=0, vmax=1,
                         interpolation="nearest", aspect="equal")
    cb = fig.colorbar(im, ax=ax[2, 0], fraction=0.03, pad=0.02, ticks=[0, 1])
    cb.set_label("Active State", fontsize=12)
    ax[2, 0].set_title(f"Active Electrodes = {100 * act.mean():.2f} %.", loc="left", fontweight="bold", fontsize=10)
    for a in ax[:, 0]:
        a.set_xticks([]); a.set_yticks([])

    firing = s["firing"]
    hists = ((rate[firing], "Firing Rate [Hz]", "Electrode Count"),
             (amp[firing], "Spike Amplitude [µV]", "Electrode Count"),
             (s["isi"], "Interspike Interval [ms]", "Interval Count"))
    for a, (v, xl, yl) in zip(ax[:, 1], hists):
        v = v[np.isfinite(v)]
        if v.size:
            hi = ISI_MAX_MS if "Interspike" in xl else float(np.percentile(v, 99.5))
            a.hist(v[v <= hi], bins=50, range=(0, hi), color=BLUE)
        a.set_xlabel(xl, fontsize=12); a.set_ylabel(yl, fontsize=12)
    return _png(fig)


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #
def write_page(out: Path, *, scan: Optional[Path], network: Optional[Path], title: str) -> Path:
    """Write the page for one chip. Either recording may be missing; its
    sections are then left out."""
    parts = [f"<h1>{html.escape(title)}</h1>",
             "<p class=sub>Drawn from the spikes MaxWell detected while recording. "
             f"Active electrode: firing rate ≥ {ACTIVE_HZ} Hz and amplitude ≥ {ACTIVE_UV:g} µV. "
             f"Interspike intervals up to {ISI_MAX_MS:g} ms, all electrodes pooled.</p>"]
    if network is not None:
        net = read_network(network)
        parts.append(f"<h2>Network Analysis <small>· run {html.escape(network.parent.name)} · first "
                     f"{NETWORK_WINDOW_S:g} s</small></h2><div class=grid>")
        for wid, w in sorted(net.items()):
            parts.append(f"<figure><figcaption>{html.escape(w['label'])}</figcaption>"
                         f"<img src='{network_figure(w)}' alt='Network analysis, {html.escape(w['label'])}'>"
                         f"<small>{w['channels']} channels · {len(w['t']):,} spikes</small></figure>")
            LOG.info("  network %s: %d spikes in %.0f s", w["label"], len(w["t"]), w["span"])
        parts.append("</div>")
    if scan is not None:
        sc = read_scan(scan)
        parts.append(f"<h2>Active Area <small>· activity scan run {html.escape(scan.parent.name)}</small></h2>"
                     "<div class=grid>")
        for wid, s in sorted(sc.items()):
            parts.append(f"<figure><figcaption>{html.escape(s['label'])}</figcaption>"
                         f"<img src='{active_area_figure(s)}' alt='Active area, {html.escape(s['label'])}'>"
                         f"<small>Active Area: {100 * s['active'].mean():.2f} % · "
                         f"{int(s['active'].sum()):,} of {int(np.isfinite(s['rate']).sum()):,} electrodes</small></figure>")
        parts.append("</div><h2>Results View <select id=well aria-label='Well'>"
                     + "".join(f"<option value='w{wid}'>{html.escape(s['label'])}</option>"
                               for wid, s in sorted(sc.items()))
                     + "</select></h2>")
        for i, (wid, s) in enumerate(sorted(sc.items())):
            parts.append(f"<figure class='res' id='w{wid}'{'' if i == 0 else ' hidden'}>"
                         f"<img src='{results_figure(s)}' alt='Results, {html.escape(s['label'])}'></figure>")
            LOG.info("  scan %s: %.2f %% active", s["label"], 100 * s["active"].mean())
    out.write_text(PAGE.replace("{title}", html.escape(title)).replace("{body}", "\n".join(parts)))
    return out


PAGE = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>{title}</title><style>
body{font:14px "Open Sans",system-ui,sans-serif;margin:20px;background:#f3f3f3;color:#222}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;color:#555;margin:26px 0 10px}h2 small{font-weight:400;color:#888}
.sub{color:#666;margin:0 0 8px;max-width:900px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,400px),1fr));gap:10px}
figure{margin:0;background:#fff;border:1px solid #ccc;padding:8px}figure.res{max-width:1100px}
figcaption{font-weight:600;margin-bottom:4px}small{color:#777}img{width:100%;height:auto;display:block}
select{font:inherit;margin-left:8px}
</style></head><body>{body}
<script>document.getElementById('well')?.addEventListener('change',e=>{
document.querySelectorAll('.res').forEach(f=>f.hidden=f.id!==e.target.value)});</script></body></html>"""


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("chip_dir", type=Path, help="<date folder>/<chip>")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--scan-subfolder", default="ActivityScan")
    p.add_argument("--network-subfolder", default="Network")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    scans = sorted(a.chip_dir.glob(f"{a.scan_subfolder}/*/data.raw.h5"))
    scan = scans[-1] if scans else None
    net = (find_chip_network(scan, a.network_subfolder) if scan else
           next(iter(sorted(a.chip_dir.glob(f"{a.network_subfolder}/*/data.raw.h5"))), None))
    write_page(a.out, scan=scan, network=net,
               title=f"{a.chip_dir.parent.parent.name} · {a.chip_dir.parent.name} · chip {a.chip_dir.name}")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
