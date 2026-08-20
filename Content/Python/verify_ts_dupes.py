"""Verify every zero-ref Textures_Shared asset is byte-identical to a twin elsewhere.

Writes Saved/Audit/ts_dupe_verify.json: per TS asset -> {identical_twin, safe}.
safe = zero registry referencers AND byte-identical twin exists outside Textures_Shared.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "Content"
TS_DIR = CONTENT / "EnvSandbox" / "Textures_Shared"
OUT = ROOT / "Saved" / "Audit" / "ts_dupe_verify.json"


def file_hash(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    deps = unreal.AssetRegistryDependencyOptions()

    ts_files = [p for p in TS_DIR.rglob("*.uasset") if p.is_file()]
    other_files = [p for p in CONTENT.rglob("*.uasset") if p.is_file() and not str(p).startswith(str(TS_DIR))]

    hash_by_stem: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for p in other_files:
        hash_by_stem[p.stem].append((file_hash(p), p))

    safe, unsafe, no_twin = [], [], []
    for p in ts_files:
        game = "/Game/EnvSandbox/Textures_Shared/" + str(p.relative_to(TS_DIR)).replace("\\", "/").removesuffix(".uasset")
        refs = ar.get_referencers(game, deps)
        if refs:
            unsafe.append({"path": game, "reason": f"{len(refs)} referencers"})
            continue
        twins = [t for t in hash_by_stem.get(p.stem, []) if t[0] == file_hash(p)]
        if twins:
            safe.append({"path": game, "identical_twin": str(twins[0][1]).replace(str(ROOT), "")})
        else:
            no_twin.append({"path": game, "reason": "no byte-identical twin outside Textures_Shared"})

    report = {
        "generated": "2026-08-13",
        "textures_shared_count": len(ts_files),
        "safe_delete": safe,
        "unsafe_referenced": unsafe,
        "no_identical_twin": no_twin,
        "summary": {"safe": len(safe), "unsafe": len(unsafe), "no_twin": len(no_twin)},
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"TS assets: {len(ts_files)}")
    print(f"SAFE (zero-ref + byte-identical twin): {len(safe)}")
    print(f"UNSAFE (has referencers): {len(unsafe)}")
    print(f"NO twin (unique content): {len(no_twin)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
