"""One-off inventory scan: Melodia Content materials → category counts."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"G:\Melodia\Content")

BATCH1_MEL = {
    "M_SDF_TrueParallax",
    "M_SDF_GildedStucco",
    "M_SDF_GildedFiligree",
    "M_SDF_OrnamentLayer",
    "M_SDF_OrnamentLayer_Enhanced",
    "M_SDF_Baroque",
}

MATERIAL_PREFIX = re.compile(r"^(M_|MI_|ML_|MF_|MPC_)", re.I)


def classify(name: str, rel: str) -> str:
    rl = rel.lower().replace("\\", "/")
    n = name.lower()

    if any(x in rl for x in ("/dev/", "/test", "testbench", "/debug")):
        return "defer_dev"
    if any(
        x in n
        for x in (
            "musical",
            "music",
            "beat",
            "vinyl",
            "trebleclef",
            "grandstaff",
            "sheetmusic",
            "floatingnotes",
            "pulsinggeometry",
        )
    ):
        return "defer_game"
    if any(x in n for x in ("magicorb", "cosmicportal", "combat")):
        return "defer_vfx"
    if "materiallayer" in rl or name.startswith("ML_"):
        return "defer_layers"

    if "sdf" in n or "/sdf/" in rl or "raymarch" in n:
        if any(x in n for x in ("mandelbulb", "julia", "klein", "fractal", "math")):
            return "sdf_math"
        if "/underwater/" in rl or any(
            x in n for x in ("coral", "kelp", "caustic", "underwater", "seaweed")
        ):
            return "sdf_underwater"
        return "sdf"

    if any(x in rl for x in ("landscape", "terrain", "heightfield")):
        return "landscape"
    if any(
        x in n
        for x in ("grass", "foliage", "leaf", "tree", "bark", "moss", "fern", "ivy", "plant")
    ):
        return "foliage"
    if any(x in n for x in ("toon", "cel", "stylized", "stylised", "cartoon", "anime")):
        return "stylized"
    if any(x in rl for x in ("character", "skin", "hair", "cloth", "fabric", "costume")):
        return "character"
    if "/ui/" in rl or "widget" in rl or "/hud/" in rl:
        return "ui"
    if any(x in n for x in ("pp_", "postprocess", "outline", "screen")):
        return "postprocess"

    if any(
        x in n
        for x in (
            "stone",
            "wood",
            "metal",
            "concrete",
            "brick",
            "marble",
            "plaster",
            "stucco",
            "gold",
            "glass",
            "water",
            "fabric",
            "leather",
            "paint",
            "oil",
            "hybrid",
            "universal",
        )
    ):
        return "environment"
    if "/04_materials/" in rl or "/materials/" in rl:
        return "environment"

    return "other"


def migration_status(name: str) -> str:
    if name in BATCH1_MEL:
        return "batch1_migrated"
    base = name.replace("_Enhanced", "")
    if base in BATCH1_MEL:
        return "batch1_migrated"
    if name.startswith("MI_Toon_SDF"):
        return "batch1_instance"
    return "remaining"


def tier_for_sdf(name: str, rel: str) -> str:
    n, rl = name.lower(), rel.lower()
    if any(x in n for x in ("musical", "music", "magic", "portal", "test", "vinyl", "staff", "clef", "note")):
        return "C"
    if "underwater" in rl or any(x in n for x in ("mandel", "julia", "klein", "fractal")):
        return "B"
    return "A"


def main() -> None:
    materials: list[tuple[str, str, str]] = []
    textures: list[tuple[str, str]] = []

    for p in ROOT.rglob("*.uasset"):
        name = p.stem
        rel = str(p.relative_to(ROOT))
        if MATERIAL_PREFIX.match(name):
            materials.append((name, rel, classify(name, rel)))
        elif name.startswith("T_") or "/textures/" in rel.lower():
            textures.append((name, rel))

    cats: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for name, rel, cat in materials:
        cats[cat].append((name, rel))

    order = [
        "sdf",
        "sdf_underwater",
        "sdf_math",
        "environment",
        "landscape",
        "foliage",
        "stylized",
        "character",
        "postprocess",
        "ui",
        "defer_layers",
        "defer_game",
        "defer_vfx",
        "defer_dev",
        "other",
    ]

    print("=== MATERIAL COUNTS BY CATEGORY ===")
    for cat in order:
        items = cats.get(cat, [])
        masters = sum(
            1
            for n, _ in items
            if n.startswith("M_") and not n.startswith("MI_") and not n.startswith("ML_")
        )
        inst = sum(1 for n, _ in items if n.startswith("MI_"))
        ml = sum(1 for n, _ in items if n.startswith("ML_"))
        mf = sum(1 for n, _ in items if n.startswith("MF_"))
        mpc = sum(1 for n, _ in items if n.startswith("MPC_"))
        print(f"{cat:16} total={len(items):4}  M={masters} MI={inst} ML={ml} MF={mf} MPC={mpc}")

    print(f"\nTOTAL material-like: {len(materials)}")
    print(f"TOTAL textures: {len(textures)}")

    sdf_all = cats["sdf"] + cats["sdf_underwater"] + cats["sdf_math"]
    sdf_masters = sorted({(n, r) for n, r in sdf_all if n.startswith("M_") and not n.startswith("MI_")})

    print("\n=== ALL SDF MASTERS ===")
    tier_a_rem = tier_b = tier_c = 0
    for name, rel in sdf_masters:
        tier = tier_for_sdf(name, rel)
        status = migration_status(name)
        if tier == "A" and status == "remaining":
            tier_a_rem += 1
        elif tier == "B":
            tier_b += 1
        elif tier == "C":
            tier_c += 1
        print(f"  [Tier {tier}] [{status:16}] {name}  |  {rel}")

    print(f"\nSDF masters total: {len(sdf_masters)}")
    print(f"  Tier A remaining: {tier_a_rem}")
    print(f"  Tier B: {tier_b}")
    print(f"  Tier C: {tier_c}")
    print(f"  Batch 1 migrated sources: {sum(1 for n,_ in sdf_masters if migration_status(n)=='batch1_migrated')}")

    for cat_name in ("environment", "stylized", "landscape", "foliage"):
        items = cats.get(cat_name, [])
        masters = [n for n, _ in items if n.startswith("M_") and not n.startswith("MI_")]
        print(f"\n=== {cat_name.upper()} masters ({len(masters)}) ===")
        for n in sorted(masters)[:50]:
            print(f"  {n}")
        if len(masters) > 50:
            print(f"  ... +{len(masters)-50} more")

    defer_total = sum(len(cats.get(c, [])) for c in ("defer_layers", "defer_game", "defer_vfx", "defer_dev", "ui"))
    print(f"\nDEFER (layers+game+vfx+dev+ui): {defer_total}")


if __name__ == "__main__":
    main()
