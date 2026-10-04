"""In-game wardrobe edits -- grant/equip/unequip on the LIVE PIE pawn.

Same call path as Tools/skirt_proof_pie.py (subsystem Get(world) +
Wardrobe component on BP_MelusinaJRPGCharacter). Nothing new: these are the
existing BlueprintCallable owners, driven from the Melodia > Wardrobe menu
while PIE runs. Editor-only safety: every function HOLDs outside PIE.

Menu: Melodia > Wardrobe (init_unreal._register_melodia_menu).
"""
from __future__ import annotations

from typing import Any

PAWN_PATH = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C"
WARDROBE_COMP_PATH = "/Script/MelodiaWardrobe.MelodiaWardrobeComponent"


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _live(unreal):
    """Resolve (world, subsystem, wardrobe component) or (None, HOLD-dict)."""
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    except Exception as exc:
        return None, {"ok": False, "status": "HOLD", "error": f"game world unreadable: {exc}"}
    if world is None:
        return None, {"ok": False, "status": "HOLD", "error": "no PIE game world; press Play first"}
    try:
        subsys = unreal.MelodiaWardrobeSubsystem.get(world)
    except Exception as exc:
        return None, {"ok": False, "error": f"wardrobe subsystem missing: {exc}"}
    try:
        pawn_cls = unreal.load_class(None, PAWN_PATH)
        pawn = unreal.GameplayStatics.get_actor_of_class(world, pawn_cls)
        ward_cls = unreal.load_class(None, WARDROBE_COMP_PATH)
        ward = pawn.get_component_by_class(ward_cls) if pawn else None
    except Exception as exc:
        return None, {"ok": False, "error": f"pawn/wardrobe resolve failed: {exc}"}
    if ward is None:
        return None, {"ok": False, "error": "no Wardrobe component on the live pawn"}
    return (world, subsys, ward), None


def _slot_enum(unreal, name: str):
    enum = unreal.MelodiaWardrobeSlot
    key = name.upper()
    if hasattr(enum, key):
        return getattr(enum, key)
    names = [n for n in dir(enum) if n.isupper()]
    raise ValueError(f"unknown slot '{name}' (known: {', '.join(names)})")


def equipped_summary() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    live, hold = _live(unreal)
    if hold:
        return hold
    _, subsys, _ = live
    rows = []
    for name in [n for n in dir(unreal.MelodiaWardrobeSlot) if n.isupper()]:
        try:
            rows.append({"slot": name, "equipped": str(subsys.get_equipped(getattr(unreal.MelodiaWardrobeSlot, name)))})
        except Exception as exc:
            rows.append({"slot": name, "error": str(exc)[:120]})
    return {"ok": True, "slots": rows}


def grant(cosmetic_id: str, grant_id: str = "menu_grant") -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    live, hold = _live(unreal)
    if hold:
        return hold
    _, subsys, _ = live
    try:
        accepted = subsys.grant_cosmetic(cosmetic_id, grant_id)
        return {"ok": bool(accepted), "cosmetic": cosmetic_id, "owned": bool(subsys.is_owned(cosmetic_id))}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}


def equip(cosmetic_id: str) -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    live, hold = _live(unreal)
    if hold:
        return hold
    _, _, ward = live
    try:
        accepted = ward.equip_cosmetic(cosmetic_id)
        return {"ok": bool(accepted), "cosmetic": cosmetic_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}


def unequip(slot_name: str) -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    live, hold = _live(unreal)
    if hold:
        return hold
    _, _, ward = live
    try:
        ward.unequip_slot(_slot_enum(unreal, slot_name))
        still = ward.is_slot_equipped(_slot_enum(unreal, slot_name))
        return {"ok": not bool(still), "slot": slot_name.upper(), "equipped_after": bool(still)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}


def menu_equipped_summary() -> str:
    state = equipped_summary()
    if not state.get("ok"):
        return f"[Wardrobe] HOLD ({state.get('error')})"
    lines = ["[Wardrobe] live equipped:"]
    for row in state["slots"]:
        lines.append(f"  {row['slot']}: {row.get('equipped', row.get('error'))}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(menu_equipped_summary())
