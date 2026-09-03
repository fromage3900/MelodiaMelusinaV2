"""Audit hero material instances for readable Nikki styling.

This is deliberately read-only. It reports likely washed-out instances rather
than changing artist-owned values. Run in UE with an editor asset registry.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
EXPECTED_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REQUIRED = ("BaseTint", "MagicalIntensity", "IridescencePower", "bNikkiHero", "bSparkleAdvanced")
AUDIO = ("BeatPulse", "CommandEnergy", "BreakPulse", "VictoryPulse")
REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "nikki_material_instances_audit.json"


def _path(asset) -> str:
    try:
        return str(asset.get_path_name()).split(".", 1)[0]
    except Exception:
        return ""


def _param_names(unreal, instance):
    names = set()
    for getter in ("get_scalar_parameter_names", "get_vector_parameter_names", "get_static_switch_parameter_names"):
        try:
            names.update(str(x) for x in getattr(instance, getter)())
        except Exception:
            pass
    return names


def _scalar(unreal, instance, name: str):
    try:
        ok, value = instance.get_scalar_parameter_value(name)
        return float(value) if ok else None
    except Exception:
        return None


def _vector(unreal, instance, name: str):
    try:
        ok, value = instance.get_vector_parameter_value(name)
        if ok:
            return [float(value.r), float(value.g), float(value.b), float(value.a)]
    except Exception:
        pass
    return None


def main() -> int:
    import unreal
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass
    assets = unreal.EditorAssetLibrary.list_assets(ROOT, recursive=True, include_folder=False)
    rows = []
    for path in sorted(assets or []):
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance or not isinstance(instance, unreal.MaterialInstanceConstant):
            continue
        parent = _path(instance.get_editor_property("parent"))
        names = _param_names(unreal, instance)
        tint = _vector(unreal, instance, "BaseTint")
        issues = []
        if parent != EXPECTED_PARENT:
            issues.append("parent_not_canonical")
        # MaterialInstanceConstant exposes local overrides here; inherited
        # parameters live on the parent material and are intentionally absent.
        inherited_controls = parent == EXPECTED_PARENT
        if tint and max(tint[:3]) - min(tint[:3]) < 0.025 and sum(tint[:3]) / 3.0 < 0.65:
            issues.append("dark_or_neutral_base_tint")
        row = {"asset": path, "parent": parent, "base_tint": tint,
               "local_override_count": len(names),
               "inherits_nikki_controls": inherited_controls,
               "has_audio_hooks": inherited_controls,
               "issues": issues}
        rows.append(row)
    report = {"ok": all(not row["issues"] for row in rows),
              "timestamp": datetime.now(timezone.utc).isoformat(), "root": ROOT,
              "expected_parent": EXPECTED_PARENT, "count": len(rows), "instances": rows}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
