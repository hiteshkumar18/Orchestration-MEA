#!/usr/bin/env python3
"""A stand-in for the lab's /usr/local/bin/mea-slurm, for tests.

Same commands and JSON as the real client (submit, status, logs, cancel).
Jobs run here, detached, as the current user. Controlled by environment
variables:

  FAKE_SLURM_DIR       where jobs, logs and job states are kept (required)
  FAKE_SLURM_NODES     computers to pick from, comma separated (first free)
  FAKE_SLURM_PENDING   seconds a job waits as PENDING before it runs
  FAKE_SLURM_FORGET    "1": finished jobs are no longer known (as after a day)
  FAKE_SLURM_REFUSE    a message: refuse every submission with it
  FAKE_SLURM_KILLWAIT  seconds between TERM and KILL on cancel (Slurm: 30)
"""
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

D = Path(os.environ["FAKE_SLURM_DIR"])


def fail(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


def state_file(j):
    return D / "state" / f"{j}.json"


def read(j):
    f = state_file(j)
    if not f.exists():
        fail("Invalid job id specified")
    st = json.loads(f.read_text())
    if os.environ.get("FAKE_SLURM_FORGET") == "1" and st["state"] in ("COMPLETED", "FAILED", "CANCELLED"):
        fail("Invalid job id specified")
    return st


def write(j, **kw):
    f = state_file(j)
    st = json.loads(f.read_text()) if f.exists() else {}
    st.update(kw)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(st))
    tmp.replace(f)
    return st


def record(st):
    return {"job_id": st["job_id"], "state": st["state"], "nodes": st.get("node") or "(null)",
            "exit_code": st.get("exit_code", "0:0"), "reason": st.get("reason", "None"),
            "cpus": str(st.get("cpus", 1))}


def submit(args):
    if os.environ.get("FAKE_SLURM_REFUSE"):
        fail(os.environ["FAKE_SLURM_REFUSE"])
    opts = {"--cpus": "8", "--mem-mib": "16384", "--minutes": "240", "--name": "mea-job", "--node": ""}
    gpu = False
    i = 0
    while i < len(args):
        if args[i] == "--gpu":
            gpu = True
            i += 1
        else:
            opts[args[i]] = args[i + 1]
            i += 2
    body = sys.stdin.read()
    if not body:
        fail("Provide a batch script on stdin (maximum 1 MiB)")
    (D / "state").mkdir(parents=True, exist_ok=True)
    (D / "logs").mkdir(exist_ok=True)
    counter = D / "counter"
    j = int(counter.read_text()) + 1 if counter.exists() else 100
    counter.write_text(str(j))
    token = uuid.uuid4().hex
    work = D / "jobs" / token
    work.mkdir(parents=True)
    (work / "job.sbatch").write_text(body)
    log = D / "logs" / f"{token}-{j}.out"
    node = opts["--node"] or os.environ.get("FAKE_SLURM_NODES", "node-a").split(",")[0]
    write(j, job_id=str(j), state="PENDING", reason="Resources", node=None, want_node=node,
          cpus=int(opts["--cpus"]), gpu=gpu, name=opts["--name"], log=str(log), work=str(work),
          mem=int(opts["--mem-mib"]), minutes=int(opts["--minutes"]))
    subprocess.Popen([sys.executable, __file__, "_run", str(j)], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(json.dumps({"job_id": str(j), "workspace": str(work), "log": str(log)}))


def run(j):
    st = json.loads(state_file(j).read_text())
    end = time.time() + float(os.environ.get("FAKE_SLURM_PENDING", "0"))
    while time.time() < end:
        if json.loads(state_file(j).read_text()).get("cancel"):
            write(j, state="CANCELLED", reason="None", exit_code="0:15")
            return
        time.sleep(0.2)
    node = st["want_node"]
    host = Path(st["work"]) / ".host"
    host.mkdir()
    (host / "hostname").write_text(f"#!/bin/sh\necho {node}\n")
    (host / "hostname").chmod(0o755)
    env = {**os.environ, "PATH": f"{host}:{os.environ['PATH']}", "SLURM_JOB_ID": str(j),
           "SLURM_CPUS_PER_TASK": str(st["cpus"])}
    env.pop("FAKE_SLURM_FORGET", None)
    with open(st["log"], "w") as log:
        p = subprocess.Popen(["bash", str(Path(st["work"]) / "job.sbatch")], cwd=st["work"],
                             env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(j, state="RUNNING", reason="None", node=node, pid=p.pid)
        rc = p.wait()
    st = json.loads(state_file(j).read_text())
    if st.get("cancel"):
        write(j, state="CANCELLED", exit_code=f"{max(rc, 0)}:15")
    else:
        write(j, state="COMPLETED" if rc == 0 else "FAILED", exit_code=f"{rc if rc >= 0 else 0}:0")


def cancel(j):
    st = read(j)
    write(j, cancel=True)
    if st["state"] == "RUNNING" and st.get("pid"):
        pid = st["pid"]
        try:
            os.kill(pid, signal.SIGTERM)            # the batch shell, as Slurm does first
        except ProcessLookupError:
            return
        def later():
            time.sleep(float(os.environ.get("FAKE_SLURM_KILLWAIT", "30")))
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        if os.fork() == 0:
            os.setsid()
            later()
            os._exit(0)


def main():
    a = sys.argv[1:]
    if not a:
        fail("no command")
    if a[0] == "_run":
        return run(int(a[1]))
    if a[0] == "submit":
        return submit(a[1:])
    j = int(a[1])
    if a[0] == "status":
        print(json.dumps(record(read(j))))
    elif a[0] == "cancel":
        cancel(j)
        print(json.dumps({**record(read(j)), "cancel_requested": True}))
    elif a[0] == "logs":
        st = read(j)
        text = Path(st["log"]).read_bytes()[-65536:].decode(errors="replace") if Path(st["log"]).exists() else ""
        print(json.dumps({**record(st), "text": text}))
    else:
        fail(f"unknown command {a[0]}")


if __name__ == "__main__":
    main()
