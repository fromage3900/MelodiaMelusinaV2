"""Venetian loggia greybox kit — bifora void rhythm + cornice shelf."""

from __future__ import annotations


def build_venetian_loggia_bay(tree, M, props, base_x=-1400):
    """Modular loggia bay: wall slab, paired bifora voids, colonnette, projecting cornice."""
    W = getattr(props, "gb_width", 3.0)
    H = getattr(props, "gb_height", 4.8)
    t = getattr(props, "gb_wall_thick", 0.35)
    sill = getattr(props, "gb_window_sill", 1.0)
    win_h = getattr(props, "gb_window_height", H * 0.55)
    light_w = W / max(getattr(props, "bifora_lights", 2), 2)
    parts = []

    slab = M._gb_box(tree, (W, t, H), (0, 0, H * 0.5), base_x, 0)
    cutters = []
    for i, sx in enumerate((-1, 1)):
        cx = sx * W * 0.22
        cutters.append(
            M._gb_box(
                tree,
                (light_w * 0.82, t * 4, win_h),
                (cx, 0, sill + win_h * 0.5),
                base_x + 400,
                i * 100,
                "window",
            )
        )
    cut = M._gb_bool_diff(tree, slab, cutters, base_x + 800, 0) if slab else None
    if cut:
        parts.append(cut)

    col_w = max(t * 0.75, 0.14)
    colonnette = M._gb_box(
        tree,
        (col_w, t * 1.3, win_h * 0.92),
        (0, 0, sill + win_h * 0.46),
        base_x,
        200,
        "trim:colonnette",
    )
    parts.append(colonnette)

    recess = M._gb_trim_depth(props, t)
    cornice_h = max(t * 0.75, 0.18)
    cornice_d = max(t * 1.6, 0.28)
    cornice = M._gb_box(
        tree,
        (W * 1.06, cornice_d, cornice_h),
        (0, t * 0.5 + cornice_d * 0.5 - recess * 0.3, H + cornice_h * 0.48),
        base_x,
        500,
        "trim:cornice_shelf",
    )
    parts.append(cornice)

    shelf = M._gb_box(
        tree,
        (W * 0.92, t * 0.55, t * 0.45),
        (0, t * 0.5 + recess * 0.2, H - t * 0.25),
        base_x,
        600,
        "trim:sill_band",
    )
    parts.append(shelf)

    parts.extend(M._gb_doorway_frame_trim(tree, props, base_x + 900, light_w, win_h, t, node_y=0))

    return M._gb_join(tree, parts, base_x + 1200, 0)


def compute_venetian_loggia_snap_points(M, props):
    W = getattr(props, "gb_width", 3.0)
    H = getattr(props, "gb_height", 4.8)
    unit = getattr(props, "unit_size", 2.0)
    return [
        M._gb_snap_point("bay_nx", "WALL", (-W * 0.5, 0, H * 0.5), (-1, 0, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("bay_px", "WALL", (W * 0.5, 0, H * 0.5), (1, 0, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
        M._gb_snap_point("cornice", "TRIM", (0, 0, H + 0.2), (0, 1, 0)),
    ]
