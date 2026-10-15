"""Several people on one server: signing in, who started each run (in the
state and the history database), and the warning when a date someone already
analysed is queued again — with stand-in jobs through the real dispatch."""
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
from accounts import Accounts, clean_login
from history import RunHistory
from watcher import JOB_ACTIVITY, JobConfig, Watcher

ANA = {"id": 1, "name": "Ana Lab", "email": "ana@lab.org"}
BO = {"id": 2, "name": "Bo Lab", "email": "bo@lab.org"}
# Writes the results folder it is given, then (optionally) takes a while.
JOB = "import os, sys, time; os.makedirs(sys.argv[1], exist_ok=True); time.sleep(float(sys.argv[2]))"


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.acc = Accounts(Path(self.tmp.name) / "users.sqlite")

    def test_sign_in_creates_and_finds_the_person(self):
        token, user = self.acc.login("  Ana   Lab ", "Ana@Lab.org", ip="10.0.0.5")
        self.assertEqual((user["name"], user["email"]), ("Ana Lab", "ana@lab.org"))
        self.assertEqual(self.acc.user_for(token)["email"], "ana@lab.org")
        self.assertIsNone(self.acc.user_for("not-a-token"))
        self.assertIsNone(self.acc.user_for(None))

    def test_same_email_is_the_same_person(self):
        t1, u1 = self.acc.login("Ana", "ana@lab.org")
        t2, u2 = self.acc.login("Ana Lab", "ANA@lab.org")
        self.assertEqual(u1["id"], u2["id"])
        self.assertNotEqual(t1, t2)                        # one session per browser
        self.assertEqual(self.acc.user_for(t1)["name"], "Ana Lab")
        self.assertEqual(len(self.acc.users()), 1)

    def test_bad_input_is_refused_plainly(self):
        for name, email in (("", "a@b.org"), ("Ana", ""), ("Ana", "not-an-email"),
                            ("Ana", "a@b"), ("x" * 61, "a@b.org")):
            with self.assertRaises(ValueError):
                clean_login(name, email)

    def test_sign_out_ends_the_session(self):
        token, _ = self.acc.login("Ana", "ana@lab.org")
        self.acc.logout(token)
        self.assertIsNone(self.acc.user_for(token))

    def test_who_did_what(self):
        self.acc.record(ANA, "queued for analysis", "260821")
        self.acc.record(None, "something")
        rows = self.acc.audit()
        self.assertEqual(rows[1]["name"], "Ana Lab")
        self.assertEqual(rows[1]["detail"], "260821")
        self.assertIsNone(rows[0]["name"])


class HistoryUpgradeTest(unittest.TestCase):
    def test_old_history_file_gets_the_new_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run_history.sqlite"
            db = sqlite3.connect(str(path))
            db.executescript("CREATE TABLE runs (id TEXT PRIMARY KEY, key TEXT NOT NULL, folder TEXT NOT NULL, "
                             "project TEXT, date TEXT, job TEXT, job_label TEXT, status TEXT, detail TEXT, "
                             "error TEXT, command TEXT, log TEXT, returncode INTEGER, dispatched_at TEXT, "
                             "started_at TEXT, completed_at TEXT, duration_s REAL, settings TEXT, "
                             "imported INTEGER DEFAULT 0, created TEXT NOT NULL);"
                             "INSERT INTO runs(id, key, folder, status, created, settings) VALUES "
                             "('a', '/in/P/260821::network', '/in/P/260821', 'done', '2026-10-01', "
                             "'{\"output_dir\": \"/out\"}');")
            db.commit()
            db.close()
            h = RunHistory(path)
            cols = {r[1] for r in sqlite3.connect(str(path)).execute("PRAGMA table_info(runs)")}
            self.assertTrue({"started_by", "started_by_email", "output_dir"} <= cols)
            prev = h.last_done("/in/P/260821::network")
            self.assertEqual(prev["settings"]["output_dir"], "/out")
            self.assertIsNone(prev["started_by"])
            self.assertEqual(h.list()["runs"][0]["started_by"], None)


class AttributionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.watch = root / "watch" / "Proj"
        self.watch.mkdir(parents=True)
        self.out = root / "out"
        cfg = JobConfig(work_dir=str(root / "work"), watch_dir=str(self.watch),
                        driver_options={"output_dir": str(self.out)},
                        run_network=False, run_activity=True, max_concurrent_activity=1,
                        queue_poll_seconds=1, kill_grace_seconds=2, poll_seconds=1,
                        settle_seconds=0, require_finished_marker=False)
        self.w = Watcher(cfg)
        self.seconds = {}
        self.w.jobs_for = lambda run_dir, max_age=0: [JOB_ACTIVITY]
        self.w.build_command = lambda run_dir, job: [
            sys.executable, "-c", JOB, self.w.cfg.result_dir_for(run_dir, job),
            str(self.seconds.get(run_dir.name, 0))]
        self.addCleanup(self._quiet)

    def _quiet(self):
        self.w.stop()
        self.w.hold()
        self.wait_for(lambda: not any(e.get("status") in ("running", "dispatched")
                                      for e in self.w.state.all().values()))

    def date(self, name, seconds=0):
        d = self.watch / name
        d.mkdir()
        self.seconds[name] = seconds
        return d

    def key(self, d):
        return self.w.state_key(d.resolve(), JOB_ACTIVITY)

    def wait_for(self, cond, timeout=30.0):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.2)
        return False

    def done(self, d):
        return self.wait_for(lambda: self.w.state.status(self.key(d)) == "done")

    def rows(self, d):
        db = sqlite3.connect(str(Path(self.w.work_dir) / "run_history.sqlite"))
        return db.execute("SELECT started_by, started_by_email, output_dir, status FROM runs "
                          "WHERE key=? ORDER BY created", (self.key(d),)).fetchall()

    def test_queued_run_names_who_started_it(self):
        d = self.date("260821")
        res = self.w.queue_folders([str(d)], user=ANA)
        self.assertEqual(len(res["queued"]), 1)
        self.assertTrue(self.done(d))
        e = self.w.state.get(self.key(d))
        self.assertEqual((e["started_by"], e["started_by_email"]), ("Ana Lab", "ana@lab.org"))
        self.assertTrue(e["dispatched_at"])
        out = str(self.out / "Proj" / "ActivityScan" / "260821")
        self.assertEqual(self.rows(d), [("Ana Lab", "ana@lab.org", out, "done")])
        run = self.w.history.list()["runs"][0]
        self.assertEqual(run["started_by"], "Ana Lab")
        # Shown on the status the page polls.
        row = next(r for r in self.w.snapshot()["runs"] if r["path"] == self.key(d))
        self.assertEqual(row["started_by"], "Ana Lab")

    def test_second_person_is_told_who_analysed_it_and_where(self):
        d = self.date("260822")
        self.w.queue_folders([str(d)], user=ANA)
        self.assertTrue(self.done(d))
        ins = self.w.inspect_folders([str(d)])[0]["jobs"][0]
        self.assertTrue(ins["analysed"])
        self.assertEqual(ins["previous"]["by"], "Ana Lab")
        self.assertTrue(ins["previous"]["output"].endswith("ActivityScan/260822"))

        res = self.w.queue_folders([str(d)], user=BO)
        self.assertEqual(res["queued"], [])
        reason = res["skipped"][0]["reason"]
        self.assertIn("already analysed by Ana Lab", reason)
        self.assertIn(str(self.out / "Proj" / "ActivityScan" / "260822"), reason)

        # Run again anyway: allowed, and recorded as Bo's.
        res = self.w.queue_folders([str(d)], rerun=True, user=BO)
        self.assertEqual(len(res["queued"]), 1)
        self.assertTrue(self.wait_for(lambda: len(self.rows(d)) == 2 and self.rows(d)[1][3] == "done"))
        self.assertEqual([r[0] for r in self.rows(d)], ["Ana Lab", "Bo Lab"])
        self.assertEqual(self.w.previous_analysis(d, JOB_ACTIVITY)["by"], "Bo Lab")

    def test_still_known_after_the_job_list_is_cleared(self):
        d = self.date("260823")
        self.w.queue_folders([str(d)], user=ANA)
        self.assertTrue(self.done(d))
        self.w.state.reset(self.key(d))              # "Clear finished" in the page
        res = self.w.queue_folders([str(d)], user=BO)
        self.assertEqual(res["queued"], [])
        self.assertIn("Ana Lab", res["skipped"][0]["reason"])

    def test_deleted_results_count_as_not_analysed(self):
        d = self.date("260824")
        self.w.queue_folders([str(d)], user=ANA)
        self.assertTrue(self.done(d))
        shutil.rmtree(self.out / "Proj" / "ActivityScan" / "260824")
        ins = self.w.inspect_folders([str(d)])[0]["jobs"][0]
        self.assertFalse(ins["analysed"])
        self.assertFalse(ins["previous"]["output_exists"])
        res = self.w.queue_folders([str(d)], user=BO)
        self.assertEqual(len(res["queued"]), 1)
        self.assertTrue(self.wait_for(lambda: len(self.rows(d)) == 2 and self.rows(d)[1][3] == "done"))
        self.assertEqual(self.rows(d)[1][0], "Bo Lab")

    def test_queued_while_someone_elses_run_is_going(self):
        d = self.date("260825", seconds=30)
        self.w.queue_folders([str(d)], user=ANA)
        self.assertTrue(self.wait_for(lambda: self.w.state.status(self.key(d)) == "running"))
        ins = self.w.inspect_folders([str(d)])[0]["jobs"][0]
        self.assertEqual(ins["in_flight"]["by"], "Ana Lab")
        res = self.w.queue_folders([str(d)], rerun=True, user=BO)
        self.assertEqual(res["queued"], [])
        self.assertIn("started by Ana Lab", res["skipped"][0]["reason"])

    def test_two_people_queue_one_after_another(self):
        a, b, c = self.date("260826", 1), self.date("260827", 1), self.date("260828", 1)
        self.w.queue_folders([str(a), str(b)], user=ANA)
        self.w.queue_folders([str(c)], user=BO)
        for d in (a, b, c):
            self.assertTrue(self.done(d), d.name)
        self.assertEqual([self.rows(d)[0][0] for d in (a, b, c)], ["Ana Lab", "Ana Lab", "Bo Lab"])
        # One slot: they ran one at a time.
        starts = sorted((self.w.state.get(self.key(d))["started_at"],
                         self.w.state.get(self.key(d))["completed_at"]) for d in (a, b, c))
        for (s1, e1), (s2, _) in zip(starts, starts[1:]):
            self.assertLessEqual(e1, s2)

    def test_the_same_date_queued_by_two_people_at_once_runs_once(self):
        d = self.date("260829", seconds=5)
        results = []
        go = threading.Barrier(2)

        def queue(user):
            go.wait()
            results.append(self.w.queue_folders([str(d)], user=user))
        ts = [threading.Thread(target=queue, args=(u,)) for u in (ANA, BO)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(sum(len(r["queued"]) for r in results), 1)
        self.assertTrue(self.done(d))
        self.assertEqual(len(self.rows(d)), 1)

    def test_watched_dates_are_started_by_whoever_is_watching(self):
        self.w.start(user=BO)
        d = self.date("260830")
        self.assertTrue(self.done(d))
        self.assertEqual(self.rows(d)[0][0], "Bo Lab")


    def test_resume_is_not_blocked_by_the_earlier_run(self):
        """Analysed once, queued again and put on hold: Resume continues that
        run; it is not a repeat of the earlier one."""
        d = self.date("260831")
        self.w.queue_folders([str(d)], user=ANA)
        self.assertTrue(self.done(d))
        self.seconds["260831"] = 30
        self.w.queue_folders([str(d)], rerun=True, user=BO)
        self.assertTrue(self.wait_for(lambda: self.w.state.status(self.key(d)) == "running"))
        self.w.hold([self.key(d)])
        self.assertTrue(self.wait_for(lambda: self.w.state.status(self.key(d)) == "held"))
        self.seconds["260831"] = 0
        res = self.w.queue_folders([str(d)], user=ANA)            # Resume
        self.assertEqual(len(res["queued"]), 1, res["skipped"])
        self.assertTrue(self.done(d))
        self.assertEqual(self.rows(d)[-1][0], "Ana Lab")


class StartDuringResetTest(unittest.TestCase):
    """Starting to watch takes a while; a queue reset or pause pressed by
    someone else meanwhile must still leave watching off."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "watch").mkdir()
        self.w = Watcher(JobConfig(work_dir=str(root / "work"), watch_dir=str(root / "watch"),
                                   run_network=False, run_activity=True))
        self.w.warn_about_foreign_pipelines = lambda: time.sleep(2)   # a slow start
        self.addCleanup(self.w.stop)

    def _start_then(self, action):
        t = threading.Thread(target=self.w.start, kwargs={"user": ANA})
        t.start()
        time.sleep(0.5)                     # the start is under way, not finished
        res = action()
        t.join(10)
        time.sleep(0.3)
        return res

    def test_reset_during_start_leaves_watching_off(self):
        res = self._start_then(self.w.reset_queue)
        self.assertTrue(res["paused_watching"])
        self.assertFalse(self.w.is_running)

    def test_pause_during_start_leaves_watching_off(self):
        self._start_then(self.w.stop)
        self.assertFalse(self.w.is_running)


class HoldWhilePreparingTest(unittest.TestCase):
    """A run held while its folder is still being prepared (old sorter output
    cleared, results staged) ends there and never starts its analysis."""

    def test_held_before_the_analysis_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "watch" / "260901").mkdir(parents=True)
            marker = root / "started"
            w = Watcher(JobConfig(work_dir=str(root / "work"), watch_dir=str(root / "watch"),
                                  driver_options={"output_dir": str(root / "out"),
                                                  "skip_spikesorting": True},
                                  run_network=True, run_activity=False, dry_run=False))
            w.preflight = lambda force=False: {"ok": True}
            w.jobs_for = lambda run_dir, max_age=0: ["network"]
            w.clear_stale_sorter_output = lambda run_dir: time.sleep(2) or []    # slow preparation
            w.build_command = lambda run_dir, job: [sys.executable, "-c",
                                                    f"open({str(marker)!r}, 'w').write('x')"]
            d = root / "watch" / "260901"
            key = w.state_key(d.resolve(), "network")
            w.queue_folders([str(d)], user=ANA)
            time.sleep(0.5)
            self.assertEqual(w.state.status(key), "dispatched")
            w.hold([key])
            end = time.time() + 10
            while time.time() < end and w.state.status(key) != "held":
                time.sleep(0.1)
            self.assertEqual(w.state.status(key), "held")
            time.sleep(1)
            self.assertFalse(marker.exists(), "the analysis must not have started")
            self.assertEqual(w._active["network"], 0)

