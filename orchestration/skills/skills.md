# MEA analysis report: skills

You are writing a scientific report from multi-electrode array (MEA) results
that have already been computed. This file tells you what the data is, where it
is, what every number means, and the rules the report must follow. Read it in
full before opening any result file.

The study's own requirements are in `REQUIREMENTS.md` next to this file. Where
they conflict with a **default** here, the requirements win. They never override
the **rules** in section 1.

---

## 1. Rules (always apply)

1. **Never modify, move, or delete anything** outside the `report/` folder of
   this handoff. The raw recordings (the *input* folder named in `PROMPT.md`)
   are read-only and must not be opened for writing, touched, or copied into.
   The analysis output folder is also read-only to you.
2. **Every number comes from a file.** Never estimate, round-trip from memory,
   or invent a value. Each figure and table must be traceable to a specific
   file; list those files in the report's *Data sources* section.
3. **Missing is missing.** If a well, chip, metric, or group has no data, say
   so explicitly ("no data", "QC fail", "not analysed"). Do not fill gaps and
   do not silently drop wells. Report how many wells were expected, analysed,
   excluded, and why.
4. **Say what a "unit" is.** In *detection-only* mode (the default — see §3) a
   unit is an **electrode channel**, not a sorted neuron. Never call these
   neurons or cells. Only `processing_mode: "sorted"` outputs contain neurons.
5. **The unit of replication is the well**, not the electrode, unit, or burst.
   Electrodes in a well are not independent samples. Statistics across
   conditions use per-well values (n = wells), and n is stated on every
   comparison.
6. **No over-claiming.** Describe differences with their size and spread. Only
   use "significant" with a named test, its statistic, n, and p-value. With
   n < 3 wells per group, describe, do not test.
7. Work in a scratch copy if you need to transform data; write only to
   `report/`.

---

## 2. What the experiment is

* **MaxWell MaxOne / MaxTwo high-density MEA.** A chip has ~26,400
  electrodes on a 17.5 µm pitch. A MaxTwo plate has 6 wells, each its own chip
  area. Recordings are sampled at 10 kHz (`fs` in the results) or 20 kHz.
* **Two recording types (assays)** are made per chip per session:
  * **ActivityScan** — sweeps the whole array block by block (each block
    recorded for ~30 s). Gives a map of *where* activity is, across all 26,400
    electrodes, but electrodes in different blocks were never recorded at the
    same time.
  * **Network** — records ~1,020 selected electrodes simultaneously for
    minutes. Gives *network dynamics*: bursts, synchrony, firing patterns. It
    covers ~4 % of the array, chosen from the ActivityScan.
* **Folder naming.** Raw data is `<project>/<YYMMDD>/<chip_id>/<assay>/<run_id>/data.raw.h5`.
  `YYMMDD` is the recording date (e.g. `260903` = 2026-09-03). `chip_id`
  looks like `M08121`. `run_id` is a six-digit MaxWell run number. Wells are
  `well000`–`well005` (Network) or `well_id` 0–5 (ActivityScan); the plate
  label printed on the dish (`well_label`) is `well_id + 1`.
* **Age.** Days in vitro (DIV) or days post-plating = recording date minus
  `plating_date` (ActivityScan `summary.json`, format `D.M.YYYY`). Use it as the
  time axis for longitudinal reports.

---

## 3. Where the results are

`PROMPT.md` gives the exact folders and `MANIFEST.json` lists every result file
found. The layouts are:

### 3a. Network analysis (MEA-Analysis pipeline)

```
<output>/<project>/<YYMMDD>/<chip_id>/Network/<run_id>/<well>/
    network_results.json      bursts and network metrics (main source)
    unit_stats.csv            per-unit firing statistics
    processing_info.json      how the well was processed
    checkpoints/*_checkpoint.json   completion status, errors
    bad_channels.json         channels excluded as noisy
    spike_times.npy           spike times per unit (numpy pickle dict)
    network_plot_data.npz     arrays behind the raster/network plots
    raster_burst_plot*.png    pipeline figures (full, 30 s and 60 s views)
    <run>_<well>_pipeline.log per-well log
```

**`processing_info.json` → `processing_mode`** decides how to read everything:

| mode | meaning |
|---|---|
| `spike_detection_only` (default) | Threshold crossings (negative, 5 × noise MAD) per electrode channel. No sorting, no waveforms, no quality metrics. Units = channels. |
| sorted (`used_spike_sorting: true`) | Kilosort4 sorted units with curation. Units ≈ putative neurons. Extra files: `qm_*.csv`, `waveforms_grid.pdf`, `analyzer_output/`. |

**Completion.** A well is complete when its checkpoint has no `error` /
`failed_stage` and either `stage` = 10, or the mode is detection-only and
`network_results.json` exists. A checkpoint with `error` set is a failed well:
quote the first line of the error in the QC section. `ValueError: n_samples=…
should be >= n_clusters=…` means the well had almost no spikes — a biological
result (silent well), not a software fault. `stream_id wellNNN is not in
['well…']` means the driver asked for a well that this recording file does not
contain — the well was not recorded in that run; report it as "not recorded",
not as a failed analysis. A checkpoint stuck below completion with no `error`
means the well's process stopped without reporting why; take the reason from
the date's driver log in `<output>/<project>/orchestration_logs/` when it is
there, and say "stopped without an error" when it is not.

**`network_results.json`** top level:

| key | meaning |
|---|---|
| `n_units` | units (channels in detection-only mode) in the well |
| `fs`, `duration_s` | sampling rate (Hz), recording length (s) |
| `project`, `date`, `chip_id`, `run_id`, `well` | identity |
| `network_bursts.metrics` | **the primary network-burst measures** |
| `network_bursts.events[]` | one entry per burst (start/end/peak time, spike count, participation) |
| `burst_fragments` | shorter sub-burst events before merging; secondary |
| `superbursts` | long merged burst trains (≥ `superburst_min_dur_s`); often empty |
| `diagnostics` | detection parameters and validity (`burst_detection_valid`, thresholds, `n_bursty_units`) |

Inside each `metrics` block (values marked † are `{mean, std, cv}` across bursts):

| metric | unit | meaning |
|---|---|---|
| `burst_count` | count | bursts detected in the recording |
| `burst_rate_hz` | Hz | bursts per second (× 60 for bursts/min) |
| `burst_duration_s` † | s | burst length |
| `ibi_s` † (`ifbi_s` for fragments) | s | inter-burst interval; its `cv` measures regularity |
| `spike_count_per_burst` † | spikes | spikes inside a burst |
| `participation_fraction` † | 0–1 | fraction of units active during a burst |
| `peak_participation_fraction` † | 0–1 | fraction of units active at the burst peak |
| `peak_population_firing_rate_hz` † | Hz | summed firing rate at the burst peak |
| `burst_area` † | a.u. | integral of the population-rate curve over the burst |

If `diagnostics.burst_detection_valid` is 0 or `burst_count` is 0, report the
well as "no network bursts detected", not as zero-valued metrics.

**Check before trusting burst metrics.** `burst_detection_valid: 1` does not
mean the bursts are real. Plot the participation signal in
`network_plot_data.npz` (`time_s`, `participation_fraction_signal`,
`nb_peak_times_s`) for every well and look. Flag a well's burst metrics as
unreliable, keep it in every table, and leave it out of pooled plots and
correlations, when any of these holds:

* more than **60 network bursts per minute** (over one per second): the
  detector is riding on noise fluctuations — peaks spread densely over a flat
  trace, not discrete events;
* fewer than **10 spiking channels**: participation is a fraction of a handful
  of channels and jumps in big steps (often pinned near 1.0);
* no network bursts.

State these criteria in the report. Do not draw the detection threshold from
`diagnostics` on the participation plot: its scale is not that of the signal,
and peaks appear below it.

**Noisy channels.** In detection-only mode a few channels often fire at
hundreds to thousands of Hz for the whole recording — not neuronal. Count
channels with a mean rate above **100 Hz** per well and the share of the well's
spikes they carry (spike counts per channel from `spike_times.npy`,
`np.load(..., allow_pickle=True).item()`, a dict channel → spike times in s).
They inflate total spikes, `spike_count_per_burst` and population firing rates;
burst *detection* works on participation and is much less affected. Report
them; do not exclude wells for them alone. Use medians, not means, for
per-well channel firing rates.

**Recording length** is not always in `network_results.json` (`fs`,
`duration_s` are missing in some outputs). Derive it as spikes ÷
`mean_firing_rate_hz` per channel (median across channels), and say so.

**`unit_stats.csv`** — one row per unit: `mean_firing_rate_hz`, `cv_isi`,
`cv2`, `lv` (local variation; ~1 Poisson, <1 regular, >1 bursty),
`bimodality_coefficient`, `is_bursty`. Summarise per well (median, IQR,
fraction bursty) before comparing wells.

### 3b. ActivityScan analysis (this tool)

```
<activity_output>/<YYMMDD>/<chip_id>/<run_id>/
    summary.json        per-well metrics + QC (main source)
    per_electrode.csv   every electrode: x_um, y_um, spikes, seconds, rate_hz, mean_amplitude_uv
    plate_overview.png, wellNNN_activity.png, wellNNN_network.png,
    wellNNN_functional.png, group_comparison.png
<activity_output>/activity_scan_index.json   index of all processed scans
```

`summary.json` has run identity (`chip_id`, `run_id`, `source`,
`active_threshold_hz`, `array_electrodes`) and `wells[]`, each with:

| field | unit | meaning |
|---|---|---|
| `well_id`, `well_label` | | well (label = id + 1) |
| `group`, `control` | | experimental group as entered in MaxWell; whether it is a control |
| `plating_date` | D.M.YYYY | for DIV |
| `electrodes_scanned`, `array_coverage_pct` | | how much of the array was scanned |
| `electrodes_active`, `active_fraction` | count, 0–1 | electrodes above `active_threshold_hz` |
| `total_spikes` | count | |
| `rate_mean_hz`, `rate_median_hz`, `rate_p90_hz`, `rate_max_hz` | Hz | firing rate over active electrodes |
| `amplitude_mean_uv`, `amplitude_median_uv`, `amplitude_p90_uv` | µV | spike amplitude |
| `centroid_um`, `dispersion_um`, `occupied_area_mm2`, `occupied_bins_100um`, `clustering_index` | µm, mm² | spatial extent of activity |
| `isi_cv_median`, `burst_fraction_mean`, `rate_stability_cv` | | single-electrode firing pattern |
| `population_rate_hz`, `synchrony_fano` | Hz, a.u. | population activity, synchrony (within a block only) |
| `network_burst_rate_hz`, `network_burst_count`, `burst_duration_mean_s`, `spikes_per_burst_mean`, `pct_spikes_in_bursts`, `interburst_interval_mean_s` | | bursts detected within scan blocks |
| `correlation_mean/median/p95/max`, `mean_degree`, `functional_electrodes` | | functional connectivity, within block only |
| `qc`, `qc_reasons` | `pass`/`warn`/`fail` | per-well quality verdict and why |

**Electrode-selection fields** (`selected_electrodes`, `selected_active_fraction`,
`selected_rate_mean_hz`, `selection_enrichment`, `captured_activity_fraction`,
`selection_recall`, `selection_efficiency`, `selection_quality`) compare the
scan with the electrodes chosen for a Network recording. Check
`summary.json` → `selection_source`: it must be a Network recording **on the
same chip** (same `<chip_id>` folder). If it is missing, absent, or names
another chip, do not report the selection fields for that run — say why.
Older scans have no `selection_source`; treat their selection fields as
unverified.

ActivityScan bursts and correlations are computed over ~30 s blocks, so they
are **not** comparable in absolute value to Network-recording bursts. Report
them separately, and never mix the two in one statistic.

---

## 4. Default report (when the requirements do not say otherwise)

**Format:** one self-contained HTML file, `report/report.html`, with all
figures embedded (base64 PNG or inline SVG) so it opens offline. Plus
`report/tables/` with every table as CSV. Use Python (pandas, matplotlib)
for computation and plotting; save the script as `report/build_report.py` so
the report can be regenerated.

**Sections, in order:**

1. **Summary** — 4–6 bullet points of the main findings, each with its number
   and n.
2. **Dataset** — recording dates, chips, wells, groups, DIV; table of wells
   expected vs analysed vs excluded.
3. **Quality control** — failed wells with error, silent wells, ActivityScan
   `qc` warn/fail with reasons, bad channels. State what was excluded and why.
4. **Network activity** — per-well table of key metrics (n_units, burst rate
   per minute, burst duration, IBI and its CV, participation, spikes per
   burst, median unit firing rate); group comparison plots (individual wells
   as points over mean ± SEM or box); representative raster from the pipeline's
   `raster_burst_plot_60s.png`.
5. **Whole-array activity (ActivityScan)** — active fraction, rate,
   amplitude, spatial extent, QC; plate overview images.
6. **Development over time** — only if more than one recording date: metric
   vs DIV per group, wells linked across sessions by `chip_id` + well.
7. **Methods** — processing mode (detection-only vs sorted), thresholds from
   `diagnostics` and `active_threshold_hz`, software (MEA-Analysis pipeline,
   Orchestration-MEA ActivityScan), statistics used.
8. **Data sources** — every file read, by path.

**Figures:** label axes with units; one colour per group, consistent across
the report; show every well as a point; title each figure with what it shows,
not with a file name.

**Statistics:** compare groups on per-well values. Default to a
Mann-Whitney U test for two groups and Kruskal-Wallis with Dunn's post-hoc for
more; state n per group and the exact p. For longitudinal data, describe
trajectories; use a mixed model only if the requirements ask for it.

---

## 5. How to work

1. Read `PROMPT.md`, `REQUIREMENTS.md`, and `MANIFEST.json`.
2. Load the results listed in the manifest into one table per level (well,
   unit, ActivityScan well). Check counts against the manifest before
   analysing — if they disagree, say so in the report.
3. **Look before summarising.** Render the participation traces and a few
   per-well figures and check them by eye; apply the reliability checks in
   §3a and the selection check in §3b. A number that is computed correctly
   from a bad detection is still a bad number.
4. Decide groups: from the requirements first; otherwise ActivityScan
   `group`/`control` matched by `chip_id` + well; otherwise by chip. State which.
5. Build the report, then re-check every number in the text against the table
   it came from.
6. Finish with a short message listing the report path, what is in it, and
   anything you could not do (missing data, ambiguous requirements).
