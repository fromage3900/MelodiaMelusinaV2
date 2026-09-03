"""Build seed batch: 20 Melodia-inspired SDF material instances to bootstrap the factory.

Three waves, each parented to M_Toon_SDF (or M_Master_SDF_Toon for landscape).
Creates material instances with band-relief parameters matched to Melodia texture families.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/build_melodia_sdf_batch.py"

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="G:/.../build_melodia_sdf_batch.py" -unattended -nullrhi

This seeds the sdf_factory_history.json so the SDF Factory loop has a baseline
to research/learn from.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
PARENT_SDF = f"{MATERIALS_ROOT}/Masters/M_Toon_SDF.M_Toon_SDF"
PARENT_SDF_MATURED = f"{MATERIALS_ROOT}/Masters/M_Master_SDF_Toon.M_Master_SDF_Toon"

# ── Wave 1: Cathedral / Gothic (8 materials) ───────────────────────────────
WAVE1_CATHEDRAL = [
    {
        "name": "MI_SDF_RoseWindow_Radial",
        "tint": (0.62, 0.28, 0.48, 1.0), "accent": (0.92, 0.78, 0.42, 1.0),
        "band_scale": 0.065, "band_strength": 0.35,
        "texture_family": "Voronoi", "style": "stained glass radial with gold tracery bands",
        "tags": ["cathedral", "gothic", "stained_glass"],
    },
    {
        "name": "MI_SDF_GildedTracery_Arched",
        "tint": (0.55, 0.48, 0.42, 1.0), "accent": (0.85, 0.65, 0.25, 1.0),
        "band_scale": 0.045, "band_strength": 0.28,
        "texture_family": "Vein", "style": "gilded baroque tracery in arched stone",
        "tags": ["baroque", "tracery", "gilded"],
    },
    {
        "name": "MI_SDF_BaroqueColumn_Spiral",
        "tint": (0.72, 0.62, 0.52, 1.0), "accent": (0.48, 0.38, 0.28, 1.0),
        "band_scale": 0.05, "band_strength": 0.22,
        "texture_family": "Marble", "style": "spiral baroque column in marble with shadow bands",
        "tags": ["baroque", "column", "spiral"],
    },
    {
        "name": "MI_SDF_StainedGlass_Kaleidoscope",
        "tint": (0.35, 0.28, 0.65, 1.0), "accent": (0.95, 0.45, 0.35, 1.0),
        "band_scale": 0.07, "band_strength": 0.40,
        "texture_family": "Swirl", "style": "kaleidoscopic stained glass with rich color bands",
        "tags": ["stained_glass", "colorful", "cathedral"],
    },
    {
        "name": "MI_SDF_Vault_Ribbed",
        "tint": (0.50, 0.45, 0.42, 1.0), "accent": (0.68, 0.58, 0.50, 1.0),
        "band_scale": 0.04, "band_strength": 0.18,
        "texture_family": "Cracks", "style": "ribbed gothic vault ceiling with stone relief",
        "tags": ["vault", "ribbed", "ceiling"],
    },
    {
        "name": "MI_SDF_Buttress_Flying",
        "tint": (0.48, 0.42, 0.38, 1.0), "accent": (0.62, 0.55, 0.48, 1.0),
        "band_scale": 0.035, "band_strength": 0.15,
        "texture_family": "Grainy", "style": "flying buttress exterior stone with grain bands",
        "tags": ["buttress", "exterior", "stone"],
    },
    {
        "name": "MI_SDF_Altar_GoldFiligree",
        "tint": (0.78, 0.68, 0.52, 1.0), "accent": (0.95, 0.82, 0.35, 1.0),
        "band_scale": 0.06, "band_strength": 0.32,
        "texture_family": "Melt", "style": "gilded altar with flowing gold filigree relief",
        "tags": ["altar", "gold", "filigree"],
    },
    {
        "name": "MI_SDF_Cloister_Arcade",
        "tint": (0.42, 0.45, 0.40, 1.0), "accent": (0.58, 0.62, 0.56, 1.0),
        "band_scale": 0.04, "band_strength": 0.20,
        "texture_family": "Gabor", "style": "cloister arcade stone with rhythmic arch bands",
        "tags": ["cloister", "arcade", "rhythmic"],
    },
]

# ── Wave 2: Cosmo / Atmospheric (6 materials) ──────────────────────────────
WAVE2_COSMO = [
    {
        "name": "MI_SDF_Starfield_Dust",
        "tint": (0.06, 0.04, 0.18, 1.0), "accent": (0.45, 0.42, 0.95, 1.0),
        "band_scale": 0.08, "band_strength": 0.42,
        "texture_family": "Milky", "style": "deep space starfield with luminous blue dust bands",
        "tags": ["cosmic", "starfield", "deep"],
    },
    {
        "name": "MI_SDF_Nebula_Veil",
        "tint": (0.15, 0.08, 0.25, 1.0), "accent": (0.85, 0.35, 0.72, 1.0),
        "band_scale": 0.06, "band_strength": 0.35,
        "texture_family": "Super_Noise", "style": "nebula veil with magenta-purple gaseous bands",
        "tags": ["cosmic", "nebula", "atmospheric"],
    },
    {
        "name": "MI_SDF_Aurora_Band",
        "tint": (0.12, 0.15, 0.22, 1.0), "accent": (0.25, 0.85, 0.55, 1.0),
        "band_scale": 0.05, "band_strength": 0.38,
        "texture_family": "Perlin", "style": "aurora borealis banding with green-blue shimmer",
        "tags": ["aurora", "atmospheric", "shimmer"],
    },
    {
        "name": "MI_SDF_Eclipse_Halo",
        "tint": (0.04, 0.03, 0.08, 1.0), "accent": (0.92, 0.72, 0.28, 1.0),
        "band_scale": 0.07, "band_strength": 0.30,
        "texture_family": "Streak", "style": "solar eclipse halo with golden corona bands",
        "tags": ["eclipse", "halo", "golden"],
    },
    {
        "name": "MI_SDF_Void_DarkMatter",
        "tint": (0.03, 0.02, 0.06, 1.0), "accent": (0.18, 0.15, 0.45, 1.0),
        "band_scale": 0.09, "band_strength": 0.48,
        "texture_family": "Turbulence", "style": "dark matter void with deep blue turbulence bands",
        "tags": ["void", "dark", "deep"],
    },
    {
        "name": "MI_SDF_Cosmic_Portal",
        "tint": (0.10, 0.06, 0.15, 1.0), "accent": (0.55, 0.85, 0.95, 1.0),
        "band_scale": 0.065, "band_strength": 0.40,
        "texture_family": "Spokes", "style": "cosmic portal with cyan radial spoke bands",
        "tags": ["portal", "radial", "cyan"],
    },
]

# ── Wave 3: Melusina Landscape SDF (6 materials) ───────────────────────────
WAVE3_LANDSCAPE = [
    {
        "name": "MI_SDF_HybridStone_Cello",
        "tint": (0.45, 0.38, 0.32, 1.0), "accent": (0.58, 0.52, 0.45, 1.0),
        "band_scale": 0.05, "band_strength": 0.20,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Textures", "style": "hybrid stone with cello wood-grain banding",
        "tags": ["landscape", "stone", "hybrid"],
    },
    {
        "name": "MI_SDF_Terrain_Crystal",
        "tint": (0.35, 0.42, 0.48, 1.0), "accent": (0.65, 0.72, 0.78, 1.0),
        "band_scale": 0.06, "band_strength": 0.25,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Perlin", "style": "crystal terrain with blue-white mineral bands",
        "tags": ["landscape", "crystal", "terrain"],
    },
    {
        "name": "MI_SDF_Moss_Soil",
        "tint": (0.35, 0.42, 0.28, 1.0), "accent": (0.48, 0.52, 0.38, 1.0),
        "band_scale": 0.04, "band_strength": 0.16,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Grainy", "style": "mossy soil with organic green-brown band relief",
        "tags": ["landscape", "moss", "organic"],
    },
    {
        "name": "MI_SDF_Grass_Weave",
        "tint": (0.38, 0.52, 0.32, 1.0), "accent": (0.52, 0.65, 0.42, 1.0),
        "band_scale": 0.035, "band_strength": 0.14,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Techno", "style": "woven grass pattern with subtle green banding",
        "tags": ["landscape", "grass", "woven"],
    },
    {
        "name": "MI_SDF_Rock_Stembell",
        "tint": (0.52, 0.48, 0.42, 1.0), "accent": (0.65, 0.58, 0.50, 1.0),
        "band_scale": 0.045, "band_strength": 0.22,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Cracks", "style": "stem bell rock with cracked stone band relief",
        "tags": ["landscape", "rock", "cracked"],
    },
    {
        "name": "MI_SDF_Sand_Leafcool",
        "tint": (0.72, 0.68, 0.55, 1.0), "accent": (0.58, 0.62, 0.48, 1.0),
        "band_scale": 0.04, "band_strength": 0.18,
        "parent": PARENT_SDF_MATURED,
        "texture_family": "Swirl", "style": "sandy leaf-cool terrain with warm swirl bands",
        "tags": ["landscape", "sand", "warm"],
    },
]

ALL_WAVES = [("cathedral", WAVE1_CATHEDRAL), ("cosmo", WAVE2_COSMO), ("landscape", WAVE3_LANDSCAPE)]


def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _inst_path(name: str) -> str:
    return f"{SDF_INST_DIR}/{name}.{name}"


def _load_parent(path: str) -> unreal.Material:
    p = unreal.load_asset(path)
    if not p:
        raise RuntimeError(f"Missing parent: {path}")
    return p


def _set_vector(inst, param: str, rgba) -> None:
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        inst, param, unreal.LinearColor(*rgba))


def _set_scalar(inst, param: str, value: float) -> None:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, param, value)


def build_wave(wave_name: str, specs: list[dict]) -> list[dict]:
    _ensure_directory(SDF_INST_DIR)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    results: list[dict] = []

    for spec in specs:
        name = spec["name"]
        full_path = _inst_path(name)
        parent_path = spec.get("parent", PARENT_SDF)
        entry = {"name": name, "status": "unknown"}

        if unreal.EditorAssetLibrary.does_asset_exist(full_path):
            entry["status"] = "exists"
            unreal.log(f"[SDFBatch/{wave_name}] exists: {name}")
            results.append(entry)
            continue

        parent = _load_parent(parent_path)
        instance = asset_tools.create_asset(name, SDF_INST_DIR, unreal.MaterialInstanceConstant, factory)
        if not instance:
            entry["status"] = "create_failed"
            results.append(entry)
            continue

        unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
        _set_vector(instance, "BaseTint", spec["tint"])
        _set_vector(instance, "AccentTint", spec["accent"])
        _set_scalar(instance, "SDF_BandScale", spec["band_scale"])
        _set_scalar(instance, "SDF_BandStrength", spec["band_strength"])

        unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
        entry["status"] = "created"
        entry["style"] = spec["style"]
        entry["texture_family"] = spec["texture_family"]
        results.append(entry)
        unreal.log(f"[SDFBatch/{wave_name}] created {name} — {spec['style']}")

    return results


def build_all() -> int:
    unreal.log("=== Melodia SDF Seed Batch (20 materials, 3 waves) ===")

    all_results: list[dict] = []
    total_created = 0
    total_existed = 0

    for wave_name, specs in ALL_WAVES:
        unreal.log(f"[SDFBatch] Wave: {wave_name} ({len(specs)} materials)")
        results = build_wave(wave_name, specs)
        created = sum(1 for r in results if r["status"] == "created")
        existed = sum(1 for r in results if r["status"] == "exists")
        total_created += created
        total_existed += existed
        all_results.extend(results)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "waves": [
            {"name": w, "count": len(s), "materials": [r["name"] for r in build_wave(w, s)]}
            for w, s in ALL_WAVES
        ],
        "total_created": total_created,
        "total_existed": total_existed,
        "results": [r for r in all_results if r["status"] == "created"],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "melodia_sdf_seed_batch.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    unreal.log(f"[SDFBatch] complete: {total_created} new, {total_existed} existing -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_all())
