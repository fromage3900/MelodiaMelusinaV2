"""Compute SAFE-to-delete duplicate textures: byte-identical to a referenced twin.

Safety proof per candidate:
  1. Registry reports zero referencers for the candidate path.
  2. The file is byte-identical to another .uasset with the same stem elsewhere
     in EnvSandbox (the canonical copy that carries the real references).

Deletes NOTHING - writes Saved/Audit/safe_delete_textures.json with the list.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "safe_delete_textures.json"


def file_hash(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def game_to_disk(game: str) -> Path:
    return ROOT / "Content" / (game.removeprefix("/Game/").replace("/", "\\") + ".uasset")


def main() -> int:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    deps = unreal.AssetRegistryDependencyOptions()
    assets = unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox", recursive=True, include_folder=False)

    # Map stem -> list of (path, hash)
    by_stem = defaultdict(list)
    for path in assets:
        disk = game_to_disk(path.split(".", 1)[0])
        if not disk.is_file():
            continue
        try:
            h = file_hash(disk)
        except OSError:
            continue
        by_stem[disk.stem].append((path, h))

    safe = []
    for stem, entries in by_stem.items():
        if len(entries) < 2:
            continue
        hashes = defaultdict(list)
        for path, h in entries:
            hashes[h].append(path)
        for h, group in hashes.items():
            if len(group) < 2:
                continue
            for cand in group:
                refs = ar.get_referencers(cand.split(".", 1)[0], deps)
                if not refs:
                    others = [g for g in group if g != cand]
                    referenced = any(
                        ar.get_referencers(o.split(".", 1)[0], deps) for o in others
                    )
                    if referenced:
                        safe.append({
                            "candidate": cand,
                            "identical_twins": others,
                            "twin_referenced": True,
                        })

    report = {
        "generated": "2026-08-13",
        "safe_delete_count": len(safe),
        "candidates": safe,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"safe-delete texture candidates: {len(safe)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
