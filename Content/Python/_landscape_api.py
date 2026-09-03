import unreal

# ============================================================
# HEIGHT-AWARE PLACEMENT - Using Landscape collision directly
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

print(f"Landscape: {landscape.get_actor_label()} at Z={landscape.get_actor_location().z:.0f}")

# Use landscape collision interface
# Landscape has a method to get height at location
# Try using the landscape proxy
landscape_proxy = landscape.get_editor_property("landscape_proxy")
print(f"Landscape proxy: {landscape_proxy}")

# Try to get height data from landscape
# Landscape has GetHeightAtLocation method
try:
    # Get height at (0, 0)
    height = landscape.get_height_at_location(unreal.Vector(0, 0, 0))
    print(f"Height at (0,0): {height:.0f}")
except Exception as e:
    print(f"get_height_at_location failed: {e}")

# Try using landscape collision component
collision = landscape.get_component_by_class(unreal.LandscapeHeightfieldCollisionComponent)
if collision:
    print(f"Collision component found")
    # Get collision height
    height = collision.get_editor_property("collision_height")
    print(f"Collision height: {height}")
else:
    print("No collision component")

# Try using landscape info
info = landscape.get_editor_property("landscape_info")
if info:
    print(f"Landscape info: {info}")
    # Get bounds from info
    bounds = info.get_editor_property("bounds")
    print(f"Info bounds: {bounds}")
