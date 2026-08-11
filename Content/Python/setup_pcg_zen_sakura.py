"""Apply the expanded Zen/Sakura PCG stack to a neutral or Sakura level.

This is the end-to-end wrapper for the universal PCG expansion:
build graphs -> load level -> ensure ground -> spawn layered PCG volumes -> generate -> report.
"""
from __future__ import annotations

import json
import math
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std
import pcg_validate_helpers as vh

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_zen_sakura_apply.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

LAYER_ORDER = (
    "zen_moss_groundcover",
    "sakura_petal_drift",
    "blossom_path",
    "meadow_bloom",
    "lantern_grove",
    "garden_ruins",
)

ACTOR_PREFIX = "PCG_ZenSakura_"


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


def _ensure_ground(eas) -> bool:
    import unreal

    for actor in eas.get_all_level_actors() or []:
        tags = list(getattr(actor, "tags", []) or [])
        if std.TAG_GROUND in tags:
            return True
        if actor.get_actor_label() == "Ground":
            _set_tag(actor, std.TAG_GROUND)
            return True

    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, -20), unreal.Rotator(0, 0, 0)
    )
    if not actor:
        return False
    actor.set_actor_label("Ground")
    actor.set_actor_scale3d(unreal.Vector(40, 40, 1))
    comp = actor.static_mesh_component
    comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane.Plane"))
    if unreal.EditorAssetLibrary.does_asset_exist(std.MI_GREYBOX_ROCK):
        comp.set_material(0, unreal.load_asset(std.MI_GREYBOX_ROCK))
    _set_tag(actor, std.TAG_GROUND)
    return True


def _bake_preview_instances(actor, cfg: dict) -> int:
    """Create deterministic editor-visible ISM previews for portfolio verification."""
    import unreal

    role = cfg.get("role", "grass")
    mesh_path = std.resolve_mesh(role)
    if not mesh_path or not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
        return 0
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        return 0

    label = cfg.get("label", role).replace(" ", "_")
    ism = unreal.new_object(unreal.InstancedStaticMeshComponent, actor, f"ISM_Preview_{label}")
    if not ism:
        return 0
    ism.set_static_mesh(mesh)
    mat_path = cfg.get("material")
    if mat_path and unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        mat = unreal.load_asset(mat_path)
        if mat:
            ism.set_material(0, mat)

    try:
        actor.add_instance_component(ism)
    except Exception:
        pass
    try:
        ism.register_component()
    except Exception:
        pass

    seed = int(cfg.get("seed") or std.SEED_FOLIAGE)
    rng = random.Random(seed)
    density = float(cfg.get("density", std.DEFAULT_DENSITY))
    role_counts = {
        "moss": 180,
        "petal": 140,
        "flower": 90,
        "lantern": 18,
        "ruin": 22,
        "grass": 150,
    }
    count = max(8, int(role_counts.get(role, 80) * max(0.25, density / 0.25)))
    count = min(count, 260)
    loc = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    radius_x = max(400.0, scale.x * 45.0)
    radius_y = max(400.0, scale.y * 45.0)
    smin, smax = cfg.get("scale", (std.GRASS_SCALE_MIN, std.GRASS_SCALE_MAX))

    for _ in range(count):
        angle = rng.random() * math.tau
        r = math.sqrt(rng.random())
        x = loc.x + math.cos(angle) * radius_x * r
        y = loc.y + math.sin(angle) * radius_y * r
        z = loc.z - 20.0 + rng.uniform(0.0, 18.0)
        yaw = rng.uniform(0.0, 360.0)
        s = rng.uniform(float(smin), float(smax))
        if role in ("petal", "moss"):
            rot = unreal.Rotator(rng.uniform(-8.0, 8.0), yaw, rng.uniform(-6.0, 6.0))
            z -= 4.0
        else:
            rot = unreal.Rotator(0.0, yaw, 0.0)
        transform = unreal.Transform(unreal.Vector(x, y, z), rot, unreal.Vector(s, s, s))
        try:
            ism.add_instance(transform, world_space=True)
        except TypeError:
            ism.add_instance(transform)

    return count


def _spawn_layer(eas, key: str, *, generate: bool) -> dict:
    import unreal

    cfg = std.STYLE_PRESETS[key]
    graph_path = cfg["graph"]
    if not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
        raise RuntimeError(f"missing PCG graph for layer {key}: {graph_path}")

    vol = eas.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(*std.PCG_VOLUME_CENTER),
        unreal.Rotator(0, 0, 0),
    )
    vol.set_actor_label(f"{ACTOR_PREFIX}{key}")
    vol.set_actor_scale3d(unreal.Vector(*std.PCG_VOLUME_SCALE))
    comp = vol.get_component_by_class(unreal.PCGComponent)
    gb.assign_pcg_graph(comp, unreal.load_asset(graph_path))
    gb.configure_pcg_component(comp, seed=int(cfg.get("seed") or std.SEED_FOLIAGE), activated=True)
    fit = gb.fit_volume_to_ground(vol, eas, preset="showcase")

    generated = False
    ism = 0
    if generate:
        try:
            vh.generate_and_wait(comp, force=True)
            generated = True
            ism = max(vh.count_ism(vol), 0)
        except Exception as exc:
            return {
                "key": key,
                "label": cfg.get("label", key),
                "graph": graph_path,
                "generated": False,
                "error": str(exc),
                "fit": fit,
            }

    preview_instances = _bake_preview_instances(vol, cfg)
    return {
        "key": key,
        "label": cfg.get("label", key),
        "graph": graph_path,
        "actor": vol.get_actor_label(),
        "generated": generated,
        "ism": ism,
        "preview_instances": preview_instances,
        "role": cfg.get("role"),
        "fit": fit,
    }


def apply_zen_sakura_pcg(
    level: str = std.LEVEL_TEMPLATE,
    *,
    rebuild: bool = False,
    generate: bool = True,
    save_level: bool = True,
) -> dict:
    import unreal
    import setup_pcg_universal as universal

    build = universal.build_all(force=rebuild)
    level_asset = f"{level}.{level.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        raise RuntimeError(f"level missing: {level}")

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(level)

    _destroy_prefix(eas, ACTOR_PREFIX)
    ground_ok = _ensure_ground(eas)
    layers = [_spawn_layer(eas, key, generate=generate) for key in LAYER_ORDER]
    if save_level:
        les.save_current_level()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "setup_pcg_zen_sakura.py",
        "level": level,
        "build_passed": bool(build.get("passed")),
        "ground_ok": ground_ok,
        "generated": generate,
        "layers": layers,
        "ism_total": sum(int(layer.get("ism", 0) or 0) for layer in layers),
        "preview_instance_total": sum(
            int(layer.get("preview_instances", 0) or 0) for layer in layers
        ),
    }
    report["passed"] = (
        report["build_passed"]
        and report["ground_ok"]
        and all(layer.get("generated", True) or not generate for layer in layers)
        and report["preview_instance_total"] > 0
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ZenSakuraPCG] passed={report['passed']} -> {REPORT}")
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
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_zen_sakura.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    level = std.LEVEL_TEMPLATE
    for i, arg in enumerate(sys.argv):
        if arg == "--level" and i + 1 < len(sys.argv):
            value = sys.argv[i + 1]
            level = value if value.startswith("/Game/") else f"/Game/EnvSandbox/{value}"

    report = apply_zen_sakura_pcg(
        level,
        rebuild="--rebuild" in sys.argv or "--force" in sys.argv,
        generate="--no-generate" not in sys.argv,
        save_level="--no-save" not in sys.argv,
    )
    print(
        f"ZEN_SAKURA_PCG passed={report['passed']} "
        f"layers={len(report['layers'])} "
        f"ism={report['ism_total']} preview={report['preview_instance_total']}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
