"""Party System — companion management for Melodia rhythm battle.

Provides:
- Party formation and member management
- Companion stats integration
- Battle slot assignment
- Party UI state

Usage:
    from gmm.game.party import Party, PartyMember
    party = Party()
    party.add_member(companion_stats)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartyMember:
    """A companion in the player's party."""
    member_id: str
    character_name: str
    archetype: str  # "SakuraDreamer", "CosmicWeaver", "MirageDancer"
    level: int = 1
    max_hp: float = 80.0
    hp: float = 80.0
    max_sp: float = 50.0
    sp: float = 50.0
    speed: int = 85
    element: str = "Forte"  # Primary element affinity
    
    # Skills available to this companion
    unlocked_skills: list[str] = field(default_factory=list)
    
    # Battle position (1-4)
    battle_position: int = 0
    
    # Equipment slots (limited compared to player)
    equipped_weapon: Optional[str] = None
    equipped_utility: Optional[str] = None  # Instead of full armor set
    
    def to_dict(self) -> dict:
        return {
            "member_id": self.member_id,
            "character_name": self.character_name,
            "archetype": self.archetype,
            "level": self.level,
            "hp": f"{self.hp:.0f}/{self.max_hp:.0f}",
            "sp": f"{self.sp:.0f}/{self.max_sp:.0f}",
            "speed": self.speed,
            "element": self.element,
            "skills": self.unlocked_skills,
            "battle_position": self.battle_position,
        }
    
    def is_alive(self) -> bool:
        return self.hp > 0
    
    def take_damage(self, amount: float) -> float:
        actual = max(0, amount - 5)  # Basic defense
        self.hp = max(0, self.hp - actual)
        return actual
    
    def heal(self, amount: float) -> float:
        healed = min(self.max_hp - self.hp, amount)
        self.hp = min(self.max_hp, self.hp + amount)
        return healed


class Party:
    """Player's party of companions.
    
    Maximum 3 companions in addition to player.
    """
    
    MAX_SIZE: int = 3
    
    def __init__(self):
        self.members: list[PartyMember] = []
        self.leader: Optional[PartyMember] = None  # Usually player
    
    def add_member(self, member: PartyMember) -> bool:
        """Add a companion to the party."""
        if len(self.members) >= self.MAX_SIZE:
            return False
        if member.member_id in [m.member_id for m in self.members]:
            return False
        self.members.append(member)
        return True
    
    def remove_member(self, member_id: str) -> Optional[PartyMember]:
        """Remove a companion from the party."""
        for i, m in enumerate(self.members):
            if m.member_id == member_id:
                return self.members.pop(i)
        return None
    
    def get_member(self, member_id: str) -> Optional[PartyMember]:
        """Get a party member by ID."""
        for m in self.members:
            if m.member_id == member_id:
                return m
        return None
    
    def set_battle_positions(self):
        """Assign battle positions to all members."""
        for i, m in enumerate(self.members):
            m.battle_position = i + 1
    
    def alive_members(self) -> list[PartyMember]:
        """Get all living party members."""
        return [m for m in self.members if m.is_alive()]
    
    def active_battlers(self) -> list[PartyMember]:
        """Get members available for battle (alive)."""
        return self.alive_members()
    
    def to_dict(self) -> dict:
        return {
            "size": len(self.members),
            "max_size": self.MAX_SIZE,
            "members": [m.to_dict() for m in self.members],
            "alive_count": len(self.alive_members()),
        }


# -----------------------------------------------------------------------------
# Companion Archetypes
# -----------------------------------------------------------------------------

COMPANION_ARCHETYPES = {
    "SakuraDreamer": {
        "display_name": "Sakura Dreamer",
        "description": "Healer support with Forte/Tide magic",
        "element": "Forte",
        "base_stats": {"hp": 85, "sp": 60, "speed": 80},
    },
    "CosmicWeaver": {
        "display_name": "Cosmic Weaver",
        "description": "High magic damage with Arcane/Radiant spells",
        "element": "Arcane",
        "base_stats": {"hp": 70, "sp": 80, "speed": 75},
    },
    "MirageDancer": {
        "display_name": "Mirage Dancer",
        "description": "Fast attacker with Gale/Umbral abilities",
        "element": "Gale",
        "base_stats": {"hp": 75, "sp": 65, "speed": 100},
    },
}


def create_companion(
    companion_id: str,
    archetype: str,
    level: int = 1,
) -> Optional[PartyMember]:
    """Create a companion from archetype."""
    archetype_data = COMPANION_ARCHETYPES.get(archetype)
    if not archetype_data:
        return None
    
    stats = archetype_data["base_stats"]
    return PartyMember(
        member_id=companion_id,
        character_name=archetype_data["display_name"],
        archetype=archetype,
        level=level,
        max_hp=stats["hp"] * level,
        hp=stats["hp"] * level,
        max_sp=stats["sp"] * level,
        sp=stats["sp"] * level,
        speed=stats["speed"],
        element=archetype_data["element"],
    )


def party_system_summary() -> dict:
    """Get summary of the party system."""
    return {
        "max_party_size": Party.MAX_SIZE,
        "archetypes": list(COMPANION_ARCHETYPES.keys()),
        "archetype_details": COMPANION_ARCHETYPES,
    }