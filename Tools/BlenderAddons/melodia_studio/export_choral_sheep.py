#!/usr/bin/env python3
"""Export the Choral Sheep for UE5 import as a skeletal mesh.

P0 deliverable: the companion rig FBX that imports to
  /Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep

Run headless (after saving the .blend):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
      "C:/path/to/choral_sheep.blend" \
      --python "Tools/BlenderAddons/melodia_studio/export_choral_sheep.py" \
      -- --out "C:/EnvironmentPortfolio/BS_GodFile/Saved/Exports/ChoralSheep/SK_ChoralSheep.fbx"

Project FBX conventions (from melodia-creative-tools skill):
  - scale: Blender meters -> UE centimeters (scale object by 100, or global_scale=100)
  - rotation: axis_forward='-Z', axis_up='Y'  (UE5 coordinate system)
  - materials: material slots set BEFORE export (UE imports empty slots as indices)
  - skeletal: must export the armature + mesh together for a rigged mesh

Definition requirements (ChoralSheepDefinition.json):
  - skeletal_mesh_path: /Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep
  - follow_distance 180cm / acceptance 75cm / interaction radius 160cm
  - interactions: Graze, Harmonize, Guide
"""
import argparse
import os
import sys

import bpy


def log(msg: str) -> None:
    print(f"[choral-sheep-export] {msg}", flush=True)


def find_sheep_mesh() -> bpy.types.Object:
    """Locate the sheep body mesh by known name, else any Skin_* mesh."""
    for name in ("Skin_Sheep_ZSpheres2", "Skin_Sheep_25Spheres2", "sheep", "Sheep"):
        if name in bpy.data.objects and bpy.data.objects[name].type == "MESH":
            return bpy.data.objects[name]
    # prefer a character mesh (Skin_ prefix) over rig helper meshes
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("Skin_"):
            return o
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh object found in the scene")
    if len(meshes) == 1:
        return meshes[0]
    # prefer the largest mesh as the character
    def size(o):
        return o.dimensions.x * o.dimensions.y * o.dimensions.z
    return max(meshes, key=size)


def find_armature() -> bpy.types.Object | None:
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    return arms[0] if arms else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output .fbx path")
    ap.add_argument("--scale", type=float, default=100.0,
                    help="unit scale meters->cm (default 100)")
    ap.add_argument("--axis-forward", default="-Z")
    ap.add_argument("--axis-up", default="Y")
    ap.add_argument("--name", default="SK_ChoralSheep", help="object/asset name hint")
    args = ap.parse_args()

    out = args.out
    if not out.lower().endswith(".fbx"):
        out += ".fbx"
    os.makedirs(os.path.dirname(out), exist_ok=True)

    sheep = find_sheep_mesh()
    arm = find_armature()
    log(f"mesh: '{sheep.name}' ({sheep.type}, dims={sheep.dimensions[:]})")
    log(f"armature: {arm.name if arm else 'NONE'}")

    # Select mesh + armature for a skeletal export (set state directly; the
    # bpy.ops.object.select_all operator can fail in background/factory mode)
    for o in bpy.data.objects:
        o.select_set(False)
    sheep.select_set(True)
    objects_to_export = [sheep]
    if arm is not None:
        arm.select_set(True)
        objects_to_export.append(arm)
    # ensure an active object for the export operator
    if bpy.context.view_layer.objects.active is None or \
       bpy.context.view_layer.objects.active not in objects_to_export:
        bpy.context.view_layer.objects.active = sheep

    if not sheep.data.materials:
        log("WARNING: mesh has NO material slots — UE will import empty material indices. "
            "Add at least one material slot before export for clean import.")
    else:
        log(f"materials: {[m.name for m in sheep.data.materials if m]}")

    # Deform-only export: ship ONLY the deformation skeleton to UE.
    # The rig is ZSpheres/Rigify-style (474 bones = 106 deform + 368 controls).
    # UE retargeting needs a clean deform skeleton; control bones (c_* FK/IK)
    # are unusable there and bloat SK_ChoralSheep. use_armature_deform_only
    # is exactly this switch.
    bpy.ops.export_scene.fbx(
        filepath=out,
        use_selection=True,
        global_scale=args.scale,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward=args.axis_forward,
        axis_up=args.axis_up,
        use_custom_props=True,
        path_mode="AUTO",
        embed_textures=False,
        batch_mode="OFF",
        object_types={"ARMATURE", "MESH"} if arm is not None else {"MESH"},
        use_armature_deform_only=True,   # <-- clean skeleton for UE retarget
    )

    # --- verify the exported skeleton is deform-only ---
    if arm is not None:
        exported_bones = [b.name for b in arm.data.bones if b.use_deform]
        log(f"exported deform bones: {len(exported_bones)} "
            f"(total rig bones: {len(arm.data.bones)})")
        log(f"sample: {exported_bones[:10]}")

    log(f"exported -> {out}")
    log(f"size: {os.path.getsize(out)} bytes")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[choral-sheep-export] FATAL: {e}", flush=True)
        sys.exit(1)
