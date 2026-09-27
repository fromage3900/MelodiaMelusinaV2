# Regalia v4 -> UE (WRITES; run only when the editor is clear). New assets only, all under DST. Never replaces/saves existing assets.
# Set STAGE before exec: "import" | "materials" | "level" | "assemble" | "capture"
import unreal, json, os, math, time
STAGE = globals().get("STAGE", "import")
E = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4"
FBXD = E + r"\restpose"
DST = "/Game/Melodia/Characters/Melusina/Regalia_v4"
LEVEL = DST + "/L_Regalia_v4_Test"
SHOTS = r"C:\Users\froma\Documents\lookdev_regalia_v2\ue_v4"
BODY = "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body"
HAIR = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
CAPLEVEL = "/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture"
PIECES = ["SM_Regalia_v4_Circlet", "SM_Regalia_v4_Tiara", "SM_Regalia_v4_Earrings", "SM_Regalia_v4_Necklace"]
EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
LOG = {"stage": STAGE, "t": time.strftime("%H:%M:%S"), "created": [], "saved": [], "notes": [], "errors": []}
def note(*a): LOG["notes"].append(" ".join(str(x) for x in a))
def err(*a): LOG["errors"].append(" ".join(str(x) for x in a))
def ap(n): return DST + "/" + n
def save_new(asset):
    p = asset.get_path_name().split(".")[0]
    assert p.startswith(DST + "/"), "refusing to save outside " + DST + ": " + p
    EAL.save_loaded_asset(asset, only_if_is_dirty=False); LOG["saved"].append(p)
def save_folder():
    for p in EAL.list_assets(DST, recursive=True, include_folder=False):
        pp = p.split(".")[0]
        if not pp.startswith(DST + "/"): continue
        a = unreal.load_asset(pp)
        if a is None or isinstance(a, unreal.World): continue
        if EAL.save_asset(pp, only_if_is_dirty=True): LOG["saved"].append(pp)
SC = json.load(open(E + r"\restpose\regalia_v4_ue_export_sidecar.json"))
AT_JSON = E + r"\ue_attach_v4.json"
ATT = json.load(open(AT_JSON)) if os.path.exists(AT_JSON) else None

def stage_import():
    for n in PIECES:
        if EAL.does_asset_exist(ap(n)): note("exists, not re-importing", ap(n)); continue
        t = unreal.AssetImportTask(); t.filename = FBXD + "\\" + n + ".fbx"; t.destination_path = DST; t.destination_name = n
        t.automated = True; t.replace_existing = False; t.save = False
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_animations = False
        ui.import_materials = False; ui.import_textures = False; ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        d = ui.static_mesh_import_data; d.combine_meshes = True; d.auto_generate_collision = False; d.generate_lightmap_u_vs = False
        d.convert_scene = True; d.force_front_x_axis = False; d.convert_scene_unit = False; d.transform_vertex_to_absolute = True; d.bake_pivot_in_vertex = False
        d.import_uniform_scale = 1.0; d.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        t.options = ui
        AT.import_asset_tasks([t])
        paths = list(t.imported_object_paths or []); LOG["created"] += paths; note("imported", n, paths)
    # verify bounds against the Blender sidecar (blender-cm space)
    for n in PIECES:
        sm = unreal.load_asset(ap(n))
        if not sm: err("missing after import", n); continue
        b = sm.get_bounding_box(); mn = [b.min.x, b.min.y, b.min.z]; mx = [b.max.x, b.max.y, b.max.z]
        exp = SC["pieces"][n]["bbox_ue_bcm"]; dev = max(abs(a - e) for a, e in zip(mn + mx, exp[0] + exp[1]))
        LOG.setdefault("bounds", {})[n] = {"min": mn, "max": mx, "expected": exp, "max_dev_cm": dev,
            "slots": [str(m.material_slot_name) for m in sm.static_materials], "tris": sm.get_num_triangles(0)}
        if dev > 0.5: err("BOUNDS MISMATCH", n, dev)
        # any auto-created materials land only in DST; record them
    LOG["folder_assets"] = EAL.list_assets(DST, recursive=True)
    save_folder()

def make_mat(name, base, metallic, rough, spec=0.5, emis=0.0):
    if EAL.does_asset_exist(ap(name)): return unreal.load_asset(ap(name))
    m = AT.create_asset(name, DST, unreal.Material, unreal.MaterialFactoryNew()); LOG["created"].append(ap(name))
    MEL = unreal.MaterialEditingLibrary
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0); c.set_editor_property("constant", unreal.LinearColor(*base, 1))
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for i, (v, prop) in enumerate(((metallic, unreal.MaterialProperty.MP_METALLIC), (rough, unreal.MaterialProperty.MP_ROUGHNESS), (spec, unreal.MaterialProperty.MP_SPECULAR))):
        k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 150 + 90 * i); k.set_editor_property("r", v); MEL.connect_material_property(k, "", prop)
    if emis > 0:
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 450); e.set_editor_property("constant", unreal.LinearColor(*[x * emis for x in base], 1))
        MEL.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); return m

def stage_materials():
    M = {"Gold": make_mat("M_Regalia_v4_Gold", (1.0, 0.72, 0.33), 1.0, 0.22),
         "GemAqua": make_mat("M_Regalia_v4_GemAqua", (0.42, 0.78, 0.86), 0.0, 0.04, 1.0, 0.06),
         "GemPurple": make_mat("M_Regalia_v4_GemPurple", (0.42, 0.10, 0.72), 0.0, 0.05, 1.0, 0.06),
         "Pearl": make_mat("M_Regalia_v4_Pearl", (0.93, 0.90, 0.86), 0.0, 0.30, 0.6)}
    for n in PIECES:
        sm = unreal.load_asset(ap(n)); mats = sm.static_materials; ch = []
        for i, sl in enumerate(mats):
            nm = str(sl.material_slot_name)
            key = "Gold" if "Gold" in nm else "GemAqua" if "Aqua" in nm else "GemPurple" if "Purple" in nm else "Pearl" if "Pearl" in nm else None
            if key: sm.set_material(i, M[key]); ch.append((nm, key))
            else: err("unmapped slot", n, nm)
        note("slots", n, ch)
    save_folder()

def stage_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    cur = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    LOG["level_before"] = cur.get_path_name()
    dm = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]; LOG["dirty_maps_before"] = dm
    if cur.get_path_name().startswith(LEVEL): note("already in test level"); return
    if dm: err("current map has unsaved changes -> NOT switching level (would prompt). dirty:", dm); return
    if EAL.does_asset_exist(LEVEL): ok = les.load_level(LEVEL)
    else: ok = les.new_level(LEVEL); LOG["created"].append(LEVEL)
    LOG["level_after"] = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(); note("level switch ok", ok)

def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def T(loc, qxyzw, s):
    q = unreal.Quat(*qxyzw); return unreal.Transform(unreal.Vector(*loc), q.rotator(), unreal.Vector(s, s, s))
def stage_assemble():
    w = world(); assert w.get_path_name().startswith(LEVEL), "not in the test level: " + w.get_path_name()
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("REGV4_"): note("assembly exists already; skipping spawn"); return
    body = unreal.load_asset(BODY); hair = unreal.load_asset(HAIR)
    # --- level assembly (bone-attached actors): the robust path
    ba = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); ba.set_actor_label("REGV4_Melusina_Body")
    bc = ba.skeletal_mesh_component; bc.set_skinned_asset_and_update(body) if hasattr(bc, "set_skinned_asset_and_update") else bc.set_skeletal_mesh(body)
    head = ATT["head_bone"]; neck = ATT["neck_bone"]
    hb = bc.get_socket_transform(head, unreal.RelativeTransformSpace.RTS_COMPONENT)
    ha = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); ha.set_actor_label("REGV4_Melusina_Hair")
    hc = ha.skeletal_mesh_component; hc.set_skinned_asset_and_update(hair) if hasattr(hc, "set_skinned_asset_and_update") else hc.set_skeletal_mesh(hair)
    ha.attach_to_actor(ba, head, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
    ha.root_component.set_relative_transform(hb.inverse(), False, False)   # same as MelodiaHairComponent: cancel head_x bind pose
    LOG["actors"] = {"body": ba.get_path_name(), "hair": ha.get_path_name()}
    for n in PIECES:
        a = ATT["attach"][n]
        sa = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); sa.set_actor_label("REGV4_" + n.replace("SM_Regalia_v4_", ""))
        sa.static_mesh_component.set_static_mesh(unreal.load_asset(ap(n))); sa.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        sa.attach_to_actor(ba, a["bone"], unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
        sa.root_component.set_relative_transform(T(a["loc"], a["quat_xyzw"], a["scale"]), False, False)
        LOG["actors"][n] = sa.get_path_name()
        # check: world-space bounds of the placed piece vs expected (component-space similarity)
        o, e = sa.get_actor_bounds(False); LOG.setdefault("placed_bounds", {})[n] = [o.x, o.y, o.z, e.x, e.y, e.z]
    # --- blueprint wrapper (component-space placement; sockets where the API allows)
    try: build_bp(body, hair, hb)
    except Exception as ex: err("BP build failed (level assembly still valid):", repr(ex))
    # lighting: stream her capture level (read-only use) if present, else a simple 3-point rig
    lights()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); LOG["saved"].append(LEVEL)
    LOG["dirty_maps_after"] = [p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]

def build_bp(body, hair, hb):
    name = "BP_Melusina_Regalia_v4_Test"
    if EAL.does_asset_exist(ap(name)): note("BP exists"); return
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
    bp = AT.create_asset(name, DST, unreal.Blueprint, f); LOG["created"].append(ap(name))
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    def add(parent, cls, nm):
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
        sds.rename_subobject(h, unreal.Text(nm)); return h, L.get_object(L.get_data(h))
    bh, bo = add(root, unreal.SkeletalMeshComponent, "Body")
    bo.set_editor_property("skeletal_mesh_asset", body)
    socket_ok = hasattr(L, "set_socket_name") or hasattr(sds, "set_socket_name")
    hh, ho = add(bh, unreal.SkeletalMeshComponent, "Hair"); ho.set_editor_property("skeletal_mesh_asset", hair)
    # hair: component-space = body (inverse head bind applied only if socketed)
    for n in PIECES:
        a = ATT["attach"][n]; h, o = add(bh, unreal.StaticMeshComponent, n.replace("SM_Regalia_v4_", ""))
        o.set_editor_property("static_mesh", unreal.load_asset(ap(n)))
        cs = ATT["component_space"]
        o.set_editor_property("relative_location", unreal.Vector(*cs["loc"])); o.set_editor_property("relative_rotation", unreal.Quat(*cs["quat_xyzw"]).rotator())
        o.set_editor_property("relative_scale3d", unreal.Vector(cs["scale"], cs["scale"], cs["scale"]))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); save_new(bp)
    note("BP created; components placed in body component space (ref pose). socket API available:", socket_ok)

def lights():
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); w = world()
    if EAL.does_asset_exist(CAPLEVEL):
        try:
            unreal.EditorLevelUtils.add_level_to_world(w, CAPLEVEL, unreal.LevelStreamingAlwaysLoaded); note("streamed capture level for her lighting (not modified, not saved)")
            return
        except Exception as ex: err("stream capture level failed", repr(ex))
    for lbl, rot, inten in (("REGV4_Key", (-35, 60, 0), 6.0), ("REGV4_Fill", (-15, -40, 0), 1.5), ("REGV4_Rim", (-20, 200, 0), 4.0)):
        d = EAS.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 300), unreal.Rotator(rot[0], rot[1], rot[2])); d.set_actor_label(lbl)
        d.light_component.set_intensity(inten)
    s = EAS.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400), unreal.Rotator(0, 0, 0)); s.set_actor_label("REGV4_Sky")

def stage_capture():
    w = world(); EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
    ba = acts["REGV4_Melusina_Body"]; bc = ba.skeletal_mesh_component
    hp = bc.get_socket_location(ATT["head_bone"])
    circ = acts["REGV4_Circlet"]; co, ce = circ.get_actor_bounds(False)
    tgt = unreal.Vector(co.x, co.y, co.z - 12.0)
    fwd = ba.get_actor_right_vector()      # UE char meshes face +Y in component space
    os.makedirs(SHOTS, exist_ok=True)
    hide = [a for l, a in acts.items() if not l.startswith("REGV4_") and a.get_class().get_name() in ("SkeletalMeshActor", "StaticMeshActor") and "Melusina" in l]
    shots = {"front": (0, 95, 0), "threequarter": (35, 95, 5), "profile": (90, 95, 0), "circlet_close": (12, 45, 2), "bust_wide": (25, 150, 6)}
    only_circ = {"threequarter_circletonly": (35, 95, 5), "front_circletonly": (0, 95, 0)}
    RL = unreal.RenderingLibrary
    rt = RL.create_render_target2d(w, 2048, 2048, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    def shoot(nm, yaw, dist, pitch, hide_extra=()):
        yr = math.radians(yaw); pr = math.radians(pitch)
        right = ba.get_actor_forward_vector()
        dirv = unreal.Vector(fwd.x * math.cos(yr) + right.x * math.sin(yr), fwd.y * math.cos(yr) + right.y * math.sin(yr), math.sin(pr))
        cam = unreal.Vector(tgt.x + dirv.x * dist, tgt.y + dirv.y * dist, tgt.z + dirv.z * dist)
        rot = unreal.MathLibrary.find_look_at_rotation(cam, tgt)
        ca = EAS.spawn_actor_from_class(unreal.SceneCapture2D, cam, rot); ca.set_actor_label("REGV4_CAP_" + nm)
        sc = ca.capture_component2d; sc.texture_target = rt; sc.fov_angle = 30.0
        sc.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR; sc.capture_every_frame = False; sc.capture_on_movement = False
        sc.hidden_actors = hide + list(hide_extra)
        sc.capture_scene(); RL.export_render_target(w, rt, SHOTS, "ue_v4_" + nm + ".png"); LOG.setdefault("shots", []).append(nm)
        EAS.destroy_actor(ca)
    for nm, (y, d, p) in shots.items(): shoot(nm, y, d, p)
    for nm, (y, d, p) in only_circ.items(): shoot(nm, y, d, p, [acts["REGV4_Tiara"]])
    shoot("threequarter_nohair", 35, 95, 5, [acts["REGV4_Melusina_Hair"]])
    shoot("profile_nohair", 90, 95, 0, [acts["REGV4_Melusina_Hair"]])
    LOG["capture_target"] = [tgt.x, tgt.y, tgt.z]; LOG["head_bone_world"] = [hp.x, hp.y, hp.z]

try:
    {"import": stage_import, "materials": stage_materials, "level": stage_level, "assemble": stage_assemble, "capture": stage_capture}[STAGE]()
except Exception as ex:
    import traceback; err("EXC", traceback.format_exc())
json.dump(LOG, open(E + r"\ue_stage_%s.json" % STAGE, "w"), indent=1, default=str)
print("REGV4_STAGE_DONE", STAGE, "errors", len(LOG["errors"]))
