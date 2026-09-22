#!/usr/bin/env python3
"""Faraway Mother deterministic static-field baker.

Designed to run under Houdini's hython or a compatible Python environment with
numpy + Pillow. It emits source/presentation data only; it never imports Unreal.

The math mirrors Tools/PCG/build_faraway_mother_pcg_ecosystem.py:
  - Chladni mode (3,5) by default
  - finite-difference tension gradient (du=dv=0.001)
  - Faraway moisture formula
  - ResonantSeamWay mask abs(chladni) < 0.12

RGBA:
  R = WorldField.Tension
  G = WorldField.ResonanceBase (abs Chladni normalized to 0..1)
  B = WorldField.Moisture
  A = ResonantSeamWay mask
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PCG_SOURCE = ROOT / "Tools" / "PCG" / "build_faraway_mother_pcg_ecosystem.py"
DEFAULT_OUT = ROOT / "Saved" / "Audit" / "houdini_faraway_mother"
SCHEMA = "melodia.faraway_static_field/v1"


def _load_pcg_module():
    spec = importlib.util.spec_from_file_location("faraway_pcg_authority", PCG_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load PCG authority: {PCG_SOURCE}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _chladni(u: np.ndarray, v: np.ndarray, n: int, m: int) -> np.ndarray:
    pi = math.pi
    return (
        np.cos(n * pi * u) * np.cos(m * pi * v)
        - np.cos(m * pi * u) * np.cos(n * pi * v)
    )


def build_field(res: int, mode_n: int, mode_m: int):
    # Pixel centers match the deterministic grid style used by the PCG generator.
    axis = (np.arange(res, dtype=np.float64) + 0.5) / float(res)
    u, v = np.meshgrid(axis, axis, indexing="xy")

    z = _chladni(u, v, mode_n, mode_m)
    du = 0.001
    dv = 0.001
    z_u = _chladni(u + du, v, mode_n, mode_m)
    z_v = _chladni(u, v + dv, mode_n, mode_m)
    grad_u = (z_u - z) / du
    grad_v = (z_v - z) / dv
    tension = np.clip(np.sqrt(grad_u * grad_u + grad_v * grad_v) / 8.0, 0.0, 1.0)

    altitude = z * 4000.0 + np.sin(u * math.pi * 2.0) * 1500.0
    moisture = np.clip(0.5 - (altitude / 8000.0) + (1.0 - tension) * 0.3, 0.0, 1.0)
    resonance = np.clip(np.abs(z) / 2.0, 0.0, 1.0)
    seam = (np.abs(z) < 0.12).astype(np.float64)

    return tension, resonance, moisture, seam


def crosscheck_authority(mod, mode_n: int, mode_m: int) -> dict:
    samples = [
        (0.125, 0.125),
        (0.25, 0.75),
        (0.5, 0.5),
        (0.875, 0.375),
    ]
    chladni_err = 0.0
    tension_err = 0.0
    for u, v in samples:
        authority_z = float(mod.evaluate_chladni(u, v, mode_n, mode_m))
        vector_z = float(_chladni(np.array(u), np.array(v), mode_n, mode_m))
        chladni_err = max(chladni_err, abs(authority_z - vector_z))

        # PCG authority's tension helper currently hardcodes (3,5); compare it
        # only when the requested modes are the canonical Faraway modes.
        if (mode_n, mode_m) == (3, 5):
            authority_t = float(mod.evaluate_tension(u, v))
            z = vector_z
            du = dv = 0.001
            zu = float(_chladni(np.array(u + du), np.array(v), mode_n, mode_m))
            zv = float(_chladni(np.array(u), np.array(v + dv), mode_n, mode_m))
            vector_t = min(1.0, max(0.0, math.sqrt(((zu-z)/du)**2 + ((zv-z)/dv)**2) / 8.0))
            tension_err = max(tension_err, abs(authority_t - vector_t))

    return {
        "sample_count": len(samples),
        "max_chladni_abs_error": chladni_err,
        "max_tension_abs_error": tension_err,
        "passes": chladni_err <= 1e-12 and tension_err <= 1e-12,
    }


def save_rgba(out_dir: Path, channels, res: int) -> tuple[Path, Path]:
    tension, resonance, moisture, seam = channels
    rgba = np.stack([tension, resonance, moisture, seam], axis=-1)
    rgba8 = np.round(np.clip(rgba, 0.0, 1.0) * 255.0).astype(np.uint8)

    field_path = out_dir / "T_FarawayMother_StaticField_RGBA.png"
    Image.fromarray(rgba8, mode="RGBA").save(field_path)

    # Preview = R | G | B | A as four grayscale panels, useful without a custom viewer.
    panels = []
    for channel in (tension, resonance, moisture, seam):
        gray = np.round(np.clip(channel, 0.0, 1.0) * 255.0).astype(np.uint8)
        panels.append(np.stack([gray, gray, gray], axis=-1))
    preview = np.concatenate(panels, axis=1)
    preview_path = out_dir / "T_FarawayMother_StaticField_preview.png"
    Image.fromarray(preview, mode="RGB").save(preview_path)
    return field_path, preview_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=3900)
    ap.add_argument("--mode-n", type=int, default=3)
    ap.add_argument("--mode-m", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if args.res < 64 or args.res > 8192:
        raise SystemExit("--res must be in [64,8192]")
    if args.mode_n < 1 or args.mode_m < 1:
        raise SystemExit("modes must be positive")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pcg = _load_pcg_module()
    check = crosscheck_authority(pcg, args.mode_n, args.mode_m)
    if not check["passes"]:
        raise SystemExit(f"PCG authority cross-check failed: {check}")

    channels = build_field(args.res, args.mode_n, args.mode_m)
    field_path, preview_path = save_rgba(args.out_dir, channels, args.res)

    try:
        import hou  # type: ignore
        runtime = f"hython/hou {hou.applicationVersionString()}"
    except Exception:
        runtime = f"python {sys.version.split()[0]} (hou unavailable)"

    bounds = [-400000.0, -400000.0, 400000.0, 400000.0]
    manifest = {
        "schema": SCHEMA,
        "generator": "Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py",
        "runtime": runtime,
        "seed": args.seed,
        "resolution": [args.res, args.res],
        "world_bounds_uu": bounds,
        "uv_mapping": {
            "u": "(WorldX + 400000) / 800000",
            "v": "(WorldY + 400000) / 800000",
        },
        "field_basis": {
            "type": "chladni",
            "mode_n": args.mode_n,
            "mode_m": args.mode_m,
            "resonant_seam_threshold_abs": 0.12,
        },
        "channels": {
            "R": "WorldField.Tension",
            "G": "WorldField.ResonanceBase",
            "B": "WorldField.Moisture",
            "A": "ResonantSeamWayMask",
        },
        "source_authority": str(PCG_SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "authority_crosscheck": check,
        "outputs": {
            "field": {
                "path": str(field_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(field_path),
            },
            "preview": {
                "path": str(preview_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha256(preview_path),
                "layout": "R | G | B | A",
            },
        },
        "note": "Source/presentation data only. Unreal remains gameplay/save/world-state authority.",
    }

    manifest_path = args.out_dir / "resonance_field_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(manifest_path)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
