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

Binds to `127.0.0.1` by default. At the machine itself, open
<http://localhost:8000>. From anywhere else, forward the port over SSH — see
[section 4](#4-connecting-from-your-own-computer).

Override with `UI_HOST=0.0.0.0 ./run.sh` only if you have a reason to; the UI is
unauthenticated and can browse the filesystem.

---

## 4. Connecting from your own computer

The UI runs on the analysis server and binds to `127.0.0.1`. You reach it by
forwarding a port over SSH — it is unauthenticated and can browse the server's
filesystem, so it should not be exposed on the network.

**Picking folders works the same from any client.** The folder button in the UI
lists directories *on the server* and returns *server* paths. It is a web page
talking to the server, so there is nothing to install and no difference between
Windows, macOS, and Linux.

### macOS / Linux

```bash
ssh -N -L 8000:127.0.0.1:8000 user@server
```

Leave it running, then open <http://localhost:8000>.

Use `127.0.0.1` rather than `localhost` in the `-L` argument: on some servers
`localhost` resolves to IPv6 first and the forward is refused. If port 8000 is
busy on your own machine, map a different one: `-L 9000:127.0.0.1:8000`.

### Windows

Windows 10 and 11 include OpenSSH, so in PowerShell or Windows Terminal the
command is identical:

```powershell
ssh -N -L 8000:127.0.0.1:8000 user@server
```

With **PuTTY** instead: Connection → SSH → Tunnels, Source port `8000`,
Destination `127.0.0.1:8000`, Local, **Add**, then connect.

Then open <http://localhost:8000>. Nothing else is required.

### Optional: the native file manager dialog

The **File manager** button in the folder picker opens the desktop's own chooser
(`zenity`, the dialog GNOME/Nautilus uses). It appears only when the server has a
display, because it is a real GUI window that opens on the server's screen.

| Situation | Native dialog | Built-in browser |
|---|---|---|
| Sitting at the lab machine | Yes | Yes |
| SSH tunnel, no X forwarding | No — hidden | Yes |
| SSH tunnel with X11 forwarding | Yes | Yes |

To get it remotely, forward X11 as well. The dialog then renders on your
computer while still browsing the **server's** filesystem, which is what you
want.

**macOS** — install [XQuartz](https://www.xquartz.org), then:

```bash
ssh -X -L 8000:127.0.0.1:8000 user@server
cd Orchestration-MEA && ./run.sh      # must start from this session
```

**Windows** — you need an X server:

* **MobaXterm** — easiest; bundles one and enables forwarding by default
* **VcXsrv** or **Xming** — start it, then `ssh -X user@server`
* **WSL2 on Windows 11** — WSLg is built in; SSH with `-X` from inside WSL

With PuTTY also tick Connection → SSH → X11 → *Enable X11 forwarding*.

`run.sh` must be launched from the forwarded session so it inherits `DISPLAY`.
A systemd service will not have it unless you add `Environment=DISPLAY=:0`.

X11 dialogs are noticeably laggy over a network. For everyday use the built-in
browser is faster and needs no setup — the native dialog is a convenience, not a
capability, and both return the same server paths.

---

## 5. Keep it running

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

## 6. Verify

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

## 7. First run through the UI

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
