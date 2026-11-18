# Running analyses on the lab's Slurm cluster

The lab's three computers (BenShalomLabServer, benshalom-labtower1,
benshalom-labtower2) form one Slurm queue, `mea`, set up on 2026-11-12 (see
the lab's `mea-lab-docs`, especially `HITESH-HANDOFF.md`). With
**Settings → Where analyses run → The lab cluster**, MEA Bench sends each date's
Network analysis to that queue instead of running it on its own GPU. Activity
scans always run on the bench's machine.

## What happens to one date

1. When the date's turn comes in the bench's own first-come line, the bench
   writes a batch script and submits it through `/usr/local/bin/mea-slurm`.
   The Slurm job id is saved with the run before anything else.
   At most `slurm_max_jobs` dates are handed to Slurm at once; the rest wait in
   the bench's line, where they can still be held.
2. Earlier results of the date are copied into the job's shared folder,
   `/mnt/mea-cluster/results/mea-bench/<token>/seed`, so finished wells are
   skipped.
3. On whichever computer Slurm picks, the job, running as `lab-jobs`:
   - looks up that computer's analysis Python, MEA-Analysis folder and NAS
     mount (they differ: the main server mounts the NAS at
     `/mnt/ben-shalom_nas`, the towers at `/mnt/benshalom-nas`);
   - copies the recordings from the NAS (read only) to
     `/mnt/mea-scratch/mea-bench/<token>`, its own SSD;
   - runs `run_pipeline_driver.py` there in its own process group, with
     `--output-dir` on the SSD;
   - copies the results (without `binary/`) to the shared folder, compares the
     two listings, and deletes the SSD copy only if they match. Otherwise it
     keeps it and says where.
   - writes its exit code to the shared folder last.
4. The bench follows the job (`mea-slurm status`), shows "waiting in the
   cluster queue" or "analysing on <computer>", and mirrors its log into the
   run's usual log, so the stuck-job watchdog and the well view work as
   before.
5. When the job ends, the bench copies the results from the shared folder into
   the results folder, checks every file arrived, and only then deletes the
   shared folder.

Hold and Stop cancel the Slurm job (`mea-slurm cancel`); the job's script
stops the pipeline, brings back the finished wells it can within Slurm's 30
seconds, and deletes its SSD folder, also when stopped while still copying
the recordings. A job Slurm kills outright (out of time or memory) cannot
clean up after itself; the bench sees that in its log and sends a small
clean-up job to that computer. A hold while the earlier results are still
being copied for the job takes effect at once, and nothing is submitted. If
the bench restarts while jobs are in the cluster, it follows the same jobs
again; it never submits a date twice on a guess. A submission whose outcome
is unknown (the client timed out) is reported, not retried. Slurm forgets
finished jobs after about a day; the exit code in the shared folder still
tells the bench how a job ended.

Spike sorting asks Slurm for one whole GPU for the job (optionally on one
named computer: labtower1 has 32 GB, the others 12 GB). Detection only asks
for none.

The bench never falls back to its own machine by itself: where dates run is
the setting. NWB conversion and pipeline options naming a local path (`--config`,
`--checkpoint-dir`, `--reference`) cannot be used with the cluster, and the
settings say so. A date must be on the NAS (`slurm_nas_here`) for the cluster
to read it.

## Setting up the machine the bench runs on

The bench submits through the lab's client, which runs Slurm as `lab-jobs`
through one narrow sudo rule. On benshalom-labtower1 this was installed on
2026-11-13 from copies of the main server's files:

```bash
sudo install -d -o root -g root -m 755 /usr/local/libexec
sudo install -o root -g root -m 755 mea-slurm-client /usr/local/libexec/mea-slurm-client
sudo install -o root -g root -m 755 mea-slurm        /usr/local/bin/mea-slurm
echo '<bench account> ALL=(lab-jobs) NOPASSWD: /usr/local/libexec/mea-slurm-client *' > /tmp/rule
sudo visudo -cf /tmp/rule && sudo install -o root -g root -m 440 /tmp/rule /etc/sudoers.d/mea-slurm-submit
sudo usermod -aG lab-jobs <bench account>
```

The bench must run in the `lab-jobs` group to read and write the shared
results folder: start it from a fresh login after being added (or under
`sg lab-jobs -c ./run.sh`). Every computer also needs the MaxWell HDF5 plugin
at `/usr/local/hdf5/lib/plugin/libcompression.so`.

**Settings → Where analyses run → Check the cluster** sends a small job to each
computer (2 CPUs, a few minutes) that checks, as `lab-jobs`: the analysis
Python and its packages, MEA-Analysis, the NAS, the plugin, rsync, writing to
the shared and scratch folders, the GPU when spike sorting is on, and
decoding one recording of a watched project.

## Where results go

The lab's results folder is `/mnt/MaxwellData_Backup/MEA_Analysis`, the same
path on all three computers: on BenShalomLabServer it is its own 22 TB disk;
the towers reach it over NFS, set up on 2026-11-18. Only that folder is
shared, not the raw backup beside it (`Maxtwo`).

```bash
# BenShalomLabServer
sudo install -d -o lab-jobs -g lab-jobs -m 2775 /mnt/MaxwellData_Backup/MEA_Analysis
echo '/mnt/MaxwellData_Backup/MEA_Analysis 10.157.209.11(rw,sync,root_squash,no_subtree_check) 10.157.209.12(rw,sync,root_squash,no_subtree_check)' \
  | sudo tee /etc/exports.d/mea-results.exports
sudo exportfs -ra
# each tower: /etc/systemd/system/mnt-MaxwellData_Backup-MEA_Analysis.mount
#   What=10.157.208.197:/mnt/MaxwellData_Backup/MEA_Analysis
#   Where=/mnt/MaxwellData_Backup/MEA_Analysis
#   Type=nfs  Options=vers=4.2,rw,hard,_netdev,nosuid,nodev
sudo systemctl daemon-reload && sudo systemctl enable --now mnt-MaxwellData_Backup-MEA_Analysis.mount
```

A bench with no results folder set starts from it (`MEA_OUTPUT_DIR` overrides
that on other machines), and Settings offers it when another folder is set.
Files the bench writes there belong to group `lab-jobs`; on the main server
their owner shows as whoever has the bench account's number there.

## Settings (`job.json`)

| Setting | Meaning |
|---|---|
| `executor` | `local` or `slurm` |
| `slurm_nodes` | each computer: `node`, `python`, `mea_repo`, `nas` |
| `slurm_nas_here` | where the NAS is mounted on the bench's machine |
| `slurm_cpus`, `slurm_mem_gb`, `slurm_hours` | asked for each date (1–24 CPUs, up to 48 GB, up to 24 h) |
| `slurm_max_jobs` | dates handed to Slurm at once |
| `slurm_gpu_node` | where spike sorting runs (blank: any) |
| `slurm_results_dir`, `slurm_scratch_dir` | `/mnt/mea-cluster/results/mea-bench`, `/mnt/mea-scratch/mea-bench` |
| `slurm_client`, `slurm_hdf5_plugin_path`, `slurm_poll_seconds` | rarely changed |
