import unreal
L = unreal.log_warning

LEVEL = '/Game/ZenForestTest'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('FAILED')
else:
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    L('Actors: {}'.format(len(existing)))
    
    # Only spawn what's missing
    if 'MelodiaEncounter_SakuraPhantom_01' not in existing:
        e = eas.spawn_actor_from_class(unreal.MelodiaEncounterTrigger, unreal.Vector(500,0,100), unreal.Rotator(0,0,0))
        e.set_actor_label('MelodiaEncounter_SakuraPhantom_01')
        e.set_editor_property('EncounterLevel',1)
        e.set_editor_property('EnemyId',unreal.Name('SakuraPhantom'))
        e.set_editor_property('EncounterDisplayName',unreal.Text('Sakura Phantom'))
        e.set_editor_property('bOneShot',True)
        L('Spawned encounter')
    
    if 'RoguelikeDungeonGenerator_Melodia' not in existing:
        bp=unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
        g=eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(1400,0,-40), unreal.Rotator(0,0,0))
        g.set_actor_label('RoguelikeDungeonGenerator_Melodia')
        L('Spawned generator')
    
    if 'Melodia_FirstDungeonCoordinator' not in existing:
        cc=unreal.load_class(None,'/Script/MelodiaCore.MelodiaDungeonRunCoordinator')
        c=eas.spawn_actor_from_class(cc, unreal.Vector(1400,0,-40), unreal.Rotator(0,0,0))
        c.set_actor_label('Melodia_FirstDungeonCoordinator')
        L('Spawned coordinator')
    
    if 'Melodia_FirstDungeonGate' not in existing:
        gc=unreal.load_class(None,'/Script/MelodiaCore.MelodiaFirstDungeonGate')
        g2=eas.spawn_actor_from_class(gc, unreal.Vector(1050,0,-40), unreal.Rotator(0,0,0))
        g2.set_actor_label('Melodia_FirstDungeonGate')
        L('Spawned gate')
    
    if 'MelodiaTeleporter_ToDreamstate' not in existing:
        tb=unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Blueprints/Volumes/BP_MelodiaTeleporterVolume')
        t=eas.spawn_actor_from_class(tb.generated_class(), unreal.Vector(1200,0,100), unreal.Rotator(0,0,0))
        t.set_actor_label('MelodiaTeleporter_ToDreamstate')
        L('Spawned teleporter')
    
    # Use EditorAssetLibrary to save the package directly
    pkg = '/Game/ZenForestTest'
    L('Saving via EditorAssetLibrary...')
    saved = unreal.EditorAssetLibrary.save_asset(pkg, only_if_is_dirty=False)
    L('Save result: {}'.format(saved))
    
    L('Total actors: {}'.format(len(eas.get_all_level_actors())))

L('DONE')
