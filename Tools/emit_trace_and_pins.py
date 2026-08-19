"""Emit the trace artifact + digest pins + 0.1% metrics.

Builds three artifacts under the same evidence discipline as every lane:

1. `melodia.trace.v1` — JSONL chain: every claim/run/gate row -> evidence
   file -> sha256 -> status. A claim without a file sha is listed, not
   believed.
2. `digest_pins.v1.json` — sha256 pins of every spec + evidence input, plus
   the ollama model digests, so any published score can be re-derived.
3. `melodia.metrics.v1` — derived numbers only: task_success_rate,
   recovery-under-failure, cost-per-task (raw tokens, no fake economics).

Run:
    python Tools/emit_trace_and_pins.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
LEDGER = ROOT / "Saved" / "gate_ledger.json"
WORKSPACE = Path(r"C:\EnvironmentPortfolio")
STATUS = WORKSPACE / "generated" / "melodia" / "status"
SITE = WORKSPACE / "my-site-clean"

SPEC_FILES = [
    "specs/mcp/math_tasks.v1.json",
    "specs/mcp/qsharp_tasks.v1.json",
    "specs/mcp/guardrails_policy.v1.json",
]
RUN_GLOB = "math_run_*.json"
OLLAMA = "http://127.0.0.1:11434"


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _ollama_digests() -> dict[str, str]:
    try:
        raw = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read().decode()
        data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return {}
    return {
        str(m.get("name") or ""): str(m.get("digest") or "")
        for m in data.get("models") or []
    }


def _latest_run(path: Path, kind: str | None = None) -> dict | None:
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(body, dict) and (kind is None or body.get("kind") == kind):
        return body
    return None


def _trace_events() -> list[dict]:
    events: list[dict] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if LEDGER.is_file():
        try:
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ledger = {}
        gates = ledger.get("gates") or []
        by_id: dict[str, dict] = {}
        for row in gates:
            by_id[row.get("id")] = row  # last row per id wins (ledger order)
        for gid, row in by_id.items():
            events.append({
                "event": "gate",
                "id": gid,
                "status": row.get("status"),
                "date": row.get("date"),
                "session": row.get("session"),
                "note": row.get("note"),
                "source": "Saved/gate_ledger.json",
                "pinned_at": now,
            })

    for path in sorted(AUDIT.glob(RUN_GLOB)):
        if path.name == "math_run_models_latest.json":
            continue
        body = _latest_run(path)
        if not isinstance(body, dict):
            continue
        events.append({
            "event": "run",
            "id": body.get("kind"),
            "model": body.get("model"),
            "file": path.name,
            "sha256": _sha256(path),
            "passed": body.get("passed"),
            "total": body.get("total"),
            "status": body.get("status", "completed" if body.get("passed") is not None else "unknown"),
            "captured_at": body.get("captured_at"),
            "pinned_at": now,
        })

    guardrails = _latest_run(AUDIT / "guardrails_2026-08-19.json")
    if guardrails:
        events.append({
            "event": "lane",
            "id": "guardrails",
            "file": "guardrails_2026-08-19.json",
            "sha256": _sha256(AUDIT / "guardrails_2026-08-19.json"),
            "stats": guardrails.get("stats"),
            "nemo": (guardrails.get("nemo") or {}).get("status"),
            "pinned_at": now,
        })
    return events


def _metrics(events: list[dict]) -> dict:
    # task_success_rate is the canonical tool-surface eval only (math_run_latest),
    # never an aggregate that would blend pre-fix and post-fix runs of the same day.
    latest_eval = _latest_run(AUDIT / "math_run_latest.json")
    task_success_rate = None
    if isinstance(latest_eval, dict) and isinstance(latest_eval.get("total"), int):
        total = int(latest_eval["total"])
        if total > 0:
            task_success_rate = round(float(latest_eval.get("passed") or 0) / total * 100.0, 1)

    recovery = None
    guardrails = [e for e in events if e["event"] == "lane" and e["id"] == "guardrails"]
    if guardrails:
        stats = guardrails[0].get("stats") or {}
        benign = stats.get("passed", 0) or 0
        if benign:
            recovery = round((stats.get("recovery", 0) or 0) / benign * 100.0, 1)

    tokens_constrained = None
    tokens_unconstrained = None
    bundle = _latest_run(AUDIT / "math_run_models_latest.json")
    if isinstance(bundle, dict):
        for r in bundle.get("runs") or []:
            if isinstance(r, dict):
                tokens_constrained = r.get("tokens_constrained") or tokens_constrained
                tokens_unconstrained = r.get("tokens_unconstrained") or tokens_unconstrained

    return {
        "task_success_rate_pct": task_success_rate,
        "recovery_under_failure_pct": recovery,
        "tokens_constrained": tokens_constrained,
        "tokens_unconstrained": tokens_unconstrained,
        "note": "derived from run JSONs only; tokens are raw counts, not economics",
    }


def _write(text: str, relative: Path) -> Path:
    target = STATUS / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    events = _trace_events()
    metrics = _metrics(events)

    pins: dict[str, Any] = {
        "schema": "melodia.digest_pins.v1",
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "specs": {},
        "evidence": {},
        "models": {},
    }
    for rel in SPEC_FILES:
        p = ROOT / rel
        pins["specs"][rel] = _sha256(p) if p.is_file() else None
    for ev in events:
        if ev["event"] == "run" and ev.get("file"):
            p = AUDIT / ev["file"]
            if p.is_file():
                pins["evidence"][ev["file"]] = _sha256(p)
    for name, digest in sorted(_ollama_digests().items()):
        if digest:
            pins["models"][name] = digest.split(":")[-1][:16]

    trace = {
        "schema": "melodia.trace.v1",
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(events),
        "events": events,
    }
    stamp = datetime.now().strftime("%Y-%m-%d")
    trace_path = AUDIT / f"melodia_trace_{stamp}.json"
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8")
    pins_path = ROOT / "specs" / "mcp" / "digest_pins.v1.json"
    pins_path.write_text(json.dumps(pins, indent=2, sort_keys=True), encoding="utf-8")

    written = [
        _write(json.dumps(trace, indent=2), f"melodia_trace_{stamp}.json"),
        _write(json.dumps(metrics, indent=2, sort_keys=True), f"melodia_metrics_{stamp}.json"),
    ]
    for p in written:
        print(f"  -> {p}")
    print(
        f"trace {len(events)} events -> {trace_path.name}\n"
        f"pins: {len(pins['specs'])} specs, {len(pins['evidence'])} evidence, {len(pins['models'])} models -> {pins_path.name}\n"
        f"metrics: success_rate={metrics['task_success_rate_pct']}%  recovery={metrics['recovery_under_failure_pct']}%  "
        f"tokens={metrics['tokens_constrained']}/{metrics['tokens_unconstrained']}"
    )
    if args.json:
        print(json.dumps(trace, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())