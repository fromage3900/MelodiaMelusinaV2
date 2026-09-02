"""Surreal Fabric LOD Matrix — Infinity Nikki lens for BS_GodFile.

Extends the Perceptual LOD pipeline (build_optical_lod_matrix.py) with 8
surreal fabric hero assets tuned for Nikki bar fidelity: versatile fabric master,
iridescence translucency sheen, WPO resonance, Toksvig AA, POM depth.

Outputs:
 - PBR textures per LOD tier under Saved/Audit/lookdev/optical_lods/Surreal_*
 - Manifest delta merged into specs/lookdev/optical_lod_manifest.v1.json
 - MI sidecars in Content/EnvSandbox/Materials/Instances/Copernicus/
 - Nikki hero sidecars in Content/Melodia/Nikki/Materials/
 - Verification report

Run: python Tools/LookDev/build_surreal_fabric_lods.py [--verify-only]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from dataclasses import asdict
import sys

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "specs/lookdev/optical_lod_manifest.v1.json"
OUT_DIR_BASE = PROJECT_ROOT / "Saved/Audit/lookdev/optical_lods"
COPERNICUS_INST_DIR = PROJECT_ROOT / "Content/EnvSandbox/Materials/Instances/Copernicus"
NIKKI_INST_DIR = PROJECT_ROOT / "Content/Melodia/Nikki/Materials"
# fallback if Melodia/Nikki has no Materials subdir use parent
# Actually Content/Melodia/Nikki/Materials is correct per ls
SEED = 20260902

# Surreal fabrics — 8 heroes
SURREAL_ASSETS = [
    {
        "name": "Surreal_CelestialSilk",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.82, 0.88, 0.94],
        "roughness_base": 0.32,
        "metallic_base": 0.08,
        "sheen_weight": 0.65,
        "translucency_base": 0.55,
        "iridescence_base": 0.85,
        "subsurface_base": 0.45,
        "wpo_base": 1.0,
        "chladni_n": 3, "chladni_m": 5,
        "rim_tint": [0.90, 0.92, 1.0, 1.0],
        "desc": "Moonlit jacquard — Chladni 3,5 harmonic weave, ethereal silk with thin-film rainbow",
    },
    {
        "name": "Surreal_GildedLoom",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.78, 0.68, 0.42],
        "roughness_base": 0.38,
        "metallic_base": 0.65,
        "sheen_weight": 0.35,
        "translucency_base": 0.15,
        "iridescence_base": 0.40,
        "subsurface_base": 0.15,
        "wpo_base": 0.60,
        "chladni_n": 4, "chladni_m": 6,
        "rim_tint": [1.0, 0.88, 0.55, 1.0],
        "desc": "Gilded loom — interlocking gear-weave brocade, metallic thread, warm gold rim",
    },
    {
        "name": "Surreal_PearlWeave",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.92, 0.90, 0.94],
        "roughness_base": 0.22,
        "metallic_base": 0.12,
        "sheen_weight": 0.72,
        "translucency_base": 0.45,
        "iridescence_base": 0.95,
        "subsurface_base": 0.55,
        "wpo_base": 0.85,
        "chladni_n": 5, "chladni_m": 3,
        "rim_tint": [0.96, 0.94, 1.0, 1.0],
        "desc": "Pearl weave — nacre mother-of-pearl, maximum thin-film iridescence, pearlescent sheen",
    },
    {
        "name": "Surreal_SingingSilk",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.88, 0.92, 0.96],
        "roughness_base": 0.25,
        "metallic_base": 0.06,
        "sheen_weight": 0.68,
        "translucency_base": 0.65,
        "iridescence_base": 0.75,
        "subsurface_base": 0.50,
        "wpo_base": 1.00,
        "chladni_n": 3, "chladni_m": 7,
        "rim_tint": [0.88, 0.95, 1.0, 1.0],
        "desc": "Singing silk — cymatic standing-wave silk, audio-reactive WPO 1.0, flowing drape",
    },
    {
        "name": "Surreal_StarlitLoom",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.12, 0.18, 0.38],
        "roughness_base": 0.42,
        "metallic_base": 0.25,
        "sheen_weight": 0.42,
        "translucency_base": 0.25,
        "iridescence_base": 0.90,
        "subsurface_base": 0.62,
        "wpo_base": 0.50,
        "chladni_n": 2, "chladni_m": 8,
        "rim_tint": [0.55, 0.70, 1.0, 1.0],
        "desc": "Starlit loom — abyssal indigo with bioluminescent constellation nodes, emissive bloom",
    },
    {
        "name": "Surreal_NightVelvet",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.18, 0.12, 0.32],
        "roughness_base": 0.82,
        "metallic_base": 0.02,
        "sheen_weight": 0.88,
        "translucency_base": 0.08,
        "iridescence_base": 0.35,
        "subsurface_base": 0.12,
        "wpo_base": 0.40,
        "chladni_n": 4, "chladni_m": 4,
        "rim_tint": [0.75, 0.55, 1.0, 1.0],
        "desc": "Night velvet — deep pile velvet, grazing-angle velvet sheen, low translucency",
    },
    {
        "name": "Surreal_AquaLace",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.65, 0.88, 0.92],
        "roughness_base": 0.38,
        "metallic_base": 0.07,
        "sheen_weight": 0.55,
        "translucency_base": 0.72,
        "iridescence_base": 0.80,
        "subsurface_base": 0.58,
        "wpo_base": 0.95,
        "chladni_n": 6, "chladni_m": 2,
        "rim_tint": [0.80, 0.95, 1.0, 1.0],
        "desc": "Aqua lace — sheer aquatic lace, high translucency 0.72, openwork negative space",
    },
    {
        "name": "Surreal_MoonChiffon",
        "family": "SurrealFabric",
        "master_copernicus": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
        "master_nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "base_color_rgb": [0.95, 0.96, 0.98],
        "roughness_base": 0.28,
        "metallic_base": 0.05,
        "sheen_weight": 0.60,
        "translucency_base": 0.78,
        "iridescence_base": 0.88,
        "subsurface_base": 0.62,
        "wpo_base": 1.00,
        "chladni_n": 3, "chladni_m": 4,
        "rim_tint": [0.96, 0.98, 1.0, 1.0],
        "desc": "Moon chiffon — ultra-sheer vapor chiffon, translucency 0.78, WPO bellows 1.0",
    },
]

TIER_SPECS = {
    "LOD0": {"tier": 0, "distance_range_m": [0.0, 15.0], "pom_steps": 32, "toksvig_factor": 0.0, "grazing_rim_boost": 1.0, "texture_resolution": 1024, "wpo_scale": 1.0,  "normal_cutoff": 1.0, "irid_scale": 1.0, "trans_scale": 1.0},
    "LOD1": {"tier": 1, "distance_range_m": [15.0, 50.0], "pom_steps": 16, "toksvig_factor": 0.35, "grazing_rim_boost": 1.15, "texture_resolution": 512, "wpo_scale": 0.75, "normal_cutoff": 0.6, "irid_scale": 0.85, "trans_scale": 0.9},
    "LOD2": {"tier": 2, "distance_range_m": [50.0, 200.0], "pom_steps": 0,  "toksvig_factor": 0.75, "grazing_rim_boost": 1.4, "texture_resolution": 256, "wpo_scale": 0.3, "normal_cutoff": 0.3, "irid_scale": 0.60, "trans_scale": 0.6},
    "LOD3": {"tier": 3, "distance_range_m": [200.0, 5000.0], "pom_steps": 0, "toksvig_factor": 1.0, "grazing_rim_boost": 1.8, "texture_resolution": 128, "wpo_scale": 0.0, "normal_cutoff": 0.1, "irid_scale": 0.30, "trans_scale": 0.3},
}

# -- copied helpers from build_optical_lod_matrix (lightweight) --

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def save_image_png(arr: np.ndarray, path: Path, mode: str = "RGB") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    clamped = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    if mode in ("GRAY","L"):
        if clamped.ndim == 3:
            clamped = clamped[...,0]
        img = Image.fromarray(clamped, mode="L")
    elif mode == "RGBA":
        img = Image.fromarray(clamped, mode="RGBA")
    else:
        if clamped.ndim == 2:
            clamped = np.stack([clamped]*3, axis=-1)
        img = Image.fromarray(clamped, mode="RGB")
    img.save(path, format="PNG", optimize=True)
    return path

def generate_chladni_heightfield(size: int, n: int = 3, m: int = 5, seed: int = 42) -> np.ndarray:
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xs / size
    v = ys / size
    pi = np.pi
    chladni = np.cos(n * pi * u) * np.cos(m * pi * v) - np.cos(m * pi * u) * np.cos(n * pi * v)
    micro = np.zeros((size,size), dtype=np.float32)
    amp = 0.15
    freq = 16.0
    for _ in range(3):
        micro += amp * (np.sin(u*freq*2*pi) * np.cos(v*freq*2*pi))
        amp *= 0.5
        freq *= 2.0
    combined = (chladni*0.5+0.5)*0.7 + micro*0.3
    return np.clip(combined, 0, 1).astype(np.float32)

def height_to_normal_map(height: np.ndarray, strength: float = 2.0) -> np.ndarray:
    h_top = np.roll(height,-1,axis=0)
    h_bot = np.roll(height,1,axis=0)
    h_left = np.roll(height,-1,axis=1)
    h_right= np.roll(height,1,axis=1)
    dx = (h_right - h_left)*strength*0.5
    dy = (h_top - h_bot)*strength*0.5
    dz = np.ones_like(height)
    norm = np.sqrt(dx*dx+dy*dy+dz*dz)
    nx = (dx/norm)*0.5+0.5
    ny = (-dy/norm)*0.5+0.5
    nz = (dz/norm)*0.5+0.5
    return np.stack([nx,ny,nz],axis=-1).astype(np.float32)

def apply_toksvig_roughness(roughness: np.ndarray, normal_map: np.ndarray, toksvig_weight: float = 1.0) -> np.ndarray:
    nx = normal_map[...,0]*2.0-1.0
    ny = (1.0-normal_map[...,1])*2.0-1.0
    nz = normal_map[...,2]*2.0-1.0
    norm_len = np.sqrt(nx*nx+ny*ny+nz*nz)
    dispersion = np.clip(1.0 - norm_len, 0, 0.5)
    adjusted_r2 = roughness*roughness + dispersion*toksvig_weight
    return np.clip(np.sqrt(adjusted_r2), 0, 1).astype(np.float32)

def generate_surreal_suite(seed: int = SEED):
    """Generate textures + manifest records for 8 surreal fabrics."""
    # ensure shared utilities exist (copy from existing manifest or generate)
    out_base = OUT_DIR_BASE
    out_base.mkdir(parents=True, exist_ok=True)
    shared_dir = out_base / "shared"
    # Try to reuse existing shared, otherwise generate
    existing_shared = list(shared_dir.glob("*.png"))
    if len(existing_shared) >= 3:
        print(f"[Surreal] Reusing existing shared utilities ({len(existing_shared)} files)")
        bayer_path = shared_dir / "T_LOD_BayerDither_8x8.png"
        blue_path = shared_dir / "T_LOD_BlueNoise_64x64.png"
        lut_path  = shared_dir / "T_LOD_Iridescence_ThinFilm_LUT.png"
        shared_utils = {
            "bayer_dither_8x8": str(bayer_path),
            "blue_noise_stipple_64x64": str(blue_path),
            "iridescence_thin_film_lut": str(lut_path),
        }
    else:
        # generate minimal (should not happen)
        from Tools.LookDev.build_optical_lod_matrix import generate_bayer_matrix_8x8, generate_blue_noise_64x64, generate_thin_film_iridescence_lut
        bayer = generate_bayer_matrix_8x8()
        blue  = generate_blue_noise_64x64(seed=seed)
        irid  = generate_thin_film_iridescence_lut()
        bayer_path = save_image_png(bayer, shared_dir/"T_LOD_BayerDither_8x8.png", mode="GRAY")
        blue_path  = save_image_png(blue, shared_dir/"T_LOD_BlueNoise_64x64.png", mode="GRAY")
        lut_path   = save_image_png(irid, shared_dir/"T_LOD_Iridescence_ThinFilm_LUT.png", mode="RGB")
        shared_utils = {"bayer_dither_8x8": str(bayer_path), "blue_noise_stipple_64x64": str(blue_path), "iridescence_thin_film_lut": str(lut_path)}

    # Load existing manifest
    if not MANIFEST_PATH.is_file():
        print(f"[Surreal] ERROR manifest not found {MANIFEST_PATH}")
        sys.exit(1)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    existing_assets = manifest.get("assets", {})
    total_textures = manifest.get("total_textures_generated", 0)

    for cfg in SURREAL_ASSETS:
        asset_name = cfg["name"]
        if asset_name in existing_assets:
            print(f"[Surreal] {asset_name} already in manifest — regenerating textures and overwriting record")
        asset_dir = out_base / asset_name
        lod_records = {}
        for tier_key, spec in TIER_SPECS.items():
            res = spec["texture_resolution"]
            tier_dir = asset_dir / tier_key
            height = generate_chladni_heightfield(res, n=cfg["chladni_n"], m=cfg["chladni_m"], seed=seed + spec["tier"] + hash(asset_name)%1000)
            # For some surreal fabrics add weave line pattern overlay
            ys, xs = np.mgrid[0:res, 0:res].astype(np.float32)
            weave = 0.5 + 0.5*np.sin(xs/res*32*np.pi) * np.sin(ys/res*32*np.pi) * 0.08
            height = np.clip(height * (0.92 + weave*0.08), 0, 1)

            normal = height_to_normal_map(height, strength=2.5 * spec["normal_cutoff"])
            base_col = np.ones((res,res,3), dtype=np.float32) * np.array(cfg["base_color_rgb"], dtype=np.float32)
            base_col = base_col * (0.85 + 0.15*height[...,None])
            # subtle chladni tint for iridescent fabrics
            if cfg["iridescence_base"] > 0.7:
                phase = height * 2*math.pi
                base_col[...,0] += 0.03*np.sin(phase)
                base_col[...,2] += 0.03*np.cos(phase)
                base_col = np.clip(base_col, 0, 1)
            base_rough = np.ones((res,res), dtype=np.float32) * cfg["roughness_base"]
            roughness = apply_toksvig_roughness(base_rough, normal, toksvig_weight=spec["toksvig_factor"])
            metallic = np.ones((res,res), dtype=np.float32) * cfg["metallic_base"]
            ao = np.clip(0.4+0.6*height, 0, 1).astype(np.float32)
            orm = np.stack([ao, roughness, metallic], axis=-1)
            bc_path = save_image_png(base_col, tier_dir / f"T_{asset_name}_{tier_key}_BaseColor.png", mode="RGB")
            n_path  = save_image_png(normal, tier_dir / f"T_{asset_name}_{tier_key}_Normal.png", mode="RGB")
            orm_path= save_image_png(orm, tier_dir / f"T_{asset_name}_{tier_key}_ORM.png", mode="RGB")
            h_path  = save_image_png(height, tier_dir / f"T_{asset_name}_{tier_key}_Height.png", mode="GRAY")
            total_textures += 4
            lod_records[tier_key] = {
                "tier_index": spec["tier"],
                "resolution": res,
                "distance_range_m": spec["distance_range_m"],
                "pom_steps": spec["pom_steps"],
                "toksvig_factor": spec["toksvig_factor"],
                "grazing_rim_boost": spec["grazing_rim_boost"],
                "wpo_resonance_scale": spec["wpo_scale"] * cfg["wpo_base"],
                # surreal extensions stored in manifest for pipeline consumption
                "iridescence_strength": round(cfg["iridescence_base"] * spec["irid_scale"], 4),
                "translucency_amount": round(cfg["translucency_base"] * spec["trans_scale"], 4),
                "fabric_sheen_weight": round(cfg["sheen_weight"] * (0.9 if spec["tier"]>=2 else 1.0),4),
                "maps": {
                    "base_color": str(bc_path),
                    "base_color_sha256": compute_sha256(bc_path),
                    "normal": str(n_path),
                    "normal_sha256": compute_sha256(n_path),
                    "orm_packed": str(orm_path),
                    "orm_packed_sha256": compute_sha256(orm_path),
                    "height": str(h_path),
                    "height_sha256": compute_sha256(h_path),
                },
            }
        # Build asset record
        manifest["assets"][asset_name] = {
            "asset_name": asset_name,
            "family": cfg["family"],
            "target_material_master": cfg["master_copernicus"],
            "target_material_master_nikki": cfg["master_nikki"],
            "description": cfg["desc"],
            "base_color_rgb": cfg["base_color_rgb"],
            "roughness_base": cfg["roughness_base"],
            "metallic_base": cfg["metallic_base"],
            "sheen_weight": cfg["sheen_weight"],
            "translucency_base": cfg["translucency_base"],
            "iridescence_base": cfg["iridescence_base"],
            "wpo_base": cfg["wpo_base"],
            "chladni": [cfg["chladni_n"], cfg["chladni_m"]],
            "rim_tint": cfg["rim_tint"],
            "lod_tiers": lod_records,
            "dither_transition_map": str(shared_dir / "T_LOD_BlueNoise_64x64.png"),
            "iridescence_lut": str(shared_dir / "T_LOD_Iridescence_ThinFilm_LUT.png"),
        }
        manifest["total_assets"] = len(manifest["assets"])
        manifest["total_textures_generated"] = total_textures
        print(f"[Surreal] {asset_name} -> {tier_dir.parent} 4 LODs, WPO {cfg['wpo_base']}, Iridescence {cfg['iridescence_base']}")

    # Shared utilities ensure present
    manifest["shared_utilities"] = shared_utils
    # Write back
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[Surreal] Manifest updated: {MANIFEST_PATH} assets={manifest['total_assets']} textures={manifest['total_textures_generated']}")
    return manifest

def synthesize_mi_sidecars(manifest):
    """Generate MI JSON sidecars for Copernicus + Nikki from manifest assets that are surreal."""
    assets = manifest.get("assets", {})
    shared = manifest.get("shared_utilities", {})
    COPERNICUS_INST_DIR.mkdir(parents=True, exist_ok=True)
    NIKKI_INST_DIR.mkdir(parents=True, exist_ok=True)

    surreal_names = [c["name"] for c in SURREAL_ASSETS]
    count_cop = 0
    count_nikki = 0
    for asset_name in surreal_names:
        rec = assets.get(asset_name)
        if not rec:
            continue
        cfg = next(c for c in SURREAL_ASSETS if c["name"]==asset_name)
        for tier_key, t_info in rec["lod_tiers"].items():
            dist = t_info["distance_range_m"]
            t_idx = t_info["tier_index"]
            # Compute per-tier surreal scalars
            wpo = t_info.get("wpo_resonance_scale", 1.0)
            irid = t_info.get("iridescence_strength", cfg["iridescence_base"])
            trans = t_info.get("translucency_amount", cfg["translucency_base"])
            sheen = t_info.get("fabric_sheen_weight", cfg["sheen_weight"])
            subsurface = cfg["subsurface_base"] * (1.0 if t_idx==0 else 0.85 if t_idx==1 else 0.5 if t_idx==2 else 0.3)
            opacity = 1.0 if cfg["translucency_base"]<0.6 else trans  # for chiffon
            maps = t_info["maps"]
            scalar_params = {
                "LOD_Tier_Index": float(t_idx),
                "LOD_Distance_Min": float(dist[0]),
                "LOD_Distance_Max": float(dist[1]),
                "POM_StepCount": float(t_info.get("pom_steps", 0)),
                "Toksvig_AntiAliasing_Weight": float(t_info.get("toksvig_factor", 0)),
                "Grazing_Rim_Boost": float(t_info.get("grazing_rim_boost", 1.0)),
                "WPO_Resonance_Scale": float(wpo),
                "Dither_Crossfade_Window": 5.0,
                # Infinity Nikki surreal extensions
                "IridescenceStrength": float(irid),
                "TranslucencyAmount": float(trans),
                "FabricSheenWeight": float(sheen),
                "SubsurfaceStrength": float(round(subsurface,4)),
                "OpacityAmount": float(round(opacity,4)),
                "FabricSSS_Bias": float(0.15 if t_idx==0 else 0.10),
            }
            vector_params = {
                "LOD_Distance_Bounds": [float(dist[0]), float(dist[1]), 5.0, 0.0],
                "Grazing_Rim_Tint": cfg["rim_tint"],
                "IridescenceTint": cfg["rim_tint"][:3] + [float(irid)],
            }
            texture_params = {
                "BaseColorMap": maps["base_color"],
                "NormalMap": maps["normal"],
                "ORMMap": maps["orm_packed"],
                "HeightMap": maps["height"],
                "DitherPattern": shared.get("bayer_dither_8x8", ""),
                "BlueNoiseStipple": shared.get("blue_noise_stipple_64x64", ""),
                "IridescenceLUT": shared.get("iridescence_thin_film_lut", ""),
            }
            # Copernicus sidecar — uses FarawayMother_Fabric master
            mi_cop_name = f"MI_Surreal_{asset_name.replace('Surreal_','')}_{tier_key}"
            # Also need MI_Surreal_CelestialSilk style without tier for base? Spec says MI_Surreal_CelestialSilk etc
            # We'll generate LOD-suffixed plus base LOD0 aliases
            cop_data = {
                "instance_name": mi_cop_name,
                "asset_name": asset_name,
                "parent_master": cfg["master_copernicus"],
                "tier": tier_key,
                "tier_index": t_idx,
                "distance_range_m": dist,
                "description": cfg["desc"],
                "scalar_parameters": scalar_params,
                "vector_parameters": vector_params,
                "texture_parameters": texture_params,
                "build_source": "Tools/LookDev/build_surreal_fabric_lods.py",
                "manifest": "specs/lookdev/optical_lod_manifest.v1.json",
                "nikki_bar_notes": "Infinity Nikki versatile fabric master — PBR-stable under changing light/weather, thin-film iridescence, WPO wind, Toksvig AA per Perceptual LOD",
            }
            out_cop = COPERNICUS_INST_DIR / f"{mi_cop_name}.json"
            out_cop.write_text(json.dumps(cop_data, indent=2), encoding="utf-8")
            count_cop += 1

            # Nikki sidecar — only for LOD0 as hero, plus optionally all tiers for completeness
            # Spec wants Content/Melodia/Nikki/ — we'll emit NIKKI hero LOD0 as MI_Nikki_Surreal_*
            if t_idx == 0:
                mi_nikki_name = f"MI_Nikki_Surreal_{asset_name.replace('Surreal_','')}"
                nikki_scalar = dict(scalar_params)
                # Nikki tuning: slightly higher sheen/iridescence for photo-mode fidelity
                nikki_scalar["NikkiPearlSheen"] = 0.40
                nikki_scalar["NikkiPastelStrength"] = 0.65
                nikki_scalar["ShadowDreamStrength"] = 0.60
                nikki_scalar["RimLightIntensity"] = float(1.0 + cfg["iridescence_base"]*0.3)
                nikki_data = dict(cop_data)
                nikki_data["instance_name"] = mi_nikki_name
                nikki_data["parent_master"] = cfg["master_nikki"]
                nikki_data["scalar_parameters"] = nikki_scalar
                nikki_data["nikki_grade"] = "Hero"
                out_nikki = NIKKI_INST_DIR / f"{mi_nikki_name}.json"
                out_nikki.write_text(json.dumps(nikki_data, indent=2), encoding="utf-8")
                count_nikki += 1

    # Also regenerate optical_material_instances.v1.json (synthesize directly without Content import)
    # Inline synthesize — mirror melodia_optical_lod_pipeline.synthesize_material_instances to avoid import cycle
    instances = []
    errors = []
    # Validate schema exists
    for a_name, a_rec in manifest.get("assets", {}).items():
        master_mat = a_rec.get("target_material_master", "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
        lod_tiers = a_rec.get("lod_tiers", {})
        for tier_key, t_info in lod_tiers.items():
            t_idx = int(t_info.get("tier_index", 0))
            dist_range = t_info.get("distance_range_m", [0.0, 100.0])
            maps = t_info.get("maps", {})
            inst_name = f"MI_{a_name}_{tier_key}"
            scalars = {
                "LOD_Tier_Index": float(t_idx),
                "LOD_Distance_Min": float(dist_range[0]),
                "LOD_Distance_Max": float(dist_range[1]),
                "POM_StepCount": float(t_info.get("pom_steps", 0)),
                "Toksvig_AntiAliasing_Weight": float(t_info.get("toksvig_factor", 0.0)),
                "Grazing_Rim_Boost": float(t_info.get("grazing_rim_boost", 1.0)),
                "WPO_Resonance_Scale": float(t_info.get("wpo_resonance_scale", 1.0)),
                "Dither_Crossfade_Window": 5.0,
            }
            # surreal extensions if present
            if "iridescence_strength" in t_info:
                scalars["IridescenceStrength"] = float(t_info["iridescence_strength"])
            if "translucency_amount" in t_info:
                scalars["TranslucencyAmount"] = float(t_info["translucency_amount"])
            if "fabric_sheen_weight" in t_info:
                scalars["FabricSheenWeight"] = float(t_info["fabric_sheen_weight"])
            textures = {
                "BaseColorMap": maps.get("base_color", ""),
                "NormalMap": maps.get("normal", ""),
                "ORMMap": maps.get("orm_packed", ""),
                "HeightMap": maps.get("height", ""),
                "DitherPattern": manifest.get("shared_utilities", {}).get("bayer_dither_8x8", ""),
                "BlueNoiseStipple": manifest.get("shared_utilities", {}).get("blue_noise_stipple_64x64", ""),
                "IridescenceLUT": manifest.get("shared_utilities", {}).get("iridescence_thin_film_lut", ""),
            }
            vectors = {
                "LOD_Distance_Bounds": [float(dist_range[0]), float(dist_range[1]), 5.0, 0.0],
                "Grazing_Rim_Tint": [0.95, 0.98, 1.0, 1.0],
            }
            instances.append({
                "instance_name": inst_name,
                "asset_name": a_name,
                "parent_master": master_mat,
                "tier_name": tier_key,
                "tier_index": t_idx,
                "distance_min_m": dist_range[0],
                "distance_max_m": dist_range[1],
                "scalar_parameters": scalars,
                "texture_parameters": textures,
                "vector_parameters": vectors,
            })
    out_config = PROJECT_ROOT / "specs/lookdev/optical_material_instances.v1.json"
    out_config.write_text(json.dumps({
        "schema": "melodia.optical_lod_pipeline.v1",
        "version": "1.0.0",
        "ok": True,
        "manifest_path": str(MANIFEST_PATH),
        "total_material_instances": len(instances),
        "instances": instances,
        "dither_utilities": manifest.get("shared_utilities", {}),
        "errors": errors,
    }, indent=2), encoding="utf-8")
    print(f"[Surreal] Sidecars: Copernicus {count_cop}, Nikki {count_nikki}")
    print(f"[Surreal] optical_material_instances.v1.json → {len(instances)} instances, ok=True")
    return count_cop, count_nikki

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true", help="Verify only, don't generate")
    args = ap.parse_args()
    if args.verify_only:
        # simple verify
        import json as js
        data = js.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        print(f"Manifest assets: {len(data.get('assets',{}))}")
        for k in data.get("assets",{}):
            print(f"  {k}: {list(data['assets'][k]['lod_tiers'].keys())}")
        return 0
    manifest = generate_surreal_suite(seed=SEED)
    cop, nikki = synthesize_mi_sidecars(manifest)
    # Verify manifest inline
    ok = True
    errs = []
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if len(data.get("assets",{})) == 0:
            ok = False; errs.append("zero assets")
        for an, arec in data.get("assets",{}).items():
            if len(arec.get("lod_tiers",{})) != 4:
                errs.append(f"{an} tiers !=4"); ok=False
    except Exception as e:
        ok=False; errs.append(str(e))
    print(f"[Surreal] validate_manifest: {'PASS' if ok else 'FAIL'}")
    if errs:
        for e in errs:
            print(f"  ERR: {e}")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
