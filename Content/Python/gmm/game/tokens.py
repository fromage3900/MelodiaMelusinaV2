"""Melodia Token System — data structures and types.

Defines token types, wallet management, and integration points with the game system.
Uses existing Melody Token textures (Heart, Star, Swirl, Water) for visual variants.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Token Types
# ---------------------------------------------------------------------------

TOKEN_TYPES = {
    # Elemental energy shards using Melody Token textures
    "heart": {
        "display_name": "Forte Shard",
        "description": "Burn element energy - fuels attack skills",
        "element": "Forte",
        # Corrected 2026-08-01: the old path pointed at
        # melodsytoken_textures/MelodyToken_Heart_BaseColor, which does not exist. Heart's
        # textures live under melodsytoken/Textures/ and carry the T_ prefix, unlike the
        # other three variants.
        "texture_path": "/Game/EnvSandbox/Textures/melodsytoken/Textures/T_MelodyToken_Heart_BaseColor",
        "material_path": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart",
        "value": 10,
        "rarity": "common",
    },
    "star": {
        "display_name": "Radiant Shard",
        "description": "Radiant element energy - fuels light magic",
        "element": "Radiant",
        "texture_path": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Star_BaseColor",
        "material_path": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star",
        "value": 12,
        "rarity": "uncommon",
    },
    "swirl": {
        "display_name": "Arcane Shard",
        "description": "Arcane element energy - fuels mystic arts",
        "element": "Arcane",
        "texture_path": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Swirl_BaseColor",
        "material_path": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl",
        "value": 15,
        "rarity": "rare",
    },
    "water": {
        "display_name": "Tide Shard",
        "description": "Tide element energy - fuels healing and flow",
        "element": "Tide",
        "texture_path": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Water_BaseColor",
        "material_path": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water",
        "value": 12,
        "rarity": "common",
    },
}

# 2026-08-01: the authored variant material instances now exist, so star/swirl/water no
# longer declare `material_fallback: "heart"`. All four are built on
# M_Master_Toon_Universal (previously Heart was an orphaned glTF import with no parent at
# all), and star/swirl/water drive real parallax from their Displacement maps.

# Additional elemental types (use Heart texture as fallback)
EXTRA_ELEMENTAL_TYPES = {
    "stone": {"display_name": "Stone Shard", "element": "Stone", "value": 11, "rarity": "uncommon"},
    "gale": {"display_name": "Gale Shard", "element": "Gale", "value": 11, "rarity": "uncommon"},
    "umbral": {"display_name": "Umbral Shard", "element": "Umbral", "value": 13, "rarity": "rare"},
}

# The Unreal DataAsset is canonical; this published mirror keeps the offline Python model
# and its tests in agreement with the editor-owned catalog. The literals above remain a
# bootstrap fallback for a partial checkout, but a present mirror always wins.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
TOKEN_CATALOG_PATH = PROJECT_ROOT / "specs" / "economy" / "melodia_token_catalog.v1.json"
TOKEN_SOURCE = ""


def _load_token_catalog() -> None:
    """Overlay token definitions from the canonical text mirror when it exists."""
    global EXTRA_ELEMENTAL_TYPES, TOKEN_SOURCE, TOKEN_TYPES

    if not TOKEN_CATALOG_PATH.exists():
        return

    with TOKEN_CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)

    if catalog.get("schema") != "melodia_token_catalog.v1":
        raise ValueError(f"Unsupported token catalog schema in {TOKEN_CATALOG_PATH}")

    rows = catalog.get("tokens")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Token catalog has no token rows: {TOKEN_CATALOG_PATH}")

    TOKEN_TYPES = {
        str(row["variant_id"]): dict(row)
        for row in rows
        if row.get("variant_id")
    }
    EXTRA_ELEMENTAL_TYPES = {
        str(row["variant_id"]): dict(row)
        for row in (catalog.get("extra_elemental_types") or [])
        if row.get("variant_id")
    }
    TOKEN_SOURCE = str(TOKEN_CATALOG_PATH)


_load_token_catalog()

# ---------------------------------------------------------------------------
# Token Definitions
# ---------------------------------------------------------------------------

@dataclass
class MelodiaTokenDef:
    """Token definition for a collectible item."""
    token_id: str
    display_name: str
    description: str = ""
    element: str = ""  # Elemental type this token represents
    value: int = 10    # Energy value or currency amount
    rarity: str = "common"  # common, uncommon, rare, epic, legendary
    texture_path: str = ""
    material_path: str = ""
    material_fallback: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TokenWallet:
    """Player token inventory."""
    # Energy shards by element
    shards: dict[str, int] = field(default_factory=lambda: {e: 0 for e in [
        "Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"
    ]})
    
    # Mana (regenerating energy)
    mana_current: float = 50.0
    mana_max: float = 100.0
    
    # Currency tokens
    golden_tokens: int = 0
    
    # Token count
    total_collected: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def add_shard(self, element: str, amount: int = 1) -> int:
        """Add elemental shards. Returns new total."""
        if element not in self.shards:
            self.shards[element] = 0
        self.shards[element] += amount
        self.total_collected += amount
        return self.shards[element]
    
    def spend_shard(self, element: str, amount: int = 1) -> bool:
        """Spend elemental shards. Returns True if successful."""
        if self.shards.get(element, 0) >= amount:
            self.shards[element] -= amount
            return True
        return False
    
    def add_mana(self, amount: float) -> float:
        """Add mana. Returns new current value."""
        self.mana_current = min(self.mana_max, self.mana_current + amount)
        return self.mana_current
    
    def spend_mana(self, amount: float) -> bool:
        """Spend mana. Returns True if successful."""
        if self.mana_current >= amount:
            self.mana_current -= amount
            return True
        return False
    
    def add_golden(self, amount: int = 1) -> int:
        """Add golden tokens (currency). Returns new total."""
        self.golden_tokens += amount
        return self.golden_tokens
    
    def spend_golden(self, amount: int = 1) -> bool:
        """Spend golden tokens. Returns True if successful."""
        if self.golden_tokens >= amount:
            self.golden_tokens -= amount
            return True
        return False


def get_token_def(token_id: str) -> Optional[MelodiaTokenDef]:
    """Get token definition by ID."""
    data = TOKEN_TYPES.get(token_id) or EXTRA_ELEMENTAL_TYPES.get(token_id)
    if not data:
        return None
    return MelodiaTokenDef(
        token_id=token_id,
        display_name=data.get("display_name", token_id),
        description=data.get("description", ""),
        element=data.get("element", ""),
        value=data.get("value", 10),
        rarity=data.get("rarity", "common"),
        texture_path=data.get("texture_path", ""),
        material_path=data.get("material_path", ""),
        material_fallback=data.get("material_fallback", ""),
    )


def list_token_defs() -> list[MelodiaTokenDef]:
    """Get all token definitions."""
    result = []
    for tid, data in TOKEN_TYPES.items():
        result.append(MelodiaTokenDef(
            token_id=tid,
            display_name=data.get("display_name", tid),
            description=data.get("description", ""),
            element=data.get("element", ""),
            value=data.get("value", 10),
            rarity=data.get("rarity", "common"),
            texture_path=data.get("texture_path", ""),
            material_path=data.get("material_path", ""),
            material_fallback=data.get("material_fallback", ""),
        ))
    for tid, data in EXTRA_ELEMENTAL_TYPES.items():
        result.append(MelodiaTokenDef(
            token_id=tid,
            display_name=data.get("display_name", tid),
            description=data.get("description", ""),
            element=data.get("element", ""),
            value=data.get("value", 10),
            rarity=data.get("rarity", "common"),
        ))
    return result


def token_system_summary() -> dict:
    """Get summary of token system."""
    return {
        "total_types": len(TOKEN_TYPES) + len(EXTRA_ELEMENTAL_TYPES),
        "elements_covered": list(set(t["element"] for t in TOKEN_TYPES.values() if t.get("element")) | 
                               set(t["element"] for t in EXTRA_ELEMENTAL_TYPES.values() if t.get("element"))),
        "rarity_counts": {
            "common": sum(1 for t in TOKEN_TYPES.values() if t.get("rarity") == "common") +
                      sum(1 for t in EXTRA_ELEMENTAL_TYPES.values() if t.get("rarity") == "common"),
            "uncommon": sum(1 for t in TOKEN_TYPES.values() if t.get("rarity") == "uncommon") +
                        sum(1 for t in EXTRA_ELEMENTAL_TYPES.values() if t.get("rarity") == "uncommon"),
            "rare": sum(1 for t in TOKEN_TYPES.values() if t.get("rarity") == "rare") +
                    sum(1 for t in EXTRA_ELEMENTAL_TYPES.values() if t.get("rarity") == "rare"),
        },
    }
