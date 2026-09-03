"""Patch portfolio SDF texture uassets: replace _PROJECT FString paths with local copies."""
from __future__ import annotations

import json
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXTURES = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "SDF" / "Textures"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_texture_path_patch.json"

REPLACEMENTS: list[tuple[str, str]] = [
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
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_2_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_2_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_4_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_4_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_10_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_10_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_11_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_11_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_12_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_12_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_13_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_13_-_512x512",
    ),
    (
        "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_14_-_512x512",
        "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_14_-_512x512",
    ),
]


def _fstring_blob(path: str) -> bytes:
    raw = path.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def patch_file(path: Path, report: dict) -> int:
    data = bytearray(path.read_bytes())
    changed = 0
    for old_path, new_path in REPLACEMENTS:
        old_blob = _fstring_blob(old_path)
        new_blob = _fstring_blob(new_path)
        count = data.count(old_blob)
        if count:
            data = bytearray(bytes(data).replace(old_blob, new_blob))
            changed += count
            report["changes"].append(
                {"file": str(path.relative_to(PROJECT_ROOT)), "from": old_path, "to": new_path, "count": count}
            )
    if changed:
        path.write_bytes(data)
    return changed


def main() -> int:
    print(
        "ERROR: patch_portfolio_texture_paths.py is disabled — FString length changes corrupt texture uassets. "
        "Use rewire_portfolio_texture_refs.py inside the editor instead."
    )
    return 1
    report: dict = {"patched_refs": 0, "files_touched": 0, "changes": [], "errors": []}
    if not TEXTURES.exists():
        report["errors"].append(f"missing: {TEXTURES}")
        return 1
    for path in TEXTURES.rglob("*.uasset"):
        n = patch_file(path, report)
        if n:
            report["patched_refs"] += n
            report["files_touched"] += 1
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
