"""Taking runs off the queue: Hold, Resume, Reset queue and Stop all, with real
(stand-in) jobs going through the watcher's own dispatch and supervisor."""
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
from watcher import JOB_ACTIVITY, JobConfig, Watcher

SLEEP = "import time, sys; print('started', flush=True); time.sleep(float(sys.argv[1]))"


class QueueResetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.watch = root / "watch"
        self.watch.mkdir()
        cfg = JobConfig(work_dir=str(root / "work"), watch_dir=str(self.watch),
                        run_network=False, run_activity=True, max_concurrent_activity=1,
                        queue_poll_seconds=1, kill_grace_seconds=2)
        self.w = Watcher(cfg)
        self.seconds = {}                       # folder name -> how long its job runs
        self.w.build_command = lambda run_dir, job: [
            sys.executable, "-c", SLEEP, str(self.seconds.get(run_dir.name, 60))]
        self.addCleanup(self._stop_all)

    def _stop_all(self):
        self.w.hold()
        self.wait_for(lambda: not any(e.get("status") in ("running", "dispatched")
                                      for e in self.w.state.all().values()), timeout=30)

    def date(self, name, seconds=60):
        d = self.watch / name
        d.mkdir()
        self.seconds[name] = seconds
        return d

    def key(self, d):
        return self.w.state_key(d.resolve(), JOB_ACTIVITY)

    def status(self, d):
        return self.w.state.status(self.key(d))

    def wait_for(self, cond, timeout=30.0):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.2)
        return False

    def history_status(self, d):
        db = sqlite3.connect(str(Path(self.w.work_dir) / "run_history.sqlite"))
        rows = db.execute("SELECT status FROM runs WHERE key=? ORDER BY created", (self.key(d),)).fetchall()
        return [r[0] for r in rows]

    # ------------------------------------------------------------------ hold
    def test_waiting_run_leaves_the_queue_without_running(self):
        a, b = self.date("260101"), self.date("260102")
        self.w.dispatch(a, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "running"))
        self.w.dispatch(b, JOB_ACTIVITY)                 # waits: one slot only
        time.sleep(1.5)
        self.assertEqual(self.status(b), "dispatched")

        res = self.w.hold([self.key(b)])
        self.assertEqual(res["removed"], [self.key(b)])
        self.assertTrue(self.wait_for(lambda: self.status(b) == "held"))
        self.assertNotIn("started_at", self.w.state.get(self.key(b)))
        self.assertEqual(self.status(a), "running")      # the other run is untouched

    def test_running_run_is_stopped_and_held(self):
        a = self.date("260101")
        self.w.dispatch(a, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "running"))
        t0 = time.time()
        res = self.w.hold([self.key(a)])
        self.assertEqual(res["stopping"], [self.key(a)])
        self.assertTrue(self.wait_for(lambda: self.status(a) == "held", timeout=20))
        self.assertLess(time.time() - t0, 15, "a stop should take seconds, not minutes")
        self.assertEqual(self.w._active[JOB_ACTIVITY], 0)
        self.assertEqual(self.history_status(a), ["held"])

    def test_interrupted_run_is_held_and_not_picked_up(self):
        a = self.date("260101")
        self.w.state.update(self.key(a), status="interrupted", job=JOB_ACTIVITY, run=a.name)
        self.w.hold([self.key(a)])
        self.assertEqual(self.status(a), "held")
        self.assertTrue(self.w.state.is_claimed(self.key(a)))
        self.assertEqual(self.history_status(a), [], "holding an interrupted date is not a new run")

    def test_finished_runs_are_not_touched(self):
        a = self.date("260101")
        self.w.state.update(self.key(a), status="done", job=JOB_ACTIVITY, run=a.name)
        res = self.w.hold([self.key(a)])
        self.assertEqual(res, {"stopping": [], "removed": [], "held": []})
        self.assertEqual(self.status(a), "done")

    # ---------------------------------------------------------------- resume
    def test_resume_is_queueing_again(self):
        a = self.date("260101", seconds=0.5)
        self.w.state.update(self.key(a), status="held", job=JOB_ACTIVITY, run=a.name)
        self.w.jobs_for = lambda run_dir, max_age=0: [JOB_ACTIVITY]
        res = self.w.queue_folders([str(a)])
        self.assertEqual(len(res["queued"]), 1)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "done"))

    # ----------------------------------------------------------- reset queue
    def test_reset_queue_holds_everything_unfinished(self):
        run, wait, intr, done = (self.date(n) for n in ("260101", "260102", "260103", "260104"))
        self.w.state.update(self.key(intr), status="interrupted", job=JOB_ACTIVITY, run=intr.name)
        self.w.state.update(self.key(done), status="done", job=JOB_ACTIVITY, run=done.name)
        self.w.dispatch(run, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(run) == "running"))
        self.w.dispatch(wait, JOB_ACTIVITY)

        res = self.w.reset_queue()
        self.assertEqual((len(res["stopping"]), len(res["removed"]), len(res["held"])), (1, 1, 1))
        self.assertTrue(self.wait_for(lambda: self.status(run) == "held" and self.status(wait) == "held",
                                      timeout=20))
        self.assertEqual(self.status(intr), "held")
        self.assertEqual(self.status(done), "done")

    def test_reset_queue_stops_watching_and_a_scan_starts_nothing(self):
        a = self.date("260101")
        self.w.state.update(self.key(a), status="interrupted", job=JOB_ACTIVITY, run=a.name)
        self.w.cfg.skip_settle_for_existing = True
        self.w.start()
        self.assertTrue(self.w.is_running)
        res = self.w.reset_queue()
        self.assertTrue(res["paused_watching"])
        self.assertFalse(self.w.is_running)
        self.w.scan_once()
        self.assertEqual(self.status(a), "held")

    def test_cancelled_batch_builds_no_report(self):
        a = self.date("260101")
        fired = []
        self.w.jobs_for = lambda run_dir, max_age=0: [JOB_ACTIVITY]
        self.w.queue_folders([str(a)], on_complete=fired.append)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "running"))
        self.w.reset_queue()
        self.assertTrue(self.wait_for(lambda: self.status(a) == "held", timeout=20))
        time.sleep(0.5)
        self.assertEqual(fired, [])
        self.assertTrue(self.w.batches()[0]["finished"])

    # ------------------------------------------------- start with interrupted
    def test_start_can_keep_interrupted_dates_on_hold(self):
        a = self.date("260101")
        self.w.state.update(self.key(a), status="interrupted", job=JOB_ACTIVITY, run=a.name)
        self.w.start(hold_interrupted=True)
        self.addCleanup(self.w.stop)
        self.assertEqual(self.status(a), "held")
        self.assertEqual(self.w.resumable(), [])

    # -------------------------------------------------------------- stop all
    def test_stop_all_then_queue_again_runs_to_the_end(self):
        """Stop all used to leave a flag set that cancelled the next run
        queued by hand within half a minute."""
        a, b = self.date("260101"), self.date("260102", seconds=8)
        self.w.dispatch(a, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "running"))
        self.w.cancel_all()
        self.assertTrue(self.wait_for(lambda: self.status(a) == "failed", timeout=20))
        self.assertIn("cancelled", self.w.state.get(self.key(a))["error"])

        self.w.dispatch(b, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(b) in ("done", "failed"), timeout=40))
        self.assertEqual(self.status(b), "done", self.w.state.get(self.key(b)))

    def test_a_new_dispatch_clears_an_old_cancellation(self):
        a = self.date("260101", seconds=0.5)
        self.w._cancel[self.key(a)] = "held"          # left over, nothing running
        self.w.dispatch(a, JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: self.status(a) == "done"))


if __name__ == "__main__":
    unittest.main()
