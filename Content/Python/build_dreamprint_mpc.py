"""Dreamprint — build MPC_MelodiaInk, the post-process ink runtime surface.

Written by the Melodia lookdev director / MetaSound amplitude bridge at runtime;
read by M_PP_MelodiaInk and M_PP_MeluColorGrade. Kept under an Ink* prefix so the
Custom HLSL globals never collide with the pre-existing MPC_Melodia_Palette surface.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MPC_FOLDER = "/Game/Melodia/_PROJECT/04_Materials"
MPC_NAME = "MPC_MelodiaInk"
MPC_PATH = f"{MPC_FOLDER}/{MPC_NAME}.{MPC_NAME}"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_mpc_build.json"

SCALARS = {
    # global print weight — profile/director knob (0 = no print, 1 = full ink)
    "InkMasterWeight": 1.0,
    # sync-vision pulse strength (0 = off, preserves locked look; profiles opt in)
    "InkSyncVision": 0.0,
    # MetaSound amplitude bridge (envelope follower writes these; 0 until a music
    # source runs). Distinct Ink* names so they never collide with Portfolio_Audio.
    "InkBass": 0.0,
    "InkMid": 0.0,
    "InkTreble": 0.0,
    "InkReact": 0.0,
    # director pitch -> print-hue shift (0..1)
    "InkHueShift": 0.5,
}

VECTORS = {
    "InkAccentTint": (0.20, 0.28, 0.42, 1.0),
}


def main() -> int:
    if not unreal.EditorAssetLibrary.does_directory_exist(MPC_FOLDER):
        unreal.EditorAssetLibrary.make_directory(MPC_FOLDER)

    mpc = None
    if unreal.EditorAssetLibrary.does_asset_exist(MPC_PATH):
        mpc = unreal.load_asset(MPC_PATH)
    if mpc is None:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialParameterCollectionFactoryNew()
        mpc = asset_tools.create_asset(MPC_NAME, MPC_FOLDER, unreal.MaterialParameterCollection, factory)
    if mpc is None:
        raise RuntimeError(f"Failed to create MPC {MPC_PATH}")

    existing = {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("scalar_parameters") or [])}
    scalars = list(mpc.get_editor_property("scalar_parameters") or [])
    added = []
    for name, default in SCALARS.items():
        if name in existing:
            continue
        p = unreal.CollectionScalarParameter()
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", default)
        scalars.append(p)
        added.append(name)
    mpc.set_editor_property("scalar_parameters", scalars)

    existing_v = {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("vector_parameters") or [])}
    vectors = list(mpc.get_editor_property("vector_parameters") or [])
    added_v = []
    for name, rgba in VECTORS.items():
        if name in existing_v:
            continue
        p = unreal.CollectionVectorParameter()
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(*rgba))
        vectors.append(p)
        added_v.append(name)
    mpc.set_editor_property("vector_parameters", vectors)

    unreal.EditorAssetLibrary.save_loaded_asset(mpc, only_if_is_dirty=False)
    final = {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("scalar_parameters") or [])}
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc": MPC_PATH,
        "added_scalars": added,
        "added_vectors": added_v,
        "missing": sorted(set(SCALARS) - final),
        "ok": set(SCALARS).issubset(final),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())