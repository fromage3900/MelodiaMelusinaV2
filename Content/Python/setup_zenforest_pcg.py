"""Apply PCG scatter to ZenForestTest landscape.

  py Content/Python/setup_zenforest_pcg.py
  py Content/Python/setup_zenforest_pcg.py --mode melodia
  py Content/Python/setup_zenforest_pcg.py --mode portfolio --no-generate
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std
import pcg_validate_helpers as vh

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zenforest_pcg_apply.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

LEVEL_ZEN_FOREST = "/Game/ZenForestTest"
LEVEL = LEVEL_ZEN_FOREST

MELODIA_PCG_ROOT = "/Game/Melodia/_PROJECT/PCG"
GRAPH_MELODIA = f"{MELODIA_PCG_ROOT}/Graphs/PCG_MelodiaForest"

ACTOR_FOREST = "PCG_ZenForest_Cover"
ACTOR_ROCKS = "PCG_ZenForest_Rocks"
MIN_ISM = 80


def _destroy_prefix(eas, prefix: str) -> None:
    for actor in list(eas.get_all_level_actors() or []):
        label = actor.get_actor_label()
        if label == prefix or label.startswith(prefix):
            eas.destroy_actor(actor)


def _spawn_volume(eas, label: str, graph_path: str, seed: int = 1001):
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
        raise RuntimeError(f"missing graph: {graph_path}")
    graph = unreal.load_asset(graph_path)
    vol = eas.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(0, 0, 0),
        unreal.Rotator(0, 0, 0),
    )
    vol.set_actor_label(label)
    vol.set_actor_scale3d(unreal.Vector(100, 100, 10))
    comp = vol.get_component_by_class(unreal.PCGComponent)
    gb.assign_pcg_graph(comp, graph)
    gb.configure_pcg_component(comp, seed=seed, activated=True)
    return vol, comp


def apply(mode: str = "portfolio", generate: bool = True) -> dict:
    import unreal
    import setup_pcg_universal as uni

    level_asset = f"{LEVEL}.{LEVEL.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        raise RuntimeError(f"level missing: {LEVEL}")

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level(LEVEL)

    landscape = _find_landscape_actor(eas)
    if not landscape:
        return {"passed": False, "error": "no landscape actor in level"}

    if mode == "portfolio":
        forest_graph = std.GRAPH_FOLIAGE
        uni.build_foliage(force=True, density=0.42, voxel_cm=180.0, grass_mi=std.MI_GREYBOX_GRASS)
    else:
        forest_graph = GRAPH_MELODIA

    _destroy_prefix(eas, ACTOR_FOREST)
    _destroy_prefix(eas, ACTOR_ROCKS)

    forest_vol, forest_comp = _spawn_volume(eas, ACTOR_FOREST, forest_graph, seed=std.SEED_FOLIAGE)
    gb.fit_volume_to_ground(forest_vol, eas)

    ism_forest = 0
    gen_ok = False
    if generate:
        try:
            vh.generate_and_wait(forest_comp, force=True)
            gen_ok = True
            ism_forest = max(vh.count_ism(forest_vol), 0)
        except Exception as exc:
            unreal.log_error(f"[ZenForestPCG] generate failed: {exc}")

    ism_rocks = 0
    rock_vol, rock_comp = _spawn_volume(eas, ACTOR_ROCKS, std.GRAPH_ROCK, seed=std.SEED_ROCKS)
    if generate:
        try:
            vh.generate_and_wait(rock_comp, force=True)
            ism_rocks = vh.count_ism(rock_vol)
        except Exception:
            pass

    total_ism = ism_forest + ism_rocks
    passed = gen_ok and total_ism >= MIN_ISM if generate else True

    les.save_current_level()
    report = {
        "level": LEVEL,
        "mode": mode,
        "landscape": bool(landscape),
        "graphs": {"forest": forest_graph, "rock": std.GRAPH_ROCK},
        "ism_forest": ism_forest,
        "ism_rocks": ism_rocks,
        "ism_total": total_ism,
        "min_ism": MIN_ISM,
        "generated": gen_ok,
        "passed": passed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ZenForestPCG] passed={report['passed']} ism={total_ism} -> {REPORT}")
    return report


def _find_landscape_actor(eas):
    """Find a Landscape actor in the level (LandscapeProxy or Landscape)."""
    import unreal

    for actor in eas.get_all_level_actors() or []:
        if isinstance(actor, (unreal.Landscape, unreal.LandscapeProxy)):
            return actor
        cls_name = actor.get_class().get_name()
        if "Landscape" in cls_name:
            return actor
    return None


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            return 1
        script = (PROJECT_ROOT / 'Content/Python/setup_zenforest_pcg.py').as_posix()
        forwarded = [a for a in sys.argv[1:] if a.startswith("--")]
        script_cmd = f"{script} {' '.join(forwarded)}" if forwarded else script
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={script_cmd}",
            "-stdout", "-unattended", "-nosplash", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    mode = "portfolio"
    generate = "--no-generate" not in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1].lower()

    result = apply(mode=mode, generate=generate)
    print(f"ZENFOREST_PCG mode={mode} passed={result.get('passed')} ism={result.get('ism_total')}")
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
