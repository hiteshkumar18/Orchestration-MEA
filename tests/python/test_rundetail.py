"""Log parsing, progress estimates and outputs for the run page."""
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
import rundetail
from rundetail import estimate, outputs, parse_activity_log, parse_job_log, parse_log_file

NAS = "/mnt/nas/BenShalomLab/IPN/IPN/260821"
RAW = f"""Starting
[2026-10-05 17:03:47,590] INFO: Processing : {NAS}/M07036/Network/000023/data.raw.h5 recording : rec0000 well_id : well002
[2026-10-05 17:03:50,000] INFO: --- [Phase 1] Preprocessing ---
[2026-10-05 17:03:55,000] INFO: --- [Phase 2-Alt] Spike Detection (No Sorting) ---
[2026-10-05 17:04:00,000] INFO: Detected 1016958 total spikes.
Processing Complete for well002
[2026-10-05 17:04:18,125] INFO: Processing : {NAS}/M07036/Network/000023/data.raw.h5 recording : rec0000 well_id : well003
[2026-10-05 17:04:19,000] INFO: --- [Phase 1] Preprocessing ---
CRITICAL FAILURE in well003: stream_id well003 is not in ['well002']
[2026-10-05 17:04:21,208] ERROR: Subprocess failed for well003 in {NAS}/M07036/Network/000023/data.raw.h5
[2026-10-05 17:04:21,431] INFO: Processing : {NAS}/M07037/Network/000019/data.raw.h5 recording : rec0000 well_id : well000
[2026-10-05 17:05:00,000] INFO: Detected 0 total spikes.
Processing Complete for well000
[2026-10-05 17:05:01,000] INFO: Processing : {NAS}/M07037/Network/000019/data.raw.h5 recording : rec0000 well_id : well001
CRITICAL FAILURE in well001: CUDA out of memory
[2026-10-05 17:05:30,000] ERROR: Subprocess failed for well001 in {NAS}/M07037/Network/000019/data.raw.h5
[2026-10-05 17:05:31,000] INFO: Processing : {NAS}/M07037/Network/000019/data.raw.h5 recording : rec0000 well_id : well002
[2026-10-05 17:05:40,000] INFO: --- [Phase 1] Preprocessing ---
"""
OUT = "/out/IPN/NWB/IPN/260818"
NWB = f"""NWB route: converting {NAS} into /out/IPN/NWB, then analysing from the NWB files
[2026-10-08 23:43:56] NWB: converted M07036/000015/well002 -> {OUT}/M07036/Network/000015/well002.nwb (38 ch, 6000600 samples, 97 MB, 11 s)
[2026-10-08 23:43:57] NWB: reused {OUT}/M07037/Network/000013/well001.nwb
[2026-10-08 23:43:58] NWB: NWB conversion failed for well003 in {NAS}/M07036/Network/000015/data.raw.h5: stream_id well003 is not in ['well002']
[2026-10-08 23:43:59] NWB: NWB conversion failed for well004 in {NAS}/M07036/Network/000015/data.raw.h5: disk full
[2026-10-09 00:19:53] NWB: done in 2168 s: 1 converted, 1 reused, 2 failed
[2026-10-09 00:19:54,000] INFO: Processing : {OUT}/M07036/Network/000015/well002.nwb recording : rec0000 well_id : well002
[2026-10-09 00:19:59,030] INFO: Detected 1102364 total spikes.
Processing Complete for well002
[2026-10-09 00:20:30,000] INFO: Pipeline driver completed in 36.5 seconds
"""


class ParseJobLogTest(unittest.TestCase):
    def test_raw_outcomes(self):
        p = parse_job_log(RAW)
        self.assertEqual(p["route"], "raw")
        w = {(x["chip"], x["run"], x["well"]): x for x in p["wells"]}
        self.assertEqual(len(w), 5)
        ok = w[("M07036", "000023", "well002")]
        self.assertEqual((ok["outcome"], ok["spikes"], ok["seconds"]), ("complete", 1016958, 13.0))
        self.assertEqual(ok["phase"], "Spike Detection (No Sorting)")
        nr = w[("M07036", "000023", "well003")]
        self.assertEqual(nr["outcome"], "not_recorded")
        self.assertIn("stream_id well003", nr["reason"])
        self.assertEqual(w[("M07037", "000019", "well000")]["outcome"], "silent")
        bad = w[("M07037", "000019", "well001")]
        self.assertEqual((bad["outcome"], bad["reason"]), ("failed", "CUDA out of memory"))
        self.assertEqual(w[("M07037", "000019", "well002")]["outcome"], "running")
        self.assertEqual(p["counts"], {"complete": 1, "not_recorded": 1, "silent": 1, "failed": 1, "running": 1})

    def test_finished_job_marks_unfinished_wells_stopped(self):
        p = parse_job_log(RAW, finished=True)
        last = p["wells"][-1]
        self.assertEqual(last["outcome"], "stopped")
        self.assertTrue(last["reason"])
        self.assertNotIn("running", p["counts"])

    def test_nwb_route(self):
        p = parse_job_log(NWB, finished=True)
        self.assertEqual(p["route"], "nwb")
        c = {x["well"]: x for x in p["conversion"]}
        self.assertEqual((c["well002"]["outcome"], c["well002"]["seconds"], c["well002"]["chip"]),
                         ("converted", 11, "M07036"))
        self.assertEqual((c["well001"]["outcome"], c["well001"]["chip"], c["well001"]["run"]),
                         ("reused", "M07037", "000013"))
        self.assertEqual(c["well003"]["outcome"], "not_recorded")
        self.assertEqual((c["well004"]["outcome"], c["well004"]["reason"]), ("failed", "disk full"))
        self.assertEqual(c["well004"]["chip"], "M07036")
        self.assertEqual(p["conversion_summary"], {"seconds": 2168, "converted": 1, "reused": 1, "failed": 2})
        self.assertEqual(p["wells"][0]["chip"], "M07036")
        self.assertEqual(p["wells"][0]["outcome"], "complete")
        self.assertEqual(p["driver_seconds"], 36.5)

    def test_empty_and_junk(self):
        self.assertEqual(parse_job_log("")["wells"], [])
        p = parse_job_log("garbage\n\x00\nProcessing Complete for well001\n")
        self.assertEqual(p["counts"], {})

    def test_activity_log(self):
        t = ("wrote /out/IPN/ActivityScan/260821/M07036/summary.json\n"
             "wrote /out/IPN/ActivityScan/260821/M07037/summary.json\n"
             "Done — 2 run(s), 12 well(s), 3 flagged\n")
        p = parse_activity_log(t)
        self.assertEqual(p["summary"], {"runs": 2, "wells": 12, "flagged": 3})
        self.assertEqual(p["chips"], ["M07036", "M07037"])
        self.assertIsNone(parse_activity_log("")["summary"])


class EstimateTest(unittest.TestCase):
    def test_estimate(self):
        p = {"counts": {"complete": 8, "not_recorded": 1, "running": 1}}
        e = estimate(p, 27, 600)
        self.assertEqual((e["done"], e["total"], e["fraction"]), (9, 27, 0.333))
        self.assertEqual(e["seconds_left"], 1200)

    def test_unknown_total(self):
        e = estimate({"counts": {"complete": 3}}, 0, 100)
        self.assertEqual((e["done"], e["total"], e["fraction"], e["seconds_left"]), (3, None, None, None))

    def test_nothing_done_or_all_done(self):
        self.assertIsNone(estimate({"counts": {"running": 1}}, 27, 100)["seconds_left"])
        e = estimate({"counts": {"complete": 30}}, 27, 100)
        self.assertEqual((e["fraction"], e["seconds_left"]), (1.0, None))
        self.assertIsNone(estimate({"counts": {"complete": 3}}, 27, None)["seconds_left"])


class FilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_log_file_caches_and_refreshes(self):
        log = self.root / "a.log"
        log.write_text(RAW)
        a = parse_log_file(str(log), "network", False)
        self.assertIs(parse_log_file(str(log), "network", False), a)
        self.assertEqual(parse_log_file(str(log), "network", True)["wells"][-1]["outcome"], "stopped")
        with log.open("a") as f:
            f.write("Processing Complete for well002\n")
        self.assertEqual(parse_log_file(str(log), "network", False)["wells"][-1]["outcome"], "complete")
        self.assertIsNone(parse_log_file(None, "network", False))
        self.assertIsNone(parse_log_file(str(self.root / "missing.log"), "network", False))
        self.assertIn("summary", parse_log_file(str(log), "activity", True))

    def test_outputs(self):
        out = self.root / "out"
        for w in ("well000", "well001"):
            d = out / "IPN" / "260821" / "M1" / "Network" / "000001" / w
            d.mkdir(parents=True)
            (d / "network_results.json").write_text("{}")
        n = out / "IPN" / "NWB" / "IPN" / "260821" / "M1" / "Network" / "000001"
        n.mkdir(parents=True)
        (n / "well000.nwb").write_bytes(b"x" * 100)
        (n / "well000.nwb.metadata").write_text("{}")
        log = self.root / "l.log"
        log.write_text("hi")
        items = outputs(str(out), "/nas/IPN/260821", "network", str(log),
                        [{"project": "IPN", "label": "260821", "path": "/r.html"},
                         {"project": "IPN", "label": "260822", "path": "/other.html"}])
        by = {i["label"]: i for i in items}
        self.assertEqual(by["Network results"]["count"], 2)
        self.assertEqual(by["NWB files"]["count"], 1)
        self.assertGreaterEqual(by["NWB files"]["bytes"], 100)
        self.assertEqual(by["Report"]["path"], "/r.html")
        self.assertEqual(by["Log"]["bytes"], 2)
        self.assertEqual(len(items), 4)
        act = outputs(str(out), "/nas/IPN/260821", "activity", None, [])
        self.assertEqual(act[0]["label"], "Activity scan results")
        self.assertEqual(act[0]["count"], 0)
        self.assertEqual(outputs(None, "/nas/IPN/260821", "network", None, []), [])

    def test_expected_wells(self):
        try:
            import h5py
        except ImportError:
            self.skipTest("h5py not available")
        date = self.root / "IPN" / "260821"
        for chip, run, wells in (("M1", "000001", ["well000", "well001"]), ("M2", "000002", ["well005"])):
            d = date / chip / "Network" / run
            d.mkdir(parents=True)
            with h5py.File(d / "data.raw.h5", "w") as f:
                for w in wells:
                    f.create_group(f"wells/{w}")
        act = date / "M1" / "ActivityScan" / "000003"
        act.mkdir(parents=True)
        with h5py.File(act / "data.raw.h5", "w") as f:
            f.create_group("wells/well000")
        rundetail._expected.pop(str(date), None)
        e = rundetail.expected_wells(str(date))
        self.assertEqual(e["total"], 3)
        self.assertEqual(e["by_recording"], {"M1/000001": 2, "M2/000002": 1})
        # Cached variant: answered from the cache now.
        self.assertEqual(rundetail.expected_wells_cached(str(date))["total"], 3)


if __name__ == "__main__":
    unittest.main()
