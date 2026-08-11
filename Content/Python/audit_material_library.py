"""Audit BS_GodFile material library: orphans, dead refs, duplicates, Melodia paths.

Run standalone (no editor):
  python Content/Python/audit_material_library.py

Run in UE editor (adds redirector detection):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_material_library.py"
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Repo root: Content/Python -> Content -> project
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = PROJECT_ROOT / "Content"
MATERIALS_ROOT = CONTENT_ROOT / "EnvSandbox" / "Materials"
ENVSANDBOX_ROOT = CONTENT_ROOT / "EnvSandbox"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "material_library_audit.json"

PATH_RE = re.compile(rb"(/Game/[A-Za-z0-9_./-]+)\x00")
MATERIAL_PREFIX = re.compile(r"^(M_|MI_|MF_|TP_)", re.I)
TEXTURE_NAME = re.compile(
    r"^(T_|Marble_|Perlin_|Voronoi_|Noise_|SDF_)", re.I
)
MELODIA_PATH_MARKERS = ("/Game/_PROJECT/", "/Game/Melodia/")

# Schema: textures belong under SDF/Textures/ (or documented exceptions)
TEXTURE_SCHEMA_DIRS = (
    "/Game/EnvSandbox/Materials/SDF/Textures/",
)


def asset_game_path(uasset: Path) -> str:
    rel = uasset.relative_to(CONTENT_ROOT).with_suffix("")
    return "/Game/" + rel.as_posix()


def extract_paths(data: bytes) -> set[str]:
    return {m.group(1).decode("ascii", "ignore") for m in PATH_RE.finditer(data)}


def resolve_on_disk(game_path: str) -> Path | None:
    if not game_path.startswith("/Game/"):
        return None
    rel = game_path.removeprefix("/Game/").replace("/", "\\") + ".uasset"
    candidate = CONTENT_ROOT / rel
    return candidate if candidate.exists() else None


def is_texture_asset(uasset: Path) -> bool:
    name = uasset.stem
    path_lower = str(uasset).lower()
    if TEXTURE_NAME.match(name):
        return True
    if "/textures/" in path_lower:
        return True
    return False


def is_material_like(uasset: Path) -> bool:
    return bool(MATERIAL_PREFIX.match(uasset.stem))


def classify_texture_folder(game_path: str) -> str | None:
    """Return issue string if texture is outside schema, else None."""
    if not any(game_path.startswith(d) for d in TEXTURE_SCHEMA_DIRS):
        return f"outside schema (expected under SDF/Textures/): {game_path}"
    return None


def scan_tree(root: Path) -> dict:
    all_uassets: dict[str, Path] = {}
    textures: dict[str, Path] = {}
    materials: dict[str, Path] = {}

    if not root.exists():
        return {
            "error": f"root missing: {root}",
            "textures": {},
            "materials": {},
            "all_uassets": {},
        }

    for p in root.rglob("*.uasset"):
        ap = asset_game_path(p)
        all_uassets[ap] = p
        if is_texture_asset(p):
            textures[ap] = p
        if is_material_like(p):
            materials[ap] = p

    refs_from: dict[str, set[str]] = defaultdict(set)
    refs_to: dict[str, set[str]] = defaultdict(set)
    melodia_refs: list[dict[str, str]] = []
    missing_texture_refs: list[dict[str, str]] = []

    for p in root.rglob("*.uasset"):
        ap = asset_game_path(p)
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for ref in extract_paths(data):
            if ref == ap:
                continue
            refs_from[ap].add(ref)
            refs_to[ref].add(ap)
            if any(m in ref for m in MELODIA_PATH_MARKERS):
                melodia_refs.append({"source": ap, "target": ref})
            if (
                "/Textures/" in ref
                or ref.rsplit("/", 1)[-1].startswith("T_")
                or any(
                    x in ref
                    for x in ("Marble_", "Perlin_", "Voronoi_", "Noise_", "SDF_")
                )
            ):
                if resolve_on_disk(ref) is None:
                    missing_texture_refs.append({"source": ap, "target": ref})

    orphans = sorted(
        tap
        for tap in textures
        if not refs_to.get(tap)
    )

    by_name: dict[str, list[str]] = defaultdict(list)
    for tap in textures:
        by_name[Path(tap).name].append(tap)
    duplicates = {k: v for k, v in by_name.items() if len(v) > 1}

    wrong_folder = [
        {"path": tap, "issue": issue}
        for tap in textures
        if (issue := classify_texture_folder(tap))
    ]

    # Materials referencing missing textures (any path)
    dead_material_refs: list[dict[str, str]] = []
    seen_dead: set[tuple[str, str]] = set()
    for src, ref in [
        (s, r) for s, refs in refs_from.items() for r in refs if s in materials
    ]:
        if resolve_on_disk(ref) is None and not any(m in ref for m in MELODIA_PATH_MARKERS):
            key = (src, ref)
            if key not in seen_dead:
                seen_dead.add(key)
                dead_material_refs.append({"source": src, "target": ref})

    return {
        "root": str(root),
        "texture_count": len(textures),
        "material_count": len(materials),
        "uasset_count": len(all_uassets),
        "orphan_textures": orphans,
        "missing_texture_refs": missing_texture_refs,
        "dead_material_refs": dead_material_refs,
        "melodia_path_refs": melodia_refs,
        "duplicate_texture_names": duplicates,
        "wrong_folder_textures": wrong_folder,
        "refs_from": {k: sorted(v) for k, v in refs_from.items()},
        "refs_to": {k: sorted(v) for k, v in refs_to.items()},
    }


def scan_envsandbox_melodia_refs() -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if not ENVSANDBOX_ROOT.exists():
        return found
    for p in ENVSANDBOX_ROOT.rglob("*.uasset"):
        ap = asset_game_path(p)
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for ref in extract_paths(data):
            if any(m in ref for m in MELODIA_PATH_MARKERS):
                found.append({"source": ap, "target": ref})
    return found


def count_legacy_content() -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in ("_PROJECT", "Textures", "04_Materials", "Melodia"):
        d = CONTENT_ROOT / name
        if d.exists():
            counts[name] = sum(1 for _ in d.rglob("*.uasset"))
    return counts


def try_redirector_scan() -> dict | None:
    try:
        import unreal  # type: ignore
    except ImportError:
        return None

    redirectors: list[str] = []
    if MATERIALS_ROOT.exists():
        paths = unreal.EditorAssetLibrary.list_assets(
            "/Game/EnvSandbox/Materials", recursive=True, include_folder=False
        )
        for p in paths:
            ad = unreal.EditorAssetLibrary.find_asset_data(p)
            if str(ad.asset_class) == "ObjectRedirector":
                redirectors.append(p)
    melodia_redirectors = [p for p in redirectors if "_PROJECT" in p or "Melodia" in p]
    return {
        "redirector_count": len(redirectors),
        "melodia_redirector_count": len(melodia_redirectors),
        "redirectors": redirectors[:50],
        "melodia_redirectors": melodia_redirectors[:50],
    }


def print_report(materials: dict, env_melodia: list, legacy: dict, redirectors: dict | None) -> None:
    print("=" * 60)
    print("BS_GodFile Material Library Audit")
    print("=" * 60)
    print(f"Materials root: {materials.get('root')}")
    print(f"  Textures:  {materials.get('texture_count', 0)}")
    print(f"  Materials: {materials.get('material_count', 0)}")
    print(f"  UAssets:   {materials.get('uasset_count', 0)}")

    orphans = materials.get("orphan_textures", [])
    print(f"\n--- Orphan textures (no incoming refs): {len(orphans)} ---")
    for o in orphans[:15]:
        print(f"  {o}")
    if len(orphans) > 15:
        print(f"  ... +{len(orphans) - 15} more")

    missing = materials.get("missing_texture_refs", [])
    unique_missing = {(m["source"], m["target"]) for m in missing}
    print(f"\n--- Missing texture refs (pink risk): {len(unique_missing)} ---")
    for src, tgt in sorted(unique_missing)[:20]:
        print(f"  {src.rsplit('/', 1)[-1]} -> {tgt}")
    if len(unique_missing) > 20:
        print(f"  ... +{len(unique_missing) - 20} more")

    dead = materials.get("dead_material_refs", [])
    print(f"\n--- Dead material refs (non-Melodia, missing on disk): {len(dead)} ---")
    for d in dead[:15]:
        print(f"  {d['source'].rsplit('/', 1)[-1]} -> {d['target']}")

    mel = materials.get("melodia_path_refs", [])
    mel_unique = sorted({m["target"] for m in mel})
    print(f"\n--- Melodia/_PROJECT refs inside Materials: {len(mel_unique)} unique ---")
    for r in mel_unique[:15]:
        print(f"  {r}")
    if len(mel_unique) > 15:
        print(f"  ... +{len(mel_unique) - 15} more")

    env_unique = sorted({m["target"] for m in env_melodia})
    print(f"\n--- Melodia/_PROJECT refs in all EnvSandbox: {len(env_unique)} unique ---")
    for r in env_unique[:10]:
        print(f"  {r}")

    dupes = materials.get("duplicate_texture_names", {})
    print(f"\n--- Duplicate texture names: {len(dupes)} ---")
    for name, paths in sorted(dupes.items()):
        print(f"  {name}:")
        for p in paths:
            print(f"    {p}")

    wrong = materials.get("wrong_folder_textures", [])
    print(f"\n--- Wrong-folder textures: {len(wrong)} ---")
    for w in wrong[:10]:
        print(f"  {w['path']}")

    print("\n--- Legacy Content folders (not in schema) ---")
    for k, v in sorted(legacy.items()):
        print(f"  Content/{k}: {v} uassets")

    if redirectors:
        print(f"\n--- Redirectors (editor scan): {redirectors['redirector_count']} ---")
        for r in redirectors.get("redirectors", [])[:10]:
            print(f"  {r}")

    print(f"\nFull JSON report: {REPORT_PATH}")


def main() -> int:
    materials = scan_tree(MATERIALS_ROOT)
    env_melodia = scan_envsandbox_melodia_refs()
    legacy = count_legacy_content()
    redirectors = try_redirector_scan()

    report = {
        "materials": materials,
        "envsandbox_melodia_refs": env_melodia,
        "legacy_content_counts": legacy,
        "redirectors": redirectors,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print_report(materials, env_melodia, legacy, redirectors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
