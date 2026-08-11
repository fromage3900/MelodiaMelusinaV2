"""Romanesque modular kit — round-arch bay with colonette and impost block."""

from __future__ import annotations

import math


def build_romanesque_arcade_bay(tree, M, props, base_x=-1400):
    """Modular round-arch bay: colonettes, impost blocks, semicircular arch, barrel vault cap."""
    W = getattr(props, "gb_width", 3.2)
    H = getattr(props, "gb_height", 4.2)
    t = getattr(props, "gb_wall_thick", 0.35)
    col_r = max(getattr(props, "gb_leg_thick", 0.18), 0.12)
    arch_r = W * 0.46
    spring_z = arch_r + t * 0.5
    parts = []

    for sx, ny in ((-1, 0), (1, 200)):
        col = M._gb_box(
            tree,
            (col_r * 2.0, col_r * 2.0, spring_z),
            (sx * (W * 0.5 - col_r), 0, spring_z * 0.5),
            base_x,
            ny,
            "trim:colonette",
        )
        if col:
            parts.append(col)
        impost = M._gb_box(
            tree,
            (col_r * 2.8, t * 1.4, col_r * 1.4),
            (sx * (W * 0.5 - col_r), 0, spring_z + col_r * 0.5),
            base_x,
            ny + 50,
            "trim:impost_block",
        )
        if impost:
            parts.append(impost)

    spandrel_h = max(H - spring_z - arch_r * 0.15, t)
    spandrel = M._gb_box(
        tree,
        (W, t, spandrel_h),
        (0, 0, spring_z + spandrel_h * 0.5),
        base_x,
        400,
    )
    if spandrel:
        parts.append(spandrel)

    arch = _round_arch_segment(tree, M, arch_r, t, W, spring_z, base_x, 600)
    if arch:
        from .trim_color_bake import tag_face_trim_attrs
        arch = tag_face_trim_attrs(M, tree, arch, base_x + 700, 600, zone_value=3.0, trim_flag=1.0)
        parts.append(arch)

    if getattr(props, "gb_corridor_ceiling", "FULL") != "OPEN":
        vault = _barrel_vault_cap(tree, M, W, t, arch_r, spring_z + arch_r, base_x, 900)
        if vault:
            parts.append(vault)

    parts.extend(M._gb_doorway_frame_trim(tree, props, base_x + 1200, W * 0.55, arch_r * 1.05, t, node_y=0))

    return M._gb_join(tree, parts, base_x + 1600, 0)


def _round_arch_segment(tree, M, radius, thickness, span, base_z, base_x, node_y):
    """Semicircular arch spanning the bay opening."""
    props_holder = type("ArchProps", (), {})()
    props_holder.arch_radius = radius
    props_holder.arch_sweep_deg = 180.0
    props_holder.arch_thickness = thickness
    props_holder.arch_rib_count = 0
    props_holder.ornament_density = 0.0
    props_holder.musical_freq_a = 1.0
    props_holder.musical_freq_b = 1.0
    props_holder.harmonic_layers = 1
    arch_geom = M.build_arch(tree, props_holder, base_x + 200)
    if not arch_geom:
        return None
    tr = M._safe_node(tree, "GeometryNodeTransform", (base_x + 500, node_y))
    if tr:
        try:
            tr.inputs["Translation"].default_value = (0.0, 0.0, base_z)
            tr.inputs["Rotation"].default_value = (0.0, math.pi * 0.5, 0.0)
        except Exception:
            pass
        M._link(tree, arch_geom, tr.inputs["Geometry"])
        return tr.outputs["Geometry"]
    return arch_geom


def _barrel_vault_cap(tree, M, span, thickness, rise, base_z, base_x, node_y):
    """Shallow barrel vault segment over the bay."""
    if hasattr(M, "_baroque_barrel_vault"):
        geom = M._baroque_barrel_vault(tree, span * 0.92, thickness * 2.5, rise * 0.55, base_x)
        if geom:
            from .trim_color_bake import tag_face_trim_attrs
            return tag_face_trim_attrs(M, tree, geom, base_x + 300, node_y, zone_value=4.0, trim_flag=1.0)
        return geom
    return M._gb_box(
        tree,
        (span * 0.9, thickness * 2.0, rise * 0.35),
        (0, 0, base_z + rise * 0.2),
        base_x,
        node_y,
        "trim:barrel_vault",
    )


def build_romanesque_apse(tree, M, props, base_x=-1400):
    """Semicircular apse termination — choir end cap with recess shell for trim sheets."""
    W = getattr(props, "gb_width", 4.0)
    D = getattr(props, "gb_depth", 3.5)
    H = getattr(props, "gb_height", 4.5)
    t = getattr(props, "gb_wall_thick", 0.35)
    recess = M._gb_trim_depth(props, t)
    parts = []

    back = M._gb_box(tree, (W, t, H), (0, -D * 0.5 + t * 0.5, H * 0.5), base_x, 0, "wall")
    if back:
        parts.append(back)

    for sx, ny in ((-1, 100), (1, 200)):
        side = M._gb_box(tree, (t, D * 0.85, H), (sx * (W * 0.5 - t * 0.5), 0, H * 0.5), base_x, ny, "wall")
        if side:
            parts.append(side)

    apse_r = W * 0.48
    shell = M._gb_box(tree, (apse_r * 2.0, t, H * 0.85), (0, D * 0.15, H * 0.45), base_x, 400, "trim:apse_shell")
    if shell:
        parts.append(shell)
    inner = M._gb_box(
        tree,
        (apse_r * 2.0 - recess * 4, t * 3, H * 0.75),
        (0, D * 0.15 + recess, H * 0.45),
        base_x,
        500,
        "window",
    )
    if shell and inner:
        cut = M._gb_bool_diff(tree, shell, [inner], base_x + 600, 0)
        if cut:
            parts[-1] = cut

    vault = _barrel_vault_cap(tree, M, W * 0.9, t, apse_r * 0.6, H * 0.92, base_x, 800)
    if vault:
        parts.append(vault)

    return M._gb_join(tree, parts, base_x + 1200, 0)


def compute_romanesque_snap_points(M, props, arch_type):
    W = getattr(props, "gb_width", 3.2)
    H = getattr(props, "gb_height", 4.2)
    D = getattr(props, "gb_depth", 3.5)
    unit = getattr(props, "unit_size", 2.0)
    pts = []
    if arch_type == "GB_ROMANESQUE_APSE":
        pts.append(
            M._gb_snap_point("apse_open", "WALL", (0, -D * 0.5, H * 0.5), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit)
        )
        pts.append(M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit))
        pts.append(M._gb_snap_point("apse_center", "ARCH", (0, D * 0.2, H * 0.55), (0, 1, 0)))
    elif arch_type == "GB_ROMANESQUE_ARCADE":
        pts.append(
            M._gb_snap_point("bay_nx", "WALL", (-W * 0.5, 0, H * 0.5), (-1, 0, 0), "MUST_CONNECT", grid_quantum=unit)
        )
        pts.append(
            M._gb_snap_point("bay_px", "WALL", (W * 0.5, 0, H * 0.5), (1, 0, 0), "MUST_CONNECT", grid_quantum=unit)
        )
        pts.append(M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit))
        pts.append(M._gb_snap_point("arch_center", "ARCH", (0, 0, H * 0.65), (0, 1, 0)))
    return pts
