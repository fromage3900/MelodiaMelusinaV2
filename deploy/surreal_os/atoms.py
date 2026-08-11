"""Architectural atoms — resolve atom id to kit / trim / snap contracts."""

from __future__ import annotations

from ._io import load_data

_ATOM_CACHE: dict | None = None


def _atoms_table() -> dict:
    global _ATOM_CACHE
    if _ATOM_CACHE is None:
        data = load_data("schema", "architectural_atoms.json")
        _ATOM_CACHE = data.get("atoms", {}) if isinstance(data, dict) else {}
    return _ATOM_CACHE


def list_atoms() -> list[str]:
    return sorted(_atoms_table().keys())


def resolve_atom(atom_id: str) -> dict | None:
    return _atoms_table().get(atom_id)


def atom_for_kit(arch_type: str) -> str | None:
    for aid, spec in _atoms_table().items():
        if spec.get("kit") == arch_type:
            return aid
    return None


def kits_with_atoms() -> dict[str, str]:
    out = {}
    for aid, spec in _atoms_table().items():
        kit = spec.get("kit")
        if kit:
            out[kit] = aid
    return out
