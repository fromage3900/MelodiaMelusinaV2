"""Create/open the bounded playable fixture using the canonical Melusina GameMode.

Run from Unreal's Python console:
    import stage_hybrid_waveharp_playtest as test; test.stage()
Assets are authored by Unreal and stay under the existing CombatTrial test surface.
"""
import unreal

MAP = '/Game/Melodia/CombatTrial/L_HybridWaveHarpPlaytest'
MORNING = '/Game/Melodia/Levels/Opening/L_MelusinaMorning'


def _stock_definitions():
    """Author valid test stats; the stock resolver still owns every calculation."""
    folder = '/Game/Melodia/CombatTrial/HybridStats'
    definitions = []
    for name, parent_path, values in [
        ('BP_WaveHarpTestAttackerStats', '/Game/TurnBasedJRPGTemplate/Blueprints/Units/PlayerUnits/BP_ArcherPlayerUnit', {'hit': 100, 'minAttack': 20, 'maxAttack': 20}),
        ('BP_WaveHarpTestDefenderStats', '/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase', {'speed': 1, 'defense': 0}),
    ]:
        path = folder + '/' + name
        asset = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if asset is None:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property('parent_class', unreal.load_class(None, parent_path + '.' + parent_path.rsplit('/', 1)[1] + '_C'))
            asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Blueprint, factory)
        if asset is None:
            raise RuntimeError('Could not author stock test definition ' + path)
        unreal.BlueprintEditorLibrary.compile_blueprint(asset)
        cls = unreal.load_class(None, path + '.' + name + '_C')
        default = unreal.get_default_object(cls)
        for key, value in values.items():
            default.set_editor_property(key, value)
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
            raise RuntimeError('Could not save stock test definition ' + path)
        definitions.append(cls)
    return definitions


def _configure_target(target):
    attacker, defender = _stock_definitions()
    target.set_editor_property('stock_attacker_definition', attacker)
    target.set_editor_property('stock_defender_definition', defender)
    target.set_editor_property('stock_pure_damage', 20)


def prepare_zenforest():
    """Restore the canonical pawn/controller and add one scoped practice encounter.

    Run only with PIE stopped. Does not rewrite terrain, hero assets or animations.
    """
    if unreal.EditorLevelLibrary.get_pie_worlds(False):
        raise RuntimeError('Stop PIE before preparing ZenForest')
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not editor.load_level('/Game/ZenForestTest'):
        raise RuntimeError('ZenForestTest did not load')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mode = unreal.load_class(None, '/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.BP_MelodiaJRPGGameMode_C')
    world.get_world_settings().set_editor_property('default_game_mode', mode)
    existing = [a for a in actors.get_all_level_actors() if a.get_actor_label() == 'WaveHarp Practice Echo']
    if not existing:
        starts = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]
        if not starts:
            raise RuntimeError('ZenForest has no PlayerStart')
        start = starts[0]
        location = start.get_actor_location() + start.get_actor_forward_vector() * 800 + unreal.Vector(0, 0, 40)
        target = actors.spawn_actor_from_class(unreal.MelodiaWorldSlimeNode, location)
        target.set_actor_label('WaveHarp Practice Echo')
        target.set_editor_property('max_hp', 250.0)
        target.hybrid_encounter.set_editor_property('encounter_id', 'melodia_slime_tutorial')
        target.slime_mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
        target.slime_mesh.set_relative_scale3d(unreal.Vector(1.4, 1.4, 1.4))
        target.slime_mesh.set_collision_profile_name('BlockAllDynamic')
        _configure_target(target)
    else:
        _configure_target(existing[0])
    if not editor.save_current_level():
        raise RuntimeError('ZenForest did not save')
    unreal.log('HYBRID_ZENFOREST_READY canonical GameMode; one practice echo')


def prepare_morning():
    """Add one practice echo to the open Morning level after owner playtesting.

    Does not load another map or change its GameMode/PlayerStart/quest actors.
    Uses the existing smoke identity so killing it cannot complete the authored
    slime tutorial. Existing durable outcomes are preserved, never reset here.
    """
    if unreal.EditorLevelLibrary.get_pie_worlds(False):
        raise RuntimeError('Stop PIE before preparing Morning')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MORNING:
        raise RuntimeError('Open L_MelusinaMorning before preparing its encounter')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    loaded = actors.get_all_level_actors()
    config = unreal.load_asset('/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig')
    identity = 'melodia_smoke_encounter'
    if identity not in [str(x) for x in config.get_editor_property('encounter_ids')]:
        raise RuntimeError('The practice identity is not in the existing allowlist')
    existing = [a for a in loaded if isinstance(a, unreal.MelodiaWorldSlimeNode)
                and str(a.hybrid_encounter.get_encounter_id()) == identity]
    if len(existing) > 1:
        raise RuntimeError('Multiple practice HP owners found; refusing to add another')
    if existing:
        target = existing[0]
    else:
        starts = [a for a in loaded if isinstance(a, unreal.PlayerStart)]
        if len(starts) != 1:
            raise RuntimeError('Expected one loaded Morning PlayerStart')
        start = starts[0]
        catchers = [a for a in loaded if a.get_actor_label() == 'SM_BowStage_Catcher']
        if len(catchers) != 1:
            raise RuntimeError('Expected the existing BowStage catcher to anchor the practice area')
        catcher = catchers[0]
        anchor = catcher.get_actor_location() + unreal.Vector(0,220,0)
        ground = unreal.SystemLibrary.line_trace_single(
            world, anchor + unreal.Vector(0,0,1200), anchor - unreal.Vector(0,0,3000),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [start,catcher], unreal.DrawDebugTrace.NONE, True)
        if ground is None:
            raise RuntimeError('No ground under the practice position; no actor was created')
        # UE 5.8 returns an optional HitResult, not the older (bool, hit) tuple.
        impact = ground.to_tuple()[5]
        location = impact
        target = actors.spawn_actor_from_class(unreal.MelodiaWorldSlimeNode, location)
        if target is None:
            raise RuntimeError('Morning practice target did not spawn')
        target.set_actor_label('Morning / WaveHarp Practice Echo')
        target.set_folder_path('AI/BowStage')
        target.set_editor_property('max_hp', 250.0)
        target.hybrid_encounter.set_editor_property('encounter_id', identity)
        target.slime_mesh.set_static_mesh(unreal.load_asset('/Game/Melodia/_PROJECT/Characters/Enemies/SM_MelodySlime'))
        # Verified mesh bounds are 5.95 x 4.93 x 4.21 cm; make a 1.05 m echo.
        target.slime_mesh.set_relative_scale3d(unreal.Vector(25,25,25))
        target.hit_volume.set_world_scale3d(unreal.Vector(1,1,1))
        target.slime_mesh.set_collision_profile_name('BlockAllDynamic')
    _configure_target(target)
    # Save this actor's package only; preserve the owner's other dirty packages.
    package = target.get_package()
    if not unreal.EditorLoadingAndSavingUtils.save_packages([package], False):
        raise RuntimeError('Could not save the scoped Morning practice actor')
    unreal.log('HYBRID_MORNING_READY ' + target.get_path_name() + ' identity=' + identity)
    return target


def stage():
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        editor.load_level(MAP)
        for target in actors.get_all_level_actors():
            if isinstance(target, unreal.MelodiaWorldSlimeNode):
                _configure_target(target)
        if not editor.save_current_level():
            raise RuntimeError('The playtest level did not save')
        unreal.log('HYBRID_PLAYTEST_READY ' + MAP)
        return
    if not editor.new_level(MAP):
        raise RuntimeError('Could not create the dedicated playtest level')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mode = unreal.load_class(None, '/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.BP_MelodiaJRPGGameMode_C')
    world.get_world_settings().set_editor_property('default_game_mode', mode)

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -20))
    floor.set_actor_label('Hybrid Playtest / Ground')
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(40, 40, .4))
    floor.static_mesh_component.set_collision_profile_name('BlockAll')
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 120), unreal.Rotator(-4, 0, 0))
    start.set_actor_label('Hybrid Playtest / Melusina Start')

    target = actors.spawn_actor_from_class(unreal.MelodiaWorldSlimeNode, unreal.Vector(950, 0, 180))
    target.set_actor_label('Hybrid Playtest / Single Encounter')
    target.set_editor_property('max_hp', 250.0)
    target.hybrid_encounter.set_editor_property('encounter_id', 'melodia_slime_tutorial')
    target.slime_mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
    target.slime_mesh.set_relative_scale3d(unreal.Vector(1.4, 1.4, 1.4))
    target.slime_mesh.set_collision_profile_name('BlockAllDynamic')
    _configure_target(target)

    light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 700), unreal.Rotator(-40, -30, 0))
    light.light_component.set_editor_property('intensity', 3.0)
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 700))
    actors.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, -200))
    if not editor.save_current_level():
        raise RuntimeError('The playtest level did not save')
    unreal.log('HYBRID_PLAYTEST_READY ' + MAP)


if __name__ == '__main__':
    stage()
