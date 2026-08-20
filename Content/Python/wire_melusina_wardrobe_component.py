# -*- coding: utf-8 -*-
"""Verify or materialize the single Melusina V2 wardrobe component.

This is an editor-only, fail-closed bridge for
``BP_MelusinaJRPGCharacter``. It reads the same checked-in catalog manifest as
the catalog authoring script, adds at most one ``UMelodiaWardrobeComponent``,
and assigns only the four non-body V2 defaults. It never changes the pawn body
mesh, the legacy outfit component, battle wardrobe state, or any map.

The default mode is read-only verification. Pass ``-- --apply`` explicitly to
add/configure the component. Both modes compile/save only when applying and
perform a post-save readback; no transport response is treated as persistence
proof.

Run in the Unreal editor, one editor only:

    editor_query run_python: Content/Python/wire_melusina_wardrobe_component.py
    ... -- --verify-only
    ... -- --apply
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
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "melusina_wardrobe_component.json"
PAWN_PATH = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
WARDROBE_CLASS_PATH = "/Script/MelodiaWardrobe.MelodiaWardrobeComponent"
LEGACY_CLASS_MARKER = "MelodiaOutfitComponent"


def log(message: str) -> None:
    line = f"[wardrobe-pawn] {message}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load_source() -> tuple[dict | None, list[str]]:
    try:
        manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"source_manifest_unreadable_{exc}"]
    if not isinstance(manifest, dict):
        return None, ["source_manifest_must_be_object"]
    first = manifest.get("first_outfit")
    if not isinstance(first, dict):
        return manifest, ["first_outfit_missing"]
    if manifest.get("battle_gate") is not False:
        return manifest, ["battle_gate_must_be_false"]
    if first.get("battle_wardrobe_enabled") is not False:
        return manifest, ["first_outfit_battle_wardrobe_must_be_false"]
    records = first.get("records")
    defaults = first.get("default_slots")
    if not isinstance(records, list) or not isinstance(defaults, list):
        return manifest, ["first_outfit_records_or_defaults_missing"]
    by_slot = {row.get("slot"): row for row in records if isinstance(row, dict)}
    errors = []
    for slot in defaults:
        row = by_slot.get(slot)
        if not row:
            errors.append(f"default_slot_missing_from_catalog_{slot}")
        elif not row.get("mesh"):
            errors.append(f"default_slot_mesh_missing_{slot}")
    first["default_records"] = [by_slot[slot] for slot in defaults if slot in by_slot]
    return manifest, errors


def reflected_class():
    if unreal is None:
        return None
    value = getattr(unreal, "MelodiaWardrobeComponent", None)
    if value:
        return value
    return unreal.load_class(None, WARDROBE_CLASS_PATH)


def reflected_enum_value(name: str):
    enum_type = getattr(unreal, "MelodiaWardrobeSlot", None)
    if enum_type is None:
        raise RuntimeError("MelodiaWardrobeSlot is not reflected; closed-editor build is required")
    for candidate in (name, name.upper(), name.replace("_", ""), name.replace("_", "").upper()):
        value = getattr(enum_type, candidate, None)
        if value is not None:
            return value
    raise RuntimeError(f"MelodiaWardrobeSlot has no reflected value {name}")


def path_name(value) -> str:
    if value is None:
        return ""
    getter = getattr(value, "get_path_name", None)
    text = getter() if callable(getter) else str(value)
    return str(text).split(".", 1)[0]


def object_for_handle(library, handle):
    try:
        return library.get_object(library.get_data(handle))
    except Exception:
        return None


def gathered_objects(bp) -> list:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp) or [])
    return [object_for_handle(library, handle) for handle in handles]


def component_rows(bp, wardrobe_class) -> tuple[list, list]:
    objects = [obj for obj in gathered_objects(bp) if obj is not None]
    wardrobes = []
    legacy = []
    for obj in objects:
        class_name = str(obj.get_class().get_name())
        if wardrobe_class and isinstance(obj, wardrobe_class):
            wardrobes.append(obj)
        elif class_name == "MelodiaWardrobeComponent":
            wardrobes.append(obj)
        if LEGACY_CLASS_MARKER in class_name:
            legacy.append(obj)
    return wardrobes, legacy


def add_component(bp, wardrobe_class):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp) or [])
    if not handles:
        raise RuntimeError("pawn Blueprint has no root subobject")
    params = unreal.AddNewSubobjectParams(
        parent_handle=handles[0],
        new_class=wardrobe_class,
        blueprint_context=bp,
    )
    new_handle, failure = subsystem.add_new_subobject(params)
    if not failure.is_empty():
        raise RuntimeError(f"could not add wardrobe component: {failure}")
    subsystem.rename_subobject(new_handle, unreal.Text("Wardrobe"))
    component = object_for_handle(library, new_handle)
    if component is None:
        raise RuntimeError("wardrobe component was added but could not be read back")
    return component


def expected_defaults(manifest: dict) -> dict:
    return {
        str(row["slot"]): str(row["mesh"])
        for row in manifest["first_outfit"]["default_records"]
    }


def set_defaults(component, manifest: dict) -> None:
    defaults = expected_defaults(manifest)
    values = {
        reflected_enum_value(slot): unreal.load_asset(mesh_path)
        for slot, mesh_path in defaults.items()
    }
    missing = [slot for slot, mesh in values.items() if mesh is None]
    if missing:
        raise RuntimeError(f"default mesh load failed for reflected slots: {missing}")
    component.set_editor_property("default_garment_meshes", values)
    component.set_editor_property("b_enable_battle_wardrobe", False)


def property_value(component, name: str, default=None):
    try:
        return component.get_editor_property(name)
    except Exception:
        return default


def readback_defaults(component) -> dict:
    stored = property_value(component, "default_garment_meshes", {}) or {}
    result = {}
    try:
        entries = stored.items()
    except AttributeError:
        entries = []
    for slot, mesh in entries:
        slot_name = str(slot).split(".")[-1]
        result[slot_name] = path_name(mesh)
    return result


def verify_readback(bp, wardrobe_class, manifest: dict) -> dict:
    wardrobes, legacy = component_rows(bp, wardrobe_class)
    row = {
        "component_count": len(wardrobes),
        "legacy_component_count": len(legacy),
        "components": [str(obj.get_name()) for obj in wardrobes],
        "legacy_components": [str(obj.get_name()) for obj in legacy],
        "default_garment_meshes": {},
        "battle_wardrobe_enabled": None,
        "errors": [],
    }
    if len(wardrobes) != 1:
        row["errors"].append(f"wardrobe_component_count_{len(wardrobes)}_not_1")
        return row
    component = wardrobes[0]
    row["default_garment_meshes"] = readback_defaults(component)
    row["battle_wardrobe_enabled"] = bool(
        property_value(component, "b_enable_battle_wardrobe", True)
    )
    if row["battle_wardrobe_enabled"]:
        row["errors"].append("battle_wardrobe_enabled")
    if row["legacy_component_count"]:
        row["errors"].append("legacy_outfit_component_present")
    expected = {
        slot.upper(): mesh for slot, mesh in expected_defaults(manifest).items()
    }
    actual = {
        str(slot).split(".")[-1].upper(): mesh
        for slot, mesh in row["default_garment_meshes"].items()
    }
    for slot, mesh in expected.items():
        if actual.get(slot, "").casefold() != mesh.casefold():
            row["errors"].append(
                f"default_{slot}_{actual.get(slot, '')}_not_{mesh}"
            )
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        row["errors"].append(f"unexpected_default_slots_{unexpected}")
    row["ok"] = not row["errors"]
    return row


def write_report(report: dict) -> None:
    try:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        log(f"WARN could not write audit: {exc}")


def main() -> int:
    if unreal is None:
        log("ABORT: must run inside the Unreal editor")
        return 2
    apply = "--apply" in args()
    manifest, source_errors = load_source()
    report = {
        "pawn": PAWN_PATH,
        "source_manifest": str(SOURCE_MANIFEST),
        "mode": "apply" if apply else "verify-only",
        "editor_only": True,
        "ok": False,
    }
    if source_errors or manifest is None:
        report["errors"] = source_errors or ["source_manifest_missing"]
        write_report(report)
        return 1
    bp = unreal.EditorAssetLibrary.load_asset(PAWN_PATH)
    if not bp:
        report["errors"] = [f"pawn_load_failed_{PAWN_PATH}"]
        write_report(report)
        return 1
    wardrobe_class = reflected_class()
    if not wardrobe_class:
        report["errors"] = ["wardrobe_component_class_unavailable"]
        write_report(report)
        return 1

    wardrobes, legacy = component_rows(bp, wardrobe_class)
    report["preflight"] = {
        "wardrobe_component_count": len(wardrobes),
        "legacy_component_count": len(legacy),
        "mesh_paths": expected_defaults(manifest),
    }
    if len(wardrobes) > 1:
        report["errors"] = ["multiple_wardrobe_components_refuse_mutation"]
        write_report(report)
        return 1
    if legacy:
        # Do not silently remove the quarantined authority. An owner/editor pass
        # must decide what the existing component is doing before cleanup.
        report["errors"] = ["legacy_outfit_component_present_refuse_mutation"]
        write_report(report)
        return 1

    if not apply:
        report["readback"] = verify_readback(bp, wardrobe_class, manifest)
        report["ok"] = report["readback"]["ok"]
        write_report(report)
        return 0 if report["ok"] else 1

    try:
        component = wardrobes[0] if wardrobes else add_component(bp, wardrobe_class)
        set_defaults(component, manifest)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
            raise RuntimeError(f"pawn save returned false: {PAWN_PATH}")
    except Exception as exc:  # pragma: no cover - editor API
        report["errors"] = [f"apply_failed_{exc}"]
        write_report(report)
        return 1

    # The save response is not proof. Reload the package and inspect the CDO/SCS
    # state that the next process will actually consume.
    reloaded = unreal.EditorAssetLibrary.load_asset(PAWN_PATH)
    report["readback"] = (
        verify_readback(reloaded, wardrobe_class, manifest)
        if reloaded else {"ok": False, "errors": ["pawn_reload_failed"]}
    )
    report["materialization_proof"] = "editor_compile_save_and_readback"
    report["ok"] = report["readback"]["ok"]
    write_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
