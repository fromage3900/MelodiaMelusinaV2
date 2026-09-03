"""Binary FString patch: rewire EnvSandbox materials from _PROJECT/Art paths to portfolio paths.

WARNING: Do not run this script â€” FString length changes corrupt uasset packages.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
MATERIALS = CONTENT / "EnvSandbox" / "Materials"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_path_patch.json"

REPLACEMENTS: list[tuple[str, str]] = sorted(
    [
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_1_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_1_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_3_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_3_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_5_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_5_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_6_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_6_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_7_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_7_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_9_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_9_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Perlin/Perlin_1_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Perlin/Perlin_1_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Voronoi/Voronoi_2_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_2_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/Textures/Voronoi/Voronoi_11_-_512x512",
            "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_11_-_512x512",
        ),
        (
            "/Game/_PROJECT/04_Materials/baroque/M_SDF_GildedFiligree",
            "/Game/EnvSandbox/Materials/Masters/M_SDF_GildedFiligree",
        ),
        (
            "/Game/_PROJECT/04_Materials/baroque/M_SDF_RoseWindow",
            "/Game/EnvSandbox/Materials/Masters/M_SDF_RoseWindow",
        ),
        (
            "/Game/_PROJECT/04_Materials/SDF/M_SDF_TrueParallax_Inst",
            "/Game/EnvSandbox/Materials/SDF/Instances/M_SDF_TrueParallax_Inst",
        ),
        (
            "/Game/_PROJECT/04_Materials/SDF/M_SDF_TrueParallax",
            "/Game/EnvSandbox/Materials/Masters/M_SDF_TrueParallax",
        ),
        (
            "/Game/_PROJECT/04_Materials/SDF/M_SDF_RayMarch_Gothic",
            "/Game/EnvSandbox/Materials/Masters/M_SDF_RayMarch_Gothic",
        ),
    ],
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def _fstring_blob(path: str) -> bytes:
    raw = path.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def patch_file(path: Path, report: dict) -> int:
    if not path.exists():
        return 0
    data = bytearray(path.read_bytes())
    changed = 0
    for old_path, new_path in REPLACEMENTS:
        old_blob = _fstring_blob(old_path)
        new_blob = _fstring_blob(new_path)
        count = bytes(data).count(old_blob)
        if count:
            data = bytearray(bytes(data).replace(old_blob, new_blob))
            changed += count
            report["changes"].append(
                {
                    "file": str(path.relative_to(PROJECT_ROOT)),
                    "from": old_path,
                    "to": new_path,
                    "count": count,
                }
            )
    if changed:
        path.write_bytes(data)
    return changed


def main() -> int:
    print("ERROR: patch_portfolio_uasset_paths.py is disabled (corrupts uassets).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
