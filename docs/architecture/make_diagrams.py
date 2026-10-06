#!/usr/bin/env python3
"""
Generate the pipeline architecture diagrams (SVG) in this folder.

    python docs/architecture/make_diagrams.py
    # PNGs: rendered from the SVGs with headless Chrome (see the bottom of this file)

Two layers:
  architecture-overview.svg  stages and data flow, with / without spike sorting
  architecture-detail.svg    components, files, phases, hardware and storage
"""

from __future__ import annotations

import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "Helvetica, Arial, 'DejaVu Sans', sans-serif"
MONO = "'DejaVu Sans Mono', Menlo, Consolas, monospace"

# Palette: one hue per role, used consistently in both diagrams.
C = {
    "ink": "#111827", "ink2": "#4b5563", "line": "#9ca3af", "bg": "#ffffff",
    "store": ("#f3f4f6", "#6b7280"),      # storage / data
    "orch": ("#eff6ff", "#2563eb"),       # Orchestration-MEA
    "mea": ("#f9fafb", "#374151"),        # MEA-Analysis
    "sort": ("#fff7ed", "#ea580c"),       # with spike sorting (GPU)
    "nosort": ("#ecfdf5", "#059669"),     # without spike sorting (default)
    "scan": ("#f5f3ff", "#7c3aed"),       # activity scan
    "ai": ("#fdf2f8", "#db2777"),         # AI report
    "hw": ("#fefce8", "#ca8a04"),         # hardware
}


class Svg:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.parts = w, h, []
        self.warnings: list[str] = []

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=13, weight=400, color=None, anchor="start", mono=False, italic=False):
        style = ' font-style="italic"' if italic else ""
        self.add(f'<text xml:space="preserve" x="{x}" y="{y}" font-family="{MONO if mono else FONT}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{color or C["ink"]}" text-anchor="{anchor}"'
                 f'{style}>{html.escape(s)}</text>')

    def box(self, x, y, w, h, title, lines=(), role="orch", title_size=15, line_size=12.5,
            dashed=False, sub=None, rx=10, mono_lines=False):
        fill, stroke = C[role]
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="1.6"{dash}/>')
        ty = y + 24
        if title:
            self.text(x + 12, ty, title, size=title_size, weight=700, color=stroke)
            self._fit(title, title_size, w - 24, 0.6)
            ty += 6
        if sub:
            ty += 14
            self.text(x + 12, ty, sub, size=11.5, color=C["ink2"], italic=True)
            self._fit(sub, 11.5, w - 24)
        for ln in lines:
            ty += line_size + 6
            bullet = ln.startswith("• ")
            self.text(x + 12, ty, ln, size=line_size, mono=mono_lines and not bullet)
            self._fit(ln, line_size, w - 24, 0.62 if mono_lines and not bullet else 0.53)
        if ty > y + h - 6:
            self.warnings.append(f"text overflows box '{title}' ({ty:.0f} > {y + h - 6})")

    def _fit(self, s, size, width, k=0.53):
        if len(s) * size * k > width:
            self.warnings.append(f"possibly too wide ({len(s) * size * k:.0f}>{width}): {s!r}")

    def container(self, x, y, w, h, label, role="orch", sub=None):
        fill, stroke = C[role]
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" '
                 f'stroke="{stroke}" stroke-width="1.4" stroke-dasharray="7 5"/>')
        self.add(f'<rect x="{x + 14}" y="{y - 11}" width="{len(label) * 8.6 + 20}" height="22" rx="6" '
                 f'fill="{C["bg"]}"/>')
        self.text(x + 24, y + 5, label, size=14, weight=700, color=stroke)
        if sub:
            self.text(x + w - 14, y + 22, sub, size=11.5, color=C["ink2"], anchor="end", italic=True)

    def arrow(self, pts, color=None, label=None, lx=None, ly=None, dashed=False, width=1.8):
        color = color or C["line"]
        d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
        mid = {"#9ca3af": "a-grey"}.get(color, "a-" + color.strip("#"))
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} '
                 f'marker-end="url(#{mid})"/>')
        self._markers.add((mid, color))
        if label:
            self.text(lx, ly, label, size=getattr(self, "label_size", 11.5), color=C["ink2"], anchor="middle",
                      italic=True)

    _markers: set = set()

    def render(self) -> str:
        defs = "".join(
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>'
            for mid, col in sorted(self._markers))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}"><defs>{defs}</defs>'
                f'<rect width="100%" height="100%" fill="{C["bg"]}"/>' + "".join(self.parts) + "</svg>")


def legend(s: Svg, x, y, items):
    for role, label in items:
        fill, stroke = C[role]
        s.add(f'<rect x="{x}" y="{y - 11}" width="16" height="14" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        s.text(x + 22, y, label, size=12.5, color=C["ink2"])
        x += 22 + len(label) * 7.0 + 26


# --------------------------------------------------------------------------- #
# 1. Overview
# --------------------------------------------------------------------------- #
def overview() -> Svg:
    s = Svg(1820, 1040)
    s.text(40, 46, "MEA analysis pipeline — end to end", size=26, weight=700)
    s.text(40, 72, "From the MaxWell recording to an AI-written report. Network analysis runs with or "
                   "without spike sorting; without is the default.", size=14, color=C["ink2"])

    # Stage headers
    for x, w, t in ((40, 250, "1  Acquire"), (330, 270, "2  Detect & dispatch"), (640, 650, "3  Analyse"),
                    (1330, 210, "4  Results"), (1580, 210, "5  Report")):
        s.text(x, 112, t, size=15, weight=700, color=C["ink2"])
        s.add(f'<line x1="{x}" y1="120" x2="{x + w}" y2="120" stroke="#e5e7eb" stroke-width="2"/>')

    # 1 Acquire
    s.box(40, 150, 250, 112, "MaxWell MaxTwo rig", role="store",
          lines=["High-density MEA", "26,400 electrodes per well", "Network + ActivityScan assays"])
    s.box(40, 320, 250, 220, "Lab NAS — raw data", role="store", sub="read-only, never modified",
          lines=["<project>/<date>/<chip>/", "  Network/<run>/", "    data.raw.h5", "  ActivityScan/<run>/",
                 "    data.raw.h5"], mono_lines=True)
    s.arrow([(165, 262), (165, 316)], color=C["store"][1], label="copied", lx=200, ly=294)

    # 2 Detect & dispatch
    s.container(330, 150, 270, 500, "Orchestration-MEA", role="orch")
    s.box(348, 178, 234, 140, "Watcher", role="orch",
          lines=["Finds finished folders:", "• a recording is present", "• MaxWell 'finished' marker",
                 "• no file changes for 10 min"])
    s.box(348, 340, 206, 86, "Queue (web UI)", role="orch", lines=["Folders chosen by", "hand, one batch"])
    s.box(348, 450, 234, 124, "Dispatcher", role="orch",
          lines=["One job per analysis", "Network: 2 at a time", "Activity scan: 2 at a time",
                 "Fast local SSD as scratch"])
    s.arrow([(290, 430), (318, 430), (318, 248), (346, 248)], color=C["orch"][1])
    # Watcher and Queue are two ways in; both feed the dispatcher.
    s.arrow([(570, 318), (570, 448)], color=C["orch"][1], label="auto", lx=591, ly=388)
    s.arrow([(465, 426), (465, 448)], color=C["orch"][1], label="manual", lx=500, ly=442)
    s.text(465, 610, "Web UI: status, logs, per-well progress,", size=11.5, color=C["ink2"], anchor="middle")
    s.text(465, 626, "requirements for the AI report", size=11.5, color=C["ink2"], anchor="middle")

    # 3 Analyse — Network
    s.container(640, 150, 650, 560, "Network analysis — MEA-Analysis pipeline", role="mea",
                sub="one subprocess per well")
    s.box(660, 182, 610, 80, "Phase 1 · Preprocessing (CPU)", role="mea",
          lines=["Read data.raw.h5 → band-pass filter + common reference →",
                 "uncompressed scratch copy of the well (deleted after)"])
    s.box(660, 300, 296, 330, "A · With spike sorting", role="sort", sub="opt-in — needs the GPU",
          lines=["Kilosort4 spike sorting (GPU)", "   ↓", "Merge split units (optional)", "   ↓",
                 "Analyzer: waveforms, quality", "metrics (single CPU core)", "   ↓",
                 "Curation + network bursts + figures", "", "Units = putative neurons", "≈ 1 hour per well"])
    s.box(974, 300, 296, 330, "B · Without spike sorting", role="nosort", sub="default — no GPU",
          lines=["Threshold spike detection (CPU),", "per channel, 5 × noise level", "   ↓",
                 "Network bursts + raster figures", "", "", "", "", "",
                 "Units = electrode channels", "≈ 1–3 minutes per well"])
    s.arrow([(808, 262), (808, 298)], color=C["sort"][1])
    s.arrow([(1122, 262), (1122, 298)], color=C["nosort"][1])
    s.text(965, 286, "--skip-spikesorting decides the path", size=11.5, color=C["ink2"], anchor="middle",
           italic=True)

    # 3 Analyse — Activity scan
    s.box(640, 740, 650, 150, "Activity scan — Orchestration-MEA (per chip, CPU, seconds)", role="scan",
          lines=["Reads the on-chip spike events of the whole-array scan (no sorting, no GPU)",
                 "→ activity maps, firing rates and amplitudes, QC verdict, bursts, synchrony",
                 "→ how well the Network recording's electrode selection covers the activity",
                 "   (compared with the same chip's Network recording)"])

    # dispatcher → analyses
    s.arrow([(582, 500), (620, 500), (620, 222), (658, 222)], color=C["orch"][1])
    s.arrow([(582, 540), (620, 540), (620, 815), (638, 815)], color=C["orch"][1])
    # NAS → analyses (data read)
    s.arrow([(165, 540), (165, 940), (965, 940), (965, 892)], color=C["store"][1], dashed=True,
            label="recordings read directly from the NAS (read-only)", lx=560, ly=932)

    # 4 Results
    s.box(1330, 182, 210, 270, "Network results", role="store", sub="per well",
          lines=["network_results.json", "unit_stats.csv", "spike_times.npy", "raster plots",
                 "checkpoints", "", "+ with sorting:", "quality metrics,", "waveforms"])
    s.box(1330, 486, 210, 104, "Per-well status", role="orch",
          lines=["Read from checkpoints;", "shown live in the UI"])
    s.box(1330, 740, 210, 150, "Scan results", role="store", sub="per chip",
          lines=["summary.json", "per_electrode.csv", "maps + QC figures"])
    s.arrow([(808, 630), (808, 680), (1312, 680), (1312, 300), (1328, 300)], color=C["sort"][1])
    s.arrow([(1122, 630), (1122, 660), (1300, 660), (1300, 340), (1328, 340)], color=C["nosort"][1])
    s.arrow([(1290, 815), (1328, 815)], color=C["scan"][1])
    s.arrow([(1435, 452), (1435, 484)], color=C["orch"][1])
    s.text(1435, 920, "spike_detection/<project>/", size=12, color=C["ink2"], anchor="middle", mono=True)
    s.text(1435, 938, "on the output disk", size=11.5, color=C["ink2"], anchor="middle")

    # 5 Report
    s.box(1580, 182, 210, 210, "AI handoff folder", role="ai", sub="one per date",
          lines=["PROMPT.md", "skills.md — rules and", "  what each metric means", "REQUIREMENTS.md — from UI",
                 "MANIFEST.json — files"])
    s.box(1580, 430, 210, 100, "Claude Code", role="ai",
          lines=["Reads the handoff and", "results; never edits data"])
    s.box(1580, 570, 210, 130, "report.html", role="ai",
          lines=["Tab 1: Network analysis", "Tab 2: Activity scan", "+ every table as CSV"])
    s.arrow([(1540, 300), (1578, 300)], color=C["ai"][1])
    s.arrow([(1540, 800), (1560, 800), (1560, 340), (1578, 340)], color=C["ai"][1])
    s.arrow([(1685, 392), (1685, 428)], color=C["ai"][1])
    s.arrow([(1685, 530), (1685, 568)], color=C["ai"][1])

    legend(s, 40, 1000, [("store", "data / storage"), ("orch", "Orchestration-MEA"), ("mea", "MEA-Analysis"),
                         ("sort", "with spike sorting"), ("nosort", "without spike sorting (default)"),
                         ("scan", "activity scan"), ("ai", "AI report")])
    return s


# --------------------------------------------------------------------------- #
# 2. Detail
# --------------------------------------------------------------------------- #
def detail() -> Svg:
    s = Svg(1820, 1300)
    s.text(40, 46, "MEA analysis pipeline — components, files and hardware", size=26, weight=700)
    s.text(40, 72, "benshalom-labtower1. Orchestration-MEA drives MEA-Analysis as a subprocess and never "
                   "modifies it; raw data is never written to.", size=14, color=C["ink2"])

    # Your computer
    s.container(40, 120, 250, 250, "Your computer", role="store")
    s.box(58, 150, 214, 110, "Browser", role="orch",
          lines=["Web UI (app.js + React,", "served locally)", "polls status every 2 s"])
    s.box(58, 280, 214, 72, "SSH tunnel", role="store", lines=["localhost:8000 → server"])

    # Orchestration-MEA server
    s.container(330, 120, 1010, 560, "Orchestration-MEA  (tmux session 'mea', port 8000)", role="orch")
    s.box(350, 150, 300, 250, "api.py — FastAPI", role="orch",
          lines=["/api/status     jobs + counts", "/api/queue      queue folders", "/api/config     settings",
                 "/api/runs/checkpoints", "/api/handoff    AI handoff", "/api/requirements",
                 "/api/watcher/stop?cancel"], mono_lines=True)
    s.box(670, 150, 330, 250, "watcher.py — scheduler", role="orch",
          lines=["• cached, depth-limited folder scan", "• completion: recording + marker +",
                 "  10 min without changes", "• state: watcher_state.json",
                 "• slots: Network 2 · Activity 2", "• GPU check — sorting only",
                 "• watchdog: stop after 120 min", "  with no log output",
                 "• Stop & cancel kills whole", "  process groups"])
    s.box(1020, 150, 300, 250, "Local staging", role="hw", sub="scratch on the NVMe SSD",
          lines=["/home/s-user-b/mea_scratch/", "  <project>/<date>/", "• job writes its scratch here",
                 "• results copied to output disk", "• scratch deleted after the job",
                 "• ≥ 200 GB always kept free;", "  otherwise runs on output disk"])
    s.box(350, 420, 300, 120, "checkpoints.py", role="orch",
          lines=["Per-well truth from the", "pipeline's checkpoint files:", "complete / failed / running"])
    s.box(670, 420, 330, 120, "activity_scan.py", role="scan",
          lines=["Whole-array scan → maps, QC,", "bursts, synchrony; selection vs", "same-chip Network recording"])
    s.box(1020, 420, 300, 120, "handoff.py", role="ai",
          lines=["Writes AI_HANDOFF/<stamp>_<date>/", "PROMPT · skills.md ·", "REQUIREMENTS · MANIFEST"])
    s.box(350, 560, 970, 100, "Config + rules", role="orch",
          lines=["job.json: input folder, output folder, skip_spikesorting = true (default), staging, concurrency, "
                 "AI requirements text",
                 "Refuses any output / scratch / checkpoint folder inside the input folder — the raw data is read-only"])
    s.arrow([(272, 205), (348, 205)], color=C["orch"][1])
    s.arrow([(650, 275), (668, 275)], color=C["orch"][1])
    s.arrow([(1000, 275), (1018, 275)], color=C["hw"][1])

    # MEA-Analysis
    s.container(330, 720, 1010, 440, "MEA-Analysis  (separate repository, never modified)", role="mea")
    s.box(350, 750, 300, 100, "run_pipeline_driver.py", role="mea",
          lines=["Finds every recording × well", "in a date folder; one", "subprocess per well"])
    s.box(670, 750, 650, 100, "mea_analysis_routine.py — one well", role="mea",
          lines=["Phase 1 · Preprocessing: read .h5 (MaxWell plugin) → filter + common reference →",
                 "float32 binary scratch copy; 16 CPU workers. Checkpoint saved after each stage."])
    s.box(670, 870, 318, 270, "A · With spike sorting", role="sort",
          lines=["Phase 2 · Kilosort4 — GPU", "Merge · UnitMatch (optional)", "Phase 3 · Analyzer — waveforms,",
                 "  quality metrics (1 CPU core)", "Phase 4 · curation, bursts,", "  figures, PDFs",
                 "", "Measured: ≈ 56 min per well", "(46 % sorting, 37 % analyzer)"])
    s.box(1002, 870, 318, 270, "B · Without spike sorting", role="nosort", sub="--skip-spikesorting (default)",
          lines=["Phase 2-Alt · detect_peaks,", "  by channel, 5 × MAD noise", "Burst analysis + rasters",
                 "", "No GPU · no waveforms", "", "Measured: ≈ 1–3 min per well;", "time is mostly Phase 1",
                 "(disk-bound → SSD scratch)"])
    s.box(350, 870, 300, 270, "Outputs per well", role="store",
          lines=["network_results.json", "unit_stats.csv", "spike_times.npy", "processing_info.json",
                 "raster_burst_plot*.png", "checkpoints/", "+ sorted only: qm_*.csv,", "waveforms, analyzer_output/",
                 "", "→ written to the output disk", "   (via SSD scratch)"])
    s.arrow([(650, 800), (668, 800)], color=C["mea"][1])
    s.arrow([(828, 850), (828, 868)], color=C["sort"][1])
    s.arrow([(1160, 850), (1160, 868)], color=C["nosort"][1])
    s.arrow([(670, 1005), (652, 1005)], color=C["sort"][1])
    s.arrow([(1160, 1140), (1160, 1152), (500, 1152), (500, 1142)], color=C["nosort"][1])
    s.arrow([(835, 400), (835, 420)], color=C["orch"][1])
    s.arrow([(690, 400), (690, 410), (340, 410), (340, 800), (348, 800)], color=C["orch"][1])
    s.text(346, 700, "launches", size=11.5, color=C["ink2"], italic=True)

    # Storage + hardware
    s.container(1380, 120, 400, 1040, "Storage and hardware", role="hw")
    s.box(1400, 150, 360, 150, "Lab NAS (CIFS)", role="store", sub="/mnt/benshalom-nas — read-only",
          lines=["Raw recordings: <project>/<date>/", "<chip>/{Network,ActivityScan}/", "<run>/data.raw.h5"])
    s.box(1400, 320, 360, 150, "NVMe SSD (Samsung 980 PRO)", role="hw", sub="system disk, ~450 GB free",
          lines=["Scratch only: uncompressed copy", "of the well being analysed;", "deleted when the job ends"])
    s.box(1400, 490, 360, 200, "Output disk (HDD, /mnt/Vol20tb2)", role="store",
          sub="hitesh_mea_analysis/spike_detection/",
          lines=["<project>/<date>/…/<well>/  results", "<project>/ActivityScan/   scans",
                 "<project>/orchestration_logs/", "<project>/AI_HANDOFF/     reports"], mono_lines=False)
    s.box(1400, 710, 360, 110, "GPU — RTX 5090, 32 GB", role="hw",
          lines=["Used only by Kilosort4 (path A)", "Idle in the default path"])
    s.box(1400, 840, 360, 110, "CPU — 32 cores, 62 GB RAM", role="hw",
          lines=["Preprocessing (16 workers / well),", "detection, bursts, activity scan"])
    s.box(1400, 970, 360, 170, "AI report", role="ai",
          lines=["Claude Code reads", "AI_HANDOFF/<stamp>_<date>/PROMPT.md", "→ report/report.html",
                 "   (Network tab + Activity tab)", "→ report/tables/*.csv"])
    s.arrow([(1340, 470), (1398, 470), (1398, 1000)], color=C["ai"][1], dashed=True)
    s.arrow([(1398, 230), (1342, 230)], color=C["store"][1], dashed=True, label="read", lx=1370, ly=222)
    s.arrow([(1340, 300), (1398, 380)], color=C["hw"][1], dashed=True)

    s.text(40, 1220, "Data rules: the raw-data folders are never written; other users' folders and processes are "
                     "never touched; SSD scratch exists only while a job runs.", size=13, color=C["ink2"])
    legend(s, 40, 1260, [("store", "data / storage"), ("orch", "Orchestration-MEA"), ("mea", "MEA-Analysis"),
                         ("sort", "with spike sorting"), ("nosort", "without spike sorting (default)"),
                         ("scan", "activity scan"), ("ai", "AI report"), ("hw", "hardware / scratch")])
    return s


# --------------------------------------------------------------------------- #
# 3. Data flow — high level, no explanations (style of the lab's data-flow slide)
# --------------------------------------------------------------------------- #
F = {  # fill, stroke, title colour
    "built": ("#e9f4ec", "#b9dcc4", "#2f6b45"),
    "lab": ("#e8f0f8", "#bfd3e8", "#2b5c8a"),
    "plain": ("#f4f5f7", "#d4d8de", "#4b5563"),
    "ext": ("#fdf3e1", "#efd7a6", "#8a5a00"),
}


def fbox(s: Svg, x, y, w, h, title, lines=(), kind="built", pill=None):
    fill, stroke, tc = F[kind]
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    n = 1 + len(lines) + (1 if pill else 0)
    block = 26 + 21 * len(lines) + (30 if pill else 0)
    ty = y + (h - block) / 2 + 20
    s.text(x + w / 2, ty, title, size=21, weight=700, color=tc, anchor="middle")
    s._fit(title, 21, w - 20, 0.6)
    for ln in lines:
        ty += 22
        s.text(x + w / 2, ty, ln, size=15.5, color="#4b5563", anchor="middle")
        s._fit(ln, 15.5, w - 20, 0.52)
    if pill:
        label, pc = pill
        pw = len(label) * 8.2 + 22
        s.add(f'<rect x="{x + w / 2 - pw / 2}" y="{ty + 12}" width="{pw}" height="24" rx="12" fill="{pc}"/>')
        s.text(x + w / 2, ty + 29, label, size=13, weight=700, color="#ffffff", anchor="middle")


def zone(s: Svg, x, y, w, h, label, sub=""):
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#c9ced6" '
          f'stroke-width="1.4" stroke-dasharray="6 5"/>')
    s.add(f'<text x="{x + 22}" y="{y + 32}" font-family="{FONT}" font-size="15" font-weight="700" '
          f'fill="#4b5563" letter-spacing="2.5">{html.escape(label)}</text>')
    if sub:
        s.text(x + 22, y + 54, sub, size=14, color="#9ca3af")


def dataflow() -> Svg:
    s = Svg(2000, 1240)
    s.label_size = 14.5
    G = "#6b7280"
    s.text(44, 52, "MEA Orchestration — data flow", size=34, weight=700)
    s.text(44, 84, "From recording to report — the recording drive is only ever read from.", size=18, color=G)

    zone(s, 40, 130, 300, 470, "INSTRUMENTS", "Ben-Shalom Lab")
    fbox(s, 66, 205, 248, 80, "MaxTwo", ["multi-well HD-MEA"], "lab")
    fbox(s, 66, 305, 248, 80, "MaxOne", ["single-well HD-MEA"], "lab")
    fbox(s, 66, 420, 248, 90, "Recording PCs", ["write raw HDF5"], "lab")

    zone(s, 380, 130, 300, 470, "STORAGE", "lab NAS")
    fbox(s, 404, 220, 252, 110, "Lab NAS", ["raw data", "read-only to us"], "lab")
    fbox(s, 404, 370, 252, 110, "<date>/<chip>/", ["Network/", "ActivityScan/"], "plain")

    for y in (245, 345, 465):
        s.arrow([(314, y), (360, y), (360, 275), (402, 275)], color=G)
    s.text(360, 500, "copy", size=15, color=G, anchor="middle")

    zone(s, 720, 130, 860, 950, "ANALYSIS TOWER", "benshalom-labtower1 · RTX 5090")
    fbox(s, 750, 200, 800, 80, "Watcher", ["finished recordings"])
    fbox(s, 750, 300, 800, 80, "Queue", ["Network ×2 · Activity scan ×2"])
    s.arrow([(1150, 280), (1150, 298)], color=G)

    # Network analysis
    s.add('<rect x="748" y="410" width="512" height="452" rx="14" fill="#fbfcfd" stroke="#d4d8de"/>')
    s.add(f'<text x="768" y="438" font-family="{FONT}" font-size="13.5" font-weight="700" fill="#2b5c8a" '
          f'letter-spacing="2">NETWORK ANALYSIS</text>')
    fbox(s, 770, 456, 468, 78, "Preprocessing", ["filter · scratch on SSD"], "lab")
    fbox(s, 770, 572, 226, 168, "With spike sort", ["Kilosort4", "analyzer · curation"], "lab",
         pill=("GPU", "#ea580c"))
    fbox(s, 1012, 572, 226, 168, "Without spike sort", ["threshold detection"], "lab",
         pill=("CPU · default", "#059669"))
    fbox(s, 770, 772, 468, 72, "Network bursts", ["per well"], "lab")
    s.arrow([(883, 534), (883, 570)], color="#ea580c")
    s.arrow([(1125, 534), (1125, 570)], color="#059669")
    s.arrow([(883, 740), (883, 770)], color="#ea580c")
    s.arrow([(1125, 740), (1125, 770)], color="#059669")

    # Activity scan
    s.add('<rect x="1280" y="410" width="272" height="452" rx="14" fill="#fbfcfd" stroke="#d4d8de"/>')
    s.add(f'<text x="1300" y="438" font-family="{FONT}" font-size="13.5" font-weight="700" fill="#2f6b45" '
          f'letter-spacing="2">ACTIVITY SCAN</text>')
    fbox(s, 1300, 456, 232, 78, "On-chip spikes", ["whole array"])
    fbox(s, 1300, 572, 232, 168, "Maps · QC", ["rates · amplitudes", "bursts · synchrony"],
         pill=("CPU", "#059669"))
    fbox(s, 1300, 772, 232, 72, "Selection check", ["vs Network"])
    s.arrow([(1416, 534), (1416, 570)], color=G)
    s.arrow([(1416, 740), (1416, 770)], color=G)

    s.arrow([(1004, 380), (1004, 454)], color=G)
    s.arrow([(1490, 380), (1490, 454)], color=G)

    fbox(s, 750, 920, 800, 80, "Control UI", ["browser · SSH tunnel"])
    # NAS → watcher (read only); UI controls the tower
    s.arrow([(656, 275), (700, 275), (700, 225), (748, 225)], color=G, label="read only", lx=690, ly=208)
    s.arrow([(750, 960), (736, 960), (736, 262), (748, 262)], color=G)
    s.add(f'<text x="728" y="640" font-family="{FONT}" font-size="15" fill="{G}" text-anchor="middle" '
          f'transform="rotate(-90 728 640)">controls</text>')

    zone(s, 1620, 130, 340, 700, "OUTPUTS", "analysis disk")
    fbox(s, 1648, 470, 284, 130, "Results", ["<project>/<date>/", "<chip>/…/<well>/"], "plain")
    fbox(s, 1648, 650, 284, 110, "AI handoff", ["skills.md · requirements"])
    s.arrow([(1004, 844), (1004, 880), (1600, 880), (1600, 560), (1646, 560)], color=G)
    s.arrow([(1552, 808), (1590, 808), (1590, 520), (1646, 520)], color=G, label="results", lx=1604, ly=500)
    s.arrow([(1790, 600), (1790, 648)], color=G)

    zone(s, 1620, 870, 340, 300, "AI REPORT", "Claude")
    fbox(s, 1648, 940, 284, 80, "Claude Code", ["writes the report"], "ext")
    fbox(s, 1648, 1050, 284, 90, "report.html", ["Network · Activity scan"], "plain")
    s.arrow([(1790, 760), (1790, 938)], color=G, dashed=True)
    s.arrow([(1790, 1020), (1790, 1048)], color=G)

    lx = 44
    for kind, label in (("built", "Built by the orchestrator"), ("lab", "Existing lab infrastructure"),
                        ("ext", "Outside the lab (AI)")):
        fill, stroke, _ = F[kind]
        s.add(f'<rect x="{lx}" y="1190" width="22" height="20" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        s.text(lx + 32, 1206, label, size=17, color="#4b5563")
        lx += 32 + len(label) * 8.8 + 50
    s.text(1956, 1210, "Orchestration-MEA · Ben-Shalom Lab", size=14, color="#9ca3af", anchor="end")
    return s


if __name__ == "__main__":
    for name, fn in (("architecture-overview", overview), ("architecture-detail", detail),
                     ("architecture-dataflow", dataflow)):
        Svg._markers = set()
        svg = fn()
        (HERE / f"{name}.svg").write_text(svg.render())
        print(f"wrote {name}.svg")
        for w in svg.warnings:
            print("  warn:", w)
    # PNG (2x) via headless Chrome:
    #   google-chrome --headless=new --no-sandbox --hide-scrollbars --force-device-scale-factor=2 \
    #     --window-size=W,H --screenshot=out.png file://.../architecture-overview.svg
