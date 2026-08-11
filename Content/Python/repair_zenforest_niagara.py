"""Repair and place the ZenForestTest Niagara starter kit in UE 5.8."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
REPORT = ROOT / "Saved/Audit/zenforest_niagara_repair.json"
LEVEL = "/Game/ZenForestTest"
MAT_DIR = "/Game/EnvSandbox/VFX/Materials"
SYS_DIR = "/Game/EnvSandbox/VFX/Systems/Sakura"
PARENT = f"{MAT_DIR}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite"


def _asset(path: str):
    return unreal.EditorAssetLibrary.load_asset(path)


def _rename_material_if_needed(name: str) -> str | None:
    path = f"{MAT_DIR}/{name}.{name}"
    asset = _asset(path)
    if not asset or asset.get_class().get_name() != "Material":
        return None
    legacy = f"{MAT_DIR}/M_{name}_Legacy"
    if unreal.EditorAssetLibrary.does_asset_exist(f"{legacy}.{legacy.rsplit('/', 1)[-1]}"):
        return legacy
    if unreal.EditorAssetLibrary.rename_asset(path, legacy):
        return legacy
    raise RuntimeError(f"Could not preserve and rename incorrect material asset: {path}")


def _create_mi(name: str, parent_path: str = PARENT):
    path = f"{MAT_DIR}/{name}.{name}"
    existing = _asset(path)
    if existing:
        if existing.get_class().get_name() == "ObjectRedirector":
            if not unreal.EditorAssetLibrary.delete_asset(path):
                raise RuntimeError(f"Could not remove redirector before recreating material instance: {path}")
            existing = None
    if existing:
        if existing.get_class().get_name() != "MaterialInstanceConstant":
            raise RuntimeError(f"Expected MI after repair, found {existing.get_class().get_name()}: {path}")
        return existing, False
    parent = _asset(parent_path)
    if not parent:
        raise RuntimeError(f"Missing Niagara sprite parent: {parent_path}")
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, factory)
    if not instance:
        raise RuntimeError(f"Failed to create material instance: {name}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    return instance, True


def _duplicate_if_missing(source_name: str, target_name: str) -> bool:
    source = f"{SYS_DIR}/{source_name}.{source_name}"
    target = f"{SYS_DIR}/{target_name}.{target_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        return False
    if not unreal.EditorAssetLibrary.duplicate_asset(source, target):
        raise RuntimeError(f"Failed to duplicate Niagara system {source} -> {target}")
    return True


def _restore_system_material_alias(source_name: str, target_name: str) -> bool:
    """Restore an exact package name used by older Niagara systems."""
    source = f"{MAT_DIR}/{source_name}.{source_name}"
    target = f"{MAT_DIR}/{target_name}.{target_name}"
    existing = _asset(target)
    if existing:
        if existing.get_class().get_name() == "ObjectRedirector":
            unreal.EditorAssetLibrary.delete_asset(target)
        else:
            return False
    if not unreal.EditorAssetLibrary.duplicate_asset(source, target):
        raise RuntimeError(f"Failed to restore Niagara material alias {source} -> {target}")
    return True


def _spawn_or_update(eas, label: str, system_name: str, location: tuple[float, float, float], scale: tuple[float, float, float], active: bool) -> bool:
    system_path = f"{SYS_DIR}/{system_name}.{system_name}"
    system = _asset(system_path)
    if not system:
        raise RuntimeError(f"Missing Niagara system for actor {label}: {system_path}")
    actor = next((a for a in eas.get_all_level_actors() or [] if a.get_actor_label() == label), None)
    if not actor:
        actor = eas.spawn_actor_from_class(unreal.NiagaraActor, unreal.Vector(*location), unreal.Rotator(0, 0, 0))
    if not actor:
        raise RuntimeError(f"Failed to spawn Niagara actor: {label}")
    actor.set_actor_label(label)
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.get_component_by_class(unreal.NiagaraComponent)
    if not component:
        raise RuntimeError(f"Niagara actor has no component: {label}")
    component.set_asset(system)
    component.set_auto_activate(active)
    if active:
        component.activate(True)
    return True


def main() -> int:
    renamed = []
    for name in ("MI_Niagara_Petal", "MI_Niagara_Gust"):
        old = _rename_material_if_needed(name)
        if old:
            renamed.append({"name": name, "legacy": old})

    made_materials = []
    for name in ("MI_Niagara_Petal", "MI_Niagara_Gust", "MI_Niagara_Petal_Instance", "MI_Niagara_Gust_Instance", "MI_Niagara_NebulaPetal", "MI_Niagara_Cosmic", "MI_Niagara_AuroraRibbon"):
        if name in ("MI_Niagara_Petal", "MI_Niagara_Gust"):
            continue
        _, created = _create_mi(name)
        if created:
            made_materials.append(name)

    restored_aliases = []
    for source, target in (("MI_Niagara_Petal_Instance", "MI_Niagara_Petal"), ("MI_Niagara_Gust_Instance", "MI_Niagara_Gust")):
        if _restore_system_material_alias(source, target):
            restored_aliases.append(target)

    duplicated_systems = []
    for source, target in (("NS_SakuraWaterPetals", "NS_CosmicPetalOrbit"), ("NS_WindRibbonGust", "NS_SakuraCosmicAurora")):
        if _duplicate_if_missing(source, target):
            duplicated_systems.append({"source": source, "target": target})

    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
        raise RuntimeError(f"Could not load level: {LEVEL}")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    placements = (
        ("VFX_SakuraCanopy", "NS_SakuraPetals_v2", (550.0, 0.0, 300.0), (1.0, 1.0, 1.0), True),
        ("VFX_SakuraGround", "NS_SakuraGroundPetals", (550.0, 0.0, 10.0), (1.0, 1.0, 1.0), True),
        ("VFX_PetalGust", "NS_SakuraPetalGust", (700.0, 0.0, 120.0), (1.0, 1.0, 1.0), False),
        ("VFX_CosmicPetals", "NS_CosmicPetalOrbit", (900.0, 0.0, 220.0), (1.0, 1.0, 1.0), True),
        ("VFX_CosmicAurora", "NS_SakuraCosmicAurora", (900.0, 0.0, 360.0), (1.0, 1.0, 1.0), True),
    )
    spawned = []
    for item in placements:
        _spawn_or_update(eas, *item)
        spawned.append(item[0])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

    report = {
        "ok": True,
        "level": LEVEL,
        "renamed_legacy_materials": renamed,
        "material_instances_created": made_materials,
        "system_material_aliases_restored": restored_aliases,
        "systems_created_from_valid_templates": duplicated_systems,
        "actors_spawned_or_updated": spawned,
        "note": "Cosmic systems are valid starter derivatives of existing petal templates and require final Niagara-editor artistic tuning.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
