import unreal
import json

# ============================================================
# GAEA TERRAIN: Reposition to match Sea Above coordinate space
# Cathedral base: Z=13405, area ~5000 radius
# Gaea terrain: 5000x3000m, Z range 147-508m
# Scale: 1x (5000 UE units), Z offset: 13405 - 147 = 13258
# ============================================================

# Delete existing Gaea
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if 'Gaea' in a.get_actor_label():
        unreal.EditorLevelLibrary.destroy_actor(a)
        print(f"Deleted: {a.get_actor_label()}")

# Reload Gaea mesh
gaea_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/SM_Gaea_LiquidCathedral_1025.SM_Gaea_LiquidCathedral_1025"
gaea = unreal.EditorAssetLibrary.load_asset(gaea_path)
gaea_mi_path = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate.MI_Gaea_LiquidCathedral_Substrate"
gaea_mi = unreal.EditorAssetLibrary.load_asset(gaea_mi_path)

# Place at 1x scale, centered at cathedral XY, Z offset to match base
gaea_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    gaea,
    unreal.Vector(0, 0, 13258),  # Z offset so terrain surface ~13405
    unreal.Rotator(0, 0, 0)
)

if gaea_actor:
    gaea_actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    gaea_actor.set_actor_label("Gaea_LiquidCathedral_Terrain")
    print(f"Placed Gaea at 1x scale, Z=13258")
    
    if gaea_mi:
        comp = gaea_actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_editor_property("override_materials", [gaea_mi])
            print("Applied Gaea MI")
else:
    print("[FAIL] Could not place Gaea")

unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
