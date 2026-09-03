"""CC0 Surfaces layer maps for M_Master_Toon_Landscape_HeightBlend.

Run audit (no editor):
  python Content/Python/portfolio_landscape_textures.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_cc0_textures.json"
CC0 = "/Game/Surfaces_CC0"
AUTHORED_ROOT = "/Game/Melodia/Art/Materials/Landscape"

# Canonical destination and naming contract for new terrain maps.  The authored
# maps are always preferred; CC0 is a temporary fallback, not art direction.
# Export BaseColor, Normal, ORM (R=AO/G=roughness/B=metallic), and Height.
AUTHORED_SURFACES = {
    "Rock": "ZenForest_Stone",
    "Grass": "ZenForest_MossGround",
    "Mud": "ZenForest_Soil",
    "Path": "ZenForest_CompactedPath",
}


def authored_path(surface: str, channel: str) -> str:
    """Return the stable asset path for one authored landscape PBR map."""
    stem = f"T_Land_{surface}_{channel}"
    return f"{AUTHORED_ROOT}/{surface}/Textures/{stem}.{stem}"


def authored_chain(layer: str, channel: str) -> list[str]:
    surface = AUTHORED_SURFACES[layer]
    aliases = {
        "Albedo": ("BC", "BaseColor"),
        "Normal": ("N", "Normal"),
        "ORM": ("ORM",),
        "Height": ("H", "Height"),
    }
    return [authored_path(surface, suffix) for suffix in aliases[channel]]


def cc0_path(surface: str, channel: str) -> str:
    """Build /Game/Surfaces_CC0 texture path for a CC0 surface pack."""
    stem = f"T_{surface}_2K-JPG_{channel}"
    rel = f"{CC0}/{surface}/{surface}_2K-JPG/Textures/{stem}"
    return f"{rel}.{stem}"


def cc0_chain(surface: str) -> dict[str, list[str]]:
    """Albedo / Normal / Height / ORM candidate chains for one CC0 surface."""
    import portfolio_texture_catalog as catalog

    color = cc0_path(surface, "Color")
    normal_gl = cc0_path(surface, "NormalGL")
    disp = cc0_path(surface, "Displacement")
    ao = cc0_path(surface, "AmbientOcclusion")
    rough = cc0_path(surface, "Roughness")
    return {
        "Albedo": [color, *catalog._chain(catalog.MARBLE["warm_stone"])],
        "Normal": [normal_gl, *catalog._normal_chain()],
        "Height": [disp, ao, rough, *catalog._chain(catalog.HEIGHT["perlin"])],
        # CC0 packs have no packed ORM (R=AO/G=rough/B=metal). Route the
        # packed-neutral ORM so the slot never falls back to a color pack.
        # Authored terrain maps (T_Land_*_ORM) supersede this once imported.
        "ORM": [catalog.NEUTRAL["orm"], catalog.NEUTRAL["roughness"], catalog.NEUTRAL["metallic"]],
    }


# Rock=cliff stone, Grass=ground, Mud=worn brick, Path=paving
LANDSCAPE_LAYER_TEXTURES: dict[str, dict[str, list[str]]] = {
    # Distinct fallback surfaces preserve material roles while authored maps are
    # being produced.  Never use one placeholder for both rock and ground.
    "Rock": cc0_chain("Marble012"),
    "Grass": cc0_chain("Ground037"),
    "Mud": cc0_chain("Bricks066"),  # worn brick — NOT Ground037 (grass)
    "Path": cc0_chain("PavingStones070"),
}

# Alternate CC0 fallbacks per layer (first existing wins in editor)
LANDSCAPE_LAYER_FALLBACKS: dict[str, dict[str, list[str]]] = {
    "Rock": cc0_chain("Bricks051"),
    "Grass": cc0_chain("Fabric045"),
    "Mud": cc0_chain("Tiles093"),  # distinct packed-earth read, never Ground037
    "Path": cc0_chain("Tiles074"),
}


def resolve_layer_textures(layer: str) -> dict[str, list[str]]:
    """Merge primary + fallback CC0 chains for a landscape layer."""
    primary = LANDSCAPE_LAYER_TEXTURES.get(layer, {})
    fallback = LANDSCAPE_LAYER_FALLBACKS.get(layer, {})
    merged: dict[str, list[str]] = {}
    for key in ("Albedo", "Normal", "ORM", "Height"):
        chain: list[str] = []
        for p in authored_chain(layer, key):
            if p not in chain:
                chain.append(p)
        for src in (primary, fallback):
            for p in src.get(key, []):
                if p not in chain:
                    chain.append(p)
        merged[key] = chain
    return merged


def scan_disk() -> dict:
    """List which CC0 paths exist on disk (for headless audit)."""
    content = PROJECT_ROOT / "Content"
    found: dict[str, dict[str, bool]] = {}
    for layer, tex in LANDSCAPE_LAYER_TEXTURES.items():
        found[layer] = {}
        for kind, paths in tex.items():
            ok = False
            for p in paths:
                rel = p.split(".", 1)[0].replace("/Game/", "").replace("/", "\\")
                if (content / f"{rel}.uasset").exists():
                    ok = True
                    break
            found[layer][kind] = ok
    return found


def scan_authored_disk() -> dict[str, dict[str, bool]]:
    """Report readiness of the production PBR library without requiring UE."""
    content = PROJECT_ROOT / "Content"
    found: dict[str, dict[str, bool]] = {}
    for layer in AUTHORED_SURFACES:
        found[layer] = {}
        for channel in ("Albedo", "Normal", "ORM", "Height"):
            found[layer][channel] = any(
                (content / f"{path.split('.', 1)[0].replace('/Game/', '')}.uasset").exists()
                for path in authored_chain(layer, channel)
            )
    return found


def main() -> int:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layers": list(LANDSCAPE_LAYER_TEXTURES.keys()),
        "textures": LANDSCAPE_LAYER_TEXTURES,
        "disk": scan_disk(),
        "authored_pbr_destination": AUTHORED_ROOT,
        "authored_pbr": scan_authored_disk(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"LANDSCAPE_CC0_OK layers={len(LANDSCAPE_LAYER_TEXTURES)} -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
