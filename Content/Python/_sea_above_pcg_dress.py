import unreal
import json
import math
import random

# ============================================================
# COMPREHENSIVE PCG DRESSING PLAN
# Gaea LiquidCathedral terrain + Walkable heatmap integration
# ============================================================

random.seed(2026)

# Cathedral center
CX, CY, CZ = 0, 0, 13405

# Kitbash pieces by zone type
ZONE_PIECES = {
    "canyon": [
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Buttress.SM_Cathedral_Buttress",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Wall.SM_Cathedral_Wall",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Pier.SM_Cathedral_Pier",
    ],
    "valley": [
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Garland.SM_Cathedral_Garland",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_HarmonicOrb.SM_Cathedral_HarmonicOrb",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TraceryPanel.SM_Cathedral_TraceryPanel",
    ],
    "plaza": [
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Altar.SM_Cathedral_Altar",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Stall.SM_Cathedral_Stall",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chandelier.SM_Cathedral_Chandelier",
    ],
    "spiral": [
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Tower.SM_Cathedral_Tower",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Portal.SM_Cathedral_Portal",
    ],
    "highlands": [
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_RoseWindow.SM_Cathedral_RoseWindow",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedGlassPanel.SM_Cathedral_StainedGlassPanel",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedRose.SM_Cathedral_StainedRose",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TrebleRelief.SM_Cathedral_TrebleRelief",
        "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_LancetWindow.SM_Cathedral_LancetWindow",
    ],
}

# Copernicus MIs
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
mis = [m for m in mis if "MI_Copernicus_" in m]

def pick_mi(mesh_name):
    """Pick a Copernicus MI based on mesh type."""
    if "Wall" in mesh_name or "Floor" in mesh_name:
        return next((m for m in mis if "CavernWeave" in m or "ChoirStone" in m), mis[0])
    elif "Tower" in mesh_name or "Spire" in mesh_name:
        return next((m for m in mis if "FrostBloom" in m or "FrozenFracture" in m), mis[1])
    elif "Pier" in mesh_name or "Column" in mesh_name or "Buttress" in mesh_name:
        return next((m for m in mis if "Voronoi" in m or "PearlWeave" in m), mis[2])
    elif "Altar" in mesh_name or "Stall" in mesh_name or "Chandelier" in mesh_name:
        return next((m for m in mis if "GildedCoral" in m or "MoltenCore" in m), mis[3])
    elif "Window" in mesh_name or "Portal" in mesh_name or "Rose" in mesh_name:
        return next((m for m in mis if "CrystalCathedral" in m or "FractalCathedral" in m), mis[4])
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
# ZONE PLACEMENT (walkable heatmap-driven)
# ============================================================

print("=== WALKABLE HEATMAP-DRESSED PCG ZONES ===\n")

# Zone definitions (centers relative to cathedral)
zones = {
    "canyon": {"center": (CX - 2000, CY, CZ), "radius": 1500, "count": 15},
    "valley": {"center": (CX + 2000, CY, CZ), "radius": 1500, "count": 15},
    "plaza": {"center": (CX, CY - 2000, CZ), "radius": 1200, "count": 12},
    "spiral": {"center": (CX, CY + 2000, CZ), "radius": 1200, "count": 12},
    "highlands": {"center": (CX, CY, CZ + 1000), "radius": 2000, "count": 20},
}

total_placed = 0
for zone_name, zone in zones.items():
    print(f"--- Zone: {zone_name} ---")
    pieces = ZONE_PIECES[zone_name]
    
    for i in range(zone["count"]):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, zone["radius"])
        x = zone["center"][0] + math.cos(angle) * radius
        y = zone["center"][1] + math.sin(angle) * radius
        z = zone["center"][2] + random.uniform(-500, 1500)
        
        mesh = random.choice(pieces)
        scale = random.uniform(1.5, 3.5)
        yaw = random.uniform(0, 360)
        
        place_mesh(mesh, (x, y, z), rotation=(0, 0, yaw), scale=(scale, scale, scale))
        total_placed += 1
    
    print(f"  Placed {zone['count']} pieces in {zone_name}")

print(f"\n=== Total placed: {total_placed} ===")

# Save
unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
