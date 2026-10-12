# Orchestration-MEA — session memory

Handoff notes for a new Claude session. Last updated 2026-10-12.

Read this first, then `README.md`, `docs/FIELD-NOTES.md` and `docs/USER-GUIDE.md`.

## What this project is

A web UI and orchestrator that watches the lab's MaxWell MEA recordings, queues
each date, runs the MEA-Analysis pipeline on it (optionally staged on a local
SSD), tracks per-well progress, and hands the results to an AI for a report.
The users are non-technical lab members.

- Repo: `https://github.com/hiteshkumar18/Orchestration-MEA`
- Lab machine: `benshalom-labtower1` (RTX 5090, 63 GB RAM)
- Main worktree: `/mnt/Vol20tb1/user_workspaces/hitesh/Orchestration-MEA`
- Live server: `mea-ui` on port 8000

## Standing rules from the user

- Input folders on the NAS (`/mnt/benshalom-nas/...`) are read-only. Never modify them.
- The SSD (`/home/s-user-b/mea_scratch`) is scratch only. Delete a job's scratch
  after it completes. Never touch other users' folders.
- Do not change MEA-Analysis (`/mnt/Vol20tb1/user_workspaces/hitesh/MEA-Analysis`).
- Keep the backend intact; nothing may break. Test on a separate test server
  (for example port 8766 with its own `--work-dir`), never on the live one on 8000.
- No new packages in the live `.venv`. Tests are stdlib `unittest` plus
  jsdom/puppeteer in `tests/node_modules`.
- When the user says "let's discuss", do not change the codebase.
- UI text is for non-technical users: plain language.
- Commit email: `hikumar@ucdavis.edu`.

## Branches

| Branch | Head | State |
|---|---|---|
| `main` | `fdfba83` | Holds everything. Work from here. |
| `feat/ai-reports` | `3c16281` | Merged (PRs #1, #2) |
| `feat/ui-redesign` | `5523956` | Merged (PRs #3, #4) |
| `feat/nwb-conversion` | `cd55259` | Merged through the dashboard branch (PR #5) |
| `feat/dashboard` | `43563b4` | Merged (PR #5) |

All five are on GitHub and there are no open pull requests. Cut a new branch
from `main` for any new work.

Worktrees on the lab machine:

- `Orchestration-MEA` → the main worktree; the live server runs from here
- `Orchestration-MEA-nwb` → `feat/nwb-conversion` (merged, no longer needed)
- `Orchestration-MEA-dash` → `feat/dashboard` (merged, no longer needed)

`origin/claude/memory-md-tasks-7ays59` is a cloud session's correction to this
file, written before PRs #4 and #5 were merged. This version replaces it, so
that branch can be deleted.

## What has been done

### Reports (2026-09-03 to 2026-09-16)
- Report generation with an optional AI-written summary; org-scoped API keys;
  clearer API errors.
- HTML reports restyled on the lab's figure-sheet layout, with an activity-scan view.
- `--explain`, with every metric traced to its source column.
- Metric mapping corrected against the real `network_results.json` at all three
  levels; analysis parameters are never reported as measurements; implausible
  values are flagged.

### Reliability on real data (2026-09-25 to 2026-10-02)
- Interpreter handling: `python3` resolves to the pipeline interpreter for the
  driver and its well subprocesses (per-interpreter shim); the resolved chain is
  logged at the top of every run.
- Queue: jobs left in flight by a previous process are retired or re-queued; a
  hung driver no longer blocks the queue; only one watcher runs at a time.
- Scanning: no walking of the input directory inside request handlers; back-off
  on a slow watch directory; already-dispatched folders are skipped.
- Unfinished `sorter_output` is cleared before a run so wells stop failing.
- Local SSD staging, with a corrected size estimate and the option to decline
  when scratch cannot afford it; staged results are copied back before a run is
  marked done.
- Operator control: a stop that really stops, and no arbitrary job killing.
- Startup warnings for stray pipeline processes and for placeholder values left
  in `config.env`.
- Lab-notebook explorer: any spreadsheet to figures and an HTML report.

### UI (2026-10-05 to 2026-10-07)
- Fixed the blank UI (a hook below `App`'s early returns) and added the missing
  Wells component.
- Per-project outputs, same-chip selection, spike sorting skipped by default.
- Control UI redesigned as a lab notebook: plain paper background, cool palette
  (navy ink, slate/teal/violet accents).
- Wells are classified from the driver log and never show "in progress" on a
  finished date.
- AI report instructions and a standard report command for any dates; the server
  writes a report kit into the output folder on every start.
- Docs: `docs/USER-GUIDE.md`, `docs/FIELD-NOTES.md`, `docs/DEPLOYMENT.md`,
  `docs/ACTIVITY_SCAN.md`, architecture diagrams.

### NWB route — `feat/nwb-conversion` (`cd55259`, 2026-10-09)
- Optional, off by default: Settings → "Convert to NWB first".
- `orchestration/nwb/convert_date.py` (separate `.venv-nwb`, created by
  `setup-nwb.sh`) splits each well, converts it with the vendored Braingeneers
  converter, validates it against the source, then moves it to
  `<output>/<project>/NWB/<project>/<date>/<chip>/Network/<run>/wellNNN.nwb`.
- `run_wells.py` runs MEA-Analysis's per-well routine on each NWB file, in the
  driver's own log format, so progress, Wells and reports work unchanged.
- `routine_shim.py` works around a `read_nwb(load_if_exists=True)` incompatibility
  without modifying MEA-Analysis.
- Vendored converter changes are listed in `orchestration/nwb/vendor/VENDOR.md`.
- Verified end to end on 260818 (21 wells): signal identical to the raw file,
  units identical per well. See `docs/NWB.md`.

### Dashboard — `feat/dashboard` (`43563b4`, 2026-10-11)
- New default Dashboard tab: what needs attention, what is running with progress
  and a time-left estimate, machine health, and every run ever made.
- `history.py`: permanent run history in `work_dir/run_history.sqlite`.
- `rundetail.py`: per-well outcomes and NWB steps parsed from a run's log.
- `monitor.py`: CPU, memory, GPU, disks and pipeline processes from a background
  sampler.
- API: `/api/overview`, `/api/system`, `/api/history`, `/api/history/{id}`.
- UI: run page at `#run/<id>`; Details on Progress rows.
- All tests passed: `npm test` (including `dashboard_ui.js`), 51 stdlib unittests
  in `tests/python`, puppeteer end-to-end, and a real 260818 run.

## The 2026-10-07 crash

The server was killed by an out-of-memory failure. 260903 well
`M07301/000097/well000` detected 725 million spikes (a noisy well), and loading
them for network-burst analysis used up the 63 GB of RAM while 261003 was
running alongside. Re-running 260903 unchanged will very likely fail the same way.

## State of the lab machine on 2026-10-12

The machine was rebooted to fix a GPU "Driver/library version mismatch".

- GPU works again (`nvidia-smi` shows the RTX 5090, driver 595.99.02).
- `mea-ui` is **not running**; nothing listens on port 8000. It was a transient
  `systemd-run` unit, which does not survive a reboot.
- 59 GB of RAM free; no pipeline processes running.
- Test outputs still present: `/mnt/Vol20tb2/hitesh_mea_analysis/dash_test` and
  `nwb_test`.
- SSD scratch `/home/s-user-b/mea_scratch/IPN_Organoids_08142026_PVS/260903`
  (139 GB) holds 9 finished wells that were never copied back.

## Still to do

On the lab machine (a cloud session cannot reach it — see below):

1. Start `mea-ui` on port 8000 from `main` with `OOMPolicy=continue`, so that one
   well running out of memory does not stop the server.
2. Reset the failed `261003::network` step with `POST /api/runs/reset`, then queue
   260919, 260930 and 261003 with `POST /api/queue` (`rerun=false`). Hold 260903.
3. Delete the test outputs `dash_test` and `nwb_test`. The user approved this
   before the reboot; confirm once more before deleting.
4. Decide 260903: skip the noisy well, or run the date alone. Keep its SSD scratch
   until that is decided.

In the repository:

5. A guard against the 260903 failure. Not designed yet. The spike count is only
   known inside MEA-Analysis's per-well routine, which must not be changed, so
   the guard belongs in the orchestrator: for example a per-well memory cap
   through a cgroup or `systemd-run`. It has to be tested on the lab machine.
6. DANDI upload: the subject and lab metadata must come from the user.
7. Housekeeping: delete `origin/claude/memory-md-tasks-7ays59`, and remove the
   two merged worktrees once nothing in them is needed.

Finished since the last update: every feature branch is merged into `main`
(PRs #1 to #5, the last on 2026-10-12).

## What a cloud session can and cannot do

A cloud session works from a clone of the GitHub repository. It has no access to
the NAS recordings, the output volume, the SSD scratch, MEA-Analysis, the GPU or
the live server.

- It can do code, tests and docs: `npm test` in `tests/` and the stdlib unittests
  in `tests/python` need none of the lab data.
- It cannot do items 1 to 4, test the guard in item 5, or make any run on real
  recordings. Those need a session on `benshalom-labtower1`.
- It only sees branches that are pushed. `main` on GitHub has everything.
