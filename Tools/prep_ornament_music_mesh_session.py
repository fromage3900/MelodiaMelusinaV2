# -*- coding: utf-8 -*-
"""Prep SurrealArch / Kitbash for ornament + musical mesh authoring session.

Ensures export folders, writes the authoring queue, and (when run inside Blender)
spawns a review grid with EXPORT quality + Prefer Melodia GN enabled.

Headless folder/queue only:
  python Tools/prep_ornament_music_mesh_session.py

Blender (preferred - opens stage + grid):
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" ^
    KitbashExport/Melodia_Portfolio_Stage_v4.blend ^
    -P Tools/prep_ornament_music_mesh_session.py

Factory bake queue (no stage):
  blender --factory-startup -b -P Tools/prep_ornament_music_mesh_session.py -- --grid
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
QUEUE_PATH = AUDIT / "ornament_music_authoring_queue.json"

ORN_DIR = ROOT / "KitbashExport" / "OrnamentalMeshes"
MUS_DIR = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
ORN_PRODUCT = ROOT / "Products" / "OrnamentKitbash" / "FBX"
MUS_PRODUCT = ROOT / "Products" / "MusicalOrnamentKitbash" / "FBX"
GN_LIB = ROOT / "deploy" / "surreal_arch" / "GN_Library"
WIP_DIR = ROOT / "KitbashExport" / "OrnamentMusic_WIP"

# Live kitbash SPECS (what UE / product bus already expects)
ORNAMENT_TARGETS = [
    ("SM_Orn_RoseWindow_8Petal", "ROSE_WINDOW", "gothic"),
    ("SM_Orn_RosetteMedallion", "ROSE_WINDOW", "gothic"),
    ("SM_Orn_GothicTracery", "FILIGREE_PANEL", "ornament"),
    ("SM_Orn_VaultRibs", "BAROQUE_VAULT", "gothic"),
    ("SM_Orn_DoorArchway", "GOTHIC_ARCH", "gothic"),
    ("SM_Orn_QuatrefoilArch", "TREFOIL", "gothic"),
    ("SM_Orn_OculusFrame", "CUSPED_ARCH", "gothic"),
    ("SM_Orn_FiligreeRing", "FILIGREE_PANEL", "ornament"),
    ("SM_Orn_WovenRing", "FILIGREE_PANEL", "ornament"),
    ("SM_Orn_CornerAcanthus", "FILIGREE_PANEL", "ornament"),
    ("SM_Orn_KeystoneHeraldic", "FILIGREE_PANEL", "ornament"),
    ("SM_Orn_FinialSpire", "GOTHIC_FINIAL", "gothic"),
    ("SM_Orn_BalustradeSegment", "BALUSTRADE", "gothic"),
    ("SM_Orn_CorniceBracket", "CORBEL", "gothic"),
    ("SM_Orn_CeilingMedallion", "ROSE_WINDOW", "gothic"),
]

MUSICAL_TARGETS = [
    ("SM_Orn_TrebleClef", "TREBLE_CLEF", "music"),
    ("SM_Orn_NoteHead", "NOTE_HEAD", "music"),
    ("SM_Orn_NoteBeam", "NOTE_HEAD", "music"),
    ("SM_Orn_SheetMusicRail", "SHEET_MUSIC_RAIL", "music"),
    ("SM_Orn_MusicalCorner", "FILIGREE_PANEL", "music"),
    ("SM_Orn_MusicalDivider", None, "music"),  # bpy fallback in regen
    ("SM_Orn_PearlJewel", None, "music"),
]

# Melodia GN natives (new lane - bake alongside if authoring GN ornaments)
MELODIA_GN_TARGETS = [
    ("SM_Orn_GN_Vine", "ORN_VINE", "melodia_gn"),
    ("SM_Orn_GN_Radial", "ORN_RADIAL", "melodia_gn"),
    ("SM_Orn_GN_Frame", "ORN_FRAME", "melodia_gn"),
    ("SM_Orn_GN_Panel", "ORN_PANEL", "melodia_gn"),
    ("SM_Orn_GN_Grid", "ORN_GRID", "melodia_gn"),
    ("SM_Orn_GN_NoteHead", "MELODIA_NOTE_HEAD", "melodia_gn"),
    ("SM_Orn_GN_TrebleClef", "MELODIA_TREBLE_CLEF", "melodia_gn"),
    ("SM_Orn_GN_Staff", "MELODIA_STAFF", "melodia_gn"),
    ("SM_Orn_GN_Harmonic", "MELODIA_HARMONIC", "melodia_gn"),
    ("SM_Orn_GN_Phrase", "MELODIA_PHRASE", "melodia_gn"),
]


def _fbx_status(name: str, lane: str) -> dict:
    if lane == "music" or name.startswith("SM_Orn_Treble") or name in {t[0] for t in MUSICAL_TARGETS}:
        base = MUS_DIR
        product = MUS_PRODUCT
    elif lane == "melodia_gn":
        base = WIP_DIR
        product = WIP_DIR
    else:
        base = ORN_DIR
        product = ORN_PRODUCT
    fbx = base / f"{name}.fbx"
    prod = product / f"{name}.fbx"
    return {
        "fbx": str(fbx),
        "exists": fbx.is_file(),
        "product_exists": prod.is_file(),
        "bytes": fbx.stat().st_size if fbx.is_file() else 0,
    }


def ensure_folders() -> list[str]:
    created = []
    for d in (ORN_DIR, MUS_DIR, ORN_PRODUCT, MUS_PRODUCT, GN_LIB, WIP_DIR, AUDIT):
        if not d.is_dir():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    return created


def build_queue() -> dict:
    items = []
    for name, arch, lane in ORNAMENT_TARGETS + MUSICAL_TARGETS + MELODIA_GN_TARGETS:
        st = _fbx_status(name, lane if lane != "ornament" else "gothic")
        if lane == "music":
            st = _fbx_status(name, "music")
        items.append({
            "asset": name,
            "arch_type": arch,
            "lane": lane,
            **st,
            "status": "ready" if st["exists"] else "missing",
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "quality": "EXPORT",
        "prefer_melodia_gn": True,
        "stage": str(ROOT / "KitbashExport" / "Melodia_Portfolio_Stage_v4.blend"),
        "folders": {
            "ornament_fbx": str(ORN_DIR),
            "musical_fbx": str(MUS_DIR),
            "wip_gn": str(WIP_DIR),
            "gn_library": str(GN_LIB),
        },
        "regen": {
            "ornament": "Tools/regenerate_ornaments_surreal_arch.py",
            "musical": "Tools/regenerate_musical_ornaments_surreal_arch.py",
        },
        "counts": {
            "ornament": len(ORNAMENT_TARGETS),
            "musical": len(MUSICAL_TARGETS),
            "melodia_gn": len(MELODIA_GN_TARGETS),
            "fbx_present": sum(1 for i in items if i["exists"]),
            "fbx_missing": sum(1 for i in items if not i["exists"]),
        },
        "items": items,
    }


def write_queue(queue: dict) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    return QUEUE_PATH


def _want_grid() -> bool:
    argv = sys.argv
    if "--" in argv:
        return "--grid" in argv[argv.index("--") + 1 :]
    return "--grid" in argv


def setup_blender_session(spawn_grid: bool = True) -> dict:
    import bpy

    deploy = str(ROOT / "deploy")
    if deploy not in sys.path:
        sys.path.insert(0, deploy)

    report = {"ok": False, "spawned": [], "errors": []}

    try:
        import surreal_architecture_gen as monolith

        monolith.register()
    except Exception as exc:
        report["errors"].append(f"register: {exc}")
        # Continue - props may already exist in stage blend

    try:
        from surreal_arch.quality_props import register_quality_props

        register_quality_props()
        q = bpy.context.scene.surreal_arch_quality
        q.export_quality = "EXPORT"
        q.prefer_melodia_gn = True
        report["quality"] = "EXPORT"
        report["prefer_melodia_gn"] = True
    except Exception as exc:
        report["errors"].append(f"quality_props: {exc}")

    # Bake Melodia GN library into memory (and optionally disk)
    try:
        from surreal_arch.melodia_gn.bake import bake_all

        lib = bake_all(overwrite=True)
        report["gn_library"] = lib
    except Exception as exc:
        report["errors"].append(f"melodia_gn bake: {exc}")

    if not spawn_grid:
        report["ok"] = len(report["errors"]) == 0
        return report

    # Clear WIP collection
    col_name = "OrnamentMusic_Authoring"
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    # Spawn musical + Melodia GN first (priority for this session), then key ornaments
    spawn_list = (
        [(n, a, l) for n, a, l in MUSICAL_TARGETS if a]
        + [(n, a, l) for n, a, l in MELODIA_GN_TARGETS]
        + [(n, a, l) for n, a, l in ORNAMENT_TARGETS if l == "ornament"]
    )

    cols = 6
    spacing = 3.5
    apply_fn = None
    try:
        import surreal_architecture_gen as monolith

        apply_fn = getattr(monolith, "apply_geometry_nodes_to_object", None)
    except Exception:
        pass

    for i, (name, arch, lane) in enumerate(spawn_list):
        x = (i % cols) * spacing
        y = -(i // cols) * spacing
        mesh = bpy.data.meshes.new(f"{name}_mesh")
        obj = bpy.data.objects.new(name, mesh)
        col.objects.link(obj)
        obj.location = (x, y, 0.0)
        if not hasattr(obj, "surreal_arch_props"):
            report["errors"].append(f"{name}: no surreal_arch_props")
            continue
        props = obj.surreal_arch_props
        try:
            props.arch_type = arch
        except TypeError:
            # Melodia GN natives may not be in enum - set via IDProperties fallback skip
            report["errors"].append(f"{name}: enum rejected {arch}")
            continue
        if hasattr(props, "export_quality"):
            try:
                props.export_quality = "EXPORT"
            except Exception:
                pass
        if apply_fn:
            try:
                apply_fn(obj, props, monolith=monolith)
                report["spawned"].append({"name": name, "arch": arch, "lane": lane})
            except Exception as exc:
                report["errors"].append(f"generate {name}: {exc}")
        else:
            report["spawned"].append({"name": name, "arch": arch, "lane": lane, "generated": False})

    report["ok"] = len(report["spawned"]) > 0
    report["collection"] = col_name
    print(f"[prep] spawned {len(report['spawned'])} authoring targets in {col_name}", flush=True)
    return report


def main() -> int:
    created = ensure_folders()
    queue = build_queue()
    path = write_queue(queue)
    print(f"[prep] folders created: {len(created)}", flush=True)
    print(f"[prep] queue -> {path}", flush=True)
    print(
        f"[prep] ornament={queue['counts']['ornament']} "
        f"musical={queue['counts']['musical']} "
        f"gn={queue['counts']['melodia_gn']} "
        f"fbx_ok={queue['counts']['fbx_present']} "
        f"missing={queue['counts']['fbx_missing']}",
        flush=True,
    )

    in_blender = "bpy" in sys.modules or any("blender" in (a or "").lower() for a in sys.argv[:1])
    try:
        import bpy  # noqa: F401

        in_blender = True
    except ImportError:
        in_blender = False

    if in_blender:
        report = setup_blender_session(spawn_grid=_want_grid() or True)
        (AUDIT / "ornament_music_prep_session.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(f"[prep] blender session ok={report.get('ok')} spawned={len(report.get('spawned', []))}", flush=True)
        if report.get("errors"):
            for e in report["errors"][:8]:
                print(f"[prep] WARN: {e}", flush=True)
        return 0 if report.get("ok") else 1

    print("[prep] folders+queue ready. Open Blender with this script to spawn the authoring grid.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
