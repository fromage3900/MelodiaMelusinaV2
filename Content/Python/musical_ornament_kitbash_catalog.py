"""Musical Ornament Kitbash — product catalog (sibling SKU to gothic v1).

10 celestial sheet-music SM_Orn_* meshes at /Game/EnvSandbox/Meshes/OrnamentMusical/
(7 original + 3 Melody Tokens). Separate from gothic architecture kitbash v1.
Lane B ornaments only — never wardrobe / Live Link / MelodiaGameUI PNG atlas.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paths import ENV

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ORNAMENT_DIR = f"{ENV}/Meshes/OrnamentMusical"
FBX_EXPORT_DIR = PROJECT_ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
PRODUCT_ROOT = PROJECT_ROOT / "Products" / "MusicalOrnamentKitbash"
PRODUCT_FBX = PRODUCT_ROOT / "FBX"
DEMO_LEVEL = f"{ENV}/Environments/Demo/L_MusicalOrnamentShowcase"

PRODUCT_ID = "melodia-musical-ornament-kitbash-v1"
PRODUCT_NAME = "Melodia Musical Ornament Kitbash"
PRODUCT_TAGLINE = "10 celestial sheet-music ornaments (incl. Melody Tokens) for Unreal Engine 5.8+"
LAUNCH_PRICE_USD = 14
LIST_PRICE_USD = 18

GUMROAD_URL_PLACEHOLDER = "https://fromage3900.gumroad.com/l/musical-ornament-kitbash"
ARTSTATION_URL_PLACEHOLDER = "https://www.artstation.com/marketplace"
STORE_LIVE = False
ARTSTATION_LIVE = False

PILLAR = "CelestialSheetMusic"


@dataclass(frozen=True)
class OrnamentMesh:
    asset_name: str
    key: str
    tier: str  # hero | detail
    pillar: str
    description: str
    use_cases: tuple[str, ...]
    material_slots: tuple[str, ...] = ("Base", "Trim")
    lods: int = 3

    @property
    def ue_path(self) -> str:
        return f"{ORNAMENT_DIR}/{self.asset_name}"

    @property
    def fbx_name(self) -> str:
        return f"{self.asset_name}.fbx"


MESHES: tuple[OrnamentMesh, ...] = (
    OrnamentMesh(
        "SM_Orn_TrebleClef",
        "Treble_Clef",
        "hero",
        PILLAR,
        "Decorative G-clef scroll for shrine facades and HUD-scale set dressing.",
        ("title atelier props", "shrine wall accents", "rhythm arena markers"),
    ),
    OrnamentMesh(
        "SM_Orn_NoteHead",
        "Note_Head",
        "detail",
        PILLAR,
        "Quarter note head with stem — clear silhouette at kitbash scale.",
        ("scatter notes", "highway prop accents", "jewelry-scale dressing"),
    ),
    OrnamentMesh(
        "SM_Orn_NoteBeam",
        "Note_Beam",
        "detail",
        PILLAR,
        "Beamed eighth pair — Perfect telegraph / combo motif.",
        ("combo bursts", "rail ornaments", "judgment telegraph props"),
    ),
    OrnamentMesh(
        "SM_Orn_SheetMusicRail",
        "Sheet_Music_Rail",
        "hero",
        PILLAR,
        "Five-line staff rail segment with bar lines and note pearls.",
        ("balcony rails", "stage aprons", "sheet-music architecture"),
    ),
    OrnamentMesh(
        "SM_Orn_MusicalCorner",
        "Musical_Corner",
        "detail",
        PILLAR,
        "L-bracket filigree corner with clef-scroll curl (4-corner rotatable).",
        ("frame corners", "HUD 3D mirrors", "panel kitbash"),
    ),
    OrnamentMesh(
        "SM_Orn_MusicalDivider",
        "Musical_Divider",
        "detail",
        PILLAR,
        "Horizontal divider bar with repeating note-beam motif.",
        ("section dividers", "entablature accents", "UI 3D chrome"),
    ),
    OrnamentMesh(
        "SM_Orn_PearlJewel",
        "Pearl_Jewel",
        "detail",
        PILLAR,
        "Pearl center jewel with gold/iri trim ring — boss / medallion core.",
        ("ceiling bosses", "hitline jewels", "amulet props"),
    ),
    OrnamentMesh(
        "SM_Orn_MelodyToken_01",
        "Melody_Token_01",
        "hero",
        PILLAR,
        "Melody Token I — collectible rhythm medallion (placeholder until beauty pass).",
        ("collectible props", "rhythm pickup mirrors", "shop hero plate"),
    ),
    OrnamentMesh(
        "SM_Orn_MelodyToken_02",
        "Melody_Token_02",
        "detail",
        PILLAR,
        "Melody Token II — collectible harmony medallion (placeholder until beauty pass).",
        ("collectible props", "combo rewards", "kitbash scatter"),
    ),
    OrnamentMesh(
        "SM_Orn_MelodyToken_03",
        "Melody_Token_03",
        "detail",
        PILLAR,
        "Melody Token III — collectible coda medallion (placeholder until beauty pass).",
        ("collectible props", "finale markers", "jewelry-scale dressing"),
    ),
)

HERO_MESHES = tuple(m for m in MESHES if m.tier == "hero")
DETAIL_MESHES = tuple(m for m in MESHES if m.tier == "detail")

PACKAGE_CONTENTS = {
    "fbx": "10 FBX meshes (7 musical + 3 Melody Tokens), 2 material slots (Base + Trim)",
    "unreal": "UE 5.8 folder: /Game/EnvSandbox/Meshes/OrnamentMusical",
    "docs": "Installation README + celestial sheet-music scale notes",
}

STORE_TAGS = (
    "kitbash",
    "ornament",
    "musical",
    "sheet-music",
    "melody-token",
    "unreal-engine",
    "ue5",
    "fantasy",
    "melodia",
    "stylized",
)

EXCLUDED_FROM_PACK = (
    {
        "name": "Gothic Ornamental Architecture Kitbash (15)",
        "reason": "Sibling SKU — architectural gothic/baroque, not musical.",
        "path": f"{ENV}/Meshes/Ornament",
    },
    {
        "name": "Melodia game UI textures (T_Melodia_*)",
        "reason": "2D HUD / Batch N atlas — not 3D kitbash meshes.",
        "path": f"{ENV}/Textures/Source/MelodiaGameUI",
    },
    {
        "name": "Melusina wardrobe / Live Link",
        "reason": "Character clothes lane — never mixed with SM_Orn_*.",
        "path": "Exports/MelusinaClothes",
    },
)


def mesh_names() -> list[str]:
    return [m.asset_name for m in MESHES]


def as_product_dict() -> dict:
    return {
        "product_id": PRODUCT_ID,
        "name": PRODUCT_NAME,
        "tagline": PRODUCT_TAGLINE,
        "launch_price_usd": LAUNCH_PRICE_USD,
        "list_price_usd": LIST_PRICE_USD,
        "mesh_count": len(MESHES),
        "hero_count": len(HERO_MESHES),
        "detail_count": len(DETAIL_MESHES),
        "engine": "Unreal Engine 5.8+",
        "formats": ["FBX", "UAsset"],
        "gumroad_url": GUMROAD_URL_PLACEHOLDER,
        "artstation_url": ARTSTATION_URL_PLACEHOLDER,
        "store_live": STORE_LIVE,
        "artstation_live": ARTSTATION_LIVE,
        "sibling_of": "melodia-ornamental-architecture-kitbash-v1",
        "meshes": [
            {
                "asset_name": m.asset_name,
                "key": m.key,
                "tier": m.tier,
                "pillar": m.pillar,
                "description": m.description,
                "use_cases": list(m.use_cases),
                "ue_path": m.ue_path,
                "fbx_name": m.fbx_name,
            }
            for m in MESHES
        ],
        "package_contents": PACKAGE_CONTENTS,
        "store_tags": list(STORE_TAGS),
        "excluded": list(EXCLUDED_FROM_PACK),
        "ue_paths": {
            "ornament_dir": ORNAMENT_DIR,
            "demo_level": DEMO_LEVEL,
            "fbx_export": str(FBX_EXPORT_DIR).replace("\\", "/"),
            "product_root": str(PRODUCT_ROOT).replace("\\", "/"),
        },
    }
