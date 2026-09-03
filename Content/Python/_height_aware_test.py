import unreal
import json
import math
import random

# ============================================================
# HEIGHT-AWARE ATLANTIS PLACEMENT
# Snap pieces to CanonicalLandscape surface
# ============================================================

random.seed(2026)

# Cathedral center
CX, CY, CZ = 0, 0, 13405

# Get CanonicalLandscape
actors = unreal.EditorLevelLibrary.get_all_level_actors()
canonical = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        canonical = a
        break

if canonical is None:
    print("[FATAL] CanonicalLandscape not found")
    exit()

# Use landscape raycasting to get height at any (X, Y)
# Landscape has a method to get height at location
landscape = canonical

# Function to get Z at (X, Y) using landscape collision
def get_landscape_z(x, y):
    """Raycast down to find landscape Z at (X, Y)."""
    # Start high above and raycast down
    start_z = 25000  # Well above landscape
    end_z = -10000   # Well below
    
    # Use line trace
    hit = unreal.SystemLibrary.line_trace_single(
        unreal.EditorLevelLibrary.get_editor_world(),
        unreal.Vector(x, y, start_z),
        unreal.Vector(x, y, end_z),
        unreal.DrawDebugType.NONE,
        True,  # trace complex
        [],    # actors to ignore
        unreal.CollisionChannel.Visibility
    )
    
    if hit and hit.get_editor_property("bBlockingHit"):
        impact = hit.get_editor_property("ImpactPoint")
        return impact.z
    
    # Fallback: use actor location Z + offset
    loc = landscape.get_actor_location()
    return loc.z

# Test height at center
center_z = get_landscape_z(CX, CY)
print(f"Landscape Z at center (0,0): {center_z:.0f}")

# Test at a few points
test_points = [
    (1000, 0),
    (0, 1000),
    (-1000, 0),
    (0, -1000),
    (2000, 2000),
]
for px, py in test_points:
    z = get_landscape_z(px, py)
    print(f"  Z at ({px},{py}): {z:.0f}")

print(f"\nCanonicalLandscape actor Z: {canonical.get_actor_location().z:.0f}")
