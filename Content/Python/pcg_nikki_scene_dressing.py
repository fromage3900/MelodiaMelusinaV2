"""Additive Nikki-inspired dressing recipes for the musical PCG proof levels.

This module is intentionally split into a pure manifest and an explicit editor
apply step.  The apply step only accepts the musical proof maps, assigns
existing material instances to proof-level actors, and never edits a water
master, production map, or musical gameplay contract.
"""
from __future__ import annotations

import json
from typing import Any, Mapping


PROOF_ROOT = "/Game/EnvSandbox/PCG/Musical/Hero/"
MATERIAL_ROOT = "/Game/EnvSandbox/Materials/Instances/"
NIKKI_MAPPED_ROOT = f"{MATERIAL_ROOT}NikkiIntegrated/Mapped/"


RECIPES: dict[str, dict[str, Any]] = {
    "ResonanceCathedral": {
        "level": f"{PROOF_ROOT}L_PCG_Hero_ResonanceCathedral",
        "hero_tag": "PCG_ResonanceCathedral",
        "architecture_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SpaceCathedral_IntegratedV1",
        "hero_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_CosmicOrrery_IntegratedV1",
        "accent_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SakuraDream_IntegratedV1",
        "water_material": f"{MATERIAL_ROOT}Water/v10/Integrated/MI_WaterV10_Integrated_CinematicHero",
        "fog_color": (0.18, 0.25, 0.46, 1.0),
        "fog_density": 0.012,
        "tone": "moonlit cathedral with rose-gold resonator accents",
    },
    "ArpeggioBridge": {
        "level": f"{PROOF_ROOT}L_PCG_Hero_ArpeggioBridge",
        "hero_tag": "PCG_ArpeggioBridge",
        "architecture_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_BaroqueCastle_IntegratedV1",
        "hero_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_CosmicOrrery_IntegratedV1",
        "accent_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SakuraDream_IntegratedV1",
        "water_material": f"{MATERIAL_ROOT}Water/v10/Integrated/MI_WaterV10_Integrated_CalmPond",
        "fog_color": (0.20, 0.35, 0.52, 1.0),
        "fog_density": 0.009,
        "tone": "high-key dream bridge over a calm blue void",
    },
    "BellTreeGarden": {
        "level": f"{PROOF_ROOT}L_PCG_Hero_BellTreeGarden",
        "hero_tag": "PCG_BellTreeGarden",
        "architecture_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_BioGrotto_IntegratedV1",
        "hero_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_CosmicOrrery_IntegratedV1",
        "accent_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SakuraDream_IntegratedV1",
        "water_material": f"{MATERIAL_ROOT}Water/v10/Integrated/MI_WaterV10_Integrated_BiolumGrotto",
        "fog_color": (0.12, 0.32, 0.28, 1.0),
        "fog_density": 0.014,
        "tone": "bioluminescent garden with restrained landmark supports",
    },
    "XylophoneTrail": {
        "level": f"{PROOF_ROOT}L_PCG_Hero_XylophoneTrail",
        "hero_tag": "PCG_XylophoneTrail",
        "architecture_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SakuraDream_IntegratedV1",
        "hero_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_CosmicOrrery_IntegratedV1",
        "accent_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_BaroqueCastle_IntegratedV1",
        "water_material": f"{MATERIAL_ROOT}Water/v10/Integrated/MI_WaterV10_Integrated_RiverClear",
        "fog_color": (0.28, 0.18, 0.38, 1.0),
        "fog_density": 0.010,
        "tone": "sakura-lit traversal garden with a clear playable spine",
    },
    "CrystalHarpGrove": {
        "level": f"{PROOF_ROOT}L_PCG_Hero_CrystalHarpGrove",
        "hero_tag": "PCG_CrystalHarpGrove",
        "architecture_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SpaceCathedral_IntegratedV1",
        "hero_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_CosmicOrrery_IntegratedV1",
        "accent_material": f"{NIKKI_MAPPED_ROOT}MI_NikkiHero_SakuraDream_IntegratedV1",
        "water_material": f"{MATERIAL_ROOT}Water/v10/Integrated/MI_WaterV10_Integrated_BiolumGrotto",
        "fog_color": (0.18, 0.38, 0.46, 1.0),
        "fog_density": 0.011,
        "tone": "moonlit crystal harp grove with glass-blue frame rails and sparse arches",
    },
}


def recipe_manifest() -> dict[str, Any]:
    """Return a serializable, reviewable dressing manifest."""
    return {
        "proof_only": True,
        "production_maps_touched": False,
        "water_masters_modified": False,
        "audio_or_clock_modified": False,
        "recipes": RECIPES,
    }


def _set_if_present(obj: Any, name: str, value: Any) -> bool:
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception:
        return False


def _tag(actor: Any, value: str) -> None:
    try:
        tags = list(actor.tags or [])
        if value not in [str(item) for item in tags]:
            tags.append(value)
            actor.tags = tags
    except Exception:
        pass


def _load(unreal: Any, path: str) -> Any:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"required dressing asset is missing: {path}")
    return asset


def _actor_material_role(actor: Any, hero_tag: str) -> str | None:
    label = str(actor.get_actor_label() or "").lower()
    tags = {str(item) for item in (actor.tags or [])}
    class_name = str(actor.get_class().get_name() or "").lower()
    # The PCG host owns the generated static architecture ISMs. Its hero tag
    # is intentionally shared with the proof, but its material role is the
    # architecture palette; only spawned Music Node actors are hero surfaces.
    if "graphhost" in class_name or ("pcg hero" in label and "music node" not in label):
        return "architecture"
    if hero_tag in tags or any(token in label for token in ("piano", "resonator", "bell", "xylophone", "harp", "arpeggio", "music node")):
        return "hero"
    if "water" in label or "pond" in label or "void" in label:
        return "water"
    if any(token in label for token in ("floor", "rail", "column", "arch", "support", "deck", "pylon", "garden")):
        return "architecture"
    return None


def _set_mesh_material(actor: Any, material: Any) -> bool:
    if not material:
        return False
    components = []
    try:
        components = actor.get_components_by_class(actor.get_class())
    except Exception:
        pass
    try:
        unreal_module = __import__("unreal")
        components = list(actor.get_components_by_class(unreal_module.StaticMeshComponent) or [])
        procedural_class = getattr(unreal_module, "ProceduralMeshComponent", None)
        if procedural_class is not None:
            components.extend(list(actor.get_components_by_class(procedural_class) or []))
    except Exception:
        pass
    changed = False
    for component in components or []:
        if _set_if_present(component, "override_materials", [material]):
            changed = True
        else:
            try:
                component.set_material(0, material)
                changed = True
            except Exception:
                pass
    return changed


def _find_or_spawn_atmosphere(unreal: Any, actor_subsystem: Any, actors: Mapping[str, Any], recipe: Mapping[str, Any]) -> dict[str, Any]:
    label = f"{recipe['hero_tag']} Nikki Atmosphere"
    existing = next((actor for actor in actors.values() if actor and actor.get_actor_label() == label), None)
    fog_class = getattr(unreal, "ExponentialHeightFog", None)
    if existing is None and fog_class is not None:
        existing = actor_subsystem.spawn_actor_from_class(fog_class, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
        if existing:
            existing.set_actor_label(label)
    if not existing:
        return {"label": label, "spawned": False}
    _tag(existing, "PCG_NikkiProofDressing")
    component = existing.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if component:
        _set_if_present(component, "fog_density", float(recipe["fog_density"]))
        _set_if_present(component, "fog_height_falloff", 0.18)
        _set_if_present(component, "fog_inscattering_color", unreal.LinearColor(*recipe["fog_color"]))
    return {"label": label, "spawned": True}


def apply_loaded_proof_level(unreal: Any, recipe_name: str, *, save: bool = False) -> dict[str, Any]:
    """Apply one recipe to the currently loaded proof level.

    The caller must load the exact proof map separately.  This function refuses
    to run if the recipe path is not under the musical proof root.
    """
    recipe = RECIPES[recipe_name]
    level_path = str(recipe["level"])
    if not level_path.startswith(PROOF_ROOT):
        raise RuntimeError("refusing to dress a non-proof level")

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = {str(actor.get_actor_label()): actor for actor in (actor_subsystem.get_all_level_actors() or []) if actor}
    materials = {key: _load(unreal, str(recipe[key])) for key in ("architecture_material", "hero_material", "accent_material", "water_material")}
    counts = {"hero": 0, "architecture": 0, "water": 0, "accent": 0}
    changed = []
    for actor in actors.values():
        role = _actor_material_role(actor, str(recipe["hero_tag"]))
        if role is None:
            continue
        material = materials["hero_material"] if role == "hero" else materials[f"{role}_material"]
        if _set_mesh_material(actor, material):
            counts[role] += 1
            _tag(actor, "PCG_NikkiProofDressing")
            changed.append(str(actor.get_actor_label()))

    atmosphere = _find_or_spawn_atmosphere(unreal, actor_subsystem, actors, recipe)
    if save:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, level_path):
            raise RuntimeError(f"could not save proof map: {level_path}")
    return {
        "ok": True,
        "recipe": recipe_name,
        "level": level_path,
        "tone": recipe["tone"],
        "counts": counts,
        "changed_actor_count": len(changed),
        "atmosphere": atmosphere,
        "saved": bool(save),
        "production_maps_touched": False,
        "water_masters_modified": False,
    }


if __name__ == "__main__":
    print(json.dumps(recipe_manifest(), indent=2))
