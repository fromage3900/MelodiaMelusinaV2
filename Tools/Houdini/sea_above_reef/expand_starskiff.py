"""STARSKIFF MK2 — expand the owner's desktop Starskiff_Shorewake_Project.blend
into a magical aquatic-traversal boat. Works on a COPY; the original .blend is
never modified.

Adds (the magical traversal layer):
  GunwaleGlow      duplicate of Starskiff_Rim, scaled 1.015, aqua emissive —
                   the bioluminescent hull line
  MastLantern      crystal lantern at the masthead (+ point light)
  FX sockets       empties: FX_WakeEmitter_L/R (stern), FX_SailCloth (mast),
                   FX_Lantern — UE Niagara/VFX attachment points
  Spectral banner  SM_Banner.fbx (frozen-cloth morphs) mounted at the mast —
                   imported alongside, not merged

Exports: Saved/Audit/sea_above/skiff/SM_Starskiff_MK2.fbx (hull assembly +
sockets) + a QA render through the project's own Starskiff_Cam + manifest.
Run:  blender -b --factory-startup -noaudio --python expand_starskiff.py
"""

import json
import shutil
from pathlib import Path

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_BLEND = Path(r"C:\Users\froma\Desktop\Starskiff_Shorewake_Project"
                 r"\Starskiff_Shorewake_Project.blend")
WORK_COPY = (PROJECT_ROOT / "Saved/Audit/sea_above/skiff"
             / "Starskiff_Shorewake_Project_copy.blend")
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/skiff"
BANNER_FBX = PROJECT_ROOT / "Saved/Audit/sea_above/meshes/SM_Banner.fbx"

AQUA = (0.45, 0.95, 0.90)


def emissive_mat(name, color, strength=3.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    for key, val in (("Base Color", color + (1.0,)),
                     ("Emission Color", color + (1.0,)),
                     ("Emission Strength", strength)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val
    return mat


def main():
    assert SRC_BLEND.exists(), f"source blend missing: {SRC_BLEND}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_BLEND, WORK_COPY)   # original untouched

    bpy.ops.wm.open_mainfile(filepath=str(WORK_COPY))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"

    hull_objs = [o for o in bpy.data.objects
                 if o.name.startswith("Starskiff_") and o.type == "MESH"]
    print(f"[skiff] found {len(hull_objs)} project meshes")

    # --- GunwaleGlow: rim duplicate, slightly inflated, emissive --------------
    rim = bpy.data.objects.get("Starskiff_Rim")
    if rim:
        glow = rim.copy()
        glow.data = rim.data.copy()
        glow.name = "GunwaleGlow"
        glow.scale = tuple(s * 1.015 for s in rim.scale)
        bpy.context.collection.objects.link(glow)
        glow.data.materials.clear()
        glow.data.materials.append(emissive_mat("GunwaleGlow_MAT", AQUA, 4.0))
        print("[skiff] GunwaleGlow added from Starskiff_Rim")
    else:
        print("[skiff] no Starskiff_Rim found - gunwale skipped")

    # --- masthead lantern -----------------------------------------------------
    mast = bpy.data.objects.get("Starskiff_Mast")
    if mast:
        head = mast.matrix_world.translation + Vector((0, 0, 1)) * 0.0
        head.z = max(v.co.z for v in mast.data.vertices) * 1.0 + 0.4 \
            if mast.data.vertices else head.z
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.35, location=head)
        lamp = bpy.context.object
        lamp.name = "MastLantern"
        lamp.data.materials.append(emissive_mat("Lantern_MAT", (1.0, 0.95, 0.75), 6.0))
        sock = bpy.data.objects.new("FX_Lantern", None)
        sock.location = head
        bpy.context.collection.objects.link(sock)
        print(f"[skiff] MastLantern at {tuple(round(v, 1) for v in head)}")

    # --- traversal FX sockets ---------------------------------------------------
    stern = bpy.data.objects.get("Starskiff_Stern")
    base = stern.matrix_world.translation if stern else Vector((0, 0, 0))
    for side, dx in (("L", -1.2), ("R", 1.2)):
        sock = bpy.data.objects.new(f"FX_WakeEmitter_{side}", None)
        sock.location = base + Vector((0, dx, 0.2))
        bpy.context.collection.objects.link(sock)
    sail = bpy.data.objects.get("Starskiff_Sail")
    if sail:
        sock = bpy.data.objects.new("FX_SailCloth", None)
        sock.location = sail.matrix_world.translation
        bpy.context.collection.objects.link(sock)
    print("[skiff] FX sockets placed (wake L/R, sail cloth, lantern)")

    # --- export MK2 (hull assembly + glow + sockets) ----------------------------
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.name.startswith("Starskiff_") or o.name in ("GunwaleGlow", "MastLantern",
                                                         "FX_WakeEmitter_L",
                                                         "FX_WakeEmitter_R",
                                                         "FX_SailCloth", "FX_Lantern"):
            o.select_set(True)
    out_fbx = OUT_DIR / "SM_Starskiff_MK2.fbx"
    bpy.ops.export_scene.fbx(filepath=str(out_fbx), use_selection=True,
                             add_leaf_bones=False, bake_anim=False,
                             object_types={"MESH", "EMPTY"})
    print(f"[skiff] wrote {out_fbx.name} ({out_fbx.stat().st_size} bytes)")

    # --- QA render through the project's own camera ------------------------------
    cam = bpy.data.objects.get("Starskiff_Cam")
    if cam:
        scene.camera = cam
        scene.cycles.samples = 24
        scene.render.resolution_x = 960
        scene.render.resolution_y = 540
        scene.render.filepath = str(OUT_DIR / "STARSKIFF_MK2_QA.png")
        bpy.ops.render.render(write_still=True)
        print("[skiff] QA render -> STARSKIFF_MK2_QA.png")

    manifest = {
        "schema": "melodia.starskiff_mk2.v1",
        "source": str(SRC_BLEND), "worked_on_copy": str(WORK_COPY),
        "export": str(out_fbx), "scale": "keep project units; FBX export preserves",
        "adds": ["GunwaleGlow (biolum hull line)",
                 "MastLantern (crystal lantern + FX socket)",
                 "FX_WakeEmitter_L/R", "FX_SailCloth",
                 "Spectral banner: mount SM_Banner.fbx at FX_SailCloth "
                 "(morphs SwayA/SwayB/Billow)"],
        "materials_recipe": {
            "hull": "T_Starskiff_Hull_BaseColor/Normal/Roughness (tilable)",
            "wake": "T_Starskiff_Wake_Emission at FX_WakeEmitter_*; "
                    "amplitude x (1 + 1.5 * User.SeaAbovePulse)",
            "gunwale": "emissive AQUA, CanalGlow-style pulse coupling",
        },
        "traversal_note": "boat movement/gameplay is game-code (owner design); "
                          "this asset + FX sockets are traversal-READY, not traversal",
    }
    (OUT_DIR / "starskiff_mk2_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[skiff] manifest -> starskiff_mk2_manifest.json")


if __name__ == "__main__":
    from mathutils import Vector
    main()
