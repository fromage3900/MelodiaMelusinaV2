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

Task classes: triage audit code cpp author deep review orchestrator vision

Default model: qwen.qwen3-coder-next on bedrock-mantle (needs AWS_PROFILE=bedrock).
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
    # Ollama exposes an OpenAI-compatible /v1/chat/completions on the same port.
    # Free, offline, and the only lane that works when the network dies. The
    # installed fleet is deepseek-r1:14b + qwen2.5-coder:7b (2026-08-13).
    "ollama": os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
    # bedrock-mantle (2026-08-14) — OpenAI-compatible, so it drops straight into
    # chat() below: same /chat/completions path, same response shape, no adapter.
    # Only auth differs (SigV4, or a Bedrock API key as a bearer token).
    #
    # NOTE THE HOST: `bedrock-mantle.{region}.api.aws`, **not** `.amazonaws.com`.
    # Pointing an OpenAI client at the amazonaws.com host is why Cline failed.
    #
    # This is the lane that actually works on this account. Plain `bedrock-runtime`
    # Converse still returns `ValidationException: Operation not allowed` for every
    # model including Amazon's own Nova — an unexplained account-level quirk — while
    # Mantle serves 55 models happily. Verified live: qwen3-coder-next, kimi-k2.5
    # and deepseek.v3.2 all returned completions with real token counts.
    "mantle": os.environ.get(
        "MELODIA_MANTLE_URL", "https://bedrock-mantle.us-east-1.api.aws/v1"),
}

# --------------------------------------------------------------------------
# Bedrock (added 2026-08-13)
#
# Why: OpenRouter here is a free-tier key. The paid-model daily quota exhausts
# mid-day (Grok/DeepSeek/Mistral start returning 402) and TokenRouter drops out
# sporadically -- both recorded in _SESSION_HANDOFF.md. Every lane that depends
# on this router inherits that wall. Bedrock is billed per token against the
# account, so it has no daily cliff; it is the reliable tail of each chain, not
# the default.
#
# Bedrock is NOT an OpenAI-compatible endpoint, so it does not live in ENDPOINTS
# above. It goes through boto3's Converse API and is adapted back to the
# OpenAI response shape in _bedrock_converse(), so every caller downstream --
# run_chat, run_test, log_usage -- is unchanged.
#
# Model id form depends on the model, and getting it wrong is a hard failure:
#
#   INFERENCE_PROFILE  -> MUST use the `us.` prefix. Anthropic Claude, Meta Llama
#                         and DeepSeek R1. The base id fails with "Invocation of
#                         model ID ... with on-demand throughput isn't supported".
#   ON_DEMAND          -> MUST use the bare id, no prefix. Qwen3 (all variants),
#                         DeepSeek v3.2, openai gpt-oss.
#
# Check with:
#   aws bedrock list-foundation-models --region us-east-1 \
#     --query 'modelSummaries[].{id:modelId,types:inferenceTypesSupported}'
#
# (An earlier version of this comment said every id must be profile-prefixed.
# That was wrong for the Qwen and DeepSeek-v3.2 families -- corrected 2026-08-13
# against the live catalogue.)
#
# Region: profiles are enumerated in us-east-1 (119 models). The account default
# is ca-central-1, which carries only 30 and lacks most of these -- hence the
# explicit override rather than inheriting the CLI default.
BEDROCK_REGION = os.environ.get("MELODIA_BEDROCK_REGION", "us-east-1")

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
    # Local Ollama (free, offline). Confirmed installed 2026-08-13:
    #   deepseek-r1:14b  14.8B Q4_K_M  (131K ctx, reasoning)
    #   qwen2.5-coder:7b 7.6B Q4_K_M  (32K ctx, code/tools)
    "deepseek-r1:14b": (0.0, 0.0),
    "qwen2.5-coder:7b": (0.0, 0.0),
    # Bedrock, us-east-1 on-demand, USD per token. Confirm against
    # https://aws.amazon.com/bedrock/pricing/ before trusting the cost ledger --
    # these are entered by hand and Bedrock pricing changes.
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": (0.000001, 0.000005),
    "us.anthropic.claude-sonnet-4-6": (0.000003, 0.000015),
    "us.meta.llama4-scout-17b-instruct-v1:0": (0.00000017, 0.00000066),
    "us.meta.llama4-maverick-17b-instruct-v1:0": (0.00000024, 0.00000097),
    "us.meta.llama3-3-70b-instruct-v1:0": (0.00000072, 0.00000072),
    # Coder / long-context tier. Read from the AWS Price List API on 2026-08-13
    # (AmazonBedrock, on-demand, USD per 1K tokens -> divided by 1000 here), not
    # from memory. Re-check with:
    #   aws pricing get-products --service-code AmazonBedrock --region us-east-1
    "qwen.qwen3-coder-next": (0.0000006, 0.0000012),   # measured 2026-08-14
    "qwen.qwen3-coder-30b-a3b-v1:0": (0.0000002, 0.0000007),  # input est.; only batch input was listed
    "qwen.qwen3-next-80b-a3b": (0.0000000721, 0.00000141),
    "deepseek.v3.2": (0.00000074, 0.00000222),
    # bedrock-mantle ids. Prices READ FROM the AWS Price List API 2026-08-14
    # (AmazonBedrock on-demand, per 1K tokens -> per token here), replacing the
    # hand-entered estimates that were here before. Mantle ids drop the `us.`
    # prefix and the `-v1:0` suffix that bedrock-runtime uses.
    "qwen.qwen3-coder-480b-a35b-instruct": (0.00000047, 0.00000185),
    "qwen.qwen3-coder-30b-a3b-instruct": (0.0000002, 0.0000007),
    "qwen.qwen3-235b-a22b-2507": (0.00000026, 0.00000161),
    "mistral.devstral-2-123b": (0.0000004, 0.000002),   # not in Price List; still an estimate
    "moonshotai.kimi-k2.5": (0.0000006, 0.0000025),     # not in Price List; still an estimate
    "moonshotai.kimi-k2-thinking": (0.0000006, 0.0000025),  # ditto
    # Cheap tier -- an order of magnitude below the coders, for high-volume
    # mechanical work (log triage, doc sweeps, first-pass classification).
    "openai.gpt-oss-20b": (0.00000008, 0.00000036),
    "openai.gpt-oss-120b": (0.00000009, 0.00000093),
    "zai.glm-4.7-flash": (0.00000008, 0.0000004),
    "google.gemma-3-12b-it": (0.00000011, 0.00000035),
    # Frontier tier
    "zai.glm-5": (0.000001, 0.00000384),
    "minimax.minimax-m2": (0.00000018, 0.00000141),
    "qwen.qwen3-vl-235b-a22b": (0.00000026, 0.00000161),
    "us.deepseek.r1-v1:0": (0.00000135, 0.00000135),          # output not listed; mirrored input
}

BLOCKED = {"meta/muse-spark-1.2": "requires 18+ confirmation at openrouter.ai/settings/preferences"}

POLICY = {
    "triage": [
        ("deepseek-r1:14b", "ollama", "local reasoning, offline"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free 1M ctx"),
        ("openai/gpt-oss-20b:free", "openrouter", "free code"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "slow but strong fallback"),
        ("us.meta.llama4-scout-17b-instruct-v1:0", "bedrock", "reliable tail: cheap, fast, no daily wall"),
    ],
    "audit": [
        ("deepseek-r1:14b", "ollama", "local reasoning, offline"),
        ("nvidia/nemotron-3-ultra-550b-a55b:free", "openrouter", "free heavy"),
        ("deepseek/deepseek-v4-flash", "openrouter", "analysis"),
        ("meta/muse-spark-1.2", "openrouter", "gamedev-ranked"),
        ("us.anthropic.claude-sonnet-4-6", "bedrock", "reliable tail: strong analysis"),
    ],
    # Qwen3 Coder Next is the DEFAULT coder (2026-08-14). It leads rather than the
    # local model because Ollama cold-starts a model on first use -- on this box that
    # exceeded the remote timeout and made the first call of a session cost minutes.
    # Local stays as the offline fallback, which is what it is actually good for.
    "code": [
        ("qwen.qwen3-coder-next", "mantle", "DEFAULT: coder-tuned, long ctx, verified"),
        ("qwen.qwen3-coder-480b-a35b-instruct", "mantle", "heavier coder"),
        ("qwen2.5-coder:7b", "ollama", "offline fallback, free"),
        ("deepseek/deepseek-v4-flash", "openrouter", "free-tier fallback"),
    ],
    "author": [
        ("deepseek-r1:14b", "ollama", "local reasoning, offline"),
        ("mistralai/mistral-medium-3-5", "openrouter", "creative/agentic frontier"),
        ("moonshotai/kimi-k3-free", "tokenrouter", "free fallback"),
        ("us.anthropic.claude-sonnet-4-6", "bedrock", "reliable tail: creative"),
    ],
    "deep": [
        ("moonshotai.kimi-k2-thinking", "mantle", "VERIFIED family: long complex reasoning"),
        ("moonshotai.kimi-k2.5", "mantle", "VERIFIED 2026-08-14"),
        ("qwen.qwen3-235b-a22b-2507", "mantle", "large general"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
    ],
    "review": [
        ("deepseek-r1:14b", "ollama", "local reasoning, offline"),
        ("x-ai/grok-4.5", "openrouter", "fresh-eyes verifier"),
        ("meta/muse-spark-1.2", "openrouter", "multimodal review"),
        ("mistralai/mistral-medium-3-5", "openrouter", "frontier fallback"),
        ("us.anthropic.claude-sonnet-4-6", "bedrock", "reliable tail: fresh-eyes verifier"),
    ],
    "orchestrator": [
        ("deepseek-r1:14b", "ollama", "local reasoning, offline"),
        ("x-ai/grok-4.20-multi-agent", "openrouter", "multi-agent orchestration"),
        ("x-ai/grok-4.5", "openrouter", "frontier fallback"),
        ("us.anthropic.claude-sonnet-4-6", "bedrock", "reliable tail: orchestration"),
    ],
    # Long C++/engine work. The LOCAL coder leads now: qwen2.5-coder:7b is free,
    # offline and fast on the 4070 SUPER. Bedrock Qwen3-Coder Next is the strong
    # paid tail when the local model either isn't installed or lacks the depth
    # for a hard engine refactor. The chain never burns a paid call when the
    # free local lane solves it.
    "cpp": [
        ("qwen.qwen3-coder-next", "mantle", "VERIFIED 2026-08-14: coder, long ctx"),
        ("qwen.qwen3-coder-480b-a35b-instruct", "mantle", "bigger coder"),
        ("deepseek.v3.2", "mantle", "VERIFIED: reasoning coder"),
        ("mistral.devstral-2-123b", "mantle", "code specialist"),
        ("deepseek/deepseek-v4-flash", "openrouter", "free-tier last resort"),
    ],
    "vision": [
        ("mistralai/mistral-medium-3-5", "openrouter", "screenshot review"),
        ("meta/muse-spark-1.2", "openrouter", "video input (age-confirm first)"),
        ("us.meta.llama4-maverick-17b-instruct-v1:0", "bedrock", "reliable tail: Meta multimodal"),
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

    # Bedrock authenticates with IAM, not a bearer token, so there is no key to
    # load. run_chat() gates every candidate on `keys.get(endpoint)`, so put a
    # truthy sentinel there only when a call could actually succeed -- otherwise
    # the chain would stall on Bedrock instead of falling through.
    reason = _bedrock_unavailable_reason()
    keys["bedrock"] = "" if reason else "iam"
    keys["_bedrock_reason"] = reason

    # Ollama needs no bearer token, but it must be reachable or the chain would
    # stall. A truthy sentinel means "try it"; a connection error simply falls
    # through to the next candidate like every other endpoint (cheap, local).
    keys["ollama"] = "local" if _ollama_reachable() else ""

    # mantle accepts EITHER a Bedrock API key (bearer) or SigV4, so it is usable
    # whenever either exists. A bearer token alone is enough -- it needs no boto3
    # and no configured profile, which is why it is checked first.
    keys["mantle"] = "bearer" if os.environ.get("AWS_BEARER_TOKEN_BEDROCK") else (
        "" if _bedrock_unavailable_reason() else "sigv4")
    return keys


def _ollama_reachable():
    """Cheap liveness probe for the local Ollama server (no model invoked)."""
    try:
        import socket  # noqa: PLC0415
        port = int(os.environ.get("OLLAMA_PORT", "11434"))
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except Exception:
        return False


def _bedrock_unavailable_reason():
    """Return a human-readable reason Bedrock cannot be used, or "" if it can.

    Deliberately does NOT invoke a model -- that costs money and this runs on
    every router call. It checks only that the SDK is importable and that
    credentials resolve at all.
    """
    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return "boto3 not installed (pip install boto3)"
    try:
        session = boto3.session.Session()
        if session.get_credentials() is None:
            return "no AWS credentials (run: aws login)"
    except Exception as exc:  # noqa: BLE001
        return "AWS session error: %s" % exc
    return ""


def _bedrock_converse(model, prompt, system=None, max_tokens=2000, temperature=0.2,
                      request_timeout=REQUEST_TIMEOUT):
    """Invoke Bedrock via Converse and return an OpenAI-shaped response.

    Converse (not InvokeModel) because it gives one request/response shape across
    Anthropic, Meta and Nova; InvokeModel needs a different body per provider and
    getting it wrong yields "Malformed input request".

    `maxTokens` is always sent explicitly. Leaving it unset defaults to the
    model's maximum and silently reserves that much quota, which is the usual
    cause of surprise ThrottlingException.
    """
    import boto3  # noqa: PLC0415
    from botocore.config import Config  # noqa: PLC0415

    client = boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=Config(
            read_timeout=request_timeout,
            connect_timeout=10,
            # Adaptive backs off on ThrottlingException instead of hammering.
            retries={"max_attempts": 5, "mode": "adaptive"},
        ),
    )
    kwargs = {
        "modelId": model,
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        kwargs["system"] = [{"text": system}]
        # Prompt caching: mark the system prompt as a cache point. Every lane
        # re-sends AGENTS.md + the working agreement on each call; Anthropic is
        # the one Bedrock family that honours cache points through Converse
        # (Qwen/DeepSeek/Nova ignore the field). Cache reads bill ~90% less.
        # This is a 1-token write per call; it cannot make anything worse.
        if model.startswith("us.anthropic."):
            kwargs["system"].append({"cachePoint": {"type": "default"}})

    resp = client.converse(**kwargs)

    text = "".join(
        block.get("text", "")
        for block in resp.get("output", {}).get("message", {}).get("content", [])
    )
    usage = resp.get("usage", {})
    # Adapt to the OpenAI shape every caller in this file already expects, so
    # run_chat/run_test/log_usage need no Bedrock-specific branches.
    return {
        "model": model,
        "choices": [{"message": {"content": text}}],
        "usage": {
            "prompt_tokens": usage.get("inputTokens", 0),
            "completion_tokens": usage.get("outputTokens", 0),
        },
    }


def chat(model, endpoint, prompt, keys, system=None, max_tokens=2000, temperature=0.2,
         request_timeout=REQUEST_TIMEOUT):
    if endpoint == "bedrock":
        return _bedrock_converse(model, prompt, system=system, max_tokens=max_tokens,
                                 temperature=temperature, request_timeout=request_timeout)
    # Local Ollama cold-starts a model on first use — on Windows the llama-server
    # load + GPU copy can exceed the 90s remote timeout. Give the local lane 3x.
    if endpoint == "ollama":
        request_timeout = max(request_timeout, 180)
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

    if endpoint == "mantle":
        headers = _mantle_auth_headers(url, data)
    else:
        headers = {
            "Authorization": "Bearer " + keys[endpoint],
            "Content-Type": "application/json",
        }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=request_timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _mantle_auth_headers(url, data):
    """Auth headers for bedrock-mantle: Bedrock API key if present, else SigV4.

    Both are supported by the endpoint. The bearer path is preferred when
    AWS_BEARER_TOKEN_BEDROCK is set because it needs no signing and is what the
    OpenAI SDK / Cline / OpenCode use. SigV4 is the fallback so the router works
    from a plain `aws configure` profile with no extra key to manage.

    The signing service name is **`bedrock`**, not `bedrock-mantle` -- the IAM
    *action* namespace is `bedrock-mantle:*` but the SigV4 service is `bedrock`.
    Getting that wrong yields a signature mismatch that reads like bad credentials.
    """
    token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")
    if token:
        return {"Authorization": "Bearer " + token,
                "Content-Type": "application/json"}

    import boto3  # noqa: PLC0415
    from botocore.auth import SigV4Auth  # noqa: PLC0415
    from botocore.awsrequest import AWSRequest  # noqa: PLC0415

    region = ENDPOINTS["mantle"].split("bedrock-mantle.")[1].split(".api.aws")[0]
    creds = boto3.session.Session().get_credentials().get_frozen_credentials()
    signed = AWSRequest(method="POST", url=url, data=data,
                        headers={"Content-Type": "application/json"})
    SigV4Auth(creds, "bedrock", region).add_auth(signed)
    return dict(signed.headers)


def log_usage(task_class, model, endpoint, usage, ok=True, error=None):
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
        # Failure reasons were never recorded -- only ok:false -- which forced
        # every diagnosis to live probes. Truncate so a wall of 402 text or a
        # stack trace cannot balloon the ledger.
        if error is not None:
            row["error"] = str(error)[:300]
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
            last_err = (keys.get("_bedrock_reason") if endpoint in ("bedrock", "mantle")
                        else None) or "no key for %s" % endpoint
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
            log_usage(task_class, model, endpoint, None, ok=False, error=last_err)
        except Exception as exc:
            last_err = "%s after %.0fs" % (exc, time.time() - started)
            log_usage(task_class, model, endpoint, None, ok=False, error=last_err)
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
            why = (keys.get("_bedrock_reason") if endpoint in ("bedrock", "mantle")
                   else None) or "no key for %s" % endpoint
            print("  SKIP %-40s %s" % (model, why))
            continue
        try:
            result = chat(model, endpoint, "Reply with exactly: OK", keys, max_tokens=10)
            usage = result.get("usage")
            log_usage("health", model, endpoint, usage)
            print("  PASS %-40s %s" % (model, note))
        except Exception as exc:
            ok_all = False
            log_usage("health", model, endpoint, None, ok=False, error=exc)
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
        err = " " + row["error"][:60] if row.get("error") else ""
        print("%s %-5s %-40s in=%-7d out=%-7d $%.6f %s%s" % (
            row["ts"], row["class"], row["model"], row["in"], row["out"],
            row["cost_usd"], "OK" if row["ok"] else "FAIL", err))
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
