#!/usr/bin/env python3
"""Minimal OpenRouter chat helper for model eval lanes (Muse Spark, fallbacks)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OPENROUTER_URL = os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions").rstrip("/")
MUSE_PRIMARY = os.environ.get("MUSE_MODEL", "meta/muse-spark-1.2")
MUSE_FALLBACK = os.environ.get("MUSE_FALLBACK_MODEL", "deepseek/deepseek-v4-flash")


def _resolve_key() -> str | None:
    for name in ("OPENROUTER_API_KEY", "MUSE_API_KEY", "TOKENROUTER_API_KEY", "KIMIFREE_OPENROUTER_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def _headers(key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "https://github.com/MelodiaGame/Melusina"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "Melodia Hermes MATH Eval"),
    }


def chat(
    user: str,
    *,
    system: str,
    model: str | None = None,
    timeout: float = 90.0,
    temperature: float = 0.0,
    max_tokens: int = 256,
) -> tuple[str, str | None, str]:
    """Return (content, error, model_used)."""
    key = _resolve_key()
    if not key:
        return "", "OPENROUTER_API_KEY unset", model or MUSE_PRIMARY
    chosen = model or MUSE_PRIMARY
    payload: dict[str, Any] = {
        "model": chosen,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(key),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return "", str(exc), chosen
    if isinstance(body.get("error"), dict):
        err = str(body["error"].get("message") or body["error"])
        if chosen == MUSE_PRIMARY and model is None:
            fb_text, fb_err, fb_model = chat(
                user,
                system=system,
                model=MUSE_FALLBACK,
                timeout=timeout,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if fb_text:
                return fb_text, None, fb_model
            return "", fb_err or err, fb_model
        return "", err, chosen
    choices = body.get("choices") or []
    if not choices:
        return "", "empty choices", chosen
    msg = (choices[0].get("message") or {}).get("content") or ""
    return str(msg), None, chosen


def probe_muse(timeout: float = 20.0) -> dict[str, Any]:
    """Lightweight connectivity check for Muse / OpenRouter lane."""
    text, err, model = chat(
        "Reply with exactly: OK",
        system="Reply with one word only.",
        timeout=timeout,
        max_tokens=8,
    )
    return {
        "ok": bool(text) and not err,
        "model": model,
        "sample": (text or err or "")[:120],
        "has_key": bool(_resolve_key()),
    }
