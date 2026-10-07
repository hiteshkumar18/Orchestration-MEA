# MEA Bench — user guide

**For lab members who want their MEA recordings analysed and turned into
reports.** No programming needed: you will copy a few commands once, then do
everything else by clicking in a web page.

What this tool does:

1. You choose which recording dates to analyse (or let it pick up new ones automatically).
2. It analyses every well — the **Network analysis** (spikes and network bursts) and the
   **Activity scan** (whole-chip activity maps) — on the lab's analysis computer.
3. You ask an AI assistant to write a **report** for the dates you care about.

Your raw recordings are **only ever read**, never changed or moved.

---

## Contents

- [Before you start](#before-you-start)
- [Part 1 — One-time setup (about 45 minutes)](#part-1--one-time-setup-about-45-minutes)
- [Part 2 — Open the control page](#part-2--open-the-control-page)
- [Part 3 — First-time settings](#part-3--first-time-settings)
- [Part 4 — Analyse recordings](#part-4--analyse-recordings)
- [Part 5 — Follow progress](#part-5--follow-progress)
- [Part 6 — Get a report from an AI](#part-6--get-a-report-from-an-ai)
- [Part 7 — Everyday tasks](#part-7--everyday-tasks)
- [Rules for sharing the computer](#rules-for-sharing-the-computer)
- [Troubleshooting](#troubleshooting)
- [Words used in this guide](#words-used-in-this-guide)

---

## Before you start

You need:

| What | Where to get it |
|---|---|
| An account on the lab's analysis computer (**benshalom-labtower1**) — a user name and password | The lab's computer administrator |
| Access to the two code repositories on GitHub: **Orchestration-MEA** and **MEA-Analysis** | Ask Hitesh to give your GitHub account access |
| Your own **port number** between 8001 and 8099 (any number nobody else uses) | Pick one and tell the lab, e.g. 8012 |
| Where your recordings are (the project folder on the lab NAS) | Your supervisor |

**How to type the commands in this guide.** Each grey box is one or more
commands. Copy it, paste it into the terminal window, press **Enter**, and wait
until the terminal is ready again (you see the prompt, ending in `$`). Replace
anything in `<angle brackets>` — including the brackets — with your own value,
e.g. `<your-name>` → `maria`.

**Open a terminal on your own computer**

- **Mac:** open **Terminal** (Applications → Utilities → Terminal).
- **Windows 10/11:** open **PowerShell** (Start menu → type *PowerShell* → open it).

---

## Part 1 — One-time setup (about 45 minutes)

You do this once. It installs your own copy of the tool on the analysis computer.

### 1.1 Log in to the analysis computer

In the terminal on your computer:

```bash
ssh <your-user>@benshalom-labtower1
```

The first time, it asks *"Are you sure you want to continue connecting?"* —
type `yes`. Then type your password (nothing appears while you type; that is
normal) and press **Enter**. You are now typing on the analysis computer.

> If `benshalom-labtower1` is not found, ask the administrator for its full
> address and use that instead. You may need to be on the university network
> or VPN.

### 1.2 Make your workspace folder

```bash
mkdir -p /mnt/Vol20tb1/user_workspaces/<your-name>
cd /mnt/Vol20tb1/user_workspaces/<your-name>
```

### 1.3 Download (clone) the two repositories

```bash
git clone https://github.com/hiteshkumar18/MEA-Analysis.git
git clone https://github.com/hiteshkumar18/Orchestration-MEA.git
```

If it asks for a GitHub user name and password: use your GitHub user name, and
as the password a **personal access token** (GitHub → Settings → Developer
settings → Personal access tokens). If you are unsure, ask Hitesh.

Both folders must sit side by side in your workspace:

```
/mnt/Vol20tb1/user_workspaces/<your-name>/
    MEA-Analysis/
    Orchestration-MEA/
```

### 1.4 Install the analysis software (about 30 minutes)

```bash
cd /mnt/Vol20tb1/user_workspaces/<your-name>/MEA-Analysis
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

This downloads several gigabytes. Wait until the prompt comes back. A last line
like `Successfully installed …` means it worked.

### 1.5 Set up the orchestrator

```bash
cd /mnt/Vol20tb1/user_workspaces/<your-name>/Orchestration-MEA
./setup.sh
```

It finds the analysis software from step 1.4 and adds two small pieces to it.
Near the end you should see:

```
Driver option contract: OK
pipeline interpreter: … — OK
```

### 1.6 Set your port number

Replace `<your-port>` with your number (e.g. 8012):

```bash
sed -i 's/^UI_PORT=.*/UI_PORT=<your-port>/' config.env
grep UI_PORT config.env
```

The second command should print `UI_PORT=<your-port>`.

### 1.7 Start it so it keeps running

```bash
loginctl enable-linger $USER
systemd-run --user --unit=mea-ui --working-directory=$PWD --property=Restart=on-failure ./run.sh
```

It answers `Running as unit: mea-ui.service`. The tool now runs in the
background and **keeps running after you log out** — you do not need to keep
this window open. Check it any time with:

```bash
systemctl --user status mea-ui
```

`Active: active (running)` means all is well. Type `q` to leave that screen.

You can now type `exit` to log out of the analysis computer. Setup is done.

---

## Part 2 — Open the control page

The control page is a web page served by the analysis computer. For safety it
is not open to the network; you reach it through an **SSH tunnel** — a private
connection from your computer.

**Each time you want to use it:**

1. Open a terminal on your computer (Mac: Terminal; Windows: PowerShell) and type:

   ```bash
   ssh -N -L <your-port>:127.0.0.1:<your-port> <your-user>@benshalom-labtower1
   ```

   Enter your password. **Nothing else appears — that is correct.** Leave this
   window open while you use the page.

2. In your web browser (Chrome, Safari, Edge, Firefox) go to:

   ```
   http://localhost:<your-port>
   ```

You see **MEA Bench** with four tabs: **Progress**, **Add recordings**,
**AI report**, **Settings**.

When you are done, close the browser tab and close the terminal window (or
press **Ctrl + C** in it). The analyses keep running on the analysis computer.

---

## Part 3 — First-time settings

Open the **Settings** tab.

**Where things are**

| Setting | What to put |
|---|---|
| **Recordings come from** | Your project folder on the NAS — the folder that contains the date folders (like `260818`, `260821`). Press **Choose** to browse. This folder is only ever read. |
| **Results go to** | A folder for your results, on the large analysis disk — for example `/mnt/Vol20tb2/<your-name>_mea_analysis/spike_detection`. It is created if it does not exist. Each project gets its own folder inside it. **Never** choose a folder inside the recordings folder (the tool refuses). |

**What to analyse** — recommended:

| Switch | Recommended | Why |
|---|---|---|
| Network analysis | **On** | Spikes and network bursts for every well. |
| Spike sorting (slow — about an hour per well) | **Off** | Off counts spikes on each electrode in minutes. Turn on only if you need individual neurons and have discussed it with the lab — it uses the graphics card for hours. |
| Activity scan | **On** | Whole-chip activity maps and quality checks; takes seconds. |
| Use the fast local disk while working | **On** | Several times faster. Temporary files go on the computer's fast disk and are deleted after each job. |

If you turn on the fast disk, open **Advanced settings** and set **Fast-disk
folder** to `/home/<your-user>/mea_scratch` (it is created and cleaned up for you).
Leave everything else in Advanced as it is.

Press **Save settings**.

> Settings are locked while analyses are running, so a change cannot disturb
> work in progress. They unlock when the current analyses finish.

---

## Part 4 — Analyse recordings

There are two ways. Most people use the first.

### Choose dates yourself — "Add recordings" tab

1. Open **Add recordings**. You see a card for every recording date in your project.
   - **analysed** — already done.
   - **partly done** — one of the two analyses is done.
   - **copying** — the recording is still being copied from the rig; wait.
2. Tick the dates you want (or press **Select all new**).
3. Press **Analyse N dates** at the bottom.

The dates are analysed in order, one at a time (you can allow two at once under
**Settings → Advanced → Network analyses at once**, if the lab agrees). To analyse an already analysed
date again, also tick **Also redo …** — its results are computed again and replaced.

### Automatic — "Watch for new"

Press **Watch for new** (top right). From then on, every new recording date that
appears in your project folder is analysed automatically, once its copy has
finished. Press **Pause watching** to stop picking up new dates (analyses that
are already running carry on).

---

## Part 5 — Follow progress

Open **Progress**.

The four numbers at the top count recording dates: **Waiting**, **Analysing**,
**Done**, **Need attention**. Below, each project has one line per date.

| Label on a date | Meaning |
|---|---|
| **In line** | Waiting for a free slot; it starts automatically. |
| **Waiting for copy** | The recording is still arriving from the rig. |
| **Analysing** | Running now. "N wells finished so far" updates as it goes. |
| **Done** | Both analyses finished. A note says how many wells finished. |
| **Paused — will resume** | Interrupted (e.g. the computer restarted); it continues by itself. |
| **Needs attention** | Something went wrong — press **Log** to see why, or ask for help. |

**Buttons on each line**

- **Wells** — a map of every chip, one circle per well:
  green = finished · amber = no activity (no spikes found) · red = a problem
  (the reason is written underneath) · dashed = not in the recording file (the
  rig recorded no data for that well — not an error) · faint = not recorded.
  Hover over a circle to read what happened to that well.
- **Log** — what the analysis did, step by step, in a side panel. Errors are
  highlighted in red. **Show everything** shows the raw log.
- **Report** — opens the newest report for that date (appears once a report exists).
- **↻** — analyse this date again.

Typical times with spike sorting off: a few minutes per well, so roughly
30 minutes to 2 hours per recording date depending on its size.

---

## Part 6 — Get a report from an AI

Reports are written by an AI assistant that runs on the analysis computer and
follows the lab's instructions. You can use any assistant that runs there and
can run commands — for example **Claude Code** (`claude`) or **ChatGPT Codex**
(`codex`). The first time, it asks you to sign in with your own account.

The instructions are already waiting in your results folder: every time you
start analysing, the tool places `AI_REPORT_INSTRUCTIONS.md` and a
`report_tools` folder there.

**Steps**

1. Log in to the analysis computer (as in step 1.1) and go to your results folder:

   ```bash
   ssh <your-user>@benshalom-labtower1
   cd <your results folder>
   ```

2. Start your AI assistant, e.g. type `claude` or `codex`, and sign in if asked.

3. Paste a message like this (fill in your folder, project and dates):

   ```
   Instructions: <your results folder>/AI_REPORT_INSTRUCTIONS.md
   Output folder: <your results folder>
   Please make me a report on <project> for <dates, e.g. 25 and 28 August>.
   ```

   You can also ask for "all finished dates", "everything in September", and so on.
   If it asks permission to run a command, allow it.

4. After a minute or two it tells you:
   - where the report is,
   - a short plain-language summary with the main numbers,
   - what to be careful about (unreliable wells, noisy electrodes, silent wells).

**Open the report:** in the control page, **AI report** tab → **Open report**
(or the **Report** button on that date's line in **Progress**).

**What is in a report**

- **One date:** one page with two tabs — **Network analysis** and **Activity
  scan** — with a summary, quality checks, every measurement per well, plots,
  activity maps and the pipeline's raster plots. Every table is also saved as a
  spreadsheet (CSV) next to the report.
- **Several dates:** an **overview** with trends over time and a link to each
  date's full report.

**Asking for more:** you can ask the AI for extras — for example "compare the
80K and 30K groups", "only show burst rate and duration", "make a figure for
my slides". It adds them in a separate `extras` folder and leaves the standard
report unchanged. If your groups are not recorded in the data, it will ask
which chips belong to which group.

**Good to know:** the AI may only *read* your results and *create* report
folders. It never changes your data, and every number it gives you comes from
the report's tables. Without spike sorting, a "unit" is an **electrode
channel**, not a neuron.

---

## Part 7 — Everyday tasks

| I want to… | Do this |
|---|---|
| Use the page again later | Part 2: open the tunnel, go to `http://localhost:<your-port>`. |
| Analyse more dates | **Add recordings** → tick → **Analyse**. |
| Redo one date | **Progress** → **↻** on that line. |
| Stop everything now | **Stop all** (top right). Dates that were running must be analysed again later. |
| Change settings | **Settings** → change → **Save settings** (only while nothing is analysing). |
| See if the tool is running | Log in, then `systemctl --user status mea-ui`. |
| Restart the tool | Log in, then `systemctl --user restart mea-ui`. **This stops any analysis that is running.** |
| Turn the tool off | Log in, then `systemctl --user stop mea-ui` (also stops running analyses). |
| Start it again after turning it off | Log in, `cd` to your Orchestration-MEA folder, run the `systemd-run …` command from step 1.7. |
| Get the newest version of the tool | Ask Hitesh first; then log in and run `git pull` in both folders, then restart the tool. |

---

## Rules for sharing the computer

The analysis computer is shared. Please:

1. **Never change, move or delete anything in the recordings folders** on the
   NAS. The tool only reads them.
2. **Never stop or delete other people's work.** Only use the buttons in *your*
   control page; do not stop processes you did not start.
3. **Keep spike sorting off** unless you have agreed it with the lab — it ties
   up the graphics card for hours.
4. **Mind the disk space.** Results go to your own folder on the large analysis
   disk. Temporary files on the fast disk are deleted automatically after each job.
5. **Use your own port number** so you do not open someone else's page.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `ssh: Could not resolve hostname` | Use the full address of the analysis computer (ask the administrator); connect to the university network/VPN first. |
| The page does not open (`localhost refused to connect`) | Is the tunnel window still open? Did you use your own port in both places? Is the tool running (`systemctl --user status mea-ui`)? |
| `Address already in use` when opening the tunnel | Another tunnel is already open on that port — close the other terminal window, or restart your computer's terminal. |
| *Can't reach the analysis server* on the page | The tool is restarting or stopped. Wait a minute and reload; otherwise restart it (Part 7). |
| A date says **Needs attention** | Press **Log** and look for red lines; ask for help with a screenshot. |
| **Wells** says *Reading well results…* for a long time | The results disk is busy with running analyses; it can take a minute or two. You can keep using the page. |
| A date stays **In line** for hours | Dates run one (or two) at a time; the others wait their turn. |
| The AI says `report_tools/make_report: not found` | Start analysing once from the page (it writes the report tools into your results folder), then ask again. |
| The AI says a date is *not finished yet* | Wait until **Progress** shows it as **Done**, then ask again. |
| `git clone` asks for a password and rejects it | Use a GitHub *personal access token* as the password, and check you have been given access. |

When asking for help, include: your user name, your port, the date folder, and
a screenshot of the page.

---

## Words used in this guide

| Word | Meaning |
|---|---|
| **Analysis computer** | The lab's shared Linux computer, *benshalom-labtower1*, where the analyses run. |
| **Terminal** | A window where you type commands. |
| **SSH / tunnel** | A secure way to log in to, or connect to a page on, the analysis computer. |
| **Port** | A number that identifies your copy of the control page (e.g. 8012). |
| **Recording date folder** | A folder named like `260821` (21 Aug 2026) containing one session's recordings. |
| **Chip / well** | A MaxTwo plate (e.g. `M07037`) and one of its wells. |
| **Network analysis** | Finds spikes on each electrode and network bursts (moments when many electrodes fire together). |
| **Activity scan** | A quick scan of the whole chip showing where the activity is. |
| **Spike sorting** | Separating spikes into individual neurons. Slow; off by default. |
| **Unit / channel** | Without spike sorting, one electrode channel (not a neuron). |
| **Silent well** | A well where no spikes were detected. |
| **Not in the recording file** | The rig did not record data for that well; nothing to analyse — not an error. |
