"""Validate and optionally import a surreal_arch_world_v1 manifest into UE.

Run (editor):
  py Content/Python/import_world_manifest.py --manifest world.json
  py Content/Python/import_world_manifest.py --manifest world.json --apply

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="Content/Python/import_world_manifest.py" ^
    -manifest="world.json" ^
    -stdout -unattended -nullrhi

Without `--apply`, the command is a read-only import plan. With `--apply`, it
spawns StaticMeshActors only for instances that provide an explicit
`static_mesh_path`; it never guesses a mesh from a library name.
"""
from __future__ import annotations

import json
import math
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "import_world_manifest.json"
logger = logging.getLogger(__name__)


def _resolve_manifest_path() -> Path | None:
    for i, arg in enumerate(sys.argv):
        if arg == "--manifest" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1])
    cwd = Path.cwd()
    for name in ("world.json", "manifest.json", "surreal_arch_world_v1.json"):
        p = cwd / name
        if p.exists():
            return p
    return None


def validate_manifest(data: dict) -> list[str]:
    """Validate the manifest against the JSON‑Schema (same file as export)."""
    import jsonschema
    schema_path = Path(__file__).resolve().parents[2] / "Config" / "world_schema.json"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return ["schema file missing"]
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=str):
        errors.append(error.message)
    return errors


def _matrix_transform(matrix: list[list[float]]) -> dict:
    """Convert a row-major Blender-style 4x4 matrix to UE centimeters/yaw."""
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise ValueError("transform must be a 4x4 matrix")
    sx = math.sqrt(matrix[0][0] ** 2 + matrix[0][1] ** 2 + matrix[0][2] ** 2)
    sy = math.sqrt(matrix[1][0] ** 2 + matrix[1][1] ** 2 + matrix[1][2] ** 2)
    sz = math.sqrt(matrix[2][0] ** 2 + matrix[2][1] ** 2 + matrix[2][2] ** 2)
    return {
        "location_cm": [
            float(matrix[3][0]) * 100.0,
            float(matrix[3][1]) * 100.0,
            float(matrix[3][2]) * 100.0,
        ],
        "yaw_degrees": math.degrees(math.atan2(matrix[1][0], matrix[0][0])),
        "scale": [sx, sy, sz],
    }


def _apply_instance(unreal, entry: dict, transform: dict) -> str:
    mesh_path = entry.get("static_mesh_path")
    if not mesh_path:
        raise ValueError("apply requires an explicit static_mesh_path")
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        raise ValueError(f"static mesh not found: {mesh_path}")

    location = unreal.Vector(*transform["location_cm"])
    rotation = unreal.Rotator(0.0, transform["yaw_degrees"], 0.0)
    scale = unreal.Vector(*transform["scale"])
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        location,
        rotation,
    )
    if not actor:
        raise RuntimeError("EditorLevelLibrary.spawn_actor_from_class returned null")
    actor.set_actor_scale3d(scale)
    component = actor.static_mesh_component
    component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(str(entry.get("role") or entry.get("object") or "WorldInstance"))
    return str(actor.get_path_name())


def import_manifest(manifest_path: Path, apply: bool = False) -> dict:
    try:
        import unreal
    except Exception as e:
        logger.error(f"Unreal Python API not available: {e}")
        return {"ok": False, "error": "unreal module unavailable"}

    if not manifest_path.exists():
        return {"ok": False, "error": f"manifest missing: {manifest_path}"}
    try:
        raw = manifest_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        return {"ok": False, "error": f"json load failed: {exc}"}

    schema_errors = validate_manifest(data)
    if schema_errors:
        logger.error(f"Schema validation failed: {schema_errors}")
        return {"ok": False, "error": "schema errors", "errors": schema_errors}

    results: dict = {}
    instances = data.get("instances") or []
    # Accept the old actor-map shape during migration, but make the canonical
    # world_schema.json `instances` array the source of truth.
    if not instances and isinstance(data.get("actors"), dict):
        instances = [
            {"object": name, **(entry if isinstance(entry, dict) else {})}
            for name, entry in data["actors"].items()
        ]
    for index, entry in enumerate(instances):
        try:
            transform = _matrix_transform(entry.get("transform") or [])
            mesh_path = entry.get("static_mesh_path")
            material_role = entry.get("material_role") or entry.get("role")
            result = {
                "object": entry.get("object") or f"instance_{index}",
                "transform": transform,
                "mesh": mesh_path,
                "role": material_role,
                "applied": False,
            }
            if apply:
                result["actor"] = _apply_instance(unreal, entry, transform)
                result["applied"] = True
            results[str(result["object"])] = result
        except Exception as exc:
            results[str(entry.get("object") or f"instance_{index}")] = {"error": str(exc)}
    failures = [value for value in results.values() if "error" in value]
    return {
        "ok": not failures,
        "applied": apply,
        "instances": results,
        "errors": len(failures),
    }


def main() -> int:
    apply = "--apply" in sys.argv
    path = _resolve_manifest_path()
    if not path:
        logger.error("No manifest found via command line or cwd.")
        return 1
    result = import_manifest(path, apply=apply)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_world_manifest.py",
        **result,
        "manifest": str(path),
    }, indent=2), encoding="utf-8")
    print(f"IMPORT_MANIFEST ok={result['ok']} -> {REPORT}")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())