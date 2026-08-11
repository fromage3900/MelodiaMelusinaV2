"""Audit and verify PCG scatter on all 4 WP pillar levels in a single pass.

Run in-editor:
  py Content/Python/wp_pillar_verify.py
  py Content/Python/wp_pillar_verify.py --pillar SakuraDream
  py Content/Python/wp_pillar_verify.py --heatmap

Output:
  Saved/Audit/wp_pillar_verify_{timestamp}.json    — per-pillar instance counts + health
  Saved/Portfolio/PCG/{level}_pcg_heatmap_*.png    — (if --heatmap) density plates

Verification checks:
  - Level loaded successfully
  - PCGVolume actors found with assigned graphs
  - Each graph generates > 0 ISM instances (without crashing)
  - Graph paths are resolvable (no missing asset errors)
  - Self-pruning property names logged (via pcg_probe_settings if available)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


LEVEL_DIR = "/Game/EnvSandbox/Environments/WP"
PILLAR_LEVELS = {
    "SakuraDream": f"{LEVEL_DIR}/L_WP_SakuraDream",
    "SpaceCathedral": f"{LEVEL_DIR}/L_WP_SpaceCathedral",
    "BaroqueGrotto": f"{LEVEL_DIR}/L_WP_BaroqueGrotto",
    "CosmicOrrery": f"{LEVEL_DIR}/L_WP_CosmicOrrery",
}

MIN_ISM_THRESHOLD = 10  # minimum instances per graph to consider it "producing"


def verify_level(level_path: str, pillar_key: str) -> dict:
    import unreal

    import pcg_validate_helpers as vh

    result: dict = {
        "pillar": pillar_key,
        "level_path": level_path,
        "loaded": False,
        "pcg_volumes": [],
        "total_ism": 0,
        "graphs_failing": [],
        "graphs_producing": [],
        "errors": [],
    }

    # 1. Load level
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    try:
        les.load_level(level_path)
        result["loaded"] = True
        unreal.log(f"[WPVfy] Loaded {level_path}")
    except Exception as e:
        result["errors"].append(f"load failed: {e}")
        return result

    # 2. Find PCGVolume actors
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = eas.get_all_level_actors() or []
    pcg_vols = []
    pcg_vol_cls = unreal.PCGVolume.static_class()

    for actor in all_actors:
        if actor.get_class() != pcg_vol_cls:
            continue
        comp = actor.get_component_by_class(unreal.PCGComponent)
        if not comp:
            continue
        graph = comp.get_editor_property("graph_instance") or comp.get_graph()
        if not graph:
            pcg_vols.append({"label": actor.get_actor_label(), "graph": None, "ism": 0, "error": "no graph assigned"})
            continue
        pcg_vols.append({
            "label": actor.get_actor_label(),
            "graph": graph.get_path_name(),
            "location": {
                "x": actor.get_actor_location().x,
                "y": actor.get_actor_location().y,
                "z": actor.get_actor_location().z,
            },
        })

    # 3. Generate and count
    for vol_info in pcg_vols:
        if vol_info.get("error"):
            result["graphs_failing"].append(vol_info)
            continue

        label = vol_info["label"]
        actor = eas.get_actor_reference(label)
        if not actor:
            vol_info["error"] = "actor reference lost"
            result["graphs_failing"].append(vol_info)
            continue

        comp = actor.get_component_by_class(unreal.PCGComponent)
        if not comp:
            vol_info["error"] = "no PCG component"
            result["graphs_failing"].append(vol_info)
            continue

        try:
            vh.generate_and_wait(comp, force=True)
            ism = max(vh.count_ism(actor), 0)
            vol_info["ism"] = ism
            result["total_ism"] += ism

            if ism >= MIN_ISM_THRESHOLD:
                result["graphs_producing"].append(vol_info)
            else:
                vol_info["error"] = f"low count ({ism} < {MIN_ISM_THRESHOLD})"
                result["graphs_failing"].append(vol_info)

        except Exception as exc:
            vol_info["error"] = str(exc)[:200]
            result["graphs_failing"].append(vol_info)
            unreal.log_warning(f"[WPVfy] {label} generate failed: {exc}")

    # 4. Health summary
    total_graphs = len(pcg_vols)
    result["health"] = {
        "total_graphs": total_graphs,
        "producing": len(result["graphs_producing"]),
        "failing": len(result["graphs_failing"]),
        "total_ism": result["total_ism"],
        "pass": len(result["graphs_failing"]) == 0 and total_graphs > 0,
    }

    unreal.log(f"[WPVfy] {pillar_key}: {result['health']['producing']}/{total_graphs} producing, {result['total_ism']} total ISM")
    return result


def probe_self_pruning() -> dict | None:
    try:
        import pcg_probe_settings
        return pcg_probe_settings.probe_pcg_self_pruning()
    except Exception:
        return None


def main() -> int:
    args = _parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Optional: probe SelfPruning properties
    pruning_info = None
    if args.get("probe"):
        pruning_info = probe_self_pruning()

    # Select pillars
    pillar_keys = [args["pillar"]] if args["pillar"] else list(PILLAR_LEVELS.keys())

    report = {
        "timestamp": timestamp,
        "pillars_checked": pillar_keys,
        "self_pruning_probe": pruning_info,
        "results": [],
        "summary": {"pass": [], "fail": []},
    }

    for key in pillar_keys:
        level_path = PILLAR_LEVELS[key]
        result = verify_level(level_path, key)
        report["results"].append(result)
        if result["health"]["pass"]:
            report["summary"]["pass"].append(key)
        else:
            report["summary"]["fail"].append(key)

    # Write audit
    import unreal
    audit_dir = Path(unreal.Paths.project_saved_dir()) / "Audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    out_path = audit_dir / f"wp_pillar_verify_{timestamp}.json"

    with open(str(out_path), "w") as f:
        json.dump(report, f, indent=2, default=str)

    unreal.log(f"[WPVfy] Report: {out_path}")

    # Optional heatmap
    if args.get("heatmap"):
        try:
            import pcg_heatmap_exporter
            for key in pillar_keys:
                les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
                les.load_level(PILLAR_LEVELS[key])
                pcg_heatmap_exporter.export_pcg_heatmap()
        except Exception as e:
            unreal.log_warning(f"[WPVfy] Heatmap failed: {e}")

    if "json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    else:
        passed = len(report["summary"]["pass"])
        failed = len(report["summary"]["fail"])
        print(f"[WPVfy] {passed} passed, {failed} failed. Report: {out_path}")

    return 0 if not report["summary"]["fail"] else 1


def _parse_args() -> dict:
    args: dict = {"pillar": "", "probe": False, "heatmap": False}
    for arg in sys.argv:
        if arg.startswith("--pillar="):
            args["pillar"] = arg.split("=", 1)[1]
        elif arg == "--pillar":
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                args["pillar"] = sys.argv[idx + 1]
        elif arg == "--probe":
            args["probe"] = True
        elif arg == "--heatmap":
            args["heatmap"] = True
    return args


if __name__ == "__main__":
    raise SystemExit(main())
