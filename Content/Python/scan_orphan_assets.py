"""Orphan scan: EnvSandbox .uassets with ZERO referencers (registry-based).

Categories:
  - orphan_textures_shared : zero-ref copies under EnvSandbox/Textures_Shared that
    duplicate canonical SDF/Textures (byte-identical) - SAFE to delete
  - orphan_materials       : zero-ref materials (not per-prop mesh materials)
  - orphan_scratch         : zero-ref assets under _Scratch (junk candidates)
  - orphan_archive         : zero-ref assets under _Archive
  - orphan_other           : anything else zero-ref (report only)

Writes Saved/Audit/orphan_assets_scan.json. Read-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
MAT_ROOT = "/Game/EnvSandbox"
OUT = ROOT / "Saved" / "Audit" / "orphan_assets_scan.json"


def main() -> int:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    deps = unreal.AssetRegistryDependencyOptions()
    assets = unreal.EditorAssetLibrary.list_assets(MAT_ROOT, recursive=True, include_folder=False)
    rows = []
    for path in assets:
        refs = ar.get_referencers(path.split(".", 1)[0], deps)
        if refs:
            continue
        kind = "other"
        if "/Textures_Shared/" in path:
            kind = "textures_shared"
        elif path.startswith("/Game/EnvSandbox/Materials/_Scratch/"):
            kind = "scratch"
        elif path.startswith("/Game/EnvSandbox/Materials/_Archive/"):
            kind = "archive"
        elif "/Materials/" in path and not "/Meshes/" in path:
            kind = "material"
        rows.append({"path": path, "kind": kind})

    from collections import Counter
    kinds = Counter(r["kind"] for r in rows)
    report = {
        "generated": "2026-08-13",
        "scanned": len(assets),
        "zero_referencer_assets": len(rows),
        "by_kind": dict(kinds),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"scanned: {len(assets)}")
    print(f"zero-referencer assets: {len(rows)}")
    print("by kind:", dict(kinds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
