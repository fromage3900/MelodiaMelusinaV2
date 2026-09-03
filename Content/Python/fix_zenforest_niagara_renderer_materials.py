"""Bind valid Niagara material instances to the ZenForestTest particle systems."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
REPORT = ROOT / "Saved/Audit/zenforest_niagara_material_bindings.json"
SYSTEM_ROOT = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATERIAL_ROOT = "/Game/EnvSandbox/VFX/Materials"
ASSIGNMENTS = (
    ("NS_SakuraPetals_v2", "MI_Niagara_Petal_Instance"),
    ("NS_SakuraGroundPetals", "MI_Niagara_Petal_Instance"),
    ("NS_SakuraPetalGust", "MI_Niagara_Gust_Instance"),
    ("NS_SakuraWaterPetals", "MI_Niagara_Petal_Instance"),
    ("NS_CosmicPetalOrbit", "MI_Niagara_NebulaPetal"),
    ("NS_SakuraCosmicAurora", "MI_Niagara_AuroraRibbon"),
)


def asset(path: str):
    return unreal.EditorAssetLibrary.load_asset(path)


def main() -> int:
    report = {"assignments": [], "errors": [], "saved": []}
    library = getattr(unreal, "NiagaraEditorLibrary", None)
    if not library or not hasattr(library, "set_renderer_material"):
        report["errors"].append("UE 5.8 NiagaraEditorLibrary.set_renderer_material is unavailable")
    else:
        for system_name, material_name in ASSIGNMENTS:
            system_path = f"{SYSTEM_ROOT}/{system_name}.{system_name}"
            material_path = f"{MATERIAL_ROOT}/{material_name}.{material_name}"
            system = asset(system_path)
            material = asset(material_path)
            entry = {"system": system_path, "material": material_path, "ok": False}
            if not system or system.get_class().get_name() != "NiagaraSystem":
                entry["error"] = "missing or invalid NiagaraSystem"
            elif not material or material.get_class().get_name() != "MaterialInstanceConstant":
                entry["error"] = "missing or invalid MaterialInstanceConstant"
            else:
                try:
                    library.set_renderer_material(system, material)
                    unreal.EditorAssetLibrary.save_loaded_asset(system)
                    entry["ok"] = True
                    report["saved"].append(system_name)
                except Exception as exc:
                    entry["error"] = str(exc)
            report["assignments"].append(entry)

    report["ok"] = bool(report["assignments"]) and not report["errors"] and all(e["ok"] for e in report["assignments"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
