#!/usr/bin/env python3
"""Deterministic fallback field_atlas cook for Houdini Foundry recipes.

Stands in for the missing `HDA_Foundry_FieldAtlas_1.0.hda` (every recipe that
needs it carries `source.exists_on_main=false`). Same pattern as
`Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py`: pure-numpy
Chladni base field, documented per-channel derivations, no Unreal imports.

Runs under hython (needs hou for version/license reporting, numpy, OIIO for
EXR, PIL for the preview). Emits the foundry bake manifest directly:

    hython Tools/Houdini/foundry/cook_field_atlas.py \
        recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FOUNDRY_PATH = ROOT / "Tools" / "Houdini" / "foundry" / "houdini_foundry.py"


def _load_foundry():
    spec = importlib.util.spec_from_file_location("houdini_foundry", FOUNDRY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["houdini_foundry"] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _chladni(u: np.ndarray, v: np.ndarray, n: int, m: int) -> np.ndarray:
    pi = math.pi
    return np.cos(n * pi * u) * np.cos(m * pi * v) - np.cos(m * pi * u) * np.cos(n * pi * v)


def _box_blur(a: np.ndarray, radius: int, passes: int = 2) -> np.ndarray:
    """Deterministic separable box blur (edge-replicated), numpy only."""
    out = a.astype(np.float64)
    for _ in range(passes):
        pad = np.pad(out, ((radius, radius), (radius, radius)), mode="edge")
        c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
        c = np.pad(c, ((1, 0), (1, 0)))
        k = 2 * radius + 1
        out = (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / float(k * k)
    return out


def _gaussian_hotspot(u: np.ndarray, v: np.ndarray, cu: float, cv: float, sigma: float) -> np.ndarray:
    return np.exp(-((u - cu) ** 2 + (v - cv) ** 2) / (2.0 * sigma * sigma))


def build_channels(res: int, seed: int, bake_bounds: list[float]) -> dict[str, np.ndarray]:
    """All channels derived from one Chladni base field. Deterministic in (res, seed)."""
    n, m = 3, 5  # canonical Faraway mode pair (see faraway_static_field.py docstring)
    phase_u = (seed * 0.6180339887498949) % 1.0
    phase_v = (seed * 0.7548776662466927) % 1.0
    axis = (np.arange(res, dtype=np.float64) + 0.5) / float(res)
    u, v = np.meshgrid(axis, axis, indexing="xy")
    u_p = u + phase_u
    v_p = v + phase_v

    z = _chladni(u_p, v_p, n, m)
    du = 0.001
    z_u = _chladni(u_p + du, v_p, n, m)
    z_v = _chladni(u_p, v_p + du, n, m)
    grad_u = (z_u - z) / du
    grad_v = (z_v - z) / du
    grad_mag = np.sqrt(grad_u * grad_u + grad_v * grad_v)
    tension = np.clip(grad_mag / 8.0, 0.0, 1.0)
    z_uu = (_chladni(u_p + du, v_p, n, m) - 2 * z + _chladni(u_p - du, v_p, n, m)) / (du * du)
    z_vv = (_chladni(u_p, v_p + du, n, m) - 2 * z + _chladni(u_p, v_p - du, n, m)) / (du * du)
    laplacian = z_uu + z_vv
    lap_max = float(np.max(np.abs(laplacian))) or 1.0
    curvature = np.clip(laplacian / lap_max, -1.0, 1.0)

    altitude = z * 2400.0 + np.sin(u * math.pi * 2.0) * 900.0
    moisture = np.clip(0.5 - (altitude / 8000.0) + (1.0 - tension) * 0.3, 0.0, 1.0)
    resonance = np.clip(np.abs(z) / 2.0, 0.0, 1.0)
    seam = (np.abs(z) < 0.12).astype(np.float64)
    seam_blur = _box_blur(seam, radius=max(2, res // 64))

    slope = np.clip(grad_mag / (float(np.max(grad_mag)) or 1.0), 0.0, 1.0)
    concavity = np.clip(curvature, 0.0, 1.0)
    convexity = np.clip(-curvature, 0.0, 1.0)

    hot_u = (seed * 0.4142135623730951) % 1.0
    hot_v = (seed * 0.5773502691896258) % 1.0

    channels = {
        "height": altitude.astype(np.float64),
        "slope": slope,
        "curvature": curvature,
        "concavity": concavity,
        "convexity": convexity,
        "exposure": np.clip(1.0 - tension * 0.9, 0.0, 1.0),
        "flow": np.power(tension, 1.5),
        "sediment": moisture * (1.0 - tension),
        "debris": convexity * slope,
        "wetness": np.clip(moisture * 0.8 + seam_blur * 0.4, 0.0, 1.0),
        "shore_influence": np.clip(seam_blur, 0.0, 1.0),
        "cliff": np.clip((slope - 0.55) / 0.25, 0.0, 1.0),
        "hero_weight": np.clip(_gaussian_hotspot(u, v, hot_u, hot_v, 0.08), 0.0, 1.0),
        "resonance": resonance,
        # extra base channels, recorded in the manifest for downstream reuse
        "tension": tension,
        "moisture": moisture,
    }
    return channels


def write_raster(path: Path, data: np.ndarray, lo: float, hi: float) -> None:
    """16-bit grayscale PNG fallback raster.

    EXR (the recipe's stated format) cannot be written by this workstation's
    hython 22.0.368 build: both OpenEXR (Shiboken mis-init) and OIIO's EXR
    codec (IlmThread segfault) crash for >= 512px tiles. PNG16 is the
    deterministic, UE-importable fallback; the manifest records the
    32f-linear -> 16-bit normalization (lo/hi) per channel.
    """
    from PIL import Image

    span = (hi - lo) or 1.0
    scaled = np.round(np.clip((data - lo) / span, 0.0, 1.0) * 65535.0).astype(np.uint16)
    Image.fromarray(scaled).save(path)


def write_preview(path: Path, panels: list[np.ndarray]) -> None:
    from PIL import Image

    grays = []
    for panel in panels:
        lo, hi = float(panel.min()), float(panel.max())
        span = (hi - lo) or 1.0
        gray = np.round(np.clip((panel - lo) / span, 0.0, 1.0) * 255.0).astype(np.uint8)
        grays.append(np.stack([gray, gray, gray], axis=-1))
    Image.fromarray(np.concatenate(grays, axis=1)).save(path)


def git_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        pass
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("recipe", type=Path)
    ap.add_argument("--tile", default=None, help="tile_id; default = first planned tile")
    ap.add_argument("--res", type=int, default=None, help="override params.resolution_px")
    ap.add_argument("--out-root", type=Path, default=None, help="override Saved/HoudiniFoundry root")
    args = ap.parse_args(argv)

    # hython 22.0.368 segfaults when a DeprecationWarning is *formatted*
    # (PyErr_WarnExplicitFormat re-enters Shiboken module init). Silence all
    # warnings at interpreter level for the cook process.
    import warnings

    warnings.simplefilter("ignore")

    foundry = _load_foundry()
    recipe = foundry.load_json(args.recipe if args.recipe.is_absolute() else ROOT / args.recipe)
    errors = foundry.validate_recipe(recipe)
    if errors:
        print("FAIL recipe invalid:")
        for error in errors:
            print(f"  - {error}")
        return 1

    tiles = foundry.plan_tiles(recipe)
    if args.tile:
        tiles = [t for t in tiles if t["tile_id"] == args.tile]
    if not tiles:
        print("FAIL: no tile matched")
        return 1
    tile = tiles[0]

    res = args.res or int(recipe["params"].get("resolution_px", 512))
    out_root = args.out_root or Path(foundry.OUTPUT_ROOT)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    tile_dir = out_root / f"{recipe['recipe_id']}_{recipe['seed']}" / "tiles" / tile["tile_id"]
    tile_dir.mkdir(parents=True, exist_ok=True)

    channels = build_channels(res, tile["seed"], tile["bake_bounds_cm"])
    wanted = list(recipe["params"]["channels"])
    missing = [c for c in wanted if c not in channels]
    if missing:
        print(f"FAIL: cook has no formulas for requested channels: {missing}")
        return 1

    # Importing hou in the same process as OIIO segfaults hython teardown in
    # this build (Shiboken module init). Probe version/license via subprocess.
    hou_version, license_category = "unknown", "unknown"
    try:
        probe_code = (
            "import hou,json,sys;"
            "print(json.dumps({'v':hou.applicationVersionString(),'l':str(hou.licenseCategory())}));"
            "sys.stdout.flush()"
        )
        proc = subprocess.run(
            [sys.executable, "-c", probe_code], capture_output=True, text=True, timeout=120
        )
        line = next((ln for ln in reversed(proc.stdout.splitlines()) if ln.startswith("{")), "")
        if line:
            info = json.loads(line)
            hou_version, license_category = info["v"], info["l"]
    except Exception:
        pass

    outputs = []
    for name in wanted:
        path = tile_dir / f"field_atlas_{tile['tile_id']}_{name}.png16.png"
        data = channels[name]
        lo, hi = float(data.min()), float(data.max())
        write_raster(path, data, lo, hi)
        outputs.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "channels": [name],
            "format": "png16",
            "range": [lo, hi],
        })

    preview_panels = [channels[c] for c in ("height", "slope", "flow", "resonance") if c in channels]
    preview_path = tile_dir / f"field_atlas_{tile['tile_id']}_preview.png"
    write_preview(preview_path, preview_panels[:4])
    outputs.append({
        "path": str(preview_path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha256(preview_path),
        "bytes": preview_path.stat().st_size,
        "channels": ["height", "slope", "flow", "resonance"],
    })

    manifest_dir = out_root / f"{recipe['recipe_id']}_{recipe['seed']}"
    manifest = {
        "schema": foundry.MANIFEST_SCHEMA,
        "recipe_id": recipe["recipe_id"],
        "recipe_sha256": foundry.content_hash(recipe),
        "seed": recipe["seed"],
        "tile_id": tile["tile_id"],
        "houdini_version": hou_version,
        "license_category": license_category,
        "tool": {
            "path": "Tools/Houdini/foundry/cook_field_atlas.py",
            "git_sha": git_sha(),
        },
        "params": {
            "resolution_px": res,
            "channels": wanted,
            "tile": tile,
            "uv_bounds_cm": tile["bake_bounds_cm"],
            "base_field": "chladni(3,5) with seed-derived uv phase; see cook_field_atlas.py docstrings",
            "format_override": "png16 rasters; recipe-stated EXR is blocked on this workstation (OIIO EXR/IlmThread segfault, OpenEXR Shiboken init crash). Re-emit EXR when a working EXR writer is available.",
        },
        "outputs": outputs,
        "status": "PASS",
    }
    manifest_path = manifest_dir / "bake_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    sys.exit(main())
