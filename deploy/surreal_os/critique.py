"""Phase 5 critique — refactor hints for new generators."""

from __future__ import annotations

from . import atoms, taxonomy


def critique_kit(arch_type: str) -> dict:
    """Return pass flag and hints for a kit arch_type."""
    hints = []
    passed = True
    atom_id = atoms.atom_for_kit(arch_type)
    if not atom_id:
        hints.append("add atom entry in architectural_atoms.yaml")
        passed = False
    gen = taxonomy.get_generator(arch_type)
    if not gen:
        hints.append("add generator entry in procedural_taxonomy.yaml")
        passed = False
    elif not gen.get("atom") and atom_id:
        hints.append("link taxonomy atom id to generator entry")
    if arch_type.startswith("GB_") and gen and gen.get("type") != "graph":
        if not gen.get("outputs"):
            hints.append("document outputs in taxonomy")
    return {"passed": passed, "hints": hints, "atom_id": atom_id}


def critique_all_zen_kits(kit_dispatch: dict) -> tuple[bool, list[str]]:
    fails = []
    for kid in sorted(kit_dispatch):
        if not kid.startswith("GB_ZEN_"):
            continue
        result = critique_kit(kid)
        if not result["passed"]:
            fails.append(f"{kid}: {'; '.join(result['hints'])}")
    return len(fails) == 0, fails
