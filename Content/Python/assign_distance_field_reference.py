import unreal
LEVEL='/Game/Melodia/Levels/DistanceFieldBlendLab'
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mat=unreal.load_asset('/Game/Melodia/Materials/DistanceField/M_DF_ContactReference')
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ('DFLab_Ground','DFLab_EmbeddedRock','DFLab_WallContact','DFLab_ColumnContact','DFLab_SeparatedRock'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent): c.set_material(0,mat)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('[DistanceFieldReference] assigned')
