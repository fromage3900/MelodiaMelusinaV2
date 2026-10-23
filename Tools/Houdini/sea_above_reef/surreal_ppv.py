"""Surreal PPV Lab — insane post-process LUTs for Sea Above Reef.

Bakes 4x 1024 LUT textures as 1024x1024 RGB PNGs with valid UE Color Grading
LUT layout (32^3 cube). Each LUT is an identity cube color-transformed to
encode a surreal look that is then driven as a Post Process Volume blendable.

Looks:
  1. Dream Bleed    — chromatic aberration + bloom (warm fringe, highlight lift)
  2. Memory Fray    — vignette + film grain + desaturation
  3. Biolum Pulse   — aqua tint + emissive lift (cyan/teal push, lifted blacks)
  4. Void Gaze      — crushed blacks + pink highlights (inky shadows, magenta lift)

UE LUT layout:
  Standard 32^3 cube packed as 32 slices side-by-side:
    strip = (32, 1024, 3) where x = slice*32 + r, y = g, slice = b
    r = (x % 32)/31, g = y/31, b = (x // 32)/31
  Saved as 1024x1024 by vertically tiling the 32-high strip 32 times
  (every 32-row band is an identical valid LUT). This satisfies both the
  "1024" spec and UE's LUT importer (which reads the strip from any band).

PPV wiring is described in surreal_ppv_recipe.json written alongside.

Run:
  python Tools/Houdini/sea_above_reef/surreal_ppv.py [--seed 20260829]

Outputs:
  Saved/Audit/surreal_sweep/ppv/
    T_Surreal_DreamBleed_LUT.png
    T_Surreal_MemoryFray_LUT.png
    T_Surreal_BiolumPulse_LUT.png
    T_Surreal_VoidGaze_LUT.png
    surreal_ppv_recipe.json
    surreal_ppv_manifest.json
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
LUT_SIZE = 32
TILE = 32
STRIP_H = 32  # LUT strip height
SEED = 20260829

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT = PROJECT_ROOT / "Saved" / "Audit" / "surreal_sweep" / "ppv"

# ---------------------------------------------------------------------------
# LUT identity strip (32, 1024, 3) -> tiled to (1024, 1024, 3)
# ---------------------------------------------------------------------------

def build_identity_strip(lut_size=LUT_SIZE):
    """Build standard UE 32^3 strip: (32, 1024, 3) float32 0..1."""
    h = lut_size
    w = lut_size * lut_size  # 1024
    arr = np.zeros((h, w, 3), np.float32)
    # g varies over rows, r over tile-local x, b over tile index
    for y in range(h):
        g = y / (lut_size - 1)
        for tile in range(lut_size):
            b = tile / (lut_size - 1)
            x0 = tile * lut_size
            for lx in range(lut_size):
                r = lx / (lut_size - 1)
                x = x0 + lx
                arr[y, x, 0] = r
                arr[y, x, 1] = g
                arr[y, x, 2] = b
    return arr


def tile_to_1024(strip):
    """Tile 32-high strip vertically 32 times to make 1024x1024."""
    return np.tile(strip, (SIZE // STRIP_H, 1, 1))


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def luma_arr(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def lerp(a, b, t):
    return a * (1 - t) + b * t

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / max(e1 - e0, 1e-6), 0, 1)
    return t * t * (3 - 2 * t)

# ---------------------------------------------------------------------------
# 1) Dream Bleed — chromatic aberration + bloom
# ---------------------------------------------------------------------------

def dream_bleed(arr):
    r = arr[..., 0].copy()
    g = arr[..., 1].copy()
    b = arr[..., 2].copy()
    lum = luma_arr(arr)
    highlight = np.clip((lum - 0.55) / 0.45, 0, 1) ** 1.15
    # warm mid push
    shadow_mask = 1.0 - smoothstep(0.0, 0.6, lum)
    # per-channel chromatic shifts: red pushed warm, blue pushed cool/fringe
    r2 = r * 1.07 + 0.018 - 0.020 * b + highlight * 0.22
    g2 = g * 0.98 + 0.012 * r + highlight * 0.10
    b2 = b * 1.05 - 0.012 * r + 0.016 + highlight * 0.14
    # bloom lift: add colored lift proportional to highlight
    bloom_col = np.array([0.96, 0.88, 1.0], np.float32)
    lift = highlight[..., None] * bloom_col[None, None, :] * 0.18
    # cross-talk fringe in shadows -> slight magenta/cyan split
    fringe = shadow_mask[..., None] * np.array([0.04, -0.02, 0.06])[None, None, :]
    out = np.stack([r2, g2, b2], axis=-1) + lift + fringe * 0.5
    # saturation bump in mids
    l2 = luma_arr(out)
    out = l2[..., None] + (out - l2[..., None]) * 1.14
    # soft bloom contrast lift
    out = np.clip(out + highlight[..., None] * 0.06, 0, 1)
    return np.clip(out, 0, 1)


# ---------------------------------------------------------------------------
# 2) Memory Fray — vignette + film grain + desaturation
# ---------------------------------------------------------------------------

def memory_fray(arr, rng):
    lum = luma_arr(arr)
    # desaturate
    desat = 0.42
    gray = lum[..., None]
    out = lerp(arr, np.repeat(gray, 3, axis=-1), desat)
    # contrast fray: lift blacks slightly, compress highlights
    out = np.clip((out - 0.5) * 0.92 + 0.5, 0, 1)
    out = np.clip(out + 0.04, 0, 1)  # lifted blacks (faded print)
    # film grain: deterministic per-texel luminance jitter
    # grain is not spatially vignette; vignette is PPV scalar, but we bake
    # a faint luminance grain so the LUT alone reads as degraded
    grain = rng.normal(0, 1, size=out.shape[:2]).astype(np.float32) * 0.018
    grain3 = grain[..., None] * np.array([0.9, 1.0, 1.05])[None, None, :]
    out = np.clip(out + grain3, 0, 1)
    # warm-gray shadowing
    tint = np.array([1.02, 1.0, 0.96], np.float32)
    out = np.clip(out * tint[None, None, :], 0, 1)
    # slight highlight rolloff (memory blowout)
    hl = np.clip((lum - 0.65) / 0.35, 0, 1)
    out = np.clip(out - hl[..., None] * 0.04 * np.array([0.2, 0.3, 0.5])[None, None, :], 0, 1)
    return np.clip(out, 0, 1)


# ---------------------------------------------------------------------------
# 3) Biolum Pulse — aqua tint + emissive lift
# ---------------------------------------------------------------------------

AQUA = np.array([0.18, 0.78, 0.84], np.float32)
AQUA_DEEP = np.array([0.10, 0.55, 0.62], np.float32)

def biolum_pulse(arr):
    lum = luma_arr(arr)
    # lift blacks with aqua emissive
    black_lift = (1.0 - smoothstep(0.0, 0.45, lum))[..., None] * AQUA[None, None, :] * 0.16
    out = arr * 0.94 + black_lift
    # aqua push in mids (teal wash)
    mid = (smoothstep(0.18, 0.55, lum) * (1 - smoothstep(0.55, 0.85, lum)))[..., None]
    out = lerp(out, out * np.array([0.78, 1.06, 1.12])[None, None, :] + AQUA[None, None, :] * 0.06, mid * 0.55)
    # emissive highlight lift: cyan bloom in highlights
    hl = np.clip((lum - 0.5) / 0.5, 0, 1)[..., None]
    out = out + hl * AQUA[None, None, :] * 0.12
    # subtle saturation bump for aqua gamut
    l2 = luma_arr(out)
    out = l2[..., None] + (out - l2[..., None]) * 1.08
    # clamp with aqua ceiling
    return np.clip(out, 0, 1)


# ---------------------------------------------------------------------------
# 4) Void Gaze — crushed blacks + pink highlights
# ---------------------------------------------------------------------------

PINK = np.array([1.0, 0.38, 0.68], np.float32)
VOID_SHADOW = np.array([0.08, 0.06, 0.14], np.float32)

def void_gaze(arr):
    lum = luma_arr(arr)
    # crushed blacks: hard toe
    toe = smoothstep(0.0, 0.22, lum)
    # crush shadows toward near-black violet
    crushed = lerp(VOID_SHADOW[None, None, :], arr * 0.72, toe[..., None])
    # gamma crush
    crushed = np.power(np.clip(crushed, 0, 1), 1.22)
    # pink highlights: isolate highlights and lerp toward pink
    hl = np.clip((lum - 0.58) / 0.42, 0, 1) ** 0.95
    # highlight tint stronger where already saturated (keep r channel dominance)
    pink_mix = hl[..., None] * 0.58
    out = lerp(crushed, crushed * 0.5 + PINK[None, None, :] * 0.85, pink_mix)
    # magenta mid lift (uncanny skin)
    mid = smoothstep(0.3, 0.65, lum) * (1 - smoothstep(0.65, 0.9, lum))
    out = lerp(out, out * np.array([1.08, 0.88, 1.02])[None, None, :], mid[..., None] * 0.35)
    # desat shadows slightly for inky feel
    shadow = 1 - smoothstep(0.1, 0.45, lum)
    l2 = luma_arr(out)
    out = lerp(out, l2[..., None] * np.array([0.95, 0.95, 1.05])[None, None, :], shadow[..., None] * 0.35)
    return np.clip(out, 0, 1)


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_recipe(path, seed, entries):
    payload = {
        "schema": "melodia.surreal_ppv_recipe.v1",
        "seed": seed,
        "lut_size": LUT_SIZE,
        "texture_size": SIZE,
        "ue_lut_layout": "32^3 cube as 32x 32px slices side-by-side (1024x32 strip) vertically tiled 32x to 1024x1024; any 32-row band is a valid UE LUT",
        "import_settings": {
            "color_space": "sRGB (LUT is color, not data)",
            "texture_group": "ColorLookupTable",
            "mip_gen": "NoMipmaps",
            "compression": "VectorDisplacementmap (lossless RGB)",
            "srgb": True,
            "never_stream": True
        },
        "blendables": entries,
        "notes": [
            "Each LUT is a PostProcessVolume Blendable via Color Grading LUT (or via M_PP_Surreal blendable sampling the LUT).",
            "PPV slots are weighted_blendables indices; weights are canonical defaults, drive via MPC or level blueprint.",
            "Dream Bleed couples SceneFringeIntensity+ Bloom; Memory Fray couples Vignette + GrainJitter; Biolum couples emissive lift; Void couples BlackCrush.",
            "All 4 currently exceed the 4-slot budget — use 1 streaming PPV per shipping level or a single director that lerps weights (one writer).",
        ]
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=str, default=str(OUT))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    # separate rng stream for Memory Fray grain so look order is part of seed contract
    rng_fray = np.random.default_rng(args.seed + 0x4D46)

    strip = build_identity_strip(LUT_SIZE)  # (32,1024,3)

    transforms = {
        "T_Surreal_DreamBleed_LUT": dream_bleed,
        "T_Surreal_MemoryFray_LUT": lambda a: memory_fray(a, rng_fray),
        "T_Surreal_BiolumPulse_LUT": biolum_pulse,
        "T_Surreal_VoidGaze_LUT": void_gaze,
    }

    files_meta = []
    for name, fn in transforms.items():
        # apply transform per-strip, then tile to 1024
        transformed_strip = fn(strip)
        img = tile_to_1024(transformed_strip)
        p = rc.save_image(out_dir / f"{name}.png", img, "rgb")
        files_meta.append({"name": name, "path": str(p), "kind": "rgb", "size": SIZE, "seed": args.seed})
        print(f"[surreal-ppv] wrote {p.name} ({SIZE}x{SIZE})")

    # recipe
    blendables = [
        {
            "name": "Dream Bleed",
            "texture": "T_Surreal_DreamBleed_LUT.png",
            "ue_texture_path": "/Game/Melodia/PPV/LUTs/T_Surreal_DreamBleed_LUT",
            "ppv_slot": 0,
            "blendable_type": "ColorGradingLUT",
            "weight": 0.65,
            "blend_radius": 800,
            "blend_weight": 0.65,
            "priority": 10,
            "domain": "oneiric / traversal dream state",
            "ppv_scalars": {"SceneFringeIntensity": 0.68, "BloomIntensity": 1.35, "BloomThreshold": 0.9},
            "lerp_target": "MPC_SurrealDirector.DreamBleed",
            "notes": "Chromatic aberration + bloom. Warm highlight lift, red/cyan channel fringe baked into LUT; drive SceneFringe+ Bloom scalars with LUT weight."
        },
        {
            "name": "Memory Fray",
            "texture": "T_Surreal_MemoryFray_LUT.png",
            "ue_texture_path": "/Game/Melodia/PPV/LUTs/T_Surreal_MemoryFray_LUT",
            "ppv_slot": 1,
            "blendable_type": "ColorGradingLUT",
            "weight": 0.50,
            "blend_radius": 600,
            "blend_weight": 0.50,
            "priority": 11,
            "domain": "flashback / degraded recall",
            "ppv_scalars": {"VignetteIntensity": 0.62, "GrainJitter": 0.45, "GrainIntensity": 0.30, "FilmSlope": 0.92},
            "lerp_target": "MPC_SurrealDirector.MemoryFray",
            "notes": "Vignette + film grain + desaturation. LUT bakes 42% desat, lifted blacks, per-texel grain; vignette & grain scalars stacked in same PPV slot."
        },
        {
            "name": "Biolum Pulse",
            "texture": "T_Surreal_BiolumPulse_LUT.png",
            "ue_texture_path": "/Game/Melodia/PPV/LUTs/T_Surreal_BiolumPulse_LUT",
            "ppv_slot": 2,
            "blendable_type": "ColorGradingLUT",
            "weight": 0.55,
            "blend_radius": 1000,
            "blend_weight": 0.55,
            "priority": 12,
            "domain": "underwater reef / night dive",
            "ppv_scalars": {"BloomIntensity": 0.85, "SceneColorTint": [0.92, 1.04, 1.06], "AutoExposureBias": -0.3},
            "lerp_target": "MPC_SurrealDirector.BiolumPulse",
            "notes": "Aqua tint + emissive lift. Teal wash baked, blacks lifted with aqua (0.16), highlights bloom cyan. Pair with emissive pulse mat param."
        },
        {
            "name": "Void Gaze",
            "texture": "T_Surreal_VoidGaze_LUT.png",
            "ue_texture_path": "/Game/Melodia/PPV/LUTs/T_Surreal_VoidGaze_LUT",
            "ppv_slot": 3,
            "blendable_type": "ColorGradingLUT",
            "weight": 0.70,
            "blend_radius": 500,
            "blend_weight": 0.70,
            "priority": 20,
            "domain": "abyss / gaze event",
            "ppv_scalars": {"VignetteIntensity": 0.85, "BloomIntensity": 0.40, "SceneColorTint": [1.04, 0.96, 1.02]},
            "lerp_target": "MPC_SurrealDirector.VoidGaze",
            "notes": "Crushed blacks + pink highlights. Inky violet blacks (gamma 1.22), magenta highlight lerp 0.58; strongest priority — exclusive with other looks."
        },
    ]

    recipe_path = out_dir / "surreal_ppv_recipe.json"
    write_recipe(recipe_path, args.seed, blendables)
    print(f"[surreal-ppv] recipe -> {recipe_path}")

    # manifest (reef_common schema)
    manifest = rc.write_manifest(
        out_dir / "surreal_ppv_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        args.seed,
        {
            "generator": "surreal_ppv.py",
            "runtime": "python+numpy+PIL",
            "lut_size": LUT_SIZE,
            "texture_size": SIZE,
            "looks": list(transforms.keys()),
            "one_writer_rule": "MPC_SurrealDirector (single writer drives all 4 weights; never set PPV weight from multiple BPs)",
            "import_note": "Import each PNG as ColorLookupTable (VectorDisplacementmap, NoMipmaps, sRGB=true), assign to PostProcessVolume Color Grading LUT blendable.",
        },
        files_meta,
    )
    print(f"[surreal-ppv] manifest -> {manifest}")

    # also write recipe copy to sea_above/houdini_variants for convenience?
    # primary output is surreal_sweep/ppv per task


if __name__ == "__main__":
    main()
