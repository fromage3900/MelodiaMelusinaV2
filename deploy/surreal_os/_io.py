"""Load YAML/JSON data files from the surreal_os package."""

from __future__ import annotations

import json
import os

_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
_CACHE: dict[str, object] = {}


def package_path(*parts: str) -> str:
    return os.path.join(_PKG_ROOT, *parts)


def _load_yaml_text(text: str):
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        pass
    text = text.strip()
    if not text:
        return None
    raise ImportError("PyYAML not available; use .json data files")


def load_data(*parts: str, use_cache: bool = True):
    """Load .yaml or .json from package; prefers YAML when PyYAML is installed."""
    key = "/".join(parts)
    if use_cache and key in _CACHE:
        return _CACHE[key]

    yaml_path = package_path(*parts) if parts[-1].endswith((".yaml", ".yml", ".json")) else package_path(*parts)
    if not yaml_path.endswith((".yaml", ".yml", ".json")):
        for ext in (".yaml", ".json"):
            candidate = yaml_path + ext
            if os.path.isfile(candidate):
                yaml_path = candidate
                break

    if not os.path.isfile(yaml_path):
        alt = yaml_path.replace(".yaml", ".json")
        if os.path.isfile(alt):
            yaml_path = alt

    with open(yaml_path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    if yaml_path.endswith(".json"):
        data = json.loads(raw)
    else:
        try:
            data = _load_yaml_text(raw)
        except ImportError:
            json_path = yaml_path.replace(".yaml", ".json")
            with open(json_path, "r", encoding="utf-8") as jh:
                data = json.load(jh)

    if use_cache:
        _CACHE[key] = data
    return data


def clear_cache():
    _CACHE.clear()
