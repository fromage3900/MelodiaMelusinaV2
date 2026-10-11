import unreal
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()=='L_InfiniteScore'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
A=sub.get_all_level_actors()
for a in list(A):
    if a.get_actor_label()=='ScoreWagon': sub.destroy_actor(a)
spl_actor=[a for a in A if a.get_actor_label()=='NavProxy_ScoreWalk_Curved'][0]; spl=spl_actor.get_component_by_class(unreal.SplineComponent)
d0=600.0
loc=spl.get_location_at_distance_along_spline(d0,unreal.SplineCoordinateSpace.WORLD); rot=spl.get_rotation_at_distance_along_spline(d0,unreal.SplineCoordinateSpace.WORLD)
cls=unreal.load_asset('/Game/Melodia/Vehicles/BP_ScoreWagon').generated_class()
w=sub.spawn_actor_from_class(cls,loc,rot); w.set_actor_label('ScoreWagon'); w.set_actor_scale3d(unreal.Vector(5,5,5))
w.set_editor_property('SplineActor',spl_actor); w.set_editor_property('Distance',d0); w.set_editor_property('SpeedCmPerSec',400.0)
w.tags=[unreal.Name('InfiniteScore.Wagon')]   # distinct tag: the dress script must not delete it
w.modify(); print('wagon',w.get_class().get_name(), unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
