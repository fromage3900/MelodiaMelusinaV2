"""Import surreal_arch_world_v1 manifest into UE with schema validation.

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_world_manifest.py"
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_world_manifest.py" manifest.json

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_world_manifest.py" ^
    -manifest="G:/.../world.json" ^
    -stdout -unattended -nullrhi
"""
from __future__ import annotations

import json
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


def import_manifest(manifest_path: Path) -> dict:
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
    actors = data.get("actors") or {}
    for name, entry in actors.items():
        try:
            transform = entry.get("transform") or [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
            mesh_path = entry.get("mesh") or entry.get("static_mesh")
            material_role = entry.get("material_role") or entry.get("role")
            results[name] = {
                "transform_len": len(transform),
                "mesh": mesh_path,
                "role": material_role,
            }
        except Exception as exc:
            results[name] = {"error": str(exc)}
    return {"ok": True, "actors": results}


def main() -> int:
    path = _resolve_manifest_path()
    if not path:
        logger.error("No manifest found via command line or cwd.")
        return 1
    result = import_manifest(path)
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