"""VRM Source Registry — defines where NPC VRMs come from and their licensing.

Supports three sources:
1. VRoid Studio — locally created/exported VRMs (free, commercial-friendly)
2. VRoid Hub — curated downloads (check license per model)
3. Custom Blender — hand-crafted VRMs for hero NPCs
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional
import json


class VRMSourceType(Enum):
    VROID_STUDIO = "vroid_studio"
    VROID_HUB = "vroid_hub"
    CUSTOM_BLENDER = "custom_blender"


class VRMLicense(Enum):
    VROID_STUDIO_TOS = "vroid_studio_tos"          # Commercial OK, credit required
    CC_BY_4_0 = "cc_by_4_0"                        # Commercial OK, attribution required
    CC_BY_NC_4_0 = "cc_by_nc_4_0"                  # Non-commercial only
    CUSTOM = "custom"                              # Per-model agreement
    UNKNOWN = "unknown"


@dataclass
class VRMSource:
    """Single VRM source entry."""
    source_id: str
    source_type: VRMSourceType
    archetype: str  # "SakuraDreamer", "CosmicWeaver", "MirageDancer"

    # File info
    local_path: str  # Relative to SourceVRMs/
    filename: str

    # Metadata
    author: str
    license: VRMLicense
    license_url: str = ""
    commercial_ok: bool = True

    # VRoid Hub specific
    hub_url: str = ""
    hub_model_id: str = ""

    # Character traits (used for matching)
    body_type: str = "standard"      # "petite", "standard", "tall", "willowy"
    base_hair_color: str = ""
    base_eye_color: str = ""
    expression_presets: list[str] = field(default_factory=list)  # e.g., ["smile", "surprised", "gentle"]

    # Pipeline status
    imported: bool = False
    import_path: str = ""  # UE asset path after import
    bone_count: int = 0
    tri_count: int = 0
    audit_passed: bool = False


# ──────────────────────────────────────────────────────────────────────
# SOURCE REGISTRY — Edit this to add your 10 VRMs
# ──────────────────────────────────────────────────────────────────────

VROID_STUDIO_SOURCES: list[VRMSource] = [
    # Sakura Dreamer ×4 (petite/standard, warm palettes)
    VRMSource(
        source_id="SD_01_SakuraMaiden",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="SakuraDreamer",
        local_path="VRoidStudio/SD_01_SakuraMaiden.vrm",
        filename="SD_01_SakuraMaiden.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="petite",
        base_hair_color="#D6A9B0",
        base_eye_color="#E7C9CE",
        expression_presets=["gentle_smile", "soft_laugh", "thoughtful", "dreamy"],
    ),
    VRMSource(
        source_id="SD_02_PetalPriestess",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="SakuraDreamer",
        local_path="VRoidStudio/SD_02_PetalPriestess.vrm",
        filename="SD_02_PetalPriestess.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="standard",
        base_hair_color="#E7C9CE",
        base_eye_color="#F5E8EA",
        expression_presets=["prayer", "gentle_smile", "blessing", "serene"],
    ),
    VRMSource(
        source_id="SD_03_BlossomGuide",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="SakuraDreamer",
        local_path="VRoidStudio/SD_03_BlossomGuide.vrm",
        filename="SD_03_BlossomGuide.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="willowy",
        base_hair_color="#F5E8EA",
        base_eye_color="#D6A9B0",
        expression_presets=["guiding_smile", "curious", "gentle_laugh", "welcoming"],
    ),
    VRMSource(
        source_id="SD_04_FlowerMerchant",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="SakuraDreamer",
        local_path="VRoidStudio/SD_04_FlowerMerchant.vrm",
        filename="SD_04_FlowerMerchant.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="standard",
        base_hair_color="#E7C9CE",
        base_eye_color="#F5E8EA",
        expression_presets=["merchant_smile", "proud", "thoughtful", "laughing"],
    ),

    # Cosmic Weaver ×2 (tall/willowy, cool palettes)
    VRMSource(
        source_id="CW_01_StarWeaver",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="CosmicWeaver",
        local_path="VRoidStudio/CW_01_StarWeaver.vrm",
        filename="CW_01_StarWeaver.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="tall",
        base_hair_color="#6E5AA6",
        base_eye_color="#A99AD0",
        expression_presets=["mystical", "knowing_smile", "contemplative", "stargazing"],
    ),
    VRMSource(
        source_id="CW_02_VoidSeamstress",
        source_type=VRMSourceType.VROID_STUDIO,
        archetype="CosmicWeaver",
        local_path="VRoidStudio/CW_02_VoidSeamstress.vrm",
        filename="CW_02_VoidSeamstress.vrm",
        author="Melodia Team (VRoid Studio)",
        license=VRMLicense.VROID_STUDIO_TOS,
        commercial_ok=True,
        body_type="willowy",
        base_hair_color="#3C5C9E",
        base_eye_color="#8AA9D6",
        expression_presets=["focused", "subtle_smile", "weaving", "distant"],
    ),

    # Mirage Dancer ×? (will add 2 from VRoid Hub)
]

# VRoid Hub curated models — REPLACE THESE with actual URLs/model IDs
VROID_HUB_SOURCES: list[VRMSource] = [
    # Need 1 more Cosmic Weaver + 2 Mirage Dancers from Hub
    VRMSource(
        source_id="CW_03_AstralScribe",
        source_type=VRMSourceType.VROID_HUB,
        archetype="CosmicWeaver",
        local_path="VRoidHub/CW_03_AstralScribe.vrm",
        filename="CW_03_AstralScribe.vrm",
        author="VRoid Hub Creator (TODO: add name)",
        license=VRMLicense.CC_BY_4_0,  # Verify per model!
        commercial_ok=True,
        license_url="https://hub.vroid.com/characters/XXXXXXXX",  # REPLACE
        hub_url="https://hub.vroid.com/characters/XXXXXXXX",
        hub_model_id="XXXXXXXX",
        body_type="tall",
        base_hair_color="#6E5AA6",
        base_eye_color="#C2BAE0",
        expression_presets=["writing", "looking_up", "gentle_smile", "concentrating"],
    ),
    VRMSource(
        source_id="MD_01_TwilightDancer",
        source_type=VRMSourceType.VROID_HUB,
        archetype="MirageDancer",
        local_path="VRoidHub/MD_01_TwilightDancer.vrm",
        filename="MD_01_TwilightDancer.vrm",
        author="VRoid Hub Creator (TODO: add name)",
        license=VRMLicense.CC_BY_4_0,
        commercial_ok=True,
        license_url="https://hub.vroid.com/characters/XXXXXXXX",
        hub_url="https://hub.vroid.com/characters/XXXXXXXX",
        hub_model_id="XXXXXXXX",
        body_type="willowy",
        base_hair_color="#8AA9D6",
        base_eye_color="#C9A86A",
        expression_presets=["dancing", "joyful", "wind_swept", "playful"],
    ),
    VRMSource(
        source_id="MD_02_WindWalker",
        source_type=VRMSourceType.VROID_HUB,
        archetype="MirageDancer",
        local_path="VRoidHub/MD_02_WindWalker.vrm",
        filename="MD_02_WindWalker.vrm",
        author="VRoid Hub Creator (TODO: add name)",
        license=VRMLicense.CC_BY_4_0,
        commercial_ok=True,
        license_url="https://hub.vroid.com/characters/XXXXXXXX",
        hub_url="https://hub.vroid.com/characters/XXXXXXXX",
        hub_model_id="XXXXXXXX",
        body_type="standard",
        base_hair_color="#C9A86A",
        base_eye_color="#8AA9D6",
        expression_presets=["walking", "determined", "breezy", "confident"],
    ),
]

# Custom Blender VRMs — Hero NPCs with unique proportions
CUSTOM_BLENDER_SOURCES: list[VRMSource] = [
    VRMSource(
        source_id="MD_03_ZephyrChampion",
        source_type=VRMSourceType.CUSTOM_BLENDER,
        archetype="MirageDancer",
        local_path="CustomBlender/MD_03_ZephyrChampion.vrm",
        filename="MD_03_ZephyrChampion.vrm",
        author="Melodia Art Team (Blender + VRM Addon)",
        license=VRMLicense.CUSTOM,
        commercial_ok=True,
        body_type="athletic",
        base_hair_color="#DDC79B",  # gold.300
        base_eye_color="#66D9FF",   # portfolio.iri.cyan
        expression_presets=["champion_pose", "wind_mastery", "confident_grin", "battle_ready"],
    ),
    VRMSource(
        source_id="SD_05_EternalGardener",
        source_type=VRMSourceType.CUSTOM_BLENDER,
        archetype="SakuraDreamer",
        local_path="CustomBlender/SD_05_EternalGardener.vrm",
        filename="SD_05_EternalGardener.vrm",
        author="Melodia Art Team (Blender + VRM Addon)",
        license=VRMLicense.CUSTOM,
        commercial_ok=True,
        body_type="standard",
        base_hair_color="#D6A9B0",
        base_eye_color="#FF6EB4",   # portfolio.iri.magenta
        expression_presets=["nurturing", "gentle_wisdom", "blooming_smile", "peaceful"],
    ),
]


def get_all_sources() -> list[VRMSource]:
    """Get all VRM sources combined."""
    return VROID_STUDIO_SOURCES + VROID_HUB_SOURCES + CUSTOM_BLENDER_SOURCES


def get_sources_by_archetype(archetype: str) -> list[VRMSource]:
    """Filter sources by archetype."""
    return [s for s in get_all_sources() if s.archetype == archetype]


def get_sources_by_type(source_type: VRMSourceType) -> list[VRMSource]:
    """Filter sources by type."""
    return [s for s in get_all_sources() if s.source_type == source_type]


def validate_licenses() -> dict:
    """Check all sources for license compliance."""
    results = {
        "total": len(get_all_sources()),
        "commercial_ok": 0,
        "needs_attribution": 0,
        "non_commercial": 0,
        "unknown": 0,
        "issues": [],
    }
    for src in get_all_sources():
        if not src.commercial_ok:
            results["non_commercial"] += 1
            results["issues"].append(f"{src.source_id}: Non-commercial license ({src.license.value})")
        elif src.license in (VRMLicense.CC_BY_4_0, VRMLicense.VROID_STUDIO_TOS):
            results["commercial_ok"] += 1
            results["needs_attribution"] += 1
        elif src.license == VRMLicense.UNKNOWN:
            results["unknown"] += 1
            results["issues"].append(f"{src.source_id}: Unknown license")
        else:
            results["commercial_ok"] += 1
    return results


def export_registry(output_path: Path = None) -> str:
    """Export registry to JSON for pipeline consumption."""
    if output_path is None:
        output_path = Path(__file__).parent / "vrm_registry.json"

    data = {
        "sources": [asdict(s) for s in get_all_sources()],
        "validation": validate_licenses(),
        "counts": {
            "total": len(get_all_sources()),
            "by_archetype": {
                "SakuraDreamer": len(get_sources_by_archetype("SakuraDreamer")),
                "CosmicWeaver": len(get_sources_by_archetype("CosmicWeaver")),
                "MirageDancer": len(get_sources_by_archetype("MirageDancer")),
            },
            "by_type": {
                "vroid_studio": len(get_sources_by_type(VRMSourceType.VROID_STUDIO)),
                "vroid_hub": len(get_sources_by_type(VRMSourceType.VROID_HUB)),
                "custom_blender": len(get_sources_by_type(VRMSourceType.CUSTOM_BLENDER)),
            },
        },
    }

    # Convert enums to strings
    def serialize(obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, list):
            return [serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        return obj

    json_str = json.dumps(serialize(data), indent=2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json_str, encoding="utf-8")
    return json_str


if __name__ == "__main__":
    # Print registry summary
    print("=== VRM SOURCE REGISTRY ===")
    for src in get_all_sources():
        print(f"  [{src.archetype}] {src.source_id} -- {src.source_type.value} -- {src.license.value}")

    print(f"\nTotal: {len(get_all_sources())} VRMs")
    print(f"  SakuraDreamer: {len(get_sources_by_archetype('SakuraDreamer'))}")
    print(f"  CosmicWeaver: {len(get_sources_by_archetype('CosmicWeaver'))}")
    print(f"  MirageDancer: {len(get_sources_by_archetype('MirageDancer'))}")

    validation = validate_licenses()
    print(f"\nLicense Check: {validation['commercial_ok']}/{validation['total']} commercial OK")
    for issue in validation["issues"]:
        print(f"  WARN: {issue}")

    # Export
    export_registry()
    print(f"\nExported to vrm_registry.json")