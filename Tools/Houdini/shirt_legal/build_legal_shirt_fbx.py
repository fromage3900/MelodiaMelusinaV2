"""Route (a): make the 481-bone shirt candidate LEGAL against the shared skeleton.

Input : G: .../MelusinaShirtKawaii_20261003/shirt_skinfit_candidate.fbx  (481 joints
        = 464 canonical body bones + 17 hem bones; 861 verts; 234 leg-bound verts)
Apply : the Oct-6 Houdini weight fix (shirt_weight_fix_v1.json) — leg-chain ->
        strongest torso, top-4, renormalised, hem weights preserved. Index
        alignment with the candidate is proven (533 identical, hem set identical).
Output: Saved/Audit/ShirtBones_20261020/SK_Melusina_V2_Shirt_HemRig_Legal.fbx

Nothing here touches Content/, the live skeleton, or the editor. Read-only
inputs, staging-only output. Export settings are copied verbatim from the
original builder (build_shirt_skinfit_candidate.py) so the coordinate
convention round-trips unchanged.

  "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b --python build_legal_shirt_fbx.py
"""
import json
import os

import bpy
from mathutils import Matrix

FBX = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\MelusinaShirtKawaii_20261003\shirt_skinfit_candidate.fbx"
DELTA = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_animation_doctor\shirt_fix\shirt_weight_fix_v1.json"
OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ShirtBones_20261020"
OUT = os.path.join(OUT_DIR, "SK_Melusina_V2_Shirt_HemRig_Legal.fbx")
REPORT = os.path.join(OUT_DIR, "blender_apply_report.json")

rep = {"schema": "melodia.shirt_legal_fbx_build.v1", "input_fbx": FBX, "output_fbx": OUT}

# ---------------------------------------------------------------- clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

try:
    bpy.ops.import_scene.fbx(filepath=FBX, use_anim=False)
except TypeError:
    bpy.ops.import_scene.fbx(filepath=FBX)

rep["scene_objects"] = [[o.name, o.type] for o in bpy.context.scene.objects]
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
rep["mesh_objects"] = [[o.name, len(o.data.vertices)] for o in meshes]
rep["armature_objects"] = [o.name for o in arms]

shirt = max(meshes, key=lambda o: len(o.data.vertices))
arm = max(arms, key=lambda o: len(o.data.bones))
rep["shirt_object"] = shirt.name
rep["shirt_verts"] = len(shirt.data.vertices)
rep["armature_object"] = arm.name
rep["armature_bones"] = len(arm.data.bones)
bone_names = [b.name for b in arm.data.bones]
rep["bone_dupes"] = [n for n in bone_names if n.endswith(".001")]
rep["bone_dots"] = [n for n in bone_names if "." in n]
rep["hem_bones_present"] = sorted(n for n in bone_names if "hem" in n.lower())

# ------------------------------------------------- bake mesh transform (as orig)
# The source FBX keeps cm-range mesh coords under a 0.01 object transform;
# bake it into the vertices so the export round-trips identically.
shirt.data.transform(shirt.matrix_world)
shirt.matrix_world = Matrix.Identity(4)

# ------------------------------------------------------------- apply weights
delta = json.load(open(DELTA, encoding="utf-8"))["verts"]
if len(delta) != len(shirt.data.vertices):
    raise RuntimeError(
        "delta/mesh vertex count mismatch: delta=%d mesh=%d" % (len(delta), len(shirt.data.vertices))
    )

for g in list(shirt.vertex_groups):
    shirt.vertex_groups.remove(g)

needed = sorted({b for e in delta.values() for b, _w in e})
groups = {}
for b in needed:
    groups[b] = shirt.vertex_groups.new(name=b)

applied = 0
for key, entry in delta.items():
    idx = int(key)
    for b, w in entry:
        groups[b].add([idx], float(w), "REPLACE")
        applied += 1
rep["vertex_groups_created"] = len(groups)
rep["weight_assignments"] = applied
rep["delta_vertex_count"] = len(delta)

# armature modifier must point at the imported armature
arm_mods = [m for m in shirt.modifiers if m.type == "ARMATURE"]
if not arm_mods:
    m = shirt.modifiers.new(name="Armature", type="ARMATURE")
    m.object = arm
    rep["armature_modifier"] = "created"
else:
    arm_mods[0].object = arm
    rep["armature_modifier"] = "rebound"

# ------------------------------------------------------------------- export
for o in bpy.context.scene.objects:
    o.select_set(False)
shirt.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm

bpy.ops.export_scene.fbx(
    filepath=OUT,
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    use_mesh_modifiers=False,
    add_leaf_bones=False,
    bake_anim=False,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    use_armature_deform_only=False,
    mesh_smooth_type="OFF",
    path_mode="AUTO",
)

rep["output_bytes"] = os.path.getsize(OUT)
rep["output_exists"] = os.path.exists(OUT)
json.dump(rep, open(REPORT, "w"), indent=2)
print("BUILD_REPORT=" + json.dumps(rep))
