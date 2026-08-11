"""Master PCG portfolio audit — plugins, inventory, levels, dead systems.

  python Content/Python/audit_pcg_portfolio.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_portfolio_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


import pcg_graph_builder as gb


def _is_null_rhi() -> bool:
    for arg in sys.argv:
        if "nullrhi" in arg.lower():
            return True
    try:
        import unreal

        rhi = str(unreal.SystemLibrary.get_console_variable_string("r.RHI.Name") or "").lower()
        return rhi == "null" or "null" in rhi
    except Exception:
        return False


def _scan_level_volumes(level_path: str) -> list[dict]:
    import unreal

    results: list[dict] = []
    level_asset = f"{level_path}.{level_path.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        return [{"level": level_path, "error": "level_missing"}]

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    try:
        les.load_level(level_path)
    except Exception as exc:
        return [{"level": level_path, "error": f"load_failed: {exc}"}]
    for actor in eas.get_all_level_actors() or []:
        comp = actor.get_component_by_class(unreal.PCGComponent) if hasattr(unreal, "PCGComponent") else None
        if not comp:
            continue
        graph_path = gb.graph_package_path(comp)
        activated = False
        for prop in ("b_is_active", "b_activated", "is_active", "activated"):
            try:
                activated = bool(comp.get_editor_property(prop))
                break
            except Exception:
                continue
        results.append({
            "level": level_path,
            "actor": actor.get_actor_label(),
            "graph": graph_path,
            "activated": activated,
            "ism_count": sum(
                c.get_instance_count()
                for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
            ) if hasattr(unreal, "InstancedStaticMeshComponent") else 0,
            "project_leak": graph_path and "/_PROJECT/" in graph_path,
            "missing_graph": graph_path is None,
        })
    return results


def _inventory_envsandbox() -> list[dict]:
    import unreal

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    items: list[dict] = []
    filt = unreal.ARFilter(package_paths=[std.PCG_ROOT], recursive_paths=True)
    for ad in ar.get_assets(filt) or []:
        path = str(ad.package_name)
        name = path.rsplit("/", 1)[-1]
        parent = path.rsplit("/", 1)[0]
        compliant = any(parent.startswith(d) for d in (
            std.DIR_UNIVERSAL, std.DIR_GREYBOX, std.DIR_COLLECTIONS,
            std.DIR_STYLES, std.DIR_DEPRECATED,
        ))
        if path == std.PCG_ROOT:
            compliant = True
        items.append({
            "path": path,
            "name": name,
            "folder_compliant": compliant or name == "PCG",
            "owner": std.PCG_PYTHON_OWNERS.get(path),
        })
    return sorted(items, key=lambda x: x["path"])


def _dead_systems(inventory: list[dict], volumes: list[dict]) -> list[dict]:
    import unreal

    issues: list[dict] = []
    known = {i["path"] for i in inventory}
    if unreal.EditorAssetLibrary.does_asset_exist(std.ORPHAN_MEADOW_SCATTER):
        if unreal.EditorAssetLibrary.does_asset_exist(std.DEPRECATED_MEADOW):
            issues.append({
                "id": "stale_orphan",
                "severity": "warn",
                "path": std.ORPHAN_MEADOW_SCATTER,
                "message": "Stale root-level redirect — delete duplicate at PCG root",
            })
        else:
            issues.append({
                "id": "orphan_graph",
                "severity": "warn",
                "path": std.ORPHAN_MEADOW_SCATTER,
                "message": "Root-level orphan — move to _Deprecated",
            })
    if unreal.EditorAssetLibrary.does_asset_exist(std.ORPHAN_SAKURA_GROVE):
        if unreal.EditorAssetLibrary.does_asset_exist(std.GRAPH_SAKURA_GROVE):
            issues.append({
                "id": "stale_orphan",
                "severity": "warn",
                "path": std.ORPHAN_SAKURA_GROVE,
                "message": "Stale root-level redirect — delete duplicate at PCG root",
            })
        else:
            issues.append({
                "id": "orphan_graph",
                "severity": "warn",
                "path": std.ORPHAN_SAKURA_GROVE,
                "message": "Root-level orphan — move to Styles/Sakura",
            })
    for vol in volumes:
        if vol.get("missing_graph"):
            issues.append({
                "id": "dangling_volume",
                "severity": "critical",
                "level": vol.get("level"),
                "actor": vol.get("actor"),
                "message": "PCGVolume has no graph assigned",
            })
        if vol.get("project_leak"):
            issues.append({
                "id": "project_leak",
                "severity": "critical",
                "level": vol.get("level"),
                "actor": vol.get("actor"),
                "graph": vol.get("graph"),
                "message": "EnvSandbox volume references _PROJECT graph",
            })
    return issues


def _audit_in_ue() -> dict:
    import unreal

    null_rhi = _is_null_rhi()
    plugin_health = []
    if not null_rhi:
        for name in ("PCG", "PCGExtendedToolkit", "PCGPythonInterop"):
            try:
                plugin_health.append({
                    "name": name,
                    "enabled": unreal.PluginBlueprintLibrary.is_plugin_enabled(name),
                })
            except Exception:
                plugin_health.append({"name": name, "enabled": None})
    else:
        plugin_health = [
            {"name": name, "enabled": None, "note": "skipped_null_rhi"}
            for name in ("PCG", "PCGExtendedToolkit", "PCGPythonInterop")
        ]

    inventory = _inventory_envsandbox()
    volumes: list[dict] = []
    if null_rhi:
        volumes.append({"note": "level_scan_skipped", "reason": "null_rhi"})
    else:
        for level in std.SHIPPING_LEVELS:
            volumes.extend(_scan_level_volumes(level))

    dead = _dead_systems(inventory, volumes)
    critical = sum(1 for d in dead if d.get("severity") == "critical")

    melodia_summary = {}
    melodia_path = PROJECT_ROOT / "Saved" / "Audit" / "melodia_pcg_reference.json"
    if melodia_path.exists():
        try:
            melodia_summary = json.loads(melodia_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "null_rhi": null_rhi,
        "plugin_health": plugin_health,
        "envsandbox_inventory": inventory,
        "inventory_count": len(inventory),
        "level_volumes": volumes,
        "dead_systems": dead,
        "critical_count": critical,
        "melodia_summary": {
            "graph_count": melodia_summary.get("graph_count"),
            "tier_counts": melodia_summary.get("tier_counts"),
        },
        "clean": critical == 0,
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"PCG_PORTFOLIO_AUDIT clean={report['clean']} critical={report['critical_count']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_pcg_portfolio.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
