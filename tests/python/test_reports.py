"""Reports when only the activity scan was run: the report command accepts the
project, the report builds with an empty Network page, the package tells
Claude what is expected, and a date the watcher finished on its own is
announced for its report (a hand-queued one is reported by its batch)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
import handoff
from watcher import JOB_ACTIVITY, JobConfig, Watcher

ROOT = Path(__file__).resolve().parents[2]
MAKE_REPORT = ROOT / "orchestration" / "report" / "make_report.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "activity_only"
# The report needs pandas, matplotlib and scipy: MEA-Analysis's environment.
REPORT_PY = os.environ.get("MEA_REPORT_PYTHON",
                           str(ROOT.parent / "MEA-Analysis" / ".venv" / "bin" / "python3"))

sys.path.insert(0, str(MAKE_REPORT.parent))
import make_report  # noqa: E402


class ActivityOnlyReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.results = Path(self.tmp.name) / "results"
        self.project = self.results / "Test_Organoids_PVS"
        shutil.copytree(FIXTURE, self.project)

    def run_report(self, *args):
        # A server that is not there: status unknown, so nothing is refused.
        env = dict(os.environ, MEA_STATUS_URL="http://127.0.0.1:9/api/status")
        return subprocess.run([REPORT_PY, str(MAKE_REPORT), *args], capture_output=True,
                              text=True, env=env, timeout=600)

    def test_activity_only_folder_is_a_project(self):
        self.assertTrue(make_report.is_project_dir(self.project))
        self.assertFalse(make_report.is_project_dir(self.project / "ActivityScan"))
        self.assertFalse(make_report.is_project_dir(self.results / "missing"))

    def test_results_folder_names_the_project(self):
        r = self.run_report("--project-dir", str(self.results), "--list")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Test_Organoids_PVS", r.stdout + r.stderr)
        self.assertNotIn("ActivityScan", (r.stdout + r.stderr).split("one of:")[-1])

    def test_list_shows_the_scan_dates(self):
        r = self.run_report("--project-dir", str(self.project), "--list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"260821 .* 0 +2")

    @unittest.skipUnless(Path(REPORT_PY).exists(), "needs MEA-Analysis's Python for the report")
    def test_report_builds_without_network_results(self):
        r = self.run_report("--project-dir", str(self.project), "--dates", "260821")
        self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])
        res = json.loads(r.stdout[r.stdout.rfind("\n{") + 1:])
        self.assertEqual((res["network_wells"], res["activity_runs"]), (0, 2))
        self.assertEqual(res["built"], {"260821": True})
        page = Path(res["report"]).read_text()
        self.assertIn("No Network analysis results", page)
        self.assertIn("Test_Organoids_PVS", page)
        self.assertIn("'activity')", page.split("show(location.hash")[1][:200],
                      "an activity-only report should open on the Activity page")
        self.assertTrue((Path(res["report"]).parent / "tables" / "activity_qc.csv").is_file())


class PromptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pkg = Path(self.tmp.name)

    def prompt(self, net, act, built=None):
        return handoff.write_prompt(self.pkg, project="P", dates=["260821"], network_wells=net,
                                    activity_runs=act, built=built or {"260821": True},
                                    results_dir="/r", input_dir="/in").read_text()

    def test_activity_only_says_it_is_expected(self):
        t = self.prompt(0, 6)
        self.assertIn("Activity scan only", t)
        self.assertIn("do not ask about it", t)
        self.assertIn("already built", t)
        self.assertIn("21 Aug 2026", t)

    def test_both_analyses(self):
        t = self.prompt(14, 5)
        self.assertIn("Network analysis (14 wells) and Activity scan (5 scans)", t)

    def test_failed_build_is_named(self):
        self.assertIn("could not be built:** 260821", self.prompt(0, 6, {"260821": False}))


class DateFinishedTest(unittest.TestCase):
    """Watched dates are announced for their report once their last job ends;
    dates queued by hand are left to their batch, so nothing is reported twice."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.watch = root / "watch"
        self.watch.mkdir()
        self.events = []
        cfg = JobConfig(work_dir=str(root / "work"), watch_dir=str(self.watch),
                        run_network=False, run_activity=True, queue_poll_seconds=1)
        self.w = Watcher(cfg, on_event=lambda k, d: self.events.append((k, d)), reconcile=False)
        self.w.build_command = lambda run_dir, job: [sys.executable, "-c", "pass"]
        self.w.jobs_for = lambda run_dir, max_age=0: [JOB_ACTIVITY]

    def finished(self):
        return [d["folder"] for k, d in self.events if k == "date_finished"]

    def wait_done(self, d):
        key = self.w.state_key(d.resolve(), JOB_ACTIVITY)
        end = time.time() + 30
        while time.time() < end and self.w.state.status(key) not in ("done", "failed"):
            time.sleep(0.2)
        time.sleep(0.5)

    def test_watched_date_is_announced(self):
        d = self.watch / "260821"
        d.mkdir()
        self.w.dispatch(d, JOB_ACTIVITY)
        self.wait_done(d)
        self.assertEqual(self.finished(), [str(d.resolve())])

    def test_hand_queued_date_is_left_to_its_batch(self):
        d = self.watch / "260822"
        d.mkdir()
        batches = []
        self.w.queue_folders([str(d)], on_complete=batches.append)
        self.wait_done(d)
        self.assertEqual(self.finished(), [])
        self.assertTrue(self.w.batches()[0]["finished"])


if __name__ == "__main__":
    unittest.main()
