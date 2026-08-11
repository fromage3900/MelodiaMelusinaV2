import unreal
level='/Game/Melodia/Levels/DistanceFieldBlendLab'
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith('DFLab_'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                unreal.log('[DFProbe] %s runtimeVT=%s mats=%s' % (a.get_actor_label(), str(c.get_editor_property('runtime_virtual_textures')), str(c.get_editor_property('override_materials'))))
            except Exception as e:
                unreal.log_warning('[DFProbe] %s %s' % (a.get_actor_label(), e))
