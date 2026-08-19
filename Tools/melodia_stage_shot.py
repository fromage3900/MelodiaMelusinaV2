# -*- coding: utf-8 -*-
"""Melodia Stage one-command beauty / cine stills.

Run (preferred — open stage first so load is fast):
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki

Or let the script open the stage:
  blender --factory-startup -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject melusina

Subjects:
  melusina              Solo Melusina (default)
  outfit:<id>           Melusina body + Wardrobe_<id> (hair Water Advance protected)
  ornament:<id>         Import KitbashExport FBX (e.g. ornament:vault_ribs)
  prop:<name>           Show collection/object matching name (best-effort)

Writes PNG + asset passport under my-site-clean/generated/.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from melodia_website_root import resolve_website_root  # noqa: E402
from melodia_stage_paths import resolve_stage_blend  # noqa: E402

SITE = resolve_website_root(ROOT)
ASSETS = SITE / "generated" / "assets"
ORN_DIR = ROOT / "KitbashExport" / "OrnamentalMeshes"
MUSICAL_ORN_DIR = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"

STAGE_BLEND = resolve_stage_blend()

PRESET_CAM = {
    "beauty": "Cam_Beauty",
    "front": "Cam_Front",
    "macro": "Cam_Macro",
    "low": "Cam_Low",
    "silhouette": "Cam_Beauty",
    "three_quarter": "Cam_Beauty",
}

LIGHT_ALIASES = {
    "nikki": "Nikki",
    "jewelry": "Jewelry",
    "silhouette": "Silhouette",
}

ORNAMENT_FBX = {
    "vault_ribs": "SM_Orn_VaultRibs.fbx",
    "corbel": "SM_Orn_CorbelBracket.fbx",
    "crown_molding": "SM_Orn_CrownMolding.fbx",
    "torus_knot": "SM_Orn_TorusKnot.fbx",
    "rose_window": "SM_Orn_RoseWindow_8Petal.fbx",
    "filigree_ring": "SM_Orn_FiligreeRing.fbx",
    "rosette": "SM_Orn_RosetteMedallion.fbx",
    "spiral_stair": "SM_Orn_SpiralStaircase.fbx",
    "gothic_tracery": "SM_Orn_GothicTracery.fbx",
    "oculus_frame": "SM_Orn_OculusFrame.fbx",
    "quatrefoil": "SM_Orn_QuatrefoilArch.fbx",
    "door_archway": "SM_Orn_DoorArchway.fbx",
    "column_capital": "SM_Orn_ColumnCapital.fbx",
    "pendant_finial": "SM_Orn_PendantFinial.fbx",
    "woven_ring": "SM_Orn_WovenRing.fbx",
    # Musical sibling SKU
    "treble_clef": "SM_Orn_TrebleClef.fbx",
    "note_head": "SM_Orn_NoteHead.fbx",
    "note_beam": "SM_Orn_NoteBeam.fbx",
    "sheet_music_rail": "SM_Orn_SheetMusicRail.fbx",
    "musical_corner": "SM_Orn_MusicalCorner.fbx",
    "musical_divider": "SM_Orn_MusicalDivider.fbx",
    "pearl_jewel": "SM_Orn_PearlJewel.fbx",
}

MUSICAL_ORN_IDS = frozenset({
    "musical", "treble_clef", "note_head", "note_beam", "sheet_music_rail",
    "musical_corner", "musical_divider", "pearl_jewel",
})

LIGHT_RECIPES = {
    "Nikki": {
        "L_KeyWarm": (900, (1.0, 0.92, 0.85)),
        "L_RimPink": (550, (1.0, 0.55, 0.75)),
        "L_FillCool": (280, (0.7, 0.85, 1.0)),
        "L_GoldKick": (140, (1.0, 0.85, 0.45)),
    },
    "Jewelry": {
        "L_KeyWarm": (1100, (1.0, 0.95, 0.9)),
        "L_RimPink": (320, (0.9, 0.7, 1.0)),
        "L_FillCool": (180, (0.75, 0.9, 1.0)),
        "L_GoldKick": (420, (1.0, 0.88, 0.5)),
    },
    "Silhouette": {
        "L_KeyWarm": (40, (1.0, 0.9, 0.8)),
        "L_RimPink": (900, (1.0, 0.45, 0.7)),
        "L_FillCool": (60, (0.5, 0.6, 0.9)),
        "L_GoldKick": (20, (1.0, 0.8, 0.4)),
    },
}


def log(msg: str) -> None:
    print(f"[stage-shot] {msg}", flush=True)


def _argv_after_sep() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def ensure_stage() -> None:
    cur = Path(bpy.data.filepath or "")
    if cur.resolve() == STAGE_BLEND.resolve():
        log(f"already on stage {STAGE_BLEND.name}")
        return
    if STAGE_BLEND.is_file():
        log(f"opening {STAGE_BLEND}")
        bpy.ops.wm.open_mainfile(filepath=str(STAGE_BLEND))
    else:
        raise FileNotFoundError(f"Stage missing: {STAGE_BLEND}")


def setup_eevee() -> None:
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 2000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64


def apply_lights(preset_key: str) -> str:
    name = LIGHT_ALIASES.get(preset_key.lower(), preset_key)
    recipe = LIGHT_RECIPES.get(name)
    if not recipe:
        log(f"WARN unknown lights {preset_key} — leaving as-is")
        return name
    for light_name, (energy, color) in recipe.items():
        ob = bpy.data.objects.get(light_name)
        if ob and ob.type == "LIGHT":
            ob.data.energy = float(energy)
            ob.data.color = color
            ob.hide_render = False
            ob.hide_viewport = False
    for p in LIGHT_RECIPES:
        coll = bpy.data.collections.get(f"Lights_{p}")
        if coll:
            # Marker collections only — do not hide_viewport (locks Outliner).
            coll.hide_render = p != name
    # Actual studio lamps live in Lights (not Lights_Nikki).
    lights = bpy.data.collections.get("Lights")
    if lights:
        lights.hide_render = False
        lights.hide_viewport = False
    # Hide noisy prop lights
    for n in ("zenlantern_Light", "violin_Light", "violin_Sun"):
        lit = bpy.data.objects.get(n)
        if lit:
            lit.hide_render = True
    log(f"lights={name}")
    return name


def select_camera(preset: str) -> bpy.types.Object:
    cam_name = PRESET_CAM.get(preset, "Cam_Beauty")
    cam = bpy.data.objects.get(cam_name) or bpy.data.objects.get("Cam_Beauty")
    if cam is None:
        raise RuntimeError("Cam_Beauty missing on stage")
    bpy.context.scene.camera = cam
    log(f"camera={cam.name} preset={preset}")
    return cam


def set_collection_render(name: str, visible: bool) -> None:
    coll = bpy.data.collections.get(name)
    if coll:
        coll.hide_render = not visible
        # Do not touch hide_viewport — keeps Outliner toggles usable.


def _protect_water_advance_hair() -> None:
    """Never hide hair meshes that carry Water (Advance)."""
    mel = bpy.data.collections.get("Asset_melusina")
    if not mel:
        return
    # Avoid collection.all_objects — can AV on linked overrides (4.2 vs newer stage).
    for o in _mesh_objs_in_collection(mel):
        try:
            mats = [s.material.name if s.material else "" for s in o.material_slots]
            if "Water (Advance)" in mats or "hair" in o.name.lower() or "strand" in o.name.lower():
                o.hide_render = False
                o.hide_viewport = False
        except ReferenceError:
            continue


def _mesh_objs_in_collection(coll: bpy.types.Collection | None) -> list[bpy.types.Object]:
    if not coll:
        return []
    out: list[bpy.types.Object] = []
    seen: set[str] = set()
    for o in list(coll.objects):
        try:
            if o and o.type == "MESH" and o.name not in seen:
                out.append(o)
                seen.add(o.name)
        except ReferenceError:
            continue
    # Recurse children collections without all_objects
    for child in coll.children:
        for o in _mesh_objs_in_collection(child):
            if o.name not in seen:
                out.append(o)
                seen.add(o.name)
    return out


def isolate_melusina() -> list[bpy.types.Object]:
    # Solo Melusina — match STAGE_README defaults
    for name, on in (
        ("Asset_melusina", True),
        ("FX_Hero", True),
        ("Lights_Nikki", True),
        ("Set_Diorama", False),
        ("Melusina_WaterFX", False),
        ("Asset_sirmelodious", True),
        ("RenderSubject", False),
    ):
        set_collection_render(name, on)
    # Hide other Asset_* / Wardrobe_* collections (never Sir Melodious)
    for coll in bpy.data.collections:
        if coll.name.startswith("Asset_") and coll.name not in ("Asset_melusina", "Asset_sirmelodious"):
            coll.hide_render = True
            # viewport stay toggleable — never hide_viewport here
        if coll.name.startswith("Wardrobe_"):
            coll.hide_render = True
    _protect_water_advance_hair()
    objs = _mesh_objs_in_collection(bpy.data.collections.get("Asset_melusina"))
    if not objs:
        mel = bpy.data.objects.get("Melusina")
        if mel:
            objs = [mel]
    log(f"subject=melusina meshes={len(objs)}")
    return objs


def isolate_outfit(outfit_id: str) -> list[bpy.types.Object]:
    """Show Melusina body + Wardrobe_<id>; hide other wardrobe packs and FX optional."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in outfit_id)
    target = f"Wardrobe_{safe}"
    ward = bpy.data.collections.get(target)
    if ward is None:
        for c in bpy.data.collections:
            if c.name.lower() == target.lower():
                ward = c
                target = c.name
                break
    if ward is None:
        raise FileNotFoundError(f"Missing collection {target}")

    for name, on in (
        ("Asset_melusina", True),
        ("FX_Hero", False),
        ("Lights_Nikki", True),
        ("Set_Diorama", False),
        ("Melusina_WaterFX", False),
        ("Asset_sirmelodious", True),
        ("RenderSubject", False),
    ):
        set_collection_render(name, on)

    for coll in bpy.data.collections:
        if coll.name.startswith("Asset_") and coll.name not in ("Asset_melusina", "Asset_sirmelodious"):
            coll.hide_render = True
        if coll.name.startswith("Wardrobe_"):
            on = coll.name == target
            coll.hide_render = not on

    _protect_water_advance_hair()

    objs = _mesh_objs_in_collection(bpy.data.collections.get("Asset_melusina"))
    objs.extend(_mesh_objs_in_collection(ward))
    log(f"subject=outfit:{safe} wardrobe={target} meshes={len(objs)}")
    return objs


def ensure_coll(name: str) -> bpy.types.Collection:
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def clear_render_subject() -> None:
    coll = bpy.data.collections.get("RenderSubject")
    if not coll:
        return
    for o in list(coll.objects):
        mesh = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def import_ornament(orn_id: str) -> list[bpy.types.Object]:
    # Full musical review grid already on stage
    if orn_id == "musical":
        for name in ("Asset_melusina", "FX_Hero", "Set_Diorama", "Melusina_WaterFX"):
            set_collection_render(name, False)
        col = bpy.data.collections.get("MusicalOrnaments_Review")
        if col:
            col.hide_render = False
            col.hide_viewport = False
            meshes = _mesh_objs_in_collection(col)
            log(f"subject=ornament:musical review_grid meshes={len(meshes)}")
            return meshes
        # Fall through: import treble as hero stand-in
        orn_id = "treble_clef"

    fbx_name = ORNAMENT_FBX.get(orn_id, f"SM_Orn_{orn_id}.fbx")
    base = MUSICAL_ORN_DIR if orn_id in MUSICAL_ORN_IDS else ORN_DIR
    path = base / fbx_name
    if not path.is_file() and base is MUSICAL_ORN_DIR:
        path = ORN_DIR / fbx_name
    if not path.is_file():
        raise FileNotFoundError(f"Missing ornament FBX: {path}")
    # Hide character / diorama for plate
    for name in ("Asset_melusina", "FX_Hero", "Set_Diorama", "Melusina_WaterFX"):
        set_collection_render(name, False)
    clear_render_subject()
    subject = ensure_coll("RenderSubject")
    subject.hide_render = False
    subject.hide_viewport = False
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=str(path))
    meshes = [o for o in bpy.data.objects if o.name not in before and o.type == "MESH"]
    for o in meshes:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        subject.objects.link(o)
    log(f"subject=ornament:{orn_id} meshes={len(meshes)} ← {fbx_name}")
    return meshes


def aim_at(cam: bpy.types.Object, objs: list[bpy.types.Object], pad: float = 1.65) -> None:
    if not objs:
        return
    coords = []
    for o in objs:
        coords.extend(o.matrix_world @ Vector(c) for c in o.bound_box)
    mn = Vector((min(c.x for c in coords), min(c.y for c in coords), min(c.z for c in coords)))
    mx = Vector((max(c.x for c in coords), max(c.y for c in coords), max(c.z for c in coords)))
    mid = (mn + mx) * 0.5
    radius = max((mx - mn).length * 0.5, 0.25)
    dist = radius * pad * 2.2
    cam.location = Vector((mid.x + dist * 0.55, mid.y - dist, mid.z + dist * 0.35))
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    if cam.data:
        cam.data.lens = 50
    log(f"auto-aim mid={tuple(round(x, 2) for x in mid)} radius={radius:.2f}")


def resolve_out(subject: str, preset: str, out_arg: str | None) -> Path:
    if out_arg:
        return Path(out_arg)
    if subject.startswith("ornament:"):
        oid = subject.split(":", 1)[1]
        return ASSETS / "ornaments" / f"{oid}_stage_{preset}.png"
    if subject.startswith("prop:"):
        pid = subject.split(":", 1)[1]
        return ASSETS / "props" / f"{pid}_stage_{preset}.png"
    if subject.startswith("outfit:"):
        oid = subject.split(":", 1)[1]
        return ASSETS / "character" / f"melusina_outfit_{oid}_stage_{preset}.png"
    return ASSETS / "character" / f"melusina_stage_{preset}.png"


def emit_passport(subject: str, objs: list[bpy.types.Object], capture: str, out_path: Path) -> None:
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from melodia_asset_passport import passport_for_objects
    except ImportError:
        log(
            "passport skip: melodia_asset_passport module is missing (lost 2026-07-31, "
            "only .pyc + a known-bad reconstruction remain — see _TASK_QUEUE.md); "
            "continuing without passport output"
        )
        return
    except Exception as exc:
        log(f"passport skip: {exc}")
        return
    if subject.startswith("ornament:"):
        asset_id = subject.split(":", 1)[1]
        project = asset_id.replace("_", " ").title()
        category = "Prop / ornament"
    elif subject.startswith("prop:"):
        asset_id = subject.split(":", 1)[1]
        project = asset_id
        category = "Prop / props"
    elif subject.startswith("outfit:"):
        asset_id = subject.split(":", 1)[1]
        project = f"Melusina Outfit {asset_id}"
        category = "Character / Outfit"
    else:
        asset_id = "melusina"
        project = "Melusina"
        category = "Character / Water Hair"
    passport, paths = passport_for_objects(
        objs,
        asset_id=asset_id,
        project=project,
        category=category,
        version="stage-shot",
        shader="Melodia Portfolio Stage",
        capture=f"{capture} · {out_path.name}",
        software="Blender · Melodia Portfolio Stage v4",
        engine=bpy.context.scene.render.engine,
    )
    log(f"passport → {paths.get('json')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Melodia Stage one-command still")
    parser.add_argument("--preset", default="beauty", choices=sorted(PRESET_CAM.keys()))
    parser.add_argument("--lights", default="nikki", help="nikki|jewelry|silhouette")
    parser.add_argument(
        "--subject",
        default="melusina",
        help="melusina|outfit:<id>|ornament:<id>|prop:<name>",
    )
    parser.add_argument("--out", default=None, help="Output PNG path")
    parser.add_argument("--auto-aim", action="store_true", help="Reframe Cam at subject bounds")
    parser.add_argument("--no-passport", action="store_true")
    args = parser.parse_args(_argv_after_sep())

    ensure_stage()
    # Do not rewrite scene.render.engine / samples — use whatever is in the .blend
    apply_lights(args.lights)
    cam = select_camera(args.preset)

    subject = args.subject.strip().lower()
    if subject == "melusina":
        objs = isolate_melusina()
        auto_aim = args.auto_aim  # stage cams usually composed
    elif subject.startswith("outfit:"):
        oid = subject.split(":", 1)[1]
        objs = isolate_outfit(oid)
        auto_aim = args.auto_aim
    elif subject.startswith("ornament:"):
        oid = subject.split(":", 1)[1]
        objs = import_ornament(oid)
        auto_aim = True if not args.auto_aim else True
    elif subject.startswith("prop:"):
        name = subject.split(":", 1)[1]
        objs = [o for o in bpy.data.objects if name.lower() in o.name.lower() and o.type == "MESH"]
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.hide_render = o not in objs
        auto_aim = True
        log(f"subject=prop:{name} meshes={len(objs)}")
    else:
        log(f"FATAL unknown subject {subject}")
        return 2

    if auto_aim or subject.startswith("ornament:") or subject.startswith("prop:"):
        aim_at(cam, objs)

    out = resolve_out(subject, args.preset, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    if not out.is_file() or out.stat().st_size < 1000:
        log(f"FATAL empty render {out}")
        return 1
    log(f"wrote {out} ({out.stat().st_size} bytes)")

    if not args.no_passport:
        emit_passport(subject, objs, args.preset, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
