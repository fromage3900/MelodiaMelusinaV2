import unreal
import json
import math

# ============================================================
# PHASE 2: Place Crystal Cathedral + kitbash in Sea Above
# Center: (0, 0, 13405) — the BP_Starskiff location, open water
# ============================================================

def place_actor(mesh_path, location, rotation=None, scale=None, label=""):
    """Spawn a static mesh actor in the editor world."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        print(f"[FAIL] Could not load mesh: {mesh_path}")
        return None
    
    world = unreal.EditorLevelLibrary.get_editor_world()
    loc = unreal.Vector(location[0], location[1], location[2])
    rot = unreal.Rotator(0, 0, 0) if rotation is None else unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scl = unreal.Vector(1, 1, 1) if scale is None else unreal.Vector(scale[0], scale[1], scale[2])
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        name = label or mesh_path.split('/')[-1]
        print(f"[OK] {name:40s} @[{location[0]:.0f},{location[1]:.0f},{location[2]:.0f}]")
        return actor
    else:
        print(f"[FAIL] Could not spawn {mesh_path}")
        return None

CATHEDRAL = "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_6Bays_Harmony.SM_P4_Cathedral_Crystal_6Bays_Harmony"
ROSE = "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_RoseWindow_6Bays.SM_P4_Cathedral_RoseWindow_6Bays"
FRACTAL = "/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Fractal_6Bays_Harmony.SM_P4_Cathedral_Fractal_6Bays_Harmony"

# Kitbash pieces
KITBASH_BASE = "/Game/EnvSandbox/Meshes/Cathedral/"
ALTAR = f"{KITBASH_BASE}SM_Cathedral_Altar.SM_Cathedral_Altar"
SPIRE = f"{KITBASH_BASE}SM_Cathedral_Spire.SM_Cathedral_Spire"
BUTTRESS = f"{KITBASH_BASE}SM_Cathedral_Buttress.SM_Cathedral_Buttress"
CHAPEL = f"{KITBASH_BASE}SM_Cathedral_Chapel.SM_Cathedral_Chapel"
LANCET = f"{KITBASH_BASE}SM_Cathedral_LancetWindow.SM_Cathedral_LancetWindow"
CHANDELIER = f"{KITBASH_BASE}SM_Cathedral_Chandelier.SM_Cathedral_Chandelier"
VAULT = f"{KITBASH_BASE}SM_Cathedral_VaultBay.SM_Cathedral_VaultBay"
WALL = f"{KITBASH_BASE}SM_Cathedral_Wall.SM_Cathedral_Wall"
PARAPET = f"{KITBASH_BASE}SM_Cathedral_WallParapet.SM_Cathedral_WallParapet"
TRACERY = f"{KITBASH_BASE}SM_Cathedral_TraceryPanel.SM_Cathedral_TraceryPanel"
PILLAR = f"{KITBASH_BASE}SM_Cathedral_Pier.SM_Cathedral_Pier"
STAIRS = f"{KITBASH_BASE}SM_Cathedral_SpiralStairs.SM_Cathedral_SpiralStairs"
TOWER = f"{KITBASH_BASE}SM_Cathedral_Tower.SM_Cathedral_Tower"
ROSE_KIT = f"{KITBASH_BASE}SM_Cathedral_RoseWindow.SM_Cathedral_RoseWindow"
STAINED = f"{KITBASH_BASE}SM_Cathedral_StainedGlassPanel.SM_Cathedral_StainedGlassPanel"
GARLAND = f"{KITBASH_BASE}SM_Cathedral_Garland.SM_Cathedral_Garland"
HARMONIC_ORB = f"{KITBASH_BASE}SM_Cathedral_HarmonicOrb.SM_Cathedral_HarmonicOrb"
MUSIC_ORB = f"{KITBASH_BASE}SM_Cathedral_MusicOrb.SM_Cathedral_MusicOrb"

# Center of Sea Above (water level ~13405)
CX, CY, CZ = 0, 0, 13405

print("\n=== PHASE 2: Placing Crystal Cathedral Nave (Hero) ===\n")

# Hero: Crystal Cathedral Nave 6-Bay, scaled up 3x
place_actor(CATHEDRAL, (CX, CY, CZ), scale=(3, 3, 3), label="Crystal Nave 6-Bay (Hero)")

# Rose windows flanking
place_actor(ROSE, (CX-1500, CY-500, CZ+500), scale=(2, 2, 2), label="Rose Window L")
place_actor(ROSE, (CX+1500, CY-500, CZ+500), scale=(2, 2, 2), label="Rose Window R")

# Fractal naves as side aisles
place_actor(FRACTAL, (CX-2500, CY, CZ), scale=(2, 2, 2), label="Fractal Aisle L")
place_actor(FRACTAL, (CX+2500, CY, CZ), scale=(2, 2, 2), label="Fractal Aisle R")

# Altar at the end
place_actor(ALTAR, (CX, CY-3000, CZ+200), scale=(2, 2, 2), label="Altar")

# Spires at corners
place_actor(SPIRE, (CX-2000, CY-2000, CZ), scale=(2, 2, 2), label="Spire FL")
place_actor(SPIRE, (CX+2000, CY-2000, CZ), scale=(2, 2, 2), label="Spire FR")
place_actor(SPIRE, (CX-2000, CY+2000, CZ), scale=(2, 2, 2), label="Spire BL")
place_actor(SPIRE, (CX+2000, CY+2000, CZ), scale=(2, 2, 2), label="Spire BR")

# Buttresses along sides
for i in range(4):
    z_off = CZ - 1000 + i * 600
    place_actor(BUTTRESS, (CX-1800, CY, z_off), scale=(1.5, 1.5, 1.5), label=f"Buttress L{i}")
    place_actor(BUTTRESS, (CX+1800, CY, z_off), scale=(1.5, 1.5, 1.5), label=f"Buttress R{i}")

# Chapel behind altar
place_actor(CHAPEL, (CX, CY-4000, CZ+500), scale=(2, 2, 2), label="Chapel")

# Chandeliers inside
place_actor(CHANDELIER, (CX-500, CY-500, CZ+1500), scale=(2, 2, 2), label="Chandelier 1")
place_actor(CHANDELIER, (CX+500, CY-500, CZ+1500), scale=(2, 2, 2), label="Chandelier 2")
place_actor(CHANDELIER, (CX, CY-1500, CZ+1500), scale=(2, 2, 2), label="Chandelier 3")

# Vault bays above
for i in range(3):
    place_actor(VAULT, (CX, CY-1000+i*1000, CZ+2000), scale=(2, 2, 2), label=f"Vault {i}")

# Walls
place_actor(WALL, (CX-3000, CY, CZ), scale=(2, 2, 2), label="Wall L")
place_actor(WALL, (CX+3000, CY, CZ), scale=(2, 2, 2), label="Wall R")

# Parapets on top
place_actor(PARAPET, (CX-3000, CY, CZ+1500), scale=(2, 2, 2), label="Parapet L")
place_actor(PARAPET, (CX+3000, CY, CZ+1500), scale=(2, 2, 2), label="Parapet R")

# Tracery panels
place_actor(TRACERY, (CX-2500, CY-1000, CZ+1000), scale=(1.5, 1.5, 1.5), label="Tracery L")
place_actor(TRACERY, (CX+2500, CY-1000, CZ+1000), scale=(1.5, 1.5, 1.5), label="Tracery R")

# Towers at front
place_actor(TOWER, (CX-3500, CY+3000, CZ), scale=(2, 2, 2), label="Tower BL")
place_actor(TOWER, (CX+3500, CY+3000, CZ), scale=(2, 2, 2), label="Tower BR")

# Stained glass panels
for i in range(4):
    place_actor(STAINED, (CX-2000, CY-500+i*500, CZ+800), scale=(1.5, 1.5, 1.5), label=f"Stained L{i}")
    place_actor(STAINED, (CX+2000, CY-500+i*500, CZ+800), scale=(1.5, 1.5, 1.5), label=f"Stained R{i}")

# Harmonic orbs (floating)
place_actor(HARMONIC_ORB, (CX-1000, CY-1000, CZ+2500), scale=(2, 2, 2), label="Harmonic Orb 1")
place_actor(HARMONIC_ORB, (CX+1000, CY-1000, CZ+2500), scale=(2, 2, 2), label="Harmonic Orb 2")
place_actor(MUSIC_ORB, (CX, CY-2000, CZ+2500), scale=(2, 2, 2), label="Music Orb")

# Garlands
place_actor(GARLAND, (CX-1500, CY+500, CZ+1200), scale=(1.5, 1.5, 1.5), label="Garland L")
place_actor(GARLAND, (CX+1500, CY+500, CZ+1200), scale=(1.5, 1.5, 1.5), label="Garland R")

# Stairs leading up
place_actor(STAIRS, (CX, CY+2000, CZ-500), scale=(2, 2, 2), label="Spiral Stairs")

print("\n=== PHASE 2 complete ===\n")
