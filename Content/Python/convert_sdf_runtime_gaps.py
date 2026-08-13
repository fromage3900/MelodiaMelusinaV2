"""Convert the freshly ported _PROJECT masters to Substrate Toon (Strategy C).

Reads Saved/Audit/sdf_runtime_port.json (list of ported stems), loads each
asset from /Game/EnvSandbox/Materials/Masters, and runs the established
Strategy C conversion (preserve graph, swap root -> SubstrateToonBSDF ->
MP_FRONT_MATERIAL). Non-material assets are reported and skipped.

Run in editor via Monolith editor_query run_python.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORT_REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sdf_runtime_port.json"
CONVERT_REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sdf_runtime_convert.json"
MASTERS_ROOT = "/Game/EnvSandbox/Materials/Masters"

sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))
import convert_masters_to_substrate_toon as conv  # noqa: E402


def rescan(folder: str) -> None:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        ar.scan_paths_synchronous([folder], force_rescan=True)
    except Exception as exc:
        unreal.log_warning(f"[SDFFold] rescan failed: {exc}")


def main() -> int:
    if not PORT_REPORT.is_file():
        print(f"Port report missing: {PORT_REPORT}")
        return 1
    report = json.loads(PORT_REPORT.read_text(encoding="utf-8"))
    stems = report.get("copied", [])
    if not stems:
        print("No ported stems to convert")
        return 0

    rescan("/Game/EnvSandbox/Materials/Masters")

    results: list[dict] = []
    for stem in sorted(stems):
        path = f"{MASTERS_ROOT}/{stem}"
        entry: dict = {"stem": stem, "path": path}
        try:
            asset = unreal.load_asset(path)
        except Exception as exc:
            entry["status"] = "load_error"
            entry["error"] = str(exc)
            results.append(entry)
            continue
        if asset is None:
            entry["status"] = "not_found"
            results.append(entry)
            continue
        cls = type(asset).__name__
        if cls == "MaterialInstanceConstant":
            entry["status"] = "skipped_instance"
            entry["class"] = cls
            results.append(entry)
            continue
        if cls != "Material":
            entry["status"] = "skipped_non_material"
            entry["class"] = cls
            results.append(entry)
            continue
        if conv._has_substrate_toon_bsdf(asset):
            entry["status"] = "skipped_already_toon"
            results.append(entry)
            continue
        try:
            r = conv.convert_master(path)
            entry.update({k: r.get(k) for k in ("status", "profile", "color_source", "roughness_source", "normal_source", "error")})
        except Exception as exc:
            entry["status"] = "convert_error"
            entry["error"] = str(exc)
        results.append(entry)
        unreal.log(f"[SDFFold] {stem}: {entry['status']}")

    CONVERT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    CONVERT_REPORT.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": len(results),
                "results": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Converted {len(results)} masters -> {CONVERT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
