"""Build the Melodia v3 non-commercial Houdini heightfield laboratory.

Run with Houdini 22 hython.  The scene remains .hipnc under Apprentice and is
never an Unreal production input.  Neutral JSON + PGM masks are the supported
interchange with the Blender-authoritative pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import hou

SCHEMA = "melodia.houdini.planetary_lab.v1"
MASKS = ("height", "slope", "cavity", "shoreline", "biome", "traversal")


def _field(size: int, seed: int, tile_x: int, tile_y: int):
    values = {name: [] for name in MASKS}
    for y in range(size):
        row = {name: [] for name in MASKS}
        for x in range(size):
            wx = tile_x * (size - 1) + x
            wy = tile_y * (size - 1) + y
            macro = 0.5 + 0.25 * math.sin((wx + seed * 0.17) * 0.071) + 0.25 * math.cos((wy - seed * 0.11) * 0.053)
            mid = 0.5 + 0.5 * math.sin((wx + wy + seed) * 0.19)
            h = max(0.0, min(1.0, macro * 0.78 + mid * 0.22))
            slope = min(1.0, abs(math.cos((wx + seed) * 0.071)) * 0.55 + abs(math.sin((wy - seed) * 0.053)) * 0.45)
            cavity = max(0.0, min(1.0, 0.5 + (macro - mid)))
            shore = max(0.0, 1.0 - abs(h - 0.48) * 12.0)
            biome = max(0.0, min(1.0, macro))
            traversal = max(0.0, 1.0 - abs((y / max(1, size - 1)) - 0.5) * 12.0)
            for name, value in (("height", h), ("slope", slope), ("cavity", cavity),
                                ("shoreline", shore), ("biome", biome), ("traversal", traversal)):
                row[name].append(value)
        for name in MASKS:
            values[name].append(row[name])
    return values


def _write_pgm(path: Path, field):
    height = len(field); width = len(field[0])
    body = bytearray(round(max(0.0, min(1.0, v)) * 65535) for row in field for v in row for _ in ())
    # 16-bit PGM is big-endian.
    body = bytearray()
    for row in field:
        for value in row:
            sample = round(max(0.0, min(1.0, value)) * 65535)
            body.extend(((sample >> 8) & 255, sample & 255))
    path.write_bytes(f"P5\n{width} {height}\n65535\n".encode("ascii") + body)


def build(output: Path, size: int, seed: int, tile_x: int, tile_y: int):
    output.mkdir(parents=True, exist_ok=True)
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "MEL_Planetary_Lab")
    for child in geo.children():
        child.destroy()
    hf = geo.createNode("heightfield", "heightfield_source")
    hf.parm("sizex").set(1024.0); hf.parm("sizey").set(1024.0)
    hf.parm("gridspacing").set(1024.0 / max(2, size - 1))
    noise = geo.createNode("heightfield_noise", "macro_mid_micro")
    noise.setInput(0, hf); noise.parm("elementsize").set(240.0); noise.parm("amp").set(110.0)
    for seed_name in ("seed", "noiseseed", "offset"):
        if noise.parm(seed_name): noise.parm(seed_name).set(seed); break
    terrace = geo.createNode("heightfield_terrace", "musical_terraces"); terrace.setInput(0, noise)
    if terrace.parm("terrace_step"): terrace.parm("terrace_step").set(8.0)
    erode = geo.createNode("heightfield_erode", "erosion_masks"); erode.setInput(0, terrace)
    mask = geo.createNode("heightfield_maskbyfeature", "cliff_slope_mask"); mask.setInput(0, erode)
    null = geo.createNode("null", "OUT_TECHNICAL_REVIEW"); null.setInput(0, mask); null.setDisplayFlag(True); null.setRenderFlag(True)
    geo.layoutChildren()

    license_name = str(hou.licenseCategory())
    hip = output / "Melodia_Planetary_Lab.hipnc"
    hou.hipFile.save(str(hip))
    fields = _field(size, seed, tile_x, tile_y)
    artifacts = []
    for name in MASKS:
        path = output / f"mel_{name}.pgm"
        _write_pgm(path, fields[name])
        raw = path.read_bytes()
        flat = [v for row in fields[name] for v in row]
        artifacts.append({"role": name, "path": str(path), "bytes": len(raw),
                          "sha256": hashlib.sha256(raw).hexdigest(),
                          "min": min(flat), "max": max(flat)})
    report = {
        "schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
        "houdini_version": hou.applicationVersionString(), "license_category": license_name,
        "production_eligible": "Apprentice" not in license_name and "NonCommercial" not in license_name,
        "seed": seed, "tile": {"x": tile_x, "y": tile_y}, "resolution": [size, size],
        "units": "metres", "hip": str(hip), "masks": artifacts,
        "authority": "technical_noncommercial_only",
    }
    manifest = output / "melodia_houdini_planetary_lab.json"
    manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(manifest), "license": license_name, "masks": len(artifacts)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--resolution", type=int, default=129)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--tile-x", type=int, default=0)
    parser.add_argument("--tile-y", type=int, default=0)
    args = parser.parse_args()
    build(Path(args.output).resolve(), args.resolution, args.seed, args.tile_x, args.tile_y)


if __name__ == "__main__":
    main()
