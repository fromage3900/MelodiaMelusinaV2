"""
Simple erosion/weathering processor for heightfields.

Applies:
- Gaussian blur for smoothing (PIL fallback)
- Hydraulic erosion simulation (numpy-like logic with lists)
- Sediment deposition
- Flow-based detail enhancement

All processing is offline and does not require Blender or Gaea.
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class ErosionParams:
    """Parameters for erosion simulation."""

    iterations: int = 32
    rain_rate: float = 0.01
    evaporation: float = 0.02
    sediment_capacity: float = 0.05
    deposition: float = 0.03
    min_slope: float = 0.001
    blur_sigma: float = 1.0


def load_heightfield(path: str | Path) -> list[list[float]]:
    """Load heightfield PNG as 2D float list in [0, 1]."""
    from PIL import Image

    img = Image.open(path)
    rows = np_array_to_rows(img)
    if img.mode in ("I;16", "I;16B", "I;16L"):
        return _scale_rows(rows, 65535.0)
    if img.mode == "F":
        # Pillow's F mode is already 32-bit floating point. Gaea exports
        # normalized heightfields in this mode; dividing by 255 flattens them.
        return _clamp_rows(rows)
    if img.mode == "I":
        # I is a 32-bit integer mode without a fixed content range. Normalize
        # its observed range instead of treating it as an 8-bit image.
        return _normalize_integer_rows(rows)
    return _scale_rows(rows, 255.0)


def _clamp_rows(rows: list[list[float]]) -> list[list[float]]:
    return [[max(0.0, min(1.0, float(v))) for v in row] for row in rows]


def _scale_rows(rows: list[list[float]], divisor: float) -> list[list[float]]:
    if divisor <= 0.0:
        raise ValueError("Heightfield divisor must be positive")
    return _clamp_rows([[float(v) / divisor for v in row] for row in rows])


def _normalize_integer_rows(rows: list[list[float]]) -> list[list[float]]:
    values = [float(v) for row in rows for v in row]
    if not values:
        return []
    lo, hi = min(values), max(values)
    if 0.0 <= lo and hi <= 1.0:
        return _clamp_rows(rows)
    if hi <= lo:
        return [[0.0 for _ in row] for row in rows]
    if lo < 0.0:
        span = hi - lo
        return _clamp_rows([[(float(v) - lo) / span for v in row] for row in rows])
    return _clamp_rows([[float(v) / hi for v in row] for row in rows])


def np_array_to_rows(img) -> list[list[float]]:
    """Convert PIL image to list of rows of ints."""
    w, h = img.size
    pixels = list(img.getdata())
    if isinstance(pixels[0], tuple):
        pixels = [sum(c) / len(c) for c in pixels]
    return [pixels[i * w:(i + 1) * w] for i in range(h)]


def save_heightfield(arr: list[list[float]], path: str | Path) -> dict[str, Any]:
    """Save heightfield as 16-bit PNG."""
    from PIL import Image

    h = len(arr)
    w = len(arr[0]) if h else 0
    flat = []
    for row in arr:
        for v in row:
            flat.append(int(max(0, min(65535, int(v * 65535)))))
    img = Image.new("I;16", (w, h))
    img.putdata(flat)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)

    vals = [v for row in arr for v in row]
    return {
        "path": str(path),
        "width": w,
        "height": h,
        "min": min(vals) if vals else 0.0,
        "max": max(vals) if vals else 0.0,
        "mean": sum(vals) / len(vals) if vals else 0.0,
    }


def box_blur(arr: list[list[float]], radius: int) -> list[list[float]]:
    """Simple box blur."""
    if radius <= 0:
        return arr
    h = len(arr)
    w = len(arr[0]) if h else 0
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            s = 0.0
            c = 0
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        s += arr[ny][nx]
                        c += 1
            out[y][x] = s / c
    return out


def gaussian_blur(arr: list[list[float]], sigma: float) -> list[list[float]]:
    """Gaussian-ish blur via repeated box blur."""
    if sigma <= 0:
        return arr
    radius = max(1, int(sigma * 1.5))
    return box_blur(arr, radius)


def height_to_gradients(arr: list[list[float]]) -> tuple[list[list[float]], list[list[float]]]:
    """Compute dx, dy gradients."""
    h = len(arr)
    w = len(arr[0]) if h else 0
    dx = [[0.0] * w for _ in range(h)]
    dy = [[0.0] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            dx[y][x] = (arr[y][x + 1] - arr[y][x - 1]) * 0.5
            dy[y][x] = (arr[y + 1][x] - arr[y - 1][x]) * 0.5
    return dx, dy


def hydraulic_erosion(arr: list[list[float]], params: ErosionParams) -> list[list[float]]:
    """Simplified hydraulic erosion simulation."""
    height = [row[:] for row in arr]
    h = len(height)
    w = len(height[0]) if h else 0

    for _ in range(params.iterations):
        # Rainfall
        for y in range(h):
            for x in range(w):
                height[y][x] += params.rain_rate * random.random()

        # Gradients
        dx, dy = height_to_gradients(height)

        # Erosion + deposition
        sediment = [[0.0] * w for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                slope = (abs(dx[y][x]) + abs(dy[y][x])) + params.min_slope
                erosion = params.sediment_capacity * slope
                sediment[y][x] += erosion
                height[y][x] -= erosion

        # Transport: average sediment from neighbors
        new_sediment = [[0.0] * w for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                s = sediment[y][x]
                s += sediment[y - 1][x] * 0.25
                s += sediment[y + 1][x] * 0.25
                s += sediment[y][x - 1] * 0.25
                s += sediment[y][x + 1] * 0.25
                new_sediment[y][x] = s

        # Deposition
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                dep = params.deposition * new_sediment[y][x]
                height[y][x] += dep

        # Evaporation
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                height[y][x] *= 1.0 - params.evaporation

        # Clamp
        for y in range(h):
            for x in range(w):
                if height[y][x] < 0.0:
                    height[y][x] = 0.0
                if height[y][x] > 1.0:
                    height[y][x] = 1.0

    return height


def enhance_flow_detail(arr: list[list[float]], strength: float = 0.15) -> list[list[float]]:
    """Add micro-detail based on gradient magnitude."""
    h = len(arr)
    w = len(arr[0]) if h else 0
    dx, dy = height_to_gradients(arr)
    out = [row[:] for row in arr]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            flow = abs(dx[y][x]) + abs(dy[y][x])
            out[y][x] += strength * flow * (random.random() - 0.5)
            if out[y][x] < 0.0:
                out[y][x] = 0.0
            if out[y][x] > 1.0:
                out[y][x] = 1.0
    return out


def _sample_heightfield(arr: list[list[float]], x: float, y: float) -> float:
    """Bilinearly sample a normalized heightfield in pixel/cell space."""
    if not arr or not arr[0]:
        return 0.0
    height = len(arr)
    width = len(arr[0])
    x = max(0.0, min(float(width - 1), float(x)))
    y = max(0.0, min(float(height - 1), float(y)))
    x0, y0 = int(x), int(y)
    x1, y1 = min(x0 + 1, width - 1), min(y0 + 1, height - 1)
    tx, ty = x - x0, y - y0
    top = arr[y0][x0] * (1.0 - tx) + arr[y0][x1] * tx
    bottom = arr[y1][x0] * (1.0 - tx) + arr[y1][x1] * tx
    return top * (1.0 - ty) + bottom * ty


def _dressing_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    dressing = plan.get("dressing")
    if isinstance(dressing, dict) and isinstance(dressing.get("items"), list):
        return [item for item in dressing["items"] if isinstance(item, dict)]
    if isinstance(plan.get("items"), list):
        return [item for item in plan["items"] if isinstance(item, dict)]
    return []


def _reproject_dressing_plan(
    plan: dict[str, Any],
    source_field: list[list[float]],
    processed_field: list[list[float]],
    height_scale: float = 1.0,
) -> dict[str, Any]:
    """Move dressing bases by the erosion delta at their original XY cells."""
    updated = 0
    for item in _dressing_items(plan):
        location = item.get("location")
        if not isinstance(location, list) or len(location) < 3:
            continue
        try:
            x, y, old_z = float(location[0]), float(location[1]), float(location[2])
        except (TypeError, ValueError):
            continue
        before = _sample_heightfield(source_field, x, y)
        after = _sample_heightfield(processed_field, x, y)
        location[2] = old_z + (after - before) * float(height_scale)
        updated += 1

    return {
        "applied": True,
        "items_updated": updated,
        "height_scale": float(height_scale),
        "source_dimensions": {
            "width": len(source_field[0]) if source_field else 0,
            "height": len(source_field),
        },
        "processed_dimensions": {
            "width": len(processed_field[0]) if processed_field else 0,
            "height": len(processed_field),
        },
    }


def process_heightfield(
    input_png: str | Path,
    output_png: str | Path,
    params: ErosionParams | None = None,
) -> dict[str, Any]:
    """Full processing pipeline: load -> blur -> erode -> enhance -> save."""
    params = params or ErosionParams()
    arr = load_heightfield(input_png)
    if not arr:
        raise RuntimeError("Empty heightfield")

    # Smooth raw voxel terrain
    arr = gaussian_blur(arr, sigma=params.blur_sigma)

    # Erosion/weathering
    arr = hydraulic_erosion(arr, params)

    # Flow-based detail
    arr = enhance_flow_detail(arr)

    result = save_heightfield(arr, output_png)
    result.update({
        "erosion_iterations": params.iterations,
        "blur_sigma": params.blur_sigma,
    })
    return result


def build_mesh_terrain_handoff(
    heightfield_png: str | Path,
    dressing_plan: str | Path,
    preset_id: str,
    output_dir: str | Path,
    source_heightfield: str | Path | None = None,
    height_scale: float = 1.0,
) -> dict[str, Any]:
    """Assemble Mesh Terrain import package for UE 5.8."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    src_hf = Path(heightfield_png)
    src_dp = Path(dressing_plan)

    if not src_hf.exists():
        raise FileNotFoundError(src_hf)
    if not src_dp.exists():
        raise FileNotFoundError(src_dp)

    dst_hf = output_dir / "heightfield.png"
    dst_dp = output_dir / "dressing_plan.json"

    import shutil
    if src_hf.resolve() != dst_hf.resolve():
        shutil.copy2(src_hf, dst_hf)

    plan = json.loads(src_dp.read_text(encoding="utf-8"))
    reprojection = {"applied": False, "items_updated": 0}
    if source_heightfield is not None:
        src_original_hf = Path(source_heightfield)
        if not src_original_hf.exists():
            raise FileNotFoundError(src_original_hf)
        reprojection = _reproject_dressing_plan(
            plan,
            load_heightfield(src_original_hf),
            load_heightfield(src_hf),
            height_scale=height_scale,
        )
    plan["terrain_reprojection"] = reprojection
    dst_dp.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "kind": "melodia_mesh_terrain_handoff",
        "preset_id": preset_id,
        "ue": {
            "engine": "5.8",
            "target": "Mesh Terrain",
            "import_scale_cm_per_meter": 100.0,
            "required_plugins": ["MeshPartition", "MeshTerrainMode", "PCGMeshPartitionInterop"],
            "classic_landscape_used": False,
            "recommended_content_path": f"/Game/_PROJECT/ResonantWorld/Offline/{preset_id}",
        },
        "artifacts": {
            "heightfield": {"path": str(dst_hf), "format": "PNG_16bit"},
            "dressing_plan": {"path": str(dst_dp), "format": "JSON"},
        },
        "validation": {
            "heightfield_exists": True,
            "dressing_plan_exists": True,
            "pixel_dimensions": _get_image_dimensions(src_hf),
            "dressing_reprojection": reprojection,
        },
    }

    manifest_path = output_dir / "handoff_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _get_image_dimensions(path: Path) -> dict[str, int]:
    try:
        from PIL import Image
        img = Image.open(path)
        return {"width": img.width, "height": img.height}
    except Exception:
        return {"width": 0, "height": 0}


def process_preset(
    preset_id: str,
    base_dir: str | Path,
    params: ErosionParams | None = None,
    height_scale: float = 1.0,
) -> dict[str, Any]:
    """Process a single preset: erosion + handoff."""
    base = Path(base_dir) / preset_id
    input_hf = base / f"heightfield_{preset_id}.png"
    input_dp = base / f"dressing_plan_{preset_id}.json"
    output_dir = base / "ue_handoff"

    if not input_hf.exists() or not input_dp.exists():
        return {"status": "error", "reason": "missing_input", "path": str(base)}

    result = process_heightfield(input_hf, output_dir / "heightfield.png", params)
    handoff = build_mesh_terrain_handoff(
        output_dir / "heightfield.png",
        input_dp,
        preset_id,
        output_dir,
        source_heightfield=input_hf,
        height_scale=height_scale,
    )

    return {
        "status": "ok",
        "preset_id": preset_id,
        "processed_heightfield": result,
        "handoff": handoff,
    }
