"""Generic modifier-stack evaluator for Melodia rule modifiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from gmm.game.rules_generated import RULES


_MODIFIER_RULES = RULES["modifiers"]
_REGISTRY = {entry["id"]: dict(entry) for entry in _MODIFIER_RULES["registry"]}


@dataclass
class ActiveModifier:
    id: str
    stat: str
    op: str
    value: float
    duration_turns: int
    stacking: str
    max_stacks: int
    stacks: int = 1
    remaining_turns: int = 0

    @classmethod
    def from_rule(cls, rule: dict) -> "ActiveModifier":
        duration = int(rule["duration_turns"])
        return cls(
            id=str(rule["id"]),
            stat=str(rule["stat"]),
            op=str(rule["op"]),
            value=float(rule["value"]),
            duration_turns=duration,
            stacking=str(rule["stacking"]),
            max_stacks=max(1, int(rule["max_stacks"])),
            stacks=1,
            remaining_turns=duration,
        )

    @property
    def is_permanent(self) -> bool:
        return self.duration_turns < 0

    def refresh(self) -> None:
        self.remaining_turns = self.duration_turns


class ModifierStack:
    """Applies generated-rule add/mul modifiers by stat."""

    def __init__(self, registry: dict[str, dict] | None = None):
        self.registry = registry or _REGISTRY
        self.active: list[ActiveModifier] = []

    def add(self, modifier_id: str) -> bool:
        rule = self.registry.get(modifier_id)
        if not rule:
            return False
        return self.add_rule(rule)

    def add_rule(self, rule: dict) -> bool:
        incoming = ActiveModifier.from_rule(rule)
        existing = [mod for mod in self.active if mod.id == incoming.id]

        if existing:
            current = existing[0]
            if incoming.stacking == "ignore":
                return False
            if incoming.stacking == "refresh":
                current.refresh()
                return True
            if incoming.stacking == "stack":
                if current.stacks >= current.max_stacks:
                    current.refresh()
                    return False
                current.stacks += 1
                current.refresh()
                return True

        self.active.append(incoming)
        return True

    def evaluate(self, stat: str, base_value: float) -> float:
        value = float(base_value)
        for modifier in self._matching(stat, "add"):
            value += modifier.value * modifier.stacks
        for modifier in self._matching(stat, "mul"):
            value *= modifier.value ** modifier.stacks
        return value

    def tick_turn(self) -> None:
        kept: list[ActiveModifier] = []
        for modifier in self.active:
            if modifier.is_permanent:
                kept.append(modifier)
                continue
            modifier.remaining_turns -= 1
            if modifier.remaining_turns > 0:
                kept.append(modifier)
        self.active = kept

    def clear(self) -> None:
        self.active.clear()

    def snapshot(self) -> list[dict]:
        return [
            {
                "id": mod.id,
                "stat": mod.stat,
                "op": mod.op,
                "value": mod.value,
                "stacks": mod.stacks,
                "remaining_turns": mod.remaining_turns,
            }
            for mod in self.active
        ]

    def _matching(self, stat: str, op: str) -> Iterable[ActiveModifier]:
        return (mod for mod in self.active if mod.stat == stat and mod.op == op)


def modifier_registry_summary() -> dict:
    return {
        "count": len(_REGISTRY),
        "ids": list(_REGISTRY.keys()),
        "stats": sorted({entry["stat"] for entry in _REGISTRY.values()}),
    }
