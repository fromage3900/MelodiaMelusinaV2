"""Brutalist modular kit — recess-panel walls with pilaster rhythm."""

from __future__ import annotations


def build_brutalist_panel_wall(tree, M, props, base_x=-1400):
    """Standalone wall module: pilaster rhythm + recessed panels for trim sheets."""
    L = getattr(props, "gb_length", 4.0)
    H = getattr(props, "gb_height", 3.5)
    t = getattr(props, "gb_wall_thick", 0.45)
    bay = max(getattr(props, "unit_size", 2.0), 1.2)
    recess = M._gb_trim_depth(props, t)
    panel_t = max(t * 0.14, 0.025)
    n_bays = max(1, int(L / bay))
    bay_len = L / n_bays
    pilaster_w = max(t * 0.5, 0.2)
    base_h = max(getattr(props, "gb_baseboard_height", 0.12), 0.0)
    panel_h = max(H - base_h - 0.12, H * 0.75)
    parts = []

    wall = M._gb_box(tree, (t, L, H), (0, 0, H * 0.5), base_x, 0)
    if wall:
        parts.append(wall)

    for i in range(n_bays + 1):
        cy = -L * 0.5 + i * bay_len
        proud = recess * 0.35
        pil = M._gb_box(
            tree,
            (t + proud, pilaster_w, H),
            (proud * 0.5, cy, H * 0.5),
            base_x,
            200 + i * 40,
            "trim:pilaster",
        )
        if pil:
            parts.append(pil)

    inner_x = t * 0.5 - recess - panel_t * 0.5
    for i in range(n_bays):
        cy = -L * 0.5 + (i + 0.5) * bay_len
        panel_w = max(bay_len - pilaster_w * 0.85, bay_len * 0.55)
        panel = M._gb_box(
            tree,
            (panel_t, panel_w, panel_h),
            (inner_x, cy, base_h + panel_h * 0.5),
            base_x,
            600 + i * 40,
            "trim:recess_panel",
        )
        if panel:
            parts.append(panel)

    if base_h > 0.01:
        sill = M._gb_box(
            tree,
            (panel_t, L * 0.96, base_h),
            (inner_x, 0, base_h * 0.5),
            base_x,
            1000,
            "trim:baseboard",
        )
        if sill:
            parts.append(sill)

    return M._gb_join(tree, parts, base_x + 1400, 0)


def compute_brutalist_snap_points(M, props):
    L = getattr(props, "gb_length", 4.0)
    H = getattr(props, "gb_height", 3.5)
    unit = getattr(props, "unit_size", 2.0)
    return [
        M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
        M._gb_snap_point("wall_ny", "WALL", (0, -L * 0.5, H * 0.5), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("wall_py", "WALL", (0, L * 0.5, H * 0.5), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("panel_face", "WALL", (0, 0, H * 0.5), (0, -1, 0)),
    ]
