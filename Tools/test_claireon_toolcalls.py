#!/usr/bin/env python3
"""Claireon two-tool discovery-pattern probe against local Ollama models.

Claireon exposes exactly TWO MCP tools: tool_search (discover) and
python_execute (act, where catalog tools are callable as claireon.<name>(...)).
This harness scores whether a local model produces that two-step pattern
instead of hallucinating a flat tool name.

Not a substitute for a live Claireon editor: this measures the CLIENT side
(model behaviour under a 2-tool manifest) with the editor offline.

    python Tools/test_claireon_toolcalls.py --model qwen2.5-coder:7b
    python Tools/test_claireon_toolcalls.py --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
OLLAMA = "http://127.0.0.1:11434"
PROXY_REG_PORT = 43017

# Claireon's 2-tool MCP manifest, verbatim in shape from its README.
CLAIREON_MANIFEST = """Available MCP tools (exactly two):
- tool_search: Search the editor tool catalog. Args: {"query": "<free text>"} or {"tool_name": "<exact>"} for full detail on one tool.
- python_execute: Run Python in the Unreal editor. Args: {"code": "<python>"}. Every catalog tool is callable as claireon.<tool_name>(...)."""

SYSTEM = (
    "You are an agent connected to the Claireon MCP server for Unreal Engine. "
    "It exposes ONLY two tools: tool_search and python_execute. "
    "You must discover tools with tool_search before calling them via python_execute. "
    'Reply with ONLY a JSON object: {"tool": "<tool_search|python_execute>", "args": {...}}. No markdown, no prose.'
)

# Each task: what the user wants, and which of the 2 tools is the correct FIRST move.
TASKS: list[dict[str, Any]] = [
    {
        "id": "discover_blueprint",
        "prompt": "Find out what tools are available for editing Blueprint graphs.",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["query"],
        "arg_hint": "blueprint",
    },
    {
        "id": "discover_statetree",
        "prompt": "I need to inspect a State Tree asset. What can I use?",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["query"],
        "arg_hint": "state tree",
    },
    {
        "id": "detail_named_tool",
        "prompt": "Show me the full schema and parameters for the tool named bp_apply_delta.",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["tool_name"],
        "arg_hint": "bp_apply_delta",
    },
    {
        "id": "execute_known_tool",
        "prompt": "You already know the tool asset_list exists. List assets under /Game/MelodiaIntegration now.",
        "gold_tool": "python_execute",
        "expect_arg_keys": ["code"],
        "arg_hint": "claireon.asset_list",
    },
    {
        "id": "execute_python_direct",
        "prompt": "Run editor Python that prints the number of currently selected actors.",
        "gold_tool": "python_execute",
        "expect_arg_keys": ["code"],
        "arg_hint": "unreal",
    },
    {
        "id": "discover_niagara",
        "prompt": "What is available for inspecting Niagara particle systems?",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["query"],
        "arg_hint": "niagara",
    },
    {
        "id": "no_flat_hallucination",
        "prompt": "Compile the Blueprint at /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["query"],
        "arg_hint": "compile",
        "note": "Correct behaviour is to SEARCH first, not invent a flat bp_compile tool.",
    },
    {
        "id": "widget_discovery",
        "prompt": "I want to read a UMG widget hierarchy. Find the right tool.",
        "gold_tool": "tool_search",
        "expect_arg_keys": ["query"],
        "arg_hint": "widget",
    },
]


def claireon_port(worktree: Path) -> int:
    """Claireon binds SHA-256(canonical root) folded into 49152-65535."""
    canonical = str(worktree.resolve())
    digest = hashlib.sha256(canonical.lower().encode("utf-8")).hexdigest()
    return 49152 + (int(digest[:8], 16) % 16384)


def port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.6) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def ollama_tags() -> list[str]:
    try:
        raw = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read().decode()
        data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []
    return [str(m.get("name") or "") for m in data.get("models") or []]


def chat(model: str, user: str, timeout: float) -> tuple[str, str | None, int, int]:
    payload = json.dumps({
        "model": model,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 256},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
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
    return str(msg), None, int(body.get("prompt_eval_count") or 0), int(body.get("eval_count") or 0)


def parse_call(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if "</think>" in raw:
        raw = raw.split("</think>", 1)[1].strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "tool" not in data:
        return None
    data.setdefault("args", {})
    if not isinstance(data["args"], dict):
        data["args"] = {}
    return data


VALID_TOOLS = {"tool_search", "python_execute"}


def score_task(task: dict[str, Any], parsed: dict[str, Any] | None) -> dict[str, Any]:
    """Score one task. Returns row dict with the four graded axes."""
    gold = task["gold_tool"]
    chosen = None if not parsed else str(parsed.get("tool") or "")
    args = {} if not parsed else dict(parsed.get("args") or {})

    # Axis 1: did it stay inside the 2-tool surface at all?
    in_surface = chosen in VALID_TOOLS
    # Axis 2: did it pick the right one of the two?
    tool_match = chosen == gold
    # Axis 3: did it use the expected arg key?
    arg_keys_ok = any(k in args for k in task["expect_arg_keys"])
    # Axis 4: does the arg value point at the right subject?
    hint = str(task.get("arg_hint") or "").lower()
    arg_value = " ".join(str(v) for v in args.values()).lower()
    hint_ok = bool(hint) and hint in arg_value

    return {
        "id": task["id"],
        "gold_tool": gold,
        "chosen_tool": chosen,
        "in_surface": in_surface,
        "tool_match": tool_match,
        "arg_keys_ok": arg_keys_ok,
        "hint_ok": hint_ok,
        "status": "pass" if (tool_match and arg_keys_ok) else "fail",
        "args": args,
        "note": task.get("note"),
    }


def run_model(model: str, timeout: float) -> dict[str, Any]:
    worktree = ROOT
    port = claireon_port(worktree)
    editor_live = port_listening(port)
    proxy_live = port_listening(PROXY_REG_PORT)

    rows: list[dict[str, Any]] = []
    prompt_tokens = completion_tokens = 0

    for task in TASKS:
        user = f"{CLAIREON_MANIFEST}\n\nTask: {task['prompt']}"
        text, err, pt, ct = chat(model, user, timeout)
        prompt_tokens += pt
        completion_tokens += ct
        parsed = parse_call(text) if not err else None
        row = score_task(task, parsed)
        row["error"] = err
        row["raw_head"] = (text or "")[:160]
        rows.append(row)

    n = len(rows)
    in_surface = sum(1 for r in rows if r["in_surface"])
    tool_hits = sum(1 for r in rows if r["tool_match"])
    arg_hits = sum(1 for r in rows if r["arg_keys_ok"])
    hint_hits = sum(1 for r in rows if r["hint_ok"])
    passed = sum(1 for r in rows if r["status"] == "pass")

    return {
        "schema": "claireon.toolcall_probe.v1",
        "kind": "client_side_two_tool_discovery",
        "note": "Measures whether a local model produces Claireon's tool_search -> python_execute "
                "pattern under a 2-tool manifest. Editor offline = no python_execute round-trip.",
        "model": model,
        "backend": f"ollama ({model})",
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "worktree": str(worktree),
        "claireon_port": port,
        "editor_reachable": editor_live,
        "proxy_reachable": proxy_live,
        "total": n,
        "passed": passed,
        "failed": n - passed,
        "surface_adherence_pct": round(100.0 * in_surface / n, 1) if n else 0.0,
        "tool_choice_pct": round(100.0 * tool_hits / n, 1) if n else 0.0,
        "arg_shape_pct": round(100.0 * arg_hits / n, 1) if n else 0.0,
        "arg_subject_pct": round(100.0 * hint_hits / n, 1) if n else 0.0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tasks": rows,
    }


def write_report(report: dict[str, Any]) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    slug = report["model"].replace(":", "_").replace("/", "_")
    stamp = datetime.now().strftime("%Y-%m-%d")
    path = AUDIT / f"claireon_probe_{slug}_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def print_summary(report: dict[str, Any]) -> None:
    print(f"\n  model            {report['model']}")
    print(f"  claireon port    {report['claireon_port']} "
          f"(editor {'UP' if report['editor_reachable'] else 'DOWN'}, "
          f"proxy {'UP' if report['proxy_reachable'] else 'DOWN'})")
    print(f"  passed           {report['passed']}/{report['total']}")
    print(f"  surface adherence {report['surface_adherence_pct']}%   (stayed inside the 2 tools)")
    print(f"  tool choice       {report['tool_choice_pct']}%   (picked the right one of 2)")
    print(f"  arg shape         {report['arg_shape_pct']}%   (used expected arg key)")
    print(f"  arg subject       {report['arg_subject_pct']}%   (arg points at right subject)")
    print()
    print(f"  {'id':22} {'gold':16} {'chosen':16} status")
    print(f"  {'-'*22} {'-'*16} {'-'*16} ------")
    for r in report["tasks"]:
        chosen = r["chosen_tool"] or "(unparsed)"
        print(f"  {r['id']:22} {r['gold_tool']:16} {chosen:16} {r['status']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", help="Ollama model tag")
    ap.add_argument("--all", action="store_true", help="Run every installed Ollama model")
    ap.add_argument("--timeout", type=float, default=1200.0,
                    help="Per-call timeout in seconds. Default 1200 (20 min) because "
                         "OLLAMA_MODELS may live on a slow disk — a cold 14B+ load can "
                         "take 5-11 minutes. See Tools/fix_ollama_setup.ps1.")
    args = ap.parse_args()

    tags = ollama_tags()
    if not tags:
        print("Ollama not reachable on 127.0.0.1:11434", file=sys.stderr)
        return 2

    if args.all:
        models = tags
    elif args.model:
        if args.model not in tags:
            print(f"Model {args.model!r} not installed. Available:", file=sys.stderr)
            for t in tags:
                print(f"  {t}", file=sys.stderr)
            return 3
        models = [args.model]
    else:
        print("Pass --model <tag> or --all. Installed:")
        for t in tags:
            print(f"  {t}")
        return 0

    failures: list[str] = []
    for model in models:
        # One model's failure must not abort the sweep — a cold-load timeout on a
        # 30B is expected on a slow store and should not lose the other results.
        try:
            report = run_model(model, args.timeout)
            path = write_report(report)
            print_summary(report)
            print(f"  report -> {path}", flush=True)
        except KeyboardInterrupt:
            print("\ninterrupted", file=sys.stderr)
            return 130
        except Exception as exc:
            failures.append(f"{model}: {exc}")
            print(f"\n  {model}: SWEEP ERROR — {exc}", file=sys.stderr, flush=True)

    if failures:
        print("\nModels that errored (not scored, NOT estimated):", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


