"""ZenTrim 4K trimsheet texture sets — Layer A/B maps for M_Master_Toon_Universal instances.

Textures live under /Game/Textures/ZenTrim_<Variant>_<Channel>.
Layer A = clean base (default Base4K). Layer B = environment variation overlay.
The master lerps all maps via LayerBlend — instances only assign textures + scalars.

Headless audit:
  python Content/Python/zen_trim_textures.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zen_trim_textures.json"
TEX = "/Game/Textures"

# Variant folder stems (match uasset names on disk)
ZEN_TRIM_VARIANTS = (
    "Base4K",
    "ColourShift",
    "CrackedToHell",
    "FlowersLIttleBit",
    "FlowersLOTS",
    "FlowersMid",
    "Wet",
)

# Channel suffix on each uasset
CHANNELS = (
    "Alpha",
    "BaseColor",
    "Displacement",
    "Emission",
    "Metallic",
    "Normal",
    "Roughness",
)


def trim_path(variant: str, channel: str) -> str:
    stem = f"ZenTrim_{variant}_{channel}"
    return f"{TEX}/{stem}.{stem}"


def variant_maps(variant: str) -> dict[str, str]:
    """Map master MI texture param names → single ZenTrim asset path."""
    return {
        "Albedo": trim_path(variant, "BaseColor"),
        "NormalMap": trim_path(variant, "Normal"),
        "HeightMap": trim_path(variant, "Displacement"),
        "ORM": trim_path(variant, "Roughness"),
        "RoughnessMap": trim_path(variant, "Roughness"),
        "MetallicMap": trim_path(variant, "Metallic"),
        "DetailNormal": trim_path(variant, "Alpha"),
        "MotifMask": trim_path(variant, "Alpha"),
    }


def layer_b_maps(variant: str) -> dict[str, str]:
    """Layer B param names on M_Master_Toon_Universal."""
    base = variant_maps(variant)
    return {
        "LayerB_Albedo": base["Albedo"],
        "LayerB_NormalMap": base["NormalMap"],
        "LayerB_HeightMap": base["HeightMap"],
        "LayerB_ORM": base["ORM"],
    }


def apply_zen_trim_layers(instance, layer_a: str, layer_b: str) -> dict[str, str]:
    """Wire Layer A + Layer B ZenTrim sets on an existing material instance."""
    import material_lib as lib

    wired: dict[str, str] = {}
    for pname, path in variant_maps(layer_a).items():
        if pname in ("RoughnessMap", "MetallicMap", "MotifMask"):
            continue
        resolved = lib.set_instance_texture(instance, pname, [path])
        if resolved:
            wired[pname] = resolved
    for pname, path in layer_b_maps(layer_b).items():
        resolved = lib.set_instance_texture(instance, pname, [path])
        if resolved:
            wired[pname] = resolved
    return wired


def scan_disk() -> dict[str, dict[str, bool]]:
    content = PROJECT_ROOT / "Content" / "Textures"
    out: dict[str, dict[str, bool]] = {}
    for variant in ZEN_TRIM_VARIANTS:
        out[variant] = {}
        for ch in CHANNELS:
            stem = f"ZenTrim_{variant}_{ch}"
            out[variant][ch] = (content / f"{stem}.uasset").exists()
    return out


def main() -> int:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "variants": list(ZEN_TRIM_VARIANTS),
        "default_layer_a": "Base4K",
        "disk": scan_disk(),
        "sample_base": variant_maps("Base4K"),
        "sample_cracked_b": layer_b_maps("CrackedToHell"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"ZEN_TRIM_CATALOG variants={len(ZEN_TRIM_VARIANTS)} -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
