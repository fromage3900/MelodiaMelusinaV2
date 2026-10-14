"""Anthropic Messages API -> Nous Portal (OpenAI chat completions) translating proxy.

Lets the `claude` CLI (which only speaks /v1/messages) run against Nous Portal.
Stdlib only. Binds 127.0.0.1 only. The Nous key is re-read from Hermes' auth.json
on EVERY request because it is short-lived and Hermes rotates it.

Env:
  NOUS_PROXY_PORT     listen port (default 47821)
  NOUS_MODEL          upstream model id (default: model.default from Hermes config.yaml)
  NOUS_AUTH_JSON      path to Hermes auth.json
  NOUS_REFRESH_CMD    shell command run when the key is expired (default: Hermes' own
                      resolve_nous_runtime_credentials(force_refresh=True) via its venv)
  PROXY_UPSTREAM      "nous" (default) or "gemini"; runtime-switchable via POST /set_upstream
  GEMINI_API_KEY      Gemini key for the gemini upstream (fallback: %LOCALAPPDATA%\\hermes\\gemini_api_key.txt)

Gemini upstream speaks Google's OpenAI-compatible surface
(https://generativelanguage.googleapis.com/v1beta/openai) so the existing
Anthropic->OpenAI translation is reused unchanged; the key is re-read per request.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("NOUS_PROXY_PORT", "47821"))
HERMES_HOME = os.path.expanduser("~/AppData/Local/hermes")
AUTH_JSON = os.environ.get("NOUS_AUTH_JSON", os.path.join(HERMES_HOME, "auth.json"))
HERMES_CONFIG = os.path.join(HERMES_HOME, "config.yaml")
_HERMES_EXE = os.path.join(HERMES_HOME, "bin", "hermes.exe")
_HERMES_PY = os.path.join(HERMES_HOME, "hermes-agent", "venv", "Scripts", "python.exe")
_HERMES_REFRESH = ('"%s" auth refresh nous' % _HERMES_EXE) if os.path.exists(_HERMES_EXE) else (
    ('"%s" -c "from hermes_cli.auth import resolve_nous_runtime_credentials as r; '
     'r(timeout_seconds=30, force_refresh=True)"' % _HERMES_PY) if os.path.exists(_HERMES_PY) else "")
REFRESH_CMD = os.environ.get("NOUS_REFRESH_CMD") or _HERMES_REFRESH
_refresh_lock = threading.Lock()
ACTIVE_MODEL_FILE = os.path.join(HERMES_HOME, "active_proxy_model.txt")
UPSTREAM_FILE = os.path.join(HERMES_HOME, "active_proxy_upstream.txt")
GEMINI_KEY_FILE = os.path.join(HERMES_HOME, "gemini_api_key.txt")
GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
UPSTREAMS = ("nous", "gemini")


def current_upstream():
    """Active upstream: state file wins, then env, else nous."""
    try:
        val = open(UPSTREAM_FILE, encoding="utf-8-sig").read().strip().lstrip("\ufeff").lower()
        if val in UPSTREAMS:
            return val
    except OSError:
        pass
    env = os.environ.get("PROXY_UPSTREAM", "").strip().lower()
    return env if env in UPSTREAMS else "nous"


def default_model():
    if os.path.exists(ACTIVE_MODEL_FILE):
        try:
            with open(ACTIVE_MODEL_FILE, "r", encoding="utf-8-sig") as f:
                val = f.read().strip().lstrip("\ufeff")
                if val:
                    return val
        except OSError:
            pass
    if os.environ.get("NOUS_MODEL"):
        return os.environ["NOUS_MODEL"]
    try:
        text = open(HERMES_CONFIG, encoding="utf-8").read()
        m = re.search(r"^model:\s*\n\s+default:\s*(\S+)", text, re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    return "stepfun/step-5-preview:free"


def _expired(nous):
    raw = nous.get("agent_key_expires_at")
    if not raw:
        return False
    try:
        return datetime.fromisoformat(raw).timestamp() < time.time() + 60
    except ValueError:
        return False


def load_credentials():
    """Return (key, base_url). The Gemini branch reads its key per request; the Nous
    branch runs REFRESH_CMD once if the short-lived agent key is expired."""
    if current_upstream() == "gemini":
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            try:
                key = open(GEMINI_KEY_FILE, encoding="utf-8-sig").read().strip().lstrip("\ufeff")
            except OSError:
                key = ""
        if not key:
            raise PermissionError(
                "gemini upstream selected but no GEMINI_API_KEY (env or %s). "
                "Run Scripts\\nous_proxy\\set_gemini_key.ps1 once." % GEMINI_KEY_FILE)
        return key, GEMINI_OPENAI_BASE

    def read():
        nous = json.load(open(AUTH_JSON, encoding="utf-8"))["providers"]["nous"]
        return nous["agent_key"], nous["inference_base_url"].rstrip("/"), nous
    key, base, nous = read()
    if _expired(nous) and REFRESH_CMD:
        with _refresh_lock:
            key, base, nous = read()
            if _expired(nous):
                subprocess.run(REFRESH_CMD, shell=True, timeout=120, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                key, base, nous = read()
    if _expired(nous):
        raise PermissionError(
            "Nous agent key expired at %s. Automatic refresh failed; run Hermes once or set NOUS_REFRESH_CMD."
            % nous.get("agent_key_expires_at"))
    return key, base


# ---------------------------------------------------------------- request translation
def _text_of(content):
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if b.get("type") == "text")


def _tool_result_text(content):
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    return content if isinstance(content, str) else json.dumps(content)


def to_openai(req, model):
    msgs = []
    if req.get("system"):
        msgs.append({"role": "system", "content": _text_of(req["system"])})
    for m in req.get("messages", []):
        c = m["content"]
        if isinstance(c, str):
            msgs.append({"role": m["role"], "content": c})
            continue
        if m["role"] == "assistant":
            text = "".join(b.get("text", "") for b in c if b["type"] == "text")
            calls = []
            for b in c:
                if b["type"] != "tool_use":
                    continue
                call = {"id": b["id"], "type": "function",
                        "function": {"name": b["name"], "arguments": json.dumps(b.get("input", {}))}}
                sig = _SIGS.get(b["id"])
                if sig:
                    call["extra_content"] = {"google": {"thought_signature": sig}}
                calls.append(call)
            out = {"role": "assistant", "content": text or None}
            if calls:
                out["tool_calls"] = calls
            msgs.append(out)
        else:
            # tool results must directly follow the assistant tool_calls message
            for b in c:
                if b["type"] == "tool_result":
                    msgs.append({"role": "tool", "tool_call_id": b["tool_use_id"],
                                 "content": _tool_result_text(b.get("content", ""))})
            parts = []
            for b in c:
                if b["type"] == "text":
                    parts.append({"type": "text", "text": b["text"]})
                elif b["type"] == "image" and b.get("source", {}).get("type") == "base64":
                    s = b["source"]
                    parts.append({"type": "image_url", "image_url": {
                        "url": "data:%s;base64,%s" % (s["media_type"], s["data"])}})
            if parts:
                msgs.append({"role": "user", "content": parts if len(parts) > 1 or parts[0]["type"] != "text" else parts[0]["text"]})
    out = {"model": model, "messages": msgs, "stream": bool(req.get("stream"))}
    for src, dst in (("max_tokens", "max_tokens"), ("temperature", "temperature"), ("top_p", "top_p")):
        if src in req:
            out[dst] = req[src]
    if req.get("stop_sequences"):
        out["stop"] = req["stop_sequences"]
    if req.get("tools"):
        out["tools"] = [{"type": "function", "function": {
            "name": t["name"], "description": t.get("description", ""),
            "parameters": t.get("input_schema", {"type": "object", "properties": {}})}}
            for t in req["tools"]]
        tc = req.get("tool_choice") or {}
        kind = tc.get("type")
        if kind == "any":
            out["tool_choice"] = "required"
        elif kind == "tool":
            out["tool_choice"] = {"type": "function", "function": {"name": tc["name"]}}
        elif kind == "none":
            out["tool_choice"] = "none"
    if out["stream"] and current_upstream() != "gemini":
        # stream_options is OpenAI-specific; Google's OpenAI-compat surface may reject it.
        out["stream_options"] = {"include_usage": True}
    return out


STOP = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use", "function_call": "tool_use"}

# Gemini thinking models attach a thought_signature to each functionCall; Google
# rejects the follow-up turn unless it is echoed back. Claude Code cannot carry
# the field (Anthropic tool_use has no slot for it), so the proxy caches it by
# tool_call id and replays it on the outbound assistant history. Nous never sets
# extra_content.google, so this cache stays empty on the Nous path.
_SIGS = {}
_SIGS_ORDER = []
_SIGS_LOCK = threading.Lock()
_SIG_MAX = 1024


def _remember_sig(tool_id, sig):
    if not tool_id or not sig:
        return
    with _SIGS_LOCK:
        if tool_id in _SIGS:
            _SIGS_ORDER.remove(tool_id)
        _SIGS[tool_id] = sig
        _SIGS_ORDER.append(tool_id)
        while len(_SIGS_ORDER) > _SIG_MAX:
            _SIGS.pop(_SIGS_ORDER.pop(0), None)


def _sig_of_tool_call(tc):
    return ((tc.get("extra_content") or {}).get("google") or {}).get("thought_signature")


def _args(raw):
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        return {}


def to_anthropic(resp, model):
    ch = resp["choices"][0]
    msg = ch["message"]
    blocks = []
    if msg.get("content"):
        blocks.append({"type": "text", "text": msg["content"]})
    for tc in msg.get("tool_calls") or []:
        _remember_sig(tc.get("id"), _sig_of_tool_call(tc))
        blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"],
                       "input": _args(tc["function"].get("arguments"))})
    u = resp.get("usage") or {}
    return {"id": "msg_" + uuid.uuid4().hex[:24], "type": "message", "role": "assistant",
            "model": model, "content": blocks or [{"type": "text", "text": ""}],
            "stop_reason": STOP.get(ch.get("finish_reason"), "end_turn"), "stop_sequence": None,
            "usage": {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0)}}


# ---------------------------------------------------------------- HTTP server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    model = None

    def log_message(self, fmt, *a):
        sys.stderr.write("[nous-proxy] " + fmt % a + "\n")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg, kind="api_error"):
        self._json(code, {"type": "error", "error": {"type": kind, "message": msg}})

    def _sse(self, event, data):
        self.wfile.write(("event: %s\ndata: %s\n\n" % (event, json.dumps(data))).encode())
        self.wfile.flush()

    def get_model(self):
        return default_model()

    def do_GET(self):
        if self.path.startswith("/v1/models"):
            self._json(200, {"data": [{"id": self.get_model(), "type": "model"}], "has_more": False})
        else:
            self._json(200, {"status": "ok", "upstream": current_upstream(),
                             "upstream_model": self.get_model()})

    do_HEAD = do_GET

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        req = json.loads(self.rfile.read(n) or b"{}")
        path = self.path.split("?")[0]
        if path.endswith("/set_upstream"):
            up = (req.get("upstream") or "").strip().lower()
            if up not in UPSTREAMS:
                return self._err(400, "upstream must be one of %s" % "|".join(UPSTREAMS))
            with open(UPSTREAM_FILE, "w", encoding="utf-8") as f:
                f.write(up)
            model = (req.get("model") or "").strip()
            if model:
                with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
                    f.write(model.lstrip("﻿"))
            return self._json(200, {"status": "ok", "upstream": current_upstream(),
                                    "upstream_model": self.get_model()})
        if path.endswith("/set_model"):
            new_m = req.get("model", "").strip()
            if new_m:
                with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
                    f.write(new_m.strip().lstrip("﻿"))
                self.model = new_m
                return self._json(200, {"status": "ok", "upstream_model": new_m})
            return self._err(400, "missing model parameter")
        if path.endswith("/count_tokens"):
            est = len(json.dumps(req.get("messages", []))) // 4 + len(json.dumps(req.get("system", ""))) // 4
            return self._json(200, {"input_tokens": max(est, 1)})
        if not path.endswith("/v1/messages"):
            return self._err(404, "unsupported path " + path, "not_found_error")
        try:
            key, base = load_credentials()
        except Exception as e:  # noqa: BLE001
            return self._err(401, str(e), "authentication_error")
        current_model = self.get_model()
        body = to_openai(req, current_model)
        up = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(),
                                    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            r = urllib.request.urlopen(up, timeout=600)
        except urllib.error.HTTPError as e:
            raw_err = e.read()[:500].decode("utf-8", "replace")
            sys.stderr.write("[nous-proxy] Upstream error %d for model %s: %s\n" % (e.code, current_model, raw_err))
            return self._err(e.code, raw_err)
        except Exception as e:  # noqa: BLE001
            return self._err(502, "upstream failure: %s" % e)
        if not body["stream"]:
            return self._json(200, to_anthropic(json.load(r), current_model))
        self.stream(r, current_model)

    def stream(self, r, model=None):
        active = model or self.get_model()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        self._sse("message_start", {"type": "message_start", "message": {
            "id": "msg_" + uuid.uuid4().hex[:24], "type": "message", "role": "assistant", "model": active,
            "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}}})
        nxt = 0          # next anthropic block index
        text_idx = None  # open text block
        tools = {}       # openai tool index -> anthropic block index
        tool_ids = {}    # openai tool index -> tool_call id
        sigs = {}        # openai tool index -> thought_signature (gemini)
        finish, usage = "stop", {}

        def close_text():
            nonlocal text_idx
            if text_idx is not None:
                self._sse("content_block_stop", {"type": "content_block_stop", "index": text_idx})
                text_idx = None

        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                ev = json.loads(payload)
            except ValueError:
                continue
            if ev.get("usage"):
                usage = ev["usage"]
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                if d.get("content"):
                    if text_idx is None:
                        text_idx, nxt = nxt, nxt + 1
                        self._sse("content_block_start", {"type": "content_block_start", "index": text_idx,
                                                          "content_block": {"type": "text", "text": ""}})
                    self._sse("content_block_delta", {"type": "content_block_delta", "index": text_idx,
                                                      "delta": {"type": "text_delta", "text": d["content"]}})
                for tc in d.get("tool_calls") or []:
                    i = tc.get("index", 0)
                    if tc.get("id"):
                        tool_ids[i] = tc["id"]
                    sig = _sig_of_tool_call(tc)
                    if sig:
                        sigs[i] = sig
                    if i not in tools:
                        close_text()
                        tools[i], nxt = nxt, nxt + 1
                        self._sse("content_block_start", {"type": "content_block_start", "index": tools[i],
                                                          "content_block": {"type": "tool_use",
                                                                            "id": tc.get("id") or "toolu_" + uuid.uuid4().hex[:20],
                                                                            "name": (tc.get("function") or {}).get("name", ""),
                                                                            "input": {}}})
                    frag = (tc.get("function") or {}).get("arguments")
                    if frag:
                        self._sse("content_block_delta", {"type": "content_block_delta", "index": tools[i],
                                                          "delta": {"type": "input_json_delta", "partial_json": frag}})
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
        close_text()
        for idx in tools.values():
            self._sse("content_block_stop", {"type": "content_block_stop", "index": idx})
        for idx, tid in tool_ids.items():
            _remember_sig(tid, sigs.get(idx))
        self._sse("message_delta", {"type": "message_delta",
                                    "delta": {"stop_reason": STOP.get(finish, "end_turn"), "stop_sequence": None},
                                    "usage": {"output_tokens": usage.get("completion_tokens", 0)}})
        self._sse("message_stop", {"type": "message_stop"})


def main():
    Handler.model = default_model()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)  # loopback ONLY
    sys.stderr.write("[nous-proxy] 127.0.0.1:%d -> Nous model %s\n" % (PORT, Handler.model))
    srv.serve_forever()


if __name__ == "__main__":
    main()
