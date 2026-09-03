import json
from pathlib import Path
import unreal

LEVEL='/Game/ZenForestTest'
BP='/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'
REPORT=Path(unreal.Paths.project_saved_dir())/'Melodia'/'roguelike_zenforest_placement.json'
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(LEVEL): raise RuntimeError('Could not load ZenForestTest')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
label='RoguelikeDungeonGenerator_Melodia'
actor=next((a for a in eas.get_all_level_actors() if a.get_actor_label()==label),None)
bp=unreal.EditorAssetLibrary.load_asset(BP)
if not bp: raise RuntimeError('Missing '+BP)
cls=bp.generated_class()
if not actor:
    actor=eas.spawn_actor_from_class(cls, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
    actor.set_actor_label(label)
try: actor.set_editor_property('seed',1337)
except Exception: pass
try: actor.set_editor_property('seed_type',0)
except Exception: pass
les.save_current_level()
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({'level':LEVEL,'generator':BP,'label':label,'placed':bool(actor)},indent=2),encoding='utf-8')
unreal.log('[RoguelikePlacement] '+str(REPORT))
