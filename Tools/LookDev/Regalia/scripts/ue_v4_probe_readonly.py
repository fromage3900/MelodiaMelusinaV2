# READ-ONLY probe for Regalia v4 (no asset/level writes, no saves). Writes a JSON report outside Content.
import unreal, json, os, time
OUT = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4\ue_probe_v4.json"
R = {"t": time.strftime("%Y-%m-%d %H:%M:%S")}
def P(k, fn):
    try: R[k] = fn()
    except Exception as e: R[k] = "ERR %r" % e
ELS = unreal.EditorLoadingAndSavingUtils
P("dirty_content", lambda: [p.get_path_name() for p in ELS.get_dirty_content_packages()])
P("dirty_maps", lambda: [p.get_path_name() for p in ELS.get_dirty_map_packages()])
P("current_level", lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())
BODY = "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body"; HAIR = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
def skinfo(path):
    sk = unreal.load_asset(path); d = {"class": sk.get_class().get_name()}
    skel = sk.get_editor_property("skeleton"); d["skeleton"] = skel.get_path_name() if skel else None
    b = sk.get_bounds(); d["bounds_origin"] = [b.origin.x, b.origin.y, b.origin.z]; d["bounds_extent"] = [b.box_extent.x, b.box_extent.y, b.box_extent.z]
    pose = unreal.AnimPoseExtensions.get_reference_pose(skel)
    names = unreal.AnimPoseExtensions.get_bone_names(pose); d["n_bones"] = len(names); bones = {}
    for n in names:
        t = unreal.AnimPoseExtensions.get_ref_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD)
        q = t.rotation; bones[str(n)] = [t.translation.x, t.translation.y, t.translation.z, q.x, q.y, q.z, q.w, t.scale3d.x]
    d["bones_cs"] = bones
    d["materials"] = [(str(m.material_slot_name), m.material_interface.get_path_name() if m.material_interface else None) for m in sk.get_editor_property("materials")]
    return d
P("body", lambda: skinfo(BODY)); P("hair", lambda: skinfo(HAIR))
P("has_MelodiaHairComponent", lambda: hasattr(unreal, "MelodiaHairComponent"))
P("api", lambda: {k: hasattr(unreal, k) for k in ("SubobjectDataSubsystem", "SubobjectDataBlueprintFunctionLibrary", "AnimPoseExtensions", "InterchangeManager", "FbxImportUI", "EditorLevelUtils", "LevelEditorSubsystem")})
P("regalia_folder_exists", lambda: unreal.EditorAssetLibrary.does_directory_exist("/Game/Melodia/Characters/Melusina/Regalia_v4"))
P("capture_level_exists", lambda: unreal.EditorAssetLibrary.does_asset_exist("/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture"))
P("interchange_fbx", lambda: str(unreal.SystemLibrary.get_console_variable_int_value("Interchange.FeatureFlags.Import.FBX")))
P("sds_methods", lambda: [m for m in dir(unreal.SubobjectDataSubsystem) if not m.startswith("_")])
P("sdbfl_methods", lambda: [m for m in dir(unreal.SubobjectDataBlueprintFunctionLibrary) if not m.startswith("_")])
P("scenecomp_socket_props", lambda: [m for m in dir(unreal.SceneComponent) if "socket" in m.lower() or "attach" in m.lower()])
P("monolith_note", lambda: "see HTTP tools/list separately")
json.dump(R, open(OUT, "w"), indent=1, default=str)
print("PROBE_OK", OUT)
