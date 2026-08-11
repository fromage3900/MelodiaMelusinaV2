"""Build the grandmaster audio channels and M_PP_ToonOutline post-process material.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_audio_outline.py"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "audio_outline_build.json"

MPC_NAME = "MPC_Melodia_Palette"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
PP_NAME = "M_PP_ToonOutline"

MPC_SCALARS = [
    ("GlobalReactivity", 0.0),
    ("Bass", 0.0),
    ("Mid", 0.0),
    ("Treble", 0.0),
    ("BeatPhase", 0.0),
]


def build_mpc() -> str:
    # Grandmaster MPC already carries the runtime audio channels; do not recreate
    # a second MPC island. Ensure the five channels exist and return the path.
    if not unreal.EditorAssetLibrary.does_asset_exist(MPC_PATH):
        raise RuntimeError(f"Missing grandmaster MPC {MPC_PATH}")

    mpc = unreal.load_asset(MPC_PATH)
    existing = {s.get_editor_property("parameter_name")
                for s in mpc.get_editor_property("scalar_parameters")}
    for param_name, default in MPC_SCALARS:
        if param_name not in existing:
            try:
                mpc.set_scalar_parameter_default_value(param_name, default)
            except Exception as exc:
                unreal.log_warning(f"[AudioOutline] MPC param {param_name}: {exc}")

    unreal.log(f"[AudioOutline] grandmaster MPC ok: {MPC_PATH}")
    return MPC_PATH


def build_post_process(force: bool = False) -> str:
    lib.ensure_directory(lib.POST_DIR)
    lib.close_open_material_editors((PP_NAME,))
    path = lib.asset_path(lib.POST_DIR, PP_NAME)
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        if material and not force:
            unreal.log(f"[AudioOutline] reusing PP {path}")
            return path
        if material and force:
            lib.clear_material_graph(material)

    if not material:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(
            PP_NAME, lib.POST_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not material:
        raise RuntimeError(f"Failed to create {PP_NAME}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    material.set_editor_property("blendable_location", unreal.BlendableLocation.BL_REPLACING_TONEMAPPER)

    scene_tex = lib.create_expression(material, unreal.MaterialExpressionSceneTexture, -800, 0)
    scene_tex.set_editor_property(
        "scene_texture_id", lib.post_process_scene_texture_id()
    )

    edge_width = lib.scalar_param(material, "OutlineWidth", "Outline", 1.5, -800, 160)
    edge_color = lib.vector_param(
        material, "OutlineColor", "Outline", (0.02, 0.02, 0.05, 1.0), -800, 280
    )
    edge_strength = lib.scalar_param(material, "EdgeStrength", "Outline", 1.0, -800, 400)
    audio_pulse = lib.scalar_param(material, "AudioPulseStrength", "Outline", 0.35, -800, 520)

    mpc_path = MPC_PATH
    beat_mod = None
    if unreal.EditorAssetLibrary.does_asset_exist(mpc_path):
        mpc = unreal.load_asset(mpc_path)
        if mpc:
            beat = lib.create_expression(material, unreal.MaterialExpressionCollectionParameter, -560, 520)
            beat.set_editor_property("collection", mpc)
            beat.set_editor_property("parameter_name", "BeatPhase")
            beat_mod = lib.create_expression(material, unreal.MaterialExpressionMultiply, -360, 440)
            lib.connect(beat, "", beat_mod, "A")
            lib.connect(audio_pulse, "", beat_mod, "B")

    depth_tex = lib.create_expression(material, unreal.MaterialExpressionSceneTexture, -800, 520)
    depth_tex.set_editor_property(
        "scene_texture_id", unreal.SceneTextureId.PPI_SCENE_DEPTH
    )

    depth_delta = lib.create_expression(material, unreal.MaterialExpressionDDX, -560, 520)
    lib.connect_unary(depth_tex, depth_delta)
    depth_edge = lib.create_expression(material, unreal.MaterialExpressionAbs, -360, 520)
    lib.connect_unary(depth_delta, depth_edge)

    edge_mask = lib.create_expression(material, unreal.MaterialExpressionMultiply, -160, 280)
    strength_src = beat_mod if beat_mod else edge_strength
    lib.connect(depth_edge, "", edge_mask, "A")
    lib.connect(strength_src, "", edge_mask, "B")

    scene_rgb = lib.mask_rgb(material, scene_tex, -400, 0)
    edge_rgb = lib.mask_rgb(material, edge_color, -200, 280)
    outline_mix = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 80, 120)
    lib.connect(scene_rgb, "", outline_mix, "A")
    lib.connect(edge_rgb, "", outline_mix, "B")
    lib.connect(edge_mask, "", outline_mix, "Alpha")

    unreal.MaterialEditingLibrary.connect_material_property(
        outline_mix, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )

    try:
        unreal.MaterialEditingLibrary.recompile_material(material)
    except Exception as exc:
        unreal.log_warning(f"[AudioOutline] PP compile warning: {exc}")

    lib.save_package(material)
    unreal.log(f"[AudioOutline] built PP {path}")
    return path


def build_all(force: bool = False) -> int:
    unreal.log("=== Audio + Outline build ===")
    mpc_path = build_mpc()
    pp_path = build_post_process(force=force)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc": mpc_path,
        "post_process": pp_path,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0


if __name__ == "__main__":
    import sys

    rebuild = "--rebuild" in sys.argv or "--force" in sys.argv
    raise SystemExit(build_all(force=rebuild))
