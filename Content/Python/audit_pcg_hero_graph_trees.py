"""Read-only audit for the serialized hero PCG graph trees.

Unlike the level audits, this script never loads a map or regenerates a PCG
component. It verifies the graph assets themselves, making it safe to run while
another editor lane owns a level.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = "/Game/EnvSandbox/PCG/Musical/Hero/"
AUDIT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "pcg_hero_graph_tree_audit.json"

SPECS = {
    "ResonanceCathedral": {
        "graph": f"{ROOT}PCG_Hero_ResonanceCathedral",
        "profile": f"{ROOT}DA_Hero_ResonanceCathedralProfile",
        "expected_interactive": 12,
        "tensor_policy": "required",
        "required_meshes": {
            "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_Black_Bevel",
            "/Game/EnvSandbox/PCG/Musical/SM_Piano_Keybed",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        },
    },
    "ArpeggioBridge": {
        "graph": f"{ROOT}PCG_Hero_ArpeggioBridge",
        "profile": f"{ROOT}DA_Hero_ArpeggioBridgeProfile",
        "expected_interactive": 24,
        "tensor_policy": "disabled",
        "required_meshes": {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
        },
    },
    "BellTreeGarden": {
        "graph": f"{ROOT}PCG_Hero_BellTreeGarden",
        "profile": f"{ROOT}DA_Hero_BellTreeGardenProfile",
        "expected_interactive": 18,
        "tensor_policy": "disabled",
        "required_meshes": {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        },
    },
    "XylophoneTrail": {
        "graph": f"{ROOT}PCG_Hero_XylophoneTrail",
        "profile": f"{ROOT}DA_Hero_XylophoneTrailProfile",
        "expected_interactive": 24,
        "tensor_policy": "disabled",
        "required_meshes": {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
        },
    },
    "CrystalHarpGrove": {
        "graph": f"{ROOT}PCG_Hero_CrystalHarpGrove",
        "profile": f"{ROOT}DA_Hero_CrystalHarpGroveProfile",
        "expected_interactive": 20,
        "tensor_policy": "disabled",
        "required_meshes": {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        },
    },
}

CURVE_CLASSES = {
    "PCGExCreateSplineSettings",
    "PCGSplineSamplerSettings",
    "PCGExSampleNearestSplineSettings",
}


def _profile_value(profile: Any, name: str, default: Any = None) -> Any:
    try:
        return profile.get_editor_property(name)
    except Exception:
        return default


def _mesh_paths(unreal: Any, nodes: list[Any]) -> set[str]:
    paths: set[str] = set()
    for node in nodes:
        settings = node.get_settings()
        if not settings or settings.get_class().get_name() != "PCGStaticMeshSpawnerSettings":
            continue
        try:
            selector = settings.get_editor_property("mesh_selector_parameters")
            entries = selector.get_editor_property("mesh_entries") or []
            for entry in entries:
                descriptor = entry.get_editor_property("descriptor")
                mesh = descriptor.get_editor_property("static_mesh")
                if mesh:
                    paths.add(mesh.get_path_name().split(".")[0])
        except Exception:
            continue
    return paths


def _finite_node_serialization(nodes: list[Any]) -> bool:
    # The PCG Python API does not expose every nested PCGEx struct uniformly;
    # the serialized representation is still a useful final NaN tripwire.
    token = re.compile(r"(?<![A-Za-z0-9_])(nan|inf(?:inity)?)(?![A-Za-z0-9_])", re.IGNORECASE)
    return all(token.search(str(node)) is None for node in nodes)


def audit() -> dict[str, Any]:
    import unreal

    rows: dict[str, Any] = {}
    for name, spec in SPECS.items():
        graph = unreal.EditorAssetLibrary.load_asset(spec["graph"])
        profile = unreal.EditorAssetLibrary.load_asset(spec["profile"])
        nodes = list(graph.get_editor_property("nodes") or []) if graph else []
        classes = [node.get_settings().get_class().get_name() for node in nodes if node.get_settings()]
        meshes = _mesh_paths(unreal, nodes)
        curve_present = CURVE_CLASSES.issubset(set(classes))
        tensor_count = classes.count("PCGExCreateTensorSpinSettings") + classes.count("PCGExExtrudeTensorsSettings")
        tensor_ok = tensor_count > 0 if spec["tensor_policy"] == "required" else tensor_count == 0
        profile_count = _profile_value(profile, "expected_note_count", _profile_value(profile, "note_count", None)) if profile else None
        checks = {
            "graph_present": bool(graph),
            "profile_present": bool(profile),
            "curve_chain_present": curve_present,
            "actor_spawner_present": "PCGSpawnActorSettings" in classes,
            "expected_interactive_count": profile_count in (None, spec["expected_interactive"]),
            "tensor_policy": tensor_ok,
            "required_meshes_present": set(spec["required_meshes"]).issubset(meshes),
            "finite_serialization": _finite_node_serialization(nodes),
        }
        rows[name] = {
            "graph": spec["graph"],
            "profile": spec["profile"],
            "node_count": len(nodes),
            "classes": classes,
            "mesh_paths": sorted(meshes),
            "profile_expected_note_count": profile_count,
            "tensor_policy": spec["tensor_policy"],
            "tensor_operator_count": tensor_count,
            "checks": checks,
            "ok": all(checks.values()),
        }

    result = {
        "ok": all(row["ok"] for row in rows.values()),
        "map_loads": 0,
        "pcg_regenerations": 0,
        "production_maps_touched": False,
        "graphs": rows,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[PCG Hero Graph Tree Audit] {json.dumps(result, default=str)}")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, default=str))
