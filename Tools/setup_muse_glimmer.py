#!/usr/bin/env python3
"""Probe and optionally install Muse Glimmer for Hermes MATH eval.

Local path (recommended offline):
    ollama pull hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M
    ollama cp hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M muse-glimmer-30b

Cloud path:
    set OPENROUTER_API_KEY=sk-or-...   (User env)
    Complete 18+ attestation for meta/muse-spark-1.2 on openrouter.ai

Usage:
    python Tools/setup_muse_glimmer.py
    python Tools/setup_muse_glimmer.py --pull
    python Tools/setup_muse_glimmer.py --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

OLLAMA = "http://127.0.0.1:11434"
HF_TAG = "hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M"
LOCAL_ALIAS = "muse-glimmer-30b"
LOCAL_WEIGHTS = Path(r"G:\AI\Models\weights\Muse-Glimmer-30B-direct")


def _ollama_tags() -> list[str]:
    try:
        raw = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read().decode()
        data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []
    return [str(m.get("name") or "") for m in data.get("models") or []]


def probe() -> dict:
    from openrouter_chat import probe_muse

    tags = _ollama_tags()
    muse_tags = [t for t in tags if "muse" in t.lower() or "glimmer" in t.lower()]
    or_probe = probe_muse()
    return {
        "ollama_muse_tags": muse_tags,
        "ollama_hf_tag_present": HF_TAG in tags or any(HF_TAG.split(":")[0] in t for t in tags),
        "local_alias": LOCAL_ALIAS,
        "local_alias_present": LOCAL_ALIAS in tags or f"{LOCAL_ALIAS}:latest" in tags,
        "local_weights_dir": str(LOCAL_WEIGHTS),
        "local_weights_present": LOCAL_WEIGHTS.is_dir(),
        "openrouter": or_probe,
        "ready": bool(muse_tags) or or_probe.get("ok"),
        "recommended": (
            f"ollama pull {HF_TAG} && ollama cp {HF_TAG} {LOCAL_ALIAS}"
            if not muse_tags
            else "python Tools/run_math_models.py --run-muse"
        ),
    }


def _pull() -> int:
    print(f"Pulling {HF_TAG} (~17 GB). This may take a while...")
    rc = subprocess.call(["ollama", "pull", HF_TAG])
    if rc != 0:
        return rc
    print(f"Creating alias {LOCAL_ALIAS}...")
    return subprocess.call(["ollama", "cp", HF_TAG, LOCAL_ALIAS])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pull", action="store_true", help="Pull HF GGUF and create muse-glimmer-30b alias")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.pull:
        return _pull()
    report = probe()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ready={report['ready']}")
        print(f"ollama_muse_tags={report['ollama_muse_tags']}")
        print(f"openrouter_ok={report['openrouter'].get('ok')} model={report['openrouter'].get('model')}")
        print(f"recommended: {report['recommended']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
