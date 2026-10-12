"""RunHistory: one row per run, a timeline of changes, and the settings used."""
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from history import RunHistory
from watcher import StateStore

K = "/nas/IPN/260821::network"


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "run_history.sqlite"
        self.h = RunHistory(self.db, settings_snapshot=lambda: {"spike_sorting": False})
        self.state = StateStore(Path(self.tmp.name) / "watcher_state.json")
        self.state.on_update = self.h.record

    def tearDown(self):
        self.tmp.cleanup()

    def runs(self, **kw):
        return self.h.list(**kw)["runs"]

    def test_waiting_is_not_a_run(self):
        self.state.update(K, status="waiting", detail="waiting for marker")
        self.assertEqual(self.runs(), [])
        self.assertIsNone(self.h.current_run_id(K))

    def test_full_lifecycle(self):
        self.state.update(K, status="waiting", detail="settling")
        self.state.update(K, status="dispatched", dispatched_at="2026-10-01T00:00:00+00:00",
                          job="network", job_label="Network", command="python x")
        rid = self.h.current_run_id(K)
        self.state.update(K, detail="staged on local disk: /s")
        self.state.update(K, status="running", started_at="2026-10-01T00:01:00+00:00")
        self.state.update(K, status="done", completed_at="2026-10-01T01:00:00+00:00",
                          returncode=0, duration_s=3540.0)
        runs = self.runs()
        self.assertEqual(len(runs), 1)
        r = self.h.get(rid)
        self.assertEqual((r["project"], r["date"], r["job"], r["status"]), ("IPN", "260821", "network", "done"))
        self.assertEqual(r["duration_s"], 3540.0)
        self.assertEqual(r["returncode"], 0)
        self.assertEqual(r["command"], "python x")
        self.assertEqual(r["settings"], {"spike_sorting": False})
        self.assertEqual(r["attempt"], 1)
        self.assertEqual([e["status"] for e in r["events"]], ["dispatched", None, "running", "done"])
        self.assertEqual(r["events"][1]["message"], "staged on local disk: /s")
        # Detail after the run ended does not reopen it or create a run.
        self.state.update(K, detail="late")
        self.assertEqual(len(self.runs()), 1)

    def test_heartbeat_is_not_a_step(self):
        self.state.update(K, status="dispatched"); self.state.update(K, status="running")
        for t in ("30s", "1m", "1h 2m"):
            self.state.update(K, detail=f"running {t} · last log output 0s ago")
        self.state.update(K, detail="copying results from local scratch")
        r = self.h.get(self.h.current_run_id(K))
        self.assertEqual([e["message"] for e in r["events"]],
                         [None, None, "copying results from local scratch"])
        self.state.update(K, detail="running 2h · last log output 5s ago")
        self.assertEqual(self.h.get(r["id"])["detail"], "running 2h · last log output 5s ago")

    def test_failure_records_the_error(self):
        self.state.update(K, status="dispatched")
        self.state.update(K, status="running")
        self.state.update(K, status="failed", error="boom\nmore")
        r = self.h.get(self.h.current_run_id(K))
        self.assertEqual(r["status"], "failed")
        self.assertEqual(r["error"], "boom\nmore")
        self.assertEqual(r["events"][-1]["message"], "boom\nmore")

    def test_redispatch_is_a_new_run(self):
        self.state.update(K, status="dispatched"); self.state.update(K, status="failed", error="x")
        first = self.h.current_run_id(K)
        self.state.update(K, status="dispatched"); self.state.update(K, status="running")
        second = self.h.current_run_id(K)
        self.assertNotEqual(first, second)
        self.assertEqual(self.h.get(second)["attempt"], 2)
        self.assertEqual(self.h.get(first)["status"], "failed")

    def test_dispatch_while_open_supersedes(self):
        self.state.update(K, status="dispatched")
        first = self.h.current_run_id(K)
        self.state.update(K, status="dispatched")
        self.assertEqual(self.h.get(first)["status"], "interrupted")
        self.assertIn("superseded", self.h.get(first)["events"][-1]["message"])

    def test_interrupted_by_restart(self):
        self.state.update(K, status="dispatched"); self.state.update(K, status="running")
        rid = self.h.current_run_id(K)
        self.state.update(K, status="interrupted", error="server restarted")
        self.assertEqual(self.h.get(rid)["status"], "interrupted")
        # An interruption with nothing open does not invent a run.
        self.state.update("/nas/IPN/260822::network", status="interrupted")
        self.assertEqual(len(self.runs()), 1)

    def test_failure_before_dispatch_is_a_run(self):
        self.state.update(K, status="failed", error="no recordings")
        self.assertEqual(self.runs()[0]["status"], "failed")

    def test_dry_run_detected(self):
        self.state.update(K, status="detected")
        self.assertEqual(self.runs()[0]["status"], "detected")
        self.state.update(K, status="dispatched")
        self.assertEqual(len(self.runs()), 2)

    def test_close_open_after_manual_reset(self):
        self.state.update(K, status="dispatched")
        rid = self.h.current_run_id(K)
        self.h.close_open(K, "cleared by hand")
        self.assertEqual(self.h.get(rid)["status"], "interrupted")
        self.h.close_open(K, "again")                      # no open run: no-op
        self.assertEqual(len(self.h.get(rid)["events"]), 2)

    def test_survives_reopen(self):
        self.state.update(K, status="dispatched")
        rid = self.h.current_run_id(K)
        h2 = RunHistory(self.db)
        self.assertEqual(h2.current_run_id(K), rid)
        h2.record(K, {"status": "done"}, {"status": "done"})
        self.assertEqual(self.h.get(rid)["status"], "done")
        self.assertEqual(len(self.runs()), 1)

    def test_two_instances_one_file(self):
        """A watcher replaced by a settings save keeps finishing its jobs."""
        self.state.update(K, status="dispatched")
        rid = self.h.current_run_id(K)
        h2 = RunHistory(self.db)
        h2.record(K, {"status": "done"}, {"status": "done"})     # the new one closes it
        # The old one has it as open; its next dispatch must start a new run,
        # not mark the finished one superseded.
        self.state.update(K, status="dispatched")
        self.assertEqual(self.h.get(rid)["status"], "done")
        self.assertEqual(len(self.runs()), 2)

    def test_import_state_once(self):
        st = {K: {"status": "done", "dispatched_at": "2026-09-01T00:00:00+00:00", "duration_s": 5},
              "/nas/IPN/260822::activity": {"status": "running"},
              "/nas/IPN/260823::network": {"status": "waiting"}}
        self.assertEqual(self.h.import_state(st), 2)
        self.assertEqual(self.h.import_state(st), 0)
        rows = {r["date"]: r for r in self.runs()}
        self.assertEqual(set(rows), {"260821", "260822"})
        self.assertEqual(rows["260821"]["imported"], 1)
        self.assertEqual(rows["260822"]["job"], "activity")
        self.assertEqual(self.h.current_run_id("/nas/IPN/260822::activity"), rows["260822"]["id"])

    def test_list_filters(self):
        for i, (proj, job, st) in enumerate([("A", "network", "done"), ("A", "activity", "failed"),
                                             ("B", "network", "done")]):
            k = f"/nas/{proj}/26080{i}::{job}"
            self.state.update(k, status="dispatched"); self.state.update(k, status=st)
        self.assertEqual(self.h.list()["total"], 3)
        self.assertEqual(self.h.list()["projects"], ["A", "B"])
        self.assertEqual(self.h.list(project="A")["total"], 2)
        self.assertEqual(self.h.list(job="network")["total"], 2)
        self.assertEqual(self.h.list(status="failed")["total"], 1)
        self.assertEqual(self.h.list(status="done,failed")["total"], 3)
        self.assertEqual(self.h.list(date="260802")["runs"][0]["project"], "B")
        self.assertEqual(len(self.h.list(limit=1, offset=1)["runs"]), 1)
        self.assertIsNone(self.h.get("nope"))

    def test_knows_log(self):
        self.state.update(K, status="dispatched", log="/out/logs/a.log")
        self.assertTrue(self.h.knows_log("/out/logs/a.log"))
        self.assertTrue(self.h.knows_log("", "/out/logs/a.log"))
        self.assertFalse(self.h.knows_log("/etc/passwd"))
        self.assertFalse(self.h.knows_log(""))

    def test_record_never_raises(self):
        self.h._db.close()
        self.h.record(K, {"status": "dispatched"}, {"status": "dispatched"})   # no exception

    def test_broken_hook_does_not_break_state(self):
        def bad(*a):
            raise RuntimeError("x")
        self.state.on_update = bad
        self.state.update(K, status="dispatched")
        self.assertEqual(self.state.status(K), "dispatched")


if __name__ == "__main__":
    unittest.main()
