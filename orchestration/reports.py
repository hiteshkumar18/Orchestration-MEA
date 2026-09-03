#!/usr/bin/env python3
"""
Generate reports from analysed MEA output.

Four report types, from the same collected data:

  run           one session: unit counts, firing rates, bursts, per-well detail
  condition     wells grouped by genotype/condition, with a group comparison
  qc            what passed, what failed, which units were rejected and why
  longitudinal  the same metrics across sessions / DIV

Two formats:

  html          self-contained, figures inlined as base64 — one file to send
  pptx          slides for a lab meeting

Usage
-----
    python orchestration/reports.py /path/to/AnalyzedData
    python orchestration/reports.py /path/to/AnalyzedData --type condition --format pptx
    python orchestration/reports.py /path/to/AnalyzedData --type qc --format html pptx
    python orchestration/reports.py /path/to/AnalyzedData \
        --activity-dir /path/to/ActivityScan     # adds genotype labels

Notes
-----
* ``python-pptx`` is needed only for slides; HTML has no extra dependency.
* Rasters are SVG, which python-pptx cannot embed — they are converted with
  cairosvg when it is available, and referenced by path when it is not.
* Metric names are matched tolerantly (see ``report_data``), so a column named
  slightly differently still appears.
"""

from __future__ import annotations

import argparse
import base64
import html as html_mod
import io
import logging
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_data import (  # noqa: E402
    PRETTY, Well, assign_div, attach_activity, available_metrics, collect_wells,
    group_wells, summarise,
)

LOG = logging.getLogger("mea.reports")

# Palette: deep midnight with an electrode-teal accent — chosen for recordings
# on a dark array rather than a generic corporate blue.
INK = "171A3A"
INK_SOFT = "3D4166"
ACCENT = "2DD4BF"
ACCENT_2 = "6366F1"
PAPER = "FFFFFF"
MUTED = "8A8FA8"
OK, WARN, BAD = "1D8A4E", "B45309", "C8352B"
SERIES = ["6366F1", "2DD4BF", "F59E0B", "EC4899", "10B981", "8B5CF6"]

REPORT_TITLES = {
    "run": "Run summary",
    "condition": "Condition comparison",
    "qc": "Quality control",
    "longitudinal": "Longitudinal trends",
}


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150, "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#" + INK_SOFT, "text.color": "#" + INK,
        "axes.labelcolor": "#" + INK_SOFT, "xtick.color": "#" + INK_SOFT,
        "ytick.color": "#" + INK_SOFT,
    })
    return plt


def _fig_png(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return buf.getvalue()


def chart_per_well(wells: list[Well], metric: str) -> Optional[bytes]:
    """Bar of one metric per well, coloured by group when groups exist."""
    vals = [(w, w.get(metric)) for w in wells]
    vals = [(w, v) for w, v in vals if v is not None]
    if not vals:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(5, len(vals) * 0.55), 3.0))
    groups = sorted({w.group for w, _ in vals if w.group})
    colour_of = {g: "#" + SERIES[i % len(SERIES)] for i, g in enumerate(groups)}
    labels = [w.well.replace("well", "w") for w, _ in vals]
    ax.bar(range(len(vals)), [v for _, v in vals],
           color=[colour_of.get(w.group, "#" + ACCENT_2) for w, _ in vals], width=.68)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=45 if len(vals) > 10 else 0, ha="right" if len(vals) > 10 else "center")
    ax.set_ylabel(PRETTY.get(metric, metric))
    ax.set_title(PRETTY.get(metric, metric) + " by well")
    if groups:
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(facecolor=colour_of[g], label=g) for g in groups],
                  fontsize=8, frameon=False)
    fig.tight_layout()
    return _fig_png(fig)


def chart_by_group(wells: list[Well], metrics: list[str]) -> Optional[bytes]:
    """Group means with every well drawn individually.

    With a handful of wells per group the spread matters more than the mean, so
    the points are the data and the bar is only context.
    """
    groups = {g: ws for g, ws in group_wells(wells).items() if g != "ungrouped"}
    if len(groups) < 2:
        return None
    metrics = [m for m in metrics if any(w.get(m) is not None for w in wells)][:4]
    if not metrics:
        return None

    plt = _plt()
    names = sorted(groups)
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.2 * len(metrics), 3.2))
    for ax, metric in zip(list(axes) if len(metrics) > 1 else [axes], metrics):
        for i, g in enumerate(names):
            vals = [w.get(metric) for w in groups[g] if w.get(metric) is not None]
            if not vals:
                continue
            c = "#" + SERIES[i % len(SERIES)]
            ax.bar(i, statistics.fmean(vals), .62, color=c, alpha=.30,
                   edgecolor=c, linewidth=1.3)
            xs = [i + o for o in _spread(len(vals))]
            ax.scatter(xs, vals, s=26, color=c, zorder=3,
                       edgecolors="white", linewidths=.7)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, fontsize=8.5)
        ax.set_title(PRETTY.get(metric, metric), fontsize=9.5)
        ax.margins(x=.28)
    fig.tight_layout()
    return _fig_png(fig)


def _spread(n: int) -> list[float]:
    if n == 1:
        return [0.0]
    step = 0.24 / max(n - 1, 1)
    return [-0.12 + i * step for i in range(n)]


def chart_longitudinal(wells: list[Well], metric: str) -> Optional[bytes]:
    """Metric against DIV (or session order), one line per group."""
    pts = [(w, w.div) for w in wells if w.div is not None and w.get(metric) is not None]
    if len({d for _, d in pts}) < 2:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    groups = sorted({w.group for w, _ in pts if w.group}) or [""]
    for i, g in enumerate(groups):
        c = "#" + SERIES[i % len(SERIES)]
        xs = sorted({d for w, d in pts if (w.group or "") == g})
        means = []
        for x in xs:
            v = [w.get(metric) for w, d in pts if d == x and (w.group or "") == g]
            v = [q for q in v if q is not None]
            means.append(statistics.fmean(v) if v else None)
            ax.scatter([x] * len(v), v, s=22, color=c, alpha=.42, linewidths=0)
        ok = [(x, m) for x, m in zip(xs, means) if m is not None]
        if ok:
            ax.plot([x for x, _ in ok], [m for _, m in ok], "-o",
                    color=c, lw=1.8, ms=4.5, label=g or "all")
    ax.set_xlabel("DIV")
    ax.set_ylabel(PRETTY.get(metric, metric))
    ax.set_title(PRETTY.get(metric, metric) + " over time")
    if groups != [""]:
        ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    return _fig_png(fig)


def chart_qc(wells: list[Well]) -> Optional[bytes]:
    """Units kept vs rejected per well — the operational QC picture."""
    rows = [w for w in wells if w.units is not None or w.units_rejected is not None]
    if not rows:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(5, len(rows) * 0.55), 3.0))
    kept = [w.units or 0 for w in rows]
    rej = [w.units_rejected or 0 for w in rows]
    x = range(len(rows))
    ax.bar(x, kept, .68, label="kept", color="#" + ACCENT_2)
    ax.bar(x, rej, .68, bottom=kept, label="rejected", color="#" + BAD, alpha=.75)
    ax.set_xticks(list(x))
    ax.set_xticklabels([w.well.replace("well", "w") for w in rows],
                       rotation=45 if len(rows) > 10 else 0,
                       ha="right" if len(rows) > 10 else "center")
    ax.set_ylabel("Units")
    ax.set_title("Units kept and rejected, by well")
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    return _fig_png(fig)


def svg_to_png(path: Path, width: int = 1400) -> Optional[bytes]:
    """Rasterise an SVG figure. python-pptx cannot embed SVG directly."""
    try:
        import cairosvg
        return cairosvg.svg2png(url=str(path), output_width=width)
    except Exception as exc:  # noqa: BLE001
        LOG.debug("Could not rasterise %s (%s)", path.name, exc)
        return None


def figure_png(well: Well, key: str = "raster") -> Optional[bytes]:
    p = well.figures.get(key)
    if not p:
        return None
    path = Path(p)
    if path.suffix.lower() == ".svg":
        return svg_to_png(path)
    if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
        try:
            return path.read_bytes()
        except OSError:
            return None
    return None


# --------------------------------------------------------------------------- #
# Report content — shared by both renderers
# --------------------------------------------------------------------------- #
def fmt(value: Optional[float], places: int = 2) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1000 or (value == int(value) and abs(value) < 1e6):
        return f"{value:,.0f}"
    return f"{value:,.{places}f}"


def headline_stats(wells: list[Well], summary: dict) -> list[tuple[str, str, str]]:
    """(value, label, note) tiles for the top of a report."""
    metrics = summary["metrics"]
    out: list[tuple[str, str, str]] = [
        (str(summary["wells"]), "Wells analysed",
         ", ".join(summary["chips"][:3]) or ""),
    ]
    if summary["total_units"]:
        per = summary["total_units"] / max(summary["wells"], 1)
        out.append((f"{summary['total_units']:,}", "Units detected",
                    f"{per:.0f} per well"))
    for key in ("firing_rate_hz", "burst_rate_hz", "pct_spikes_in_bursts"):
        if key in metrics:
            vals = [w.get(key) for w in wells]
            vals = [v for v in vals if v is not None]
            if vals:
                out.append((fmt(statistics.fmean(vals)),
                            PRETTY.get(key, key), "mean across wells"))
            break
    done = summary["status"].get("complete", 0)
    failed = summary["status"].get("failed", 0)
    if done or failed:
        out.append((f"{done}/{summary['wells']}", "Wells complete",
                    f"{failed} failed" if failed else "all succeeded"))
    return out[:4]


def group_table(wells: list[Well], metrics: list[str]) -> list[list[str]]:
    groups = {g: ws for g, ws in group_wells(wells).items() if g != "ungrouped"}
    if not groups:
        return []
    head = ["Group", "n"] + [PRETTY.get(m, m) for m in metrics]
    rows = [head]
    for g in sorted(groups):
        row = [g, str(len(groups[g]))]
        for m in metrics:
            v = [w.get(m) for w in groups[g] if w.get(m) is not None]
            row.append(f"{fmt(statistics.fmean(v))} ± {fmt(statistics.pstdev(v)) if len(v) > 1 else '—'}"
                       if v else "—")
        rows.append(row)
    return rows


def well_table(wells: list[Well], metrics: list[str]) -> list[list[str]]:
    head = ["Well", "Group", "Status"] + [PRETTY.get(m, m) for m in metrics]
    rows = [head]
    for w in wells:
        rows.append([w.well, w.group or "—", w.status]
                    + [fmt(w.get(m)) for m in metrics])
    return rows


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
def _b64(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


# --------------------------------------------------------------------------- #
# Narrative (written by a model, from orchestration.narrate)
# --------------------------------------------------------------------------- #
# Every number in this prose has been checked against the briefing before it
# gets here, but a reader still needs to know which words a model wrote. The
# narrative is therefore kept in its own visually distinct block and labelled,
# rather than blended into the measured sections.
AI_LABEL = "Written by Claude from the measured values above"


def _label(metric: str) -> str:
    """Readable name for a metric, tolerating keys outside the PRETTY table."""
    return PRETTY.get(metric) or metric.replace("_", " ").strip().capitalize()


def _narrative_html(narrative: dict, e) -> str:
    if not narrative:
        return ""
    parts: list[str] = []

    head = narrative.get("headline") or ""
    if head:
        parts.append(f'<p class="lede">{e(head)}</p>')

    for f in narrative.get("findings") or []:
        cited = ", ".join(_label(m) for m in (f.get("metrics_cited") or []))
        parts.append(
            f'<div class="finding"><h3>{e(f.get("title", ""))}</h3>'
            f'<p>{e(f.get("text", ""))}</p>'
            + (f'<div class="cited">{e(cited)}</div>' if cited else "")
            + "</div>")

    add = narrative.get("additional")
    if add and add.get("text"):
        parts.append(
            f'<div class="finding extra"><h3>{e(add.get("title", "Also noted"))}</h3>'
            f'<p>{e(add["text"])}</p></div>')

    notes = [q.get("note", "") for q in (narrative.get("qc_notes") or []) if q.get("note")]
    if notes:
        items = "".join(f"<li>{e(n)}</li>" for n in notes)
        parts.append(f'<div class="side"><h4>Data quality</h4><ul>{items}</ul></div>')

    caveats = [c for c in (narrative.get("caveats") or []) if c]
    if caveats:
        items = "".join(f"<li>{e(c)}</li>" for c in caveats)
        parts.append(f'<div class="side"><h4>Caveats</h4><ul>{items}</ul></div>')

    return (f'<section class="ai"><div class="aihead"><h2>Summary</h2>'
            f'<span class="badge">{e(AI_LABEL)}</span></div>'
            f'{"".join(parts)}</section>')


def build_html(wells: list[Well], kind: str, out: Path,
               activity_dir: Optional[Path] = None,
               narrative: Optional[dict] = None) -> Path:
    s = summarise(wells)
    metrics = s["metrics"]
    e = html_mod.escape
    figs: list[tuple[str, bytes]] = []

    if kind == "condition":
        c = chart_by_group(wells, metrics)
        if c:
            figs.append(("Group comparison", c))
    elif kind == "longitudinal":
        for m in metrics[:4]:
            c = chart_longitudinal(wells, m)
            if c:
                figs.append((PRETTY.get(m, m), c))
    elif kind == "qc":
        c = chart_qc(wells)
        if c:
            figs.append(("Units kept and rejected", c))
    else:
        for m in metrics[:3]:
            c = chart_per_well(wells, m)
            if c:
                figs.append((PRETTY.get(m, m), c))

    def table_html(rows: list[list[str]]) -> str:
        if not rows:
            return ""
        head = "".join(f"<th>{e(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                       for r in rows[1:])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    tiles = "".join(
        f'<div class="tile"><div class="v">{e(v)}</div>'
        f'<div class="l">{e(l)}</div><div class="n">{e(n)}</div></div>'
        for v, l, n in headline_stats(wells, s))

    charts = "".join(
        f'<section><h2>{e(t)}</h2><img src="{_b64(p)}" alt="{e(t)}"></section>'
        for t, p in figs)

    extra = ""
    if kind == "qc":
        bad = [w for w in wells if w.status == "failed" or w.error]
        if bad:
            items = "".join(
                f"<li><b>{e(w.well)}</b> — {e((w.error or 'failed')[:300])}</li>"
                for w in bad)
            extra += f'<section><h2>Failures</h2><ul class="fail">{items}</ul></section>'
        reasons: dict[str, int] = {}
        for w in wells:
            for r, n in w.rejection_reasons.items():
                reasons[r] = reasons.get(r, 0) + n
        if reasons:
            rows = [["Reason", "Units"]] + [[k, str(v)] for k, v in
                                            sorted(reasons.items(), key=lambda x: -x[1])]
            extra += f"<section><h2>Why units were rejected</h2>{table_html(rows)}</section>"

    if kind == "condition":
        gt = group_table(wells, metrics)
        if gt:
            extra += f"<section><h2>By group</h2>{table_html(gt)}</section>"

    rasters = ""
    with_raster = [w for w in wells if w.figures.get("raster")][:8]
    if kind in ("run", "qc") and with_raster:
        cards = []
        for w in with_raster:
            png = figure_png(w)
            if png:
                cards.append(f'<figure><img src="{_b64(png)}" alt="raster {e(w.well)}">'
                             f'<figcaption>{e(w.well)}'
                             f'{" · " + e(w.group) if w.group else ""}</figcaption></figure>')
        if cards:
            rasters = f'<section><h2>Rasters</h2><div class="grid">{"".join(cards)}</div></section>'

    scope = " · ".join(x for x in [
        ", ".join(s["chips"][:4]) or "",
        f"{len(s['runs'])} run(s)" if s["runs"] else "",
        ", ".join(s["groups"]) if s["groups"] else "",
    ] if x)

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>MEA {e(REPORT_TITLES.get(kind, kind))}</title><style>
*{{box-sizing:border-box}}
body{{margin:0;background:#F7F8FB;color:#{INK};
 font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 letter-spacing:-.011em}}
.wrap{{max-width:1080px;margin:0 auto;padding:40px 28px 72px}}
header{{background:#{INK};color:#fff;margin:-40px -28px 32px;padding:44px 28px 36px}}
h1{{margin:0;font-size:30px;font-weight:600;letter-spacing:-.025em}}
.sub{{margin-top:8px;font-size:14px;opacity:.75}}
h2{{font-size:18px;font-weight:600;letter-spacing:-.02em;margin:0 0 14px}}
section{{background:#fff;border:1px solid #E6E8F0;border-radius:14px;
 padding:22px 24px;margin-bottom:20px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
 gap:14px;margin-bottom:22px}}
.tile{{background:#fff;border:1px solid #E6E8F0;border-radius:14px;padding:18px 20px}}
.tile .v{{font-size:31px;font-weight:600;letter-spacing:-.03em;line-height:1}}
.tile .l{{font-size:13px;color:#{INK_SOFT};margin-top:7px;font-weight:500}}
.tile .n{{font-size:11.5px;color:#{MUTED};margin-top:2px}}
img{{max-width:100%;height:auto;border-radius:8px;display:block}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th{{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;
 color:#{INK_SOFT};font-weight:600;padding:8px 10px;border-bottom:2px solid #E6E8F0}}
td{{padding:9px 10px;border-bottom:1px solid #F0F2F7;font-variant-numeric:tabular-nums}}
tr:last-child td{{border-bottom:none}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}
figure{{margin:0}}
figcaption{{font-size:12px;color:#{INK_SOFT};margin-top:7px}}
ul.fail{{margin:0;padding-left:20px;font-size:13.5px}}
ul.fail li{{margin-bottom:8px}}
.ai{{border-left:3px solid #{ACCENT}}}
.aihead{{display:flex;align-items:baseline;justify-content:space-between;
 gap:16px;flex-wrap:wrap;margin-bottom:16px}}
.aihead h2{{margin:0}}
.badge{{font-size:11px;color:#{INK_SOFT};background:#F2F4FA;border-radius:999px;
 padding:4px 11px;font-weight:500;white-space:nowrap}}
.lede{{font-size:19px;line-height:1.45;letter-spacing:-.017em;margin:0 0 20px;
 font-weight:500}}
.finding{{margin-bottom:18px}}
.finding h3{{font-size:14.5px;font-weight:600;margin:0 0 5px}}
.finding p{{margin:0;color:#{INK_SOFT};font-size:14px}}
.finding.extra h3::after{{content:"beyond the standard sections";font-weight:400;
 font-size:11px;color:#{MUTED};margin-left:8px}}
.cited{{font-size:11px;color:#{MUTED};margin-top:5px}}
.side{{border-top:1px solid #F0F2F7;padding-top:14px;margin-top:16px}}
.side h4{{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;
 color:#{INK_SOFT};margin:0 0 7px;font-weight:600}}
.side ul{{margin:0;padding-left:18px;font-size:13px;color:#{INK_SOFT}}}
.side li{{margin-bottom:5px}}
footer{{font-size:12px;color:#{MUTED};margin-top:26px}}
</style></head><body><div class="wrap">
<header><h1>MEA {e(REPORT_TITLES.get(kind, kind))}</h1>
<div class="sub">{e(scope) or "No scope detected"}</div></header>
<div class="tiles">{tiles}</div>
{_narrative_html(narrative, e)}
{charts}{extra}
<section><h2>Per well</h2>{table_html(well_table(wells, metrics))}</section>
{rasters}
<footer>Generated {e(datetime.now().strftime("%Y-%m-%d %H:%M"))} ·
Orchestration-MEA · metrics read from {e(", ".join(sorted({x for w in wells for x in w.sources})) or "pipeline output")}
</footer></div></body></html>"""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    LOG.info("Wrote %s", out)
    return out


# --------------------------------------------------------------------------- #
# PPTX
# --------------------------------------------------------------------------- #
def build_pptx(wells: list[Well], kind: str, out: Path,
               narrative: Optional[dict] = None) -> Optional[Path]:
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Emu, Inches, Pt
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        LOG.error("python-pptx is not installed — run: pip install python-pptx")
        return None

    s = summarise(wells)
    metrics = s["metrics"]
    rgb = lambda h: RGBColor.from_string(h)  # noqa: E731
    W, H = Inches(13.333), Inches(7.5)

    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]

    def text(slide, txt, x, y, w, h, size=16, bold=False, colour=INK,
             align=PP_ALIGN.LEFT, font="Calibri"):
        box = slide.shapes.add_textbox(x, y, w, h)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = rgb(colour)
        return box

    def fill(slide, x, y, w, h, colour):
        from pptx.enum.shapes import MSO_SHAPE
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(colour)
        sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def picture(slide, png: bytes, x, y, max_w, max_h):
        from PIL import Image
        im = Image.open(io.BytesIO(png))
        ratio = min(max_w / Emu(int(im.width * 9525)), max_h / Emu(int(im.height * 9525)))
        w = Emu(int(im.width * 9525 * ratio))
        h = Emu(int(im.height * 9525 * ratio))
        slide.shapes.add_picture(io.BytesIO(png), x + int((max_w - w) / 2), y, w, h)

    # ── Title (dark) ────────────────────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    bg = sl.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(INK)
    text(sl, "MEA " + REPORT_TITLES.get(kind, kind), Inches(.9), Inches(2.5),
         Inches(11.5), Inches(1.2), size=44, bold=True, colour="FFFFFF", font="Cambria")
    scope = " · ".join(x for x in [", ".join(s["chips"][:4]),
                                   f"{s['wells']} wells",
                                   ", ".join(s["groups"])] if x)
    text(sl, scope, Inches(.9), Inches(3.8), Inches(11.5), Inches(.6),
         size=17, colour="C9CCE0")
    text(sl, datetime.now().strftime("%d %B %Y"), Inches(.9), Inches(6.3),
         Inches(6), Inches(.4), size=13, colour="8A8FA8")
    sl.notes_slide.notes_text_frame.text = (
        "Generated by Orchestration-MEA from the pipeline's analysed output.")

    # ── Narrative ───────────────────────────────────────────────────────────
    if narrative:
        def bullets(slide, items, x, y, w, h, size=14, colour=INK_SOFT, gap=6):
            box = slide.shapes.add_textbox(x, y, w, h)
            tf = box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = 0
            for i, (label, body) in enumerate(items):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.space_after = Pt(gap)
                if label:
                    r = p.add_run()
                    r.text = label + "  "
                    r.font.size = Pt(size)
                    r.font.bold = True
                    r.font.name = "Calibri"
                    r.font.color.rgb = rgb(INK)
                r = p.add_run()
                r.text = body
                r.font.size = Pt(size)
                r.font.name = "Calibri"
                r.font.color.rgb = rgb(colour)
            return box

        findings = list(narrative.get("findings") or [])
        add = narrative.get("additional")
        if add and add.get("text"):
            findings.append({"title": add.get("title", "Also noted"),
                             "text": add["text"]})

        # Three findings per slide keeps the text at a readable size; more than
        # that and the body copy has to shrink below what reads from a room.
        pages = [findings[i:i + 3] for i in range(0, len(findings), 3)] or [[]]
        for page_no, page in enumerate(pages):
            sl = prs.slides.add_slide(blank)
            text(sl, "Summary" + (f" ({page_no + 1}/{len(pages)})"
                                  if len(pages) > 1 else ""),
                 Inches(.7), Inches(.5), Inches(11), Inches(.7),
                 size=30, bold=True, font="Cambria")
            top = Inches(1.3)
            if page_no == 0 and narrative.get("headline"):
                text(sl, narrative["headline"], Inches(.7), top, Inches(11.9),
                     Inches(1.0), size=19, bold=True, colour=INK_SOFT)
                top = Inches(2.5)
            if page:
                bullets(sl, [(f.get("title", ""), f.get("text", "")) for f in page],
                        Inches(.7), top, Inches(11.9), Inches(6.4) - top,
                        size=14, gap=14)
            text(sl, AI_LABEL, Inches(.7), Inches(6.85), Inches(11.9), Inches(.35),
                 size=10, colour=MUTED)
            sl.notes_slide.notes_text_frame.text = (
                "Narrative written by Claude. Every figure it cites was checked "
                "against the measured values before this file was written.")

        side = [("Caveat", c) for c in (narrative.get("caveats") or []) if c]
        side += [("Data quality", q.get("note", ""))
                 for q in (narrative.get("qc_notes") or []) if q.get("note")]
        if side:
            sl = prs.slides.add_slide(blank)
            text(sl, "Caveats and data quality", Inches(.7), Inches(.5),
                 Inches(11), Inches(.7), size=30, bold=True, font="Cambria")
            bullets(sl, side, Inches(.7), Inches(1.5), Inches(11.9), Inches(5.0),
                    size=14, gap=12)
            text(sl, AI_LABEL, Inches(.7), Inches(6.85), Inches(11.9), Inches(.35),
                 size=10, colour=MUTED)

    # ── Headline numbers ────────────────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    text(sl, "At a glance", Inches(.7), Inches(.55), Inches(9), Inches(.7),
         size=32, bold=True, font="Cambria")
    tiles = headline_stats(wells, s)
    tw, gap = Inches(2.85), Inches(.28)
    for i, (v, label, note) in enumerate(tiles):
        x = Inches(.7) + i * (tw + gap)
        fill(sl, x, Inches(1.75), tw, Inches(1.9), "F2F4FA")
        text(sl, v, x + Inches(.28), Inches(2.0), tw - Inches(.5), Inches(.8),
             size=40, bold=True, colour=INK)
        text(sl, label, x + Inches(.28), Inches(2.85), tw - Inches(.5), Inches(.35),
             size=13, bold=True, colour=INK_SOFT)
        if note:
            text(sl, note, x + Inches(.28), Inches(3.18), tw - Inches(.5), Inches(.35),
                 size=11, colour=MUTED)

    chart = (chart_by_group(wells, metrics) if kind == "condition" else
             chart_qc(wells) if kind == "qc" else
             chart_longitudinal(wells, metrics[0]) if kind == "longitudinal" and metrics else
             chart_per_well(wells, metrics[0]) if metrics else None)
    if chart:
        picture(sl, chart, Inches(.7), Inches(3.95), Inches(11.9), Inches(2.9))

    # ── Charts, one per slide ───────────────────────────────────────────────
    series: list[tuple[str, bytes]] = []
    if kind == "condition":
        for m in metrics[:6]:
            c = chart_per_well(wells, m)
            if c:
                series.append((PRETTY.get(m, m) + " by well", c))
    elif kind == "longitudinal":
        for m in metrics[:6]:
            c = chart_longitudinal(wells, m)
            if c:
                series.append((PRETTY.get(m, m), c))
    else:
        for m in metrics[1:5]:
            c = chart_per_well(wells, m)
            if c:
                series.append((PRETTY.get(m, m), c))

    for title, png in series:
        sl = prs.slides.add_slide(blank)
        text(sl, title, Inches(.7), Inches(.55), Inches(11), Inches(.7),
             size=30, bold=True, font="Cambria")
        picture(sl, png, Inches(.7), Inches(1.6), Inches(11.9), Inches(5.2))

    # ── Table ───────────────────────────────────────────────────────────────
    rows = (group_table(wells, metrics) if kind == "condition" and group_table(wells, metrics)
            else well_table(wells, metrics[:6]))
    if rows:
        sl = prs.slides.add_slide(blank)
        text(sl, "By group" if kind == "condition" and len(rows[0]) and rows[0][0] == "Group"
             else "Per well", Inches(.7), Inches(.55), Inches(11), Inches(.7),
             size=30, bold=True, font="Cambria")
        # Fit the table to the canvas: rows beyond the available height would
        # run off the bottom of the slide rather than being clipped.
        top, row_h, bottom_margin = Inches(1.5), Inches(.4), Inches(.75)
        max_rows = int((H - top - bottom_margin) / row_h)
        shown = rows[:max_rows]
        tbl = sl.shapes.add_table(len(shown), len(shown[0]), Inches(.7), top,
                                  Inches(11.9), row_h * len(shown)).table
        for c, name in enumerate(shown[0]):
            cell = tbl.cell(0, c)
            cell.text = str(name)
            para = cell.text_frame.paragraphs[0]
            para.runs[0].font.size = Pt(11)
            para.runs[0].font.bold = True
            para.runs[0].font.color.rgb = rgb("FFFFFF")
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(INK)
        for r, row in enumerate(shown[1:], start=1):
            for c, val in enumerate(row):
                cell = tbl.cell(r, c)
                cell.text = str(val)
                run = cell.text_frame.paragraphs[0].runs[0]
                run.font.size = Pt(10.5)
                run.font.color.rgb = rgb(INK_SOFT)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb("FFFFFF" if r % 2 else "F7F8FC")
        if len(rows) > len(shown):
            text(sl, f"{len(rows) - len(shown)} more row(s) not shown — the HTML report has all of them",
                 Inches(.7), top + row_h * len(shown) + Inches(.12), Inches(10),
                 Inches(.3), size=11, colour=MUTED)

    # ── QC failures ─────────────────────────────────────────────────────────
    if kind == "qc":
        bad = [w for w in wells if w.status == "failed" or w.error]
        if bad:
            sl = prs.slides.add_slide(blank)
            text(sl, "Failures", Inches(.7), Inches(.55), Inches(11), Inches(.7),
                 size=30, bold=True, colour=BAD, font="Cambria")
            y = Inches(1.6)
            for w in bad[:8]:
                fill(sl, Inches(.7), y, Inches(11.9), Inches(.62), "FDF2F2")
                text(sl, w.well, Inches(.95), y + Inches(.15), Inches(1.6),
                     Inches(.32), size=13, bold=True, colour=BAD)
                text(sl, (w.error or "failed").split("\n")[0][:110],
                     Inches(2.6), y + Inches(.15), Inches(9.8), Inches(.32),
                     size=11.5, colour=INK_SOFT)
                y += Inches(.75)

    # ── Rasters ─────────────────────────────────────────────────────────────
    if kind in ("run", "qc"):
        for w in [x for x in wells if x.figures.get("raster")][:6]:
            png = figure_png(w)
            if not png:
                continue
            sl = prs.slides.add_slide(blank)
            title = w.well + (f" · {w.group}" if w.group else "")
            text(sl, title, Inches(.7), Inches(.55), Inches(11), Inches(.7),
                 size=30, bold=True, font="Cambria")
            bits = [f"{PRETTY.get(m, m)} {fmt(w.get(m))}" for m in metrics[:4]
                    if w.get(m) is not None]
            if bits:
                text(sl, "   ·   ".join(bits), Inches(.7), Inches(1.25),
                     Inches(11.9), Inches(.4), size=13, colour=INK_SOFT)
            picture(sl, png, Inches(.7), Inches(1.85), Inches(11.9), Inches(5.0))

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    LOG.info("Wrote %s (%d slides)", out, len(prs.slides.__iter__.__self__._sldIdLst))
    return out


# --------------------------------------------------------------------------- #
# Entry point shared by the CLI and the web UI
# --------------------------------------------------------------------------- #
def generate(output_dir: Path,
             kinds: list[str],
             formats: list[str],
             report_dir: Optional[Path] = None,
             activity_dir: Optional[Path] = None,
             use_ai: bool = False,
             model: Optional[str] = None,
             on_progress=None) -> dict:
    """Build reports from analysed pipeline output.

    Returns a result dict rather than raising for the ordinary "nothing to
    report" cases, because the UI needs to show the reason rather than a stack
    trace. `on_progress(str)` is called at each phase so the button can report
    what it is doing; the model call is much the slowest phase.
    """
    def say(msg: str) -> None:
        LOG.info(msg)
        if on_progress:
            on_progress(msg)

    result: dict = {"files": [], "skipped": [], "warnings": [],
                    "narrative": None, "ai_error": None}

    say("Reading analysed output")
    wells = collect_wells(output_dir)
    if not wells:
        result["error"] = (
            f"No analysed wells found under {output_dir}. Expected per-well "
            "folders containing metrics_curated.xlsx, network_results.json, "
            "or checkpoints/.")
        return result

    plating = attach_activity(wells, activity_dir)
    time_kind = assign_div(wells, plating)
    s = summarise(wells)
    result["summary"] = s
    say(f"{s['wells']} well(s), {s['total_units']} unit(s)")
    if not s["metrics"]:
        result["warnings"].append(
            "No recognised metrics were found — the report will be thin.")

    kinds = (["run", "condition", "qc", "longitudinal"]
             if "all" in kinds else list(kinds))

    # A narrative is written once and reused across every requested report, so
    # asking for HTML and PPTX together costs one model call, not two.
    narrative = None
    if use_ai:
        import narrate as narrate_mod  # late import: the SDK is optional
        st = narrate_mod.status()
        if not st["ready"]:
            result["ai_error"] = st["reason"]
            say(f"Skipping the written summary: {st['reason']}")
        else:
            kind_for_brief = kinds[0] if kinds else "run"
            say("Sending the measured values to Claude")
            try:
                brief = narrate_mod.build_brief(
                    wells, kind_for_brief, s["metrics"], time_kind)
                narrative = narrate_mod.narrate(brief, model=model)
                result["narrative"] = narrative
                say("Summary received and checked against the data")
            except Exception as exc:                      # noqa: BLE001
                # A failed or unverifiable narrative must not cost the user
                # their charts: fall through and build the measured report.
                result["ai_error"] = str(exc)
                say(f"Written summary unavailable: {exc}")
            finally:
                dest_for_audit = report_dir or (output_dir / "reports")
                try:
                    narrate_mod.write_audit(dest_for_audit, locals().get("brief"),
                                            narrative, result["ai_error"])
                except Exception:                          # noqa: BLE001
                    LOG.debug("Could not write the narrative audit log",
                              exc_info=True)

    dest = report_dir or (output_dir / "reports")
    stamp = datetime.now().strftime("%Y%m%d_%H%M")

    for kind in kinds:
        if kind == "condition" and len(s["groups"]) < 2:
            result["skipped"].append(
                f"condition — {len(s['groups'])} group(s) found; genotype labels "
                "come from the activity-scan output.")
            continue
        if kind == "longitudinal" and len({w.div for w in wells if w.div is not None}) < 2:
            result["skipped"].append("longitudinal — fewer than 2 timepoints.")
            continue
        if kind == "longitudinal" and time_kind != "div":
            result["warnings"].append(
                f"No plating date found — the longitudinal x-axis is {time_kind} "
                "order, not true DIV.")
        for f in formats:
            out = dest / f"mea_{kind}_{stamp}.{f}"
            say(f"Writing {out.name}")
            r = (build_html(wells, kind, out, activity_dir, narrative) if f == "html"
                 else build_pptx(wells, kind, out, narrative))
            if r:
                result["files"].append(str(r))
            elif f == "pptx":
                result["warnings"].append(
                    "python-pptx is not installed — no PowerPoint was written.")
    return result


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("output_dir", type=Path, help="Pipeline --output-dir")
    p.add_argument("--type", nargs="+", default=["run"],
                   choices=["run", "condition", "qc", "longitudinal", "all"])
    p.add_argument("--format", nargs="+", default=["html"], choices=["html", "pptx"])
    p.add_argument("--report-dir", type=Path, default=None,
                   help="Where to write (default: <output_dir>/reports)")
    p.add_argument("--activity-dir", type=Path, default=None,
                   help="Activity-scan output, to attach genotype labels")
    p.add_argument("--ai", action="store_true",
                   help="Add a written summary from Claude (needs ANTHROPIC_API_KEY)")
    p.add_argument("--model", default=None, help="Override the model id")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")

    res = generate(a.output_dir, a.type, a.format, a.report_dir, a.activity_dir,
                   use_ai=a.ai, model=a.model)
    if res.get("error"):
        raise SystemExit(res["error"])
    for w in res["warnings"]:
        LOG.warning(w)
    for sk in res["skipped"]:
        LOG.warning("Skipped %s", sk)
    if res.get("ai_error"):
        LOG.warning("Written summary unavailable: %s", res["ai_error"])
    if res["files"]:
        LOG.info("Done — %d report(s):", len(res["files"]))
        for f in res["files"]:
            LOG.info("  %s", f)
    else:
        LOG.warning("No reports produced.")



if __name__ == "__main__":
    main()
