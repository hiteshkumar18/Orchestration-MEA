#!/usr/bin/env python3
"""
Turn a lab-notebook spreadsheet into figures, tables and one HTML report.

    python orchestration/explore.py "MaxTwo Organoids Assays.csv"
    python orchestration/explore.py notebook.xlsx --out reports/ --max-sheets 20

Written for the files the lab actually keeps: several tables on one sheet,
headers spanning two rows with a chip name banded over a group of columns, and
plenty of empty cells. ``tabular.py`` finds the tables; this module decides what
is worth drawing and writes the report.

What it will not do
-------------------
Invent meaning. Axis labels are the column's own header, exactly as written in
the file, and no unit is ever added. If a column is called ``P1W4`` the axis
says ``P1W4`` — the file does not say whether that is hertz, and neither does
this. Anything inferred (a header row, a band, a column's type) is stated in the
report as inferred, so a reader can tell what was read from what was guessed.
"""

from __future__ import annotations

import argparse
import base64
import html as html_mod
import io
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tabular import Block, Column, analyse  # noqa: E402

LOG = logging.getLogger("mea.explore")

# Same palette as the pipeline's reports, so the two look like one tool.
INK, INK_SOFT = "1F2328", "4A5560"
ACCENT, ACCENT_BG, ACCENT_LINE = "2F6F52", "E6F0EA", "CFE3D8"
MUTED, LABEL, BORDER, PAPER = "8A94A6", "6B7684", "E3E7EC", "FFFFFF"
SERIES = ["2F6F52", "4F9D7A", "7FB3A0", "B45309", "5B7C99", "8B6F9E",
          "C2678D", "5C8A3A"]

# Column names that usually mean "time since plating" in these files.
TIME_HINTS = ("doc", "div", "day", "age", "timepoint")

MAX_TABLE_ROWS = 40        # rows shown in a preview table
MAX_SERIES = 12            # trajectories drawn on one axes before thinning


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 140, "savefig.dpi": 140, "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#" + INK_SOFT, "text.color": "#" + INK,
        "axes.labelcolor": "#" + INK_SOFT, "xtick.color": "#" + INK_SOFT,
        "ytick.color": "#" + INK_SOFT,
    })
    return plt


def _png(fig) -> bytes:
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def pick_time_column(cols: list[Column]) -> Optional[Column]:
    """A column to plot against: an age-like number first, else a date."""
    numeric = [c for c in cols if c.kind == "number" and c.filled >= 3]
    for c in numeric:
        if any(h in c.name.lower() for h in TIME_HINTS):
            return c
    dates = [c for c in cols if c.kind == "date" and c.filled >= 3]
    return dates[0] if dates else None


def _pairs(x: Column, y: Column) -> tuple[list, list]:
    """Rows where both columns have a value, sorted by x."""
    both = [(a, b) for a, b in zip(x.values, y.values)
            if a is not None and b is not None]
    both.sort(key=lambda t: t[0])
    return [t[0] for t in both], [t[1] for t in both]


def fig_measures_vs_time(time_col: Column, series: list[Column],
                         title: str) -> Optional[bytes]:
    """One small panel per column, each with its own y-axis.

    Columns from a notebook share nothing but a row number — one may run 0–5
    and its neighbour 0–120,000. Drawn on one axis the small column flattens
    into the baseline, so each gets its own panel.
    """
    usable = [c for c in series
              if len([v for v in c.values if v is not None]) >= 2][:MAX_SERIES]
    if not usable or time_col is None:
        return None

    plt = _plt()
    ncol = min(3, len(usable))
    nrow = (len(usable) + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.4 * ncol, 2.5 * nrow),
                             squeeze=False, sharex=True)
    is_date = isinstance(next((v for v in time_col.values if v is not None), None),
                         (date, datetime))
    for k, c in enumerate(usable):
        ax = axes[k // ncol][k % ncol]
        xs, ys = _pairs(time_col, c)
        colour = "#" + SERIES[k % len(SERIES)]
        # Several rows can share one time point. Joining them draws a zigzag
        # that suggests a change over time that the file does not record.
        if len(set(map(str, xs))) < len(xs):
            ax.scatter(xs, ys, s=18, color=colour, alpha=.75,
                       edgecolors="white", linewidths=.5)
        else:
            ax.plot(xs, ys, "-o", ms=3.4, lw=1.5, color=colour)
        ax.set_title(c.name, fontsize=9)
        ax.tick_params(labelsize=7.5)
    for k in range(len(usable), nrow * ncol):
        axes[k // ncol][k % ncol].axis("off")
    fig.suptitle(title, fontsize=10.5)
    fig.supxlabel(time_col.name, fontsize=9)
    if is_date:
        fig.autofmt_xdate()
    fig.tight_layout()
    return _png(fig)


def fig_grid_heatmap(grid: dict, time_col: Optional[Column],
                     title: str) -> Optional[bytes]:
    """Wide well grid as time (rows) by well (columns)."""
    import numpy as np
    members = [c for c in grid["columns"] if c.kind == "number"]
    if len(members) < 4:
        return None
    members.sort(key=lambda c: grid["coords"][c.index])
    n_rows = max(len(c.values) for c in members)
    data = np.full((n_rows, len(members)), np.nan)
    for j, c in enumerate(members):
        for i, v in enumerate(c.values):
            if v is not None:
                data[i, j] = v
    keep = ~np.all(np.isnan(data), axis=1)
    data = data[keep]
    if data.size == 0 or data.shape[0] < 2:
        return None

    if time_col is not None:
        labels = [str(v) for v, k in zip(time_col.values, keep) if k]
    else:
        labels = [str(i + 1) for i in range(data.shape[0])]

    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(7.0, len(members) * 0.26), 3.4))
    im = ax.imshow(data, aspect="auto", cmap="viridis", interpolation="nearest")
    ax.set_xticks(range(len(members)))
    ax.set_xticklabels([c.name for c in members], rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.set_ylabel(time_col.name if time_col is not None else "row")
    ax.set_title(title, fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.012,
                 label="value as recorded")
    fig.tight_layout()
    return _png(fig)


def fig_grid_by_band(grid: dict, time_col: Optional[Column],
                     title: str) -> Optional[bytes]:
    """Each band (chip) as its own small panel of well trajectories."""
    bands: dict[str, list[Column]] = {}
    for c in grid["columns"]:
        if c.kind == "number":
            bands.setdefault(c.band or "—", []).append(c)
    bands = {k: v for k, v in bands.items()
             if any(len([x for x in c.values if x is not None]) >= 2 for c in v)}
    if not bands or time_col is None:
        return None

    plt = _plt()
    n = len(bands)
    ncol = min(4, n)
    nrow = (n + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.2 * ncol, 2.5 * nrow),
                             squeeze=False, sharex=True, sharey=True)
    for k, (name, cols) in enumerate(sorted(bands.items())):
        ax = axes[k // ncol][k % ncol]
        drawn = 0
        for i, c in enumerate(cols):
            xs, ys = _pairs(time_col, c)
            if len(xs) >= 2:
                ax.plot(xs, ys, "-o", ms=2.6, lw=1.2,
                        color="#" + SERIES[i % len(SERIES)], label=c.name)
                drawn += 1
        ax.set_title(name, fontsize=9)
        ax.tick_params(labelsize=7)
        if 0 < drawn <= 6:
            ax.legend(fontsize=6, frameon=False)
    for k in range(len(bands), nrow * ncol):
        axes[k // ncol][k % ncol].axis("off")
    fig.suptitle(title, fontsize=10.5)
    fig.supxlabel(time_col.name, fontsize=9)
    fig.tight_layout()
    return _png(fig)


def fig_by_category(cat: Column, num: Column, title: str) -> Optional[bytes]:
    """Every value drawn, with the group mean behind it."""
    import statistics
    groups: dict[str, list[float]] = {}
    for g, v in zip(cat.values, num.values):
        if g is not None and v is not None:
            groups.setdefault(_fmt(g), []).append(v)
    groups = {k: v for k, v in groups.items() if v}
    if len(groups) < 2 or len(groups) > 12:
        return None

    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(4.4, len(groups) * 1.05), 3.2))
    names = sorted(groups)
    for i, g in enumerate(names):
        vals = groups[g]
        c = "#" + SERIES[i % len(SERIES)]
        ax.bar(i, statistics.fmean(vals), .6, color=c, alpha=.28,
               edgecolor=c, linewidth=1.2)
        step = 0.22 / max(len(vals) - 1, 1)
        xs = [i - 0.11 + k * step for k in range(len(vals))] if len(vals) > 1 else [i]
        ax.scatter(xs, vals, s=20, color=c, zorder=3,
                   edgecolors="white", linewidths=.6)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=8, rotation=20 if len(names) > 4 else 0,
                       ha="right" if len(names) > 4 else "center")
    ax.set_ylabel(num.name)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return _png(fig)


def fig_counts(cat: Column, title: str) -> Optional[bytes]:
    counts: dict[str, int] = {}
    for v in cat.values:
        if v is not None:
            counts[_fmt(v)] = counts.get(_fmt(v), 0) + 1
    if not 1 < len(counts) <= 20:
        return None
    plt = _plt()
    items = sorted(counts.items(), key=lambda t: -t[1])
    fig, ax = plt.subplots(figsize=(max(4.2, len(items) * .62), 2.9))
    ax.bar(range(len(items)), [n for _, n in items], .64, color="#" + ACCENT)
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels([k[:18] for k, _ in items], rotation=30, ha="right", fontsize=7.5)
    ax.set_ylabel("recordings")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return _png(fig)


def fig_distribution(num: Column, title: str) -> Optional[bytes]:
    vals = [v for v in num.values if v is not None]
    if len(vals) < 8 or len(set(vals)) < 4:
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=(4.4, 2.8))
    ax.hist(vals, bins=min(24, max(6, len(set(vals)) // 2)),
            color="#" + ACCENT, alpha=.85)
    ax.set_xlabel(num.name)
    ax.set_ylabel("rows")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    return _png(fig)


# --------------------------------------------------------------------------- #
# Choosing what to draw
# --------------------------------------------------------------------------- #
CODE_MAX_LEVELS = 20       # distinct integers below which a column reads as a label
CODE_MAX_RATIO = 0.5       # ...and only if they repeat often enough to be levels
SERIAL_MIN_ROWS = 6        # rows needed before uniqueness means "serial number"


def _all_integers(vals: list[float]) -> bool:
    return bool(vals) and all(float(v).is_integer() for v in vals)


def roles(cols: list[Column], grid: Optional[dict]) -> dict:
    """Sort a table's columns into a time axis, measures, labels and skips.

    A number in a notebook is not automatically a measurement. ``Run #`` counts
    from 1 to 143 and never repeats — a serial number. ``Wells_Recorded`` holds
    123456, meaning wells one through six — a packed code. Plotting either as a
    quantity produces a chart that is drawn correctly and means nothing, so the
    split is made on the shape of the values and the reason is reported.
    """
    time_col = pick_time_column(cols)
    spoken_for = {id(c) for c in (grid["columns"] if grid else [])}

    measures: list[Column] = []
    labels: list[Column] = []
    skipped: list[tuple[Column, str]] = []

    for c in cols:
        if c is time_col or id(c) in spoken_for or c.kind in ("empty", "text"):
            continue
        if c.kind == "number":
            vals = [v for v in c.values if v is not None]
            if len(vals) < 3:
                skipped.append((c, "fewer than three values"))
            elif (_all_integers(vals) and len(vals) >= SERIAL_MIN_ROWS
                  and c.uniques >= 0.9 * len(vals)):
                skipped.append((c, "whole numbers, almost never repeated — reads "
                                   "as a serial number or row index"))
            elif (_all_integers(vals) and c.uniques <= CODE_MAX_LEVELS
                  and c.uniques <= CODE_MAX_RATIO * len(vals)):
                labels.append(c)
            else:
                measures.append(c)
        elif c.kind == "category" and 1 < c.uniques <= CODE_MAX_LEVELS:
            labels.append(c)
    return {"time": time_col, "measures": measures,
            "labels": labels, "skipped": skipped}


def figures_for(block: Block, cols: list[Column], grid: Optional[dict],
                r: Optional[dict] = None) -> list[tuple]:
    """(caption, png, wide?) for one table, best first."""
    out: list[tuple[str, bytes, bool]] = []
    r = r or roles(cols, grid)
    time_col = r["time"]

    measures, labels = r["measures"], r["labels"]
    axis = time_col.name if time_col is not None else "row order"

    if grid:
        n_num = sum(1 for c in grid["columns"] if c.kind == "number")
        heat = fig_grid_heatmap(grid, time_col,
                                f"All {n_num} grid columns over {axis}")
        if heat:
            out.append(("Grid overview", heat, True))
        panels = fig_grid_by_band(grid, time_col, f"Each column over {axis}, by group")
        if panels:
            out.append(("By group", panels, True))

    if time_col is not None and measures:
        traj = fig_measures_vs_time(time_col, measures, f"Measures against {axis}")
        if traj:
            out.append((f"Against {axis}", traj, len(measures) > 2))

    for lab in labels[:2]:
        for num in measures[:2]:
            f = fig_by_category(lab, num, f"{num.name} by {lab.name}")
            if f:
                out.append((f"{num.name} by {lab.name}", f, False))
                break
    for lab in labels[:4]:
        f = fig_counts(lab, f"Rows per {lab.name}")
        if f:
            out.append((f"Rows per {lab.name}", f, False))
    if not out:
        for num in measures[:3]:
            f = fig_distribution(num, f"Distribution of {num.name}")
            if f:
                out.append((f"Distribution of {num.name}", f, False))
    return out


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _b64(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:,.4g}"
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v)


def summarise_columns(cols: list[Column], n_rows: int) -> list[list[str]]:
    rows = [["Column", "Type", "Filled", "Distinct", "Range or examples"]]
    for c in cols:
        if c.kind == "empty":
            continue
        vals = [v for v in c.values if v is not None]
        if c.kind in ("number", "date") and vals:
            detail = f"{_fmt(min(vals))} … {_fmt(max(vals))}"
        else:
            seen, uniq = set(), []
            for v in vals:
                if str(v) not in seen:
                    seen.add(str(v))
                    uniq.append(str(v))
                if len(uniq) == 3:
                    break
            detail = ", ".join(u[:26] for u in uniq)
        rows.append([c.label, c.kind, f"{c.filled}/{n_rows}",
                     str(c.uniques or "—"), detail])
    return rows


def preview_rows(block: Block, cols: list[Column]) -> list[list[str]]:
    show = [c for c in cols if c.kind != "empty"][:12]
    rows = [[c.name for c in show]]
    for i in range(min(len(block.rows), MAX_TABLE_ROWS)):
        rows.append([_fmt(c.values[i]) if i < len(c.values) else "—" for c in show])
    return rows


def build_report(path: Path, tables: list[dict], out: Path,
                 png_dir: Optional[Path] = None) -> Path:
    e = html_mod.escape
    parts: list[str] = []

    for n, t in enumerate(tables, 1):
        block, cols, grid = t["block"], t["columns"], t["grid"]
        r = roles(cols, grid)
        figs = figures_for(block, cols, grid, r)

        if png_dir:
            png_dir.mkdir(parents=True, exist_ok=True)
            for k, (caption, png, _wide) in enumerate(figs, 1):
                safe = "".join(ch if ch.isalnum() else "_" for ch in caption)[:40]
                (png_dir / f"table{n}_{k}_{safe}.png").write_bytes(png)

        where = (f"sheet <b>{e(block.sheet)}</b> · columns {block.col0 + 1}–{block.col1} "
                 f"· rows {block.row0 + 1}–{block.row1}")
        notes = "".join(f"<li>{e(x)}</li>" for x in block.notes)
        if grid:
            n_num = sum(1 for c in grid["columns"] if c.kind == "number")
            notes += (f"<li>{len(grid['columns'])} columns follow a "
                      f"{e(grid['outer_name'])}&lt;n&gt;{e(grid['inner_name'])}&lt;n&gt; "
                      f"naming scheme ({n_num} carry values); drawn as a grid.</li>")
        if r["time"] is not None:
            notes += (f"<li>Plotted against <b>{e(r['time'].name)}</b>, the column "
                      "that reads as a time axis.</li>")
        for col, why in r["skipped"]:
            notes += (f"<li>Numeric column <b>{e(col.name)}</b> was not drawn as a "
                      f"measurement: {e(why)}. Its values are unchanged in the "
                      "tables below.</li>")

        cells = "".join(
            f'<div class="cell{" wide" if wide else ""}">'
            f'<div class="cap">{e(caption)}</div>'
            f'<div class="panel"><img src="{_b64(png)}" alt="{e(caption)}"></div></div>'
            for caption, png, wide in figs)

        def table_html(rows: list[list[str]]) -> str:
            head = "".join(f"<th>{e(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                           for r in rows[1:])
            return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

        more = (f'<div class="tnote">Showing the first {MAX_TABLE_ROWS} of '
                f'{block.n_rows} rows.</div>' if block.n_rows > MAX_TABLE_ROWS else "")

        parts.append(f'''
<section>
  <div class="shead"><h2>Table {n}</h2><span class="m">{where}</span></div>
  <div class="facts">
    <span><b>{block.n_rows}</b> rows</span>
    <span><b>{sum(1 for c in cols if c.kind != "empty")}</b> columns with data</span>
    <span><b>{sum(1 for c in cols if c.kind == "number")}</b> numeric</span>
  </div>
  {f'<ul class="notes">{notes}</ul>' if notes else ""}
  <div class="cols">{cells}</div>
  <div class="cols"><div class="cell wide"><div class="cap">Columns</div>
    <div class="panel scroll">{table_html(summarise_columns(cols, block.n_rows))}</div></div></div>
  <div class="cols"><div class="cell wide"><div class="cap">First rows</div>
    <div class="panel scroll">{table_html(preview_rows(block, cols))}{more}</div></div></div>
</section>''')

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(path.name)} — contents</title><style>
*{{box-sizing:border-box}}
body{{margin:0;background:#{PAPER};color:#{INK};
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:34px 34px 64px}}
h1{{margin:0;font-size:28px;font-weight:700;letter-spacing:-.02em}}
.sub{{margin-top:7px;font-size:13.5px;color:#{MUTED}}}
.warn{{margin:22px 0 4px;border:1px solid #{ACCENT_LINE};background:#{ACCENT_BG};
 border-radius:8px;padding:14px 18px;font-size:12.5px;color:#{INK_SOFT}}}
section{{margin-top:38px;padding-top:26px;border-top:1px solid #{BORDER}}}
.shead{{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}}
.shead h2{{margin:0;font-size:19px;font-weight:700}}
.shead .m{{font-size:12.5px;color:#{MUTED}}}
.facts{{display:flex;gap:22px;margin:12px 0 4px;font-size:13px;color:#{INK_SOFT}}}
.facts b{{font-size:17px;color:#{INK};font-weight:700}}
ul.notes{{margin:10px 0 0;padding-left:18px;font-size:12.5px;color:#{MUTED}}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));
 gap:20px 24px;align-items:start;margin-top:18px}}
.cell{{min-width:0}} .cell.wide{{grid-column:1 / -1}}
.cap{{font-size:12.5px;font-weight:600;color:#{LABEL};margin:0 0 8px}}
.panel{{background:#{PAPER};border:1px solid #{BORDER};border-radius:8px;padding:12px}}
.panel.scroll{{overflow-x:auto}}
.panel.scroll table{{min-width:100%;width:max-content}}
.panel.scroll th,.panel.scroll td{{white-space:nowrap}}
img{{max-width:100%;height:auto;display:block;border-radius:4px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;
 color:#{LABEL};font-weight:600;padding:8px 10px;border-bottom:1px solid #{BORDER}}}
td{{padding:7px 10px;border-bottom:1px solid #F1F3F5;font-variant-numeric:tabular-nums}}
tr:last-child td{{border-bottom:none}}
.tnote{{margin-top:10px;font-size:11.5px;color:#{MUTED}}}
footer{{margin-top:40px;border-top:1px solid #{BORDER};padding-top:16px;
 font-size:11.5px;color:#{MUTED}}}
@media print{{.wrap{{max-width:none;padding:0}} .cell{{break-inside:avoid}}}}
</style></head><body><div class="wrap">
<h1>{e(path.name)}</h1>
<div class="sub">{len(tables)} table(s) found · read {e(datetime.now().strftime("%Y-%m-%d %H:%M"))}</div>
<div class="warn"><b>Read this before citing a figure.</b> Axis labels are the
column headings exactly as they appear in the file — no units have been added,
because the file does not record them. Table boundaries, header rows and column
types were inferred from the layout; each table lists what was inferred.</div>
{"".join(parts)}
<footer>Generated by Orchestration-MEA · explore.py · from {e(str(path))}</footer>
</div></body></html>"""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    LOG.info("Wrote %s", out)
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", type=Path, help="A .csv, .tsv or .xlsx lab notebook")
    p.add_argument("--out", type=Path, default=None,
                   help="Output folder (default: beside the input file)")
    p.add_argument("--max-sheets", type=int, default=0,
                   help="Stop after this many tables (0 = all)")
    p.add_argument("--no-png", action="store_true",
                   help="Only write the HTML, not the separate figure files")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(levelname)-7s %(message)s")
    if not a.file.is_file():
        raise SystemExit(f"No such file: {a.file}")

    tables = analyse(a.file)
    if not tables:
        raise SystemExit(
            f"No tables recognised in {a.file.name}. Expected a sheet with a "
            "header row and at least a few rows of data beneath it.")
    if a.max_sheets:
        tables = tables[:a.max_sheets]

    dest = a.out or a.file.parent
    stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in a.file.stem)[:60]
    out = dest / f"{stem}_contents.html"
    png_dir = None if a.no_png else dest / f"{stem}_figures"

    LOG.info("%d table(s) in %s", len(tables), a.file.name)
    build_report(a.file, tables, out, png_dir)
    LOG.info("Done — %s", out)
    if png_dir and png_dir.is_dir():
        LOG.info("Figures — %s (%d)", png_dir, len(list(png_dir.glob("*.png"))))


if __name__ == "__main__":
    main()
