"""Storybook post-process: cel outline + vine/branch growth along detected edges.

Stack after M_PP_ToonOutline on the portfolio PostProcessVolume:
  1. M_PP_ToonOutline — depth/normal edge ink
  2. M_PP_StorybookVines (or M_PP_StorybookVines_Inst) — organic growth from edges

Default VineBranchMask: /Game/Stylization/T_Flow_Swirl (fallback Voronoi_11).

Run:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_storybook_outline.py"
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_storybook_outline.py" --rebuild

Shell:
  python Content/Python/setup_storybook_outline.py --rebuild
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

import unreal

import material_lib as lib
import portfolio_alpha_paths as alphas

REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "storybook_outline_build.json"
PP_NAME = "M_PP_StorybookVines"
PP_INST_NAME = "M_PP_StorybookVines_Inst"


def _clear_material_graph(material) -> None:
    try:
        for expr in list(unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
            unreal.MaterialEditingLibrary.delete_material_expression(material, expr)
    except Exception as exc:
        unreal.log_warning(f"[StorybookPP] clear graph: {exc}")


def _needs_graph_rebuild(material) -> bool:
    """Detect pre-fix graph (missing diagonal scroll + R-channel mask)."""
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(material)
    except Exception:
        return True
    types = {type(e).__name__ for e in exprs if e}
    return "MaterialExpressionAppendVector" not in types


def _vine_mask_expression(material):
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if (
            expr
            and type(expr).__name__ == "MaterialExpressionTextureSampleParameter2D"
            and expr.get_editor_property("parameter_name") == "VineBranchMask"
        ):
            return expr
    return None


def _acquire_storybook_material(force: bool):
    """Return (material, path) creating or reusing the PP material asset."""
    lib.ensure_directory(lib.POST_DIR)
    lib.close_open_material_editors((PP_NAME, "M_PP_ToonOutline"))
    path = lib.asset_path(lib.POST_DIR, PP_NAME)
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        if not material:
            unreal.log_warning(f"[StorybookPP] stale registry entry at {path} — deleting")
            unreal.EditorAssetLibrary.delete_asset(path)
            try:
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            except Exception:
                pass

    if material and not force and not _needs_graph_rebuild(material):
        return material, path

    if material and (force or _needs_graph_rebuild(material)):
        lib.clear_material_graph(material)
        return material, path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        PP_NAME, lib.POST_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not material:
        outline_path = lib.asset_path(lib.POST_DIR, "M_PP_ToonOutline")
        dest = f"{lib.POST_DIR}/{PP_NAME}"
        if unreal.EditorAssetLibrary.does_asset_exist(outline_path):
            unreal.log("[StorybookPP] create_asset failed — duplicating M_PP_ToonOutline shell")
            dup_ok = unreal.EditorAssetLibrary.duplicate_asset(outline_path, dest)
            unreal.log(f"[StorybookPP] duplicate_asset -> {dup_ok} exists={unreal.EditorAssetLibrary.does_asset_exist(path)}")
            if dup_ok and unreal.EditorAssetLibrary.does_asset_exist(path):
                material = unreal.load_asset(path)
                if material:
                    lib.clear_material_graph(material)
    if not material:
        material = unreal.load_asset(path)
    if not material:
        raise RuntimeError(
            f"Failed to create or load {PP_NAME} — close open material tabs and retry"
        )
    return material, path


def _set_pp_blendable_location(material) -> str:
    loc = lib.post_process_blendable_location()
    material.set_editor_property("blendable_location", loc)
    return str(loc)


def build_storybook_pp(force: bool = False) -> str:
    material, path = _acquire_storybook_material(force)
    if not _needs_graph_rebuild(material):
        lib.set_expression_texture(_vine_mask_expression(material), alphas.VINE_BRANCH_MASK)
        _set_pp_blendable_location(material)
        try:
            unreal.MaterialEditingLibrary.recompile_material(material)
        except Exception as exc:
            unreal.log_warning(f"[StorybookPP] recompile: {exc}")
        lib.save_package(material)
        unreal.log(f"[StorybookPP] reused {path}")
        return path

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    blend_loc = _set_pp_blendable_location(material)

    scene = lib.create_expression(material, unreal.MaterialExpressionSceneTexture, -1000, 0)
    scene.set_editor_property("scene_texture_id", lib.post_process_scene_texture_id())
    scene_rgb = lib.mask_rgb(material, scene, -880, 0)

    depth = lib.create_expression(material, unreal.MaterialExpressionSceneTexture, -1000, 200)
    depth.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_SCENE_DEPTH)

    normals = lib.create_expression(material, unreal.MaterialExpressionSceneTexture, -1000, 400)
    normals.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_WORLD_NORMAL)

    # outline edge mask (depth + normal discontinuity)
    ddx_d = lib.create_expression(material, unreal.MaterialExpressionDDX, -760, 200)
    lib.connect_unary(depth, ddx_d)
    ddy_d = lib.create_expression(material, unreal.MaterialExpressionDDY, -760, 280)
    lib.connect_unary(depth, ddy_d)
    edge_d = lib.create_expression(material, unreal.MaterialExpressionAdd, -560, 240)
    lib.connect(ddx_d, "", edge_d, "A")
    lib.connect(ddy_d, "", edge_d, "B")

    ddx_n = lib.create_expression(material, unreal.MaterialExpressionDDX, -760, 400)
    lib.connect_unary(normals, ddx_n)
    ddy_n = lib.create_expression(material, unreal.MaterialExpressionDDY, -760, 480)
    lib.connect_unary(normals, ddy_n)
    edge_n = lib.create_expression(material, unreal.MaterialExpressionAdd, -560, 440)
    lib.connect(ddx_n, "", edge_n, "A")
    lib.connect(ddy_n, "", edge_n, "B")

    edge_raw = lib.create_expression(material, unreal.MaterialExpressionAdd, -360, 320)
    lib.connect(edge_d, "", edge_raw, "A")
    lib.connect(edge_n, "", edge_raw, "B")
    edge_abs = lib.create_expression(material, unreal.MaterialExpressionAbs, -200, 320)
    lib.connect_unary(edge_raw, edge_abs)

    edge_width = lib.scalar_param(material, "OutlineWidth", "Storybook", 2.0, -1000, 600)
    edge_str = lib.scalar_param(material, "EdgeStrength", "Storybook", 1.0, -1000, 700)
    edge_mask = lib.create_expression(material, unreal.MaterialExpressionMultiply, 0, 320)
    lib.connect(edge_abs, "", edge_mask, "A")
    lib.connect(edge_width, "", edge_mask, "B")
    edge_sat = lib.create_expression(material, unreal.MaterialExpressionMultiply, 160, 320)
    lib.connect(edge_mask, "", edge_sat, "A")
    lib.connect(edge_str, "", edge_sat, "B")
    edge_clamp = lib.create_expression(material, unreal.MaterialExpressionSaturate, 320, 320)
    lib.connect_unary(edge_sat, edge_clamp)

    # vine growth: branch mask scrolled along screen-space diagonal + edge seed
    vine_len = lib.scalar_param(material, "VineGrowthLength", "Storybook", 0.35, -1000, 820)
    vine_scale = lib.scalar_param(material, "VineBranchScale", "Storybook", 6.0, -1000, 920)
    vine_str = lib.scalar_param(material, "VineBranchStrength", "Storybook", 0.75, -1000, 1020)
    vine_speed = lib.scalar_param(material, "VineGrowthSpeed", "Storybook", 0.08, -1000, 1120)
    speed_src = vine_speed
    sakura_mpc = "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream.MPC_SakuraDream"
    if unreal.EditorAssetLibrary.does_asset_exist(sakura_mpc):
        mpc = unreal.load_asset(sakura_mpc)
        if mpc:
            gust = lib.create_expression(material, unreal.MaterialExpressionCollectionParameter, -760, 1200)
            gust.set_editor_property("collection", mpc)
            gust.set_editor_property("parameter_name", "GustTrigger")
            gust_boost = lib.create_expression(material, unreal.MaterialExpressionAdd, -560, 1120)
            lib.connect(vine_speed, "", gust_boost, "A")
            lib.connect(gust, "", gust_boost, "B")
            speed_src = gust_boost
    vine_ink = lib.vector_param(material, "VineInkColor", "Storybook", (0.04, 0.12, 0.06, 1.0), -1000, 1220)
    leaf_tint = lib.vector_param(material, "LeafHighlightColor", "Storybook", (0.35, 0.62, 0.28, 1.0), -1000, 1340)
    branch_tex = lib.texture_param(material, "VineBranchMask", "Storybook", -1000, 1460)
    vine_branch_path = lib.set_expression_texture(branch_tex, alphas.VINE_BRANCH_MASK)
    if not vine_branch_path:
        unreal.log_warning("[StorybookPP] VineBranchMask: no texture found — assign T_Flow_Swirl in editor")

    screen_uv = lib.create_expression(material, unreal.MaterialExpressionTextureCoordinate, -760, 900)
    time_n = lib.create_expression(material, unreal.MaterialExpressionTime, -760, 1040)
    scroll = lib.create_expression(material, unreal.MaterialExpressionMultiply, -560, 1040)
    lib.connect(time_n, "", scroll, "A")
    lib.connect(speed_src, "", scroll, "B")
    # diagonal 2D scroll (scalar+scalar -> float2); avoids invalid float2+scalar add
    scroll_uv = lib.create_expression(material, unreal.MaterialExpressionAppendVector, -560, 1120)
    lib.connect(scroll, "", scroll_uv, "A")
    lib.connect(scroll, "", scroll_uv, "B")
    uv_scroll = lib.create_expression(material, unreal.MaterialExpressionAdd, -360, 900)
    lib.connect(screen_uv, "", uv_scroll, "A")
    lib.connect(scroll_uv, "", uv_scroll, "B")
    uv_scale = lib.create_expression(material, unreal.MaterialExpressionMultiply, -160, 900)
    lib.connect(uv_scroll, "", uv_scale, "A")
    lib.connect(vine_scale, "", uv_scale, "B")
    lib.connect(uv_scale, "", branch_tex, "Coordinates")

    branch_r = lib.create_expression(material, unreal.MaterialExpressionComponentMask, 320, 1460)
    branch_r.set_editor_property("r", True)
    branch_r.set_editor_property("g", False)
    branch_r.set_editor_property("b", False)
    branch_r.set_editor_property("a", False)
    lib.connect(branch_tex, "", branch_r, "")

    branch_seed = lib.create_expression(material, unreal.MaterialExpressionMultiply, 480, 520)
    lib.connect(edge_clamp, "", branch_seed, "A")
    lib.connect(branch_r, "", branch_seed, "B")
    vine_grow = lib.create_expression(material, unreal.MaterialExpressionMultiply, 640, 520)
    lib.connect(branch_seed, "", vine_grow, "A")
    lib.connect(vine_len, "", vine_grow, "B")
    vine_w = lib.create_expression(material, unreal.MaterialExpressionMultiply, 800, 520)
    lib.connect(vine_grow, "", vine_w, "A")
    lib.connect(vine_str, "", vine_w, "B")

    ink_line = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 480, 200)
    lib.connect(scene_rgb, "", ink_line, "A")
    lib.connect(lib.mask_rgb(material, vine_ink, 400, 200), "", ink_line, "B")
    lib.connect(edge_clamp, "", ink_line, "Alpha")

    vine_line = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, 960, 360)
    lib.connect(ink_line, "", vine_line, "A")
    lib.connect(lib.mask_rgb(material, leaf_tint, 880, 360), "", vine_line, "B")
    lib.connect(vine_w, "", vine_line, "Alpha")

    unreal.MaterialEditingLibrary.connect_material_property(
        vine_line, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )

    try:
        unreal.MaterialEditingLibrary.recompile_material(material)
    except Exception as exc:
        unreal.log_warning(f"[StorybookPP] compile warning: {exc}")

    lib.save_package(material)
    unreal.log(f"[StorybookPP] built {path} blendable={blend_loc} vine_mask={vine_branch_path}")
    return path


def build_storybook_pp_instance(parent_path: str | None = None) -> str | None:
    parent = parent_path or lib.asset_path(lib.POST_DIR, PP_NAME)
    if not unreal.EditorAssetLibrary.does_asset_exist(parent):
        unreal.log_warning(f"[StorybookPP] skip instance — missing parent {parent}")
        return None

    inst_path = lib.asset_path(lib.POST_DIR, PP_INST_NAME)
    inst = lib.create_material_instance(PP_INST_NAME, lib.POST_DIR, parent)
    lib.set_instance_texture(inst, "VineBranchMask", alphas.VINE_BRANCH_MASK)
    lib.save_package(inst)
    unreal.log(f"[StorybookPP] instance {inst_path}")
    return inst_path


def build_all(force: bool = False) -> int:
    alphas.ensure_alpha_imports()
    path = build_storybook_pp(force=force)
    inst_path = build_storybook_pp_instance(path)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "post_process": path,
        "post_process_instance": inst_path,
        "vine_branch_mask": lib.resolve_texture_path(alphas.VINE_BRANCH_MASK),
        "blendable_location": str(lib.post_process_blendable_location()),
        "alpha_catalog": alphas.catalog_summary(),
        "stack_note": "Add to PPV blendables after M_PP_ToonOutline (prefer Inst for mask swaps)",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


def _in_ue() -> bool:
    try:
        import unreal as _u  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    rebuild = "--rebuild" in sys.argv or "--force" in sys.argv
    if _in_ue():
        return build_all(force=rebuild)
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "storybook_rebuild.log"
    script = (
        PROJECT_ROOT / "Content/Python/setup_storybook_outline_rebuild.py"
        if rebuild
        else PROJECT_ROOT / "Content/Python/setup_storybook_outline.py"
    )
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={script.as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    print(f"Storybook -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        raise SystemExit(main())
    raise SystemExit(main())
