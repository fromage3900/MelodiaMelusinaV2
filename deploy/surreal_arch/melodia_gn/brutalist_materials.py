"""BRUTALIST exterior material library - board-formed concrete to Komikaze ink.

Scope note (house Lane rule): these are SET materials. `setup_melusina_master_studio.py`
allows a full material replace on sets (Lane B) but requires the character lane (Lane A)
to keep its hybrid graphs. Nothing here touches Melusina.

"Use Komikaze wisely" means: the house already has a Komikaze signature in
`ue_proxy_kit.build_npr_halftone_material()` - a Checker dot grid gated by Layer Weight
Facing, so dots compress at grazing angles and darken the silhouette. This module
REUSES that exact construction rather than inventing a second ink look, and applies it
to the exterior surfaces it was never written for (concrete / asphalt / paving).

Deliberately NOT used: `Shader to RGB`. It is the true Komikaze ink pass but is
EEVEE-only, so any Cycles or background-preview path would render it black. The
Checker+LayerWeight construction reads the same in both engines. Keep the film look on
EEVEE (see Humber_FinalYear_Prep/EEVEE_Komikaze_Polished_Prototypes_Plan.md).

Every material is built as a PBR base PLUS a `_KOMIKAZE` twin with the identical base
colour ramp, so the team A/Bs a look by swapping one material slot instead of editing a
graph. The `Looks` dict is what the staging script iterates for the contact sheet.
"""

from __future__ import annotations

import bpy

# name suffix -> look label used by the staging/contact-sheet scripts
LOOK_SUFFIX = {
    "": "PBR",
    "_KOMIKAZE": "Komikaze",
}
LOOKS = ("PBR", "Komikaze")


def _mat(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat, nt


def _out(nt, x=1400):
    n = nt.nodes.new("ShaderNodeOutputMaterial")
    n.location = (x, 0)
    return n


# Inputs a build pass asked for but the node did not have. Populated at build time and
# asserted EMPTY by Tools/verify_brutalist_materials.py.
#
# This list exists because for the entire life of this module `Base_Color=` was passed to
# _bsdf() while the real Principled socket is `Base Color` (space, not underscore). The
# `if k in n.inputs` guard below failed, the `except Exception: pass` behind it stayed
# quiet, and every brutalist surface rendered at the Principled default grey (0.8, 0.8,
# 0.8) -- asphalt included, which is authored at 0.13. Nothing errored anywhere.
#
# A dropped input is a defect, not a fallback. Never swallow one again.
SKIPPED_INPUTS = []


def _set_input(node, name, value, ctx=""):
    """Set one socket by exact name, recording (never swallowing) a miss."""
    sock = node.inputs.get(name)
    if sock is None:
        SKIPPED_INPUTS.append("%s.%s -> %s" % (type(node).__name__, ctx or node.name, name))
        print("BRUTALIST_MAT_WARN no such input %r on %s (%s)" % (name, node.name, ctx))
        return False
    try:
        sock.default_value = value
    except Exception as exc:                      # wrong type for the socket: same class
        SKIPPED_INPUTS.append("%s.%s -> %s (%s)" % (type(node).__name__, ctx or node.name, name, exc))
        print("BRUTALIST_MAT_WARN cannot set %r on %s: %s" % (name, node.name, exc))
        return False
    return True


def _bsdf(nt, x=1100, **kw):
    n = nt.nodes.new("ShaderNodeBsdfPrincipled")
    n.location = (x, 0)
    for k, v in kw.items():
        _set_input(n, k, v, ctx="bsdf")
    return n


def _in(node, name, value):
    return _set_input(node, name, value, ctx="in")


def _ink_mask(nt, scale=6.0, x=-200, y=340):
    """The house Komikaze dot mask: checker grid x Layer Weight Facing.

    Copied from ue_proxy_kit.build_npr_halftone_material() so the exterior reads as the
    SAME ink as the character, rather than a second unrelated halftone.
    """
    grid = nt.nodes.new("ShaderNodeTexChecker")
    grid.location = (x, y)
    _in(grid, "Scale", scale)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.location = (x, y - 220)
    _in(lw, "Blend", 0.5)
    dot = nt.nodes.new("ShaderNodeMix")
    dot.location = (x + 220, y)
    dot.data_type = "RGBA"
    nt.links.new(lw.outputs["Facing"], dot.inputs["Factor"])
    dot.inputs["A"].default_value = (0.06, 0.06, 0.08, 1.0)   # ink
    dot.inputs["B"].default_value = (1.0, 1.0, 1.0, 1.0)      # paper
    # mix the dot pattern in by a constant so it reads at any scale
    mix = nt.nodes.new("ShaderNodeMix")
    mix.location = (x + 420, y)
    mix.data_type = "RGBA"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(dot.outputs["Result"], mix.inputs["A"])
    nt.links.new(grid.outputs["Color"], mix.inputs["B"])
    return mix


def _board_form(nt, base_colour, x=-200, y=-160, board_scale=1.6, grain=48.0,
                strength=0.18):
    """Board-marked formwork: horizontal board lines + aggregate grain.

    Returns (bump, tint). `tint` is `base_colour` MULTIPLIED by the greyscale board/grain
    pattern -- NOT the pattern itself.

    The original returned the raw wave/noise mix and the caller linked it straight into
    Base Color. Both sources are greyscale 0..1, so that link *replaced* the authored
    surface colour rather than detailing it: concrete lost its warm (0.60, 0.59, 0.55)
    and rendered desaturated grey in both looks, and the Komikaze branch then mixed ink
    into the grey (it reads `Base Color`'s link as its base), compounding the loss.
    Detail belongs on top of the colour; it is not the colour.
    """
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (x - 200, y)

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (x, y)
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    _in(wave, "Scale", board_scale)
    _in(wave, "Distortion", 0.0)
    _in(wave, "Detail", 0.0)
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (x, y - 260)
    _in(noise, "Scale", grain)
    _in(noise, "Detail", 6.0)
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])

    pattern = nt.nodes.new("ShaderNodeMix")          # greyscale detail field, 0..1
    pattern.location = (x + 220, y - 120)
    pattern.data_type = "RGBA"
    pattern.inputs["Factor"].default_value = 0.30
    nt.links.new(wave.outputs["Color"], pattern.inputs["A"])
    nt.links.new(noise.outputs["Color"], pattern.inputs["B"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (x + 420, y - 300)
    _in(bump, "Strength", 0.22)
    _in(bump, "Distance", 0.02)
    nt.links.new(pattern.outputs["Result"], bump.inputs["Height"])

    tint = nt.nodes.new("ShaderNodeMix")             # colour x detail -> Base Color
    tint.location = (x + 420, y - 60)
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = strength   # 0 -> flat authored colour
    tint.inputs["A"].default_value = base_colour
    nt.links.new(pattern.outputs["Result"], tint.inputs["B"])
    return bump, tint


def _vein(nt, base_colour, x=-200, y=-160, strength=0.22):
    """Alabaster: soft double-scale veining. Alabaster is quarried, not cast, so it must
    never inherit board marks -- the formwork vocabulary belongs to concrete alone."""
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (x - 200, y)

    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.location = (x, y + 60)
    _in(fine, "Scale", 3.2)
    _in(fine, "Detail", 8.0)
    _in(fine, "Roughness", 0.62)
    nt.links.new(coord.outputs["Object"], fine.inputs["Vector"])

    broad = nt.nodes.new("ShaderNodeTexNoise")
    broad.location = (x, y - 180)
    _in(broad, "Scale", 0.55)
    _in(broad, "Detail", 3.0)
    _in(broad, "Roughness", 0.35)
    nt.links.new(coord.outputs["Object"], broad.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (x + 220, y - 60)
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[1].position = 0.62
    nt.links.new(broad.outputs["Fac"], ramp.inputs["Fac"])

    weave = nt.nodes.new("ShaderNodeMix")
    weave.location = (x + 440, y - 60)
    weave.data_type = "RGBA"
    weave.blend_type = "MULTIPLY"
    weave.inputs["Factor"].default_value = 0.5
    nt.links.new(ramp.outputs["Color"], weave.inputs["A"])
    nt.links.new(fine.outputs["Color"], weave.inputs["B"])

    tint = nt.nodes.new("ShaderNodeMix")
    tint.location = (x + 640, y - 60)
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = strength
    tint.inputs["A"].default_value = base_colour
    nt.links.new(weave.outputs["Result"], tint.inputs["B"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (x + 640, y - 300)
    _in(bump, "Strength", 0.06)                      # polished stone: barely there
    _in(bump, "Distance", 0.004)
    nt.links.new(weave.outputs["Result"], bump.inputs["Height"])
    return bump, tint


# ---------------------------------------------------------------------------
# Surfaces. Each is built TWICE from one function so the PBR and Komikaze
# versions cannot drift apart - same base colour, same bump, ink added or not.
# ---------------------------------------------------------------------------

# surface -> (material stem, base colour, roughness, metallic, transmission)
SURFACES = {
    # cast / board-marked
    "concrete":   ("BR_Concrete",   (0.60, 0.59, 0.55, 1.0), 0.88, 0.00, 0.00),
    "precast":    ("BR_Precast",    (0.52, 0.52, 0.51, 1.0), 0.72, 0.00, 0.00),
    # quarried / polished
    "alabaster":  ("BR_Alabaster",  (0.86, 0.82, 0.74, 1.0), 0.55, 0.00, 0.12),
    "terrazzo":   ("BR_Terrazzo",   (0.55, 0.53, 0.50, 1.0), 0.35, 0.00, 0.00),
    "brick":      ("BR_Brick",      (0.31, 0.17, 0.13, 1.0), 0.90, 0.00, 0.00),
    # metals
    "corten":     ("BR_Corten",     (0.35, 0.17, 0.08, 1.0), 0.86, 0.15, 0.00),
    "steel":      ("BR_Steel",      (0.44, 0.45, 0.47, 1.0), 0.32, 1.00, 0.00),
    # glazing
    "glazing":    ("BR_Glazing",    (0.72, 0.80, 0.86, 1.0), 0.08, 0.00, 0.85),
    "glass_block": ("BR_GlassBlock", (0.64, 0.72, 0.70, 1.0), 0.28, 0.00, 0.55),
    # ground plane
    "asphalt":    ("BR_Asphalt",    (0.13, 0.13, 0.14, 1.0), 0.95, 0.00, 0.00),
    "tarmac":     ("BR_Tarmac",     (0.19, 0.19, 0.20, 1.0), 0.93, 0.00, 0.00),
    "paving":     ("BR_Paving",     (0.42, 0.42, 0.40, 1.0), 0.80, 0.00, 0.00),
    "markings":   ("BR_Markings",   (0.88, 0.87, 0.80, 1.0), 0.75, 0.00, 0.00),
    "soil":       ("BR_Soil",       (0.22, 0.17, 0.12, 1.0), 0.96, 0.00, 0.00),
}
# Formwork-marked pours. Board marks are a MOULD trace, so only surfaces that were cast in
# a mould may carry them. asphalt/paving would read as noise, alabaster is quarried.
BOARD_FORM = {"concrete", "precast"}
# Quarried stone: veining, never board marks.
VEINED = {"alabaster", "terrazzo"}


def build_brutalist_material(surface, look="PBR"):
    """One material datablock. `look` is 'PBR' or 'Komikaze'.

    Idempotent: re-running rebuilds the node tree in place and keeps the same
    material name, so the staged .blend stays referencable across re-runs.
    """
    stem, colour, rough, metal, trans = SURFACES[surface]
    suffix = "" if look == "PBR" else "_KOMIKAZE"
    name = stem + suffix
    mat, nt = _mat(name)

    out = _out(nt)
    # `Base Color` is spelled with a SPACE. The underscore form `Base_Color=` never
    # matched a socket, was silently dropped by the old guard, and left every surface at
    # the Principled default grey. If you refactor _bsdf to take kwargs generically,
    # socket names -- not Python identifier names -- are what must be passed.
    bsdf = _bsdf(nt, **{"Base Color": colour, "Roughness": rough, "Metallic": metal})
    _in(bsdf, "Transmission Weight", trans)
    if trans > 0.5:
        _in(bsdf, "IOR", 1.45)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # `base` is whatever currently feeds Base Color: a node output, or None when the
    # flat authored default stands. Komikaze mixes ink over THIS, not over a re-typed
    # colour literal, so the two looks cannot drift in their base tone.
    base = None
    if surface in BOARD_FORM:
        bump, base = _board_form(nt, colour)
    elif surface in VEINED:
        bump, base = _vein(nt, colour)
    if base is not None:
        nt.links.new(base.outputs["Result"], bsdf.inputs["Base Color"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    if look == "Komikaze":
        # Ink over the SAME base: keeps the surface colour, adds the house dot mask.
        ink = _ink_mask(nt)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.location = (700, 0)
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.45
        if base is not None:
            nt.links.new(base.outputs["Result"], mix.inputs["A"])
        else:
            mix.inputs["A"].default_value = colour
        nt.links.new(ink.outputs["Result"], mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        _in(bsdf, "Roughness", 0.95)

    mat["brutalist_surface"] = surface
    mat["brutalist_look"] = look
    return mat


def build_brutalist_materials():
    """Build every surface x look. Returns {'concrete:PBR': mat, ...}."""
    lib = {}
    for surface in SURFACES:
        for look in LOOKS:
            lib["%s:%s" % (surface, look)] = build_brutalist_material(surface, look)
    return lib


def apply_brutalist_material(obj, surface, look="PBR"):
    """Assign a BR_ material to an object (slot 0, or the first empty slot)."""
    name = SURFACES[surface][0] + ("" if look == "PBR" else "_KOMIKAZE")
    mat = bpy.data.materials.get(name) or build_brutalist_material(surface, look)
    if obj is None or obj.type != "MESH":
        return None
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return mat


def material_name(surface, look="PBR"):
    """The datablock name for a surface/look pair."""
    return SURFACES[surface][0] + ("" if look == "PBR" else "_KOMIKAZE")


def set_material_slots(tree, surface_map, look="PBR"):
    """Write surfaces onto a builder's Group Input Material sockets.

    `surface_map` maps interface socket name -> surface key, e.g.
        {"Massing Material": "concrete", "Ground Material": "asphalt"}

    The builders expose per-surface Material sockets on their group interface and gate
    their internal Set Material nodes on them -- but `if MAT_MASS is not None` tests
    whether the SOCKET exists, which it always does, not whether a material was ever
    supplied. The staging script only ever wrote slot 0 on the OBJECT, so those sockets
    stayed empty and every staged object measured exactly one material slot: a city with
    no ground or glazing surface at all.

    Returns {"set": [...], "missing": [...]}. Missing sockets are REPORTED, never raised
    and never quietly skipped -- a builder that exposes two sockets and one that exposes
    none must be distinguishable from the return value, because both look like success
    from a `success: true`.
    """
    result = {"set": [], "missing": []}
    if tree is None or surface_map is None:
        return result
    iface = getattr(tree, "interface", None)
    if iface is None:
        return result
    for sock in iface.items_tree:
        if getattr(sock, "item_type", "") != "SOCKET":
            continue
        if getattr(sock, "in_out", "") != "INPUT":
            continue
        surface = surface_map.get(sock.name)
        if surface is None:
            continue
        if getattr(sock, "socket_type", "") != "NodeSocketMaterial":
            result["missing"].append("%s (type %s, not MATERIAL)"
                                     % (sock.name, getattr(sock, "socket_type", "?")))
            continue
        if surface not in SURFACES:
            result["missing"].append("%s (unknown surface %r)" % (sock.name, surface))
            continue
        mat = bpy.data.materials.get(material_name(surface, look)) \
            or build_brutalist_material(surface, look)
        try:
            sock.default_value = mat
        except Exception as exc:
            result["missing"].append("%s (%s)" % (sock.name, exc))
            continue
        result["set"].append("%s=%s" % (sock.name, mat.name))
    asked = set(surface_map or {})
    for name in sorted(asked - {s.split("=")[0] for s in result["set"]}
                       - {m.split(" (")[0] for m in result["missing"]}):
        result["missing"].append("%s (no such input socket)" % name)
    return result


def assign_surfaces(obj, surfaces, look="PBR"):
    """Fill an object's material SLOTS from a list of surface keys, in order.

    Complements set_material_slots: the group sockets decide which Set Material node
    stamps which face, the object slots are what the renderer and the exporter can see.
    Both are needed -- an object with a single slot cannot display a three-surface split
    no matter what the node tree asks for.
    """
    if obj is None or obj.type != "MESH":
        return []
    names = []
    for surface in surfaces:
        if surface not in SURFACES:
            continue
        mat = bpy.data.materials.get(material_name(surface, look)) \
            or build_brutalist_material(surface, look)
        if mat.name in names:
            continue
        names.append(mat.name)
    if list(obj.data.materials.keys()) != names:
        obj.data.materials.clear()
        for n in names:
            obj.data.materials.append(bpy.data.materials[n])
    return names


