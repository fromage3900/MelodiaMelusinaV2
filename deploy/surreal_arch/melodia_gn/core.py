"""Core GN tree builder utilities -- safe node creation, linking, coloring."""

from __future__ import annotations

import bpy
import math

from .logging import log

# Blender 5.x renames / domain moves. Applied when bpy.app.version >= (5, 0, 0).
NODE_REMAP_52 = {
    "GeometryNodeCube": "GeometryNodeMeshCube",
    "GeometryNodeUVSphere": "GeometryNodeMeshUVSphere",
    "GeometryNodeBevelMesh": "GeometryNodeMeshBevel",
    "GeometryNodeBevel": "GeometryNodeMeshBevel",
    "GeometryNodeMeshToDualMesh": "GeometryNodeDualMesh",
    "GeometryNodeSeparateXYZ": "ShaderNodeSeparateXYZ",
    "GeometryNodeCombineXYZ": "ShaderNodeCombineXYZ",
    "ShaderNodeCombineColor": "FunctionNodeCombineColor",
    "ShaderNodeSeparateColor": "FunctionNodeSeparateColor",
    "ShaderNodeTime": "GeometryNodeInputSceneTime",
}


def _resolve_bl_idname(bl_idname: str) -> str:
    if bpy.app.version >= (5, 0, 0):
        return NODE_REMAP_52.get(bl_idname, bl_idname)
    return bl_idname


def sock(node, *names, outputs=False):
    """Return the first matching input/output socket by name, or None."""
    if node is None:
        return None
    collection = node.outputs if outputs else node.inputs
    for name in names:
        try:
            s = collection.get(name)
        except Exception:
            s = None
        if s is not None:
            return s
    for name in names:
        for s in collection:
            if getattr(s, "name", None) == name:
                return s
    return None


def set_resample_count(resample, count_socket_or_value=None):
    """Map legacy ResampleCurve COUNT semantics onto Blender 5.x sockets."""
    if resample is None:
        return
    # 5.x: mode is often a menu socket defaulting to Count; property may be gone.
    try:
        resample.mode = "COUNT"
    except Exception:
        try:
            resample.mode = "OFFSET"
        except Exception:
            pass
    if count_socket_or_value is None:
        return
    target = sock(resample, "Count", "Offset", "Length")
    if target is None:
        return
    if hasattr(count_socket_or_value, "id_data"):
        # Linked as a socket elsewhere - caller should use link_sockets.
        return
    try:
        target.default_value = count_socket_or_value
    except Exception:
        pass


def safe_node(tree, bl_idname, loc, fallback_callable=None):
    """Create a node, returns None on failure. Optionally call fallback.

    Logs failure at WARNING level so users can trace missing-node issues.
    On Blender 5.x, remaps known legacy bl_idnames via NODE_REMAP_52.
    """
    resolved = _resolve_bl_idname(bl_idname)
    try:
        n = tree.nodes.new(resolved)
        n.location = loc
        return n
    except Exception as exc:
        if resolved != bl_idname:
            try:
                n = tree.nodes.new(bl_idname)
                n.location = loc
                return n
            except Exception:
                pass
        log.warning(
            "safe_node: '%s' not available in %s - %s",
            bl_idname, tree.name, exc,
        )
        if fallback_callable:
            log.debug("safe_node: attempting fallback for '%s'", bl_idname)
            try:
                return fallback_callable()
            except Exception as fb_exc:
                log.warning(
                    "safe_node: fallback also failed for '%s' - %s",
                    bl_idname, fb_exc,
                )
        return None


def require_node(tree, bl_idname, loc, *aliases):
    """Create a node or raise. Missing SKU nodes must not silently passthrough."""
    tried = (bl_idname,) + tuple(aliases)
    for name in tried:
        node = safe_node(tree, name, loc)
        if node is not None:
            return node
    raise RuntimeError(
        "GN node unavailable in %s: tried %s"
        % (getattr(tree, "name", "?"), tried)
    )


def _geometry_inputs(node):
    sockets = []
    for s in getattr(node, "inputs", []):
        stype = str(getattr(s, "type", "") or "")
        if "GEOMETRY" in stype.upper() or getattr(s, "name", "") in (
            "Mesh", "Mesh 1", "Mesh 2", "Geometry",
        ):
            sockets.append(s)
    return sockets


def mesh_boolean_node(tree, loc, operation, mesh_a, mesh_b):
    """Mesh Boolean with Blender 5.2 socket names.

    DIFFERENCE: mesh_a minus mesh_b (Mesh 1 - Mesh 2).
    UNION: mesh_a union mesh_b.
    Returns (node, mesh_output_socket).
    """
    node = require_node(tree, "GeometryNodeMeshBoolean", loc)
    try:
        node.operation = operation
    except Exception:
        op_in = sock(node, "Operation")
        if op_in is not None:
            try:
                op_in.default_value = operation
            except Exception:
                pass
    try:
        node.solver = "EXACT"
    except Exception:
        pass
    a_in = sock(node, "Mesh 1", "Mesh", "Geometry")
    b_in = None
    try:
        b_in = node.inputs.get("Mesh 2")
    except Exception:
        b_in = None
    geos = _geometry_inputs(node)
    if b_in is None:
        if a_in is not None:
            b_in = next((s for s in geos if s != a_in), None)
        if b_in is None and len(geos) >= 2:
            a_in, b_in = geos[0], geos[1]
        elif b_in is None and len(geos) == 1:
            a_in = b_in = geos[0]
    if a_in is None:
        a_in = node.inputs[0]
    if b_in is None:
        b_in = node.inputs[1] if len(node.inputs) > 1 else a_in
    link_sockets(tree, mesh_a, a_in)
    link_sockets(tree, mesh_b, b_in)
    out = sock(node, "Mesh", "Geometry", outputs=True)
    if out is None:
        out = node.outputs[0]
    return node, out


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
            "link_sockets: cannot link %s → %s in %s — %s",
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
        log.debug("color_node: cannot color node '%s' — %s", getattr(node, "name", "?"), exc)


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
        "panel_hint": "Radial pavilion with columns, engawa deck, roof, and finial.",
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
        "panel_hint": "Walkable staff railing: posts, five swept lines, notes at pitch-height.",
    },
    "MUSIC_KEY_UNIT": {
        "ui_label": "Music Key Unit",
        "mel_tree": "MEL_music_key_unit",
        "category": "Musical Notation",
        "panel_hint": "Life-size piano key: box plus front lip, accidental switch, pitch.",
    },
    "MUSIC_PIANO_ROLL": {
        "ui_label": "Music Piano Roll",
        "mel_tree": "MEL_music_piano_roll",
        "category": "Musical Notation",
        "panel_hint": "Instance keys on a spline. Profile 0-3: PIANO / XYLO / MARIMBA / GLOCK.",
    },
    "MUSIC_HARP": {
        "ui_label": "Music Harp",
        "mel_tree": "MEL_music_harp",
        "category": "Musical Notation",
        "panel_hint": "Pedal harp: pillar, neck curve, strings on spline, soundboard, pitch index.",
    },
    "MUSIC_ROOM_SHELL": {
        "ui_label": "Music Room Shell",
        "mel_tree": "MEL_music_room_shell",
        "category": "Structures",
        "panel_hint": "Greybox hollow room with openings and optional dado staff band.",
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
        "panel_hint": "Pointed portal/bay window with tracery (gothic_kit language).",
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
        "panel_hint": "Full castle composition with default keep/towers/walls seed.",
    },
    "STEPPED_PYRAMID": {
        "ui_label": "Stepped Pyramid",
        "mel_tree": "MEL_stepped_pyramid",
        "category": "Primitives",
        "panel_hint": "Stacked shrinking terraces with wired XY size.",
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
    "EFFECT_MAGIC": {
        "ui_label": "Magic Distortion",
        "mel_tree": "MEL_effect_magic",
        "category": "Magic Effects",
        "panel_hint": "Combined magical distortion - intensity, noise, layers, chromatic, attractor.",
    },
    "EFFECT_WAVE": {
        "ui_label": "Wave Effect",
        "mel_tree": "MEL_effect_wave",
        "category": "Magic Effects",
        "panel_hint": "Sine-wave displacement along an axis, with normal-space toggle.",
    },
    "FILIGREE_SPIRAL": {
        "ui_label": "Filigree Spiral",
        "mel_tree": "MEL_filigree_spiral",
        "category": "Filigree and Crests",
        "panel_hint": "Art Nouveau logarithmic filigree scroll with tapered profile.",
    },
    "FILIGREE_CORNER_VOLUTE": {
        "ui_label": "Filigree Corner Volute",
        "mel_tree": "MEL_filigree_corner_volute",
        "category": "Filigree and Crests",
        "panel_hint": "Corner volute scroll with tapered profile and finial.",
    },
    "FILIGREE_FINIAL_CROSS": {
        "ui_label": "Filigree Finial Cross",
        "mel_tree": "MEL_filigree_finial_cross",
        "category": "Filigree and Crests",
        "panel_hint": "Bar-and-ball finial cross for spire and crest tips.",
    },
    "FILIGREE_WREATH_RING": {
        "ui_label": "Filigree Wreath Ring",
        "mel_tree": "MEL_filigree_wreath_ring",
        "category": "Filigree and Crests",
        "panel_hint": "Laurel wreath ring with tilted leaves.",
    },
    "CIRCULAR_ARRAY": {
        "ui_label": "Circular Array",
        "mel_tree": "MEL_circular_array",
        "category": "Primitives",
        "panel_hint": "Instance geometry on a circle - cockpit GN Stack smoke click.",
    },
    "GREYBOX_ROOM_KIT": {
        "ui_label": "Greybox Room Kit",
        "mel_tree": "MEL_greybox_room_kit",
        "category": "Structures",
        "panel_hint": "Hollow room shell with wall thickness and optional ceiling.",
    },
    "GREYBOX_OPENINGS": {
        "ui_label": "Greybox Openings",
        "mel_tree": "MEL_greybox_openings",
        "category": "Structures",
        "panel_hint": "Door and window boolean cuts for greybox interiors.",
    },
    "GREYBOX_CORRIDOR": {
        "ui_label": "Greybox Corridor",
        "mel_tree": "MEL_greybox_corridor",
        "category": "Structures",
        "panel_hint": "Tileable hollow hall with optional end caps.",
    },
    "GREYBOX_JUNCTION": {
        "ui_label": "Greybox Junction",
        "mel_tree": "MEL_greybox_junction",
        "category": "Structures",
        "panel_hint": "T or X join of corridor volumes, then shell.",
    },
    "GREYBOX_COMPOSER": {
        "ui_label": "Greybox Composer",
        "mel_tree": "MEL_greybox_composer",
        "category": "Structures",
        "panel_hint": "Join room, corridor, and junction groups (snap later).",
    },
    "COLUMN": {
        "ui_label": "Column",
        "mel_tree": "MEL_column",
        "category": "Profiles",
        "panel_hint": "Classical column profile with editable radius and height.",
    },
    "BEVEL_PROFILE": {
        "ui_label": "Bevel Profile",
        "mel_tree": "MEL_bevel_profile",
        "category": "Mesh Tools",
        "panel_hint": "Weighted bevel with profile control for live mesh edges.",
    },
    "ADD_GEOMETRY": {
        "ui_label": "Add (Union)",
        "mel_tree": "MEL_add_geometry",
        "category": "Math and Attributes",
        "panel_hint": "Boolean union compose helper.",
    },
    "OP_ITERATE": {
        "ui_label": "Iterate + Power Falloff",
        "mel_tree": "MEL_op_iterate",
        "category": "Operations",
        "panel_hint": "Instance N times along an axis with power-scale falloff.",
    },
    "WATER_THEM_GAZEBO": {
        "ui_label": "Water-Themed Gazebo",
        "mel_tree": "MEL_water_them_gazebo",
        "category": "Set Dressing",
        "panel_hint": "Existing water gazebo (no new Set Dressing factories).",
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
            log.warning("new_geometry_tree: cannot remove old tree '%s' — %s", name, exc)
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
            "new_geometry_tree: cannot link default I/O on '%s' — %s", name, exc,
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
                "make_group_input: cannot create input '%s' (%s) in tree '%s' — %s",
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
            log.debug("make_group_input: cannot set default on '%s' — %s", name, exc)
    if min_val is not None:
        try:
            sock.min_value = min_val
        except Exception as exc:
            log.debug("make_group_input: cannot set min on '%s' — %s", name, exc)
    if max_val is not None:
        try:
            sock.max_value = max_val
        except Exception as exc:
            log.debug("make_group_input: cannot set max on '%s' — %s", name, exc)
    return sock


def make_group_output(tree, socket_type, name):
    iface = getattr(tree, "interface", None)
    if iface is not None:
        try:
            return iface.new_socket(name=name, in_out="OUTPUT", socket_type=socket_type)
        except Exception as exc:
            log.debug(
                "make_group_output: interface.new_socket failed for '%s' — %s",
                name, exc,
            )
    outputs = getattr(tree, "outputs", None)
    if outputs is not None:
        try:
            return outputs.new(socket_type, name)
        except Exception as exc:
            log.warning(
                "make_group_output: cannot create output '%s' in tree '%s' — %s",
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
            "link_float_to_vector: skipping — source=%s target=%s",
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


def mesh_line_to_curve(tree, loc, mesh_sock):
    """Convert a Mesh Line / Mesh Circle into a curve for Curve-to-Mesh."""
    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", loc)
    if to_curve is None:
        return mesh_sock
    link_sockets(tree, mesh_sock, to_curve.inputs.get("Mesh") or to_curve.inputs[0])
    return to_curve.outputs.get("Curve") or to_curve.outputs.get("Geometry")


def sweep_profile(tree, loc, curve_or_mesh_sock, radius_sock, profile_res=8, already_curve=False):
    """AAA railing / vault pattern: curve + circle profile -> mesh."""
    curve_sock = curve_or_mesh_sock
    if not already_curve:
        curve_sock = mesh_line_to_curve(tree, (loc[0] - 180, loc[1]), curve_or_mesh_sock)
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 180, loc[1] - 140))
    if profile is None:
        profile = safe_node(tree, "GeometryNodeMeshCircle", (loc[0] - 180, loc[1] - 140))
    try:
        profile.inputs["Resolution"].default_value = profile_res
    except Exception:
        pass
    try:
        profile.inputs["Vertices"].default_value = profile_res
    except Exception:
        pass
    if radius_sock is not None:
        try:
            link_sockets(tree, radius_sock, profile.inputs["Radius"])
        except Exception:
            pass
    # Rotate profile 90deg X so it stands perpendicular to the curve.
    # Without this, the circle lies flat and produces zero-area faces.
    prof_xf = safe_node(tree, "GeometryNodeTransform", (loc[0] - 80, loc[1] - 140))
    if prof_xf:
        link_sockets(tree, profile.outputs.get("Curve") or profile.outputs[0],
                     prof_xf.inputs["Geometry"])
        try:
            prof_xf.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
        except Exception:
            pass
        prof_out = prof_xf.outputs["Geometry"]
    else:
        prof_out = profile.outputs.get("Curve") or profile.outputs[0]
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", loc)
    link_sockets(tree, curve_sock, sweep.inputs.get("Curve") or sweep.inputs[0])
    prof_in = sweep.inputs.get("Profile Curve") or sweep.inputs.get("Profile")
    if prof_in is not None:
        link_sockets(tree, prof_out, prof_in)
    return sweep.outputs.get("Mesh") or sweep.outputs.get("Geometry")


def add_music_influence_params(tree):
    """Sockets for the Universal Musical Influence post-pass (default 0 = no warp)."""
    add_float_param(tree, "Music Influence", 0.0, 0.0, 1.0)
    add_float_param(tree, "Musical Amplitude", 1.0, 0.0, 4.0)
    add_float_param(tree, "Musical Freq A", 2.0, 0.1, 12.0)
    add_float_param(tree, "Musical Freq B", 3.0, 0.1, 12.0)


def apply_universal_music_pass(tree, gin, geom, loc=(2400, 0)):
    """Radial harmonic pulse - same math as monolith add_universal_music_pass.

    Gated by Music Influence (skip wiring warp when socket missing).
    """
    inf = gin.outputs.get("Music Influence")
    if inf is None or geom is None:
        return geom
    x, y = loc
    pos = safe_node(tree, "GeometryNodeInputPosition", (x, y + 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (x + 200, y + 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    z_freq = safe_node(tree, "ShaderNodeMath", (x + 400, y + 200))
    z_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Z"], z_freq.inputs[0])
    fa = gin.outputs.get("Musical Freq A")
    if fa is not None:
        link_sockets(tree, fa, z_freq.inputs[1])
    else:
        z_freq.inputs[1].default_value = 2.0
    sine_z = safe_node(tree, "ShaderNodeMath", (x + 600, y + 200))
    sine_z.operation = "SINE"
    link_sockets(tree, z_freq.outputs[0], sine_z.inputs[0])
    atan2 = safe_node(tree, "ShaderNodeMath", (x + 400, y))
    atan2.operation = "ARCTAN2"
    link_sockets(tree, sep.outputs["Y"], atan2.inputs[0])
    link_sockets(tree, sep.outputs["X"], atan2.inputs[1])
    a_freq = safe_node(tree, "ShaderNodeMath", (x + 600, y))
    a_freq.operation = "MULTIPLY"
    link_sockets(tree, atan2.outputs["Value"], a_freq.inputs[0])
    fb = gin.outputs.get("Musical Freq B")
    if fb is not None:
        link_sockets(tree, fb, a_freq.inputs[1])
    else:
        a_freq.inputs[1].default_value = 3.0
    sine_a = safe_node(tree, "ShaderNodeMath", (x + 800, y))
    sine_a.operation = "SINE"
    link_sockets(tree, a_freq.outputs["Value"], sine_a.inputs[0])
    addn = safe_node(tree, "ShaderNodeMath", (x + 800, y + 100))
    addn.operation = "ADD"
    link_sockets(tree, sine_z.outputs[0], addn.inputs[0])
    link_sockets(tree, sine_a.outputs[0], addn.inputs[1])
    amp = safe_node(tree, "ShaderNodeMath", (x + 1000, y + 100))
    amp.operation = "MULTIPLY"
    link_sockets(tree, addn.outputs[0], amp.inputs[0])
    ma = gin.outputs.get("Musical Amplitude")
    if ma is not None:
        link_sockets(tree, ma, amp.inputs[1])
    else:
        amp.inputs[1].default_value = 1.0
    scaled = safe_node(tree, "ShaderNodeMath", (x + 1200, y + 100))
    scaled.operation = "MULTIPLY"
    link_sockets(tree, amp.outputs[0], scaled.inputs[0])
    link_sockets(tree, inf, scaled.inputs[1])
    rxy = safe_node(tree, "ShaderNodeCombineXYZ", (x + 800, y - 200))
    link_sockets(tree, sep.outputs["X"], rxy.inputs["X"])
    link_sockets(tree, sep.outputs["Y"], rxy.inputs["Y"])
    rxy.inputs["Z"].default_value = 0.0
    norm = safe_node(tree, "ShaderNodeVectorMath", (x + 1000, y - 200))
    norm.operation = "NORMALIZE"
    link_sockets(tree, rxy.outputs["Vector"], norm.inputs[0])
    pulse = safe_node(tree, "ShaderNodeVectorMath", (x + 1200, y - 100))
    pulse.operation = "SCALE"
    link_sockets(tree, norm.outputs["Vector"], pulse.inputs[0])
    link_sockets(tree, scaled.outputs[0], pulse.inputs["Scale"])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (x + 1400, y))
    link_sockets(tree, geom, set_pos.inputs["Geometry"])
    link_sockets(tree, pulse.outputs[0], set_pos.inputs["Offset"])
    color_node(set_pos, "universal")
    return set_pos.outputs["Geometry"]


def input_geometry_with_default(tree, gin, loc, kind="ico"):
    """Modifier default seed: ico-sphere or grid when Use Default Seed is on."""
    add_bool_param(tree, "Use Default Seed", True)
    if kind == "grid":
        seed = safe_node(tree, "GeometryNodeMeshGrid", loc)
        seed.inputs["Size X"].default_value = 4.0
        seed.inputs["Size Y"].default_value = 4.0
        seed.inputs["Vertices X"].default_value = 32
        seed.inputs["Vertices Y"].default_value = 32
        seed_sock = seed.outputs.get("Mesh") or seed.outputs.get("Geometry")
    else:
        seed = safe_node(tree, "GeometryNodeMeshIcoSphere", loc)
        if seed is None:
            seed = safe_node(tree, "GeometryNodeMeshUVSphere", loc)
        try:
            seed.inputs["Radius"].default_value = 1.0
        except Exception:
            pass
        try:
            seed.inputs["Subdivisions"].default_value = 3
        except Exception:
            pass
        try:
            seed.inputs["Segments"].default_value = 32
            seed.inputs["Rings"].default_value = 16
        except Exception:
            pass
        seed_sock = seed.outputs.get("Mesh") or seed.outputs.get("Geometry")
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1]))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Use Default Seed"], sw.inputs["Switch"])
    true_in = sw.inputs.get("True") or sw.inputs.get("TRUE")
    false_in = sw.inputs.get("False") or sw.inputs.get("FALSE")
    link_sockets(tree, seed_sock, true_in)
    geo_in = gin.outputs.get("Geometry")
    if geo_in is not None:
        link_sockets(tree, geo_in, false_in)
    color_node(seed, "geometry")
    return sw.outputs.get("Output") or sw.outputs.get("Geometry")


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


# ═══════════════════════════════════════════════════════════════════════
# Builder registry — populated by each module via register_builder()
# ═══════════════════════════════════════════════════════════════════════

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


def register_builder(tree_name, builder_fn, label, description="", category="",
                     hidden=False, role="sku"):
    """Register a GN tree builder into the global registry.

    hidden=True keeps the live id (RQ / blends) but omits it from GN Stack.
    role is sku | modifier | tool | factory | pcg_alias | pcg_keep.
    """
    def _labeled_builder(*args, **kwargs):
        result = builder_fn(*args, **kwargs)
        tree = result[0] if isinstance(result, (tuple, list)) else result
        return ensure_labeled_tree(tree, tree_name, category)

    GROUP_BUILDERS[tree_name] = _labeled_builder
    GROUP_METADATA[tree_name] = {
        "label":       label,
        "description": description,
        "category":    category,
        "builder":     builder_fn,
        "hidden":      bool(hidden),
        "role":        role or "sku",
    }


def is_hidden_builder(tree_name: str) -> bool:
    return bool(GROUP_METADATA.get(tree_name, {}).get("hidden"))


# Derived data (rebuilt by __init__.py after all builder registrations)
TREE_TYPES: list[tuple[str, str]] = []
TREE_LABEL_MAP: dict[str, str] = {}
TREE_DESCRIPTIONS: dict[str, str] = {}
TREE_CATEGORY_MAP: dict[str, str] = {}
TREE_CATEGORIES: dict[str, dict] = {}


def _rebuild_derived_data():
    """Rebuild all lookup tables from GROUP_METADATA after all registrations.

    Called once by __init__.py after importing every builder module.
    Idempotent - safe to call on addon reload.

    IMPORTANT: mutate existing container objects in place. Other modules
    (e.g. stack.py) bind names via `from .core import TREE_CATEGORIES` at
    import time - rebinding these globals would leave those aliases empty
    forever (Studio Health shows 165 builders while GN Stack sections stay blank).
    """
    global TREE_TYPES, TREE_LABEL_MAP, TREE_DESCRIPTIONS, TREE_CATEGORY_MAP, TREE_CATEGORIES

    new_types = sorted(
        [(name, meta["label"]) for name, meta in GROUP_METADATA.items()],
        key=lambda x: x[1],
    )
    TREE_TYPES.clear()
    TREE_TYPES.extend(new_types)

    TREE_LABEL_MAP.clear()
    TREE_LABEL_MAP.update({name: meta["label"] for name, meta in GROUP_METADATA.items()})

    TREE_DESCRIPTIONS.clear()
    TREE_DESCRIPTIONS.update(
        {
            name: meta["description"]
            for name, meta in GROUP_METADATA.items()
            if meta["description"]
        }
    )

    TREE_CATEGORY_MAP.clear()
    TREE_CATEGORY_MAP.update(
        {
            name: meta["category"]
            for name, meta in GROUP_METADATA.items()
            if meta["category"]
        }
    )

    # Build categorized lookup (category_id -> {label, icon, trees})
    cats: dict[str, dict] = {}
    for cid, cinfo in CATEGORY_META.items():
        cats[cid] = {
            "label": cinfo["label"],
            "icon": cinfo["icon"],
            "trees": [],
        }
    uncategorized: list[str] = []
    for name, meta in GROUP_METADATA.items():
        cid = meta.get("category", "")
        if cid in cats:
            cats[cid]["trees"].append(name)
        elif cid:
            uncategorized.append(name)
    # Keep unknown category ids visible in the N-panel instead of dropping them.
    for name in uncategorized:
        cid = GROUP_METADATA[name]["category"]
        if cid not in cats:
            cats[cid] = {
                "label": cid.replace("_", " ").title(),
                "icon": "NODETREE",
                "trees": [],
            }
        cats[cid]["trees"].append(name)

    TREE_CATEGORIES.clear()
    TREE_CATEGORIES.update(cats)


def purge_stale_builders():
    """Drop entries whose module failed to reload (Sync & Reload ghosts).

    Removes GROUP_METADATA entries that have no corresponding builder in
    GROUP_BUILDERS - these are ghosts left behind by `Sync & Reload` when a
    builder module is renamed or removed but its old registration lingers in
    the live Blender session. Safe to call before _rebuild_derived_data().
    """
    # GROUP_BUILDERS is the source of truth populated by register_builder()
    try:
        stale = [k for k in list(GROUP_METADATA.keys()) if k not in GROUP_BUILDERS]
    except NameError:
        return
    for k in stale:
        GROUP_METADATA.pop(k, None)
