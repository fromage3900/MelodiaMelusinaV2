import unreal
import json
import math
import random

# ============================================================
# HEIGHT-AWARE ATLANTIS PLACEMENT (respects landscape)
# ============================================================

random.seed(2026)

actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find landscape
landscape = None
for a in actors:
    if "CanonicalLandscape" in a.get_actor_label():
        landscape = a
        break

landscape_z = landscape.get_actor_location().z
print(f"Landscape Z: {landscape_z:.0f}")

# Copernicus MIs
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
mis = [m for m in mis if "MI_Copernicus_" in m]

def pick_mi(mesh_name):
    if "Arch" in mesh_name or "Column" in mesh_name:
        return next((m for m in mis if "CavernWeave" in m or "ChoirStone" in m), mis[0])
    elif "Bench" in mesh_name or "Chair" in mesh_name or "Table" in mesh_name or "Stool" in mesh_name:
        return next((m for m in mis if "PearlWeave" in m or "SingingSilk" in m), mis[2])
    elif "Tree" in mesh_name or "Shrub" in mesh_name or "Ivy" in mesh_name:
        return next((m for m in mis if "FrostBloom" in m or "FrozenFracture" in m), mis[1])
    else:
        return mis[random.randint(0, len(mis)-1)]

def place_mesh(mesh_path, location, rotation=None, scale=None):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        return None
    loc = unreal.Vector(location[0], location[1], location[2])
    rot = unreal.Rotator(0, 0, 0) if rotation is None else unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scl = unreal.Vector(1, 1, 1) if scale is None else unreal.Vector(scale[0], scale[1], scale[2])
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        mi_path = pick_mi(mesh_path.split('/')[-1])
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        if mi:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("override_materials", [mi])
        return actor
    return None

# Atlantis meshes
atlantis_arches = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchB.SM_ATL_Palace_ArchB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchC.SM_ATL_Palace_ArchC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchD.SM_ATL_Palace_ArchD",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchE.SM_ATL_Palace_ArchE",
]

atlantis_columns = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsA.SM_ATL_Palace_ColumnsA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsB.SM_ATL_Palace_ColumnsB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsC.SM_ATL_Palace_ColumnsC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ColumnsD.SM_ATL_Palace_ColumnsD",
]

atlantis_seating = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchA.SM_ATL_Palace_BenchA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchB.SM_ATL_Palace_BenchB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_BenchC.SM_ATL_Palace_BenchC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableA.SM_ATL_Palace_TableA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TableB.SM_ATL_Palace_TableB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ChairA.SM_ATL_Palace_ChairA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ChairB.SM_ATL_Palace_ChairB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolA.SM_ATL_Palace_StoolA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolB.SM_ATL_Palace_StoolB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_StoolC.SM_ATL_Palace_StoolC",
]

atlantis_nature = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeA.SM_ATL_Palace_TreeA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeB.SM_ATL_Palace_TreeB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeC.SM_ATL_Palace_TreeC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeD.SM_ATL_Palace_TreeD",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_TreeE.SM_ATL_Palace_TreeE",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsA.SM_ATL_Palace_ShrubsA",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsB.SM_ATL_Palace_ShrubsB",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsC.SM_ATL_Palace_ShrubsC",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsD.SM_ATL_Palace_ShrubsD",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ShrubsE.SM_ATL_Palace_ShrubsE",
]

CX, CY = 0, 0
base_z = landscape_z + 50

total = 0

# Zone 1: Processional (front of cathedral, -Y)
print("--- Processional Arches ---")
for i, mesh in enumerate(atlantis_arches):
    x = CX + (i - len(atlantis_arches)/2) * 600
    y = CY - 3500 - i * 200
    scale = random.uniform(2.5, 4.0)
    place_mesh(mesh, (x, y, base_z), rotation=(0, 0, 0), scale=(scale, scale, scale))
    total += 1

# Zone 2: Plaza seating (near cathedral, -Y)
print("--- Plaza Seating ---")
for i, mesh in enumerate(atlantis_seating):
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(0, 1000)
    x = CX + math.cos(angle) * radius
    y = CY - 2000 + math.sin(angle) * radius
    scale = random.uniform(1.5, 3.0)
    yaw = random.uniform(0, 360)
    place_mesh(mesh, (x, y, base_z), rotation=(0, 0, yaw), scale=(scale, scale, scale))
    total += 1

# Zone 3: Water's edge (far radius)
print("--- Water's Edge ---")
for i, mesh in enumerate(atlantis_nature):
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(4000, 6000)
    x = CX + math.cos(angle) * radius
    y = CY + math.sin(angle) * radius
    scale = random.uniform(2.0, 4.0)
    place_mesh(mesh, (x, y, base_z), scale=(scale, scale, scale))
    total += 1

# Zone 4: Columns (flanking, ±X)
print("--- Columned Courtyard ---")
for i, mesh in enumerate(atlantis_columns):
    side = 1 if i % 2 == 0 else -1
    x = CX + side * (2000 + (i // 2) * 500)
    y = CY + random.uniform(-1500, 1500)
    scale = random.uniform(2.5, 4.0)
    place_mesh(mesh, (x, y, base_z), scale=(scale, scale, scale))
    total += 1

print(f"\nTotal Atlantis pieces placed: {total}")

unreal.EditorLevelLibrary.save_current_level()
print("Level saved.")
