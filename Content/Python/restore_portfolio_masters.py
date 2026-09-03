"""Restore EnvSandbox SDF masters from _PROJECT/04_Materials (never deletes _PROJECT)."""
from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials"
DST = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"

RESTORE_MAP: list[tuple[str, str]] = [
    ("SDF/M_SDF_TrueParallax", "M_SDF_TrueParallax"),
    ("baroque/M_SDF_GildedStucco", "M_SDF_GildedStucco"),
    ("baroque/M_SDF_GildedFiligree", "M_SDF_GildedFiligree"),
    ("SDF/M_SDF_Baroque", "M_SDF_Baroque"),
    ("SDF/M_SDF_OrnamentLayer", "M_SDF_OrnamentLayer"),
    ("SDF/M_SDF_OrnamentLayer_Enhanced", "M_SDF_OrnamentLayer_Enhanced"),
    ("SDF/M_SDF_GothicArchitecture", "M_SDF_GothicArchitecture"),
    ("SDF/M_SDF_GothicArchitecture_Enhanced", "M_SDF_GothicArchitecture_Enhanced"),
    ("baroque/M_SDF_RoseWindow", "M_SDF_RoseWindow"),
    ("SDF/M_SDF_RayMarch_Gothic", "M_SDF_RayMarch_Gothic"),
    ("SDF/M_HybridStone_SDF", "M_HybridStone_SDF"),
    ("SDF/M_SDF_CathedralVault", "M_SDF_CathedralVault"),
    ("SDF/M_SDF_FlyingButtress", "M_SDF_FlyingButtress"),
    ("SDF/M_SDF_BaroqueColumn", "M_SDF_BaroqueColumn"),
    ("SDF/M_SDF_GildedAltar", "M_SDF_GildedAltar"),
    ("SDF/M_SDF_GothicRoseWindow", "M_SDF_GothicRoseWindow"),
    ("SDF/M_SDF_Grass_Field", "M_SDF_Grass_Field"),
]


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    for rel, stem in RESTORE_MAP:
        src = SRC_ROOT / rel.replace("/", "\\")
        src = src.with_suffix(".uasset") if src.suffix != ".uasset" else src
        if not src.name.endswith(".uasset"):
            src = Path(str(src) + ".uasset") if not str(src).endswith(".uasset") else src
        src = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / Path(rel).with_suffix(".uasset")
        dst = DST / f"{stem}.uasset"
        if src.exists():
            shutil.copy2(src, dst)
            restored.append(stem)
            print(f"Restored {stem}")
        else:
            print(f"Missing source: {src}")
    print(f"Restored {len(restored)} masters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
