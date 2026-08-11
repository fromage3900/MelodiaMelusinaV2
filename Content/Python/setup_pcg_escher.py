"""Escher style deployment — spawn PCG volumes with Escher impossible geometry.

Builds all 6 Escher PCG graphs (Relativity Room, Penrose Loop, Recursive Room,
Gravity Shift Corridor, Belvedere, Waterfall) then spawns tagged PCG volumes
in the target level.

Run (editor):
  py Content/Python/setup_pcg_escher.py
  py Content/Python/setup_pcg_escher.py --level L_SakuraPath
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_escher_deploy.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

ESCHER_DIR = "/Game/EnvSandbox/PCG/Styles/Escher"
ESCHER_GRAPHS = {
    "relativity_room": f"{ESCHER_DIR}/PCG_EscherRelativityRoom",
    "penrose_loop": f"{ESCHER_DIR}/PCG_EscherPenroseLoop",
    "recursive_room": f"{ESCHER_DIR}/PCG_EscherRecursiveRoom",
    "gravity_shift": f"{ESCHER_DIR}/PCG_EscherGravityShiftCorridor",
    "belvedere": f"{ESCHER_DIR}/PCG_EscherBelvedere",
    "waterfall": f"{ESCHER_DIR}/PCG_EscherWaterfall",
}
ESCHER_PREFIX = "PCG_Escher_"
DEFAULT_LEVEL = std.LEVEL_TEMPLATE

# Keep the primary room on the playable spine and stage the other studies as
# readable side exhibits instead of stacking every graph at the origin.
ESCHER_LAYOUT = {
    "relativity_room": (0.0, 520.0, 28.0),
    "penrose_loop": (0.0, 1120.0, 28.0),
    "recursive_room": (900.0, 1120.0, 28.0),
    "gravity_shift": (-900.0, 1120.0, 28.0),
    "belvedere": (900.0, 520.0, 28.0),
    "waterfall": (-900.0, 520.0, 28.0),
}


def _set_tag(actor, tag: str) -> None:
    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _destroy_prefix(eas, prefix: str) -> None:
    for actor in list(eas.get_all_level_actors() or []):
        label = actor.get_actor_label()
        if label == prefix or label.startswith(prefix):
            eas.destroy_actor(actor)


def _ensure_ground_tag(eas) -> bool:
    import unreal

    for actor in eas.get_all_level_actors() or []:
        tags = list(getattr(actor, "tags", []) or [])
        if std.TAG_GROUND in tags:
            return True
        if actor.get_actor_label() == "Ground":
            _set_tag(actor, std.TAG_GROUND)
            return True
    return False


def _ensure_ground_plane(eas) -> bool:
    import unreal

    if _ensure_ground_tag(eas):
        return True
    plane = "/Engine/BasicShapes/Plane.Plane"
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, -20), unreal.Rotator(0, 0, 0),
    )
    if not actor:
        return False
    try:
        actor.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass
    actor.set_actor_label("Ground")
    actor.set_actor_scale3d(unreal.Vector(80, 80, 1))
    sm = actor.static_mesh_component
    sm.set_static_mesh(unreal.load_asset(plane))
    _set_tag(actor, std.TAG_GROUND)
    return True


def _count_actor_ism(actor) -> int:
    import unreal

    return sum(
        component.get_instance_count()
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
    )


def _wait_for_actor_ism(actor, timeout_seconds: float = 20.0) -> int:
    """Allow the async PCG output to register before validating the volume."""
    deadline = time.time() + timeout_seconds
    count = 0
    while time.time() < deadline:
        count = _count_actor_ism(actor)
        if count > 0:
            return count
        time.sleep(0.25)
    return count


def build_escher_graphs(*, force: bool = False) -> dict:
    """Build all 6 Escher PCG graphs via build_escher_relativity_room."""
    import build_escher_relativity_room as ber

    return ber.build_all()


def deploy_escher_pcg(
    level: str = DEFAULT_LEVEL,
    *,
    rebuild: bool = False,
    generate: bool = True,
    save_level: bool = True,
) -> dict:
    import unreal

    graph_results = build_escher_graphs(force=rebuild)
    level_asset = f"{level}.{level.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        raise RuntimeError(f"level missing: {level}")

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(level)

    _destroy_prefix(eas, ESCHER_PREFIX)
    ground_ok = _ensure_ground_plane(eas)

    volumes: list[dict] = []
    total_ism = 0
    cx, cy, cz = std.PCG_VOLUME_CENTER
    sx, sy, sz = std.PCG_VOLUME_SCALE

    for key, graph_path in ESCHER_GRAPHS.items():
        label = f"{ESCHER_PREFIX}{key}"
        if not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
            volumes.append({"key": key, "label": label, "graph": graph_path, "error": "graph_missing"})
            continue
        graph = unreal.load_asset(graph_path)
        vol = eas.spawn_actor_from_class(
            unreal.PCGVolume,
            unreal.Vector(cx, cy, cz),
            unreal.Rotator(0, 0, 0),
        )
        try:
            vol.set_editor_property("is_spatially_loaded", False)
        except Exception:
            pass
        vol.set_actor_label(label)
        if key in ESCHER_LAYOUT:
            vol.set_actor_location(unreal.Vector(*ESCHER_LAYOUT[key]), False, False)
        vol.set_actor_scale3d(unreal.Vector(sx * 2, sy * 2, sz * 2))
        comp = vol.get_component_by_class(unreal.PCGComponent)
        gb.assign_pcg_graph(comp, graph)
        gb.configure_pcg_component(comp, seed=key.__hash__() % 100000, activated=True)

        generated = False
        ism_count = 0
        walkability = None
        if generate:
            import pcg_validate_helpers as vh

            try:
                vh.generate_and_wait(comp, force=True)
                generated = True
                # The helper can scan before PCG registers its output. Count
                # the generated actor as well so zero-output graphs cannot
                # look successful.
                ism_count = max(vh.count_ism(vol), _wait_for_actor_ism(vol))
                total_ism += ism_count
            except Exception as exc:
                volumes.append({"key": key, "label": label, "graph": graph_path, "generated": False, "error": str(exc)})
                continue

            import pcg_scale_alignment as psa

            walkability = psa.check_walkability_from_instances(vol)

        volumes.append({
            "key": key,
            "label": label,
            "graph": graph_path,
            "generated": generated,
            "ism": ism_count,
            "walkability": walkability,
        })

    # PCG output can register after the per-volume helper returns, especially
    # in World Partition maps. Reconcile the report from the live actors once
    # all graphs have had a chance to publish their ISM components.
    if generate:
        time.sleep(2.0)
        import pcg_scale_alignment as psa
        live_by_label = {
            actor.get_actor_label(): actor
            for actor in eas.get_all_level_actors() or []
            if actor.get_actor_label().startswith(ESCHER_PREFIX)
        }
        total_ism = 0
        for entry in volumes:
            actor = live_by_label.get(entry["label"])
            if actor:
                entry["ism"] = max(entry.get("ism", 0), _count_actor_ism(actor))
                if entry["ism"] > 0:
                    entry["walkability"] = psa.check_walkability_from_instances(actor)
            total_ism += entry.get("ism", 0)

    if save_level:
        les.save_current_level()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "setup_pcg_escher.py",
        "level": level,
        "ground_ok": ground_ok,
        "graph_results": graph_results,
        "volumes": volumes,
        "ism_total": total_ism,
    }
    report["passed"] = ground_ok and all(
        v.get("generated", True) and (not generate or v.get("ism", 0) > 0)
        for v in volumes
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[EscherPCG] passed={report['passed']} volumes={len(volumes)} ism={total_ism} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_escher.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    level = DEFAULT_LEVEL
    for i, arg in enumerate(sys.argv):
        if arg == "--level" and i + 1 < len(sys.argv):
            value = sys.argv[i + 1]
            level = value if value.startswith("/Game/") else f"/Game/EnvSandbox/{value}"

    report = deploy_escher_pcg(
        level,
        rebuild="--rebuild" in sys.argv or "--force" in sys.argv,
        generate="--no-generate" not in sys.argv,
        save_level="--no-save" not in sys.argv,
    )
    print(f"ESCHER_PCG passed={report['passed']} volumes={len(report['volumes'])} ism={report['ism_total']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
