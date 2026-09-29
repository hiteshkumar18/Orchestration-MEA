"""The Orchestrator data-flow diagram, as data.

One layout drives every output — the SVG, the PNG inside the Word document,
and the native Word shapes — so the three can never drift apart.

Coordinates are in points (1/72"), origin top-left, sized for a landscape
A4/Letter page with margins.
"""

W, H = 980, 690

INK        = "#1F2328"
MUTED      = "#6B7684"
LINE       = "#C8D0D8"
GREEN      = "#2F6F52"   # the orchestrator's own components
GREEN_BG   = "#E6F0EA"
GREEN_LINE = "#CFE3D8"
GREY_BG    = "#F4F6F8"
BLUE       = "#2C5F8A"   # existing lab infrastructure
BLUE_BG    = "#E8F0F7"
BLUE_LINE  = "#CBDDEB"
AMBER      = "#8A5A00"
AMBER_BG   = "#FBF3E4"
AMBER_LINE = "#EBDCBE"

# ── Zones: the machines the work happens on ───────────────────────────────
ZONES = [
    dict(id="instr", x=24,  y=92,  w=190, h=238, label="INSTRUMENTS",
         note="Ben-Shalom Lab"),
    dict(id="nas",   x=242, y=92,  w=176, h=238, label="STORAGE",
         note="ben-shalom_nas.local"),
    dict(id="tower", x=446, y=92,  w=346, h=448, label="ANALYSIS TOWER",
         note="benshalom-labtower1 · RTX 5090"),
    dict(id="out",   x=820, y=92,  w=136, h=392, label="OUTPUTS",
         note="analysis disk"),
    dict(id="ext",   x=820, y=508, w=136, h=124, label="EXTERNAL",
         note="outside the lab"),
]

# ── Boxes ─────────────────────────────────────────────────────────────────
# kind: "infra" (existing), "orch" (what we built), "ext" (outside the lab)
BOXES = [
    dict(id="maxtwo",  x=44,  y=132, w=150, h=44, kind="infra",
         title="MaxTwo", sub="24-well HD-MEA"),
    dict(id="maxone",  x=44,  y=190, w=150, h=44, kind="infra",
         title="MaxOne (irc)", sub="single-well"),
    dict(id="reccomp", x=44,  y=256, w=150, h=52, kind="infra",
         title="Recording computers", sub="write raw HDF5"),

    dict(id="nasbox",  x=262, y=150, w=136, h=66, kind="infra",
         title="Ben-Shalom NAS", sub="raw_data/…\nread-only to us"),
    dict(id="naspath", x=262, y=238, w=136, h=62, kind="note",
         title="<date>/<chip>/", sub="Network/ · ActivityScan/\n<run>/data.raw.h5"),

    dict(id="watcher", x=470, y=134, w=298, h=58, kind="orch",
         title="Watcher", sub="polls for finished recordings · settle window + MaxWell marker"),
    dict(id="queue",   x=470, y=212, w=298, h=54, kind="orch",
         title="Queue", sub="1 Network job at a time (GPU) · 2 activity scans"),
    dict(id="driver",  x=626, y=288, w=142, h=72, kind="infra",
         title="MEA-Analysis", sub="run_pipeline_driver\n→ per-well routine\n→ Kilosort4"),
    dict(id="actscan", x=470, y=288, w=142, h=72, kind="orch",
         title="Activity scan", sub="whole-array\ncoverage\nCPU only"),
    dict(id="reports", x=470, y=390, w=298, h=54, kind="orch",
         title="Report builder", sub="one report per session folder · HTML + PowerPoint"),
    dict(id="ui",      x=470, y=466, w=298, h=54, kind="orch",
         title="Control UI", sub="browser over an SSH tunnel · 127.0.0.1 only"),

    dict(id="outtree", x=836, y=276, w=104, h=96, kind="note",
         title="Analysed", sub="<project>/\n<date>/<chip>/\n<assay>/<run>/\n<well>/"),
    dict(id="outrep",  x=836, y=380, w=104, h=74, kind="note",
         title="Reports", sub="in each\nsession folder\nHTML · PPTX"),
    dict(id="claude",  x=836, y=548, w=104, h=76, kind="ext",
         title="Claude API", sub="optional\nwritten summary\ncomputed values\nonly"),
]

# ── Arrows: (from, to, label, style) ──────────────────────────────────────
ARROWS = [
    ("maxtwo",  "nasbox",  "",            "solid"),
    ("maxone",  "nasbox",  "",            "solid"),
    ("reccomp", "nasbox",  "copy",        "solid"),
    ("nasbox",  "watcher", "read only",   "solid"),
    ("watcher", "queue",   "",            "solid"),
    ("queue",   "driver",  "",            "solid"),
    ("queue",   "actscan", "",            "solid"),
    ("driver",  "reports", "",            "solid"),
    ("actscan", "reports", "",            "solid"),
    ("driver",  "outtree", "results",     "solid"),
    ("reports", "outrep",  "",            "solid"),
    ("reports", "claude",  "opt-in",      "dashed"),
    ("ui",      "watcher", "controls", "solid"),
]

LEGEND = [
    ("orch",  "Built by the orchestrator"),
    ("infra", "Existing lab infrastructure"),
    ("ext",   "Outside the lab (opt-in)"),
]

TITLE    = "MEA Orchestration — data flow"
SUBTITLE = "From recording to report — the recording drive is only ever read from."

STYLES = {
    "orch":  (GREEN_BG, GREEN_LINE, GREEN),
    "infra": (BLUE_BG,  BLUE_LINE,  BLUE),
    "ext":   (AMBER_BG, AMBER_LINE, AMBER),
    "note":  (GREY_BG,  LINE,       MUTED),
}
BY_ID = {b["id"]: b for b in BOXES}
