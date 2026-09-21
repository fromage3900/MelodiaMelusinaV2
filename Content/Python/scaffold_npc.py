"""Scaffold a reusable Melodia NPC pair — Blueprint + definition asset — from a spec.

Contract (do not invent a second authority):
  * Actor base:      AMelodiaNPCBase              (/Script/MelodiaCore.MelodiaNPCBase)
  * Definition:      UMelodiaNPCDefinitionAsset   (FMelodiaNPCDef payload)
  * Interaction:     UMelodiaNPCInteractionComponent (talk prompt / Quill bridge)
  * Spawn path:      UMelodiaNPCSpawnLibrary::SpawnNPCBatch (PrimaryAssetType "MelodiaNPC")

What this creates, idempotently (existing assets are updated in place, never
duplicated):
  /Game/Melodia/Gameplay/NPC/Blueprints/BP_<AssetName>_NPC   (child of AMelodiaNPCBase,
                                                              with the interaction component)
  /Game/Melodia/Gameplay/NPC/Definitions/DA_<AssetName>      (definition asset)

Spec schema (one JSON per NPC; see specs/npcs/*.json):
  {
    "schema": "melodia.npc_scaffold.v1",
    "npc_id": "ellettra_vell",              # required, stable FName, no spaces
    "asset_name": "EllettraVell",           # optional; derived from npc_id when absent
    "display_name": "Ellettra Vell",
    "role": "Ambient|Merchant|Quest|Companion",
    "skeletal_mesh": "/Game/.../SK_X.SK_X", # at least one mesh is required for a
    "static_mesh": "/Game/.../SM_X.SM_X",   # valid FMelodiaNPCDef
    "dialogue_keys": ["..."],               # Quill-side keys, optional
    "behavior_tag": "..."                   # optional
  }

Run inside the live editor (Monolith run_python), or via the editor console:
  __file__ = r"<project>/Content/Python/scaffold_npc.py"
  exec(open(__file__, encoding="utf-8").read())

Reports land in Saved/Audit/npc_scaffold/<npc_id>.json.

Known boundaries (verified 2026-09-20, UE 5.8):
  * The minimal FMelodiaNPCDef has no AnimBlueprint field by design; a scaffolded
    skeletal NPC wears its rest pose until a shipping consumer justifies the field.
  * Packaged spawn via SpawnNPCBatch needs PrimaryAssetType "MelodiaNPC" in
    DefaultGame.ini -> [/Script/Engine.AssetManagerSettings] PrimaryAssetTypesToScan.
    This tool reports that gap; it does not edit Config/.
"""
from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

import unreal

BP_FOLDER = "/Game/Melodia/Gameplay/NPC/Blueprints"
DA_FOLDER = "/Game/Melodia/Gameplay/NPC/Definitions"

NPC_BASE_CLASS_PATH = "/Script/MelodiaCore.MelodiaNPCBase"
NPC_DA_CLASS_PATH = "/Script/MelodiaCore.MelodiaNPCDefinitionAsset"
NPC_INTERACTION_CLASS_PATH = "/Script/MelodiaCore.MelodiaNPCInteractionComponent"

ROLE_NAMES = ("Ambient", "Merchant", "Quest", "Companion")


def _project_root() -> Path:
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        env = os.environ.get("MELODIA_PROJECT_ROOT")
        return Path(env) if env else Path(r"C:/EnvironmentPortfolio/BS_GodFile")


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _text(value) -> "unreal.Text":
    return unreal.Text(str(value))


def _name(value) -> "unreal.Name":
    return unreal.Name(str(value))


def _role_value(role_name: str):
    """EMelodiaNPCRole from Python: the E-prefix is stripped (unreal.MelodiaNPCRole)."""
    enum = getattr(unreal, "MelodiaNPCRole", None)
    if enum is None:
        return None
    for candidate in (role_name.upper(), role_name):
        value = getattr(enum, candidate, None)
        if value is not None:
            return value
    return None


def _derive_asset_name(npc_id: str) -> str:
    return "".join(part.capitalize() for part in npc_id.split("_") if part)


def _load_classes() -> dict:
    classes = {
        "base": unreal.load_class(None, NPC_BASE_CLASS_PATH),
        "da": unreal.load_class(None, NPC_DA_CLASS_PATH),
        "interaction": unreal.load_class(None, NPC_INTERACTION_CLASS_PATH),
    }
    missing = [key for key, value in classes.items() if value is None]
    if missing:
        raise RuntimeError(
            "MelodiaCore NPC classes unavailable (%s); rebuild the plugin first." % ", ".join(missing)
        )
    return classes


def _load_soft_object(path: str):
    """TSoftObjectPtr setters want the loaded object (a SoftObjectPath does not nativize)."""
    if not path:
        return None
    try:
        return unreal.EditorAssetLibrary.load_asset(str(path).split(".")[0])
    except Exception:
        return None


def _scs_component_handles(sds, bp, class_token: str):
    """Handles whose SCS export text names the given class.

    SubobjectData hides its fields from Python (to_dict() is empty), but
    export_text() carries the template's object path — that is the reliable
    identity check, verified live 2026-09-20.
    """
    matches = []
    try:
        handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    except Exception:
        return matches
    for handle in handles:
        try:
            text = sds.k2_find_subobject_data_from_handle(handle).export_text()
        except Exception:
            continue
        if class_token in text:
            matches.append(handle)
    return matches


def _component_template_from_handle(sds, handle):
    """Resolve the SCS template object (a CDO subobject) from a handle."""
    try:
        text = sds.k2_find_subobject_data_from_handle(handle).export_text()
    except Exception:
        return None
    match = re.search(r"WeakObjectPtr=\"[^']*'([^']+)'\"", text)
    if not match:
        return None
    path = match.group(1)
    for resolver in (unreal.load_object, unreal.find_object):
        try:
            obj = resolver(None, path)
            if obj:
                return obj
        except Exception:
            continue
    return None


def _ensure_interaction_component(bp, interaction_cls, npc_id: str, display_name: str, report: dict):
    """Add the talk component to the BP's construction script once, then set defaults."""
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    class_token = "/Script/MelodiaCore.MelodiaNPCInteractionComponent"

    handles = _scs_component_handles(sds, bp, class_token)
    status = "present"
    if not handles:
        try:
            root_handles = sds.k2_gather_subobject_data_for_blueprint(bp)
            params = unreal.AddNewSubobjectParams()
            params.set_editor_property("parent_handle", root_handles[0])
            params.set_editor_property("new_class", interaction_cls)
            params.set_editor_property("blueprint_context", bp)
            new_handle, fail_reason = sds.add_new_subobject(params)
            if fail_reason and str(fail_reason):
                report["warnings"].append("component_add_refused: %s" % fail_reason)
                return "failed", None
            handles = [new_handle]
            status = "added"
        except Exception as exc:
            report["warnings"].append("component_add_exception: %s" % exc)
            return "failed", None

    # A crashed earlier run can leave duplicates; keep the first, delete the rest.
    if len(handles) > 1:
        try:
            context_candidates = list(sds.k2_gather_subobject_data_for_blueprint(bp))
        except Exception:
            context_candidates = []
        for extra in handles[1:]:
            deleted = False
            for context in context_candidates:
                try:
                    if sds.delete_subobject(context, extra, bp):
                        deleted = True
                        break
                except Exception:
                    continue
            if deleted:
                status += "+deduped"
            else:
                report["warnings"].append(
                    "component_dedupe_failed: no context handle accepted the delete"
                )

    handle = handles[0]
    try:
        sds.rename_subobject(handle, "Interaction")
    except Exception as exc:
        report["warnings"].append("component_rename_failed: %s" % exc)

    template = _component_template_from_handle(sds, handle)
    if template is not None:
        try:
            template.set_editor_property("npc_id", _name(npc_id))
            template.set_editor_property("speaker_name", _text(display_name))
            template.set_editor_property("interaction_prompt", _text("Press E to talk"))
        except Exception as exc:
            report["warnings"].append("component_defaults_failed: %s" % exc)
    else:
        report["warnings"].append("component_template_unresolved: defaults not set")
    return status, template


def _ensure_definition_asset(classes, spec: dict, report: dict):
    asset_name = report["asset_name"]
    da_path = "%s/DA_%s" % (DA_FOLDER, asset_name)
    editor = unreal.EditorAssetLibrary

    if editor.does_asset_exist(da_path):
        da = editor.load_asset(da_path)
        created = False
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("supported_class", classes["da"])
        da = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_%s" % asset_name, DA_FOLDER, classes["da"], factory
        )
        created = True
    if not da:
        raise RuntimeError("Could not create/load definition asset at %s" % da_path)

    definition = unreal.MelodiaNPCDef()
    definition.set_editor_property("npc_id", _name(spec["npc_id"]))
    definition.set_editor_property("display_name", _text(spec.get("display_name") or spec["npc_id"]))

    role_name = str(spec.get("role") or "Ambient")
    role_value = _role_value(role_name)
    if role_value is not None:
        definition.set_editor_property("role", role_value)
    else:
        report["warnings"].append(
            "role_not_set (%s); unreal.MelodiaNPCRole unavailable — left at asset default" % role_name
        )

    skeletal = spec.get("skeletal_mesh")
    static = spec.get("static_mesh")
    if skeletal:
        mesh = _load_soft_object(skeletal)
        if mesh is not None:
            definition.set_editor_property("skeletal_mesh", mesh)
        else:
            report["warnings"].append("skeletal_mesh_missing: %s" % skeletal)
    if static:
        mesh = _load_soft_object(static)
        if mesh is not None:
            definition.set_editor_property("static_mesh", mesh)
        else:
            report["warnings"].append("static_mesh_missing: %s" % static)
    if not skeletal and not static:
        report["warnings"].append("no_mesh_reference: FMelodiaNPCDef::IsValid will refuse this asset")

    dialogue_keys = spec.get("dialogue_keys") or []
    if dialogue_keys:
        definition.set_editor_property("dialogue_keys", [_name(key) for key in dialogue_keys])
    behavior_tag = spec.get("behavior_tag")
    if behavior_tag:
        definition.set_editor_property("behavior_tag", _name(behavior_tag))

    da.set_editor_property("definition", definition)
    saved = editor.save_loaded_asset(da)
    report["definition"].update({
        "path": da_path,
        "created": created,
        "saved": bool(saved),
        "role": role_name,
        "skeletal_mesh": skeletal,
        "static_mesh": static,
    })
    return da


def _ensure_blueprint(classes, spec: dict, da, report: dict):
    asset_name = report["asset_name"]
    bp_path = "%s/BP_%s_NPC" % (BP_FOLDER, asset_name)
    editor = unreal.EditorAssetLibrary

    created = False
    if editor.does_asset_exist(bp_path):
        bp = editor.load_asset(bp_path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", classes["base"])
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "BP_%s_NPC" % asset_name, BP_FOLDER, unreal.Blueprint, factory
        )
        created = True
    if not bp:
        raise RuntimeError("Could not create/load Blueprint at %s" % bp_path)

    component_status, _ = _ensure_interaction_component(
        bp, classes["interaction"], spec["npc_id"],
        spec.get("display_name") or spec["npc_id"], report,
    )

    # Compile BEFORE any CDO write: compile wipes CDO overrides (melodia-p0-loop).
    if created or component_status != "present":
        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        except Exception as exc:
            report["warnings"].append("compile_failed: %s" % exc)

    cdo = unreal.get_default_object(bp.generated_class())
    try:
        cdo.set_editor_property("npc_definition", da)
    except Exception as exc:
        report["warnings"].append("cdo_definition_ref_failed: %s" % exc)

    saved = editor.save_loaded_asset(bp)
    report["blueprint"].update({
        "path": bp_path,
        "created": created,
        "saved": bool(saved),
        "interaction_component": component_status,
    })
    return bp


def scaffold_npc(spec: dict) -> dict:
    npc_id = str(spec.get("npc_id") or "").strip()
    if not npc_id or " " in npc_id:
        raise ValueError("spec.npc_id is required and must not contain spaces")

    report = {
        "tool": "scaffold_npc.py",
        "schema": "melodia.npc_scaffold.v1",
        "ran_utc": _utc_now(),
        "npc_id": npc_id,
        "asset_name": spec.get("asset_name") or _derive_asset_name(npc_id),
        "blueprint": {},
        "definition": {},
        "warnings": [],
    }

    classes = _load_classes()
    da = _ensure_definition_asset(classes, spec, report)
    _ensure_blueprint(classes, spec, da, report)

    report_dir = _project_root() / "Saved" / "Audit" / "npc_scaffold"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / ("%s.json" % npc_id)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    print("MELODIA_NPC_SCAFFOLD_OK npc_id=%s bp=%s da=%s warnings=%d"
          % (npc_id, report["blueprint"].get("path"), report["definition"].get("path"), len(report["warnings"])))
    for warning in report["warnings"]:
        print("MELODIA_NPC_SCAFFOLD_WARN %s" % warning)
    return report


def _spec_paths() -> list[Path]:
    env_path = os.environ.get("MELODIA_NPC_SPEC")
    if env_path:
        return [Path(env_path)]
    spec_dir = _project_root() / "specs" / "npcs"
    return sorted(spec_dir.glob("*.json"))


def main() -> None:
    paths = _spec_paths()
    if not paths:
        print("MELODIA_NPC_SCAFFOLD_NO_SPECS (looked in specs/npcs; set MELODIA_NPC_SPEC for a single file)")
        return
    for path in paths:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
        try:
            scaffold_npc(spec)
        except Exception as exc:
            print("MELODIA_NPC_SCAFFOLD_FAIL %s: %s" % (path, exc))


if os.environ.get("MELODIA_NPC_SCAFFOLD_AUTORUN", "1") == "1":
    main()
