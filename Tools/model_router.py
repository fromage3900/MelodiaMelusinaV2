#!/usr/bin/env python3
"""Model Router — policy-based model selection, chat dispatch, cost ledger.

Picks the best model per task class, with ordered fallbacks, then can run the
chat call itself. Keys come from env (OPENROUTER_API_KEY / TOKENROUTER_API_KEY)
or fall back to the root .mcp.json (single source of truth, no key duplication).

Usage:
  python model_router.py pick <class> [--detail]
  python model_router.py chat <class> --prompt "..." [--json]
  python model_router.py test [--class <class>] [--include-blocked]
  python model_router.py ledger [--tail N]
  python model_router.py cost

Task classes: triage audit code author review orchestrator vision
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
REQUEST_TIMEOUT = 90

ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "tokenrouter": "https://api.tokenrouter.com/v1",
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
}

BLOCKED = {"meta/muse-spark-1.2": "requires 18+ confirmation at openrouter.ai/settings/preferences"}

POLICY = {
    "triage": [
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free 1M ctx"),
        ("openai/gpt-oss-20b:free", "openrouter", "free code"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "slow but strong fallback"),
    ],
    "audit": [
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free heavy"),
        ("deepseek/deepseek-v4-flash", "openrouter", "analysis"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "code": [
        ("deepseek/deepseek-v4-flash", "openrouter", "default coder"),
        ("mistralai/codestral-2508", "openrouter", "code specialist"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "author": [
        ("mistralai/mistral-medium-3-5", "openrouter", "creative/agentic frontier"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "free fallback"),
    ],
    "deep": [
        ("moonshotai/kimi-k3-free", "tokenrouter", "SLOW but strong: long complex tasks, clear rules, 3D spatial"),
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
}


def load_keys():
    keys = {
        "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
        "tokenrouter": os.environ.get("TOKENROUTER_API_KEY", ""),
    }
    if not any(keys.values()):
        try:
            with open(ROOT_MCP, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for name, server in data.get("mcpServers", {}).items():
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
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + keys[endpoint],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=request_timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def log_usage(task_class, model, endpoint, usage, ok=True):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        tokens_in = (usage or {}).get("prompt_tokens", 0)
        tokens_out = (usage or {}).get("completion_tokens", 0)
        p_in, p_out = PRICES.get(model, (0.0, 0.0))
        cost = tokens_in * p_in + tokens_out * p_out
        row = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "class": task_class,
            "model": model,
            "endpoint": endpoint,
            "in": tokens_in,
            "out": tokens_out,
            "cost_usd": round(cost, 6),
            "ok": ok,
        }
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        return row
    except Exception:
        return None


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
    for model, endpoint, _note in candidates:
        if model in BLOCKED and attempt == 0:
            continue
        if not keys.get(endpoint):
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
        if not keys.get(endpoint):
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


if __name__ == "__main__":
    main()
