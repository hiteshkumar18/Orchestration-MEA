"""
Locate and validate the MEA-Analysis checkout this orchestrator drives.

Orchestration-MEA is a **separate repository**. It never imports MEA-Analysis —
it invokes ``run_pipeline_driver.py`` as a subprocess and reads the output and
checkpoint files the pipeline writes. That keeps the analysis repo untouched and
lets the two evolve independently.

The cost of that independence is a contract expressed in two places: the driver's
argparse surface (mirrored in ``driver_schema.py``) and the checkpoint schema
(mirrored in ``checkpoints.py``). Both are checked at startup so a drift shows up
as a warning rather than as a silently wrong command months later.

Resolution order for the MEA repo path:

1. ``--mea-repo`` on the command line
2. ``MEA_REPO`` in the environment (or ``.env``)
3. ``mea_repo`` in the saved job config
4. A sibling ``../MEA-Analysis`` directory
"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Any, Optional

LOG = logging.getLogger("mea.repo")

DRIVER_NAME = "run_pipeline_driver.py"
ROUTINE_NAME = "mea_analysis_routine.py"

# What the pipeline needs that this orchestrator deliberately does not install.
# Used to check an interpreter before it is used to launch the driver.
DRIVER_IMPORTS = ("pandas", "h5py", "spikeinterface")


def _in_our_venv(python: str) -> bool:
    """True if this interpreter is the orchestration virtualenv."""
    try:
        return Path(python).resolve().is_relative_to(
            (Path(__file__).resolve().parent.parent / ".venv").resolve())
    except (OSError, ValueError, AttributeError):
        return False


def candidate_pythons(repo: Optional[Path]) -> list[str]:
    """Interpreters that might have the pipeline's dependencies, best first.

    The orchestration venv is intentionally last: it holds fastapi/h5py/numpy
    for this tool, not pandas/torch/kilosort for the pipeline. Launching the
    driver with it fails at ``import pandas``.
    """
    import shutil
    import sys as _sys

    out: list[str] = []
    if repo:
        for rel in (".venv/bin/python", "venv/bin/python", "env/bin/python"):
            p = repo / rel
            if p.is_file():
                out.append(str(p))
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found and not _in_our_venv(found):
            out.append(found)
    out.append(_sys.executable)          # last resort
    # de-duplicate, keep order
    seen, uniq = set(), []
    for p in out:
        rp = str(Path(p).resolve()) if Path(p).exists() else p
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def check_python(python: str, modules: tuple[str, ...] = DRIVER_IMPORTS) -> dict[str, Any]:
    """Ask an interpreter which of the pipeline's dependencies it can import."""
    import subprocess
    code = ("import json,sys;m={};" +
            "".join(f"\ntry:\n import {m} as _x\n m[{m!r}]=getattr(_x,'__version__','?')\n"
                    f"except Exception as e:\n m[{m!r}]=None\n" for m in modules) +
            "\nprint(json.dumps({'v':sys.version.split()[0],'m':m}))")
    try:
        r = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"python": python, "ok": False, "error": (r.stderr or "").strip()[:200]}
        import json as _json
        data = _json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as exc:  # noqa: BLE001
        return {"python": python, "ok": False, "error": str(exc)[:200]}

    missing = [k for k, v in data["m"].items() if v is None]
    return {
        "python": python,
        "version": data["v"],
        "modules": data["m"],
        "missing": missing,
        "ok": not missing,
    }


def find_driver_python(repo: Optional[Path], explicit: str = "") -> dict[str, Any]:
    """Pick an interpreter that can actually run the driver.

    An explicit choice is reported as-is even when incomplete — the operator's
    setting is not silently replaced, but the problem is named.
    """
    if explicit:
        res = check_python(explicit)
        res["source"] = "configured"
        return res

    tried = []
    for cand in candidate_pythons(repo):
        res = check_python(cand)
        tried.append({"python": cand, "missing": res.get("missing"), "ok": res.get("ok")})
        if res.get("ok"):
            res["source"] = "auto-detected"
            res["tried"] = tried
            return res

    import sys as _sys
    fallback = check_python(_sys.executable)
    fallback["source"] = "fallback"
    fallback["tried"] = tried
    return fallback


def candidate_paths(explicit: Optional[str] = None) -> list[Path]:
    here = Path(__file__).resolve().parent.parent
    out: list[Path] = []
    if explicit:
        out.append(Path(explicit).expanduser())
    if os.environ.get("MEA_REPO"):
        out.append(Path(os.environ["MEA_REPO"]).expanduser())
    out += [here.parent / "MEA-Analysis", here.parent / "MEA_Analysis", Path("/MEA_Analysis")]
    return out


def find_mea_repo(explicit: Optional[str] = None) -> Optional[Path]:
    """First candidate that actually contains the driver.

    An explicitly supplied path is never silently overridden: if it is given and
    does not contain the driver, that is an error rather than a reason to fall
    back to a sibling checkout, which would quietly run the wrong code.
    """
    def has_driver(p: Path) -> bool:
        try:
            return (p / DRIVER_NAME).is_file()
        except OSError:
            return False

    if explicit:
        p = Path(explicit).expanduser()
        if has_driver(p):
            return p.resolve()
        LOG.error("Given MEA repo has no %s: %s — not falling back to another checkout",
                  DRIVER_NAME, p)
        return None

    for p in candidate_paths():
        if has_driver(p):
            return p.resolve()
    return None


def describe(repo: Optional[Path]) -> dict[str, Any]:
    """Summary of the linked repo, for the UI and startup banner."""
    if repo is None:
        return {"found": False}
    info: dict[str, Any] = {
        "found": True,
        "path": str(repo),
        "driver": str(repo / DRIVER_NAME),
        "has_routine": (repo / ROUTINE_NAME).is_file(),
    }
    head = repo / ".git" / "HEAD"
    try:
        if head.is_file():
            ref = head.read_text().strip()
            if ref.startswith("ref: "):
                info["branch"] = ref.split("/")[-1]
                sha = repo / ".git" / ref[5:]
                if sha.is_file():
                    info["commit"] = sha.read_text().strip()[:8]
            else:
                info["commit"] = ref[:8]
    except OSError:
        pass
    return info


# --------------------------------------------------------------------------- #
# Contract checks — catch drift between the two repos
# --------------------------------------------------------------------------- #
def driver_arguments(repo: Path) -> dict[str, Any]:
    """Parse the driver's ``add_argument`` calls without importing or running it.

    Uses the AST, so this works even when the pipeline's heavy dependencies
    (torch, kilosort, spikeinterface) are not installed on this machine.
    """
    src = (repo / DRIVER_NAME).read_text(errors="ignore")
    found: dict[str, Any] = {}
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        LOG.warning("Could not parse %s: %s", DRIVER_NAME, exc)
        return found

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            continue
        flags = [a.value for a in node.args
                 if isinstance(a, ast.Constant) and isinstance(a.value, str)
                 and a.value.startswith("--")]
        if not flags:
            continue
        spec: dict[str, Any] = {"default": None, "action": None, "choices": None}
        for kw in node.keywords:
            if kw.arg == "default":
                try:
                    spec["default"] = ast.literal_eval(kw.value)
                except (ValueError, SyntaxError):
                    spec["default"] = "<expr>"
            elif kw.arg == "action":
                spec["action"] = getattr(kw.value, "value", None) or "<expr>"
            elif kw.arg == "choices":
                try:
                    spec["choices"] = ast.literal_eval(kw.value)
                except (ValueError, SyntaxError):
                    pass
        found[flags[0]] = spec
    return found


def check_schema_drift(repo: Path) -> list[str]:
    """Compare our mirrored option table against the driver's real argparse.

    Returns human-readable problems. This is the check that makes a two-repo
    split safe: if someone adds or renames a driver flag, the UI finds out at
    startup instead of building a command the driver rejects.
    """
    from driver_schema import FIELDS  # local import; keeps this module standalone

    problems: list[str] = []
    try:
        actual = driver_arguments(repo)
    except OSError as exc:
        return [f"Could not read {DRIVER_NAME}: {exc}"]
    if not actual:
        return [f"No arguments parsed from {DRIVER_NAME} — check the file is intact"]

    ours = {spec["flag"]: spec for spec in FIELDS.values()}

    for flag in sorted(set(ours) - set(actual)):
        problems.append(f"{flag}: in the UI but not in {DRIVER_NAME} (removed or renamed upstream)")
    for flag in sorted(set(actual) - set(ours)):
        problems.append(f"{flag}: new driver option not exposed in the UI")

    for flag in sorted(set(ours) & set(actual)):
        want, got = ours[flag], actual[flag]
        # Only compare where the driver states an explicit default; store_true
        # flags default to False on both sides by definition.
        if got.get("action") in (None, "store", "append"):
            # A UI default of None means "emit nothing", so the driver applies
            # its own default and the config chain is preserved — that is the
            # desired state, not drift. Only a concrete UI default that differs
            # is a problem, because that value would be sent on every run and
            # would suppress mea_config.json.
            ours_default = want.get("default")
            if (ours_default is not None and got.get("default") != "<expr>"
                    and ours_default != got.get("default")):
                problems.append(
                    f"{flag}: UI always sends {ours_default!r} but the driver defaults to "
                    f"{got.get('default')!r} — this would override mea_config.json")
        if got.get("choices") and want.get("choices") and \
                sorted(map(str, got["choices"])) != sorted(map(str, want["choices"])):
            problems.append(f"{flag}: choices differ — driver {got['choices']}, UI {want['choices']}")

    return problems


def report(repo: Optional[Path], strict: bool = False) -> None:
    """Log the linked repo and any contract drift. Raises if strict and broken."""
    if repo is None:
        msg = ("MEA-Analysis checkout not found. Set MEA_REPO, pass --mea-repo, "
               "or place this repo beside MEA-Analysis.")
        if strict:
            raise SystemExit(msg)
        LOG.error(msg)
        return

    info = describe(repo)
    LOG.info("MEA-Analysis: %s%s", info["path"],
             f" ({info.get('branch','?')} @ {info.get('commit','?')})" if info.get("commit") else "")

    drift = check_schema_drift(repo)
    if not drift:
        LOG.info("Driver option contract: OK")
        return
    LOG.warning("Driver option contract: %d difference(s) vs %s", len(drift), DRIVER_NAME)
    for d in drift:
        LOG.warning("  %s", d)
    if strict:
        raise SystemExit("Refusing to start with driver option drift (--strict).")
