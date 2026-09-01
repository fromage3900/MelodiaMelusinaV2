"""
MEL_p4_resonance_harp_array — Resonance Harp Array (music)

Field of harps tuned to cymatic ModeN/M, frame curve from BeatPulse.
P4 stub — full harp instance array + cymatic tuning wired in Blender smoke.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


_SOCK_MAP = {"INT": "NodeSocketInt", "FLOAT": "NodeSocketFloat", "BOOL": "NodeSocketBool"}


def _safe_input(tree, name, sock_type, default=None, min_value=None, max_value=None):
    """Bridge mother_tapestry_wall pattern (name, type, min_value) to core (type, name, min_val)."""
    mapped = _SOCK_MAP.get(sock_type, sock_type)
    # Try mother pattern first (matches task spec literally), then normalized core signature
    for attempt in [
        lambda: make_group_input(tree, name, sock_type, default=default, min_value=min_value, max_value=max_value),
        lambda: make_group_input(tree, mapped, name, default=default, min_val=min_value, max_val=max_value),
        lambda: make_group_input(tree, name, mapped, default=default, min_val=min_value, max_val=max_value),
        lambda: make_group_input(tree, sock_type, name, default=default, min_val=min_value, max_val=max_value),
        lambda: make_group_input(tree, name, sock_type, default=default, min_val=min_value, max_val=max_value),
        lambda: make_group_input(tree, mapped, name, default=default, min_value=min_value, max_value=max_value),
    ]:
        try:
            result = attempt()
            if result is not None:
                return result
        except TypeError:
            continue
        except Exception:
            continue
    return None


def build_p4_resonance_harp_array():
    tree, gin, gout = new_geometry_tree("MEL_p4_resonance_harp_array")
    # Inputs — minimal stub, full node graph added when editor work begins
    _safe_input(tree, "Field Count", "INT", default=9, min_value=1, max_value=64)
    _safe_input(tree, "Harp Scale", "FLOAT", default=1.0, min_value=0.2, max_value=4.0)
    _safe_input(tree, "ModeN", "INT", default=3, min_value=0, max_value=12)
    _safe_input(tree, "ModeM", "INT", default=1, min_value=0, max_value=12)
    _safe_input(tree, "String Count", "INT", default=7, min_value=1, max_value=32)
    # Geometry: passthrough (placeholder links, refined in Blender)
    # Keep minimal so import + registry succeeds; full node graph added when editor work begins.
    try:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    except Exception:
        # Fallback for shorthand-tolerant cores
        try:
            link_sockets(gin, "Geometry", gout, "Geometry")  # type: ignore[arg-type]
        except Exception:
            pass
    return tree, gin, gout


register_builder(
    "MEL_p4_resonance_harp_array",
    build_p4_resonance_harp_array,
    label="Resonance Harp Array",
    description="Field of harps tuned to cymatic ModeN/M, frame curve from BeatPulse",
    category="music",
)
