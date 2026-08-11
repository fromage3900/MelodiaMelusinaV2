import unreal
L = unreal.log_warning

try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
except Exception as ex:
    L('save_dirty_packages failed: {}'.format(str(ex)))

LEVEL = '/Game/ZenForestTest'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('FAILED load')
else:
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    L('Actors: {}'.format(len(existing)))
    
    spawned = []
    if 'MelodiaEncounter_SakuraPhantom_01' not in existing:
        L('Spawning encounter...')
        e = eas.spawn_actor_from_class(unreal.MelodiaEncounterTrigger, unreal.Vector(500,0,100), unreal.Rotator(0,0,0))
        e.set_actor_label('MelodiaEncounter_SakuraPhantom_01')
        e.set_editor_property('EncounterLevel',1)
        e.set_editor_property('EnemyId',unreal.Name('SakuraPhantom'))
        e.set_editor_property('EncounterDisplayName',unreal.Text('Sakura Phantom'))
        e.set_editor_property('bOneShot',True)
        spawned.append('encounter')
    
    if 'RoguelikeDungeonGenerator_Melodia' not in existing:
        L('Spawning generator...')
        bp=unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
        g=eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(1400,0,-40), unreal.Rotator(0,0,0))
        g.set_actor_label('RoguelikeDungeonGenerator_Melodia')
        try: g.set_editor_property('seed',1337)
        except: pass
        spawned.append('generator')
    
    if 'Melodia_FirstDungeonCoordinator' not in existing:
        L('Spawning coordinator...')
        cc=unreal.load_class(None,'/Script/MelodiaCore.MelodiaDungeonRunCoordinator')
        c=eas.spawn_actor_from_class(cc, unreal.Vector(1400,0,-40), unreal.Rotator(0,0,0))
        c.set_actor_label('Melodia_FirstDungeonCoordinator')
        spawned.append('coordinator')
    
    if 'Melodia_FirstDungeonGate' not in existing:
        L('Spawning gate...')
        gc=unreal.load_class(None,'/Script/MelodiaCore.MelodiaFirstDungeonGate')
        g2=eas.spawn_actor_from_class(gc, unreal.Vector(1050,0,-40), unreal.Rotator(0,0,0))
        g2.set_actor_label('Melodia_FirstDungeonGate')
        spawned.append('gate')
    
    if 'MelodiaTeleporter_ToDreamstate' not in existing:
        L('Spawning teleporter...')
        tb=unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Blueprints/Volumes/BP_MelodiaTeleporterVolume')
        t=eas.spawn_actor_from_class(tb.generated_class(), unreal.Vector(1200,0,100), unreal.Rotator(0,0,0))
        t.set_actor_label('MelodiaTeleporter_ToDreamstate')
        spawned.append('teleporter')
    
    L('Spawned: {}'.format(', '.join(spawned) if spawned else 'none'))
    
    L('Saving via save_current_level...')
    r = les.save_current_level()
    L('save_current_level: {}'.format(r))

L('DONE')
