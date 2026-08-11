"""Create presentation-authored JRPG skill children without changing stock assets.

This intentionally creates named, editable skill assets only.  The reciprocal
Resonance effect is authored later inside the stock buff contract after a
focused battle test; no UI, MIDI, subsystem, or parallel combat state is used.
"""
from __future__ import annotations

import unreal


SPECS = (
    {
        "source": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaFocusAttack",
        "target": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence",
        "name": "Petal Cadence",
        "short": "A precise blossom-step that opens a resonant refrain.",
        "long": "Melusina marks one foe with a petal-bright cadence. Sir Melodious can answer the marked target with Skybound Refrain.",
        "mp": 40,
    },
    {
        "source": "/Game/TurnBasedJRPGTemplate/Blueprints/Skills/BP_FocusAttack",
        "target": "/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain",
        "name": "Skybound Refrain",
        "short": "A sure melodic strike that answers Melusina's cadence.",
        "long": "Sir Melodious sends a clear aerial refrain. It gains its authored Resonance payoff only on a target marked by Petal Cadence.",
        "mp": 40,
    },
)

RESONANCE_SOURCE = "/Game/TurnBasedJRPGTemplate/Blueprints/Skills/Buffs/BP_BuffBase"
RESONANCE_TARGET = "/Game/MelodiaIntegration/Party/Skills/Buffs/BP_Resonance"


def create_or_update(spec: dict) -> str:
    asset = unreal.load_asset(spec["target"])
    if not asset:
        if not unreal.EditorAssetLibrary.duplicate_asset(spec["source"], spec["target"]):
            raise RuntimeError("Could not duplicate {} to {}".format(spec["source"], spec["target"]))
        asset = unreal.load_asset(spec["target"])
    if not asset:
        raise RuntimeError("Could not load {}".format(spec["target"]))

    cdo = unreal.get_default_object(asset.generated_class())
    cdo.set_editor_property("name", unreal.Text(spec["name"]))
    cdo.set_editor_property("shortDescription", unreal.Text(spec["short"]))
    cdo.set_editor_property("longDescription", unreal.Text(spec["long"]))
    cdo.set_editor_property("manaRequired", spec["mp"])
    unreal.BlueprintEditorLibrary.compile_blueprint(asset)
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("Could not save {}".format(spec["target"]))
    return spec["target"]


created = [create_or_update(spec) for spec in SPECS]

# Additive only: preserve every existing stock/previously-authored entry while
# exposing the new children at level one on future party-unit instances.
unit_skill_maps = {
    "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation": (
        ("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaDoubleHit.BP_MelusinaDoubleHit_C", 2),
        ("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaFocusAttack.BP_MelusinaFocusAttack_C", 2),
        ("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaTrueStrike.BP_MelusinaTrueStrike_C", 1),
        ("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence.BP_MelusinaPetalCadence_C", 1),
    ),
    "/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit": (
        ("/Game/TurnBasedJRPGTemplate/Blueprints/Skills/BP_FocusAttack.BP_FocusAttack_C", 1),
        ("/Game/TurnBasedJRPGTemplate/Blueprints/Skills/BP_TrueStrike.BP_TrueStrike_C", 5),
        ("/Game/TurnBasedJRPGTemplate/Blueprints/Skills/BP_DoubleHit.BP_DoubleHit_C", 10),
        ("/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain.BP_SirSkyboundRefrain_C", 1),
    ),
}
for unit_path, entries in unit_skill_maps.items():
    unit = unreal.load_asset(unit_path)
    if not unit:
        raise RuntimeError("Missing unit {}".format(unit_path))
    skills = {}
    for class_path, level in entries:
        skill_class = unreal.load_class(None, class_path)
        if not skill_class:
            raise RuntimeError("Missing skill class {}".format(class_path))
        skills[skill_class] = level
    unit_cdo = unreal.get_default_object(unit.generated_class())
    unit_cdo.set_editor_property("battleSkills", skills)
    unreal.BlueprintEditorLibrary.compile_blueprint(unit)
    if not unreal.EditorAssetLibrary.save_loaded_asset(unit, only_if_is_dirty=False):
        raise RuntimeError("Could not save {}".format(unit_path))

# A deliberately data-only marker. BP_BattleSkillBase owns its spawn/reset and
# BP_BuffBase owns expiry/removal; Skybound Refrain will read this exact class
# from target.activeBuffs in its focused follow-up graph pass.
resonance = unreal.load_asset(RESONANCE_TARGET)
if not resonance:
    if not unreal.EditorAssetLibrary.duplicate_asset(RESONANCE_SOURCE, RESONANCE_TARGET):
        raise RuntimeError("Could not duplicate Resonance buff")
    resonance = unreal.load_asset(RESONANCE_TARGET)
if not resonance:
    raise RuntimeError("Could not load Resonance buff")
resonance_cdo = unreal.get_default_object(resonance.generated_class())
resonance_cdo.set_editor_property("durationTurn", 1)
resonance_cdo.set_editor_property("durationTime", 0.0)
unreal.BlueprintEditorLibrary.compile_blueprint(resonance)
if not unreal.EditorAssetLibrary.save_loaded_asset(resonance, only_if_is_dirty=False):
    raise RuntimeError("Could not save Resonance buff")

petal = unreal.load_asset("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence")
petal_cdo = unreal.get_default_object(petal.generated_class())
buffs = list(petal_cdo.get_editor_property("buffs"))
resonance_class = unreal.load_class(None, RESONANCE_TARGET + ".BP_Resonance_C")
if not resonance_class:
    raise RuntimeError("Could not resolve Resonance generated class")
if resonance_class not in buffs:
    buffs.append(resonance_class)
    petal_cdo.set_editor_property("buffs", buffs)
unreal.BlueprintEditorLibrary.compile_blueprint(petal)
if not unreal.EditorAssetLibrary.save_loaded_asset(petal, only_if_is_dirty=False):
    raise RuntimeError("Could not save Petal Cadence")

unreal.log("MELODIA_SKILL_FOUNDATION_AUTHORED: {}".format(created))
