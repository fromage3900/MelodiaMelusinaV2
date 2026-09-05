"""PREP — Hero Gem cymatic PBR material instances on M_Master_Toon_Universal.

AUTHOR-TIME PREP ONLY. This script is the editor-guarded plan for
AUDIO_HERO_MATERIAL_PLAN_2026-09-02\nPhase D: import the 9 cooked MelodiaHeroGem
cymatic PBR PNGs into a stable /Game texture folder, create a small Material
Instance family on M_Master_Toon_Universal, and pre-set the MPC_Hero_Material
scalar lanes as MI default parameters.

It NEVER executes writes on a prep pass. The first thing it does is try to
import `unreal`. Outside the live UE editor that import fails, the script prints
a clear REFUSED message and exits 0 — no .uasset is created, no MB is imported.
Only when it is actually run inside the editor (import unreal succeeds) does it
import maps / create MIs.

Canonical source piece: M_Master_Toon_Universal (the "god material", Substrate
Toon, ~192 params / 12 families) — the reusable environment pillar the hero gem
must derive from, per the plan's single-writer / read-only architecture contract.
MPC_Melodia_Palette is the SINGLE audio MPC writer (read-only for this prep);
MPC_Hero_Material is the SCAFFOLDED subsystem-owned MPC written at runtime by
UMelodiaNeuralHeroMaterialSubsystem. MPC->material paramet ers bind by NAME at
runtime; this prep only guarantees the MI exposes those lanes with defaults.

Cymatic source (cooked 9/9 PASS):
  Saved/Audit/copernicus_cymatic/MelodiaHeroGem/T_Cymatic_MelodiaHeroGem_{BaseColor,
  Normal,Roughness,Metallic,Height,ORM,Emissive,Iridescence,Opacity}.png  (1024)

Palette entry (bass->treble chladni modes, low-rough jew el facets, molten gold
veins, nacre iridescence, nodal emissive):
  Tools/Houdini/copernicus/copernicus_cymatic_parallax.py -> VARIANTS["MelodiaHeroGem"]

Run inside the live editor (via the in-editor Python / File > Execute Python
Script, or Monolith run_python). Style mirrors import_atlantis_textures.py +
apply_theme_instances.py.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Guard (1): the ONLY thing allowed before this is the pure-Python imports above.
# --------------------------------------------------------------------------
try:
    import unreal  # noqa: F401
    IN_EDITOR = True
except ImportError:
    IN_EDITOR = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# === Resolved canonical paths ==============================================
# Verified across the repo (apply_theme_instances.py, apply_zen_instances.py,
# annotate_master_columns.py, MATERIAL_SYSTEM_REVIEW.md, docs sentinel lsg):
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MASTER_ASSET = f"{MASTER_PATH}.M_Master_Toon_Universal"

# === Stable /Game destination folders ======================================
TEX_DEST = "/Game/EnvSandbox/Textures/Cymatic/MelodiaHeroGem"
MI_FOLDER = "/Game/EnvSandbox/Materials/MelodiaHeroGem"

# === On-disk cymatic cook ==================================================
CYMATIC_SRC = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic" / "MelodiaHeroGem"

# === MPC lanes (plan §2) ===================================================
# Single audio MPC writer — READ-ONLY here.
MPC_AUDIO_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
# SCAFFOLDED subsystem-owned MPC (written at runtime by the neural seam). It is
# NOT a disk asset yet — may be absent at prep time; binding is by name at runtime.
MPC_HERO_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Hero_Material"
# lane_name -> (kind, default). EmissiveTint is a LinearColor; the rest are scalars.
MPC_HERO_LANES = {
    "EmissiveStrength": ("scalar", 0.9),
    "EmissiveTint": ("vector", (0.73, 0.84, 1.0, 1.0)),
    "SubsurfaceScatter": ("scalar", 0.6),
    "Displacement": ("scalar", 0.05),
    "SpecBoost": ("scalar", 1.0),
}

# === 9-map job table: purpose -> (sRGB, master-param match keywords) ========
# sRGB follows the repo convention: basecolor/emissive ON; all data maps OFF.
MAP_JOBS = [
    # (suffix,          srgb,   match-keywords)
    ("BaseColor",   True,  ("base", "albedo", "diffuse")),
    ("Normal",      False, ("normal",)),
    ("Roughness",   False, ("rough",)),
    ("Metallic",    False, ("metal",)),
    ("Height",      False, ("height", "displace")),
    ("ORM",         False, ("orm", "packed", "ao", "ambientocc", "ambientoccl")),
    ("Emissive",    True,  ("emissive", "glow", "selfi")),
    ("Iridescence", False, ("irid", "nacre", "thinfilm")),
    ("Opacity",     False, ("opacity", "alpha", "mask")),
]

# MI family: each derived from the master, all sharing the 9 imported maps.
MI_FAMILY = [
    {"name": "MI_HeroGem_Crystal", "scalars": {"SubsurfaceScatter": 0.7, "EmissiveStrength": 1.2}},
    {"name": "MI_HeroGem_GoldVein", "scalars": {"SubsurfaceScatter": 0.4, "EmissiveStrength": 0.8}},
    {"name": "MI_HeroGem_NacreSheen", "scalars": {"SubsurfaceScatter": 0.5, "EmissiveStrength": 0.9}},
]

REPORT = PROJECT_ROOT / "Saved" / "Audit" / "herogem_mi_prep_manifest.json"

_MISSING = object()


def _match_param(available, keywords, fallback):
    """Return the first available param name containing any keyword, else fallback."""
    names = list(available)
    low = [n.lower() for n in names]
    for kw in keywords:
        for i, n in enumerate(low):
            if kw in n:
                return names[i]
    return fallback


def _run_in_editor() -> int:
    import unreal  # noqa: F401 — guaranteed by the guard, kept for clarity.

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "D_prep",
        "prep_only": True,
        "master": MASTER_PATH,
        "master_resolved_path": MASTER_ASSET,
        "cymatic_source": str(CYMATIC_SRC),
        "texture_dest": TEX_DEST,
        "mi_folder": MI_FOLDER,
        "mpc_audio": MPC_AUDIO_PATH,
        "mpc_hero": MPC_HERO_PATH,
        "status": "REFUSED",
        "refused_reason": None,
    }

    unreal.log("[HeroGemPrep] START — editor guard passed, preparing Phase D wiring.")
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        report["status"] = "MISSING_MASTER"
        report["refused_reason"] = f"master not found: {MASTER_PATH}"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        unreal.log_error(f"[HeroGemPrep] refuse: {report['refused_reason']}")
        print("REFUSED: missing master", MASTER_PATH)
        return 0

    if not CYMATIC_SRC.is_dir():
        report["status"] = "MISSING_CYMATIC_SOURCE"
        report["refused_reason"] = f"cooked map dir not found: {CYMATIC_SRC}"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("REFUSED: missing cymatic cook", CYMATIC_SRC)
        return 0

    pngs = {p.name: p for p in sorted(CYMATIC_SRC.glob("*.png"))}
    expected = [f"T_Cymatic_MelodiaHeroGem_{s}.png" for s, _, _ in MAP_JOBS]
    missing = [n for n in expected if n not in pngs]
    if missing:
        report["status"] = "MISSING_MAPS"
        report["refused_reason"] = f"missing cooked maps: {missing}"
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("REFUSED: missing cooked maps", missing)
        return 0

    # --- (3) import the 9 PNGs with slot-aware sRGB ------------------------
    imported, skipped, failed_tex = [], [], []
    unreal.EditorAssetLibrary.make_directory(TEX_DEST)
    for suffix, srgb, _kw in MAP_JOBS:
        src = pngs[f"T_Cymatic_MelodiaHeroGem_{suffix}.png"]
        asset = f"{TEX_DEST}/T_Cymatic_MelodiaHeroGem_{suffix}"
        if unreal.EditorAssetLibrary.does_asset_exist(asset):
            skipped.append(asset)
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("filename", str(src))
        task.set_editor_property("destination_path", TEX_DEST)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.EditorAssetLibrary.load_asset(asset)
        if tex:
            try:
                tex.set_editor_property("srgb", srgb)
            except Exception as exc:  # noqa: BLE001
                unreal.log_warning(f"[HeroGemPrep] srgb {asset}: {exc}")
            imported.append(asset)
        else:
            failed_tex.append(src.name)

    for asset in imported:
        try:
            unreal.EditorAssetLibrary.save_asset(asset)
        except Exception:  # noqa: BLE001
            pass

    # --- master param name resolution (fuzzy, robust to master naming) -----
    mat = unreal.load_asset(MASTER_PATH)
    tex_params = list(unreal.MaterialEditingLibrary.get_material_texture_parameter_names(mat))
    scalar_params = list(unreal.MaterialEditingLibrary.get_material_scalar_parameter_names(mat))
    vector_params = list(unreal.MaterialEditingLibrary.get_material_vector_parameter_names(mat))

    texture_wires: dict[str, str] = {}
    for suffix, _srgb, kw in MAP_JOBS:
        default_param = f"Cymatic{suffix}"
        param = _match_param(tex_params, kw, default_param)
        texture_wires[param] = f"{TEX_DEST}/T_Cymatic_MelodiaHeroGem_{suffix}"

    # --- (4) create / open MIs + bind map texture params --------------------
    created_mis: list[dict] = []
    atls = unreal.AssetToolsHelpers.get_asset_tools()
    for spec in MI_FAMILY:
        name = spec["name"]
        unreal.EditorAssetLibrary.make_directory(MI_FOLDER)
        inst_path = f"{MI_FOLDER}/{name}"
        existed = unreal.EditorAssetLibrary.does_asset_exist(inst_path)
        if existed:
            inst = unreal.load_asset(inst_path)
        else:
            factory = unreal.MaterialInstanceConstantFactoryNew()
            inst = atls.create_asset(name, MI_FOLDER, unreal.MaterialInstanceConstant, factory)
            if not inst:
                failed_tex.append(name)
                continue
            unreal.MaterialEditingLibrary.set_material_instance_parent(
                inst, unreal.load_asset(MASTER_PATH)
            )
        wired_textures: dict[str, bool] = {}
        for param, tex_path in texture_wires.items():
            wired_textures[param] = bool(
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    inst, param, unreal.load_asset(tex_path)
                )
            )
        # lane-level overrides per MI (Crystal/Gold/Nacre)
        for lane, val in spec.get("scalars", {}).items():
            real = _match_param(scalar_params, (lane.lower(),), lane)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                inst, real, float(val)
            )
        try:
            unreal.EditorAssetLibrary.save_asset(inst_path)
        except Exception:  # noqa: BLE001
            pass
        created_mis.append({
            "instance": inst_path,
            "created_or_existing": "existing" if existed else "created",
            "status": "created",
            "textures_wired": {k: v for k, v in wired_textures.items() if v},
        })

    # --- (5) pre-set MPC_Hero_Material lanes as MI defaults ------------------
    # MPC->material binds BY NAME at runtime (single audio MPC is unchanged, read-only).
    # This prep only guarantees the MI exposes the lanes with defaults; the C++ seam
    # (MelodiaNeuralHeroMaterialSubsystem) writes MPC_Hero_Material which drives them.
    lanes_wired: dict[str, dict] = {}
    for lane, (kind, default) in MPC_HERO_LANES.items():
        if kind == "scalar":
            param = _match_param(scalar_params, (lane.lower(),), lane)
            real_name = param if param != _MISSING else lane
            real_name = str(real_name)
            lanes_wired[lane] = {"param": real_name, "kind": "scalar", "default": default}
            for spec in MI_FAMILY:
                inst = unreal.load_asset(f"{MI_FOLDER}/{spec['name']}")
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    inst, real_name, float(default)
                )
        else:
            param = _match_param(vector_params, (lane.lower(),), lane)
            real_name = str(param) if param != _MISSING else lane
            lanes_wired[lane] = {"param": real_name, "kind": "vector", "default": list(default)}
            for spec in MI_FAMILY:
                inst = unreal.load_asset(f"{MI_FOLDER}/{spec['name']}")
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                    inst, real_name, unreal.LinearColor(*default)
                )

    mpc_hero_present = bool(
        unreal.EditorAssetLibrary.does_asset_exist(MPC_HERO_PATH)
    )

    report.update({
        "status": "PREPARED",
        "maps_imported": imported,
        "maps_skipped_existing": skipped,
        "maps_import_failed": failed_tex,
        "texture_wires": texture_wires,
        "mi_count": len(created_mis),
        "mis": created_mis,
        "mpc_lanes": lanes_wired,
        "mpc_hero_asset_present_at_prep": mpc_hero_present,
        "mpc_binding_note": (
            "MPC_Hero_Material is SCAFFOLDED (runtime, written by "
            "UMelodiaNeuralHeroMaterialSubsystem). Lanes bind to MI params BY NAME at "
            "runtime. This prep pre-sets matching MI defaults so the lanes exist."
        ),
    })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[HeroGemPrep] PREPARED: {len(imported)} maps, {len(created_mis)} MIs, "
               f"{len(lanes_wired)} MPC lanes -> {REPORT}")
    print(f"HERO_GEM_PREP_OK maps={len(imported)} mis={len(created_mis)} "
          f"lanes={len(lanes_wired)} failed_tex={len(failed_tex)}")
    return 0 if not failed_tex else 1


def _write_refused(reason: str) -> int:
    """Record the REFUSED-outside-editor prep state (no editor writes)."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "D_prep",
        "prep_only": True,
        "master": MASTER_PATH,
        "master_resolved_path": MASTER_ASSET,
        "cymatic_source": str(CYMATIC_SRC),
        "texture_dest": TEX_DEST,
        "mi_folder": MI_FOLDER,
        "mpc_audio": MPC_AUDIO_PATH,
        "mpc_hero": MPC_HERO_PATH,
        "status": "REFUSED",
        "refused_reason": reason,
        "note": (
            "Outside the live UE editor this prep does NOT create MIs or import "
            "textures. Run inside the editor to execute Phase D wiring."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    if IN_EDITOR:
        return _run_in_editor()
    refused = (
        "REFUSED-outside-editor: `unreal` is not importable here. Prep_hero_gem_material_instances "
        "is an in-editor Phase D wiring script. No .uasset was created and no texture was imported. "
        "Run inside the live UE 5.8 editor to execute."
    )
    print(refused)
    _write_refused("REFUSED-outside-editor: import unreal failed (not running inside UE editor).")
    return 0  # prep pass — clean non-error exit, nothing mutated


if __name__ == "__main__":
    raise SystemExit(main())