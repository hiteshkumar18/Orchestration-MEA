"""Copying a date's recordings to the scratch disk before analysing them.

Measured on 2026-10-23, one run at a time: reading the recordings from the NAS
in small pieces ran at 15-38 MB/s, one plain copy at ~115 MB/s. These tests
check that the copy is analysed instead of the original, that the original is
only ever read, and that no clean-up can reach the input or a network mount.
"""
import hashlib
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _path  # noqa: F401
import watcher as watcher_mod
from watcher import JOB_NETWORK, JobConfig, Watcher

# Stands in for run_pipeline_driver.py: records what it was given, reads the
# recording it was pointed at, and leaves a result where MEA-Analysis would.
FAKE_DRIVER = r"""
import sys, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[3])
rec = next(src.rglob("data.raw.h5"))
res = out / src.parent.name / src.name / rec.relative_to(src).parent / "well000"
res.mkdir(parents=True, exist_ok=True)
(res / "spike_times.npy").write_bytes(rec.read_bytes()[:4])
(out / "argv.txt").write_text(str(src))
"""


def digest(root: Path) -> dict:
    """Every file under root with its content hash and mtime."""
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(root.rglob("*")) if p.is_file()}


class CopyCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.watch = self.root / "nas" / "IPN" / "IPN"
        self.out = self.root / "out"
        self.scratch = self.root / "ssd"
        self.addCleanup(self.writable, self.root / "nas")

    def writable(self, top: Path):
        for p in [top, *top.rglob("*")]:
            if p.is_dir():
                p.chmod(0o755)

    def make(self, **kw):
        kw.setdefault("work_dir", str(self.root / "work"))
        kw.setdefault("watch_dir", str(self.watch))
        kw.setdefault("stage_locally", True)
        kw.setdefault("scratch_dir", str(self.scratch))
        kw.setdefault("copy_input_first", True)
        kw.setdefault("stage_min_free_gb", 0)
        kw.setdefault("memory_limit_gb", -1)
        kw.setdefault("gpu_cooldown_seconds", 0)
        kw.setdefault("kill_grace_seconds", 2)
        w = Watcher(JobConfig(**kw), reconcile=False)
        w.cfg.driver_options["output_dir"] = str(self.out)
        w.cfg.driver_options["clean_up"] = True
        w.cfg.driver_options["skip_spikesorting"] = True
        return w

    def date(self, name="260825", recordings=2, read_only=True):
        """A date laid out like the NAS, with real bytes in each recording.
        Read-only by default, so any write to it fails the test."""
        d = self.watch / name
        for i in range(recordings):
            run = d / "M07037" / "Network" / f"{i:06d}"
            run.mkdir(parents=True)
            (run / "data.raw.h5").write_bytes(os.urandom(4096) + bytes([i]))
            (run / ".metadata").write_text("[properties]\nrunid = %d\n" % i)
        (d / "M07037" / "ActivityScan" / "000100").mkdir(parents=True)
        (d / "M07037" / "ActivityScan" / "000100" / "data.raw.h5").write_bytes(b"activity")
        if read_only:
            for p in [d, *d.rglob("*")]:
                if p.is_dir():
                    p.chmod(stat.S_IRUSR | stat.S_IXUSR)
        return d


class CopyInputTest(CopyCase):
    def test_copies_network_recordings_with_their_layout(self):
        w = self.make()
        d = self.date()
        local = self.scratch / "IPN" / d.name
        local.mkdir(parents=True)
        before = digest(d)
        dest = w._copy_input(d, local, "k")
        self.assertEqual(dest, local / Watcher.INPUT_DIR / "IPN" / d.name)
        for i in range(2):
            rel = Path("M07037/Network") / f"{i:06d}"
            self.assertEqual((dest / rel / "data.raw.h5").read_bytes(),
                             (d / rel / "data.raw.h5").read_bytes())
            self.assertTrue((dest / rel / ".metadata").is_file())
        # MEA-Analysis reads project and date from parts[-6] and parts[-5].
        parts = str(next(dest.rglob("data.raw.h5"))).split(os.sep)
        self.assertEqual((parts[-6], parts[-5]), ("IPN", d.name))
        self.assertFalse((dest / "M07037" / "ActivityScan").exists(), "only Network is analysed")
        self.assertEqual(digest(d), before, "the original must not change")

    def test_refuses_a_copy_that_overlaps_the_input(self):
        w = self.make(scratch_dir=str(self.watch))
        d = self.date()
        before = digest(d)
        self.assertIsNone(w._copy_input(d, self.watch / "IPN" / d.name, "k"))
        self.assertEqual(digest(d), before)

    def test_other_layouts_are_read_in_place(self):
        w = self.make()
        d = self.watch / "flat"
        (d / "Network").mkdir(parents=True)
        (d / "Network" / "data.raw.h5").write_bytes(b"x")
        local = self.scratch / "IPN" / "flat"
        local.mkdir(parents=True)
        self.assertIsNone(w._copy_input(d, local, "k"))

    def test_cancel_stops_the_copy(self):
        w = self.make()
        d = self.date(recordings=3)
        local = self.scratch / "IPN" / d.name
        local.mkdir(parents=True)
        w._cancel["k"] = "held"
        self.assertIsNone(w._copy_input(d, local, "k"))

    def test_estimate_counts_the_copies(self):
        w = self.make()
        d = self.date()
        size = sum(p.stat().st_size for p in d.rglob("Network/*/data.raw.h5"))
        with_copy = w._staging_estimate_gb(d)
        w.cfg.copy_input_first = False
        self.assertAlmostEqual(with_copy - w._staging_estimate_gb(d), size / 2**30, places=9)


class CopyInputJobTest(CopyCase):
    def test_job_analyses_the_copy_and_leaves_the_original_alone(self):
        w = self.make()
        d = self.date()
        before = digest(d)
        key = w.state_key(d.resolve(), JOB_NETWORK)
        cmd = [sys.executable, "-c", FAKE_DRIVER, str(d), "--output-dir", str(self.out)]
        w._run_job(d, JOB_NETWORK, key, cmd, self.root / "job.log")
        e = w.state.all()[key]
        self.assertEqual(e["status"], "done", e)
        analysed = Path((self.out / "argv.txt").read_text())
        self.assertIn(Watcher.INPUT_DIR, analysed.parts, "the driver must read the copy")
        results = list((self.out / "IPN" / d.name / "M07037" / "Network").glob("*/well000/spike_times.npy"))
        self.assertEqual(len(results), 1, "results are copied back")
        self.assertFalse((self.out / Watcher.INPUT_DIR).exists(), "copies are not results")
        self.assertFalse(self.scratch.exists() and any(self.scratch.rglob("*")), "scratch is emptied")
        self.assertEqual(digest(d), before, "the original must not change")

    def test_off_reads_the_original(self):
        w = self.make(copy_input_first=False)
        d = self.date()
        key = w.state_key(d.resolve(), JOB_NETWORK)
        cmd = [sys.executable, "-c", FAKE_DRIVER, str(d), "--output-dir", str(self.out)]
        w._run_job(d, JOB_NETWORK, key, cmd, self.root / "job.log")
        self.assertEqual(Path((self.out / "argv.txt").read_text()), d)


class DeleteGuardTest(CopyCase):
    def test_allows_scratch(self):
        w = self.make()
        t = self.scratch / "IPN" / "260825"
        t.mkdir(parents=True)
        self.assertTrue(w._may_delete(t.resolve()))

    def test_refuses_outside_scratch(self):
        w = self.make()
        self.assertFalse(w._may_delete((self.root / "elsewhere").resolve()))

    def test_refuses_the_input_even_inside_scratch(self):
        w = self.make(scratch_dir=str(self.root / "nas"))
        self.assertFalse(w._may_delete(self.watch.resolve()))
        self.assertFalse(w._may_delete((self.watch / "260825").resolve()))

    def test_refuses_network_mounts(self):
        w = self.make()
        t = (self.scratch / "IPN").resolve()
        t.mkdir(parents=True)
        with mock.patch.object(watcher_mod, "network_mounts", return_value=[str(self.scratch.resolve())]):
            self.assertFalse(w._may_delete(t))
            w._remove_scratch(t)
        self.assertTrue(t.is_dir(), "nothing on a network mount is deleted")

    def test_network_mounts_parsed(self):
        rows = ("//nas/MEA /mnt/benshalom-nas cifs rw 0 0\n"
                "/dev/nvme1n1p1 /mnt/STUART_SSD_SCRATCH ext4 rw 0 0\n"
                "nas:/x /mnt/with\\040space nfs4 rw 0 0\n")
        with mock.patch("builtins.open", mock.mock_open(read_data=rows)):
            self.assertEqual(watcher_mod.network_mounts(), ["/mnt/benshalom-nas", "/mnt/with space"])


if __name__ == "__main__":
    unittest.main()
