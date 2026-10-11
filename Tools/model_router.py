#!/usr/bin/env python3
"""Model Router - policy-based model selection, chat dispatch, cost ledger.

Picks the best model per task class, with ordered fallbacks, then can run the
chat call itself. Keys come from env (OPENROUTER_API_KEY / TOKENROUTER_API_KEY /
LOCAL_LLM_API_KEY / NOUS_API_KEY) or fall back to the root .mcp.json (legacy; prefer env).
The Nous Portal key+endpoint are read from Hermes' auth.json (refreshed when expired),
so `nous` candidates work with no env setup.

Owner default (2026-10-05): `deepseek/deepseek-v4.1-flash` on the Nous Portal leads
every general class; daemon + production lanes stay local-first.

Local daemons: set LOCAL_LLM_BASE_URL (default http://127.0.0.1:11434/v1 for Ollama).

Usage:
  python model_router.py pick <class> [--detail]
  python model_router.py chat <class> --prompt "..." [--json]
  python model_router.py test [--class <class>] [--include-blocked]
  python model_router.py ledger [--tail N]
  python model_router.py cost
  python model_router.py classes
  python model_router.py tier <task> [--detail]
  python model_router.py tasks
  python model_router.py route <packet.json> [--json]        # H1: packet -> dispatch
  python model_router.py route-batch 'Tools/agent_router/fixtures/*.json'

Policy authority: Docs/Production/MODEL_LANES_2026-08-12.md
Packet/tier authority: specs/orchestration/model_tiers.v1.json + Tools/agent_router/task_packet.schema.json
Editor lease (the real single-writer guard): Tools/agent_lease.py
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_MCP = os.path.abspath(os.path.join(_TOOLS_DIR, "..", "..", ".mcp.json"))
LEDGER = os.path.abspath(os.path.join(_TOOLS_DIR, "..", "Saved", "router_ledger.jsonl"))
# Local models on a cold load can exceed 90s before first token, especially the
# 21-30 GB tags. Override with LLM_REQUEST_TIMEOUT when driving production lanes.
TIERS_SPEC = os.path.abspath(os.path.join(_TOOLS_DIR, "..", "specs", "orchestration", "model_tiers.v1.json"))

REQUEST_TIMEOUT = int(os.environ.get("LLM_REQUEST_TIMEOUT", "90"))

LOCAL_BASE = os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")

# Nous Portal (inference-api.nousresearch.com): the agent key in Hermes' auth.json is
# short-lived and rotated by Hermes; _nous_creds() re-reads (and refreshes) it at call time.
NOUS_AUTH_JSON = os.environ.get("NOUS_AUTH_JSON") or os.path.expanduser(
    os.path.join("~", "AppData", "Local", "hermes", "auth.json"))
_HERMES_PY = os.path.expanduser(
    os.path.join("~", "AppData", "Local", "hermes", "hermes-agent", "venv", "Scripts", "python.exe"))
NOUS_REFRESH_CMD = os.environ.get("NOUS_REFRESH_CMD") or (
    ('"%s" -c "from hermes_cli.auth import resolve_nous_runtime_credentials as r; '
     'r(timeout_seconds=30, force_refresh=True)"' % _HERMES_PY)
    if os.path.exists(_HERMES_PY) else "")

ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "tokenrouter": "https://api.tokenrouter.com/v1",
    "local": LOCAL_BASE,
    "bedrock": os.environ.get("BEDROCK_MANTLE_URL", "https://bedrock-mantle.us-east-1.api.aws/v1"),
    "nous": os.environ.get("NOUS_BASE_URL", "https://inference-api.nousresearch.com/v1"),
}

PRICES = {
    "deepseek/deepseek-v4-flash": (0.00000014, 0.00000028),
    # Owner default (Nous Portal). Price estimate mirrors v4-flash; update if the
    # portal rate differs.
    "deepseek/deepseek-v4.1-flash": (0.00000014, 0.00000028),
    "deepseek/deepseek-v4-pro": (0.00000063168, 0.00000126336),
    "mistralai/mistral-medium-3-5": (0.0000015, 0.0000075),
    "x-ai/grok-4.5": (0.000002, 0.000006),
    "x-ai/grok-4.20-multi-agent": (0.00000125, 0.0000025),
    "meta/muse-spark-1.2": (0.00000125, 0.00000425),
    "moonshotai/kimi-k3-free": (0.0, 0.0),
    "nvidia/nemotron-3-ultra-550b-a55b:free": (0.0, 0.0),
    "nvidia/nemotron-3-super-120b-a12b:free": (0.0, 0.0),
    "openai/gpt-oss-20b:free": (0.0, 0.0),
    # Free rotation 2026-09-02: opencode-go/deepseek → nous → meituan (OpenRouter free tier rotation)
    "meituan/longcat-2.0:free": (0.0, 0.0),
    "meituan/longcat-flash-chat:free": (0.0, 0.0),
    "nousresearch/hermes-4-405b:free": (0.0, 0.0),
    "nousresearch/hermes-4-70b:free": (0.0, 0.0),
    "nousresearch/hermes-3-llama-3.1-405b:free": (0.0, 0.0),
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
    # Bedrock Mantle (OpenAI-shaped, bearer token) - free tier on AWS account
    "qwen.qwen3-coder-next": (0.0, 0.0),
    "anthropic.claude-sonnet-5": (0.0, 0.0),
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
# Exception, owner-set 2026-10-05: `NOUS_DEFAULT` below leads every GENERAL class
# (triage..docs). The production lanes above and `daemon` stay local-first; `author`
# and `vision` keep their local/multimodal chains.
#
# Model-fit evidence, not vibes:
#   qwen2.5-coder:7b   -- 7/8 with 100% surface adherence on the 2-tool discovery probe
#                         (Docs/CLAIREON_PROBE_RESULTS_2026-08-20.md). Never invented a
#                         tool outside the manifest. Best structured-output local model.
#   deepseek-coder:6.7b -- 1/8. Names the right tool in prose, emits no JSON. Routed
#                         NOWHERE. Do not add it to a lane without constrained decoding.
# Owner default (2026-10-05): first candidate for every general class below.
NOUS_DEFAULT = ("deepseek/deepseek-v4.1-flash", "nous", "owner default: Nous Portal")

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
        ("qwen3-coder:30b", "local", "installed; qwen2.5-coder:7b no longer pulled"),
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
        ("muse-glimmer:30b", "local", "installed tag name (ollama list 2026-09-26)"),
        ("muse-glimmer-30b", "local", "narrative-weighted; QuillScript dialogue drafts"),
        ("muse-glimmer-30b-cpu", "local", "CPU build when VRAM is held by the editor"),
        ("mistralai/mistral-medium-3-5", "openrouter", "cloud fallback only"),
    ],
    "asset_qa": [
        ("qwen3-coder:30b", "local", "installed; qwen2.5-coder:7b no longer pulled"),
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
        NOUS_DEFAULT,
        ("zai.glm-4.7-flash", "bedrock", "Mantle fast/bulk, verified live 2026-09-26"),
        # Free rotation 2026-09-02: deepseek (opencode-go) → nous → meituan ; local fallback last
        ("meituan/longcat-2.0:free", "openrouter", "free rotation primary: meituan (switched)"),
        ("nousresearch/hermes-4-405b:free", "openrouter", "free rotation secondary: nous"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free rotation tertiary: nvidia (prev deepseek lane)"),
        ("openai/gpt-oss-20b:free", "openrouter", "free code fallback"),
        ("qwen3:8b", "local", "local daemon triage"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "slow but strong fallback"),
    ],
    "audit": [
        NOUS_DEFAULT,
        ("zai.glm-4.7-flash", "bedrock", "Mantle fast/bulk, verified live 2026-09-26"),
        ("meituan/longcat-2.0:free", "openrouter", "free rotation primary: meituan"),
        ("nousresearch/hermes-4-405b:free", "openrouter", "free rotation secondary: nous"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free heavy fallback"),
        ("deepseek/deepseek-v4-flash", "openrouter", "analysis (paid fallback)"),
        ("qwen3-coder:14b", "local", "local static-gate loops"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "code": [
        NOUS_DEFAULT,
        ("qwen.qwen3-coder-next", "bedrock", "Mantle coder, verified live 2026-09-26"),
        ("deepseek/deepseek-v4-flash", "openrouter", "default coder"),
        ("mistralai/codestral-2508", "openrouter", "code specialist"),
        ("qwen3-coder:14b", "local", "local code daemon"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
    ],
    "cpp": [
        NOUS_DEFAULT,
        ("qwen.qwen3-coder-480b-a35b-instruct", "bedrock", "Mantle heavy C++"),
        ("qwen.qwen3-coder-next", "bedrock", "Mantle coder, verified live 2026-09-26"),
        ("deepseek/deepseek-v4-pro", "openrouter", "stronger C++/UE reasoning"),
        ("deepseek/deepseek-v4-flash", "openrouter", "fast C++ fallback"),
        ("qwen3-coder:32b", "local", "local C++ if 24GB+ VRAM"),
        ("devstral-small", "local", "agentic multi-file local"),
    ],
    "mcp": [
        NOUS_DEFAULT,
        ("qwen.qwen3-coder-next", "bedrock", "Mantle agentic, verified live 2026-09-26"),
        ("x-ai/grok-4.5", "openrouter", "MCP multi-step plans"),
        ("mistralai/mistral-medium-3-5", "openrouter", "tool-orchestration fallback"),
        ("qwen3-coder-next", "local", "local agentic MCP (80A3)"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "MCP-strong free"),
    ],
    "playtest": [
        NOUS_DEFAULT,
        ("x-ai/grok-4.5", "openrouter", "fresh-eyes on assertion JSON"),
        ("mistralai/mistral-medium-3-5", "openrouter", "report grading"),
        ("qwen3-coder:14b", "local", "grade reports only - never record pass alone"),
    ],
    "author": [
        ("heretic-27b:latest", "local", "installed; local creative drafts"),
        ("mistralai/mistral-medium-3-5", "openrouter", "creative/agentic frontier"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "free fallback"),
        ("qwen3:8b", "local", "local dialogue drafts"),
    ],
    "deep": [
        NOUS_DEFAULT,
        ("qwen.qwen3-235b-a22b-2507", "bedrock", "Mantle long reasoning, verified live 2026-09-26"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "SLOW but strong: long complex tasks"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
    ],
    "review": [
        NOUS_DEFAULT,
        ("qwen.qwen3-235b-a22b-2507", "bedrock", "Mantle fresh-eyes, verified live 2026-09-26"),
        ("x-ai/grok-4.5", "openrouter", "fresh-eyes verifier"),
        ("meta/muse-spark-1.2", "openrouter", "multimodal review"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
    ],
    "orchestrator": [
        NOUS_DEFAULT,
        ("x-ai/grok-4.20-multi-agent", "openrouter", "multi-agent orchestration"),
        ("x-ai/grok-4.5", "openrouter", "frontier fallback"),
    ],
    "vision": [
        ("mistralai/mistral-medium-3-5", "openrouter", "screenshot review"),
        ("meta/muse-spark-1.2", "openrouter", "video input (age-confirm first)"),
    ],
    "daemon": [
        ("qwen3-coder:30b", "local", "installed 2026-09-26 (ollama list)"),
        ("qwen3-coder:14b", "local", "overnight code/audit loops (16GB+)"),
        ("qwen3:8b", "local", "overnight triage/docs (8GB)"),
        ("qwen3-coder-next", "local", "agentic daemon if pulled"),
        ("gpt-oss:20b", "local", "alt local free-weight"),
    ],
    "docs": [
        NOUS_DEFAULT,
        ("zai.glm-4.7-flash", "bedrock", "Mantle fast/bulk, verified live 2026-09-26"),
        ("deepseek/deepseek-v4-flash", "openrouter", "handoff/fold-in prose"),
        ("qwen3:8b", "local", "local docs daemon"),
        ("openai/gpt-oss-20b:free", "openrouter", "free fallback"),
    ],
}


def _nous_creds():
    """(key, base_url) from Hermes auth.json; refresh once if the agent key expired."""
    def read():
        with open(NOUS_AUTH_JSON, "r", encoding="utf-8") as fh:
            nous = json.load(fh)["providers"]["nous"]
        exp = nous.get("agent_key_expires_at") or ""
        stale = False
        if exp:
            try:
                stale = datetime.fromisoformat(exp).timestamp() < time.time() + 60
            except ValueError:
                stale = False
        return nous.get("agent_key", ""), (nous.get("inference_base_url") or "").rstrip("/"), stale

    try:
        key, base, stale = read()
        if stale and NOUS_REFRESH_CMD:
            subprocess.run(NOUS_REFRESH_CMD, shell=True, timeout=120, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            key, base, stale = read()
        if stale:
            return "", ""
        return key, base
    except Exception:
        return "", ""


def load_keys():
    keys = {
        "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
        "tokenrouter": os.environ.get("TOKENROUTER_API_KEY", ""),
        "local": os.environ.get("LOCAL_LLM_API_KEY", "ollama"),
        "bedrock": os.environ.get("AWS_BEARER_TOKEN_BEDROCK", ""),
        "nous": os.environ.get("NOUS_API_KEY", ""),
    }
    if not keys["nous"]:
        key, base = _nous_creds()
        keys["nous"] = key
        if base and not os.environ.get("NOUS_BASE_URL"):
            ENDPOINTS["nous"] = base
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
        "Authorization": "Bearer " + (_key_for(keys, endpoint) or "ollama"),
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

def pick_task(task_name, detail=False):
    if not os.path.exists(TIERS_SPEC):
        sys.exit("tiers spec not found: %s" % TIERS_SPEC)
    with open(TIERS_SPEC, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    routing = spec.get("routing_matrix", {})
    if task_name not in routing:
        sys.exit("unknown task: %s (available: %s)" % (task_name, " ".join(sorted(routing.keys()))))
    entry = routing[task_name]
    tier_id = entry.get("tier", "UNKNOWN")
    tier_map = {t["id"]: t for t in spec.get("tiers", []) if isinstance(t, dict) and "id" in t}
    tier_info = tier_map.get(tier_id, {})
    if detail:
        print("Task:       %s" % task_name)
        print("Tier:       %s (%s)" % (tier_id, tier_info.get("label", "")))
        print("Intent:     %s" % tier_info.get("intent", ""))
        print("Profile:    %s" % tier_info.get("cost_profile", ""))
        print("Primary:    %s (%s)" % (entry.get("model_primary"), entry.get("provider_primary")))
        print("Fallback:   %s (%s)" % (entry.get("model_fallback"), entry.get("provider_fallback")))
        print("Timeout:    %ss" % entry.get("timeout_s"))
        print("Rationale:  %s" % entry.get("rationale"))
        return
    print("%s (%s)" % (entry.get("model_primary"), tier_id))


def list_tasks():
    if not os.path.exists(TIERS_SPEC):
        sys.exit("tiers spec not found: %s" % TIERS_SPEC)
    with open(TIERS_SPEC, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    routing = spec.get("routing_matrix", {})
    print("%-28s %-6s %-32s %s" % ("TASK", "TIER", "PRIMARY MODEL", "PROVIDER"))
    print("-" * 80)
    for t_name in sorted(routing.keys()):
        r = routing[t_name]
        print("%-28s %-6s %-32s %s" % (t_name, r.get("tier"), r.get("model_primary"), r.get("provider_primary")))


# ----------------------------------------------------------------------------
# H1: `route` -- Task Packet -> dispatch decision.
#
# This is the only new routing surface. It is a subcommand of the EXISTING
# router on purpose: specs/orchestration/model_tiers.v1.json says
# "Extend Tools/model_router.py. No second router, orchestrator, lease or lane
# framework may be created."
#
# Contract, from the registry's own rules block:
#   deterministic      routing is a pure function of (packet, registry).
#                      No randomness, no voting, no free-form judgement.
#   widest_tier_wins   when several escalation triggers match, the highest tier wins.
#   no_silent_paid_fallback
#                      a local/bulk lane that cannot reach its own endpoint FAILS
#                      LOUDLY (classical-fallback). It never drifts up to a paid one.
#   no_self_certification
#                      a mutating packet is never graded by the lane that produced it.
#   one_editor_writer  needs_editor is advisory; the LEASE (Tools/agent_lease.py)
#                      is what actually enforces a single writer.
#
# `classical-fallback` means: DO NOT AUTO-DISPATCH. The card goes to the owner.
# It is a correct outcome, not an error - it is the safe answer whenever the
# packet is under-specified or the cheap lane is unavailable.
# ----------------------------------------------------------------------------

TASK_PACKET_SCHEMA = os.path.abspath(
    os.path.join(_TOOLS_DIR, "agent_router", "task_packet.schema.json"))

# Highest number == most restrictive. "widest_tier_wins" walks this in order.
TIER_RANK = {
    "T0_ARCHITECT": 0,
    "T1_VERIFIER": 1,
    "T2_EXECUTOR": 2,
    "T3_BULK": 3,
    "T4_LOCAL": 4,
}
VERIFIER_TIER = "T1_VERIFIER"
LOCAL_TIER = "T4_LOCAL"

MUTATION_RANK = {"none": 0, "files": 1, "editor": 2, "git": 3}


def _tier_order(tier_id):
    """Sort key for tiers. Unknown tiers sort as most restrictive (0) so an
    unrecognised tier can never silently widen a lane."""
    return TIER_RANK.get(tier_id, 0)


def _wider(a, b):
    return a if _tier_order(a) <= _tier_order(b) else b


def _glob_to_regex(pattern):
    """`**` spans separators, `*` does not, `?` is one non-separator char.
    Python's fnmatch would let `*` cross '/', which would make
    `Config/**` match `Config/a/b` but also let a bare `*` swallow the whole
    tree. Escalation globs must not over-match."""
    out = ["^"]
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif ch == "*":
            out.append("[^/]*")
            i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    out.append("$")
    return re.compile("".join(out))


_GLOB_CACHE = {}


def _path_matches(pattern, path):
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        rx = _GLOB_CACHE[pattern] = _glob_to_regex(pattern)
    return bool(rx.match(path))


def load_packet(source):
    """Accept a path to a .json packet, or a JSON document inline."""
    text = source
    stripped = source.strip()
    if not stripped.startswith("{"):
        if not os.path.exists(source):
            sys.exit("packet not found: %s" % source)
        with open(source, "r", encoding="utf-8") as fh:
            text = fh.read()
    try:
        packet = json.loads(text)
    except ValueError as exc:
        sys.exit("packet is not valid JSON: %s" % exc)
    if not isinstance(packet, dict):
        sys.exit("packet must be a JSON object")
    return packet


def validate_packet(packet):
    """Return a list of human-readable schema violations.

    Uses `jsonschema` when importable, because a real validator is the guard
    rail; falls back to a small hand-checked subset otherwise so the router
    still fails closed on a machine without the library. Never silently
    passes an obviously malformed packet.
    """
    if not os.path.exists(TASK_PACKET_SCHEMA):
        return ["task packet schema missing: %s" % TASK_PACKET_SCHEMA]
    with open(TASK_PACKET_SCHEMA, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    try:
        import jsonschema
    except ImportError:
        problems = []
        for key in schema.get("required", []):
            if key not in packet:
                problems.append("missing required field: %s" % key)
        for key, rule in schema.get("properties", {}).items():
            if key not in packet:
                continue
            allowed = rule.get("enum")
            if allowed and packet[key] not in allowed:
                problems.append("%s must be one of %s (got %r)"
                                % (key, "/".join(str(a) for a in allowed), packet[key]))
        return problems
    validator = jsonschema.Draft202012Validator(schema)
    return ["%s: %s" % ("/".join(str(p) for p in err.path) or "<root>", err.message)
            for err in sorted(validator.iter_errors(packet), key=lambda e: list(e.path))]


def match_escalations(packet, spec):
    """Every escalation trigger that fires for this packet, with the evidence.

    Two independent ways to fire, both from the registry:
      path_globs     against mutation_paths first, then inputs (a read of a
                     never-touch path still means the packet is about that path).
      goal_keywords  substring match against the goal, lowercased.
    """
    mutation_paths = packet.get("mutation_paths") or []
    inputs = packet.get("inputs") or []
    goal = (packet.get("goal") or "").lower()
    hits = []
    for trig in spec.get("escalation_triggers", []):
        matched = []
        for path in mutation_paths:
            for pat in trig.get("path_globs") or []:
                if _path_matches(pat, path):
                    matched.append({"via": "path", "value": path, "glob": pat})
                    break
        if not matched:
            for path in inputs:
                for pat in trig.get("path_globs") or []:
                    if _path_matches(pat, path):
                        matched.append({"via": "input", "value": path, "glob": pat})
                        break
        for kw in trig.get("goal_keywords") or []:
            if kw and kw.lower() in goal:
                matched.append({"via": "goal", "value": kw, "glob": None})
        if matched:
            hits.append({
                "id": trig.get("id"),
                "required_tier": trig.get("required_tier"),
                "why": trig.get("why"),
                "evidence": matched[:6],
            })
    return hits


def local_endpoint_reachable(timeout=1.5):
    """Is the local tier actually up? A T4_LOCAL packet must never drift to a
    paid endpoint just because Ollama is asleep - that is the
    `no_silent_paid_fallback` rule. So we probe, and we say so out loud."""
    parsed = urllib.parse.urlparse(LOCAL_BASE)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def local_models(timeout=3.0):
    """Models the local server actually has. `local_endpoint_reachable()` only
    proves something is LISTENING on 11434; it says nothing about whether the tag
    this packet needs exists. On 2026-10-03 the port was open with zero models
    pulled, and the router happily reported `dispatch: true` for a model it could
    not have served."""
    parsed = urllib.parse.urlparse(LOCAL_BASE)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    url = "http://%s:%s/api/tags" % (host, port)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return None
    return [m.get("name") for m in (payload.get("models") or [])]


def model_is_servable_locally(model):
    """True / False / None(unknown). `None` means we could not ask, and callers
    must not treat that as a pass."""
    tags = local_models()
    if tags is None:
        return None
    wanted = model.split("/")[-1]
    for tag in tags:
        if tag == model or tag == wanted:
            return True
        # ollama reports name as 'qwen2.5-coder:7b' but tolerates 'qwen2.5-coder'
        base = wanted.split(":")[0]
        if tag.split(":")[0] == base:
            return True
    return False


def resolve_model(tier_id, task_class, spec):
    """Pick the model for a tier.

    Preference order, all deterministic:
      1. the task class's own routing_matrix entry, when its tier IS the tier
      2. the first POLICY candidate of a class the tier lists in default_classes
      3. nothing -> caller returns classical-fallback
    BLOCKED models are skipped in every case.
    """
    routing = spec.get("routing_matrix", {})
    entry = routing.get(task_class) or {}
    if entry.get("tier") == tier_id:
        model = entry.get("model_primary")
        provider = entry.get("provider_primary")
        if model and model not in BLOCKED:
            return {"model": model, "provider": provider, "via": "routing_matrix",
                    "endpoint": _endpoint_for(provider)}
    tier_map = {t["id"]: t for t in spec.get("tiers", []) if isinstance(t, dict) and "id" in t}
    for cls in tier_map.get(tier_id, {}).get("default_classes", []):
        for model, endpoint, _note in POLICY.get(cls, []):
            if model in BLOCKED:
                continue
            return {"model": model, "provider": "policy", "via": "tier.default_classes:%s" % cls,
                    "endpoint": endpoint}
    if entry.get("model_primary") and entry["model_primary"] not in BLOCKED:
        return {"model": entry["model_primary"], "provider": entry.get("provider_primary"),
                "via": "routing_matrix.tier_mismatch", "endpoint": _endpoint_for(entry.get("provider_primary"))}
    return None


def _endpoint_for(provider):
    return ENDPOINTS.get(provider, provider)


def infer_verify_kind(packet):
    """Closed set from registry.verification_kinds. Explicit wins; otherwise the
    strongest artifact shape present wins. 'none' is legal only for a read-only
    packet - a mutating packet always leaves something to open."""
    explicit = packet.get("verify_kind")
    if explicit:
        # An explicit verify_kind is the packet author's decision and it wins.
        # Inference only fills a gap.
        return explicit
    kinds = set()
    artifacts = [a.lower() for a in (packet.get("artifacts_expected") or [])]
    done = [d.lower() for d in (packet.get("done_when") or [])]
    blob = " ".join(artifacts + done)
    for path in artifacts:
        if path.endswith((".png", ".jpg", ".jpeg", ".webp", ".exr")):
            kinds.add("image_look")
        elif path.endswith((".log", ".txt")) and "screenshot" not in path:
            kinds.add("test_log")
        elif path.endswith(".json"):
            kinds.add("artifact_open")
    if any(p.endswith((".md", ".diff", ".patch")) for p in artifacts):
        kinds.add("diff_review")
    if not kinds:
        kinds.add("artifact_open")
    if packet.get("mutation_scope") == "none":
        return "log_cite"
    for pref in ("artifact_open", "test_log", "image_look", "diff_review"):
        if pref in kinds:
            return pref
    return sorted(kinds)[0]


def adjudicate_with_jev(packet, allowed_classes):
    """Optional Jev overlay from the orchestrator plan.

    Closed sets only, one question, and it can never widen a tier. If the SDK is
    absent, the call fails, or the answer falls outside the allowed set, we
    return None and the caller keeps the deterministic answer - or, when the
    packet has no task_class at all, returns classical-fallback. The card goes
    to the owner; it is never auto-dispatched on a guess.
    """
    try:
        from typesafe_sdk import TypeSafeClient  # noqa: F401
    except Exception:
        return None
    try:  # pragma: no cover - depends on an external service + credential
        client = TypeSafeClient()
        answer = client.system_one(packet.get("goal"), {
            "criteria": {"task_class": sorted(allowed_classes)},
        })
    except Exception:
        return None
    if not isinstance(answer, str) or answer not in allowed_classes:
        return None
    return answer


def route_packet(packet, adjudicator="deterministic", schema_ok=True):
    """The whole decision, as a dict. No prints, no exits - so the offline test
    can assert on it."""
    with open(TIERS_SPEC, "r", encoding="utf-8") as fh:
        spec = json.load(fh)

    decision = {
        "packet_id": packet.get("id"),
        "goal": packet.get("goal"),
        "schema_ok": schema_ok,
        "adjudicator": adjudicator,
        "dispatch": False,
        "classical_fallback": False,
        "reasons": [],
        "escalations": [],
        "tier": None,
        "model": None,
        "execution": "none",
        "lane": packet.get("task_class"),
        "needs_editor": False,
        "verify_kind": None,
        "budget_usd": 0.0,
        "artifacts_dir": None,
    }

    if not schema_ok:
        decision["classical_fallback"] = True
        decision["reasons"].append("packet fails Tools/agent_router/task_packet.schema.json")
        return decision

    task_class = packet.get("task_class")
    if not task_class:
        if adjudicator == "jev":
            task_class = adjudicate_with_jev(packet, set(spec.get("routing_matrix", {}).keys()))
            if task_class:
                decision["lane"] = task_class
                decision["adjudicator"] = "jev"
        if not task_class:
            decision["classical_fallback"] = True
            decision["reasons"].append(
                "no task_class and the router does not guess; set task_class to a key of "
                "`python Tools/model_router.py tasks`")
            return decision

    routing = spec.get("routing_matrix", {})
    if task_class not in routing:
        decision["classical_fallback"] = True
        decision["reasons"].append("task_class %r is not in routing_matrix" % task_class)
        return decision

    scope = packet.get("mutation_scope")
    if scope != "none" and not (packet.get("mutation_paths") or []):
        decision["classical_fallback"] = True
        decision["reasons"].append(
            "mutation_scope=%r but mutation_paths is empty; the router cannot tell what "
            "would be written" % scope)
        return decision
    if not (packet.get("done_when") or []):
        decision["classical_fallback"] = True
        decision["reasons"].append("done_when is empty; nothing for a verifier to open")
        return decision

    base_tier = routing[task_class].get("tier", "UNKNOWN")
    tier_id = base_tier

    hits = match_escalations(packet, spec)
    decision["escalations"] = hits
    for hit in hits:
        tier_id = _wider(tier_id, hit["required_tier"])

    needs_editor = scope == "editor" or any(h["id"] == "editor_mutation" for h in hits)
    decision["needs_editor"] = bool(needs_editor)

    if needs_editor and "editor_write" in (packet.get("surfaces") or []):
        pass  # the lease, not the router, is the enforcement point
    if needs_editor and scope != "editor" and any(
            h["id"] == "editor_mutation" for h in hits):
        decision["reasons"].append(
            "editor_mutation fired from inputs/goal but mutation_scope is %r; "
            "escalated anyway" % scope)

    # no_self_certification: a mutating packet is graded above its own tier.
    if scope != "none":
        tier_id = _wider(tier_id, VERIFIER_TIER)
    if scope == "git":
        tier_id = _wider(tier_id, "T0_ARCHITECT")

    if tier_id != base_tier:
        decision["reasons"].append(
            "tier escalated %s -> %s (widest_tier_wins)" % (base_tier, tier_id))

    # Describe the packet fully before any gate can return, so a refusal is still
    # a complete description of what WOULD have run.
    decision["verify_kind"] = infer_verify_kind(packet)
    if decision["verify_kind"] == "none" and scope != "none":
        decision["reasons"].append("verify_kind 'none' is illegal on a mutating packet")

    picked = resolve_model(tier_id, task_class, spec)
    if picked is None:
        decision["classical_fallback"] = True
        decision["reasons"].append("no non-blocked model resolves for tier %s" % tier_id)
        decision["tier"] = tier_id
        return decision

    decision["tier"] = tier_id
    decision["model"] = picked["model"]

    # --- EXECUTABILITY GATE -------------------------------------------------
    # Discovered by running the loop on 2026-10-03: `route` reads the registry's
    # `routing_matrix`, while `run_chat` executes `POLICY`. All 8 routing_matrix
    # classes were missing from POLICY, so `route` answered `dispatch: true` for
    # a card that `run_chat` then killed with KeyError. A dispatch the executor
    # cannot run is worse than a refusal, so refuse here instead.
    if picked["model"] == "deterministic":
        decision["execution"] = "deterministic"
    elif _runnable(task_class):
        decision["execution"] = "chat:%s" % task_class
    else:
        decision["classical_fallback"] = True
        decision["execution"] = "none"
        decision["reasons"].append(
            "REGISTRY DRIFT: task_class %r is in model_tiers.v1.json routing_matrix but has "
            "no runnable candidate in either POLICY or the registry, so `route` would hand it "
            "to `chat` and `chat` could only fail. Run `python Tools/model_router.py audit`."
            % task_class)
        return decision

    if picked["endpoint"] == "local" or tier_id == LOCAL_TIER:
        if not local_endpoint_reachable():
            decision["classical_fallback"] = True
            decision["tier"] = tier_id
            decision["model"] = picked["model"]
            decision["reasons"].append(
                "%s is local-only and %s is not answering; failing loudly instead of "
                "spending a paid endpoint (no_silent_paid_fallback)" % (picked["model"], LOCAL_BASE))
            return decision
        servable = model_is_servable_locally(picked["model"])
        if servable is False:
            decision["classical_fallback"] = True
            decision["reasons"].append(
                "%s is listening but does not have the tag %r. An open port is not a "
                "served model. `ollama pull %s`, or route this elsewhere."
                % (LOCAL_BASE, picked["model"], picked["model"]))
            return decision
        if servable is None:
            decision["reasons"].append(
                "could not query %s/api/tags; assuming the local tag is present" % LOCAL_BASE)
        if packet.get("budget_usd"):
            decision["reasons"].append("budget_usd ignored: local lane costs nothing")

    decision["tier"] = tier_id
    decision["model"] = picked["model"]
    decision["provider"] = picked["provider"]
    decision["endpoint"] = picked["endpoint"]
    decision["model_via"] = picked["via"]
    decision["fallback_model"] = routing[task_class].get("model_fallback")

    tier_map = {t["id"]: t for t in spec.get("tiers", []) if isinstance(t, dict) and "id" in t}
    tier_meta = tier_map.get(tier_id, {})
    cap = packet.get("budget_usd")
    default_budget = tier_meta.get("budget_usd_default", 0.0)
    ceiling = tier_meta.get("budget_usd_max", default_budget)
    if cap is None:
        cap = 0.0 if picked["endpoint"] == "local" else default_budget
    decision["budget_usd"] = round(min(float(cap), float(ceiling)), 4)

    decision["verify_kind"] = infer_verify_kind(packet)
    if decision["verify_kind"] == "none" and scope != "none":
        decision["reasons"].append("verify_kind 'none' is illegal on a mutating packet")

    if packet.get("id"):
        decision["artifacts_dir"] = os.path.join("Saved", "Audit", packet["id"])

    # A git/p4 operation is owner-only by law. The router says so and refuses to
    # dispatch; it does not pretend that is a scheduling problem.
    if scope == "git":
        decision["reasons"].append(
            "git/p4 operations need explicit owner permission; dispatch stays false")
        return decision

    decision["dispatch"] = True
    return decision


def _runnable(task_class):
    """Does this task class have at least one candidate `chat` could actually try?"""
    return [c for c in candidates_for(task_class)
            if c[0] and c[0] not in BLOCKED and c[1]]


def probe_openrouter_models(timeout=45):
    """The live catalogue of model IDs this machine can actually call.

    Discovered 2026-10-03 by running the loop for real: every model named in
    model_tiers.v1.json routing_matrix was absent from the 466-model OpenRouter
    catalogue, because the registry uses bare display names (`gemini-2-5-flash`)
    while the API requires provider-prefixed ids (`google/gemini-2.5-flash`).
    The registry had therefore never been executed against a provider, and `route`
    was dispatching confidently to model ids that do not exist.

    Returns (set_of_ids, None) or (None, error_message).
    """
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        try:
            with open(ROOT_MCP, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for _n, server in data.get("mcpServers", {}).items():
                if "openrouter" in server.get("env", {}).get("OPENAI_BASE_URL", ""):
                    key = server["env"].get("OPENAI_API_KEY", "")
                    break
        except Exception:
            pass
    if not key:
        return None, "no OPENROUTER_API_KEY"
    req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                 headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    return {m.get("id") for m in payload.get("data", [])}, None


def run_audit(json_out=False, probe_models=False):
    """Cross-check the two registries that `route` and `chat` actually use.

    `route` reads `model_tiers.v1.json -> routing_matrix`.
    `chat`  reads `POLICY` in this file.
    Nothing connected them, and for eight days they were completely disjoint:
    every routable class raised KeyError the moment a worker tried to run it.
    This is the check that would have caught it on day one.

    Exit 1 when the registries disagree, so a gate can fail on it.
    """
    if not os.path.exists(TIERS_SPEC):
        sys.exit("tiers spec not found: %s" % TIERS_SPEC)
    with open(TIERS_SPEC, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    matrix = spec.get("routing_matrix", {})
    routable = set(matrix)
    policy_classes = set(POLICY)

    # The defect is EXECUTABILITY, not which table a class lives in. `chat` resolves
    # candidates from POLICY first and from the tier registry second, so a class
    # missing from POLICY is fine as long as the registry can still produce a
    # runnable candidate for it.
    unroutable = sorted(k for k in routable if not _runnable(k))
    not_in_policy = sorted(routable - policy_classes)
    undeclared = sorted(policy_classes - routable)

    # A tier is only a real ceiling if some task class actually sits at it.
    tiers_in_matrix = sorted({r.get("tier") for r in matrix.values()})
    tiers_defined = sorted({t["id"] for t in spec.get("tiers", [])
                            if isinstance(t, dict) and "id" in t})
    tier_gap = sorted(set(tiers_in_matrix) - set(tiers_defined))

    local_up = local_endpoint_reachable()
    local_tags = local_models() if local_up else None

    report = {
        "schema": "melodia.model_router_audit/v1",
        "routing_matrix_classes": len(routable),
        "policy_classes": len(policy_classes),
        "routable_but_not_executable": unroutable,
        "routable_not_in_policy": not_in_policy,
        "executable_but_not_routable": undeclared,
        "tiers_in_matrix": tiers_in_matrix,
        "tiers_defined": tiers_defined,
        "tiers_used_but_undefined": tier_gap,
        "local_tier": {"reachable": local_up, "tags": local_tags,
                       "base_url": LOCAL_BASE},
        "registry_gap_count": len(unroutable) + len(tier_gap),
    }

    if probe_models:
        catalogue, err = probe_openrouter_models()
        named = sorted({r.get(k) for r in matrix.values()
                        for k in ("model_primary", "model_fallback")
                        if r.get(k)})
        if catalogue is None:
            report["model_probe"] = {"ok": False, "detail": err}
        else:
            # 'deterministic' is the sentinel for "no model call", not a model id.
            remote_only = [m for m in named
                           if "/" not in m and m not in catalogue
                           and m != "deterministic"]
            report["model_probe"] = {
                "ok": not remote_only,
                "catalogue_size": len(catalogue),
                "named_by_registry": named,
                "not_callable_as_written": remote_only,
                "detail": ("every bare name must be provider-prefixed for the API; "
                           "see Docs/Production/MODEL_ROUTING_CANON.md"),
            }

    if json_out:
        print(json.dumps(report, indent=2))
        return 1 if (report["registry_gap_count"]
                     or (report.get("model_probe", {}).get("ok") is False)) else 0

    print("=" * 72)
    print(" MODEL ROUTER AUDIT - route and chat must not disagree about what runs")
    print("=" * 72)
    print("\nroute reads  model_tiers.v1.json -> routing_matrix : %d classes"
          % len(routable))
    print("chat  reads  POLICY, then the routing_matrix        : %d classes"
          % len(policy_classes))
    if unroutable:
        print("\nROUTABLE BUT NOT EXECUTABLE  (no runnable candidate at all)")
        for key in unroutable:
            entry = matrix.get(key) or {}
            print("  %-28s tier=%-14s model=%s"
                  % (key, entry.get("tier"), entry.get("model_primary")))
    else:
        print("\nROUTABLE BUT NOT EXECUTABLE: none - every routable class can run")
    if not_in_policy:
        print("\nINFORMATIONAL: routable via the registry, absent from POLICY (%d)"
              % len(not_in_policy))
        print("  " + ", ".join(not_in_policy))
    if undeclared:
        print("\nINFORMATIONAL: in POLICY, not routable from a packet (%d)" % len(undeclared))
        print("  " + ", ".join(undeclared))
    if tier_gap:
        print("\nTIERS USED BUT NOT DEFINED: %s" % ", ".join(tier_gap))
    print("\nLOCAL TIER")
    print("  %s reachable=%s" % (LOCAL_BASE, local_up))
    if local_tags is not None:
        print("  tags pulled: %s" % (", ".join(local_tags) if local_tags
                                      else "NONE - every local packet will refuse"))
    print("\nREGISTRY GAPS: %d" % report["registry_gap_count"])

    if probe_models:
        probe = report.get("model_probe") or {}
        print("\nMODEL ID PROBE (live provider catalogue)")
        if not probe.get("ok") and "detail" in probe and "catalogue_size" not in probe:
            print("  could not probe: %s" % probe["detail"])
        else:
            print("  catalogue size: %s" % probe.get("catalogue_size"))
            print("  models named by the registry that are NOT callable as written: %d"
                  % len(probe.get("not_callable_as_written", [])))
            for model in probe.get("not_callable_as_written", []):
                print("    %-28s bare name; the API needs provider/model" % model)
            if probe.get("not_callable_as_written"):
                print("\n  The registry uses display names; the API needs ids.")
                print("  This is an owner-reviewed registry edit, not an agent's guess.")
    return 1 if (report["registry_gap_count"]
                 or (report.get("model_probe", {}).get("ok") is False)) else 0


def run_route(source, adjudicator="deterministic", json_out=False):
    packet = load_packet(source)
    problems = validate_packet(packet)
    if problems:
        sys.stderr.write("packet schema violations:\n")
        for problem in problems[:20]:
            sys.stderr.write("  - %s\n" % problem)
    decision = route_packet(packet, adjudicator=adjudicator, schema_ok=not problems)
    if json_out:
        print(json.dumps(decision, indent=2, ensure_ascii=False))
        return 0
    print("%s" % decision["packet_id"])
    print("  lane          %s" % decision["lane"])
    print("  tier          %s%s" % (decision["tier"],
                                   "  (classical-fallback)" if decision["classical_fallback"] else ""))
    if decision["model"]:
        print("  model         %s  [%s via %s]" % (decision["model"],
                                                   decision.get("endpoint") or "?",
                                                   decision.get("model_via") or "?"))
    print("  execution     %s" % decision.get("execution", "?"))
    print("  needs_editor  %s" % decision["needs_editor"])
    print("  verify_kind   %s" % decision["verify_kind"])
    print("  budget_usd    %.2f" % decision["budget_usd"])
    print("  dispatch      %s" % decision["dispatch"])
    for reason in decision["reasons"]:
        print("  ! %s" % reason)
    if decision["escalations"]:
        print("  escalations   %s" % ", ".join(
            "%s->%s" % (h["id"], h["required_tier"]) for h in decision["escalations"]))
    # A refusal must be visible to a script, not just to a reader. Exit 2 is the
    # same code the packet schema uses for "refused", deliberately.
    return 2 if decision["classical_fallback"] else 0


def run_route_batch(pattern, adjudicator="deterministic"):
    """Offline determinism harness: route every packet matching a glob and print
    one canonical line each, so two runs can be diffed byte for byte."""
    import glob as _glob
    paths = sorted(_glob.glob(pattern))
    if not paths:
        sys.exit("no packets matched: %s" % pattern)
    for path in paths:
        packet = load_packet(path)
        problems = validate_packet(packet)
        decision = route_packet(packet, adjudicator=adjudicator, schema_ok=not problems)
        print("%-28s %-16s %-12s %-38s editor=%-5s verify=%-13s dispatch=%s" % (
            decision["packet_id"], decision["lane"] or "-",
            decision["tier"] or "-", decision["model"] or "-",
            decision["needs_editor"], decision["verify_kind"], decision["dispatch"]))
    return 0


def _provider_for_endpoint(endpoint):
    """Reverse of ENDPOINTS. `keys` is keyed by PROVIDER NAME, while a candidate
    synthesised from the tier registry carries an endpoint URL, so `keys.get(url)`
    missed and the router reported 'no key' for a provider whose key was present."""
    if endpoint in ("local", "openrouter", "tokenrouter", "bedrock"):
        return endpoint
    for provider, url in ENDPOINTS.items():
        if url == endpoint:
            return provider
    return None


def _key_for(keys, endpoint):
    provider = _provider_for_endpoint(endpoint)
    if provider and keys.get(provider):
        return keys[provider]
    return keys.get(endpoint)


def _is_local_endpoint(endpoint):
    """A loopback endpoint needs no credential.

    The old check was `endpoint != "local"`, which only matched the literal POLICY
    tag. A candidate synthesised from the tier registry carries a full URL
    (`http://127.0.0.1:11434/v1`), so the local lane was asked for an API key it
    does not need and refused to run. Loopback is loopback whatever string the
    registry happens to use.
    """
    if endpoint == "local":
        return True
    try:
        host = urllib.parse.urlparse(endpoint).hostname
    except ValueError:
        return False
    return host in ("127.0.0.1", "localhost", "::1", "0.0.0.0")


def candidates_for(task_class, attempt=0):
    """Ordered (model, endpoint, note) candidates for a task class.

    POLICY is the richer table (primary + hand-ordered fallbacks) and wins when the
    class is in it. For a class that only exists in the tier registry's
    routing_matrix, synthesise candidates from that registry instead of failing.

    Why this exists: `route` reads routing_matrix and `chat` reads POLICY, and for
    eight days the two were completely disjoint. Every routable card dispatched into
    a KeyError. Synthesising from the registry removes the duplication that caused
    the drift, rather than copying eight entries into a second table by hand.
    """
    if task_class in POLICY:
        return POLICY[task_class][attempt:]
    if not os.path.exists(TIERS_SPEC):
        return []
    with open(TIERS_SPEC, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    entry = (spec.get("routing_matrix") or {}).get(task_class)
    if not entry:
        return []
    pairs = [(entry.get("model_primary"), entry.get("provider_primary")),
             (entry.get("model_fallback"), entry.get("provider_fallback"))]
    out = []
    for model, provider in pairs:
        if not model:
            continue
        out.append((model, _endpoint_for(provider),
                    "from model_tiers.v1.json routing_matrix"))
    return out[attempt:]


def run_chat(task_class, prompt, system=None, json_out=False, attempt=0, max_tokens=2000,
             timeout=None):
    keys = load_keys()
    candidates = candidates_for(task_class, attempt)
    last_err = None
    # daemon + production lanes: local first - never silently fall through to paid
    # cloud. Production lanes produce game artifacts; a surprise cloud bill or a
    # network dependency in the content pipeline is a defect, not a fallback.
    if task_class in LOCAL_ONLY_CLASSES:
        candidates = [c for c in candidates if c[1] == "local"]
    for model, endpoint, _note in candidates:
        if model in BLOCKED and attempt == 0:
            continue
        if not _is_local_endpoint(endpoint) and not _key_for(keys, endpoint):
            last_err = "no key for %s" % (endpoint,)
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
        if not _is_local_endpoint(endpoint) and not _key_for(keys, endpoint):
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
    p_tier = sub.add_parser("tier")
    p_tier.add_argument("task_name")
    p_tier.add_argument("--detail", action="store_true")
    sub.add_parser("tasks")
    p_audit = sub.add_parser("audit", help="cross-check routing_matrix against POLICY")
    p_audit.add_argument("--json", dest="json_out", action="store_true")
    p_audit.add_argument("--probe-models", action="store_true",
                         help="call the provider catalogue and report registry models that are not callable")
    p_route = sub.add_parser("route", help="Task Packet -> dispatch decision (H1)")
    p_route.add_argument("packet", help="path to a packet .json, or an inline JSON document")
    p_route.add_argument("--adjudicator", choices=["deterministic", "jev"], default="deterministic",
                         help="deterministic = pure function of packet+registry (default). "
                              "jev = one closed-set system_one call, which can only pick the "
                              "task class, never lower a tier.")
    p_route.add_argument("--json", dest="json_out", action="store_true")
    p_route_batch = sub.add_parser("route-batch", help="route every packet matching a glob")
    p_route_batch.add_argument("glob")
    p_route_batch.add_argument("--adjudicator", choices=["deterministic", "jev"], default="deterministic")

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
    elif args.cmd == "tier":
        pick_task(args.task_name, detail=args.detail)
    elif args.cmd == "tasks":
        list_tasks()
    elif args.cmd == "audit":
        sys.exit(run_audit(json_out=args.json_out, probe_models=args.probe_models))
    elif args.cmd == "route":
        sys.exit(run_route(args.packet, adjudicator=args.adjudicator, json_out=args.json_out))
    elif args.cmd == "route-batch":
        sys.exit(run_route_batch(args.glob, adjudicator=args.adjudicator))



if __name__ == "__main__":
    main()


