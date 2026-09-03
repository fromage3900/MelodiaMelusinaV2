"""NPC Palette Mapper — translates Melodia design tokens into 3 archetype MPC parameter sets.

Each archetype maps design system primitives to MToon material parameters for VRM4U characters.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────────────
# Design Token Reference (from tokens.json)
# ──────────────────────────────────────────────────────────────────────
# primitives.sakura      → Sakura Dreamer (floral, petal, warm pink)
# primitives.astral + iris → Cosmic Weaver (stellar, violet-blue, iridescent)
# primitives.astral + gold + portfolio.motif.grotto → Mirage Dancer (twilight, gradient, gold accent)
# ──────────────────────────────────────────────────────────────────────


@dataclass
class MToonParams:
    """MToon material parameter overrides for a single NPC."""
    # Base color / shading
    base_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    shade_color: tuple[float, float, float, float] = (0.2, 0.15, 0.25, 1.0)
    shade_shift: float = 0.0
    shade_toony: float = 0.5
    lighting_influence: float = 0.8

    # MatCap / Rim
    matcap_blend: float = 0.0
    matcap_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    rim_color: tuple[float, float, float, float] = (1.0, 0.8, 0.6, 1.0)
    rim_fresnel: float = 0.5
    rim_lift: float = 0.0

    # Outline
    outline_width: float = 0.03
    outline_color: tuple[float, float, float, float] = (0.1, 0.05, 0.15, 1.0)
    outline_lighting_mix: float = 0.0

    # Emission / Glow
    emission_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    emission_strength: float = 0.0

    # Subsurface (for skin/fabric translucency)
    subsurface_color: tuple[float, float, float, float] = (1.0, 0.9, 0.95, 1.0)
    subsurface_amount: float = 0.0

    # NPC-specific MPC parameters (exposed to MPC_SakuraDream extension)
    npc_dream_intensity: float = 1.0
    npc_color_shift: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    npc_wind_strength: float = 1.0
    npc_glow_intensity: float = 0.0

    def to_mpc_dict(self, prefix: str = "") -> dict[str, Any]:
        """Convert to MPC parameter dictionary with prefix."""
        result = {}
        for k, v in asdict(self).items():
            if isinstance(v, tuple):
                result[f"{prefix}{k}_r"] = v[0]
                result[f"{prefix}{k}_g"] = v[1]
                result[f"{prefix}{k}_b"] = v[2]
                result[f"{prefix}{k}_a"] = v[3]
            else:
                result[f"{prefix}{k}"] = v
        return result


@dataclass
class ArchetypePalette:
    """Complete palette definition for an NPC archetype."""
    name: str
    display_name: str
    description: str
    count: int
    battle_role: str

    # Primary color triad (base, shade, accent)
    base_hex: str
    shade_hex: str
    accent_hex: str

    # MToon parameter preset
    mtoon: MToonParams = field(default_factory=MToonParams)

    # Outfit piece definitions (for cloth setup)
    outfit_pieces: list[str] = field(default_factory=list)

    # Element affinity (for battle integration)
    element: str = "Forte"

    # BPM preference
    bpm: float = 120.0


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    """Convert hex color to 0-1 RGBA tuple."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


def create_archetype_palettes() -> dict[str, ArchetypePalette]:
    """Create the three archetype palettes mapped from design tokens."""

    # ─── SAKURA DREAMER ───
    sakura = ArchetypePalette(
        name="SakuraDreamer",
        display_name="Sakura Dreamer",
        description="Floral support archetype — petal motifs, flowing sleeves, cherry blossom palette. Healer/buffer in battle.",
        count=4,
        battle_role="Support",
        base_hex="#F5E8EA",      # sakura.100 - petal white
        shade_hex="#E7C9CE",     # sakura.300 - dusty sakura
        accent_hex="#D6A9B0",    # sakura.500 - sakura pink
        element="Radiant",
        bpm=128.0,
        outfit_pieces=["kimono_sleeve_top", "hakama_skirt", "petal_hair_ribbon", "falling_petal_accessory"],
    )
    sakura.mtoon = MToonParams(
        base_color=hex_to_rgba(sakura.base_hex),
        shade_color=hex_to_rgba(sakura.shade_hex),
        shade_shift=0.05,
        shade_toony=0.6,
        lighting_influence=0.7,
        matcap_blend=0.15,
        matcap_color=hex_to_rgba("#FFE4F0"),  # soft petal matcap
        rim_color=hex_to_rgba("#FFB3C6", 0.8),
        rim_fresnel=0.3,
        rim_lift=0.1,
        outline_width=0.025,
        outline_color=hex_to_rgba("#8B5A6B"),
        subsurface_color=hex_to_rgba("#FFDDE6"),
        subsurface_amount=0.15,
        npc_dream_intensity=1.2,
        npc_color_shift=hex_to_rgba("#D6A9B0", 0.3),
        npc_wind_strength=0.8,
        npc_glow_intensity=0.2,
    )

    # ─── COSMIC WEAVER ───
    cosmic = ArchetypePalette(
        name="CosmicWeaver",
        display_name="Cosmic Weaver",
        description="Stellar controller archetype — star-field fabric, constellation jewelry, iridescent violet-blue. Buff/debuffer in battle.",
        count=3,
        battle_role="Controller",
        base_hex="#141A30",      # astral.900 - astral night
        shade_hex="#26365E",     # astral.700 - deep astral
        accent_hex="#6E5AA6",    # iris.500 - amethyst/iris
        element="Arcane",
        bpm=144.0,
        outfit_pieces=["stellar_cape", "constellation_corset", "orbital_hair_ornaments", "cosmic_gloves"],
    )
    cosmic.mtoon = MToonParams(
        base_color=hex_to_rgba(cosmic.base_hex),
        shade_color=hex_to_rgba(cosmic.shade_hex),
        shade_shift=-0.05,
        shade_toony=0.4,
        lighting_influence=0.6,
        matcap_blend=0.4,
        matcap_color=hex_to_rgba("#C2BAE0"),  # lavender.300 - iridescent
        rim_color=hex_to_rgba("#A99AD0", 0.9),
        rim_fresnel=0.7,
        rim_lift=0.2,
        outline_width=0.03,
        outline_color=hex_to_rgba("#3C5C9E"),  # astral.500
        emission_color=hex_to_rgba("#6E5AA6", 0.15),
        emission_strength=0.1,
        subsurface_color=hex_to_rgba("#ECE6F4"),
        subsurface_amount=0.05,
        npc_dream_intensity=1.5,
        npc_color_shift=hex_to_rgba("#3C5C9E", 0.4),  # astral.500 shift
        npc_wind_strength=0.5,
        npc_glow_intensity=0.5,
    )

    # ─── MIRAGE DANCER ───
    mirage = ArchetypePalette(
        name="MirageDancer",
        display_name="Mirage Dancer",
        description="Twilight evasion archetype — gradient fabrics, trailing ribbons, gold-accented aurora palette. High-mobility DPS in battle.",
        count=3,
        battle_role="DPS",
        base_hex="#E5EAF5",      # astral.100 - pale astral
        shade_hex="#8AA9D6",     # astral.300 - mid astral
        accent_hex="#C9A86A",    # gold.500 - champagne gold
        element="Gale",
        bpm=180.0,
        outfit_pieces=["asymmetric_gradient_dress", "wind_torn_scarf", "ankle_bells", "trailing_ribbons"],
    )
    mirage.mtoon = MToonParams(
        base_color=hex_to_rgba(mirage.base_hex),
        shade_color=hex_to_rgba(mirage.shade_hex),
        shade_shift=0.0,
        shade_toony=0.5,
        lighting_influence=0.75,
        matcap_blend=0.25,
        matcap_color=hex_to_rgba("#F0E6D2"),  # gold.100 - warm matcap
        rim_color=hex_to_rgba("#DDC79B", 0.9),  # gold.300
        rim_fresnel=0.5,
        rim_lift=0.15,
        outline_width=0.028,
        outline_color=hex_to_rgba("#A7884E"),  # gold.700
        emission_color=hex_to_rgba("#C9A86A", 0.08),
        emission_strength=0.05,
        subsurface_color=hex_to_rgba("#F7F4EF"),  # ivory.100
        subsurface_amount=0.1,
        npc_dream_intensity=1.0,
        npc_color_shift=hex_to_rgba("#8AA9D6", 0.25),  # astral.300 shift
        npc_wind_strength=1.5,
        npc_glow_intensity=0.3,
    )

    return {
        "SakuraDreamer": sakura,
        "CosmicWeaver": cosmic,
        "MirageDancer": mirage,
    }


def generate_palette_json(output_path: str | Path = None) -> str:
    """Generate palette JSON for pipeline consumption."""
    palettes = create_archetype_palettes()
    output = {}
    for key, palette in palettes.items():
        output[key] = {
            "name": palette.name,
            "display_name": palette.display_name,
            "description": palette.description,
            "count": palette.count,
            "battle_role": palette.battle_role,
            "element": palette.element,
            "bpm": palette.bpm,
            "outfit_pieces": palette.outfit_pieces,
            "colors": {
                "base": palette.base_hex,
                "shade": palette.shade_hex,
                "accent": palette.accent_hex,
            },
            "mtoon_params": palette.mtoon.to_mpc_dict(prefix="npc_"),
        }

    json_str = json.dumps(output, indent=2)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json_str, encoding="utf-8")

    return json_str


def load_design_tokens(tokens_path: str | Path = None) -> dict:
    """Load and resolve design tokens from tokens.json."""
    if tokens_path is None:
        tokens_path = Path(__file__).parent.parent.parent.parent.parent / "_staging" / "design-system" / "tokens.json"
    else:
        tokens_path = Path(tokens_path)

    with open(tokens_path, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    # Resolve references (simple string replacement for {primitives.xxx})
    def resolve_refs(obj: Any, primitives: dict) -> Any:
        if isinstance(obj, dict):
            if "value" in obj and isinstance(obj["value"], str) and obj["value"].startswith("{"):
                ref = obj["value"].strip("{}")
                parts = ref.split(".")
                val = primitives
                for p in parts:
                    if isinstance(val, dict) and p in val:
                        val = val[p]
                    else:
                        return obj["value"]
                if isinstance(val, dict) and "value" in val:
                    return val["value"]
                return val
            return {k: resolve_refs(v, primitives) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item, primitives) for item in obj]
        return obj

    primitives = tokens.get("primitives", {})
    resolved = resolve_refs(tokens, primitives)
    return resolved


if __name__ == "__main__":
    # Generate palette JSON
    output = Path(__file__).parent / "archetype_palettes.json"
    json_str = generate_palette_json(output)
    print(f"Generated palette mapping: {output}")
    print(json_str)