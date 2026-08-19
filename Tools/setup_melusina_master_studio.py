"""
Melusina master studio pass — Fade Sky + Komikaze set + Melusina-framed cameras.

STOP / consent:
  Do not run on live Melodia_Portfolio_Stage_*.blend without artist consent.
  Honors Saved/Audit/MELUSINA_SHADER_AGENT_STOP (read-only abort).
  Never bpy.ops.wm.save_mainfile on stage blends.
  Collection isolate uses hide_render only (soft Outliner eyes stay usable).

Runs in open Blender 5.1 on Melodia_Portfolio_Stage_v4.blend (MCP or Text Editor).

- Fade Assets sky world (Gradient Spherical → magical-night tint)
- Studio cyclorama + Komikaze NPR on Studio_FloorCard / Backdrop / Set_Diorama only (Lane B)
- Cameras recomposed to live Melusina head/hips (not scaffold placeholder)
- Hides broken FV2 star-skirt from beauty; restores Melusina_Skirt
- Does not full-replace Melusina character materials (Lane A hybrids stay —
  Water Advance hair + SHAWL-style PBR/Komikaze mixes are authored on the character)
- Never move Studio_FloorCard (boot contact pin)

Usage:
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\setup_melusina_master_studio.py").read())
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
STOP = ROOT / "Saved" / "Audit" / "MELUSINA_SHADER_AGENT_STOP"
AUDIT = ROOT / "Saved" / "Audit" / "melusina_master_studio.json"
FADE_DATA = Path(
    r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.1"
    r"\extensions\user_default\fadeassets\data\data.blend"
)
FADE_SKY = "Sky Night"  # Melodia magical-night; alt: "Gradient Spherical"
WORLD_NAME = "W_MelodiaStudio_Fade"

# Portrait plate
RES_X, RES_Y = 1600, 2000

# Melodia-tinted night (multiplied into Fade sky BG if editable)
TINT_HORIZON = (0.55, 0.35, 0.62, 1.0)
TINT_ZENITH = (0.08, 0.06, 0.18, 1.0)


def log(msg: str) -> None:
    print(f"[master-studio] {msg}", flush=True)


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_obj(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def aim_camera(cam: bpy.types.Object, target: Vector) -> None:
    direction = target - cam.matrix_world.translation
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def melusina_anchors() -> dict[str, Vector]:
    """Head / chest / feet from live rig; fall back to mesh bounds."""
    head = chest = feet = None
    rig = bpy.data.objects.get("character_rig") or bpy.data.objects.get("FinalUERig43")
    if rig and rig.type == "ARMATURE":
        for bn in ("head.x", "head", "Head"):
            if bn in rig.pose.bones:
                head = rig.matrix_world @ rig.pose.bones[bn].head
                break
        for bn in ("spine_02.x", "spine_01.x", "spine_03.x", "hips", "root.x"):
            if bn in rig.pose.bones:
                chest = rig.matrix_world @ rig.pose.bones[bn].head
                break
        for bn in ("foot.l", "foot.r", "toe.l"):
            if bn in rig.pose.bones:
                feet = rig.matrix_world @ rig.pose.bones[bn].head
                break

    if head is None or chest is None:
        pts: list[Vector] = []
        deps = bpy.context.evaluated_depsgraph_get()
        for o in bpy.data.objects:
            if o.type != "MESH":
                continue
            if any("melusina" in c.name.lower() for c in o.users_collection):
                if "hair" in o.name.lower() or o.name.startswith("cs_"):
                    continue
                ev = o.evaluated_get(deps)
                for c in ev.bound_box:
                    pts.append(o.matrix_world @ Vector(c))
        if pts:
            zs = [p.z for p in pts]
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            zmin, zmax = min(zs), max(zs)
            head = Vector((cx, cy, zmax * 0.92))
            chest = Vector((cx, cy, zmin + (zmax - zmin) * 0.55))
            feet = Vector((cx, cy, zmin))

    head = head or Vector((0, -0.16, 1.44))
    chest = chest or Vector((0, -0.18, 1.10))
    feet = feet or Vector((0, -0.20, 0.05))
    # Beauty aim: upper chest / lower face — classic ¾ portrait
    beauty = Vector((chest.x, chest.y, (chest.z + head.z) * 0.5))
    return {"head": head, "chest": chest, "feet": feet, "beauty": beauty}


def setup_fade_sky() -> str:
    """Append Fade Assets sky world and assign to scene."""
    if not FADE_DATA.is_file():
        raise FileNotFoundError(f"Fade Assets data missing: {FADE_DATA}")

    # Prefer Melodia night spherical gradient
    sky_name = FADE_SKY
    existing = bpy.data.worlds.get(WORLD_NAME) or bpy.data.worlds.get(sky_name)
    if existing is None:
        before = {w.name for w in bpy.data.worlds}
        with bpy.data.libraries.load(str(FADE_DATA), link=False) as (data_from, data_to):
            if sky_name not in data_from.worlds:
                raise RuntimeError(f"Fade sky '{sky_name}' not in library: {list(data_from.worlds)}")
            data_to.worlds = [sky_name]
        added = [w for w in bpy.data.worlds if w.name not in before]
        world = added[0] if added else bpy.data.worlds.get(sky_name)
        if world is None:
            raise RuntimeError("Failed to append Fade sky world")
        world.name = WORLD_NAME
    else:
        world = existing
        if world.name != WORLD_NAME:
            world.name = WORLD_NAME

    bpy.context.scene.world = world
    world.use_nodes = True

    # Soft Melodia tint on Background nodes when present
    nt = world.node_tree
    if nt:
        bgs = [n for n in nt.nodes if n.type == "BACKGROUND"]
        if len(bgs) >= 2:
            bgs[0].inputs[0].default_value = TINT_ZENITH
            bgs[1].inputs[0].default_value = TINT_HORIZON
        elif len(bgs) == 1:
            bgs[0].inputs[0].default_value = TINT_HORIZON
            if bgs[0].inputs[1].default_value < 0.35:
                bgs[0].inputs[1].default_value = 0.55

    # Mist for depth (Fade-friendly)
    if hasattr(world, "mist_settings"):
        world.mist_settings.use_mist = True
        world.mist_settings.start = 4.0
        world.mist_settings.depth = 18.0
        world.mist_settings.falloff = "QUADRATIC"

    log(f"Fade sky active: {world.name}")
    return world.name


def _komikaze_append(material_name: str):
    tools = ROOT / "Tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import komikaze_stage_looks as klooks  # noqa: WPS433

    return klooks.komikaze_append(material_name)


def setup_studio_set() -> dict:
    """Cyclorama + Komikaze ground/backdrop; diorama foliage look."""
    studio = ensure_collection("Studio")
    report: dict = {"ground": None, "backdrop": None, "komikaze": {}}

    # Ground
    ground = bpy.data.objects.get("Ground")
    if ground is None:
        bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0, 0, 0))
        ground = bpy.context.active_object
        ground.name = "Ground"
    link_obj(ground, studio)
    ground.scale = (1.4, 1.4, 1.0)
    gmat = _komikaze_append("Gradient (Linear)") or _komikaze_append("Cel Shade 3 Tones (Soft)")
    if gmat:
        ground.data.materials.clear()
        ground.data.materials.append(gmat)
        report["komikaze"]["Ground"] = gmat.name
    if hasattr(ground, "is_shadow_catcher"):
        ground.is_shadow_catcher = False
    report["ground"] = ground.name

    # Cyclorama backdrop behind Melusina
    backdrop = bpy.data.objects.get("Studio_Backdrop")
    if backdrop is None:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 3.2, 1.6))
        backdrop = bpy.context.active_object
        backdrop.name = "Studio_Backdrop"
        backdrop.scale = (7.0, 4.2, 1.0)
        backdrop.rotation_euler = (math.radians(90), 0, 0)
    link_obj(backdrop, studio)
    bmat = _komikaze_append("Gradient (Radial)") or _komikaze_append("Gradient (Freeform)")
    if bmat:
        backdrop.data.materials.clear()
        backdrop.data.materials.append(bmat)
        report["komikaze"]["Studio_Backdrop"] = bmat.name
    # Sky Night fills the frame — keep card available but off for master beauty
    backdrop.hide_viewport = True
    backdrop.hide_render = True
    report["backdrop"] = backdrop.name
    report["backdrop_hidden"] = True

    # Soft floor card (optional second ring)
    ring = bpy.data.objects.get("Studio_FloorCard")
    if ring is None:
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=2.4, fill_type="NGON", location=(0, 0, 0.002))
        ring = bpy.context.active_object
        ring.name = "Studio_FloorCard"
    link_obj(ring, studio)
    rmat = _komikaze_append("Cel Shade 2 Tones (Soft)")
    if rmat:
        ring.data.materials.clear()
        ring.data.materials.append(rmat)
        report["komikaze"]["Studio_FloorCard"] = rmat.name

    # Diorama NPR (safe — never Melusina)
    try:
        import komikaze_stage_looks as klooks

        looks = klooks.setup_stage_looks()
        n = klooks.apply_look_to_collection("Set_Diorama", "foliage")
        report["komikaze"]["Set_Diorama"] = {"looks": looks, "meshes": n}
    except Exception as exc:  # noqa: BLE001
        report["komikaze"]["Set_Diorama_error"] = str(exc)

    # Keep diorama off for beauty by default
    diorama = bpy.data.collections.get("Set_Diorama")
    if diorama:
        diorama.hide_render = True
        diorama.hide_viewport = True

    return report


def reframes_cameras(anchors: dict[str, Vector]) -> dict:
    """Recompose stage cameras to live Melusina."""
    beauty_t = anchors["beauty"]
    head_t = anchors["head"]
    chest_t = anchors["chest"]

    # Positions tuned for ~2.3m character, portrait 4:5
    # Full-figure beauty: hat headroom + boots; eyes near upper third of body mass
    beauty_look = Vector((beauty_t.x, beauty_t.y, chest_t.z - 0.02))
    specs = {
        "Cam_Beauty": {
            "loc": Vector((3.05, -4.45, 1.55)),
            "lens": 50.0,
            "look": beauty_look,
            "dof_dist": (Vector((3.05, -4.45, 1.55)) - beauty_look).length,
        },
        "Cam_Front": {
            "loc": Vector((0.0, -4.80, 1.35)),
            "lens": 55.0,
            "look": Vector((chest_t.x, chest_t.y, chest_t.z)),
            "dof_dist": None,
        },
        "Cam_Macro": {
            "loc": Vector((0.85, -1.70, 1.46)),
            "lens": 90.0,
            "look": head_t,
            "dof_dist": (Vector((0.85, -1.70, 1.46)) - head_t).length,
        },
        "Cam_Low": {
            "loc": Vector((2.55, -3.55, 0.40)),
            "lens": 42.0,
            "look": Vector((chest_t.x, chest_t.y, head_t.z - 0.15)),
            "dof_dist": None,
        },
        "Cam_Turntable": {
            "loc": Vector((3.60, -4.60, 1.60)),
            "lens": 52.0,
            "look": beauty_look,
            "dof_dist": None,
        },
    }

    cams_c = ensure_collection("Cameras")
    out = {}
    for name, spec in specs.items():
        cam = bpy.data.objects.get(name)
        if cam is None or cam.type != "CAMERA":
            data = bpy.data.cameras.new(name)
            cam = bpy.data.objects.new(name, data)
            cams_c.objects.link(cam)
        cam.location = spec["loc"]
        cam.data.lens = spec["lens"]
        cam.data.clip_start = 0.05
        cam.data.clip_end = 200.0
        cam.data.sensor_width = 36.0
        aim_camera(cam, spec["look"])
        # Gentle DOF on beauty + macro
        if spec.get("dof_dist") and hasattr(cam.data, "dof"):
            cam.data.dof.use_dof = True
            cam.data.dof.focus_distance = float(spec["dof_dist"])
            cam.data.dof.aperture_fstop = 2.8 if name == "Cam_Macro" else 3.5
        else:
            if hasattr(cam.data, "dof"):
                cam.data.dof.use_dof = False
        out[name] = {
            "loc": [round(x, 3) for x in cam.location],
            "lens": cam.data.lens,
            "look": [round(x, 3) for x in spec["look"]],
        }
        log(f"{name} → loc={out[name]['loc']} lens={cam.data.lens}")

    beauty = bpy.data.objects.get("Cam_Beauty")
    if beauty:
        bpy.context.scene.camera = beauty
    return out


def tune_lights() -> dict:
    """Nikki beauty balance — key dominates, pink rim reads on hair."""
    energies = {
        "L_KeyWarm": (620.0, (1.0, 0.93, 0.84)),
        "L_RimPink": (380.0, (1.0, 0.45, 0.72)),
        "L_FillCool": (180.0, (0.45, 0.82, 1.0)),
        "L_GoldKick": (90.0, (1.0, 0.88, 0.45)),
    }
    # Reposition relative to Melusina
    places = {
        "L_KeyWarm": Vector((2.6, -2.4, 3.4)),
        "L_RimPink": Vector((-2.4, 1.6, 2.8)),
        "L_FillCool": Vector((0.4, 2.8, 2.2)),
        "L_GoldKick": Vector((1.0, -0.8, 4.5)),
    }
    report = {}
    for name, (energy, color) in energies.items():
        lit = bpy.data.objects.get(name)
        if not lit or lit.type != "LIGHT":
            continue
        lit.hide_render = False
        lit.hide_viewport = False
        lit.data.energy = energy
        lit.data.color = color
        if name in places:
            lit.location = places[name]
        if lit.data.type == "AREA":
            lit.data.size = 1.8 if name == "L_KeyWarm" else 1.2
        report[name] = {"energy": energy, "loc": [round(x, 2) for x in lit.location]}

    # Hide asset junk lights
    for name in ("zenlantern_Light", "violin_Light", "violin_Sun"):
        o = bpy.data.objects.get(name)
        if o:
            o.hide_render = True
            o.hide_viewport = True

    nikki = bpy.data.collections.get("Lights_Nikki")
    if nikki:
        nikki.hide_render = False
        nikki.hide_viewport = False
    for off in ("Lights_Jewelry", "Lights_Silhouette"):
        c = bpy.data.collections.get(off)
        if c:
            c.hide_render = True
            c.hide_viewport = False  # soft: render-only quiet
    return report


def cleanup_beauty_subjects() -> dict:
    """Hide foam/FX/FV2 clutter only — never hide outfit Retopo clothing layers."""
    report = {"hidden": [], "shown": []}

    # Real clutter / FX only. Do NOT hide Retopo_Plane* (skirtpanel/shawl/frontpanel/gloves)
    # or Retopo_Cube* bows / Retopo_starfrill — those are Melusina outfit meshes.
    hide_exact = (
        "fluid_surface",
        "FX_KawaiiSparkles",
        "Kawaii_Sparkle Effect",
        "Kawaii_Sparkle Effect.001",
        "Star",
        "cross_Instance Star.001",
        "FF_MelusinaHair_Domain",
        "FF_MelusinaHair_Drip",
        "FF_MelusinaHair_Sheet",
        "cs_skirt_master",
    )
    for name in hide_exact:
        o = bpy.data.objects.get(name)
        if o:
            o.hide_set(True)
            o.hide_viewport = True
            o.hide_render = True
            report["hidden"].append(name)

    for o in bpy.data.objects:
        n = o.name.lower()
        if "fv2" in n or "accordion" in n:
            o.hide_set(True)
            o.hide_viewport = True
            o.hide_render = True
            report["hidden"].append(o.name)
        if any(c.name == "character1_cs" for c in o.users_collection):
            o.hide_viewport = True
            o.hide_render = True

    # Ensure outfit + body layers are visible
    clothing = (
        "Melusina",
        "Melusina_Sleeve",
        "Melusina_Skirt",
        "Melusina_SkirtPanel",
        "Melusina_Shawl",
        "Melusina_FrontPanel",
        "Melusina_Gloves",
        "Melusina_Bow",
        "Melusina_Bow.001",
        # legacy aliases (pre-2026-07-13 rename)
        "Melusina.002",
        "simply_coll",
        "Retopo_Plane.002",
        "Retopo_Plane.003",
        "Retopo_Plane.006",
        "Retopo_Plane005.002",
        "Retopo_Cube_003.001",
        "Retopo_Cube_003.003",
        "Retopo_starfrill",
        "Retopo_Melusina_006.001",
        "NurbsCurve_profile.001",
        "Retopo_boot 2.001",
        "Retopo_boot 2.002",
        "Retopo_tophat!.001",
    )
    for name in clothing:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        o.hide_set(False)
        o.hide_render = False
        o.hide_viewport = False
        report["shown"].append(name)

    for cname, on in (
        ("Asset_melusina", True),
        ("FX_Hero", True),
        ("Lights_Nikki", True),
        ("Studio", True),
        ("Cameras", True),
        ("Melusina_WaterFX", False),
        ("Melusina_WaterHair_Ref", False),
        ("Set_Diorama", False),
        ("Asset_sirmelodious", True),
        ("Surreal_Regen_Starlight", False),
        ("MusicalOrnaments_Review", False),
        ("Review_Queue", False),
        ("Asset_melusina_elixir", False),
    ):
        c = bpy.data.collections.get(cname)
        if c:
            # Render isolate only — never Collection.hide_viewport (hard Outliner lock)
            c.hide_render = not on
            c.hide_viewport = False

    for c in bpy.data.collections:
        if c.name.startswith("Wardrobe_"):
            c.hide_render = True
            c.hide_viewport = False
            report["hidden"].append(c.name)

    # Quiet FX meshes for clean beauty (opt-in later) — render only
    for name in ("FX_SheerVeil", "FX_RibbonJiggle", "FX_SanctusJewelryHero"):
        o = bpy.data.objects.get(name)
        if o:
            o.hide_render = True

    return report


def setup_render() -> dict:
    scene = bpy.context.scene
    engines = {e.identifier for e in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    if hasattr(scene, "eevee"):
        ee = scene.eevee
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = 64
        if hasattr(ee, "use_bloom"):
            ee.use_bloom = True
        if hasattr(ee, "bloom_intensity"):
            ee.bloom_intensity = 0.05
    return {
        "engine": scene.render.engine,
        "res": [RES_X, RES_Y],
        "camera": scene.camera.name if scene.camera else None,
    }


def main() -> dict:
    if STOP.is_file():
        msg = (
            f"ABORT: {STOP} present — do not mutate Melusina/stage lookdev. "
            "Artist consent + remove stop flag required."
        )
        log(msg)
        return {"ok": False, "error": "MELUSINA_SHADER_AGENT_STOP"}
    anchors = melusina_anchors()
    world = setup_fade_sky()
    set_report = setup_studio_set()
    cams = reframes_cameras(anchors)
    lights = tune_lights()
    cleanup = cleanup_beauty_subjects()
    render = setup_render()

    # Note empty for cockpit
    note = bpy.data.objects.get("NOTE_MasterStudio")
    if note is None:
        note = bpy.data.objects.new("NOTE_MasterStudio", None)
        fx = ensure_collection("FX_Hero")
        fx.objects.link(note)
    note.empty_display_type = "PLAIN_AXES"
    note.empty_display_size = 0.05
    note.location = (0, -0.5, 2.6)
    note["melodia_note"] = (
        f"Master studio: Fade sky={world}; Komikaze on Ground/Backdrop; "
        "cameras framed to Melusina; FV2 hidden until materials fixed."
    )

    result = {
        "world": world,
        "anchors": {k: [round(v.x, 3), round(v.y, 3), round(v.z, 3)] for k, v in anchors.items()},
        "cameras": cams,
        "lights": lights,
        "set": set_report,
        "cleanup": cleanup,
        "render": render,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
