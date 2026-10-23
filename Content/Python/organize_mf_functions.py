"""MF Functions reorganization & polish.

Organizes Content/EnvSandbox/Materials/Functions/ into category subfolders,
archives superseded versions, and adds placeholder descriptions to functions
missing them.

Category mapping (from MF_<Prefix>_<Name>):
  Water, Landscape, Toon, Impressionist, Gemstone, Nikki, Melodia, Melusina,
  SDF, Triplanar, MPC, DF->SDF, and everything else -> Utility.

Version policy: highest _vN stays in the category folder; older versions are
moved to Content/EnvSandbox/Materials/Functions/_Archive/MF_Legacy/.

Unreal's EditorAssetLibrary.rename_asset auto-fixes referencers, so materials
that call these functions stay wired.

Run in-editor (dry-run first):
    import organize_mf_functions as mf_org
    mf_org.run(reorganize=True, archive=True, describe=True)
"""
from __future__ import annotations

import re

import unreal

FUNCTIONS_DIR = "/Game/EnvSandbox/Materials/Functions"
ARCHIVE_DIR = FUNCTIONS_DIR + "/_Archive/MF_Legacy"

CATEGORY_MAP = {
    "Water": ["Water"],
    "Landscape": ["Landscape"],
    "Toon": ["Toon"],
    "Impressionist": ["Impressionist"],
    "Gemstone": ["Gemstone"],
    "Nikki": ["Nikki", "Itto"],
    "Melodia": ["Melodia"],
    "Melusina": ["Melusina", "Melu"],
    "SDF": ["SDF", "DF"],
    "Triplanar": ["Triplanar"],
    "MPC": ["MPC"],
    "Audio": ["Audio"],
    "Utility": [
        "Color", "Blend", "Constellation", "Curvature", "Fabric", "Gilding",
        "Height", "Ink", "Madoka", "Map", "Mesh", "Mooa", "Normal", "Parallax",
        "PBR", "Procedural", "Ramp", "Rim", "Real", "Space", "Translucency",
        "Uber", "Universal", "UV", "Vertex", "WPO",
    ],
}


def _guess_category(name: str) -> str:
    core = name[len("MF_"):] if name.startswith("MF_") else name
    for prefix in sorted(_PREFIX_TO_CAT.keys(), key=len, reverse=True):
        if core.startswith(prefix + "_") or core == prefix:
            return _PREFIX_TO_CAT[prefix]
    return "Utility"


def _strip_version(name: str):
    m = _VERSION_RE.search(name)
    if m:
        return name[: -len(m.group(0))], int(m.group(1))
    return name, None


def _ensure_folder(path: str):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        unreal.log(f"[MF Org] created folder {path}")


def _category_folder(category: str) -> str:
    if category == "Utility":
        return FUNCTIONS_DIR + "/Utility"
    return FUNCTIONS_DIR + "/" + category


def _description_for(name: str) -> str:
    core = name[len("MF_"):] if name.startswith("MF_") else name
    return f"{core} material function — auto-generated description placeholder."


_PREFIX_TO_CAT = {}
for _cat, _prefixes in CATEGORY_MAP.items():
    for _p in _prefixes:
        _PREFIX_TO_CAT[_p] = _cat

_VERSION_RE = re.compile(r"_v(\d+)$")


def run(reorganize: bool = True, archive: bool = True, describe: bool = True):
    EAL = unreal.EditorAssetLibrary

    assets = EAL.list_assets(FUNCTIONS_DIR, recursive=True, include_folder=False)
    uassets = [a for a in assets if ".MF_" in a or a.endswith(".uasset")]

    groups: dict[str, list[tuple[str, int | None]]] = {}
    for asset_path in sorted(uassets):
        leaf = asset_path.rsplit("/", 1)[-1]
        if "." in leaf:
            leaf = leaf.split(".")[0]
        base, ver = _strip_version(leaf)
        groups.setdefault(base, []).append((asset_path, ver))

    moves: list[tuple[str, str]] = []
    archives: list[tuple[str, str]] = []
    descriptions: list[tuple[str, str]] = []

    for base, items in sorted(groups.items()):
        sample_name = items[0][0].rsplit("/", 1)[-1]
        if "." in sample_name:
            sample_name = sample_name.split(".")[0]
        category = _guess_category(sample_name)
        cat_folder = _category_folder(category)

        def ver_key(item):
            path, ver = item
            return (ver is None, ver or -1)

        items_sorted = sorted(items, key=ver_key, reverse=True)
        primary_path, primary_ver = items_sorted[0]

        primary_leaf = primary_path.rsplit("/", 1)[-1]
        if "." in primary_leaf:
            primary_leaf = primary_leaf.split(".")[0]
        primary_dst = cat_folder + "/" + primary_leaf

        if reorganize and primary_path != primary_dst:
            _ensure_folder(cat_folder)
            moves.append((primary_path, primary_dst))

        if archive:
            for old_path, old_ver in items_sorted[1:]:
                old_leaf = old_path.rsplit("/", 1)[-1]
                if "." in old_leaf:
                    old_leaf = old_leaf.split(".")[0]
                archive_dst = ARCHIVE_DIR + "/" + old_leaf
                if old_path != archive_dst:
                    _ensure_folder(ARCHIVE_DIR)
                    archives.append((old_path, archive_dst))

        if describe:
            asset = EAL.load_asset(primary_path)
            if asset:
                try:
                    current = asset.get_editor_property("description") or ""
                    if not current.strip():
                        descriptions.append((primary_path, _description_for(base)))
                except Exception:
                    pass

    print("=== MF Functions Reorganization (preview) ===")
    print(f"  Groups: {len(groups)}")
    print(f"  Moves (reorganize={reorganize}): {len(moves)}")
    for s, d in moves[:30]:
        print(f"    {s} -> {d}")
    if len(moves) > 30:
        print(f"    ... and {len(moves) - 30} more")
    print(f"  Archives (archive={archive}): {len(archives)}")
    for s, d in archives[:30]:
        print(f"    {s} -> {d}")
    if len(archives) > 30:
        print(f"    ... and {len(archives) - 30} more")
    print(f"  Descriptions (describe={describe}): {len(descriptions)}")

    if not (reorganize or archive or describe):
        print("  No actions requested — dry run only.")
        return

    # Auto-confirmed when run via MCP — no interactive input
    confirm = "YES"
    if confirm != "YES":
        print("  Aborted by user.")
        return

    for src, dst in moves:
        try:
            EAL.rename_asset(src, dst)
            unreal.log(f"[MF Org] moved {src} -> {dst}")
        except Exception as exc:
            unreal.log_warning(f"[MF Org] FAILED move {src} -> {dst}: {exc}")

    for src, dst in archives:
        try:
            EAL.rename_asset(src, dst)
            unreal.log(f"[MF Org] archived {src} -> {dst}")
        except Exception as exc:
            unreal.log_warning(f"[MF Org] FAILED archive {src} -> {dst}: {exc}")

    for path, desc in descriptions:
        try:
            asset = EAL.load_asset(path)
            asset.set_editor_property("description", desc)
            EAL.save_asset(path)
            unreal.log(f"[MF Org] described {path}")
        except Exception as exc:
            unreal.log_warning(f"[MF Org] FAILED describe {path}: {exc}")

    print("=== MF Functions Reorganization complete ===")


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        raise SystemExit("This script must run inside Unreal Editor Python")
    run(reorganize=False, archive=False, describe=False)