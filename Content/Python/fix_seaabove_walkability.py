import unreal

# ============================================================
# SEA ABOVE WALKABILITY FIX - NavMesh, Collision, Height-Aware
# Run via: unreal editor Python (requires editor open)
# ============================================================

print("="*60)
print("SEA ABOVE WALKABILITY FIX")
print("="*60)

# 1. Ensure NavMeshBoundsVolume covers walkable area
# Find existing NavMeshBoundsVolume
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
nav_volumes = [a for a in all_actors if "NavMeshBoundsVolume" in a.get_class().get_name()]
print(f"Found {len(nav_volumes)} NavMeshBoundsVolume(s)")

# Check RecastNavMesh
nav_meshes = [a for a in all_actors if "RecastNavMesh" in a.get_class().get_name()]
print(f"Found {len(nav_meshes)} RecastNavMesh(es)")

# Find PlayerStart
starts = [a for a in all_actors if "PlayerStart" in a.get_class().get_name()]
for s in starts:
    loc = s.get_actor_location()
    print(f"PlayerStart '{s.get_actor_label()}' at ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})")

# Find walkable surfaces
statics = [a for a in all_actors if "StaticMeshActor" in a.get_class().get_name()]
combat_floors = [a for a in statics if "CombatFloor" in a.get_actor_label()]
islands = [a for a in statics if "Island" in a.get_actor_label()]
cathedral_floors = [a for a in statics if "CombatFloor" in str(a.get_actor_label()) or "Cathedral" in str(a.get_actor_label())]

print(f"Total StaticMeshActors: {len(statics)}")
print(f"CombatFloors: {len(combat_floors)}")
print(f"Islands: {len(islands)}")

# 2. Fix NavMeshBoundsVolume to cover entire walkable area
# Compute bounds of all walkable meshes
if nav_volumes and statics:
    # Expand NavMeshBoundsVolume to cover walkable area + buffer
    vol = nav_volumes[0]
    # Get current bounds
    loc = vol.get_actor_location()
    scale = vol.get_actor_scale3d()
    print(f"Current NavMeshBoundsVolume at ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) scale ({scale.x:.1f},{scale.y:.1f},{scale.z:.1f})")
    
    # Collect walkable mesh locations to compute needed extent
    walkable_locs = []
    for a in combat_floors + islands:
        walkable_locs.append(a.get_actor_location())
    # Also include cathedral pieces as walkable context
    for a in statics:
        if "Cathedral" in a.get_actor_label():
            walkable_locs.append(a.get_actor_location())
    
    if walkable_locs:
        min_x = min(l.x for l in walkable_locs)
        max_x = max(l.x for l in walkable_locs)
        min_y = min(l.y for l in walkable_locs)
        max_y = max(l.y for l in walkable_locs)
        min_z = min(l.z for l in walkable_locs)
        max_z = max(l.z for l in walkable_locs)
        print(f"Walkable bounds: X[{min_x:.0f},{max_x:.0f}] Y[{min_y:.0f},{max_y:.0f}] Z[{min_z:.0f},{max_z:.0f}]")
        
        # NavMesh volume should cover with 2000uu buffer, height from min_z-500 to max_z+2000
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        extent_x = (max_x - min_x) / 2 + 2000
        extent_y = (max_y - min_y) / 2 + 2000
        extent_z = (max_z - min_z) / 2 + 3000
        
        # Default NavMeshBoundsVolume brush is 200x200x200 cm, scaled
        # Scale = extent / 100 (since brush is 200 units, half-extent 100)
        new_scale_x = max(extent_x / 100.0, scale.x)
        new_scale_y = max(extent_y / 100.0, scale.y)
        new_scale_z = max(extent_z / 100.0, scale.z)
        
        # Only expand if needed
        if new_scale_x > scale.x or new_scale_y > scale.y or new_scale_z > scale.z:
            # Move volume to center of walkable area
            new_loc = unreal.Vector(center_x, center_y, center_z)
            vol.set_actor_location(new_loc, False)
            vol.set_actor_scale3d(unreal.Vector(new_scale_x, new_scale_y, new_scale_z))
            print(f"FIXED NavMeshBoundsVolume -> loc ({center_x:.0f},{center_y:.0f},{center_z:.0f}) scale ({new_scale_x:.1f},{new_scale_y:.1f},{new_scale_z:.1f})")
        else:
            print(f"NavMeshBoundsVolume already covers walkable area - no resize needed")

# 3. Fix collision on walkable meshes - ensure CombatFloor and Islands have collision enabled
fixed_collision = 0
for actor in statics:
    label = actor.get_actor_label()
    if "CombatFloor" in label or "Island" in label or "RockChunk" in label:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            mesh = comp.get_editor_property("static_mesh")
            if mesh:
                body_setup = mesh.get_editor_property("body_setup")
                if body_setup:
                    # Ensure collision trace is not NoCollision-equivalent
                    coll = comp.get_editor_property("collision_enabled")
                    # Set to QueryAndPhysics if not already
                    if str(coll) != "QueryAndPhysics":
                        try:
                            comp.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                            fixed_collision += 1
                            print(f"Fixed collision on {label}: {coll} -> QueryAndPhysics")
                        except Exception as e:
                            print(f"  Skip {label}: {e}")
                    # Ensure CanEverAffectNavigation
                    try:
                        comp.set_editor_property("can_ever_affect_navigation", True)
                    except:
                        pass

print(f"Fixed collision on {fixed_collision} walkable meshes")

# 4. Height-aware placement check - detect floating or gaps
# Raycast down from each walkable mesh to check if it contacts ground/landscape
floating = []
for actor in combat_floors + islands:
    loc = actor.get_actor_location()
    # Trace down 2000uu
    world = unreal.EditorLevelLibrary.get_editor_world()
    start = unreal.Vector(loc.x, loc.y, loc.z + 100)
    end = unreal.Vector(loc.x, loc.y, loc.z - 5000)
    # Use line trace
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.DrawDebugType.NONE, True, [], unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugType.NONE, 0
    )
    # This trace checks if mesh is floating far from supporting surface
    # For now, just report Z heights for manual gap check
    pass

# Report Z variance for gap detection
if combat_floors:
    z_vals = sorted([a.get_actor_location().z for a in combat_floors])
    print(f"CombatFloor Z range: {z_vals[0]:.0f} to {z_vals[-1]:.0f} (spread {z_vals[-1]-z_vals[0]:.0f})")
    # Detect gaps > 100uu between sorted floors (potential fall-through)
    gaps = [(z_vals[i+1]-z_vals[i], z_vals[i], z_vals[i+1]) for i in range(len(z_vals)-1) if z_vals[i+1]-z_vals[i] > 50]
    if gaps:
        print(f"Potential Z gaps between CombatFloors (>50uu): {len(gaps)}")
        for gap, a, b in gaps[:5]:
            print(f"  Gap {gap:.0f} between Z {a:.0f} and {b:.0f}")
    else:
        print("No significant Z gaps between CombatFloors - GOOD")

# 5. Trigger NavMesh rebuild
print("\nTriggering NavMesh rebuild...")
try:
    unreal.EditorLevelLibrary.editor_build_navmesh()
    print("NavMesh build triggered")
except Exception as e:
    print(f"NavMesh build via editor_build_navmesh not available: {e}")
    # Alternative: mark package dirty to trigger rebuild on save
    try:
        # Request navmesh rebuild via console
        unreal.SystemLibrary.execute_console_command(None, "RebuildNavigation")
        print("RebuildNavigation console command sent")
    except Exception as e2:
        print(f"  Fallback also failed: {e2}")

print("\n" + "="*60)
print("WALKABILITY FIX COMPLETE")
print("="*60)
print("Verify in PIE: walk on islands/cathedral, check no fall-through, no floating")
