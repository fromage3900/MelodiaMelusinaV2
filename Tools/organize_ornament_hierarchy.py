# -*- coding: utf-8 -*-
"""Organize ornament FBX into WIP + staging hierarchy (KitbashExport SSOT stays flat).

  python Tools/organize_ornament_hierarchy.py
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOTHIC_SSOT = ROOT / "KitbashExport" / "OrnamentalMeshes"
MUSICAL_SSOT = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
WIP = ROOT / "KitbashExport" / "OrnamentMusic_WIP"
STAGING = ROOT / "Products" / "_Staging" / "OrnamentSculptReview_20260712"
PROD_G = ROOT / "Products" / "OrnamentKitbash" / "FBX"
PROD_M = ROOT / "Products" / "MusicalOrnamentKitbash" / "FBX"
AUDIT = ROOT / "Saved" / "Audit" / "ornament_hierarchy_sync.json"

GOTHIC_P0 = ("SM_Orn_TorusKnot", "SM_Orn_FiligreeRing", "SM_Orn_CrownMolding")
GOTHIC_P1 = (
    "SM_Orn_RoseWindow_8Petal",
    "SM_Orn_VaultRibs",
    "SM_Orn_OculusFrame",
    "SM_Orn_SpiralStaircase",
)
GOTHIC_ALL = (
    "SM_Orn_ColumnCapital",
    "SM_Orn_CorbelBracket",
    "SM_Orn_CrownMolding",
    "SM_Orn_DoorArchway",
    "SM_Orn_FiligreeRing",
    "SM_Orn_GothicTracery",
    "SM_Orn_OculusFrame",
    "SM_Orn_PendantFinial",
    "SM_Orn_QuatrefoilArch",
    "SM_Orn_RoseWindow_8Petal",
    "SM_Orn_RosetteMedallion",
    "SM_Orn_SpiralStaircase",
    "SM_Orn_TorusKnot",
    "SM_Orn_VaultRibs",
    "SM_Orn_WovenRing",
)
GOTHIC_P2 = tuple(n for n in GOTHIC_ALL if n not in GOTHIC_P0 and n not in GOTHIC_P1)

MUSICAL_HAND = ("SM_Orn_TrebleClef", "SM_Orn_MusicalCorner")
MUSICAL_TOKENS = ("SM_Orn_MelodyToken_01", "SM_Orn_MelodyToken_02", "SM_Orn_MelodyToken_03")
MUSICAL_POLISH = (
    "SM_Orn_NoteHead",
    "SM_Orn_NoteBeam",
    "SM_Orn_SheetMusicRail",
    "SM_Orn_MusicalDivider",
    "SM_Orn_PearlJewel",
)


def _copy_named(names: tuple[str, ...], src: Path, dest: Path, copied: list, missing: list) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for stem in names:
        fbx = src / f"{stem}.fbx"
        if not fbx.is_file():
            missing.append(str(fbx))
            continue
        out = dest / f"{stem}.fbx"
        shutil.copy2(fbx, out)
        copied.append({"src": str(fbx), "dst": str(out), "bytes": out.stat().st_size})


def _mirror_flat(src: Path, dest: Path, copied: list) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for fbx in sorted(src.glob("SM_Orn_*.fbx")):
        out = dest / fbx.name
        shutil.copy2(fbx, out)
        copied.append({"src": str(fbx), "dst": str(out), "bytes": out.stat().st_size})
        n += 1
    return n


def _bucket_listing(root: Path) -> dict:
    out = {}
    if not root.is_dir():
        return out
    for fbx in sorted(root.rglob("SM_Orn_*.fbx")):
        rel = str(fbx.relative_to(root)).replace("\\", "/")
        out.setdefault(str(fbx.parent.relative_to(root)).replace("\\", "/"), []).append(
            {"name": fbx.name, "bytes": fbx.stat().st_size}
        )
    return out


def main() -> None:
    copied: list = []
    missing: list = []

    buckets = [
        (GOTHIC_P0, GOTHIC_SSOT, WIP / "Gothic" / "P0_Fix"),
        (GOTHIC_P1, GOTHIC_SSOT, WIP / "Gothic" / "P1_Heroes"),
        (GOTHIC_P2, GOTHIC_SSOT, WIP / "Gothic" / "P2_Detail"),
        (MUSICAL_HAND, MUSICAL_SSOT, WIP / "Musical" / "HandRemake"),
        (MUSICAL_TOKENS, MUSICAL_SSOT, WIP / "Musical" / "Tokens"),
        (MUSICAL_POLISH, MUSICAL_SSOT, WIP / "Musical" / "Polish"),
        (GOTHIC_P0, GOTHIC_SSOT, STAGING / "Gothic" / "P0_Fix"),
        (GOTHIC_P1, GOTHIC_SSOT, STAGING / "Gothic" / "P1_Heroes"),
        (GOTHIC_P2, GOTHIC_SSOT, STAGING / "Gothic" / "P2_Detail"),
        (MUSICAL_HAND, MUSICAL_SSOT, STAGING / "Musical" / "HandRemake"),
        (MUSICAL_TOKENS, MUSICAL_SSOT, STAGING / "Musical" / "Tokens"),
        (MUSICAL_POLISH, MUSICAL_SSOT, STAGING / "Musical" / "Polish"),
    ]
    for names, src, dest in buckets:
        _copy_named(names, src, dest, copied, missing)

    # Keep legacy flat Gothic/Musical mirrors for older tools
    _mirror_flat(GOTHIC_SSOT, STAGING / "Gothic", copied)
    _mirror_flat(MUSICAL_SSOT, STAGING / "Musical", copied)

    n_g = _mirror_flat(GOTHIC_SSOT, PROD_G, copied)
    n_m = _mirror_flat(MUSICAL_SSOT, PROD_M, copied)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(STAGING),
        "blend": str(STAGING / "OrnamentSculptReview.blend"),
        "gothic_count": n_g,
        "musical_count": n_m,
        "hierarchy": {
            "Gothic/P0_Fix": list(GOTHIC_P0),
            "Gothic/P1_Heroes": list(GOTHIC_P1),
            "Gothic/P2_Detail": list(GOTHIC_P2),
            "Musical/HandRemake": list(MUSICAL_HAND),
            "Musical/Tokens": list(MUSICAL_TOKENS),
            "Musical/Polish": list(MUSICAL_POLISH),
        },
        "wip_root": str(WIP),
        "note": "TrebleClef + MusicalCorner = HandRemake (do not auto-regen). KitbashExport SSOT stays flat.",
        "buckets": _bucket_listing(STAGING),
    }
    STAGING.mkdir(parents=True, exist_ok=True)
    (STAGING / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    audit = {
        "ok": True,
        "generated_at": manifest["generated_at"],
        "copied": len(copied),
        "missing": missing,
        "product_gothic": n_g,
        "product_musical": n_m,
        "ssot_gothic": len(list(GOTHIC_SSOT.glob("SM_Orn_*.fbx"))),
        "ssot_musical": len(list(MUSICAL_SSOT.glob("SM_Orn_*.fbx"))),
        "wip": str(WIP),
        "staging": str(STAGING),
        "hand_remake": list(MUSICAL_HAND),
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({"copied": len(copied), "missing": len(missing), "gothic": n_g, "musical": n_m}, indent=2))


if __name__ == "__main__":
    main()
