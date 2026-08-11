import json,time
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()); out=ROOT/'Saved'/'Melodia'/'zenforest_pie_smoke.json'
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); les.load_level('/Game/ZenForestTest')
report={'level':'/Game/ZenForestTest','generator_present':False,'pie_requested':False,'pie_ended':False}
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report['generator_present']=any(a.get_actor_label()=='RoguelikeDungeonGenerator_Melodia' for a in eas.get_all_level_actors())
try:
    unreal.EditorLevelLibrary.editor_play_simulate(); report['pie_requested']=True; time.sleep(3.0); unreal.EditorLevelLibrary.editor_end_play(); report['pie_ended']=True
except Exception as exc: report['error']=str(exc)
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8'); unreal.log('[ZenForestPIE] '+str(out))
