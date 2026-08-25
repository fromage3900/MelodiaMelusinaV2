#!/usr/bin/env python3
"""Model Router - policy-based model selection, chat dispatch, cost ledger.

Picks the best model per task class, with ordered fallbacks, then can run the
chat call itself. Keys come from env (OPENROUTER_API_KEY / TOKENROUTER_API_KEY /
LOCAL_LLM_API_KEY) or fall back to the root .mcp.json (legacy; prefer env).

Local daemons: set LOCAL_LLM_BASE_URL (default http://127.0.0.1:11434/v1 for Ollama).

Usage:
  python model_router.py pick <class> [--detail]
  python model_router.py chat <class> --prompt "..." [--json]
  python model_router.py test [--class <class>] [--include-blocked]
  python model_router.py ledger [--tail N]
  python model_router.py cost
  python model_router.py classes

Policy authority: Docs/Production/MODEL_LANES_2026-08-12.md
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_MCP = os.path.abspath(os.path.join(_TOOLS_DIR, "..", "..", ".mcp.json"))
LEDGER = os.path.abspath(os.path.join(_TOOLS_DIR, "..", "Saved", "router_ledger.jsonl"))
# Local models on a cold load can exceed 90s before first token, especially the
# 21-30 GB tags. Override with LLM_REQUEST_TIMEOUT when driving production lanes.
REQUEST_TIMEOUT = int(os.environ.get("LLM_REQUEST_TIMEOUT", "90"))

LOCAL_BASE = os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")

ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "tokenrouter": "https://api.tokenrouter.com/v1",
    "local": LOCAL_BASE,
}

PRICES = {
    "deepseek/deepseek-v4-flash": (0.00000014, 0.00000028),
    "deepseek/deepseek-v4-pro": (0.00000063168, 0.00000126336),
    "mistralai/mistral-medium-3-5": (0.0000015, 0.0000075),
    "x-ai/grok-4.5": (0.000002, 0.000006),
    "x-ai/grok-4.20-multi-agent": (0.00000125, 0.0000025),
    "meta/muse-spark-1.2": (0.00000125, 0.00000425),
    "moonshotai/kimi-k3-free": (0.0, 0.0),
    "nvidia/nemotron-3-ultra-550b-a55b:free": (0.0, 0.0),
    "nvidia/nemotron-3-super-120b-a12b:free": (0.0, 0.0),
    "openai/gpt-oss-20b:free": (0.0, 0.0),
    "mistralai/codestral-2508": (0.0000003, 0.0000009),
    # Local Ollama tags - zero API cost
    # Verified installed 2026-08-20 via `ollama list`.
    "qwen2.5-coder:7b": (0.0, 0.0),
    "qwen2.5-coder:14b": (0.0, 0.0),
    "qwen3.8-27b": (0.0, 0.0),
    "muse-glimmer-30b": (0.0, 0.0),
    "muse-glimmer-30b-cpu": (0.0, 0.0),
    "deepseek-r1:7b": (0.0, 0.0),
    "deepseek-r1:14b": (0.0, 0.0),
    "deepseek-coder:6.7b": (0.0, 0.0),
    "qwen3:8b": (0.0, 0.0),
    "qwen3-coder:14b": (0.0, 0.0),
    "qwen3-coder:32b": (0.0, 0.0),
    "qwen3-coder-next": (0.0, 0.0),
    "devstral-small": (0.0, 0.0),
    "gpt-oss:20b": (0.0, 0.0),
}

BLOCKED = {
    "meta/muse-spark-1.2": "requires 18+ confirmation at openrouter.ai/settings/preferences",
    # Corrupt weights on disk, verified 2026-08-20: loads, then emits repeated tokens.
    # Docs/OLLAMA_SETUP_FIX_2026-08-20.md. Remove after re-pull + coherence smoke test.
    "qwen2.5-coder:14b": "corrupt weights on disk - emits repeated tokens; re-pull and smoke-test first",
    # 1/8 on the discovery probe: right tool in prose, no JSON.
    "deepseek-coder:6.7b": "no structured output - unusable as an MCP client without constrained decoding",
}

# Classes that must never silently reach a paid cloud endpoint.
# `daemon` runs unattended overnight; the production lanes generate game content.
PRODUCTION_CLASSES = frozenset({
    "wardrobe_catalog", "beatmap_author", "quill_author", "asset_qa", "anim_bindings",
})
LOCAL_ONLY_CLASSES = frozenset({"daemon"}) | PRODUCTION_CLASSES

# Production lanes MUST NOT do these. Mirrors the AGENTS.md must-not table.
PRODUCTION_MUST_NOT = {
    "wardrobe_catalog": "invent slots, or bypass UMelodiaWardrobeSubsystem",
    "beatmap_author": "make rhythm a second combat authority",
    "quill_author": "emit an id that is not in the allowlist",
    "asset_qa": "fabricate a file path",
    "anim_bindings": "write .uasset",
}
# No production lane certifies its own gate. An artifact is accepted by
# `Tools/echo_run.py record <gate> pass`, run by a human or a gate script -- never
# by the model that produced it.

# Narrowest class wins. See Docs/Production/MODEL_LANES_2026-08-12.md
#
# PRODUCTION LANES (added 2026-08-20, paradigm shift).
# The AI tooling is a tool. These five lanes route REAL game work to local models.
# A lane's output counts only when an Echo gate accepts the artifact --
# `python Tools/echo_run.py record <gate> pass|fail`. A score is not an acceptance.
#
# Local-first by design: every production lane leads with a model that is actually
# pulled on this workstation (verified 2026-08-20 via `ollama list`). Cloud entries
# are fallbacks, never the default -- production content should not require network.
#
# Model-fit evidence, not vibes:
#   qwen2.5-coder:7b   -- 7/8 with 100% surface adherence on the 2-tool discovery probe
#                         (Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md). Never invented a
#                         tool outside the manifest. Best structured-output local model.
#   deepseek-coder:6.7b -- 1/8. Names the right tool in prose, emits no JSON. Routed
#                         NOWHERE. Do not add it to a lane without constrained decoding.
POLICY = {
    # ---- production lanes: real game artifacts, gate-accepted ----
    #
    # QUARANTINED - do not add to any lane until re-verified:
    #   qwen2.5-coder:14b  -- CORRUPT WEIGHTS ON DISK. Loads fine, then emits pure
    #                         repeated tokens ("8888888..."), 0/8 with all responses
    #                         unparsed. Isolated to this tag: qwen2.5-coder:7b is
    #                         coherent on identical config/prompt/store, and both tags
    #                         carry exclusive blobs, so it is not shared-blob
    #                         corruption. Docs/OLLAMA_SETUP_FIX_2026-08-20.md.
    #                         Fix: `ollama rm` + `ollama pull`, then a coherence smoke
    #                         test BEFORE any sweep. Re-add only after that passes.
    #   deepseek-coder:6.7b -- 1/8 on the discovery probe. Names the right tool in
    #                         prose, emits no JSON. Unusable without constrained decoding.
    #
    # Load times on this workstation are dominated by disk, not compute: the model
    # store is on a 32 MB/s HDD, so a 9 GB tag needs ~5 min and a 21 GB tag ~11 min to
    # page in cold. Drive production lanes with LLM_REQUEST_TIMEOUT=1200.
    "wardrobe_catalog": [
        ("qwen2.5-coder:7b", "local", "7/8, 100% surface adherence; coherent smoke test"),
        ("qwen3.8-27b", "local", "larger local fallback (~11 min cold load)"),
        ("deepseek/deepseek-v4-flash", "openrouter", "cloud fallback only"),
    ],
    "beatmap_author": [
        ("qwen3.8-27b", "local", "beat maps vs MelodiaRhythmSkillDefinition"),
        ("qwen2.5-coder:7b", "local", "smaller/faster fallback"),
        ("mistralai/mistral-medium-3-5", "openrouter", "cloud fallback only"),
    ],
    "quill_author": [
        ("muse-glimmer-30b", "local", "narrative-weighted; QuillScript dialogue drafts"),
        ("muse-glimmer-30b-cpu", "local", "CPU build when VRAM is held by the editor"),
        ("mistralai/mistral-medium-3-5", "openrouter", "cloud fallback only"),
    ],
    "asset_qa": [
        ("qwen2.5-coder:7b", "local", "art/credits/bp gate triage - only verified-coherent coder tag"),
        ("deepseek-r1:14b", "local", "reasoning fallback for triage"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free wide-context fallback"),
    ],
    "anim_bindings": [
        ("deepseek-r1:14b", "local", "ABP state machine + pose binding cross-check"),
        ("deepseek-r1:7b", "local", "lighter fallback"),
        ("deepseek/deepseek-v4-flash", "openrouter", "cloud fallback only"),
    ],
    "triage": [
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free 1M ctx"),
        ("openai/gpt-oss-20b:free", "openrouter", "free code"),
        ("qwen3:8b", "local", "local daemon triage"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "slow but strong fallback"),
    ],
    "audit": [
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free heavy"),
        ("deepseek/deepseek-v4-flash", "openrouter", "analysis"),
        ("qwen3-coder:14b", "local", "local static-gate loops"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "code": [
        ("deepseek/deepseek-v4-flash", "openrouter", "default coder"),
        ("mistralai/codestral-2508", "openrouter", "code specialist"),
        ("qwen3-coder:14b", "local", "local code daemon"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "cpp": [
        ("deepseek/deepseek-v4-pro", "openrouter", "stronger C++/UE reasoning"),
        ("deepseek/deepseek-v4-flash", "openrouter", "fast C++ fallback"),
        ("qwen3-coder:32b", "local", "local C++ if 24GB+ VRAM"),
        ("devstral-small", "local", "agentic multi-file local"),
    ],
    "mcp": [
        ("x-ai/grok-4.5", "openrouter", "MCP multi-step plans"),
        ("mistralai/mistral-medium-3-5", "openrouter", "tool-orchestration fallback"),
        ("qwen3-coder-next", "local", "local agentic MCP (80A3)"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "MCP-strong free"),
    ],
    "playtest": [
        ("x-ai/grok-4.5", "openrouter", "fresh-eyes on assertion JSON"),
        ("mistralai/mistral-medium-3-5", "openrouter", "report grading"),
        ("qwen3-coder:14b", "local", "grade reports only - never record pass alone"),
    ],
    "author": [
        ("mistralai/mistral-medium-3-5", "openrouter", "creative/agentic frontier"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "free fallback"),
        ("qwen3:8b", "local", "local dialogue drafts"),
    ],
    "deep": [
        ("moonshotai/kimi-k3-free", "tokenrouter", "SLOW but strong: long complex tasks"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
    ],
    "review": [
        ("x-ai/grok-4.5", "openrouter", "fresh-eyes verifier"),
        ("meta/muse-spark-1.2", "openrouter", "multimodal review"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
    ],
    "orchestrator": [
        ("x-ai/grok-4.20-multi-agent", "openrouter", "multi-agent orchestration"),
        ("x-ai/grok-4.5", "openrouter", "frontier fallback"),
    ],
    "vision": [
        ("mistralai/mistral-medium-3-5", "openrouter", "screenshot review"),
        ("meta/muse-spark-1.2", "openrouter", "video input (age-confirm first)"),
    ],
    "daemon": [
        ("qwen3-coder:14b", "local", "overnight code/audit loops (16GB+)"),
        ("qwen3:8b", "local", "overnight triage/docs (8GB)"),
        ("qwen3-coder-next", "local", "agentic daemon if pulled"),
        ("gpt-oss:20b", "local", "alt local free-weight"),
    ],
    "docs": [
        ("deepseek/deepseek-v4-flash", "openrouter", "handoff/fold-in prose"),
        ("qwen3:8b", "local", "local docs daemon"),
        ("openai/gpt-oss-20b:free", "openrouter", "free fallback"),
    ],
}


def load_keys():
    keys = {
        "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
        "tokenrouter": os.environ.get("TOKENROUTER_API_KEY", ""),
        "local": os.environ.get("LOCAL_LLM_API_KEY", "ollama"),
    }
    if not keys["openrouter"] or not keys["tokenrouter"]:
        try:
            with open(ROOT_MCP, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for _name, server in data.get("mcpServers", {}).items():
                env = server.get("env", {})
                base = env.get("OPENAI_BASE_URL", "")
                key = env.get("OPENAI_API_KEY", "")
                if "openrouter" in base and key and not keys["openrouter"]:
                    keys["openrouter"] = key
                if "tokenrouter" in base and key and not keys["tokenrouter"]:
                    keys["tokenrouter"] = key
        except Exception:
            pass
    return keys


def chat(model, endpoint, prompt, keys, system=None, max_tokens=2000, temperature=0.2,
         request_timeout=REQUEST_TIMEOUT):
    url = ENDPOINTS[endpoint] + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        payload["messages"].insert(0, {"role": "system", "content": system})
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + (keys.get(endpoint) or "ollama"),
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=request_timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def estimate_cost(model, usage):
    if not usage:
        return 0.0
    pin, pout = PRICES.get(model, (0.0, 0.0))
    return pin * usage.get("prompt_tokens", 0) + pout * usage.get("completion_tokens", 0)


def log_usage(task_class, model, endpoint, usage, ok=True):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "class": task_class,
        "model": model,
        "endpoint": endpoint,
        "in": (usage or {}).get("prompt_tokens", 0),
        "out": (usage or {}).get("completion_tokens", 0),
        "cost_usd": estimate_cost(model, usage) if ok else 0.0,
        "ok": ok,
    }
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def pick(task_class, detail=False):
    if task_class not in POLICY:
        sys.exit("unknown task class: %s (use: %s)" % (task_class, " ".join(sorted(POLICY))))
    if detail:
        for i, (model, endpoint, note) in enumerate(POLICY[task_class]):
            marker = " BLOCKED: " + BLOCKED[model] if model in BLOCKED else ""
            print("%d. %-40s %-11s %s%s" % (i + 1, model, endpoint, note, marker))
        return
    print(POLICY[task_class][0][0])


def run_chat(task_class, prompt, system=None, json_out=False, attempt=0, max_tokens=2000,
             timeout=None):
    keys = load_keys()
    candidates = POLICY[task_class][attempt:]
    last_err = None
    # daemon + production lanes: local first - never silently fall through to paid
    # cloud. Production lanes produce game artifacts; a surprise cloud bill or a
    # network dependency in the content pipeline is a defect, not a fallback.
    if task_class in LOCAL_ONLY_CLASSES:
        candidates = [c for c in candidates if c[1] == "local"]
    for model, endpoint, _note in candidates:
        if model in BLOCKED and attempt == 0:
            continue
        if endpoint != "local" and not keys.get(endpoint):
            last_err = "no key for %s" % endpoint
            continue
        started = time.time()
        try:
            result = chat(model, endpoint, prompt, keys, system=system, max_tokens=max_tokens,
                          request_timeout=timeout or REQUEST_TIMEOUT)
            usage = result.get("usage")
            log_usage(task_class, model, endpoint, usage)
            if json_out:
                print(json.dumps({"model": result.get("model"), "content": result["choices"][0]["message"]["content"], "usage": usage, "elapsed_s": round(time.time() - started, 1)}, ensure_ascii=False))
            else:
                print(result["choices"][0]["message"]["content"])
            return 0
        except urllib.error.HTTPError as exc:
            last_err = "HTTP %s %s" % (exc.code, exc.reason)
            log_usage(task_class, model, endpoint, None, ok=False)
        except Exception as exc:
            last_err = "%s after %.0fs" % (exc, time.time() - started)
            log_usage(task_class, model, endpoint, None, ok=False)
    sys.exit("all candidates failed for %s: %s" % (task_class, last_err))


def run_test(task_class, include_blocked=False):
    keys = load_keys()
    print("health check: %s" % task_class)
    ok_all = True
    for model, endpoint, note in POLICY[task_class]:
        if model in BLOCKED and not include_blocked:
            print("  SKIP %-40s %s" % (model, BLOCKED[model]))
            continue
        if endpoint != "local" and not keys.get(endpoint):
            print("  SKIP %-40s no key for %s" % (model, endpoint))
            continue
        try:
            result = chat(model, endpoint, "Reply with exactly: OK", keys, max_tokens=10)
            usage = result.get("usage")
            log_usage("health", model, endpoint, usage)
            print("  PASS %-40s %s" % (model, note))
        except Exception as exc:
            ok_all = False
            log_usage("health", model, endpoint, None, ok=False)
            print("  FAIL %-40s %s" % (model, exc))
    return 0 if ok_all else 1


def show_ledger(tail):
    if not os.path.exists(LEDGER):
        print("no ledger yet: %s" % LEDGER)
        return
    lines = open(LEDGER, encoding="utf-8").read().strip().splitlines()
    total = 0.0
    for line in lines[-tail:]:
        row = json.loads(line)
        total += row.get("cost_usd", 0.0)
        print("%s %-5s %-40s in=%-7d out=%-7d $%.6f %s" % (
            row["ts"], row["class"], row["model"], row["in"], row["out"],
            row["cost_usd"], "OK" if row["ok"] else "FAIL"))
    print("last %d calls: $%.6f" % (len(lines[-tail:]), total))


def show_cost():
    if not os.path.exists(LEDGER):
        print("no ledger yet")
        return
    by_model = {}
    total = 0.0
    for line in open(LEDGER, encoding="utf-8"):
        row = json.loads(line)
        if not row.get("ok"):
            continue
        key = row["model"]
        cost = row.get("cost_usd", 0.0)
        by_model.setdefault(key, {"calls": 0, "in": 0, "out": 0, "cost": 0.0})
        by_model[key]["calls"] += 1
        by_model[key]["in"] += row["in"]
        by_model[key]["out"] += row["out"]
        by_model[key]["cost"] += cost
        total += cost
    for model, s in sorted(by_model.items(), key=lambda kv: -kv[1]["cost"]):
        print("%-42s calls=%-4d in=%-8d out=%-8d $%.4f" % (
            model, s["calls"], s["in"], s["out"], s["cost"]))
    print("TOTAL: $%.4f" % total)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_pick = sub.add_parser("pick")
    p_pick.add_argument("task_class")
    p_pick.add_argument("--detail", action="store_true")
    p_chat = sub.add_parser("chat")
    p_chat.add_argument("task_class")
    p_chat.add_argument("--prompt")
    p_chat.add_argument("--prompt-file")
    p_chat.add_argument("--system")
    p_chat.add_argument("--max-tokens", type=int, default=2000)
    p_chat.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT)
    p_chat.add_argument("--json", dest="json_out", action="store_true")
    p_test = sub.add_parser("test")
    p_test.add_argument("--class", dest="task_class", default="code")
    p_test.add_argument("--include-blocked", action="store_true")
    p_ledger = sub.add_parser("ledger")
    p_ledger.add_argument("--tail", type=int, default=20)
    p_cost = sub.add_parser("cost")
    sub.add_parser("classes")
    args = ap.parse_args()

    if args.cmd == "pick":
        pick(args.task_class, detail=args.detail)
    elif args.cmd == "chat":
        prompt = args.prompt
        if args.prompt_file:
            with open(args.prompt_file, "r", encoding="utf-8") as fh:
                prompt = fh.read()
        run_chat(args.task_class, prompt, system=args.system, json_out=args.json_out,
                 max_tokens=args.max_tokens, timeout=args.timeout)
    elif args.cmd == "test":
        sys.exit(run_test(args.task_class, include_blocked=args.include_blocked))
    elif args.cmd == "ledger":
        show_ledger(args.tail)
    elif args.cmd == "cost":
        show_cost()
    elif args.cmd == "classes":
        for name in sorted(POLICY):
            print("%-14s %s" % (name, POLICY[name][0][0]))


if __name__ == "__main__":
    main()
