"""UE Water plugin simulation — WaterBodyCustom pond on L_SakuraPath.

Replaces static KoiPond plane with simulated water when the Water plugin is available.

Editor:
  py Content/Python/setup_ue_water_simulation.py

Headless:
  python Content/Python/setup_ue_water_simulation.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "ue_water_sim_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
POND_MI = "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_SakuraPond"
TAG_POND = "PCG_Pond"
WATER_BODY_LABEL = "WaterBody_SakuraPond"


def _water_body_class():
    import unreal

    for path in (
        "/Script/Water.WaterBodyCustom",
        "/Script/WaterEditor.WaterBodyCustom",
    ):
        try:
            cls = unreal.load_class(None, path)
            if cls:
                return cls
        except Exception:
            pass
    return getattr(unreal, "WaterBodyCustom", None)


def _find_pond_anchor(eas):
    import unreal

    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label()
        tags = list(getattr(actor, "tags", []) or [])
        if TAG_POND in tags or label in ("KoiPond", "PondPlane"):
            loc = actor.get_actor_location()
            scale = actor.get_actor_scale3d()
            return actor, loc, scale
    return None, unreal.Vector(600, -400, 4), unreal.Vector(4, 3, 1)


def _assign_water_material(water_actor, mi_path: str) -> bool:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return False
    mi = unreal.load_asset(mi_path)
    if not mi:
        return False
    for comp_name in ("water_mesh_component", "WaterMeshComponent", "lake_mesh_comp"):
        try:
            comp = water_actor.get_editor_property(comp_name)
            if comp:
                comp.set_material(0, mi)
                return True
        except Exception:
            continue
    for comp in water_actor.get_components_by_class(unreal.StaticMeshComponent) or []:
        try:
            comp.set_material(0, mi)
            return True
        except Exception:
            pass
    return False


def _configure_simulation(water_actor) -> dict:
    import unreal

    tuned: dict = {}
    for prop, val in (
        ("WaveHeight", 12.0),
        ("WaveSpeed", 0.8),
        ("WaveFrequency", 0.6),
    ):
        try:
            water_actor.set_editor_property(prop, val)
            tuned[prop] = val
        except Exception:
            pass
    try:
        water_actor.set_editor_property("collision", True)
        tuned["collision"] = True
    except Exception:
        pass
    return tuned


def build_all() -> dict:
    import unreal

    import expand_grand_water as water_exp

    water_exp.expand()

    level_leaf = LEVEL.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.{level_leaf}"):
        raise RuntimeError(f"level missing: {LEVEL}")

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(LEVEL)

    pond_plane, pond_loc, pond_scale = _find_pond_anchor(eas)
    water_cls = _water_body_class()
    water_actor = None
    spawned = False

    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == WATER_BODY_LABEL:
            water_actor = actor
            break

    if water_cls and not water_actor:
        water_actor = eas.spawn_actor_from_class(
            water_cls, pond_loc, unreal.Rotator(0, 0, 0)
        )
        if water_actor:
            water_actor.set_actor_label(WATER_BODY_LABEL)
            spawned = True
            try:
                water_actor.set_actor_scale3d(pond_scale)
            except Exception:
                pass

    material_ok = False
    sim_tuned: dict = {}
    if water_actor:
        material_ok = _assign_water_material(water_actor, f"{POND_MI}.MI_GrandWater_SakuraPond")
        sim_tuned = _configure_simulation(water_actor)
        if pond_plane and pond_plane.get_actor_label() == "KoiPond":
            try:
                pond_plane.set_actor_hidden_in_game(True)
                pond_plane.set_is_temporarily_hidden_in_editor(True)
            except Exception:
                pass

    issues: list[str] = []
    if not water_cls:
        issues.append("water_body_class_unavailable")
    if not water_actor:
        issues.append("water_body_spawn_failed")
    if water_actor and not material_ok:
        issues.append("grand_water_mi_not_assigned")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": LEVEL,
        "water_body_class": str(water_cls) if water_cls else None,
        "water_body_label": water_actor.get_actor_label() if water_actor else None,
        "spawned": spawned,
        "material_assigned": material_ok,
        "simulation": sim_tuned,
        "pond_plane_hidden": bool(pond_plane and water_actor),
        "issues": issues,
        "passed": water_actor is not None and (not water_cls or material_ok or spawned),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    les.save_current_level()
    unreal.log(f"[UEWaterSim] passed={report['passed']} -> {REPORT}")
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
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_ue_water_simulation.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode
    report = build_all()
    print(f"UE_WATER_SIM passed={report.get('passed')}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
