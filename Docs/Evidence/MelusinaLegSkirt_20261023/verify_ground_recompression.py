"""Duplicate-only codec control for an existing, unbound ground-frame candidate.

Reuses the established native track writer. Never binds or promotes an asset.
Writes a failure receipt as well as a passing one; never overwrites a control.
"""
from pathlib import Path
import hashlib,json,sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'Tools/animation'))
from repair_loop_seam import checked_call,python_result

name=sys.argv[1]
assert name in ['A_Melusina_Walk_Mocap_RootX_SeamFix','A_Melusina_Run_Mocap_RootX_SeamFix','A_Melusina_Sprint_Mocap_RootX'], 'bounded locomotion controls only'
src='/Game/Melodia/Characters/Melusina/Animations/Locomotion/'+name
candidate='/Game/Staging/AnimationDoctor/LegSkirt_20261023/'+name+'_GroundFrame'
control='/Game/Staging/AnimationDoctor/LegSkirt_20261023/'+name+'_RecompressionControl'
source_file=REPO/'Content/Melodia/Characters/Melusina/Animations/Locomotion'/(name+'.uasset')
before=hashlib.sha256(source_file.read_bytes()).hexdigest()
report={'source':src,'candidate':candidate,'control':control,'source_sha256_before':before,
        'runtime_admission':'UNVERIFIED','passed':False}
try:
 state=python_result("""import unreal,json
e=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
print(json.dumps({'world':e.get_editor_world().get_path_name(),'pie':bool(e.get_game_world()),
 'source_exists':unreal.EditorAssetLibrary.does_asset_exist(%r),
 'candidate_exists':unreal.EditorAssetLibrary.does_asset_exist(%r),
 'control_exists':unreal.EditorAssetLibrary.does_asset_exist(%r)}))
"""%(src,candidate,control))
 report['preflight']=state
 assert not state['pie'], 'PIE is active; do not write tracks'
 assert state['world'].startswith('/Game/Staging/AnimationDoctor/LegSkirt_20261023/L_LegSkirtDiagnostic.'), 'diagnostic editor ownership changed'
 assert state['source_exists'] and state['candidate_exists'] and not state['control_exists'], 'missing prerequisite or control already exists'
 bones=['c_traj','root_x','c_root_master_x']
 tracks={b:checked_call('animation',{'action':'get_bone_track_keys','asset_path':src,'bone_name':b}) for b in bones}
 duplicate=python_result("import unreal,json\na=unreal.EditorAssetLibrary.duplicate_asset(%r,%r);assert a\nprint(json.dumps({'duplicated':a.get_path_name()}))"%(src,control))
 report['duplicate']=duplicate
 for bone,track in tracks.items():
  checked_call('animation',{'action':'set_bone_track_keys','asset_path':control,'bone_name':bone,
    'positions_json':json.dumps(track['positions']),'rotations_json':json.dumps(track['rotations']),
    'scales_json':json.dumps(track['scales'])})
  readback=checked_call('animation',{'action':'get_bone_track_keys','asset_path':control,'bone_name':bone})
  for key in ['positions','rotations','scales']:
   assert len(track[key])==len(readback[key]),(bone,key,'count')
   assert max(abs(a-b) for p,q in zip(track[key],readback[key]) for a,b in zip(p,q))<2e-5,(bone,key,'readback')
 checked_call('blueprint',{'action':'save_asset','asset_path':control})
 proof=python_result("""import unreal,json,math
paths=%r
assets=[unreal.load_asset(x) for x in paths];assert all(assets)
m=unreal.load_asset('/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body')
opt=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.COMPRESSED,should_retarget=True,optional_skeletal_mesh=m)
names=['root','c_pos','root_x','c_root_master_x','head_x','spine_01_x','foot_l','foot_r','toes_01_l','toes_01_r','thigh_stretch_l','thigh_stretch_r','leg_stretch_l','leg_stretch_r','c_kilt_master_x']+[x+'_'+s for s in ['l','r'] for x in ['shoulder','arm_stretch','forearm_stretch','hand']]
frames=[unreal.AnimationLibrary.get_num_keys(a) for a in assets];assert len(set(frames))==1
pairs=[(0,1,'source_vs_control'),(0,2,'source_vs_candidate'),(1,2,'control_vs_candidate')]
metrics={key:{'max_world_position_delta_cm':0.,'max_world_quaternion_component_delta':0.} for i,j,key in pairs}
for f in range(frames[0]):
 poses=[unreal.AnimPoseExtensions.get_anim_pose_at_frame(a,f,opt) for a in assets]
 for n in names:
  ts=[unreal.AnimPoseExtensions.get_bone_pose(p,n,unreal.AnimPoseSpaces.WORLD) for p in poses]
  for i,j,key in pairs:
   a,b=ts[i],ts[j];v=metrics[key]
   pos=math.dist([a.translation.x,a.translation.y,a.translation.z],[b.translation.x,b.translation.y,b.translation.z])
   qa=[a.rotation.x,a.rotation.y,a.rotation.z,a.rotation.w];qb=[b.rotation.x,b.rotation.y,b.rotation.z,b.rotation.w]
   q=min(max(abs(x-y) for x,y in zip(qa,qb)),max(abs(x+y) for x,y in zip(qa,qb)))
   if pos>v['max_world_position_delta_cm']:v['worst_position']={'frame':f,'bone':n}
   if q>v['max_world_quaternion_component_delta']:v['worst_rotation']={'frame':f,'bone':n}
   v['max_world_position_delta_cm']=max(v['max_world_position_delta_cm'],pos)
   v['max_world_quaternion_component_delta']=max(v['max_world_quaternion_component_delta'],q)
print(json.dumps({'frames':frames[0],'bones_checked':len(names),'metrics':metrics}))
"""%[src,control,candidate])
 report['compressed_pose_control']=proof
 v=proof['metrics']['control_vs_candidate']
 report['gates']={'position_same_codec_control':v['max_world_position_delta_cm']<.002,
                  'rotation_same_codec_control':v['max_world_quaternion_component_delta']<1e-5}
 report['passed']=all(report['gates'].values())
except Exception as exc:
 report['error']=str(exc)
finally:
 report['source_sha256_after']=hashlib.sha256(source_file.read_bytes()).hexdigest()
 report['source_file_unchanged']=report['source_sha256_after']==before
 report['passed']=report['passed'] and report['source_file_unchanged']
 (HERE/(name+'_recompression_control.json')).write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
sys.exit(0 if report['passed'] else 1)
