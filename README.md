# Orchestration-MEA

Automation and analysis layer for the MEA pipeline. Watches for completed
MaxWell recordings, runs the analysis automatically, and adds whole-array
ActivityScan extraction that the pipeline itself does not perform.

Drives [`MEA-Analysis`](https://github.com/hiteshkumar18/MEA-Analysis) without
modifying it.

---

## Relationship to MEA-Analysis

This repository **never imports** MEA-Analysis. It:

* invokes `run_pipeline_driver.py` as a subprocess, exactly as a person would,
* reads the output and checkpoint files the pipeline writes,
* and treats the recording folders as read-only.

That means the analysis repo stays untouched, the two version independently, and
this layer works against any MEA-Analysis checkout you point it at.

The cost of that independence is a contract in two places — the driver's
command-line options and its checkpoint format. Both are mirrored here and
**checked at startup**, so an upstream rename shows up as a warning instead of a
malformed command weeks later:

```
MEA-Analysis: /home/you/MEA-Analysis (main @ 41c05b95)
Driver option contract: OK
```

If it has drifted:

```
Driver option contract: 2 difference(s) vs run_pipeline_driver.py
  --raster-sort: in the UI but not in run_pipeline_driver.py (removed or renamed upstream)
  --brand-new-flag: new driver option not exposed in the UI
```

Use `--strict` to refuse to start in that state.

---

## Install

Runs from a virtualenv — no Docker, no root, nothing system-wide.

```bash
git clone https://github.com/<you>/Orchestration-MEA.git
cd Orchestration-MEA

./setup.sh                          # finds ../MEA-Analysis automatically
./setup.sh /path/to/MEA-Analysis    # or say where it is

./run.sh
```

`setup.sh` creates `.venv`, installs dependencies, writes `config.env`, and
verifies the link to the analysis repo. `run.sh` starts the UI on
`127.0.0.1:8000`.

The MEA checkout is located in this order: `--mea-repo` → `$MEA_REPO` →
`config.env` → a sibling `../MEA-Analysis`. An explicitly given path is never
silently overridden — if it has no driver, that is an error rather than a reason
to fall back to a different checkout.

Reach the UI over an SSH tunnel rather than exposing the port; it is
unauthenticated and can browse the filesystem:

```bash
ssh -N -L 8000:127.0.0.1:8000 user@server        # macOS/Linux, and Windows PowerShell
```

Folder selection works the same from any client — the picker lists directories
on the *server* and returns *server* paths, so there is nothing to install on
Windows, macOS, or Linux. Windows/PuTTY setup and the optional native file
manager dialog are covered in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#4-connecting-from-your-own-computer).

To keep it running: `tmux new -s mea './run.sh'`, or install the systemd user
service in [docs/](docs/orchestration-mea.service). See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## What it does

### Watcher

Detects when a recording folder has finished being written, then dispatches the
analyses. A folder is only dispatched when:

1. it contains a recording (`data.raw.h5`),
2. MaxWell wrote a `finished=` marker into `mxassay.metadata` (optional, checked
   per assay), and
3. **quiescence** — nothing under the folder changed across two polls separated
   by the settle window.

Quiescence is what actually proves a multi-GB copy finished; the MaxWell marker
only says the recording completed on the rig. Polling is used rather than
inotify because inotify is unreliable across NFS, CIFS, and bind mounts.

If the copy finished *before* you started watching, enable **Folders already
here are ready** to skip that wait for folders present at start. Later arrivals
still get the full window.

### Two independent analyses

|  | Network | Activity scan |
|---|---|---|
| Runs | `run_pipeline_driver.py` (external) | `orchestration/activity_scan.py` |
| Reads | `<chip>/Network/<run>/data.raw.h5` | `<chip>/ActivityScan/<run>/data.raw.h5` |
| Does | Kilosort4, curation, bursts | Whole-array maps, QC, network bursts |
| Needs | GPU; hours per chip | CPU only; seconds per chip |

They are enabled separately, tracked separately, and fail independently. Each
appears as its own row in the UI.

**Concurrency is per analysis type.** Kilosort4 reserves several GB of VRAM, so
two Network jobs on one GPU will OOM. The default limit is 1; extra jobs queue
and show as **Queued**. A configurable GPU cooldown covers the case where CUDA
has not released memory by the time the next job starts.

### ActivityScan analysis

A chip has ~26,400 electrodes but records ~1,020 at once, so the Network file you
spike-sort covers about 4% of the array. The scan is the only view of the rest.

MaxWell stores on-chip threshold-crossing spikes with electrode positions in
plain, uncompressed HDF5, so this needs **no spike sorting, no GPU, and not even
the MaxWell HDF5 plugin**. A 6 GB, 6-well recording processes in about 8 seconds.

Produces per-electrode activity and amplitude maps, per-well QC verdicts,
network burst detection and synchrony, functional connectivity, selection-quality
scoring against the electrodes the Network recording kept, and per-group
comparisons. See [docs/ACTIVITY_SCAN.md](docs/ACTIVITY_SCAN.md).

### True completion status

A subprocess exit code cannot tell "every well failed" from "one well hit an OOM
and the rest are fine". `checkpoints.py` reads the pipeline's own per-well
checkpoint files and reports the real verdict:

```bash
python orchestration/checkpoints.py /path/to/AnalyzedData
```

```
6 well(s): 5 complete, 1 failed, 0 running  →  PARTIAL
  FAIL M07420/000016/well005  Sorting
       ↳ Sorting: torch.OutOfMemoryError: CUDA out of memory...
```

The UI shows the same per-well breakdown behind the **Wells** button.

### Longitudinal trends

```bash
python orchestration/activity_trends.py /path/to/scan_output
```

Aggregates scans across sessions into maturation curves per experimental group,
per-well trajectories, and per-timepoint comparisons. Scans are a better basis
for this than Network recordings, which use a different electrode selection each
session and so compare different samples of the array.

---

## Command line

Everything is usable without the UI:

```bash
# Watch and dispatch
python orchestration/watcher.py --watch-dir /data/incoming --output-dir /data/out

# One-shot dry run
python orchestration/watcher.py --watch-dir /data/incoming --once --dry-run

# Activity scan
python orchestration/activity_scan.py /data/240605 --output-dir /data/scan_out

# Per-well status
python orchestration/checkpoints.py /data/out
```

---

## Layout

```
setup.sh             one-time: virtualenv, dependencies, config
run.sh               start the UI
config.env           per-machine settings (not committed)
orchestration/
  watcher.py         completion detection and dispatch
  api.py             FastAPI backend
  static/index.html  single-file UI, no build step
  driver_schema.py   mirror of the driver's CLI options
  mea_repo.py        locates MEA-Analysis, checks the contract
  checkpoints.py     per-well status from pipeline checkpoints
  activity_scan.py   whole-array ActivityScan analysis
  activity_trends.py cross-session aggregation
```

## Requirements

`fastapi`, `uvicorn`, `h5py`, `numpy`, `matplotlib` — installed by `setup.sh`
into `.venv`. The watcher and checkpoint reader are standard library only.

**The Network analysis is not a dependency of this repo.** Spike sorting runs in
whatever environment `run_pipeline_driver.py` is launched with, so that checkout
needs its own working install (Kilosort4, SpikeInterface, CUDA torch, and the
MaxWell HDF5 plugin). If the pipeline lives in a different environment, set
`driver` and `python` in `.mea-watcher/job.json` to that environment's paths.

The activity scan needs neither a GPU nor the HDF5 plugin — it reads only
uncompressed spike data.

## Known limitations

* The UI has no authentication — reach it over an SSH tunnel.
* Report/slide generation from pipeline output is not implemented yet.
* ActivityScan metrics are electrode-level, not sorted units; correlation and
  synchrony are computed within a recording block only, since electrodes in
  different blocks were never recorded simultaneously.
