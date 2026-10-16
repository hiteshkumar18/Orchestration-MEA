"""A results folder the server may not write to: refused when settings are
saved or a date is queued, and an activity scan where every recording failed
is reported as failed, not done."""
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import activity_scan
from watcher import JobConfig, cannot_write


@unittest.skipIf(os.getuid() == 0, "root can write anywhere")
class WritableTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.ok = root / "mine"
        self.locked = root / "someone_elses"
        self.locked.mkdir()
        # Exists, but this user may not create anything in it.
        self.locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(self.locked.chmod, stat.S_IRWXU)
        self.watch = root / "recordings"
        self.watch.mkdir()

    def test_probe(self):
        self.assertIsNone(cannot_write(self.ok))
        self.assertTrue(self.ok.is_dir())
        self.assertEqual(os.listdir(self.ok), [], "the test file is removed")
        why = cannot_write(self.locked)
        self.assertIn("Permission denied", why)
        self.assertIn("runs as the user", why)
        # A new folder inside a locked one cannot be made either.
        self.assertIsNotNone(cannot_write(self.locked / "project"))

    def test_settings_refused(self):
        cfg = JobConfig(watch_dir=str(self.watch), driver_options={"output_dir": str(self.locked)},
                        work_dir=str(Path(self.tmp.name) / "work"))
        errs = cfg.validate()
        self.assertTrue(any("not writable" in e and str(self.locked) in e for e in errs), errs)
        cfg.driver_options["output_dir"] = str(self.ok)
        self.assertFalse([e for e in cfg.validate() if "not writable" in e])


class AllFailedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.targets = [Path(self.tmp.name) / f"{i}" / "data.raw.h5" for i in range(3)]

    def run_main(self, outcomes):
        def fake(t, *a, **k):
            r = outcomes.pop(0)
            if isinstance(r, Exception):
                raise r
            return r
        with mock.patch.object(activity_scan, "discover", return_value=self.targets), \
             mock.patch.object(activity_scan, "process_file", side_effect=fake):
            activity_scan.main([self.tmp.name, "--output-dir", str(Path(self.tmp.name + "_out"))])

    def test_every_recording_failed_exits_non_zero(self):
        with self.assertRaises(SystemExit) as ctx, self.assertLogs(activity_scan.LOG, "ERROR"):
            self.run_main([PermissionError(13, "Permission denied")] * 3)
        self.assertIn("All 3 recording(s) failed", str(ctx.exception.code))

    def test_some_failed_still_succeeds(self):
        wells = {"run": "x", "wells": [{"qc": "pass"}]}
        with self.assertLogs(activity_scan.LOG, "ERROR"):
            self.run_main([PermissionError(13, "Permission denied"), wells, wells])
        self.assertTrue((Path(self.tmp.name + "_out") / "activity_scan_index.json").is_file())
        import shutil
        shutil.rmtree(self.tmp.name + "_out")


if __name__ == "__main__":
    unittest.main()
