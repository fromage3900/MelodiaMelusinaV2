import unreal
L = unreal.log_warning

LEVEL = '/Game/ZenForestTest'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('FAILED')
else:
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    L('Loaded {} actors'.format(len(existing)))
    
    # === ENCOUNTER ===
    enc = existing.get('MelodiaEncounter_SakuraPhantom_01')
    if not enc:
        enc = eas.spawn_actor_from_class(unreal.MelodiaEncounterTrigger, unreal.Vector(500, 0, 100), unreal.Rotator(0, 0, 0))
        enc.set_actor_label('MelodiaEncounter_SakuraPhantom_01')
        L('Spawned encounter')
    enc.set_editor_property('EncounterLevel', 1)
    enc.set_editor_property('EnemyId', unreal.Name('SakuraPhantom'))
    enc.set_editor_property('EncounterDisplayName', unreal.Text('Sakura Phantom'))
    enc.set_editor_property('bOneShot', True)
    
    # === GENERATOR ===
    gen = existing.get('RoguelikeDungeonGenerator_Melodia')
    if not gen:
        bp = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
        gen = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(1400, 0, -40), unreal.Rotator(0, 0, 0))
        gen.set_actor_label('RoguelikeDungeonGenerator_Melodia')
        L('Spawned generator')
    try: gen.set_editor_property('seed', 1337)
    except: pass
    
    # === COORDINATOR ===
    coord = existing.get('Melodia_FirstDungeonCoordinator')
    if not coord:
        cc = unreal.load_class(None, '/Script/MelodiaCore.MelodiaDungeonRunCoordinator')
        coord = eas.spawn_actor_from_class(cc, unreal.Vector(1400, 0, -40), unreal.Rotator(0, 0, 0))
        coord.set_actor_label('Melodia_FirstDungeonCoordinator')
        L('Spawned coordinator')
    coord.set_editor_property('DungeonGenerator', gen)
    coord.set_editor_property('bStartRunOnBeginPlay', False)
    coord.set_editor_property('InitialRunSeed', 1337)
    
    # === GATE ===
    gate = existing.get('Melodia_FirstDungeonGate')
    if not gate:
        gc = unreal.load_class(None, '/Script/MelodiaCore.MelodiaFirstDungeonGate')
        gate = eas.spawn_actor_from_class(gc, unreal.Vector(1050, 0, -40), unreal.Rotator(0, 0, 0))
        gate.set_actor_label('Melodia_FirstDungeonGate')
        L('Spawned gate')
    gate.set_editor_property('RunCoordinator', coord)
    gate.set_editor_property('FirstRunSeed', 1337)
    
    # === TELEPORTER ===
    tele = existing.get('MelodiaTeleporter_ToDreamstate')
    if not tele:
        tb = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Blueprints/Volumes/BP_MelodiaTeleporterVolume')
        tele = eas.spawn_actor_from_class(tb.generated_class(), unreal.Vector(1200, 0, 100), unreal.Rotator(0, 0, 0))
        tele.set_actor_label('MelodiaTeleporter_ToDreamstate')
        L('Spawned teleporter')
    
    # Save
    L('Saving level...')
    saved = les.save_current_level()
    L('Save result: {}'.format(saved))
    
    # Verify
    actors = eas.get_all_level_actors()
    L('Total actors: {}'.format(len(actors)))

L('DONE')
