"""The watched-projects calls, over HTTP against a running test server (never
the live one), as two different people:

    MEA_TEST_URL=http://localhost:8766 MEA_TEST_LAB=/a/scratch/folder \\
        python -m unittest test_projects_api

MEA_TEST_LAB is a folder the server can read, where this test makes its own
stand-in projects; they are deleted afterwards. Skipped when no server
answers or MEA_TEST_LAB is not set.
"""
import http.cookiejar
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

URL = os.environ.get("MEA_TEST_URL", "http://localhost:8766").rstrip("/")
LAB = os.environ.get("MEA_TEST_LAB", "")


class Person:
    def __init__(self, name, email):
        self.name, self.email = name, email
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.call("/api/login", {"name": name, "email": email})

    def call(self, path, body=None):
        req = urllib.request.Request(URL + path, method="POST" if body is not None else "GET",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, raw


def server_up() -> bool:
    try:
        urllib.request.urlopen(URL + "/api/status", timeout=5)
        return True
    except Exception:                                       # noqa: BLE001
        return False


@unittest.skipUnless(LAB and server_up(), "needs MEA_TEST_URL (a test server) and MEA_TEST_LAB")
class ProjectsApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "benshalom-nas" in os.path.realpath(LAB):
            raise unittest.SkipTest("MEA_TEST_LAB must not be on the NAS")
        cls.root = Path(tempfile.mkdtemp(prefix="projects-api-", dir=LAB))
        cls.lab = cls.root / "Lab"
        for name in ("ProjA", "ProjB"):
            for date in ("260901", "260902"):
                (cls.lab / name / name / date / "M00001" / "Network" / "000001").mkdir(parents=True)
        cls.a = str(cls.lab / "ProjA" / "ProjA")
        cls.b = str(cls.lab / "ProjB" / "ProjB")
        cls.ana = Person("Ana Test", "ana.test@lab.edu")
        cls.ben = Person("Ben Test", "ben.test@lab.edu")

    @classmethod
    def tearDownClass(cls):
        for p in (cls.a, cls.b):
            cls.ana.call("/api/projects/remove", {"path": p})
        shutil.rmtree(cls.root, ignore_errors=True)

    def projects(self):
        return {p["path"]: p for p in self.ana.call("/api/projects")[1]["projects"]}

    def test_1_check_says_which_folder_was_picked(self):
        code, r = self.ana.call("/api/projects/check", {"path": str(self.lab)})
        self.assertEqual((code, r["kind"], r["ok"]), (200, "lab", False))
        self.assertEqual(r["suggestions"], [self.a, self.b])
        code, r = self.ana.call("/api/projects/check", {"path": str(Path(self.a).parent)})
        self.assertEqual((r["kind"], r["suggestions"]), ("outer", [self.a]))
        code, r = self.ana.call("/api/projects/check", {"path": self.a})
        self.assertEqual((r["kind"], r["ok"], r["dates"]), ("project", True, 2))

    def test_2_wrong_folders_are_refused(self):
        code, r = self.ana.call("/api/projects/add", {"path": str(self.lab)})
        self.assertEqual(code, 400)
        self.assertEqual(r["detail"]["suggestions"], [self.a, self.b])
        code, _ = self.ana.call("/api/projects/add", {"path": self.a + "/260901"})
        self.assertEqual(code, 400)
        self.assertNotIn(self.a, self.projects())

    def test_3_two_people_add_two_projects(self):
        code, r = self.ana.call("/api/projects/add", {"path": self.a})
        self.assertEqual(code, 200, r)
        code, r = self.ben.call("/api/projects/add", {"path": self.b + "/"})
        self.assertEqual(code, 200, r)
        ps = self.projects()
        self.assertEqual(ps[self.a]["added_by"], "Ana Test")
        self.assertEqual(ps[self.b]["added_by"], "Ben Test")
        self.assertFalse(ps[self.a]["paused"])
        # In the status the page polls, too.
        status = {p["path"]: p for p in self.ben.call("/api/status")[1]["projects"]}
        self.assertIn(self.a, status)

    def test_4_the_same_or_a_nested_folder_is_refused(self):
        code, r = self.ben.call("/api/projects/add", {"path": self.a})
        self.assertEqual(code, 400)
        self.assertIn("already being watched (added by Ana Test)", json.dumps(r))
        code, r = self.ben.call("/api/projects/check", {"path": str(Path(self.a).parent.parent)})
        self.assertFalse(r["ok"])

    def test_5_saving_settings_keeps_the_projects(self):
        code, cfg = self.ana.call("/api/config")
        if any(r.get("status") in ("dispatched", "queued", "running")
               for r in self.ana.call("/api/status")[1]["runs"]):
            self.skipTest("settings are locked while analyses run")
        body = {k: v for k, v in cfg.items() if k not in ("env", "work_dir", "watch_dirs")}
        code, r = self.ana.call("/api/config", body)
        self.assertEqual(code, 200, r)
        self.assertIn(self.a, self.projects())
        self.assertIn(self.b, self.projects())

    def test_6_pausing_someone_elses_project_is_recorded(self):
        code, r = self.ben.call("/api/projects/pause", {"path": self.a, "paused": True})
        self.assertEqual(code, 200, r)
        self.assertTrue(self.projects()[self.a]["paused"])
        audit = self.ben.call("/api/audit?limit=20")[1]["entries"]
        self.assertTrue(any(e["name"] == "Ben Test" and e["action"] == "paused watching a project"
                            and "added by Ana Test" in (e.get("detail") or "") for e in audit), audit[:3])
        code, r = self.ana.call("/api/projects/pause", {"path": self.a, "paused": False})
        self.assertEqual(code, 200, r)
        self.assertFalse(self.projects()[self.a]["paused"])

    def test_7_removing_touches_nothing_on_disk(self):
        before = sorted(str(p) for p in Path(self.b).rglob("*"))
        code, r = self.ana.call("/api/projects/remove", {"path": self.b})
        self.assertEqual(code, 200, r)
        self.assertNotIn(self.b, self.projects())
        self.assertEqual(sorted(str(p) for p in Path(self.b).rglob("*")), before)
        code, _ = self.ana.call("/api/projects/remove", {"path": self.b})
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
