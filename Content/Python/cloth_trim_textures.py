"""ClothTrim 4K trimsheet texture sets — Layer A/B maps for fabric trimsheet instances.

Textures: /Game/Textures/ClothTrim_<Variant>_<Channel>
Variants are auto-discovered from Content/Textures/ClothTrim_*_BaseColor.uasset.

Headless catalog:
  python Content/Python/cloth_trim_textures.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "cloth_trim_textures.json"
TEX = "/Game/Textures"

CHANNELS = (
    "Alpha",
    "BaseColor",
    "Displacement",
    "Emission",
    "Metallic",
    "Normal",
    "Roughness",
)

_STEM_RE = re.compile(r"^(?:T_)?ClothTrim_(.+)_(Alpha|BaseColor|BC|Displacement|Emission|Metallic|Normal|N|Roughness|ORM|H)$")


def discover_variants() -> tuple[str, ...]:
    """Return variant names found on disk (sorted)."""
    content = PROJECT_ROOT / "Content" / "Textures"
    if not content.is_dir():
        return ()
    found: set[str] = set()
    for path in list(content.glob("*ClothTrim_*.*")):
        if path.suffix.lower() in (".uasset", ".png"):
            m = _STEM_RE.match(path.stem)
            if m:
                found.add(m.group(1))
    return tuple(sorted(found))


def trim_path(variant: str, channel: str) -> str:
    stem = f"T_ClothTrim_{variant}_{channel}"
    return f"{TEX}/{stem}.{stem}"


def variant_maps(variant: str) -> dict[str, str]:
    return {
        "Albedo": trim_path(variant, "BC"),
        "NormalMap": trim_path(variant, "N"),
        "HeightMap": trim_path(variant, "H"),
        "ORM": trim_path(variant, "ORM"),
        "RoughnessMap": trim_path(variant, "Roughness"),
        "MetallicMap": trim_path(variant, "Metallic"),
        "DetailNormal": trim_path(variant, "Alpha"),
        "MotifMask": trim_path(variant, "Alpha"),
    }



def layer_b_maps(variant: str) -> dict[str, str]:
    base = variant_maps(variant)
    return {
        "LayerB_Albedo": base["Albedo"],
        "LayerB_NormalMap": base["NormalMap"],
        "LayerB_HeightMap": base["HeightMap"],
        "LayerB_ORM": base["ORM"],
    }


def apply_cloth_trim_layers(instance, layer_a: str, layer_b: str) -> dict[str, str]:
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
    for variant in discover_variants():
        out[variant] = {}
        for ch in ("BC", "BaseColor", "Normal", "N", "ORM", "Roughness", "Metallic", "H", "Displacement", "Alpha"):
            stem1 = f"ClothTrim_{variant}_{ch}"
            stem2 = f"T_ClothTrim_{variant}_{ch}"
            exists = (
                (content / f"{stem1}.uasset").exists()
                or (content / f"{stem1}.png").exists()
                or (content / f"{stem2}.uasset").exists()
                or (content / f"{stem2}.png").exists()
            )
            out[variant][ch] = exists
    return out



def overlay_variants() -> tuple[str, ...]:
    """Variants suitable as Layer B (everything except Base4K when present)."""
    variants = discover_variants()
    if "Base4K" in variants:
        return tuple(v for v in variants if v != "Base4K")
    return variants


def main() -> int:
    variants = discover_variants()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "variants": list(variants),
        "overlay_variants": list(overlay_variants()),
        "default_layer_a": "Base4K" if "Base4K" in variants else (variants[0] if variants else None),
        "disk": scan_disk(),
        "naming": "ClothTrim_<Variant>_<Channel>.uasset under Content/Textures/",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"CLOTH_TRIM_CATALOG variants={len(variants)} -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
