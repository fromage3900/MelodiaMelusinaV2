"""Load YAML/JSON data files from the surreal_os package.

Reconstructed 2026-08-23 from surviving bytecode (original was untracked and
lost in a deploy-tree mirror). API surface: package_path, load_data, clear_cache.
JSON is native; YAML uses PyYAML when available with a minimal fallback parser
for flat key:value / inline-list documents.
"""

from __future__ import annotations

import json
import os
from os import path

_PKG_ROOT = path.dirname(path.abspath(__file__))
_CACHE: dict[str, object] = {}


def package_path(*parts: str) -> str:
    """Resolve a path relative to the surreal_os package root."""
    return os.path.join(_PKG_ROOT, *parts)


def _load_yaml_text(text: str):
    """Parse YAML text; PyYAML if installed, else a minimal fallback."""
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        pass

    # Minimal fallback: flat "key: value" lines, "# comments", inline [a, b] lists.
    result: dict[str, object] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            parsed: object = []
            for item in items:
                try:
                    parsed.append(int(item))
                except ValueError:
                    try:
                        parsed.append(float(item))
                    except ValueError:
                        parsed.append(item)
            result[key] = parsed
        else:
            try:
                result[key] = int(value)
            except ValueError:
                try:
                    result[key] = float(value)
                except ValueError:
                    result[key] = value.strip("'\"")
    return result


def load_data(*parts: str):
    """Load a JSON/YAML file from the package (cached by normalized path).

    Variadic to match call sites like ``load_data("genomes", f"{gid}.json")``.
    Returns ``None`` when the file does not exist (graceful for optional data).
    """
    norm = "/".join(parts).replace("\\", "/")
    if norm in _CACHE:
        return _CACHE[norm]

    full = package_path(*norm.split("/"))
    if not os.path.isfile(full):
        return None

    with open(full, "r", encoding="utf-8-sig") as handle:
        if norm.endswith(".json"):
            data = json.load(handle)
        else:
            data = _load_yaml_text(handle.read())

    _CACHE[norm] = data
    return data


def clear_cache() -> None:
    _CACHE.clear()
