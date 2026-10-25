"""Runtime-only test of the necklace's authored chest attachment frame."""
import unreal,json,pathlib,math
HERE=pathlib.Path(unreal.Paths.project_saved_dir()).resolve()/'Audit/MelusinaLegSkirt_20261023'
assert unreal._mel_legskirt_comparison['finished']
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
body=next(c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='CharacterMesh0')
neck=next(c for c in p.get_components_by_class(unreal.StaticMeshComponent) if 'Necklace' in c.get_name())
def td(t):
 return {'location':[t.translation.x,t.translation.y,t.translation.z],
         'quat_xyzw':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],
         'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z]}
bone='spine_03_x'
ref=next(b for b in json.loads((HERE/'necklace_native_bind.json').read_text())['bones'] if b['name']==bone)['component']
frame=unreal.Transform()
frame.translation=unreal.Vector(**ref['location'])
frame.rotation=unreal.Rotator(**ref['rotation']).quaternion()
frame.scale3d=unreal.Vector(**ref['scale'])
align=json.loads((pathlib.Path(unreal.Paths.project_dir())/'Tools/LookDev/Regalia/ue/ue_attach_v4.json').read_text())['component_space']
author=unreal.Transform();author.translation=unreal.Vector(*align['loc'])
author.rotation=unreal.Quat(*align['quat_xyzw']);author.scale3d=unreal.Vector(align['scale'],align['scale'],align['scale'])
local=unreal.MathLibrary.make_relative_transform(author,frame)
reconstructed=unreal.MathLibrary.compose_transforms(local,frame)
reconstruction_error=math.dist(td(reconstructed)['location'],td(author)['location'])
assert reconstruction_error<1e-4
report={'mesh':neck.get_editor_property('static_mesh').get_path_name(),'before_socket':str(neck.get_attach_socket_name()),
 'before_relative':td(neck.get_relative_transform()),'authored_component_alignment':td(author),'native_bind':td(frame),
 'candidate_socket':bone,'candidate_relative':td(local),'ref_reconstruction_error_cm':reconstruction_error,
 'scope':'runtime-only attachment canary; no asset write'}
assert neck.attach_to_component(body,bone,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
neck.set_relative_transform(local,False,False)
report['readback_socket']=str(neck.get_attach_socket_name());report['readback_relative']=td(neck.get_relative_transform())
assert report['readback_socket']==bone
(HERE/'necklace_attachment_canary.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
MEL_COMPARE_PREFIX='neck_static_after_';MEL_CAPTURE_ONLY=True;MEL_CAPTURE_OUTFIT_ONLY=True
MEL_USE_STATIC_CAMERAS_ONLY=True
exec((HERE/'compare_runtime_layers.py').read_text())
