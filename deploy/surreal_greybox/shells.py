"""Corridor + room shell builders — surreal_greybox phase 2."""

from __future__ import annotations

_M = None

_GB_PROFILE_WIDTH = {
    "SINGLE": 1.8,
    "DOUBLE": 3.0,
    "MAINTENANCE": 1.2,
}


def bind(monolith):
    global _M
    _M = monolith


def _require():
    if _M is None:
        raise RuntimeError("surreal_greybox.shells not bound — call bind(monolith) at register")


def _patch(name, fn):
    _require()
    setattr(_M, name, fn)
    mod = getattr(_M, "__name__", None)
    if mod:
        import sys
        module = sys.modules.get(mod)
        if module is not None:
            setattr(module, name, fn)


def corridor_rib_offset(props, wall_t):
    rib_mode = getattr(props, "gb_corridor_rib_mode", None)
    if rib_mode == "NONE":
        return 0.0
    if rib_mode == "OFFSET":
        return -_M._gb_trim_depth(props, wall_t) * 0.5
    if rib_mode == "INSET":
        return _M._gb_trim_depth(props, wall_t)
    mode = _M._gb_trim_mode(props)
    if mode == "NONE":
        return 0.0
    return _M._gb_trim_depth(props, wall_t) if mode == "RECESS" else _M._gb_trim_depth(props, wall_t) * 0.5


def resolve_corridor_width(props):
    profile = getattr(props, "gb_corridor_profile", "DOUBLE")
    if profile in _GB_PROFILE_WIDTH:
        return _GB_PROFILE_WIDTH[profile]
    return getattr(props, "gb_width", 3.0)


def corridor_dims(props):
    L = getattr(props, "gb_length", 8.0)
    W = resolve_corridor_width(props)
    H = getattr(props, "gb_height", 3.5)
    t = getattr(props, "gb_wall_thick", 0.3)
    return L, W, H, t


def ceiling_mode(props):
    return getattr(props, "gb_corridor_ceiling", "FULL")


def ceiling_active(props):
    mode = ceiling_mode(props)
    if mode == "OPEN":
        return False
    if mode in ("FULL", "PARTIAL_GRID"):
        return True
    return getattr(props, "gb_ceiling", True)


def add_corridor_ceiling(tree, props, base_x, span_w, span_l, H, t, cx, cy, node_y, along_x=False):
    if not ceiling_active(props):
        return []
    mode = ceiling_mode(props)
    parts = []
    if mode == "PARTIAL_GRID":
        beam_t = max(t * 0.55, 0.07)
        n_main = max(2, int(span_l / 2.0))
        for i in range(n_main + 1):
            frac = i / max(1, n_main)
            if along_x:
                yy = cy - span_l * 0.5 + frac * span_l
                bx = _M._gb_box(tree, (span_w, beam_t, beam_t), (cx, yy, H + beam_t * 0.5),
                                base_x, node_y + i * 35, "ceiling")
            else:
                xx = cx - span_l * 0.5 + frac * span_l
                bx = _M._gb_box(tree, (beam_t, span_w, beam_t), (xx, cy, H + beam_t * 0.5),
                                base_x, node_y + i * 35, "ceiling")
            if bx:
                parts.append(bx)
        n_cross = max(1, int(span_w / 2.0))
        for j in range(n_cross + 1):
            frac = j / max(1, n_cross)
            if along_x:
                xx = cx - span_w * 0.5 + frac * span_w
                bx = _M._gb_box(tree, (beam_t, span_l, beam_t), (xx, cy, H + beam_t * 0.5),
                                base_x, node_y + 800 + j * 35, "ceiling")
            else:
                yy = cy - span_l * 0.5 + frac * span_l
                bx = _M._gb_box(tree, (span_l, beam_t, beam_t), (cx, yy, H + beam_t * 0.5),
                                base_x, node_y + 800 + j * 35, "ceiling")
            if bx:
                parts.append(bx)
        return parts
    if along_x:
        bx = _M._gb_box(tree, (span_l, span_w, t), (cx, cy, H + t * 0.5), base_x, node_y, "ceiling")
    else:
        bx = _M._gb_box(tree, (span_w, span_l, t), (cx, cy, H + t * 0.5), base_x, node_y, "ceiling")
    return [bx] if bx else []


def corridor_ribs(tree, props, base_x, span_l, W, H, t, cx, cy, along_x, node_y):
    if getattr(props, "gb_corridor_rib_mode", "INSET") == "NONE":
        if not getattr(props, "gb_ribs", True):
            return []
    elif not getattr(props, "gb_ribs", True):
        return []
    n_ribs = max(1, int(span_l / 2.5))
    rib_w = t * 1.4
    rib_inset = corridor_rib_offset(props, t)
    parts = []
    for i in range(n_ribs + 1):
        frac = i / max(1, n_ribs)
        wall_z = t + (H - t) * 0.5
        if along_x:
            xx = cx - span_l * 0.5 + frac * span_l
            for sy in (-1, 1):
                ry = cy + sy * (W * 0.5 - t - rib_inset)
                rib = _M._gb_box(tree, (rib_w, rib_w, H - t), (xx, ry, wall_z),
                                 base_x, node_y + i * 50, "trim")
                if rib:
                    parts.append(rib)
        else:
            yy = cy - span_l * 0.5 + frac * span_l
            for sx in (-1, 1):
                rx = cx + sx * (W * 0.5 - t - rib_inset)
                rib = _M._gb_box(tree, (rib_w, rib_w, H - t), (rx, yy, wall_z),
                                 base_x, node_y + i * 50, "trim")
                if rib:
                    parts.append(rib)
    return parts


def corridor_wainscot(tree, props, base_x, span_l, W, H, t, cx, cy, along_x, node_y, side_sign=1):
    wh = getattr(props, "gb_wainscot_height", 0.0)
    bb = getattr(props, "gb_baseboard_height", 0.0)
    if wh < 0.01 and bb < 0.01:
        return []
    recess = max(_M._gb_trim_depth(props, t) * 0.5, 0.015)
    panel_t = max(t * 0.12, 0.02)
    parts = []
    if along_x:
        wall_x = cx + side_sign * (W * 0.5 - t * 0.5 + recess - panel_t * 0.5)
        if wh > 0.01:
            parts.append(_M._gb_box(tree, (span_l, panel_t, wh), (cx, wall_x, bb + wh * 0.5),
                                      base_x, node_y, "trim"))
        if bb > 0.01:
            parts.append(_M._gb_box(tree, (span_l, panel_t, bb), (cx, wall_x, bb * 0.5),
                                      base_x, node_y + 100, "trim"))
    else:
        wall_y = cy + side_sign * (W * 0.5 - t * 0.5 + recess - panel_t * 0.5)
        if wh > 0.01:
            parts.append(_M._gb_box(tree, (panel_t, span_l, wh), (wall_y, cx, bb + wh * 0.5),
                                      base_x, node_y, "trim"))
        if bb > 0.01:
            parts.append(_M._gb_box(tree, (panel_t, span_l, bb), (wall_y, cx, bb * 0.5),
                                      base_x, node_y + 100, "trim"))
    return [p for p in parts if p is not None]


def opening_cutter_depth(t, mult=4.0):
    return t * mult


def collect_door_cutters_for_rect(tree, props, rw, rd, t, dh, dw, base_x, node_y, rx=0.0, ry=0.0):
    door_z = t + dh * 0.5
    depth = opening_cutter_depth(t)
    cutters_ns, cutters_ew = [], []
    if getattr(props, "gb_door_n", True):
        cutters_ns.append(("N", _M._gb_box(tree, (dw, depth, dh),
                                          (rx, ry + rd * 0.5, door_z), base_x, node_y + 300, "door")))
    if getattr(props, "gb_door_s", False):
        cutters_ns.append(("S", _M._gb_box(tree, (dw, depth, dh),
                                            (rx, ry - rd * 0.5, door_z), base_x, node_y + 600, "door")))
    if getattr(props, "gb_door_e", False):
        cutters_ew.append(("E", _M._gb_box(tree, (depth, dw, dh),
                                            (rx + rw * 0.5, ry, door_z), base_x, node_y + 900, "door")))
    if getattr(props, "gb_door_w", False):
        cutters_ew.append(("W", _M._gb_box(tree, (depth, dw, dh),
                                            (rx - rw * 0.5, ry, door_z), base_x, node_y + 1200, "door")))
    return cutters_ns, cutters_ew


def collect_window_cutters_for_rect(tree, props, rw, rd, t, H, base_x, node_y, rx=0.0, ry=0.0):
    cutters_ns, cutters_ew = [], []
    depth = opening_cutter_depth(t)
    if getattr(props, "gb_windows_enabled", False):
        win_w = getattr(props, "gb_window_width", 0.8)
        win_h = getattr(props, "gb_window_height", 0.8)
        sill = getattr(props, "gb_window_sill", 1.0)
        win_z = t + sill + win_h * 0.5
        n_ns = max(0, getattr(props, "gb_window_count_ns", 0))
        n_ew = max(0, getattr(props, "gb_window_count_ew", 0))
        for i in range(n_ns):
            frac = (i + 1) / (n_ns + 1)
            wx = rx - rw * 0.5 + frac * rw
            cutters_ns.append(("N", _M._gb_box(tree, (win_w, depth, win_h),
                                               (wx, ry + rd * 0.5, win_z), base_x, node_y + 1500 + i, "door")))
            cutters_ns.append(("S", _M._gb_box(tree, (win_w, depth, win_h),
                                               (wx, ry - rd * 0.5, win_z), base_x, node_y + 1600 + i, "door")))
        for i in range(n_ew):
            frac = (i + 1) / (n_ew + 1)
            wy = ry - rd * 0.5 + frac * rd
            cutters_ew.append(("E", _M._gb_box(tree, (depth, win_w, win_h),
                                                (rx + rw * 0.5, wy, win_z), base_x, node_y + 1700 + i, "door")))
            cutters_ew.append(("W", _M._gb_box(tree, (depth, win_w, win_h),
                                                (rx - rw * 0.5, wy, win_z), base_x, node_y + 1800 + i, "door")))
    else:
        win_w = getattr(props, "gb_window_width", getattr(props, "gb_door_width", 1.0) * 0.8)
        win_h = getattr(props, "gb_window_height", 1.4)
        wn = getattr(props, "gb_window_count", 2)
        win_z = t + H * 0.58
        for do_win, wall_dir, w_dir_x, w_dir_y in (
            (getattr(props, "gb_window_n", False), "N", 0, rd * 0.5),
            (getattr(props, "gb_window_s", False), "S", 0, -rd * 0.5),
            (getattr(props, "gb_window_e", True), "E", rw * 0.5, 0),
            (getattr(props, "gb_window_w", True), "W", -rw * 0.5, 0),
        ):
            if not do_win:
                continue
            wall_len = rw if wall_dir in ("N", "S") else rd
            for wi in range(wn):
                frac = (wi + 0.5) / wn
                if wall_dir in ("N", "S"):
                    wx = rx - rw * 0.5 + wall_len * frac
                    wy = ry + w_dir_y
                    cutters_ns.append((wall_dir, _M._gb_box(tree, (win_w, depth, win_h),
                                                            (wx, wy, win_z), base_x, node_y + 1900 + wi, "door")))
                else:
                    wx = rx + w_dir_x
                    wy = ry - rd * 0.5 + wall_len * frac
                    cutters_ew.append((wall_dir, _M._gb_box(tree, (depth, win_w, win_h),
                                                            (wx, wy, win_z), base_x, node_y + 2000 + wi, "door")))
    return cutters_ns, cutters_ew


def apply_openings_to_wall(tree, wall_geom, side, cutters_ns, cutters_ew, base_x, node_y):
    if wall_geom is None:
        return None
    pool = cutters_ns if side in ("N", "S") else cutters_ew
    cutters = [c for s, c in pool if s == side and c is not None]
    if not cutters:
        return wall_geom
    return _M._gb_bool_diff(tree, wall_geom, cutters, base_x + 1000, node_y)


def rect_room_shell(tree, props, rw, rd, H, t, base_x, node_y,
                    rx=0.0, ry=0.0, with_ceiling=None,
                    with_doors=True, with_windows=True):
    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    floor = _M._gb_box(tree, (rw, rd, t), (rx, ry, t * 0.5), base_x, node_y)
    if floor:
        parts.append(floor)

    ns_wall = _M._gb_box(tree, (rw, t, wh), (rx, ry + rd * 0.5 - t * 0.5, wz), base_x, node_y + 300)
    ss_wall = _M._gb_box(tree, (rw, t, wh), (rx, ry - rd * 0.5 + t * 0.5, wz), base_x, node_y + 600)
    ew_wall = _M._gb_box(tree, (t, rd, wh), (rx + rw * 0.5 - t * 0.5, ry, wz), base_x, node_y + 900)
    ww_wall = _M._gb_box(tree, (t, rd, wh), (rx - rw * 0.5 + t * 0.5, ry, wz), base_x, node_y + 1200)

    cutters_ns, cutters_ew = [], []
    if with_doors:
        d_ns, d_ew = collect_door_cutters_for_rect(
            tree, props, rw, rd, t, getattr(props, "gb_door_height", 2.4),
            getattr(props, "gb_door_width", 1.6), base_x, node_y, rx, ry)
        cutters_ns.extend(d_ns)
        cutters_ew.extend(d_ew)
    if with_windows:
        w_ns, w_ew = collect_window_cutters_for_rect(
            tree, props, rw, rd, t, H, base_x, node_y, rx, ry)
        cutters_ns.extend(w_ns)
        cutters_ew.extend(w_ew)

    for wall, side, ny in (
        (ns_wall, "N", 300), (ss_wall, "S", 600),
        (ew_wall, "E", 900), (ww_wall, "W", 1200),
    ):
        cut = apply_openings_to_wall(tree, wall, side, cutters_ns, cutters_ew, base_x, node_y + ny)
        if cut:
            parts.append(cut)

    if with_ceiling is None:
        with_ceiling = getattr(props, "gb_ceiling", False)
    if with_ceiling:
        ceil = _M._gb_box(tree, (rw, rd, t), (rx, ry, H + t * 0.5), base_x, node_y + 700, "ceiling")
        if ceil:
            parts.append(ceil)
    return parts


def build_greybox_room(tree, props, base_x=-1400):
    W = getattr(props, "gb_width", 8.0)
    D = getattr(props, "gb_depth", 6.0)
    H = getattr(props, "gb_height", 3.5)
    t = getattr(props, "gb_wall_thick", 0.3)
    parts = rect_room_shell(tree, props, W, D, H, t, base_x, 0)
    return _M._gb_join(tree, parts, base_x + 1600, 0)


def build_greybox_corridor(tree, props, base_x=-1400):
    L, W, H, t = corridor_dims(props)
    parts = []

    floor = _M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0)
    if floor:
        parts.append(floor)

    wall_z = t + (H - t) * 0.5
    wall_h = H - t
    lw = _M._gb_box(tree, (t, L, wall_h), (-W * 0.5 + t * 0.5, 0, wall_z), base_x, 300)
    rw = _M._gb_box(tree, (t, L, wall_h), (W * 0.5 - t * 0.5, 0, wall_z), base_x, 600)
    if lw:
        parts.append(lw)
    if rw:
        parts.append(rw)

    parts.extend(add_corridor_ceiling(tree, props, base_x, W, L, H, t, 0, 0, 900))
    parts.extend(corridor_ribs(tree, props, base_x, L, W, H, t, 0, 0, False, 1200))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, 0, 0, False, 2000, -1))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, 0, 0, False, 2100, 1))

    return _M._gb_join(tree, parts, base_x + 1600, 0)


def junction_column(tree, props, base_x, cx, cy, W, H, t, node_y):
    if not getattr(props, "gb_junction_column", False):
        return []
    col_w = max(W * 0.22, t * 2.5, 0.35)
    col = _M._gb_box(tree, (col_w, col_w, H - t), (cx, cy, t + (H - t) * 0.5), base_x, node_y, "trim")
    return [col] if col else []


def corner_sleeve_bend(tree, props, base_x, W, L, H, t, node_y):
    """L-bend inner corner sleeve — quarter floor + return walls (not solid infill)."""
    parts = []
    sleeve = min(W, L) * 0.5
    wh = H - t
    wz = t + wh * 0.5
    icx = W * 0.5 - t
    icy = L - sleeve * 0.5
    qf = _M._gb_box(tree, (sleeve, sleeve, t), (icx - sleeve * 0.5, icy, t * 0.5), base_x, node_y, "floor")
    if qf:
        parts.append(qf)
    rw_a = _M._gb_box(tree, (t, sleeve, wh), (W * 0.5 - t * 1.5, icy, wz), base_x, node_y + 80, "wall")
    rw_b = _M._gb_box(tree, (sleeve, t, wh), (icx - sleeve * 0.5, L - t * 1.5, wz), base_x, node_y + 160, "wall")
    if rw_a:
        parts.append(rw_a)
    if rw_b:
        parts.append(rw_b)
    chamfer = max(t * 0.9, 0.14)
    ch = _M._gb_box(
        tree,
        (chamfer, chamfer, wh),
        (W * 0.5 - t - chamfer * 0.5, L - t - chamfer * 0.5, wz),
        base_x,
        node_y + 240,
        "trim",
    )
    if ch:
        parts.append(ch)
    parts.extend(add_corridor_ceiling(tree, props, base_x, sleeve, sleeve, H, t, icx - sleeve * 0.5, icy, node_y + 320))
    return parts


def build_greybox_corridor_bend(tree, props, base_x=-1400):
    """90° bent (L-shaped) corridor: Arm A along +Y, Arm B along +X."""
    L, W, H, t = corridor_dims(props)
    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t

    parts.append(_M._gb_box(tree, (W, L, t), (0, L * 0.5, t * 0.5), base_x, 0))
    parts.append(_M._gb_box(tree, (t, L, wh), (-W * 0.5 + t * 0.5, L * 0.5, wz), base_x, 300))
    parts.append(_M._gb_box(tree, (t, L, wh), (W * 0.5 - t * 0.5, L * 0.5, wz), base_x, 600))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, L, H, t, 0, L * 0.5, 900))
    parts.extend(corridor_ribs(tree, props, base_x, L, W, H, t, 0, L * 0.5, False, 1000))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, 0, L * 0.5, False, 1100, -1))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, 0, L * 0.5, False, 1150, 1))

    ox = W * 0.5 + L * 0.5
    oy = L
    parts.append(_M._gb_box(tree, (L, W, t), (ox, oy, t * 0.5), base_x, 1200))
    parts.append(_M._gb_box(tree, (L, t, wh), (ox, oy - W * 0.5 + t * 0.5, wz), base_x, 1500))
    parts.append(_M._gb_box(tree, (L, t, wh), (ox, oy + W * 0.5 - t * 0.5, wz), base_x, 1800))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, L, H, t, ox, oy, 2100, along_x=True))
    parts.extend(corridor_ribs(tree, props, base_x, L, W, H, t, ox, oy, True, 2200))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, ox, oy, True, 2300, -1))
    parts.extend(corridor_wainscot(tree, props, base_x, L, W, H, t, ox, oy, True, 2350, 1))

    parts.extend(corner_sleeve_bend(tree, props, base_x, W, L, H, t, 2400))
    return _M._gb_join(tree, parts, base_x + 3200, 0)


def build_greybox_corridor_cross(tree, props, base_x=-1400):
    """4-way cross intersection with optional hub column and ceiling kit."""
    L, W, H, t = corridor_dims(props)
    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t

    parts.append(_M._gb_box(tree, (W, W, t), (0, 0, t * 0.5), base_x, 0))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, W, H, t, 0, 0, 300))
    parts.extend(junction_column(tree, props, base_x, 0, 0, W, H, t, 350))

    arms = [
        (L * 0.5 + W * 0.5, 0, True),
        (-(L * 0.5 + W * 0.5), 0, True),
        (0, L * 0.5 + W * 0.5, False),
        (0, -(L * 0.5 + W * 0.5), False),
    ]
    for ai, (ax, ay, along_x) in enumerate(arms):
        ny = 600 + ai * 500
        if along_x:
            fw, fd = L, W
            wall_off = W * 0.5 - t * 0.5
            parts.append(_M._gb_box(tree, (fw, fd, t), (ax, ay, t * 0.5), base_x, ny))
            parts.append(_M._gb_box(tree, (fw, t, wh), (ax, ay - wall_off, wz), base_x, ny + 100))
            parts.append(_M._gb_box(tree, (fw, t, wh), (ax, ay + wall_off, wz), base_x, ny + 200))
            parts.extend(add_corridor_ceiling(tree, props, base_x, fd, fw, H, t, ax, ay, ny + 300, along_x=True))
            parts.extend(corridor_ribs(tree, props, base_x, fw, fd, H, t, ax, ay, True, ny + 400))
        else:
            fw, fd = W, L
            wall_off = W * 0.5 - t * 0.5
            parts.append(_M._gb_box(tree, (fw, fd, t), (ax, ay, t * 0.5), base_x, ny))
            parts.append(_M._gb_box(tree, (t, fd, wh), (ax - wall_off, ay, wz), base_x, ny + 100))
            parts.append(_M._gb_box(tree, (t, fd, wh), (ax + wall_off, ay, wz), base_x, ny + 200))
            parts.extend(add_corridor_ceiling(tree, props, base_x, fw, fd, H, t, ax, ay, ny + 300))
            parts.extend(corridor_ribs(tree, props, base_x, fd, fw, H, t, ax, ay, False, ny + 400))
    return _M._gb_join(tree, parts, base_x + 2600, 0)


def build_greybox_corridor_t(tree, props, base_x=-1400):
    """T-junction corridor: main hall along Y + side arm along +X."""
    L, W, H, t = corridor_dims(props)
    arm_len = L * 0.6
    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t

    parts.append(_M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0))
    parts.append(_M._gb_box(tree, (t, L, wh), (-W * 0.5 + t * 0.5, 0, wz), base_x, 300))
    parts.append(_M._gb_box(tree, (t, L, wh), (W * 0.5 - t * 0.5, 0, wz), base_x, 600))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, L, H, t, 0, 0, 900))
    parts.extend(corridor_ribs(tree, props, base_x, L, W, H, t, 0, 0, False, 1000))
    parts.extend(junction_column(tree, props, base_x, 0, 0, W, H, t, 1050))

    ax = W * 0.5 + arm_len * 0.5
    ay = 0
    parts.append(_M._gb_box(tree, (arm_len, W, t), (ax, ay, t * 0.5), base_x, 1200))
    parts.append(_M._gb_box(tree, (arm_len, t, wh), (ax, ay - W * 0.5 + t * 0.5, wz), base_x, 1500))
    parts.append(_M._gb_box(tree, (arm_len, t, wh), (ax, ay + W * 0.5 - t * 0.5, wz), base_x, 1800))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, arm_len, H, t, ax, ay, 2100, along_x=True))
    parts.extend(corridor_ribs(tree, props, base_x, arm_len, W, H, t, ax, ay, True, 2200))
    return _M._gb_join(tree, parts, base_x + 2800, 0)


def build_greybox_corridor_door_end(tree, props, base_x=-1400):
    """Corridor end cap: short tileable run + end wall with door boolean + recess trim."""
    L, W, H, t = corridor_dims(props)
    dw = getattr(props, "gb_door_width", 1.6)
    dh = getattr(props, "gb_door_height", 2.6)
    stub = min(L, max(W * 1.5, 2.0))
    parts = []
    wh = H - t
    wz = t + wh * 0.5
    end_y = stub * 0.5

    parts.append(_M._gb_box(tree, (W, stub, t), (0, 0, t * 0.5), base_x, 0))
    parts.append(_M._gb_box(tree, (t, stub, wh), (-W * 0.5 + t * 0.5, 0, wz), base_x, 200))
    parts.append(_M._gb_box(tree, (t, stub, wh), (W * 0.5 - t * 0.5, 0, wz), base_x, 400))
    parts.extend(add_corridor_ceiling(tree, props, base_x, W, stub, H, t, 0, 0, 600))
    parts.extend(corridor_ribs(tree, props, base_x, stub, W, H, t, 0, 0, False, 700))
    parts.extend(corridor_wainscot(tree, props, base_x, stub, W, H, t, 0, 0, False, 800, -1))
    parts.extend(corridor_wainscot(tree, props, base_x, stub, W, H, t, 0, 0, False, 850, 1))

    slab = _M._gb_box(tree, (W, t, H), (0, end_y, H * 0.5), base_x, 1000)
    cutter = _M._gb_box(tree, (dw, t * 4, dh), (0, end_y, dh * 0.5), base_x + 400, 1000, "door")
    cut = _M._gb_bool_diff(tree, slab, [cutter], base_x + 800, 1000)
    if cut:
        parts.append(cut)
    parts.extend(_M._gb_doorway_frame_trim(tree, props, base_x + 1200, dw, dh, t, node_y=1000))
    return _M._gb_join(tree, parts, base_x + 2000, 0)


def attach_to_monolith(monolith):
    bind(monolith)
    mapping = {
        "_gb_corridor_rib_offset": corridor_rib_offset,
        "_gb_resolve_corridor_width": resolve_corridor_width,
        "_gb_corridor_dims": corridor_dims,
        "_gb_ceiling_mode": ceiling_mode,
        "_gb_ceiling_active": ceiling_active,
        "_gb_add_corridor_ceiling": add_corridor_ceiling,
        "_gb_corridor_ribs": corridor_ribs,
        "_gb_corridor_wainscot": corridor_wainscot,
        "_gb_opening_cutter_depth": opening_cutter_depth,
        "_gb_collect_door_cutters_for_rect": collect_door_cutters_for_rect,
        "_gb_collect_window_cutters_for_rect": collect_window_cutters_for_rect,
        "_gb_apply_openings_to_wall": apply_openings_to_wall,
        "_gb_rect_room_shell": rect_room_shell,
        "build_greybox_room": build_greybox_room,
        "build_greybox_corridor": build_greybox_corridor,
        "_gb_junction_column": junction_column,
        "_gb_corner_sleeve_bend": corner_sleeve_bend,
        "build_greybox_corridor_bend": build_greybox_corridor_bend,
        "build_greybox_corridor_cross": build_greybox_corridor_cross,
        "build_greybox_corridor_t": build_greybox_corridor_t,
        "build_greybox_corridor_door_end": build_greybox_corridor_door_end,
    }
    for name, fn in mapping.items():
        _patch(name, fn)
