"""Staged source ground-frame normalization through the existing clip writer.

Moves only the existing unweighted trajectory frame, preserving its two child
world transforms. The normal FootPlacement node can then use the footwear
support plane without shortening the anatomical legs. Originals stay intact.
"""
import sys, json, pathlib, math, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Tools/animation'))
from repair_loop_seam import checked_call, python_result

name=sys.argv[1]
plane=float(sys.argv[2])
assert math.isfinite(plane)
src='/Game/Melodia/Characters/Melusina/Animations/Locomotion/'+name
dst='/Game/Staging/AnimationDoctor/LegSkirt_20261023/'+name+'_GroundFrame'
out=pathlib.Path(__file__).resolve().parent
info=python_result("""import unreal,json
a=unreal.load_asset(%r);m=unreal.load_asset('/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body');assert a and m
opt=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.COMPRESSED,should_retarget=True,optional_skeletal_mesh=m)
n=unreal.AnimationLibrary.get_num_keys(a);rows=[]
for f in range(n):
 p=unreal.AnimPoseExtensions.get_anim_pose_at_frame(a,f,opt)
 t=unreal.AnimPoseExtensions.get_bone_pose(p,'c_traj',unreal.AnimPoseSpaces.WORLD)
 parent=unreal.AnimPoseExtensions.get_bone_pose(p,'c_pos',unreal.AnimPoseSpaces.WORLD)
 rows.append({'z':t.translation.z,'parent_q':[parent.rotation.x,parent.rotation.y,parent.rotation.z,parent.rotation.w],'scale':[parent.scale3d.x,parent.scale3d.y,parent.scale3d.z]})
print(json.dumps({'frames':n,'rows':rows}))
""" % src)
assert max(x['z'] for x in info['rows'])-min(x['z'] for x in info['rows'])<1e-4,'trajectory reference is animated vertically; use KineFX frame-preserving solve'
for row in info['rows']:
 assert abs(row['parent_q'][0])+abs(row['parent_q'][1])<1e-5 and max(abs(x-1) for x in row['scale'])<1e-5,'nonlevel or scaled parent requires full matrix solve'
delta=plane-info['rows'][0]['z']
tracks={b:checked_call('animation',{'action':'get_bone_track_keys','asset_path':src,'bone_name':b}) for b in ['c_traj','root_x','c_root_master_x']}
for q in tracks['c_traj']['rotations']:
 assert abs(q[0])+abs(q[1])+abs(q[2])<1e-5 and abs(abs(q[3])-1)<1e-5,'nonidentity local trajectory rotation'
python_result("import unreal,json\nassert not unreal.EditorAssetLibrary.does_asset_exist(%r),'candidate already exists'\na=unreal.EditorAssetLibrary.duplicate_asset(%r,%r);assert a\nprint(json.dumps({'duplicate':a.get_path_name()}))"%(dst,src,dst))
changes=[]
for bone,track in tracks.items():
 positions=[list(p) for p in track['positions']]
 for p in positions:p[2]+=delta if bone=='c_traj' else -delta
 checked_call('animation',{'action':'set_bone_track_keys','asset_path':dst,'bone_name':bone,'positions_json':json.dumps(positions),'rotations_json':json.dumps(track['rotations']),'scales_json':json.dumps(track['scales'])})
 back=checked_call('animation',{'action':'get_bone_track_keys','asset_path':dst,'bone_name':bone})
 err=max(abs(a-b) for p,q in zip(positions,back['positions']) for a,b in zip(p,q))
 assert len(positions)==len(back['positions']) and err<2e-5,(bone,err)
 changes.append({'bone':bone,'position_readback_error_cm':err})
checked_call('blueprint',{'action':'save_asset','asset_path':dst})
proof=python_result("""import unreal,json,math
a=unreal.load_asset(%r);b=unreal.load_asset(%r);m=unreal.load_asset('/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body')
opt=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.COMPRESSED,should_retarget=True,optional_skeletal_mesh=m)
names=['root','c_pos','root_x','c_root_master_x','head_x','spine_01_x','foot_l','foot_r','toes_01_l','toes_01_r','thigh_stretch_l','thigh_stretch_r','leg_stretch_l','leg_stretch_r','c_kilt_master_x']+[x+'_'+s for s in ['l','r'] for x in ['shoulder','arm_stretch','forearm_stretch','hand']]
maxp=0.;maxq=0.;plane=[]
for f in range(unreal.AnimationLibrary.get_num_keys(a)):
 pa=unreal.AnimPoseExtensions.get_anim_pose_at_frame(a,f,opt);pb=unreal.AnimPoseExtensions.get_anim_pose_at_frame(b,f,opt)
 for n in names:
  ta=unreal.AnimPoseExtensions.get_bone_pose(pa,n,unreal.AnimPoseSpaces.WORLD);tb=unreal.AnimPoseExtensions.get_bone_pose(pb,n,unreal.AnimPoseSpaces.WORLD)
  maxp=max(maxp,math.dist([ta.translation.x,ta.translation.y,ta.translation.z],[tb.translation.x,tb.translation.y,tb.translation.z]))
  qa=[ta.rotation.x,ta.rotation.y,ta.rotation.z,ta.rotation.w];qb=[tb.rotation.x,tb.rotation.y,tb.rotation.z,tb.rotation.w];maxq=max(maxq,min(max(abs(x-y) for x,y in zip(qa,qb)),max(abs(x+y) for x,y in zip(qa,qb))))
 t=unreal.AnimPoseExtensions.get_bone_pose(pb,'c_traj',unreal.AnimPoseSpaces.WORLD);plane.append(t.translation.z)
print(json.dumps({'frames':unreal.AnimationLibrary.get_num_keys(a),'bones_checked':len(names),'max_world_position_delta_cm':maxp,'max_world_quaternion_component_delta':maxq,'ground_plane_range_cm':[min(plane),max(plane)]}))
"""%(src,dst))
passed=proof['max_world_position_delta_cm']<0.002 and proof['max_world_quaternion_component_delta']<1e-5
report={'source':src,'candidate':dst,'support_plane_cs_cm':plane,'trajectory_delta_cm':delta,'changed_tracks':changes,'compressed_pose_preservation':proof,'direct_compressed_preservation_pass':passed,'same_codec_control_required':not passed,'runtime_admission':'UNVERIFIED'}
(out/(name+'_ground_frame.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report))
sys.exit(0 if passed else 1)
