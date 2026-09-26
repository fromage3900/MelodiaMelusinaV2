"""Validate staged Melusina FBX files: bone count, height, required morphs. Run: blender -b --factory-startup --python <this>."""
import bpy, glob, json, os, sys

STAGE = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Staging/MelusinaExport_20260925/"
MORPHS = {"Body": ["eyeBlinkLeft", "eyeBlinkRight"]}
report = {}
for path in sorted(glob.glob(STAGE + "*.fbx")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arm = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    keys = sorted({k.name for m in meshes if m.data.shape_keys for k in m.data.shape_keys.key_blocks})
    zs = [(m.matrix_world @ v.co).z for m in meshes for v in m.data.vertices]
    part = os.path.basename(path)[len("SK_Melusina_V2_"):-4]
    need = [k for k in MORPHS.get(part, []) if k not in keys]
    r = {"armatures": len(arm), "bones": len(arm[0].data.bones) if arm else 0, "meshes": len(meshes),
         "height_m": round(max(zs) - min(zs), 3) if zs else 0, "morphs": len(keys), "missing_morphs": need}
    # Body 1.988 here == 198.8 cm in UE (owner-confirmed 2026-09-25 via scratch import).
    r["ok"] = len(arm) == 1 and not need and r["bones"] == 463 and (part != "Body" or 1.9 < r["height_m"] < 2.1)
    report[part] = r
    print(f"FBXCHECK {part} {r}")
json.dump(report, open(STAGE + "validate_report.json", "w"), indent=1)
print("FBXCHECK_DONE", all(r["ok"] for r in report.values()))
sys.stdout.flush(); os._exit(0)
