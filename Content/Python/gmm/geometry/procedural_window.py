"""Pure-Python procedural window cutter generator for GMM modifier stacks.

This module mirrors the Blender `GeometryNodeMeshBoolean` DIFFERENCE workflow
used in `deploy/surreal_greybox/shells.py`. It produces a `ModifierStack` of
boolean-difference cutters ready for UE intake.

No `unreal` import happens at module load time; the contract is serialized and
validated in pure Python.
"""
from __future__ import annotations

from dataclasses import dataclass

from .modifiers import GeometryModifier, ModifierStack


@dataclass
class WindowSpec:
    """Describes a wall and the windows to cut into it."""

    wall_width: float = 8.0
    wall_height: float = 3.5
    wall_thickness: float = 0.3
    window_width: float = 1.2
    window_height: float = 1.4
    window_sill_height: float = 1.0
    count: int = 2
    spacing: float | None = None

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("count must be non-negative")
        if self.wall_width <= 0:
            raise ValueError("wall_width must be greater than 0")
        if self.wall_height <= 0:
            raise ValueError("wall_height must be greater than 0")
        if self.wall_thickness <= 0:
            raise ValueError("wall_thickness must be greater than 0")
        if self.window_width <= 0:
            raise ValueError("window_width must be greater than 0")
        if self.window_height <= 0:
            raise ValueError("window_height must be greater than 0")
        if self.window_sill_height < 0:
            raise ValueError("window_sill_height must be non-negative")


def _cutter_depth(thickness: float, multiplier: float = 4.0) -> float:
    """Return a cutter depth large enough to fully penetrate the wall."""
    return max(thickness * multiplier, 0.1)


def build_window_cutters(spec: WindowSpec, base_id: str = "window") -> list[GeometryModifier]:
    """Build boolean-difference modifiers representing window cutters.

    Cutters are distributed evenly along the wall width, centered on the wall
    face. The cutter depth is exaggerated so it punches through walls of the
    given thickness regardless of small transform errors.
    """
    if spec.count == 0:
        return []

    effective_spacing = (
        spec.spacing
        if spec.spacing is not None
        else spec.wall_width / (spec.count + 1)
    )

    start_x = -((spec.count - 1) * effective_spacing) / 2.0
    cutter_depth = _cutter_depth(spec.wall_thickness)
    window_z = spec.window_sill_height + spec.window_height * 0.5

    cutters: list[GeometryModifier] = []
    for i in range(spec.count):
        center_x = start_x + i * effective_spacing
        cutter = GeometryModifier(
            modifier_id=f"{base_id}_{i:03d}",
            modifier_type="boolean_difference",
            parameters={
                "operation": "difference",
                "cutter_mesh_path": "/Game/EnvSandbox/Meshes/Primitives/SM_WindowCutter",
                "cutter_location": {"x": center_x, "y": 0.0, "z": window_z},
                "cutter_rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "cutter_scale": {
                    "x": spec.window_width,
                    "y": cutter_depth,
                    "z": spec.window_height,
                },
                "show_preview": True,
                "preserve_cutter": False,
            },
        )
        cutters.append(cutter)
    return cutters


def build_window_stack(
    target: str,
    spec: WindowSpec,
    *,
    base_id: str = "window",
    include_frame: bool = False,
) -> ModifierStack:
    """Return a `ModifierStack` ready for UE intake with window cutters.

    Args:
        target: Unreal asset path of the wall mesh to cut.
        spec: Window layout specification.
        base_id: Prefix used for generated modifier IDs.
        include_frame: Reserved for future window-frame additive modifiers.
    """
    stack = ModifierStack(target)
    for cutter in build_window_cutters(spec, base_id=base_id):
        stack.add(cutter)
    if include_frame:
        # Future: append a frame/bevel modifier after the cutters.
        pass
    return stack
