"""Guarded live UE promotion for MUAL-2.

This is the only live promotion writer in the universal lane.  It uses the
project's existing Monolith animation/editor actions, snapshots the live
consumer state before mutation, refuses duplicate samples/assets, saves only
the requested package, and verifies the result before marking a manifest
promoted.  Without ``--apply`` it performs the read-only preflight only.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT = PIPELINE_DIR.parents[1]
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
TOOLS_DIR = PROJECT / "Tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from manifest_v2 import read_json, validate_v2  # noqa: E402
from mcp_client import monolith  # noqa: E402


BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
BACKUP_DIR = PROJECT / "Saved/Audit/mual_promotion_backups"
DEFAULT_REPORT = PROJECT / "Saved/Audit/mual_live_promotion.json"


class LivePromotionError(RuntimeError):
    pass


def _call(tool: str, action: str, params: dict[str, Any] | None = None, timeout: int = 90) -> dict[str, Any]:
    raw = monolith(tool, {"action": action, "params": params or {}}, timeout=timeout)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise LivePromotionError(f"{tool}:{action}: {raw}")
    try:
        result = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise LivePromotionError(f"{tool}:{action}: invalid JSON response: {raw!r}") from exc
    if isinstance(result, dict) and (result.get("success") is False or result.get("ok") is False or result.get("error")):
        raise LivePromotionError(f"{tool}:{action}: {result.get('error') or result}")
    if not isinstance(result, dict):
        raise LivePromotionError(f"{tool}:{action}: response is not an object")
    return result


def _asset_path(value: str) -> str:
    return str(value or "").split(".", 1)[0].replace("\\", "/")


def _sample_rows(info: dict[str, Any]) -> list[dict[str, Any]]:
    rows = info.get("samples")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _backup(label: str, payload: dict[str, Any]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"{stamp}_{label}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _save_package(package_path: str) -> dict[str, Any]:
    return _call(
        "editor_query",
        "save_packages",
        {"packages": [_asset_path(package_path)], "fail_on_unrequested_dirty": True},
    )


def _editor_python_json(command: str) -> dict[str, Any]:
    """Run a read-only editor probe and decode its final JSON print."""
    response = _call("editor_query", "run_python", {"command": command})
    for entry in reversed(response.get("output") or []):
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("output") or "").strip()
        if not value:
            continue
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed
    raise LivePromotionError(f"editor verification returned no JSON object: {response}")


def _blendspace_preflight(
    animation: str,
    speed: float,
    *,
    replace_existing_speed: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], str, list[dict[str, Any]]]:
    before = _call("animation_query", "get_blend_space_info", {"asset_path": BLENDSPACE})
    skeleton = str(before.get("skeleton", ""))
    if TARGET_SKELETON not in skeleton:
        raise LivePromotionError(f"BlendSpace skeleton is {skeleton!r}, expected {TARGET_SKELETON!r}")
    rows = _sample_rows(before)
    normalized_animation = _asset_path(animation)
    if any(_asset_path(str(row.get("animation", ""))) == normalized_animation for row in rows):
        raise LivePromotionError("animation already exists as a live BlendSpace sample")
    replacement_rows = [
        row for row in rows
        if abs(float(row.get("x", 0.0)) - speed) < 0.01
    ]
    if replacement_rows and not replace_existing_speed:
        raise LivePromotionError("speed already exists as a live BlendSpace sample")
    if len(replacement_rows) > 1:
        raise LivePromotionError("multiple live samples occupy the replacement speed")
    return before, rows, normalized_animation, replacement_rows


def _promote_blendspace(
    animation: str,
    speed: float,
    *,
    replace_existing_speed: bool = False,
) -> dict[str, Any]:
    before, rows, normalized_animation, replacement_rows = _blendspace_preflight(
        animation,
        speed,
        replace_existing_speed=replace_existing_speed,
    )
    backup = _backup(
        "blendspace",
        {
            "consumer": "blendspace",
            "asset": BLENDSPACE,
            "before": before,
            "replacement_rows": replacement_rows,
        },
    )
    deleted = None
    if replacement_rows:
        deleted = _call(
            "animation_query",
            "delete_blendspace_sample",
            {"asset_path": BLENDSPACE, "sample_index": int(replacement_rows[0].get("index", 0))},
        )
    added = _call(
        "animation_query",
        "add_blendspace_sample",
        {"asset_path": BLENDSPACE, "anim_path": normalized_animation, "x": speed, "y": 0.0},
    )
    saved = _save_package(BLENDSPACE)
    after = _call("animation_query", "get_blend_space_info", {"asset_path": BLENDSPACE})
    after_rows = _sample_rows(after)
    matches = [
        row for row in after_rows
        if _asset_path(str(row.get("animation", ""))) == normalized_animation
        and abs(float(row.get("x", 0.0)) - speed) < 0.01
    ]
    expected_count = len(rows) if replacement_rows else len(rows) + 1
    if len(matches) != 1 or len(after_rows) != expected_count:
        raise LivePromotionError("live BlendSpace verification found an unexpected sample count or placement")
    if replacement_rows and any(
        _asset_path(str(row.get("animation", ""))) == _asset_path(str(replacement_rows[0].get("animation", "")))
        and abs(float(row.get("x", 0.0)) - speed) < 0.01
        for row in after_rows
    ):
        raise LivePromotionError("replacement BlendSpace sample was not removed")
    return {
        "consumer": "blendspace",
        "asset": BLENDSPACE,
        "added": added,
        "deleted": deleted,
        "saved": saved,
        "before": before,
        "after": after,
        "rollback_backup": str(backup),
        "replacement": bool(replacement_rows),
    }


def _montage_preflight(montage_target: str) -> tuple[str, dict[str, Any] | None]:
    target = _asset_path(montage_target)
    if not target:
        raise LivePromotionError("montage target is required")
    try:
        existing = _call("animation_query", "get_montage_info", {"asset_path": target})
    except LivePromotionError as exc:
        if "Montage not found" not in str(exc):
            raise
        existing = None
    if existing is not None:
        raise LivePromotionError("montage target already exists; refusing to overwrite a runtime asset")
    return target, existing


def _promote_montage(animation: str, montage_target: str) -> dict[str, Any]:
    target, existing = _montage_preflight(montage_target)
    backup = _backup("montage", {"consumer": "montage", "asset": target, "before": None, "note": "target did not exist; rollback is delete-new-asset only"})
    # UE's AnimMontageFactory is the solved editor path for a one-sequence
    # montage: unlike the generic Monolith section helper, it initializes the
    # read-only SequenceLength from the source AnimSequence before saving.
    # Keep this inside the existing editor bridge so the universal promoter
    # remains idempotent and does not spawn another Unreal process.
    factory_script = (
        "import unreal\n"
        f"target = {target!r}\n"
        f"folder = {target.rsplit('/', 1)[0]!r}\n"
        f"animation = { _asset_path(animation)!r}\n"
        "sequence = unreal.EditorAssetLibrary.load_asset(animation)\n"
        "skeleton = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton')\n"
        "if sequence is None or skeleton is None: raise RuntimeError('montage source sequence or target skeleton is missing')\n"
        "factory = unreal.AnimMontageFactory()\n"
        "factory.set_editor_property('source_animation', sequence)\n"
        "factory.set_editor_property('target_skeleton', skeleton)\n"
        "asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(target.rsplit('/', 1)[1], folder, unreal.AnimMontage, factory)\n"
        "if asset is None: raise RuntimeError('AnimMontageFactory returned no asset')\n"
        "import json\n"
        "print(json.dumps({'asset': asset.get_path_name(), 'duration': asset.get_play_length(), 'skeleton': asset.get_skeleton().get_path_name()}))\n"
    )
    created = _call(
        "editor_query",
        "run_python",
        {"command": factory_script},
    )
    blend = _call(
        "animation_query",
        "set_montage_blend",
        {"asset_path": target, "blend_in_time": 0.25, "blend_out_time": 0.25, "enable_auto_blend_out": True},
    )
    saved = _save_package(target)
    after = _call("animation_query", "get_montage_info", {"asset_path": target})
    verified = _editor_python_json(
        "import unreal, json; "
        f"m=unreal.EditorAssetLibrary.load_asset({target!r}); "
        "print(json.dumps({'asset': m.get_path_name(), 'duration': m.get_play_length(), 'skeleton': m.get_skeleton().get_path_name() if m.get_skeleton() else '', 'slot_count': len(m.get_editor_property('slot_anim_tracks')), 'section_count': m.get_num_sections()}))"
    )
    if float(verified.get("duration", 0.0)) > float(after.get("duration", 0.0)):
        after["duration"] = verified["duration"]
    after["editor_verify"] = verified
    # Package save/indexing can briefly expose the newly-created montage with
    # a stale zero play length.  Re-read the same asset without mutating it;
    # a persistent zero remains a hard failure.
    for _ in range(20):
        if float(after.get("duration", 0.0)) > 0.0:
            break
        time.sleep(0.5)
        after = _call("animation_query", "get_montage_info", {"asset_path": target})
    if TARGET_SKELETON not in str(after.get("skeleton", "")):
        raise LivePromotionError(f"created montage skeleton is {after.get('skeleton')!r}")
    slot_count = int(after.get("slot_count", len(after.get("slots") or [])))
    section_count = int(after.get("section_count", len(after.get("sections") or [])))
    if slot_count < 1 or section_count < 1 or float(after.get("duration", 0.0)) <= 0.0:
        raise LivePromotionError("created montage has no slot, section, or animation duration")
    return {"consumer": "montage", "asset": target, "created": created, "blend": blend, "saved": saved, "after": after, "rollback_backup": str(backup)}


def promote(manifest_path: Path, ue_report_path: Path, plan_path: Path, *, apply: bool, output: Path, animation: str, consumer: str, montage_target: str = "", speed: float | None = None) -> int:
    manifest = read_json(manifest_path)
    ue_report = read_json(ue_report_path)
    plan = read_json(plan_path)
    report: dict[str, Any] = {
        "schema": "melodia.mual_live_promotion.v1",
        "apply": apply,
        "manifest": str(manifest_path),
        "ue_report": str(ue_report_path),
        "plan": str(plan_path),
        "animation": _asset_path(animation),
        "consumer": consumer,
        "ok": False,
        "promotion_allowed": False,
        "errors": [],
        "blockers": [],
    }
    try:
        errors = validate_v2(manifest)
        if errors:
            raise LivePromotionError("manifest v2 contract failed: " + "; ".join(errors))
        # The offline plan has already reduced the pilot's union of gates to
        # the requested consumer.  Require the core UE audit, but do not make
        # a montage depend on the unrelated locomotion speed gate.
        if not ue_report.get("ok") or not plan.get("promotion_allowed"):
            raise LivePromotionError("UE audit or offline promotion plan is not allowed")
        if plan.get("manifest_clip_id") != manifest.get("clip_id"):
            raise LivePromotionError("promotion plan manifest clip ID does not match the supplied manifest")
        if plan.get("consumer") != consumer:
            raise LivePromotionError("consumer does not match the promotion plan")
        if plan.get("animation") and _asset_path(str(plan.get("animation"))) != _asset_path(animation):
            raise LivePromotionError("promotion plan animation does not match the supplied animation")
        if consumer == "blendspace":
            measured = plan.get("measured_speed") if speed is None else speed
            if measured is None:
                raise LivePromotionError("measured BlendSpace speed is missing")
            if speed is not None and plan.get("measured_speed") is not None:
                try:
                    if abs(float(plan["measured_speed"]) - float(speed)) > 0.01:
                        raise LivePromotionError("CLI speed does not match the promotion plan")
                except (TypeError, ValueError) as exc:
                    raise LivePromotionError("promotion plan measured speed is malformed") from exc
            if apply:
                result = _promote_blendspace(
                    animation,
                    float(measured),
                    replace_existing_speed=bool(plan.get("replace_existing_speed")),
                )
            else:
                before, rows, normalized_animation, replacement_rows = _blendspace_preflight(
                    animation,
                    float(measured),
                    replace_existing_speed=bool(plan.get("replace_existing_speed")),
                )
                result = {
                    "dry_run": True,
                    "consumer": consumer,
                    "asset": BLENDSPACE,
                    "animation": normalized_animation,
                    "measured_speed": float(measured),
                    "live_before": before,
                    "live_sample_count": len(rows),
                    "replacement_rows": replacement_rows,
                }
        elif consumer == "montage":
            target = montage_target or str(plan.get("montage_target", ""))
            if montage_target and plan.get("montage_target") and _asset_path(montage_target) != _asset_path(str(plan.get("montage_target"))):
                raise LivePromotionError("montage target does not match the promotion plan")
            if apply:
                result = _promote_montage(animation, target)
            else:
                target, existing = _montage_preflight(target)
                result = {"dry_run": True, "consumer": consumer, "asset": target, "live_before": existing}
        else:
            raise LivePromotionError(f"unsupported consumer: {consumer}")
        report["result"] = result
        report["promotion_allowed"] = True
        report["ok"] = True
        if apply:
            manifest["status"] = "promoted"
            # Keep every successful consumer destination.  The singular
            # field remains the latest destination for older tooling, while
            # the list prevents a later BlendSpace promotion from erasing
            # the already-verified montage provenance.
            targets = list(manifest.get("promotion_targets") or [])
            prior_target = str(manifest.get("promotion_target") or "")
            if prior_target and prior_target not in targets:
                targets.append(prior_target)
            if result["asset"] not in targets:
                targets.append(result["asset"])
            manifest["promotion_targets"] = targets
            manifest["promotion_target"] = result["asset"]
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            report["manifest_updated"] = True
    except LivePromotionError as exc:
        report["errors"].append(str(exc))
        report["blockers"].append("live_promotion_not_verified")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(output), "errors": report["errors"], "blockers": report["blockers"]}, indent=2))
    return 0 if report["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("ue_report", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--animation", required=True)
    parser.add_argument("--consumer", choices=("blendspace", "montage"), required=True)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--montage-target", default="")
    parser.add_argument("--apply", action="store_true", help="Perform guarded UE mutation; default is read-only.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    return promote(args.manifest.resolve(), args.ue_report.resolve(), args.plan.resolve(), apply=args.apply, output=args.output.resolve(), animation=args.animation, consumer=args.consumer, montage_target=args.montage_target, speed=args.speed)


if __name__ == "__main__":
    raise SystemExit(main())
