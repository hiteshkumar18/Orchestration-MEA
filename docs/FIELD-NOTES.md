# Field notes

What this system does on real hardware with real data, what went wrong, and why
each fix is the shape it is. Written after a week of running the IPN organoid
dataset end to end on `benshalom-labtower1`.

Read this before changing performance behaviour or the watcher's control flow.
Most of it was learned the expensive way, and several of the obvious changes are
obvious *and wrong* for reasons that are not visible in the code.

---

## 1. Where the time actually goes

Measured across six wells of `260904`, output on a local disk:

| Phase | Share | Hardware | Notes |
|---|---|---|---|
| 1 — Preprocessing | ~16% (~9 min) | CPU + disk | Writes the float32 binary. Runs 16 workers. |
| 2 — Spike sorting | ~46% (~26 min) | GPU + disk | Kilosort4. Two full passes over the binary. |
| 3 — Analyzer | ~37% (~21 min) | **one CPU core** | Waveforms, quality metrics. See §6. |

About **56 minutes per well** on the heavy recordings. Short recordings
(`260818`, `260825`, `260828`) run at 1.7–3.5 min/well — the spread between
folders is recording *length*, not anything about the pipeline.

### The single most important fact

The pipeline writes an **uncompressed float32 copy of the whole recording** to
`<output-dir>/<...>/<well>/binary/`, and Kilosort reads it back two or more
times. Measured: a 26 GB `.h5` produced an **81 GB** binary for one well.

`--clean-up` deletes it afterwards, so it is pure scratch — but it is scratch
written to wherever `--output-dir` points.

**With the output directory on the NAS**, that meant ~324 GB crossing CIFS per
well. The GPU sampled at **0% utilisation for two solid minutes** while a job had
been "running" for three hours. The machine was not computing; it was waiting on
the network.

| | Output on NAS | Output on local disk |
|---|---|---|
| Heavy folder | ~90 min/well | ~57 min/well |
| 12 activity scans | 11 min | 4 min |
| Directory listing of the input mount, during a job | **2770 s** | 5–30 s |

That last row is the tell. The same `ls`-equivalent took 8 seconds when idle and
46 minutes while a sorting job ran. If you ever see scan times explode, look for
something writing bulk data to the same mount.

**Current setting:** output is on `/mnt/Vol20tb2/hitesh_mea_analysis/mea_outputs`.
Raw data is still read from the NAS — that is one sequential read of a compressed
file per well, roughly 9 minutes, and moving it would buy little.

### Local staging (`stage_locally`)

If the output directory ever has to be a network path again, `stage_locally`
runs the job against local scratch and copies results back afterwards. It is
**off by default** and only worth turning on in that situation — with output
already local it adds a pointless copy.

It estimates the working set as **3.5 × the largest recording in the run**,
measured against the *whole* `.h5`, not one well's share of it. The first
version divided by the well count and underestimated by six times (13 GB
predicted against 81 GB actual). The `.h5` is compressed; its size on disk tells
you very little about the uncompressed working set.

It declines rather than fills a disk: if staging would take the volume below
`stage_min_free_gb` (200 by default), it logs why and runs against the output
directory as normal.

---

## 2. Concurrency

`max_concurrent_network` was 1, with a comment saying two Kilosort jobs would
exhaust a single GPU. Measured on the RTX 5090 during the sorting phase:

* **peak VRAM 7.7 GB** of 31.4 — about a quarter of the card
* **mean utilisation 37%**, oscillating `1% → 100% → 1%` as it waits for data

So two jobs fit on memory, and the second mostly fills the first one's idle
gaps. Better still, one job's CPU-only Phase 3 overlaps another's GPU Phase 2.

**Currently set to 2.** Three may also fit (23 GB, ~110% utilisation) but has
not been tried. If you raise it, watch `free -g`: each job's preprocessing runs
16 workers, and RAM is the resource with the least headroom data behind it.

Do not restore the old "raise only with multiple GPUs" advice. It was written
before anything was measured and it is wrong for this card.

---

## 3. Failure modes seen in production

### Stale `sorter_output` — cost 13 of 48 wells

`mea_sorting.py` calls `si.run_sorter(..., remove_existing_folder=True)`, so
SpikeInterface runs `shutil.rmtree(sorter_output)` **with no error handling**. On
this network mount that raises:

```
OSError: [Errno 39] Directory not empty: 'sorter_output'
```

and the well exits 1. The pipeline resumes from its checkpoint and reaches the
same line within ~30 seconds on every retry, so a well that hits this fails
identically forever.

Confirmed, not inferred: `--clean-up` survives the same operation on the same
mount only because it passes `ignore_errors=True`, and the leftover empty
`binary/` directories prove `rmtree` is emptying directories it then cannot
remove.

**Fix:** `clear_stale_sorter_output()` renames the folder aside before dispatch
and deletes the renamed copy best-effort. A rename does not require the directory
to be empty, so it works whatever is holding those entries. Only wells whose
checkpoint is **below `SORTING_COMPLETE` (stage 4)** are touched — at or above
it the pipeline reads `sorter_output` back to resume.

### Orphaned processes — caused the above, repeatedly

`pkill -f run_pipeline_driver` kills the driver and **leaves every per-well
subprocess running**, reparented to init. They keep writing to the output tree,
and a fresh server then queues the same folders — two processes creating and
deleting the same `sorter_output`.

To stop everything by hand:

```bash
pkill -f run_pipeline_driver && sleep 2 && pkill -f mea_analysis_routine
```

Better: use **Stop & cancel** in the UI, which kills process groups properly.

The server now warns at startup about any pipeline process it did not start,
with a ready-made `kill` command. It reports, never kills — a long sort is
expensive to discard, and a matching process might be someone else's.

### Two watchers in one process

Saving configuration replaced `_watcher` without stopping the old one, and
`get_watcher()` was an unguarded `if None: create` while FastAPI serves requests
from a thread pool. Two watchers meant two scan loops and two `StateStore`
instances writing the same file: entries clobbered each other (runs vanished from
the UI) and `watcher_state.tmp` raced into `FileNotFoundError`.

Both closed. `_flush()` also writes to a per-process, per-thread temp name now,
so concurrent writers cannot delete each other's file mid-rename.

### Scan storms

`/api/status` is polled every 2 s and called `candidate_runs()`, which `rglob`'d
every recording folder — twice per folder, once per enabled job. On this NAS that
is a full recursive walk of the dataset every two seconds. The endpoint took
longer to answer than the poll interval, the thread pool filled with overlapping
walks, and the UI stopped updating entirely.

Three changes: `/api/status` never walks (serves the scan loop's cache, returns
`None` while a first scan runs); `jobs_for()` walks once and partitions by assay
instead of once per job; and **folders whose work is already claimed are never
deep-read again**. Steady state is now `0 of 12 folder(s) needed a full read`.

A fourth change was a mistake worth recording: an adaptive back-off that slept as
long as the last scan took. On a contended mount that measured contention and
scheduled another equally long walk — a feedback loop. It is capped at
`max_poll_seconds` now, and the real fix was not walking at all.

### The watchdog killing healthy jobs

Two separate errors here, both mine.

`stall_minutes` was 45. During the scan storms, jobs starved of I/O went quiet
for longer than that and were killed as stuck. Now **120 minutes**, and the
message no longer asserts the GPU is at fault — it lists both possibilities and
points at the log.

`max_runtime_hours` was 12. An 18-well folder at ~57 min/well is a 17-hour job
working perfectly; five were destroyed by this. **Now 0 — disabled.** Whether a
job is stuck is answered by it going quiet, which is evidence. Elapsed time is
evidence only that the work is large.

### NVIDIA driver/library mismatch

`nvidia-smi` reporting `Driver/library version mismatch` after a driver upgrade
does not make CUDA fail cleanly — **it makes CUDA calls block**. Kilosort hangs,
holds the GPU slot, and nothing in any log explains it. `rmmod` fails while the
desktop session holds `nvidia_drm`, so this needs a reboot.

`check_gpu()` now probes before a Network job takes the slot, with its own 90 s
deadline, and fails the job with a readable message instead of hanging.
`GET /api/gpu` gives the same answer on demand.

---

## 4. Things that look like bugs and are not

**GPU at 0%.** Normal during Phase 1 and Phase 3. Only Phase 2 uses the GPU.
Sample over a minute and check which phase the log is in before concluding
anything.

**Seventeen identical `mea_analysis_routine.py` processes.** One well plus its
16 preprocessing workers. `n_jobs=16` is hardcoded in `mea_preprocessing.py`.

**Silence in the orchestration log for hours.** It only logs job start and
finish. Per-well progress is in the driver log and the checkpoints.

**`ValueError: n_samples=2 should be >= n_clusters=6`.** A well with essentially
no spikes. Real biology, not a fault. Expect roughly 1 in 20.

**A run marked Complete with "N of M well subprocess(es) failed".** Correct: the
job finished, and some wells failed. The row note is coloured when it says
`failed`.

**`ps %cpu`** is a lifetime average, not an instantaneous reading. A process at
28% has used 28% of one core *since it started*.

---

## 5. Debugging playbook

```bash
# Is anything actually running, and is it ours?
ps -eo pid,ppid,etime,cmd | grep -E "run_pipeline_driver|mea_analysis_routine" | grep -v grep

# What does the server think is happening?
curl -s localhost:8000/api/status | python3 -c "import sys,json;d=json.load(sys.stdin);\
print('running:',d['running']);[print('%-8s %-13s %-9s %s'%(r['run'],r['job_label'],r['status'],\
r.get('error') or r.get('detail') or '')) for r in d['runs']]"

# Per-well truth for one folder (path= the INPUT folder)
curl -s "localhost:8000/api/runs/checkpoints?path=/path/to/input/260904" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['summary'])"

# Can spike sorting run at all?
curl -s "localhost:8000/api/gpu?refresh=true"

# Which phase is the current well in?
ls -t <output>/orchestration_logs/*_network_*.log | head -1 | xargs tail -n 20

# Phase timings across a whole folder
ls -t <output>/orchestration_logs/260904_network_*.log | head -1 \
  | xargs grep -E "Phase 1|Phase 2\]|Phase 3|Sorting finished"

# Is the GPU busy, over time rather than one sample?
for i in $(seq 1 24); do nvidia-smi --query-gpu=memory.used,utilization.gpu \
  --format=csv,noheader; sleep 5; done

# How big is the working set right now?
find <output> -type d -name binary -exec du -sh {} \;
```

### Re-running selectively

Two layers decide what happens:

1. **The state file** decides whether a folder is dispatched at all.
   `CLAIMED = {detected, dispatched, running, done, failed}` — a claimed folder
   is skipped entirely. Note **`failed` is claimed**, so a failed job never
   re-runs on its own; clear it first (per-row ↻, or
   `POST /api/runs/reset-all {"which":"failed"}`).
   `interrupted` is *not* claimed, so jobs cut short by a restart resume
   automatically.

2. **The pipeline's checkpoints**, which live inside the output folder, decide
   which wells actually compute. `should_skip()` returns true at
   `REPORTS_COMPLETE`, so finished wells exit in seconds.

So re-queuing a folder costs a driver launch plus a few seconds per finished
well. Deleting the output folder discards the checkpoints and genuinely re-runs
everything.

---

## 6. Known, measured, not fixed

### The analyzer runs on one core of thirty-two

Phase 3 is ~37% of per-well time and is single-threaded. `mea_analyzer.py`
already has the plumbing:

```python
compute_kwargs = {'verbose': self.verbose}
if self.n_jobs is not None:
    compute_kwargs['n_jobs'] = int(self.n_jobs)
```

But `n_jobs` is only a Python-level argument of `MEARunOptions` — **no CLI flag
sets it**, so it is always `None` and SpikeInterface's default of 1 applies. By
contrast `mea_preprocessing.py` hardcodes a fallback of 16, which is why Phase 1
is the fast phase.

Fixing it needs about six lines in MEA-Analysis (`--n-jobs` in two argparse
blocks, pass-through in `MEARunOptions`, three entries in `config_loader.py`).
**That repo is deliberately not modified**, so this is left alone. There is no
external route: `set_global_job_kwargs()` is per-process and not persisted.

Estimated gain if it were done: Phase 3 from ~21 to ~5 min, so ~56 → ~40 min per
well.

### Other open items

* **OneDrive delivery** — discussed, not built. The architectural point: push
  finished reports with `rclone` after generation rather than mounting OneDrive
  and writing into it. A hung FUSE mount blocks every process that touches the
  path. Institutional tenants usually need admin consent for the app
  registration, which is the real blocker.
* **`/mnt/Vol20tb1` is at 99%** (332 GB free of 19 TB). Not used for anything
  here any more, but worth knowing.

---

## 7. Constraints that must hold

* **MEA-Analysis is never modified.** Everything here works around it: the
  `python3` shim, clearing `sorter_output`, local staging. That is the cost of
  the independence, and it is deliberate.
* **The input directory is read-only.** The watcher never writes into the folder
  it watches.
* **The API key comes from `ANTHROPIC_API_KEY` only** — never stored, logged, or
  accepted over HTTP.
* **The UI is unauthenticated** and binds 127.0.0.1. The SSH tunnel is the
  security boundary.
* **The model is never the source of a number in a report.** `narrate.py`
  validates every figure in the generated prose against the computed values and
  drops anything that does not match.

---

## 8. Testing the UI

The UI is one Babel-transformed `<script>` served as a static file. A runtime
error anywhere in it blanks the whole page, with nothing in the server log —
this happened twice, and both times the JSX parsed perfectly.

```bash
cd tests
npm install        # jsdom, react, react-dom, @babel/standalone
npm test
```

`render_ui.js` renders the page under jsdom with `fetch` stubbed, in the stopped
and running states, and fails if it comes out blank. `click_ui.js` opens the
Wells and Log panels, which is where the second failure was: `RunBlock` rendered
`<Wells>` and no such component existed.

**Run this after any change to `index.html`.** Parsing is not enough.

Two specific traps in that file:

* `App` has early returns. **Every hook must sit above them.** A `useEffect`
  added below them ran on later renders but not the first, which is
  "rendered more hooks than during the previous render" and unmounts everything.
* The configuration panel only renders when the watcher is **stopped**, and the
  control that reveals it is itself hidden while running.
