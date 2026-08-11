"""Procedural taxonomy registry — I/O contracts for primitives/modifiers/generators."""

from __future__ import annotations

from ._io import load_data

_TABLE: dict | None = None


def _table() -> dict:
    global _TABLE
    if _TABLE is None:
        _TABLE = load_data("schema", "procedural_taxonomy.json")
    return _TABLE


def list_generators() -> list[str]:
    return sorted((_table().get("generators") or {}).keys())


def get_generator(gen_id: str) -> dict | None:
    return (_table().get("generators") or {}).get(gen_id)


def kit_ids() -> list[str]:
    return [k for k, v in (_table().get("generators") or {}).items() if v.get("type") != "graph" and k.startswith("GB_")]


def validate_kit_dispatch(kit_dispatch: dict) -> list[str]:
    """Return missing taxonomy entries for kits in _KIT_DISPATCH."""
    missing = []
    tax_kits = set(kit_ids())
    for kid in kit_dispatch:
        if kid.startswith("GB_ZEN_") and kid not in tax_kits:
            missing.append(kid)
    return missing
