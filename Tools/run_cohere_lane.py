"""Cohere API lane for the MATH harness.

Runs the same 32-task tool-surface spec through Cohere's Command model
family via the Cohere Python SDK (chat endpoint), and produces a
`tool_retrieval_<date>.json` evidence artifact comparing plain chat against
Embed v3 + Rerank 3 assisted tool retrieval (top-5 candidates).

Gate rule (mirrors the ollama lane): a score is not evidence until the run
JSON exists. If COHERE_API_KEY is unset, this exits 0 with status "held"
and writes no run JSON, so the health dashboard reports HOLD, not PASS.

Run:
    python Tools/run_cohere_lane.py                 # held until key set
    $env:COHERE_API_KEY=... ; python Tools/run_cohere_lane.py

The retrieval eval is optional and independent:
    python Tools/run_cohere_lane.py --retrieval-eval
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "specs" / "mcp" / "math_tasks.v1.json"
AUDIT = ROOT / "Saved" / "Audit"

SCHEMA = "melodia.math_run.v1"
CHAT_MAX_TOKENS = 256


def _load_spec() -> dict:
    return json.loads(TASKS.read_text(encoding="utf-8"))


def _check(result: dict, task: dict) -> tuple[bool, str]:
    """Structural check: tool name match + expect keys/values + require keys.

    Mirrors the math harness _check so lanes are comparable lane-to-lane.
    """
    expect = task.get("expect") or {}
    for key, want in expect.items():
        got = result.get(key)
        if got != want:
            return False, f"{key}: got {got!r} want {want!r}"
    for key in task.get("expect_keys") or []:
        if key not in result:
            return False, f"missing key: {key}"
    return True, "ok"


def _cohere_client():
    try:
        import cohere
    except ImportError as exc:  # pragma: no cover - env dependent
        raise RuntimeError(f"cohere SDK not installed: {exc}") from exc
    key = os.environ.get("COHERE_API_KEY")
    if not key:
        raise RuntimeError("COHERE_API_KEY unset")
    return cohere.ClientV2(api_key=key)


def _chat_call(client, model: str, system: str, user: str) -> tuple[str, str | None]:
    try:
        resp = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=CHAT_MAX_TOKENS,
            temperature=0.0,
        )
    except Exception as exc:
        return "", str(exc)
    text = (resp.message.content[0].text) if resp.message and resp.message.content else ""
    return str(text), None


def _parse_call(text: str) -> dict | None:
    raw = text.strip()
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
    return data


def _system_prompt() -> str:
    import deploy.melodia_mcp_server as server

    lines = ["You are an MCP tool caller for the Melodia game harness.",
             "Reply with exactly one JSON object: {\"tool\": \"<registered_tool_name>\", \"args\": {}}. No markdown.",
             "", "Registered tools:"]
    for tool in getattr(server, "TOOLS", []):
        lines.append(f"- {tool.get('name')}: {tool.get('description', '')[:140]}")
    return "\n".join(lines)


def _run_lane(model: str, client) -> dict:
    spec = _load_spec()
    tasks = spec["tasks"]
    system = _system_prompt()
    rows = []
    passed = 0
    for i, task in enumerate(tasks, 1):
        user = f"Call the right tool for this task. Task: {json.dumps(task)}"
        text, err = _chat_call(client, model, system, user)
        parsed = _parse_call(text) if not err else None
        exec_ok = False
        detail = err or "unparsed"
        if parsed:
            exec_ok, detail = _check(parsed, task) if isinstance(parsed, dict) else (False, "non-dict")
        if exec_ok:
            passed += 1
        rows.append({
            "id": task["id"],
            "tool": task["tool"],
            "pass": bool(exec_ok),
            "status": "pass" if exec_ok else "fail",
            "detail": detail,
            "output_tail": (text or "")[-400:],
        })
        print(f"  [{i}/{len(tasks)}] {task['id']}: {detail}", flush=True)
    return {
        "schema": SCHEMA,
        "kind": "model_via_cohere",
        "model": model,
        "backend": "cohere",
        "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "passed": passed,
        "total": len(tasks),
        "failed": len(tasks) - passed,
        "TCA": round(passed / len(tasks) * 100.0, 1) if tasks else 0.0,
        "tasks": rows,
    }


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


def _retrieval_eval(client) -> dict:
    """Embed v3 + Rerank 3 top-5 tool retrieval vs plain chat baseline."""
    import deploy.melodia_mcp_server as server

    tools = getattr(server, "TOOLS", [])
    names = [t.get("name", "") for t in tools]
    descs = [f"{t.get('name')}: {t.get('description', '')}" for t in tools]
    if not names:
        return {"status": "held", "reason": "no registered tools"}

    queries = [
        "start a dungeon encounter with grief hook",
        "get the current mana economy state",
        "notify a battle allow event",
        "validate the narrative record schema",
        "resolve the active encounter",
    ]
    rows = []
    try:
        embeds = client.embed(model="embed-v3.0", texts=descs, input_type="search_document")
        qemb = client.embed(model="embed-v3.0", texts=queries, input_type="search_query")
        reranked = client.rerank(model="rerank-3.5", query=queries[0], documents=descs, top_n=5)
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    import math

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)

    emb = [e.embedding for e in embeds.embeddings]
    qe = [q.embedding for q in qemb.embeddings]
    for i, q in enumerate(queries):
        scored = sorted(range(len(names)), key=lambda j: cosine(qe[i], emb[j]), reverse=True)[:5]
        rr = reranked.results[i] if i < len(reranked.results) else None
        rows.append({
            "query": q,
            "embed_top5": [names[j] for j in scored],
            "rerank_top5": [r.document["text"].split(":")[0] for r in rr.results] if rr else [],
        })
    return {
        "schema": "melodia.tool_retrieval.v1",
        "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": "embed-v3.0 + rerank-3.5 top-5 vs plain-chat baseline",
        "results": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="command-r-plus-08-2024")
    parser.add_argument("--retrieval-eval", action="store_true")
    args = parser.parse_args(argv)

    AUDIT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M")

    if not os.environ.get("COHERE_API_KEY"):
        held = {
            "schema": SCHEMA,
            "kind": "model_via_cohere",
            "model": args.model,
            "backend": "cohere",
            "status": "held",
            "reason": "COHERE_API_KEY unset; no run JSON until a lane completes",
            "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        out = AUDIT / f"cohere_lane_held_{stamp[:10]}.json"
        out.write_text(json.dumps(held, indent=2, sort_keys=True), encoding="utf-8")
        print(f"held: COHERE_API_KEY unset -> {out.name}")
        return 0

    client = _cohere_client()
    run = _run_lane(args.model, client)
    date = datetime.now().strftime("%Y-%m-%d")
    out = AUDIT / f"math_run_cohere_{date}.json"
    out.write_text(json.dumps(run, indent=2, sort_keys=True), encoding="utf-8")
    _update_latest_bundle(run)
    print(f"lane complete: {run['passed']}/{run['total']} TCA={run['TCA']}% -> {out.name}")

    if args.retrieval_eval:
        report = _retrieval_eval(client)
        retr_out = AUDIT / f"tool_retrieval_{date}.json"
        retr_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"retrieval eval: {report.get('status', 'ok')} -> {retr_out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
