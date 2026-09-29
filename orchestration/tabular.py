#!/usr/bin/env python3
"""
Find the tables inside a lab-notebook spreadsheet.

These files are written for people, not programs: one sheet holds several
independent tables side by side, headers span two rows with a chip name banded
over a group of columns, and most cells are empty. Reading such a sheet as a
single rectangle produces nonsense, so this module locates each table first and
resolves its header before any value is interpreted.

Nothing here guesses what a column *means*. Names are carried through exactly as
written in the file, and anything inferred (a header row, a banded group, a
column's type) is recorded so the report can say so rather than imply certainty.

Used by ``explore.py``. Depends only on the standard library and openpyxl.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

LOG = logging.getLogger("mea.tabular")

Cell = Optional[Any]
Grid = list[list[Cell]]

# A block narrower or shorter than this is noise — a stray note, a legend.
MIN_COLS, MIN_ROWS = 2, 3

# Columns whose values repeat rarely are identifiers rather than categories.
CATEGORY_MAX_UNIQUE = 25
CATEGORY_MAX_RATIO = 0.5


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def read_grids(path: Path) -> list[tuple[str, Grid]]:
    """(sheet name, grid) for every sheet. A CSV is a single unnamed sheet."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv", ".txt"):
        delim = "\t" if suffix == ".tsv" else ","
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            rows = [[c if c.strip() else None for c in r]
                    for r in csv.reader(fh, delimiter=delim)]
        return [(path.stem, rows)]

    if suffix in (".xlsx", ".xlsm", ".xltx"):
        try:
            import openpyxl
        except ImportError as exc:                       # pragma: no cover
            raise RuntimeError("openpyxl is needed to read .xlsx files "
                               "(pip install openpyxl)") from exc
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets:
            grid = [[c if c not in ("", None) else None for c in row]
                    for row in ws.iter_rows(values_only=True)]
            out.append((ws.title, grid))
        wb.close()
        return out

    raise RuntimeError(f"Unsupported file type: {suffix or path.name}")


# --------------------------------------------------------------------------- #
# Blocks
# --------------------------------------------------------------------------- #
@dataclass
class Block:
    """One table found inside a sheet."""
    sheet: str
    col0: int
    col1: int                      # exclusive
    row0: int
    row1: int                      # exclusive
    header: list[str] = field(default_factory=list)
    header_rows: int = 1
    banded: dict[int, str] = field(default_factory=dict)   # col index -> band
    rows: list[list[Cell]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def width(self) -> int:
        return self.col1 - self.col0

    @property
    def n_rows(self) -> int:
        return len(self.rows)


def _filled(grid: Grid) -> tuple[list[int], list[int]]:
    """How many non-empty cells each row and each column holds."""
    width = max((len(r) for r in grid), default=0)
    per_row = [sum(1 for c in r if c is not None) for r in grid]
    per_col = [0] * width
    for r in grid:
        for i, c in enumerate(r):
            if c is not None:
                per_col[i] += 1
    return per_row, per_col


def _runs(flags: list[bool]) -> list[tuple[int, int]]:
    """Index ranges where ``flags`` is True, as (start, end-exclusive)."""
    out, start = [], None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        elif not f and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(flags)))
    return out


# How many consecutive empty rows count as a break between stacked tables.
# One or two blank rows inside a run log are just spacing, and splitting on
# those tore a single table into fragments that each lost the header.
ROW_GAP = 3

# Rows searched for a header before giving up.
HEADER_SEARCH = 6


def _text_mask(grid: Grid, row: int, c0: int, c1: int) -> list[bool]:
    """Which columns carry a label-like cell in this row."""
    r = grid[row] if row < len(grid) else []
    out = []
    for i in range(c0, c1):
        v = r[i] if i < len(r) else None
        out.append(isinstance(v, str) and bool(v.strip()) and not _is_number(v))
    return out


def _header_row_per_column(grid: Grid, c0: int, c1: int,
                           r0: int, r1: int) -> list[Optional[int]]:
    """For each column, the row its header most likely sits on.

    Tables that sit side by side often head their columns on different rows —
    a run log labelled on row 0 beside a well grid labelled on row 1, with chip
    names banded above it. Picking one header row for the whole sheet mixes the
    two together, so each column is asked separately and columns are grouped by
    the answer.

    A column can have text on several rows (a banded chip name above a well
    name). The row where *most other columns* also have labels wins, which is
    the real header rather than the band.
    """
    rows = list(range(r0, min(r0 + HEADER_SEARCH, r1)))
    masks = {r: _text_mask(grid, r, c0, c1) for r in rows}
    coverage = {r: sum(m) / max(len(m), 1) for r, m in masks.items()}

    per_col: list[Optional[int]] = []
    for i in range(c1 - c0):
        best, best_cov = None, 0.0
        for r in rows:
            if masks[r][i] and coverage[r] > best_cov:
                best, best_cov = r, coverage[r]
        per_col.append(best if best_cov >= 0.25 else None)

    # A data cell that happens to hold text ("M08121", "NA") can out-vote a
    # column's real header and split a table down the middle. Columns sitting
    # together almost always share a header row, so let the neighbourhood
    # decide when the column has a label there too.
    smoothed = list(per_col)
    for i in range(len(per_col)):
        lo, hi = max(0, i - 3), min(len(per_col), i + 4)
        window = [r for r in per_col[lo:hi] if r is not None]
        if not window:
            continue
        mode = max(set(window), key=window.count)
        if smoothed[i] != mode and mode in masks and masks[mode][i]:
            smoothed[i] = mode
    return smoothed


def find_blocks(sheet: str, grid: Grid) -> list[Block]:
    """Split a sheet into the tables it actually contains.

    Columns first (an always-empty column separates neighbours), then rows on a
    genuine gap, then by where each column's header sits — which is what
    separates two tables that touch with no blank column between them.
    """
    if not grid:
        return []
    per_row, per_col = _filled(grid)
    if not per_col:
        return []

    blocks: list[Block] = []
    for c0, c1 in _runs([n > 0 for n in per_col]):
        if c1 - c0 < MIN_COLS:
            continue
        occupied = [any(r[i] is not None for i in range(c0, min(c1, len(r))))
                    for r in grid]

        # Only a real gap splits stacked tables.
        gaps = [(a, b) for a, b in _runs([not o for o in occupied]) if b - a >= ROW_GAP]
        bounds, prev = [], 0
        for a, b in gaps:
            if a > prev:
                bounds.append((prev, a))
            prev = b
        if prev < len(grid):
            bounds.append((prev, len(grid)))

        for r0, r1 in bounds:
            while r0 < r1 and not occupied[r0]:
                r0 += 1
            while r1 > r0 and not occupied[r1 - 1]:
                r1 -= 1
            if r1 - r0 < MIN_ROWS:
                continue

            # Group neighbouring columns that share a header row.
            per_col_hdr = _header_row_per_column(grid, c0, c1, r0, r1)
            start, current = 0, per_col_hdr[0] if per_col_hdr else None
            for i in range(1, len(per_col_hdr) + 1):
                this = per_col_hdr[i] if i < len(per_col_hdr) else "END"
                if this != current:
                    if i - start >= MIN_COLS and current is not None:
                        blocks.append(Block(sheet=sheet, col0=c0 + start,
                                            col1=c0 + i, row0=r0, row1=r1,
                                            header_rows=1))
                        blocks[-1].__dict__["_hdr_row"] = current
                    start, current = i, this
    return blocks


# --------------------------------------------------------------------------- #
# Headers
# --------------------------------------------------------------------------- #
def _as_text(v: Cell) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return str(v).strip()


def _looks_like_header(cells: list[Cell]) -> float:
    """How header-ish a row is: short, non-numeric, mostly filled labels."""
    vals = [c for c in cells if c is not None]
    if not vals:
        return 0.0
    texty = sum(1 for v in vals
                if isinstance(v, str) and len(v) < 40 and not _is_number(v))
    return texty / len(vals) * (len(vals) / max(len(cells), 1))


def _is_number(v: Cell) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        try:
            float(v.replace(",", "").strip())
            return True
        except ValueError:
            return False
    return False


def resolve_header(block: Block, grid: Grid) -> None:
    """Fill in a block's header, band and data rows.

    The header row was already decided when the block was cut out — columns
    were grouped by it — so it is used rather than guessed at a second time.
    Rows above it that carry a sparse label every few columns are a band (chip
    names over well columns); the band is kept as a group label because it is
    the only thing tying a well column to its chip.
    """
    width = block.width

    def row_slice(r: int) -> list[Cell]:
        row = grid[r] if r < len(grid) else []
        return [row[i] if i < len(row) else None
                for i in range(block.col0, block.col1)]

    hdr_row = block.__dict__.get("_hdr_row")
    if hdr_row is None:
        block.header = [f"col{i + 1}" for i in range(width)]
        block.header_rows = 0
        block.rows = [r for r in (row_slice(x) for x in range(block.row0, block.row1))
                      if any(c is not None for c in r)]
        block.notes.append("No header row was recognised; columns are numbered.")
        return

    block.header = [_as_text(c) or f"col{i + 1}"
                    for i, c in enumerate(row_slice(hdr_row))]
    block.header_rows = 1

    for r in range(block.row0, hdr_row):
        above = row_slice(r)
        n = sum(1 for c in above if c is not None)
        if 0 < n <= max(2, width // 4):
            band, current = {}, None
            for i, c in enumerate(above):
                if c is not None:
                    current = _as_text(c)
                if current:
                    band[i] = current
            if band:
                block.banded = band
                block.header_rows = 2
                block.notes.append(
                    f"Two-row header: {len(set(band.values()))} group(s) banded "
                    "over the columns beneath.")
                break

    block.rows = [r for r in (row_slice(x) for x in range(hdr_row + 1, block.row1))
                  if any(c is not None for c in r)]


# --------------------------------------------------------------------------- #
# Column typing
# --------------------------------------------------------------------------- #
DATE_PATTERNS = (
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%Y/%m/%d",
    "%d-%b-%Y", "%b %d, %Y", "%Y-%m-%d %H:%M:%S",
)


def parse_date(v: Cell):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        s = v.strip()
        for fmt in DATE_PATTERNS:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def to_number(v: Cell) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").replace("%", "").strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


@dataclass
class Column:
    index: int
    name: str
    band: str = ""
    kind: str = "empty"            # date | number | category | identifier | text | empty
    values: list = field(default_factory=list)      # parsed, aligned to block.rows
    filled: int = 0
    uniques: int = 0

    @property
    def label(self) -> str:
        return f"{self.band} · {self.name}" if self.band else self.name


def classify(block: Block) -> list[Column]:
    """Type every column from its values, not its name."""
    cols: list[Column] = []
    for i, name in enumerate(block.header):
        raw = [r[i] if i < len(r) else None for r in block.rows]
        present = [v for v in raw if v is not None]
        col = Column(index=i, name=name, band=block.banded.get(i, ""),
                     filled=len(present))

        if not present:
            col.values = [None] * len(raw)
            cols.append(col)
            continue

        dates = [parse_date(v) for v in present]
        nums = [to_number(v) for v in present]
        n_dates = sum(1 for d in dates if d is not None)
        n_nums = sum(1 for n in nums if n is not None)

        if n_dates >= max(2, int(0.7 * len(present))):
            col.kind = "date"
            col.values = [parse_date(v) for v in raw]
        elif n_nums and n_nums >= max(1, int(0.7 * len(present))):
            col.kind = "number"
            col.values = [to_number(v) for v in raw]
        else:
            texts = [_as_text(v) for v in raw]
            col.values = [t or None for t in texts]
            uniq = {t for t in texts if t}
            col.uniques = len(uniq)
            ratio = len(uniq) / max(len(present), 1)
            if len(uniq) <= CATEGORY_MAX_UNIQUE and ratio <= CATEGORY_MAX_RATIO:
                col.kind = "category"
            elif max((len(t) for t in uniq), default=0) > 60:
                col.kind = "text"
            else:
                col.kind = "identifier"

        if col.kind in ("number", "date"):
            col.uniques = len({v for v in col.values if v is not None})
        cols.append(col)
    return cols


# --------------------------------------------------------------------------- #
# Wide grids
# --------------------------------------------------------------------------- #
GRID_NAME = re.compile(r"^([A-Za-z]+)(\d+)([A-Za-z]+)(\d+)$")   # P1W4, C2R11


def detect_grid(cols: list[Column]) -> Optional[dict]:
    """Numeric columns named on a two-part scheme, e.g. P<plate>W<well>.

    Reported as a grid so it can be drawn as a heatmap and as trajectories,
    rather than as forty-two unrelated series.
    """
    members = []
    for c in cols:
        if c.kind not in ("number", "empty"):
            continue
        m = GRID_NAME.match(c.name.strip())
        if m:
            members.append((c, m.group(1), int(m.group(2)), m.group(3), int(m.group(4))))
    if sum(1 for m in members if m[0].kind == "number") < 6:
        return None
    outer = {m[1] for m in members}
    inner = {m[3] for m in members}
    if len(outer) != 1 or len(inner) != 1:
        return None
    return {
        "columns": [m[0] for m in members],
        "outer_name": members[0][1],
        "inner_name": members[0][3],
        "outer_values": sorted({m[2] for m in members}),
        "inner_values": sorted({m[4] for m in members}),
        "coords": {m[0].index: (m[2], m[4]) for m in members},
    }


def analyse(path: Path) -> list[dict]:
    """Every table in a file, with its header resolved and columns typed."""
    out = []
    for sheet, grid in read_grids(path):
        for block in find_blocks(sheet, grid):
            resolve_header(block, grid)
            if not block.rows:
                continue
            cols = classify(block)
            if not any(c.kind in ("number", "date", "category") for c in cols):
                continue                       # nothing plottable or countable
            out.append({"block": block, "columns": cols, "grid": detect_grid(cols)})
    return out
