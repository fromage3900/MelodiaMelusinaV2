import unreal
import json
from pathlib import Path

L = unreal.log_warning

LEVEL = '/Game/ZenForestTest'
ENCOUNTER_LABEL = 'MelodiaEncounter_SakuraPhantom_01'
GENERATOR_LABEL = 'RoguelikeDungeonGenerator_Melodia'
COORDINATOR_LABEL = 'Melodia_FirstDungeonCoordinator'
GATE_LABEL = 'Melodia_FirstDungeonGate'

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('FAILED to load {}'.format(LEVEL))

actors = eas.get_all_level_actors()
existing = {a.get_actor_label(): a for a in actors}
L('Loaded {} actors'.format(len(actors)))

# Find encounter
encounter = existing.get(ENCOUNTER_LABEL)
if not encounter:
    L('ERROR: Encounter {} not found'.format(ENCOUNTER_LABEL))
else:
    L('Found encounter: {}'.format(encounter.get_actor_label()))
    encounter.set_editor_property('EnemyId', unreal.Name('SakuraPhantom'))
    encounter.set_editor_property('EncounterDisplayName', unreal.Text('Sakura Phantom'))
    encounter.set_editor_property('bOneShot', True)

# Find generator
generator = existing.get(GENERATOR_LABEL)
if not generator:
    L('ERROR: Generator {} not found'.format(GENERATOR_LABEL))
else:
    L('Found generator: {}'.format(generator.get_actor_label()))

# Spawn coordinator (C++ class)
coordinator = existing.get(COORDINATOR_LABEL)
if not coordinator:
    coord_cls = unreal.load_class(None, '/Script/MelodiaCore.MelodiaDungeonRunCoordinator')
    if coord_cls:
        coordinator = eas.spawn_actor_from_class(coord_cls, unreal.Vector(1400, 0, -40), unreal.Rotator(0, 0, 0))
        coordinator.set_actor_label(COORDINATOR_LABEL)
        L('Spawned coordinator: {}'.format(coordinator is not None))
    else:
        L('ERROR: MelodiaDungeonRunCoordinator class not found - need to build MelodiaCore first')
else:
    L('Coordinator already exists')

if coordinator and generator:
    coordinator.set_editor_property('DungeonGenerator', generator)
    coordinator.set_editor_property('bStartRunOnBeginPlay', False)
    coordinator.set_editor_property('InitialRunSeed', 1337)

# Spawn gate (C++ class)
gate = existing.get(GATE_LABEL)
if not gate:
    gate_cls = unreal.load_class(None, '/Script/MelodiaCore.MelodiaFirstDungeonGate')
    if gate_cls:
        gate = eas.spawn_actor_from_class(gate_cls, unreal.Vector(1050, 0, -40), unreal.Rotator(0, 0, 0))
        gate.set_actor_label(GATE_LABEL)
        L('Spawned gate: {}'.format(gate is not None))
    else:
        L('ERROR: MelodiaFirstDungeonGate class not found')
else:
    L('Gate already exists')

if gate and coordinator:
    gate.set_editor_property('RunCoordinator', coordinator)
    gate.set_editor_property('FirstRunSeed', 1337)

les.save_current_level()
L('=== DUNGEON UNLOCK SETUP DONE ===')
