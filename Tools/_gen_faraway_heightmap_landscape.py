#!/usr/bin/env python
"""
Faraway Mother — 8192x8192 16-bit RAW heightfield for UE Landscape import.

Sibling to Tools/_gen_faraway_heightmap.py (the 1k Nanite-mesh path, contract
"Nanite StaticMesh, no Landscape"). This generator materializes the OTHER lane:
the P2_FABRIC_MOUNTAIN_PLAN Layer-1 "Houdini heightfield -> UE Landscape
8192x8192", authorized by the owner 2026-09-21 after the Grok stage-1
Landscape ruling.

Design (hybrid profile — owner question "real heightmap as reference?"):
  - Real terrain is used as SILHOUETTE REFERENCE ONLY (reclining-figure ridge
    class, e.g. sleeping-giant formations). No DEM import: erosion noise reads
    as Earth geology and fights the "fabric behaves like geography" doctrine,
    and Docs/Monoliths/P1_FARAWAY_MOTHER_PLAN_2026-08-29.md forbids a clean
    giant-person read. --profile-dem flag exists for a literal DEM if the
    owner ever wants one.
  - Macro: anatomy anchored to the 7 STAGED instance XYs from
    Saved/Audit/faraway_mother_staging_report.md (head north at y~9000,
    cascade channel, shoulder ridge band, shoulder/torso valleys, limb flats),
    plus the EXACT swell formula from build_faraway_mother_height_aware_pcg.py
    (line 141) so the Landscape agrees with the offline ground ref the staged
    Z offsets were computed against.
  - Medium/micro: cloth-drape folds ORIENTED PERPENDICULAR to the macro
    gradient (real drape behavior), amplitudes per the P2 skill WPO stack
    (medium 100 m / 10-20 m, micro ~8 m / 1-2 m), same fold language as the
    1k generator.

UE import (documented in the manifest):
  - RAW 16-bit little-endian, row 0 = south (min Y). Value = 32768 + z_m at
    UE default ZScale=100 (1 unit = 1 m). Quad 256 cm -> 20,971.52 m field.
  - Center (-700, 600) so every staged instance XY fits inside.

Evidence: manifest_landscape_raw_v1.json carries seed, sha256(RAW), the
per-anchor probe table (bilinear-sampled ground Z at each staged XY = the
Z log the editor raycast is verified against), fold params, import recipe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "faraway_mother" / "fabric_ridge_terrain"

SEED = 20260829  # same family as the 1k generator + height-aware PCG manifests
SIZE = 8192
# Owner 2026-09-22: the terrain is the Universe Foundry field contract footprint,
# world X/Y -400000..+400000 uu (8 km square, centred on the origin).
EXTENT_M = 8000.0
QUAD_CM = EXTENT_M * 100.0 / SIZE
CENTER_X, CENTER_Y = 0.0, 0.0
# ANCHORS / PROBE_XYS / swell are authored in staged UE units; this maps them onto
# the 8 km footprint (head 9000 -> 3600 m). Heights and FOLDS stay in real metres.
ANATOMY_M_PER_UNIT = 0.4

# Anatomy anchors: (name, x, y, amp_m, sigma_along_m, sigma_across_m, rot_deg)
# rot = direction of the MAJOR axis (deg, world CCW from +x)
ANCHORS = [
    ("head_mound",        0.0,   9000.0,  +52.0, 1400.0, 1700.0,   0.0),
    ("shoulder_ridge", -700.0,   3650.0,  +26.0, 2600.0,  500.0,  44.3),  # band through (-2600,1800)->(1200,5500)
    ("shoulder_valley",  0.0,   -800.0,  -48.0, 1500.0, 1300.0,   0.0),
    ("torso_valley",   400.0,  -4200.0,  -95.0, 1900.0, 1700.0,   0.0),
    ("limbs_flat",       0.0,  -7800.0,   -6.0, 2200.0, 1800.0,   0.0),
    ("cascade_channel", -450.0, 7400.0, -22.0, 1300.0,  180.0, 111.4),  # groove (0,8600)->(-900,6200)
]

# Fold octaves: (wavelength_m, amp_m, phase_wobble_m, exponent)
FOLDS = [
    (100.0, 14.0, 7000.0, 1.5),
    (32.0,   4.5, 2600.0, 1.3),
    (8.0,    1.2,    0.0, 1.1),
]

SLOPE_REF = 0.5  # m/m — slope at which fold amplitude reaches full strength

# Staged instance XYs (faraway_mother_staging_report.md §1) for the probe table
PROBE_XYS = [
    ("FM_Ridge_HeadSilhouette_01",     0.0,  9000.0),
    ("FM_Ridge_Fabric_02",          1200.0,  5500.0),
    ("FM_Hair_Cascade_03",          -900.0,  6200.0),
    ("FM_Ridge_Fabric_04",         -2600.0,  1800.0),
    ("FM_Valley_Shoulder_05",          0.0,  -800.0),
    ("FM_Valley_Torso_06",           400.0, -4200.0),
    ("FM_Haze_Limbs_07",               0.0, -7800.0),
]


def swell(wx: np.ndarray, wy: np.ndarray) -> np.ndarray:
    """Exact staging synthetic ground (build_faraway_mother_height_aware_pcg.py)."""
    return 15.0 * np.sin(wx * 0.0004) + 12.0 * np.cos(wy * 0.0005)


def build_macro(wx: np.ndarray, wy: np.ndarray) -> np.ndarray:
    h = swell(wx, wy).astype(np.float32)
    for name, cx, cy, amp, sa, sb, rot in ANCHORS:
        th = math.radians(rot)
        dx = wx - cx
        dy = wy - cy
        u = dx * math.cos(th) + dy * math.sin(th)
        v = -dx * math.sin(th) + dy * math.cos(th)
        g = amp * np.exp(-(u * u / (2.0 * sa * sa) + v * v / (2.0 * sb * sb)))
        h += g.astype(np.float32)
        del g
    return h


def build_folds(macro: np.ndarray, wx: np.ndarray, wy: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    gx, gy = np.gradient(macro, QUAD_CM / 100.0, QUAD_CM / 100.0)
    slope = np.hypot(gx, gy)
    sn = np.clip(slope / SLOPE_REF, 0.0, 1.0).astype(np.float32)
    del slope
    inv = 1.0 / (np.hypot(gx, gy) + 1e-6)
    dx = (gx * inv).astype(np.float32)
    dy = (gy * inv).astype(np.float32)
    del gx, gy, inv
    # drape coordinate: position projected on the downhill direction
    u = (wx * dx + wy * dy).astype(np.float32)
    del dx, dy

    folds = np.zeros_like(macro)
    for i, (lam, amp, wob, expn) in enumerate(FOLDS):
        phase = 2.0 * np.pi * u / lam
        if wob > 0.0:
            phase = phase + float(rng.uniform(0, 2 * math.pi)) + 1.2 * np.sin(wy * 2.0 * np.pi / wob)
        ridge = np.power(np.clip(1.0 - np.abs(np.sin(phase)), 0.0, 1.0), expn).astype(np.float32)
        if i == len(FOLDS) - 1:  # micro survives slightly on flats
            folds += amp * ridge * (0.4 + 0.6 * sn)
        else:
            folds += amp * ridge * sn
        del phase, ridge
    return folds


def bilinear_sample(h: np.ndarray, wx: float, wy: float, min_x: float, min_y: float, quad_m: float) -> float:
    fx = (wx - min_x) / quad_m - 0.5
    fy = (wy - min_y) / quad_m - 0.5
    i0, j0 = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - i0, fy - j0
    i0 = max(0, min(SIZE - 2, i0)); j0 = max(0, min(SIZE - 2, j0))
    a = h[j0, i0] * (1 - tx) + h[j0, i0 + 1] * tx
    b = h[j0 + 1, i0] * (1 - tx) + h[j0 + 1, i0 + 1] * tx
    return float(a * (1 - ty) + b * ty)


def main() -> None:
    global SIZE, QUAD_CM
    ap = argparse.ArgumentParser(description="Faraway Mother 8k Landscape RAW heightfield")
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--out-dir", type=str, default=str(OUT_DIR))
    ap.add_argument("--profile-dem", type=str, default=None,
                    help="Optional literal DEM (png/tif 16-bit) to use as macro instead of authored anatomy")
    args = ap.parse_args()
    SIZE = args.size
    QUAD_CM = EXTENT_M * 100.0 / SIZE
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    quad_m = QUAD_CM / 100.0
    field_m = SIZE * quad_m
    min_x, min_y = CENTER_X - field_m / 2.0, CENTER_Y - field_m / 2.0
    rng = np.random.default_rng(SEED)

    print(f"[FM-heightfield] size={SIZE} quad={QUAD_CM}cm field={field_m:.2f}m "
          f"center=({CENTER_X},{CENTER_Y}) seed={SEED}")

    # World coordinate vectors (broadcast, never materialize the mgrid)
    wx = (min_x + (np.arange(SIZE, dtype=np.float64) + 0.5) * quad_m).astype(np.float32)
    wy = (min_y + (np.arange(SIZE, dtype=np.float64) + 0.5) * quad_m).astype(np.float32)
    wx_row = wx[np.newaxis, :]          # x varies along columns
    wy_col = wy[:, np.newaxis]          # y varies along rows (row 0 = south/min Y)

    k = ANATOMY_M_PER_UNIT
    macro = build_macro(wx_row / k, wy_col / k)
    folds = build_folds(macro, wx_row, wy_col, rng)
    height = macro + folds
    del macro, folds

    # UE heightmap convention: z_cm = (level - 32768) * Z_SCALE / 128.
    # Z_SCALE 50 -> +-128 m range at 3.9 mm per level (1 m levels erased the micro folds).
    Z_SCALE = 50.0
    cm_per_level = Z_SCALE / 128.0
    z_lo, z_hi = -32768 * cm_per_level / 100.0, 32767 * cm_per_level / 100.0
    np.clip(height, z_lo, z_hi, out=height)
    print(f"[FM-heightfield] z range {height.min():.2f}..{height.max():.2f} m "
          f"mean {height.mean():.2f} m")

    raw = np.rint(32768.0 + height * 100.0 / cm_per_level).astype(np.uint16)
    raw_path = out_dir / "T_FarawayMother_FabricRidge_Height_8k_Landscape.raw"
    raw.tofile(raw_path)
    # 16-bit PNG twin — pixel data identical to the RAW (importers that want an image)
    png16_path = out_dir / "T_FarawayMother_FabricRidge_Height_8k_MeshTerrain.png"
    Image.fromarray(raw, mode="I;16").save(png16_path)
    sha = hashlib.sha256()
    with open(raw_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)

    # Previews (8-bit, saved north-up: flipud so image top = max Y = north)
    def save_preview(arr: np.ndarray, path: Path, size: int) -> None:
        lo, hi = float(arr.min()), float(arr.max())
        img = ((arr - lo) / max(hi - lo, 1e-6) * 255.0).astype(np.uint8)
        img = np.flipud(img)  # row 0 of data = south; display north-up
        Image.fromarray(img).resize((size, size), Image.LANCZOS).save(path)

    prev_path = out_dir / "T_FarawayMother_FabricRidge_Height_8k_Landscape_preview.png"
    save_preview(height, prev_path, 2048)

    crops = {
        "head_cascade": (-2500.0, 5800.0, 1500.0, 9800.0),
        "ridge_band":   (-3400.0, 1200.0, 2000.0, 6200.0),
        "torso":        (-1200.0, -5600.0, 1800.0, -2600.0),
    }
    for name, (x0, y0, x1, y1) in crops.items():
        x0, y0, x1, y1 = x0 * k, y0 * k, x1 * k, y1 * k
        i0 = max(0, int((x0 - min_x) / quad_m)); i1 = min(SIZE, int((x1 - min_x) / quad_m))
        j0 = max(0, int((y0 - min_y) / quad_m)); j1 = min(SIZE, int((y1 - min_y) / quad_m))
        save_preview(height[j0:j1, i0:i1], out_dir / f"T_FarawayMother_8k_crop_{name}.png", 512)

    # Probe table: ground Z at each staged instance XY (bilinear)
    probes = []
    for name, px, py in PROBE_XYS:
        px, py = px * k, py * k
        z = bilinear_sample(height, px, py, min_x, min_y, quad_m)
        probes.append({"instance": name, "x_m": px, "y_m": py, "ground_z_m": round(z, 2)})
        print(f"[FM-heightfield] probe {name:34s} ({px:7.0f},{py:7.0f})  ground Z = {z:8.2f} m")

    manifest = {
        "schema": "melodia.faraway_mother.landscape_raw.v1",
        "generated": "2026-09-22",
        "seed": SEED,
        "footprint": "Universe Foundry field contract: world X/Y -400000..+400000 uu; field UV = (XY+400000)/800000 lands 1:1 on this terrain",
        "anatomy_m_per_unit": ANATOMY_M_PER_UNIT,
        "size_px": SIZE,
        "quad_cm": QUAD_CM,
        "field_m": round(field_m, 2),
        "world_center_xy": [CENTER_X, CENTER_Y],
        "world_min_xy": [round(min_x, 2), round(min_y, 2)],
        "row0": "south (min Y); first RAW row = min Y, columns ascend +X",
        "ue_import": {
            "mode": "Landscape import (owner-authorized 2026-09-21)",
            "raw": str(raw_path),
            "z_scale": Z_SCALE,
            "value_encoding": "UE convention: z_cm = (uint16 - 32768) * z_scale / 128 (3.9 mm per level, +-128 m)",
            "quads_per_side": SIZE,
            "note": "If editor raycast N-S mirrors vs probe table, re-export with rows flipped.",
        },
        "mesh_terrain_import": {
            "decision": "OWNER PIVOT 2026-09-21: UE 5.8 MeshTerrain (Nanite mesh) instead of Landscape — matches the staging-contract 'Nanite StaticMesh, no Landscape' and carries the fabric WPO stack",
            "inputs": {"raw": str(raw_path), "png16": str(png16_path)},
            "encoding": "UE convention: z_cm = (level - 32768) * z_scale / 128, z_scale = 50 (level 32768 = Z 0)",
            "import_settings": {"z_scale": Z_SCALE, "xy_extent_uu": 800000, "xy_spacing_uu": QUAD_CM,
                                "location_uu": [0, 0, 0], "min_corner_uu": [-400000, -400000]},
            "extent_m": round(field_m, 2),
            "origin_min_corner_xy": [round(min_x, 2), round(min_y, 2)],
            "world_center_xy": [CENTER_X, CENTER_Y],
            "row0": "south (min Y); flip on import if raycast N-S mirrors vs probe table",
            "collision_note": "raycast against terrain mesh must use trace-complex; WPO animation does NOT affect collision (raycast sees the base mesh)",
            "material_contract": "M_Master_Toon_Landscape_HeightBlend (copernicus_terrain_height_to_nanite contract) or M_Master_Nikki_Landscape (1k mesh manifest); Copernicus Faraway* MI families consume via MPC_Cymatics_Driver",
            "probe_targets": "hold as-is at 1 m per gray level; scale linearly with height_scale — re-emit probe table if not 1:1",
        },
        "profile": "hybrid: authored reclining-figure anatomy (real terrain as silhouette REFERENCE only, no DEM) + drape folds oriented perpendicular to macro gradient",
        "continuity": {
            "swell_formula": "15*sin(x*0.0004)+12*cos(y*0.0005) — verbatim from build_faraway_mother_height_aware_pcg.py offline ground ref",
            "seed_family": "20260829 (1k mesh generator + height-aware PCG manifests)",
            "sibling_1k_path": "Tools/_gen_faraway_heightmap.py (Nanite-mesh lane, no-Landscape contract)",
        },
        "anchors": [
            {"name": n, "x": x, "y": y, "amp_m": a, "sigma_along_m": sa, "sigma_across_m": sb, "rot_deg": r}
            for (n, x, y, a, sa, sb, r) in ANCHORS
        ],
        "folds": [
            {"wavelength_m": lam, "amp_m": amp, "orientation": "perpendicular to macro gradient (cloth drape)", "slope_ref_m_per_m": SLOPE_REF}
            for (lam, amp, _, _) in FOLDS
        ],
        "z_clamp_m": [z_lo, z_hi],
        "probes": probes,
        "raw_sha256": sha.hexdigest(),
        "raw_bytes": raw_path.stat().st_size,
        "preview": str(prev_path),
        "editor_next": [
            "UE Landscape import with the settings above (owner-authorized lane; Grok stage 1 holds until import)",
            "Re-run the height-aware raycast pass — expect ground Z within ~2 m of the probe table",
            "Then the staged instance z_offsets re-verify idempotently (faraway_mother_staging_report.md)",
        ],
    }
    man_path = out_dir / "manifest_landscape_raw_v1.json"
    man_path.write_text(json.dumps(manifest, indent=2))
    print(f"[FM-heightfield] RAW  {raw_path}  sha256={sha.hexdigest()[:16]}…  {raw_path.stat().st_size/1e6:.1f} MB")
    print(f"[FM-heightfield] manifest {man_path}")


if __name__ == "__main__":
    main()
