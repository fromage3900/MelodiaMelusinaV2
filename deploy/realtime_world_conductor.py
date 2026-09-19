#!/usr/bin/env python3
"""Realtime world conductor — watch surreal_arch_world_v1 manifests and
hot-reimport only dirty HISM groups.

This is a conductor, not a sixth Monolith agent and not a second world
compiler. It composes with:

  deploy/monolith_orchestrator.py          5-agent health / routing
  deploy/start_world_loop.ps1              10m world micro-cycle + run_verify
  Content/Python/import_world_manifest.py  authored-actor import (WIA)
  deploy/probe_world_pipeline.py           Blender addon probe (not CI-importable)
  Content/Python/gmm/pcg/manifest.py       structural v1/v2 contract

Usage:
  python deploy/realtime_world_conductor.py --once
  python deploy/realtime_world_conductor.py --once --manifest path/to/root.world.json
  python deploy/realtime_world_conductor.py --watch --interval 5
  python deploy/realtime_world_conductor.py --once --apply   # UE session only

Offline --once is SOURCE-TOOL PROVEN. Live HISM hot-reimport is not claimed
until a UE session writes a receipt through import_world_manifest --apply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_PY = PROJECT_ROOT / "Content" / "Python"
DEPLOY = PROJECT_ROOT / "deploy"
AUDIT = PROJECT_ROOT / "Saved" / "Audit"
SCHEMA_PATH = PROJECT_ROOT / "Config" / "world_schema.json"
STATUS_PATH = AUDIT / "realtime_world_conductor_status.json"
RECEIPT_PATH = AUDIT / "realtime_world_conductor_receipt.json"
STOP_SENTINEL = DEPLOY / "SURREAL_REALTIME_WORLD_LOOP_STOP"
FORMAT_ID = "surreal_arch_world_v1"

DEFAULT_SEARCH_ROOTS = (
    PROJECT_ROOT / "deploy" / "fixtures",
    PROJECT_ROOT / "Saved" / "WorldExport",
)

if str(CONTENT_PY) not in sys.path:
    sys.path.insert(0, str(CONTENT_PY))
if str(DEPLOY) not in sys.path:
    sys.path.insert(0, str(DEPLOY))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema() -> dict | None:
    if not SCHEMA_PATH.exists():
        return None
    return _load_json(SCHEMA_PATH)


def structural_errors(data: Any) -> list[str]:
    """v1-safe required-field check that does not need jsonschema."""
    if not isinstance(data, dict):
        return ["manifest root must be an object"]
    errors: list[str] = []
    if data.get("format") != FORMAT_ID:
        errors.append(f"format must be {FORMAT_ID!r}")
    version = data.get("schema_version")
    if not isinstance(version, int) or version < 1:
        errors.append("schema_version must be a positive integer")
    if not isinstance(data.get("coordinate_system"), str) or not data.get("coordinate_system"):
        errors.append("coordinate_system must be a non-empty string")
    instances = data.get("instances")
    if not isinstance(instances, list):
        errors.append("instances must be an array")
        return errors
    if data.get("instance_count") != len(instances):
        errors.append("instance_count must equal len(instances)")
    for index, entry in enumerate(instances):
        prefix = f"instances[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("role", "lib", "object"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                errors.append(f"{prefix}.{field} must be a non-empty string")
        transform = entry.get("transform")
        if not (
            isinstance(transform, list)
            and len(transform) == 4
            and all(isinstance(row, list) and len(row) == 4 for row in transform)
        ):
            errors.append(f"{prefix}.transform must be a 4x4 matrix")
    return errors


def jsonschema_errors(data: dict) -> list[str]:
    schema = load_schema()
    if schema is None:
        return ["schema file missing"]
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []
    validator = jsonschema.Draft7Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(data), key=str)]


def gmm_errors(data: dict) -> list[str]:
    try:
        from gmm.pcg.manifest import validate_manifest
    except Exception:
        return []
    try:
        return list(validate_manifest(data, require_resolved_meshes=False))
    except Exception as exc:
        return [f"gmm validate failed: {exc}"]


def validate_manifest(data: Any) -> dict:
    structural = structural_errors(data)
    schema = jsonschema_errors(data) if isinstance(data, dict) and data.get("format") == FORMAT_ID else []
    gmm = gmm_errors(data) if isinstance(data, dict) and data.get("format") == FORMAT_ID else []
    errors = structural + [f"jsonschema: {msg}" for msg in schema] + [f"gmm: {msg}" for msg in gmm]
    return {
        "ok": not structural and not schema,
        "structural": structural,
        "jsonschema": schema,
        "gmm": gmm,
        "errors": errors,
    }


def group_key(role: str, lib: str, static_mesh_path: str = "") -> str:
    return f"{role}|{lib}|{static_mesh_path}"


def build_hism_groups(instances: list[dict]) -> list[dict]:
    """Same grouping as deploy/surreal_world/export.py, without importing bpy."""
    groups: dict[tuple[str, str, str], dict] = {}
    for entry in instances:
        role = str(entry.get("role") or "")
        lib = str(entry.get("lib") or "")
        mesh = str(entry.get("static_mesh_path") or "")
        key = (role, lib, mesh)
        if key not in groups:
            groups[key] = {
                "role": role,
                "lib": lib,
                "ue_material_hint": entry.get("ue_material_hint", ""),
                "static_mesh_path": mesh,
                "lod_group": entry.get("lod_group", ""),
                "stream_priority": entry.get("stream_priority"),
                "sector_id": entry.get("sector_id", ""),
                "instance_count": 0,
                "transforms": [],
            }
        groups[key]["transforms"].append(entry.get("transform"))
        groups[key]["instance_count"] += 1
    return list(groups.values())


def groups_from_manifest(data: dict) -> list[dict]:
    groups = data.get("hism_groups")
    if isinstance(groups, list) and groups:
        return [group for group in groups if isinstance(group, dict)]
    return build_hism_groups(list(data.get("instances") or []))


def fingerprint_group(group: dict) -> dict:
    role = str(group.get("role") or "")
    lib = str(group.get("lib") or "")
    mesh = str(group.get("static_mesh_path") or "")
    payload = {
        "role": role,
        "lib": lib,
        "static_mesh_path": mesh,
        "ue_material_hint": group.get("ue_material_hint", ""),
        "lod_group": group.get("lod_group", ""),
        "stream_priority": group.get("stream_priority"),
        "sector_id": group.get("sector_id", ""),
        "transforms": group.get("transforms") or [],
    }
    return {
        "key": group_key(role, lib, mesh),
        "hash": _sha256_bytes(_canonical(payload).encode("utf-8")),
        "instance_count": int(group.get("instance_count") or len(group.get("transforms") or [])),
        "lod_group": group.get("lod_group") or "",
        "stream_priority": group.get("stream_priority"),
        "sector_id": str(group.get("sector_id") or ""),
    }


def load_receipt() -> dict:
    if not RECEIPT_PATH.exists():
        return {"manifests": {}}
    try:
        payload = _load_json(RECEIPT_PATH)
    except Exception:
        return {"manifests": {}}
    manifests = payload.get("manifests")
    return payload if isinstance(manifests, dict) else {"manifests": {}}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def discover_manifests(explicit: list[Path], extra_roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            return
        seen.add(resolved)
        found.append(resolved)

    for path in explicit:
        add(path)
    roots = list(extra_roots)
    if not explicit:
        roots = list(DEFAULT_SEARCH_ROOTS) + roots
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.world.json")):
            if path.name.startswith("realtime_dirty_"):
                continue
            add(path)
        for path in sorted(root.glob("world.json")):
            add(path)
    return found


def expand_tiles(manifest_path: Path, data: dict, seen: set[Path] | None = None) -> list[tuple[Path, dict]]:
    """Follow optional tiles[].manifest_path relative to the parent file."""
    if seen is None:
        seen = set()
    resolved = manifest_path.resolve()
    if resolved in seen:
        return []
    seen.add(resolved)
    out = [(manifest_path, data)]
    for tile in data.get("tiles") or []:
        if not isinstance(tile, dict):
            continue
        raw = tile.get("manifest_path")
        if not isinstance(raw, str) or not raw:
            continue
        child = Path(raw)
        if not child.is_absolute():
            child = (manifest_path.parent / child).resolve()
        if not child.is_file():
            continue
        try:
            child_data = _load_json(child)
        except Exception:
            continue
        if not isinstance(child_data, dict) or child_data.get("format") != FORMAT_ID:
            continue
        out.extend(expand_tiles(child, child_data, seen))
    return out


def filtered_manifest(data: dict, dirty_keys: set[str]) -> dict:
    instances = [
        entry
        for entry in (data.get("instances") or [])
        if isinstance(entry, dict)
        and group_key(str(entry.get("role") or ""), str(entry.get("lib") or ""), str(entry.get("static_mesh_path") or ""))
        in dirty_keys
    ]
    payload = {key: value for key, value in data.items() if key not in ("instances", "hism_groups", "instance_count")}
    payload["instances"] = instances
    payload["instance_count"] = len(instances)
    payload["hism_groups"] = [
        group
        for group in groups_from_manifest(data)
        if group_key(str(group.get("role") or ""), str(group.get("lib") or ""), str(group.get("static_mesh_path") or ""))
        in dirty_keys
    ]
    return payload


def try_import_dirty(filtered_path: Path, apply: bool) -> dict:
    """Invoke import_world_manifest when Unreal is actually present.

    CI / laptop / no-editor runs stay on the stub. probe_world_pipeline.py
    imports bpy and is never imported here.
    """
    hook = {
        "module": "import_world_manifest",
        "attempted": apply,
        "status": "not_requested",
        "todo": (
            "Inside UE: py Content/Python/import_world_manifest.py "
            f"--manifest {filtered_path} --apply"
        ),
        "probe_world_pipeline": (
            "Blender-only. Run deploy/probe_world_pipeline.py with blender "
            "--background --factory-startup --python; do not import bpy here."
        ),
    }
    if not apply:
        hook["status"] = "stubbed_offline"
        return hook
    try:
        import import_world_manifest
    except Exception as exc:
        hook["status"] = "stubbed_import_unavailable"
        hook["error"] = str(exc)
        return hook
    result = import_world_manifest.import_manifest(filtered_path, apply=True)
    hook["status"] = "applied" if result.get("ok") and result.get("applied") else "import_reported"
    hook["result"] = {
        "ok": result.get("ok"),
        "applied": result.get("applied"),
        "errors": result.get("errors"),
        "error": result.get("error"),
    }
    if result.get("error") == "unreal module unavailable":
        hook["status"] = "stubbed_offline"
        hook["todo"] = hook["todo"] + " (unreal module unavailable in this process)"
    return hook


def tick(manifests: list[Path], *, apply: bool) -> dict:
    receipt = load_receipt()
    stored = receipt.get("manifests") if isinstance(receipt.get("manifests"), dict) else {}
    new_receipt: dict[str, Any] = {}
    scanned: list[dict] = []
    dirty: list[dict] = []
    unchanged: list[dict] = []
    skipped: list[dict] = []
    schema_failures: list[dict] = []
    seen_files: set[Path] = set()

    for path in manifests:
        try:
            data = _load_json(path)
        except Exception as exc:
            skipped.append({"path": str(path), "reason": f"json load failed: {exc}"})
            continue
        if not isinstance(data, dict) or data.get("format") != FORMAT_ID:
            skipped.append({
                "path": str(path),
                "reason": f"not {FORMAT_ID} (got {data.get('format') if isinstance(data, dict) else type(data).__name__})",
            })
            continue

        for child_path, child_data in expand_tiles(path, data):
            resolved = child_path.resolve()
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            report = validate_manifest(child_data)
            world_root = str(child_data.get("world_root") or child_path.stem)
            sector_id = str(child_data.get("sector_id") or "")
            file_hash = _sha256_bytes(child_path.read_bytes())
            groups = [fingerprint_group(group) for group in groups_from_manifest(child_data)]
            previous = stored.get(str(child_path)) if isinstance(stored.get(str(child_path)), dict) else {}
            previous_groups = previous.get("groups") if isinstance(previous.get("groups"), dict) else {}

            group_records = {}
            file_dirty: list[dict] = []
            file_unchanged: list[dict] = []
            current_keys = {item["key"] for item in groups}
            for item in groups:
                group_records[item["key"]] = item
                old_hash = (previous_groups.get(item["key"]) or {}).get("hash")
                record = {
                    "path": str(child_path),
                    "world_root": world_root,
                    "sector_id": sector_id or item.get("sector_id") or "",
                    "group": item["key"],
                    "instance_count": item["instance_count"],
                    "lod_group": item.get("lod_group") or "",
                    "stream_priority": item.get("stream_priority"),
                    "hash": item["hash"],
                }
                if old_hash != item["hash"]:
                    record["change"] = "added" if old_hash is None else "modified"
                    file_dirty.append(record)
                else:
                    record["change"] = "unchanged"
                    file_unchanged.append(record)
            for old_key in previous_groups:
                if old_key not in current_keys:
                    file_dirty.append({
                        "path": str(child_path),
                        "world_root": world_root,
                        "sector_id": sector_id,
                        "group": old_key,
                        "change": "removed",
                    })

            scanned.append({
                "path": str(child_path),
                "world_root": world_root,
                "sector_id": sector_id,
                "schema_version": child_data.get("schema_version"),
                "instance_count": child_data.get("instance_count"),
                "group_count": len(groups),
                "seed": child_data.get("seed"),
                "biome_tags": child_data.get("biome_tags") or [],
                "validation": report,
            })
            if not report["ok"]:
                schema_failures.append({"path": str(child_path), "errors": report["errors"]})

            dirty_path = None
            apply_hook = None
            dirty_keys = {item["group"] for item in file_dirty if item.get("change") != "removed"}
            if dirty_keys and report["ok"]:
                filtered = filtered_manifest(child_data, dirty_keys)
                token = f"{world_root}_{sector_id or 'root'}"
                safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in token)
                dirty_path = AUDIT / f"realtime_dirty_{safe}.world.json"
                save_json(dirty_path, filtered)
                apply_hook = try_import_dirty(dirty_path, apply=apply)

            dirty.extend(file_dirty)
            unchanged.extend(file_unchanged)
            new_receipt[str(child_path)] = {
                "sha256": file_hash,
                "mtime": child_path.stat().st_mtime,
                "world_root": world_root,
                "sector_id": sector_id,
                "groups": group_records,
                "dirty_manifest": str(dirty_path) if dirty_path else None,
                "apply": apply_hook,
            }

    apply_hooks = [
        record.get("apply")
        for record in new_receipt.values()
        if isinstance(record, dict) and record.get("apply")
    ]
    status = {
        "generated_at": _now(),
        "generated_by": "realtime_world_conductor.py",
        "ok": not schema_failures,
        "evidence_level": "SOURCE-TOOL PROVEN; not LIVE PROVEN",
        "format": FORMAT_ID,
        "manifests_scanned": len(scanned),
        "dirty_group_count": len(dirty),
        "unchanged_group_count": len(unchanged),
        "skipped": skipped,
        "schema_failures": schema_failures,
        "dirty_groups": dirty,
        "unchanged_groups": unchanged,
        "scanned": scanned,
        "apply": apply_hooks[0] if len(apply_hooks) == 1 else apply_hooks,
        "hooks": {
            "import_world_manifest": "Content/Python/import_world_manifest.py (UE --apply; stubbed without unreal)",
            "probe_world_pipeline": "deploy/probe_world_pipeline.py (Blender; never imported here)",
            "monolith_orchestrator": "deploy/monolith_orchestrator.py --workflow realtime_world",
            "world_loop": "deploy/start_world_loop.ps1 (compose, do not replace)",
        },
        "receipt": str(RECEIPT_PATH),
    }
    save_json(STATUS_PATH, status)
    save_json(RECEIPT_PATH, {
        "generated_at": _now(),
        "generated_by": "realtime_world_conductor.py",
        "manifests": new_receipt,
    })
    return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("Usage:", 1)[0].strip())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Single diff pass (default).")
    mode.add_argument("--watch", action="store_true", help="Poll until the stop sentinel exists.")
    parser.add_argument("--interval", type=float, default=5.0, help="Watch interval in seconds.")
    parser.add_argument("--manifest", action="append", default=[], help="Explicit manifest path. Repeatable.")
    parser.add_argument("--root", action="append", default=[], help="Extra search directory. Repeatable.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Attempt import_world_manifest --apply for dirty groups. No-ops without Unreal.",
    )
    args = parser.parse_args(argv)
    if not args.watch:
        args.once = True
    return args


def resolve_manifests(args: argparse.Namespace) -> list[Path]:
    explicit = [Path(item) for item in args.manifest]
    roots = [Path(item) for item in args.root]
    return discover_manifests(explicit, roots)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    AUDIT.mkdir(parents=True, exist_ok=True)
    if args.watch:
        print(f"[realtime-world] watch interval={args.interval}s stop={STOP_SENTINEL}")
        if STOP_SENTINEL.exists():
            STOP_SENTINEL.unlink()
        while True:
            if STOP_SENTINEL.exists():
                print("[realtime-world] stop sentinel detected")
                break
            status = tick(resolve_manifests(args), apply=args.apply)
            print(
                f"[realtime-world] ok={status['ok']} scanned={status['manifests_scanned']} "
                f"dirty={status['dirty_group_count']} -> {STATUS_PATH}"
            )
            time.sleep(max(0.5, args.interval))
        return 0
    status = tick(resolve_manifests(args), apply=args.apply)
    print(f"REALTIME_WORLD_CONDUCTOR ok={status['ok']} dirty={status['dirty_group_count']} -> {STATUS_PATH}")
    return 0 if status.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
