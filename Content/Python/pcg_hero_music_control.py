"""Shared PCG_Control reader and alias layer for the reusable hero graphs.

The driver actor keeps its existing eleven property names and ``PCG_Control``
tag. The graph builders consume a snapshot for generation-time values, while
this module records the canonical target aliases so a regeneration is auditable
and never silently relies on a mismatched PCG attribute name.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping


CONTROL_TAG = "PCG_Control"
CONTROL_PROPERTIES = (
    "Depth",
    "Density",
    "WalkWidth",
    "ArrayCount",
    "ArraySpacing",
    "ResampleSpacing",
    "ScaleMin",
    "ScaleMax",
    "CullDistance",
    "StencilValue",
    "WriteCustomDepth",
)

# Native PCG reader outputs used by the shared universal alias graph. Hero
# graphs may refine the generation-time names (VaultHeight, StationCount, and
# so on), but these are the actual PCG target attributes.
CONTROL_ALIAS_TARGETS = {
    "Depth": "Depth",
    "Density": "Density",
    "WalkWidth": "WalkWidth",
    "ArrayCount": "ArrayCount",
    "ArraySpacing": "CellSize",
    "ResampleSpacing": "DistanceBetweenPoints",
    "ScaleMin": "ScaleMin",
    "ScaleMax": "ScaleMax",
    "CullDistance": "InstanceEndCullDistance",
    "StencilValue": "CustomDepthStencilValue",
    "WriteCustomDepth": "RenderCustomDepth",
}


@dataclass(frozen=True)
class HeroMusicControlSnapshot:
    Depth: float = 1800.0
    Density: float = 0.40
    WalkWidth: float = 220.0
    ArrayCount: int = 4
    ArraySpacing: float = 480.0
    ResampleSpacing: float = 120.0
    ScaleMin: float = 0.85
    ScaleMax: float = 1.20
    CullDistance: float = 0.0
    StencilValue: int = 3
    WriteCustomDepth: bool = True


DEFAULT_SNAPSHOT = HeroMusicControlSnapshot()

# Authoring baselines are deliberately independent from whichever proof map is
# currently open. The live driver still owns On-Demand regeneration when an
# explicit snapshot is supplied; these values make unattended graph rebuilds
# reproducible across editor lanes.
PROOF_GRAPH_DEFAULTS: dict[str, dict[str, Any]] = {
    "ResonanceCathedral": {
        "Depth": 1800.0, "Density": 0.40, "WalkWidth": 220.0,
        "ArrayCount": 6, "ArraySpacing": 480.0, "ResampleSpacing": 120.0,
    },
    "ArpeggioBridge": {
        "Depth": 1800.0, "Density": 0.40, "WalkWidth": 220.0,
        "ArrayCount": 24, "ArraySpacing": 180.0, "ResampleSpacing": 120.0,
    },
    "BellTreeGarden": {
        "Depth": 900.0, "Density": 0.45, "WalkWidth": 300.0,
        "ArrayCount": 18, "ArraySpacing": 260.0, "ResampleSpacing": 120.0,
    },
    "XylophoneTrail": {
        "Depth": 1800.0, "Density": 0.40, "WalkWidth": 220.0,
        "ArrayCount": 4, "ArraySpacing": 480.0, "ResampleSpacing": 120.0,
    },
    "CrystalHarpGrove": {
        "Depth": 760.0, "Density": 0.55, "WalkWidth": 280.0,
        "ArrayCount": 20, "ArraySpacing": 520.0, "ResampleSpacing": 100.0,
    },
}


def authoring_overrides(graph_kind: str) -> dict[str, Any]:
    """Return a copy of a proof baseline for deterministic graph authoring."""
    for name, values in PROOF_GRAPH_DEFAULTS.items():
        if name.lower() == str(graph_kind).lower():
            return dict(values)
    return dict(asdict(DEFAULT_SNAPSHOT))


def _coerce_value(name: str, value: Any) -> Any:
    if name in {"ArrayCount", "StencilValue"}:
        return int(round(float(value)))
    if name == "WriteCustomDepth":
        return bool(value)
    return float(value)


def sanitize_snapshot(values: Mapping[str, Any] | None = None) -> HeroMusicControlSnapshot:
    """Clamp a snapshot to safe generation/render ranges."""
    raw = asdict(DEFAULT_SNAPSHOT)
    if values:
        for name in CONTROL_PROPERTIES:
            if name in values:
                raw[name] = _coerce_value(name, values[name])

    raw["Depth"] = max(1.0, raw["Depth"])
    raw["Density"] = min(1.0, max(0.0, raw["Density"]))
    raw["WalkWidth"] = max(1.0, raw["WalkWidth"])
    raw["ArrayCount"] = max(1, raw["ArrayCount"])
    raw["ArraySpacing"] = max(1.0, raw["ArraySpacing"])
    raw["ResampleSpacing"] = max(1.0, raw["ResampleSpacing"])
    raw["ScaleMin"] = max(0.01, raw["ScaleMin"])
    raw["ScaleMax"] = max(raw["ScaleMin"], raw["ScaleMax"])
    raw["CullDistance"] = max(0.0, raw["CullDistance"])
    raw["StencilValue"] = min(255, max(0, raw["StencilValue"]))
    return HeroMusicControlSnapshot(**raw)


def _read_actor_property(actor: Any, name: str) -> Any:
    try:
        return actor.get_editor_property(name)
    except Exception:
        return getattr(actor, name, None)


def _has_control_tag(actor: Any) -> bool:
    try:
        return CONTROL_TAG in [str(tag) for tag in actor.tags]
    except Exception:
        return False


def find_control_actor(unreal_module: Any, actors: Iterable[Any] | None = None) -> Any | None:
    """Find the level's canonical BP_MelodiaPCGControl by tag."""
    if actors is None:
        try:
            actors = unreal_module.get_editor_subsystem(unreal_module.EditorActorSubsystem).get_all_level_actors()
        except Exception:
            actors = ()
    for actor in actors:
        if _has_control_tag(actor):
            return actor
    return None


def read_control_snapshot(unreal_module: Any, actors: Iterable[Any] | None = None, overrides: Mapping[str, Any] | None = None) -> HeroMusicControlSnapshot:
    """Read the tagged driver and apply optional proof-level overrides."""
    actor = find_control_actor(unreal_module, actors)
    values: dict[str, Any] = {}
    if actor:
        for name in CONTROL_PROPERTIES:
            value = _read_actor_property(actor, name)
            if value is not None:
                values[name] = value
    if overrides:
        values.update(overrides)
    return sanitize_snapshot(values)


def map_control_aliases(snapshot: HeroMusicControlSnapshot, graph_kind: str) -> dict[str, Any]:
    """Return explicit aliases used by the graph-generation contract."""
    is_cathedral = "cathedral" in graph_kind.lower()
    is_bell_garden = "bell" in graph_kind.lower() or "garden" in graph_kind.lower()
    is_xylophone = "xylophone" in graph_kind.lower()
    if is_xylophone:
        return {
            "Depth": "TrailRise",
            "Density": "RailAccentDensity",
            "WalkWidth": "BarWidth",
            "ArrayCount": "BarSectionCount",
            "ArraySpacing": "BarSpacing",
            "ResampleSpacing": "DistanceBetweenPoints",
            "ScaleMin": "ScaleMin",
            "ScaleMax": "ScaleMax",
            "CullDistance": "InstanceEndCullDistance",
            "StencilValue": "CustomDepthStencilValue",
            "WriteCustomDepth": "RenderCustomDepth",
        }
    if "harp" in graph_kind.lower():
        return {
            "Depth": "GroveRise",
            "Density": "FrameRailDensity",
            "WalkWidth": "StringBankWidth",
            "ArrayCount": "StringCount",
            "ArraySpacing": "StationSpacing",
            "ResampleSpacing": "DistanceBetweenPoints",
            "ScaleMin": "ScaleMin",
            "ScaleMax": "ScaleMax",
            "CullDistance": "InstanceEndCullDistance",
            "StencilValue": "CustomDepthStencilValue",
            "WriteCustomDepth": "RenderCustomDepth",
        }
    return {
        "Depth": "VaultHeight" if is_cathedral else ("GardenRise" if is_bell_garden else "BridgeRise"),
        "Density": "Density",
        "WalkWidth": "AisleWidth" if is_cathedral else ("GardenPathWidth" if is_bell_garden else "ClearTraversalWidth"),
        "ArrayCount": "StationCount" if is_cathedral else ("BellCount" if is_bell_garden else "NoteCount"),
        "ArraySpacing": "StationSpacing" if is_cathedral else ("BellSpacing" if is_bell_garden else "StepSpacing"),
        "ResampleSpacing": "DistanceBetweenPoints",
        "ScaleMin": "ScaleMin",
        "ScaleMax": "ScaleMax",
        "CullDistance": "InstanceEndCullDistance",
        "StencilValue": "CustomDepthStencilValue",
        "WriteCustomDepth": "RenderCustomDepth",
    }


def control_alias_manifest(snapshot: HeroMusicControlSnapshot, graph_kind: str) -> dict[str, Any]:
    aliases = map_control_aliases(snapshot, graph_kind)
    return {
        "tag": CONTROL_TAG,
        "properties": list(CONTROL_PROPERTIES),
        "snapshot": asdict(snapshot),
        "aliases": aliases,
        "generation_time_controls": ["Depth", "Density", "WalkWidth", "ArrayCount", "ArraySpacing", "ResampleSpacing", "ScaleMin", "ScaleMax"],
        "render_controls": ["CullDistance", "StencilValue", "WriteCustomDepth"],
        "regeneration": "On-Demand PCG regeneration consumes a fresh tagged-driver snapshot",
    }


def apply_control_to_static_descriptor(descriptor: Any, snapshot: HeroMusicControlSnapshot) -> dict[str, bool]:
    """Apply render aliases to a PCG mesh descriptor where UE exposes them."""
    report: dict[str, bool] = {}
    for prop, value in (
        ("instance_end_cull_distance", float(snapshot.CullDistance)),
        ("render_custom_depth", bool(snapshot.WriteCustomDepth)),
        ("custom_depth_stencil_value", int(snapshot.StencilValue)),
    ):
        try:
            descriptor.set_editor_property(prop, value)
            report[prop] = True
        except Exception:
            report[prop] = False
    return report


def regression_payload() -> dict[str, Any]:
    snapshot = sanitize_snapshot()
    return {
        "all_properties_present": tuple(asdict(snapshot).keys()) == CONTROL_PROPERTIES,
        "proof_preset": {
            "CullDistance": snapshot.CullDistance,
            "WriteCustomDepth": snapshot.WriteCustomDepth,
            "StencilValue": snapshot.StencilValue,
        },
        "alias_count": len(map_control_aliases(snapshot, "cathedral")),
    }
