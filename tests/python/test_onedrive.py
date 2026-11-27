"""Copying activity scans to OneDrive.

The copy runs the real rclone against a local folder standing in for OneDrive
(":local:<path>"), so what is tested is what happens: files arrive, nothing is
deleted or moved on either side, and only the activity scans go.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import _path  # noqa: F401
import api
import onedrive

HAVE_RCLONE = bool(shutil.which("rclone"))


def cfg(out, dest="", on=True, activity_dir=""):
    return SimpleNamespace(driver_options={"output_dir": str(out)}, output_dir=str(out),
                           activity_output_dir=activity_dir, onedrive_copy=on, onedrive_dest=dest)


class CommandTest(unittest.TestCase):
    def test_only_ever_copies(self):
        cmd = onedrive.copy_command(Path("/out/P/ActivityScan"), "onedrive:Lab/P/ActivityScan")
        self.assertEqual(cmd[1], "copy")
        for word in ("sync", "move", "delete", "purge", "--delete-excluded"):
            self.assertNotIn(word, cmd)

    def test_where_things_go(self):
        self.assertEqual(onedrive.join("onedrive:Lab", "P/ActivityScan"), "onedrive:Lab/P/ActivityScan")
        self.assertEqual(onedrive.join("onedrive:Lab/", "P/ActivityScan"), "onedrive:Lab/P/ActivityScan")
        self.assertEqual(onedrive.join("onedrive:", "P/ActivityScan"), "onedrive:P/ActivityScan")

    def test_sources_are_each_projects_activity_scans(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            for p in ("B6J/ActivityScan/261106", "Canine/ActivityScan/261112", "B6J/261106", "Empty"):
                (out / p).mkdir(parents=True)
            self.assertEqual([r for _, r in onedrive.sources(cfg(out))],
                             ["B6J/ActivityScan", "Canine/ActivityScan"])
            self.assertEqual(onedrive.sources(cfg(out, activity_dir=str(out / "B6J/ActivityScan"))),
                             [(out / "B6J/ActivityScan", "ActivityScan")])
            self.assertEqual(onedrive.sources(cfg(out / "missing")), [])

    def test_check_explains_what_is_missing(self):
        self.assertFalse(onedrive.check("no colon")["ok"])
        run = mock.Mock(return_value=SimpleNamespace(stdout="other:\n", stderr="", returncode=0))
        r = onedrive.check("onedrive:Lab", run=run)
        self.assertFalse(r["ok"])
        self.assertIn("rclone config", r["say"])
        outs = iter([SimpleNamespace(stdout="onedrive:\n", stderr="", returncode=0),
                     SimpleNamespace(stdout="", stderr="ERROR : directory not found", returncode=3)])
        r = onedrive.check("onedrive:Lab", run=lambda *a, **k: next(outs))
        self.assertTrue(r["ok"])
        self.assertIn("made on the first copy", r["say"])


@unittest.skipUnless(HAVE_RCLONE, "rclone is not installed")
class CopyTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.out, self.cloud = Path(t.name) / "results", Path(t.name) / "cloud"
        run = self.out / "B6J/ActivityScan/261106/M08073/000092"
        run.mkdir(parents=True)
        (run / "maxwell_summary.html").write_text("<html>page</html>")
        (run / "plate_overview.png").write_bytes(b"png")
        (self.out / "B6J/ActivityScan/261106/261106_activity.log").write_text("log")
        (self.out / "B6J/261106").mkdir(parents=True)
        (self.out / "B6J/261106/network_results.json").write_text("{}")
        self.c = cfg(self.out, dest=":local:" + str(self.cloud))
        self.copier = onedrive.OneDriveCopier(lambda: self.c, Path(t.name) / "work/onedrive.json")

    def files(self, root):
        return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())

    def test_copies_activity_scans_and_keeps_them_in_the_results_folder(self):
        before = self.files(self.out)
        self.assertTrue(self.copier.trigger("test", wait=True))
        self.assertEqual(self.files(self.cloud), ["B6J/ActivityScan/261106/M08073/000092/maxwell_summary.html",
                                                  "B6J/ActivityScan/261106/M08073/000092/plate_overview.png"])
        self.assertEqual(self.files(self.out), before, "the results folder is untouched")
        last = self.copier.last
        self.assertTrue(last["ok"])
        self.assertEqual(last["copied"], 2)
        self.assertEqual(json.loads(Path(self.copier.state_path).read_text())["copied"], 2)

    def test_second_copy_sends_only_what_is_new_and_never_deletes(self):
        self.copier.trigger("first", wait=True)
        (self.cloud / "B6J/ActivityScan/notes.txt").write_text("someone's note")
        (self.out / "B6J/ActivityScan/261106/M08073/000092/plate_overview.png").unlink()
        new = self.out / "B6J/ActivityScan/261112/M08073/000101"
        new.mkdir(parents=True)
        (new / "summary.json").write_text("{}")
        self.copier.trigger("second", wait=True)
        self.assertEqual(self.copier.last["copied"], 1)
        cloud = self.files(self.cloud)
        self.assertIn("B6J/ActivityScan/notes.txt", cloud, "files only on OneDrive stay")
        self.assertIn("B6J/ActivityScan/261106/M08073/000092/plate_overview.png", cloud,
                      "a file removed from the results folder stays on OneDrive")
        self.assertIn("B6J/ActivityScan/261112/M08073/000101/summary.json", cloud)

    def test_off_or_without_a_destination_does_nothing(self):
        self.c.onedrive_copy = False
        self.assertFalse(self.copier.trigger("test", wait=True))
        self.c.onedrive_copy, self.c.onedrive_dest = True, ""
        self.assertFalse(self.copier.trigger("test", wait=True))
        self.assertFalse(self.cloud.exists())

    def test_a_failed_copy_is_reported(self):
        self.c.onedrive_dest = "nosuchremote:Lab"
        self.copier.trigger("test", wait=True)
        self.assertFalse(self.copier.last["ok"])
        self.assertTrue(self.copier.last["errors"])


class ApiTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.c = cfg(Path(t.name), dest="")
        self.c.save = mock.Mock()
        self.audit = []
        self.copier = onedrive.OneDriveCopier(lambda: self.c, Path(t.name) / "od.json")
        self.copier.trigger = mock.Mock(return_value=True)
        self.copier.start_timer = mock.Mock()
        for name, value in (("_watcher", SimpleNamespace(cfg=self.c)), ("_onedrive", self.copier),
                            ("_audit", lambda req, action, detail="": self.audit.append((action, detail)))):
            p = mock.patch.object(api, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_saving_the_destination(self):
        r = api.api_onedrive_save(api.OneDrivePayload(dest=" onedrive:Lab/Scans "), None)
        self.assertEqual(self.c.onedrive_dest, "onedrive:Lab/Scans")
        self.assertEqual(r["dest"], "onedrive:Lab/Scans")
        self.c.save.assert_called_once()
        self.assertEqual(self.audit, [("changed the OneDrive copy", "to onedrive:Lab/Scans")])
        self.copier.trigger.assert_called_with("settings saved")
        with self.assertRaises(api.HTTPException):
            api.api_onedrive_save(api.OneDrivePayload(dest="just a folder"), None)

    def test_a_finished_activity_scan_starts_a_copy(self):
        api._record_event("done", {"run": "261106", "job": "activity", "returncode": 0})
        self.copier.trigger.assert_called_once()
        self.copier.trigger.reset_mock()
        api._record_event("done", {"run": "261106", "job": "network", "returncode": 0})
        self.copier.trigger.assert_not_called()


if __name__ == "__main__":
    unittest.main()
