r"""Before/after scene-context cycle for Melodia Unreal worldbuilding agents.

This is a thin companion to ``scene_context_snapshot.py``. It does not mutate the
level. It creates a stable before packet, regenerates the live snapshot after an
edit, and writes a compact spatial diff for review/falsification.

Typical editor usage:

    exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_cycle.py").read()); begin()
    # make the bounded world/level change
    exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python\scene_context_cycle.py").read()); end()

Outputs under ``Saved/Audit/SceneContext/<LevelName>/``:

    scene_context_before.json
    viewport_before.png
    top_before.png
    scene_context_after.json
    viewport_after.png
    top_after.png
    scene_context_diff.json

The diff is spatial evidence only. CURRENT_STATE.md and durable contracts remain
authoritative. Actor comparisons are intentionally limited to the prioritized
scene-context set emitted by ``scene_context_snapshot.py``.
"""

from __future__ import annotations

import importlib.util
import json
import math
import shutil
from pathlib import Path


def _load_snapshot_module():
    module_path = Path(__file__).with_name("scene_context_snapshot.py")
    spec = importlib.util.spec_from_file_location("melodia_scene_context_snapshot", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load scene context module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _output_dir(report: dict) -> Path:
    import unreal

    level_name = report["level"]["name"]
    return Path(unreal.Paths.project_saved_dir()) / "Audit" / "SceneContext" / level_name


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)


def _write_packet(report: dict, label: str) -> Path:
    out = _output_dir(report)
    out.mkdir(parents=True, exist_ok=True)
    packet = out / f"scene_context_{label}.json"
    packet.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _copy_if_exists(out / "viewport_latest.png", out / f"viewport_{label}.png")
    _copy_if_exists(out / "top_latest.png", out / f"top_{label}.png")
    return packet


def _actor_key(row: dict) -> str:
    return f"{row.get('class', '')}::{row.get('label', '')}"


def _actor_map(report: dict) -> dict[str, dict]:
    return {
        _actor_key(row): row
        for row in report.get("spatial_context_actors", [])
    }


def _pcg_map(report: dict) -> dict[str, dict]:
    return {_actor_key(row): row for row in report.get("pcg_actors", [])}


def _vec_delta(a: dict | None, b: dict | None) -> float:
    if not a or not b:
        return 0.0
    return math.sqrt(
        (float(b.get("x", 0.0)) - float(a.get("x", 0.0))) ** 2
        + (float(b.get("y", 0.0)) - float(a.get("y", 0.0))) ** 2
        + (float(b.get("z", 0.0)) - float(a.get("z", 0.0))) ** 2
    )


def _rotation_changed(a: dict | None, b: dict | None, tolerance=0.05) -> bool:
    if not a or not b:
        return False
    return any(
        abs(float(b.get(axis, 0.0)) - float(a.get(axis, 0.0))) > tolerance
        for axis in ("pitch", "yaw", "roll")
    )


def _scale_changed(a: dict | None, b: dict | None, tolerance=0.001) -> bool:
    if not a or not b:
        return False
    return any(
        abs(float(b.get(axis, 0.0)) - float(a.get(axis, 0.0))) > tolerance
        for axis in ("x", "y", "z")
    )


def _tagged_keys(report: dict) -> set[str]:
    return {_actor_key(row) for row in report.get("route_and_exclusion_actors", [])}


def compare(before: dict, after: dict) -> dict:
    if before.get("level", {}).get("path") != after.get("level", {}).get("path"):
        raise RuntimeError(
            "Scene-context baseline and after packet are from different levels: "
            f"{before.get('level', {}).get('path')} != {after.get('level', {}).get('path')}"
        )

    bmap = _actor_map(before)
    amap = _actor_map(after)
    bkeys, akeys = set(bmap), set(amap)

    added = [amap[key] for key in sorted(akeys - bkeys)]
    removed = [bmap[key] for key in sorted(bkeys - akeys)]
    changed = []

    for key in sorted(bkeys & akeys):
        b, a = bmap[key], amap[key]
        distance = _vec_delta(b.get("location"), a.get("location"))
        rot_changed = _rotation_changed(b.get("rotation"), a.get("rotation"))
        scale_changed = _scale_changed(b.get("scale"), a.get("scale"))
        tags_changed = b.get("tags", []) != a.get("tags", [])
        mesh_changed = b.get("static_mesh") != a.get("static_mesh")
        if distance > 0.1 or rot_changed or scale_changed or tags_changed or mesh_changed:
            changed.append(
                {
                    "key": key,
                    "location_delta_cm": round(distance, 3),
                    "rotation_changed": rot_changed,
                    "scale_changed": scale_changed,
                    "tags_changed": tags_changed,
                    "static_mesh_changed": mesh_changed,
                    "before": b,
                    "after": a,
                }
            )

    bpcg, apcg = _pcg_map(before), _pcg_map(after)
    pcg_changes = []
    for key in sorted(set(bpcg) | set(apcg)):
        b = bpcg.get(key)
        a = apcg.get(key)
        if b is None or a is None:
            pcg_changes.append({"key": key, "before": b, "after": a})
            continue
        bcount = int(b.get("pcg", {}).get("generated_instance_count", 0))
        acount = int(a.get("pcg", {}).get("generated_instance_count", 0))
        bgraph = b.get("pcg", {}).get("graph")
        agraph = a.get("pcg", {}).get("graph")
        if bcount != acount or bgraph != agraph or _vec_delta(b.get("location"), a.get("location")) > 0.1:
            pcg_changes.append(
                {
                    "key": key,
                    "instance_count_before": bcount,
                    "instance_count_after": acount,
                    "instance_count_delta": acount - bcount,
                    "graph_before": bgraph,
                    "graph_after": agraph,
                    "location_delta_cm": round(_vec_delta(b.get("location"), a.get("location")), 3),
                }
            )

    before_tagged = _tagged_keys(before)
    after_tagged = _tagged_keys(after)

    return {
        "schema": "melodia.scene_context_diff.v1",
        "authority": "Ephemeral spatial evidence only; not project status or gameplay authority.",
        "level": before.get("level", {}).get("path"),
        "summary": {
            "prioritized_actors_added": len(added),
            "prioritized_actors_removed": len(removed),
            "prioritized_actors_changed": len(changed),
            "pcg_actors_changed": len(pcg_changes),
            "route_or_exclusion_membership_changed": before_tagged != after_tagged,
            "actor_count_before": before.get("level", {}).get("actor_count"),
            "actor_count_after": after.get("level", {}).get("actor_count"),
        },
        "world_bounds_before": before.get("level", {}).get("world_bounds"),
        "world_bounds_after": after.get("level", {}).get("world_bounds"),
        "viewport_before": before.get("viewport"),
        "viewport_after": after.get("viewport"),
        "added": added,
        "removed": removed,
        "changed": changed,
        "pcg_changes": pcg_changes,
        "route_or_exclusion_added": sorted(after_tagged - before_tagged),
        "route_or_exclusion_removed": sorted(before_tagged - after_tagged),
        "review_questions": [
            "Did the intended landmark/silhouette improve from the same camera?",
            "Did any PCG count or graph change unexpectedly?",
            "Did route/no-scatter/landmark-clear membership change intentionally?",
            "Did the edit preserve human-scale traversal clearance?",
            "Are added/removed actors expected and promotable?",
        ],
        "limitations": [
            "Actor diffs cover the prioritized spatial-context set, not every actor in the level.",
            "Visual quality still requires owner/editor judgment from before/after captures.",
        ],
    }


def begin() -> dict:
    snapshot = _load_snapshot_module()
    report = snapshot.snapshot_scene(capture_images=True)
    packet = _write_packet(report, "before")
    import unreal
    unreal.log(f"[SceneContextCycle] BEFORE -> {packet}")
    return report


def end() -> dict:
    snapshot = _load_snapshot_module()
    report = snapshot.snapshot_scene(capture_images=True)
    out = _output_dir(report)
    before_path = out / "scene_context_before.json"
    if not before_path.exists():
        raise RuntimeError(
            f"No baseline at {before_path}. Run scene_context_cycle.begin() before editing."
        )
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after_path = _write_packet(report, "after")
    after = json.loads(after_path.read_text(encoding="utf-8"))
    diff = compare(before, after)
    diff_path = out / "scene_context_diff.json"
    diff_path.write_text(json.dumps(diff, indent=2), encoding="utf-8")
    import unreal
    unreal.log(
        "[SceneContextCycle] AFTER actors_changed=%d pcg_changed=%d -> %s"
        % (
            diff["summary"]["prioritized_actors_changed"],
            diff["summary"]["pcg_actors_changed"],
            diff_path,
        )
    )
    return diff


if __name__ == "__main__":
    print(
        "Scene Context Cycle loaded. Call begin() before a bounded spatial edit, "
        "then end() after the edit."
    )
