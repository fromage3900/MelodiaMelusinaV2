# World Compiler UE lane for the melodic archipelago (editor only, idempotent). Set BUNDLE before exec.
# Spawns one StaticMeshActor per island (label ARCH_<recipe>_NN) plus one PCG biome volume per island top
# (meadow -> flowers+grass, grove -> tree belt, crystal -> crystal garden). Never deletes or edits foreign actors.
import unreal, csv

BUNDLE_DIR = BUNDLE  # noqa: F821  e.g. "C:/EnvironmentPortfolio/BS_GodFile/Saved/WorldCompiler/kaleido_archipelago_4101/"
PREFIX = PREFIX      # noqa: F821  e.g. "ARCH_kaleido_archipelago_"
GRAPH = {"meadow": "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_MorningMeadow",
         "grove": "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_IslandGrove",
         "crystal": "/Game/Melodia/PCG/MassiveBiome/PCG_Biome_CrystalGarden"}

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not ues.get_editor_world() or ues.get_game_world():
    print("BUSY")
    raise SystemExit
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = {}
for a in sub.get_all_level_actors():
    L.setdefault(a.get_actor_label(), a)
rows = list(csv.DictReader(open(BUNDLE_DIR + "archipelago.csv", encoding="utf-8")))
graphs = {k: unreal.load_asset(v) for k, v in GRAPH.items()}
meshes, made, vols = {}, [], []
ok = all(graphs.values())
unreal.SystemLibrary.execute_console_command(ues.get_editor_world(), "pcg.FlushCache")
for r in rows:
    i = int(r["island_id"])
    lab = f"{PREFIX}{i:02d}"
    m = meshes.get(r["mesh"]) or unreal.load_asset(r["mesh"])
    meshes[r["mesh"]] = m
    loc = unreal.Vector(float(r["x"]), float(r["y"]), float(r["z"]))
    rot = unreal.Rotator(0.0, float(r["yaw"]), 0.0)
    a = L.get(lab)
    if a is None:
        a = sub.spawn_actor_from_object(m, loc, rot)
        a.set_actor_label(lab)
    else:
        a.set_actor_location(loc, False, False); a.set_actor_rotation(rot, False)
    sc = float(r["scale"])
    a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
    a.tags = [unreal.Name("WorldCompiler.archipelago"), unreal.Name("Arch." + r["biome"])]
    made.append(a)
    # biome volume over the island top
    half = float(r["radius_cm"]) * 0.7
    top = float(r["top_z_cm"])
    vl = f"{PREFIX}{i:02d}_{r['biome']}_PCG"
    v = L.get(vl)
    vloc = unreal.Vector(float(r["x"]), float(r["y"]), top - 150.0)
    if v is None:
        v = sub.spawn_actor_from_class(unreal.PCGVolume, vloc)
        v.set_actor_label(vl)
    else:
        v.set_actor_location(vloc, False, False)
    v.set_actor_scale3d(unreal.Vector(half / 100.0, half / 100.0, 14.0))
    v.tags = [unreal.Name("WorldCompiler.archipelago")]
    pc = v.get_component_by_class(unreal.PCGComponent)
    pc.set_graph(graphs[r["biome"]])
    pc.generate(True)
    vols.append(v)
    if r["biome"] == "meadow":   # flowers come from the biome graph; lay a healthy grass carpet over the same top
        gl = f"{PREFIX}{i:02d}_grass_PCG"
        gv = L.get(gl)
        if gv is None:
            gv = sub.spawn_actor_from_class(unreal.PCGVolume, vloc)
            gv.set_actor_label(gl)
        gv.set_actor_location(vloc, False, False)
        gv.set_actor_scale3d(unreal.Vector(half / 100.0, half / 100.0, 14.0))
        gv.tags = [unreal.Name("WorldCompiler.archipelago")]
        gc = gv.get_component_by_class(unreal.PCGComponent)
        gc.set_graph(unreal.load_asset("/Game/Melodia/PCG/MassiveBiome/PCG_Biome_GrassField"))
        gc.generate(True)
        vols.append(gv)
print("islands", len(made), "volumes", len(vols), "meshes loaded", len(meshes))
pk = {x.get_package().get_name(): x.get_package() for x in made + vols}
print("save", unreal.EditorLoadingAndSavingUtils.save_packages(list(pk.values()), False))
print("STEP_OK" if ok and len(made) == len(rows) else "NOT_OK")
