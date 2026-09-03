"""Sakura petal Niagara audit — spawn alignment, MPC exposure, hand-tune gates.

  py Content/Python/audit_sakura_petal_niagara.py

Headless (asset + spawn checks only; particle bands require editor PIE):
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_sakura_petal_niagara.py"
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sakura_petal_niagara.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

SYSTEMS_SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"

PARTICLE_BANDS = {
    "NS_SakuraPetals_v2": (400, 1200),
    "NS_SakuraGroundPetals": (30, 80),
    "NS_SakuraPetalGust": (40, 80),
}


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


def _audit_system(spec_name: str, setup_mod) -> dict:
    import unreal

    path = f"{SYSTEMS_SAKURA}/{spec_name}.{spec_name}"
    entry: dict = {"name": spec_name, "path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return entry

    entry["exists"] = True
    system = unreal.load_asset(path)
    if not system:
        entry["error"] = "load_failed"
        return entry

    spec = next((s for s in setup_mod.SAKURA_SYSTEMS if s.name == spec_name), None)
    if spec:
        mat_path = f"/Game/EnvSandbox/VFX/Materials/{spec.sprite_material}.{spec.sprite_material}"
        entry["sprite_material"] = spec.sprite_material
        entry["material_assigned"] = setup_mod._assign_sprite_material(system, mat_path)
        entry["user_params"] = [p[0] for p in spec.user_params]
        entry["hand_tune"] = setup_mod.SAKURA_TUNING_NOTES.get(spec_name, [])
        entry["mpc_exposure"] = setup_mod._probe_system_mpc_exposure(system, spec)

    for prop in ("fixed_bounds", "b_fixed_bounds"):
        try:
            entry["fixed_bounds"] = bool(system.get_editor_property(prop))
            break
        except Exception:
            continue

    return entry


def _audit_level_spawns(setup_mod) -> dict:
    import unreal

    level_asset = f"{LEVEL}.L_SakuraPath"
    result: dict = {"level": LEVEL, "spawns": [], "anchors": {}}
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        result["error"] = "level_missing"
        return result

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(LEVEL)
    anchors = setup_mod._spawn_anchors_from_scene(eas)
    result["anchors"] = {
        k: {
            "location": v.get("location"),
            "scale": v.get("scale"),
            "source": v.get("source"),
        }
        for k, v in anchors.items()
    }

    trunk_bounds = anchors.get("canopy", {}).get("trunks") or []
    for spawn in setup_mod._resolve_level_spawns(eas):
        actor_info: dict = {
            "label": spawn["label"],
            "system": spawn["system"],
            "expected_location": list(spawn["location"]),
            "expected_scale": list(spawn["scale"]),
            "anchor_source": spawn.get("anchor_source"),
            "auto_activate": spawn.get("auto_activate", True),
        }
        actor = None
        for a in eas.get_all_level_actors() or []:
            if a.get_actor_label() == spawn["label"]:
                actor = a
                break
        if actor:
            loc = actor.get_actor_location()
            actor_info["actual_location"] = [loc.x, loc.y, loc.z]
            comp = actor.get_component_by_class(unreal.NiagaraComponent)
            if comp:
                actor_info["auto_activate_actual"] = bool(comp.get_auto_activate())
                actor_info["is_active"] = bool(comp.is_active())
        if spawn["label"] == "VFX_SakuraGround" and trunk_bounds:
            falloff_hits = []
            sx, sy, sz = spawn["location"]
            for tx, ty, tz in trunk_bounds:
                dist = ((sx - tx) ** 2 + (sy - ty) ** 2) ** 0.5
                if dist < setup_mod.TRUNK_FALLOFF_RADIUS_UU:
                    falloff_hits.append({"trunk": [tx, ty, tz], "distance_uu": round(dist, 1)})
            actor_info["trunk_falloff_overlap"] = falloff_hits
        result["spawns"].append(actor_info)
    return result


def _hand_tune_flags(setup_mod, systems: list[dict]) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for name in setup_mod.PETAL_SYSTEMS:
        sys_entry = next((s for s in systems if s["name"] == name), None)
        flags[f"{name}_asset"] = bool(sys_entry and sys_entry.get("exists"))
        flags[f"{name}_material"] = bool(sys_entry and sys_entry.get("material_assigned"))
        flags[f"{name}_emitter_authored"] = False  # editor-only; set true after PIE review
    flags["gust_inactive_default"] = False
    return flags


def run_audit() -> dict:
    import unreal

    import setup_sakura_niagara as setup

    setup_mod = setup
    petal_names = list(setup_mod.PETAL_SYSTEMS) + [setup_mod.CANOPY_SYSTEM_LEGACY]
    systems = [_audit_system(name, setup_mod) for name in petal_names]
    mpc_material = setup_mod._probe_mpc_material_bindings()
    spawns = _audit_level_spawns(setup_mod)
    hand_tune = _hand_tune_flags(setup_mod, systems)

    for spawn in spawns.get("spawns", []):
        if spawn.get("label") == "VFX_PetalGust":
            hand_tune["gust_inactive_default"] = spawn.get("auto_activate_actual") is False

    issues: list[dict] = []
    canopy = setup_mod.canonical_canopy_system()
    if canopy != setup_mod.CANOPY_SYSTEM_V2:
        issues.append({
            "id": "canopy_not_v2",
            "severity": "warn",
            "message": f"Canonical canopy is {canopy} — v2 asset missing on disk",
        })
    for sys in systems:
        if sys["name"] not in setup_mod.PETAL_SYSTEMS:
            continue
        if not sys.get("exists"):
            issues.append({"id": "missing_petal_system", "severity": "critical", "system": sys["name"]})
        elif not sys.get("material_assigned"):
            issues.append({
                "id": "material_unassigned",
                "severity": "warn",
                "system": sys["name"],
                "message": "Sprite material not bound via Python — assign in Niagara Editor",
            })
    if not hand_tune.get("gust_inactive_default"):
        issues.append({
            "id": "gust_auto_active",
            "severity": "warn",
            "message": "VFX_PetalGust should have auto_activate=False until triggered",
        })

    particle_gate = {"skipped": _is_null_rhi(), "bands": PARTICLE_BANDS, "note": "PIE/editor only"}
    critical = sum(1 for i in issues if i.get("severity") == "critical")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "canonical_canopy": canopy,
        "systems": systems,
        "mpc_material_bindings": mpc_material,
        "level_spawns": spawns,
        "hand_tune_checklist": hand_tune,
        "hand_tune_notes": {k: setup_mod.SAKURA_TUNING_NOTES.get(k, []) for k in setup_mod.PETAL_SYSTEMS},
        "particle_count_gate": particle_gate,
        "issues": issues,
        "critical_count": critical,
        "clean": critical == 0 and not any(i.get("severity") == "warn" for i in issues),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SakuraPetalAudit] clean={report['clean']} critical={critical} -> {REPORT_PATH}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_sakura_petal_niagara.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    report = run_audit()
    print(f"SAKURA_PETAL_AUDIT clean={report.get('clean')} critical={report.get('critical_count')}")
    return 0 if report.get("critical_count", 1) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
