import unreal
import json
import sys

L = unreal.log_warning

L('=== MELODIA VERTICAL SLICE AUDIT ===')

# Step 1: Build binaries check
import os
from pathlib import Path
dll_path = unreal.Paths.project_dir() + 'Plugins/MelodiaCore/Binaries/Win64/UnrealEditor-MelodiaCore.dll'
L('Build binaries: {} exists={}'.format(dll_path, os.path.exists(dll_path)))

# Step 2: BP_Melusina loaded?
bp_path = '/Game/Melodia/Characters/Melusina/BP_Melusina'
bp = unreal.load_object(name=bp_path, outer=None)
L('BP_Melusina loaded: {}'.format(bp is not None))

# Step 3: Water hair ABP loaded?
hair_path = '/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair_New'
hair = unreal.load_object(name=hair_path, outer=None)
hair2 = unreal.load_object(name='/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair', outer=None)
L('WaterHair_New loaded: {}'.format(hair is not None))
L('WaterHair loaded: {}'.format(hair2 is not None))

# Step 4: Generator loaded?
gen_path = '/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'
gen = unreal.load_object(name=gen_path, outer=None)
L('Generator loaded: {}'.format(gen is not None))

coord_path = '/Game/Melodia/Roguelike/Blueprints/BP_MelodiaDungeonRunCoordinator'
coord = unreal.load_object(name=coord_path, outer=None)
L('Coordinator loaded: {}'.format(coord is not None))

# Step 5: Room data count
room_root = '/Game/Melodia/Roguelike/RoomData'
ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path(room_root, recursive=True)
rd_assets = [a for a in assets if str(a.asset_name).startswith('RD_')]
L('Room data count: {}'.format(len(rd_assets)))

# Step 6: ZenForest level actors
try:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les.load_level('/Game/ZenForestTest'):
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = eas.get_all_level_actors()
        generator_present = any(a.get_actor_label() == 'RoguelikeDungeonGenerator_Melodia' for a in actors)
        encounter_present = any(a.get_actor_label() == 'MelodiaEncounter_SakuraPhantom_01' for a in actors)
        L('ZenForest generator present: {}'.format(generator_present))
        L('ZenForest encounter present: {}'.format(encounter_present))
        
        # Also count total actors
        L('ZenForest total actors: {}'.format(len(actors)))
        
        # Check important actors
        for a in actors:
            label = a.get_actor_label()
            cls = a.get_class().get_name()
            if any(kw in label.lower() for kw in ['player', 'spawn', 'gate', 'generator', 'encounter', 'trigger', 'volume', 'start']):
                L('  Actor: {} ({})'.format(label, cls))
    else:
        L('Failed to load ZenForestTest')
except Exception as ex:
    L('Level load error: {}'.format(str(ex)))

L('=== AUDIT DONE ===')
