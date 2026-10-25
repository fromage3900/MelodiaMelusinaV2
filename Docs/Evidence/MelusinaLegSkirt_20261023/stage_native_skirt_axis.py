"""One-property, duplicate-only Kawaii forward-axis canary with graph guards."""
from pathlib import Path
import json,sys,shutil
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'Tools/animation'))
from repair_loop_seam import checked_call,python_result
src='/Game/Staging/AnimationDoctor/LegSkirt_20261023/ABP_LegTargetNeutral_Candidate'
dst='/Game/Staging/AnimationDoctor/LegSkirt_20261023/ABP_LegSkirt_Axis_Candidate'
proof=json.loads((HERE/'KineFX/native_tip_axis_verification.json').read_text());assert proof['passed']
report={'source':src,'candidate':dst,'axis_before':'X_Positive','axis_after':'Y_Negative','runtime_admission':'UNVERIFIED'}
def fp(asset):return checked_call('blueprint',{'action':'get_graph_fingerprint','asset_path':asset,'graph_name':'AnimGraph','mode':'topology+defaults'})
try:
 preflight=python_result("""import unreal,json
e=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
print(json.dumps({'pie':bool(e.get_game_world()),'world':e.get_editor_world().get_path_name(),'exists':unreal.EditorAssetLibrary.does_asset_exist(%r)}))
"""%dst)
 assert not preflight['pie'] and not preflight['exists']
 assert preflight['world'].startswith('/Game/Staging/AnimationDoctor/LegSkirt_20261023/L_LegSkirtDiagnostic.')
 disk=REPO/'Content/Staging/AnimationDoctor/LegSkirt_20261023/ABP_LegTargetNeutral_Candidate.uasset'
 shutil.copy2(disk,HERE/'ABP_LegTargetNeutral_Candidate_before_axis.uasset')
 graph=checked_call('blueprint',{'action':'export_graph','asset_path':src,'graph_name':'AnimGraph'})
 (HERE/'axis_source_graph_before.json').write_text(json.dumps(graph,indent=2))
 first,second=fp(src),fp(src);assert first['fingerprint']==second['fingerprint']
 checked_call('blueprint',{'action':'save_asset','asset_path':src})
 third=fp(src);assert first['fingerprint']==third['fingerprint']
 report['stable_source_fingerprints']=[x['fingerprint'] for x in [first,second,third]]
 python_result("import unreal,json\na=unreal.EditorAssetLibrary.duplicate_asset(%r,%r);assert a\nprint(json.dumps({'duplicated':a.get_path_name()}))"%(src,dst))
 assert fp(dst)['fingerprint']==first['fingerprint']
 report['property_edit']=checked_call('animation',{'action':'set_anim_graph_node_property','asset_path':dst,
  'node_id':'AnimGraphNode_KawaiiPhysics_0','graph_name':'AnimGraph','property_path':'BoneForwardAxis','value':'Y_Negative'})
 report['compile']=checked_call('blueprint',{'action':'compile_blueprint','asset_path':dst})
 assert report['compile']['error_count']==0 and report['compile']['warning_count']==0,report['compile']
 report['graph_assertion']=checked_call('blueprint',{'action':'assert_graph_matches','asset_path':dst,'graph_name':'AnimGraph','mode':'exact','spec':graph})
 assert report['graph_assertion']['matched'],report['graph_assertion']
 checked_call('blueprint',{'action':'save_asset','asset_path':dst})
 report['native_readback']=python_result("""import unreal,json
p=%r;n=unreal.find_object(None,p);assert n
s=n.get_editor_property('node')
print(json.dumps({'axis':str(s.get_editor_property('bone_forward_axis')),'dummy_length':s.get_editor_property('dummy_bone_length'),'damping':s.get_editor_property('physics_settings').get_editor_property('damping')}))
"""%(dst+'.'+dst.rsplit('/',1)[-1]+':AnimGraph.AnimGraphNode_KawaiiPhysics_0'))
 assert 'Y_NEGATIVE' in report['native_readback']['axis'] and report['native_readback']['dummy_length']==3
 report['after_fingerprint']=fp(dst);report['passed']=True
except Exception as exc:
 report['passed']=False;report['error']=str(exc)
finally:
 (HERE/'native_skirt_axis_candidate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
sys.exit(0 if report['passed'] else 1)
