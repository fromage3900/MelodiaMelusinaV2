import unreal
import sys
import os
import json

L = unreal.log_warning

L('=== SETUP: Opening Levels ===')

# Run the existing opening levels setup
script_path = unreal.Paths.project_dir() + 'Content/Python/setup_melodia_opening_levels.py'
exec(open(script_path).read())

L('=== SETUP: ZenForestTest actors ===')

LEVEL = '/Game/ZenForestTest'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('Failed to load {}'.format(LEVEL))
else:
    actors = eas.get_all_level_actors()
    existing = {a.get_actor_label(): a for a in actors}
    L('Loaded ZenForestTest with {} actors'.format(len(actors)))
    
    # Check what's there
    for label, actor in sorted(existing.items()):
        L('  Existing: {} ({}) at {}'.format(label, actor.get_class().get_name(), str(actor.get_actor_location())))
    
    # Spawn encounter trigger if not present
    # C++ class MelodiaEncounterTrigger
    encounter_cls = None
    try:
        encounter_cls = unreal.load_class(None, '/Script/MelodiaCore.MelodiaEncounterTrigger')
        L('EncounterTrigger class: {}'.format(encounter_cls))
    except Exception as ex:
        L('Cannot load MelodiaEncounterTrigger: {}'.format(str(ex)))
    
    # The encounter trigger BP is probably BP_Enemy_SakuraPhantom
    # Actually, encounter triggers use the C++ class to spawn enemy encounters in the world
    # Let me check if there's a BP version
    bp_encounter = unreal.load_object(name='/Game/Melodia/Enemies/BP_Enemy_SakuraPhantom.BP_Enemy_SakuraPhantom', outer=None)
    L('BP_Enemy_SakuraPhantom loaded: {}'.format(bp_encounter is not None))
    
    # The generator BP
    bp_gen = unreal.load_asset('/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
    L('Generator BP loaded: {}'.format(bp_gen is not None))
    
    # Check if we can get the generated class
    if bp_gen:
        gen_cls = bp_gen.generated_class()
        L('Generator generated class: {}'.format(gen_cls))

L('=== DONE ===')
