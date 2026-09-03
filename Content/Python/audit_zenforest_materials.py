"""ZenForestTest — find mesh components rendering the default material.

Loads the level (read-only) and audits every primitive component's material
slots: override array + mesh slot list; flags slots that resolve to nothing,
to a missing asset, or to an MI with a missing parent. Reports anomalies only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "zenforest_material_audit.json"

LEVEL = "/Game/ZenForestTest"

COMPONENT_CLASSES = (
    "StaticMeshComponent",
    "InstancedStaticMeshComponent",
    "HierarchicalInstancedStaticMeshComponent",
    "SplineMeshComponent",
    "NaniteDisplacedMeshComponent",
)


def material_state(mat) -> dict:
    if mat is None:
        return {"resolved": False, "reason": "no material in slot"}
    path = str(mat.get_path_name())
    pkg = path.split(".")[0]
    cls = type(mat).__name__
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
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.ZenForestTest"):
        return {"ok": False, "error": "level missing"}
    les.load_level(LEVEL)

    anomalies: list[dict] = []
    checked = 0
    actors = eas.get_all_level_actors() or []
    for actor in actors:
        comps = actor.get_components_by_class(unreal.PrimitiveComponent) or []
        for comp in comps:
            if type(comp).__name__ not in COMPONENT_CLASSES:
                continue
            mesh = None
            try:
                mesh = comp.get_editor_property("static_mesh") if type(comp).__name__ in (
                    "StaticMeshComponent", "InstancedStaticMeshComponent",
                    "HierarchicalInstancedStaticMeshComponent") else None
            except Exception:
                pass
            overrides = []
            try:
                overrides = list(comp.get_editor_property("materials") or [])
            except Exception:
                pass
            mesh_slots = []
            if mesh:
                try:
                    mesh_slots = list(mesh.get_editor_property("materials") or [])
                except Exception:
                    pass
            slot_count = max(len(overrides), len(mesh_slots))
            if slot_count == 0:
                continue
            checked += 1
            for i in range(slot_count):
                mat = None
                src = "mesh"
                if i < len(overrides) and overrides[i] is not None:
                    mat = overrides[i]
                    src = "override"
                elif i < len(mesh_slots):
                    mat = mesh_slots[i]
                st = material_state(mat)
                if not st["resolved"]:
                    anomalies.append({
                        "actor": actor.get_actor_label(),
                        "component": comp.get_name(),
                        "mesh": str(mesh.get_path_name()) if mesh else None,
                        "slot": i,
                        "source": src,
                        "material_path": st.get("path"),
                        "reason": st["reason"],
                    })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": LEVEL,
        "actors": len(actors),
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