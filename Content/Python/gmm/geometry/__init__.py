"""GMM geometry modifier contracts and stack model."""

from .modifiers import (
    GeometryModifier, ModifierStack,
    INSET_DEFAULTS, POKE_DEFAULTS, SUBDIVISION_DEFAULTS,
    MULTI_BEVEL_DEFAULTS, WEIGHTED_BEVEL_DEFAULTS, BEVEL_PROFILE_DEFAULTS,
)
from .schemas import validate_bevel_parameters
from .sessions import PreviewSession, PreviewSessionRegistry, SESSIONS
from .water import (
    default_request as default_water_request,
    serialize_request as serialize_water_request,
    validate_request as validate_water_request,
)
from .array_tools import (
    compute_spiral_array, compute_radial_array, compute_weighted_array,
    compute_curve_array, spec_to_pcg_params, ARRAY_TOOL_SPECS,
    ArrayTransform,
)

__all__ = [
    "GeometryModifier",
    "ModifierStack",
    "PreviewSession",
    "PreviewSessionRegistry",
    "SESSIONS",
    "validate_bevel_parameters",
    "INSET_DEFAULTS",
    "POKE_DEFAULTS",
    "SUBDIVISION_DEFAULTS",
    "MULTI_BEVEL_DEFAULTS",
    "WEIGHTED_BEVEL_DEFAULTS",
    "BEVEL_PROFILE_DEFAULTS",
    "default_water_request",
    "serialize_water_request",
    "validate_water_request",
    "compute_spiral_array",
    "compute_radial_array",
    "compute_weighted_array",
    "compute_curve_array",
    "spec_to_pcg_params",
    "ARRAY_TOOL_SPECS",
    "ArrayTransform",
]
