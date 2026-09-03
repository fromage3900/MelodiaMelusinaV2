"""Evidence-based audit for the seven-step Melodia vertical-slice setup."""
import json
from pathlib import Path
import unreal

def load(path):
    try:
        return unreal.load_object(None, path)
    except Exception:
        return None

def main():
    bp_path = '/Game/Melodia/Characters/Melusina/BP_Melusina'
    hair_path = '/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair'
    gen_path = '/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'
    room_root = '/Game/Melodia/Roguelike/RoomData'
    report = {
        'build_binaries': bool(list((Path(unreal.Paths.project_dir()) / 'Plugins' / 'MelodiaCore' / 'Binaries' / 'Win64').glob('UnrealEditor-MelodiaCore.dll'))),
        'bp_melusina_loaded': load(bp_path) is not None,
        'water_hair_abp_loaded': load(hair_path) is not None,
        'water_hair_assignment': False,
        'generator_loaded': load(gen_path) is not None,
        'room_data_count': 0,
        'zenforest_generator_present': False,
        'zenforest_encounter_trigger_present': False,
        'pie_smoke': False,
        'manual_animgraph_copy_pose': False,
        'interactive_encounter_rhythm_clear_advance': 'not automated/proven',
    }
    bp = load(bp_path)
    try:
        abp = load(hair_path)
        nodes = abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh) if abp is not None else []
        report['manual_animgraph_copy_pose'] = len(nodes) > 0 and nodes[0].get_editor_property('Node').get_editor_property('use_attached_parent')
    except Exception as e:
        report['manual_animgraph_error'] = str(e)
    if bp is not None:
        try:
            cdo = unreal.get_default_object(bp.generated_class())
            hair = cdo.get_editor_property('WaterHairMesh')
            report['water_hair_assignment'] = hair is not None and hair.get_editor_property('anim_class') is not None
        except Exception as e:
            report['water_hair_assignment_error'] = str(e)
    try:
        assets = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(room_root, recursive=True)
        report['room_data_count'] = len([a for a in assets if str(a.asset_name).startswith('RD_')])
    except Exception:
        pass
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les.load_level('/Game/ZenForestTest'):
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            actors = eas.get_all_level_actors()
            report['zenforest_generator_present'] = any(a.get_actor_label() == 'RoguelikeDungeonGenerator_Melodia' for a in actors)
            report['zenforest_encounter_trigger_present'] = any(a.get_actor_label() == 'MelodiaEncounter_SakuraPhantom_01' for a in actors)
    except Exception as e:
        report['level_error'] = str(e)
    smoke = Path(unreal.Paths.project_saved_dir()) / 'Melodia' / 'zenforest_pie_smoke.json'
    if smoke.exists():
        try:
            data = json.loads(smoke.read_text(encoding='utf-8'))
            report['pie_smoke'] = data.get('generator_present') is True and data.get('pie_ended') is True
        except Exception:
            pass
    out = Path(unreal.Paths.project_saved_dir()) / 'Melodia' / 'melodia_vertical_slice_audit.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('[MelodiaAudit] ' + str(out))
    unreal.log(json.dumps(report, indent=2))
    return report

main()
