import json
from pathlib import Path
import unreal

LEVEL='/Game/ZenForestTest'
BP='/Game/Melodia/Blueprints/Volumes/BP_MelodiaTeleporterVolume'
LABEL='MelodiaTeleporter_ToDreamstate'
REPORT=Path(unreal.Paths.project_saved_dir())/'Melodia'/'zenforest_teleporter_placement.json'
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not les.load_level(LEVEL): raise RuntimeError('End PIE before placement')
e=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
a=next((x for x in e.get_all_level_actors() if x.get_actor_label()==LABEL),None)
bp=unreal.EditorAssetLibrary.load_asset(BP)
if a is None:
    a=e.spawn_actor_from_class(bp.generated_class(),unreal.Vector(1200,0,100),unreal.Rotator(0,0,0)); a.set_actor_label(LABEL)
try: a.set_actor_scale3d(unreal.Vector(2.0,2.0,1.0))
except Exception: pass
les.save_current_level()
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({'level':LEVEL,'label':LABEL,'blueprint':BP,'destination':'L_Melodia_Dreamstate','placed':a is not None},indent=2),encoding='utf-8')
unreal.log('[TeleporterPlacement] '+str(REPORT))
