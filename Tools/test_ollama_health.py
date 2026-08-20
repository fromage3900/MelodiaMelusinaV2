#!/usr/bin/env python3
"""Pure tests for the Ollama health contract; no live service required."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ollama_health  # noqa: E402


class _Response:
    def __init__(self, value: dict):
        self.value = json.dumps(value).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.value


class OllamaHealthTests(unittest.TestCase):
    def test_probe_passes_when_all_contract_models_exist(self):
        def fake_urlopen(request, timeout):
            self.assertGreater(timeout, 0)
            if request.full_url.endswith("/api/version"):
                return _Response({"version": "0.32.9"})
            return _Response(
                {
                    "models": [
                        {"name": "deepseek-r1:14b", "digest": "sha256:one"},
                        {"name": "qwen2.5-coder:7b", "digest": "sha256:two"},
                        {"name": "qwen2.5-coder:14b", "digest": "sha256:three"},
                    ]
                }
            )

        with patch.object(ollama_health.urllib.request, "urlopen", fake_urlopen):
            report = ollama_health.probe("http://127.0.0.1:11434")

        self.assertTrue(report["healthy"])
        self.assertEqual(report["version"], "0.32.9")
        self.assertEqual(report["missing_models"], [])

    def test_probe_holds_when_a_model_tag_is_missing(self):
        def fake_urlopen(request, timeout):
            if request.full_url.endswith("/api/version"):
                return _Response({"version": "0.32.9"})
            return _Response({"models": [{"name": "qwen2.5-coder:7b"}]})

        with patch.object(ollama_health.urllib.request, "urlopen", fake_urlopen):
            report = ollama_health.probe()

        self.assertFalse(report["healthy"])
        self.assertIn("deepseek-r1:14b", report["missing_models"])

    def test_probe_holds_when_api_is_unreachable(self):
        def fake_urlopen(request, timeout):
            raise OSError("connection refused")

        with patch.object(ollama_health.urllib.request, "urlopen", fake_urlopen):
            report = ollama_health.probe()

        self.assertFalse(report["reachable"])
        self.assertFalse(report["healthy"])
        self.assertIn("connection refused", report["error"])


if __name__ == "__main__":
    unittest.main()
