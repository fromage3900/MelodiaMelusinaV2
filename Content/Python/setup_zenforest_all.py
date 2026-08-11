import unreal
import json
from pathlib import Path
import sys
L = unreal.log_warning

LEVEL = '/Game/ZenForestTest'
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not les.load_level(LEVEL):
    L('FAILED: Could not load ZenForestTest')
    sys.exit(1)

existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
L('Loaded ZenForestTest - {} actors'.format(len(existing)))

# === 1. Place encounter trigger ===
LABEL_ENC = 'MelodiaEncounter_SakuraPhantom_01'
enc = existing.get(LABEL_ENC)
if not enc:
    try:
        enc_cls = unreal.MelodiaEncounterTrigger
    except:
        enc_cls = unreal.load_class(None, '/Script/MelodiaCore.MelodiaEncounterTrigger')
    enc = eas.spawn_actor_from_class(enc_cls, unreal.Vector(500, 0, 100), unreal.Rotator(0, 0, 0))
    enc.set_actor_label(LABEL_ENC)
    L('Spawned encounter: {}'.format(enc is not None))
else:
    L('Encounter already exists')
if enc:
    enc.set_editor_property('EncounterLevel', 1)
    enc.set_editor_property('EnemyId', unreal.Name('SakuraPhantom'))
    enc.set_editor_property('EncounterDisplayName', unreal.Text('Sakura Phantom'))
    enc.set_editor_property('bOneShot', True)

# === 2. Place dungeon generator ===
LABEL_GEN = 'RoguelikeDungeonGenerator_Melodia'
gen = existing.get(LABEL_GEN)
if not gen:
    bp = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
    if bp:
        gen = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(1400, 0, -40), unreal.Rotator(0, 0, 0))
        gen.set_actor_label(LABEL_GEN)
        L('Spawned generator: {}'.format(gen is not None))
else:
    L('Generator already exists')
if gen:
    try: gen.set_editor_property('seed', 1337)
    except: pass

# === 3. Place teleporter ===
LABEL_TELE = 'MelodiaTeleporter_ToDreamstate'
tele = existing.get(LABEL_TELE)
if not tele:
    tele_bp = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Blueprints/Volumes/BP_MelodiaTeleporterVolume')
    if tele_bp:
        tele = eas.spawn_actor_from_class(tele_bp.generated_class(), unreal.Vector(1200, 0, 100), unreal.Rotator(0, 0, 0))
        tele.set_actor_label(LABEL_TELE)
        L('Spawned teleporter: {}'.format(tele is not None))
else:
    L('Teleporter already exists')

# === 4. Verify ===
les.save_current_level()
actors_after = eas.get_all_level_actors()
L('ZenForestTest now has {} actors'.format(len(actors_after)))
for a in actors_after:
    label = a.get_actor_label()
    cls = a.get_class().get_name()
    if label != 'PlayerStart' and label != 'PostProcessVolume':
        L('  {} ({})'.format(label, cls))

L('=== ZENFOREST SETUP DONE ===')
