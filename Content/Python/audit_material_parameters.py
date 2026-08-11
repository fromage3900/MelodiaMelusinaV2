"""Audit scalar/vector/texture parameters across EnvSandbox material library.

Standalone (no editor):
  python Content/Python/audit_material_parameters.py

In editor (full graph param names):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_material_parameters.py"

Output: Saved/Audit/material_parameter_audit.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
CONTENT_ROOT = PROJECT_ROOT / "Content"
MATERIALS_ROOT = CONTENT_ROOT / "EnvSandbox" / "Materials"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "material_parameter_audit.json"

# Portfolio cohesion schema — canonical names per family
CANONICAL = {
    "SDF_Core": {
        "vectors": ("BaseTint", "AccentTint", "DeepTint"),
        "scalars": ("SDF_BandScale", "SDF_BandStrength", "BandScale", "ReliefDepth", "NoiseScale"),
        "groups": ("Toon", "SDF", "Palette", "Animation"),
    },
    "SDF_MCP": {
        "vectors": ("BaseTint", "AccentTint", "DeepTint", "GoldTint", "HighlightTint", "StoneTint", "LeadTint", "PulseTint"),
        "scalars": ("BandScale", "ReliefDepth", "NoiseScale", "FiligreeScale", "RimStrength", "AnimSpeed", "RadialScale", "TraceryMix", "WearAmount", "StoneTiling", "PulseSpeed", "GlowStrength"),
        "groups": ("Toon", "SDF", "Palette"),
    },
    "Impressionist": {
        "vectors": ("ColorRampLow", "ColorRampMid", "ColorRampHigh", "BrushDirection"),
        "scalars": (
            "BrushScale",
            "StrokeStrength",
            "ImpastoStrength",
            "ImpastoHeight",
            "NormalStrength",
            "Wetness",
            "DryRoughness",
            "WetRoughness",
            "InkIntensity",
            "TemporalStrength",
            "WindSpeed",
            "NoiseScale",
            "SmearStrength",
        ),
        "groups": ("Palette", "Brush", "Impasto", "Surface", "Animation"),
    },
}

PLACEHOLDER_RE = re.compile(r"^(MCP_\d+|Param\d*|NewParam|VectorParam|ScalarParam)$", re.I)
# UE stores many strings in uassets; filter plausible parameter names
NAME_RE = re.compile(rb"[\x20-\x7e]{2,64}\x00")

KNOWN_PREFIXES = ("M_", "MI_", "MF_", "TP_")


def asset_game_path(uasset: Path) -> str:
    rel = uasset.relative_to(CONTENT_ROOT).with_suffix("")
    return "/Game/" + rel.as_posix()


def classify_family(game_path: str) -> str:
    if "/Impressionist/" in game_path:
        return "Impressionist"
    if "/Masters/M_SDF_" in game_path or "/Masters/M_Toon_SDF" in game_path:
        if any(x in game_path for x in ("ReliefPanel", "FiligreeRim", "GothicTracery", "HybridStone", "ParallaxPulse")):
            return "SDF_MCP"
        return "SDF_Core"
    if "/SDF/Instances/MI_SDF_" in game_path:
        return "SDF_MCP"
    if "/SDF/Instances/MI_Toon_SDF" in game_path:
        return "SDF_Core"
    return "Other"


def extract_strings_from_uasset(data: bytes) -> set[str]:
    found: set[str] = set()
    for m in NAME_RE.finditer(data):
        s = m.group(0)[:-1].decode("ascii", "ignore")
        if PLACEHOLDER_RE.match(s):
            found.add(s)
        elif re.match(r"^[A-Z][A-Za-z0-9_]{2,48}$", s) and not s.startswith("Material"):
            if any(k in s for k in ("Tint", "Scale", "Strength", "Color", "Roughness", "Height", "Speed", "Amount", "Mix", "Wetness", "Brush", "Band", "Relief", "Noise", "Gold", "Stone", "Pulse", "Rim", "Anim", "Wear", "Glow", "Tracery", "Filigree", "Impasto", "Wind", "Temporal", "Stroke")):
                found.add(s)
    return found


def scan_disk() -> list[dict]:
    rows: list[dict] = []
    if not MATERIALS_ROOT.exists():
        return rows

    for p in MATERIALS_ROOT.rglob("*.uasset"):
        if not any(p.stem.startswith(pref) for pref in KNOWN_PREFIXES):
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        game_path = asset_game_path(p)
        family = classify_family(game_path)
        params = sorted(extract_strings_from_uasset(data))
        placeholders = [x for x in params if PLACEHOLDER_RE.match(x)]
        canonical = CANONICAL.get(family, {})
        expected = set(canonical.get("vectors", ())) | set(canonical.get("scalars", ()))
        missing = sorted(expected - set(params)) if expected else []
        unexpected = sorted(set(params) - expected - set(placeholders)) if expected else params

        rows.append(
            {
                "path": game_path,
                "stem": p.stem,
                "family": family,
                "params_detected": params,
                "placeholders": placeholders,
                "missing_canonical": missing,
                "non_canonical": unexpected,
            }
        )
    return rows


def scan_editor() -> list[dict]:
    import unreal  # type: ignore
    import material_lib as lib

    rows: list[dict] = []
    root = "/Game/EnvSandbox/Materials"
    paths = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
    for game_path in paths:
        stem = lib.list_path_stem(game_path)
        if not any(stem.startswith(p) for p in KNOWN_PREFIXES):
            continue
        ad = unreal.EditorAssetLibrary.find_asset_data(game_path)
        cls = str(getattr(ad, "asset_class", "") or "")
        if cls not in ("Material", "MaterialInstanceConstant"):
            if lib.asset_class_name(ad) not in ("Material", "MaterialInstanceConstant"):
                continue

        asset = unreal.load_asset(game_path)
        if not asset:
            asset = lib.load_asset_from_list_path(game_path)
        if not asset:
            continue
        family = classify_family(game_path)
        params: list[dict] = []

        if isinstance(asset, unreal.Material):
            for expr in list(unreal.MaterialEditingLibrary.get_material_expressions(asset)):
                if not expr:
                    continue
                tname = type(expr).__name__
                if "ScalarParameter" in tname:
                    params.append(
                        {
                            "name": expr.get_editor_property("parameter_name"),
                            "kind": "scalar",
                            "group": expr.get_editor_property("group") or "",
                            "default": expr.get_editor_property("default_value"),
                        }
                    )
                elif "VectorParameter" in tname:
                    params.append(
                        {
                            "name": expr.get_editor_property("parameter_name"),
                            "kind": "vector",
                            "group": expr.get_editor_property("group") or "",
                        }
                    )
                elif "TextureSampleParameter" in tname or "TextureObjectParameter" in tname:
                    params.append(
                        {
                            "name": expr.get_editor_property("parameter_name"),
                            "kind": "texture",
                            "group": expr.get_editor_property("group") or "",
                        }
                    )
        elif isinstance(asset, unreal.MaterialInstanceConstant):
            for name in asset.get_editor_property("scalar_parameter_values") or []:
                params.append({"name": str(name), "kind": "scalar_instance", "group": ""})
            for name in asset.get_editor_property("vector_parameter_values") or []:
                params.append({"name": str(name), "kind": "vector_instance", "group": ""})

        names = [p["name"] for p in params]
        placeholders = [n for n in names if PLACEHOLDER_RE.match(n)]
        canonical = CANONICAL.get(family, {})
        expected = set(canonical.get("vectors", ())) | set(canonical.get("scalars", ()))
        missing = sorted(expected - set(names)) if expected else []
        non_canonical = sorted(set(names) - expected) if expected else names

        rows.append(
            {
                "path": game_path,
                "stem": stem,
                "family": family,
                "asset_class": cls,
                "params": params,
                "placeholders": placeholders,
                "missing_canonical": missing,
                "non_canonical": non_canonical,
            }
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    by_family: dict[str, list] = defaultdict(list)
    all_placeholders: list[dict] = []
    all_missing: list[dict] = []

    for r in rows:
        by_family[r["family"]].append(r["stem"])
        for ph in r.get("placeholders", []):
            all_placeholders.append({"path": r["path"], "name": ph})
        for miss in r.get("missing_canonical", []):
            all_missing.append({"path": r["path"], "missing": miss})

    return {
        "material_count": len(rows),
        "by_family": {k: len(v) for k, v in by_family.items()},
        "placeholder_count": len(all_placeholders),
        "placeholders": all_placeholders[:50],
        "missing_canonical_count": len(all_missing),
        "missing_canonical": all_missing[:50],
    }


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue() -> int:
    rows = scan_editor()
    summary = summarize(rows)
    report = {
        "mode": "editor",
        "summary": summary,
        "materials": rows,
        "canonical_schema": CANONICAL,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("=" * 60)
    print("Material Parameter Audit")
    print("=" * 60)
    print(f"Mode: editor")
    print(f"Materials scanned: {summary['material_count']}")
    print(f"By family: {summary['by_family']}")
    print(f"Placeholder params: {summary['placeholder_count']}")
    print(f"Missing canonical: {summary['missing_canonical_count']}")
    print(f"Report: {REPORT_PATH}")
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()

    if "--disk" not in sys.argv and UE_CMD.exists():
        log = PROJECT_ROOT / "Saved" / "Logs" / "material_parameter_audit.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_material_parameters.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            f"-log={log}",
        ]
        print(f"Material parameter audit -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    rows = scan_disk()
    summary = summarize(rows)

    report = {
        "mode": "disk",
        "summary": summary,
        "materials": rows,
        "canonical_schema": CANONICAL,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 60)
    print("Material Parameter Audit")
    print("=" * 60)
    print(f"Mode: {report['mode']}")
    print(f"Materials scanned: {summary['material_count']}")
    print(f"By family: {summary['by_family']}")
    print(f"Placeholder params: {summary['placeholder_count']}")
    print(f"Missing canonical: {summary['missing_canonical_count']}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
