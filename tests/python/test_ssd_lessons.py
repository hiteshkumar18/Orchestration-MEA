"""What the first full run on the SSD scratch disk (2026-10-20/21) got wrong.

The scratch disk filled because the space estimate assumed each well's working
files were deleted as it finished, which they were not. Five dates were killed
whole by systemd-oomd and showed "failed" with no reason. A date whose logging
failed reported 77 failed wells when far fewer had. A job that ended before it
ran stayed counted as queued by hand. Each test below covers one of these.
"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import memguard
import watcher as watcher_mod
from watcher import JOB_NETWORK, JobConfig, Watcher

GB = 2**30
Usage = namedtuple("Usage", "total used free")

# A driver log as the full disk left it: one well logged normally, one whose
# ERROR line could not be written (Python then prints the traceback, quoting
# the source line, and the message), and one that finished.
FULL_DISK_LOG = """\
[2026-10-20 08:38:30,338] INFO: [DRIVER] Launching: python3 routine.py '/d/000082/data.raw.h5' --rec rec0000 --well well000
Processing Complete for well000
[2026-10-20 08:44:52,786] INFO: [DRIVER] Launching: python3 routine.py '/d/000082/data.raw.h5' --rec rec0000 --well well001
[2026-10-20 17:59:12,260] ERROR: Subprocess failed for well001 in /d/000082/data.raw.h5
[2026-10-20 17:59:12,276] ERROR: Exit Code: 1
[2026-10-20 17:59:13,000] INFO: [DRIVER] Launching: python3 routine.py '/d/000086/data.raw.h5' --rec rec0000 --well well001
--- Logging error ---
Traceback (most recent call last):
    logger.info(f"[DRIVER] Launching: {command}")
OSError: [Errno 28] No space left on device
Message: "[DRIVER] Launching: python3 routine.py '/d/000086/data.raw.h5' --rec rec0000 --well well001"
Arguments: ()
--- Logging error ---
Traceback (most recent call last):
  File "run_pipeline_driver.py", line 983, in run
    logger.error(f"Subprocess failed for {stream_id} in {file_path}")
OSError: [Errno 28] No space left on device
Message: 'Subprocess failed for well001 in /d/000086/data.raw.h5'
Arguments: ()
--- Logging error ---
Traceback (most recent call last):
    logger.error(f"Subprocess failed for {stream_id} in {file_path}")
OSError: [Errno 28] No space left on device
Message: 'Subprocess failed for well001 in /d/000086/data.raw.h5'
Arguments: ()
"""

# Ends itself the way systemd-oomd ends a job: SIGKILL, nothing logged.
KILLED = "import os, signal; print('started', flush=True); os.kill(os.getpid(), signal.SIGKILL)"
SLEEP = "import time; print('started', flush=True); time.sleep(120)"


class WellCountTest(unittest.TestCase):
    def verdict(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "driver.log"
            p.write_text(text)
            return Watcher.read_driver_verdict(p)

    def test_traceback_copies_are_not_counted_twice(self):
        # Three launches, two different wells failed; the old count said 4 of 3.
        self.assertEqual(self.verdict(FULL_DISK_LOG),
                         "2 of 3 well subprocess(es) failed — see the driver log")

    def test_same_well_in_two_recordings_counts_twice(self):
        text = ("[DRIVER] Launching: a.h5 --well well000\n[DRIVER] Launching: b.h5 --well well000\n"
                "ERROR: Subprocess failed for well000 in a.h5\n"
                "ERROR: Subprocess failed for well000 in b.h5\n")
        self.assertTrue(self.verdict(text).startswith("the driver exited 0 but all 2 "))

    def test_wells_missing_from_their_recording_are_not_failures(self):
        text = ("[DRIVER] Launching: a.h5 --well well000\nProcessing Complete for well000\n"
                "[DRIVER] Launching: a.h5 --well well001\n"
                "AssertionError: stream_id well001 is not in ['well000', 'well002']\n"
                "ERROR: Subprocess failed for well001 in a.h5\n"
                "[DRIVER] Launching: a.h5 --well well002\n"
                "ERROR: Subprocess failed for well002 in a.h5\n")
        self.assertEqual(self.verdict(text),
                         "1 of 3 well subprocess(es) failed — see the driver log; "
                         "1 well(s) are not in their recording file, so there was nothing to analyse")
        only_missing = text.split("[DRIVER] Launching: a.h5 --well well002")[0]
        self.assertEqual(self.verdict(only_missing),
                         "1 well(s) are not in their recording file, so there was nothing to analyse")

    def test_ordinary_logs_read_as_before(self):
        ok = "[DRIVER] Launching: a.h5 --well well000\nProcessing Complete for well000\n"
        self.assertIsNone(self.verdict(ok))
        self.assertEqual(self.verdict("No data files found in x\n"),
                         "the driver found no recordings to analyse")
        nwb = ("[DRIVER] Launching: a.nwb --well well000\n"
               "NWB: NWB conversion failed for well001 in a.h5: bad chunk\n"
               "NWB: NWB conversion failed for well001 in a.h5: bad chunk\n")
        self.assertEqual(self.verdict(nwb), "1 of 2 well subprocess(es) failed — see the driver log")

    def test_the_real_log_from_that_night(self):
        log = Path("/mnt/Vol20tb2/hitesh_mea_analysis/output/B6J_09092026_PVS/orchestration_logs/"
                   "261003_network_20261019_235855.log")
        if not log.exists():
            self.skipTest("the 2026-10-20 log is not on this machine")
        # 66 wells were launched and 27 failed; the old count said 77 of 116.
        self.assertEqual(Watcher.read_driver_verdict(log),
                         "27 of 66 well subprocess(es) failed — see the driver log")


class ExitReasonTest(unittest.TestCase):
    def test_killed(self):
        r = Watcher.exit_reason(-9)
        self.assertIn("stopped by the system (killed)", r)
        self.assertIn("Finished wells are kept", r)
        self.assertNotIn("systemd-oomd", r)
        self.assertIn("systemd-oomd", Watcher.exit_reason(-9, oomd=True))
        self.assertIn("killed", Watcher.exit_reason(137))

    def test_other_codes(self):
        self.assertIn("signal 15", Watcher.exit_reason(-15))
        self.assertIn("code 2", Watcher.exit_reason(2))
        self.assertIn("retry", Watcher.exit_reason(1, network=False))
        self.assertNotIn("wells", Watcher.exit_reason(1, network=False))


class WatcherCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.watch = self.root / "watch"
        self.watch.mkdir()

    def make(self, **kw):
        kw.setdefault("work_dir", str(self.root / "work"))
        kw.setdefault("watch_dir", str(self.watch))
        kw.setdefault("gpu_cooldown_seconds", 0)
        kw.setdefault("queue_poll_seconds", 1)
        kw.setdefault("kill_grace_seconds", 2)
        return Watcher(JobConfig(**kw), reconcile=False)

    def date(self, name, sizes_gb=()):
        """A date whose Network recordings have these sizes (sparse files)."""
        d = self.watch / name
        for i, size in enumerate(sizes_gb):
            f = d / "M00001" / "Network" / f"{i:06d}" / "data.raw.h5"
            f.parent.mkdir(parents=True)
            with open(f, "wb") as fh:
                fh.truncate(int(size * GB))
        d.mkdir(exist_ok=True)
        return d

    def wait_for(self, cond, timeout=30.0):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.2)
        return False


class StagingEstimateTest(WatcherCase):
    def test_with_clean_up_one_well_at_a_time(self):
        w = self.make()
        w.cfg.driver_options["clean_up"] = True
        d = self.date("261003", (66, 47, 11))
        self.assertAlmostEqual(w._staging_estimate_gb(d), 66 * Watcher.BINARY_VS_RAW, places=3)

    def test_without_clean_up_every_well_together(self):
        w = self.make()
        w.cfg.driver_options["clean_up"] = False
        d = self.date("261003", (66, 47, 11))
        self.assertAlmostEqual(w._staging_estimate_gb(d), 124 * Watcher.ALL_WELLS_VS_RAW, places=3)

    def test_that_night_would_not_have_staged(self):
        """3.4 TB free, 261003's 472 GB of recordings, clean-up off: decline."""
        w = self.make(stage_locally=True, scratch_dir=str(self.root / "scratch"))
        w.cfg.driver_options["clean_up"] = False
        d = self.date("261003", (66, 62, 62, 62, 47, 47, 47, 47, 18, 11))
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(3600 * GB, 200 * GB, 3400 * GB)):
            self.assertIsNone(w._stage_in(d))
            w.cfg.driver_options["clean_up"] = True
            staged = w._stage_in(d)
        self.assertIsNotNone(staged)
        w._remove_scratch(staged[0])


class ScratchGuardTest(WatcherCase):
    def test_low_space_is_reported(self):
        w = self.make(stage_min_free_gb=200)
        scratch = self.root / "scratch"
        scratch.mkdir()
        self.assertIsNone(w._scratch_too_low(None))
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(3600 * GB, 3500 * GB, 150 * GB)):
            msg = w._scratch_too_low(scratch)
            self.assertIn("150 GB free", msg)
            self.assertIn("at least 200 GB", msg)
            self.assertIn("Delete each well's working files as soon as it finishes", msg)
            w.cfg.driver_options["clean_up"] = True
            self.assertIn("fewer dates at once", w._scratch_too_low(scratch))
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(3600 * GB, 3000 * GB, 600 * GB)):
            self.assertIsNone(w._scratch_too_low(scratch))

    def test_floor_of_zero_still_stops_before_full(self):
        w = self.make(stage_min_free_gb=0)
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(100 * GB, 95 * GB, 5 * GB)):
            self.assertIsNotNone(w._scratch_too_low(self.root))

    def test_running_job_is_stopped(self):
        w = self.make(stage_min_free_gb=200)
        scratch = self.root / "scratch"
        scratch.mkdir()
        log = self.root / "job.log"
        t = time.time()
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(3600 * GB, 3500 * GB, 100 * GB)):
            with open(log, "w") as fh:
                rc, why = w._supervise([sys.executable, "-c", SLEEP], dict(os.environ), fh, log,
                                       "261003", "Network", "k", scratch=scratch)
        self.assertLess(time.time() - t, 60)
        self.assertNotEqual(rc, 0)
        self.assertIn("scratch disk", why)

    def test_unstaged_job_is_not_watched(self):
        w = self.make()
        log = self.root / "job.log"
        with mock.patch.object(watcher_mod.shutil, "disk_usage",
                               return_value=Usage(100 * GB, 100 * GB, 0)):
            with open(log, "w") as fh:
                rc, why = w._supervise([sys.executable, "-c", "print('ok')"], dict(os.environ),
                                       fh, log, "261003", "Network", "k")
        self.assertEqual((rc, why), (0, None))


class KilledJobTest(WatcherCase):
    def test_killed_job_says_why(self):
        w = self.make(memory_limit_gb=-1)          # no scope: the reason must not blame oomd
        w.cfg.driver_options["skip_spikesorting"] = True
        d = self.date("260916")
        key = w.state_key(d.resolve(), JOB_NETWORK)
        log = self.root / "killed.log"
        w._run_job(d, JOB_NETWORK, key, [sys.executable, "-c", KILLED], log)
        e = w.state.all()[key]
        self.assertEqual(e["status"], "failed")
        self.assertEqual(e["returncode"], -9)
        self.assertIn("stopped by the system (killed)", e["error"])
        self.assertNotIn("systemd-oomd", e["error"])

    def test_oomd_named_when_it_can_be_the_cause(self):
        w = self.make()
        w.cfg.driver_options["skip_spikesorting"] = True
        d = self.date("260916")
        key = w.state_key(d.resolve(), JOB_NETWORK)
        with mock.patch.object(memguard, "oomd_kills_whole_jobs", return_value=True), \
                mock.patch.object(w, "_memory_limit", return_value=27.3), \
                mock.patch.object(memguard, "wrap", side_effect=lambda cmd, *a: cmd):
            w._run_job(d, JOB_NETWORK, key, [sys.executable, "-c", KILLED], self.root / "k.log")
        self.assertIn("systemd-oomd", w.state.all()[key]["error"])


class OomdCheckTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, memguard, "_oomd", memguard._oomd)

    def run_with(self, active, policy, refresh=True):
        def fake(cmd, **kw):
            out = active if cmd[1] == "is-active" else policy
            return mock.Mock(stdout=out + "\n", returncode=0)
        with mock.patch.object(memguard.subprocess, "run", side_effect=fake), \
                mock.patch.object(memguard.shutil, "which", return_value="/bin/systemctl"):
            return memguard.oomd_kills_whole_jobs(refresh=refresh)

    def test_policy(self):
        self.assertTrue(self.run_with("active", "kill"))
        self.assertFalse(self.run_with("active", "auto"))
        self.assertFalse(self.run_with("inactive", "kill"))

    def test_cached_then_rechecked(self):
        """An administrator can switch it off while the server runs."""
        memguard._oomd = (True, time.time())
        self.assertTrue(self.run_with("active", "auto", refresh=False))      # still cached
        memguard._oomd = (True, time.time() - memguard.OOMD_RECHECK_S - 1)
        self.assertFalse(self.run_with("active", "auto", refresh=False))     # stale: asked again

    def test_this_machine_answers(self):
        self.assertIsInstance(memguard.oomd_kills_whole_jobs(refresh=True), bool)


class HealthWarningTest(unittest.TestCase):
    def test_warning_only_when_it_applies(self):
        import monitor
        self.assertTrue(any("systemd-oomd" in w["text"]
                            for w in monitor.warnings({"oomd_kills_whole_jobs": True,
                                                       "gpu": {"ok": True}})))
        self.assertFalse(any("systemd-oomd" in w["text"]
                             for w in monitor.warnings({"oomd_kills_whole_jobs": False,
                                                        "gpu": {"ok": True}})))


class EndedEarlyTest(WatcherCase):
    def test_dry_run_lets_go_of_the_hand_queued_key(self):
        w = self.make(dry_run=True, run_network=True)
        d = self.date("260825", (1,))
        res = w.queue_folders([str(d)])
        self.assertEqual(len(res["queued"]), 1)
        key = res["queued"][0]["key"]
        self.assertEqual(w.state.status(key), "detected")
        self.assertNotIn(key, w._hand_queued)
        self.assertTrue(w.batches()[0]["finished"])

    def test_cancelled_while_waiting_lets_go_too(self):
        w = self.make(max_concurrent_network=1)
        w.cfg.driver_options["skip_spikesorting"] = True
        w.build_command = lambda run_dir, job: [sys.executable, "-c", SLEEP]
        w.preflight = lambda: {"ok": True}
        a, b = self.date("260825", (1,)), self.date("260828", (1,))
        res = w.queue_folders([str(a), str(b)])
        ka, kb = (q["key"] for q in res["queued"])
        self.assertTrue(self.wait_for(lambda: "running" in (w.state.status(ka), w.state.status(kb))))
        waiting = kb if w.state.status(ka) == "running" else ka
        w.hold([waiting])
        self.assertTrue(self.wait_for(lambda: w.state.status(waiting) == "held"))
        self.assertTrue(self.wait_for(lambda: waiting not in w._hand_queued, timeout=10))
        w.hold()
        self.assertTrue(self.wait_for(lambda: not any(
            e.get("status") in ("running", "dispatched") for e in w.state.all().values())))


if __name__ == "__main__":
    unittest.main()
