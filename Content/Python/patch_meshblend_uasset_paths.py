"""Binary uasset FString path patch for MeshBlend activator refs (no editor required).

Patches ANSI FString soft paths in EnvSandbox material uassets.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "meshblend_activator_fix.json"

REPLACEMENTS: list[tuple[str, str]] = [
    (
        "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index",
        "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_0",
    ),
    (
        "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index",
        "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_0",
    ),
    (
        "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index_0",
        "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_0",
    ),
    (
        "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index_1",
        "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_1",
    ),
]

TARGETS = sorted(
    set(
        list((PROJECT_ROOT / "Content/EnvSandbox/Materials/Masters").glob("M_*.uasset"))
        + list((PROJECT_ROOT / "Content/EnvSandbox/Materials/Functions").glob("MF_MeshBlend*.uasset"))
    )
)


def _fstring_blob(path: str) -> bytes:
    raw = path.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def patch_file(path: Path, report: dict) -> int:
    if not path.exists():
        report["errors"].append(f"missing: {path}")
        return 0

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
    report: dict = {"patched_refs": 0, "files_touched": 0, "changes": [], "errors": []}
    for target in TARGETS:
        n = patch_file(target, report)
        if n:
            report["patched_refs"] += n
            report["files_touched"] += 1

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
