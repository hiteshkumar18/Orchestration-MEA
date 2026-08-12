# Deployment

Orchestration-MEA runs from a Python virtualenv. No Docker, no root, nothing
installed system-wide — everything lives inside the checkout.

---

## 1. Clone and set up

```bash
cd ~                       # or wherever you keep code
git clone https://github.com/<you>/Orchestration-MEA.git
cd Orchestration-MEA

./setup.sh                          # finds ../MEA-Analysis automatically
./setup.sh /path/to/MEA-Analysis    # or say where it is
```

`setup.sh` creates `.venv`, installs dependencies, writes `config.env`, and
verifies the link to the analysis repo:

```
Python 3.10  (/usr/bin/python3)
Creating virtualenv at .venv
Installing dependencies
MEA-Analysis: /home/you/MEA-Analysis
Verifying
  driver options mirrored: 39
  INFO    MEA-Analysis: /home/you/MEA-Analysis (main @ 41c05b95)
  INFO    Driver option contract: OK
```

**"Driver option contract: OK"** means this repo's understanding of
`run_pipeline_driver.py` matches the checkout. If upstream renames or adds a
flag, it is listed here instead of failing silently later.

If `python3 -m venv` fails on Debian/Ubuntu: `sudo apt install python3-venv`,
or use conda: `conda create -n mea python=3.10 && conda activate mea && pip install -r requirements.txt`.

---

## 2. Configure

Edit `config.env` (not committed):

```bash
MEA_REPO=/home/you/MEA-Analysis
UI_PORT=8000
WORK_DIR=/home/you/Orchestration-MEA/.mea-watcher
```

Input and output folders are set in the UI, not here — they change per
experiment.

---

## 3. Run

```bash
./run.sh
```

Binds to `127.0.0.1` by default. The UI is unauthenticated and can browse the
filesystem, so reach it over an SSH tunnel rather than exposing the port. From
your laptop:

```bash
ssh -N -L 8000:127.0.0.1:8000 user@server
```

Then open <http://localhost:8000>. Use `127.0.0.1` rather than `localhost` in
the `-L` argument — on some servers `localhost` resolves to IPv6 first and the
forward is refused.

---

## 4. Keep it running

`run.sh` in the foreground stops when you log out. Two options:

**tmux** — simplest:

```bash
tmux new -s mea './run.sh'     # Ctrl-b d to detach
tmux attach -t mea             # to come back
```

**systemd user service** — survives reboots, no root needed:

```bash
mkdir -p ~/.config/systemd/user
cp docs/orchestration-mea.service ~/.config/systemd/user/
$EDITOR ~/.config/systemd/user/orchestration-mea.service   # set WorkingDirectory

systemctl --user daemon-reload
systemctl --user enable --now orchestration-mea
systemctl --user status orchestration-mea
journalctl --user -u orchestration-mea -f
```

To keep it running when you are not logged in: `sudo loginctl enable-linger $USER`
(this one does need root, once).

---

## 5. Verify

```bash
# Imports and option mirror
.venv/bin/python -c "import sys;sys.path.insert(0,'orchestration');\
import watcher,api,checkpoints,activity_scan,driver_schema;\
print('OK ·',len(driver_schema.FIELDS),'options')"

# Activity scan on real data — no GPU, no MEA repo needed
.venv/bin/python orchestration/activity_scan.py /path/to/session \
  --output-dir /tmp/scan_test -v 2>&1 | head

# Per-well status of a previous pipeline run
.venv/bin/python orchestration/checkpoints.py /path/to/AnalyzedData
```

---

## 6. First run through the UI

1. **Setup → Folders** — input is the folder *containing* run folders; output is
   where the pipeline writes.
2. **Analyses** — enable Network and/or Activity scan. Keep **Concurrent Network
   jobs = 1** unless you have more than one GPU.
3. **Detection** — if the data was copied before you started, enable **Folders
   already here are ready** so it does not wait out the settle window.
4. **Dry run** first: confirm runs reach *Detected* and **Preview command** shows
   what you expect. Then turn it off and start for real.

---

## The Network analysis environment

This repo does not install the pipeline's dependencies. Spike sorting runs
inside whatever environment `run_pipeline_driver.py` is launched with, so that
checkout needs its own working install (Kilosort4, SpikeInterface, torch with
CUDA, and the MaxWell HDF5 plugin for reading raw traces).

By default the driver is launched with the same interpreter as the watcher. If
the pipeline lives in a different environment, set `driver` and `python` in the
saved job config (`.mea-watcher/job.json`) to that environment's paths.

The activity scan has no such dependency: it reads only uncompressed spike data,
so it needs neither a GPU nor the HDF5 plugin.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `No virtualenv found` | Run `./setup.sh` first |
| `Driver option contract: N difference(s)` | The MEA checkout's CLI changed — update `driver_schema.py` |
| `run_pipeline_driver.py not found` | `MEA_REPO` wrong in `config.env` |
| Browser shows "Failed to fetch" | The HTML was opened as a file — open `http://localhost:<port>` |
| SSH tunnel refused | Nothing listening yet, or the tunnel port does not match `UI_PORT` |
| Runs never leave *waiting* | Still copying, or a missing `finished=` marker — the row says which |
| Runs reprocessed after restart | `WORK_DIR` was not persistent |
| CUDA OOM | Two Kilosort jobs at once — keep concurrency at 1 and raise the GPU cooldown |
