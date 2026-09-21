"""VRM -> NPC intake: registry-driven import, spec refresh, scaffold hand-off.

One entry point for staging a VRM character as a Melodia NPC:

    registry (Content/Python/gmm/npc/vrm_registry.json)
      -> resolve the staged .vrm file on disk
      -> VRM4U import into /Game/NPCs/Imported/{archetype}/{source_id}
      -> find the SkeletalMesh VRM4U produced
      -> write/refresh specs/npcs/<npc_id>.v1.json   (schema melodia.npc_scaffold.v1)
      -> invoke Content/Python/scaffold_npc.py -> scaffold_npc(spec)  (BP + definition asset)
      -> merge the run into Saved/Audit/npc_vrm_intake.json

Dry run (no editor, never imports `unreal` — safe from plain python anywhere):

    python Content/Python/npc_vrm_intake.py --source-id SD_02_PetalPriestess --dry-run

Live run (one editor open; Monolith :9316 or the editor console):

    import sys; sys.path.insert(0, r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python")
    import npc_vrm_intake
    npc_vrm_intake.run(source_id="SD_02_PetalPriestess")

UNVERIFIED PATH (2026-09-20): the VRM4U import call itself. This lane had no
editor access, so `_discover_vrm4u_adapter()` discovers the VRM4U Python surface
at runtime instead of hardcoding it, every run records `"adapter_verified": false`,
and the audit lists the candidates that were tried with their exact exceptions.
`gmm/npc/vrm4u_import.py` is a reference, not truth: its `unreal.VRM4UFactoryNew()`
call and its "the .vrm lives in the Content Browser" assumption are both unconfirmed.
The parallel editor lane must report which candidate works; then the constant
`ADAPTER_VERIFIED_UTC` below gets a date and the probe list can be narrowed.

Editor-only assumptions are isolated in functions marked `[UE]`; everything else
(registry, file resolution, spec construction, audit, scaffolder namespace check)
runs with plain python.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import types
from pathlib import Path

TOOL = "npc_vrm_intake.py"
TOOL_VERSION = "1.0.0"
AUDIT_SCHEMA = "melodia.npc_intake.v1"
SPEC_SCHEMA = "melodia.npc_scaffold.v1"

#: Date the VRM4U import path was last exercised end-to-end by an editor lane.
#: Empty string == never verified. While empty, every run says so out loud.
ADAPTER_VERIFIED_UTC = ""

REGISTRY_REL = Path("Content/Python/gmm/npc/vrm_registry.json")
VRM_ROOT_REL = Path("Content/NPCs/VRM_Sources")
SPEC_DIR_REL = Path("specs/npcs")
SCAFFOLDER_REL = Path("Content/Python/scaffold_npc.py")
AUDIT_REL = Path("Saved/Audit/npc_vrm_intake.json")

#: Destination convention (see Docs/Handoffs/VRM4U_NPC_PLACEHOLDERS_2026-08-14.md).
DEST_TEMPLATE = "/Game/NPCs/Imported/{archetype}/{source_id}"

ROLES = ("Ambient", "Merchant", "Quest", "Companion")

#: Attribute names probed on any `unreal` symbol whose name contains "vrm".
#: Probed, never required: an absent name is simply not a candidate.
VRM_IMPORT_ATTR_HINTS = ("import_vrm", "import_vrm_file", "importvrm", "import_from_file")

#: Set MELODIA_VRM_INTAKE_STATIC_PROBE=0 to keep the live import from calling
#: discovered static import functions (only the factory/AssetTools path is tried).
STATIC_PROBE_ENV = "MELODIA_VRM_INTAKE_STATIC_PROBE"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _project_root() -> Path:
    """Project root from __file__; env override for exec'd callers without __file__."""
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        env = os.environ.get("MELODIA_PROJECT_ROOT")
        return Path(env) if env else Path(r"C:/EnvironmentPortfolio/BS_GodFile")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload) -> None:
    """Write JSON via a sibling temp file so a crash never leaves a half file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _configure_stdout() -> None:
    """Creator names in the registry are non-ASCII; legacy Windows consoles choke."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _get_unreal():
    """Lazy `unreal` lookup. Returns None outside the editor — never raises."""
    try:
        import unreal  # type: ignore
        return unreal
    except Exception:
        return None


# ---------------------------------------------------------------------------
# registry + source resolution (plain python)
# ---------------------------------------------------------------------------

def load_registry(project_root: Path = None) -> dict:
    root = Path(project_root) if project_root else _project_root()
    path = root / REGISTRY_REL
    data = _read_json(path)
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("%s has no 'sources' list" % path)
    seen = set()
    for entry in sources:
        source_id = str(entry.get("source_id") or "").strip()
        if not source_id:
            raise ValueError("%s: a source entry has no source_id" % path)
        if source_id in seen:
            raise ValueError("%s: duplicate source_id %s" % (path, source_id))
        seen.add(source_id)
        if not entry.get("archetype"):
            raise ValueError("%s: %s has no archetype" % (path, source_id))
    data["_path"] = str(path)
    return data


def resolve_source(entry: dict, project_root: Path = None) -> dict:
    """Find the staged .vrm for a registry entry. Filesystem wins over registry claims."""
    root = Path(project_root) if project_root else _project_root()
    vrm_root = root / VRM_ROOT_REL
    source_id = str(entry["source_id"])
    filename = str(entry.get("filename") or "%s.vrm" % source_id)

    candidates = []
    local_path = entry.get("local_path")
    if local_path:
        candidates.append(vrm_root / str(local_path))
    candidates.append(vrm_root / filename)
    for sub in ("VRoidHub", "VRoidStudio", "CustomBlender"):
        candidates.append(vrm_root / sub / filename)

    # de-dupe, keep order
    seen, ordered = set(), []
    for cand in candidates:
        key = str(cand)
        if key not in seen:
            seen.add(key)
            ordered.append(cand)

    found = next((cand for cand in ordered if cand.is_file()), None)
    report = {
        "source_id": source_id,
        "filename": filename,
        "searched": [str(cand) for cand in ordered],
        "disk_path": str(found) if found else "",
        "relative_path": str(found.relative_to(vrm_root)).replace("\\", "/") if found else "",
        "exists": bool(found),
        "size_bytes": found.stat().st_size if found else 0,
        "sha256": _sha256_file(found) if found else "",
    }
    if not found:
        report["error"] = "no .vrm found on disk for %s (looked in %s)" % (source_id, VRM_ROOT_REL)
    elif entry.get("on_disk") is False:
        report["registry_conflict"] = (
            "registry marks %s as missing, but a file exists at %s" % (source_id, report["relative_path"])
        )
    return report


# ---------------------------------------------------------------------------
# spec construction (plain python)
# ---------------------------------------------------------------------------

def derive_npc_id(source_id: str) -> str:
    """Snake_case FName-safe id: 'SD_02_PetalPriestess' -> 'sd_02_petal_priestess'."""
    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", str(source_id)).strip("_").lower()
    return re.sub(r"_{2,}", "_", cleaned)


def validate_npc_id(npc_id: str) -> str:
    if not npc_id or " " in npc_id:
        raise ValueError("npc_id must be non-empty and contain no spaces: %r" % npc_id)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]*", npc_id):
        raise ValueError("npc_id must be snake_case (a-z, 0-9, _): %r" % npc_id)
    return npc_id


def derive_asset_name(source_id: str) -> str:
    """'SD_02_PetalPriestess' -> 'Sd02PetalPriestess'.

    Like scaffold_npc's rule, but a part that is already CamelCase keeps its
    case ('PetalPriestess' stays readable instead of collapsing to
    'Petalpriestess').
    """
    parts = [part for part in re.split(r"[^0-9A-Za-z]+", str(source_id)) if part]
    return "".join(part if re.search(r"[A-Z]", part[1:]) else part.capitalize() for part in parts)


def derive_display_name(source_id: str) -> str:
    """'SD_02_PetalPriestess' -> 'Petal Priestess' (drop the SD_02_ style prefix)."""
    stripped = re.sub(r"^[A-Za-z]{1,4}_\d{1,3}_", "", str(source_id))
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", stripped or str(source_id))
    return re.sub(r"[_]+", " ", words).strip() or str(source_id)


def spec_path_for(npc_id: str, project_root: Path = None) -> Path:
    root = Path(project_root) if project_root else _project_root()
    return root / SPEC_DIR_REL / ("%s.v1.json" % npc_id)


def _attribution_line(entry: dict) -> str:
    author = str(entry.get("author") or "unrecorded")
    license_name = str(entry.get("license") or "unrecorded")
    page = str(entry.get("hub_url") or entry.get("license_url") or "")
    line = "author: %s | license: %s" % (author, license_name)
    if entry.get("attribution"):
        line += " | credit: %s" % entry["attribution"]
    if entry.get("attribution_status") and not entry.get("attribution"):
        line += " | attribution: %s" % entry["attribution_status"]
    if page:
        line += " | page: %s" % page
    return line


def build_spec(entry: dict, resolution: dict, skeletal_mesh: str = None,
               project_root: Path = None, now_utc: str = None) -> dict:
    """Build the melodia.npc_scaffold.v1 spec this source should scaffold from."""
    source_id = str(entry["source_id"])
    npc_id = validate_npc_id(str(entry.get("npc_id") or derive_npc_id(source_id)))
    role = str(entry.get("role") or "Ambient")
    if role not in ROLES:
        role = "Ambient"

    mesh = skeletal_mesh
    if not mesh:
        existing = spec_path_for(npc_id, project_root)
        if existing.is_file():
            try:
                mesh = _read_json(existing).get("skeletal_mesh") or None
            except Exception:
                mesh = None

    notes = "VRM intake %s: source %s (%s%s) | %s | generated by %s" % (
        now_utc or _utc_now(),
        source_id,
        resolution.get("relative_path") or "path unresolved",
        (", sha256 %s" % resolution["sha256"][:16]) if resolution.get("sha256") else "",
        _attribution_line(entry),
        TOOL,
    )

    spec = {
        "schema": SPEC_SCHEMA,
        "npc_id": npc_id,
        "asset_name": str(entry.get("asset_name") or derive_asset_name(source_id)),
        "display_name": str(entry.get("display_name") or derive_display_name(source_id)),
        "role": role,
        "skeletal_mesh": mesh,
        "static_mesh": None,
        "dialogue_keys": [],
        "behavior_tag": None,
        "notes": notes,
    }
    return spec


def destination_for(entry: dict) -> str:
    return DEST_TEMPLATE.format(archetype=str(entry.get("archetype")), source_id=str(entry["source_id"]))


# ---------------------------------------------------------------------------
# scaffolder hand-off (plain python check; live call needs the editor)
# ---------------------------------------------------------------------------

def _exec_scaffolder_namespace(project_root: Path, unreal_module) -> tuple:
    """exec scaffold_npc.py into a fresh namespace WITHOUT running its main().

    Required contract (specs/npcs/README.md):
      * MELODIA_NPC_SCAFFOLD_AUTORUN=0 first — scaffold_npc.py's last line runs
        main() unless that env var is "0";
      * the namespace globals carry __file__ = the real path, because
        scaffold_npc._project_root() resolves parents[2] off it.
    """
    path = (Path(project_root) if project_root else _project_root()) / SCAFFOLDER_REL
    info = {"path": str(path), "exists": path.is_file(), "namespace_extraction": "not_attempted",
            "scaffold_callable": False, "error": ""}
    if not info["exists"]:
        info["error"] = "scaffolder not found at %s" % path
        return None, info

    source = path.read_text(encoding="utf-8")
    info["autorun_guard"] = "MELODIA_NPC_SCAFFOLD_AUTORUN" in source

    previous_env = os.environ.get("MELODIA_NPC_SCAFFOLD_AUTORUN")
    os.environ["MELODIA_NPC_SCAFFOLD_AUTORUN"] = "0"
    stub = None
    if unreal_module is None:
        # Dry-run only: satisfy the module-level `import unreal` so the namespace
        # contract can be proven with plain python. Nothing is called on the stub.
        stub = types.ModuleType("unreal")
        sys.modules["unreal"] = stub
    try:
        namespace = {"__file__": str(path), "__name__": "melodia_scaffold_npc_probe"}
        exec(compile(source, str(path), "exec"), namespace)
        info["scaffold_callable"] = callable(namespace.get("scaffold_npc"))
        info["namespace_extraction"] = "ok" if info["scaffold_callable"] else "symbol_missing"
        return namespace.get("scaffold_npc"), info
    except Exception as exc:
        info["namespace_extraction"] = "failed"
        info["error"] = "%s: %s" % (type(exc).__name__, exc)
        return None, info
    finally:
        if stub is not None and sys.modules.get("unreal") is stub:
            del sys.modules["unreal"]
        if previous_env is None:
            os.environ.pop("MELODIA_NPC_SCAFFOLD_AUTORUN", None)
        else:
            os.environ["MELODIA_NPC_SCAFFOLD_AUTORUN"] = previous_env


def check_scaffolder(project_root: Path = None) -> dict:
    """Dry-run check: does the scaffolder source yield a callable without running main()?"""
    _, info = _exec_scaffolder_namespace(project_root, None)
    return info


# ---------------------------------------------------------------------------
# [UE] VRM4U import — discovered at runtime, never hardcoded
# ---------------------------------------------------------------------------

def _discover_vrm4u_adapter(unreal_module) -> dict:
    """[UE] Find a VRM4U import entry point by scanning the live `unreal` module.

    This is the ONE place that guesses at VRM4U's Python surface. It returns
    candidates with their evidence and never raises; the caller decides what to
    try. Nothing here is verified — see the module docstring.
    """
    report = {
        "adapter_verified": bool(ADAPTER_VERIFIED_UTC),
        "verified_utc": ADAPTER_VERIFIED_UTC,
        "plugin_enabled": None,
        "vrm_symbols": [],
        "candidates": [],
        "notes": [],
    }
    try:
        report["vrm_symbols"] = sorted(name for name in dir(unreal_module) if "vrm" in name.lower())
    except Exception as exc:
        report["notes"].append("dir(unreal) failed: %s" % exc)
        return report
    if not report["vrm_symbols"]:
        report["notes"].append("no symbol in dir(unreal) contains 'vrm' — VRM4U is probably not loaded "
                               "(plugin not enabled, or the editor has not restarted since enabling it)")
        return report

    try:  # plugin state is a nice-to-have, never a hard gate
        manager = getattr(unreal_module, "PluginManager", None)
        finder = getattr(manager, "find_plugin", None)
        plugin = finder("VRM4U") if callable(finder) else None
        report["plugin_enabled"] = bool(plugin.is_enabled()) if plugin is not None else None
    except Exception as exc:
        report["notes"].append("plugin probe failed: %s" % exc)

    for name in report["vrm_symbols"]:
        try:
            symbol = getattr(unreal_module, name)
        except Exception:
            continue
        lowered = name.lower()
        if callable(symbol) and "factory" in lowered:
            report["candidates"].append({
                "kind": "factory",
                "symbol": name,
                "how": "AssetTools.import_asset(asset_name, package_path, factory, filename=<abs .vrm path>)",
            })
        for attr in VRM_IMPORT_ATTR_HINTS:
            try:
                fn = getattr(symbol, attr, None)
            except Exception:
                continue
            if callable(fn):
                report["candidates"].append({
                    "kind": "static_callable",
                    "symbol": "%s.%s" % (name, attr),
                    "how": "call(vrm_path, dest_package) then call(vrm_path)",
                })
    if not report["candidates"]:
        report["notes"].append("'vrm' symbols exist but none looked like a factory or an import callable: %s"
                               % ", ".join(report["vrm_symbols"]))
    report["notes"].append("UNVERIFIED: this lane had no editor access; candidates are name-scan guesses")
    return report


def _save_asset_tree(unreal_module, package_path: str) -> dict:
    """[UE] Save every asset under package_path.

    Verified live 2026-09-20: after a 71-asset VRM import, `task.save=True` had
    persisted exactly ONE package. Anything not saved explicitly dies with the
    editor, so the intake always saves its own destination tree.
    """
    out = {"requested": 0, "saved": 0, "failed": []}
    try:
        paths = unreal_module.EditorAssetLibrary.list_assets(package_path, recursive=True,
                                                             include_folder=False)
    except Exception as exc:
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
        return out
    out["requested"] = len(paths)
    for path in paths:
        try:
            if unreal_module.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False):
                out["saved"] += 1
            else:
                out["failed"].append(path)
        except Exception as exc:
            out["failed"].append("%s (%s)" % (path, exc))
    return out


def _try_vrm4u_import(unreal_module, adapter: dict, vrm_path: str, dest_package: str,
                      asset_name: str, probe_static: bool = True) -> dict:
    """[UE] Attempt the discovered candidates, most-likely first, recording everything."""
    result = {"state": "no_candidate", "via": "", "attempts": [], "error": ""}

    # First-choice path, VERIFIED LIVE 2026-09-20 (SD_02_PetalPriestess -> 71 assets):
    # AssetImportTask + AssetTools.import_asset_tasks with the factory built through
    # unreal.new_object (calling the factory class directly does not work).
    # `automated` MUST be False: with True, Slate cancels VRM4U's options window
    # ("modal window tried to take control while running in unattended script mode")
    # and the import aborts with zero assets. With False the modal is real and the
    # caller blocks until somebody clicks Import — an unattended run hangs here.
    task_cls = getattr(unreal_module, "AssetImportTask", None)
    factory_cls = getattr(unreal_module, "VRM4UImporterFactory", None)
    if task_cls is not None and factory_cls is not None:
        attempt = {"kind": "asset_task", "symbol": "AssetImportTask+VRM4UImporterFactory",
                   "args": [asset_name, dest_package, vrm_path],
                   "note": "modal 'VRM Import Options' blocks the call until Import is clicked"}
        try:
            try:
                factory = unreal_module.new_object(factory_cls)
            except Exception:
                factory = factory_cls()
            task = task_cls()
            task.set_editor_property("filename", vrm_path)
            task.set_editor_property("destination_path", dest_package)
            task.set_editor_property("destination_name", asset_name)
            task.set_editor_property("automated", False)
            task.set_editor_property("save", True)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("factory", factory)
            tools = unreal_module.AssetToolsHelpers.get_asset_tools()
            tools.import_asset_tasks([task])
            imported = [str(p) for p in (task.get_editor_property("imported_object_paths") or [])]
            attempt["returned"] = "imported_object_paths=%d" % len(imported)
            result["attempts"].append(attempt)
            if imported:
                result.update(state="imported", via="asset_task")
                result["imported_object_paths"] = imported
                return result
        except Exception as exc:
            attempt["exception"] = "%s: %s" % (type(exc).__name__, exc)
            result["attempts"].append(attempt)

    # Then the discovered candidates: factories first (the documented VRM4U path is
    # factory + AssetTools.import_asset), then any static import callables.
    candidates = sorted(adapter.get("candidates", []), key=lambda item: 0 if item["kind"] == "factory" else 1)
    for candidate in candidates:
        kind, symbol = candidate["kind"], candidate["symbol"]
        if kind == "factory":
            attempt = {"kind": kind, "symbol": symbol, "args": [asset_name, dest_package, vrm_path]}
            try:
                factory = getattr(unreal_module, symbol)()
                tools = unreal_module.AssetToolsHelpers.get_asset_tools()
                imported = tools.import_asset(asset_name=asset_name, package_path=dest_package,
                                              factory=factory, filename=vrm_path)
                attempt["returned"] = str(imported)
                result["attempts"].append(attempt)
                if imported:
                    result.update(state="imported", via=symbol)
                    return result
            except Exception as exc:
                attempt["exception"] = "%s: %s" % (type(exc).__name__, exc)
                result["attempts"].append(attempt)
        elif kind == "static_callable" and probe_static:
            target = unreal_module
            for part in symbol.split("."):
                target = getattr(target, part, None)
                if target is None:
                    break
            if not callable(target):
                continue
            for args in ((vrm_path, dest_package), (vrm_path,)):
                attempt = {"kind": kind, "symbol": symbol, "args": list(args)}
                try:
                    returned = target(*args)
                    attempt["returned"] = str(returned)
                    result["attempts"].append(attempt)
                    if returned:
                        result.update(state="imported", via="%s(%d args)" % (symbol, len(args)))
                        return result
                except Exception as exc:
                    attempt["exception"] = "%s: %s" % (type(exc).__name__, exc)
                    result["attempts"].append(attempt)
    if not result["attempts"]:
        result["error"] = "no usable candidate (see adapter report)"
    else:
        result["error"] = "every candidate failed; see attempts"
    return result


def _find_skeletal_meshes(unreal_module, package_path: str) -> dict:
    """[UE] Assets under package_path whose class is SkeletalMesh (VRM4U names them)."""
    report = {"state": "not_run", "candidates": [], "error": ""}
    try:
        paths = unreal_module.EditorAssetLibrary.list_assets(package_path, recursive=True, include_folder=False)
    except Exception as exc:
        report.update(state="failed", error="list_assets(%s): %s" % (package_path, exc))
        return report
    for asset_path in paths:
        try:
            asset = unreal_module.EditorAssetLibrary.load_asset(asset_path)
            class_name = asset.get_class().get_name() if asset else ""
        except Exception:
            continue
        if class_name == "SkeletalMesh":
            report["candidates"].append({"object_path": asset_path, "package": asset_path.split(".")[0]})
    report["state"] = "found" if report["candidates"] else "empty"
    return report


def _probe_vrm_meta_object(unreal_module, package_path: str) -> dict:
    """[UE] Secondary path: a VRM4U meta object that may reference the mesh.

    vrm4u_import.py assumes a class named `VrmMetaObject` with a `skeletal_mesh`
    property; both names are unverified, so they are probed, never required.
    """
    report = {"state": "not_run", "candidates": [], "notes": []}
    try:
        paths = unreal_module.EditorAssetLibrary.list_assets(package_path, recursive=True, include_folder=False)
    except Exception as exc:
        report.update(state="failed", notes=["list_assets failed: %s" % exc])
        return report
    for asset_path in paths:
        try:
            asset = unreal_module.EditorAssetLibrary.load_asset(asset_path)
            class_name = asset.get_class().get_name() if asset else ""
        except Exception:
            continue
        if "vrm" not in class_name.lower():
            continue
        entry = {"object_path": asset_path, "class": class_name}
        try:
            mesh = asset.get_editor_property("skeletal_mesh")
            entry["skeletal_mesh"] = str(mesh) if mesh else ""
        except Exception as exc:
            entry["skeletal_mesh_probe"] = "unavailable: %s" % exc
        report["candidates"].append(entry)
    report["state"] = "found" if report["candidates"] else "empty"
    return report


# ---------------------------------------------------------------------------
# per-source orchestration
# ---------------------------------------------------------------------------

def _editor_only_gaps() -> list:
    return [
        "VRM4U adapter: which discovered candidate (factory vs static callable) and which argument "
        "shape actually imports a .vrm — candidates are name-scan guesses, none executed by this lane",
        "the SkeletalMesh VRM4U actually produces (object path, skeleton, bone count, materials) — "
        "discovered only inside the editor",
        "whether the imported skeleton exceeds the 60-bone LOD0 budget and needs VRM4U bone reduction",
        "scaffold_npc: BP_<Name>_NPC + DA_<Name> creation, interaction-component defaults, compile, "
        "CDO npc_definition write and asset save — all editor-only",
        "whether VRM4U is enabled in BS_GodFile.uproject at all (owner-owned file; this tool only reports)",
    ]


def process_source(entry: dict, project_root: Path, dry_run: bool, force_import: bool,
                   unreal_module, scaffolder_callable, scaffolder_info: dict) -> dict:
    source_id = str(entry["source_id"])
    now = _utc_now()
    report = {
        "ran_utc": now,
        "mode": "dry_run" if dry_run else "live",
        "source_id": source_id,
        "archetype": str(entry.get("archetype") or ""),
        "destination": destination_for(entry),
        "warnings": [],
        "vrm": {},
        "spec": {},
        "import": {"state": "not_attempted", "via": "", "error": "", "adapter": {}, "attempts": []},
        "skeletal_mesh": {"state": "not_run", "candidates": [], "chosen": ""},
        "scaffold": {"state": "not_attempted", "report_path": ""},
    }

    resolution = resolve_source(entry, project_root)
    report["vrm"] = resolution
    if not resolution["exists"]:
        report["warnings"].append(resolution.get("error", "source file missing"))
        report["npc_id"] = str(entry.get("npc_id") or derive_npc_id(source_id))
        report["state"] = "failed"
        return report
    if resolution.get("registry_conflict"):
        report["warnings"].append(resolution["registry_conflict"])

    spec = build_spec(entry, resolution, project_root=project_root, now_utc=now)
    report["npc_id"] = spec["npc_id"]
    spec_path = spec_path_for(spec["npc_id"], project_root)
    previous_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""
    previous_sha = _sha256_text(previous_text) if previous_text else ""
    previous_mesh = ""
    if previous_text:
        try:
            previous_mesh = _read_json(spec_path).get("skeletal_mesh") or ""
        except Exception as exc:
            report["warnings"].append("existing spec unreadable (%s); it will be refreshed" % exc)

    existing_meshes = {"state": "not_run", "candidates": []}
    if dry_run:
        report["import"]["state"] = "skipped_dry_run"
        report["skeletal_mesh"]["state"] = "deferred_to_editor"
        if previous_mesh:
            report["skeletal_mesh"]["chosen"] = previous_mesh
            report["skeletal_mesh"]["source"] = "existing spec"
    else:
        existing_meshes = _find_skeletal_meshes(unreal_module, report["destination"])
        report["existing_destination_assets"] = existing_meshes
        if existing_meshes["candidates"] and not force_import:
            report["import"]["state"] = "skipped_existing_mesh"
        else:
            adapter = _discover_vrm4u_adapter(unreal_module)
            report["import"]["adapter"] = adapter
            probe_static = os.environ.get(STATIC_PROBE_ENV, "1") != "0"
            try:
                unreal_module.EditorAssetLibrary.make_directory(report["destination"])
            except Exception as exc:
                report["warnings"].append("make_directory failed: %s" % exc)
            outcome = _try_vrm4u_import(unreal_module, adapter, resolution["disk_path"],
                                        report["destination"], spec["asset_name"], probe_static)
            report["import"].update(outcome)
            if outcome["state"] != "imported":
                report["warnings"].append("VRM4U import did not report success: %s" % outcome["error"])
            else:
                report["import"]["saved"] = _save_asset_tree(unreal_module, report["destination"])
        meshes = _find_skeletal_meshes(unreal_module, report["destination"])
        report["skeletal_mesh"] = meshes
        if meshes["candidates"]:
            # Prefer the shallowest package (VRM4U puts the main mesh in the destination
            # folder itself; sub-parts sit deeper), then alphabetical for determinism.
            chosen = sorted(meshes["candidates"],
                            key=lambda item: (item["package"].count("/"), item["package"]))[0]
            report["skeletal_mesh"]["chosen"] = chosen["object_path"]
            report["skeletal_mesh"]["source"] = "destination scan"
            if len(meshes["candidates"]) > 1:
                report["warnings"].append("multiple SkeletalMeshes under %s; chose %s"
                                          % (report["destination"], chosen["object_path"]))
        else:
            report["skeletal_mesh"]["meta_object_probe"] = _probe_vrm_meta_object(unreal_module,
                                                                                  report["destination"])
            if previous_mesh:
                report["skeletal_mesh"]["chosen"] = previous_mesh
                report["skeletal_mesh"]["source"] = "existing spec (no mesh discovered this run)"
                report["warnings"].append("no SkeletalMesh found after import; kept the mesh from the existing spec")

    chosen_mesh = report["skeletal_mesh"].get("chosen") or ""
    spec["skeletal_mesh"] = chosen_mesh or None
    if not spec["skeletal_mesh"]:
        if dry_run:
            report["warnings"].append("skeletal_mesh not resolved yet (import is the editor's step) — dry-run writes "
                                      "nothing; a live run resolves the mesh before writing the spec")
        else:
            report["warnings"].append("no skeletal_mesh resolved — the definition asset will be invalid "
                                      "(FMelodiaNPCDef needs at least one mesh)")
    spec_text = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    spec_sha = _sha256_text(spec_text)
    report["spec"] = {
        "path": str(spec_path),
        "schema": spec["schema"],
        "written": False,
        "changed": spec_sha != previous_sha,
        "previous_sha256": previous_sha,
        "sha256": spec_sha,
        "content": spec,
    }

    if dry_run:
        report["scaffold"] = {
            "state": "deferred_to_editor",
            "scaffolder": scaffolder_info,
            "would_invoke": "scaffold_npc(spec)",
        }
    else:
        if scaffolder_callable is None:
            report["scaffold"] = {"state": "unavailable", "scaffolder": scaffolder_info,
                                  "error": scaffolder_info.get("error", "")}
            report["warnings"].append("scaffolder namespace load failed; BP/DA not touched")
        elif not spec["skeletal_mesh"]:
            report["scaffold"] = {"state": "skipped", "scaffolder": scaffolder_info,
                                  "reason": "no skeletal mesh resolved"}
        else:
            try:
                scaffold_report = scaffolder_callable(spec)
                report["scaffold"] = {
                    "state": "invoked",
                    "scaffolder": scaffolder_info,
                    "report_path": str(scaffold_report.get("report_path", "")),
                    "blueprint": scaffold_report.get("blueprint", {}),
                    "definition": scaffold_report.get("definition", {}),
                    "warnings": scaffold_report.get("warnings", []),
                }
                report["warnings"].extend("scaffold: %s" % item for item in scaffold_report.get("warnings", []))
            except Exception as exc:
                report["scaffold"] = {"state": "failed", "scaffolder": scaffolder_info,
                                      "error": "%s: %s" % (type(exc).__name__, exc)}
                report["warnings"].append("scaffold_npc raised: %s" % exc)

    if not dry_run:
        _write_spec(spec_path, spec_text, report)

    if dry_run:
        # Everything that can be checked without the editor passed; the import,
        # mesh discovery and scaffold are the editor lane's to prove.
        report["state"] = "deferred"
    elif report["skeletal_mesh"].get("chosen") and report["scaffold"].get("state") == "invoked" \
            and not report["scaffold"].get("warnings"):
        report["state"] = "ok"
    else:
        report["state"] = "attention"

    report["editor_only_gaps"] = _editor_only_gaps()
    return report


def _write_spec(spec_path: Path, spec_text: str, report: dict) -> None:
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = spec_path.with_suffix(spec_path.suffix + ".tmp")
    tmp.write_text(spec_text, encoding="utf-8")
    os.replace(tmp, spec_path)
    report["spec"]["written"] = True


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------

def list_sources(project_root: Path = None) -> list:
    root = Path(project_root) if project_root else _project_root()
    registry = load_registry(root)
    rows = []
    for entry in registry["sources"]:
        resolution = resolve_source(entry, root)
        rows.append({
            "source_id": entry["source_id"],
            "archetype": entry.get("archetype"),
            "npc_id": str(entry.get("npc_id") or derive_npc_id(entry["source_id"])),
            "on_disk": resolution["exists"],
            "relative_path": resolution.get("relative_path", ""),
            "size_bytes": resolution.get("size_bytes", 0),
            "author": entry.get("author", ""),
            "license": entry.get("license", ""),
        })
    return rows


def run(source_id: str = None, all_sources: bool = False, dry_run: bool = None,
        force_import: bool = False, project_root: Path = None, write_audit: bool = True,
        echo: bool = True) -> dict:
    """Process one source (or every source with a staged .vrm) end to end."""
    _configure_stdout()
    root = Path(project_root) if project_root else _project_root()
    unreal_module = None if dry_run else _get_unreal()
    if dry_run is None:
        dry_run = unreal_module is None
    if dry_run:
        unreal_module = None

    registry = load_registry(root)
    entries = registry["sources"]
    if source_id:
        entries = [entry for entry in entries if str(entry["source_id"]) == str(source_id)]
        if not entries:
            raise ValueError("source_id %r is not in %s" % (source_id, registry["_path"]))
    elif all_sources:
        entries = [entry for entry in entries if resolve_source(entry, root)["exists"]]
    else:
        raise ValueError("pass source_id=..., all_sources=True, or use the CLI (--list / --source-id / --all)")

    scaffolder_callable, scaffolder_info = (None, {"state": "not_attempted"})
    if not dry_run:
        scaffolder_callable, scaffolder_info = _exec_scaffolder_namespace(root, unreal_module)
    else:
        scaffolder_info = check_scaffolder(root)

    document = {
        "tool": TOOL,
        "tool_version": TOOL_VERSION,
        "schema": AUDIT_SCHEMA,
        "last_run_utc": _utc_now(),
        "last_mode": "dry_run" if dry_run else "live",
        "registry": {"path": registry["_path"], "sources_total": len(registry["sources"])},
        "adapter_verified_utc": ADAPTER_VERIFIED_UTC,
        "sources": {},
    }
    audit_path = root / AUDIT_REL
    if audit_path.is_file():
        try:
            previous = _read_json(audit_path)
            if isinstance(previous.get("sources"), dict):
                document["sources"] = previous["sources"]
        except Exception as exc:
            document["audit_merge_note"] = "previous audit unreadable (%s); starting fresh" % exc

    for entry in entries:
        try:
            report = process_source(entry, root, dry_run, force_import, unreal_module,
                                    scaffolder_callable, scaffolder_info)
        except Exception as exc:
            report = {"ran_utc": _utc_now(), "mode": "dry_run" if dry_run else "live",
                      "source_id": str(entry.get("source_id")), "state": "failed",
                      "error": "%s: %s" % (type(exc).__name__, exc),
                      "editor_only_gaps": _editor_only_gaps()}
        document["sources"][str(entry["source_id"])] = report
        if echo:
            _echo_source(report)

    document["summary"] = {
        "processed": len(entries),
        "mode": document["last_mode"],
        "warnings": sum(len(item.get("warnings", [])) for item in document["sources"].values()),
        "needs_attention": sorted(sid for sid, item in document["sources"].items()
                                  if item.get("state") in ("failed", "attention")),
    }
    if write_audit:
        _write_json_atomic(audit_path, document)
        if echo:
            print("AUDIT %s (%d source entries)" % (audit_path, len(document["sources"])))
    return document


def _echo_source(report: dict) -> None:
    """Human-readable one-block summary; the audit JSON is the machine record."""
    print("=" * 72)
    print("source_id   : %s  [%s, state=%s]" % (report.get("source_id"), report.get("mode"),
                                                report.get("state", "?")))
    if report.get("state") == "failed":
        print("FAILED      : %s" % report.get("error"))
        for warning in report.get("warnings", []):
            print("WARN        : %s" % warning)
        return
    vrm = report.get("vrm", {})
    print("vrm         : %s%s" % (vrm.get("relative_path") or "(not found)",
                                 "  %d bytes" % vrm["size_bytes"] if vrm.get("size_bytes") else ""))
    if vrm.get("sha256"):
        print("sha256      : %s" % vrm["sha256"])
    print("npc_id      : %s" % report.get("npc_id"))
    print("destination : %s" % report.get("destination"))
    print("import      : %s" % report.get("import", {}).get("state"))
    for attempt in report.get("import", {}).get("attempts", []):
        print("  attempt   : %s(%s) -> %s" % (attempt.get("symbol"), ", ".join(attempt.get("args", [])),
                                              attempt.get("returned") or attempt.get("exception")))
    mesh = report.get("skeletal_mesh", {})
    print("mesh        : %s%s" % (mesh.get("chosen") or "(unresolved)",
                                  "  [%s]" % mesh.get("source") if mesh.get("source") else ""))
    spec = report.get("spec", {})
    if spec:
        print("spec        : %s  written=%s changed=%s" % (spec.get("path"), spec.get("written"),
                                                           spec.get("changed")))
        print("  spec json : %s" % json.dumps(spec.get("content"), ensure_ascii=False))
    scaffold = report.get("scaffold", {})
    if scaffold:
        print("scaffold    : %s%s" % (scaffold.get("state"),
                                      "  report=%s" % scaffold["report_path"] if scaffold.get("report_path") else ""))
        if scaffold.get("scaffolder"):
            print("  namespace : %s (callable=%s)" % (scaffold["scaffolder"].get("namespace_extraction"),
                                                      scaffold["scaffolder"].get("scaffold_callable")))
    for warning in report.get("warnings", []):
        print("WARN        : %s" % warning)


def main(argv=None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="VRM -> Melodia NPC intake (registry-driven).")
    parser.add_argument("--source-id", help="registry source_id, e.g. SD_02_PetalPriestess")
    parser.add_argument("--all", action="store_true", help="every source with a staged .vrm")
    parser.add_argument("--list", action="store_true", help="list registry sources and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate registry + files + spec construction; never imports unreal")
    parser.add_argument("--live", action="store_true", help="require the editor (fails without unreal)")
    parser.add_argument("--force-import", action="store_true",
                        help="re-import even when the destination already holds a SkeletalMesh")
    parser.add_argument("--no-audit", action="store_true", help="do not write Saved/Audit/npc_vrm_intake.json")
    parser.add_argument("--registry", help="override the registry path (default Content/Python/gmm/npc/vrm_registry.json)")
    args = parser.parse_args(argv)

    root = _project_root()
    if args.registry:
        global REGISTRY_REL
        REGISTRY_REL = Path(args.registry)

    if args.list:
        rows = list_sources(root)
        print("%-26s %-14s %-26s %-6s %s" % ("source_id", "archetype", "npc_id", "disk", "path"))
        for row in rows:
            print("%-26s %-14s %-26s %-6s %s" % (row["source_id"], row["archetype"], row["npc_id"],
                                                 "yes" if row["on_disk"] else "MISSING", row["relative_path"]))
        on_disk = sum(1 for row in rows if row["on_disk"])
        print("\n%d sources, %d staged on disk, %d missing" % (len(rows), on_disk, len(rows) - on_disk))
        return 0

    if not args.source_id and not args.all:
        parser.error("pass --source-id <id>, --all, or --list")

    dry_run = None
    if args.dry_run and args.live:
        parser.error("--dry-run and --live are mutually exclusive")
    if args.dry_run:
        dry_run = True
    if args.live:
        if _get_unreal() is None:
            print("ERROR: --live needs the editor's python (no `unreal` module in this interpreter)")
            return 2
        dry_run = False

    document = run(source_id=args.source_id, all_sources=args.all, dry_run=dry_run,
                   force_import=args.force_import, project_root=root, write_audit=not args.no_audit)
    # Exit code gates on real trouble, not on the dry-run's expected "mesh is
    # deferred to the editor" note: 0 = ok/deferred, 1 = failed or attention.
    return 0 if not document["summary"].get("needs_attention") else 1


if __name__ == "__main__":
    raise SystemExit(main())
