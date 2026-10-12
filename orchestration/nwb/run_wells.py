#!/usr/bin/env python3
"""
Analyse every well NWB file of one date with MEA-Analysis's per-well routine.

Runs in MEA-Analysis's environment and does what run_pipeline_driver.py does for
raw .h5 files — one routine subprocess per well, the same options, the same log
lines — for NWB files, which the driver skips. The per-well options come from
MEA-Analysis's own config_loader, so they match a driver launch exactly.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from argparse import Namespace
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def log(level: str, msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S},000] {level}: {msg}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nwb-date-dir", type=Path, required=True,
                    help="<output>/<project>/NWB/<project>/<date>")
    ap.add_argument("--mea-repo", type=Path, required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--driver-options", type=Path, required=True,
                    help="JSON file of driver options (Orchestration-MEA driver_options)")
    ap.add_argument("--assay-subfolder", default="Network")
    a = ap.parse_args()

    sys.path.insert(0, str(a.mea_repo))
    from config_loader import build_extra_args, load_config, resolve_args  # noqa: E402

    opts = json.loads(a.driver_options.read_text())
    opts["output_dir"] = a.output_dir
    ns = Namespace(**opts)
    resolved = resolve_args(ns, load_config(getattr(ns, "config", None)))
    extra = build_extra_args(resolved, ns)

    started = time.time()
    files = sorted(p for p in a.nwb_date_dir.rglob("well*.nwb") if a.assay_subfolder in p.parts)
    if not files:
        log("CRITICAL", "No data files found (.nwb) under " + str(a.nwb_date_dir))
        return 0
    for nwb in files:
        well = nwb.stem
        log("INFO", f"Processing : {nwb} recording : rec0000 well_id : {well}")
        cmd = [sys.executable, str(HERE / "routine_shim.py"), str(a.mea_repo), str(nwb),
               "--rec", "rec0000", "--well", well, *shlex.split(extra)]
        log("INFO", "[DRIVER] Launching: " + " ".join(shlex.quote(c) for c in cmd))
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            log("ERROR", f"Subprocess failed for {well} in {nwb}")
            log("ERROR", f"Exit Code: {rc}")
    log("INFO", f"Pipeline driver completed in {time.time() - started:.2f} seconds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
