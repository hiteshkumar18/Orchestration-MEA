"""Dismissing failed runs from Needs attention.

A dismissal only hides the card: the run keeps its status and nothing is
analysed again. The same date failing again later brings a new card.
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import api
from fastapi import HTTPException
from watcher import StateStore


class FakeWatcher:
    def __init__(self, state):
        self.state, self.history = state, None
        self.cfg = mock.Mock(stall_minutes=120)

    def snapshot(self):
        return {"runs": [{"path": k, "folder": k.split("::")[0], **e} for k, e in self.state.all().items()]}


class DismissTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state = StateStore(Path(tmp.name) / "state.json")
        self.a = "/lab/P/P/260901::network"
        self.b = "/lab/P/P/260902::network"
        self.state.update(self.a, run="260901", job="network", status="failed",
                          completed_at="2026-11-18T10:00:00", error="CUDA out of memory")
        self.state.update(self.b, run="260902", job="network", status="failed",
                          completed_at="2026-11-18T11:00:00", error="no recordings")
        self.state.update("/lab/P/P/260903::network", run="260903", job="network", status="done")
        self.audit = []
        for name, value in (("_watcher", FakeWatcher(self.state)),
                            ("_audit", lambda req, action, detail="": self.audit.append((action, detail))),
                            ("get_monitor", lambda: mock.Mock(snapshot=lambda: {}))):
            p = mock.patch.object(api, name, value)
            p.start()
            self.addCleanup(p.stop)

    def cards(self):
        return [a["date"] for a in api.api_overview()["attention"] if a["kind"] == "failed"]

    def test_dismiss_hides_the_card_and_changes_nothing_else(self):
        self.assertEqual(self.cards(), ["260901", "260902"])
        r = api.api_dismiss(api.DismissPayload(paths=[self.a]), None)
        self.assertEqual(r["dismissed"], [self.a])
        self.assertEqual(self.cards(), ["260902"])
        self.assertEqual(self.state.status(self.a), "failed", "the run itself is untouched")
        self.assertEqual(self.audit, [("dismissed from Needs attention", "260901")])

    def test_failing_again_brings_the_card_back(self):
        api.api_dismiss(api.DismissPayload(paths=[self.a, self.b]), None)
        self.assertEqual(self.cards(), [])
        self.state.update(self.a, status="failed", completed_at="2026-11-19T09:00:00", error="CUDA out of memory")
        self.assertEqual(self.cards(), ["260901"])

    def test_only_failed_runs_are_dismissed(self):
        r = api.api_dismiss(api.DismissPayload(paths=["/lab/P/P/260903::network", "/nowhere::network"]), None)
        self.assertEqual(r["dismissed"], [])
        self.assertNotIn("dismissed", self.state.get("/lab/P/P/260903::network"))
        self.assertEqual(self.audit, [], "nothing to record")
        with self.assertRaises(HTTPException):
            api.api_dismiss(api.DismissPayload(paths=[]), None)

    def test_the_lab_results_disk_is_the_default(self):
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop("MEA_OUTPUT_DIR", None)
            self.assertEqual(api._runtime_env()["suggested_output"], "/mnt/MaxwellData_Backup/MEA_Analysis")
            env["MEA_OUTPUT_DIR"] = "/elsewhere"
            self.assertEqual(api._runtime_env()["suggested_output"], "/elsewhere")


if __name__ == "__main__":
    unittest.main()
