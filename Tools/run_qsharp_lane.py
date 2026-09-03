"""Q# (QDK) lane for the MATH harness.

Scores the deterministic quantum-contract task spec
`specs/mcp/qsharp_tasks.v1.json` against the existing rank_layouts service
(`Content/Python/quantum/draw_providers.rank_and_draw`) in-process, then
writes a run JSON under the same evidence discipline as every other lane:
no run JSON, no score.

Honest caveats enforced by the tasks themselves:
- the Q# kernel is a 2-candidate amplitude measurement (single Y-rotation
  + one measurement); N>2 candidates must fall back to classical-baseline;
- any provider failure degrades to classical-baseline and the response
  `backend` field reports what actually ran.

Run:
    python Tools/run_qsharp_lane.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUANTUM_DIR = ROOT / "Content" / "Python" / "quantum"
TASKS_SPEC = ROOT / "specs" / "mcp" / "qsharp_tasks.v1.json"
AUDIT = ROOT / "Saved" / "Audit"

SCHEMA = "melodia.math_run.v1"


def _load_spec() -> dict:
    return json.loads(TASKS_SPEC.read_text(encoding="utf-8"))


def _check(result: dict, task: dict) -> tuple[bool, str]:
    """Same structural check as the model lanes, plus callable expect/check."""
    expect = task.get("expect") or {}
    for key, want in expect.items():
        if callable(want):
            ok, detail = want(result)
            if not ok:
                return False, detail
            continue
        got = result.get(key)
        if got != want:
            return False, f"{key}: got {got!r} want {want!r}"
    for key in task.get("expect_keys") or []:
        if key not in result:
            return False, f"missing key: {key}"
    return True, "ok"


def _run_task(task: dict, rank_and_draw) -> tuple[dict, str]:
    """Execute one deterministic task; return (check_result, output_tail)."""
    backend = task["backend"]
    seed = task.get("seed", 1)
    candidates = task["candidates"]
    if task.get("expect_error"):
        try:
            rank_and_draw(seed, candidates, backend)
        except Exception as exc:
            return {"error": str(exc)}, f"raised as expected: {exc}"
        return {}, "no error raised"
    return rank_and_draw(seed, candidates, backend), ""


def _update_latest_bundle(run: dict) -> None:
    """Append a full run record to math_run_models_latest.json (list shape)."""
    latest = AUDIT / "math_run_models_latest.json"
    bundle: dict = {"schema": SCHEMA, "kind": "model_runs_index", "runs": []}
    if latest.is_file():
        try:
            old = json.loads(latest.read_text(encoding="utf-8"))
            if isinstance(old.get("runs"), list):
                bundle["runs"] = old["runs"]
        except json.JSONDecodeError:
            pass
    model = run.get("model")
    bundle["runs"] = [r for r in bundle["runs"] if r.get("model") != model]
    bundle["runs"].append(run)
    latest.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")


def _build_callables(spec: dict) -> dict:
    """Compile expect/check entries in the spec into callables for _check."""

    def verify_commitment(result: dict):
        c, n = result.get("commitment"), result.get("nonce")
        w = result.get("winner_id")
        if not c or not n or not w:
            return False, "commit-reveal fields missing"
        if hashlib.sha256(f"{w}:{n}".encode()).hexdigest() != c:
            return False, "sha256(winner:nonce) != commitment"
        return True, "commitment verified"

    def score_in_unit_interval(result: dict):
        s = result.get("score")
        if not isinstance(s, (int, float)):
            return False, f"score not numeric: {s!r}"
        if not (0.0 <= s <= 1.0):
            return False, f"score out of [0,1]: {s}"
        return True, "score in [0,1]"

    return {
        "verify_commitment": verify_commitment,
        "score_in_unit_interval": score_in_unit_interval,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable run JSON")
    args = parser.parse_args(argv)

    AUDIT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(QUANTUM_DIR.parent))  # Content/Python -> quantum package

    try:
        from quantum.draw_providers import rank_and_draw
    except ImportError as exc:
        held = {
            "schema": SCHEMA,
            "kind": "model_via_qsharp",
            "model": "qsharp-simulator",
            "backend": "qsharp",
            "status": "held",
            "reason": f"quantum lane unavailable: {exc}",
            "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        out = AUDIT / f"qsharp_lane_held_{datetime.now().strftime('%Y-%m-%d')}.json"
        out.write_text(json.dumps(held, indent=2, sort_keys=True), encoding="utf-8")
        print(f"held: {held['reason']} -> {out.name}")
        return 0

    spec = _load_spec()
    tasks = spec["tasks"]
    callables = _build_callables(spec)
    rows = []
    passed = 0
    for task in tasks:
        result, _tail = _run_task(task, rank_and_draw)
        ok, detail = False, "unparsed"
        expect = task.get("expect") or {}
        if result:
            ok, detail = True, "ok"
            task_check = task.get("check")
            if task_check and isinstance(task_check, str) and task_check in callables:
                ok2, det2 = callables[task_check](result)
                if not ok2:
                    ok, detail = False, det2
            if ok:
                for key, want in expect.items():
                    if callable(want):
                        ok2, det2 = want(result)
                        if not ok2:
                            ok, detail = False, det2
                            break
                    elif isinstance(want, str) and want in callables:
                        ok2, det2 = callables[want](result)
                        if not ok2:
                            ok, detail = False, det2
                            break
                    elif result.get(key) != want:
                        ok, detail = False, f"{key}: got {result.get(key)!r} want {want!r}"
                        break
            if ok:
                for key in task.get("expect_keys") or []:
                    if key not in result:
                        ok, detail = False, f"missing key: {key}"
                        break
        if ok:
            passed += 1
        rows.append({
            "id": task["id"],
            "pass": bool(ok),
            "status": "pass" if ok else "fail",
            "detail": detail,
            "output": json.dumps(result)[:600] if result else "",
        })
        print(f"  {task['id']}: {detail}", flush=True)

    run = {
        "schema": SCHEMA,
        "kind": "model_via_qsharp",
        "model": "qsharp-simulator + classical-baseline",
        "backend": "qsharp",
        "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "passed": passed,
        "total": len(tasks),
        "failed": len(tasks) - passed,
        "TCA": round(passed / len(tasks) * 100.0, 1) if tasks else 0.0,
        "tasks": rows,
    }
    date = datetime.now().strftime("%Y-%m-%d")
    out = AUDIT / f"math_run_qsharp_{date}.json"
    out.write_text(json.dumps(run, indent=2, sort_keys=True), encoding="utf-8")
    _update_latest_bundle(run)
    print(f"lane complete: {run['passed']}/{run['total']} -> {out.name}")
    if args.json:
        print(json.dumps(run, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
