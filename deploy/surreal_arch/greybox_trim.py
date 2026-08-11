"""Greybox trim extensions — window reveals."""

from __future__ import annotations


def gb_window_reveal_parts(tree, M, props, base_x, wall_w, wall_h, wall_t,
                           cx, cy, cz, facing_y=True, node_y=0, facing_x=False):
    """Recessed sill/head/jamb bands for trim-sheet window openings."""
    if not getattr(props, "gb_windows_enabled", False):
        return []
    mode = M._gb_trim_mode(props)
    if mode == "NONE":
        return []
    recess = M._gb_trim_depth(props, wall_t)
    ft = max(wall_t * 0.2, 0.03)
    ww = getattr(props, "gb_window_width", 0.8)
    wh = getattr(props, "gb_window_height", 0.8)
    sill = getattr(props, "gb_window_sill", 1.0)
    parts = []
    head_z = sill + wh + ft * 0.5
    sill_z = sill - ft * 0.5
    mid_z = sill + wh * 0.5
    if facing_y:
        y_pos = wall_t * 0.5 - recess - ft * 0.5 if mode == "RECESS" else wall_t * 0.5 + recess + ft * 0.5
        parts.append(M._gb_box(tree, (ww + ft * 2, ft, ft), (cx, cy + y_pos, head_z),
                               base_x, node_y, "trim"))
        parts.append(M._gb_box(tree, (ww + ft * 2, ft, ft), (cx, cy + y_pos, sill_z),
                               base_x, node_y + 50, "trim"))
        for sx in (-1, 1):
            parts.append(M._gb_box(tree, (ft, ft, wh + ft * 2),
                                   (cx + sx * (ww * 0.5 + ft * 0.5), cy + y_pos, mid_z),
                                   base_x, node_y + 100 + sx * 20, "trim"))
    elif facing_x:
        x_pos = wall_t * 0.5 - recess - ft * 0.5 if mode == "RECESS" else wall_t * 0.5 + recess + ft * 0.5
        parts.append(M._gb_box(tree, (ft, ww + ft * 2, ft), (cx + x_pos, cy, head_z),
                               base_x, node_y, "trim"))
        parts.append(M._gb_box(tree, (ft, ww + ft * 2, ft), (cx + x_pos, cy, sill_z),
                               base_x, node_y + 50, "trim"))
        for sy in (-1, 1):
            parts.append(M._gb_box(tree, (ft, ft, wh + ft * 2),
                                   (cx + x_pos, cy + sy * (ww * 0.5 + ft * 0.5), mid_z),
                                   base_x, node_y + 100 + sy * 20, "trim"))
    return [p for p in parts if p is not None]


def gb_rect_room_window_reveals(tree, M, props, base_x, rw, rd, H, t, rx=0.0, ry=0.0, node_y=0):
    """Window reveal trim for rectangular room shells (mirrors window cutter layout)."""
    if not getattr(props, "gb_windows_enabled", False):
        return []
    parts = []
    idx = 0
    if getattr(props, "gb_windows_enabled", False):
        win_w = getattr(props, "gb_window_width", 0.8)
        win_h = getattr(props, "gb_window_height", 0.8)
        sill = getattr(props, "gb_window_sill", 1.0)
        n_ns = max(0, getattr(props, "gb_window_count_ns", 0))
        n_ew = max(0, getattr(props, "gb_window_count_ew", 0))
        for i in range(n_ns):
            frac = (i + 1) / (n_ns + 1)
            wx = rx - rw * 0.5 + frac * rw
            parts.extend(gb_window_reveal_parts(
                tree, M, props, base_x, rw, H, t, wx, ry + rd * 0.5, 0,
                facing_y=True, node_y=node_y + 3000 + idx))
            parts.extend(gb_window_reveal_parts(
                tree, M, props, base_x, rw, H, t, wx, ry - rd * 0.5, 0,
                facing_y=True, node_y=node_y + 3100 + idx))
            idx += 1
        for i in range(n_ew):
            frac = (i + 1) / (n_ew + 1)
            wy = ry - rd * 0.5 + frac * rd
            parts.extend(gb_window_reveal_parts(
                tree, M, props, base_x, rd, H, t, rx + rw * 0.5, wy, 0,
                facing_y=False, facing_x=True, node_y=node_y + 3200 + idx))
            parts.extend(gb_window_reveal_parts(
                tree, M, props, base_x, rd, H, t, rx - rw * 0.5, wy, 0,
                facing_y=False, facing_x=True, node_y=node_y + 3300 + idx))
            idx += 1
    else:
        win_w = getattr(props, "gb_window_width", getattr(props, "gb_door_width", 1.0) * 0.8)
        win_h = getattr(props, "gb_window_height", 1.4)
        wn = getattr(props, "gb_window_count", 2)
        for do_win, wall_dir, w_dir_x, w_dir_y in [
            (getattr(props, "gb_window_n", False), "N", 0, rd * 0.5),
            (getattr(props, "gb_window_s", False), "S", 0, -rd * 0.5),
            (getattr(props, "gb_window_e", True), "E", rw * 0.5, 0),
            (getattr(props, "gb_window_w", True), "W", -rw * 0.5, 0),
        ]:
            if not do_win:
                continue
            wall_len = rw if wall_dir in ("N", "S") else rd
            for wi in range(wn):
                frac = (wi + 0.5) / wn
                if wall_dir in ("N", "S"):
                    wx = rx - rw * 0.5 + wall_len * frac
                    wy = ry + w_dir_y
                    parts.extend(gb_window_reveal_parts(
                        tree, M, props, base_x, rw, H, t, wx, wy, 0,
                        facing_y=True, node_y=node_y + 3400 + idx))
                else:
                    wx = rx + w_dir_x
                    wy = ry - rd * 0.5 + wall_len * frac
                    parts.extend(gb_window_reveal_parts(
                        tree, M, props, base_x, rd, H, t, wx, wy, 0,
                        facing_y=False, facing_x=True, node_y=node_y + 3500 + idx))
                idx += 1
    return parts
