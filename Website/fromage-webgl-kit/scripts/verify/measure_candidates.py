import bpy, os, json

CANDIDATES = [
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\MelodiaPresetReview\Melodia_AAA_Preset_Review\UE_Exports\SM_VIOLIN_BELL_RELIQUARY.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\MelodiaPresetReview\Melodia_AAA_Preset_Review\UE_Exports\SM_LUTE_PELAGIC_VAULT.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\MelodiaPresetReview\Melodia_AAA_Preset_Review\UE_Exports\SM_HARPSICHORD_SEA_ABOVE_HERO.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\MelodiaPresetReview\Melodia_AAA_Preset_Review\UE_Exports\SM_ORGAN_ABYSSAL_CATHEDRAL.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\MelodiaPresetReview\Melodia_AAA_Preset_Review\UE_Exports\SM_BELL_ANATOMY_CHAMBER.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\harp_bow\SM_Siren_Harp_Bow.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\harp_bow\SM_Harp_Bow_Base.fbx",
    r"C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\SM_MelodyToken.fbx",
]


def measure(fp):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fp)
    tris, meshes, loose = 0, 0, 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        meshes += 1
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    return meshes, tris


out = []
for fp in CANDIDATES:
    name = os.path.basename(fp)
    if not os.path.isfile(fp):
        out.append({"file": name, "error": "not found"})
        continue
    try:
        meshes, tris = measure(fp)
        out.append({
            "file": name,
            "meshes": meshes,
            "tris": tris,
            "mb": round(os.path.getsize(fp) / 1048576, 2),
        })
    except Exception as e:
        out.append({"file": name, "error": str(e)})

out.sort(key=lambda d: d.get("tris", 1 << 40))
print("RESULT_JSON_START")
print(json.dumps(out, indent=1))
print("RESULT_JSON_END")
