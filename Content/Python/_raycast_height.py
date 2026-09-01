import unreal

# ============================================================
# HEIGHT-AWARE PLACEMENT via Raycasting
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

print(f"Landscape Z: {landscape.get_actor_location().z:.0f}")

# Function to get Z using line trace
def get_z_at(x, y):
    """Raycast down to find surface Z at (X, Y)."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Start well above landscape, go well below
    start = unreal.Vector(x, y, 50000)
    end = unreal.Vector(x, y, -50000)
    
    # Perform line trace
    result = unreal.SystemLibrary.line_trace_single(
        world,
        start,
        end,
        0,  # DrawDebugType (0 = None)
        True,  # bTraceComplex
        [],  # ActorsToIgnore
        1   # CollisionChannel (1 = Visibility)
    )
    
    if result:
        blocking = result.get_editor_property("bBlockingHit")
        if blocking:
            impact = result.get_editor_property("ImpactPoint")
            return impact.z
    
    # Fallback
    return landscape.get_actor_location().z

# Test at a few points
test_points = [
    (0, 0),
    (1000, 0),
    (0, 1000),
    (-1000, 0),
    (0, -1000),
    (2000, 2000),
    (-2000, -2000),
    (5000, 5000),
]

print("\nHeight samples:")
for px, py in test_points:
    z = get_z_at(px, py)
    print(f"  ({px:5d},{py:5d}) -> Z={z:.0f}")
