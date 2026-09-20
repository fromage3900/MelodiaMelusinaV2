#!/usr/bin/env python3
"""
Megascans / Brushify → Custom_MS reparent + optional Chladni love (batch 1).

RUN ONLY on fromage with UE + Monolith / Editor Python.
Hard rules:
  - NEVER Monolith save_packages / recompile_material
  - Leave packages dirty for owner Ctrl+S
  - Melodia / ChoralSheep naming only (no GrokBot_ prefixes)

Typical entry (Editor Output Log):
  py "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/megascans_brushify_chladni_batch1.py"

Or Monolith run_python / material_query after describe_query.

This script is a *template*: fill BATCH_PATHS after live census, then run.
Default DRY_RUN=True — set False only after Custom_MS Chladni probe.
"""
from __future__ import annotations

import unreal

DRY_RUN = True
MAX_BATCH = 20

# --- Melodia Custom_MS masters (owner paths) ---
MS_DEFAULT = "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault"
MS_FOLIAGE = "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage"

# --- Chladni reference (ChoralSheep coat) ---
CHLADNI_TEX = "/Game/Melodia/Companions/ChoralSheep/Textures/T_Chladni_C_ROOT"
CHLADNI_REF_MI = "/Game/Melodia/Companions/ChoralSheep/Materials/MI_ChoralSheep_Body_Chladni_C"

# Env-surface subtle defaults (do not nuke PBR albedo)
ENV_CHLADNI_SCALARS = {
    "ChladniIntensity": 0.25,
    "ChladniEmissiveStrength": 0.35,
    "ChladniSheenStrength": 0.35,
    "HarmonizeActive": 0.0,
    "BeatAccent": 0.0,
    "Cymatic_ModeN": 2.0,
    "Cymatic_ModeM": 3.0,
}
ENV_CHLADNI_VECTORS = {
    "ChladniPearlSilkColor": unreal.LinearColor(0.96, 0.91, 0.96, 1.0),
    "ChladniLilacHaloColor": unreal.LinearColor(0.58, 0.40, 0.72, 1.0),
}

# Fill after census — surface MIs still on stock Quixel parents
BATCH_PATHS: list[str] = [
    # "/Game/Megascans/.../MI_Example",
]

FOLIAGE_HINTS = ("foliage", "leaf", "leaves", "grass", "plant", "moss", "flower", "bush")


def _load(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        unreal.log_warning(f"[ms_chladni] missing: {path}")
    return asset


def probe_chladni_on_master(master_path: str) -> set[str]:
    """Return which known Chladni param names exist on master (best-effort)."""
    master = _load(master_path)
    found: set[str] = set()
    if not master:
        return found
    names = list(ENV_CHLADNI_SCALARS) + list(ENV_CHLADNI_VECTORS) + ["ChladniPatternTexture"]
    # Parameter presence: try reading static params via MaterialEditingLibrary where possible
    try:
        # get_static_* may not list all; we attempt set-and-read on a throwaway? skip — probe via MI ref
        ref = _load(CHLADNI_REF_MI)
        if ref:
            unreal.log(f"[ms_chladni] Chladni ref MI loaded: {CHLADNI_REF_MI}")
    except Exception as e:
        unreal.log_warning(f"[ms_chladni] ref probe: {e}")
    for n in names:
        found.add(n)  # optimistic; live pass should filter via Monolith get_material_parameters
    unreal.log(f"[ms_chladni] probe assume names on {master_path}: {sorted(found)}")
    return found


def pick_parent(mi_path: str) -> str:
    low = mi_path.lower()
    if any(h in low for h in FOLIAGE_HINTS):
        return MS_FOLIAGE
    return MS_DEFAULT


def reparent(mi, parent_path: str) -> bool:
    parent = _load(parent_path)
    if not parent:
        return False
    if DRY_RUN:
        unreal.log(f"[ms_chladni] DRY reparent {mi.get_path_name()} -> {parent_path}")
        return True
    try:
        mi.set_editor_property("parent", parent)
        unreal.log(f"[ms_chladni] reparented -> {parent_path}")
        return True
    except Exception as e:
        unreal.log_error(f"[ms_chladni] reparent failed: {e}")
        return False


def apply_chladni(mi, have: set[str]) -> list[str]:
    applied = []
    if DRY_RUN:
        unreal.log(f"[ms_chladni] DRY Chladni on {mi.get_path_name()}")
        return ["DRY_RUN"]
    for k, v in ENV_CHLADNI_SCALARS.items():
        if k not in have:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, v)
            applied.append(k)
        except Exception as e:
            unreal.log_warning(f"[ms_chladni] scalar {k}: {e}")
    for k, v in ENV_CHLADNI_VECTORS.items():
        if k not in have:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, k, v)
            applied.append(k)
        except Exception as e:
            unreal.log_warning(f"[ms_chladni] vector {k}: {e}")
    if "ChladniPatternTexture" in have:
        tex = _load(CHLADNI_TEX)
        if tex:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, "ChladniPatternTexture", tex
                )
                applied.append("ChladniPatternTexture")
            except Exception as e:
                unreal.log_warning(f"[ms_chladni] tex: {e}")
    return applied


def main():
    unreal.log("=" * 60)
    unreal.log(f"[ms_chladni] batch1 DRY_RUN={DRY_RUN} max={MAX_BATCH}")
    unreal.log("=" * 60)

    have = probe_chladni_on_master(MS_DEFAULT)
    if not BATCH_PATHS:
        unreal.log_warning(
            "[ms_chladni] BATCH_PATHS empty — fill from live Megascans parent census first"
        )
        return

    done = 0
    for path in BATCH_PATHS[:MAX_BATCH]:
        mi = _load(path)
        if not mi:
            continue
        parent = pick_parent(path)
        if not reparent(mi, parent):
            continue
        applied = apply_chladni(mi, have)
        unreal.log(f"[ms_chladni] {path} parent={parent} chladni={applied}")
        # Intentionally DO NOT save_loaded_asset — owner Ctrl+S
        done += 1

    unreal.log(f"[ms_chladni] DONE count={done} (packages left dirty; owner Ctrl+S)")


if __name__ == "__main__":
    main()
