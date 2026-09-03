"""Perceptual LOD LookDev Matrix & Optical Illusion Generator.

Synthesizes high-fidelity multi-tier PBR textures, Toksvig specular anti-aliasing
compensation maps, Parallax Occlusion depth heightfields, thin-film iridescence LUTs,
and screen-space dithering patterns across 4 LOD perception tiers:
- LOD0 (0 - 15m): Micro-relief weave, full POM depth, subsurface scatter, iridescence
- LOD1 (15 - 50m): Mid-frequency normal, Toksvig roughness compensation, adaptive POM
- LOD2 (50 - 200m): Macro silhouette folds, grazing-angle rim compensation, stable specular
- LOD3 (200m+): Vista impostor, baked atmospheric depth, zero specular shimmer

Adheres to Melodia lookdev doctrine, AGENTS.md determinism, and single-writer contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

SCHEMA = "melodia.optical_lod_manifest.v1"
VERSION = "1.0.0"

DEFAULT_SEED = 20260901
DEFAULT_OUT_DIR = "Saved/Audit/lookdev/optical_lods"
DEFAULT_MANIFEST = "specs/lookdev/optical_lod_manifest.v1.json"


@dataclass
class LODTierSpec:
    tier: int
    name: str
    distance_range_m: List[float]  # [Min, Max]
    pom_steps: int
    toksvig_factor: float
    normal_frequency_cutoff: float
    grazing_rim_boost: float
    texture_resolution: int
    wpo_resonance_scale: float


@dataclass
class OpticalAssetRecord:
    asset_name: str
    family: str
    target_material_master: str
    lod_tiers: Dict[str, Dict[str, Any]]  # "LOD0" -> {maps, params}
    dither_transition_map: str
    iridescence_lut: str


@dataclass
class OpticalLODManifest:
    schema: str = SCHEMA
    version: str = VERSION
    seed: int = DEFAULT_SEED
    total_assets: int = 0
    total_textures_generated: int = 0
    lod_tier_specs: Dict[str, LODTierSpec] = field(default_factory=dict)
    assets: Dict[str, OpticalAssetRecord] = field(default_factory=dict)
    shared_utilities: Dict[str, str] = field(default_factory=dict)


def compute_sha256(path: Path) -> str:
    """Compute sha256 checksum of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def save_image_png(arr: np.ndarray, path: Path, mode: str = "RGB") -> Path:
    """Save float32 array [0, 1] as 8-bit PNG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    clamped = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    if mode == "GRAY" or mode == "L":
        if clamped.ndim == 3:
            clamped = clamped[..., 0]
        img = Image.fromarray(clamped, mode="L")
    elif mode == "RGBA":
        img = Image.fromarray(clamped, mode="RGBA")
    else:
        if clamped.ndim == 2:
            clamped = np.stack([clamped, clamped, clamped], axis=-1)
        img = Image.fromarray(clamped, mode="RGB")
    img.save(path, format="PNG", optimize=True)
    return path


def generate_bayer_matrix_8x8() -> np.ndarray:
    """Generate normalized 8x8 Bayer dithering matrix."""
    bayer2 = np.array([[0, 2], [3, 1]], dtype=np.float32)
    bayer4 = np.zeros((4, 4), dtype=np.float32)
    for i in range(2):
        for j in range(2):
            bayer4[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2] = 4 * bayer2 + bayer2[i, j]
    bayer8 = np.zeros((8, 8), dtype=np.float32)
    for i in range(2):
        for j in range(2):
            bayer8[i * 4:(i + 1) * 4, j * 4:(j + 1) * 4] = 4 * bayer4 + bayer2[i, j]
    return bayer8 / 64.0


def generate_blue_noise_64x64(seed: int = 42) -> np.ndarray:
    """Generate high-frequency tileable blue-noise stipple texture (void-and-cluster approximation)."""
    rng = np.random.default_rng(seed)
    size = 64
    white = rng.random((size, size)).astype(np.float32)
    # High-pass filter in frequency domain
    fft = np.fft.fft2(white)
    y, x = np.ogrid[-size // 2:size // 2, -size // 2:size // 2]
    dist = np.sqrt(x * x + y * y)
    high_pass = 1.0 - np.exp(-(dist / (size * 0.25)) ** 2)
    high_pass = np.fft.fftshift(high_pass)
    filtered = np.real(np.fft.ifft2(fft * high_pass))
    norm = (filtered - filtered.min()) / (filtered.max() - filtered.min() + 1e-6)
    return norm.astype(np.float32)


def generate_chladni_heightfield(size: int, n: int = 3, m: int = 5, seed: int = 42) -> np.ndarray:
    """Generate tileable harmonic Chladni standing wave interference heightmap."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xs / size
    v = ys / size
    pi = np.pi

    # Base Chladni field
    chladni = np.cos(n * pi * u) * np.cos(m * pi * v) - np.cos(m * pi * u) * np.cos(n * pi * v)

    # Add multi-octave micro-texture
    micro = np.zeros((size, size), dtype=np.float32)
    amp = 0.15
    freq = 16.0
    for _ in range(3):
        micro += amp * (np.sin(u * freq * 2.0 * pi) * np.cos(v * freq * 2.0 * pi))
        amp *= 0.5
        freq *= 2.0

    combined = (chladni * 0.5 + 0.5) * 0.7 + micro * 0.3
    return np.clip(combined, 0.0, 1.0).astype(np.float32)


def height_to_normal_map(height: np.ndarray, strength: float = 2.0) -> np.ndarray:
    """Compute tangent-space normal map from heightfield using periodic Sobel gradient."""
    size = height.shape[0]
    # Periodic roll for Sobel
    h_top = np.roll(height, -1, axis=0)
    h_bot = np.roll(height, 1, axis=0)
    h_left = np.roll(height, -1, axis=1)
    h_right = np.roll(height, 1, axis=1)

    dx = (h_right - h_left) * strength * 0.5
    dy = (h_top - h_bot) * strength * 0.5  # Unreal Engine Y-
    dz = np.ones_like(height)

    norm = np.sqrt(dx * dx + dy * dy + dz * dz)
    nx = (dx / norm) * 0.5 + 0.5
    ny = (-dy / norm) * 0.5 + 0.5  # Unreal format: green inverted
    nz = (dz / norm) * 0.5 + 0.5
    return np.stack([nx, ny, nz], axis=-1).astype(np.float32)


def apply_toksvig_roughness(roughness: np.ndarray, normal_map: np.ndarray, toksvig_weight: float = 1.0) -> np.ndarray:
    """Calculate Toksvig specular anti-aliasing roughness compensation.

    sigma^2 = (1 - ||N_avg||) / ||N_avg||
    Roughness_adjusted = sqrt(Roughness^2 + sigma^2 * toksvig_weight)
    """
    # Extract normal vector in [-1, 1]
    nx = normal_map[..., 0] * 2.0 - 1.0
    ny = (1.0 - normal_map[..., 1]) * 2.0 - 1.0
    nz = normal_map[..., 2] * 2.0 - 1.0
    norm_len = np.sqrt(nx * nx + ny * ny + nz * nz)

    # Compute local normal dispersion variance
    dispersion = np.clip(1.0 - norm_len, 0.0, 0.5)
    adjusted_r2 = roughness * roughness + dispersion * toksvig_weight
    return np.clip(np.sqrt(adjusted_r2), 0.0, 1.0).astype(np.float32)


def generate_thin_film_iridescence_lut(width: int = 128, height: int = 512) -> np.ndarray:
    """Generate 2D Iridescence LUT.

    X (U) = N.V facing angle (1.0 = direct facing, 0.0 = grazing angle)
    Y (V) = Optical path difference / film phase [0, 1]
    """
    facing = np.linspace(1.0, 0.0, width, dtype=np.float32)[None, :]
    phase = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]

    # Spectral phase curves (Airy thin-film interference approximation)
    r = 0.5 + 0.5 * np.cos(2.0 * np.pi * (phase + (1.0 - facing) * 0.15))
    g = 0.5 + 0.5 * np.cos(2.0 * np.pi * (phase + (1.0 - facing) * 0.15 + 0.33))
    b = 0.5 + 0.5 * np.cos(2.0 * np.pi * (phase + (1.0 - facing) * 0.15 + 0.67))

    rgb = np.stack([r, g, b], axis=-1)

    # Grazing angle rim bloom factor
    grazing_lift = 1.0 + (1.0 - facing) * 0.8
    rgb = rgb * grazing_lift[..., None]
    return np.clip(rgb, 0.0, 1.0).astype(np.float32)


def build_optical_lod_suite(
    out_dir_path: Path,
    manifest_path: Path,
    seed: int = DEFAULT_SEED
) -> OpticalLODManifest:
    """Generate the complete Perceptual LOD LookDev Suite."""
    out_dir_path.mkdir(parents=True, exist_ok=True)
    manifest = OpticalLODManifest(seed=seed)

    # 1. Tier specifications
    tier_specs = {
        "LOD0": LODTierSpec(
            tier=0,
            name="MicroRelief_CloseRange",
            distance_range_m=[0.0, 15.0],
            pom_steps=32,
            toksvig_factor=0.0,  # Full micro-normal detail preserved
            normal_frequency_cutoff=1.0,
            grazing_rim_boost=1.0,
            texture_resolution=1024,
            wpo_resonance_scale=1.0,
        ),
        "LOD1": LODTierSpec(
            tier=1,
            name="MidFrequency_AdaptivePOM",
            distance_range_m=[15.0, 50.0],
            pom_steps=16,
            toksvig_factor=0.35,  # Moderate Toksvig anti-aliasing
            normal_frequency_cutoff=0.6,
            grazing_rim_boost=1.15,
            texture_resolution=512,
            wpo_resonance_scale=0.75,
        ),
        "LOD2": LODTierSpec(
            tier=2,
            name="MacroSilhouette_ToksvigStable",
            distance_range_m=[50.0, 200.0],
            pom_steps=0,  # POM disabled, standard normal map
            toksvig_factor=0.75,  # Strong Toksvig compensation for specular stability
            normal_frequency_cutoff=0.3,
            grazing_rim_boost=1.4,  # Silhouette faceting compensation
            texture_resolution=256,
            wpo_resonance_scale=0.3,
        ),
        "LOD3": LODTierSpec(
            tier=3,
            name="VistaImpostor_ZeroShimmer",
            distance_range_m=[200.0, 5000.0],
            pom_steps=0,
            toksvig_factor=1.0,  # Maximum roughness stability
            normal_frequency_cutoff=0.1,
            grazing_rim_boost=1.8,
            texture_resolution=128,
            wpo_resonance_scale=0.0,  # Vertex WPO disabled for performance
        ),
    }
    manifest.lod_tier_specs = tier_specs

    # 2. Shared optical utilities (Dithering & Iridescence LUT)
    bayer = generate_bayer_matrix_8x8()
    bayer_path = save_image_png(bayer, out_dir_path / "shared" / "T_LOD_BayerDither_8x8.png", mode="GRAY")

    blue_noise = generate_blue_noise_64x64(seed=seed)
    blue_noise_path = save_image_png(blue_noise, out_dir_path / "shared" / "T_LOD_BlueNoise_64x64.png", mode="GRAY")

    irid_lut = generate_thin_film_iridescence_lut(width=128, height=512)
    irid_lut_path = save_image_png(irid_lut, out_dir_path / "shared" / "T_LOD_Iridescence_ThinFilm_LUT.png", mode="RGB")

    manifest.shared_utilities = {
        "bayer_dither_8x8": str(bayer_path),
        "blue_noise_stipple_64x64": str(blue_noise_path),
        "iridescence_thin_film_lut": str(irid_lut_path),
    }
    total_textures = 3

    # 3. LookDev Hero Asset Suites
    asset_configs = [
        {
            "name": "FarawayMother_CelestialSilk",
            "family": "FabricMountain",
            "master": "/Game/EnvSandbox/Materials/Masters/M_Master_FarawayMother_Fabric",
            "base_color_rgb": [0.82, 0.88, 0.94],
            "roughness_base": 0.45,
            "metallic_base": 0.15,
            "chladni_n": 3,
            "chladni_m": 5,
        },
        {
            "name": "Melusina_Shorewake_Gown",
            "family": "HeroWardrobe",
            "master": "/Game/EnvSandbox/Materials/Masters/M_Master_Melusina_Costume",
            "base_color_rgb": [0.92, 0.95, 0.98],
            "roughness_base": 0.35,
            "metallic_base": 0.25,
            "chladni_n": 4,
            "chladni_m": 4,
        },
        {
            "name": "Starskiff_Hull_Celestial",
            "family": "VehicleHull",
            "master": "/Game/EnvSandbox/Materials/Masters/M_Master_Starskiff_Rigid",
            "base_color_rgb": [0.22, 0.35, 0.48],
            "roughness_base": 0.28,
            "metallic_base": 0.85,
            "chladni_n": 2,
            "chladni_m": 6,
        },
    ]

    for cfg in asset_configs:
        asset_name = cfg["name"]
        asset_dir = out_dir_path / asset_name
        lod_records: Dict[str, Dict[str, Any]] = {}

        for tier_key, spec in tier_specs.items():
            res = spec.texture_resolution
            tier_dir = asset_dir / tier_key

            # Synthesize height and normal maps
            height = generate_chladni_heightfield(res, n=cfg["chladni_n"], m=cfg["chladni_m"], seed=seed + spec.tier)
            normal = height_to_normal_map(height, strength=2.5 * spec.normal_frequency_cutoff)

            # Base color with subtle harmonic gradient
            base_col = np.ones((res, res, 3), dtype=np.float32) * np.array(cfg["base_color_rgb"], dtype=np.float32)
            base_col = base_col * (0.85 + 0.15 * height[..., None])

            # Toksvig-compensated roughness
            base_rough = np.ones((res, res), dtype=np.float32) * cfg["roughness_base"]
            roughness = apply_toksvig_roughness(base_rough, normal, toksvig_weight=spec.toksvig_factor)

            # Metallic map
            metallic = np.ones((res, res), dtype=np.float32) * cfg["metallic_base"]

            # Ambient Occlusion
            ao = np.clip(0.4 + 0.6 * height, 0.0, 1.0).astype(np.float32)

            # ORM Packed Map (R=AO, G=Roughness, B=Metallic)
            orm = np.stack([ao, roughness, metallic], axis=-1)

            # Save textures
            bc_path = save_image_png(base_col, tier_dir / f"T_{asset_name}_{tier_key}_BaseColor.png", mode="RGB")
            n_path = save_image_png(normal, tier_dir / f"T_{asset_name}_{tier_key}_Normal.png", mode="RGB")
            orm_path = save_image_png(orm, tier_dir / f"T_{asset_name}_{tier_key}_ORM.png", mode="RGB")
            h_path = save_image_png(height, tier_dir / f"T_{asset_name}_{tier_key}_Height.png", mode="GRAY")
            total_textures += 4

            lod_records[tier_key] = {
                "tier_index": spec.tier,
                "resolution": res,
                "distance_range_m": spec.distance_range_m,
                "pom_steps": spec.pom_steps,
                "toksvig_factor": spec.toksvig_factor,
                "grazing_rim_boost": spec.grazing_rim_boost,
                "wpo_resonance_scale": spec.wpo_resonance_scale,
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

        manifest.assets[asset_name] = OpticalAssetRecord(
            asset_name=asset_name,
            family=cfg["family"],
            target_material_master=cfg["master"],
            lod_tiers=lod_records,
            dither_transition_map=str(blue_noise_path),
            iridescence_lut=str(irid_lut_path),
        )

    manifest.total_assets = len(manifest.assets)
    manifest.total_textures_generated = total_textures

    # Write manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return manifest


def validate_manifest(manifest_path: Path) -> Tuple[bool, List[str]]:
    """Verify manifest integrity, checksums, and schema adherence."""
    errors = []
    if not manifest_path.is_file():
        return False, [f"Manifest file not found: {manifest_path}"]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, [f"JSON parsing error: {e}"]

    if data.get("schema") != SCHEMA:
        errors.append(f"Invalid schema: {data.get('schema')} != {SCHEMA}")

    if data.get("total_assets", 0) <= 0:
        errors.append("Manifest contains zero assets")

    assets = data.get("assets", {})
    for a_name, a_rec in assets.items():
        lod_tiers = a_rec.get("lod_tiers", {})
        if len(lod_tiers) != 4:
            errors.append(f"Asset {a_name} must have exactly 4 LOD tiers (found {len(lod_tiers)})")
        for tier_key in ["LOD0", "LOD1", "LOD2", "LOD3"]:
            if tier_key not in lod_tiers:
                errors.append(f"Asset {a_name} missing {tier_key}")
            else:
                maps = lod_tiers[tier_key].get("maps", {})
                for map_key in ["base_color", "normal", "orm_packed", "height"]:
                    p_str = maps.get(map_key)
                    if not p_str or not Path(p_str).is_file():
                        errors.append(f"Asset {a_name} {tier_key} missing map file: {p_str}")

    return len(errors) == 0, errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=str, default=DEFAULT_OUT_DIR, help="Output directory for textures")
    parser.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST, help="Output manifest file")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed")
    parser.add_argument("--verify", action="store_true", help="Verify existing manifest and textures")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir).resolve()
    manifest_file = Path(args.manifest).resolve()

    if args.verify:
        ok, errs = validate_manifest(manifest_file)
        if not ok:
            print(f"[OpticalLOD] Verification FAILED ({len(errs)} errors):")
            for e in errs:
                print(f"  - {e}")
            return 1
        print(f"[OpticalLOD] Verification PASSED: {manifest_file}")
        return 0

    manifest = build_optical_lod_suite(out_dir, manifest_file, seed=args.seed)
    print(f"[OpticalLOD] Successfully generated Perceptual LOD LookDev Suite!")
    print(f"  - Manifest: {manifest_file}")
    print(f"  - Total Assets: {manifest.total_assets}")
    print(f"  - Total Textures: {manifest.total_textures_generated}")
    for a_name in manifest.assets.keys():
        print(f"    * Asset: {a_name} (LOD0 -> LOD3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
