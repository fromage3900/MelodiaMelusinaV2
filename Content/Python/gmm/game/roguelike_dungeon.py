"""Offline ProceduralDungeon fixture authoring for MelodiaCore.

MelodiaCore builds every shipping stage recipe. This module only validates catalogs,
simulates distributions, and emits RoomData-compatible fixtures for import. It is
never called by ADungeonGenerator, Blueprint runtime logic, or packaged gameplay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import random

from gmm.game.roguelike import (
    ROOM_TEMPLATES,
    ARTIFACTS,
    BLESSINGS,
    RoomTemplate,
    Artifact,
    Blessing,
    FloorState,
    RunState,
    generate_floor,
    select_random_enemy,
)


# =============================================================================
# ProceduralDungeon ↔ GMM Bridge Types
# =============================================================================

class DungeonRoomType(Enum):
    """Room type classification for ProceduralDungeon RoomData mapping."""
    START = auto()
    STANDARD = auto()
    ELITE = auto()
    BOSS = auto()
    SHOP = auto()
    TREASURE = auto()
    EVENT = auto()       # Nikki photo-spot / story vignette
    BLESSING = auto()    # Meta-progression altar room


@dataclass
class DungeonRoomSpec:
    """Specification for creating a ProceduralDungeon RoomData asset.

    Maps a GMM roguelike RoomTemplate to the data needed for a URoomData.
    """
    room_data_name: str          # e.g. "RD_WhisperingGrove_Standard"
    room_type: DungeonRoomType
    level_path: str              # e.g. "/Game/Melodia/Roguelike/Rooms/L_WhisperingGrove"
    display_name: str
    enemy_pool: list[str]        # Enemy IDs that can spawn here
    floor_tier_min: int = 1      # Minimum floor for this room variant
    floor_tier_max: int = 99
    door_positions: list[tuple[int, int, int]] = field(default_factory=list)  # FDoorDef positions
    nikki_archetype: str = ""    # "SakuraDreamer", "CosmicWeaver", "MirageDancer" — sets NPC + visual theme
    room_variant: int = 1        # 1-5 visual variants for variety
    photo_spot: bool = False     # Marked as Infinity Nikki photo-worthy
    golden_token_cost: int = 0   # For shop rooms: entry cost
    population: str = ""         # ZonePopulation reference for NPC spawning


# =============================================================================
# Infinite Nikki Style Themes — mapped to DungeonRoomType
# =============================================================================

NIKKI_ROOM_THEMES: dict[DungeonRoomType, dict] = {
    DungeonRoomType.START: {
        "archetype": "SakuraDreamer",
        "ppv": "PPV_NikkiDream",
        "lighting": "Lights_Nikki",
        "mood": "soft_dawn",
        "description": "Melodia Grove — the dream begins",
    },
    DungeonRoomType.STANDARD: {
        "archetype": "SakuraDreamer",
        "ppv": "PPV_NikkiDream",
        "lighting": "Lights_Nikki",
        "mood": "pastel_day",
        "description": "Whispering Grove — gentle encounters",
    },
    DungeonRoomType.ELITE: {
        "archetype": "CosmicWeaver",
        "ppv": "PPV_CosmicDream",
        "lighting": "Lights_Nikki",
        "mood": "twilight_tension",
        "description": "Everburning Clearing — dangerous beauty",
    },
    DungeonRoomType.BOSS: {
        "archetype": "MirageDancer",
        "ppv": "PPV_DreamBloom",
        "lighting": "Lights_Jewelry",
        "mood": "dramatic_night",
        "description": "Boss Arena — the climactic stage",
    },
    DungeonRoomType.SHOP: {
        "archetype": "SakuraDreamer",
        "ppv": "PPV_NikkiDream",
        "lighting": "Lights_Nikki",
        "mood": "cozy_interior",
        "description": "Token Shrine — rest and trade",
    },
    DungeonRoomType.TREASURE: {
        "archetype": "CosmicWeaver",
        "ppv": "PPV_CosmicDream",
        "lighting": "Lights_Jewelry",
        "mood": "hidden_sparkle",
        "description": "Abandoned Cache — guarded riches",
    },
    DungeonRoomType.EVENT: {
        "archetype": "MirageDancer",
        "ppv": "PPV_DreamBloom",
        "lighting": "Lights_Silhouette",
        "mood": "photo_spot",
        "description": "Photo Spot — a moment of beauty",
    },
    DungeonRoomType.BLESSING: {
        "archetype": "CosmicWeaver",
        "ppv": "PPV_CosmicDream",
        "lighting": "Lights_Jewelry",
        "mood": "sacred_glow",
        "description": "Blessing Altar — permanent power",
    },
}


# =============================================================================
# Roguelike Room Registry
# =============================================================================

class RoguelikeRoomRegistry:
    """Maps GMM roguelike room templates to ProceduralDungeon RoomData specs.

    This is the central registry that ProceduralDungeon's ChooseNextRoomData
    consults to pick the correct RoomData asset for each dungeon node.

    In production, this pulls from Unreal's asset registry. In GMM standalone,
    it uses the in-memory spec catalog.
    """

    def __init__(self):
        self._specs: dict[str, DungeonRoomSpec] = {}
        self._specs_by_type: dict[DungeonRoomType, list[DungeonRoomSpec]] = {
            t: [] for t in DungeonRoomType
        }
        self._init_catalog()

    def _init_catalog(self):
        """Build the initial room spec catalog from GMM roguelike templates."""
        # Map GMM room_id → DungeonRoomType
        type_map = {
            "start": DungeonRoomType.START,
            "standard": DungeonRoomType.STANDARD,
            "elite": DungeonRoomType.ELITE,
            "boss": DungeonRoomType.BOSS,
            "shop": DungeonRoomType.SHOP,
            "treasure": DungeonRoomType.TREASURE,
        }

        for room_id, template in ROOM_TEMPLATES.items():
            room_type = type_map.get(room_id, DungeonRoomType.STANDARD)
            theme = NIKKI_ROOM_THEMES.get(room_type, NIKKI_ROOM_THEMES[DungeonRoomType.STANDARD])

            # 3 visual variants per room type for variety
            for variant in range(1, 4):
                spec = DungeonRoomSpec(
                    room_data_name=f"RD_{template.display_name.replace(' ', '')}_V{variant}",
                    room_type=room_type,
                    level_path=f"/Game/Melodia/Roguelike/Rooms/L_{template.display_name.replace(' ', '')}_V{variant}",
                    display_name=f"{template.display_name} (Variant {variant})",
                    enemy_pool=list(template.enemy_pool),
                    door_positions=_generate_door_positions(room_id),
                    nikki_archetype=theme["archetype"],
                    room_variant=variant,
                    photo_spot=(room_type == DungeonRoomType.EVENT),
                    population=f"Population_{template.display_name}",
                )
                key = f"{room_id}_v{variant}"
                self._specs[key] = spec
                self._specs_by_type[room_type].append(spec)

        # Add dedicated Blessing room
        for variant in range(1, 3):
            spec = DungeonRoomSpec(
                room_data_name=f"RD_BlessingAltar_V{variant}",
                room_type=DungeonRoomType.BLESSING,
                level_path=f"/Game/Melodia/Roguelike/Rooms/L_BlessingAltar_V{variant}",
                display_name=f"Blessing Altar (Variant {variant})",
                enemy_pool=[],
                door_positions=_generate_door_positions("blessing"),
                nikki_archetype="CosmicWeaver",
                room_variant=variant,
            )
            key = f"blessing_v{variant}"
            self._specs[key] = spec
            self._specs_by_type[DungeonRoomType.BLESSING].append(spec)

        # Add dedicated Event/Photo-Spot room
        for variant in range(1, 3):
            spec = DungeonRoomSpec(
                room_data_name=f"RD_PhotoSpot_V{variant}",
                room_type=DungeonRoomType.EVENT,
                level_path=f"/Game/Melodia/Roguelike/Rooms/L_PhotoSpot_V{variant}",
                display_name=f"Starlight Reverie (Variant {variant})",
                enemy_pool=[],
                door_positions=_generate_door_positions("event"),
                nikki_archetype="MirageDancer",
                room_variant=variant,
                photo_spot=True,
            )
            key = f"event_v{variant}"
            self._specs[key] = spec
            self._specs_by_type[DungeonRoomType.EVENT].append(spec)

    def get_spec(self, room_data_name: str) -> Optional[DungeonRoomSpec]:
        return self._specs.get(room_data_name)

    def get_specs_for_type(self, room_type: DungeonRoomType) -> list[DungeonRoomSpec]:
        return self._specs_by_type.get(room_type, [])

    def get_specs_for_room_id(self, room_id: str, variant: int = 1) -> list[DungeonRoomSpec]:
        key = f"{room_id}_v{variant}"
        spec = self._specs.get(key)
        return [spec] if spec else []

    def get_start_room_spec(self) -> DungeonRoomSpec:
        specs = self._specs_by_type[DungeonRoomType.START]
        return specs[0] if specs else None

    def get_boss_room_specs(self) -> list[DungeonRoomSpec]:
        return self._specs_by_type[DungeonRoomType.BOSS]

    def get_elite_room_specs(self) -> list[DungeonRoomSpec]:
        return self._specs_by_type[DungeonRoomType.ELITE]

    def get_standard_room_specs(self) -> list[DungeonRoomSpec]:
        return self._specs_by_type[DungeonRoomType.STANDARD]

    def get_shop_room_specs(self) -> list[DungeonRoomSpec]:
        return self._specs_by_type[DungeonRoomType.SHOP]

    def all_specs(self) -> list[DungeonRoomSpec]:
        return list(self._specs.values())

    def summary(self) -> dict:
        return {
            "total_specs": len(self._specs),
            "by_type": {
                t.name: len(specs) for t, specs in self._specs_by_type.items()
            },
            "nikki_themes": {
                t.name: NIKKI_ROOM_THEMES[t]["description"]
                for t in NIKKI_ROOM_THEMES
            },
        }


# =============================================================================
# Floor Graph Generation (for ProceduralDungeon)
# =============================================================================

@dataclass
class FloorGraphNode:
    """Node in the dungeon floor graph — feeds ProceduralDungeon.

    Each node maps to one URoom placed by ProceduralDungeon's generator.
    The room_data_name points to a URoomData asset in the asset registry.
    """
    node_id: int
    room_data_name: str
    floor_number: int
    is_boss: bool = False
    is_start: bool = False
    connections: list[int] = field(default_factory=list)  # node_ids this connects to


@dataclass
class FloorGraph:
    """A full dungeon floor graph — feeds ADungeonGenerator.

    Contains nodes and edges representing room placement.
    The DungeonGenerator uses this to determine room order and connections.
    """
    floor_number: int
    seed: int
    nodes: list[FloorGraphNode] = field(default_factory=list)
    start_node_id: int = 0

    def to_dict(self) -> dict:
        return {
            "floor_number": self.floor_number,
            "seed": self.seed,
            "start_node_id": self.start_node_id,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "room_data_name": n.room_data_name,
                    "floor_number": n.floor_number,
                    "is_boss": n.is_boss,
                    "is_start": n.is_start,
                    "connections": n.connections,
                }
                for n in self.nodes
            ],
        }


def _generate_door_positions(room_id: str) -> list[tuple[int, int, int]]:
    """Generate FDoorDef positions for a room type.

    ProceduralDungeon rooms need at least 1 door. Standard rooms get N/S/E/W doors.
    Boss rooms get only a South entrance. Start gets only a North exit.
    Shop/Treasure get N/S.
    """
    door_sets = {
        "start": [(0, 1, 0)],                          # North exit only
        "standard": [
            (0, 1, 0),   # North
            (0, -1, 0),  # South
            (1, 0, 0),   # East
            (-1, 0, 0),  # West
        ],
        "elite": [
            (0, 1, 0),   # North
            (0, -1, 0),  # South
            (1, 0, 0),   # East
            (-1, 0, 0),  # West
        ],
        "boss": [(0, -1, 0)],                          # South entrance only
        "shop": [(0, 1, 0), (0, -1, 0)],               # N/S
        "treasure": [(0, 1, 0), (0, -1, 0)],           # N/S
        "blessing": [(0, 1, 0)],                        # Entrance only
        "event": [(0, 1, 0), (0, -1, 0)],              # N/S
    }
    return door_sets.get(room_id, [(0, 1, 0)])


def generate_floor_graph_for_dungeon(
    floor_number: int,
    seed: int | None = None,
    registry: Optional[RoguelikeRoomRegistry] = None,
) -> FloorGraph:
    """Generate a full floor graph compatible with ProceduralDungeon.

    Translates the linear GMM generate_floor() output into a graph of
    FloorGraphNodes that map to specific RoomData assets and define
    door connections between rooms.

    Args:
        floor_number: Current floor (1-indexed)
        seed: Deterministic seed for reproducibility
        registry: Room spec registry (created if None)

    Returns:
        FloorGraph with nodes, connections, and start node marked.
    """
    if seed is not None:
        random.seed(seed + floor_number)

    if registry is None:
        registry = RoguelikeRoomRegistry()

    graph = FloorGraph(floor_number=floor_number, seed=seed or 0)

    # Get the linear room sequence from GMM
    room_ids = generate_floor(floor_number, seed)

    # Build graph nodes
    node_id_counter = 0
    for i, room_id in enumerate(room_ids):
        is_boss = (room_id == "boss")
        is_start = (i == 0)

        # Pick a random visual variant for variety
        variant = random.randint(1, 3)
        specs = registry.get_specs_for_room_id(room_id, variant)
        if not specs:
            # Fallback to any variant
            specs = registry.get_specs_for_room_id(room_id, 1)

        if specs:
            room_data_name = specs[0].room_data_name
        else:
            room_data_name = f"RD_{room_id}_V1"

        node = FloorGraphNode(
            node_id=node_id_counter,
            room_data_name=room_data_name,
            floor_number=floor_number,
            is_boss=is_boss,
            is_start=is_start,
        )

        # Connect in sequence (linear path) with optional branches
        # Node i connects to node i+1 (forward path)
        if i < len(room_ids) - 1:
            node.connections.append(node_id_counter + 1)

        # Node i+1 connects back to node i (backtracking allowed)
        if i > 0:
            # Previous node already has forward connection to us,
            # but we add a reciprocal connection for back-tracking visibility
            prev_node = graph.nodes[i - 1]
            if node_id_counter not in prev_node.connections:
                prev_node.connections.append(node_id_counter)

        graph.nodes.append(node)
        node_id_counter += 1

        # Mark start
        if is_start:
            graph.start_node_id = node.node_id

    return graph


# =============================================================================
# Room Population — Enemy & NPC Configuration
# =============================================================================

@dataclass
class RoomEncounterConfig:
    """Encounter configuration for a single room.

    Maps to EncounterTrigger properties in the room level.
    Used by BP_RoguelikeDungeonGenerator::OnRoomAdded to auto-configure.
    """
    room_data_name: str
    enemy_id: str         # Primary enemy for this room
    enemy_level: int      # Scaled by floor
    minion_ids: list[str] = field(default_factory=list)  # Wave support
    npc_ids: list[str] = field(default_factory=list)     # NPCs to spawn
    encounter_label: str = ""
    encounter_light_color: tuple[float, float, float] = (1.0, 0.84, 0.38)  # Gold default
    b_one_shot: bool = True
    cooldown_seconds: float = 5.0


def generate_encounter_config(
    room_data_name: str,
    room_id: str,
    floor_number: int,
    seed: int | None = None,
) -> RoomEncounterConfig:
    """Generate encounter config for a room based on its type and floor.

    Integrates the Nikki aesthetic:
    - SakuraDreamer rooms → soft gold lighting, healing/support enemies
    - CosmicWeaver rooms → violet lighting, high-HP enemies
    - MirageDancer rooms → cyan lighting, fast enemies
    """
    if seed is not None:
        random.seed(seed + floor_number)

    template = ROOM_TEMPLATES.get(room_id)
    if not template:
        return RoomEncounterConfig(
            room_data_name=room_data_name,
            enemy_id="CrystalShard",
            enemy_level=floor_number,
            encounter_label=room_data_name,
        )

    enemy_id = select_random_enemy(room_id, seed)
    if not enemy_id:
        enemy_id = "CrystalShard"

    # Light color based on Nikki archetype theme
    if room_id == "boss":
        light_color = (1.0, 0.46, 0.84)  # Pink — MirageDancer / dramatic
    elif room_id == "elite":
        light_color = (0.46, 0.36, 1.0)  # Violet — CosmicWeaver
    elif room_id == "shop":
        light_color = (0.86, 0.74, 1.0)  # Lavender — gentle shop
    elif room_id == "treasure":
        light_color = (0.98, 0.82, 0.38)  # Gold — treasure glow
    else:
        light_color = (1.0, 0.54, 0.72)  # Pink — SakuraDreamer

    return RoomEncounterConfig(
        room_data_name=room_data_name,
        enemy_id=enemy_id,
        enemy_level=floor_number,
        encounter_label=template.display_name,
        encounter_light_color=light_color,
        b_one_shot=(room_id != "standard"),  # Standard rooms can respawn
    )


# =============================================================================
# Run State Persistence (across ProceduralDungeon floors)
# =============================================================================

@dataclass
class RoguelikeRunSession:
    """Persistent roguelike session spanning ProceduralDungeon floor changes.

    Survives:
    - Room-to-room transitions (same floor, same dungeon instance)
    - Floor-to-floor transitions (dungeon unload → regenerate → load new floor)
    - Act transitions (multi-floor progression)

    Stored in UGameInstanceSubsystem (like UMelodiaBattleSession).
    """
    run_state: RunState = field(default_factory=RunState)
    dungeon_seed: int = 0
    current_floor_node_id: int = 0
    rooms_cleared_this_floor: int = 0
    discovered_room_ids: list[str] = field(default_factory=list)  # RoomData names visited

    def advance_floor(self):
        """Called when player reaches exit node (boss room cleared)."""
        self.run_state.current_floor.floor_number += 1
        self.run_state.current_floor.rooms_cleared += self.rooms_cleared_this_floor
        self.rooms_cleared_this_floor = 0
        self.current_floor_node_id = 0

    def record_room_cleared(self, room_data_name: str):
        self.rooms_cleared_this_floor += 1
        if room_data_name not in self.discovered_room_ids:
            self.discovered_room_ids.append(room_data_name)

    def grant_artifact(self, artifact_id: str) -> bool:
        """Grant a mid-run artifact. Returns True if new."""
        if artifact_id in self.run_state.artifacts:
            return False
        self.run_state.artifacts.append(artifact_id)
        return True

    def has_artifact(self, artifact_id: str) -> bool:
        return artifact_id in self.run_state.artifacts

    def spend_golden_tokens(self, amount: int) -> bool:
        wallet = self.run_state.player.token_wallet
        if wallet.golden_tokens >= amount:
            wallet.golden_tokens -= amount
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "run_state": self.run_state.to_dict(),
            "dungeon_seed": self.dungeon_seed,
            "current_floor_node_id": self.current_floor_node_id,
            "rooms_cleared_this_floor": self.rooms_cleared_this_floor,
            "discovered_room_ids": self.discovered_room_ids,
        }


# =============================================================================
# Shop Generation
# =============================================================================

@dataclass
class ShopInventory:
    """Generated shop inventory for a floor."""
    floor_number: int
    golden_tokens_held: int
    artifacts_for_sale: list[tuple[str, int]] = field(default_factory=list)  # (artifact_id, price)
    blessing_available: list[str] = field(default_factory=list)  # blessing_ids affordable
    reroll_cost: int = 0

    def to_dict(self) -> dict:
        return {
            "floor_number": self.floor_number,
            "golden_tokens_held": self.golden_tokens_held,
            "artifacts_for_sale": [
                {"id": aid, "price": price, "name": ARTIFACTS[aid].display_name}
                for aid, price in self.artifacts_for_sale
            ],
            "blessing_available": [
                {"id": bid, "name": BLESSINGS[bid].display_name, "cost": BLESSINGS[bid].token_cost}
                for bid in self.blessing_available
            ],
            "reroll_cost": self.reroll_cost,
        }


def generate_shop_inventory(
    floor_number: int,
    golden_tokens_held: int,
    seed: int | None = None,
    reroll_count: int = 0,
) -> ShopInventory:
    """Generate shop inventory for a token shrine room.

    Artifact selection weighted by floor tier:
    - Floors 1-4: common artifacts (Burning Chord, Echoing Beat)
    - Floors 5-9: uncommon added (Swift Tempo, Stone Carapace)
    - Floors 10+: all artifacts available

    Pricing scales: base_cost * (1.0 + floor * 0.05)
    Reroll cost: 1 + floor // 3 + reroll_count
    """
    if seed is not None:
        random.seed(seed + floor_number + reroll_count * 1000)

    # Determine available pool by floor tier
    if floor_number < 5:
        pool = ["BurningChord", "EchoingBeat"]
    elif floor_number < 10:
        pool = list(ARTIFACTS.keys())
    else:
        pool = list(ARTIFACTS.keys())

    # Select 3 random artifacts (or all if pool < 3)
    selected = random.sample(pool, min(3, len(pool)))

    artifacts_for_sale = []
    for aid in selected:
        artifact = ARTIFACTS[aid]
        base_price = artifact.cost_golden_tokens
        # Scale: 5% per floor, rounded up
        scaled_price = int(base_price * (1.0 + floor_number * 0.05) + 0.5)
        artifacts_for_sale.append((aid, max(1, scaled_price)))

    # Check which blessings the player can afford
    blessing_available = [
        bid for bid, blessing in BLESSINGS.items()
        if blessing.token_cost <= golden_tokens_held
    ]

    reroll_cost = 1 + floor_number // 3 + reroll_count

    return ShopInventory(
        floor_number=floor_number,
        golden_tokens_held=golden_tokens_held,
        artifacts_for_sale=artifacts_for_sale,
        blessing_available=blessing_available,
        reroll_cost=reroll_cost,
    )


# =============================================================================
# Difficulty Scaling (Ascension / Dissonance system)
# =============================================================================

def scale_enemy_for_floor(
    base_hp: float,
    base_toughness: float,
    base_damage: float,
    floor_number: int,
    ascension_level: int = 0,
) -> tuple[float, float, float]:
    """Scale enemy stats for a given floor and ascension level.

    Scaling formula: base * (1.0 + (floor - 1) * 0.08) * (1.0 + ascension * 0.15)

    Floor scaling:
        Floor 1:  1.00x
        Floor 5:  1.32x
        Floor 10: 1.72x
        Floor 20: 2.52x

    With Ascension 3:
        Floor 1:  1.45x
        Floor 5:  1.91x
        Floor 10: 2.49x
    """
    floor_mult = 1.0 + (floor_number - 1) * 0.08
    ascension_mult = 1.0 + ascension_level * 0.15

    total_mult = floor_mult * ascension_mult

    return (
        base_hp * total_mult,
        base_toughness * (1.0 + (floor_number - 1) * 0.04) * (1.0 + ascension_level * 0.10),
        base_damage * total_mult * 0.8,  # Damage scales slightly slower than HP
    )


# =============================================================================
# Room Reward Calculation (Victory → Tokens)
# =============================================================================

@dataclass
class RoomReward:
    """Rewards granted after clearing a room."""
    golden_tokens: int = 0
    mana_regen: float = 0.0
    elemental_shards: dict[str, int] = field(default_factory=dict)
    bonus_artifact_chance: float = 0.0  # 0.0 - 1.0
    blessing_discount: int = 0  # Temporary discount on next blessing purchase


def calculate_room_rewards(
    room_id: str,
    floor_number: int,
    grade_counts: dict[str, int],  # {"perfect": N, "great": N, "good": N, "miss": N}
    max_combo: int,
    seed: int | None = None,
) -> RoomReward:
    """Calculate token/economy rewards for clearing a room.

    Rewards scale with:
    - Room type (boss > elite > treasure > standard)
    - Floor number
    - Performance (grade distribution, max combo)
    - Ascension level (applied separately in RunState)
    """
    if seed is not None:
        random.seed(seed + floor_number)

    reward = RoomReward()

    # Base golden tokens by room type
    type_tokens = {
        "start": 0,
        "standard": 1,
        "elite": 2,
        "boss": 3,
        "treasure": 2,
        "shop": 0,
    }
    base_tokens = type_tokens.get(room_id, 1)

    # Performance bonus
    perfect_count = grade_counts.get("perfect", 0)
    total_hits = sum(grade_counts.values())
    if total_hits > 0:
        perfect_ratio = perfect_count / total_hits
    else:
        perfect_ratio = 0

    # Combo bonus: 1 extra token per 10 combo
    combo_bonus = max_combo // 10

    # Floor bonus: 1 extra token per 5 floors
    floor_bonus = (floor_number - 1) // 5

    reward.golden_tokens = base_tokens + combo_bonus + floor_bonus

    # Perfect bonus: chance for extra token
    if perfect_ratio > 0.5:
        reward.golden_tokens += 1

    # Mana regen
    reward.mana_regen = 20.0 * (1.0 + perfect_ratio * 0.5 + (floor_number - 1) * 0.02)

    # Elemental shard drop (based on enemy element, randomized here as placeholder)
    # In production, this uses the defeated enemy's element
    elements = ["Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"]
    shard_element = random.choice(elements)
    shard_count = 1 + (max_combo // 5)
    reward.elemental_shards[shard_element] = shard_count

    # Bonus artifact chance from elite/boss rooms
    if room_id == "elite":
        reward.bonus_artifact_chance = 0.15  # 15% chance
    elif room_id == "boss":
        reward.bonus_artifact_chance = 0.50  # 50% chance — guaranteed drop feel

    return reward


# =============================================================================
# Utility / Debug
# =============================================================================

def dungeon_system_summary() -> dict:
    """Complete summary of the roguelike dungeon integration system."""
    registry = RoguelikeRoomRegistry()

    return {
        "ok": True,
        "version": "1.0.0",
        "systems": {
            "procedural_dungeon": {
                "version": "3.8.3",
                "status": "installed",
                "path": "Plugins/ProceduralDungeon/",
                "ue58_compatible": True,
            },
            "gmm_roguelike": {
                "room_templates": len(ROOM_TEMPLATES),
                "artifacts": len(ARTIFACTS),
                "blessings": len(BLESSINGS),
            },
            "nikki_aesthetic": {
                "archetypes": ["SakuraDreamer", "CosmicWeaver", "MirageDancer"],
                "room_themes": len(NIKKI_ROOM_THEMES),
                "post_process": ["PPV_NikkiDream", "PPV_CosmicDream", "PPV_DreamBloom"],
                "lighting": ["Lights_Nikki", "Lights_Jewelry", "Lights_Silhouette"],
            },
        },
        "room_registry": registry.summary(),
        "integration_points": [
            "ADungeonGenerator::ChooseFirstRoomData → RoguelikeRoomRegistry.get_start_room_spec()",
            "ADungeonGenerator::ChooseNextRoomData → generate_floor() + RoomData lookup",
            "ADungeonGenerator::OnRoomAdded → generate_encounter_config() + NPC population",
            "UMelodiaBattleSession::BeginEncounter → trigger from DungeonTrigger actor",
            "UMelodiaBattleSession::EndEncounter → RoguelikeRunSession.record_room_cleared()",
            "RoguelikeRunSession → persisted in UGameInstanceSubsystem across floor changes",
            "Generate → ADungeonGenerator::Unload() → Regenerate with next floor → ADungeonGenerator::Generate()",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(dungeon_system_summary(), indent=2))
