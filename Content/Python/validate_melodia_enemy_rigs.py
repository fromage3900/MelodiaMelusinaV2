"""Validate the battle rig contract for the three Melodia enemy assets.

Run in the UE editor after replacing the placeholder mesh paths below. The
script is intentionally read-only: it loads assets and writes an audit report
without changing meshes, skeletons, or Blueprints.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPECTED = {
    "SakuraPhantom": {
        "mesh": "/Game/Melodia/Enemies/SakuraPhantom/SK_SakuraPhantom",
        "sockets": {"aim_socket", "hit_socket", "center_socket", "vfx_socket"},
    },
    "StoneGolem": {
        "mesh": "/Game/Melodia/Enemies/StoneGolem/SK_StoneGolem",
        "sockets": {"aim_socket", "hit_socket", "center_socket", "vfx_socket"},
    },
    "CrystalShard": {
        "mesh": "/Game/Melodia/Enemies/CrystalShard/SK_CrystalShard",
        "sockets": {"aim_socket", "hit_socket", "center_socket", "vfx_socket"},
    },
}


def validate_enemy_mesh(unreal, enemy_id: str, mesh_path: str, expected_sockets: set[str]) -> dict:
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    result = {"enemy_id": enemy_id, "mesh_path": mesh_path, "loaded": bool(mesh), "errors": [], "warnings": []}
    if not mesh:
        result["errors"].append("skeletal mesh did not load")
        return result

    if not hasattr(mesh, "get_skeleton") or not mesh.get_skeleton():
        result["errors"].append("mesh has no skeleton")
    result["skeleton"] = mesh.get_skeleton().get_name() if mesh.get_skeleton() else None
    result["bounds"] = {
        "box": str(mesh.get_editor_property("extended_bounds")) if mesh.has_editor_property("extended_bounds") else None,
    }

    sockets = {socket.get_name() for socket in mesh.get_editor_property("sockets")}
    result["sockets"] = sorted(sockets)
    missing = sorted(expected_sockets - sockets)
    if missing:
        result["errors"].append(f"missing required sockets: {', '.join(missing)}")
    result["ok"] = not result["errors"]
    return result


def main() -> dict:
    import unreal

    results = [validate_enemy_mesh(unreal, enemy_id, spec["mesh"], spec["sockets"])
               for enemy_id, spec in EXPECTED.items()]
    report = {"ok": all(item.get("ok", False) for item in results), "results": results}
    root = Path(unreal.Paths.project_dir())
    output = root / "Saved" / "Melodia" / "enemy_rig_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    unreal.log("Melodia enemy rig validation: " + json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
