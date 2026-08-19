#!/usr/bin/env python3
"""Run MATH tasks through a local Ollama or OpenRouter model against the Hermes MCP harness.

Hermes here is the agentic harness (deploy/hermes_mcp.py + melodia_mcp_server.py),
not a Nous Hermes weight. This script never pulls models.

    python Tools/run_math_models.py --model qwen2.5-coder:7b
    python Tools/run_math_models.py --run-muse
    python Tools/run_math_models.py --model meta/muse-spark-1.2 --backend openrouter
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
AUDIT = ROOT / "Saved" / "Audit"
TASKS = ROOT / "specs" / "mcp" / "math_tasks.v1.json"
PROMPTS = ROOT / "specs" / "mcp" / "math_model_tasks.v1.json"
STATUS = Path(r"C:\EnvironmentPortfolio\generated\melodia\status")
OLLAMA = "http://127.0.0.1:11434"
MUSE_OLLAMA = "muse-glimmer-30b"
MUSE_OPENROUTER = "meta/muse-spark-1.2"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SYSTEM = (
    "You are calling the Melodia Hermes MCP harness. Reply with ONLY a JSON object: "
    '{"tool": "<registered_tool_name>", "args": {}}. No markdown.'
)


def _ollama_tags() -> list[str]:
    try:
        raw = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read().decode()
        data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []
    return [str(m.get("name") or "") for m in data.get("models") or []]


def _resolve_muse_ollama() -> str | None:
    tags = _ollama_tags()
    for candidate in (MUSE_OLLAMA, f"{MUSE_OLLAMA}:latest"):
        if candidate in tags:
            return candidate
    for tag in tags:
        if "muse" in tag.lower() or "glimmer" in tag.lower():
            return tag
    return None


def _chat_ollama(model: str, user: str, timeout: float, system: str | None = None) -> tuple[str, str | None, int, int]:
    """Return (text, error, prompt_tokens, completion_tokens)."""
    payload = json.dumps(
        {
            "model": model,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 256},
            "messages": [
                {"role": "system", "content": system or SYSTEM},
                {"role": "user", "content": user},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return "", str(exc), 0, 0
    msg = ((body.get("message") or {}).get("content")) or ""
    prompt_tok = int(body.get("prompt_eval_count") or 0)
    completion_tok = int(body.get("eval_count") or 0)
    return str(msg), None, prompt_tok, completion_tok


def _chat_openrouter(model: str, user: str, timeout: float, system: str | None = None) -> tuple[str, str | None, str, int, int]:
    from openrouter_chat import chat

    text, err, used = chat(user, system=system or SYSTEM, model=model, timeout=timeout)
    # OpenRouter may not return token counts; estimate from char length / 4
    est = max(1, len(user) // 4 + len(text) // 4)
    return text, err, used, est, est


def _parse_call(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "tool" not in data:
        return None
    data.setdefault("args", {})
    if not isinstance(data["args"], dict):
        data["args"] = {}
    return data


def _tool_catalog() -> str:
    import deploy.melodia_mcp_server as server

    lines = []
    for tool in getattr(server, "TOOLS", []):
        lines.append(f"- {tool.get('name')}: {tool.get('description', '')[:140]}")
    return "\n".join(lines)


def _monolith_live() -> bool:
    try:
        import deploy.melodia_mcp_server as server

        return bool(getattr(server, "_monolith_is_live", lambda: False)())
    except Exception:
        return False


def run_model(
    model: str,
    timeout: float,
    *,
    backend: str = "ollama",
    measure_ter: bool = True,
) -> dict[str, Any]:
    from run_math_eval import _check

    import deploy.melodia_mcp_server as server

    editor_live = _monolith_live()

    if backend == "openrouter":
        def _call(user: str, system: str | None = None) -> tuple[str, str | None, int, int]:
            text, err, _used, pt, ct = _chat_openrouter(model, user, timeout, system=system)
            return text, err if err else None, pt, ct

        backend_note = f"openrouter ({model})"
    else:
        def _call(user: str, system: str | None = None) -> tuple[str, str | None, int, int]:
            return _chat_ollama(model, user, timeout, system=system)

        backend_note = f"ollama ({model})"

    gold = json.loads(TASKS.read_text(encoding="utf-8"))
    prompt_spec = json.loads(PROMPTS.read_text(encoding="utf-8")) if PROMPTS.exists() else {"prompts": {}}
    catalog = _tool_catalog()
    rows = []
    tool_hits = arg_hits = exec_hits = held = 0
    tokens_unconstrained = 0
    tokens_constrained = 0
    ter_samples = 0

    UNCONSTRAINED_SYSTEM = (
        "You are a Melodia game integration assistant. Answer with a JSON object describing "
        "which API operation to call and its arguments. No markdown."
    )

    for task in gold["tasks"]:
        if task.get("editor_required") and not editor_live:
            held += 1
            rows.append({
                "id": task["id"],
                "gold_tool": task["tool"],
                "chosen_tool": None,
                "tool_match": False,
                "args_match": False,
                "exec_ok": False,
                "status": "hold",
                "detail": "editor_required — Monolith unreachable on :9316",
            })
            continue

        prompt = (prompt_spec.get("prompts") or {}).get(task["id"], task["id"])
        user_constrained = f"Registered tools:\n{catalog}\n\nTask: {prompt}"
        text, err, pt_c, ct_c = _call(user_constrained)
        tokens_constrained += pt_c + ct_c

        if measure_ter:
            user_unconstrained = (
                f"Task: {prompt}\n\n"
                "Describe the full Melodia integration operation needed, including all parameters, "
                "without using a tool registry."
            )
            _u_text, _u_err, pt_u, ct_u = _call(user_unconstrained, system=UNCONSTRAINED_SYSTEM)
            tokens_unconstrained += pt_u + ct_u
            ter_samples += 1

        parsed = _parse_call(text) if not err else None
        gold_tool, gold_args = task["tool"], task.get("args") or {}
        tool_ok = bool(parsed) and parsed.get("tool") == gold_tool
        arg_ok = bool(parsed) and dict(parsed.get("args") or {}) == dict(gold_args)
        exec_ok = False
        detail = err or "unparsed"
        if parsed:
            fn = getattr(server, str(parsed.get("tool") or ""), None)
            if fn is None:
                detail = f"unknown tool {parsed.get('tool')}"
            else:
                try:
                    result = fn(**(parsed.get("args") or {}))
                    exec_ok, detail = _check(result, task) if isinstance(result, dict) else (False, "non-dict")
                except Exception as exc:
                    detail = str(exc)
        if tool_ok:
            tool_hits += 1
        if arg_ok:
            arg_hits += 1
        if exec_ok:
            exec_hits += 1
        rows.append(
            {
                "id": task["id"],
                "gold_tool": gold_tool,
                "chosen_tool": None if not parsed else parsed.get("tool"),
                "tool_match": tool_ok,
                "args_match": arg_ok,
                "exec_ok": exec_ok,
                "status": "pass" if exec_ok else "fail",
                "detail": detail[:240],
            }
        )
    n = len(gold["tasks"])
    scored = n - held
    ter_ratio = round(tokens_constrained / tokens_unconstrained, 4) if tokens_unconstrained > 0 else None
    return {
        "schema": "melodia.math_run.v1",
        "kind": "model_via_hermes_harness",
        "harness": "hermes (deploy/hermes_mcp.py + deploy/melodia_mcp_server.py)",
        "model": model,
        "backend": backend_note,
        "note": "Scores a model choosing Hermes MCP tools. Not a Nous Hermes 3 weight pull.",
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "editor_contacted": editor_live,
        "passed": exec_hits,
        "total": n,
        "scored": scored,
        "held": held,
        "failed": scored - exec_hits,
        "tca_pct": round(100.0 * tool_hits / scored, 1) if scored else 0.0,
        "arg_pct": round(100.0 * arg_hits / scored, 1) if scored else 0.0,
        "exec_pct": round(100.0 * exec_hits / scored, 1) if scored else 0.0,
        "ter_ratio": ter_ratio,
        "ter_target": 0.20,
        "ter_meets_target": ter_ratio is not None and ter_ratio <= 0.20,
        "tokens_unconstrained": tokens_unconstrained,
        "tokens_constrained": tokens_constrained,
        "ter_samples": ter_samples,
        "tasks": rows,
    }


def _write(report: dict[str, Any], slug: str) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    path = AUDIT / f"math_run_{slug}_{stamp}.json"
    text = json.dumps(report, indent=2)
    path.write_text(text, encoding="utf-8")
    latest = AUDIT / "math_run_models_latest.json"
    if latest.exists():
        try:
            bundle = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            bundle = {"schema": "melodia.math_run_models.v1", "runs": []}
    else:
        bundle = {"schema": "melodia.math_run_models.v1", "runs": []}
    runs = [r for r in bundle.get("runs") or [] if r.get("model") != report.get("model")]
    runs.append(report)
    bundle["runs"] = runs
    bundle["updated_at"] = report["captured_at"]
    latest.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    if STATUS.is_dir():
        (STATUS / "math_run_models_latest.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        (STATUS / path.name).write_text(text, encoding="utf-8")
    return path


def _run_muse(timeout: float) -> tuple[int, dict[str, Any] | None]:
    ollama_tag = _resolve_muse_ollama()
    if ollama_tag:
        report = run_model(ollama_tag, timeout, backend="ollama")
        slug = "muse-glimmer-30b"
        path = _write(report, slug)
        print(
            f"{ollama_tag}: TCA={report['tca_pct']}% ARG={report['arg_pct']}% "
            f"EXEC={report['exec_pct']}% ({path.name})"
        )
        for row in report["tasks"]:
            mark = "PASS" if row["exec_ok"] else "FAIL"
            print(f"  {mark}  {row['id']}  tool={row.get('chosen_tool')}  {row['detail'][:80]}")
        return (0 if report["failed"] == 0 else 1, report)

    from openrouter_chat import probe_muse

    probe = probe_muse(timeout=min(timeout, 25.0))
    if probe.get("ok"):
        report = run_model(MUSE_OPENROUTER, timeout, backend="openrouter")
        slug = "muse-spark-openrouter"
        path = _write(report, slug)
        print(
            f"{MUSE_OPENROUTER} (openrouter): TCA={report['tca_pct']}% ARG={report['arg_pct']}% "
            f"EXEC={report['exec_pct']}% ({path.name})"
        )
        for row in report["tasks"]:
            mark = "PASS" if row["exec_ok"] else "FAIL"
            print(f"  {mark}  {row['id']}  tool={row.get('chosen_tool')}  {row['detail'][:80]}")
        return (0 if report["failed"] == 0 else 1, report)

    skip = {
        "schema": "melodia.math_run.v1",
        "kind": "skipped",
        "model": "muse-glimmer",
        "status": "skipped",
        "reason": (
            "no ollama muse tag; OPENROUTER probe failed — "
            f"{probe.get('sample', 'set OPENROUTER_API_KEY or run Tools/setup_muse_glimmer.py --pull')}"
        ),
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }
    skip_path = AUDIT / "math_run_muse-glimmer_skipped.json"
    skip_path.write_text(json.dumps(skip, indent=2), encoding="utf-8")
    print(f"muse-glimmer: SKIPPED ({skip['reason']})")
    return (0, None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--backend", choices=("ollama", "openrouter", "auto"), default="ollama")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--run-muse", action="store_true", help="Also evaluate Muse Glimmer lane if available")
    parser.add_argument("--skip-muse", action="store_true", help="Deprecated; default is to skip muse unless --run-muse")
    parser.add_argument("--no-ter", action="store_true", help="Skip TER (token efficiency) measurement")
    args = parser.parse_args(argv)

    backend = args.backend
    if backend == "auto":
        backend = "openrouter" if args.model.startswith("meta/") else "ollama"

    report = run_model(args.model, args.timeout, backend=backend, measure_ter=not args.no_ter)
    slug = args.model.replace(":", "_").replace("/", "_")
    path = _write(report, slug)
    ter_note = ""
    if report.get("ter_ratio") is not None:
        ter_note = f" TER={report['ter_ratio']} ({report['tokens_constrained']}/{report['tokens_unconstrained']})"
    print(
        f"{args.model}: TCA={report['tca_pct']}% ARG={report['arg_pct']}% "
        f"EXEC={report['exec_pct']}%{ter_note} ({path.name})"
    )
    for row in report["tasks"]:
        mark = "PASS" if row["exec_ok"] else "FAIL"
        print(f"  {mark}  {row['id']}  tool={row.get('chosen_tool')}  {row['detail'][:80]}")

    rc = 0 if report["failed"] == 0 else 1
    if args.run_muse:
        muse_rc, _ = _run_muse(args.timeout)
        rc = max(rc, muse_rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
