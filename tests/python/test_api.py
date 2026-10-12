"""The dashboard endpoints and every existing read endpoint, over HTTP against
a running test server (never the live one):

    MEA_TEST_URL=http://localhost:8766 python -m unittest test_api

Skipped when no server answers. Read-only apart from resetting a key that
does not exist.
"""
import json
import os
import time
import unittest
import urllib.error
import urllib.request

URL = os.environ.get("MEA_TEST_URL", "http://localhost:8766").rstrip("/")


def call(path, body=None, timeout=30):
    req = urllib.request.Request(URL + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read(), e.code
    took = time.time() - t
    try:
        data = json.loads(raw)
    except ValueError:
        data = raw
    return code, data, took


def up():
    """A just-started server can take a minute; wait for it."""
    for _ in range(int(os.environ.get("MEA_TEST_WAIT", "90")) // 3 or 1):
        try:
            if call("/api/status", timeout=5)[0] == 200:
                return True
        except OSError:
            pass
        time.sleep(3)
    return False


@unittest.skipUnless(up(), f"no test server at {URL}")
class ApiTest(unittest.TestCase):
    def test_existing_endpoints_unchanged(self):
        for path in ("/", "/static/app.js", "/api/status", "/api/config", "/api/schema", "/api/env",
                     "/api/picker", "/api/queue", "/api/logs", "/api/reports", "/api/handoff"):
            code, _, took = call(path)
            self.assertEqual(code, 200, path)
            self.assertLess(took, 5, path)
        code, cfg, _ = call("/api/config")
        for k in ("watch_dir", "driver_options", "run_network", "run_activity"):
            self.assertIn(k, cfg)

    def test_status_rows_link_to_history(self):
        _, s, _ = call("/api/status")
        for r in s["runs"]:
            self.assertIn("run_id", r)
            if r["run_id"]:
                code, d, _ = call(f"/api/history/{r['run_id']}")
                self.assertEqual(code, 200)
                self.assertEqual(d["key"], r["path"])

    def test_history_list_and_filters(self):
        code, h, took = call("/api/history")
        self.assertEqual(code, 200)
        self.assertLess(took, 2)
        self.assertEqual(set(h), {"total", "runs", "projects"})
        if not h["runs"]:
            self.skipTest("history is empty")
        r = h["runs"][0]
        _, f, _ = call(f"/api/history?project={r['project']}&job={r['job']}&status={r['status']}")
        self.assertTrue(f["runs"])
        self.assertTrue(all(x["project"] == r["project"] and x["status"] == r["status"] for x in f["runs"]))
        self.assertEqual(call("/api/history?status=no_such")[1]["total"], 0)
        self.assertEqual(len(call("/api/history?limit=0")[1]["runs"]), min(1, h["total"]))
        self.assertLessEqual(len(call("/api/history?limit=100000")[1]["runs"]), 500)
        self.assertEqual(call("/api/history?offset=-5")[0], 200)
        self.assertEqual(call("/api/history?limit=abc")[0], 422)

    def test_run_detail_for_recent_runs(self):
        _, h, _ = call("/api/history?limit=15")
        for r in h["runs"]:
            code, d, took = call(f"/api/history/{r['id']}")
            self.assertEqual(code, 200, r["id"])
            self.assertLess(took, 10, r["id"])
            for k in ("events", "settings", "attempt", "progress", "log_summary", "outputs",
                      "is_current", "elapsed_s", "live_detail", "last_output_age_s"):
                self.assertIn(k, d, r["id"])
            if d["log_summary"] and d["job"] == "network":
                self.assertIn(d["log_summary"]["route"], ("raw", "nwb"))
                for w in d["log_summary"]["wells"]:
                    self.assertIn(w["outcome"], ("complete", "silent", "not_recorded", "failed",
                                                 "stopped", "running"))
                    if d["status"] in ("done", "failed", "interrupted"):
                        self.assertNotEqual(w["outcome"], "running", (r["id"], w))

    def test_log_reads_are_restricted(self):
        """Logs of recorded runs are readable, whatever the output folder is now;
        any other file is not."""
        _, h, _ = call("/api/history?limit=200")
        logs = [r["log"] for r in h["runs"] if r.get("log") and os.path.exists(r["log"])]
        for log in logs[:5]:
            code, d, _ = call("/api/runs/log?tail=5&path=" + urllib.request.quote(log))
            self.assertEqual(code, 200, log)
            self.assertLessEqual(len(d["lines"]), 5)
        for bad in ("/etc/passwd", "/etc/hostname", __file__):
            self.assertEqual(call("/api/runs/log?path=" + urllib.request.quote(bad))[0], 403, bad)

    def test_unknown_run(self):
        code, d, _ = call("/api/history/does-not-exist")
        self.assertEqual(code, 404)
        self.assertEqual(d["detail"], "No such run")

    def test_system(self):
        for _ in range(20):
            s = call("/api/system")[1]
            if s.get("ready"):
                break
            time.sleep(1)
        self.assertTrue(s["ready"])
        self.assertGreater(s["cpu"]["cores"], 0)
        self.assertGreater(s["memory"]["total"], 0)
        self.assertIn("ok", s["gpu"])
        self.assertIn("Work folder", s["disks"])
        self.assertIsInstance(s["processes"], list)
        self.assertIsInstance(s["warnings"], list)
        self.assertLess(call("/api/system")[2], 1)

    def test_overview(self):
        code, o, took = call("/api/overview")
        self.assertEqual(code, 200)
        self.assertLess(took, 3)
        for k in ("running", "attention", "recent", "counts", "watching", "active_jobs", "limits"):
            self.assertIn(k, o)
        self.assertLessEqual(len(o["recent"]), 10)
        self.assertTrue(all(r["status"] in ("done", "failed", "interrupted") for r in o["recent"]))
        for a in o["attention"]:
            self.assertIn(a["level"], ("bad", "warn"))
            self.assertTrue(a["text"])

    def test_reset_unknown_key_is_harmless(self):
        before = call("/api/history")[1]["total"]
        code, _, _ = call("/api/runs/reset", {"path": "/nowhere/000000::network"})
        self.assertEqual(code, 200)
        self.assertEqual(call("/api/history")[1]["total"], before)

    def test_concurrent_load(self):
        """The dashboard polls several endpoints at once; none should stall."""
        from concurrent.futures import ThreadPoolExecutor
        paths = ["/api/overview", "/api/system", "/api/history", "/api/status"] * 5
        with ThreadPoolExecutor(10) as ex:
            res = list(ex.map(call, paths))
        self.assertTrue(all(c == 200 for c, _, _ in res))
        self.assertLess(max(t for _, _, t in res), 10)


if __name__ == "__main__":
    unittest.main()
