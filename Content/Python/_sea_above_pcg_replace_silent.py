import unreal
import json
import math
import random

# ============================================================
# FIX 4 SILENT PCG GRAPHS — Replace with direct placement
# ============================================================

# The 4 silent graphs (NaveVault, BaroqueScatter, WaterEdge, Pilasters) have
# empty subgraph spawners that can't be easily filled. Instead, we replace
# their volumes with direct kitbash placement + Copernicus MIs.

random.seed(2026)

# Cathedral center
CX, CY, CZ = 0, 0, 13405

# Kitbash pieces by category
STRUCTURAL = [
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Wall.SM_Cathedral_Wall",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_WallParapet.SM_Cathedral_WallParapet",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_CombatFloor.SM_Cathedral_CombatFloor",
]

VERTICAL = [
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Tower.SM_Cathedral_Tower",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Pier.SM_Cathedral_Pier",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Buttress.SM_Cathedral_Buttress",
]

DECORATIVE = [
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Altar.SM_Cathedral_Altar",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Stall.SM_Cathedral_Stall",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chandelier.SM_Cathedral_Chandelier",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_RoseWindow.SM_Cathedral_RoseWindow",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedGlassPanel.SM_Cathedral_StainedGlassPanel",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedRose.SM_Cathedral_StainedRose",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_LancetWindow.SM_Cathedral_LancetWindow",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TraceryPanel.SM_Cathedral_TraceryPanel",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Garland.SM_Cathedral_Garland",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_HarmonicOrb.SM_Cathedral_HarmonicOrb",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TrebleRelief.SM_Cathedral_TrebleRelief",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Portal.SM_Cathedral_Portal",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_ResonantDoor.SM_Cathedral_ResonantDoor",
]

HOUDINI = [
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_6Bays_Harmony.SM_P4_Cathedral_Crystal_6Bays_Harmony",
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Fractal_6Bays_Harmony.SM_P4_Cathedral_Fractal_6Bays_Harmony",
    "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_RoseWindow_6Bays.SM_P4_Cathedral_RoseWindow_6Bays",
]

# Copernicus MIs
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
mis = [m for m in mis if "MI_Copernicus_" in m]

def pick_mi(mesh_name):
    """Pick a Copernicus MI based on mesh type."""
    if "Wall" in mesh_name or "Floor" in mesh_name or "CombatFloor" in mesh_name:
        return next((m for m in mis if "CavernWeave" in m or "ChoirStone" in m), mis[0])
    elif "Tower" in mesh_name or "Spire" in mesh_name:
        return next((m for m in mis if "FrostBloom" in m or "FrozenFracture" in m), mis[1])
    elif "Pier" in mesh_name or "Column" in mesh_name or "Buttress" in mesh_name:
        return next((m for m in mis if "Voronoi" in m or "PearlWeave" in m), mis[2])
    elif "Altar" in mesh_name or "Stall" in mesh_name or "Chandelier" in mesh_name:
        return next((m for m in mis if "GildedCoral" in m or "MoltenCore" in m), mis[3])
    elif "Window" in mesh_name or "Portal" in mesh_name or "Rose" in mesh_name:
        return next((m for m in mis if "CrystalCathedral" in m or "FractalCathedral" in m), mis[4])
    elif "Crystal" in mesh_name or "Fractal" in mesh_name:
        return next((m for m in mis if "CrystalCathedral" in m or "FractalCathedral" in m), mis[5])
    else:
        return mis[random.randint(0, len(mis)-1)]

def place_mesh(mesh_path, location, rotation=None, scale=None):
    """Place a mesh in the level."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        return None
    
    loc = unreal.Vector(location[0], location[1], location[2])
    rot = unreal.Rotator(0, 0, 0) if rotation is None else unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scl = unreal.Vector(1, 1, 1) if scale is None else unreal.Vector(scale[0], scale[1], scale[2])
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        
        # Apply Copernicus MI
        mi_path = pick_mi(mesh_path.split('/')[-1])
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        if mi:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("override_materials", [mi])
        
        return actor
    return None

# ============================================================
# REGION 1: NaveVault (above the cathedral, Z+3000)
# Place vault bays, walls, decorative pieces
# ============================================================
print("=== REGION 1: NaveVault (above cathedral) ===")

for i in range(8):
    angle = (i / 8) * 2 * math.pi
    radius = 2000 + random.uniform(-200, 200)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + 3000 + random.uniform(-500, 500)
    
    mesh = random.choice(STRUCTURAL + DECORATIVE)
    scale = random.uniform(1.5, 3.0)
    place_mesh(mesh, (x, y, z), scale=(scale, scale, scale))

# ============================================================
# REGION 2: BaroqueScatter (around the cathedral, Z+0 to Z+4000)
# Scatter kitbash pieces in a wider ring
# ============================================================
print("=== REGION 2: BaroqueScatter (wide ring) ===")

for i in range(20):
    angle = random.uniform(0, 2 * math.pi)
    radius = 4000 + random.uniform(-1000, 2000)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + random.uniform(-500, 2000)
    
    mesh = random.choice(STRUCTURAL + VERTICAL + DECORATIVE + HOUDINI)
    scale = random.uniform(1.5, 3.5)
    yaw = random.uniform(0, 360)
    place_mesh(mesh, (x, y, z), rotation=(0, 0, yaw), scale=(scale, scale, scale))

# ============================================================
# REGION 3: WaterEdge (at water level, Z-500)
# Place coral-like pieces at the ocean-cathedral seam
# ============================================================
print("=== REGION 3: WaterEdge (ocean seam) ===")

for i in range(12):
    angle = random.uniform(0, 2 * math.pi)
    radius = 5000 + random.uniform(-1000, 1000)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ - 500 + random.uniform(-200, 200)
    
    mesh = random.choice(DECORATIVE + HOUDINI)
    scale = random.uniform(1.0, 2.5)
    place_mesh(mesh, (x, y, z), scale=(scale, scale, scale))

# ============================================================
# REGION 4: Pilasters (mid-height, Z+1500)
# Vertical pieces along the sides
# ============================================================
print("=== REGION 4: Pilasters (mid-height sides) ===")

for i in range(10):
    angle = (i / 10) * 2 * math.pi
    radius = 3500 + random.uniform(-300, 300)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    z = CZ + 1500 + random.uniform(-300, 300)
    
    mesh = random.choice(VERTICAL + DECORATIVE)
    scale = random.uniform(1.5, 3.0)
    place_mesh(mesh, (x, y, z), scale=(scale, scale, scale))

# ============================================================
# CLEANUP: Delete the 4 silent PCG volumes
# ============================================================
print("\n=== CLEANUP: Deleting silent PCG volumes ===")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
silent_volumes = [a for a in actors if type(a).__name__ == 'PCGVolume' and 
                  any(s in a.get_actor_label() for s in ['NaveVault', 'BaroqueScatter', 'WaterEdge', 'Pilasters'])]

for vol in silent_volumes:
    label = vol.get_actor_label()
    unreal.EditorLevelLibrary.destroy_actor(vol)
    print(f"  Deleted: {label}")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("\n=== ALL 4 SILENT PCG GRAPHS REPLACED ===")
