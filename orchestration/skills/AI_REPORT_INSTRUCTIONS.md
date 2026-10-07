# Instructions for the AI: making MEA reports

You are helping a lab member get a report on their multi-electrode array (MEA)
experiments. They are scientists, not programmers. They will give you this file
and an **output folder** (where the analysis results are), usually with little
more than a project name and the dates they care about. Your job: produce the
lab's **standard report** for those dates, check it, and explain what it shows
in plain language.

If they did not tell you the output folder, ask for it. Everything below is
relative to that folder.

Read this whole file before doing anything. Then read
`report_tools/skills.md` (inside the output folder) for what every measurement
means.

---

## 1. Rules — always

1. **Never change, move or delete existing files.** The raw recordings and the
   analysis results are read-only to you. Every report goes into a *new* folder,
   which the report command creates.
2. **Do not run analyses, stop jobs, restart services, or touch other people's
   folders or processes.** Only make reports.
3. **Use the standard report command (§3).** Do not write your own version of
   the standard report or edit its output. Its format is the lab's agreed format.
4. **Every number you tell the user comes from the report or its tables.** Never
   estimate or remember a value. If something is missing, say it is missing.
5. **Say what a "unit" is.** These results come from spike detection *without*
   spike sorting: a unit is an **electrode channel**, not a neuron. Never call
   them neurons or cells.
6. **The well is the unit of replication.** Compare groups with per-well values
   and state n (wells). No significance claims without a named test and n ≥ 3
   wells per group.
7. If you are unsure what the user wants, ask one short question rather than guess.

---

## 2. What is in the output folder

```
report_tools/make_report      the report command (already set up — just run it)
report_tools/skills.md        what every measurement means
<project>/                    one folder per project, e.g. IPN_Organoids_08142026_PVS
  <YYMMDD>/<chip>/Network/<run>/<well>/    Network analysis results per well
  ActivityScan/<YYMMDD>/<chip>/<run>/      Activity scan results per chip
  orchestration_logs/                      analysis logs per date
  AI_HANDOFF/<timestamp>_<label>/report/   finished reports (yours go here too)
```

Dates are folder names in `YYMMDD` form: `260821` is 21 August 2026.

The user may give you the output folder itself (it contains `report_tools` and
one or more project folders) or a single project folder inside it (it contains
date folders). If it is a project folder, `report_tools` is in the folder above it.

---

## 3. How to make a report

Run every command from the output folder. `<project>` is the project folder's
name; list the output folder to see the projects and ask the user which one if
there is more than one.

**Step 1 — see what exists.**

```bash
report_tools/make_report --project-dir <project> --list
```

This prints every date with results, whether its analysis has **finished**, and
how many wells and scans it has. Show the user this list in friendly form
("18 Aug 2026 — finished, 21 wells") and confirm which dates they want if they
were vague ("the latest", "all of September", "everything").

**Step 2 — make the report.** Pick one:

```bash
report_tools/make_report --project-dir <project> --dates 260821                 # one date
report_tools/make_report --project-dir <project> --dates 260818 260821 260825   # several dates
report_tools/make_report --project-dir <project> --all                          # every finished date
```

Add `--requirements "…"` to record any extra wishes the user stated (they are
saved with the report; see §5 for acting on them). Add `--label name` to give the
folder a readable name. Roughly 20–60 seconds per date.

The command refuses dates whose analysis has not finished. Only if the user
explicitly wants a partial report, add `--allow-unfinished` and tell them it is
partial.

The command ends by printing JSON with `"report": "<path to report.html>"`.
That is the report.

**Step 3 — check it.** Before you describe anything, read the report's numbers
from its tables (CSV files next to the report):

* one date: `<folder>/report/tables/` — start with `network_key_metrics.csv`,
  `network_qc.csv`, `activity_key_metrics.csv`, `activity_qc.csv`
* several dates: `<folder>/report/overview_dates.csv`, `network_all_dates.csv`,
  `activity_all_dates.csv`, and each date's tables in `<folder>/report/dates/<date>/tables/`

Confirm the well counts look right and note any wells flagged in QC.

**Step 4 — tell the user.** Reply with:

1. Where the report is: the path, and that it also appears in the control page
   (the **AI report** tab, "Open report").
2. Five to eight plain-language bullets on what it shows, each with its number
   and n, taken from the tables — e.g. "Network bursts in 19 of 27 wells, about
   13 per minute (median across wells)".
3. What to be careful about (from the QC tables): wells with unreliable burst
   metrics, noisy channels, silent wells, wells not in the recording file.
4. Anything you could not do.

Keep it short and free of jargon; explain any technical term you must use.

---

## 4. What the standard report contains

**One date** → `report.html`, one file with two tabs:

* **Network analysis** — summary, dataset, quality control, per-well metrics
  (every value the analysis produced), comparison across chips, how metrics
  relate, every channel's firing statistics, every burst, a burst timeline,
  full-length population activity per well, detection settings, and the
  pipeline's raster plots.
* **Activity scan** — summary, QC with reasons, every per-well value, activity
  maps of the whole chip, rate and amplitude distributions, how well each chip's
  Network recording covered the activity, and scan-vs-Network comparison.

Every table is also saved as CSV in `tables/`.

**Several dates** → `report.html` is an **overview**: a table of the dates with
counts and links, and trends over time (per chip and across all wells, by days
in vitro when the plating date is known) for the main Network and Activity-scan
measures. Each date's full standard report is in `dates/<date>/report.html`.

---

## 5. When the user asks for more than the standard report

Make the standard report first, then add to it — never change it.

* Put extra work in `<folder>/extras/` (create it): your script(s), figures,
  tables, and a short `README.md` saying what each file is.
* Work from the report's CSV tables where possible; they already apply the QC
  flags. Read raw result files only when the tables lack what you need
  (layouts in `report_tools/skills.md` §3).
* Follow the rules in §1 and the statistics guidance in skills.md (per-well
  values, n stated, describe when n < 3).
* Typical requests: compare named groups of chips or wells (ask which chips are
  which group — groups are usually *not* recorded in the data), focus on a few
  measures, a different file format, a slide-ready figure.

---

## 6. Reading the results correctly

* **No sorting.** Spikes are threshold crossings per electrode channel.
* **Burst metrics can be unreliable** in a well with no bursts, fewer than 10
  spiking channels, or more than 60 bursts per minute (the detector is reacting
  to noise). The report flags these wells and leaves them out of pooled plots.
* **Noisy channels** (average above 100 Hz) inflate spike counts and population
  rates; burst detection is much less affected. Reported, not removed.
* **Wells without results** are explained in the QC table: *not in the recording
  file* (MaxWell's file has no data for that well — not a failure), *no spikes
  detected* (a silent well), or a real failure with the log's reason.
* **Groups.** If every well is labelled "Default Group", no experimental groups
  were entered; comparisons are by chip only unless the user tells you the groups.
* **Small run-to-run differences.** Spike detection sets its threshold from a
  random sample of the recording, so re-running the same well can change spike
  counts by about 0.1 % and burst counts slightly. Do not over-interpret tiny
  differences.

---

## 7. If something goes wrong

| Message | Meaning / what to do |
|---|---|
| `No results for …` | That date has no results yet. Run `--list` and offer the dates that exist. |
| `Not finished yet: …` | The analysis is still running or waiting. Offer the finished dates, or a partial report if the user insists (`--allow-unfinished`). |
| `control server not reachable` in `--list` | Status unknown, so nothing is refused. Say the status could not be checked. |
| `FAILED <date>` | The report for that date could not be built. Show the user the last lines of the error and stop — do not try to repair the analysis or the script. |
| `report_tools/make_report: not found` | You are not in the output folder, or it was given as a project folder — use `../report_tools/make_report`. If `report_tools` is missing, ask the user to start watching once in the control page (it writes the folder), and stop. |
| Folder already exists | Use a different `--label`, or let the command choose the name. |
