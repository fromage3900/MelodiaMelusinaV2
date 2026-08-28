"""Author Musical Dream biome material instances.

Sources parents from existing MIs (NOT the master) to avoid touching
M_Master_Toon_Universal per the P0 convergence plan.

Families:

  Piano Roll    parent = MI_Env_Wood_Trim
                Walkable: light ivory / dark ebony, low specular, no audio.
  Coral Reef    parent = MI_Universal_IridescentShell
                Iridescent mother-of-pearl + Nikki rim glow. Three color
                variants (warm coral / cool cyan / pink pearl).
  Filigree      parent = MI_Baroque_GildedFiligree
                Existing gold-leaf filigree parent, with a musical accent
                variant tinted toward TP_Melusina.

ToonProfile is the existing TP_Melusina for harmony with Melodia hero.
Override override_color_Tint via MPC_Portfolio_Palette if a different
palette is required; defaults ride the infinity-Nikki pastel set.

Manifest: Saved/Audit/musical_dream_mis.json

Run inside the live editor:
    import author_musical_dream_mis as a; a.main()
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "Saved" / "Audit" / "musical_dream_mis.json"

# Parent references: existing MIs, never the master
PARENT_PIANO_WHITE = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Wood_Trim"
PARENT_PIANO_BLACK = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Env_Stone_Cathedral"
PARENT_CORAL = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Universal_IridescentShell"
PARENT_FILIGREE = "/Game/EnvSandbox/Materials/Instances/Environment/Baroque/MI_Baroque_GildedFiligree"

# Use a single, well-known ToonProfile for visual consistency
TOON_PROFILE = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina"

# Destination folders (Meshes/MusicalDream + Materials/Instances/MusicalDream)
DEST_MES = "/Game/EnvSandbox/Meshes/MusicalDream"
DEST_MI = "/Game/EnvSandbox/Materials/Instances/MusicalDream"

# Color palette: infinity-nikki pastel + 18% saturation bump
PALETTE = {
    "ivory":       (0.91, 0.86, 0.74, 1.0),   # warm white piano key
    "ebony":       (0.05, 0.04, 0.03, 1.0),   # black piano key
    "keybed":      (0.18, 0.10, 0.06, 1.0),   # dark wood bed
    "coral_warm":  (0.95, 0.42, 0.50, 1.0),   # warm pink-red coral
    "coral_cool":  (0.35, 0.72, 0.82, 1.0),   # cool cyan coral
    "coral_pearl": (0.88, 0.72, 0.85, 1.0),   # pink pearl
    "filigree_gold":     (0.95, 0.78, 0.32, 1.0),
    "filigree_melusina": (0.21, 0.18, 0.25, 1.0),  # dark purple accent
}


def _ensure_mi(unreal, name: str, parent_path: str, color: tuple):
    """Create or update a single MI. Returns (path, created_bool)."""
    mi_path = f"{DEST_MI}/{name}"
    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_MI):
        unreal.EditorAssetLibrary.make_directory(DEST_MI)

    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        mi = unreal.load_asset(mi_path)
        created = False
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(name, DEST_MI, unreal.MaterialInstanceConstant, factory)
        created = True

    if not mi:
        return mi_path, False, "load_failed"

    parent = unreal.load_asset(parent_path)
    if not parent:
        return mi_path, created, f"parent_missing:{parent_path}"

    mi.set_editor_property("parent", parent)

    mel = unreal.MaterialEditingLibrary
    try:
        mel.set_material_instance_vector_parameter_value(
            mi, "Color", unreal.LinearColor(*color)
        )
    except Exception:
        # not all parents expose Color; tolerate
        pass
    try:
        mel.set_material_instance_vector_parameter_value(
            mi, "Tint", unreal.LinearColor(*color)
        )
    except Exception:
        pass
    try:
        mel.set_material_instance_vector_parameter_value(
            mi, "BaseColor", unreal.LinearColor(*color)
        )
    except Exception:
        pass

    # ToonProfile: only set if the parent has the parameter
    try:
        tp = unreal.load_asset(TOON_PROFILE)
        if tp:
            mel.set_material_instance_texture_parameter_value(
                mi, "ToonProfile", tp
            )
    except Exception:
        pass

    unreal.EditorAssetLibrary.save_asset(mi_path, only_if_is_dirty=False)
    return mi_path, created, "ok"


def build_piano_roll_mis(unreal):
    items = []
    for name, color in (
        ("MI_PianoRoll_Ivory", PALETTE["ivory"]),
        ("MI_PianoRoll_Ebony", PALETTE["ebony"]),
        ("MI_PianoRoll_Keybed", PALETTE["keybed"]),
    ):
        parent = PARENT_PIANO_WHITE if name != "MI_PianoRoll_Ebony" else PARENT_PIANO_BLACK
        path, created, status = _ensure_mi(unreal, name, parent, color)
        items.append({"name": name, "path": path, "parent": parent,
                      "color": list(color), "created": created, "status": status})
    return items


def build_coral_mis(unreal):
    items = []
    for name, color in (
        ("MI_Coral_Reef_Warm", PALETTE["coral_warm"]),
        ("MI_Coral_Reef_Cool", PALETTE["coral_cool"]),
        ("MI_Coral_Reef_Pearl", PALETTE["coral_pearl"]),
    ):
        path, created, status = _ensure_mi(unreal, name, PARENT_CORAL, color)
        items.append({"name": name, "path": path, "parent": PARENT_CORAL,
                      "color": list(color), "created": created, "status": status})
    return items


def build_filigree_mis(unreal):
    items = []
    for name, color in (
        ("MI_Filigree_Gold", PALETTE["filigree_gold"]),
        ("MI_Filigree_MelusinaAccent", PALETTE["filigree_melusina"]),
    ):
        path, created, status = _ensure_mi(unreal, name, PARENT_FILIGREE, color)
        items.append({"name": name, "path": path, "parent": PARENT_FILIGREE,
                      "color": list(color), "created": created, "status": status})
    return items


def main():
    import unreal

    unreal.log("[MusicalDream] authoring material instances")
    manifest = {
        "started": datetime.now(timezone.utc).isoformat(),
        "piano_rolls": build_piano_roll_mis(unreal),
        "coral_reef": build_coral_mis(unreal),
        "filigree": build_filigree_mis(unreal),
        "finished": datetime.now(timezone.utc).isoformat(),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    unreal.log(f"[MusicalDream] MI manifest -> {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    main()
