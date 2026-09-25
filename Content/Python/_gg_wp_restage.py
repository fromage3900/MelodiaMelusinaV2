"""Restage Glassgarden kit on WP level: UDS/UDW, PCG volumes, MeshPartition bridge, SMA, fog."""
import unreal, json
from pathlib import Path

LEVEL = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/LV_Glassgarden_Shoals"
TERRAIN_DEST = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/Terrain"
OBJ = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/GlassgardenShoals/terrain/SM_Glassgarden_MeshTerrain_257.obj"
MESH_ASSET = f"{TERRAIN_DEST}/SM_Glassgarden_MeshTerrain_257"
MAT_ASSET = f"{TERRAIN_DEST}/MI_Glassgarden_MeshTerrain_Substrate"
PARENT_MAT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
UDS = "/Game/_ThirdParty/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky"
UDW = "/Game/_ThirdParty/UltraDynamicSky/Blueprints/Ultra_Dynamic_Weather"
PCG_GRAPHS = [
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_Scree",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_TerraceGarden",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisBiome",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden",
]
out = {"steps": {}}

def editor_world():
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            w = ues.get_editor_world()
            if w:
                return w
    except Exception:
        pass
    return unreal.EditorLevelLibrary.get_editor_world()

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = editor_world()
cur = w.get_path_name().split(".")[0] if w else None
if cur != LEVEL:
    out["steps"]["load_level"] = {"ok": bool(les.load_level(LEVEL)), "from": cur}
else:
    out["steps"]["load_level"] = {"ok": True, "already": cur}

def by_label():
    return {a.get_actor_label(): a for a in (eas.get_all_level_actors() or [])}

wp = {"bounds_ok": False, "markers": []}
try:
    bounds = unreal.WorldPartitionBlueprintLibrary.get_editor_world_bounds()
    wp["bounds_ok"] = bool(bounds and bounds.is_valid)
except Exception as e:
    wp["bounds_error"] = str(e)[:200]
for a in (eas.get_all_level_actors() or []):
    n = a.get_class().get_name()
    if n in ("WorldDataLayers", "WorldPartitionMiniMap", "WorldPartitionReplay"):
        wp["markers"].append(n)
out["steps"]["wp_probe"] = wp

existing = by_label()

# UDS/UDW
uds_rows = []
for path, label in [(UDS, "Glassgarden_UDS"), (UDW, "Glassgarden_UDW")]:
    bp = None
    try:
        bp = unreal.EditorAssetLibrary.load_blueprint_class(path)
    except Exception:
        bp = None
    if bp is None:
        bp = unreal.load_object(None, path + "." + path.rsplit("/", 1)[-1] + "_C")
    row = {"path": path, "label": label, "bp_ok": bp is not None}
    if not bp:
        row["error"] = "missing"
        uds_rows.append(row)
        continue
    if label in existing:
        a = existing[label]
        row["action"] = "reuse"
    else:
        a = eas.spawn_actor_from_class(bp, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if a:
            a.set_actor_label(label)
            row["action"] = "spawn"
        else:
            row["error"] = "spawn_failed"
            uds_rows.append(row)
            continue
    row["actor_class"] = a.get_class().get_name()
    uds_rows.append(row)
out["steps"]["uds_weather"] = uds_rows
existing = by_label()

# PCG volumes
pcg_rows = []
for i, gpath in enumerate(PCG_GRAPHS):
    label = "Glassgarden_PCG_" + gpath.rsplit("/", 1)[-1]
    graph_ok = unreal.EditorAssetLibrary.does_asset_exist(gpath)
    row = {"graph": gpath, "label": label, "graph_exists": graph_ok}
    if not graph_ok:
        row["error"] = "missing"
        pcg_rows.append(row)
        continue
    graph = unreal.EditorAssetLibrary.load_asset(gpath)
    if label in existing:
        vol = existing[label]
        row["action"] = "reuse"
    else:
        vol = eas.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(0, 0, 200), unreal.Rotator(0, 0, 0))
        if not vol:
            row["error"] = "spawn_failed"
            pcg_rows.append(row)
            continue
        vol.set_actor_label(label)
        row["action"] = "spawn"
    vol.set_actor_scale3d(unreal.Vector(80.0, 80.0, 10.0))
    vol.set_actor_location(unreal.Vector(float(i) * 50.0, 0.0, 100.0), False, False)
    tags = {str(t) for t in (vol.tags or [])}
    tags.update({"GlassgardenShoals", "PCGexStyleKit", "SeaAboveStyleRef"})
    vol.tags = list(tags)
    comp = vol.get_component_by_class(unreal.PCGComponent)
    graph_set = False
    notes = []
    if comp and graph:
        for meth in ("set_graph", "set_graph_local"):
            fn = getattr(comp, meth, None)
            if callable(fn):
                try:
                    fn(graph)
                    graph_set = True
                    notes.append(meth + "=ok")
                    break
                except Exception as e:
                    notes.append(meth + "=" + str(e)[:80])
        if not graph_set:
            for prop in ("graph", "Graph"):
                try:
                    comp.set_editor_property(prop, graph)
                    graph_set = True
                    notes.append("prop " + prop + "=ok")
                    break
                except Exception as e:
                    notes.append("prop " + prop + "=" + str(e)[:80])
    row["graph_set"] = graph_set
    row["graph_notes"] = notes
    pcg_rows.append(row)
out["steps"]["pcg_style_volumes"] = pcg_rows
existing = by_label()

# Terrain mesh/MI
terrain = {"obj_exists": Path(OBJ).is_file()}
if not unreal.EditorAssetLibrary.does_directory_exist(TERRAIN_DEST):
    unreal.EditorAssetLibrary.make_directory(TERRAIN_DEST)
mesh = unreal.load_asset(MESH_ASSET) if unreal.EditorAssetLibrary.does_asset_exist(MESH_ASSET) else None
if mesh is None and Path(OBJ).is_file():
    task = unreal.AssetImportTask()
    task.filename = OBJ
    task.destination_path = TERRAIN_DEST
    task.destination_name = "SM_Glassgarden_MeshTerrain_257"
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(MESH_ASSET)
    terrain["mesh_import"] = "imported" if mesh else "failed"
else:
    terrain["mesh_import"] = "existing" if mesh else "missing"

mat = unreal.load_asset(MAT_ASSET) if unreal.EditorAssetLibrary.does_asset_exist(MAT_ASSET) else None
if mat is None:
    parent = unreal.load_asset(PARENT_MAT)
    if parent:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_Glassgarden_MeshTerrain_Substrate", TERRAIN_DEST, unreal.MaterialInstanceConstant, factory
        )
        if mat:
            mat.set_editor_property("parent", parent)
            unreal.EditorAssetLibrary.save_loaded_asset(mat, True)
            terrain["material"] = "created"
        else:
            terrain["material"] = "create_failed"
    else:
        terrain["material"] = "parent_missing"
else:
    terrain["material"] = "existing"

# SMA
sma_label = "Glassgarden_MeshTerrain_SMA"
if mesh:
    if sma_label in existing:
        sma = existing[sma_label]
        terrain["sma"] = "reuse"
    else:
        sma = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if sma:
            sma.set_actor_label(sma_label)
            terrain["sma"] = "spawn"
        else:
            terrain["sma"] = "spawn_failed"
            sma = None
    if sma:
        c = sma.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        if mat:
            c.set_material(0, mat)
        sma.set_actor_scale3d(unreal.Vector(100.0, 100.0, 100.0))
        tags = {str(t) for t in (sma.tags or [])}
        tags.update({"GlassgardenShoals", "MeshTerrain", "SMA_Substrate"})
        sma.tags = list(tags)
existing = by_label()

# MeshPartition bridge
label_mt = "Glassgarden_MeshTerrain_257"
bridge_fn = getattr(getattr(unreal, "PCGScaleWorldEditorLibrary", object), "create_mesh_partition_terrain", None)
terrain["bridge_reflected"] = bridge_fn is not None
terrain["MeshPartition_reflected"] = getattr(unreal, "MeshPartition", None) is not None
if bridge_fn and mesh:
    try:
        terrain["bridge_result"] = str(
            bridge_fn(LEVEL, mesh.get_path_name(), mat.get_path_name() if mat else "", label_mt)
        )
    except Exception as exc:
        terrain["bridge_error"] = str(exc)[:400]
elif getattr(unreal, "MeshPartition", None) and mesh:
    mp_cls = unreal.MeshPartition
    if label_mt in existing:
        actor = existing[label_mt]
        terrain["actor"] = "reuse"
    else:
        actor = eas.spawn_actor_from_class(mp_cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if actor:
            actor.set_actor_label(label_mt)
            terrain["actor"] = "spawn"
        else:
            terrain["actor"] = "spawn_failed"
            actor = None
    if actor:
        tags = {str(t) for t in (actor.tags or [])}
        tags.update({"GlassgardenShoals", "MeshTerrain", "Glassgarden257"})
        actor.tags = list(tags)

existing = by_label()
mp_actor = existing.get(label_mt)
if mp_actor:
    terrain["meshpartition_present"] = True
    terrain["meshpartition_actor_class"] = mp_actor.get_class().get_name()
else:
    mps = [a for a in (eas.get_all_level_actors() or []) if a.get_class().get_name() == "MeshPartition"]
    terrain["meshpartition_present"] = len(mps) > 0
    terrain["meshpartition_labels"] = [a.get_actor_label() for a in mps]
out["steps"]["mesh_terrain"] = terrain

# Fog host
fog_label = "Glassgarden_ExponentialHeightFog"
existing = by_label()
if fog_label in existing:
    fog = existing[fog_label]
    fog_action = "reuse"
else:
    fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if fog:
        fog.set_actor_label(fog_label)
        fog_action = "spawn"
    else:
        fog_action = "spawn_failed"
        fog = None
ssfs = {"fog_actor": fog_action}
if fog:
    tags = {str(t) for t in (fog.tags or [])}
    tags.update({"GlassgardenShoals", "ScreenSpaceFogScatteringHost"})
    fog.tags = list(tags)
    try:
        comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            try:
                comp.set_editor_property("fog_density", 0.018)
            except Exception:
                pass
            ssfs["fog_component"] = comp.get_name()
    except Exception as e:
        ssfs["fog_comp_error"] = str(e)[:200]
out["steps"]["ssfs"] = ssfs

# Save
saved = bool(unreal.EditorLevelLibrary.save_current_level())
folder_saved = unreal.EditorAssetLibrary.save_directory(TERRAIN_DEST, only_if_is_dirty=False, recursive=True)
try:
    unreal.EditorAssetLibrary.save_asset(LEVEL, only_if_is_dirty=False)
except Exception:
    pass
out["steps"]["save"] = {"level_saved": saved, "terrain_folder_saved": bool(folder_saved)}

final = [{"label": a.get_actor_label(), "class": a.get_class().get_name()} for a in (eas.get_all_level_actors() or [])]
out["actors"] = final
out["actor_count"] = len(final)
out["open_level"] = editor_world().get_path_name().split(".")[0]
try:
    bounds = unreal.WorldPartitionBlueprintLibrary.get_editor_world_bounds()
    out["wp_bounds_ok"] = bool(bounds and bounds.is_valid)
except Exception as e:
    out["wp_bounds_ok"] = False
    out["wp_bounds_error"] = str(e)[:200]
print(json.dumps(out, default=str))
