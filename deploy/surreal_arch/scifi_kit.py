"""Sci-fi modular kit — pressure doors with gasket recess geometry."""

from __future__ import annotations


def build_scifi_pressure_door(tree, M, props, base_x=-1400):
    """Pressure door end-cap: corridor stub + door boolean + gasket ring + frame offset."""
    L, W, H, t = M._gb_corridor_dims(props)
    dw = getattr(props, "gb_door_width", 1.2)
    dh = getattr(props, "gb_door_height", 2.35)
    stub = min(L, max(W * 1.5, 2.0))
    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    end_y = stub * 0.5

    parts.append(M._gb_box(tree, (W, stub, t), (0, 0, t * 0.5), base_x, 0))
    parts.append(M._gb_box(tree, (t, stub, wh), (-W * 0.5 + t * 0.5, 0, wz), base_x, 200))
    parts.append(M._gb_box(tree, (t, stub, wh), (W * 0.5 - t * 0.5, 0, wz), base_x, 400))
    parts.extend(M._gb_add_corridor_ceiling(tree, props, base_x, W, stub, H, t, 0, 0, 600))

    slab = M._gb_box(tree, (W, t, H), (0, end_y, H * 0.5), base_x, 1000)
    cutter = M._gb_box(tree, (dw, t * 4, dh), (0, end_y, dh * 0.5), base_x + 400, 1000, "door")
    cut = M._gb_bool_diff(tree, slab, [cutter], base_x + 800, 1000)
    if cut:
        parts.append(cut)

    parts.extend(M._gb_doorway_frame_trim(tree, props, base_x + 1200, dw, dh, t, node_y=1000))
    parts.extend(_gasket_ring_parts(tree, M, props, base_x, dw, dh, t, end_y, 1400))

    frame_offset = M._gb_trim_depth(props, t) * 1.25
    if frame_offset > 0.01:
        outer = M._gb_box(
            tree,
            (dw + frame_offset * 4, t * 0.55, dh + frame_offset * 3),
            (0, end_y + t * 0.5 + frame_offset * 0.4, dh * 0.5),
            base_x,
            1600,
            "trim:pressure_frame",
        )
        parts.append(outer)

    return M._gb_join(tree, parts, base_x + 2000, 0)


def _gasket_ring_parts(tree, M, props, base_x, dw, dh, t, end_y, node_y):
    """Recessed gasket channel around door opening — trim-sheet friendly."""
    mode = M._gb_trim_mode(props)
    if mode == "NONE":
        return []
    recess = M._gb_trim_depth(props, t)
    ring_t = max(t * 0.12, 0.02)
    gap = max(t * 0.18, 0.03)
    y = end_y + t * 0.5 - recess - ring_t * 0.5
    parts = []
    head_z = dh + gap
    sill_z = gap
    mid_z = dh * 0.5
    parts.append(M._gb_box(tree, (dw + gap * 2, ring_t, ring_t), (0, y, head_z), base_x, node_y, "trim:gasket_ring"))
    parts.append(M._gb_box(tree, (dw + gap * 2, ring_t, ring_t), (0, y, sill_z), base_x, node_y + 50, "trim:gasket_ring"))
    for sx in (-1, 1):
        parts.append(
            M._gb_box(
                tree,
                (ring_t, ring_t, dh + gap * 2),
                (sx * (dw * 0.5 + gap + ring_t * 0.5), y, mid_z),
                base_x,
                node_y + 100 + sx * 20,
                "trim:gasket_ring",
            )
        )
    return [p for p in parts if p is not None]


def compute_scifi_pressure_door_snaps(M, props):
    L = getattr(props, "gb_length", 8.0)
    W = M._gb_resolve_corridor_width(props) if hasattr(M, "_gb_resolve_corridor_width") else getattr(props, "gb_width", 3.0)
    H = getattr(props, "gb_height", 3.2)
    stub = min(L, max(W * 1.5, 2.0))
    dh = getattr(props, "gb_door_height", 2.35)
    unit = getattr(props, "unit_size", 2.0)
    return [
        M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
        M._gb_snap_point("corridor_ny", "WALL", (0, -stub * 0.5, H * 0.5), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
        M._gb_snap_point("door", "DOOR", (0, stub * 0.5, dh * 0.5), (0, 1, 0), "MUST_CONNECT"),
        M._gb_snap_point("gasket", "TRIM", (0, stub * 0.5, dh * 0.5), (0, 1, 0)),
    ]
