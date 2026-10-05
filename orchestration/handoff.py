#!/usr/bin/env python3
"""
Prepare an AI report handoff for finished analyses.

This replaces the built-in report generator. Instead of rendering a report,
it writes a small folder that an AI assistant (Claude Code on this server) is
pointed at:

    <output>/AI_HANDOFF/<timestamp>/
        PROMPT.md        what to do, with the exact paths — give this to the AI
        skills.md        what the data is and the rules (orchestration/skills/skills.md)
        REQUIREMENTS.md  the study's requirements, typed in the UI
        MANIFEST.json    every result file found, per well
        report/          where the AI writes the report

Read-only with respect to the data: it only lists and reads result files, and
it refuses to write anywhere inside the input (watch) folder.

    python orchestration/handoff.py /path/to/output --requirements "..." \
        [--folder /input/260903 ...] [--activity-dir /path/to/ActivityScan]
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoints import read_checkpoints, summarise  # noqa: E402

LOG = logging.getLogger("mea.handoff")
HERE = Path(__file__).resolve().parent
DEFAULT_SKILLS = HERE / "skills" / "skills.md"
HANDOFF_DIRNAME = "AI_HANDOFF"

NETWORK_FILES = ("network_results.json", "unit_stats.csv", "processing_info.json",
                 "bad_channels.json", "raster_burst_plot_60s.png")


def _within(child: Path, parent: Path) -> bool:
    try:
        c, p = child.expanduser().resolve(), parent.expanduser().resolve()
    except (OSError, RuntimeError):
        return False
    return c == p or p in c.parents


def _under_any(path: str, folders: list[Path]) -> bool:
    return not folders or any(_within(Path(path), f) for f in folders)


def collect_network(output_dir: Path, folders: list[Path]) -> list[dict]:
    """One entry per well that the pipeline wrote a checkpoint for."""
    rows = read_checkpoints([output_dir])
    wells = []
    for r in rows:
        if not _under_any(r.get("data_dir") or "", folders):
            continue
        out = Path(r.get("output_dir") or Path(r["checkpoint_file"]).parent.parent)
        wells.append({
            "project": r["project"], "date": r["date"], "chip_id": r["chip_id"],
            "run_id": r["run_id"], "well": r["well"],
            "status": r["status"], "mode": r.get("mode"),
            "stage": r["stage_name"], "error": r["error"],
            "output_dir": str(out),
            "files": {f: str(out / f) for f in NETWORK_FILES if (out / f).is_file()},
            "recording": r.get("data_dir"),
        })
    return wells


def collect_activity(activity_dir: Optional[Path], folders: list[Path]) -> list[dict]:
    """One entry per ActivityScan run (each holds several wells)."""
    if not activity_dir or not activity_dir.is_dir():
        return []
    runs = []
    for summary in sorted(activity_dir.glob("*/*/*/summary.json")):
        try:
            data = json.loads(summary.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not _under_any(data.get("source") or "", folders):
            continue
        d = summary.parent
        runs.append({
            "date": d.parent.parent.name, "chip_id": data.get("chip_id"),
            "run_id": data.get("run_id"),
            "wells": [w.get("well_id") for w in data.get("wells", [])],
            "qc": {str(w.get("well_id")): w.get("qc") for w in data.get("wells", [])},
            "summary": str(summary),
            "per_electrode": str(d / "per_electrode.csv") if (d / "per_electrode.csv").is_file() else None,
            "recording": data.get("source"),
        })
    return runs


def _prompt(hdir: Path, output_dir: Path, activity_dir: Optional[Path],
            watch_dir: str, folders: list[Path], net: list[dict], act: list[dict]) -> str:
    summ = summarise([{"status": w["status"], "progress": 1.0, "well": w["well"],
                       "failed_stage": None, "error": w["error"]} for w in net]) if net else {}
    scope = ("\n".join(f"  - `{f}`" for f in folders) if folders
             else "  - all results in the output folder")
    lines = [
        "# MEA report request",
        "",
        f"Prepared {datetime.now():%Y-%m-%d %H:%M}. Work through this in order.",
        "",
        "1. Read `skills.md` in this folder completely. Its rules are binding.",
        "2. Read `REQUIREMENTS.md` in this folder — this is what the report must cover.",
        "3. Read `MANIFEST.json` in this folder — every result file to use, per well.",
        f"4. Write the report and everything it needs into `{hdir / 'report'}/` and nowhere else.",
        "",
        "## Paths",
        "",
        f"- This handoff: `{hdir}`",
        f"- Network analysis output (read-only): `{output_dir}`",
        f"- ActivityScan output (read-only): `{activity_dir or 'none'}`",
        f"- Raw recordings / input (**read-only — never write, move or delete anything here**): "
        f"`{watch_dir or 'not configured'}`",
        f"- Recording folders in scope:",
        scope,
        "",
        "## What was found",
        "",
        f"- Network wells: {len(net)}"
        + (f" ({summ.get('complete', 0)} complete, {summ.get('failed', 0)} failed, "
           f"{summ.get('running', 0) + summ.get('pending', 0)} unfinished)" if net else ""),
        f"- Processing modes: {', '.join(sorted({w['mode'] or 'unknown' for w in net})) or 'n/a'}",
        f"- ActivityScan runs: {len(act)} ({sum(len(r['wells']) for r in act)} wells)",
        "",
        "When finished, reply with the report path, a short summary of what it "
        "contains, and anything you could not do.",
        "",
    ]
    return "\n".join(lines)


def generate(output_dir: Path, requirements: str = "", *,
             watch_dir: str = "", activity_dir: Optional[Path] = None,
             folders: Optional[list[str]] = None, label: str = "",
             skills_path: Path = DEFAULT_SKILLS) -> dict[str, Any]:
    """Write a handoff folder and return its paths and counts."""
    output_dir = Path(output_dir).expanduser()
    if not output_dir.is_dir():
        raise ValueError(f"Output folder not found: {output_dir}")
    if watch_dir and _within(output_dir, Path(watch_dir)):
        raise ValueError("The output folder lies inside the input folder, which is "
                         "read-only; refusing to write a handoff there.")
    if not skills_path.is_file():
        raise ValueError(f"skills.md not found at {skills_path}")

    scope = [Path(f).expanduser() for f in (folders or [])]
    net = collect_network(output_dir, scope)
    act = collect_activity(Path(activity_dir) if activity_dir else None, scope)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{stamp}_{label}" if label else stamp
    hdir = output_dir / HANDOFF_DIRNAME / name
    (hdir / "report").mkdir(parents=True, exist_ok=False)

    shutil.copyfile(skills_path, hdir / "skills.md")
    req = requirements.strip() or ("No specific requirements were given. "
                                   "Produce the default report described in skills.md §4.")
    (hdir / "REQUIREMENTS.md").write_text("# Requirements\n\n" + req + "\n")
    (hdir / "MANIFEST.json").write_text(json.dumps({
        "created": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "activity_dir": str(activity_dir) if activity_dir else None,
        "input_dir_read_only": watch_dir or None,
        "folders_in_scope": [str(f) for f in scope],
        "network_wells": net,
        "activity_runs": act,
    }, indent=2))
    prompt = _prompt(hdir, output_dir, Path(activity_dir) if activity_dir else None,
                     watch_dir, scope, net, act)
    (hdir / "PROMPT.md").write_text(prompt)

    LOG.info("AI handoff written to %s (%d network well(s), %d activity run(s))",
             hdir, len(net), len(act))
    return {
        "dir": str(hdir),
        "prompt": str(hdir / "PROMPT.md"),
        "report_dir": str(hdir / "report"),
        "network_wells": len(net),
        "activity_runs": len(act),
        "instruction": f"cd {hdir} && claude \"Read PROMPT.md and do what it says.\"",
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Prepare an AI report handoff")
    p.add_argument("output_dir", type=Path, help="Pipeline --output-dir")
    p.add_argument("--requirements", default="", help="Requirements text (or @file)")
    p.add_argument("--folder", action="append", default=[],
                   help="Limit to these input recording folders (repeatable)")
    p.add_argument("--activity-dir", type=Path, default=None,
                   help="ActivityScan output (default: <output_dir>/ActivityScan)")
    p.add_argument("--watch-dir", default="", help="Input folder (read-only), for the prompt")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    req = a.requirements
    if req.startswith("@"):
        req = Path(req[1:]).read_text()
    act = a.activity_dir or (a.output_dir / "ActivityScan")
    res = generate(a.output_dir, req, watch_dir=a.watch_dir,
                   activity_dir=act if act.is_dir() else None, folders=a.folder)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
