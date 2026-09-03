"""Read-only UE audit for the ZenForestTest Niagara presentation lane."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
REPORT = ROOT / "Saved/Audit/zenforest_niagara_audit.json"
SYSTEM_ROOT = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATERIAL_ROOT = "/Game/EnvSandbox/VFX/Materials"
SYSTEMS = (
    "NS_SakuraPetals_v2",
    "NS_SakuraGroundPetals",
    "NS_SakuraPetalGust",
    "NS_SakuraWaterPetals",
    "NS_CosmicPetalOrbit",
    "NS_SakuraCosmicAurora",
)
MATERIALS = (
    "MI_Niagara_Petal_Instance",
    "MI_Niagara_Gust_Instance",
    "MI_Niagara_NebulaPetal",
    "MI_Niagara_Cosmic",
    "MI_Niagara_AuroraRibbon",
)


def _asset(path: str):
    return unreal.EditorAssetLibrary.load_asset(path)


def main() -> int:
    report = {"level": "/Game/ZenForestTest", "systems": [], "materials": [], "actors": [], "issues": []}
    for name in SYSTEMS:
        path = f"{SYSTEM_ROOT}/{name}.{name}"
        asset = _asset(path)
        entry = {"name": name, "path": path, "exists": bool(asset), "class": asset.get_class().get_name() if asset else None}
        report["systems"].append(entry)
        if not asset:
            report["issues"].append({"severity": "critical", "id": "missing_system", "name": name})
        elif entry["class"] != "NiagaraSystem":
            report["issues"].append({"severity": "critical", "id": "wrong_system_class", "name": name, "class": entry["class"]})

    for name in MATERIALS:
        path = f"{MATERIAL_ROOT}/{name}.{name}"
        asset = _asset(path)
        entry = {"name": name, "path": path, "exists": bool(asset), "class": asset.get_class().get_name() if asset else None}
        report["materials"].append(entry)
        if not asset:
            report["issues"].append({"severity": "critical", "id": "missing_material", "name": name})
        elif entry["class"] != "MaterialInstanceConstant":
            report["issues"].append({"severity": "critical", "id": "wrong_material_class", "name": name, "class": entry["class"]})

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les.load_level(report["level"]):
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        wanted = {"VFX_SakuraCanopy", "VFX_SakuraGround", "VFX_PetalGust", "VFX_CosmicPetals", "VFX_CosmicAurora"}
        expected_auto_activate = {
            "VFX_SakuraCanopy": True,
            "VFX_SakuraGround": True,
            "VFX_PetalGust": False,
            "VFX_CosmicPetals": True,
            "VFX_CosmicAurora": True,
        }
        for actor in eas.get_all_level_actors() or []:
            label = actor.get_actor_label()
            if label in wanted:
                comp = actor.get_component_by_class(unreal.NiagaraComponent)
                auto_activate = None
                if comp:
                    try:
                        auto_activate = bool(comp.get_editor_property("b_auto_activate"))
                    except Exception:
                        # UE 5.8 exposes the setter but not a Python getter on NiagaraComponent.
                        auto_activate = None
                entry = {
                    "label": label,
                    "has_niagara": bool(comp),
                    "auto_activate": auto_activate,
                    # is_active is not authoritative under -nullrhi; retain it only as a diagnostic.
                    "runtime_active_diagnostic": bool(comp and comp.is_active()),
                }
                report["actors"].append(entry)
                if comp and auto_activate != expected_auto_activate[label]:
                    report["issues"].append({
                        "severity": "critical",
                        "id": "unexpected_auto_activate",
                        "label": label,
                        "expected": expected_auto_activate[label],
                        "actual": auto_activate,
                    })
        missing = sorted(wanted - {a["label"] for a in report["actors"]})
        for label in missing:
            report["issues"].append({"severity": "warn", "id": "missing_level_actor", "label": label})
    else:
        report["issues"].append({"severity": "critical", "id": "level_load_failed"})

    report["critical_count"] = sum(i["severity"] == "critical" for i in report["issues"])
    report["ok"] = report["critical_count"] == 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
