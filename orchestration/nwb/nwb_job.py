#!/usr/bin/env python3
"""
Network analysis of one date via NWB: convert, then analyse from the NWB files.

Launched by the watcher in place of run_pipeline_driver.py when "Convert to NWB"
is on. Both steps write to this job's log, in the driver's format, so progress,
well status and reports read it unchanged.

    1. convert_date.py   (NWB environment)        raw .h5 -> <nwb-root>/<project>/<date>/... .nwb
    2. run_wells.py      (MEA-Analysis environment) one MEA-Analysis routine per well NWB
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", type=Path, help="Input date folder (read-only)")
    ap.add_argument("--output-dir", required=True, help="Analysis output root (MEA-Analysis --output-dir)")
    ap.add_argument("--nwb-root", type=Path, required=True, help="<output>/<project>/NWB")
    ap.add_argument("--nwb-python", required=True)
    ap.add_argument("--mea-python", required=True)
    ap.add_argument("--mea-repo", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--compression", default="gzip")
    ap.add_argument("--assay-subfolder", default="Network")
    ap.add_argument("--driver-options", required=True, help="Driver options as JSON")
    a = ap.parse_args()

    run_dir = a.run_dir.resolve()
    print(f"NWB route: converting {run_dir} into {a.nwb_root}, then analysing from the NWB files",
          flush=True)
    rc = subprocess.run([a.nwb_python, str(HERE / "convert_date.py"), "--run-dir", str(run_dir),
                         "--nwb-root", str(a.nwb_root), "--scratch", str(a.scratch),
                         "--assay-subfolder", a.assay_subfolder, "--compression", a.compression]).returncode
    if rc != 0:
        print(f"NWB conversion step exited with {rc}; analysing whatever was converted", flush=True)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(json.loads(a.driver_options), fh)
        opts_file = fh.name
    try:
        date_dir = a.nwb_root / run_dir.parent.name / run_dir.name
        return subprocess.run([a.mea_python, str(HERE / "run_wells.py"), "--nwb-date-dir", str(date_dir),
                               "--mea-repo", str(a.mea_repo), "--output-dir", a.output_dir,
                               "--driver-options", opts_file,
                               "--assay-subfolder", a.assay_subfolder]).returncode
    finally:
        Path(opts_file).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
