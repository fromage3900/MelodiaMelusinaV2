"""Validate or import a Melodia audio-terrain handoff into Unreal Engine 5.8.

Default mode is offline/read-only validation.  ``--apply`` must run inside the
Unreal Python environment and imports every manifest FBX into deterministic
builder/preset/time folders beneath the manifest's recommended content path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "melodia.audio_terrain_ue_handoff.v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_handoff(path: str | Path) -> dict:
    manifest_path = Path(path).resolve()
    errors: list[str] = []
    if not manifest_path.is_file():
        return {"ok": False, "errors": [f"manifest missing: {manifest_path}"], "artifacts": 0}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        errors.append(f"unexpected schema: {data.get('schema')!r}")
    ue = data.get("ue") or {}
    if ue.get("engine") != "5.8":
        errors.append("handoff is not targeted to UE 5.8")
    root = str(ue.get("recommended_content_path") or "")
    if not root.startswith("/Game/"):
        errors.append("recommended_content_path must start with /Game/")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty list")
        artifacts = []
    seen_tiles = set()
    importable = []
    for index, artifact in enumerate(artifacts):
        prefix = f"artifact[{index}]"
        tile = artifact.get("tile") or {}
        identity = (
            artifact.get("builder"), artifact.get("preset"), artifact.get("sample_time"),
            tile.get("x"), tile.get("y"),
        )
        if identity in seen_tiles:
            errors.append(f"{prefix}: duplicate builder/preset/time/tile identity")
        seen_tiles.add(identity)
        fbx = artifact.get("fbx")
        if not isinstance(fbx, dict):
            continue
        fbx_path = Path(str(fbx.get("path") or ""))
        if not fbx_path.is_file():
            errors.append(f"{prefix}: FBX missing: {fbx_path}")
            continue
        if fbx_path.stat().st_size != int(fbx.get("bytes") or -1):
            errors.append(f"{prefix}: FBX byte size mismatch")
            continue
        if _sha256(fbx_path) != fbx.get("sha256"):
            errors.append(f"{prefix}: FBX SHA-256 mismatch")
            continue
        importable.append(index)
    return {
        "ok": not errors,
        "errors": errors,
        "manifest": str(manifest_path),
        "artifacts": len(artifacts),
        "importable_fbx": len(importable),
        "recommended_content_path": root,
        "data": data,
    }


def _segment(value) -> str:
    text = str(value)
    return "".join(c if c.isalnum() or c == "_" else "_" for c in text).strip("_")


def apply_handoff(report: dict) -> dict:
    if not report.get("ok"):
        raise RuntimeError("refusing import: handoff validation failed")
    import unreal

    data = report["data"]
    root = report["recommended_content_path"].rstrip("/")
    tasks = []
    destinations = []
    for artifact in data["artifacts"]:
        fbx = artifact.get("fbx")
        if not fbx:
            continue
        sample = f"T{float(artifact['sample_time']):g}".replace(".", "_")
        destination = "/".join((
            root, _segment(artifact["builder"]), _segment(artifact["preset"]), sample,
        ))
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", fbx["path"])
        task.set_editor_property("destination_path", destination)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        task.set_editor_property("options", options)
        tasks.append(task)
        destinations.append(destination)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    imported = [asset for task in tasks for asset in task.get_editor_property("imported_object_paths")]
    result = {"ok": len(imported) == len(tasks), "tasks": len(tasks), "imported": imported, "destinations": destinations}
    unreal.log(f"MELODIA_AUDIO_TERRAIN_IMPORT {json.dumps(result)}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    report = validate_handoff(args.manifest)
    printable = {k: v for k, v in report.items() if k != "data"}
    if args.apply and report["ok"]:
        printable["apply"] = apply_handoff(report)
    print(json.dumps(printable, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
