#!/usr/bin/env python3
"""
Convert one recording-date folder's Network recordings to NWB, one file per well.

Runs in the NWB environment (.venv-nwb: NeuroConv, PyNWB). For every
<date>/<chip>/Network/<run>/data.raw.h5 under the input folder:

  1. split one well at a time into local scratch (vendor/split_maxtwo_by_well.py)
  2. convert it to NWB (vendor/convert_maxone_to_nwb.py: gzip, electrode positions)
  3. validate the NWB against the source (shape, scaling, positions) and only then
     move it into place
  4. delete the scratch copy

Output layout (read by MEA-Analysis exactly like the raw layout):

  <nwb-root>/<project>/<date>/<chip>/Network/<run>/wellNNN.nwb
  <nwb-root>/<project>/<date>/<chip>/Network/<run>/wellNNN.nwb.json   provenance + validation
  <nwb-root>/<project>/<date>/<chip>/Network/<run>/.metadata          run id / project / chip

A well whose NWB already exists with a matching manifest (same source size and
modification time, same converter settings) is reused, not converted again.

The input folder is only read. Nothing is written outside --nwb-root and --scratch.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
CONVERTER_ID = "orchestration-mea/vendored-2026-10-08b"   # bump when output changes


def log(msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] NWB: {msg}", flush=True)


def find_network_recordings(run_dir: Path, assay: str, max_depth: int = 6) -> list[Path]:
    base = len(run_dir.parts)
    out = []
    for cur, dirs, files in os.walk(run_dir):
        depth = len(Path(cur).parts) - base
        dirs[:] = [] if depth >= max_depth else [d for d in dirs if not d.startswith(".")]
        if "data.raw.h5" in files and assay in Path(cur).parts:
            out.append(Path(cur) / "data.raw.h5")
    return sorted(out)


def wells_of(h5_path: Path) -> list[str]:
    import h5py
    with h5py.File(h5_path, "r") as f:
        if "wells" in f:
            return sorted(f["wells"].keys())
    return ["well000"]


def source_identity(p: Path) -> dict:
    st = p.stat()
    return {"path": str(p), "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def reusable(target: Path, src: dict, settings: dict) -> bool:
    man = target.with_name(target.name + ".json")
    if not (target.is_file() and man.is_file()):
        return False
    try:
        m = json.loads(man.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return (m.get("validated") is True and m.get("source", {}).get("size") == src["size"]
            and m.get("source", {}).get("mtime_ns") == src["mtime_ns"]
            and m.get("settings") == settings and target.stat().st_size == m.get("nwb_size"))


def run(cmd: list[str], env: dict) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = (p.stdout + p.stderr).strip()
    return p.returncode, out


def validate(nwb: Path, split_file: Path) -> dict:
    """The NWB must hold exactly the source signal's shape, scaling and positions."""
    import h5py
    from pynwb import NWBHDF5IO
    with h5py.File(split_file, "r") as f:
        raw = None

        def find(name, obj):
            nonlocal raw
            if raw is None and name.endswith("groups/routed/raw") and isinstance(obj, h5py.Dataset):
                raw = obj.shape
        f.visititems(find)
    if raw is None:
        raise RuntimeError("source has no routed raw dataset")
    n_ch_src, n_samp_src = raw            # MaxWell stores channels x samples
    with NWBHDF5IO(str(nwb), "r") as io:
        f = io.read()
        es = f.acquisition["ElectricalSeries"]
        n_samp, n_ch = es.data.shape
        cols = set(f.electrodes.colnames)
        conversion = float(es.conversion)
    problems = []
    if (n_samp, n_ch) != (n_samp_src, n_ch_src):
        problems.append(f"shape {n_samp}x{n_ch} != source {n_samp_src}x{n_ch_src}")
    if not {"rel_x", "rel_y"} <= cols:
        problems.append("electrode positions (rel_x/rel_y) missing")
    if not conversion > 0:
        problems.append("no signal scaling")
    if problems:
        raise RuntimeError("; ".join(problems))
    return {"samples": n_samp, "channels": n_ch, "conversion_to_volts": conversion}


def recording_start_iso(split_file: Path, well: str) -> str:
    """When the recording started, from MaxWell's start_time (ms since epoch).

    Without it the converter stamps the NWB with the conversion time, which is
    wrong for DANDI. Empty string when the file does not record it."""
    import h5py
    try:
        with h5py.File(split_file, "r") as f:
            recs = f["wells"][well] if "wells" in f and well in f["wells"] else None
            for rec in (recs.values() if recs is not None else []):
                if "start_time" in rec:
                    ms = int(rec["start_time"][()].ravel()[0])
                    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        pass
    return ""


def write_run_metadata(run_out: Path, run_id: str, project: str, chip: str) -> None:
    """MEA-Analysis reads run id, project and chip from this file next to the input."""
    cfg = configparser.ConfigParser()
    cfg["properties"] = {"runid": run_id, "project_title": project}
    cfg["runtime"] = {"chipid": chip}
    text_path = run_out / ".metadata"
    with open(text_path, "w") as fh:
        cfg.write(fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="Input date folder <project>/<date> (read-only)")
    ap.add_argument("--nwb-root", type=Path, required=True, help="<output>/<project>/NWB")
    ap.add_argument("--scratch", type=Path, required=True, help="Local scratch for per-well split files")
    ap.add_argument("--assay-subfolder", default="Network")
    ap.add_argument("--compression", choices=["gzip", "maxwell"], default="gzip")
    ap.add_argument("--plugin-path", default=os.environ.get("HDF5_PLUGIN_PATH")
                    or str(Path.home() / "hdf5_plugin_path_maxwell"))
    a = ap.parse_args()

    run_dir = a.run_dir.resolve()
    project, date = run_dir.parent.name, run_dir.name
    out_root = a.nwb_root.resolve() / project / date
    try:
        out_root.relative_to(run_dir)
        log(f"refusing: output {out_root} is inside the input folder")
        return 2
    except ValueError:
        pass

    env = dict(os.environ, HDF5_PLUGIN_PATH=a.plugin_path, PYTHONPATH=str(VENDOR))
    settings = {"converter": CONVERTER_ID, "compression": a.compression}
    recs = find_network_recordings(run_dir, a.assay_subfolder)
    if not recs:
        log(f"no {a.assay_subfolder} recordings under {run_dir}")
        return 0

    scratch = a.scratch.resolve() / f"nwb-split-{project}-{date}-{os.getpid()}"
    started = time.time()
    done = reused = failed = 0
    try:
        for h5 in recs:
            chip, run_id = h5.parts[-4], h5.parts[-2]
            run_out = out_root / chip / a.assay_subfolder / run_id
            run_out.mkdir(parents=True, exist_ok=True)
            write_run_metadata(run_out, run_id, project, chip)
            src = source_identity(h5)
            try:
                wells = wells_of(h5)
            except Exception as exc:  # noqa: BLE001
                log(f"NWB conversion failed for {chip}/{run_id}: cannot read wells ({exc})")
                failed += 1
                continue
            for well in wells:
                target = run_out / f"{well}.nwb"
                if reusable(target, src, settings):
                    log(f"reused {target}")
                    reused += 1
                    continue
                t0 = time.time()
                work = scratch / f"{chip}_{run_id}_{well}"
                shutil.rmtree(work, ignore_errors=True)
                work.mkdir(parents=True)
                partial = run_out / f".{well}.nwb.partial"
                try:
                    rc, out = run([sys.executable, str(VENDOR / "split_maxtwo_by_well.py"),
                                   "--input-file", str(h5), "--output-dir", str(work),
                                   "--output-manifest", str(work / "manifest.json"),
                                   "--well-source", well, "--well-manifest", str(work / "well.json")], env)
                    split_files = sorted(work.glob("*.raw.h5"))
                    if rc != 0 or not split_files:
                        raise RuntimeError("split failed: " + (out.splitlines()[-1] if out else f"exit {rc}"))
                    split_file = split_files[0]
                    partial.unlink(missing_ok=True)
                    start_iso = recording_start_iso(split_file, well)
                    rc, out = run([sys.executable, str(VENDOR / "convert_maxone_to_nwb.py"),
                                   *(["--session-start-time", start_iso] if start_iso else []),
                                   "--input-file", str(split_file), "--output-file", str(partial),
                                   "--compression", a.compression,
                                   "--session-identifier-prefix", f"{project}-{date}-{chip}-{run_id}-{well}",
                                   "--session-description",
                                   f"MaxWell Network recording {project} {date} chip {chip} run {run_id} {well}"],
                                  env)
                    if rc != 0 or not partial.is_file():
                        raise RuntimeError("convert failed: " + (out.splitlines()[-1] if out else f"exit {rc}"))
                    facts = validate(partial, split_file)
                    os.replace(partial, target)
                    manifest = {
                        "source": src, "well": well, "chip": chip, "run": run_id,
                        "project": project, "date": date, "settings": settings,
                        "validated": True, "validation": facts, "nwb_size": target.stat().st_size,
                        "seconds": round(time.time() - t0, 1),
                        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    }
                    target.with_name(target.name + ".json").write_text(json.dumps(manifest, indent=2))
                    done += 1
                    log(f"converted {chip}/{run_id}/{well} -> {target} "
                        f"({facts['channels']} ch, {facts['samples']} samples, "
                        f"{target.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.0f} s)")
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    partial.unlink(missing_ok=True)
                    log(f"NWB conversion failed for {well} in {h5}: {exc}")
                finally:
                    shutil.rmtree(work, ignore_errors=True)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    log(f"done in {time.time() - started:.0f} s: {done} converted, {reused} reused, {failed} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
