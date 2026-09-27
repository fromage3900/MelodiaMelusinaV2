# Eyebrows v1 + earrings physics -> UE (WRITES; NOT RUN YET - run only on the parent's go, when the editor is clear).
# New assets only, only under DST_R / DST_B. Never replaces/saves existing assets. Set STAGE before exec:
#   "eyebrows_import" | "earrings_import" | "attach_level" (needs the held 'level' stage done: current level = L_Regalia_v4_Test)
import unreal, json, os, time
STAGE = globals().get("STAGE", "eyebrows_import")
E = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4"
DST_R = "/Game/Melodia/Characters/Melusina/Regalia_v4"
DST_B = "/Game/Melodia/Characters/Melusina/Eyebrows_v1"
ALLOW = (DST_R + "/", DST_B + "/")
LEVEL = DST_R + "/L_Regalia_v4_Test"
BROW_MI = "/Game/Melodia/Characters/Melusina/Portfolio/Staging_20260923/MI_Melusina_Brows_Dark"   # referenced, never modified
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
LOG = {"stage": STAGE, "t": time.strftime("%H:%M:%S"), "created": [], "saved": [], "notes": [], "errors": []}
def note(*a): LOG["notes"].append(" ".join(str(x) for x in a))
def err(*a): LOG["errors"].append(" ".join(str(x) for x in a))
ATT = json.load(open(E + r"\ue_attach_v4.json"))
def save_new(path):
    assert path.startswith(ALLOW), "refusing to save outside allowlist: " + path
    if EAL.save_asset(path, only_if_is_dirty=False): LOG["saved"].append(path)
def fbx_task(fn, dst, name, skeletal):
    t = unreal.AssetImportTask(); t.filename = fn; t.destination_path = dst; t.destination_name = name
    t.automated = True; t.replace_existing = False; t.save = False
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = skeletal; ui.import_animations = False
    ui.import_materials = False; ui.import_textures = False; ui.create_physics_asset = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH
    d = ui.skeletal_mesh_import_data if skeletal else ui.static_mesh_import_data
    d.convert_scene = True; d.force_front_x_axis = False; d.convert_scene_unit = False; d.transform_vertex_to_absolute = True
    d.bake_pivot_in_vertex = False; d.import_uniform_scale = 1.0; d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    if not skeletal: d.combine_meshes = True; d.auto_generate_collision = False; d.generate_lightmap_u_vs = False
    else: d.import_morph_targets = False; d.update_skeleton_reference_pose = False; d.use_t0_as_ref_pose = False
    t.options = ui; AT.import_asset_tasks([t]); p = list(t.imported_object_paths or []); LOG["created"] += p; return p
def bounds_check(asset, exp, tag):
    b = asset.get_bounding_box() if hasattr(asset, "get_bounding_box") else asset.get_bounds().box
    mn = [b.min.x, b.min.y, b.min.z]; mx = [b.max.x, b.max.y, b.max.z]
    dev = max(abs(a - e) for a, e in zip(mn + mx, exp[0] + exp[1])); LOG.setdefault("bounds", {})[tag] = {"min": mn, "max": mx, "exp": exp, "max_dev_cm": dev}
    if dev > 0.5: err("BOUNDS MISMATCH", tag, dev)

def stage_eyebrows_import():
    p = DST_B + "/SM_Melusina_Brows_v1"
    if not EAL.does_asset_exist(p):
        fbx_task(E + r"\eyebrows\SM_Melusina_Brows_v1.fbx", DST_B, "SM_Melusina_Brows_v1", False)
    sm = unreal.load_asset(p); sc = json.load(open(E + r"\eyebrows\SM_Melusina_Brows_v1_sidecar.json"))
    if not sm: err("brows import failed"); return
    bounds_check(sm, sc["bbox_ue_bcm"], "brows")
    mi = unreal.load_asset(BROW_MI)
    if mi: sm.set_material(0, mi); note("brows use existing", BROW_MI, "(reference only)")
    else: err("MI_Melusina_Brows_Dark not found; slot left default")
    save_new(p)

def stage_earrings_import():
    p = DST_R + "/SK_Regalia_v4_Earrings"
    if not EAL.does_asset_exist(p):
        fbx_task(E + r"\earrings_physics\SK_Regalia_v4_Earrings.fbx", DST_R, "SK_Regalia_v4_Earrings", True)
    sk = unreal.load_asset(p)
    if not sk: err("earrings skeletal import failed"); return
    sc = json.load(open(E + r"\earrings_physics\SK_Regalia_v4_Earrings_sidecar.json"))
    bb = sk.get_bounds().box
    LOG["sk_bounds"] = [bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z]
    LOG["skeleton"] = sk.skeleton.get_path_name() if sk.skeleton else None
    mats = sk.materials
    for i, m in enumerate(mats):
        sl = str(m.material_slot_name); tgt = {"MS_Gold": "M_Regalia_v4_Gold", "MS_GemPurple": "M_Regalia_v4_GemPurple"}.get(sl)
        if tgt:
            m.material_interface = unreal.load_asset(DST_R + "/" + tgt); mats[i] = m
    sk.materials = mats
    for pp in EAL.list_assets(DST_R, recursive=False, include_folder=False):
        pp = pp.split(".")[0]
        if "SK_Regalia_v4_Earrings" in pp: save_new(pp)

def T(loc, qxyzw, s): return unreal.Transform(unreal.Vector(*loc), unreal.Quat(*qxyzw).rotator(), unreal.Vector(s, s, s))
def stage_attach_level():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert w.get_path_name().startswith(LEVEL), "not in the test level: " + w.get_path_name()
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); acts = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
    ba = acts["REGV4_Melusina_Body"]; a = ATT["attach"]["SM_Regalia_v4_Circlet"]   # same component-space -> head_x relation
    if "REGV4_Brows_v1" not in acts:
        br = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); br.set_actor_label("REGV4_Brows_v1")
        br.static_mesh_component.set_static_mesh(unreal.load_asset(DST_B + "/SM_Melusina_Brows_v1")); br.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        br.attach_to_actor(ba, a["bone"], unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
        br.root_component.set_relative_transform(T(a["loc"], a["quat_xyzw"], a["scale"]), False, False)
    if "REGV4_Earrings_Physics" not in acts:
        ea = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); ea.set_actor_label("REGV4_Earrings_Physics")
        c = ea.skeletal_mesh_component; c.set_skinned_asset_and_update(unreal.load_asset(DST_R + "/SK_Regalia_v4_Earrings"))
        abp = unreal.load_asset(DST_R + "/ABP_Regalia_Earrings_v4")
        if abp: c.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT); c.set_anim_instance_class(abp.generated_class())
        ea.attach_to_actor(ba, a["bone"], unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
        ea.root_component.set_relative_transform(T(a["loc"], a["quat_xyzw"], a["scale"]), False, False)
        if "REGV4_Earrings" in acts: acts["REGV4_Earrings"].set_actor_hidden_in_game(True); acts["REGV4_Earrings"].set_is_temporarily_hidden_in_editor(True); note("static earrings hidden (kept)")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); LOG["saved"].append(LEVEL)

{"eyebrows_import": stage_eyebrows_import, "earrings_import": stage_earrings_import, "attach_level": stage_attach_level}[STAGE]()
print("REGV4X-LOG " + json.dumps(LOG))
