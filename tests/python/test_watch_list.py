"""Watching several projects at once.

Two or three projects record in the same month, looked after by different
people, so one server watches a list of project folders with one queue. These
tests check that picking the wrong folder is caught, that every project is
scanned and credited to whoever added it, that the read-only guards cover
every watched folder, and that the queue is first come, first served.
"""
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
from watcher import JOB_ACTIVITY, JobConfig, Watcher, check_watch_folder

SLEEP = "import time, sys; time.sleep(float(sys.argv[1]))"
ANA = {"name": "Ana", "email": "ana@lab.edu"}
BEN = {"name": "Ben", "email": "ben@lab.edu"}


def finished_run(date: Path, chip="M07037", run="000001"):
    """A recording folder as MaxWell leaves it: data, and the finished mark."""
    r = date / chip / "Network" / run
    r.mkdir(parents=True)
    (r / "data.raw.h5").write_bytes(b"x" * 64)
    (r / "mxassay.metadata").write_text("[runtime]\nfinished=2026-11-05\n")


class Lab(unittest.TestCase):
    """<lab>/<project>/<project>/<date>/<chip>/Network/<run>, like the NAS."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lab = self.root / "nas" / "BenShalomLab"

    def project(self, name, dates=()):
        p = self.lab / name / name
        p.mkdir(parents=True)
        for d in dates:
            finished_run(p / d)
        return p


class CheckFolderTest(Lab):
    def test_project_folder_is_accepted(self):
        p = self.project("B6J", ["260929", "261001"])
        r = check_watch_folder(p)
        self.assertTrue(r["ok"])
        self.assertEqual((r["kind"], r["dates"]), ("project", 2))

    def test_lab_folder_lists_its_projects(self):
        a = self.project("B6J", ["260929"])
        b = self.project("IPN", ["260825"])
        r = check_watch_folder(self.lab)
        self.assertFalse(r["ok"])
        self.assertEqual(r["kind"], "lab")
        self.assertEqual(r["suggestions"], [str(a), str(b)])

    def test_outer_project_folder_points_one_level_down(self):
        p = self.project("B6J", ["260929"])
        r = check_watch_folder(p.parent)
        self.assertFalse(r["ok"])
        self.assertEqual((r["kind"], r["suggestions"]), ("outer", [str(p)]))

    def test_date_folder_points_to_its_project(self):
        p = self.project("B6J", ["260929"])
        r = check_watch_folder(p / "260929")
        self.assertFalse(r["ok"])
        self.assertEqual((r["kind"], r["suggestions"]), ("date", [str(p)]))

    def test_new_project_without_dates_is_accepted(self):
        r = check_watch_folder(self.project("New"))
        self.assertTrue(r["ok"])
        self.assertEqual(r["kind"], "new")

    def test_missing_folder(self):
        r = check_watch_folder(self.root / "nope")
        self.assertFalse(r["ok"])
        self.assertEqual(r["kind"], "missing")

    def test_check_only_reads(self):
        p = self.project("B6J", ["260929"])
        before = sorted((str(x), x.stat().st_mtime_ns) for x in self.lab.rglob("*"))
        for target in (self.lab, p.parent, p, p / "260929"):
            check_watch_folder(target)
        self.assertEqual(sorted((str(x), x.stat().st_mtime_ns) for x in self.lab.rglob("*")), before)


class ConfigTest(Lab):
    def test_single_folder_becomes_the_first_project(self):
        p = self.project("B6J")
        cfg = JobConfig(watch_dir=str(p))
        self.assertEqual(cfg.watch_dir, "")
        self.assertEqual([e["path"] for e in cfg.watch_dirs], [str(p)])
        self.assertFalse(cfg.watch_dirs[0]["paused"])

    def test_config_saved_before_the_list_loads(self):
        p = self.project("B6J")
        f = self.root / "job.json"
        f.write_text(json.dumps({"watch_dir": str(p), "run_network": True}))
        cfg = JobConfig.load(f)
        self.assertEqual(cfg.watched(), [p])
        cfg.save(f)
        saved = json.loads(f.read_text())
        self.assertEqual(saved["watch_dir"], "")
        self.assertEqual([e["path"] for e in saved["watch_dirs"]], [str(p)])
        self.assertEqual(JobConfig.load(f).watched(), [p], "loads the same again")

    def test_adding_the_same_folder_twice_keeps_one(self):
        p = self.project("B6J")
        cfg = JobConfig()
        cfg.add_watch(str(p), ANA)
        cfg.add_watch(str(p) + "/", BEN)
        self.assertEqual(len(cfg.watch_dirs), 1)
        self.assertEqual(cfg.watch_dirs[0]["added_by"], "Ana")

    def test_outputs_inside_any_project_are_refused_even_paused(self):
        a, b = self.project("A"), self.project("B")
        cfg = JobConfig(work_dir=str(self.root / "work"),
                        driver_options={"output_dir": str(b / "results")})
        cfg.add_watch(str(a))
        cfg.add_watch(str(b))["paused"] = True
        errs = cfg.validate()
        self.assertTrue(any("inside the watched project folder" in e and str(b) in e for e in errs), errs)
        self.assertFalse((b / "results").exists(), "nothing was created in the input")

    def test_missing_folder_only_blocks_when_active(self):
        cfg = JobConfig(work_dir=str(self.root / "work"),
                        driver_options={"output_dir": str(self.root / "out")})
        cfg.add_watch(str(self.root / "gone"))
        self.assertTrue(any("does not exist" in e for e in cfg.validate()))
        cfg.watch_dirs[0]["paused"] = True
        self.assertFalse(any("does not exist" in e for e in cfg.validate()))

    def test_watching_needs_an_active_project(self):
        cfg = JobConfig(work_dir=str(self.root / "work"),
                        driver_options={"output_dir": str(self.root / "out")})
        self.assertIn("Add a project", cfg.validate_watching()[0])
        cfg.add_watch(str(self.project("A")))["paused"] = True
        self.assertIn("paused", cfg.validate_watching()[0])
        self.assertFalse(any("project" in e for e in cfg.validate()),
                         "queueing by hand needs no watched project")


class WatchTest(Lab):
    """Several projects through the watcher's own scan, dispatch and queue,
    with stand-in jobs (an activity scan that only sleeps)."""

    def make(self, **kw):
        kw.setdefault("work_dir", str(self.root / "work"))
        kw.setdefault("run_network", False)
        kw.setdefault("run_activity", True)
        kw.setdefault("require_finished_marker", True)
        kw.setdefault("skip_settle_for_existing", True)
        kw.setdefault("queue_poll_seconds", 1)
        kw.setdefault("kill_grace_seconds", 2)
        w = Watcher(JobConfig(**kw), reconcile=False)
        w.cfg.activity_subfolder = "Network"      # the fixtures only have Network
        self.seconds = {}
        w.build_command = lambda run_dir, job: [
            sys.executable, "-c", SLEEP, str(self.seconds.get(run_dir.name, 0.2))]
        self.addCleanup(lambda: (w.stop(), w.hold()))
        return w

    def wait_for(self, cond, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.1)
        return False

    def test_every_active_project_is_scanned_and_credited(self):
        a = self.project("B6J", ["260929"])
        b = self.project("IPN", ["260825", "260826"])
        c = self.project("Old", ["250101"])
        w = self.make(dry_run=True)
        w.cfg.add_watch(str(a), ANA)
        w.cfg.add_watch(str(b), BEN)
        w.cfg.add_watch(str(c), ANA)["paused"] = True
        w._preexisting = {str(d.resolve()) for d, _ in w.scan_candidates(max_age=0)}
        w.scan_once()
        st = {Path(k.split("::")[0]).name: e for k, e in w.state.all().items()}
        self.assertEqual(sorted(st), ["260825", "260826", "260929"], "paused project skipped")
        self.assertEqual(st["260929"]["started_by"], "Ana")
        self.assertEqual(st["260825"]["started_by"], "Ben")
        self.assertTrue(all(e["status"] == "detected" for e in st.values()))

        ps = {p["name"]: p for p in w.projects_status()}
        self.assertEqual((ps["IPN"]["dates_found"], ps["IPN"]["counts"]), (2, {"detected": 2}))
        self.assertEqual(ps["B6J"]["added_by"], "Ana")
        self.assertIsNone(ps["Old"]["last_checked"], "a paused project is not listed")
        self.assertTrue(ps["B6J"]["last_checked"])

    def test_first_come_first_served_across_projects(self):
        a = self.project("A", ["260901", "260903"])
        b = self.project("B", ["260902"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a), ANA)
        w.cfg.add_watch(str(b), BEN)
        order = [a / "260903", b / "260902", a / "260901"]
        for d in order:
            self.seconds[d.name] = 0.6
        # Started one after the other, as the scan or a person would.
        for d in order:
            w.dispatch(d, JOB_ACTIVITY)
            time.sleep(0.05)
        line = [r["run"] for r in sorted((r for r in w.snapshot()["runs"] if r.get("line_position")),
                                         key=lambda r: r["line_position"])]
        self.assertEqual(line, ["260902", "260901"], "the first one runs, the rest wait in order")
        self.assertTrue(self.wait_for(lambda: all(e.get("status") == "done"
                                                  for e in w.state.all().values()), 60))
        started = sorted(w.state.all().values(), key=lambda e: e["started_at"])
        self.assertEqual([e["run"] for e in started], [d.name for d in order])

    def test_the_line_is_kept_under_contention(self):
        """Many jobs waiting on one slot still start in the order they came."""
        a = self.project("A", [f"2609{i:02d}" for i in range(1, 7)])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a))
        dates = sorted(a.iterdir())
        # Longer than the one-second wait between tries, so waiting jobs
        # time out and ask again while they wait.
        for d in dates:
            self.seconds[d.name] = 1.3
            w.dispatch(d, JOB_ACTIVITY)
            time.sleep(0.05)
        self.assertTrue(self.wait_for(lambda: all(e.get("status") == "done"
                                                  for e in w.state.all().values()), 60))
        started = sorted(w.state.all().values(), key=lambda e: e["started_at"])
        self.assertEqual([e["run"] for e in started], [d.name for d in dates])

    def test_a_held_job_leaves_the_line(self):
        a = self.project("A", ["260901", "260902", "260903"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a))
        d1, d2, d3 = sorted(a.iterdir())
        self.seconds.update({"260901": 1.0, "260902": 30, "260903": 0.2})
        for d in (d1, d2, d3):
            w.dispatch(d, JOB_ACTIVITY)
        key2 = w.state_key(d2.resolve(), JOB_ACTIVITY)
        w.hold([key2])
        self.assertTrue(self.wait_for(lambda: w.state.status(
            w.state_key(d3.resolve(), JOB_ACTIVITY)) == "done", 30), "the next one is not blocked")
        self.assertEqual(w.state.status(key2), "held")
        self.assertIsNone(w.queue_position(JOB_ACTIVITY, key2))

    def test_guards_cover_every_watched_project(self):
        a, b = self.project("A", ["260901"]), self.project("B", ["260902"])
        w = self.make(stage_locally=True, scratch_dir=str(self.root / "nas"))
        w.cfg.add_watch(str(a))
        w.cfg.add_watch(str(b))["paused"] = True
        for target in (b, b / "260902", a / "260901"):
            self.assertFalse(w._may_delete(target.resolve()), target)
        self.assertIsNone(w._copy_input(b / "260902", b / "260902" / "scratch", "k"))
        self.assertFalse((b / "260902" / "scratch").exists())


if __name__ == "__main__":
    unittest.main()
