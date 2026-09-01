import unreal
import json
import math
import random

# ============================================================
# WISE PCG: Native Monolith scatter + manual placement
# Delete 4 silent PCG volumes, scatter meshes directly
# ============================================================

# First, get the bounds of the cathedral area
CX, CY, CZ = 0, 0, 13405

# Get all existing actors to understand the level
actors = unreal.EditorLevelLibrary.get_all_level_actors()
sma_count = sum(1 for a in actors if type(a).__name__ == 'StaticMeshActor')
pcg_count = sum(1 for a in actors if type(a).__name__ == 'PCGVolume')
print(f"Before: {sma_count} StaticMeshActors, {pcg_count} PCGVolumes")

# Kitbash pieces (verified to exist)
kitbash = [
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Altar.SM_Cathedral_Altar",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Buttress.SM_Cathedral_Buttress",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chapel.SM_Cathedral_Chapel",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chandelier.SM_Cathedral_Chandelier",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Wall.SM_Cathedral_Wall",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_WallParapet.SM_Cathedral_WallParapet",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TraceryPanel.SM_Cathedral_TraceryPanel",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Pier.SM_Cathedral_Pier",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Tower.SM_Cathedral_Tower",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_RoseWindow.SM_Cathedral_RoseWindow",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedGlassPanel.SM_Cathedral_StainedGlassPanel",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Garland.SM_Cathedral_Garland",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_HarmonicOrb.SM_Cathedral_HarmonicOrb",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_LancetWindow.SM_Cathedral_LancetWindow",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedRose.SM_Cathedral_StainedRose",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TrebleRelief.SM_Cathedral_TrebleRelief",
]

# Houdini pieces
houdini = [
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_6Bays_Harmony.SM_P4_Cathedral_Crystal_6Bays_Harmony",
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Fractal_6Bays_Harmony.SM_P4_Cathedral_Fractal_6Bays_Harmony",
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_RoseWindow_6Bays.SM_P4_Cathedral_RoseWindow_6Bays",
]

all_meshes = kitbash + houdini
random.seed(2026)

placed = 0
for i, mesh_path in enumerate(all_meshes):
    angle = (i / len(all_meshes)) * 2 * math.pi
    radius = 3000 + random.uniform(-500, 500)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + random.uniform(-500, 1500)
    yaw = random.uniform(0, 360)
    scale = random.uniform(1.5, 3.0)
    
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        continue
    
    loc = unreal.Vector(x, y, z)
    rot = unreal.Rotator(0, 0, yaw)
    scl = unreal.Vector(scale, scale, scale)
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        placed += 1

print(f"Placed {placed} pieces")

# Verify
actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
sma_after = sum(1 for a in actors_after if type(a).__name__ == 'StaticMeshActor')
print(f"After: {sma_after} StaticMeshActors")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
