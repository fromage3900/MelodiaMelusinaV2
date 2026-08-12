"""Core GN tree builder utilities -- safe node creation, linking, coloring."""

from __future__ import annotations

import bpy

from .logging import log


def safe_node(tree, bl_idname, loc, fallback_callable=None):
    """Create a node, returns None on failure. Optionally call fallback.

    Logs failure at WARNING level so users can trace missing-node issues.
    """
    try:
        n = tree.nodes.new(bl_idname)
        n.location = loc
        return n
    except Exception as exc:
        log.warning(
            "safe_node: '%s' not available in %s ΓÇö %s",
            bl_idname, tree.name, exc,
        )
        if fallback_callable:
            log.debug("safe_node: attempting fallback for '%s'", bl_idname)
            try:
                return fallback_callable()
            except Exception as fb_exc:
                log.warning(
                    "safe_node: fallback also failed for '%s' ΓÇö %s",
                    bl_idname, fb_exc,
                )
        return None


def link_sockets(tree, from_socket, to_socket):
    """Link two sockets. Logs mismatches at debug level for troubleshooting."""
    if from_socket is None or to_socket is None:
        log.warning(
            "link_sockets: one or both sockets are None (tree=%s, from=%s, to=%s)",
            getattr(tree, "name", "?"), from_socket, to_socket,
        )
        return
    try:
        tree.links.new(from_socket, to_socket)
    except Exception as exc:
        log.warning(
            "link_sockets: cannot link %s ΓåÆ %s in %s ΓÇö %s",
            getattr(from_socket, "name", "?"),
            getattr(to_socket, "name", "?"),
            getattr(tree, "name", "?"),
            exc,
        )


def color_node(node, tag="default"):
    if node is None:
        return
    palette = {
        "default":  (0.3, 0.3, 0.3),
        "input":    (0.2, 0.4, 0.6),
        "output":   (0.6, 0.3, 0.2),
        "geometry": (0.2, 0.6, 0.3),
        "math":     (0.5, 0.3, 0.5),
        "curve":    (0.3, 0.5, 0.6),
        "instance": (0.6, 0.5, 0.2),
        "material": (0.4, 0.2, 0.5),
        "attribute":(0.3, 0.5, 0.4),
    }
    c = palette.get(tag, palette["default"])
    try:
        node.use_custom_color = True
        node.color = c
    except Exception as exc:
        log.debug("color_node: cannot color node '%s' ΓÇö %s", getattr(node, "name", "?"), exc)


def label_tree(tree, title: str | None = None, frames: list | tuple | None = None):
    """Apply Melodia Studio labels, node colors, and optional frame titles.

    `frames` accepts strings or dictionaries with `title`, `nodes`, and `role`.
    This keeps the GN editor vocabulary stable without changing builder behavior.
    """
    if tree is None:
        return None
    if title:
        try:
            tree.name = title
        except Exception as exc:
            log.debug("label_tree: cannot rename tree '%s' -- %s", getattr(tree, "name", "?"), exc)
    for node in getattr(tree, "nodes", []):
        bl_idname = getattr(node, "bl_idname", "")
        name = (getattr(node, "name", "") or "").lower()
        if bl_idname == "NodeGroupInput":
            color_node(node, "input")
        elif bl_idname == "NodeGroupOutput":
            color_node(node, "output")
        elif "instance" in bl_idname.lower() or "instance" in name:
            color_node(node, "instance")
        elif "attribute" in bl_idname.lower() or "attr" in name:
            color_node(node, "attribute")
        elif "curve" in bl_idname.lower() or "spline" in name:
            color_node(node, "curve")
        elif "math" in bl_idname.lower() or "compare" in name:
            color_node(node, "math")
        elif "mesh" in bl_idname.lower() or "geometry" in bl_idname.lower():
            color_node(node, "geometry")
    for spec in frames or ():
        if isinstance(spec, str):
            frame_title, node_names, role = spec, (), "default"
        else:
            frame_title = spec.get("title", "Melodia")
            node_names = tuple(spec.get("nodes", ()))
            role = spec.get("role", "default")
        frame_name = f"Frame - {frame_title}"
        frame = None
        for node in tree.nodes:
            if getattr(node, "name", "") == frame_name:
                frame = node
                break
        if frame is None:
            try:
                frame = tree.nodes.new("NodeFrame")
                frame.label = frame_title
                frame.name = frame_name
                color_node(frame, role)
            except Exception as exc:
                log.debug("label_tree: cannot create frame '%s' -- %s", frame_title, exc)
                frame = None
        if frame is not None and node_names:
            wanted = {n.lower() for n in node_names}
            for node in tree.nodes:
                label = (getattr(node, "label", "") or getattr(node, "name", "") or "").lower()
                if any(part in label for part in wanted):
                    try:
                        node.parent = frame
                    except Exception:
                        pass
    return tree


def ensure_labeled_tree(tree, tree_name: str, category: str = ""):
    """Apply a minimal Melodia label contract to legacy builders.

    Newer builders pass rich frame specs directly to label_tree().  This fallback
    keeps older registered builders from surfacing as unlabeled node groups in
    the GN Stack without adding duplicate frames on repeated builds.
    """
    if tree is None:
        return None
    has_frame = any(getattr(node, "bl_idname", "") == "NodeFrame" for node in getattr(tree, "nodes", []))
    if has_frame:
        return label_tree(tree, tree_name)
    category_label = CATEGORY_META.get(category, {}).get("label", "Melodia")
    return label_tree(tree, tree_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": category_label, "nodes": (), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


STUDIO_LABELS: dict[str, dict[str, str]] = {
    "GAZEBO": {
        "ui_label": "Gazebo",
        "mel_tree": "MEL_gazebo",
        "category": "Structures",
        "panel_hint": "Radial pavilion with columns, roof, and finial.",
    },
    "PORTICO": {
        "ui_label": "Portico",
        "mel_tree": "MEL_portico",
        "category": "Structures",
        "panel_hint": "Classical entry assembly for facade composition.",
    },
    "ARCH": {
        "ui_label": "Arch",
        "mel_tree": "MEL_arch",
        "category": "Structures",
        "panel_hint": "Editable two-column arch with swept crown.",
    },
    "TREBLE_CLEF": {
        "ui_label": "Treble Clef",
        "mel_tree": "MEL_music_treble_clef",
        "category": "Musical Notation",
        "panel_hint": "Decorative G-clef curve for staff and rail pieces.",
    },
    "NOTE_HEAD": {
        "ui_label": "Note Head",
        "mel_tree": "MEL_music_note_head",
        "category": "Musical Notation",
        "panel_hint": "Editable musical note head with stem, flag, and attributes.",
    },
    "STAFF": {
        "ui_label": "Music Staff",
        "mel_tree": "MEL_music_staff",
        "category": "Musical Notation",
        "panel_hint": "Five-line staff with bars and optional treble clef.",
    },
    "SHEET_MUSIC_RAIL": {
        "ui_label": "Sheet Music Rail",
        "mel_tree": "MEL_music_sheet_rail",
        "category": "Musical Notation",
        "panel_hint": "Railing composed from staff lines, notes, and posts.",
    },
    "MELODIA_NOTE_HEAD": {
        "ui_label": "Note Head",
        "mel_tree": "MEL_music_note_head",
        "category": "Musical Notation",
        "panel_hint": "GN Stack note-head primitive.",
    },
    "MELODIA_TREBLE_CLEF": {
        "ui_label": "Treble Clef",
        "mel_tree": "MEL_music_treble_clef",
        "category": "Musical Notation",
        "panel_hint": "GN Stack treble-clef primitive.",
    },
    "MELODIA_STAFF": {
        "ui_label": "Music Staff",
        "mel_tree": "MEL_music_staff",
        "category": "Musical Notation",
        "panel_hint": "GN Stack staff primitive.",
    },
    "MELODIA_HARMONIC": {
        "ui_label": "Harmonic Driver",
        "mel_tree": "MEL_music_harmonic",
        "category": "Musical Notation",
        "panel_hint": "Pitch-attribute driver for phrase composition.",
    },
    "MELODIA_PHRASE": {
        "ui_label": "Music Phrase",
        "mel_tree": "MEL_music_phrase",
        "category": "Musical Notation",
        "panel_hint": "Composite staff, notes, harmonic attributes, and clef.",
    },
    "ORN_VINE": {
        "ui_label": "Vine Ornament",
        "mel_tree": "MEL_ornament_vine",
        "category": "Ornament",
        "panel_hint": "Art Nouveau vine curve with editable thickness.",
    },
    "ORN_RADIAL": {
        "ui_label": "Gothic Radial",
        "mel_tree": "MEL_ornament_radial",
        "category": "Ornament",
        "panel_hint": "Radial gothic spokes and rings using array composition.",
    },
    "ORN_FRAME": {
        "ui_label": "Ornament Frame",
        "mel_tree": "MEL_ornament_frame",
        "category": "Ornament",
        "panel_hint": "Bounding-box frame for panels and insets.",
    },
    "ORN_PANEL": {
        "ui_label": "Ornament Panel",
        "mel_tree": "MEL_ornament_panel",
        "category": "Ornament",
        "panel_hint": "Composite panel with style selector and frame.",
    },
    "ORN_GRID": {
        "ui_label": "Ornament Grid",
        "mel_tree": "MEL_ornament_grid",
        "category": "Ornament",
        "panel_hint": "Arabesque-style geometric grid ornament.",
    },
    "CASTLE_TOWER": {
        "ui_label": "Castle Tower",
        "mel_tree": "MEL_castle_tower",
        "category": "Castle Kit",
        "panel_hint": "Melodia castle tower node group.",
    },
    "CASTLE_GATEHOUSE": {
        "ui_label": "Castle Gatehouse",
        "mel_tree": "MEL_castle_gatehouse",
        "category": "Castle Kit",
        "panel_hint": "Melodia castle gatehouse node group.",
    },
    "CASTLE_KEEP": {
        "ui_label": "Castle Keep",
        "mel_tree": "MEL_castle_keep",
        "category": "Castle Kit",
        "panel_hint": "Melodia castle keep node group.",
    },
    "CASTLE_CRENELLATION": {
        "ui_label": "Castle Crenellation",
        "mel_tree": "MEL_castle_crenellation",
        "category": "Castle Kit",
        "panel_hint": "Battlement top with editable merlon count.",
    },
    "CASTLE_WALL_SEGMENT": {
        "ui_label": "Castle Wall Segment",
        "mel_tree": "MEL_castle_wall_segment",
        "category": "Castle Kit",
        "panel_hint": "Wall body with optional crenellation.",
    },
    "CASTLE_GOTHIC_WINDOW": {
        "ui_label": "Castle Gothic Window",
        "mel_tree": "MEL_castle_gothic_window",
        "category": "Castle Kit",
        "panel_hint": "Pointed arch window and tracery group.",
    },
    "CASTLE_BUTTRESS": {
        "ui_label": "Castle Buttress",
        "mel_tree": "MEL_castle_buttress",
        "category": "Castle Kit",
        "panel_hint": "Flying buttress support piece.",
    },
    "CASTLE_CURTAIN_WALL": {
        "ui_label": "Castle Curtain Wall",
        "mel_tree": "MEL_castle_curtain_wall",
        "category": "Castle Kit",
        "panel_hint": "Span wall with walkway and supports.",
    },
    "CASTLE_MACHICOLATIONS": {
        "ui_label": "Castle Machicolations",
        "mel_tree": "MEL_castle_machicolations",
        "category": "Castle Kit",
        "panel_hint": "Projecting parapet with murder holes.",
    },
    "CASTLE_SPIRAL_STAIRS": {
        "ui_label": "Castle Spiral Stairs",
        "mel_tree": "MEL_castle_spiral_stairs",
        "category": "Castle Kit",
        "panel_hint": "Helical stair tower component.",
    },
    "CASTLE_ASSEMBLER": {
        "ui_label": "Castle Full Assembler",
        "mel_tree": "MEL_castle_assembler",
        "category": "Castle Kit",
        "panel_hint": "Full castle composition group.",
    },
    "CASTLE_DRAWBRIDGE": {
        "ui_label": "Castle Drawbridge",
        "mel_tree": "MEL_castle_drawbridge",
        "category": "Castle Kit",
        "panel_hint": "Plank drawbridge with chain suspension and hinge.",
    },
    "CASTLE_CORNER_BASTION": {
        "ui_label": "Castle Corner Bastion",
        "mel_tree": "MEL_castle_corner_bastion",
        "category": "Castle Kit",
        "panel_hint": "90-degree wall junction with corner tower.",
    },
    "RECURSIVE_SPIRE": {
        "ui_label": "Recursive Castle Spire",
        "mel_tree": "MEL_recursive_castle_spire",
        "category": "Castle Kit",
        "panel_hint": "Fractal recursive spire with golden ratio scaling.",
    },
    "ESCHER_BRIDGE": {
        "ui_label": "Endless Escher Bridge",
        "mel_tree": "MEL_endless_escher_bridge",
        "category": "Castle Kit",
        "panel_hint": "Impossible endless stair bridge with sine modulation.",
    },
    "MATH_GOTHIC_CATHEDRAL": {
        "ui_label": "Math Gothic Cathedral",
        "mel_tree": "MEL_math_gothic_cathedral",
        "category": "Castle Kit",
        "panel_hint": "Parabolic vaulted nave with polar rose window.",
    },
    "NIKKI_FLORA_QUARTER": {
        "ui_label": "Nikki Flora Quarter",
        "mel_tree": "MEL_nikki_quarter",
        "category": "Structures",
        "panel_hint": "Infinity Nikki themed architecture: townhouse, pavilion, "
                    "spire, and ruin modes with fully editable parameters.",
    },
    "ESCHER_PENROSE_STAIRS": {
        "ui_label": "Escher Penrose Stairs",
        "mel_tree": "MEL_escher_penrose_stairs",
        "category": "Castle Kit",
        "panel_hint": "Impossible ascending staircase loop (Ascending and "
                     "Descending) with an endless second tier.",
    },
    "ESCHER_BELVEDERE": {
        "ui_label": "Escher Belvedere",
        "mel_tree": "MEL_escher_belvedere",
        "category": "Castle Kit",
        "panel_hint": "Rotated two-story loggia with threading columns and a broken stair read.",
    },
    "ESCHER_WATERFALL": {
        "ui_label": "Escher Waterfall",
        "mel_tree": "MEL_escher_waterfall",
        "category": "Castle Kit",
        "panel_hint": "Impossible perpetually-descending water channel loop "
                    "with cascade, splash ring, pillars, and tribar arch.",
    },
    "SKY_OBSERVATORY": {
        "ui_label": "Celestial Dream Observatory",
        "mel_tree": "MEL_sky_observatory",
        "category": "Structures",
        "panel_hint": "Breathtaking floating observatory hero: island, dome, "
                    "orrery rings, planets, lanterns, deck railing.",
    },
}


def iter_tree_input_items(tree):
    """Yield input interface items (Blender 4+ interface or legacy tree.inputs)."""
    iface = getattr(tree, "interface", None)
    if iface is not None:
        try:
            for item in iface.items_tree:
                if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "in_out", "") == "INPUT":
                    yield item
            return
        except Exception:
            pass
    inputs = getattr(tree, "inputs", None)
    if inputs is not None:
        for sock in inputs:
            yield sock


def tree_input_names(tree) -> list[str]:
    return [getattr(s, "name", "") for s in iter_tree_input_items(tree)]


def new_geometry_tree(name):
    """Create a new GeometryNodeTree with input/output already wired.

    Blender 4.0+ removed tree.inputs/outputs; use tree.interface instead.
    """
    old = bpy.data.node_groups.get(name)
    if old is not None:
        try:
            bpy.data.node_groups.remove(old)
            log.debug("new_geometry_tree: replaced existing tree '%s'", name)
        except Exception as exc:
            log.warning("new_geometry_tree: cannot remove old tree '%s' ΓÇö %s", name, exc)
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    try:
        tree.is_modifier = True
    except Exception:
        pass
    group_in = tree.nodes.new("NodeGroupInput")
    group_in.location = (-400, 0)
    group_out = tree.nodes.new("NodeGroupOutput")
    group_out.location = (600, 0)
    make_group_input(tree, "NodeSocketGeometry", "Geometry")
    make_group_output(tree, "NodeSocketGeometry", "Geometry")
    try:
        link_sockets(tree, group_in.outputs["Geometry"], group_out.inputs["Geometry"])
    except Exception as exc:
        log.warning(
            "new_geometry_tree: cannot link default I/O on '%s' ΓÇö %s", name, exc,
        )
    color_node(group_in, "input")
    color_node(group_out, "output")
    return tree, group_in, group_out


def make_group_input(tree, socket_type, name, default=None, min_val=None, max_val=None):
    """Add an input socket to the group.
    Returns the actual NodeSocket from the Group Input node (for linking).
    """
    iface = getattr(tree, "interface", None)
    if iface is not None:
        try:
            iface_sock = iface.new_socket(name=name, in_out="INPUT", socket_type=socket_type)
        except Exception as exc:
            log.debug(
                "make_group_input: interface.new_socket failed for '%s' (%s) \u2014 %s; falling back to legacy",
                name, socket_type, exc,
            )
            iface_sock = None
    else:
        iface_sock = None
    if iface_sock is not None:
        if default is not None:
            try:
                iface_sock.default_value = default
            except Exception:
                pass
        if min_val is not None:
            try:
                iface_sock.min_value = min_val
            except Exception:
                pass
        if max_val is not None:
            try:
                iface_sock.max_value = max_val
            except Exception:
                pass
        # Return the actual NodeSocket from the Group Input node for linking
        for node in tree.nodes:
            if node.type == "GROUP_INPUT":
                node_sock = node.outputs.get(name)
                if node_sock is not None:
                    return node_sock
        return iface_sock
    # Legacy fallback for Blender <4.0
    inputs = getattr(tree, "inputs", None)
    if inputs is not None:
        try:
            sock = inputs.new(socket_type, name)
        except Exception as exc:
            log.warning(
                "make_group_input: cannot create input '%s' (%s) in tree '%s' ΓÇö %s",
                    name, socket_type, getattr(tree, "name", "?"), exc,
            )
            return None
    else:
            log.warning(
                "make_group_input: no interface.inputs on tree '%s'",
                getattr(tree, "name", "?"),
            )
            return None
    if default is not None:
        try:
            sock.default_value = default
        except Exception as exc:
            log.debug("make_group_input: cannot set default on '%s' ΓÇö %s", name, exc)
    if min_val is not None:
        try:
            sock.min_value = min_val
        except Exception as exc:
            log.debug("make_group_input: cannot set min on '%s' ΓÇö %s", name, exc)
    if max_val is not None:
        try:
            sock.max_value = max_val
        except Exception as exc:
            log.debug("make_group_input: cannot set max on '%s' ΓÇö %s", name, exc)
    return sock


def make_group_output(tree, socket_type, name):
    iface = getattr(tree, "interface", None)
    if iface is not None:
        try:
            return iface.new_socket(name=name, in_out="OUTPUT", socket_type=socket_type)
        except Exception as exc:
            log.debug(
                "make_group_output: interface.new_socket failed for '%s' ΓÇö %s",
                name, exc,
            )
    outputs = getattr(tree, "outputs", None)
    if outputs is not None:
        try:
            return outputs.new(socket_type, name)
        except Exception as exc:
            log.warning(
                "make_group_output: cannot create output '%s' in tree '%s' ΓÇö %s",
                name, getattr(tree, "name", "?"), exc,
            )
            return None
    return None


def link_float_to_vector(tree, source_sock, target_node, target_input_name, component=0, defaults=None):
    """Link a float socket to one component of a vector input.

    Blender 5.1 removed vector socket .inputs sub-sockets, so we must
    use a CombineXYZ node as bridge. `component` is 0=X, 1=Y, 2=Z.
    `defaults` is a 3-tuple for the other two components (None = (0,0,0)).
    """
    if source_sock is None or target_node is None:
        log.debug(
            "link_float_to_vector: skipping ΓÇö source=%s target=%s",
            source_sock, getattr(target_node, "name", None),
        )
        return
    vec_sock = target_node.inputs.get(target_input_name)
    if vec_sock is None:
        log.warning(
            "link_float_to_vector: '%s' input not found on node '%s'",
            target_input_name, getattr(target_node, "name", "?"),
        )
        return

    # Reuse an existing bridge for this vector socket. Rebuilding a complete
    # CombineXYZ on every component call causes later links to replace earlier
    # ones, silently zeroing dimensions such as Width/Depth/Height.
    combine = None
    for link in tree.links:
        if link.to_socket == vec_sock and getattr(link.from_node, "bl_idname", "") == "ShaderNodeCombineXYZ":
            combine = link.from_node
            break
    if combine is None:
        combine = safe_node(tree, "ShaderNodeCombineXYZ", (
            target_node.location.x - 180,
            target_node.location.y - 60,
        ))
        if combine is None:
            log.warning("link_float_to_vector: CombineXYZ unavailable")
            return
        d = list(defaults) if defaults else [0.0, 0.0, 0.0]
        for i, val in enumerate(d):
            sock_name = ["X", "Y", "Z"][i]
            if isinstance(val, (int, float)):
                try:
                    combine.inputs[sock_name].default_value = val
                except Exception:
                    pass
            else:
                try:
                    tree.links.new(val, combine.inputs[sock_name])
                except Exception:
                    pass
        try:
            tree.links.new(combine.outputs["Vector"], vec_sock)
        except Exception:
            pass

    if component not in (0, 1, 2):
        log.warning("link_float_to_vector: invalid component %s", component)
        return
    component_socket = combine.inputs[["X", "Y", "Z"][component]]
    for link in list(tree.links):
        if link.to_socket == component_socket:
            tree.links.remove(link)
    try:
        tree.links.new(source_sock, component_socket)
    except Exception as exc:
        log.warning("link_float_to_vector: cannot link component %s -- %s", component, exc)


def add_float_param(tree, name, default=0.0, min_val=0.0, max_val=1.0, description=""):
    return make_group_input(tree, "NodeSocketFloat", name, default, min_val, max_val)


def add_int_param(tree, name, default=0, min_val=0, max_val=100, description=""):
    return make_group_input(tree, "NodeSocketInt", name, default, min_val, max_val)


def add_bool_param(tree, name, default=False, description=""):
    return make_group_input(tree, "NodeSocketBool", name, default)


def add_vector_param(tree, name, default=(0.0, 0.0, 0.0), description=""):
    return make_group_input(tree, "NodeSocketVector", name, default)


def add_mesh_torus(tree, loc, major_radius=1.5, minor_radius=0.25,
                   major_segments=48, minor_segments=12):
    """Blender 5.x replacement for the removed MeshTorus node.

    Builds a torus-shaped mesh from two curve circles (path + profile)
    swept through Curve-to-Mesh. Returns the CurveToMesh node so callers
    can wire ``outputs["Mesh"]`` as before.
    """
    path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1]))
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1] - 140))
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (loc[0], loc[1]))
    if not (path and profile and sweep):
        return None
    path.inputs["Resolution"].default_value = major_segments
    profile.inputs["Resolution"].default_value = minor_segments
    path.inputs["Radius"].default_value = major_radius
    profile.inputs["Radius"].default_value = minor_radius
    link_sockets(tree, path.outputs["Curve"], sweep.inputs["Curve"])
    link_sockets(tree, profile.outputs["Curve"], sweep.inputs["Profile Curve"])
    return sweep


def add_mesh_torus_linked(tree, loc, major_radius_sock, minor_radius_sock,
                          major_segments_sock=None, minor_segments_sock=None,
                          major_segments=48, minor_segments=12):
    """MeshTorus replacement with group-input socket links instead of defaults."""
    path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1]))
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1] - 140))
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (loc[0], loc[1]))
    if not (path and profile and sweep):
        return None
    link_sockets(tree, major_radius_sock, path.inputs["Radius"])
    link_sockets(tree, minor_radius_sock, profile.inputs["Radius"])
    if major_segments_sock is not None:
        link_sockets(tree, major_segments_sock, path.inputs["Resolution"])
    else:
        path.inputs["Resolution"].default_value = major_segments
    if minor_segments_sock is not None:
        link_sockets(tree, minor_segments_sock, profile.inputs["Resolution"])
    else:
        profile.inputs["Resolution"].default_value = minor_segments
    link_sockets(tree, path.outputs["Curve"], sweep.inputs["Curve"])
    link_sockets(tree, profile.outputs["Curve"], sweep.inputs["Profile Curve"])
    return sweep


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Builder registry ΓÇö populated by each module via register_builder()
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

GROUP_BUILDERS: dict[str, callable] = {}
GROUP_METADATA: dict[str, dict] = {}

CATEGORY_META: dict[str, dict] = {
    "primitives":  {"label": "Primitives",          "icon": "MESH_GRID"},
    "profiles":    {"label": "Profiles",             "icon": "MESH_CYLINDER"},
    "math_attrs":  {"label": "Math & Attributes",    "icon": "NODETREE"},
    "structures":  {"label": "Structures",           "icon": "HOME"},
    "effects":     {"label": "Magic Effects",        "icon": "SHADERFX"},
    "ornament":    {"label": "Ornament",             "icon": "DECORATE"},
    "filigree":    {"label": "Filigree & Crests",    "icon": "MOD_CURVE"},
    "music":       {"label": "Musical Notation",     "icon": "FILE_SOUND"},
    "castle":      {"label": "Castle Kit",           "icon": "MOD_BUILD"},
    "operations":  {"label": "Operations",           "icon": "AUTOMERGE_ON"},
    "mesh_tools":  {"label": "Mesh Tools",           "icon": "EDITMODE_HLT"},
    "set_dressing": {"label": "Set Dressing",        "icon": "PLUGIN"},
}


def register_builder(tree_name, builder_fn, label, description="", category=""):
    """Register a GN tree builder into the global registry.

    Called at module-import time by each builder module.  All derived
    data structures (TREE_TYPES, TREE_DESCRIPTIONS, etc.) are lazily
    rebuilt by _rebuild_derived_data() which __init__.py calls after
    all sub-modules have been imported.
    """
    def _labeled_builder(*args, **kwargs):
        result = builder_fn(*args, **kwargs)
        # Builders may return (tree, gin, gout) tuple or just tree
        tree = result[0] if isinstance(result, (tuple, list)) else result
        return ensure_labeled_tree(tree, tree_name, category)

    GROUP_BUILDERS[tree_name] = _labeled_builder
    GROUP_METADATA[tree_name] = {
        "label":       label,
        "description": description,
        "category":    category,
        "builder":     builder_fn,
    }


# Derived data (rebuilt by __init__.py after all builder registrations)
TREE_TYPES: list[tuple[str, str]] = []
TREE_LABEL_MAP: dict[str, str] = {}
TREE_DESCRIPTIONS: dict[str, str] = {}
TREE_CATEGORY_MAP: dict[str, str] = {}
TREE_CATEGORIES: dict[str, dict] = {}


def _rebuild_derived_data():
    """Rebuild all lookup tables from GROUP_METADATA after all registrations.

    Called once by __init__.py after importing every builder module.
    Idempotent ΓÇö safe to call on addon reload.
    """
    global TREE_TYPES, TREE_LABEL_MAP, TREE_DESCRIPTIONS, TREE_CATEGORY_MAP, TREE_CATEGORIES

    TREE_TYPES = sorted(
        [(name, meta["label"]) for name, meta in GROUP_METADATA.items()],
        key=lambda x: x[1],
    )
    TREE_LABEL_MAP = {name: meta["label"] for name, meta in GROUP_METADATA.items()}
    TREE_DESCRIPTIONS = {
        name: meta["description"]
        for name, meta in GROUP_METADATA.items()
        if meta["description"]
    }
    TREE_CATEGORY_MAP = {
        name: meta["category"]
        for name, meta in GROUP_METADATA.items()
        if meta["category"]
    }

    # Build categorized lookup (category_id ΓåÆ {label, icon, trees})
    cats: dict[str, dict] = {}
    for cid, cinfo in CATEGORY_META.items():
        cats[cid] = {
            "label": cinfo["label"],
            "icon":  cinfo["icon"],
            "trees": [],
        }
    for name, meta in GROUP_METADATA.items():
        cid = meta.get("category", "")
        if cid in cats:
            cats[cid]["trees"].append(name)
    TREE_CATEGORIES = cats
