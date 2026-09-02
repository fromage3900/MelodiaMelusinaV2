# -*- coding: utf-8 -*-
"""Materialize the roguelike JSON DataTables that shipped without (or with wrong) .uasset row types.

WHY
---
Content/Melodia/DataStuctures/*.json are checked-in source contracts:

  DT_Burdens.json      (21 rows) — .uasset exists but uses UserDefinedStruct, not FTableRowBase
  DT_Blessings.json    (26 rows) — NO .uasset
  DT_Artifacts.json    ( 4 rows) — NO .uasset
  DT_MelodiaTokens.json( 8 rows) — NO .uasset
  DT_RoguelikeRooms.json( 6 rows) — NO .uasset

The MelodySlime triple (Enemies/Skills/RoomMods) already import via
Content/Python/import_melody_slime_datatables.py against FMelodiaSlime*Row.
These five need MelodiaRoguelikeDataRows.h (FMelodiaRoguelikeBurdenRow etc).
Until that header is compiled, this script fails closed with
row_struct_unavailable_compile_required_* — it never creates a Generic-typed table.

DT_Burdens note: the existing .uasset is UserDefinedStruct-typed. This script
re-creates it as native FTableRowBase. Pass --force-reimport-burdens to replace it;
without the flag it validates the source but leaves the existing asset alone and
reports row_struct_mismatch so the mis-type is not silent.

Runs in a single editor only:

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=py "Content/Python/import_roguelike_datatables.py"
    # or inside an open editor:
    py Content/Python/import_roguelike_datatables.py --force-reimport-burdens
    py Content/Python/import_roguelike_datatables.py --verify-only

Report: Saved/Audit/roguelike_datatables.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import unreal
except ImportError:  # pragma: no cover
    unreal = None

PROJECT = Path(unreal.Paths.project_dir()) if unreal is not None else Path(__file__).resolve().parents[2]
SRC = PROJECT / "Content" / "Melodia" / "DataStuctures"
REPORT = PROJECT / "Saved" / "Audit" / "roguelike_datatables.json"
DEST = "/Game/Melodia/DataStuctures"

TABLES = {
    "DT_Burdens": {
        "row_struct": "FMelodiaRoguelikeBurdenRow",
        "identity_field": "burden_id",
        "fields": {
            "burden_id": "string", "display_name": "string", "description": "string",
            "rule_type": "string", "magnitude": "float", "duration_or_scope": "string",
            "stack_policy": "string", "source_content_pack": "string",
            "paired_blessing_id": "string", "source_row": "string",
        },
        "expected_count": 21,
    },
    "DT_Blessings": {
        "row_struct": "FMelodiaRoguelikeBlessingRow",
        "identity_field": "blessing_id",
        "fields": {
            "blessing_id": "string", "display_name": "string", "description": "string",
            "token_cost": "int", "effect_type": "string", "effect_value": "float", "effect_str": "string",
        },
        "expected_count": 26,
    },
    "DT_Artifacts": {
        "row_struct": "FMelodiaRoguelikeArtifactRow",
        "identity_field": "artifact_id",
        "fields": {
            "artifact_id": "string", "display_name": "string", "description": "string",
            "modifier_id": "string", "cost_golden_tokens": "int",
        },
        "expected_count": 4,
    },
    "DT_MelodiaTokens": {
        "row_struct": "FMelodiaTokenTypeRow",
        "identity_field": "TokenID",
        "fields": {
            "TokenID": "string", "DisplayName": "string", "Description": "string",
            "Element": "string", "Value": "int", "Rarity": "string",
            "TexturePath": "string", "MaterialPath": "string",
        },
        "expected_count": 8,
    },
    "DT_RoguelikeRooms": {
        "row_struct": "FMelodiaRoguelikeRoomRow",
        "identity_field": "room_id",
        "fields": {
            "room_id": "string", "display_name": "string", "enemy_pool": "string_array",
            "token_shrine_chance": "float", "is_boss_room": "bool",
            "is_shop_room": "bool", "is_treasure_room": "bool",
        },
        "expected_count": 6,
    },
}

report: dict = {"dest": DEST, "tables": {}, "ok": False, "mutations_issued": False}


def _struct_path(name: str) -> str:
    short = name[1:] if name.startswith("F") else name
    return f"/Script/MelodiaCore.{short}"


def resolve_row_struct(name: str):
    if unreal is None:
        raise RuntimeError("unreal_module_unavailable")
    s = unreal.load_object(None, _struct_path(name))
    if not s:
        raise RuntimeError(f"row_struct_unavailable_compile_required_{name}")
    short = name[1:] if name.startswith("F") else name
    if getattr(s, "get_name", lambda: "")() != short:
        raise RuntimeError(f"row_struct_name_mismatch_{name}")
    return s


def load_source(table_name: str):
    spec = TABLES[table_name]
    src = SRC / f"{table_name}.json"
    if not src.is_file():
        return None, [f"source_missing_{table_name}"]
    payload = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("Rows"), dict):
        return None, [f"source_rows_object_required_{table_name}"]
    rows = payload["Rows"]
    errors: list[str] = []
    if len(rows) != spec["expected_count"]:
        errors.append(f"{table_name}_row_count_{len(rows)}_not_{spec['expected_count']}")
    for row_name, row in rows.items():
        missing = sorted(set(spec["fields"]) - set(row))
        extra = sorted(set(row) - set(spec["fields"]))
        if missing:
            errors.append(f"{table_name}_{row_name}_missing_{','.join(missing)}")
        if extra:
            errors.append(f"{table_name}_{row_name}_unknown_{','.join(extra)}")
        for field, kind in spec["fields"].items():
            if field not in row:
                continue
            v = row[field]
            if kind == "string":
                ok = isinstance(v, str)
            elif kind == "int":
                ok = isinstance(v, int) and not isinstance(v, bool)
            elif kind == "float":
                ok = isinstance(v, (int, float)) and not isinstance(v, bool)
            elif kind == "string_array":
                ok = isinstance(v, list) and all(isinstance(x, str) for x in v)
            elif kind == "bool":
                ok = isinstance(v, bool)
            else:
                ok = False
            if not ok:
                errors.append(f"{table_name}_{row_name}_{field}_type_{kind}")
    return {"source": str(src), "rows": rows, "payload": payload,
            "import_rows": [{"Name": k, **v} for k, v in rows.items()]}, errors


def _row_names(table) -> list[str]:
    return sorted(str(n).split(".")[-1] for n in table.get_row_names())


def _create_or_load(name: str, row_struct, force: bool = False):
    path = f"{DEST}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if name == "DT_Burdens" and not force:
            table = unreal.EditorAssetLibrary.load_asset(path)
            actual = table.get_editor_property("row_struct") if table else None
            actual_name = getattr(actual, "get_name", lambda: "")() if actual else "<?>"
            # Surface the mis-type without mutating; caller reports it
            raise RuntimeError(f"datatable_row_struct_mismatch_{name}_{actual_name}_not_{TABLES[name]['row_struct']}_use_--force-reimport-burdens")
        # For non-Burdens, if exists just validate struct
        table = unreal.EditorAssetLibrary.load_asset(path)
        if not table:
            raise RuntimeError(f"datatable_load_failed_{name}")
        actual = table.get_editor_property("row_struct")
        actual_name = getattr(actual, "get_name", lambda: "")()
        if actual_name != TABLES[name]["row_struct"]:
            if force:
                unreal.EditorAssetLibrary.delete_asset(path)
            else:
                raise RuntimeError(f"datatable_row_struct_mismatch_{name}_{actual_name}_not_{TABLES[name]['row_struct']}")
        if force and unreal.EditorAssetLibrary.does_asset_exist(path):
            table = unreal.EditorAssetLibrary.load_asset(path)
            return table, False
        if not unreal.EditorAssetLibrary.does_asset_exist(path) or force:
            pass
        else:
            return table, False
    factory = unreal.DataTableFactory()
    factory.set_editor_property("struct", row_struct)
    pkg, asset = path.rsplit("/", 1)
    table = unreal.AssetToolsHelpers.get_asset_tools().create_asset(asset, pkg, unreal.DataTable, factory)
    if not table:
        raise RuntimeError(f"datatable_create_failed_{name}")
    return table, True


def materialize(name: str, source: dict, row_struct, force: bool):
    spec = TABLES[name]
    path = f"{DEST}/{name}"
    if name == "DT_Burdens" and force and unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    table, created = _create_or_load(name, row_struct, force=force)
    imported = bool(table.fill_from_json_string(json.dumps(source["import_rows"], separators=(",", ":")), row_struct))
    if not imported:
        raise RuntimeError(f"datatable_json_import_failed_{name}")
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(table, only_if_is_dirty=False))
    if not saved:
        raise RuntimeError(f"datatable_save_failed_{name}")
    reloaded = unreal.EditorAssetLibrary.load_asset(path)
    actual_keys = _row_names(reloaded)
    expected_keys = sorted(source["rows"])
    if actual_keys != expected_keys:
        raise RuntimeError(f"datatable_keys_mismatch_{name}_{actual_keys}_not_{expected_keys}")
    return {"path": path, "row_struct": spec["row_struct"], "created_new": created,
            "saved": True, "row_count": len(actual_keys), "keys": actual_keys, "readback_ok": True}


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    verify_only = "--verify-only" in argv or "--dry-run" in argv
    force_burdens = "--force-reimport-burdens" in argv
    if unreal is None:
        report["errors"] = ["unreal_module_unavailable"]
        return 2
    sources: dict[str, dict] = {}
    all_errors: list[str] = []
    for name in TABLES:
        src, errs = load_source(name)
        if src is not None:
            sources[name] = src
        all_errors.extend(errs)
    report["source_counts"] = {n: len(s["rows"]) for n, s in sources.items()}
    report["source_errors"] = [e for e in all_errors if not e.startswith("DT_Burdens_row_struct")]
    if report["source_errors"]:
        report["errors"] = report["source_errors"]
        return 1
    # Resolve structs (fail closed if header not compiled)
    try:
        for spec in TABLES.values():
            resolve_row_struct(spec["row_struct"])
    except Exception as exc:
        # In verify-only, report as source-validated without requiring compile
        if verify_only:
            for name, src in sources.items():
                report["tables"][name] = {"source": src["source"], "row_count": len(src["rows"]), "status": "source_validated_struct_not_compiled", "row_struct": TABLES[name]["row_struct"], "note": str(exc)}
            report["ok"] = True
            report["mutations_issued"] = False
            return 0
        report["errors"] = [str(exc)]
        return 1
    if verify_only:
        for name, src in sources.items():
            report["tables"][name] = {"source": src["source"], "row_count": len(src["rows"]), "status": "source_validated", "row_struct": TABLES[name]["row_struct"]}
        report["ok"] = True
        return 0
    report["mutations_issued"] = True
    created: list[str] = []
    try:
        for name, src in sources.items():
            if name == "DT_Burdens" and not force_burdens:
                # Report the mis-type without mutating
                try:
                    rs = resolve_row_struct(TABLES[name]["row_struct"])
                    materialize(name, src, rs, force=False)
                except RuntimeError as e:
                    if "row_struct_mismatch" in str(e):
                        report["tables"][name] = {"source": src["source"], "row_count": len(src["rows"]), "status": "existing_asset_row_struct_mismatch_needs_--force-reimport-burdens", "error": str(e), "row_struct_expected": TABLES[name]["row_struct"]}
                        continue
                    raise
            else:
                rs = resolve_row_struct(TABLES[name]["row_struct"])
                r = materialize(name, src, rs, force=force_burdens)
                report["tables"][name] = r
                if r.get("created_new"):
                    created.append(r["path"])
        report["ok"] = True
        return 0
    except Exception as exc:
        report["errors"] = [str(exc)]
        # cleanup newly created assets on failure
        for p in reversed(created):
            try:
                unreal.EditorAssetLibrary.delete_asset(p)
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    code = main()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if unreal:
        unreal.log("ROGUE_DT_REPORT:" + json.dumps(report)[:2000])
    raise SystemExit(code)
