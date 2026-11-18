"""The MaxWell-style page of a chip, on small stand-in recordings laid out
like MaxWell's files (data_store blocks, spikes in ADC units, electrode map)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import h5py
import numpy as np

import _path  # noqa: F401
import activity_scan
import activity_trends
import api
import maxwell_summary as ms
from fastapi import HTTPException
from rundetail import outputs

LSB = 6.29425e-6          # volts per ADC unit at gain 512
FS = 10000.0


def write_recording(path: Path, blocks, wells=((0, "1", "WT"), (1, "2", "KO")), chip="M1"):
    """blocks: (well_id, electrodes, seconds, spikes) with spikes as
    (time s, index into electrodes, amplitude in ADC units)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        f["wellplate/id"] = [chip.encode()]
        for i, (wid, name, group) in enumerate(wells):
            g = f.create_group(f"wellplate/well{i:03d}")
            g["id"], g["name"], g["group_name"] = [wid], [name.encode()], [group.encode()]
        for b, (wid, elecs, secs, spikes) in enumerate(blocks):
            g = f.create_group(f"data_store/data{b:04d}")
            g["well_id"] = [wid]
            g["start_time"], g["stop_time"] = [1_000_000], [1_000_000 + int(secs * 1000)]
            g["settings/lsb"], g["settings/sampling"] = [LSB], [FS]
            chans = np.arange(len(elecs)) + 100
            m = np.zeros(len(elecs), [("channel", "<i4"), ("electrode", "<i4"), ("x", "<f8"), ("y", "<f8")])
            m["channel"], m["electrode"] = chans, elecs
            m["x"], m["y"] = (np.array(elecs) % 220) * 17.5, (np.array(elecs) // 220) * 17.5
            g["settings/mapping"] = m
            f0 = 5_000_000 + b * 1_000_000
            g["groups/routed/frame_nos"] = np.arange(f0, f0 + int(secs * FS), 1000, dtype=np.uint64)
            sp = np.zeros(len(spikes), [("frameno", "<i8"), ("channel", "<i4"), ("amplitude", "<f4")])
            for k, (t, ei, amp) in enumerate(spikes):
                sp[k] = (f0 + round(t * FS), chans[ei], -amp)
            g["spikes"] = sp


def scan_blocks():
    # Well 0: electrode 10 fires at 2 Hz with 8 ADC units (~50 µV), 5 ms apart
    # in pairs; electrode 11 fires once (0.1 Hz) but small (2 units ~13 µV);
    # electrode 12 is silent. Well 1: electrode 500 fires at 1 Hz, 10 units.
    pairs = [(t + d, 0, 8.0) for t in range(0, 10, 1) for d in (0.0, 0.005)]
    return [(0, [10, 11], 10.0, pairs + [(5.5, 1, 2.0)]),
            (0, [12], 10.0, []),
            (1, [500], 10.0, [(t + 0.2, 0, 10.0) for t in range(10)])]


class ReadTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.dir = Path(d.name)

    def test_scan_rates_amplitudes_and_active(self):
        f = self.dir / "scan.h5"
        write_recording(f, scan_blocks())
        s = ms.read_scan(f)
        w0, w1 = s[0], s[1]
        self.assertEqual(w0["label"], "Well 1 · WT")
        self.assertAlmostEqual(w0["rate"][10], 2.0)
        self.assertAlmostEqual(w0["amp"][10], 8 * LSB * 1e6, places=3, msg="amplitudes in µV, not ADC units")
        self.assertAlmostEqual(w0["rate"][11], 0.1)
        self.assertEqual(w0["rate"][12], 0.0, "silent but recorded")
        self.assertTrue(np.isnan(w0["rate"][13]), "never recorded")
        self.assertTrue(w0["active"][10])
        self.assertFalse(w0["active"][11], "fires but below 20 µV")
        self.assertEqual(int(w0["active"].sum()), 1)
        self.assertTrue(np.allclose(w0["isi"], 5.0), "only intervals up to 150 ms")
        self.assertEqual(len(w0["isi"]), 10)
        self.assertTrue(w1["active"][500])

    def test_network_times_start_at_the_recording(self):
        f = self.dir / "net.h5"
        write_recording(f, [(0, [10, 11, 12], 90.0, [(0.5, 0, 9), (30.0, 2, 9), (70.0, 1, 9)])])
        n = ms.read_network(f)[0]
        self.assertEqual(n["span"], 60.0, "the first minute")
        self.assertEqual(list(np.round(n["t"], 3)), [0.5, 30.0])
        self.assertEqual(list(n["row"]), [0, 2])
        self.assertEqual(n["channels"], 3)

    def test_the_page_stands_alone(self):
        scan, net = self.dir / "scan.h5", self.dir / "net.h5"
        write_recording(scan, scan_blocks())
        write_recording(net, [(0, [10, 11], 20.0, [(t, 0, 9) for t in np.arange(0, 20, 0.1)]),
                              (1, [500], 20.0, [(t, 0, 9) for t in np.arange(0, 20, 0.5)])])
        out = ms.write_page(self.dir / "page.html", scan=scan, network=net, title="P · 260923 · chip M1")
        t = out.read_text()
        for s in ("Network Analysis", "Active Area", "Results View", "Well 1 · WT", "Well 2 · KO",
                  "<select id=well", "Active Area: "):
            self.assertIn(s, t)
        self.assertEqual(t.count("data:image/png;base64,"), 6, "2 network + 2 active area + 2 results")
        self.assertNotIn("src='http", t)
        self.assertNotIn('src="http', t)

    def test_a_chip_without_a_network_recording(self):
        scan = self.dir / "scan.h5"
        write_recording(scan, scan_blocks())
        t = ms.write_page(self.dir / "page.html", scan=scan, network=None, title="x").read_text()
        self.assertNotIn("Network Analysis", t)
        self.assertIn("Active Area", t)


class ActivityScanWritesItTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.dir = Path(d.name)
        chip = self.dir / "lab" / "Proj" / "Proj" / "260923" / "M1"
        self.scan = chip / "ActivityScan" / "000010" / "data.raw.h5"
        write_recording(self.scan, scan_blocks())
        write_recording(chip / "Network" / "000011" / "data.raw.h5",
                        [(0, [10, 11], 20.0, [(t, 0, 9) for t in np.arange(0, 20, 0.1)])])
        self.out = self.dir / "out"

    def run_scan(self):
        return activity_scan.process_file(self.scan, self.out, selection_auto="Network")

    def test_the_page_sits_beside_the_scan_results(self):
        s = self.run_scan()
        page = Path(s["output_dir"]) / "maxwell_summary.html"
        self.assertEqual(Path(s["output_dir"]), self.out / "260923" / "M1" / "000010")
        self.assertTrue(page.is_file())
        self.assertIn("Network Analysis", page.read_text(), "found the chip's Network recording")
        self.assertIn("Proj · 260923 · chip", page.read_text())

    def test_amplitudes_are_in_microvolts(self):
        s = self.run_scan()
        self.assertEqual(s["amplitude_units"], "uV")
        w0 = s["wells"][0]
        self.assertGreater(w0["amplitude_mean_uv"], 30, "ADC units would be under 10")

    def test_a_failing_page_does_not_fail_the_scan(self):
        with mock.patch("maxwell_summary.write_page", side_effect=RuntimeError("boom")):
            s = self.run_scan()
        self.assertTrue((Path(s["output_dir"]) / "summary.json").is_file())
        self.assertFalse((Path(s["output_dir"]) / "maxwell_summary.html").exists())

    def test_the_date_page_lists_and_serves_it(self):
        self.run_scan()
        # The bench's layout: <output>/<project>/ActivityScan/<date>/<chip>/<run>
        out_root = self.dir / "results"
        (out_root / "Proj").mkdir(parents=True)
        (self.out).rename(out_root / "Proj" / "ActivityScan")
        items = outputs(str(out_root), str(self.dir / "lab/Proj/Proj/260923"), "activity", None, [])
        pages = [i for i in items if i.get("maxwell")]
        self.assertEqual([i["label"] for i in pages], ["MaxWell view · chip M1"])
        w = mock.Mock(cfg=mock.Mock(output_dir=str(out_root), activity_out=str(out_root)))
        with mock.patch.object(api, "_watcher", w):
            self.assertEqual(Path(api.api_maxwell_view(pages[0]["path"]).path).name, "maxwell_summary.html")
            other = out_root / "Proj" / "ActivityScan" / "260923" / "M1" / "000010" / "summary.json"
            with self.assertRaises(HTTPException) as e:
                api.api_maxwell_view(str(other))
            self.assertEqual(e.exception.status_code, 403)
            outside = self.dir / "maxwell_summary.html"
            outside.write_text("x")
            with self.assertRaises(HTTPException):
                api.api_maxwell_view(str(outside))


class TrendsTest(unittest.TestCase):
    def test_old_amplitudes_are_left_out(self):
        with tempfile.TemporaryDirectory() as d:
            for name, units in (("old", None), ("new", "uV")):
                p = Path(d) / name / "summary.json"
                p.parent.mkdir()
                s = {"source": f"/x/{name}/data.raw.h5", "wells": [{"well_id": 1, "amplitude_mean_uv": 7.0,
                                                                     "rate_mean_hz": 1.0}]}
                if units:
                    s["amplitude_units"] = units
                p.write_text(json.dumps(s))
            rows = {Path(r["summary_file"]).parent.name: r for r in activity_trends.load_summaries(Path(d))}
        self.assertNotIn("amplitude_mean_uv", rows["old"])
        self.assertEqual(rows["old"]["rate_mean_hz"], 1.0)
        self.assertEqual(rows["new"]["amplitude_mean_uv"], 7.0)


if __name__ == "__main__":
    unittest.main()
