"""Memory ceiling for analysis jobs: the arithmetic, the command wrapper, and a
real limited job whose greedy "well" is stopped while the rest carries on."""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import _path  # noqa: F401
import memguard
from watcher import JOB_ACTIVITY, JOB_NETWORK, JobConfig, Watcher

# A stand-in for the pipeline driver: three "wells", each its own process, as
# the real driver runs them. The second asks for far more memory than allowed.
DRIVER = textwrap.dedent('''
    import subprocess, sys
    for well, mb in (("well000", 20), ("well001", 600), ("well002", 20)):
        code = f"a = bytearray({mb} * 2**20); a[::4096] = b'x' * len(a[::4096])"
        try:
            subprocess.run([sys.executable, "-c", code], check=True)
            print("Processing Complete for", well, flush=True)
        except subprocess.CalledProcessError as e:
            print("Subprocess failed for", well, flush=True)
            print("Exit Code:", e.returncode, flush=True)
''')


class ArithmeticTest(unittest.TestCase):
    def test_total_ram(self):
        self.assertAlmostEqual(memguard.total_ram_gb("MemTotal:       66060288 kB\n"), 63.0)
        self.assertEqual(memguard.total_ram_gb("nothing useful"), 0.0)
        self.assertGreater(memguard.total_ram_gb(), 0)

    def test_limit(self):
        r = memguard.resolve_limit_gb
        self.assertEqual(r(0, 63, 2), 27.5)          # automatic, shared by two jobs
        self.assertEqual(r(0, 63, 1), 55.0)
        self.assertEqual(r(0, 8, 4), memguard.MIN_AUTO_GB)
        self.assertEqual(r(40, 63, 2), 40.0)         # an explicit number wins
        self.assertIsNone(r(-1, 63, 2))              # off
        self.assertIsNone(r(0, 0, 2))                # RAM unknown: no guess

    def test_own_unit(self):
        u = memguard.own_service_unit
        self.assertEqual(u("0::/user.slice/user-1011.slice/user@1011.service/app.slice/mea-ui.service\n"),
                         "mea-ui.service")
        self.assertIsNone(u("0::/user.slice/user-1011.slice/user@1011.service/app.slice/vte-spawn-1.scope\n"))
        self.assertIsNone(u("0::/user.slice/user-1011.slice/user@1011.service\n"))

    def test_wrap(self):
        cmd = memguard.wrap(["python3", "driver.py", "a b"], 27.5, "mea-ui.service")
        self.assertEqual(cmd[-3:], ["python3", "driver.py", "a b"])
        self.assertEqual(cmd[-4], "--")
        self.assertIn("MemoryMax=28160M", cmd)
        self.assertIn("MemorySwapMax=0", cmd)
        self.assertIn("BindsTo=mea-ui.service", cmd)
        self.assertNotIn("BindsTo=", " ".join(memguard.wrap(["true"], 1)))

    def test_count_killed(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "x.log"
            log.write_text("ok\nERROR: Exit Code: -9\nExit Code: 1\nExit Code: -9\n")
            self.assertEqual(memguard.count_killed(log), 2)
            self.assertEqual(memguard.count_killed(Path(d) / "missing.log"), 0)


class WatcherSettingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(setattr, memguard, "_available", memguard._available)

    def watcher(self, **kw):
        return Watcher(JobConfig(work_dir=self.tmp.name, **kw), reconcile=False)

    def test_default_is_automatic(self):
        self.assertEqual(JobConfig().memory_limit_gb, 0.0)

    def test_which_jobs_are_limited(self):
        memguard._available = True
        w = self.watcher(memory_limit_gb=12, max_concurrent_network=2)
        self.assertEqual(w._memory_limit(JOB_NETWORK), 12.0)
        self.assertIsNone(w._memory_limit(JOB_ACTIVITY))
        self.assertIsNone(self.watcher(memory_limit_gb=-1)._memory_limit(JOB_NETWORK))

    def test_no_systemd_means_no_limit(self):
        memguard._available = False
        self.assertIsNone(self.watcher(memory_limit_gb=12)._memory_limit(JOB_NETWORK))

    def test_old_config_file_loads(self):
        w = self.watcher()
        p = Path(self.tmp.name) / "job.json"
        w.cfg.save(p)
        import json
        data = json.loads(p.read_text())
        data.pop("memory_limit_gb")
        p.write_text(json.dumps(data))
        self.assertEqual(JobConfig.load(p).memory_limit_gb, 0.0)


@unittest.skipUnless(memguard.available(), "cannot start a memory-limited scope here")
class RealLimitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.driver = Path(self.tmp.name) / "driver.py"
        self.driver.write_text(DRIVER)

    def test_same_process_and_exit_code(self):
        p = subprocess.Popen(memguard.wrap([sys.executable, "-c", "import os; print(os.getpid())"], 0.2),
                             stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate(timeout=60)
        self.assertEqual(int(out), p.pid)
        self.assertEqual(subprocess.run(memguard.wrap([sys.executable, "-c", "raise SystemExit(7)"], 0.2)).returncode, 7)

    def test_without_a_limit_every_well_finishes(self):
        out = subprocess.run([sys.executable, str(self.driver)], capture_output=True, text=True, timeout=120).stdout
        self.assertEqual(out.count("Processing Complete"), 3)

    def test_greedy_well_is_stopped_and_the_rest_carry_on(self):
        """Through the watcher's own supervisor, as a real job runs."""
        w = Watcher(JobConfig(work_dir=self.tmp.name), reconcile=False)
        log = Path(self.tmp.name) / "job.log"
        cmd = memguard.wrap([sys.executable, str(self.driver)], 0.2)
        with open(log, "w") as fh:
            rc, stall = w._supervise(cmd, dict(os.environ), fh, log, "260101", "Network", "k")
        text = log.read_text()
        self.assertEqual((rc, stall), (0, None))
        self.assertIn("Processing Complete for well000", text)
        self.assertIn("Subprocess failed for well001", text)
        self.assertIn("Processing Complete for well002", text)
        self.assertEqual(memguard.count_killed(log), 1)

    def test_whole_job_ends_done_with_a_note(self):
        """The full job path: log header, limited run, and the note on the run."""
        run_dir = Path(self.tmp.name) / "260101"
        run_dir.mkdir()
        cfg = JobConfig(work_dir=self.tmp.name, memory_limit_gb=0.2, gpu_cooldown_seconds=0)
        cfg.driver_options["skip_spikesorting"] = True
        w = Watcher(cfg, reconcile=False)
        key = w.state_key(run_dir.resolve(), JOB_NETWORK)
        log = Path(self.tmp.name) / "whole.log"
        w._run_job(run_dir, JOB_NETWORK, key, [sys.executable, str(self.driver)], log)
        entry = w.state.all()[key]
        text = log.read_text()
        self.assertEqual(entry["status"], "done", entry)
        self.assertIn("memory ceiling: 0.2 GB", text)
        self.assertIn("Processing Complete for well002", text)
        self.assertIn("1 well(s) were stopped", entry["detail"])


if __name__ == "__main__":
    unittest.main()
