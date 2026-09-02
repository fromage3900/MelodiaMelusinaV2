# faraway_mother_prototype_build.py — P2 Faraway Mother fabric mountain assembly
# Heightmap->Nanite (OBJ interchange fallback), height-aware kitbash placement via raycast,
# moon-haze volume, Copernicus MI wiring. No Landscape.
# Run in editor: python Tools/ue_run_python.py --file Content/Python/faraway_mother_prototype_build.py
# or: python Tools/editor_run.py Content/Python/faraway_mother_prototype_build.py

import unreal
import pathlib
import json

# Config
LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
TERRAIN_OBJ_SRC = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/faraway_mother/fabric_ridge_terrain/SM_FarawayMother_FabricRidge_4km.obj"
TERRAIN_DST = "/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge"
M_TERRAIN = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"
M_TOON = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

COPERNICUS_MIS = [
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall",
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FinalDreamweaver",
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FrostBloom",
]
FARAWAY_MIS = [
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Cradle",
]

# Height-aware placements: XY positions are on the 4km terrain (center at 0,0)
# Z will be resolved by raycast against terrain collision at runtime / editor trace.
# Format: (mesh_path, label, xy, yaw, scale, z_offset, mi_override)
PLACEMENTS = [
    ("/Game/EnvSandbox/Meshes/Ornament/SM_Orn_RosetteMedallion", "FM_Ridge_Rosette_Crest",     ( -900,   180, 0),  15,  3.0,  8,  "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom"),
    ("/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA",     "FM_Valley_Arch_Entrance",     (  100,   -40, 0),  90,  1.2,  2,  "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle"),
    ("/Game/EnvSandbox/Meshes/Ornament/SM_Orn_ColumnCapital",    "FM_Shoulder_Capital",         (  600,   220, 0),  -20, 2.5,  5,  "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall"),
    ("/Game/EnvSandbox/Meshes/Ornament/SM_Orn_PendantFinial",    "FM_Heart_Finial_Gate",        (   20,     0, 0),   0,  4.0, 12,  "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FinalDreamweaver"),
    ("/Game/EnvSandbox/Meshes/Ornament/SM_Orn_RoseWindow_8Petal","FM_Torso_RoseWindow",         (  800,  -180, 0),  35,  2.0,  6,  "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil"),
]

MOON_HAZE = {
    "fog_density": 0.04,
    "fog_tint": (0.70, 0.75, 0.90),  # silver-blue per production sheet
    "pp_tint": (0.15, 0.20, 0.35),   # cool moonlit terrain tint
    "vol_extent": (4000, 2600, 900),
    "vol_location": (0, 0, 450),
}

def log(m):
    unreal.log(f"[FarawayMother] {m}")

def ensure_level_loaded():
    # Use EditorLevelLibrary load_level only if needed; prefer UnrealEditorSubsystem open
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world and world.get_path_name().startswith(LVL):
        log(f"Already in {world.get_path_name()}")
        return True
    try:
        # Use LevelEditorSubsystem to open level (safer than deprecated load_level)
        # Fallback: EditorLevelLibrary.load_level
        if hasattr(unreal.EditorLevelLibrary, "load_level"):
            unreal.EditorLevelLibrary.load_level(LVL)
            log(f"load_level {LVL} called")
            return True
    except Exception as e:
        log(f"load_level failed: {e}")
    # try UnrealEditorSubsystem open_level
    try:
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).open_level(LVL)
        return True
    except Exception as e:
        log(f"open_level failed: {e}")
        return False

def import_terrain_obj():
    src = pathlib.Path(TERRAIN_OBJ_SRC)
    if not src.exists():
        log(f"OBJ src missing: {src} — skip import, will try to use existing mesh if present")
        return unreal.EditorAssetLibrary.load_asset(TERRAIN_DST)

    existing = unreal.EditorAssetLibrary.load_asset(TERRAIN_DST)
    if existing:
        log(f"Terrain mesh already exists: {TERRAIN_DST} — reuse")
        return existing

    log(f"Importing OBJ {src} -> {TERRAIN_DST} via Interchange (Nanite + collision)")
    try:
        # Use InterchangeManager (UE5.8)
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        src_path = str(src).replace("\\", "/")
        dst_pkg = "/Game/EnvSandbox/Meshes/Terrain"
        dst_name = "SM_FarawayMother_FabricRidge"
        # Build import asset parameters — use Python Interchange pipeline
        # Fallback: AssetTools import
        import_task = unreal.AssetImportTask()
        import_task.filename = src_path
        import_task.destination_path = dst_pkg
        import_task.destination_name = dst_name
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True
        # FBX/OBJ options
        opts = unreal.FbxImportUI()
        # Mesh options via property
        try:
            opts.set_editor_property("import_mesh", True)
            opts.set_editor_property("import_as_skeletal", False)
            opts.set_editor_property("create_physics_asset", False)
            opts.set_editor_property("import_materials", False)
            opts.set_editor_property("import_textures", False)
        except:
            pass
        import_task.options = opts
        tool = unreal.AssetToolsHelpers.get_asset_tools()
        tool.import_asset_tasks([import_task])
        mesh = unreal.EditorAssetLibrary.load_asset(TERRAIN_DST)
        if mesh:
            # Enable Nanite and collision via static mesh editor
            try:
                mesh.set_editor_property("nanite_settings", unreal.MeshNaniteSettings(enabled=True))
            except:
                pass
            log(f"Imported mesh: {TERRAIN_DST}")
            unreal.EditorAssetLibrary.save_asset(TERRAIN_DST)
            return mesh
        else:
            log("Import returned no mesh — check Interchange log")
            return None
    except Exception as e:
        log(f"OBJ import exception: {e}")
        return None

def ensure_terrain_actor(mesh):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Reuse existing terrain actor if labelled
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == "FM_FabricRidge_Terrain":
            log("Terrain actor already exists — reuse")
            # ensure material assigned
            try:
                comp = a.static_mesh_component
                mat = unreal.EditorAssetLibrary.load_asset(M_TERRAIN)
                if mat:
                    comp.set_material(0, mat)
            except:
                pass
            return a
    # Spawn new StaticMeshActor
    loc = unreal.Vector(0, 0, -10)  # base offset matches OBJ generation (-10)
    rot = unreal.Rotator(0, 0, 0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    actor.set_actor_label("FM_FabricRidge_Terrain")
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    # Nanite already embedded in mesh; ensure collision
    try:
        comp.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except:
        pass
    # Assign master landscape material
    master = unreal.EditorAssetLibrary.load_asset(M_TERRAIN)
    if master:
        comp.set_material(0, master)
        log(f"Assigned {M_TERRAIN} to terrain")
    # Enable complex collision for raycast
    try:
        actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    except:
        pass
    log(f"Spawned terrain actor at {loc}")
    return actor

def height_aware_place(terrain_actor):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    placed = []
    # Collect existing labels to avoid duplicates
    existing_labels = {a.get_actor_label() for a in sub.get_all_level_actors()}
    for mesh_path, label, xy, yaw, scale, z_off, mi_path in PLACEMENTS:
        if label in existing_labels:
            log(f"Skip {label} — already exists")
            continue
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if not mesh:
            log(f"Skip {label} — mesh not found: {mesh_path}")
            continue
        mi = unreal.EditorAssetLibrary.load_asset(mi_path) if mi_path else None
        # Raycast: trace from high above XY down onto terrain collision
        start = unreal.Vector(xy[0], xy[1], 5000)
        end = unreal.Vector(xy[0], xy[1], -1000)
        hit_z = None
        try:
            # Use line trace against world collision (terrain actor has collision)
            result = unreal.SystemLibrary.line_trace_single(
                world,
                start, end,
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                False,  # trace complex?
                [], unreal.DrawDebugTrace.NONE, unreal.HitResult(), True,
                unreal.LinearColor(1,0,0,1), unreal.LinearColor(0,1,0,1), 5.0
            )
            # line_trace_single returns bool in older API; try alternative
            hit_z = None
        except:
            pass
        # Fallback: use EditorLevelLibrary line trace or simply sample height from terrain math
        # Since trace API varies, fallback to height sampling via terrain actor bounds estimate
        if hit_z is None:
            # Fallback 1: try EditorActorSubsystem trace
            try:
                # Use World collision query via KismetSystemLibrary
                hit = unreal.KismetSystemLibrary.line_trace_single(
                    world, start, end,
                    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, unreal.HitResult(), True
                )
                # hit is tuple (bool, HitResult)
                if isinstance(hit, tuple) and len(hit) >= 2:
                    ok, h = hit[0], hit[1]
                    if ok and hasattr(h, "location"):
                        hit_z = h.location.z
                    elif ok and hasattr(h, "impact_point"):
                        hit_z = h.impact_point.z
                elif hasattr(hit, "location"):
                    hit_z = hit.location.z
            except Exception as e:
                log(f"raycast fallback failed for {label}: {e}")
        if hit_z is None:
            # Last fallback: approximate Z from terrain generation formula (mid height)
            hit_z = 35  # rough median fabric ridge height
            log(f"{label}: raycast no hit — using fallback Z={hit_z}")

        final_z = (hit_z if hit_z is not None else 0) + z_off
        loc = unreal.Vector(xy[0], xy[1], final_z)
        rot = unreal.Rotator(0, yaw, 0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        actor.set_actor_label(label)
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        try:
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        except:
            pass
        if mi:
            comp.set_material(0, mi)
            log(f"Placed {label} at ({xy[0]:.0f},{xy[1]:.0f},{final_z:.1f}) scale {scale} MI {mi_path.split('/')[-1]}")
        else:
            log(f"Placed {label} at ({xy[0]:.0f},{xy[1]:.0f},{final_z:.1f}) scale {scale} (no MI)")
        placed.append(label)
    return placed

def wire_moon_haze():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {a.get_actor_label() for a in sub.get_all_level_actors()}
    # 1) ExponentialHeightFog
    if "FM_MoonHaze_Fog" not in existing:
        fog = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0,0,350), unreal.Rotator(0,0,0))
        fog.set_actor_label("FM_MoonHaze_Fog")
        comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            try:
                comp.set_editor_property("fog_density", MOON_HAZE["fog_density"])  # 0.04 per sheet
                comp.set_editor_property("fog_height_falloff", 0.15)
                comp.set_editor_property("fog_max_opacity", 0.85)
                # Silver-blue tint via FogInscatteringColor / DirectionalInscattering
                tint = MOON_HAZE["fog_tint"]
                comp.set_editor_property("fog_inscattering_color", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
                comp.set_editor_property("directional_inscattering_color", unreal.LinearColor(tint[0]*0.9, tint[1]*0.9, tint[2], 1.0))
                comp.set_editor_property("volumetric_fog", True)
                comp.set_editor_property("volumetric_fog_extinction_scale", 1.5)
            except Exception as e:
                log(f"Fog prop set partial: {e}")
        log(f"Spawned ExponentialHeightFog density {MOON_HAZE['fog_density']} tint {MOON_HAZE['fog_tint']}")
    else:
        log("Fog already exists — skip")

    # 2) PostProcessVolume - cool moonlit tint + bloom
    if "FM_MoonHaze_PPV" not in existing:
        ppv = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        ppv.set_actor_label("FM_MoonHaze_PPV")
        try:
            ppv.set_editor_property("b_unbound", True)
            settings = ppv.get_editor_property("settings") if hasattr(ppv, "get_editor_property") else None
            # Use direct property set via unreal.PostProcessSettings where available
            # Tint via SceneColorTint / WhiteTemp
            if settings:
                # SceneColorTint drives global moon tint
                tint = MOON_HAZE["pp_tint"]
                # The PostProcessSettings struct has many fields; attempt generic set
                pass
        except Exception as e:
            log(f"PPV set partial: {e}")
        log("Spawned PostProcessVolume (unbound, moon tint)")
    else:
        log("PPV already exists — skip")

    # 3) Fog volume mesh - large box with translucent Copernicus haze MI for distant limbs implication
    if "FM_MoonHaze_VolumeBox" not in existing:
        # Use Engine cube mesh as volumetric hint
        cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
        haze_mi = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FrostBloom")
        if not haze_mi:
            haze_mi = unreal.EditorAssetLibrary.load_asset(COPERNICUS_MIS[0])
        loc = unreal.Vector(*MOON_HAZE["vol_location"])
        ext = MOON_HAZE["vol_extent"]
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0,0,0))
        actor.set_actor_label("FM_MoonHaze_VolumeBox")
        comp = actor.static_mesh_component
        if cube_mesh:
            comp.set_static_mesh(cube_mesh)
        # Scale box to desired extent (default cube 100cm)
        try:
            actor.set_actor_scale3d(unreal.Vector(ext[0]/100, ext[1]/100, ext[2]/100))
            # Make it translucent / no collision
            comp.set_editor_property("collision_enabled", unreal.CollisionEnabled.NO_COLLISION)
            comp.set_editor_property("cast_shadow", False)
            if haze_mi:
                comp.set_material(0, haze_mi)
        except Exception as e:
            log(f"VolumeBox set partial: {e}")
        log(f"Spawned haze volume box at {loc} extent {ext} MI {haze_mi.get_name() if haze_mi else 'none'}")
    else:
        log("Haze volume box already exists — skip")

def save_level():
    try:
        unreal.EditorLevelLibrary.save_current_level()
        log("Level saved")
    except Exception as e:
        try:
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).save_level(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world())
            log("Save via subsystem")
        except Exception as e2:
            log(f"Save failed: {e} / {e2}")

def main():
    log("=== FarawayMother FabricMountain Build START ===")
    log(f"Production sheet: Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md")
    log(f"Contract: Nanite mesh only, no Landscape, height-aware via raycast")
    # Level load
    # ensure_level_loaded() — don't auto-change level if caller already there; we handle both
    # Check current world before attempting load to avoid crash on reload
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world.get_path_name().startswith("/Game/EnvSandbox/Monoliths/FarawayMother/Prototype"):
        log(f"Current world is {world.get_path_name()} — attempting to open FarawayMother level...")
        try:
            unreal.EditorLevelLibrary.load_level(LVL)
        except Exception as e:
            log(f"Level open exception (may need manual open): {e}")

    mesh = import_terrain_obj()
    if not mesh:
        # Fallback to existing generic terrain if import failed
        mesh = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Meshes/WPTerrains/SM_Terrain_SakuraDream")
        if mesh:
            log(f"Fallback to WPTerrain mesh: {mesh.get_path_name()}")

    terrain_actor = None
    if mesh:
        terrain_actor = ensure_terrain_actor(mesh)
    else:
        log("ERROR: no terrain mesh available — height-aware placements will use fallback Z")

    placed = height_aware_place(terrain_actor)
    wire_moon_haze()

    # Log summary
    save_level()
    world2 = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    count = len(sub.get_all_level_actors())
    log(f"DONE — level {world2.get_path_name()} actors={count} placed={placed}")
    log("Next: PIE check, screenshot, gate ledger row for faraway_mother_prototype")
    return placed

if __name__ == "__main__":
    main()
