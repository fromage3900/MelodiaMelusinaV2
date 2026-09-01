import unreal
import json
import os

# ============================================================
# GAEA TERRAIN PLACEMENT + WALKABLE HEATMAP REVIEW
# ============================================================

# Load Gaea mesh
gaea_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea = unreal.EditorAssetLibrary.load_asset(gaea_path)

if gaea is None:
    print("[FATAL] Gaea mesh not found")
    exit()

# Load Gaea MI
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)

# Place Gaea terrain in level
# Gaea is 5000x3000m at Z=327, scale 100x (1 meter = 100 UE units)
# Cathedral is at Z=13405, so we need to place Gaea below it

gaea_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    gaea,
    unreal.Vector(0, 0, 0),  # Place at origin
    unreal.Rotator(0, 0, 0)
)

if gaea_actor:
    # Scale to match UE units (100x for meters to cm)
    gaea_actor.set_actor_scale3d(unreal.Vector(100, 100, 100))
    gaea_actor.set_actor_label("Gaea_LiquidCathedral_Terrain")
    print(f"Placed Gaea terrain: {gaea_actor.get_actor_label()}")
    
    # Apply Gaea MI
    if gaea_mi:
        comp = gaea_actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_editor_property("override_materials", [gaea_mi])
            print(f"Applied Gaea MI")
else:
    print("[FAIL] Could not place Gaea terrain")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
