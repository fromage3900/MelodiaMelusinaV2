# -*- coding: utf-8 -*-
"""Materialize the Melody Slime JSON DataTables into UE assets.

WHY
---
Content/Melodia/DataStuctures/DT_MelodySlime_{Enemies,Skills,RoomMods}.json hold
48 enemy variants (7 elements), 24 skills and 21 room mods -- authored 2026-08-11
and never imported. No DT_MelodySlime* .uasset exists anywhere in Content.

So the enemy roster is not missing; it is unimported. Owner wants Melody Slimes as
the integration map's default enemy so variants can be authored from them, and that
needs real DataTable assets backed by a UStruct row type.

Runs in the Unreal editor or UnrealEditor-Cmd after the MelodiaCore module has
been compiled and reflected. This script never invents rows or silently drops
fields.

Report: Saved/Audit/melody_slime_datatables.json
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import unreal
except ImportError:  # pragma: no cover - editor only
    unreal = None

PROJECT = (
    Path(unreal.Paths.project_dir())
    if unreal is not None
    else Path(__file__).resolve().parents[2]
)
SRC = PROJECT / "Content" / "Melodia" / "DataStuctures"
REPORT = PROJECT / "Saved" / "Audit" / "melody_slime_datatables.json"

DEST = "/Game/Melodia/DataStuctures"

TABLES = {
    "DT_MelodySlime_Enemies": {
        "row_struct": "FMelodiaSlimeEnemyRow",
        "identity_field": "enemy_id",
        "fields": {
            "enemy_id": "string",
            "display_name": "string",
            "max_hp": "float",
            "max_toughness": "float",
            "base_damage": "float",
            "speed": "int",
            "element": "string",
            "bpm": "float",
        },
        "expected_count": 48,
    },
    "DT_MelodySlime_Skills": {
        "row_struct": "FMelodiaSlimeSkillRow",
        "identity_field": "skill_id",
        "fields": {
            "skill_id": "string",
            "display_name": "string",
            "element": "string",
            "instrument": "string",
            "mechanic_level": "int",
            "sp_cost": "int",
            "power_scalar": "float",
            "note_pitches": "int_array",
            "note_durations": "float_array",
        },
        "expected_count": 24,
    },
    "DT_MelodySlime_RoomMods": {
        "row_struct": "FMelodiaSlimeRoomModRow",
        "identity_field": "blessing_id",
        "fields": {
            "blessing_id": "string",
            "display_name": "string",
            "description": "string",
            "token_cost": "int",
            "effect_type": "string",
            "effect_value": "float",
            "effect_str": "string",
            "curse": "string",
            "curse_effect": "string",
            "flavor": "string",
        },
        "expected_count": 21,
    },
}

report = {"dest": DEST, "tables": {}, "ok": False, "mutations_issued": False}


def probe_row_types():
    """Find an existing struct that could serve as the row type."""
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    out = []
    for a in ar.get_assets_by_path("/Game/Melodia", recursive=True):
        cls = str(a.asset_class_path.asset_name) if hasattr(a, "asset_class_path") else ""
        if cls in ("UserDefinedStruct", "ScriptStruct"):
            out.append(str(a.package_name))
    return out


def load_source(name: str) -> tuple[dict | None, list[str]]:
    """Load and validate one checked-in source table without Unreal."""
    spec = TABLES[name]
    src = SRC / f"{name}.json"
    if not src.is_file():
        return None, [f"source_missing_{name}"]
    try:
        payload = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"source_unreadable_{name}_{exc}"]
    if not isinstance(payload, dict) or not isinstance(payload.get("Rows"), dict):
        return None, [f"source_rows_object_required_{name}"]
    rows = payload["Rows"]
    errors: list[str] = []
    if len(rows) != spec["expected_count"]:
        errors.append(f"{name}_row_count_{len(rows)}_not_{spec['expected_count']}")
    fields = spec["fields"]
    for row_name, row in rows.items():
        if not isinstance(row_name, str) or not row_name.strip():
            errors.append(f"{name}_row_name_invalid")
            continue
        if not isinstance(row, dict):
            errors.append(f"{name}_{row_name}_must_be_object")
            continue
        missing = sorted(set(fields) - set(row))
        extra = sorted(set(row) - set(fields))
        if missing:
            errors.append(f"{name}_{row_name}_missing_{','.join(missing)}")
        if extra:
            errors.append(f"{name}_{row_name}_unknown_{','.join(extra)}")
        for field, kind in fields.items():
            if field not in row:
                continue
            value = row[field]
            valid = (
                isinstance(value, str) if kind == "string"
                else isinstance(value, int) and not isinstance(value, bool)
                if kind == "int"
                else isinstance(value, (int, float)) and not isinstance(value, bool)
                if kind == "float"
                else isinstance(value, list)
                and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
                if kind == "int_array"
                else isinstance(value, list)
                and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
            )
            if not valid:
                errors.append(f"{name}_{row_name}_{field}_type_{kind}")
        identity = spec["identity_field"]
        if isinstance(row.get(identity), str) and not row[identity].strip():
            errors.append(f"{name}_{row_name}_{identity}_empty")
    return {
        "source": str(src),
        "data_type": payload.get("DataType"),
        "rows": rows,
        "payload": payload,
        "import_rows": [
            {"Name": row_name, **values}
            for row_name, values in rows.items()
        ],
    }, errors


def load_all_sources() -> tuple[dict[str, dict], list[str]]:
    sources: dict[str, dict] = {}
    errors: list[str] = []
    for name in TABLES:
        source, source_errors = load_source(name)
        if source is not None:
            sources[name] = source
        errors.extend(source_errors)
    return sources, errors


def _struct_path(struct_name: str) -> str:
    reflected_name = struct_name[1:] if struct_name.startswith("F") else struct_name
    return f"/Script/MelodiaCore.{reflected_name}"


def resolve_row_struct(struct_name: str):
    """Resolve a compiled native FTableRowBase struct or fail closed."""
    if unreal is None:
        raise RuntimeError("unreal_module_unavailable")
    if not hasattr(unreal, "load_object"):
        raise RuntimeError("unreal_load_object_unavailable")
    row_struct = unreal.load_object(None, _struct_path(struct_name))
    if not row_struct:
        raise RuntimeError(f"row_struct_unavailable_compile_required_{struct_name}")
    reflected_name = struct_name[1:] if struct_name.startswith("F") else struct_name
    if not bool(getattr(row_struct, "get_name", lambda: "")() == reflected_name):
        raise RuntimeError(f"row_struct_name_mismatch_{struct_name}")
    return row_struct


def _row_names(table) -> list[str]:
    return sorted(str(name).split(".")[-1] for name in table.get_row_names())


def _create_or_load_table(name: str, row_struct):
    path = f"{DEST}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        table = unreal.EditorAssetLibrary.load_asset(path)
        if not table:
            raise RuntimeError(f"datatable_load_failed_{name}")
        actual = table.get_editor_property("row_struct")
        actual_name = getattr(actual, "get_name", lambda: "")()
        if actual_name != TABLES[name]["row_struct"]:
            raise RuntimeError(
                f"datatable_row_struct_mismatch_{name}_{actual_name}_not_"
                f"{TABLES[name]['row_struct']}"
            )
        return table, False
    factory = unreal.DataTableFactory()
    factory.set_editor_property("struct", row_struct)
    package_path, asset_name = path.rsplit("/", 1)
    table = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package_path, unreal.DataTable, factory
    )
    if not table:
        raise RuntimeError(f"datatable_create_failed_{name}")
    return table, True


def materialize_table(name: str, source: dict) -> dict:
    """Write, save, and independently read back one validated DataTable."""
    spec = TABLES[name]
    path = f"{DEST}/{name}"
    row_struct = resolve_row_struct(spec["row_struct"])
    table, created_new = _create_or_load_table(name, row_struct)
    try:
        imported = bool(table.fill_from_json_string(
            json.dumps(source["import_rows"], separators=(",", ":")),
            row_struct,
        ))
        if not imported:
            raise RuntimeError(f"datatable_json_import_failed_{name}")
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(
            table, only_if_is_dirty=False
        ))
        if not saved:
            raise RuntimeError(f"datatable_save_failed_{name}")
        reloaded = unreal.EditorAssetLibrary.load_asset(path)
        if not reloaded:
            raise RuntimeError(f"datatable_reload_failed_{name}")
        actual_keys = _row_names(reloaded)
        expected_keys = sorted(source["rows"])
        if actual_keys != expected_keys:
            raise RuntimeError(
                f"datatable_keys_mismatch_{name}_{actual_keys}_not_{expected_keys}"
            )
        return {
            "path": path,
            "row_struct": spec["row_struct"],
            "created_new": created_new,
            "saved": True,
            "row_count": len(actual_keys),
            "keys": actual_keys,
            "readback_ok": True,
        }
    except Exception as exc:
        if created_new:
            try:
                deleted = bool(unreal.EditorAssetLibrary.delete_asset(path))
            except Exception as cleanup_exc:
                raise RuntimeError(
                    f"{exc}; cleanup_failed_{path}_{cleanup_exc}"
                ) from exc
            if not deleted:
                raise RuntimeError(f"{exc}; cleanup_delete_returned_false_{path}") from exc
        raise


def main() -> int:
    if unreal is None:
        report["errors"] = ["unreal_module_unavailable"]
        return 2
    sources, source_errors = load_all_sources()
    report["source_errors"] = source_errors
    report["source_counts"] = {
        name: len(source["rows"]) for name, source in sources.items()
    }
    if source_errors:
        report["errors"] = source_errors
        return 1
    created_new_paths: list[str] = []
    try:
        report["existing_structs"] = probe_row_types()
        for name, source in sources.items():
            report["tables"][name] = {
                "source": source["source"],
                "row_count": len(source["rows"]),
                "status": "source_validated",
            }
        # Resolve every native struct before creating any DataTable. A missing
        # reflected type therefore cannot leave a partially materialized batch.
        for spec in TABLES.values():
            resolve_row_struct(spec["row_struct"])
        report["mutations_issued"] = True
        for name, source in sources.items():
            table_report = materialize_table(name, source)
            report["tables"][name] = table_report
            if table_report.get("created_new"):
                created_new_paths.append(table_report["path"])
        report["ok"] = True
        return 0
    except Exception as exc:
        report["errors"] = [str(exc)]
        cleanup: list[dict[str, object]] = []
        for path in reversed(created_new_paths):
            try:
                cleanup.append({
                    "path": path,
                    "deleted": bool(unreal.EditorAssetLibrary.delete_asset(path)),
                })
            except Exception as cleanup_exc:
                cleanup.append({
                    "path": path,
                    "deleted": False,
                    "error": str(cleanup_exc),
                })
        if cleanup:
            report["cleanup_new_assets"] = cleanup
        return 1


if __name__ == "__main__":
    exit_code = main()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if unreal:
        unreal.log("SLIME_DT_REPORT:" + json.dumps(report)[:2000])
    raise SystemExit(exit_code)
