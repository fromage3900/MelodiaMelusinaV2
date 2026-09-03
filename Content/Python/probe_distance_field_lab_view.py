import unreal
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Melodia/Levels/DistanceFieldBlendLab')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ('DFLab_Camera_Hero','DFLab_Key','DFLab_Fill','DFLab_Sky','DFLab_Ground'):
        unreal.log('[DFView] %s loc=%s rot=%s hidden=%s' % (a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation(), a.is_hidden_ed()))
