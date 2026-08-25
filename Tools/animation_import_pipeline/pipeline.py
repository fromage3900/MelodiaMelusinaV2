"""CLI for the Melusina Universal Animation Library (MUAL-2).

Offline commands are authoritative for classification and preflight.  UE
commands remain explicit and fail closed when the editor/MCP bridge is not
available, so a foreign clip can never be promoted by accidentally invoking a
legacy direct retargeter.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
PROJECT_ROOT = HERE.parent.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from manifest_v2 import load_as_v2, read_json, to_v2_manifest, validate_v2  # noqa: E402
from registry import catalog, write_registry  # noqa: E402
from promotion import build_plan  # noqa: E402


def _sidecar(path: Path, explicit: Path | None) -> Path | None:
    if explicit:
        return explicit
    for candidate in (path.with_suffix(".manifest.json"), path.with_suffix(".json")):
        if candidate.is_file():
            return candidate
    return None


def _unit_guard(path: Path, sidecar: dict[str, Any] | None) -> dict[str, Any]:
    try:
        from melusina_anim_unit_guard import preflight_fbx
        result = preflight_fbx(path, require_sidecar=False, lane_a=False)
        if sidecar and sidecar.get("status") == "canonical":
            result["errors"].extend(
                error for error in ("canonical source-rig FBX must use centimetre header" if result["header"].get("header_class") != "centimeters" else "",) if error
            )
            result["errors"].extend(
                error for error in ("canonical source-rig FBX cannot contain dotted ARP names" if result["name_style"].get("name_style") in {"dotted", "mixed"} else "",) if error
            )
            result["ok"] = not result["errors"]
        return result
    except Exception as exc:  # pragma: no cover - optional guard import fallback
        return {"ok": False, "errors": [f"unit guard unavailable: {exc}"], "warnings": []}


def cmd_catalog(args: argparse.Namespace) -> int:
    root = args.project_root.resolve()
    result = catalog(root)
    if args.write:
        output = write_registry(root, args.output.resolve() if args.output else None)
        print(json.dumps({"output": str(output), "counts": result["counts"]}, indent=2))
    else:
        print(json.dumps(result, indent=2))
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    fbx = args.fbx.resolve()
    sidecar = _sidecar(fbx, args.manifest.resolve() if args.manifest else None)
    if sidecar is None:
        print(json.dumps({"ok": False, "fbx": str(fbx), "errors": ["missing sidecar"]}, indent=2))
        return 1
    try:
        manifest, schema_errors, was_legacy = load_as_v2(sidecar, fbx)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "fbx": str(fbx), "errors": [str(exc)]}, indent=2))
        return 1
    errors = list(schema_errors)
    if was_legacy:
        errors.append("legacy sidecar is catalogued only; write a v2 sidecar before import")
    errors.extend(validate_v2(manifest) if not was_legacy else [])
    if not was_legacy and manifest.get("status") != "canonical":
        errors.append(
            f"manifest status {manifest.get('status')!r} is not importable; only canonical source-rig clips may enter the UE chain"
        )
    guard = _unit_guard(fbx, manifest)
    errors.extend(guard.get("errors", []))
    result = {"ok": not errors, "fbx": str(fbx), "manifest": manifest, "unit_guard": guard, "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


def cmd_normalize(args: argparse.Namespace) -> int:
    raw = read_json(args.input.resolve())
    manifest = to_v2_manifest(raw, args.fbx.resolve() if args.fbx else args.input.with_suffix(".fbx"))
    manifest["status"] = args.status or manifest["status"]
    if manifest["status"] == "canonical" and not args.approve_canonical:
        print(json.dumps({"ok": False, "errors": ["--approve-canonical is required to write canonical status"]}, indent=2))
        return 1
    output = args.output.resolve() if args.output else args.input.with_name(args.input.stem + ".v2.manifest.json")
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "clip_id": manifest["clip_id"], "status": manifest["status"]}, indent=2))
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    fbx = args.fbx.resolve()
    sidecar = _sidecar(fbx, args.manifest.resolve() if args.manifest else None)
    if sidecar is None:
        print(json.dumps({"ok": False, "errors": ["missing sidecar"]}, indent=2))
        return 1
    manifest, _, was_legacy = load_as_v2(sidecar, fbx)
    source_type = manifest.get("source_type")
    if source_type in {"quaternius", "foreign"} or was_legacy or manifest.get("status") == "manual_required":
        gate = "manual_cascadeur_retarget_contact_cleanup_polish"
        status = "manual_required"
    elif manifest.get("status") == "canonical":
        gate = "canonical_source_rig_export_verified"
        status = "canonical"
    else:
        gate = "blocked_until_canonical_source_export"
        status = "blocked"
    handoff = {
        "handoff_schema": "MUAL-CASCADEUR-1",
        "input_fbx": str(fbx),
        "manifest": manifest,
        "reference_fbx": str((PROJECT_ROOT / "Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx").resolve()),
        "canonical_source_rig": "SK_Source_Melusina",
        "manual_gate": gate,
        "status": status,
        "export_requirements": [
            "animation-only FBX",
            "one clip per file",
            "30 FPS",
            "centimetres",
            "underscore-normalized bone names",
            "sidecar v2 written beside the export",
        ],
        "ue_action": "import onto SK_Source_Melusina, then retarget with RTG_Source_to_Melusina",
    }
    output = args.output.resolve() if args.output else fbx.with_suffix(".cascadeur.handoff.json")
    output.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "status": status, "manual_gate": gate}, indent=2))
    return 0


def cmd_ue(args: argparse.Namespace) -> int:
    if args.status == "promote" and not args.allow_editor:
        print(json.dumps({"ok": False, "errors": ["UE promotion requires --allow-editor and a validated v2 manifest", "no live editor mutation was attempted"]}, indent=2))
        return 2
    print(json.dumps({"ok": False, "errors": ["UE execution is delegated to import_chain.py; invoke it explicitly after offline preflight"], "next": "python Tools/animation_import_pipeline/import_chain.py <fbx> --manifest <v2 manifest>"}, indent=2))
    return 2


def cmd_promotion_plan(args: argparse.Namespace) -> int:
    from promotion import main as promotion_main
    forwarded = [str(args.manifest), str(args.ue_report), "--animation", args.animation, "--consumer", args.consumer]
    if args.speed is not None:
        forwarded.extend(["--speed", str(args.speed)])
    if args.replace_existing_speed:
        forwarded.append("--replace-existing-speed")
    if args.montage_target:
        forwarded.extend(["--montage-target", args.montage_target])
    if args.output:
        forwarded.extend(["--output", str(args.output)])
    return promotion_main(forwarded)


def cmd_live_promotion(args: argparse.Namespace) -> int:
    from live_promotion import main as live_promotion_main
    forwarded = [
        str(args.manifest), str(args.ue_report), str(args.plan),
        "--animation", args.animation, "--consumer", args.consumer,
    ]
    if args.speed is not None:
        forwarded.extend(["--speed", str(args.speed)])
    if args.montage_target:
        forwarded.extend(["--montage-target", args.montage_target])
    if args.apply:
        forwarded.append("--apply")
    if args.output:
        forwarded.extend(["--output", str(args.output)])
    return live_promotion_main(forwarded)


def cmd_pie_smoke(args: argparse.Namespace) -> int:
    from pie_smoke import main as pie_smoke_main
    forwarded = [args.clip_name, "--map", args.map_path, "--expected-anim-class", args.expected_anim_class, "--duration", str(args.duration), "--timeout", str(args.timeout)]
    if args.output:
        forwarded.extend(["--output", str(args.output)])
    return pie_smoke_main(forwarded)


def cmd_acceptance(args: argparse.Namespace) -> int:
    from acceptance import main as acceptance_main
    forwarded = []
    if args.output:
        forwarded.extend(["--output", str(args.output)])
    return acceptance_main(forwarded)


def cmd_contact_audit(args: argparse.Namespace) -> int:
    from foot_contact_audit import main as contact_audit_main
    forwarded = [str(args.manifest), "--animation", args.animation, "--method", args.method]
    if args.consumer:
        forwarded.extend(["--consumer", args.consumer])
    if args.reuse_static_report:
        forwarded.extend(["--reuse-static-report", str(args.reuse_static_report)])
    if args.apply:
        forwarded.append("--apply")
    if args.output:
        forwarded.extend(["--output", str(args.output)])
    return contact_audit_main(forwarded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    catalog_parser = sub.add_parser("catalog")
    catalog_parser.add_argument("--write", action="store_true")
    catalog_parser.add_argument("--output", type=Path)
    catalog_parser.set_defaults(func=cmd_catalog)

    preflight_parser = sub.add_parser("preflight")
    preflight_parser.add_argument("fbx", type=Path)
    preflight_parser.add_argument("--manifest", type=Path)
    preflight_parser.set_defaults(func=cmd_preflight)

    normalize_parser = sub.add_parser("normalize-manifest")
    normalize_parser.add_argument("input", type=Path)
    normalize_parser.add_argument("--fbx", type=Path)
    normalize_parser.add_argument("--output", type=Path)
    normalize_parser.add_argument("--status", choices=["canonical", "manual_required", "blocked", "legacy", "promoted"])
    normalize_parser.add_argument("--approve-canonical", action="store_true")
    normalize_parser.set_defaults(func=cmd_normalize)

    handoff_parser = sub.add_parser("cascadeur-handoff")
    handoff_parser.add_argument("fbx", type=Path)
    handoff_parser.add_argument("--manifest", type=Path)
    handoff_parser.add_argument("--output", type=Path)
    handoff_parser.set_defaults(func=cmd_handoff)

    ue_parser = sub.add_parser("ue")
    ue_parser.add_argument("status", choices=["import", "promote"])
    ue_parser.add_argument("--allow-editor", action="store_true")
    ue_parser.set_defaults(func=cmd_ue)
    promotion_parser = sub.add_parser("promotion-plan")
    promotion_parser.add_argument("manifest", type=Path)
    promotion_parser.add_argument("ue_report", type=Path)
    promotion_parser.add_argument("--animation", required=True)
    promotion_parser.add_argument("--consumer", choices=("blendspace", "montage"), required=True)
    promotion_parser.add_argument("--speed", type=float)
    promotion_parser.add_argument("--replace-existing-speed", action="store_true")
    promotion_parser.add_argument("--montage-target", default="")
    promotion_parser.add_argument("--output", type=Path)
    promotion_parser.set_defaults(func=cmd_promotion_plan)
    live_promotion_parser = sub.add_parser("live-promotion")
    live_promotion_parser.add_argument("manifest", type=Path)
    live_promotion_parser.add_argument("ue_report", type=Path)
    live_promotion_parser.add_argument("plan", type=Path)
    live_promotion_parser.add_argument("--animation", required=True)
    live_promotion_parser.add_argument("--consumer", choices=("blendspace", "montage"), required=True)
    live_promotion_parser.add_argument("--speed", type=float)
    live_promotion_parser.add_argument("--montage-target", default="")
    live_promotion_parser.add_argument("--apply", action="store_true")
    live_promotion_parser.add_argument("--output", type=Path)
    live_promotion_parser.set_defaults(func=cmd_live_promotion)
    pie_parser = sub.add_parser("pie-smoke")
    pie_parser.add_argument("clip_name")
    pie_parser.add_argument("--map", dest="map_path", default="/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap")
    pie_parser.add_argument("--expected-anim-class", default="/Game/Melodia/Characters/Melusina/ABP_Melusina_Current")
    pie_parser.add_argument("--duration", type=float, default=5.0)
    pie_parser.add_argument("--timeout", type=float, default=180.0)
    pie_parser.add_argument("--output", type=Path)
    pie_parser.set_defaults(func=cmd_pie_smoke)
    acceptance_parser = sub.add_parser("acceptance")
    acceptance_parser.add_argument("--output", type=Path)
    acceptance_parser.set_defaults(func=cmd_acceptance)
    contact_parser = sub.add_parser("contact-audit")
    contact_parser.add_argument("manifest", type=Path)
    contact_parser.add_argument("--animation", required=True)
    contact_parser.add_argument("--method", choices=("auto", "from_bones", "existing", "notifies", "contact", "phase", "footspeed"), default="auto")
    contact_parser.add_argument("--consumer", choices=("blendspace", "montage"))
    contact_parser.add_argument("--reuse-static-report", type=Path)
    contact_parser.add_argument("--apply", action="store_true")
    contact_parser.add_argument("--output", type=Path)
    contact_parser.set_defaults(func=cmd_contact_audit)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
