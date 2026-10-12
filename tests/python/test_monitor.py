"""System monitor: /proc and nvidia-smi parsing, warnings, and a live sample."""
import os
import time
import unittest

import _path  # noqa: F401
import monitor
from monitor import (SystemMonitor, _target, parse_cpu_times, parse_iowait, parse_meminfo,
                     parse_nvidia_smi, warnings)

STAT = "cpu  100 0 50 800 50 0 0 0 0 0\ncpu0 1 2 3 4 5 6 7 8\n"
GB = 2**30


class ParserTest(unittest.TestCase):
    def test_cpu(self):
        self.assertEqual(parse_cpu_times(STAT), (150, 1000))
        self.assertEqual(parse_iowait(STAT), (50, 1000))

    def test_meminfo(self):
        m = parse_meminfo("MemTotal:       65536 kB\nMemAvailable:   1024 kB\nHugePages_Total:       0\nJunk\n")
        self.assertEqual(m["MemTotal"], 65536 * 1024)
        self.assertEqual(m["MemAvailable"], 1024 * 1024)
        self.assertEqual(m["HugePages_Total"], 0)

    def test_nvidia_ok(self):
        g = parse_nvidia_smi("NVIDIA RTX A6000, 37, 1200, 49140, 55\nNVIDIA RTX A6000, 0, 3, 49140, 30\n")
        self.assertTrue(g["ok"])
        self.assertEqual(len(g["gpus"]), 2)
        self.assertEqual(g["gpus"][0], {"name": "NVIDIA RTX A6000", "util": 37.0, "mem_used_mb": 1200.0,
                                        "mem_total_mb": 49140.0, "temp_c": 55.0})

    def test_nvidia_faults(self):
        g = parse_nvidia_smi("Failed to initialize NVML: Driver/library version mismatch\nNVML library version: 580.95\n")
        self.assertFalse(g["ok"])
        self.assertIn("mismatch", g["error"])
        self.assertFalse(parse_nvidia_smi("")["ok"])
        self.assertFalse(parse_nvidia_smi("[N/A], [N/A]")["ok"])

    def test_target(self):
        nas = "/mnt/nas/BenShalomLab/P/P/260821"
        self.assertEqual(_target(f"python3 mea_analysis_routine.py '{nas}/M07036/Network/000023/data.raw.h5' "
                                 "--rec rec0000 --well well002 --output-dir '/out/x'"),
                         "260821/M07036/000023/well002")
        self.assertEqual(_target("python3 routine_shim.py /repo /out/NWB/P/260818/M07036/Network/000015/well002"),
                         "260818/M07036/000015/well002")
        self.assertEqual(_target("python3 routine_shim.py /repo /out/NWB/P/260818/M07036/Network/000015/well002.nwb"),
                         "260818/M07036/000015/well002")
        self.assertEqual(_target(f"python run_pipeline_driver.py {nas} --output-dir /out"), "260821")
        self.assertEqual(_target("python driver.py --well well004"), "well004")
        self.assertEqual(_target("python x.py"), "")


class WarningsTest(unittest.TestCase):
    def texts(self, s):
        return [w["text"] for w in warnings(s)]

    def test_healthy(self):
        s = {"gpu": {"ok": True}, "memory": {"total": 100, "available": 50},
             "disks": {"Output disk": {"total": 1000 * GB, "free": 500 * GB}}, "cpu": {"iowait_percent": 5}}
        self.assertEqual(warnings(s), [])

    def test_gpu(self):
        self.assertEqual(warnings({"gpu": {"ok": False, "error": "Driver/library version mismatch"}})[0]["level"], "bad")
        self.assertEqual(warnings({"gpu": {"ok": False, "error": "nvidia-smi not installed"}}), [])
        self.assertEqual(warnings({"gpu": {"ok": False, "error": "timeout"}})[0]["level"], "warn")

    def test_memory(self):
        self.assertEqual(warnings({"gpu": {"ok": True}, "memory": {"total": 100, "available": 5}})[0]["level"], "bad")
        self.assertEqual(warnings({"gpu": {"ok": True}, "memory": {"total": 100, "available": 10}})[0]["level"], "warn")

    def test_disks(self):
        ok = {"ok": True}
        fast_low = {"gpu": ok, "disks": {"Fast disk": {"total": 2000 * GB, "free": 150 * GB}}}
        self.assertEqual(warnings(fast_low)[0]["level"], "warn")
        out_ok = {"gpu": ok, "disks": {"Output disk": {"total": 2000 * GB, "free": 150 * GB}}}
        self.assertEqual(warnings(out_ok), [])                    # 7.5% free: fine for a big disk
        full = {"gpu": ok, "disks": {"Output disk": {"total": 1000 * GB, "free": 10 * GB}}}
        self.assertEqual(warnings(full)[0]["level"], "bad")
        hung = {"gpu": ok, "disks": {"Recordings (NAS)": {"error": "did not answer within 5 s"}}}
        self.assertIn("did not answer", self.texts(hung)[0])

    def test_iowait(self):
        self.assertIn("waiting on disks", self.texts({"gpu": {"ok": True}, "cpu": {"iowait_percent": 55}})[0])


class SampleTest(unittest.TestCase):
    def test_live_sample(self):
        m = SystemMonitor(lambda: {"Here": os.getcwd(), "Gone": "/no/such/path", "Empty": ""})
        m._read_gpu = lambda: {"ok": False, "error": "skipped in test"}
        s1 = m.sample()
        self.assertTrue(s1["ready"])
        self.assertIsNone(s1["cpu"]["percent"])                   # needs two samples
        time.sleep(0.3)
        s2 = m.sample()
        self.assertIsNotNone(s2["cpu"]["percent"])
        self.assertGreater(s2["memory"]["total"], 0)
        self.assertGreater(s2["disks"]["Here"]["total"], 0)
        self.assertIn("error", s2["disks"]["Gone"])
        self.assertNotIn("Empty", s2["disks"])
        self.assertIsInstance(s2["processes"], list)

    def test_slow_disk_does_not_stall(self):
        orig = monitor.shutil.disk_usage
        monitor.shutil.disk_usage = lambda p: time.sleep(30)
        try:
            m = SystemMonitor(lambda: {"Slow": "/x"})
            t = time.time()
            m._refresh_disks()
            self.assertLess(time.time() - t, 7)
            self.assertIn("did not answer", m._disks["Slow"]["error"])
        finally:
            monitor.shutil.disk_usage = orig

    def test_snapshot_before_first_sample(self):
        m = SystemMonitor(lambda: {}, interval=3600)
        self.assertIn("ready", m.snapshot())


if __name__ == "__main__":
    unittest.main()
