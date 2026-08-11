"""Gothic modular kit builders — bay, portal, buttress, tracery panel."""

from __future__ import annotations


def build_gothic_portal(tree, M, props, base_x=-1400):
    W = getattr(props, "gb_width", 3.0)
    H = getattr(props, "gb_height", 4.0)
    t = getattr(props, "gb_wall_thick", 0.35)
    dw = getattr(props, "gb_door_width", 1.4)
    dh = getattr(props, "gb_door_height", 2.8)
    props.gothic_width = dw + 0.4
    props.gothic_radius = max(props.gothic_width * 0.55, props.gothic_width / 2 + 0.2)
    slab = M._gb_box(tree, (W, t, H), (0, 0, H * 0.5), base_x, 0)
    cutter = M._gb_box(tree, (dw, t * 4, dh), (0, 0, dh * 0.5), base_x + 400, 0, "door")
    cut = M._gb_bool_diff(tree, slab, [cutter], base_x + 800, 0)
    parts = [cut] if cut else []
    parts.extend(M._gb_doorway_frame_trim(tree, props, base_x + 1200, dw, dh, t))
    pointed = M.build_gothic_arch(tree, props, base_x + 1600)
    if pointed:
        parts.append(pointed)
    return M._gb_join(tree, parts, base_x + 2000, 0)


def build_gothic_bay(tree, M, props, base_x=-1400):
    W = getattr(props, "gothic_width", 2.4)
    H = getattr(props, "gb_height", 4.5)
    t = getattr(props, "gb_wall_thick", 0.35)
    ww = getattr(props, "gb_window_width", 0.7)
    wh = getattr(props, "gb_window_height", 2.2)
    sill = getattr(props, "gb_window_sill", 1.1)
    wall = M._gb_box(tree, (W, t, H), (0, 0, H * 0.5), base_x, 0)
    cutter = M._gb_box(tree, (ww, t * 4, wh), (0, 0, sill + wh * 0.5), base_x + 400, 0, "window")
    cut = M._gb_bool_diff(tree, wall, [cutter], base_x + 800, 0)
    parts = [cut] if cut else []
    from .greybox_trim import gb_window_reveal_parts
    parts.extend(gb_window_reveal_parts(tree, M, props, base_x + 1000, W, H, t, 0, 0, 0, True, 1200))
    return M._gb_join(tree, parts, base_x + 1400, 0)


def build_gothic_buttress(tree, M, props, base_x=-1400):
    span = getattr(props, "buttress_span", 2.5)
    H = getattr(props, "gb_height", 5.0)
    t = getattr(props, "gb_wall_thick", 0.4)
    offset = M._gb_trim_depth(props, t)
    pier = M._gb_box(tree, (t * 2.5, t * 2.5, H), (span * 0.35, offset + t, H * 0.5), base_x, 0, "trim")
    brace = M._gb_box(tree, (span * 0.5, t * 1.2, t * 1.2),
                      (span * 0.15, offset + t * 2, H * 0.65), base_x, 300, "trim")
    parts = [p for p in (pier, brace) if p]
    return M._gb_join(tree, parts, base_x + 600, 0)


def build_gothic_tracery_panel(tree, M, props, base_x=-1400):
    W = getattr(props, "gothic_width", 1.8)
    H = W
    t = getattr(props, "gothic_thickness", 0.12)
    panel = M._gb_box(tree, (W, t, H), (0, 0, H * 0.5), base_x, 0)
    petal_r = W * 0.22
    cutters = []
    for i in range(6):
        ang = i * 3.14159 / 3.0
        import math
        px = math.cos(ang) * W * 0.28
        pz = H * 0.5 + math.sin(ang) * W * 0.28
        cutters.append(M._gb_box(tree, (petal_r, t * 4, petal_r), (px, 0, pz), base_x + 200 + i * 40, "window"))
    cut = M._gb_bool_diff(tree, panel, cutters, base_x + 800, 0)
    return cut if cut else panel


def compute_gothic_snap_points(M, props, arch_type):
    H = getattr(props, "gb_height", getattr(props, "gothic_width", 3.0) * 2)
    unit = getattr(props, "unit_size", 2.0)
    pts = []
    if arch_type == "GB_GOTHIC_PORTAL":
        dh = getattr(props, "gb_door_height", 2.8)
        wt = getattr(props, "gb_wall_thick", 0.35)
        pts.append(M._gb_snap_point("door", "DOOR", (0, wt * 0.5, dh * 0.5), (0, 1, 0), "MUST_CONNECT"))
        pts.append(M._gb_snap_point("wall_neg", "WALL", (0, -wt * 0.5, H * 0.5), (0, -1, 0)))
    elif arch_type == "GB_GOTHIC_BAY":
        W = getattr(props, "gothic_width", 2.4)
        pts.append(M._gb_snap_point("wall_nx", "WALL", (-W * 0.5, 0, H * 0.5), (-1, 0, 0), "MUST_CONNECT", grid_quantum=unit))
        pts.append(M._gb_snap_point("wall_px", "WALL", (W * 0.5, 0, H * 0.5), (1, 0, 0), "MUST_CONNECT", grid_quantum=unit))
        pts.append(M._gb_snap_point("tracery", "TRACERY", (0, 0, H * 0.55), (0, 1, 0)))
    elif arch_type == "GB_GOTHIC_BUTTRESS":
        pts.append(M._gb_snap_point("wall_face", "BUTTRESS", (0, 0, H * 0.5), (0, -1, 0), "MUST_CONNECT"))
    elif arch_type == "GB_GOTHIC_TRACERY_PANEL":
        W = getattr(props, "gothic_width", 1.8)
        pts.append(M._gb_snap_point("panel_nx", "WALL", (-W * 0.5, 0, H * 0.5), (-1, 0, 0), grid_quantum=unit))
        pts.append(M._gb_snap_point("panel_px", "WALL", (W * 0.5, 0, H * 0.5), (1, 0, 0), grid_quantum=unit))
        pts.append(M._gb_snap_point("panel_face", "TRACERY", (0, 0, H * 0.5), (0, 1, 0), grid_quantum=unit))
    return pts
