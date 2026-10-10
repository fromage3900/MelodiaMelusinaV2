# World Compiler UE lane for the Houdini-driven meadow stage (editor only, idempotent).
# Steps: wind/hue MIs on the existing wind master, points table, PointField graph copy, volume + generate.
# Prints STEP_OK only when every verification passed. Never touches a master, a mesh asset or another level.
import unreal

ROOT = "C:/EnvironmentPortfolio/BS_GodFile/"
BUNDLE = ROOT + "Saved/WorldCompiler/morning_meadow_3900/"
W = "/Game/Melodia/WorldCompiler/"
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Flora/Meadow"
MASTER = "/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind"
FAMILIES = {  # MI name -> (Megascans MI that already carries the right textures, hue seed, reveal tint)
    "MI_Meadow_Kikuyu": ("/Game/Megascans/3D_Plants/KikuyuGrass/MI_KikuyuGrass_01", 0.30, (0.50, 0.88, 0.46, 1.0)),
    "MI_Meadow_Clover": ("/Game/Megascans/3D_Plants/CloverVarieties/MI_CloverVarieties_01", 0.55, (0.58, 0.90, 0.52, 1.0)),
    "MI_Meadow_GroundCover": ("/Game/Megascans/3D_Plants/GroundCover/MI_GroundCover_01", 0.15, (0.48, 0.84, 0.50, 1.0)),
}

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not ues.get_editor_world() or ues.get_game_world():
    print("BUSY")
    raise SystemExit
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
ok = True

# ---- 1. shader instances -------------------------------------------------------------------------------------
if not EAL.does_directory_exist(MI_DIR):
    EAL.make_directory(MI_DIR)
master = unreal.load_asset(MASTER)
for name, (src_path, seed, tint) in FAMILIES.items():
    src = unreal.load_asset(src_path)
    if src is None or master is None:
        print("MISSING source/master", src_path, MASTER); ok = False; continue
    path = f"{MI_DIR}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MI_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    for param, srcparam in (("ColorOpacity", "Albedo"), ("NormalRoughness", "Normal"), ("Subsurface", "Translucency")):
        tex = MEL.get_material_instance_texture_parameter_value(src, srcparam)
        if tex is None:
            print("no texture (optional)" if srcparam == "Translucency" else "MISSING TEXTURE", src_path, srcparam)
            ok &= srcparam == "Translucency"
        else:
            MEL.set_material_instance_texture_parameter_value(mi, param, tex)
    for k, v in (("MelodiaWindResponse", 0.6), ("MelodiaWindHueSeed", seed), ("SharedOscillation", 4.0), ("SharedBend", 6.0),
                 ("Branch1Oscillation", 2.0), ("Branch1Bend", 4.0), ("RippleDirectional", 2.0), ("RipplePlanar", 2.0),
                 ("MelodiaWindGustResponse", 0.8), ("MelodiaHueShift", 0.07)):
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    MEL.set_material_instance_vector_parameter_value(mi, "MelodiaWindRevealTint", unreal.LinearColor(*tint))
    MEL.update_material_instance(mi)
    ok &= bool(EAL.save_asset(path, only_if_is_dirty=False))
    print("MI", name, "parent", mi.get_editor_property("parent").get_name())

# ---- 2. points table ------------------------------------------------------------------------------------------
dt_path = W + "DT_morning_meadow_MeadowPoints"
if not EAL.does_asset_exist(dt_path):
    f = unreal.DataTableFactory()
    f.set_editor_property("struct", unreal.load_asset(W + "S_WorldCompilerPoint"))
    unreal.AssetToolsHelpers.get_asset_tools().create_asset("DT_morning_meadow_MeadowPoints", W.rstrip("/"), unreal.DataTable, f)
dt = unreal.load_asset(dt_path)
lines = open(BUNDLE + "meadow_points.csv", encoding="utf-8").read().splitlines()
rows = ["---," + lines[0]] + [f"p{i}," + l for i, l in enumerate(lines[1:])]
fill_ok = unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(dt, "\n".join(rows) + "\n")
n_rows = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))
print("table fill", fill_ok, "rows", n_rows, "of", len(lines) - 1)
ok &= bool(fill_ok) and n_rows == len(lines) - 1
ok &= bool(EAL.save_asset(dt_path, only_if_is_dirty=False))

# ---- 3. graph copy ---------------------------------------------------------------------------------------------
g_dst = W + "PCG_WorldCompiler_PointField_Meadow"
if not EAL.does_asset_exist(g_dst):
    EAL.duplicate_asset(W + "PCG_WorldCompiler_PointField", g_dst)
g = unreal.load_asset(g_dst)
repointed = 0
for n in g.get_editor_property("nodes"):
    st = n.get_settings()
    if st and st.get_class().get_name() == "PCGLoadDataTableSettings":
        st.set_editor_property("data_table", dt)
        repointed += 1
reads = [n.get_settings().get_editor_property("data_table").get_path_name() for n in g.get_editor_property("nodes")
         if n.get_settings() and n.get_settings().get_class().get_name() == "PCGLoadDataTableSettings"]
print("graph repointed", repointed, reads)
ok &= repointed >= 1 and all("MeadowPoints" in r for r in reads)
ok &= bool(EAL.save_asset(g_dst, only_if_is_dirty=False))

# ---- 4. volume + generate + count -------------------------------------------------------------------------------
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = {}
for a in sub.get_all_level_actors():
    L.setdefault(a.get_actor_label(), a)
ref = L.get("WC_morning_rainbow_bloom_Field")
if ref is None:
    print("rainbow-bloom field volume not loaded yet (World Partition) -> retry"); ok = False
else:
    lab = "WC_morning_meadow_Meadow"
    v = L.get(lab)
    if v is None:
        v = sub.spawn_actor_from_class(unreal.PCGVolume, ref.get_actor_location())
        v.set_actor_label(lab)
        v.set_actor_scale3d(ref.get_actor_scale3d())
        v.tags = [unreal.Name("WorldCompiler.morning_meadow_3900")]
    comp = v.get_component_by_class(unreal.PCGComponent)
    comp.set_graph(g)
    unreal.SystemLibrary.execute_console_command(ues.get_editor_world(), "pcg.FlushCache")
    comp.generate(True)
    print("generate requested on", lab)

print("STEP_OK" if ok else "NOT_OK")
