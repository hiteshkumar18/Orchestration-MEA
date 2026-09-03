#!/usr/bin/env python3
"""
Write the report's prose with Claude, from numbers computed here.

Division of labour
------------------
**Code computes, the model describes.** Every number — group means, effect
sizes, outliers, counts — is calculated in ``build_brief`` and handed to the
model as a briefing. The model returns only prose, in a fixed schema, and every
numeral it writes is checked back against the briefing before the report is
allowed to use it.

That split is what makes this safe to put in front of a PI: the model cannot
invent a statistic, because it is never asked to produce one.

Guardrails
----------
* **The schema has no ``recommendations`` field.** "Describe and flag, don't
  recommend" is enforced structurally rather than by instruction.
* **Number validation** — every numeral in the returned text must match a value
  in the briefing (within rounding tolerance) or the narrative is rejected.
* **Citation validation** — every well and metric a finding cites must exist.
* ``temperature=0`` where the SDK still accepts it (dropped in anthropic 1.x),
  so re-running the same briefing gives near-identical prose. This is a
  convenience, not a safety property — ``validate`` is what makes the output
  trustworthy.
* The prompt states n per group and forbids significance language below n=3.
* The briefing and the raw response are written next to the report.

The API key is read from ``ANTHROPIC_API_KEY`` in the environment. It is never
stored, logged, or accepted over HTTP.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_data import PRETTY, Well, group_wells, summarise  # noqa: E402

LOG = logging.getLogger("mea.narrate")

DEFAULT_MODEL = "claude-sonnet-5"
MAX_TOKENS = 2000

# Below this many wells in a group, a difference is described but never tested.
MIN_N_FOR_TEST = 3
OUTLIER_Z = 2.0


# --------------------------------------------------------------------------- #
# The briefing — everything the model is allowed to know
# --------------------------------------------------------------------------- #
def _stats(values: list[float]) -> dict[str, float]:
    out = {"n": len(values), "mean": round(statistics.fmean(values), 4),
           "min": round(min(values), 4), "max": round(max(values), 4)}
    if len(values) > 1:
        out["sd"] = round(statistics.stdev(values), 4)
    return out


def _cohens_d(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None
    sa, sb = statistics.stdev(a), statistics.stdev(b)
    pooled = (((len(a) - 1) * sa ** 2 + (len(b) - 1) * sb ** 2) /
              (len(a) + len(b) - 2)) ** 0.5
    if pooled == 0:
        return None
    return round((statistics.fmean(a) - statistics.fmean(b)) / pooled, 3)


def build_brief(wells: list[Well], kind: str, metrics: list[str],
                time_kind: str = "none") -> dict[str, Any]:
    """Everything the model needs, with the analysis already done.

    The model's job is to say what this means in prose — not to compute it, and
    not to see anything that isn't here.
    """
    s = summarise(wells)
    groups = {g: ws for g, ws in group_wells(wells).items() if g != "ungrouped"}

    brief: dict[str, Any] = {
        "report_type": kind,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": {
            "chips": s["chips"],
            "runs": s["runs"],
            "wells_total": s["wells"],
            "wells_complete": s["status"].get("complete", 0),
            "wells_failed": s["status"].get("failed", 0),
        },
        "units": {
            "total": s["total_units"],
            "mean_per_well": round(s["total_units"] / max(s["wells"], 1), 1),
        },
        "metric_labels": {m: PRETTY.get(m, m) for m in metrics},
        # Cohort-wide statistics, across every well regardless of group. These
        # are the figures the report's own headline tiles show, so without them
        # the model is barred from describing its own first slide.
        "overall": {},
        "per_well": [],
        "groups": [],
        "comparisons": [],
        "outliers": [],
        "failures": [],
        "rejections": {},
        "constraints": [],
    }

    for w in sorted(wells, key=lambda x: (x.run_id, x.well)):
        row = {"well": w.well, "group": w.group or None, "status": w.status}
        if w.run_id:
            row["run"] = w.run_id
        if w.div is not None:
            row["timepoint"] = w.div
        for m in metrics:
            v = w.get(m)
            if v is not None:
                row[m] = round(v, 4)
        brief["per_well"].append(row)

    for m in metrics:
        vals = [w.get(m) for w in wells if w.get(m) is not None]
        if vals:
            brief["overall"][m] = _stats(vals)

    for name, ws in sorted(groups.items()):
        entry: dict[str, Any] = {"name": name, "n_wells": len(ws),
                                 "wells": [w.well for w in ws], "metrics": {}}
        for m in metrics:
            vals = [w.get(m) for w in ws if w.get(m) is not None]
            if vals:
                entry["metrics"][m] = _stats(vals)
        brief["groups"].append(entry)

    # Pairwise comparisons, with the honest note attached to each.
    names = sorted(groups)
    if len(names) >= 2:
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                ga, gb = names[i], names[j]
                for m in metrics:
                    va = [w.get(m) for w in groups[ga] if w.get(m) is not None]
                    vb = [w.get(m) for w in groups[gb] if w.get(m) is not None]
                    if not va or not vb:
                        continue
                    ma, mb = statistics.fmean(va), statistics.fmean(vb)
                    comp = {
                        "metric": m, "groups": [ga, gb],
                        "means": [round(ma, 4), round(mb, 4)],
                        "n": [len(va), len(vb)],
                        "difference": round(ma - mb, 4),
                        "ratio": round(ma / mb, 3) if mb else None,
                        "cohens_d": _cohens_d(va, vb),
                    }
                    if min(len(va), len(vb)) < MIN_N_FOR_TEST:
                        comp["test"] = None
                        comp["note"] = (
                            f"n={min(len(va), len(vb))} in the smaller group; no statistical "
                            "test performed and none should be implied")
                    else:
                        comp["test"] = None
                        comp["note"] = "descriptive only; no test performed"
                    brief["comparisons"].append(comp)

    # Outliers, computed here so the model never has to judge "unusual".
    for m in metrics:
        vals = [(w, w.get(m)) for w in wells if w.get(m) is not None]
        if len(vals) < 4:
            continue
        xs = [v for _, v in vals]
        mu = statistics.fmean(xs)
        sd = statistics.stdev(xs) if len(xs) > 1 else 0
        if sd <= 0:
            continue
        for w, v in vals:
            z = (v - mu) / sd
            if abs(z) >= OUTLIER_Z:
                brief["outliers"].append({
                    "well": w.well, "group": w.group or None, "metric": m,
                    "value": round(v, 4), "cohort_mean": round(mu, 4),
                    "z": round(z, 2),
                })

    for w in wells:
        if w.status == "failed" or w.error:
            brief["failures"].append({
                "well": w.well, "group": w.group or None,
                "error": (w.error or "failed")[:300],
            })
        for reason, n in w.rejection_reasons.items():
            brief["rejections"][reason] = brief["rejections"].get(reason, 0) + n

    # Longitudinal view when there is more than one timepoint.
    tps = sorted({w.div for w in wells if w.div is not None})
    if len(tps) > 1:
        brief["timepoints"] = {
            "kind": time_kind,
            "values": tps,
            "note": ("true DIV" if time_kind == "div"
                     else f"{time_kind} order, not days in vitro"),
            "by_group": [
                {"group": g,
                 "series": [
                     {"timepoint": t,
                      "metrics": {m: round(statistics.fmean(v), 4)
                                  for m in metrics
                                  if (v := [w.get(m) for w in ws
                                            if w.div == t and w.get(m) is not None])}}
                     for t in tps]}
                for g, ws in sorted(groups.items())
            ],
        }

    # Stated plainly so the model does not have to infer them.
    c = brief["constraints"]
    c.append("Metrics are per-well means over sorted units, not per-neuron values.")
    if any(g["n_wells"] < MIN_N_FOR_TEST for g in brief["groups"]):
        small = [g["name"] for g in brief["groups"] if g["n_wells"] < MIN_N_FOR_TEST]
        c.append(f"Groups with fewer than {MIN_N_FOR_TEST} wells ({', '.join(small)}) "
                 "cannot support a statistical claim. Describe differences, do not "
                 "call them significant.")
    if brief["scope"]["wells_failed"]:
        c.append(f"{brief['scope']['wells_failed']} well(s) failed and are excluded "
                 "from group means.")
    if len(brief["scope"]["runs"]) > 1 and kind == "run":
        c.append(f"This covers {len(brief['scope']['runs'])} runs, not a single session.")
    if not brief["groups"]:
        c.append("No group labels are available, so no condition comparison is possible.")
    return brief


# --------------------------------------------------------------------------- #
# Schema — note the absence of a recommendations field
# --------------------------------------------------------------------------- #
SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["headline", "findings", "caveats"],
    "additionalProperties": False,
    "properties": {
        "headline": {
            "type": "string",
            "description": "One or two sentences stating what this run shows. "
                           "Readable on its own by someone who sees nothing else.",
        },
        "findings": {
            "type": "array", "minItems": 2, "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["title", "text", "metrics_cited", "wells_cited"],
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string", "description": "Short label, under 8 words."},
                    "text": {"type": "string",
                             "description": "2-4 sentences. State the numbers and why they "
                                            "matter. No recommendations, no biological "
                                            "interpretation."},
                    "metrics_cited": {"type": "array", "items": {"type": "string"},
                                      "description": "Canonical metric keys referenced."},
                    "wells_cited": {"type": "array", "items": {"type": "string"},
                                    "description": "Well ids referenced; empty if none."},
                },
            },
        },
        "caveats": {
            "type": "array", "minItems": 1, "maxItems": 6,
            "items": {"type": "string"},
            "description": "What these data cannot support. Include every applicable "
                           "constraint from the briefing.",
        },
        "qc_notes": {
            "type": "array", "maxItems": 10,
            "items": {
                "type": "object",
                "required": ["well", "note"],
                "additionalProperties": False,
                "properties": {"well": {"type": "string"}, "note": {"type": "string"}},
            },
            "description": "Only for wells that failed or are flagged. Omit if none.",
        },
        "additional": {
            "type": ["object", "null"],
            "required": ["title", "text"],
            "additionalProperties": False,
            "properties": {"title": {"type": "string"}, "text": {"type": "string"}},
            "description": "Optional extra section, only when something in the data does "
                           "not fit the sections above. Null on a routine run.",
        },
    },
}

SYSTEM_PROMPT = """\
You write the narrative sections of an automated report on multi-electrode array
(MEA) recordings of cultured neurons, for a neuroscience lab.

WHAT THE DATA IS
Neurons are grown over a grid of electrodes in independent wells. A recording is
spike-sorted into putative single units. Per well you are given the number of
units and per-well means of unit metrics (firing rate in Hz, spike amplitude in
microvolts, presence ratio, ISI-violation rate), plus network burst statistics
(burst rate, duration, spikes per burst, percentage of spikes inside bursts,
interburst interval) and, where available, whole-array activity-scan measures.
Wells may carry an experimental group label such as a genotype.

Typical healthy cultures give order 10-100 units per well and mean firing rates
of roughly 0.5-10 Hz; values far outside that are worth remarking on. Units
rejected by curation are reported separately and are not a fault by themselves.

YOUR JOB
Describe what the numbers show, and flag anything anomalous. Lead with the
takeaway. The audience is the lab: people who know MEA work, plus a supervisor
who wants the point first and the detail second. Be specific and quantitative;
write plainly and without padding.

HARD RULES
1. Use ONLY numbers that appear in the briefing. Never compute, estimate,
   extrapolate or round to a value that is not given. If you want to state a
   quantity that is not in the briefing, do not state it.
2. Do not recommend actions, next steps, or experiments.
3. Do not offer biological or mechanistic interpretation. Report what was
   measured, not what it might mean.
4. Never describe a difference as significant, and never imply a statistical
   test was performed. No test was performed. Where the briefing gives an n
   below 3 for a group, say plainly that the group is too small to support a
   comparison.
5. Every finding must cite the metric keys and well ids it refers to, using the
   exact identifiers from the briefing.
6. Include every applicable item from the briefing's "constraints" list among
   your caveats, in your own words.
7. Use "additional" only when something genuinely does not fit the other
   sections. Return null for it otherwise. A routine run needs no extra section.

Return only the JSON object described by the schema."""


# --------------------------------------------------------------------------- #
# Validation — the model's output is not trusted until it passes
# --------------------------------------------------------------------------- #
_NUM = re.compile(r"(?<![\w/.-])(-?\d+(?:,\d{3})*(?:\.\d+)?)(?![\w/-])")


def _brief_numbers(obj: Any, out: Optional[set[float]] = None) -> set[float]:
    if out is None:
        out = set()
    if isinstance(obj, dict):
        for v in obj.values():
            _brief_numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _brief_numbers(v, out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out.add(float(obj))
    return out


def _decimals(token: str) -> int:
    return len(token.split(".")[1]) if "." in token else 0


def _matches(token: str, x: float, allowed: set[float]) -> bool:
    """Whether a written numeral is a faithful rendering of an allowed value.

    Compares at the precision the model actually wrote, rather than by numeric
    proximity. Proximity matching is far too weak here: a briefing holds
    hundreds of numbers over a wide range, so a tolerance band around any
    invented value almost always contains one by chance — an earlier version of
    this check accepted a fabricated "0.83 Hz difference" for that reason.
    """
    d = _decimals(token)
    for b in allowed:
        if round(b, d) == round(x, d):
            return True
        # a fraction stated as a percentage, or the reverse
        if round(b * 100, d) == round(x, d) or round(b / 100, d) == round(x, d):
            return True
    return False


# Quantities that are legitimately derivable from a briefed ratio.
def _derived_from_ratios(entries: list[dict]) -> set[float]:
    out: set[float] = set()
    for c in entries:
        r = c.get("ratio")
        if isinstance(r, (int, float)):
            out.add(float(r))
            out.add(round((r - 1) * 100, 4))     # "26% lower"
            out.add(round(abs(r - 1) * 100, 4))
            out.add(round(r * 100, 4))
    return out


def _numbers_by_metric(brief: dict) -> dict[str, set[float]]:
    """Values associated with each metric, so a claim can be checked in context.

    Without this a number can pass merely because it appears *somewhere* in the
    briefing — a presence-ratio value vouching for a firing-rate claim. Findings
    cite the metrics they discuss, so their numbers are checked against those.
    """
    by: dict[str, set[float]] = {}

    def add(metric: str, value: Any) -> None:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            by.setdefault(metric, set()).add(float(value))

    for m, st in (brief.get("overall") or {}).items():
        for v in st.values():
            add(m, v)
    for g in brief.get("groups", []):
        for m, st in (g.get("metrics") or {}).items():
            for v in st.values():
                add(m, v)
    for c in brief.get("comparisons", []):
        m = c.get("metric", "")
        for key in ("difference", "ratio"):
            add(m, c.get(key))
        for v in c.get("means") or []:
            add(m, v)
        for v in c.get("n") or []:
            add(m, v)
        if c.get("cohens_d") is not None:
            add(m, c["cohens_d"])
        by.setdefault(m, set()).update(_derived_from_ratios([c]))
    for o in brief.get("outliers", []):
        m = o.get("metric", "")
        for key in ("value", "cohort_mean", "z"):
            add(m, o.get(key))
    for row in brief.get("per_well", []):
        for m, v in row.items():
            if m not in ("well", "group", "status", "run"):
                add(m, v)
    for series in (brief.get("timepoints") or {}).get("by_group", []):
        for point in series.get("series", []):
            for m, v in (point.get("metrics") or {}).items():
                add(m, v)
    return by


def _global_numbers(brief: dict) -> set[float]:
    """Counts and identifiers any section may legitimately cite."""
    out: set[float] = set()
    out |= _brief_numbers(brief.get("scope", {}))
    out |= _brief_numbers(brief.get("units", {}))
    out |= _brief_numbers(brief.get("rejections", {}))
    for g in brief.get("groups", []):
        out.add(float(g.get("n_wells", 0)))
    for tp in (brief.get("timepoints") or {}).get("values", []):
        out.add(float(tp))
    out.add(float(MIN_N_FOR_TEST))
    return out


def validate(narrative: dict, brief: dict) -> list[str]:
    """Problems that should stop this narrative being used."""
    problems: list[str] = []
    all_nums = _brief_numbers(brief)
    by_metric = _numbers_by_metric(brief)
    globals_ = _global_numbers(brief)
    known_wells = {w["well"] for w in brief.get("per_well", [])}
    known_metrics = set(brief.get("metric_labels", {}))

    # (location, text, allowed numbers). A finding is checked against the
    # metrics it cites; sections that cannot be scoped fall back to everything.
    texts: list[tuple[str, str, set[float]]] = [
        ("headline", narrative.get("headline", ""), all_nums)]
    for i, f in enumerate(narrative.get("findings") or []):
        cited = [m for m in (f.get("metrics_cited") or []) if m in by_metric]
        scoped = set(globals_)
        for m in cited:
            scoped |= by_metric.get(m, set())
        # An uncited finding cannot be scoped, so it is held to everything.
        allowed = scoped if cited else all_nums
        texts.append((f"findings[{i}].text", f.get("text", ""), allowed))
        texts.append((f"findings[{i}].title", f.get("title", ""), allowed))
    for i, c in enumerate(narrative.get("caveats") or []):
        texts.append((f"caveats[{i}]", c, all_nums))
    for i, q in enumerate(narrative.get("qc_notes") or []):
        texts.append((f"qc_notes[{i}].note", q.get("note", ""), all_nums))
    if narrative.get("additional"):
        texts.append(("additional.text", narrative["additional"].get("text", ""), all_nums))

    for where, text, allowed in texts:
        for raw in _NUM.findall(text or ""):
            try:
                x = float(raw.replace(",", ""))
            except ValueError:
                continue
            if not _matches(raw.replace(",", ""), x, allowed):
                problems.append(
                    f"{where}: {raw} does not match any briefed value"
                    + (" for the cited metrics" if where.startswith("findings") else ""))

    for i, f in enumerate(narrative.get("findings") or []):
        for w in f.get("wells_cited") or []:
            if w not in known_wells:
                problems.append(f"findings[{i}]: cites unknown well {w!r}")
        for m in f.get("metrics_cited") or []:
            if m not in known_metrics:
                problems.append(f"findings[{i}]: cites unknown metric {m!r}")

    for i, q in enumerate(narrative.get("qc_notes") or []):
        if q.get("well") and q["well"] not in known_wells:
            problems.append(f"qc_notes[{i}]: unknown well {q['well']!r}")

    banned = ("significant", "significantly", "p <", "p<", "p =", "p=", "we recommend",
              "you should", "next step")
    joined = " ".join(t for _, t, _a in texts).lower()
    for phrase in banned:
        if phrase in joined:
            problems.append(f"uses forbidden phrasing: {phrase!r}")

    return problems


# --------------------------------------------------------------------------- #
# The call
# --------------------------------------------------------------------------- #
def api_key_present() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def status() -> dict[str, Any]:
    """What the UI needs to decide whether to offer AI narration."""
    try:
        import anthropic  # noqa: F401
        sdk = True
    except ImportError:
        sdk = False
    key = api_key_present()
    return {
        "key_present": key,
        "sdk_installed": sdk,
        "model": os.environ.get("MEA_AI_MODEL", DEFAULT_MODEL),
        "workspace_id_set": bool(os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()),
        "ready": key and sdk,
        "reason": (None if key and sdk else
                   "Set ANTHROPIC_API_KEY in the shell that starts the server"
                   if not key else
                   "The anthropic package is not installed (pip install anthropic)"),
    }


def narrate(brief: dict, model: str = "", max_retries: int = 1) -> dict[str, Any]:
    """Ask Claude for the narrative and validate it before returning.

    Raises RuntimeError with a readable message on any failure, so the caller
    can fall back to a report without narration rather than produce a bad one.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("The anthropic package is not installed "
                           "(pip install anthropic)") from exc
    if not api_key_present():
        raise RuntimeError("ANTHROPIC_API_KEY is not set in this process's environment")

    model = model or os.environ.get("MEA_AI_MODEL", DEFAULT_MODEL)

    # An identity-linked key scoped to the whole organization can act in more
    # than one workspace, and the API will not guess which. A key scoped to a
    # single workspace needs nothing extra, so this stays optional.
    workspace = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
    headers = {"anthropic-workspace-id": workspace} if workspace else None
    client = anthropic.Anthropic(default_headers=headers)

    tool = {
        "name": "report_sections",
        "description": "Return the narrative sections for this MEA report.",
        "input_schema": SCHEMA,
    }
    user = ("Here is the briefing for this report. Every number you write must come "
            "from it.\n\n<briefing>\n"
            + json.dumps(brief, indent=1, sort_keys=False)
            + "\n</briefing>")

    last_problems: list[str] = []
    for attempt in range(max_retries + 1):
        messages = [{"role": "user", "content": user}]
        if attempt and last_problems:
            messages.append({"role": "assistant", "content":
                             "I will correct the issues and return valid JSON."})
            messages.append({"role": "user", "content":
                             "The previous response was rejected:\n- "
                             + "\n- ".join(last_problems[:10])
                             + "\n\nReturn a corrected version. Use only numbers from "
                               "the briefing."})

        LOG.info("Requesting narrative from %s (attempt %d)", model, attempt + 1)
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=[tool],
                tool_choice={"type": "tool", "name": "report_sections"},
                messages=messages,
                **_sampling_kwargs(client),
            )
        except Exception as exc:                                  # noqa: BLE001
            # Surface the fix, not just the API's wording. These two arrive as
            # opaque 400s that send people to a search engine.
            raise RuntimeError(_explain(exc)) from exc

        block = next((b for b in resp.content if getattr(b, "type", "") == "tool_use"), None)
        if block is None:
            last_problems = ["model did not return the structured tool call"]
            continue

        narrative = dict(block.input)
        problems = validate(narrative, brief)
        usage = getattr(resp, "usage", None)
        narrative["_meta"] = {
            "model": model,
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "attempt": attempt + 1,
            "validation": "passed" if not problems else "passed after retry",
        }
        if not problems:
            LOG.info("Narrative accepted (%s in / %s out tokens)",
                     narrative["_meta"]["input_tokens"],
                     narrative["_meta"]["output_tokens"])
            return narrative

        LOG.warning("Narrative rejected: %s", "; ".join(problems[:5]))
        last_problems = problems

    raise RuntimeError("The narrative failed validation: " + "; ".join(last_problems[:5]))


def _explain(exc: Exception) -> str:
    """Turn the API errors people actually hit into instructions."""
    msg = str(exc)
    low = msg.lower()
    if "anthropic-workspace-id" in low or "workspace this request acts in" in low:
        return (
            "This API key is scoped to the whole organization, so the API needs "
            "to be told which workspace to act in. Either set the workspace id "
            "alongside the key and restart:\n"
            "    export ANTHROPIC_WORKSPACE_ID=wrkspc_...\n"
            "or create a key scoped to a single workspace, which needs nothing "
            f"extra.\n\nOriginal error: {msg}")
    if "authentication_error" in low or "invalid x-api-key" in low:
        return ("The API key was rejected. Check ANTHROPIC_API_KEY in the shell "
                f"that started the server.\n\nOriginal error: {msg}")
    if "credit balance" in low or "billing" in low:
        return ("The account has no available credit for the API. Reports still "
                f"build without the summary.\n\nOriginal error: {msg}")
    if "not_found_error" in low and "model" in low:
        return ("That model id is not available to this account. Override it "
                f"with MEA_AI_MODEL=<model-id>.\n\nOriginal error: {msg}")
    if "rate_limit" in low:
        return f"Rate limited by the API — try again shortly.\n\nOriginal error: {msg}"
    return msg


def _sampling_kwargs(client) -> dict:
    """`temperature=0` where the installed SDK still accepts it.

    Anthropic SDK 1.x dropped `temperature` from `messages.create()`, and
    passing it there raises TypeError. Older 0.x releases take it and it does
    make repeated runs on the same briefing more alike, so it is used when
    available rather than dropped outright. Determinism was never what makes
    the output trustworthy — `validate()` is — so its absence costs little.
    """
    try:
        params = inspect.signature(client.messages.create).parameters
    except (TypeError, ValueError, AttributeError):
        return {}
    return {"temperature": 0} if "temperature" in params else {}


def write_audit(dest_dir: Path, brief: Optional[dict], narrative: Optional[dict],
                error: Optional[str] = None) -> Path:
    """Record what was sent and what came back, beside the report.

    Takes the report *directory* and names the file itself: an earlier version
    took a full path, and a caller that passed the directory created it as a
    file, which then broke the report write that followed.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"narrative_audit_{stamp}.json"
    dest.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "system_prompt": SYSTEM_PROMPT,
        "brief": brief,
        "narrative": narrative,
        "error": error,
    }, indent=2))
    return dest
