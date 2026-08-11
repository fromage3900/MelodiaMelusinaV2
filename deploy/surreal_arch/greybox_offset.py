"""Corridor offset kit — recessed wall panels and floor ledge for trim sheets."""

from __future__ import annotations


def build_greybox_corridor_offset(tree, M, props, base_x=-1400):
    """Tileable corridor with recessed side panels and raised floor ledge bands."""
    L, W, H, t = M._gb_corridor_dims(props)
    parts = []

    floor = M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0)
    if floor:
        parts.append(floor)

    wall_z = t + (H - t) * 0.5
    wall_h = H - t
    lw = M._gb_box(tree, (t, L, wall_h), (-W * 0.5 + t * 0.5, 0, wall_z), base_x, 300)
    rw = M._gb_box(tree, (t, L, wall_h), (W * 0.5 - t * 0.5, 0, wall_z), base_x, 600)
    if lw:
        parts.append(lw)
    if rw:
        parts.append(rw)

    parts.extend(M._gb_add_corridor_ceiling(tree, props, base_x, W, L, H, t, 0, 0, 900))
    parts.extend(M._gb_corridor_ribs(tree, props, base_x, L, W, H, t, 0, 0, False, 1200))
    parts.extend(_offset_wall_panels(tree, M, props, base_x, L, W, H, t))
    parts.extend(_floor_ledges(tree, M, props, base_x, L, W, H, t))

    return M._gb_join(tree, parts, base_x + 2000, 0)


def _offset_wall_panels(tree, M, props, base_x, span_l, W, H, t):
    """Recessed rectangular panels along both corridor side walls."""
    mode = M._gb_trim_mode(props)
    if mode == "NONE":
        return []
    recess = M._gb_trim_depth(props, t)
    panel_t = max(t * 0.14, 0.022)
    panel_h = max(H - t - 0.25, 0.5)
    bay = max(getattr(props, "unit_size", 2.0), 1.5)
    n_bays = max(1, int(span_l / bay))
    panel_depth = span_l / n_bays - panel_t * 1.5
    parts = []
    head_z = t + panel_h * 0.5
    for side_sign, ny in ((-1, 1300), (1, 1500)):
        inner_x = side_sign * (W * 0.5 - t * 0.5)
        panel_x = inner_x + side_sign * (recess - panel_t * 0.5)
        for i in range(n_bays):
            cy = -span_l * 0.5 + (i + 0.5) * (span_l / n_bays)
            box = M._gb_box(
                tree,
                (panel_t, panel_depth, panel_h),
                (panel_x, cy, head_z),
                base_x,
                ny + i * 30,
                "trim:wall_panel_recess",
            )
            if box:
                parts.append(box)
    return parts


def _floor_ledges(tree, M, props, base_x, span_l, W, H, t):
    """Raised floor ledge bands — center runner + optional side strips."""
    ledge_h = max(getattr(props, "gb_baseboard_height", 0.12), 0.08)
    ledge_w = max(W * 0.12, 0.25)
    recess = M._gb_trim_depth(props, t)
    parts = []
    center = M._gb_box(
        tree,
        (ledge_w, span_l * 0.92, ledge_h),
        (0, 0, t + ledge_h * 0.5),
        base_x,
        1700,
        "trim:floor_ledge",
    )
    if center:
        parts.append(center)
    for side_sign, ny in ((-1, 1800), (1, 1900)):
        strip_x = side_sign * (W * 0.5 - t - recess - ledge_w * 0.5)
        strip = M._gb_box(
            tree,
            (ledge_w * 0.7, span_l * 0.85, ledge_h * 0.85),
            (strip_x, 0, t + ledge_h * 0.42),
            base_x,
            ny,
            "trim:floor_ledge",
        )
        if strip:
            parts.append(strip)
    return parts


def compute_corridor_offset_snap_points(M, props):
    L, W, H, t = M._gb_corridor_dims(props)
    unit = getattr(props, "unit_size", 2.0)
    pts = [
        M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
        M._gb_snap_point("end_py", "WALL", (0, L * 0.5, H * 0.5), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("end_ny", "WALL", (0, -L * 0.5, H * 0.5), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("wall_nx", "WALL", (-W * 0.5, 0, H * 0.5), (-1, 0, 0)),
        M._gb_snap_point("wall_px", "WALL", (W * 0.5, 0, H * 0.5), (1, 0, 0)),
    ]
    return pts
