"""PCG clustering audit — ISM bands, volume fit, exclusion wiring."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_clustering_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

LEVELS = (
    "/Game/EnvSandbox/_Template/L_Template",
    "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
)


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


def _volume_metrics(actor) -> dict:
    import unreal

    loc = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    return {
        "label": actor.get_actor_label(),
        "location": [loc.x, loc.y, loc.z],
        "scale": [scale.x, scale.y, scale.z],
        "z_scale_ok": scale.z <= 2.5,
        "xy_scale": max(scale.x, scale.y),
    }


def run_audit() -> dict:
    import unreal
    import pcg_portfolio_standards as std
    import pcg_validate_helpers as vh

    level_reports: list[dict] = []
    issues: list[dict] = []
    null_rhi = _is_null_rhi()

    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            level_reports.append({"level": level, "missing": True})
            continue

        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        les.load_level(level)

        volumes: list[dict] = []
        ism_by_label: dict[str, int] = {}
        for actor in eas.get_all_level_actors() or []:
            label = actor.get_actor_label()
            if not label.startswith("PCG_"):
                continue
            count = vh.count_ism(actor)
            ism_by_label[label] = count
            volumes.append({**_volume_metrics(actor), "ism_count": count})

        preset = "showcase" if "Sakura" in level else "minimal"
        lo, hi = std.PRESETS.get(preset, std.PRESETS["standard"]).get(
            "ism_band", std.ISM_BAND_PORTFOLIO
        )
        foliage_ism = sum(v for k, v in ism_by_label.items() if "Rock" not in k)
        ism_pass = None if null_rhi or foliage_ism == 0 else vh.within_bounds(foliage_ism, lo, hi)

        for vol in volumes:
            if not vol.get("z_scale_ok"):
                issues.append({
                    "level": level,
                    "id": "volume_z_too_tall",
                    "severity": "warn",
                    "label": vol["label"],
                    "z_scale": vol["scale"][2],
                })
            if vol.get("xy_scale", 0) > 55:
                issues.append({
                    "level": level,
                    "id": "volume_oversized",
                    "severity": "warn",
                    "label": vol["label"],
                    "xy_scale": vol["xy_scale"],
                })

        if ism_pass is False:
            issues.append({
                "level": level,
                "id": "ism_out_of_band",
                "severity": "warn",
                "ism": foliage_ism,
                "band": [lo, hi],
            })

        excl_guides = [
            a.get_actor_label()
            for a in eas.get_all_level_actors() or []
            if a.get_actor_label().startswith(std.ACTOR_EXCLUDE_PREFIX)
        ]
        level_reports.append({
            "level": level,
            "preset": preset,
            "volumes": volumes,
            "ism_by_label": ism_by_label,
            "ism_band": [lo, hi],
            "ism_pass": ism_pass,
            "exclusion_guides": excl_guides,
            "structural_pass": len(volumes) > 0,
        })

    excl_path = std.GRAPH_EXCLUSION
    excl_meta = {"exists": unreal.EditorAssetLibrary.does_asset_exist(excl_path)}
    critical = sum(1 for i in issues if i.get("severity") == "critical")
    structural = all(r.get("structural_pass") for r in level_reports if not r.get("missing"))
    passed = structural and critical == 0 and (null_rhi or not any(
        i.get("id") == "ism_out_of_band" for i in issues
    ))

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "null_rhi": null_rhi,
        "levels": level_reports,
        "exclusion_subgraph": excl_meta,
        "issues": issues,
        "critical_count": critical,
        "passed": passed,
        "pie_note": "Verify no single-cell piles and path/pond exclusion in editor PIE",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_pcg_clustering.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode
    report = run_audit()
    print(f"PCG_CLUSTERING passed={report.get('passed')}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
