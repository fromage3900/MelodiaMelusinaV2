"""Small quality/preference helpers for deploy-side integration patches."""

from __future__ import annotations


_QUALITY_PROP_NAMES = ("prefer_melodia_gn",)

_DEFAULT_MELODIA_GN_ARCH_TYPES = {
    "GAZEBO",
    "PORTICO",
    "ARCH",
    "NOTE_HEAD",
    "STAFF",
    "TREBLE_CLEF",
    "SHEET_MUSIC_RAIL",
    "MELODIA_NOTE_HEAD",
    "MELODIA_STAFF",
    "MELODIA_TREBLE_CLEF",
    "MELODIA_HARMONIC",
    "MELODIA_PHRASE",
    "ORN_VINE",
    "ORN_RADIAL",
    "ORN_FRAME",
    "ORN_PANEL",
    "ORN_GRID",
    "CASTLE_TOWER",
    "CASTLE_GATEHOUSE",
    "CASTLE_KEEP",
    "CASTLE_CRENELLATION",
    "CASTLE_WALL_SEGMENT",
    "CASTLE_GOTHIC_WINDOW",
    "CASTLE_BUTTRESS",
    "CASTLE_CURTAIN_WALL",
    "CASTLE_MACHICOLATIONS",
    "CASTLE_SPIRAL_STAIRS",
    "CASTLE_ASSEMBLER",
    "ESCHER_BELVEDERE",
    "ESCHER_PENROSE_STAIRS",
    "ESCHER_WATERFALL",
    "SKY_OBSERVATORY",
}


def register_quality_props(monolith) -> None:
    """Attach deploy-side quality controls to the monolith property group."""
    props_cls = getattr(monolith, "SurrealArchProperties", None)
    if props_cls is None:
        return

    import bpy

    if not hasattr(props_cls, "prefer_melodia_gn"):
        props_cls.prefer_melodia_gn = bpy.props.BoolProperty(
            name="Prefer Melodia GN",
            description=(
                "Use polished MEL_* Geometry Nodes for supported music, ornament, "
                "castle, and structure types before falling back to legacy builders"
            ),
            default=True,
        )


def unregister_quality_props(monolith=None) -> None:
    """Remove deploy-side quality controls when the overhaul unregisters."""
    props_cls = getattr(monolith, "SurrealArchProperties", None) if monolith else None
    if props_cls is None:
        return
    for name in _QUALITY_PROP_NAMES:
        if hasattr(props_cls, name):
            try:
                delattr(props_cls, name)
            except Exception:
                pass


def prefer_melodia_gn(arch_type: str | None = None) -> bool:
    """Return whether Generate should prefer the Melodia GN path.

    The default is intentionally conservative: music routes use Melodia GN
    after this polish pass, while unrelated monolith builders keep their path.
    """
    if not arch_type:
        return True
    return arch_type in _DEFAULT_MELODIA_GN_ARCH_TYPES
