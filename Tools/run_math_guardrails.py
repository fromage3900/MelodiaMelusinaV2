#!/usr/bin/env python3
"""Guardrailed agentic-workflow benchmark on the MATH (Melodia) task set.

Extends run_math_models.py with a NeMo Guardrails / policy validation layer.
Every model-chosen tool call is intercepted BEFORE execution by a guardrail
gate (default-deny policy, optional NeMo Guardrails IORails tool-call
validation). Denied calls are counted (blocked-call rate), the denial reason
is fed back to the model, and the agent may retry within a retry budget
(agent-recovery rate). A call only reaches the engine when the gate allows it.

    python Tools/run_math_guardrails.py --model nemotron-3-nano:4b
    python Tools/run_math_guardrails.py --model nemotron-3-nano:30b --cpu
    python Tools/run_math_guardrails.py --model qwen2.5-coder:7b --guardrails nemo
    python Tools/run_math_guardrails.py --model nvidia/nemotron-3-ultra-550b-a55b:free --backend openrouter

Metrics (extends the five-suite):
  TCA   tool-call accuracy
  ARG   argument equality
  EXEC  execution/state check pass
  PAR   policy-adherence rate (authorized calls / all attempted calls)
  BLK   blocked-call rate (1 - PAR)
  REC   agent recovery rate (blocked calls that converged to a legal, exec-valid
        call within the retry budget)
  TER   token-efficiency ratio (constrained vs unconstrained)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
AUDIT = ROOT / "Saved" / "Audit"
STATUS = Path(r"C:\EnvironmentPortfolio\generated\melodia\status")

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_math_models import (  # noqa: E402
    _chat_ollama,
    _chat_openrouter,
    _monolith_live,
    _parse_call,
    _tool_catalog,
)
from run_math_eval import _check  # noqa: E402
from guardrail_gate import guard  # noqa: E402

TASKS = ROOT / "specs" / "mcp" / "math_tasks.v1.json"
PROMPTS = ROOT / "specs" / "mcp" / "math_model_tasks.v1.json"
OLLAMA = "http://127.0.0.1:11434"

SYSTEM = (
    "You are calling the Melodia Hermes MCP harness. Reply with ONLY a JSON object: "
    '{"tool": "<registered_tool_name>", "args": {}}. No markdown.'
)

UNCONSTRAINED_SYSTEM = (
    "You are a Melodia game integration assistant. Answer with a JSON object describing "
    "which API operation to call and its arguments. No markdown."
)

_RETRY_MSG = (
    "\n\nYour previous tool call was REJECTED by the guardrail layer:\n{reason}\n\n"
    "Reply again with a legal registered tool and schema-conforming arguments. "
    'Only a JSON object: {{"tool": "...", "args": {{}}}}.'
)


def _make_caller(model: str, backend: str, timeout: float, cpu: bool):
    if backend == "openrouter":
        def call(user: str, system: str | None = None):
            text, err, _used, pt, ct = _chat_openrouter(model, user, timeout, system=system)
            return text, err or None, pt, ct
    else:
        def call(user: str, system: str | None = None):
            return _chat_ollama(model, user, timeout, system=system)
    return call


def run_guardrailed(
    model: str,
    timeout: float,
    *,
    backend: str = "ollama",
    guardrails_mode: str = "policy",
    retries: int = 2,
    measure_ter: bool = True,
    cpu: bool = False,
    limit: int = 0,
) -> dict[str, Any]:
    import deploy.melodia_mcp_server as server

    editor_live = _monolith_live()
    call = _make_caller(model, backend, timeout, cpu)
    backend_note = f"{backend} ({model})" + (" cpu" if cpu else "")

    gold = json.loads(TASKS.read_text(encoding="utf-8"))
    prompt_spec = json.loads(PROMPTS.read_text(encoding="utf-8")) if PROMPTS.exists() else {"prompts": {}}
    catalog = _tool_catalog()

    rows: list[dict[str, Any]] = []
    tool_hits = arg_hits = exec_hits = held = 0
    blocked_calls = 0
    blocked_tasks = 0
    recovered_tasks = 0
    recovered_calls = 0
    attempted_calls = 0
    authorized_calls = 0
    tokens_unconstrained = 0
    tokens_constrained = 0
    ter_samples = 0

    for i, task in enumerate(gold["tasks"]):
        if limit and i >= limit:
            break
        if task.get("editor_required") and not editor_live:
            held += 1
            rows.append({
                "id": task["id"], "gold_tool": task["tool"], "chosen_tool": None,
                "tool_match": False, "args_match": False, "exec_ok": False,
                "status": "hold", "detail": "editor_required - Monolith unreachable on :9316",
                "guardrail_verdicts": [], "attempts": 1, "blocked": False,
            })
            continue

        prompt = (prompt_spec.get("prompts") or {}).get(task["id"], task["id"])
        user_constrained = f"Registered tools:\n{catalog}\n\nTask: {prompt}"
        text, err, pt_c, ct_c = call(user_constrained)
        tokens_constrained += pt_c + ct_c

        if measure_ter:
            user_unconstrained = (
                f"Task: {prompt}\n\n"
                "Describe the full Melodia integration operation needed, including all parameters, "
                "without using a tool registry."
            )
            _u_text, _u_err, pt_u, ct_u = call(user_unconstrained, system=UNCONSTRAINED_SYSTEM)
            tokens_unconstrained += pt_u + ct_u
            ter_samples += 1

        parsed = _parse_call(text) if not err else None
        gold_tool, gold_args = task["tool"], task.get("args") or {}
        exec_ok = False
        detail = err or "unparsed"
        history = text or ""
        verdicts: list[dict[str, Any]] = []

        for attempt in range(retries + 1):
            parsed = _parse_call(history) if history else None
            if not parsed:
                if attempt == 0 and err:
                    break
                detail = "unparsed response"
                break
            attempted_calls += 1
            v = guard(str(parsed.get("tool") or ""), dict(parsed.get("args") or {}), guardrails_mode)
            verdicts.append(v)
            if not v.get("allowed"):
                blocked_calls += 1
                detail = f"blocked: {v.get('reason')}"
                if attempt < retries:
                    history = user_constrained + _RETRY_MSG.format(reason=v.get("reason", "denied"))
                    text, err, pt_r, ct_r = call(history)
                    tokens_constrained += pt_r + ct_r
                    history = text or ""
                    continue
                break
            authorized_calls += 1
            fn = getattr(server, str(parsed.get("tool") or ""), None)
            if fn is None:
                detail = f"unknown tool {parsed.get('tool')}"
                if attempt < retries:
                    history = user_constrained + _RETRY_MSG.format(
                        reason=f"tool '{parsed.get('tool')}' is not registered"
                    )
                    text, err, pt_r, ct_r = call(history)
                    tokens_constrained += pt_r + ct_r
                    history = text or ""
                    continue
                break
            try:
                result = fn(**(parsed.get("args") or {}))
                exec_ok, detail = _check(result, task) if isinstance(result, dict) else (False, "non-dict")
            except Exception as exc:
                detail = str(exc)
            break

        if attempted_calls and verdicts and any(v.get("allowed") for v in verdicts):
            recovered_calls += 1
        task_had_denial = any(not v.get("allowed") for v in verdicts)
        if task_had_denial:
            blocked_tasks += 1
        if task_had_denial and verdicts and verdicts[-1].get("allowed"):
            recovered_tasks += 1

        tool_ok = bool(parsed) and parsed.get("tool") == gold_tool
        arg_ok = bool(parsed) and dict(parsed.get("args") or {}) == dict(gold_args)
        if tool_ok:
            tool_hits += 1
        if arg_ok:
            arg_hits += 1
        if exec_ok:
            exec_hits += 1
        rows.append({
            "id": task["id"], "gold_tool": gold_tool,
            "chosen_tool": None if not parsed else parsed.get("tool"),
            "tool_match": tool_ok, "args_match": arg_ok, "exec_ok": exec_ok,
            "status": "pass" if exec_ok else "fail",
            "detail": detail[:240],
            "guardrail_verdicts": verdicts,
            "attempts": len(verdicts) or 1,
            "blocked": bool(verdicts) and not verdicts[-1].get("allowed") if verdicts else False,
        })
        print(
            f"  [{i+1}/{len(gold['tasks'])}] {task['id']}: "
            f"{'PASS' if exec_ok else 'BLOCKED' if detail.startswith('blocked') else 'FAIL'} "
            f"{detail[:120]}",
            flush=True,
        )

    n = len(rows)
    scored = n - held
    total_nominal = len(gold["tasks"])
    if limit:
        total_nominal = min(limit, total_nominal)
    ter_ratio = round(tokens_constrained / tokens_unconstrained, 4) if tokens_unconstrained > 0 else None
    par_pct = round(100.0 * authorized_calls / attempted_calls, 1) if attempted_calls else 0.0
    blocked_pct = round(100.0 * blocked_calls / attempted_calls, 1) if attempted_calls else 0.0
    rec_pct = round(100.0 * recovered_tasks / blocked_tasks, 1) if blocked_tasks else 100.0

    return {
        "schema": "melodia.math_run.v1",
        "kind": "guardrailed_agentic_workflow",
        "harness": "run_math_guardrails.py (MATH + guardrail gate)",
        "model": model,
        "backend": backend_note,
        "guardrails_mode": guardrails_mode,
        "retry_budget": retries,
        "note": "Every model tool call intercepted by the guardrail gate before execution. "
                "Blocked calls counted; denial reason fed back; agent may retry within budget.",
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "editor_contacted": editor_live,
        "passed": exec_hits,
        "total": n,
        "total_nominal": total_nominal,
        "scored": scored,
        "held": held,
        "failed": scored - exec_hits,
        "tca_pct": round(100.0 * tool_hits / scored, 1) if scored else 0.0,
        "arg_pct": round(100.0 * arg_hits / scored, 1) if scored else 0.0,
        "exec_pct": round(100.0 * exec_hits / scored, 1) if scored else 0.0,
        "par_pct": par_pct,
        "blocked_call_rate_pct": blocked_pct,
        "blocked_calls": blocked_calls,
        "attempted_calls": attempted_calls,
        "authorized_calls": authorized_calls,
        "recovery_pct": rec_pct,
        "recovered_tasks": recovered_tasks,
        "blocked_tasks": blocked_tasks,
        "recovered_calls": recovered_calls,
        "ter_ratio": ter_ratio,
        "ter_target": 0.20,
        "ter_meets_target": ter_ratio is not None and ter_ratio <= 0.20,
        "tokens_unconstrained": tokens_unconstrained,
        "tokens_constrained": tokens_constrained,
        "ter_samples": ter_samples,
        "tasks": rows,
    }


def _write(report: dict[str, Any]) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    slug = (report["model"].replace(":", "_").replace("/", "_"))
    path = AUDIT / f"math_guardrails_{slug}_{stamp}.json"
    text = json.dumps(report, indent=2)
    path.write_text(text, encoding="utf-8")
    latest = AUDIT / "math_guardrails_latest.json"
    if latest.exists():
        try:
            bundle = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bundle = {"schema": "melodia.math_guardrails.v1", "runs": []}
    else:
        bundle = {"schema": "melodia.math_guardrails.v1", "runs": []}
    runs = [r for r in bundle.get("runs") or []
            if (r.get("model"), r.get("guardrails_mode")) != (report.get("model"), report.get("guardrails_mode"))]
    runs.append(report)
    bundle["runs"] = runs
    bundle["updated_at"] = report["captured_at"]
    latest.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    if STATUS.is_dir():
        (STATUS / "math_guardrails_latest.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        (STATUS / path.name).write_text(text, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="nemotron-3-nano:4b")
    parser.add_argument("--backend", choices=("ollama", "openrouter", "auto"), default="ollama")
    parser.add_argument("--guardrails", choices=("policy", "nemo"), default="policy",
                        help="policy = default-deny mcp_policy gate; nemo = + NeMo Guardrails IORails")
    parser.add_argument("--retries", type=int, default=2, help="agent recovery retry budget")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--no-ter", action="store_true")
    parser.add_argument("--cpu", action="store_true", help="force CPU-only inference")
    parser.add_argument("--limit", type=int, default=0, help="run only the first N tasks (smoke test)")
    args = parser.parse_args(argv)

    backend = args.backend
    if backend == "auto":
        backend = "openrouter" if args.model.startswith(("meta/", "nvidia/")) else "ollama"

    report = run_guardrailed(
        args.model, args.timeout, backend=backend, guardrails_mode=args.guardrails,
        retries=args.retries, measure_ter=not args.no_ter, cpu=args.cpu,
        limit=args.limit,
    )
    path = _write(report)
    print(
        f"{args.model} [{args.guardrails}]: TCA={report['tca_pct']}% ARG={report['arg_pct']}% "
        f"EXEC={report['exec_pct']}% PAR={report['par_pct']}% BLOCKED={report['blocked_call_rate_pct']}% "
        f"RECOVERY={report['recovery_pct']}% ({path.name})"
    )
    for row in report["tasks"]:
        mark = "PASS" if row["exec_ok"] else "BLK" if row["blocked"] else "FAIL"
        print(f"  {mark}  {row['id']}  tool={row.get('chosen_tool')}  {row['detail'][:80]}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())