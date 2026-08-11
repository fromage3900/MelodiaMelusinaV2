"""Convert portfolio material masters to UE 5.8 Substrate Toon BSDF output.

Strategy C: preserve existing graph logic; replace shading root with
MaterialExpressionSubstrateToonBSDF wired to MP_FRONT_MATERIAL.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/convert_masters_to_substrate_toon.py"

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/convert_masters_to_substrate_toon.py" ^
    -stdout -unattended -nosplash

Optional args (sys.argv after script path):
  --batch 1|2|all     Predefined master lists (default: all)
  --paths /Game/...   Explicit material paths (repeatable)
  --dry-run           Inventory only, no graph edits
  --finish            Repair incomplete Toon graphs (BSDF w/o Front Material)
  --fix-params        Rename MCP_* placeholders on batch-2 masters
  --assign-profiles   Set TP_* on material instances from parent family
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
PROFILE_DIR = f"{MATERIALS_ROOT}/ToonProfiles"
REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "Saved"
    / "Audit"
    / "substrate_toon_conversion.json"
)

# Masters already on Substrate Toon (skip)
ALREADY_TOON = {
    f"{MATERIALS_ROOT}/Masters/M_Toon_SDF",
    f"{MATERIALS_ROOT}/Impressionist/Masters/M_Master_Impressionist_Toon",
    f"{MATERIALS_ROOT}/Impressionist/Masters/M_Master_Impressionist_Toon_Landscape",
}

# Batch 1 — copied Melodia SDF masters (Strategy C priority)
BATCH_1 = [
    f"{MATERIALS_ROOT}/Masters/M_SDF_TrueParallax",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GildedStucco",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GildedFiligree",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Baroque",
    f"{MATERIALS_ROOT}/Masters/M_SDF_OrnamentLayer",
    f"{MATERIALS_ROOT}/Masters/M_SDF_OrnamentLayer_Enhanced",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GothicArchitecture",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GothicArchitecture_Enhanced",
    f"{MATERIALS_ROOT}/Masters/M_SDF_RoseWindow",
    f"{MATERIALS_ROOT}/Masters/M_SDF_RayMarch_Gothic",
]

# Batch 2 — hybrid stone + MCP-built masters still on Default Lit root
BATCH_2 = [
    f"{MATERIALS_ROOT}/Masters/M_HybridStone_SDF",
    f"{MATERIALS_ROOT}/Masters/M_SDF_ReliefPanel",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FiligreeRim",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GothicTracery",
    f"{MATERIALS_ROOT}/Masters/M_SDF_HybridStone",
    f"{MATERIALS_ROOT}/Masters/M_SDF_ParallaxPulse",
]

# Batch 3 — aquatic / underwater SDF (_PROJECT/SDF/Underwater)
BATCH_3_AQUATIC = [
    f"{MATERIALS_ROOT}/Masters/M_SDF_AbyssalVent",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Anemone",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Bioluminescence",
    f"{MATERIALS_ROOT}/Masters/M_SDF_BubbleColumn",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Caustics_Underwater",
    f"{MATERIALS_ROOT}/Masters/M_SDF_CoralBranching",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FishSchool_Caustics",
    f"{MATERIALS_ROOT}/Masters/M_SDF_KelpCurtain",
    f"{MATERIALS_ROOT}/Masters/M_SDF_ThermalGlow",
]

# Batch 4 — math-art, musical, cathedral expansion (ported via port_sdf_expansion.py)
BATCH_4_EXPANSION = [
    f"{MATERIALS_ROOT}/Masters/M_SDF_BaroqueColumn",
    f"{MATERIALS_ROOT}/Masters/M_SDF_CathedralVault",
    f"{MATERIALS_ROOT}/Masters/M_SDF_CosmicPortal",
    f"{MATERIALS_ROOT}/Masters/M_SDF_CrystallineSpire",
    f"{MATERIALS_ROOT}/Masters/M_SDF_EscherGeometry_Enhanced",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FloatingNotes",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FloralMagic",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FlyingButtress",
    f"{MATERIALS_ROOT}/Masters/M_SDF_FractalOrnament",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GildedAltar",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GothicRoseWindow",
    f"{MATERIALS_ROOT}/Masters/M_SDF_GrandStaff_CrossSection",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Grass_Field",
    f"{MATERIALS_ROOT}/Masters/M_SDF_InfinityMirror",
    f"{MATERIALS_ROOT}/Masters/M_SDF_JuliaSet_Quaternion",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Klein_Bottle",
    f"{MATERIALS_ROOT}/Masters/M_SDF_MagicOrb",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Mandelbulb_Master",
    f"{MATERIALS_ROOT}/Masters/M_SDF_MandelbulbSlice",
    f"{MATERIALS_ROOT}/Masters/M_SDF_MengerSponge",
    f"{MATERIALS_ROOT}/Masters/M_SDF_MetalShards",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Mobius_Strip",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Musical",
    f"{MATERIALS_ROOT}/Masters/M_SDF_Penrose_Staircase",
    f"{MATERIALS_ROOT}/Masters/M_SDF_SheetMusic_Score",
    f"{MATERIALS_ROOT}/Masters/M_SDF_SierpinskiTetrahedron",
    f"{MATERIALS_ROOT}/Masters/M_SDF_StarburstGem",
    f"{MATERIALS_ROOT}/Masters/M_SDF_TrebleClef_Ornament",
    f"{MATERIALS_ROOT}/Masters/M_SDF_VinylRecord",
]

# MCP batch-2 placeholder -> canonical renames (cohesion)
MCP_PARAM_RENAMES: dict[str, tuple[str, str]] = {
    "M_SDF_ReliefPanel": {
        "MCP_1": ("BaseTint", "Toon"),
        "MCP_2": ("AccentTint", "Toon"),
        "MCP_3": ("DeepTint", "Toon"),
        "MCP_4": ("BandScale", "SDF"),
        "MCP_5": ("ReliefDepth", "SDF"),
        "MCP_6": ("NoiseScale", "SDF"),
    },
    "M_SDF_FiligreeRim": {
        "MCP_1": ("GoldTint", "Toon"),
        "MCP_2": ("HighlightTint", "Toon"),
        "MCP_3": ("FiligreeScale", "SDF"),
        "MCP_4": ("RimStrength", "SDF"),
        "MCP_5": ("AnimSpeed", "Animation"),
    },
    "M_SDF_GothicTracery": {
        "MCP_1": ("BaseTint", "Toon"),
        "MCP_2": ("LeadTint", "Toon"),
        "MCP_3": ("GoldTint", "Toon"),
        "MCP_4": ("RadialScale", "SDF"),
        "MCP_5": ("TraceryMix", "SDF"),
    },
    "M_SDF_HybridStone": {
        "MCP_1": ("StoneTint", "Toon"),
        "MCP_2": ("MossTint", "Toon"),
        "MCP_3": ("GoldEdge", "Toon"),
        "MCP_4": ("WearAmount", "SDF"),
        "MCP_5": ("StoneTiling", "SDF"),
    },
    "M_SDF_ParallaxPulse": {
        "MCP_1": ("BaseTint", "Toon"),
        "MCP_2": ("PulseTint", "Toon"),
        "MCP_3": ("BandScale", "SDF"),
        "MCP_4": ("PulseSpeed", "Animation"),
        "MCP_5": ("GlowStrength", "SDF"),
    },
}

INSTANCE_PROFILE_BY_STEM: dict[str, str] = {
    "MI_Toon_SDF_Wall": "TP_Stucco",
    "MI_Toon_SDF_Floor": "TP_Default",
    "MI_Toon_SDF_Accent": "TP_Gold",
    "MI_Toon_SDF_Rim": "TP_Stucco",
    "MI_Toon_SDF_Ornamental": "TP_Ornamental",
    "MI_SDF_ReliefPanel_Baroque": "TP_Ornamental",
    "MI_SDF_FiligreeRim_Gold": "TP_Gold",
    "MI_SDF_GothicTracery_Rose": "TP_Gold",
    "MI_SDF_HybridStone_Worn": "TP_Default",
    "MI_SDF_ParallaxPulse_Violet": "TP_Ornamental",
    "MI_SDF_Gothic_RoseGold": "TP_Gold",
    "MI_SDF_BaroqueScrollwork": "TP_Ornamental",
    "MI_SDF_GildedFiligree": "TP_Gold",
    "MI_SDF_RoseWindow": "TP_Gold",
    "MI_SDF_Baroque_Default": "TP_Stucco",
    "MI_SDF_GildedStucco_Wall": "TP_Stucco",
    "MI_SDF_GothicArchitecture_Stone": "TP_Stucco",
    "MI_SDF_GothicArchitecture_Enhanced_Detail": "TP_Stucco",
    "MI_SDF_OrnamentLayer_Classic": "TP_Ornamental",
    "MI_SDF_OrnamentLayer_Enhanced_Gold": "TP_Ornamental",
    "MI_SDF_RayMarch_Gothic_Deep": "TP_Stucco",
    "MI_HybridStone_SDF_Moss": "TP_Default",
    "MI_SDF_TrueParallax": "TP_Stucco",
    "MI_Master_SDF_Toon_Default": "TP_Stucco",
    "MI_Master_Toon_Unified_Default": "TP_Default",
    "MI_SDF_CathedralVault": "TP_Stucco",
    "MI_SDF_FlyingButtress": "TP_Stucco",
    "MI_SDF_BaroqueColumn": "TP_Ornamental",
    "MI_SDF_GildedAltar": "TP_Gold",
    "MI_SDF_GothicRoseWindow": "TP_Gold",
    "MI_SDF_Grass_Field": "TP_Foliage",
}

COLOR_SINK_PRIORITY = (
    "LinearInterpolate",
    "Add",
    "Multiply",
    "Saturate",
    "Power",
    "Abs",
    "ComponentMask",
    "Custom",
)

PROFILE_BY_STEM: dict[str, str] = {
    "M_SDF_TrueParallax": "TP_Stucco",
    "M_SDF_GildedStucco": "TP_Stucco",
    "M_SDF_GildedFiligree": "TP_Gold",
    "M_SDF_Baroque": "TP_Stucco",
    "M_SDF_OrnamentLayer": "TP_Ornamental",
    "M_SDF_OrnamentLayer_Enhanced": "TP_Ornamental",
    "M_SDF_GothicArchitecture": "TP_Stucco",
    "M_SDF_GothicArchitecture_Enhanced": "TP_Stucco",
    "M_SDF_RoseWindow": "TP_Gold",
    "M_SDF_RayMarch_Gothic": "TP_Stucco",
    "M_HybridStone_SDF": "TP_Default",
    "M_SDF_ReliefPanel": "TP_Ornamental",
    "M_SDF_FiligreeRim": "TP_Gold",
    "M_SDF_GothicTracery": "TP_Gold",
    "M_SDF_HybridStone": "TP_Default",
    "M_SDF_ParallaxPulse": "TP_Ornamental",
    "M_SDF_AbyssalVent": "TP_Default",
    "M_SDF_Anemone": "TP_Ornamental",
    "M_SDF_Bioluminescence": "TP_Ornamental",
    "M_SDF_BubbleColumn": "TP_Default",
    "M_SDF_Caustics_Underwater": "TP_Default",
    "M_SDF_CoralBranching": "TP_Ornamental",
    "M_SDF_FishSchool_Caustics": "TP_Default",
    "M_SDF_KelpCurtain": "TP_Foliage",
    "M_SDF_ThermalGlow": "TP_Ornamental",
    "M_SDF_CosmicPortal": "TP_Ornamental",
    "M_SDF_Mandelbulb_Master": "TP_Ornamental",
    "M_SDF_Musical": "TP_Gold",
    "M_SDF_Grass_Field": "TP_Foliage",
}


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _try_set_editor_property(obj, name: str, value) -> None:
    try:
        if hasattr(obj, "has_editor_property") and obj.has_editor_property(name):
            obj.set_editor_property(name, value)
    except Exception:
        pass


def _connect(from_expr, from_output: str, to_expr, to_input: str) -> bool:
    try:
        unreal.MaterialEditingLibrary.connect_material_expressions(
            from_expr, from_output, to_expr, to_input
        )
        return True
    except Exception:
        return False


def _connect_toon_pin(toon_bsdf, expr, pin_names: tuple[str, ...]) -> bool:
    for pin in pin_names:
        if _connect(expr, "", toon_bsdf, pin):
            return True
    return False


def _connect_front_material(material, from_expr, from_output: str = "") -> None:
    unreal.MaterialEditingLibrary.connect_material_property(
        from_expr,
        from_output,
        unreal.MaterialProperty.MP_FRONT_MATERIAL,
    )


def _load_profile(stem: str) -> unreal.ToonProfile | None:
    profile_name = PROFILE_BY_STEM.get(stem, "TP_Default")
    path = _asset_path(PROFILE_DIR, profile_name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    default_path = _asset_path(PROFILE_DIR, "TP_Default")
    if unreal.EditorAssetLibrary.does_asset_exist(default_path):
        return unreal.load_asset(default_path)
    return None


def _stem_from_path(material_path: str) -> str:
    return material_path.rsplit("/", 1)[-1].split(".", 1)[0]


def _load_material(material_path: str) -> tuple[object | None, str]:
    stem = _stem_from_path(material_path)
    for candidate in (material_path, f"{material_path}.{stem}"):
        try:
            asset = unreal.load_asset(candidate)
        except Exception as exc:
            unreal.log_warning(f"[Toon] load failed {candidate}: {exc}")
            asset = None
        if asset:
            return asset, candidate
    return None, material_path


def _ensure_assets_available(paths: list[str], timeout: float = 60.0) -> None:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        if registry.is_loading_assets():
            time.sleep(0.5)
            continue
        ready = all(_load_material(p)[0] is not None for p in paths)
        if ready:
            return
        unreal.log("[Toon] Waiting for assets to load...")
        time.sleep(1.0)
    unreal.log_warning("[Toon] Timed out waiting for assets to load")


def _get_expressions(material: unreal.Material) -> list:
    """UE 5.8: Material.expressions is protected — use MaterialEditingLibrary."""
    try:
        return list(unreal.MaterialEditingLibrary.get_material_expressions(material))
    except Exception:
        return []


def _expr_position(expr) -> tuple[int, int]:
    try:
        pos = unreal.MaterialEditingLibrary.get_material_expression_node_position(expr)
        return int(pos.x), int(pos.y)
    except Exception:
        try:
            return (
                int(expr.get_editor_property("material_expression_editor_x") or 0),
                int(expr.get_editor_property("material_expression_editor_y") or 0),
            )
        except Exception:
            return 0, 0


def _has_substrate_toon_bsdf(material: unreal.Material) -> bool:
    for expr in _get_expressions(material):
        if expr and "SubstrateToonBSDF" in type(expr).__name__:
            return True
    return False


def _get_toon_bsdf(material: unreal.Material):
    for expr in _get_expressions(material):
        if expr and "SubstrateToonBSDF" in type(expr).__name__:
            return expr
    return None


def _expr_type(expr) -> str:
    return type(expr).__name__.replace("MaterialExpression", "")


def _build_input_graph(material: unreal.Material) -> tuple[list, dict]:
    lib = unreal.MaterialEditingLibrary
    all_exprs = _get_expressions(material)
    users: dict = {}
    for consumer in all_exprs:
        try:
            inputs = list(lib.get_inputs_for_material_expression(material, consumer))
        except Exception:
            inputs = []
        for inp in inputs:
            if inp:
                users.setdefault(inp, []).append(consumer)
    return all_exprs, users


def _find_mooa_or_function_color(material: unreal.Material):
    """Find color feeding MaterialFunctionCall (MooaToon) or Custom output."""
    lib = unreal.MaterialEditingLibrary
    all_exprs, _ = _build_input_graph(material)
    for expr in all_exprs:
        tname = _expr_type(expr)
        if tname not in ("MaterialFunctionCall", "Custom"):
            continue
        try:
            inputs = list(lib.get_inputs_for_material_expression(material, expr))
        except Exception:
            inputs = []
        for inp in inputs:
            if inp and _expr_type(inp) not in ("ScalarParameter", "Constant", "Time"):
                return inp
    return None


def _find_graph_color_sink(material: unreal.Material):
    """Rightmost terminal color-like expression when legacy outputs are unwired."""
    all_exprs, users = _build_input_graph(material)
    sinks = [e for e in all_exprs if e not in users]
    if not sinks:
        return None

    def score(expr) -> tuple[int, int]:
        tname = _expr_type(expr)
        pri = len(COLOR_SINK_PRIORITY)
        for i, token in enumerate(COLOR_SINK_PRIORITY):
            if token in tname:
                pri = i
                break
        x = _expr_position(expr)[0]
        return (pri, -x)

    sinks.sort(key=score)
    for expr in sinks:
        tname = _expr_type(expr)
        if tname in ("ScalarParameter", "Constant", "Time", "TextureCoordinate", "WorldPosition"):
            continue
        if "FunctionCall" in tname:
            continue
        return expr
    return sinks[0] if sinks else None


def _get_property_source(material: unreal.Material, prop: unreal.MaterialProperty):
    """Return expression feeding a legacy material output pin, if any."""
    lib = unreal.MaterialEditingLibrary
    if hasattr(lib, "get_material_property_input_node"):
        try:
            expr = lib.get_material_property_input_node(material, prop)
            if expr:
                return expr
        except Exception:
            pass

    # Fallback: scan expression output links (UE 5.8)
    try:
        for expr in _get_expressions(material):
            if not expr:
                continue
            outputs = list(lib.get_outputs_for_material_expression(material, expr))
            for out in outputs:
                try:
                    linked = lib.get_material_property_input_node(material, prop)
                    if linked == expr:
                        return expr
                except Exception:
                    continue
    except Exception:
        pass
    return None


def _find_color_source(material: unreal.Material):
    for prop in (
        unreal.MaterialProperty.MP_BASE_COLOR,
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
        unreal.MaterialProperty.MP_SUBSURFACE_COLOR,
    ):
        src = _get_property_source(material, prop)
        if src:
            return src, prop

    mooa = _find_mooa_or_function_color(material)
    if mooa:
        return mooa, None

    sink = _find_graph_color_sink(material)
    if sink:
        return sink, None

    return None, None


def _find_scalar_source(material: unreal.Material, prop: unreal.MaterialProperty):
    return _get_property_source(material, prop)


def _disconnect_property(material: unreal.Material, prop: unreal.MaterialProperty) -> None:
    lib = unreal.MaterialEditingLibrary
    if hasattr(lib, "disconnect_material_property"):
        try:
            lib.disconnect_material_property(material, prop)
            return
        except Exception:
            pass
    # Best-effort: connect constant to sever (only for non-critical legacy pins)
    if prop in (
        unreal.MaterialProperty.MP_BASE_COLOR,
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    ):
        const = lib.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, 0, 0
        )
        const.set_editor_property(
            "constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0)
        )
        try:
            lib.connect_material_property(const, "", prop)
        except Exception:
            pass


def _has_front_material_wired(material: unreal.Material) -> bool:
    return _get_property_source(material, unreal.MaterialProperty.MP_FRONT_MATERIAL) is not None


def _rename_mcp_parameters(material: unreal.Material, stem: str) -> list[str]:
    import material_lib as lib

    mapping = MCP_PARAM_RENAMES.get(stem, {})
    renamed: list[str] = []
    seen: set[str] = set()
    for expr, _owner in lib.iter_parameter_expressions(material):
        tname = _expr_type(expr)
        if "Parameter" not in tname:
            continue
        old_str = lib._param_name(expr) or ""
        if not old_str or old_str in seen:
            continue
        seen.add(old_str)
        if old_str in mapping:
            new_name, group = mapping[old_str]
            expr.set_editor_property("parameter_name", new_name)
            expr.set_editor_property("group", group)
            renamed.append(f"{old_str}->{new_name}")
        elif re.match(r"^MCP_\d+$", old_str):
            suffix = old_str.split("_", 1)[1]
            new_name = f"SDF_AuxParam_{suffix}"
            expr.set_editor_property("parameter_name", new_name)
            expr.set_editor_property("group", "SDF")
            renamed.append(f"{old_str}->{new_name}")
    if renamed:
        material.modify()
    return renamed


def _assign_instance_profiles() -> list[dict]:
    results: list[dict] = []
    inst_root = f"{MATERIALS_ROOT}/SDF/Instances"
    imp_root = f"{MATERIALS_ROOT}/Impressionist/Instances"
    for folder in (inst_root, imp_root):
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
            stem = _stem_from_path(path)
            profile_name = INSTANCE_PROFILE_BY_STEM.get(stem)
            if not profile_name:
                continue
            profile_path = _asset_path(PROFILE_DIR, profile_name)
            if not unreal.EditorAssetLibrary.does_asset_exist(profile_path):
                continue
            inst = unreal.load_asset(path)
            if not isinstance(inst, unreal.MaterialInstanceConstant):
                continue
            profile = unreal.load_asset(profile_path)
            _try_set_editor_property(inst, "toon_profile", profile)
            _try_set_editor_property(inst, "override_toon_profile", True)
            unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
            results.append({"path": path, "profile": profile_name, "status": "assigned"})
    return results


def finish_incomplete_master(material_path: str) -> dict:
    """Repair masters that have Toon BSDF but missing Front Material or profile."""
    stem = _stem_from_path(material_path)
    result = {"path": material_path, "status": "pending", "fixes": []}

    asset = unreal.load_asset(material_path)
    if not asset or isinstance(asset, unreal.MaterialInstanceConstant):
        result["status"] = "skipped"
        return result

    material = asset
    toon = _get_toon_bsdf(material)
    if not toon:
        result["status"] = "no_toon_bsdf"
        return result

    profile = _load_profile(stem)
    if profile:
        toon.set_editor_property("toon_profile", profile)
        result["fixes"].append(f"profile={PROFILE_BY_STEM.get(stem, 'TP_Default')}")

    if not _has_front_material_wired(material):
        _connect_front_material(material, toon)
        result["fixes"].append("wired_front_material")

    color_src, _ = _find_color_source(material)
    if color_src:
        if _connect_toon_pin(toon, color_src, ("BaseColor", "DiffuseColor")):
            result["fixes"].append(f"color={_expr_type(color_src)}")

    try:
        unreal.MaterialEditingLibrary.recompile_material(material)
    except Exception as exc:
        result["status"] = "finish_compile_warning"
        result["error"] = str(exc)
        return result

    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    result["status"] = "finished" if result["fixes"] else "ok"
    return result


def convert_master(material_path: str, *, dry_run: bool = False, fix_params: bool = False) -> dict:
    asset, material_path = _load_material(material_path)
    stem = _stem_from_path(material_path)
    result: dict = {
        "path": material_path,
        "stem": stem,
        "status": "pending",
        "profile": PROFILE_BY_STEM.get(stem, "TP_Default"),
        "color_source": None,
        "roughness_source": None,
        "normal_source": None,
        "error": None,
    }

    if material_path in ALREADY_TOON:
        result["status"] = "skipped_already_toon"
        return result

    if not asset:
        result["status"] = "missing"
        result["error"] = "asset not found"
        return result

    if isinstance(asset, unreal.MaterialInstanceConstant):
        result["status"] = "skipped_instance"
        result["error"] = "convert parent master instead"
        return result

    material = asset

    if fix_params:
        renamed = _rename_mcp_parameters(material, stem)
        if renamed:
            result["param_renames"] = renamed
            try:
                unreal.MaterialEditingLibrary.recompile_material(material)
            except Exception as exc:
                result["compile_warning"] = str(exc)
            unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

    if _has_substrate_toon_bsdf(material):
        result["status"] = "params_fixed" if result.get("param_renames") else "skipped_has_toon_bsdf"
        return result

    if fix_params and result.get("param_renames"):
        # Params-only pass for masters still on legacy lit root
        pass

    color_src, color_prop = _find_color_source(material)
    rough_src = _find_scalar_source(material, unreal.MaterialProperty.MP_ROUGHNESS)
    normal_src = _find_scalar_source(material, unreal.MaterialProperty.MP_NORMAL)

    result["color_source"] = type(color_src).__name__ if color_src else None
    result["roughness_source"] = type(rough_src).__name__ if rough_src else None
    result["normal_source"] = type(normal_src).__name__ if normal_src else None

    if dry_run:
        result["status"] = "dry_run_needs_conversion"
        return result

    profile = _load_profile(stem)
    if not profile:
        result["status"] = "failed"
        result["error"] = "no ToonProfile found"
        return result

    _try_set_editor_property(material, "bUsesSubstrate", True)

    # Place Toon BSDF to the right of existing graph
    max_x = max((_expr_position(e)[0] for e in _get_expressions(material)), default=0)

    toon_bsdf = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionSubstrateToonBSDF, max_x + 400, 200
    )
    toon_bsdf.set_editor_property("toon_profile", profile)

    if color_src:
        if not _connect_toon_pin(toon_bsdf, color_src, ("BaseColor", "DiffuseColor")):
            result["status"] = "failed"
            result["error"] = "could not wire color to Toon BSDF"
            return result
    else:
        # Fallback tint so compile succeeds; tune in editor
        tint = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionVectorParameter, max_x + 120, 80
        )
        tint.set_editor_property("parameter_name", "ToonFallbackTint")
        tint.set_editor_property("group", "Toon")
        tint.set_editor_property(
            "default_value", unreal.LinearColor(0.65, 0.55, 0.72, 1.0)
        )
        if not _connect_toon_pin(toon_bsdf, tint, ("BaseColor", "DiffuseColor")):
            result["status"] = "failed"
            result["error"] = "no color source and fallback failed"
            return result
        result["color_source"] = "ToonFallbackTint (added)"

    if rough_src:
        _connect_toon_pin(toon_bsdf, rough_src, ("Roughness",))

    if normal_src:
        _connect_toon_pin(
            toon_bsdf, normal_src, ("Normal", "TangentNormal", "NormalMap")
        )

    _connect_front_material(material, toon_bsdf)

    # Disconnect legacy lit outputs so Substrate root is authoritative
    for legacy_prop in (
        unreal.MaterialProperty.MP_BASE_COLOR,
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
        unreal.MaterialProperty.MP_ROUGHNESS,
        unreal.MaterialProperty.MP_METALLIC,
        unreal.MaterialProperty.MP_SPECULAR,
    ):
        if legacy_prop != color_prop:
            _disconnect_property(material, legacy_prop)
        elif color_prop == legacy_prop:
            _disconnect_property(material, legacy_prop)

    try:
        unreal.MaterialEditingLibrary.recompile_material(material)
        compile_ok = True
        compile_err = None
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)

    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

    if compile_ok:
        result["status"] = "converted"
    else:
        result["status"] = "converted_compile_warning"
        result["error"] = compile_err

    return result


def _parse_args(argv: list[str]) -> tuple[list[str], str, bool, bool, bool, bool]:
    paths: list[str] = []
    batch = "all"
    dry_run = False
    finish = False
    fix_params = False
    assign_profiles = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--batch" and i + 1 < len(argv):
            batch = argv[i + 1]
            i += 2
            continue
        if arg == "--paths":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                paths.append(argv[i])
                i += 1
            continue
        if arg == "--dry-run":
            dry_run = True
            i += 1
            continue
        if arg == "--finish":
            finish = True
            i += 1
            continue
        if arg == "--fix-params":
            fix_params = True
            i += 1
            continue
        if arg == "--assign-profiles":
            assign_profiles = True
            i += 1
            continue
        i += 1

    if not paths:
        if batch == "1":
            paths = list(BATCH_1)
        elif batch == "2":
            paths = list(BATCH_2)
        elif batch == "3":
            paths = list(BATCH_3_AQUATIC)
        elif batch == "4":
            paths = list(BATCH_4_EXPANSION)
        else:
            paths = list(BATCH_1) + list(BATCH_2) + list(BATCH_3_AQUATIC) + list(BATCH_4_EXPANSION)
    return paths, batch, dry_run, finish, fix_params, assign_profiles


def _inventory_all_masters() -> list[dict]:
    rows: list[dict] = []
    for root in (
        f"{MATERIALS_ROOT}/Masters",
        f"{MATERIALS_ROOT}/Impressionist/Masters",
    ):
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if not path.rsplit("/", 1)[-1].startswith("M_"):
                continue
            ad = unreal.EditorAssetLibrary.find_asset_data(path)
            if str(ad.asset_class) not in ("Material", "MaterialInstanceConstant"):
                continue
            try:
                asset = unreal.load_asset(path)
            except Exception:
                rows.append({"path": path, "kind": "master", "load_failed": True})
                continue
            if not asset:
                rows.append({"path": path, "kind": "master", "load_failed": True})
                continue
            if isinstance(asset, unreal.MaterialInstanceConstant):
                rows.append({"path": path, "kind": "instance", "has_toon": False})
                continue
            has_toon = _has_substrate_toon_bsdf(asset)
            rows.append(
                {
                    "path": path,
                    "kind": "master",
                    "has_toon": has_toon,
                    "has_front": _has_front_material_wired(asset) if has_toon else False,
                    "incomplete": has_toon and not _has_front_material_wired(asset),
                }
            )
    return rows


def main() -> int:
    argv = [a for a in sys.argv[1:] if not a.endswith(".py")]
    paths, batch, dry_run, finish, fix_params, assign_profiles = _parse_args(argv)

    unreal.log("=== Substrate Toon master conversion ===")
    unreal.log(
        f"Batch: {batch} | dry_run={dry_run} | finish={finish} | "
        f"fix_params={fix_params} | assign_profiles={assign_profiles} | count={len(paths)}"
    )

    inventory = _inventory_all_masters() if finish else []
    incomplete_count = sum(1 for r in inventory if r.get("incomplete"))

    if paths and not dry_run:
        _ensure_assets_available(paths)

    if finish:
        finish_paths = [r["path"] for r in inventory if r.get("incomplete")]
        results = [finish_incomplete_master(p) for p in finish_paths]
    else:
        results = [
            convert_master(p, dry_run=dry_run, fix_params=fix_params) for p in paths
        ]

    profile_results = _assign_instance_profiles() if assign_profiles else []

    converted = sum(1 for r in results if r["status"] == "converted")
    finished = sum(1 for r in results if r["status"] == "finished")
    warnings = sum(1 for r in results if r["status"] in ("converted_compile_warning", "finish_compile_warning"))
    skipped = sum(1 for r in results if str(r["status"]).startswith("skipped"))
    failed = sum(
        1
        for r in results
        if r["status"] in ("failed", "missing", "load_failed")
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "batch": batch,
        "dry_run": dry_run,
        "finish_mode": finish,
        "fix_params": fix_params,
        "inventory_masters": inventory,
        "incomplete_found": incomplete_count,
        "requested_paths": paths,
        "results": results,
        "instance_profiles": profile_results,
        "summary": {
            "reviewed": len(results),
            "converted": converted,
            "finished": finished,
            "compile_warnings": warnings,
            "skipped": skipped,
            "failed": failed,
            "instances_profiled": len(profile_results),
        },
        "next_queue": [
            p for p in (list(BATCH_1) + list(BATCH_2) + list(BATCH_3_AQUATIC) + list(BATCH_4_EXPANSION))
            if p not in ALREADY_TOON
        ],
        "monolith_installed": False,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    unreal.log(
        f"Converted: {converted} | finished: {finished} | warnings: {warnings} | "
        f"skipped: {skipped} | failed: {failed} | incomplete_found: {incomplete_count}"
    )
    for r in results:
        unreal.log(f"  [{r['status']}] {r['path']}" + (f" — {r.get('error')}" if r.get("error") else ""))
    unreal.log(f"Report: {REPORT_PATH}")

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
