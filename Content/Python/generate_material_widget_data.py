"""Compile rich dataset for the Material Instance Widget UI Panel.

Generates:
  - teamwork_projects/material_instance_widget_panel/material-instance-data.json
  - teamwork_projects/material_instance_widget_panel/material-instance-data.js (window.MATERIAL_INSTANCE_DATA)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import master_column_scheme as scheme
import master_material_clamping_engine as clamping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEST_DIR = PROJECT_ROOT.parent / "teamwork_projects" / "material_instance_widget_panel"
DEST_DIR.mkdir(parents=True, exist_ok=True)

OUT_JSON = DEST_DIR / "material-instance-data.json"
OUT_JS = DEST_DIR / "material-instance-data.js"

# Curated Hero Instances
PRESET_INSTANCES = [
    {
        "id": "MI_NikkiHero_SakuraDream",
        "name": "Sakura Dream",
        "category": "Nikki Heroes",
        "master": "M_Master_Nikki",
        "description": "Signature haute-couture petal pink satin with iridescent sheen and soft dream bloom.",
        "backdrop": "Sakura_SoftVoid",
        "overrides": {
            "BaseTint": [0.98, 0.72, 0.78, 1.0],
            "RoughnessMin": 0.12,
            "RoughnessMax": 0.45,
            "MetallicScale": 0.05,
            "FabricSheen": 1.25,
            "SheenPower": 3.2,
            "Iridescence": 0.85,
            "IridescencePower": 4.5,
            "NikkiPastelStrength": 0.90,
            "NikkiPastelBloom": 1.40,
            "NikkiGlitterHalo_Amount": 0.65,
            "NikkiGlitterHalo_Intensity": 2.50,
            "NikkiPetal_Strength": 0.75,
            "bNikkiHero": True,
            "bSheenUsesNormal": True,
        }
    },
    {
        "id": "MI_NikkiHero_CosmicOrrery",
        "name": "Cosmic Orrery",
        "category": "Nikki Heroes",
        "master": "M_Master_Toon_Universal",
        "description": "Deep indigo velvet infused with stellar constellations, nebula dust, and gold bullion trim.",
        "backdrop": "Cosmic_DeepField",
        "overrides": {
            "BaseTint": [0.08, 0.09, 0.22, 1.0],
            "Roughness": 0.28,
            "Metallic": 0.15,
            "GlowIntensity": 3.8,
            "GlowColor": [0.35, 0.75, 1.0, 1.0],
            "CelestialNebulaStrength": 2.8,
            "CelestialGalaxyStrength": 1.9,
            "ConstellationStrength": 2.2,
            "SparkleIntensity": 4.5,
            "SparkleScale": 380.0,
            "bCelestial_Active": True,
            "bSparkleAdvanced": True,
            "GildingStrength": 1.1,
        }
    },
    {
        "id": "MI_NikkiHero_SpaceCathedral",
        "name": "Space Cathedral",
        "category": "Nikki Heroes",
        "master": "M_Master_Toon_Universal",
        "description": "Gothic architectural resonance with amethyst stained-glass transmission and gold leaf accents.",
        "backdrop": "Cosmic_DeepField",
        "overrides": {
            "BaseTint": [0.15, 0.10, 0.25, 1.0],
            "Roughness": 0.18,
            "Metallic": 0.75,
            "RimIntensity": 2.8,
            "RimColor": [0.90, 0.60, 1.0, 1.0],
            "GoldTint": [1.0, 0.82, 0.35, 1.0],
            "GildingStrength": 1.45,
            "SigilStrength": 1.6,
            "SigilRings": 4.0,
            "SigilSides": 8.0,
        }
    },
    {
        "id": "MI_SDF_RosyQuartz",
        "name": "Rosy Quartz",
        "category": "Nikki Heroes",
        "master": "M_Master_Nikki",
        "description": "Translucent rose quartz crystal with internal chromatic dispersion and mother-of-pearl luster.",
        "backdrop": "Sakura_SoftVoid",
        "overrides": {
            "BaseTint": [0.95, 0.80, 0.85, 1.0],
            "RoughnessMin": 0.05,
            "RoughnessMax": 0.22,
            "MetallicScale": 0.0,
            "NikkiPearl_Strength": 1.65,
            "NikkiPearl_Frequency": 4.2,
            "NikkiPastelBloom": 1.8,
            "NikkiSDFRibbon_Strength": 1.1,
            "NikkiSDFRibbon_Sharpness": 12.0,
        }
    },
    {
        "id": "MI_Show_ElementHydro",
        "name": "Element Hydro",
        "category": "Nikki Heroes",
        "master": "M_Master_Toon_Universal",
        "description": "Fluid cymatic water surface with caustic light refraction and bioluminescent foam.",
        "backdrop": "Studio_Neutral",
        "overrides": {
            "BaseTint": [0.12, 0.65, 0.88, 1.0],
            "Roughness": 0.04,
            "Metallic": 0.0,
            "WetnessStrength": 1.0,
            "RimIntensity": 3.2,
            "RimColor": [0.45, 0.95, 1.0, 1.0],
            "MistStrength": 1.2,
            "GlintIntensity": 4.8,
            "GlintSpeed": 2.5,
        }
    },
    {
        "id": "MI_Show_CherryBlossom",
        "name": "Cherry Blossom",
        "category": "Nikki Heroes",
        "master": "M_Master_Nikki",
        "description": "Subtle porcelain glaze tinted with fluttering sakura petals and delicate pastel gradients.",
        "backdrop": "Sakura_SoftVoid",
        "overrides": {
            "BaseTint": [1.0, 0.88, 0.92, 1.0],
            "RoughnessMin": 0.15,
            "RoughnessMax": 0.35,
            "NikkiPastelStrength": 1.2,
            "NikkiPetal_Strength": 1.4,
            "NikkiPetal_Scale": 8.0,
            "NikkiPetal_Radius": 0.85,
        }
    },
    {
        "id": "MI_Universal_GoldLeaf",
        "name": "Gold Leaf Baroque",
        "category": "Universal Magical",
        "master": "M_Master_Toon_Universal",
        "description": "Hand-hammered gold leaf gilding over polished black obsidian with curvature-sensitive distress.",
        "backdrop": "Baroque_WarmVault",
        "overrides": {
            "BaseTint": [0.05, 0.05, 0.05, 1.0],
            "Roughness": 0.15,
            "Metallic": 0.95,
            "GoldRoughness": 0.22,
            "GildingStrength": 1.85,
            "CurvatureSensitivity": 6.5,
            "GoldTint": [1.0, 0.85, 0.30, 1.0],
        }
    },
    {
        "id": "MI_Universal_TemporalInk",
        "name": "Temporal Ink Wash",
        "category": "Universal Stylized",
        "master": "M_Master_Toon_Universal",
        "description": "Traditional East Asian sumi-e ink wash with dynamic fluid boiling and brush edge wear.",
        "backdrop": "Studio_Neutral",
        "overrides": {
            "BaseTint": [0.92, 0.90, 0.85, 1.0],
            "Roughness": 0.75,
            "Metallic": 0.0,
            "TemporalStrength": 1.2,
            "BoilIntensity": 0.85,
            "WindSpeed": 1.4,
            "IttoBlendAmount": 0.95,
            "IttoInkStrength": 1.4,
            "IttoPatternScale": 4.5,
        }
    },
    {
        "id": "MI_Universal_AnimeCel",
        "name": "Anime Cel Pristine",
        "category": "Universal Stylized",
        "master": "M_Master_Toon_Universal",
        "description": "Classic 2-tone anime cel shading with crisp shadow termination and stylized specular rim.",
        "backdrop": "Studio_Neutral",
        "overrides": {
            "BaseTint": [0.95, 0.85, 0.75, 1.0],
            "Roughness": 0.40,
            "Metallic": 0.0,
            "RampSharpness": 28.0,
            "RampContrast": 2.2,
            "RampStrength": 1.0,
            "RimWidth": 0.35,
            "RimIntensity": 2.4,
            "RimPower": 6.5,
        }
    },
    {
        "id": "MI_Landscape_VerdantMeadow",
        "name": "Verdant Meadow HeightBlend",
        "category": "Landscape Biomes",
        "master": "M_Master_Toon_Landscape_HeightBlend",
        "description": "Multi-layer landscape shader blending lush grass, weathered cliff rock, and damp soil paths.",
        "backdrop": "Studio_Neutral",
        "overrides": {
            "GrassRoughness": 0.65,
            "RockRoughness": 0.35,
            "MudRoughness": 0.25,
            "HeightBlendStrength": 0.85,
            "SlopeSharpness": 8.0,
            "GrassAmount": 0.70,
            "MudAmount": 0.15,
            "TriplanarPro_Scale": 4.0,
            "TriplanarPro_Sharpness": 12.0,
        }
    },
]


def build_widget_dataset() -> Dict[str, Any]:
    catalog_path = PROJECT_ROOT / "Saved" / "Audit" / "master_material_clamps_catalog.json"
    if not catalog_path.is_file():
        clamping.export_full_catalog()

    catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))

    # Compile master schemas with groups and parameter metadata
    masters_summary: Dict[str, Any] = {}
    for m_stem, m_info in catalog_data.get("masters", {}).items():
        try:
            groups_def = scheme.groups_for(m_stem)
        except ValueError:
            groups_def = scheme.UNIVERSAL_GROUPS

        groups_meta = []
        for g_label, pnames in groups_def:
            p_list = []
            for pn in pnames:
                c_info = m_info.get("parameters", {}).get(pn) or {}
                p_list.append({
                    "name": pn,
                    "min": c_info.get("slider_min", 0.0),
                    "max": c_info.get("slider_max", 1.0),
                    "desc": c_info.get("description", "Standard parameter"),
                    "rule": c_info.get("rule_source", "default"),
                })
            groups_meta.append({
                "label": g_label,
                "param_count": len(pnames),
                "parameters": p_list,
            })

        masters_summary[m_stem] = {
            "stem": m_stem,
            "total_scalars": m_info.get("total_scalars", 0),
            "group_count": len(groups_def),
            "groups": groups_meta,
        }

    dataset = {
        "schema": "melodia.material_instance_widget.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_presets": len(PRESET_INSTANCES),
        "presets": PRESET_INSTANCES,
        "masters": masters_summary,
        "backdrops": {
            "Sakura_SoftVoid": {"label": "Sakura Soft Void", "bg": "#1c1218", "tint": "#ffc4d6"},
            "Cosmic_DeepField": {"label": "Cosmic Deep Field", "bg": "#0a0a1a", "tint": "#9d4edd"},
            "Baroque_WarmVault": {"label": "Baroque Warm Vault", "bg": "#1a1208", "tint": "#ffd700"},
            "Studio_Neutral": {"label": "Studio Neutral Void", "bg": "#121418", "tint": "#a0a8b9"},
        }
    }

    # Write JSON
    OUT_JSON.write_text(json.dumps(dataset, indent=2), encoding="utf-8")

    # Write JS
    js_content = f"// Generated by Melodia Material Pipeline\nwindow.MATERIAL_INSTANCE_DATA = {json.dumps(dataset, indent=2)};\n"
    OUT_JS.write_text(js_content, encoding="utf-8")

    print(f"Compiled Material Instance Widget dataset -> {OUT_JSON.resolve()}")
    print(f"Compiled Material Instance Widget JS -> {OUT_JS.resolve()}")
    return dataset


if __name__ == "__main__":
    build_widget_dataset()
