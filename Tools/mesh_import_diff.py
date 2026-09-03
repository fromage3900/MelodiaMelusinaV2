"""Build a diff manifest: staged mesh files in Imports/Environment vs already-imported
Content meshes (offline, no unreal import). Writes Saved/Audit/mesh_import_diff.json.

Pure disk scan. Classifies each staged mesh file as:
  - already_imported : a Content uasset with the same stem exists under the mesh roots
  - missing          : no matching uasset on disk -> candidate for import
  - duplicate_pack   : the file is inside a pack folder that shares its archive SHA
                       with another pack (imported once via the other pack)
  - unlicensed       : pack folder with no PROVENANCE / license-unconfirmed -> hold

Mesh roots scanned for existing assets:
  Content/EnvSandbox/Meshes/Environment, Content/EnvSandbox/Meshes/Cathedral,
  Content/EnvSandbox/Meshes/Ornament, Content/EnvSandbox/Meshes/OrnamentMusical,
  Content/EnvSandbox/Meshes/Sakura
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORTS = PROJECT_ROOT / "Imports" / "Environment"
CONTENT = PROJECT_ROOT / "Content"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "mesh_import_diff.json"

MESH_EXTS = {".fbx", ".obj", ".glb", ".gltf", ".dae", ".stl"}

MESH_ROOTS = [
    CONTENT / "EnvSandbox" / "Meshes",
    CONTENT / "EnvSandbox" / "Meshes" / "Environment",
    CONTENT / "EnvSandbox" / "Meshes" / "Cathedral",
    CONTENT / "EnvSandbox" / "Meshes" / "Ornament",
    CONTENT / "EnvSandbox" / "Meshes" / "OrnamentMusical",
    CONTENT / "EnvSandbox" / "Meshes" / "Sakura",
]

# Pack folders that share archive content (LowPolyCrystals == KenneyModularCave).
DUPLICATE_PACK_SHA = {"48F37A6D4F241124CD7DA17DA1C6D4ED1BF1820BB149DCB233FBD5EBDD8BA996"}

# Packs with no PROVENANCE or confirmed license issues -> hold, never import.
UNLICENSED_PACKS = {
    "Instruments",
    "MelusinaTileables",
    "PBRFabrics",
    "Trimsheets",
    "ViolinScans",
}


def sha256_of_zip(folder: Path) -> str:
    for zip_file in sorted(folder.glob("*.zip")):
        try:
            h = hashlib.sha256()
            with open(zip_file, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            return h.hexdigest().upper()
        except OSError:
            continue
    return ""


def existing_stems() -> set[str]:
    stems: set[str] = set()
    for root in MESH_ROOTS:
        if not root.exists():
            continue
        for uasset in root.rglob("*.uasset"):
            stems.add(uasset.stem.lower())
    return stems


def main() -> int:
    if not IMPORTS.exists():
        print(f"[mesh_diff] imports root missing: {IMPORTS}")
        return 2

    existing = existing_stems()
    pack_sha: dict[str, str] = {}

    missing: list[str] = []
    already: list[str] = []
    unlicensed: list[str] = []
    dup_in_pack: list[str] = []

    for pack_dir in sorted(p for p in IMPORTS.iterdir() if p.is_dir()):
        pack_name = pack_dir.name
        is_unlicensed = pack_name in UNLICENSED_PACKS
        if not is_unlicensed and not (pack_dir / "PROVENANCE.md").exists():
            is_unlicensed = True
        sha = sha256_of_zip(pack_dir)
        pack_sha[pack_name] = sha
        duplicate_pack = bool(sha and sha in DUPLICATE_PACK_SHA and pack_name != "KenneyModularCave")

        for mesh in sorted(pack_dir.rglob("*")):
            if not mesh.is_file() or mesh.suffix.lower() not in MESH_EXTS:
                continue
            rel = mesh.relative_to(IMPORTS).as_posix()
            stem = mesh.stem.lower()
            if is_unlicensed:
                unlicensed.append(rel)
            elif duplicate_pack:
                dup_in_pack.append(rel)
            elif stem in existing:
                already.append(rel)
            else:
                missing.append(rel)

    summary = {
        "staged_mesh_files": len(already) + len(missing) + len(unlicensed) + len(dup_in_pack),
        "already_imported": len(already),
        "missing": len(missing),
        "unlicensed_held": len(unlicensed),
        "duplicate_pack_held": len(dup_in_pack),
        "existing_asset_stems": len(existing),
    }
    report = {
        "generated": "2026-08-13",
        "imports_root": str(IMPORTS),
        "summary": summary,
        "pack_sha256": pack_sha,
        "already_imported": already,
        "missing": missing,
        "unlicensed_held": unlicensed,
        "duplicate_pack_held": dup_in_pack,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
