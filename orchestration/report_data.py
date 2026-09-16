"""
Collect analysed results into a uniform structure for reporting.

Schema tolerance
----------------
This is written against the pipeline's *documented* output layout, without a
sample of the real files. So nothing here assumes a fixed set of keys: it reads
whatever is present, maps names we recognise onto canonical ones, and keeps
everything else rather than discarding it. A field that appears under a slightly
different name still reaches the report; a field that is missing is reported as
missing instead of raising.

Layout it walks (per the pipeline README):

    <output>/<project>/<date>/<chip>/<run_id>/<well>/
        metrics_curated.xlsx      per-unit quality metrics after curation
        rejection_log.xlsx        units removed, with reasons
        network_results.json      burst statistics
        raster_burst_plot.svg     raster + network bursts (also _30s, _60s)
        waveforms_grid.pdf        waveform overview
        locations_unfiltered.pdf  unit probe locations
        processing_info.json      whether sorting was used
        checkpoints/*.json        per-stage progress and errors

Activity-scan output (``summary.json``) is picked up too when present, so a
report can combine sorted units with whole-array context.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

LOG = logging.getLogger("mea.report_data")

# Canonical metric -> name fragments seen in the wild. Matching is on a
# lowercased, punctuation-stripped form, so "Firing Rate (Hz)", "firing_rate"
# and "mean_firing_rate" all land on the same canonical key.
ALIASES: dict[str, tuple[str, ...]] = {
    # Longest matching fragment wins, so the specific names below beat the
    # generic ones: "peak_population_firing_rate_hz" must not land on
    # firing_rate_hz, because it is a population sum at a burst peak (thousands
    # of Hz), not a per-neuron rate.
    "peak_pop_rate_hz":      ("peakpopulationfiringrate", "peakpopulationrate"),
    "firing_rate_hz":        ("firingrate", "meanfiringrate", "ratehz"),
    "amplitude_uv":          ("amplitude", "amplitudemedian", "peakamplitude"),
    "presence_ratio":        ("presenceratio",),
    "isi_violations":        ("isiviolation", "isiviolations", "rpcontamination",
                              "refractoryperiodviolation"),
    "snr":                   ("snr", "signaltonoise"),
    "num_spikes":            ("numspikes", "nspikes", "totalspikes"),
    "burst_rate_hz":         ("burstfrequency", "burstrate", "networkburstrate"),
    "burst_duration_s":      ("burstduration",),
    "spikes_per_burst":      ("spikesperburst", "numberofspikesperburst",
                              "spikecountperburst"),
    "burst_count":           ("burstcount", "nbursts"),
    "participation_fraction": ("participationfraction",),
    "peak_participation":    ("peakparticipationfraction",),
    "ifbi_s":                ("ifbi",),
    "pct_spikes_in_bursts":  ("spikeswithinbursts", "percentspikesinbursts",
                              "pctspikesinbursts", "fractionspikesinbursts"),
    "interburst_interval_s": ("interburstinterval", "ibi"),
    "network_burstiness":    ("networkburstiness", "burstiness"),
    "synchrony":             ("synchrony", "synchronyindex", "fano"),
}

PRETTY = {
    "units": "Units",
    "peak_pop_rate_hz": "Peak population rate (Hz)",
    "burst_count": "Bursts detected",
    "participation_fraction": "Units in burst (fraction)",
    "peak_participation": "Peak participation (fraction)",
    "ifbi_s": "Inter-fragment interval (s)",
    "firing_rate_hz": "Firing rate (Hz)",
    "amplitude_uv": "Amplitude (µV)",
    "presence_ratio": "Presence ratio",
    "isi_violations": "ISI violations",
    "snr": "SNR",
    "num_spikes": "Spikes",
    "burst_rate_hz": "Burst rate (Hz)",
    "burst_duration_s": "Burst duration (s)",
    "spikes_per_burst": "Spikes per burst",
    "pct_spikes_in_bursts": "Spikes in bursts (%)",
    "interburst_interval_s": "Interburst interval (s)",
    "network_burstiness": "Network burstiness",
    "synchrony": "Synchrony",
    "units_rejected": "Units rejected",
}

# Conservative sanity ranges for a per-well mean. These are not biology — they
# are wide enough that any real culture sits inside them, and exist only to
# catch a metric fed by the wrong field. A value outside the range is flagged,
# never silently altered or dropped.
PLAUSIBLE: dict[str, tuple[float, float]] = {
    "firing_rate_hz":        (0.0, 100.0),    # per-unit mean spike rate
    "amplitude_uv":          (0.0, 2000.0),
    "presence_ratio":        (0.0, 1.0),
    "pct_spikes_in_bursts":  (0.0, 100.0),
    "burst_rate_hz":         (0.0, 20.0),
    "burst_duration_s":      (0.0, 120.0),
    "interburst_interval_s": (0.0, 3600.0),
    "isi_violations":        (0.0, 100.0),
    "network_burstiness":    (0.0, 100.0),
    "participation_fraction": (0.0, 1.0),
    "peak_participation":    (0.0, 1.0),
}


def implausible(key: str, value: Optional[float]) -> Optional[str]:
    """Why a value looks wrong for its metric, or None if it looks fine."""
    base = key
    for pre in LEVEL_LABEL:
        if base.startswith(pre):
            base = base[len(pre):]
            break
    if value is None or base not in PLAUSIBLE:
        return None
    lo, hi = PLAUSIBLE[base]
    if value < lo or value > hi:
        return f"outside the expected range {lo:g}–{hi:g}"
    return None


FIGURES = {
    "raster": ("raster_burst_plot.svg", "raster_burst_plot.png"),
    "raster_30s": ("raster_burst_plot_30s.svg", "raster_burst_plot_30s.png"),
    "raster_60s": ("raster_burst_plot_60s.svg", "raster_burst_plot_60s.png"),
    "waveforms": ("waveforms_grid.pdf",),
    "locations": ("locations_unfiltered.pdf",),
}


# Blocks of tuning parameters that sit alongside results in the pipeline's
# JSON. Nothing inside these is a measurement — they are the settings the
# analysis ran with. Mapping them onto metric names put a smoothing width
# ("sigma_firing_rate_bins") into a report as a firing rate, so any field whose
# path passes through one of these is kept as context and never mapped.
PARAM_CONTAINERS = frozenset({
    "diagnostics", "diagnostic", "params", "parameters", "config",
    "configuration", "settings", "options", "meta", "metadata",
    "thresholds", "hyperparams", "args",
})

# Leaf names that describe how the analysis was run rather than what it found.
# Applied only when the name is not an exact canonical key, so a genuine
# "firing_rate_hz" is unaffected.
PARAM_HINTS = ("sigma", "threshold", "mergegap", "binsize", "bins", "window",
               "cutoff", "minunits", "maxunits", "baseline", "adaptive",
               "reference", "valid", "enabled", "seed", "version")


# The pipeline reports bursts at two levels: short "fragments", and the
# "network bursts" formed by merging them. They are different events with
# different rates and durations, so they get separate metrics — showing a
# fragment rate beside a network interburst interval, as one table of "burst"
# numbers, invites reading a relationship that is not there.
LEVEL_PREFIX = {"networkbursts": "nb_", "superbursts": "sb_"}
LEVEL_LABEL = {"nb_": "Network burst", "sb_": "Superburst"}

# Metrics that are level-specific. Anything else (amplitude, presence ratio)
# is not a burst measure and is left unprefixed.
LEVELLED = frozenset({
    "burst_rate_hz", "burst_duration_s", "spikes_per_burst", "burst_count",
    "interburst_interval_s", "participation_fraction", "peak_participation",
    "peak_pop_rate_hz", "ifbi_s",
})


def level_of(flat_key: str) -> str:
    """Prefix for the burst level a flattened key belongs to ('' if none)."""
    for part in str(flat_key).split(".")[:-1]:
        pre = LEVEL_PREFIX.get(_norm(part))
        if pre:
            return pre
    return ""


# Display names for the network-burst level. Spelled out rather than derived
# from the fragment-level name, because splicing a prefix onto a label produced
# things like "Network burst s detected".
LEVEL_NAMES: dict[str, dict[str, str]] = {
    "nb_": {
        "burst_rate_hz": "Network burst rate (Hz)",
        "burst_duration_s": "Network burst duration (s)",
        "burst_count": "Network bursts detected",
        "interburst_interval_s": "Network interburst interval (s)",
        "spikes_per_burst": "Spikes per network burst",
        "participation_fraction": "Units in network burst (fraction)",
        "peak_participation": "Peak participation, network burst",
        "peak_pop_rate_hz": "Peak population rate, network burst (Hz)",
        "ifbi_s": "Inter-network-burst interval (s)",
    },
    "sb_": {
        "burst_rate_hz": "Superburst rate (Hz)",
        "burst_duration_s": "Superburst duration (s)",
        "burst_count": "Superbursts detected",
        "interburst_interval_s": "Inter-superburst interval (s)",
    },
}


def pretty_name(key: str) -> str:
    """Display name, including the burst level when the metric has one."""
    for pre, names in LEVEL_NAMES.items():
        if key.startswith(pre):
            base = key[len(pre):]
            return names.get(base, f"{LEVEL_LABEL[pre]}: {PRETTY.get(base, base)}")
    return PRETTY.get(key, key)


def is_parameter(flat_key: str) -> bool:
    """Whether a flattened JSON key names a setting rather than a result."""
    parts = [_norm(p) for p in str(flat_key).split(".")]
    if any(p in PARAM_CONTAINERS for p in parts[:-1]):
        return True
    leaf = parts[-1] if parts else ""
    if leaf in {_norm(k) for k in ALIASES}:
        return False
    return any(h in leaf for h in PARAM_HINTS)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def canonical(name: str) -> Optional[str]:
    """Canonical key for a column/field name, or None if unrecognised.

    Scored by the longest matching fragment rather than first-match, because
    short fragments are contained in longer unrelated names: "burstfrequency"
    contains "fr", so a naive scan mapped burst rate onto firing rate. The
    longest match wins, and an exact key match always wins outright.
    """
    n = _norm(name)
    best: Optional[str] = None
    best_len = 0
    for key, frags in ALIASES.items():
        if n == _norm(key):
            return key
        for f in frags:
            if f in n and len(f) > best_len:
                best, best_len = key, len(f)
    return best


def _numeric(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def flatten(obj: Any, prefix: str = "") -> dict[str, float]:
    """Flatten nested JSON to numeric leaves, joining keys with '.'."""
    out: dict[str, float] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, (list, tuple)):
        vals = [n for n in (_numeric(x) for x in obj) if n is not None]
        if vals:                     # summarise a numeric array
            out[f"{prefix}.mean"] = sum(vals) / len(vals)
            out[f"{prefix}.n"] = float(len(vals))
    else:
        n = _numeric(obj)
        if n is not None and prefix:
            out[prefix] = n
    return out


# --------------------------------------------------------------------------- #
# Per-well record
# --------------------------------------------------------------------------- #
@dataclass
class Well:
    path: Path
    well: str = ""
    run_id: str = ""
    chip_id: str = ""
    project: str = ""
    date: str = ""
    group: str = ""                       # genotype / condition, when known
    div: Optional[int] = None

    units: Optional[int] = None
    units_rejected: Optional[int] = None
    metrics: dict[str, float] = field(default_factory=dict)   # canonical
    extra: dict[str, float] = field(default_factory=dict)     # everything else
    figures: dict[str, str] = field(default_factory=dict)
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    status: str = "unknown"
    error: Optional[str] = None
    sources: list[str] = field(default_factory=list)
    # canonical metric -> "file:original column". Recorded so a surprising
    # number in a report can be traced back to the field it came from without
    # re-reading the pipeline output by hand.
    provenance: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[float]:
        if key == "units":
            return float(self.units) if self.units is not None else None
        if key == "units_rejected":
            return float(self.units_rejected) if self.units_rejected is not None else None
        return self.metrics.get(key)


def _read_table(path: Path):
    """Read an xlsx/csv with pandas if available, else return None."""
    try:
        import pandas as pd
    except ImportError:
        LOG.debug("pandas unavailable; skipping %s", path.name)
        return None
    try:
        if path.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
            return pd.read_excel(path)
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("Could not read %s: %s", path, exc)
        return None


def load_units(well: Well, path: Path) -> None:
    """Per-unit metrics: unit count and the mean of each recognised column."""
    df = _read_table(path)
    if df is None or not len(df):
        return
    well.sources.append(path.name)
    well.units = int(len(df))
    for col in df.columns:
        key = canonical(col)
        series = df[col]
        try:
            mean = float(series.mean())
        except Exception:  # noqa: BLE001 - non-numeric column
            continue
        if mean != mean:                  # NaN
            continue
        if key:
            well.metrics[key] = mean
            well.provenance[key] = f"{path.name}:{col}"
        else:
            well.extra[f"units.{_norm(col)}"] = mean


def load_rejections(well: Well, path: Path) -> None:
    """How many units were removed, and the reasons given."""
    df = _read_table(path)
    if df is None:
        return
    well.sources.append(path.name)
    well.units_rejected = int(len(df))
    for col in df.columns:
        if "reason" in _norm(col):
            try:
                counts = df[col].astype(str).value_counts().to_dict()
                well.rejection_reasons = {str(k): int(v) for k, v in counts.items()}
            except Exception:  # noqa: BLE001
                pass
            break


def load_network(well: Well, path: Path) -> None:
    """Burst statistics — shape unknown, so flatten and map what we recognise."""
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        LOG.warning("Could not read %s: %s", path, exc)
        return
    well.sources.append(path.name)
    # A well whose only output is network_results.json still reports its unit
    # count there; without this it showed as "no units" in the report.
    UNIT_COUNT = ("nunits", "numunits", "unitcount", "nunitscurated", "ngoodunits")
    for flat_key, value in flatten(data).items():
        leaf = flat_key.split(".")[-1]
        if is_parameter(flat_key):
            well.extra[flat_key] = value        # kept, but never a metric
            continue
        if well.units is None and _norm(leaf) in UNIT_COUNT:
            well.units = int(value)
            well.provenance["units"] = f"{path.name}:{flat_key}"
            continue
        key = canonical(leaf) or canonical(flat_key)
        if key in LEVELLED:
            key = level_of(flat_key) + key
        if key and key not in well.metrics:
            well.metrics[key] = value
            well.provenance[key] = f"{path.name}:{flat_key}"
        else:
            well.extra[flat_key] = value


def load_checkpoint(well: Well, folder: Path) -> None:
    """Stage/status, so a report can distinguish complete wells from failed ones."""
    ck = folder / "checkpoints"
    if not ck.is_dir():
        return
    for fp in sorted(ck.glob("*_checkpoint.json")):
        try:
            state = json.loads(fp.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        stage = int(state.get("stage", 0) or 0)
        if state.get("failed_stage") is not None or state.get("error"):
            well.status, well.error = "failed", str(state.get("error") or "")[:500]
        elif stage >= 10:
            well.status = "complete"
        else:
            well.status = "running"
        for f in ("run_id", "chip_id", "project", "date"):
            if not getattr(well, f) and state.get(f):
                setattr(well, f, str(state[f]))
        break


def load_figures(well: Well, folder: Path) -> None:
    for key, names in FIGURES.items():
        for n in names:
            p = folder / n
            if p.is_file():
                well.figures[key] = str(p)
                break


def collect_wells(output_dir: Path) -> list[Well]:
    """Find every analysed well under an output directory."""
    root = Path(output_dir)
    if not root.is_dir():
        LOG.error("Output directory does not exist: %s", root)
        return []

    markers = ("metrics_curated.xlsx", "network_results.json",
               "rejection_log.xlsx", "processing_info.json")
    folders: set[Path] = set()
    for m in markers:
        for hit in root.rglob(m):
            folders.add(hit.parent)
    for ck in root.rglob("checkpoints"):
        if ck.is_dir():
            folders.add(ck.parent)

    wells: list[Well] = []
    for folder in sorted(folders):
        w = Well(path=folder, well=folder.name)
        parts = folder.parts
        # <project>/<date>/<chip>/<run>/<well>
        if len(parts) >= 5:
            w.run_id = w.run_id or parts[-2]
            w.chip_id = w.chip_id or parts[-3]
            w.date = w.date or parts[-4]
            w.project = w.project or parts[-5]

        load_checkpoint(w, folder)
        for name, fn in (("metrics_curated.xlsx", load_units),
                         ("rejection_log.xlsx", load_rejections),
                         ("network_results.json", load_network)):
            p = folder / name
            if p.is_file():
                fn(w, p)
        load_figures(w, folder)

        if w.sources or w.status != "unknown":
            wells.append(w)

    LOG.info("Found %d analysed well(s) under %s", len(wells), root)
    return wells


def attach_activity(wells: list[Well], activity_dir: Optional[Path]) -> dict:
    """Add genotype labels (and DIV) from activity-scan summaries.

    The pipeline output does not carry the plate's group names; the recording
    does, and the activity scan already extracted them. Matching on chip + well
    label lets a condition comparison work without a separate plate map.
    """
    if not activity_dir or not Path(activity_dir).is_dir():
        return {}
    by_key: dict[tuple[str, str], dict] = {}
    plating: dict[str, str] = {}
    for fp in Path(activity_dir).rglob("summary.json"):
        try:
            data = json.loads(fp.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        chip = str(data.get("chip_id", ""))
        for w in data.get("wells", []):
            if w.get("plating_date"):
                plating.setdefault(chip, str(w["plating_date"]))
            by_key[(chip, str(w.get("well_label", "")))] = w
            by_key[(chip, f"well{int(w.get('well_id', -1)):03d}")] = w

    matched = 0
    for w in wells:
        hit = by_key.get((w.chip_id, w.well))
        if hit is None:
            m = re.search(r"(\d+)", w.well)
            if m:
                hit = by_key.get((w.chip_id, str(int(m.group(1)) + 1)))
        if hit:
            w.group = w.group or str(hit.get("group", ""))
            matched += 1
    if matched:
        LOG.info("Matched %d well(s) to activity-scan group labels", matched)
    return plating


# Activity-scan metrics worth showing, in the order they read best. The scan
# measures the whole array before any sorting, so it answers a different
# question from the network analysis: where on the chip is there tissue, and is
# it firing — rather than what did the sorted units do.
ACTIVITY_METRICS = [
    ("active_fraction", "Active area", "%"),
    ("electrodes_active", "Active electrodes", ""),
    ("rate_mean_hz", "Mean rate (Hz)", ""),
    ("amplitude_mean_uv", "Mean amplitude (µV)", ""),
    ("occupied_area_mm2", "Occupied area (mm²)", ""),
    ("clustering_index", "Clustering", ""),
    ("array_coverage_pct", "Array scanned (%)", ""),
    ("total_spikes", "Spikes", ""),
]

ACTIVITY_FIGURES = [
    ("plate_overview.png", "Plate overview"),
    ("group_comparison.png", "By group"),
]


def collect_activity(activity_dir: Optional[Path]) -> list[dict]:
    """Read the activity-scan output into one record per scanned run.

    Returns [] when the folder is absent or holds nothing recognisable, so the
    caller can simply omit the section rather than special-casing it.
    """
    if not activity_dir or not Path(activity_dir).is_dir():
        return []

    runs: list[dict] = []
    for fp in sorted(Path(activity_dir).rglob("summary.json")):
        try:
            data = json.loads(fp.read_text())
        except (OSError, json.JSONDecodeError):
            LOG.warning("Could not read activity summary %s", fp)
            continue
        wells = data.get("wells") or []
        if not wells:
            continue

        folder = fp.parent
        figures = [(label, folder / name) for name, label in ACTIVITY_FIGURES
                   if (folder / name).is_file()]
        for w in wells:
            wid = w.get("well_id")
            if wid is None:
                continue
            w["_figures"] = [
                (label, folder / f"well{int(wid):03d}_{suffix}.png")
                for suffix, label in (("activity", "Activity map"),
                                      ("network", "Network activity"),
                                      ("functional", "Functional"))
                if (folder / f"well{int(wid):03d}_{suffix}.png").is_file()
            ]

        runs.append({
            "chip_id": str(data.get("chip_id", "")),
            "run_id": str(data.get("run_id", "") or folder.name),
            "recorded": data.get("recorded_at") or data.get("date") or "",
            "scan_seconds": data.get("scan_seconds"),
            "wells": wells,
            "figures": figures,
            "source": str(fp),
        })
    if runs:
        LOG.info("Activity scan: %d run(s), %d well(s)",
                 len(runs), sum(len(r["wells"]) for r in runs))
    return runs


def activity_value(well: dict, key: str) -> Optional[float]:
    """One activity metric, with the fraction rendered as a percentage."""
    v = well.get(key)
    if v is None or isinstance(v, bool):
        return None
    if not isinstance(v, (int, float)):
        return None
    return round(v * 100, 2) if key == "active_fraction" else v


def _parse_date(text: str):
    from datetime import datetime
    for fmt in ("%y%m%d", "%Y%m%d", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(text).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def assign_div(wells: list[Well], plating: Optional[dict] = None) -> str:
    """Give every well a timepoint, however much information is available.

    True DIV when a plating date is known; otherwise a ``DIV<n>`` path
    component; otherwise the session dates in order, so a longitudinal view
    still works and is labelled honestly as an ordering rather than as days.
    """
    plating = plating or {}
    resolved = 0
    for w in wells:
        m = re.search(r"DIV[_\-]?(\d+)", str(w.path), re.IGNORECASE)
        if m:
            w.div = int(m.group(1))
            resolved += 1
            continue
        sess = _parse_date(w.date)
        plate = _parse_date(plating.get(w.chip_id, ""))
        if sess and plate:
            w.div = (sess - plate).days
            resolved += 1
    if resolved:
        return "div"

    dates = sorted({w.date for w in wells if w.date})
    if len(dates) > 1:
        order = {d: i for i, d in enumerate(dates)}
        for w in wells:
            w.div = order.get(w.date)
        LOG.info("No plating date — using %d session dates in order as timepoints",
                 len(dates))
        return "session"

    runs = sorted({w.run_id for w in wells if w.run_id})
    if len(runs) > 1:
        order = {r: i for i, r in enumerate(runs)}
        for w in wells:
            w.div = order.get(w.run_id)
        return "run"
    return "none"


def available_metrics(wells: list[Well]) -> list[str]:
    """Canonical metrics actually present, in a sensible reporting order."""
    order = ["units", "firing_rate_hz", "amplitude_uv", "burst_rate_hz",
             "pct_spikes_in_bursts", "network_burstiness", "spikes_per_burst",
             "burst_duration_s", "interburst_interval_s", "synchrony",
             "presence_ratio", "isi_violations", "snr", "num_spikes",
             "units_rejected"]
    present = {k for w in wells for k in list(w.metrics) + ["units"] * (w.units is not None)}
    present |= {"units_rejected"} if any(w.units_rejected is not None for w in wells) else set()
    return [k for k in order if k in present]


def group_wells(wells: list[Well]) -> dict[str, list[Well]]:
    out: dict[str, list[Well]] = {}
    for w in wells:
        out.setdefault(w.group or "ungrouped", []).append(w)
    return out


def summarise(wells: list[Well]) -> dict[str, Any]:
    stats: dict[str, int] = {}
    for w in wells:
        stats[w.status] = stats.get(w.status, 0) + 1
    total_units = sum(w.units or 0 for w in wells)
    return {
        "wells": len(wells),
        "status": stats,
        "total_units": total_units,
        "chips": sorted({w.chip_id for w in wells if w.chip_id}),
        "runs": sorted({w.run_id for w in wells if w.run_id}),
        "groups": sorted({w.group for w in wells if w.group}),
        "metrics": available_metrics(wells),
    }
