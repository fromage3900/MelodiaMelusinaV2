"""Package-to-Figma Token Bridge Adapter.

Reads portfolio_package.json, applies figma_token_bridge.schema.json mappings,
and emits figma_variables_update.json ready for the Figma REST API or the
melodia-figma-plugin local consumer.

Usage (dry-run, no API call):
    python pipeline/figma/package_to_figma_tokens.py --dry-run

Usage (POST to Figma REST API):
    set FIGMA_API_TOKEN=<personal-access-token>
    set FIGMA_FILE_KEY=<file-key-from-figma-url>
    python pipeline/figma/package_to_figma_tokens.py

Environment variables:
    FIGMA_API_TOKEN   - Figma personal access token (required for --post)
    FIGMA_FILE_KEY    - Figma file key from the URL bar (required for --post)
    PORTFOLIO_ROOT    - Override project root (default: two dirs above this file)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
SCHEMA_PATH = SCRIPT_DIR / "figma_token_bridge.schema.json"
PACKAGE_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
OUTPUT_PATH = SCRIPT_DIR / "figma_variables_update.json"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _log(msg: str) -> None:
    print(f"[FigmaTokenBridge] {msg}")


def _deep_get(data: dict, dotpath: str) -> Any:
    """Resolve a dotpath like 'scene.scene_name' or 'renders.hero[0].path'."""
    parts: list[str] = []
    for segment in dotpath.replace("][", "].[").split("."):
        if "[" in segment:
            key, _, rest = segment.partition("[")
            index_str = rest.rstrip("]").strip()
            parts.append(key)
            if index_str == "*":
                parts.append("*")
            else:
                parts.append(int(index_str))
        else:
            parts.append(segment)

    node: Any = data
    for part in parts:
        if node is None:
            return None
        if part == "*":
            # wildcard: collect all values from a list of dicts (handled below)
            return node
        if isinstance(node, list):
            if isinstance(part, int):
                node = node[part] if part < len(node) else None
            else:
                node = None
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


def _wildcard_collect(data: dict, from_path: str) -> list:
    """Handle paths like 'materials[*].thumbnail' — returns a flat list."""
    star_idx = from_path.find("[*]")
    if star_idx == -1:
        return []
    list_path = from_path[:star_idx]
    tail = from_path[star_idx + 3:].lstrip(".")
    items = _deep_get(data, list_path)
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            result.append(item)
        elif tail:
            val = _deep_get(item, tail)
            if val is not None:
                result.append(val)
    return result


def _apply_transform(value: Any, transform: str | None) -> str:
    if transform == "format_number" and value is not None:
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)
    if transform == "count_keys" and isinstance(value, dict):
        return str(len(value))
    return str(value) if value is not None else ""


def _resolve_path(raw: str, project_root: Path) -> str:
    """Convert a Saved/... relative path to absolute if it exists, else keep raw."""
    candidate = project_root / raw
    if candidate.exists():
        return str(candidate.as_posix())
    return raw


# ---------------------------------------------------------------------------
# Core translation
# ---------------------------------------------------------------------------
def build_variable_updates(package: dict, schema: dict, project_root: Path) -> dict:
    """Apply schema mappings and return the Figma variables payload."""
    variables: dict[str, Any] = {}

    # --- Scalar mappings ---
    for mapping in schema.get("scalar_mappings", []):
        from_path: str = mapping["from"]
        to_key: str = mapping["to"].replace("/", ".")
        transform: str | None = mapping.get("transform")
        fallback = mapping.get("fallback", "—")

        raw = _deep_get(package, from_path)
        if raw is None:
            value = fallback
        else:
            value = _apply_transform(raw, transform)
            if not value:
                value = fallback

        variables[to_key] = {"type": mapping.get("type", "STRING"), "value": value}
        _log(f"  scalar {from_path!r} -> {to_key!r} = {value!r}")

    # --- Image slot mappings ---
    for mapping in schema.get("image_slot_mappings", []):
        from_path = mapping["from"]
        to_key = mapping["to"].replace("/", ".")
        fallback = mapping.get("fallback")
        resolve = mapping.get("resolve", "none")

        raw = _deep_get(package, from_path)
        value = None
        if raw is not None:
            value = _resolve_path(str(raw), project_root) if resolve == "project_relative" else str(raw)

        variables[to_key] = {"type": "IMAGE", "value": value or fallback}
        _log(f"  image  {from_path!r} -> {to_key!r} = {value!r}")

    # --- Array mappings ---
    for mapping in schema.get("array_mappings", []):
        from_path = mapping["from"]
        to_key = mapping["to"].replace("/", ".")
        fallback = mapping.get("fallback", [])

        if "[*]" in from_path:
            values = _wildcard_collect(package, from_path)
        else:
            values = _deep_get(package, from_path) or []

        if not values:
            values = fallback

        variables[to_key] = {"type": mapping.get("type", "STRING_ARRAY"), "value": values}
        _log(f"  array  {from_path!r} -> {to_key!r} ({len(values)} items)")

    return {"variables": variables, "source": "portfolio_package.json"}


# ---------------------------------------------------------------------------
# Figma REST API POST
# ---------------------------------------------------------------------------
def post_to_figma(payload: dict, api_token: str, file_key: str) -> None:
    endpoint = f"https://api.figma.com/v1/files/{file_key}/variables"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "X-Figma-Token": api_token,
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    _log(f"POST → {endpoint}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            _log(f"Figma API OK: {result.get('status', 'no status')}")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        _log(f"ERROR Figma API HTTP {exc.code}: {body_text}")
        sys.exit(1)
    except urllib.error.URLError as exc:
        _log(f"ERROR connecting to Figma API: {exc.reason}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Translate portfolio_package.json to Figma variables.")
    parser.add_argument("--dry-run", action="store_true", help="Write output file but skip Figma API call")
    parser.add_argument("--post", action="store_true", help="POST to Figma REST API (requires env vars)")
    parser.add_argument("--package", default=str(PACKAGE_PATH), help="Path to portfolio_package.json")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="Path to figma_token_bridge.schema.json")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output path for figma_variables_update.json")
    args = parser.parse_args()

    project_root_override = os.environ.get("PORTFOLIO_ROOT")
    project_root = Path(project_root_override) if project_root_override else PROJECT_ROOT

    # Load schema
    schema_path = Path(args.schema)
    if not schema_path.exists():
        _log(f"ERROR: schema not found at {schema_path}")
        return 1
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Load package
    package_path = Path(args.package)
    if not package_path.exists():
        _log(f"WARNING: portfolio_package.json not found at {package_path} — using empty dict")
        package: dict = {}
    else:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        _log(f"Loaded package: {package_path}")

    # Build update payload
    _log("Applying mappings…")
    payload = build_variable_updates(package, schema, project_root)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _log(f"Wrote {output_path} ({len(payload['variables'])} variables)")

    non_null = sum(1 for v in payload["variables"].values() if v.get("value") not in (None, "—", [], ""))
    _log(f"Non-null values: {non_null}/{len(payload['variables'])}")

    if args.dry_run:
        _log("Dry-run mode — skipping Figma API call")
        return 0

    if args.post:
        api_token = os.environ.get("FIGMA_API_TOKEN", "")
        file_key = os.environ.get("FIGMA_FILE_KEY", "")
        if not api_token or not file_key:
            _log("ERROR: FIGMA_API_TOKEN and FIGMA_FILE_KEY env vars required for --post")
            return 1
        post_to_figma(payload, api_token, file_key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
