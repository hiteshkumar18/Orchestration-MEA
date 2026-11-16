"""Network analyses on the lab's Slurm cluster.

fake_mea_slurm.py stands in for /usr/local/bin/mea-slurm: same commands and
JSON, but each job runs here, pretending to be the computer Slurm picked.
Everything else is real: the job script, copying the recordings and earlier
results in, the pipeline (a stand-in) in its own process group, copying the
results out and checking them, deleting scratch, following the job, cancel,
and picking jobs up again after a restart.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
import slurm_backend
from watcher import JOB_NETWORK, JobConfig, Watcher

FAKE = Path(__file__).with_name("fake_mea_slurm.py")

# Reads its input folder, writes one well's results under
# --output-dir/<project>/<date>/, and takes <repo>/seconds/<date> seconds.
FAKE_DRIVER = """
import argparse, pathlib, sys, time
ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--output-dir")
a, _ = ap.parse_known_args()
inp = pathlib.Path(a.input)
secs = pathlib.Path(__file__).parent / "seconds" / inp.name
out = pathlib.Path(a.output_dir) / inp.parent.name / inp.name / "M07037" / "well000"
print("saw earlier well:", (out.parent / "well001" / "spike_times.npy").exists(), flush=True)
out.mkdir(parents=True, exist_ok=True)
(out / "spike_times.npy").write_text(str(inp))
(out / "binary").mkdir(exist_ok=True)
(out / "binary" / "big.dat").write_text("scratch, not a result")
print("processing", inp, "recordings:", sorted(str(p.relative_to(inp)) for p in inp.rglob("*.h5")), flush=True)
time.sleep(float(secs.read_text()) if secs.exists() else 0.2)
print("Successfully processed 1 of 1 well(s)", flush=True)
"""


def finished_run(date: Path, chip="M07037", run="000001"):
    r = date / chip / "Network" / run
    r.mkdir(parents=True)
    (r / "data.raw.h5").write_bytes(b"x" * 4096)
    (r / "mxassay.metadata").write_text("[runtime]\nfinished=2026-11-05\n")
    (r / ".metadata").write_text("meta")


def tree(root: Path) -> list:
    return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns)
                  for p in root.rglob("*"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.nas = self.root / "mnt" / "benshalom-nas"
        self.lab = self.nas / "raw" / "Lab"
        # The second computer mounts the NAS somewhere else.
        (self.root / "mnt" / "other").mkdir(parents=True)
        self.nas_b = self.root / "mnt" / "other" / "ben-shalom_nas"
        self.nas_b.symlink_to(self.nas, target_is_directory=True)
        self.repo = self.root / "MEA-Analysis"
        (self.repo / "seconds").mkdir(parents=True)
        (self.repo / "run_pipeline_driver.py").write_text(FAKE_DRIVER)
        self.out = self.root / "results"
        self.out.mkdir()
        self.shared = self.root / "mea-cluster" / "results" / "mea-bench"
        self.scratch = self.root / "mea-scratch" / "mea-bench"
        self.fake_dir = self.root / "fake-slurm"
        self.env = {"FAKE_SLURM_DIR": str(self.fake_dir), "FAKE_SLURM_NODES": "node-a",
                    "FAKE_SLURM_PENDING": "0", "FAKE_SLURM_KILLWAIT": "10"}
        old = {k: os.environ.get(k) for k in [*self.env, "FAKE_SLURM_FORGET", "FAKE_SLURM_REFUSE"]}
        os.environ.update(self.env)
        os.environ.pop("FAKE_SLURM_FORGET", None)
        os.environ.pop("FAKE_SLURM_REFUSE", None)

        def restore():
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.addCleanup(restore)
        self.client = self.root / "mea-slurm"
        self.client.write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE} \"$@\"\n")
        self.client.chmod(0o755)

    def project(self, name, dates):
        p = self.lab / name / name
        for d in dates:
            finished_run(p / d)
        return p

    def nodes(self):
        return [{"node": "node-a", "python": sys.executable, "mea_repo": str(self.repo), "nas": str(self.nas)},
                {"node": "node-b", "python": sys.executable, "mea_repo": str(self.repo), "nas": str(self.nas_b)}]

    def cfg(self, **kw):
        return JobConfig(**{
            "work_dir": str(self.root / "work"), "driver": str(self.repo / "run_pipeline_driver.py"),
            "driver_python": sys.executable, "run_network": True, "run_activity": False,
            "driver_options": {"output_dir": str(self.out), "skip_spikesorting": True},
            "executor": "slurm", "slurm_client": str(self.client), "slurm_nodes": self.nodes(),
            "slurm_nas_here": str(self.nas), "slurm_results_dir": str(self.shared),
            "slurm_scratch_dir": str(self.scratch), "slurm_poll_seconds": 1, "slurm_max_jobs": 2,
            "gpu_cooldown_seconds": 0, "queue_poll_seconds": 1, "kill_grace_seconds": 3, **kw})

    def make(self, reconcile=False, **kw):
        w = Watcher(self.cfg(**kw), reconcile=reconcile)
        w.preflight = lambda force=False: {"ok": True}
        self.addCleanup(lambda: (w.stop(), w.hold(), w._halt.set()))
        return w

    def wait_for(self, cond, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.2)
        return False

    def st(self, w, d):
        return w.state.get(w.state_key(d.resolve(), JOB_NETWORK))

    def submitted(self):
        c = self.fake_dir / "counter"
        return int(c.read_text()) - 99 if c.exists() else 0


class ScriptTest(Base):
    def test_the_script_is_valid_bash_with_awkward_names(self):
        s = slurm_backend.job_script(
            token="P_x-260901-abc", project="Proj 'quoted' $HOME", date="260901",
            nodes=self.nodes(), nas_rel="raw/Lab/Proj 'quoted' $HOME/260901",
            recordings=["M1/Network/000001/data.raw.h5"],
            args=["--output-dir", slurm_backend.OUT, "--note", "a b; rm -rf /"],
            scratch_root=str(self.scratch), results_root=str(self.shared),
            hdf5_plugin_path="/usr/local/hdf5/lib/plugin")
        r = subprocess.run(["bash", "-n"], input=s, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("'a b; rm -rf /'", s)
        self.assertIn('--output-dir "$W/out"', s)

    def test_unsafe_folders_are_refused(self):
        for bad in ("/", "/tmp", "relative/x/y"):
            with self.assertRaises(ValueError):
                slurm_backend.job_script(token="t", project="p", date="d", nodes=self.nodes(),
                                         nas_rel="x", recordings=[], args=[], scratch_root=bad,
                                         results_root=str(self.shared), hdf5_plugin_path="/x")

    def test_settings_are_checked(self):
        self.nas.mkdir(parents=True)
        self.shared.parent.mkdir(parents=True)
        c = self.cfg()
        self.assertEqual(c.validate_cluster(), [], c.validate_cluster())
        c.slurm_nodes = []
        self.assertTrue(any("computers" in e for e in c.validate_cluster()))
        c = self.cfg(nwb_convert=True)
        self.assertTrue(any("NWB" in e for e in c.validate_cluster()))
        c = self.cfg()
        c.driver_options["checkpoint_dir"] = "/x"
        self.assertTrue(any("--checkpoint-dir" in e for e in c.validate_cluster()))
        c = self.cfg(slurm_client="/no/such/client")
        self.assertTrue(any("not installed" in e for e in c.validate_cluster()))
        self.assertEqual(JobConfig(executor="banana").executor, "local")

    def test_settings_survive_saving(self):
        f = self.root / "job.json"
        self.cfg().save(f)
        c = JobConfig.load(f)
        self.assertEqual((c.executor, [n["node"] for n in c.slurm_nodes], c.slurm_max_jobs),
                         ("slurm", ["node-a", "node-b"], 2))


class ClusterRunTest(Base):
    def test_dates_run_on_the_cluster_and_come_back(self):
        p = self.project("B6J", ["260901", "260902", "260903"])
        before = tree(self.lab)
        # One date had a well finished before.
        old = self.out / "B6J" / "260902" / "M07037" / "well001"
        old.mkdir(parents=True)
        (old / "spike_times.npy").write_text("finished before")
        (self.repo / "seconds" / "260901").write_text("2")
        w = self.make()
        ds = sorted(p.iterdir())
        for d in ds:
            w.dispatch(d, JOB_NETWORK)
            time.sleep(0.05)
        # Two at a time: the third waits in this server's own line.
        self.assertTrue(self.wait_for(lambda: self.st(w, ds[2]).get("line_position") == 1
                                      or any(r["run"] == "260903" and r.get("line_position") == 1
                                             for r in w.snapshot()["runs"]), 10))
        self.assertTrue(self.wait_for(lambda: all(self.st(w, d).get("status") == "done" for d in ds), 90),
                        [(self.st(w, d).get("status"), self.st(w, d).get("error")) for d in ds])
        self.assertEqual(self.submitted(), 3, "one job per date, none twice")
        for d in ds:
            e = self.st(w, d)
            self.assertEqual(e.get("worker"), "node-a")
            self.assertTrue(e.get("slurm_job_id"))
            res = self.out / "B6J" / d.name / "M07037" / "well000" / "spike_times.npy"
            self.assertTrue(res.exists(), d)
            # Made from the cluster computer's own copy of the recordings.
            self.assertIn(str(self.scratch), res.read_text())
            self.assertFalse((res.parent / "binary").exists(), "scratch binary stays behind")
            log = Path(e["log"]).read_text()
            self.assertIn("MEA-BENCH node=node-a", log)
            self.assertIn("results copied and checked; scratch deleted", log)
            self.assertIn("recordings: ['M07037/Network/000001/data.raw.h5']", log)
        self.assertIn("saw earlier well: True", Path(self.st(w, ds[1])["log"]).read_text())
        self.assertEqual((old / "spike_times.npy").read_text(), "finished before")
        self.assertEqual(list(self.shared.iterdir()), [], "shared job folders deleted")
        self.assertEqual(list(self.scratch.iterdir()), [], "scratch deleted")
        self.assertEqual(tree(self.lab), before, "recordings untouched")
        snap = w.snapshot()
        self.assertEqual((snap["executor"], snap["limits"][JOB_NETWORK]), ("slurm", 2))

    def test_a_computer_with_its_own_nas_path(self):
        p = self.project("B6J", ["260901"])
        os.environ["FAKE_SLURM_NODES"] = "node-b"
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "done", 60), self.st(w, d))
        log = Path(self.st(w, d)["log"]).read_text()
        self.assertIn(f"recordings={self.nas_b}/raw/Lab/B6J/B6J/260901", log)
        self.assertEqual(self.st(w, d)["worker"], "node-b")

    def test_waiting_in_the_cluster_queue_says_so(self):
        p = self.project("B6J", ["260901"])
        os.environ["FAKE_SLURM_PENDING"] = "4"
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "queued"
                                      and "cluster queue (Resources)" in (self.st(w, d).get("detail") or ""), 20))
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "done", 60))

    def test_hold_cancels_the_cluster_job(self):
        p = self.project("B6J", ["260901"])
        (self.repo / "seconds" / "260901").write_text("120")
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: "processing" in (Path(self.st(w, d)["log"]).read_text()
                                                              if self.st(w, d).get("log") and Path(self.st(w, d)["log"]).exists() else ""), 30))
        w.hold([w.state_key(d.resolve(), JOB_NETWORK)])
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "held", 60), self.st(w, d))
        state = json.loads((self.fake_dir / "state" / f"{self.st(w, d)['slurm_job_id']}.json").read_text())
        self.assertEqual(state["state"], "CANCELLED")
        self.assertTrue((self.out / "B6J" / "260901" / "M07037" / "well000" / "spike_times.npy").exists(),
                        "what it finished was kept")
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertEqual(list(self.shared.iterdir()), [])
        self.assertIn("MEA-BENCH: stop requested", Path(self.st(w, d)["log"]).read_text())

    def test_a_cancel_while_waiting_in_the_cluster_queue(self):
        p = self.project("B6J", ["260901"])
        os.environ["FAKE_SLURM_PENDING"] = "30"
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "queued"
                                      and self.st(w, d).get("slurm_job_id"), 20))
        w.cancel_all()
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "failed", 30), self.st(w, d))
        self.assertIn("stopped by hand", self.st(w, d)["error"])
        self.assertEqual(list(self.shared.iterdir()), [])

    def test_restart_follows_the_job_instead_of_resubmitting(self):
        p = self.project("B6J", ["260901"])
        (self.repo / "seconds" / "260901").write_text("5")
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "running", 30))
        w._halt.set()                              # the server stops; the job carries on
        time.sleep(1.5)
        self.assertEqual(self.st(w, d)["status"], "running")
        w2 = self.make(reconcile=True)
        self.assertTrue(self.wait_for(lambda: self.st(w2, d).get("status") == "done", 60), self.st(w2, d))
        self.assertEqual(self.submitted(), 1, "not submitted again")
        self.assertTrue((self.out / "B6J" / "260901" / "M07037" / "well000" / "spike_times.npy").exists())
        self.assertIn("Successfully processed", Path(self.st(w2, d)["log"]).read_text())

    def test_a_job_slurm_has_forgotten_still_ends_properly(self):
        p = self.project("B6J", ["260901"])
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "running", 30))
        w._halt.set()
        time.sleep(4)                              # it finishes while no server follows it
        os.environ["FAKE_SLURM_FORGET"] = "1"
        w2 = self.make(reconcile=True)
        self.assertTrue(self.wait_for(lambda: self.st(w2, d).get("status") == "done", 60), self.st(w2, d))
        self.assertEqual(list(self.shared.iterdir()), [])

    def test_a_refused_submission_fails_clearly(self):
        p = self.project("B6J", ["260901"])
        os.environ["FAKE_SLURM_REFUSE"] = "Limits: 1–24 CPUs"
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "failed", 30))
        self.assertIn("the cluster did not take this date: Limits", self.st(w, d)["error"])
        self.assertFalse(self.shared.exists() and list(self.shared.iterdir()))

    def test_a_date_not_on_the_nas_is_not_sent(self):
        local = self.root / "local-disk" / "Lab" / "P" / "P"
        finished_run(local / "260901")
        w = self.make()
        w.dispatch(local / "260901", JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, local / "260901").get("status") == "failed", 30))
        self.assertIn("not on the NAS", self.st(w, local / "260901")["error"])
        self.assertEqual(self.submitted(), 0)

    def test_a_computer_without_settings_is_reported(self):
        p = self.project("B6J", ["260901"])
        os.environ["FAKE_SLURM_NODES"] = "node-z"
        w = self.make()
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "failed", 30))
        self.assertIn("no settings for", self.st(w, d)["error"])

    def test_spike_sorting_asks_for_a_gpu_on_the_chosen_computer(self):
        p = self.project("B6J", ["260901"])
        w = self.make(slurm_gpu_node="node-b")
        w.cfg.driver_options["skip_spikesorting"] = False
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") in ("done", "failed"), 60))
        state = json.loads((self.fake_dir / "state" / f"{self.st(w, d)['slurm_job_id']}.json").read_text())
        self.assertEqual((state["gpu"], state["want_node"], state["cpus"], state["mem"]),
                         (True, "node-b", 8, 32 * 1024))

    def test_local_stays_local(self):
        p = self.project("B6J", ["260901"])
        w = self.make(executor="local")
        d = next(p.iterdir())
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "done", 60), self.st(w, d))
        self.assertEqual(self.submitted(), 0)
        self.assertFalse(self.st(w, d).get("slurm_job_id"))


class StopsAndLeftoversTest(Base):
    """Scratch copies on the cluster's computers never outlive their job."""

    def slow(self, name, seconds):
        """A PATH folder where `name` first sleeps, then does its job."""
        d = self.root / f"slow-{name}"
        d.mkdir(exist_ok=True)
        real = shutil.which(name)
        (d / name).write_text(f"#!/bin/sh\nsleep {seconds}\nexec {real} \"$@\"\n")
        (d / name).chmod(0o755)
        return d

    def test_a_stop_while_copying_recordings_deletes_scratch(self):
        p = self.project("B6J", ["260901"])
        token = "B6J-260901-abc"
        script = slurm_backend.job_script(
            token=token, project="B6J", date="260901", nodes=self.nodes()[:1], nas_rel=str(
                (p / "260901").relative_to(self.nas)), recordings=["M07037/Network/000001/data.raw.h5"],
            args=["--output-dir", slurm_backend.OUT], scratch_root=str(self.scratch),
            results_root=str(self.shared), hdf5_plugin_path="/nonexistent")
        host = self.root / "host"
        host.mkdir()
        (host / "hostname").write_text("#!/bin/sh\necho node-a\n")
        (host / "hostname").chmod(0o755)
        job = self.root / "job.sh"
        job.write_text(script)
        env = {**os.environ, "PATH": f"{host}:{self.slow('cp', 30)}:{os.environ['PATH']}"}
        proc = subprocess.Popen(["bash", str(job)], env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, start_new_session=True)
        self.assertTrue(self.wait_for(lambda: (self.scratch / token / ".input").is_dir(), 20))
        os.killpg(proc.pid, 15)                 # Slurm signals every process in the job
        text, _ = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 143, text)
        self.assertIn("MEA-BENCH: stop requested", text)
        self.assertIn("MEA-BENCH scratch deleted", text)
        self.assertFalse((self.scratch / token).exists())
        self.assertEqual((self.shared / token / "exit_code").read_text().strip(), "143")

    def test_a_hold_during_the_copy_of_earlier_results_is_quick(self):
        p = self.project("B6J", ["260901"])
        d = next(p.iterdir())
        earlier = self.out / "B6J" / "260901" / "M07037" / "well001"
        earlier.mkdir(parents=True)
        (earlier / "spike_times.npy").write_text("done before")
        old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.slow('rsync', 60)}:{old_path}"
        self.addCleanup(lambda: os.environ.__setitem__("PATH", old_path))
        w = self.make()
        w.dispatch(d, JOB_NETWORK)
        self.assertTrue(self.wait_for(lambda: "copying earlier results" in (self.st(w, d).get("detail") or ""), 30))
        t = time.time()
        w.hold([w.state_key(d.resolve(), JOB_NETWORK)])
        self.assertTrue(self.wait_for(lambda: self.st(w, d).get("status") == "held", 20), self.st(w, d))
        self.assertLess(time.time() - t, 15)
        self.assertEqual(self.submitted(), 0, "nothing was sent to the cluster")
        self.assertTrue(self.wait_for(lambda: not self.shared.exists() or list(self.shared.iterdir()) == [], 10))
        self.assertTrue((earlier / "spike_times.npy").exists(), "earlier results untouched")

    def test_scratch_left_by_a_killed_job_is_cleaned_up(self):
        w = self.make()
        d = self.project("B6J", ["260901"]) / "260901"
        token = "B6J-260901-killed"
        left = self.scratch / token / "out"
        left.mkdir(parents=True)
        (left / "x.npy").write_text("partial")
        log = self.root / "run.log"
        log.write_text("MEA-BENCH node=node-a job=1\nprocessing\n")
        w._sweep_left_scratch(d, "node-a", token, log, None)
        self.assertEqual(self.submitted(), 1)
        self.assertTrue(self.wait_for(lambda: not (self.scratch / token).exists(), 20))
        self.assertTrue(self.scratch.is_dir(), "only that job's folder")

        # Not when the job said it cleaned up, kept scratch on purpose, or never started.
        (self.scratch / token).mkdir()
        log.write_text("MEA-BENCH node=node-a\nMEA-BENCH scratch deleted\n")
        w._sweep_left_scratch(d, "node-a", token, log, 0)
        log.write_text("MEA-BENCH node=node-a\nscratch kept\n")
        w._sweep_left_scratch(d, "node-a", token, log, slurm_backend.EXIT_COPY_RESULTS)
        log.write_text("cluster job 5 sent\n")
        w._sweep_left_scratch(d, "node-a", token, log, None)
        self.assertEqual(self.submitted(), 1)
        self.assertTrue((self.scratch / token).exists())

    def test_cleanup_refuses_odd_tokens(self):
        for bad in ("..", "a/b", "", "x y"):
            with self.assertRaises(ValueError):
                slurm_backend.cleanup_script(token=bad, scratch_root=str(self.scratch))
        with self.assertRaises(ValueError):
            slurm_backend.cleanup_script(token="ok", scratch_root="/tmp")

    def test_wells_from_a_copy_of_the_recordings_belong_to_their_date(self):
        import checkpoints
        folder = "/mnt/nas/raw/Lab/B6J/B6J/260901"
        on_node = "/mnt/mea-scratch/mea-bench/B6J-260901-x/.input/B6J/260901/M07037/Network/000001/data.raw.h5"
        self.assertTrue(checkpoints.recording_in_folder(on_node, folder))
        self.assertFalse(checkpoints.recording_in_folder(on_node.replace("260901/M", "260902/M"), folder))
        self.assertFalse(checkpoints.recording_in_folder(on_node.replace("/B6J/260901", "/C57/260901"), folder))


class CheckScriptTest(Base):
    def test_check_reports_each_part(self):
        p = self.project("B6J", ["260901"])
        s = slurm_backend.check_script(
            nodes=self.nodes(), sample_rel="raw/Lab/B6J/B6J/260901/M07037/Network/000001/data.raw.h5",
            results_root=str(self.shared), scratch_root=str(self.scratch),
            hdf5_plugin_path=str(self.root), sorting=False, imports=["json", "no_such_module"])
        self.shared.mkdir(parents=True)
        self.scratch.mkdir(parents=True)
        fake_host = self.root / "h"
        fake_host.mkdir()
        (fake_host / "hostname").write_text("#!/bin/sh\necho node-b\n")
        (fake_host / "hostname").chmod(0o755)
        r = subprocess.run(["bash"], input=s, text=True, capture_output=True,
                           env={**os.environ, "PATH": f"{fake_host}:{os.environ['PATH']}"})
        steps = {x["what"]: x for x in slurm_backend.parse_check(r.stdout)}
        self.assertTrue(steps["nas"]["ok"] and steps["mea-analysis"]["ok"] and steps["write"]["ok"])
        self.assertFalse(steps["python"]["ok"])
        self.assertIn("no_such_module", steps["python"]["say"])
        self.assertFalse(steps["hdf5-plugin"]["ok"])
        self.assertFalse(steps["recording"]["ok"], "the stand-in file is not a real recording")
        self.assertEqual(sorted(x.name for x in self.shared.iterdir()), [], "test folders removed")
        self.assertTrue(p.exists())


if __name__ == "__main__":
    unittest.main()
