"""ZunZun Studio ΓÇö Blender setup script for all ZunZun family character models.

Creates a studio layout with all available models imported and arranged.
Run from Blender's Scripting workspace or via command line:

  blender --factory-startup -P setup_zunzun_studio.py

Requires:
  - VRM Importer addon (for .vrm files): https://github.com/saturday06/VRM-Addon-for-Blender
  - MMD Tools addon (for .pmx files): https://github.com/UuuNyaa/blender_mmd_tools

Saves: G:/EnvironmentPortfolio/BS_GodFile/KitbashExport/ZunZun_studio.blend
"""

import bpy
import os
from pathlib import Path

# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Configuration
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

OUTPUT_PATH = Path(r"G:\EnvironmentPortfolio\BS_GodFile\KitbashExport\ZunZun_studio.blend")

# Character models to import
CHARACTERS = [
    # Zundamon ΓÇö the mochi fairy
    {
        "name": "Zundamon",
        "path": Path(r"F:\Inbox\Downloads_Sweep_2026-07-11\Unzipped_Repos\Zundamon\Zundamon.vrm"),
        "type": "vrm",
        "position": (0, 0, 0),
        "scale": 1.0,
        "label": "Questkeeper / Shopkeeper / Party",
        "role": "First NPC ΓÇö quest hub",
    },
    # VRoidHub characters as stand-ins for ZunZun family
    {
        "name": "Zunko_StandIn",
        "path": Path(r"G:\EnvironmentPortfolio\BS_GodFile\Content\NPCs\VRM_Sources\VRoidHub\SD_02_PetalPriestess.vrm"),
        "type": "vrm",
        "position": (3, 0, 0),
        "scale": 1.0,
        "label": "Town Elder / Healer / Party",
        "role": "Tohoku Zunko stand-in ΓÇö replace with Zunko VRM when downloaded",
    },
    {
        "name": "Kiritan_StandIn",
        "path": Path(r"G:\EnvironmentPortfolio\BS_GodFile\Content\NPCs\VRM_Sources\VRoidHub\MD_01_TwilightDancer.vrm"),
        "type": "vrm",
        "position": (6, 0, 0),
        "scale": 1.0,
        "label": "Blacksmith / DPS / Party",
        "role": "Tohoku Kiritan stand-in ΓÇö replace with Kiritan VRM when downloaded",
    },
    {
        "name": "Itako_StandIn",
        "path": Path(r"G:\EnvironmentPortfolio\BS_GodFile\Content\NPCs\VRM_Sources\VRoidHub\CW_01_StarWeaver.vrm"),
        "type": "vrm",
        "position": (9, 0, 0),
        "scale": 1.0,
        "label": "Spirit Guide / Mage / Party",
        "role": "Tohoku Itako stand-in ΓÇö replace with Itako VRM when downloaded",
    },
    # Metan, Sora, Tsurugi ΓÇö no models yet, use placeholder cubes with labels
    {
        "name": "Metan_Placeholder",
        "type": "placeholder",
        "position": (12, 0, 0),
        "color": (0.9, 0.3, 0.3),
        "label": "Alchemist / Elemental / Party",
        "role": "Shikoku Metan ΓÇö needs VRM download",
    },
    {
        "name": "Sora_Placeholder",
        "type": "placeholder",
        "position": (15, 0, 0),
        "color": (0.3, 0.3, 0.9),
        "label": "Bard / Rhythm Host / Party",
        "role": "Kyushu Sora ΓÇö needs VRM download",
    },
    {
        "name": "Tsurugi_Placeholder",
        "type": "placeholder",
        "position": (18, 0, 0),
        "color": (0.5, 0.5, 0.5),
        "label": "Arena Master / Tank / Party",
        "role": "Chubu Tsurugi ΓÇö needs VRM download",
    },
]

# Also import Melusina model if available
MELUSINA_FBX = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Exports\SK_Melusina_FIXED.fbx")

# Zundapal building (enemy character)
ZUNDAPAL_BLEND = Path(r"G:\ZUNDYMONSKITCHEN\zundapalupdate4.blend")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Import functions
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def import_vrm(filepath: Path) -> list:
    """Import a VRM file. Returns list of imported objects."""
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return []

    print(f"  Importing VRM: {filepath.name}...")
    try:
        bpy.ops.import_scene.vrm(filepath=str(filepath))
        # Return newly imported objects
        return [o for o in bpy.context.selected_objects]
    except AttributeError:
        print(f"  WARNING: VRM Importer addon not installed!")
        print(f"  Install: https://github.com/saturday06/VRM-Addon-for-Blender")
        return []
    except Exception as e:
        print(f"  ERROR importing VRM: {e}")
        return []


def import_fbx(filepath: Path) -> list:
    """Import an FBX file."""
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return []

    print(f"  Importing FBX: {filepath.name}...")
    try:
        bpy.ops.import_scene.fbx(filepath=str(filepath))
        return [o for o in bpy.context.selected_objects]
    except Exception as e:
        print(f"  ERROR importing FBX: {e}")
        return []


def import_pmx(filepath: Path) -> list:
    """Import a PMX/MMD file using MMD Tools."""
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return []

    print(f"  Importing PMX: {filepath.name}...")
    try:
        bpy.ops.mmd_tools.import_model(
            filepath=str(filepath),
            scale=0.08,  # MMD ΓåÆ Blender scale
            types={"MESH", "ARMATURE", "MORPHS"},
        )
        return [o for o in bpy.context.selected_objects]
    except AttributeError:
        print(f"  WARNING: MMD Tools addon not installed!")
        print(f"  Install: https://github.com/UuuNyaa/blender_mmd_tools")
        return []
    except Exception as e:
        print(f"  ERROR importing PMX: {e}")
        return []


def create_placeholder(name: str, position: tuple, color: tuple) -> list:
    """Create a placeholder cube with text label."""
    print(f"  Creating placeholder: {name}...")
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    cube = bpy.context.active_object
    cube.name = name
    cube.scale = (0.5, 0.5, 1.5)

    # Set display color
    if cube.active_material is None:
        mat = bpy.data.materials.new(name=f"{name}_mat")
        mat.diffuse_color = (*color, 1.0)
        cube.data.materials.append(mat)

    # Create text label
    bpy.ops.object.text_add(location=(position[0], position[1] - 1.2, position[2] + 2.0))
    text_obj = bpy.context.active_object
    text_obj.name = f"{name}_label"
    text_obj.data.body = name.split("_")[0]
    text_obj.scale = (0.5, 0.5, 0.5)

    return [cube, text_obj]


def import_zundapal():
    """Import the Zundapal building model."""
    if not ZUNDAPAL_BLEND.exists():
        print(f"  SKIP: Zundapal blend not found at {ZUNDAPAL_BLEND}")
        return []

    print(f"  Appending Zundapal from: {ZUNDAPAL_BLEND.name}...")
    try:
        with bpy.data.libraries.load(str(ZUNDAPAL_BLEND), link=False) as (data_from, data_to):
            # Import all objects
            data_to.objects = [name for name in data_from.objects]
        imported = []
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                imported.append(obj)
        return imported
    except Exception as e:
        print(f"  ERROR appending Zundapal: {e}")
        return []


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Studio setup
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def setup_studio():
    """Create the full ZunZun studio layout."""
    print("=" * 60)
    print("ZUNZUN STUDIO SETUP")
    print("=" * 60)

    # Clear existing scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Remove unused data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    # ΓöÇΓöÇ Import all characters ΓöÇΓöÇ
    print("\n[1] Importing characters...")
    all_objects = []

    for char in CHARACTERS:
        name = char["name"]
        pos = char["position"]
        role = char["role"]

        if char["type"] == "vrm":
            objs = import_vrm(char["path"])
        elif char["type"] == "placeholder":
            objs = create_placeholder(name, pos, char["color"])
        else:
            print(f"  SKIP: unknown type for {name}")
            continue

        # Arrange imported objects
        for obj in objs:
            if obj.type == "ARMATURE" or (obj.type == "MESH" and obj.parent is None):
                obj.location = pos

        # Store role as custom property
        for obj in objs:
            obj["zunzun_role"] = role
            obj["zunzun_character"] = name

        all_objects.extend(objs)
        print(f"  Γ£ô {name}: {char['label']}")

    # ΓöÇΓöÇ Import Melusina ΓöÇΓöÇ
    print("\n[2] Importing Melusina...")
    if MELUSINA_FBX.exists():
        mel_objs = import_fbx(MELUSINA_FBX)
        for obj in mel_objs:
            if obj.type == "ARMATURE" or (obj.type == "MESH" and obj.parent is None):
                obj.location = (-3, -3, 0)
            obj["zunzun_role"] = "Threshold Guardian"
            obj["zunzun_character"] = "Melusina"
        all_objects.extend(mel_objs)
        print(f"  Γ£ô Melusina imported")
    else:
        print(f"  SKIP: Melusina FBX not found")

    # ΓöÇΓöÇ Import Zundapal building ΓöÇΓöÇ
    print("\n[3] Importing Zundapal...")
    zp_objs = import_zundapal()
    for obj in zp_objs:
        obj["zunzun_role"] = "Enemy / Building"
        obj["zunzun_character"] = "Zundapal"
    all_objects.extend(zp_objs)

    # ΓöÇΓöÇ Studio lighting ΓöÇΓöÇ
    print("\n[4] Setting up lighting...")
    # Key light
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 15))
    sun = bpy.context.active_object
    sun.name = "Studio_Key"
    sun.data.energy = 5.0
    sun.rotation_euler = (0.8, 0.2, 1.2)

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 8))
    fill = bpy.context.active_object
    fill.name = "Studio_Fill"
    fill.data.energy = 200.0
    fill.data.size = 10.0

    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 15, 5))
    rim = bpy.context.active_object
    rim.name = "Studio_Rim"
    rim.data.energy = 150.0

    # ΓöÇΓöÇ Ground plane ΓöÇΓöÇ
    print("\n[5] Creating ground plane...")
    bpy.ops.mesh.primitive_plane_add(size=30, location=(9, 0, -2))
    ground = bpy.context.active_object
    ground.name = "Studio_Ground"
    mat = bpy.data.materials.new(name="Ground_Mat")
    mat.diffuse_color = (0.15, 0.15, 0.18, 1.0)
    ground.data.materials.append(mat)

    # ΓöÇΓöÇ Cameras ΓöÇΓöÇ
    print("\n[6] Setting up cameras...")
    # Overview camera
    bpy.ops.object.camera_add(location=(9, -15, 10))
    cam_overview = bpy.context.active_object
    cam_overview.name = "Cam_Overview"
    cam_overview.rotation_euler = (1.1, 0, 0)

    # Close-up camera
    bpy.ops.object.camera_add(location=(1.5, -3, 1.2))
    cam_close = bpy.context.active_object
    cam_close.name = "Cam_CloseUp"
    cam_close.rotation_euler = (1.4, 0, 0)

    # ΓöÇΓöÇ Collections ΓöÇΓöÇ
    print("\n[7] Organizing collections...")
    # Create collection per character
    for char in CHARACTERS:
        coll = bpy.data.collections.new(char["name"])
        bpy.context.scene.collection.children.link(coll)
        for obj in all_objects:
            if obj.get("zunzun_character") == char["name"]:
                # Move to collection
                for c in obj.users_collection:
                    c.objects.unlink(obj)
                coll.objects.link(obj)

    # ΓöÇΓöÇ Save ΓöÇΓöÇ
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    print(f"\n{'='*60}")
    print(f"SAVED: {OUTPUT_PATH}")
    print(f"  {len(CHARACTERS)} characters + Melusina + Zundapal")
    print(f"  Open in Blender to prep for UE export")
    print(f"{'='*60}")


if __name__ == "__main__":
    setup_studio()
