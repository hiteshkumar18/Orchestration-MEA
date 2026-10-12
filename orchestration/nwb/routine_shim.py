#!/usr/bin/env python3
"""
Run MEA-Analysis's per-well routine on an NWB file, unchanged.

    python routine_shim.py <mea-repo> <file.nwb> --rec rec0000 --well wellNNN [routine options]

WORKAROUND, remove when MEA-Analysis is fixed: mea_preprocessing.py calls
``si.read_nwb(path, load_if_exists=True)``, an option the installed SpikeInterface
(0.103) does not accept, so the routine cannot open NWB files. This wraps
``spikeinterface.full.read_nwb`` to drop that one option, then runs
mea_analysis_routine.py exactly as the driver would. No MEA-Analysis file is modified.
"""

import runpy
import sys
from pathlib import Path

import spikeinterface.full as si

_read_nwb = si.read_nwb


def read_nwb(file_path, *args, load_if_exists=None, **kwargs):  # noqa: ARG001
    return _read_nwb(file_path, *args, **kwargs)


si.read_nwb = read_nwb

repo = Path(sys.argv[1]).resolve()
routine = repo / "mea_analysis_routine.py"
sys.path.insert(0, str(repo))
sys.argv = [str(routine)] + sys.argv[2:]
runpy.run_path(str(routine), run_name="__main__")
