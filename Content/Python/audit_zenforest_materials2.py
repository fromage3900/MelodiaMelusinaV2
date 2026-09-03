"""ZenForestTest — audit v2: ALL primitive components + landscape + water.

Flags any slot that resolves to the engine default/grid materials (the grey
brick look) or to nothing/missing assets.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "zenforest_material_audit2.json"
LEVEL = "/Game/ZenForestTest"

DEFAULTISH = (
    "/Engine/EngineMaterials/DefaultMaterial",
    "/Engine/EngineMaterials/WorldGridMaterial",
    "/Engine/EngineMaterials/DefaultDiffuse",
    "/Engine/EngineMaterials/DefaultWhiteGrid",
    "/Engine/EngineMaterials/DefaultWhiteTexture",
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/EngineMaterials/VertexColorMaterial",
    "/Engine/EngineMaterials/DefaultFlattenMaterial",
)

SKIP_CLASSES = ("MaterialBillboardComponent",)


def material_state(mat) -> dict:
    if mat is None:
        return {"resolved": False, "reason": "no material in slot"}
    path = str(mat.get_path_name())
    pkg = path.split(".")[0]
    cls = type(mat).__name__
    if pkg in DEFAULTISH:
        return {"resolved": False, "reason": "engine default/grid material", "path": path}
    if not unreal.EditorAssetLibrary.does_asset_exist(pkg):
        return {"resolved": False, "reason": f"asset missing: {pkg}", "path": path}
    if cls == "MaterialInstanceConstant":
        parent = mat.get_editor_property("parent")
        if parent is None:
            return {"resolved": False, "reason": "MI has no parent", "path": path}
        parent_pkg = str(parent.get_path_name()).split(".")[0]
        if not unreal.EditorAssetLibrary.does_asset_exist(parent_pkg):
            return {"resolved": False, "reason": f"MI parent missing: {parent_pkg}", "path": path}
    return {"resolved": True, "path": path, "class": cls}


def audit() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(LEVEL)

    anomalies: list[dict] = []
    checked = 0
    for actor in eas.get_all_level_actors() or []:
        for comp in actor.get_components_by_class(unreal.PrimitiveComponent) or []:
            cn = type(comp).__name__
            if cn in SKIP_CLASSES:
                continue
            if cn == "LandscapeComponent":
                lm = None
                try:
                    lm = comp.get_editor_property("landscape_material")
                except Exception:
                    pass
                checked += 1
                st = material_state(lm)
                if not st["resolved"]:
                    anomalies.append({"actor": actor.get_actor_label(), "component": comp.get_name(),
                                      "kind": "landscape", "material_path": st.get("path"),
                                      "reason": st["reason"]})
                continue
            mats = []
            try:
                mats = list(comp.get_editor_property("override_materials") or [])
            except Exception:
                try:
                    mats = list(comp.get_editor_property("materials") or [])
                except Exception:
                    continue
            if cn == "WaterBodyComponent" or cn == "WaterBodyIslandComponent":
                mats = list(comp.get_editor_property("materials") or [])
            if not mats:
                continue
            checked += 1
            for i, mat in enumerate(mats):
                if mat is None:
                    continue
                st = material_state(mat)
                if not st["resolved"]:
                    anomalies.append({
                        "actor": actor.get_actor_label(), "component": comp.get_name(),
                        "kind": cn, "slot": i, "material_path": st.get("path"),
                        "reason": st["reason"]})

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": LEVEL,
        "components_checked": checked,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "ok": not anomalies,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    audit()