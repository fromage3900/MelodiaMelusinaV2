# -*- coding: utf-8 -*-
"""Materialize the catalog-first Melusina V2 wardrobe source contract.

WHY THIS IS THE BLOCKER
-----------------------
`UMelodiaWardrobeSubsystem` is catalog-first and fails closed. `GrantCosmetic` and
`EquipCosmetic` both resolve the id through `FindGrantableRecord` BEFORE touching
`FMelodiaNarrativeRecord`, and refuse with a typed reason -- `no_catalog`,
`unknown_id`, `unauthored_mesh`, or `missing_mesh` -- if it does not resolve.

That is deliberate: `OwnedCosmeticIds` is persisted, so an unvalidated grant writes a
permanently unresolvable id into the save. Until this asset exists, nothing can be
granted or equipped. The subsystem logs the absence once per session at Error level
rather than failing silently.

WHAT THIS AUTHORS
-----------------
The first-outfit source manifest's five V2 pieces as decorative cosmetics --
`ResonantFormId` left as None. That is
the documented common case: most cosmetics never touch the form layer, and capabilities
belong to Resonant Forms rather than to individual garments, so a recolour never needs
its own gameplay wiring.

`Rarity` is `Common` on all five first-outfit records. The larger draft lane keeps
`Refined`/`Couture` as explicit owner decisions; those values are rejected until
the owner maps them to the reflected enum, never silently coerced to `Common`.

The source manifest, not this script, owns IDs, slots, rarity, and mesh paths. The
script refuses to replace an existing mismatched catalog unless
`--replace-existing` is explicit. `--verify-only` and `--dry-run` never write assets.

Run in the editor, one editor only:

    editor_query run_python: Content/Python/create_melodia_cosmetic_catalog.py
    ... -- --verify-only       to inspect inputs/readback without writing
    ... -- --dry-run           alias for --verify-only
    ... -- --replace-existing  explicit replacement after a failed readback
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import unreal
except ImportError:  # pragma: no cover - editor only
    unreal = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MANIFEST = PROJECT_ROOT / "specs" / "wardrobe" / "wardrobe_catalog_manifest.v1.json"
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_cosmetic_catalog_create.json"

DEFAULT_CATALOG_PATH = "/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog"


def log(msg: str) -> None:
    line = f"[cosmetic-catalog] {msg}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


def argv() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load_source() -> tuple[dict | None, list[dict], list[str]]:
    """Load and structurally validate the checked-in source manifest."""
    try:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [], [f"source_manifest_unreadable_{exc}"]
    if not isinstance(manifest, dict):
        return None, [], ["source_manifest_must_be_object"]
    if manifest.get("schema") != "melodia.wardrobe_catalog_contract.v1":
        return manifest, [], ["source_manifest_schema_mismatch"]
    first = manifest.get("first_outfit")
    if not isinstance(first, dict):
        return manifest, [], ["first_outfit_missing"]
    records = first.get("records")
    if not isinstance(records, list) or not records:
        return manifest, [], ["first_outfit_records_missing"]
    errors: list[str] = []
    if manifest.get("catalog_asset", DEFAULT_CATALOG_PATH) != DEFAULT_CATALOG_PATH:
        errors.append("catalog_asset_path_mismatch")
    if manifest.get("gacha_enabled") is not False:
        errors.append("gacha_must_remain_disabled")
    if manifest.get("materialization_status") != "source_ready_editor_materialization_pending":
        errors.append("materialization_status_mismatch")
    if first.get("outfit_id") != "MelusinaV2":
        errors.append("first_outfit_id_mismatch")
    if first.get("resonant_form_policy") != "decorative_only":
        errors.append("first_outfit_must_remain_decorative")
    reconciliation = manifest.get("draft_reconciliation")
    if not isinstance(reconciliation, dict):
        errors.append("draft_reconciliation_missing")
    else:
        rarity_policy = reconciliation.get("rarity_policy")
        if not isinstance(rarity_policy, dict) or (
            rarity_policy.get("status") != "owner_decision_required"
            or rarity_policy.get("import_action")
            != "reject_until_explicit_mapping"
        ):
            errors.append("rarity_policy_must_remain_owner_decision_and_fail_closed")
        if (
            reconciliation.get("content_pack_field") != "content_pack_id"
            or reconciliation.get("content_pack_policy")
            != "preserve_when_present_optional_until_collection_authority"
        ):
            errors.append("content_pack_policy_must_preserve_identity")
    expected_count = first.get("record_count")
    if expected_count != len(records):
        errors.append(f"first_outfit_record_count_{expected_count}_not_{len(records)}")
    if manifest.get("target_count") != len(records):
        errors.append(f"target_count_{manifest.get('target_count')}_not_{len(records)}")
    if manifest.get("battle_gate") is not False or first.get("battle_wardrobe_enabled") is not False:
        errors.append("battle_wardrobe_must_remain_disabled")
    ids = [
        row.get("cosmetic_id")
        for row in records
        if isinstance(row, dict) and isinstance(row.get("cosmetic_id"), str)
    ]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_cosmetic_id")
    default_slots = first.get("default_slots")
    record_slots = {
        row.get("slot")
        for row in records
        if isinstance(row, dict) and isinstance(row.get("slot"), str)
    }
    if (
        not isinstance(default_slots, list)
        or any(not isinstance(slot, str) for slot in default_slots)
        or len(default_slots) != len(set(default_slots))
    ):
        errors.append("default_slots_must_be_unique")
    elif not set(default_slots).issubset(record_slots):
        errors.append("default_slots_must_resolve_to_records")
    for row in records:
        if not isinstance(row, dict):
            errors.append("record_must_be_object")
            continue
        for key in ("cosmetic_id", "slot", "rarity", "mesh"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(f"record_{key}_required_{row.get('cosmetic_id')}")
        if "content_pack_id" in row and (
            not isinstance(row["content_pack_id"], str)
            or not row["content_pack_id"].strip()
        ):
            errors.append(
                f"record_content_pack_id_invalid_{row.get('cosmetic_id')}"
            )
        if row.get("rarity") != "Common":
            errors.append(f"record_{row.get('cosmetic_id')}_rarity_not_canonical")
        if not str(row.get("mesh", "")).startswith(
            "/Game/Melodia/Characters/Melusina/Outfits/V2/"
        ):
            errors.append(f"record_{row.get('cosmetic_id')}_mesh_root_mismatch")
        if row.get("resonant_form_id") is not None:
            errors.append(f"record_{row.get('cosmetic_id')}_must_be_decorative")
    return manifest, records, errors


def _enum_value(enum_type, name: str):
    """Resolve a reflected enum across Unreal Python's casing variants."""
    candidates = (
        name,
        name.upper(),
        name.replace("_", ""),
        name.replace("_", "").upper(),
    )
    for candidate in candidates:
        value = getattr(enum_type, candidate, None)
        if value is not None:
            return value
    raise RuntimeError(f"reflected enum {enum_type} has no value {name}")


def _package_path(value) -> str:
    if value is None:
        return ""
    getter = getattr(value, "get_path_name", None)
    text = getter() if callable(getter) else str(value)
    return str(text).split(".", 1)[0]


def _enum_name(value) -> str:
    text = str(value).split(".")[-1]
    return text.split(":", 1)[0].strip("<> ")


def _is_skeletal_mesh(value) -> bool:
    """Return True only for a reflected SkeletalMesh UObject."""
    if value is None:
        return False
    skeletal_mesh_type = getattr(unreal, "SkeletalMesh", None)
    if skeletal_mesh_type is not None:
        try:
            return isinstance(value, skeletal_mesh_type)
        except TypeError:
            pass
    get_class = getattr(value, "get_class", None)
    reflected_class = get_class() if callable(get_class) else None
    get_name = getattr(reflected_class, "get_name", None)
    return callable(get_name) and get_name() == "SkeletalMesh"


def resolve_meshes(expected: list[dict]) -> tuple[dict[str, object], dict]:
    """Resolve and type-check every source mesh without changing editor state."""
    resolved: dict[str, object] = {}
    missing: list[str] = []
    wrong_type: list[dict[str, str]] = []
    for source in expected:
        mesh_path = source["mesh"]
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if mesh is None:
            missing.append(mesh_path)
            continue
        if not _is_skeletal_mesh(mesh):
            get_class = getattr(mesh, "get_class", None)
            reflected_class = get_class() if callable(get_class) else None
            get_name = getattr(reflected_class, "get_name", None)
            actual_class = get_name() if callable(get_name) else type(mesh).__name__
            wrong_type.append({"path": mesh_path, "actual_class": str(actual_class)})
            continue
        resolved[mesh_path] = mesh
    return resolved, {
        "expected": [source["mesh"] for source in expected],
        "resolved": sorted(resolved),
        "missing": missing,
        "wrong_type": wrong_type,
        "type_correct": not missing and not wrong_type,
    }


def _record_identity(record) -> dict:
    identity = {
        "cosmetic_id": str(record.get_editor_property("cosmetic_id")),
        "slot": _enum_name(record.get_editor_property("slot")),
        "rarity": _enum_name(record.get_editor_property("rarity")),
        "mesh": _package_path(record.get_editor_property("mesh")),
    }
    try:
        identity["content_pack_id"] = str(
            record.get_editor_property("content_pack_id")
        )
    except Exception:
        # Older reflected builds have no metadata field; source records that
        # carry pack identity will fail the readback rather than being dropped.
        identity["content_pack_id"] = ""
    return identity


def catalog_diff(catalog, expected: list[dict]) -> list[str]:
    """Compare an existing catalog readback to the source contract."""
    try:
        actual = list(catalog.get_editor_property("cosmetics") or [])
    except Exception as exc:  # pragma: no cover - editor API
        return [f"catalog_records_read_failed_{exc}"]
    errors: list[str] = []
    if len(actual) != len(expected):
        errors.append(f"catalog_record_count_{len(actual)}_not_{len(expected)}")
    for index, source in enumerate(expected):
        if index >= len(actual):
            break
        got = _record_identity(actual[index])
        keys = ["cosmetic_id", "slot", "rarity", "mesh"]
        if "content_pack_id" in source:
            keys.append("content_pack_id")
        for key in keys:
            if got[key].casefold() != str(source[key]).casefold():
                errors.append(
                    f"record_{index}_{key}_{got[key]}_not_{source[key]}"
                )
    return errors


def build_records(expected: list[dict], resolved_meshes: dict[str, object] | None = None):
    if resolved_meshes is None:
        resolved_meshes, mesh_report = resolve_meshes(expected)
        if not mesh_report["type_correct"]:
            raise RuntimeError(f"mesh_preflight_failed_{mesh_report}")
    records = []
    enum_slots = unreal.MelodiaWardrobeSlot
    enum_rarity = unreal.MelodiaCosmeticRarity
    for source in expected:
        rec = unreal.MelodiaCosmeticRecord()
        rec.set_editor_property("cosmetic_id", unreal.Name(source["cosmetic_id"]))
        rec.set_editor_property("slot", _enum_value(enum_slots, source["slot"]))
        rec.set_editor_property("rarity", _enum_value(enum_rarity, source["rarity"]))
        if "content_pack_id" in source:
            rec.set_editor_property(
                "content_pack_id", unreal.Name(source["content_pack_id"])
            )
        # The reflected property is TSoftObjectPtr<USkeletalMesh>. In this UE
        # Python build, set_editor_property nativizes it from the loaded asset
        # object; passing SoftObjectPath raises "Cannot nativize ... as Mesh".
        rec.set_editor_property("mesh", resolved_meshes[source["mesh"]])
        # ResonantFormId is intentionally left NAME_None: this first outfit is
        # decorative and must not become a second capability authority.
        records.append(rec)
    return records


def main() -> int:
    if unreal is None:
        log("ABORT: must run inside the Unreal editor")
        return 2

    args = argv()
    verify_only = "--verify-only" in args or "--dry-run" in args
    replace_existing = "--replace-existing" in args
    manifest, expected, source_errors = load_source()
    catalog_path = (
        str(manifest.get("catalog_asset", DEFAULT_CATALOG_PATH))
        if manifest else DEFAULT_CATALOG_PATH
    )
    report: dict = {
        "asset": catalog_path,
        "source_manifest": str(SOURCE_MANIFEST),
        "verify_only": verify_only,
        "replace_existing": replace_existing,
        "pieces": expected,
        "materialization_status": "source_ready_editor_materialization_pending",
        "ok": False,
    }
    if source_errors:
        log(f"ABORT: source manifest is invalid: {source_errors}")
        report["errors"] = source_errors
        _write(report)
        return 1

    # Every mesh must exist and be a SkeletalMesh before the catalog claims it.
    # A record pointing at a missing or wrong-class asset is owned-but-
    # unpresentable, which is the exact class of silent failure the C++ gate
    # exists to prevent.
    resolved_meshes, mesh_preflight = resolve_meshes(expected)
    report["mesh_preflight"] = mesh_preflight
    if not mesh_preflight["type_correct"]:
        errors = [
            *[f"missing mesh: {mesh}" for mesh in mesh_preflight["missing"]],
            *[
                f"mesh is not SkeletalMesh: {item['path']} ({item['actual_class']})"
                for item in mesh_preflight["wrong_type"]
            ],
        ]
        log(f"ABORT: mesh type preflight failed: {errors}")
        report["errors"] = errors
        _write(report)
        return 1

    existing = unreal.EditorAssetLibrary.does_asset_exist(catalog_path)
    log(f"catalog {'exists' if existing else 'does not exist'}: {catalog_path}")
    report["catalog_exists_before"] = existing

    if verify_only:
        if existing:
            catalog = unreal.EditorAssetLibrary.load_asset(catalog_path)
            if not catalog:
                report["errors"] = ["catalog_load_failed"]
            else:
                errors = catalog_diff(catalog, expected)
                report["catalog_readback"] = {"ok": not errors, "errors": errors}
                report["ok"] = not errors
        else:
            report["catalog_readback"] = {
                "ok": False,
                "status": "not_materialized",
                "errors": [],
            }
            # Verify-only is an input preflight when the asset is absent. It is
            # deliberately not persistence proof.
            report["ok"] = True
        report["materialization_proof"] = "not_attempted"
        _write(report)
        return 0 if report["ok"] else 1

    try:
        # Construct all reflected records before creating a new DataAsset. This
        # prevents a failed property nativization from leaving an empty catalog.
        records = build_records(expected, resolved_meshes)
    except Exception as exc:  # pragma: no cover - editor API
        report["errors"] = [f"catalog_record_build_failed_{exc}"]
        _write(report)
        return 1

    if existing:
        catalog = unreal.EditorAssetLibrary.load_asset(catalog_path)
        if not catalog:
            report["errors"] = ["catalog_load_failed"]
            _write(report)
            return 1
        existing_errors = catalog_diff(catalog, expected)
        if existing_errors and not replace_existing:
            report["errors"] = [
                "existing_catalog_mismatch_requires_replace_existing",
                *existing_errors,
            ]
            _write(report)
            return 1
        if not existing_errors:
            report["action"] = "already_matches_source"
            report["catalog_readback"] = {"ok": True, "errors": []}
            report["ok"] = True
            _write(report)
            return 0
    else:
        package_path, asset_name = catalog_path.rsplit("/", 1)
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.MelodiaCosmeticCatalog)
        catalog = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name, package_path, unreal.MelodiaCosmeticCatalog, factory
        )
        if not catalog:
            report["errors"] = ["catalog_create_failed"]
            _write(report)
            return 1

    created_new = not existing
    try:
        catalog.set_editor_property("cosmetics", records)
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(
            catalog, only_if_is_dirty=False
        ))
    except Exception as exc:  # pragma: no cover - editor API
        report["errors"] = [f"catalog_write_failed_{exc}"]
        report["created_new_catalog"] = created_new
        if created_new:
            try:
                report["cleanup_deleted_new_catalog"] = bool(
                    unreal.EditorAssetLibrary.delete_asset(catalog_path)
                )
            except Exception as cleanup_exc:
                report["cleanup_deleted_new_catalog"] = False
                report["cleanup_error"] = str(cleanup_exc)
        _write(report)
        return 1
    if not saved:
        report["errors"] = ["catalog_save_failed"]
        _write(report)
        return 1

    # Read back rather than trusting the transport's saved response.
    reloaded = unreal.EditorAssetLibrary.load_asset(catalog_path)
    errors = catalog_diff(reloaded, expected) if reloaded else ["catalog_reload_failed"]
    report["catalog_readback"] = {"ok": not errors, "errors": errors}
    report["records_written"] = len(reloaded.get_editor_property("cosmetics")) if reloaded else 0
    report["materialization_proof"] = "editor_save_and_readback"
    report["ok"] = not errors
    report["created_new_catalog"] = created_new
    if errors and created_new:
        try:
            report["cleanup_deleted_new_catalog"] = bool(
                unreal.EditorAssetLibrary.delete_asset(catalog_path)
            )
        except Exception as cleanup_exc:
            report["cleanup_deleted_new_catalog"] = False
            report["cleanup_error"] = str(cleanup_exc)
    log(f"saved {catalog_path} with {report['records_written']}/{len(expected)} records")
    _write(report)
    return 0 if report["ok"] else 1


def _write(report: dict) -> None:
    try:
        with open(AUDIT, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        log(f"audit {AUDIT} ok={report.get('ok')}")
    except OSError as exc:
        log(f"WARN could not write audit: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
