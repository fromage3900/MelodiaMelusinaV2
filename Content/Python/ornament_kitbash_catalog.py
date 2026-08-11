"""Ornamental Architecture Kitbash — product catalog (single source of truth).

15 procedural SM_Orn_* meshes at /Game/EnvSandbox/Meshes/Ornament/.
Used by kitbash_prep_meshes.py, package_ornament_kitbash.py, and store listings.

Meshes NOT in this pack (separate products / internal only):
  - Greybox_Kit blockout meshes — layout prototyping, not sellable ornament art
  - surreal_architecture_gen Blender outputs — different pipeline / license scope
  - 70_Japanese_Ornament_Alphas — third-party texture pack; shader companion only
  - Melodia game UI textures — UI/VFX product lane
"""
from __future__ import annotations

from dataclasses import dataclass

from paths import MELODIA, ENV

ORNAMENT_DIR = f"{ENV}/Meshes/Ornament"
DEMO_LEVEL = f"{ENV}/Environments/Demo/L_OrnamentKitbashShowcase"
PCG_HERO_GRAPH = f"{ENV}/PCG/Universal/PCG_OrnamentalArch"
PCG_DETAIL_GRAPH = f"{ENV}/PCG/Universal/PCG_OrnamentalDetail"

PRODUCT_ID = "melodia-ornamental-architecture-kitbash-v1"
PRODUCT_NAME = "Melodia Ornamental Architecture Kitbash"
PRODUCT_TAGLINE = "15 procedural gothic & baroque ornaments for Unreal Engine 5.8+"
LAUNCH_PRICE_USD = 24
LIST_PRICE_USD = 29

GUMROAD_URL_PLACEHOLDER = "https://fromage3900.gumroad.com/l/ornamental-kitbash"
ARTSTATION_URL_PLACEHOLDER = "https://www.artstation.com/marketplace"
# Flip to True only after Gumroad has a purchasable ZIP (not just a slug URL).
STORE_LIVE = False
ARTSTATION_LIVE = False


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
        "SM_Orn_RoseWindow_8Petal", "RoseWindow_8Petal", "hero", "SpaceCathedral",
        "Gothic rose window with eight petal lobes and radial tracery ring.",
        ("cathedral facades", "boss arena backdrops", "celestial shrine oculi"),
    ),
    OrnamentMesh(
        "SM_Orn_SpiralStaircase", "Spiral_Staircase", "hero", "SpaceCathedral",
        "Spiral staircase — 24 steps, two full turns, tower interior hero piece.",
        ("tower interiors", "vertical route reveals", "cathedral ascent beats"),
    ),
    OrnamentMesh(
        "SM_Orn_VaultRibs", "Vault_Ribs", "hero", "SpaceCathedral",
        "Crossing Bezier gothic vault ribs with apex flower boss — kitbash hero cluster.",
        ("ceiling kits", "undercroft reveals", "boss room overhead structure"),
    ),
    OrnamentMesh(
        "SM_Orn_OculusFrame", "Oculus_Frame", "hero", "SpaceCathedral",
        "Circular oculus frame with sixteen-petal modulation.",
        ("dome transitions", "sky portals", "celestial observatory walls"),
    ),
    OrnamentMesh(
        "SM_Orn_QuatrefoilArch", "Quatrefoil_Arch", "detail", "BaroqueGrotto",
        "Gothic quatrefoil archway with lobed indentations.",
        ("door surrounds", "shrine thresholds", "underwater grotto entries"),
    ),
    OrnamentMesh(
        "SM_Orn_GothicTracery", "Gothic_Tracery", "detail", "SpaceCathedral",
        "Interlaced gothic tracery panel with three vertical divisions.",
        ("window infill", "screen walls", "balcony rail inserts"),
    ),
    OrnamentMesh(
        "SM_Orn_DoorArchway", "Door_Archway", "detail", "BaroqueGrotto",
        "Pointed arch door frame with flanking pillar tubes.",
        ("gate thresholds", "interior door kits", "modular wall breaks"),
    ),
    OrnamentMesh(
        "SM_Orn_ColumnCapital", "Column_Capital", "detail", "BaroqueGrotto",
        "Corinthian-style bell capital with sixteen flared lobes.",
        ("column stacks", "porch kits", "ruin scatter"),
    ),
    OrnamentMesh(
        "SM_Orn_CrownMolding", "Crown_Molding", "detail", "BaroqueGrotto",
        "Swept crown molding segment with compound profile curves.",
        ("cornice runs", "throne dais trim", "interior entablature"),
    ),
    OrnamentMesh(
        "SM_Orn_CorbelBracket", "Corbel_Bracket", "detail", "BaroqueGrotto",
        "S-curve corbel bracket for wall-supported ledges.",
        ("balcony supports", "flying buttress accents", "shelf brackets"),
    ),
    OrnamentMesh(
        "SM_Orn_RosetteMedallion", "Rosette_Medallion", "detail", "SpaceCathedral",
        "Circular rosette with twelve overlapping petals.",
        ("ceiling bosses", "floor inlays", "wall medallions"),
    ),
    OrnamentMesh(
        "SM_Orn_FiligreeRing", "Filigree_Ring", "detail", "BaroqueGrotto",
        "Decorative filigree ring with twenty-four wave modulations.",
        ("chandelier rings", "portal halos", "celestial instrument frames"),
    ),
    OrnamentMesh(
        "SM_Orn_PendantFinial", "Pendant_Finial", "detail", "BaroqueGrotto",
        "Hanging pendant finial with ridged silhouette taper.",
        ("lantern drops", "curtain finials", "processional banners"),
    ),
    OrnamentMesh(
        "SM_Orn_TorusKnot", "TorusKnot_Ornament", "detail", "CosmicOrrery",
        "Ornamental torus knot (3,2) for cosmic surface decoration.",
        ("orrery hubs", "magic crests", "jewelry-scale scatter"),
    ),
    OrnamentMesh(
        "SM_Orn_WovenRing", "Woven_Ring", "detail", "CosmicOrrery",
        "Three-strand braided ring for orbital decoration.",
        ("planetarium rings", "gate trim", "celestial machinery"),
    ),
)

HERO_MESHES = tuple(m for m in MESHES if m.tier == "hero")
DETAIL_MESHES = tuple(m for m in MESHES if m.tier == "detail")

PACKAGE_CONTENTS = {
    "fbx": "15 FBX meshes with collision, 2 material slots (Base + Trim), 3 LODs",
    "unreal": "UE 5.8 project folder: StaticMeshes + optional PCG scatter graphs",
    "docs": "Installation README, world-scale notes, stylized material pairing guide",
    "bonus": "Demo level layout L_OrnamentKitbashShowcase (grid showcase)",
}

STORE_TAGS = (
    "kitbash", "ornament", "gothic", "baroque", "unreal-engine", "ue5",
    "environment-art", "modular", "cathedral", "fantasy", "stylized",
)

EXCLUDED_FROM_PACK = (
    {
        "name": "Greybox_Kit (SM_Greybox_*, SM_Block_*)",
        "reason": "Blockout primitives for layout — not finished ornamental art.",
        "path": f"{ENV}/Greybox_Kit",
    },
    {
        "name": "Surreal Architecture Gen meshes",
        "reason": "Blender GN output — separate surreal kitbash product lane.",
        "path": "deploy/surreal_architecture_gen.py",
    },
    {
        "name": "70_Japanese_Ornament_Alphas",
        "reason": "Licensed alpha texture pack — use in your own shaders; not redistributed.",
        "path": f"{ENV}/Textures_Shared/70_Japanese_Ornament_Alphas_vfxMed",
    },
    {
        "name": "Melodia game UI textures",
        "reason": "2D HUD / rhythm UI lane — not architectural mesh content.",
        "path": f"{ENV}/Textures/Melodia/GameUI",
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
        "excluded": EXCLUDED_FROM_PACK,
        "ue_paths": {
            "ornament_dir": ORNAMENT_DIR,
            "demo_level": DEMO_LEVEL,
            "pcg_hero": PCG_HERO_GRAPH,
            "pcg_detail": PCG_DETAIL_GRAPH,
        },
    }
