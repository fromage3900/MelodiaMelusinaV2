import unreal
import json
import os

# ============================================================
# FINAL REVIEW: Count everything in the level
# ============================================================

actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma_actors = [a for a in actors if type(a).__name__ == 'StaticMeshActor']
pcg_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume']

print(f"Total actors: {len(actors)}")
print(f"StaticMeshActors: {len(sma_actors)}")
print(f"PCGVolumes: {len(pcg_volumes)}")

# Count PCG instances
pcg_instances = 0
for vol in pcg_volumes:
    isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
    for ism in isms:
        pcg_instances += ism.get_instance_count()

print(f"PCG-generated instances: {pcg_instances}")

# Count Copernicus MIs applied
mi_count = 0
for a in sma_actors:
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        mats = comp.get_editor_property("override_materials")
        if mats and len(mats) > 0:
            mi_count += 1

print(f"Actors with Copernicus MIs: {mi_count}")

# Copernicus texture count
TEXTURE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\copernicus_cymatic"
variant_count = len([d for d in os.listdir(TEXTURE_DIR) if os.path.isdir(os.path.join(TEXTURE_DIR, d))])
print(f"Copernicus variants: {variant_count}")

# MI count
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
mis = [m for m in mis if "MI_Copernicus_" in m]
print(f"Material Instances: {len(mis)}")

print("\n=== FINAL SUMMARY ===")
print(f"Direct placement actors: {len(sma_actors)}")
print(f"PCG-generated instances: {pcg_instances}")
print(f"Total cathedral pieces: {len(sma_actors) + pcg_instances}")
print(f"Copernicus materials applied: {mi_count}")
print(f"Copernicus MIs: {len(mis)}")
print(f"PCG Volumes (active): {len(pcg_volumes)}")
