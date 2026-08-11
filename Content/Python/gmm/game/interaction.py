"""World Interaction System — handles F-to-interact mechanics.

Provides:
- Interactable object base definitions
- Door interaction (opening, closing, locked states)
- Harvestable resource collection
- NPC interaction triggers
- Input binding for F key interaction

Usage:
    from gmm.game.interaction import InteractionManager, InteractableType
    InteractionManager.register_interactable(target_actor)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable


class InteractableType(Enum):
    """Types of interactable objects in the world."""
    DOOR = auto()
    HARVEST_NODE = auto()
    NPC = auto()
    CHEST = auto()
    SHRINE = auto()
    PHOTO_SPOT = auto()
    QUEST_GIVER = auto()
    SHOP_KEEPER = auto()


class InteractionResult(Enum):
    """Outcome of an interaction attempt."""
    SUCCESS = auto()
    FAILED = auto()
    LOCKED = auto()
    COOLDOWN = auto()
    NO_INTERACTION = auto()


@dataclass
class InteractionEvent:
    """Data passed when an interaction occurs."""
    interactable_id: str
    interactable_type: InteractableType
    player_state: Optional[dict] = None
    interaction_data: dict = field(default_factory=dict)
    result: InteractionResult = InteractionResult.SUCCESS

    def to_dict(self) -> dict:
        return {
            "interactable_id": self.interactable_id,
            "interactable_type": self.interactable_type.name,
            "interaction_data": self.interaction_data,
            "result": self.result.name,
        }


# -----------------------------------------------------------------------------
# Door Interaction System
# -----------------------------------------------------------------------------

@dataclass
class DoorState:
    """Door interaction state."""
    door_id: str
    is_open: bool = False
    is_locked: bool = False
    lockpick_difficulty: int = 0  # 0 = unlocked
    open_direction: tuple[float, float, float] = (0, 90, 0)  # Rotation when open
    closed_rotation: tuple[float, float, float] = (0, 0, 0)
    interaction_cooldown: float = 0.5  # Seconds before can interact again

    def to_dict(self) -> dict:
        return {
            "door_id": self.door_id,
            "is_open": self.is_open,
            "is_locked": self.is_locked,
            "lockpick_difficulty": self.lockpick_difficulty,
        }


# -----------------------------------------------------------------------------
# Harvestable Resource System
# -----------------------------------------------------------------------------

@dataclass
class HarvestNode:
    """A resource node that can be harvested."""
    node_id: str
    node_type: str  # "mana_crystal", "token_shrine", "material_deposit"
    resource_type: str  # What is harvested
    amount: int = 1
    max_harvests: int = 3
    harvests_remaining: int = 3
    respawn_time: float = 300.0  # Seconds
    interaction_prompt: str = "Press F to harvest"

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "resource_type": self.resource_type,
            "amount": self.amount,
            "max_harvests": self.max_harvests,
            "harvests_remaining": self.harvests_remaining,
        }


# -----------------------------------------------------------------------------
# Interaction Manager
# -----------------------------------------------------------------------------

class InteractionManager:
    """Central manager for world interactions.

    Registers and tracks all interactable objects in the world.
    Handles F-key input and dispatches interactions.
    """

    _instance: Optional["InteractionManager"] = None

    def __init__(self):
        self._interactables: dict[str, dict] = {}
        self._door_states: dict[str, DoorState] = {}
        self._harvest_nodes: dict[str, HarvestNode] = {}
        self._callbacks: dict[InteractableType, list[Callable]] = {t: [] for t in InteractableType}

    @classmethod
    def instance(cls) -> "InteractionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register_interactable(
        cls,
        actor_path: str,
        interactable_type: InteractableType,
        interaction_data: Optional[dict] = None,
    ) -> bool:
        """Register an actor as interactable."""
        mgr = cls.instance()
        mgr._interactables[actor_path] = {
            "type": interactable_type,
            "data": interaction_data or {},
        }
        return True

    @classmethod
    def unregister_interactable(cls, actor_path: str) -> bool:
        """Remove an interactable from the registry."""
        mgr = cls.instance()
        if actor_path in mgr._interactables:
            del mgr._interactables[actor_path]
            return True
        return False

    @classmethod
    def interact(cls, player_actor: str, target_actor: str) -> InteractionEvent:
        """Attempt to interact with a target actor."""
        mgr = cls.instance()

        if target_actor not in mgr._interactables:
            return InteractionEvent(
                interactable_id=target_actor,
                interactable_type=InteractableType.NPC,
                result=InteractionResult.NO_INTERACTION,
            )

        info = mgr._interactables[target_actor]
        itype = info["type"]
        data = info["data"]

        # Handle door interactions
        if itype == InteractableType.DOOR:
            return cls._handle_door_interaction(target_actor, data)

        # Handle harvest node interactions
        if itype == InteractableType.HARVEST_NODE:
            return cls._handle_harvest_interaction(target_actor, data)

        # Generic callback dispatch
        for callback in mgr._callbacks.get(itype, []):
            result = callback(target_actor, data)
            if result:
                return result

        return InteractionEvent(
            interactable_id=target_actor,
            interactable_type=itype,
            interaction_data=data,
            result=InteractionResult.SUCCESS,
        )

    @classmethod
    def _handle_door_interaction(cls, door_path: str, data: dict) -> InteractionEvent:
        """Handle door opening/closing."""
        mgr = cls.instance()

        door_id = data.get("door_id", door_path)
        if door_id not in mgr._door_states:
            mgr._door_states[door_id] = DoorState(door_id=door_id)

        door_state = mgr._door_states[door_id]

        if door_state.is_locked:
            return InteractionEvent(
                interactable_id=door_path,
                interactable_type=InteractableType.DOOR,
                result=InteractionResult.LOCKED,
            )

        door_state.is_open = not door_state.is_open
        return InteractionEvent(
            interactable_id=door_path,
            interactable_type=InteractableType.DOOR,
            interaction_data={"door_id": door_id, "now_open": door_state.is_open},
            result=InteractionResult.SUCCESS,
        )

    @classmethod
    def _handle_harvest_interaction(cls, node_path: str, data: dict) -> InteractionEvent:
        """Handle harvesting a resource node."""
        mgr = cls.instance()

        node_id = data.get("node_id", node_path)
        if node_id not in mgr._harvest_nodes:
            mgr._harvest_nodes[node_id] = HarvestNode(
                node_id=node_id,
                node_type=data.get("node_type", "token_shrine"),
                resource_type=data.get("resource_type", "golden_token"),
                amount=data.get("amount", 1),
                max_harvests=data.get("max_harvests", 3),
                harvests_remaining=data.get("harvests_remaining", 3),
            )

        node = mgr._harvest_nodes[node_id]

        if node.harvests_remaining <= 0:
            return InteractionEvent(
                interactable_id=node_path,
                interactable_type=InteractableType.HARVEST_NODE,
                result=InteractionResult.COOLDOWN,
            )

        node.harvests_remaining -= 1

        return InteractionEvent(
            interactable_id=node_path,
            interactable_type=InteractableType.HARVEST_NODE,
            interaction_data={
                "node_id": node_id,
                "harvested_amount": node.amount,
                "resource_type": node.resource_type,
                "remaining": node.harvests_remaining,
            },
            result=InteractionResult.SUCCESS,
        )

    @classmethod
    def register_callback(
        cls,
        interactable_type: InteractableType,
        callback: Callable[[str, dict], InteractionEvent],
    ):
        """Register a callback for a specific interaction type."""
        mgr = cls.instance()
        mgr._callbacks[interactable_type].append(callback)


# -----------------------------------------------------------------------------
# F-Key Input Binding
# -----------------------------------------------------------------------------

def get_f_key_binding() -> dict:
    """Get the F-key interaction input action definition."""
    return {
        "action_name": "Interact",
        "key": "F",
        "b_shift": False,
        "b_ctrl": False,
        "b_alt": False,
    }


def add_interact_binding_to_input_config() -> str:
    """Generate the input config addition for F-key interaction."""
    return '+ActionMappings=(ActionName="Interact",Key=F,bShift=False,bCtrl=False,bAlt=False,bCmd=False)'


# -----------------------------------------------------------------------------
# Integration Helpers
# -----------------------------------------------------------------------------

def create_door_spec(
    door_id: str,
    location: tuple[float, float, float],
    rotation: tuple[float, float, float],
    is_locked: bool = False,
) -> dict:
    """Create a door specification for level placement."""
    return {
        "door_id": door_id,
        "location": location,
        "rotation": rotation,
        "is_locked": is_locked,
        "open_rotation": (rotation[0], rotation[1] + 90, rotation[2]),
    }


def create_harvest_node_spec(
    node_id: str,
    node_type: str,
    resource_type: str,
    amount: int = 1,
    location: tuple[float, float, float] = (0, 0, 0),
) -> dict:
    """Create a harvest node specification for world placement."""
    return {
        "node_id": node_id,
        "node_type": node_type,
        "resource_type": resource_type,
        "amount": amount,
        "location": location,
        "max_harvests": 3,
    }


def interaction_system_summary() -> dict:
    """Get summary of the interaction system."""
    mgr = InteractionManager.instance()
    return {
        "interactable_types": [t.name for t in InteractableType],
        "registered_interactables": len(mgr._interactables),
        "doors_tracked": len(mgr._door_states),
        "harvest_nodes_tracked": len(mgr._harvest_nodes),
    }