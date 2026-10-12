#!/usr/bin/env bash
# One-time setup for NWB conversion: a separate environment in .venv-nwb with
# NeuroConv and PyNWB. Does not touch MEA-Analysis or its environment.
#
#   ./setup-nwb.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
PY="${PYTHON:-python3}"
echo "Creating .venv-nwb with $($PY --version)"
"$PY" -m venv .venv-nwb
.venv-nwb/bin/pip install --quiet --upgrade pip
echo "Installing NWB conversion packages (a few minutes)"
.venv-nwb/bin/pip install --quiet -r requirements-nwb.txt
echo "Checking MaxWell's HDF5 plugin (needed to read the raw recordings)"
.venv-nwb/bin/python - <<'PY'
from pathlib import Path
p = Path.home() / "hdf5_plugin_path_maxwell" / "libcompression.so"
if not p.exists():
    from neo.rawio.maxwellrawio import auto_install_maxwell_hdf5_compression_plugin
    auto_install_maxwell_hdf5_compression_plugin()
print("  plugin:", p, "OK" if p.exists() else "MISSING")
import neuroconv, pynwb  # noqa: F401
print("  NWB environment: OK")
PY
echo "Done. Turn on 'Convert to NWB' under Settings to use it."
