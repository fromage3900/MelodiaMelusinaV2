"""Serializable, application-independent GMM geometry modifier stack."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from .schemas import BEVEL_DEFAULTS, validate_bevel_parameters, validate_boolean_parameters

# Extended mesh tool parameter defaults
INSET_DEFAULTS: dict[str, object] = {"thickness": 0.2, "depth": 0.0, "individual": True}
BOOLEAN_DIFFERENCE_DEFAULTS: dict[str, object] = {
    "operation": "difference",
    "cutter_mesh_path": "",
    "cutter_location": {"x": 0.0, "y": 0.0, "z": 0.0},
    "cutter_rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
    "cutter_scale": {"x": 1.0, "y": 1.0, "z": 1.0},
    "show_preview": False,
    "preserve_cutter": False,
}
BOOLEAN_UNION_DEFAULTS: dict[str, object] = {**BOOLEAN_DIFFERENCE_DEFAULTS, "operation": "union"}
BOOLEAN_INTERSECT_DEFAULTS: dict[str, object] = {**BOOLEAN_DIFFERENCE_DEFAULTS, "operation": "intersect"}
POKE_DEFAULTS: dict[str, object] = {"height": 0.5, "inset": 0.0}
SUBDIVISION_DEFAULTS: dict[str, object] = {"levels": 2, "edge_crease": 0.0, "vert_crease": 0.0}
MULTI_BEVEL_DEFAULTS: dict[str, object] = {"main_width": 0.1, "micro_width": 0.01, "main_segments": 3, "micro_segments": 1}
WEIGHTED_BEVEL_DEFAULTS: dict[str, object] = {"base_width": 0.05, "segments": 2, "weight_attribute": "bevel_weight"}
BEVEL_PROFILE_DEFAULTS: dict[str, object] = {"width": 0.05, "segments": 2, "profile": 0.5}


@dataclass
class GeometryModifier:
    """One ordered geometry operation destined for a UE adapter."""

    modifier_id: str
    modifier_type: str
    enabled: bool = True
    scope: str = "editor"
    backend: str = "auto"
    parameters: dict[str, object] = field(default_factory=dict)

    SUPPORTED_TYPES: ClassVar[frozenset[str]] = frozenset({
        "bevel", "bevel_profile", "weighted_bevel", "multi_bevel",
        "inset", "poke", "subdivision_crease",
        "weighted_normal", "subdivision", "transform", "mirror",
        "array", "spiral_array", "radial_array", "weighted_array", "curve_array",
        "displace", "smooth", "material_override", "collision",
        "boolean_difference", "boolean_union", "boolean_intersect",
    })

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.modifier_id.strip():
            errors.append("modifier_id must not be empty")
        if self.modifier_type not in self.SUPPORTED_TYPES:
            errors.append(f"unsupported modifier_type: {self.modifier_type}")
        if self.scope not in {"editor", "runtime", "both"}:
            errors.append(f"unsupported scope: {self.scope}")
        if self.modifier_type == "bevel":
            errors.extend(validate_bevel_parameters(self.parameters))
        if self.modifier_type.startswith("boolean_"):
            errors.extend(validate_boolean_parameters(self.modifier_type, self.parameters))
        if self.modifier_type == "inset" and not self.parameters:
            self.parameters.update(INSET_DEFAULTS)
        if self.modifier_type == "poke" and not self.parameters:
            self.parameters.update(POKE_DEFAULTS)
        if self.modifier_type == "subdivision_crease" and not self.parameters:
            self.parameters.update(SUBDIVISION_DEFAULTS)
        if self.modifier_type == "multi_bevel" and not self.parameters:
            self.parameters.update(MULTI_BEVEL_DEFAULTS)
        if self.modifier_type == "weighted_bevel" and not self.parameters:
            self.parameters.update(WEIGHTED_BEVEL_DEFAULTS)
        if self.modifier_type == "bevel_profile" and not self.parameters:
            self.parameters.update(BEVEL_PROFILE_DEFAULTS)
        if self.modifier_type == "boolean_difference" and not self.parameters:
            self.parameters.update(BOOLEAN_DIFFERENCE_DEFAULTS)
        if self.modifier_type == "boolean_union" and not self.parameters:
            self.parameters.update(BOOLEAN_UNION_DEFAULTS)
        if self.modifier_type == "boolean_intersect" and not self.parameters:
            self.parameters.update(BOOLEAN_INTERSECT_DEFAULTS)
        return errors

    def to_dict(self, order: int) -> dict[str, object]:
        return {
            "id": self.modifier_id,
            "type": self.modifier_type,
            "enabled": self.enabled,
            "order": order,
            "scope": self.scope,
            "backend": self.backend,
            "parameters": dict(self.parameters),
        }


class ModifierStack:
    """Ordered stack with explicit preview/commit lifecycle state."""

    def __init__(self, target: str = "") -> None:
        self.target: str = target
        self._items: list[GeometryModifier] = []
        self.lifecycle: str = "unapplied"

    @property
    def items(self) -> tuple[GeometryModifier, ...]:
        return tuple(self._items)

    def add(self, modifier: GeometryModifier) -> None:
        errors = modifier.validate()
        if errors:
            raise ValueError("; ".join(errors))
        if any(item.modifier_id == modifier.modifier_id for item in self._items):
            raise ValueError(f"duplicate modifier_id: {modifier.modifier_id}")
        if modifier.modifier_type == "bevel" and not modifier.parameters:
            modifier.parameters.update(BEVEL_DEFAULTS)
        if modifier.modifier_type == "boolean_difference" and not modifier.parameters:
            modifier.parameters.update(BOOLEAN_DIFFERENCE_DEFAULTS)
        if modifier.modifier_type == "boolean_union" and not modifier.parameters:
            modifier.parameters.update(BOOLEAN_UNION_DEFAULTS)
        if modifier.modifier_type == "boolean_intersect" and not modifier.parameters:
            modifier.parameters.update(BOOLEAN_INTERSECT_DEFAULTS)
        self._items.append(modifier)

    def remove(self, modifier_id: str) -> GeometryModifier:
        for index, item in enumerate(self._items):
            if item.modifier_id == modifier_id:
                return self._items.pop(index)
        raise KeyError(modifier_id)

    def move(self, modifier_id: str, new_index: int) -> None:
        if not 0 <= new_index < len(self._items):
            raise IndexError(new_index)
        item = self.remove(modifier_id)
        self._items.insert(new_index, item)

    def set_enabled(self, modifier_id: str, enabled: bool) -> None:
        self._find(modifier_id).enabled = enabled

    def set_parameter(self, modifier_id: str, name: str, value: object) -> None:
        item = self._find(modifier_id)
        candidate = dict(item.parameters)
        candidate[name] = value
        if item.modifier_type == "bevel":
            errors = validate_bevel_parameters(candidate)
        elif item.modifier_type.startswith("boolean_"):
            errors = validate_boolean_parameters(item.modifier_type, candidate)
        else:
            errors = []
        if errors:
            raise ValueError("; ".join(errors))
        item.parameters[name] = value

    def mark_previewed(self) -> None:
        self.lifecycle = "preview"

    def mark_committed(self) -> None:
        self.lifecycle = "committed"

    def mark_baked(self) -> None:
        self.lifecycle = "baked"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.target.strip():
            errors.append("target must not be empty")
        for item in self._items:
            errors.extend(f"{item.modifier_id}: {error}" for error in item.validate())
        return errors

    def to_dict(self) -> dict[str, object]:
        return {
            "format": "gmm_modifier_stack_v1",
            "target": self.target,
            "lifecycle": self.lifecycle,
            "modifiers": [item.to_dict(index) for index, item in enumerate(self._items)],
        }

    def _find(self, modifier_id: str) -> GeometryModifier:
        for item in self._items:
            if item.modifier_id == modifier_id:
                return item
        raise KeyError(modifier_id)
