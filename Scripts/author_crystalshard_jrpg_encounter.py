import unreal

SOURCE_MAP = "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"
TARGET_MAP = "/Game/ZenForestTest"
SOURCE_LABEL = "BP_InteractionBattle"
TARGET_LABEL = "JRPG_CrystalShard_Battle"
TAG = unreal.Name("Encounter_CrystalShard")
NARRATIVE_TAG = unreal.Name("melodia_smoke_encounter")
PLAYER_SPAWN_PATH = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_PlayerSpawnLocation.BP_PlayerSpawnLocation_C"
ENEMY_SPAWN_PATH = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_EnemySpawnLocation.BP_EnemySpawnLocation_C"


def _surface_z(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(float(x), float(y), 10000.0),
        unreal.Vector(float(x), float(y), -10000.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        False,
        [],
        unreal.DrawDebugTrace.NONE,
        True,
        unreal.LinearColor(),
        unreal.LinearColor(),
        0.0,
    )
    data = hit.to_dict() if hit is not None else {}
    if not data.get("blocking_hit"):
        raise RuntimeError(f"ZenForest support raycast missed at ({x:.2f}, {y:.2f})")
    return float(data["impact_point"].z)


def _find_battle(label):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label and actor.get_class().get_name() == "BP_InteractionBattle_C":
            return actor
    return None


def _find_spawn(label, class_name):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label and actor.get_class().get_name() == class_name:
            return actor
    return None


def _place_spawn(world, label, class_path, class_name, location, rotation):
    actor = _find_spawn(label, class_name)
    if actor is None:
        actor_class = unreal.load_class(None, class_path)
        if actor_class is None:
            raise RuntimeError(f"Unable to load stock spawn class {class_path}")
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
        if actor is None:
            raise RuntimeError(f"Unable to spawn {class_name} {label}")
    actor.modify()
    actor.set_actor_label(label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(rotation, False)
    return actor


# Read the known-good stock fixture from the integration map. This preserves the
# authored roster, formation order, and rotations instead of synthesizing combat state.
unreal.EditorLoadingAndSavingUtils.load_map(SOURCE_MAP)
source_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
source_battle = _find_battle(SOURCE_LABEL)
if source_battle is None:
    raise RuntimeError("Known-good stock interaction battle is unavailable")

source_roster = source_battle.get_editor_property("enemyList")
if not source_roster or len(source_roster) != 1:
    raise RuntimeError("Known-good stock enemy roster is unavailable")
source_roster = source_roster[0].copy()

source_base = source_battle.get_actor_location()
spawn_specs = []
for property_name, kind in (("playerSpawnLocations", "player"), ("enemySpawnLocations", "enemy")):
    for index, source_spawn in enumerate(source_battle.get_editor_property(property_name)):
        location = source_spawn.get_actor_location()
        rotation = source_spawn.get_actor_rotation()
        support_z = _surface_z(source_world, location.x, location.y)
        relative = location - source_base
        spawn_specs.append(
            {
                "kind": kind,
                "index": index,
                "dx": float(relative.x),
                "dy": float(relative.y),
                "source_z_offset": float(location.z - support_z),
                "rotation": unreal.Rotator(pitch=rotation.pitch, yaw=rotation.yaw, roll=rotation.roll),
                "class_name": source_spawn.get_class().get_name(),
            }
        )

# Apply the same stock-authored formation to the real Persona encounter in ZenForest.
unreal.EditorLoadingAndSavingUtils.load_map(TARGET_MAP)
target_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
trigger = next(
    (actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()
     if actor.get_class().get_name() == "MelodiaEncounterTrigger"),
    None,
)
if trigger is None:
    raise RuntimeError("ZenForest encounter trigger is unavailable")
trigger_location = trigger.get_actor_location()

battle = _find_battle(TARGET_LABEL)
if battle is None:
    battle_class = unreal.load_class(
        None,
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle.BP_InteractionBattle_C",
    )
    battle = unreal.EditorLevelLibrary.spawn_actor_from_class(battle_class, trigger_location)
    if battle is None:
        raise RuntimeError("Unable to create the stock interaction battle actor.")
battle.modify()
battle.set_actor_location(trigger_location, False, False)
battle.set_actor_label(TARGET_LABEL)
battle.tags = [TAG, NARRATIVE_TAG]
battle.set_editor_property("enemyList", [source_roster])

players = []
enemies = []
for spec in spawn_specs:
    location = unreal.Vector(
        trigger_location.x + spec["dx"],
        trigger_location.y + spec["dy"],
        _surface_z(target_world, trigger_location.x + spec["dx"], trigger_location.y + spec["dy"])
        + spec["source_z_offset"],
    )
    if spec["kind"] == "player":
        actor = _place_spawn(
            target_world,
            f"JRPG_CrystalShard_PlayerSpawn_{spec['index'] + 1}",
            PLAYER_SPAWN_PATH,
            "BP_PlayerSpawnLocation_C",
            location,
            spec["rotation"],
        )
        players.append(actor)
    else:
        actor = _place_spawn(
            target_world,
            f"JRPG_CrystalShard_EnemySpawn_{spec['index'] + 1}",
            ENEMY_SPAWN_PATH,
            "BP_EnemySpawnLocation_C",
            location,
            spec["rotation"],
        )
        enemies.append(actor)

if len(players) != 3 or len(enemies) != 1:
    raise RuntimeError(f"Unexpected stock formation: {len(players)} player, {len(enemies)} enemy spawns")
battle.set_editor_property("playerSpawnLocations", players)
battle.set_editor_property("enemySpawnLocations", enemies)
unreal.EditorLevelLibrary.set_actor_selection_state(battle, False)
saved = unreal.EditorLoadingAndSavingUtils.save_map(target_world, TARGET_MAP)

unreal.log(
    "AUTHORED_JRPG_BATTLE="
    + battle.get_name()
    + " TAGS="
    + str(battle.tags)
    + " PLAYERS="
    + str(len(players))
    + " ENEMIES="
    + str(len(enemies))
    + " ROSTER="
    + str(battle.get_editor_property("enemyList")[0].export_text())
    + " SAVED="
    + str(saved)
)
