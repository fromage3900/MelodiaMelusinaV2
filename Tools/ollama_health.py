#!/usr/bin/env python3
"""Read-only Ollama capability preflight for the Melodia local-model lanes.

The port being open is not enough: a worker can still fail because its model tag
is missing. This probe checks the API, records the installed model inventory,
and verifies the model assignments used by the local content fleet.

Usage:
    python Tools/ollama_health.py
    python Tools/ollama_health.py --write-evidence
    python Tools/ollama_health.py --json
    python Tools/ollama_health.py --offline
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
EVIDENCE_PATH = ROOT / "Saved" / "Integration" / "ollama_health.json"

# Keep this list small and explicit. It is the contract for the local fleet;
# optional models may exist without becoming a hidden runtime dependency.
LANE_MODELS = {
    "reasoning": "deepseek-r1:14b",
    "code": "qwen2.5-coder:7b",
    "heavy_code": "qwen2.5-coder:14b",
    "general": "qwen2.5-coder:7b",
    "creative": "deepseek-r1:14b",
}

LANE_FALLBACKS = {
    "reasoning": ["deepseek-r1:14b", "deepseek-r1:7b", "deepseek-coder:6.7b"],
    "code": ["qwen2.5-coder:7b", "qwen2.5-coder:14b"],
    "heavy_code": ["qwen2.5-coder:14b", "qwen3.8-27b:latest", "qwen2.5-coder:7b"],
    "general": ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "hermes3:latest"],
    "creative": ["deepseek-r1:14b", "deepseek-r1:7b", "qwen2.5-coder:7b"],
}


class OllamaProbeError(RuntimeError):
    """Raised when the local Ollama API cannot provide a valid response."""


def _request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    body = None
    headers: dict[str, str] = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OllamaProbeError(str(exc)) from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OllamaProbeError(f"invalid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OllamaProbeError(f"expected JSON object from {path}")
    return value


def _model_name(entry: dict[str, Any]) -> str:
    return str(entry.get("name") or entry.get("model") or "").strip()


def probe(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 5.0,
    allow_offline_cache: bool = False,
) -> dict[str, Any]:
    """Return a JSON-serializable, fail-closed health report."""
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report: dict[str, Any] = {
        "schema": "melodia_ollama_health_v1",
        "checked_at_utc": checked_at,
        "base_url": base_url,
        "reachable": False,
        "version": None,
        "models": [],
        "lanes": {},
        "missing_models": [],
        "healthy": False,
        "error": None,
    }

    try:
        version = _request_json(base_url, "/api/version", timeout=timeout)
        tags = _request_json(base_url, "/api/tags", timeout=timeout)
    except OllamaProbeError as exc:
        if allow_offline_cache and EVIDENCE_PATH.exists():
            try:
                cached = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
                if isinstance(cached, dict) and cached.get("schema") == "melodia_ollama_health_v1":
                    cached["offline_cached"] = True
                    cached["reachable"] = False
                    cached["healthy"] = False
                    cached["checked_at_utc"] = checked_at
                    cached["error"] = str(exc)
                    return cached
            except Exception:
                pass
        report["error"] = str(exc)
        return report

    raw_models = tags.get("models", [])
    if not isinstance(raw_models, list):
        report["error"] = "Ollama /api/tags returned a non-list models field"
        return report

    models: list[dict[str, Any]] = []
    names: set[str] = set()
    for entry in raw_models:
        if not isinstance(entry, dict):
            continue
        name = _model_name(entry)
        if not name:
            continue
        names.add(name)
        models.append(
            {
                "name": name,
                "digest": entry.get("digest"),
                "size": entry.get("size"),
                "details": entry.get("details", {}),
            }
        )

    missing: list[str] = []
    for lane, model in LANE_MODELS.items():
        if model in names:
            report["lanes"][lane] = {"model": model, "available": True}
        else:
            # Check fallback models for this lane
            fallback_hit = None
            for fb in LANE_FALLBACKS.get(lane, []):
                if fb in names:
                    fallback_hit = fb
                    break
            if fallback_hit:
                report["lanes"][lane] = {
                    "model": fallback_hit,
                    "available": True,
                    "configured_primary": model,
                }
            else:
                report["lanes"][lane] = {"model": model, "available": False}
                missing.append(model)

    report["reachable"] = True
    report["version"] = version.get("version")
    report["models"] = models
    report["missing_models"] = sorted(set(missing))
    report["healthy"] = not report["missing_models"]
    return report


def write_evidence(report: dict[str, Any], path: Path = EVIDENCE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local Ollama API and required Melodia model lanes")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Force offline evidence evaluation")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.offline and EVIDENCE_PATH.exists():
        try:
            report = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
            report["offline_cached"] = True
        except Exception as exc:
            report = {"schema": "melodia_ollama_health_v1", "healthy": False, "error": str(exc)}
    else:
        report = probe(args.base_url, args.timeout)

    if args.write_evidence:
        write_evidence(report)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "PASS" if report.get("healthy") else "HOLD"
        print(f"[{status}] Ollama {report.get('base_url', DEFAULT_BASE_URL)}")
        if report.get("version"):
            print(f"version: {report['version']}")
        if report.get("models"):
            print("models: " + ", ".join(item["name"] for item in report["models"]))
        if report.get("missing_models"):
            print("missing: " + ", ".join(report["missing_models"]))
        if report.get("error"):
            print("error: " + report["error"])
        if args.write_evidence:
            print(f"evidence: {EVIDENCE_PATH}")
    return 0 if report.get("healthy") else 2


if __name__ == "__main__":
    sys.exit(main())
