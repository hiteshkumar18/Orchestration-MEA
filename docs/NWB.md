# NWB route

With **Settings → Convert to NWB first** on, the Network analysis of a recording
date runs in two steps instead of calling MEA-Analysis's batch driver:

1. **Convert** every Network recording to NWB, one file per well, on the output disk.
2. **Analyse** each well's NWB with MEA-Analysis's per-well routine, with the same
   options the driver would pass. Results land exactly where they do for raw files.

Off by default. The Activity scan is unchanged (it reads its own on-chip spike data).
The input folder is only ever read.

## Layout

```
<output>/<project>/NWB/<project>/<date>/<chip>/Network/<run>/
    well002.nwb          the well's signal, electrode positions and metadata
    well002.nwb.json     provenance: source size/mtime, settings, validation, time taken
    .metadata            run id, project, chip — read by MEA-Analysis
<output>/<project>/<date>/<chip>/Network/<run>/<well>/   analysis results (as before)
```

The project name appears again inside `NWB/` because MEA-Analysis takes the
project, date and chip from the folders above the file and builds the results path
from them. With this layout results are filed under `<output>/<project>/<date>/…`,
the same as the raw route, so progress, the Wells map and reports work unchanged.

## What each step does

`orchestration/nwb/nwb_job.py` — what the watcher launches for a date:

| Step | Script | Environment |
|---|---|---|
| Convert | `convert_date.py` | `.venv-nwb` (NeuroConv, PyNWB) |
| Analyse | `run_wells.py` → `routine_shim.py` → MEA-Analysis `mea_analysis_routine.py` | MEA-Analysis's |

Per well, `convert_date.py`:

1. splits the well out of the multi-well file into **local scratch** (the fast-disk
   folder), so the NAS is read once per well and nothing is written there;
2. converts it with the vendored Braingeneers converter;
3. **validates** the result against the source — same sample and channel count,
   signal scaling present, electrode positions present — and only then moves it into
   place (a half-written file is never left as `wellNNN.nwb`);
4. writes `wellNNN.nwb.json` and deletes the scratch copy.

A well whose NWB exists with a matching manifest (same source size and modification
time, same settings) is **reused**: re-analysing a date does not convert again.

Wells that cannot be converted are logged as `NWB conversion failed for …` and
counted like failed wells, so the date shows "N had problems".

## Format

- **Compression:** standard gzip by default, so any NWB reader and DANDI can open
  the signal without MaxWell's HDF5 plugin. *Settings → Advanced → NWB compression*
  can keep MaxWell's own compression instead (about 30 % smaller and faster to
  write, but every reader then needs MaxWell's plugin).
- **Electrode positions** are written as `rel_x` / `rel_y` (µm).
- **Signal** is stored as recorded (uint16) with the conversion to volts; reading it
  back gives exactly the same µV values as reading the raw `.h5`.

## Setup

```bash
./setup-nwb.sh        # once: creates .venv-nwb from requirements-nwb.txt
```

Then turn on **Convert to NWB first** under Settings.

## Known limitations

- **Workaround in `routine_shim.py`:** MEA-Analysis calls
  `si.read_nwb(path, load_if_exists=True)`, which its SpikeInterface (0.103) rejects.
  The shim drops that option before running the routine. Remove it once MEA-Analysis
  is fixed; no MEA-Analysis file is modified.
- **Channel ids** read from NWB look like `ch4 elec14598` instead of `4`, so unit ids
  in results differ in form from raw-route results (same channels).
- **No lab metadata yet:** the Braingeneers `ndx-cell-culture` extension (culture,
  lineage, people) is not installed; subject and experiment fields are minimal.
  DANDI upload will need these filled in.
- **Disk:** one more copy of the Network signal (gzip ≈ 0.8× the per-well raw size).
- **Stale sorting folders:** clearing a stale `sorter_output` before a re-run matches
  wells by their recording path, which on this route is the NWB file; with spike
  sorting on, a crashed sort may need clearing by hand.

## Vendored code

`orchestration/nwb/vendor/` holds three scripts from the Braingeneers workflows
repository, with four marked changes — see `vendor/VENDOR.md`.
