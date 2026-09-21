"""Scene-time authority for Melodia GN builders (single seam).

Why this module exists
----------------------
`apply_universal_music_pass` (core.py:1086) is pure spatial math:
`sin(z * Freq A) + sin(atan2(y, x) * Freq B)`. It has no scene-time node, so
the geometry it drives is FROZEN wherever Python is not running - headless
renders, a linked `melodia_gn_library.blend`, bake/export, and any session with
Convergence Mode off. `surreal_arch/convergence_mode.py` animates it only by
writing socket values from a `frame_change_post` handler, which makes that
Python handler load-bearing for a GN feature. A builder named for motion with no
time authority is a silent no-op (`chimes_gn.py` has zero time references).

This module is the one place time enters a tree, so builders share one
authority instead of each inventing one.

Determinism contract
--------------------
`Animated = False` (or `Time Scale = 0`) must reproduce the pre-time geometry
EXACTLY: every use site adds time into a phase argument, so at t = 0 the result
is identical to the frozen form. Bake/export/morph-target paths therefore stay
reproducible by turning one bool off, and fingerprints do not need a tolerance.

No parallel authority: this extends the existing `apply_universal_music_pass` /
Convergence seam. It is not a second animation system, and it never decides
whether a rhythm hit landed - Unreal remains the runtime rhythm authority.
"""
from __future__ import annotations

from .core import add_bool_param, add_float_param, link_sockets, log, safe_node

# Names are part of the public contract: build_and_verify / fingerprint tools and
# the Convergence panel address these sockets by name.
ANIMATED = "Animated"
TIME_SCALE = "Time Scale"
TIME_OFFSET = "Time Offset"


def _existing_socket(tree, name):
    """Return an interface socket by name, or None (Blender 4.0+ interface API)."""
    iface = getattr(tree, "interface", None)
    if iface is None:
        return None
    try:
        for item in iface.items_tree:
            if getattr(item, "item_type", "") == "SOCKET" and item.name == name:
                return item
    except Exception:
        return None
    return None


def add_time_params(tree, animated_default=True):
    """Declare the shared time inputs. Idempotent - never duplicates a socket.

    Reuses an existing `Animated` socket when a builder already declares one
    (`water.py` does), so no builder ends up with two contradictory switches.
    """
    if _existing_socket(tree, ANIMATED) is None:
        add_bool_param(
            tree, ANIMATED, animated_default,
            description="Drive this builder from the scene timeline. Off = frozen at t=0 "
                        "(deterministic for bake/export/fingerprint).",
        )
    if _existing_socket(tree, TIME_SCALE) is None:
        add_float_param(
            tree, TIME_SCALE, 1.0, 0.0, 10.0,
            description="Multiplier on scene time. 0 freezes (same as Animated off).",
        )
    if _existing_socket(tree, TIME_OFFSET) is None:
        add_float_param(
            tree, TIME_OFFSET, 0.0, 0.0, 3600.0,
            description="Phase offset in seconds - desynchronise repeated instances.",
        )


def time_seconds(tree, gin, loc=(0, 0)):
    """Return a float socket: scene seconds, gated by Animated, scaled + offset.

    Animated is applied as a multiply by 0/1, not a branch, so the graph shape
    and node count are identical whether motion is on or off.
    """
    add_time_params(tree)
    t_node = safe_node(tree, "GeometryNodeInputSceneTime", loc)
    if t_node is None:
        # No scene-time node: fall back to a constant 0 so callers stay wired
        # and the geometry is the deterministic frozen form, never a crash.
        log.warning("time_seconds: GeometryNodeInputSceneTime unavailable in %s",
                    getattr(tree, "name", "?"))
        zero = safe_node(tree, "ShaderNodeMath", (loc[0] + 200, loc[1]))
        if zero is not None:
            zero.operation = "ADD"
            zero.inputs[0].default_value = 0.0
            return zero.outputs[0]
        return None

    scale = safe_node(tree, "ShaderNodeMath", (loc[0] + 200, loc[1]))
    scale.operation = "MULTIPLY"
    link_sockets(tree, t_node.outputs["Seconds"], scale.inputs[0])
    ts = gin.outputs.get(TIME_SCALE)
    if ts is not None:
        link_sockets(tree, ts, scale.inputs[1])
    else:
        scale.inputs[1].default_value = 1.0

    offset = safe_node(tree, "ShaderNodeMath", (loc[0] + 400, loc[1]))
    offset.operation = "ADD"
    link_sockets(tree, scale.outputs[0], offset.inputs[0])
    to = gin.outputs.get(TIME_OFFSET)
    if to is not None:
        link_sockets(tree, to, offset.inputs[1])
    else:
        offset.inputs[1].default_value = 0.0

    if gin.outputs.get(ANIMATED) is None:
        return offset.outputs[0]

    gate = safe_node(tree, "ShaderNodeMath", (loc[0] + 600, loc[1]))
    gate.operation = "MULTIPLY"
    link_sockets(tree, offset.outputs[0], gate.inputs[0])
    try:
        link_sockets(tree, gin.outputs[ANIMATED], gate.inputs[1])
    except Exception:
        # An implicit bool->float link was refused. Keep motion ON rather than
        # silently freezing the builder, and say so - a frozen builder must
        # never be quiet.
        log.warning(
            "time_seconds: cannot gate %s by %s - motion left enabled",
            getattr(tree, "name", "?"), ANIMATED,
        )
        gate.inputs[1].default_value = 1.0
    return gate.outputs[0]


def add_time_to_phase(tree, gin, phase_sock, loc=(0, 0)):
    """Add gated time into a sine/cos phase argument.

    The retrofit primitive for existing builders: inserting it into an argument
    of `sin(...)` changes nothing at t = 0 and makes the existing math move.
    Returns the new phase socket (or the input unchanged when unavailable).
    """
    if phase_sock is None:
        return phase_sock
    t = time_seconds(tree, gin, loc)
    if t is None:
        return phase_sock
    addn = safe_node(tree, "ShaderNodeMath", (loc[0] + 800, loc[1]))
    if addn is None:
        return phase_sock
    addn.operation = "ADD"
    link_sockets(tree, phase_sock, addn.inputs[0])
    link_sockets(tree, t, addn.inputs[1])
    return addn.outputs[0]