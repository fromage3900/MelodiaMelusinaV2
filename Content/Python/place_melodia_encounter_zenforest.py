"""Author a first playable Melodia encounter trigger in ZenForestTest."""
import json
from pathlib import Path
import unreal

LEVEL='/Game/ZenForestTest'
LABEL='MelodiaEncounter_SakuraPhantom_01'
REPORT=Path(unreal.Paths.project_saved_dir())/'Melodia'/'zenforest_encounter_placement.json'
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(LEVEL):
    raise RuntimeError('Could not load ZenForestTest; end PIE before running this script')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
trigger=next((a for a in eas.get_all_level_actors() if a.get_actor_label()==LABEL),None)
if trigger is None:
    trigger=eas.spawn_actor_from_class(unreal.MelodiaEncounterTrigger, unreal.Vector(500,0,100), unreal.Rotator(0,0,0))
    trigger.set_actor_label(LABEL)
trigger.set_editor_property('EncounterLevel', 1)
trigger.set_editor_property('EnemyId', unreal.Name('SakuraPhantom'))
trigger.set_editor_property('EncounterDisplayName', unreal.Text('Sakura Phantom'))
trigger.set_editor_property('bOneShot', True)
try:
    trigger.get_editor_property('TriggerVolume').set_editor_property('box_extent', unreal.Vector(250,250,150))
except Exception as e:
    unreal.log_warning('[EncounterPlacement] extent: '+str(e))
les.save_current_level()
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({'level':LEVEL,'label':LABEL,'enemy_id':'SakuraPhantom','placed':trigger is not None,'location':[500,0,100]},indent=2),encoding='utf-8')
unreal.log('[EncounterPlacement] '+str(REPORT))
