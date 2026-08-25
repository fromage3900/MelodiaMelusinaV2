"""Corridor + room shell builders - surreal_greybox phase 2."""

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
        raise RuntimeError("surreal_greybox.shells not bound - call bind(monolith) at register")


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


def _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y, cx, cy, cz, facing_y=True):
    """Build a GN cutter for the current gb_window_shape - falls back to box if GN cylinder unavailable."""
    shape = getattr(props, "gb_window_shape", "RECT")
    arch_h = getattr(props, "gb_window_arch_height", 0.4)
    safe = getattr(_M, "_safe_node", None)
    # Helpers
    def _box(w, d, h, x, y, z, bx, ny):
        if facing_y:
            return _M._gb_box(tree, (w, d, h), (x, y, z), bx, ny, "door")
        else:
            return _M._gb_box(tree, (d, w, h), (x, y, z), bx, ny, "door")

    # Fast path: rect / lintel
    if shape in ("RECT", "LINTEL", None):
        return _box(win_w, depth, win_h, cx, cy, cz, base_x, node_y)

    # Circle / Rosette - cylinder through wall
    if shape in ("CIRCLE", "ROSETTE"):
        if safe:
            try:
                cyl = safe(tree, "GeometryNodeMeshCylinder", (base_x, node_y))
                if cyl:
                    try:
                        cyl.inputs["Radius"].default_value = max(win_w, win_h) * 0.5
                    except Exception:
                        pass
                    try:
                        cyl.inputs["Depth"].default_value = depth
                    except Exception:
                        # some Blender versions use "Depth" vs "Height"
                        try:
                            cyl.inputs[1].default_value = depth
                        except Exception:
                            pass
                    try:
                        cyl.inputs["Vertices"].default_value = 24 if shape == "CIRCLE" else 32
                    except Exception:
                        pass
                    # Rotate 90deg so axis points through wall
                    xf = safe(tree, "GeometryNodeTransform", (base_x + 50, node_y))
                    if xf:
                        tree.links.new(cyl.outputs[0], xf.inputs["Geometry"])
                        ang = (1.57079632679, 0, 0) if facing_y else (0, 1.57079632679, 0)
                        try:
                            xf.inputs["Rotation"].default_value = ang
                        except Exception:
                            pass
                        try:
                            xf.inputs["Translation"].default_value = (cx, cy, cz)
                        except Exception:
                            pass
                        # We built cutter at origin then xformed; need to compensate: cylinder already at origin, so translate to cx,cy,cz
                        # For _gb_box path we translated via box loc; here xf does it
                        return xf.outputs["Geometry"]
                    return cyl.outputs[0]
            except Exception:
                pass
        return _box(win_w, depth, win_h, cx, cy, cz, base_x, node_y)

    # Arch shapes: box + top arch (joined)
    if shape in ("ARCH_ROUND", "SEGMENTAL", "GOTHIC", "OGEE"):
        # Lower rect part
        rect_h = win_h
        rect_cz = cz
        rect = _box(win_w, depth, rect_h, cx, cy, rect_cz, base_x, node_y)
        if shape in ("GOTHIC", "OGEE") and safe:
            # Pointed arch: use two half-boxes meeting at apex (approx)
            # Build apex prism: thin box at arch peak
            apex_z = cz + rect_h * 0.5 + arch_h * 0.5
            # For GN join, create top prism as box then join
            top = _box(win_w * 0.55, depth, arch_h, cx, cy, apex_z, base_x + 40, node_y + 20)
            if rect is not None and top is not None:
                j = safe(tree, "GeometryNodeJoinGeometry", (base_x + 80, node_y))
                if j:
                    tree.links.new(rect, j.inputs["Geometry"])
                    tree.links.new(top, j.inputs["Geometry"])
                    return j.outputs["Geometry"]
            return rect if rect is not None else top
        if shape in ("ARCH_ROUND", "SEGMENTAL") and safe:
            # Round / segmental: half-cylinder on top of rect
            try:
                cyl = safe(tree, "GeometryNodeMeshCylinder", (base_x + 30, node_y + 30))
                if cyl and rect is not None:
                    rad = win_w * 0.5
                    # Clamp arch height to radius for round, or shallow for segmental
                    ah = min(arch_h, rad) if shape == "ARCH_ROUND" else min(arch_h, rad * 0.6)
                    try:
                        cyl.inputs["Radius"].default_value = rad
                    except Exception:
                        pass
                    try:
                        cyl.inputs["Depth"].default_value = depth
                    except Exception:
                        pass
                    try:
                        cyl.inputs["Vertices"].default_value = 20
                    except Exception:
                        pass
                    # Use half: we build full cylinder then intersect via transform clip? Simpler: join rect + full cyl then outer trim
                    # Position cylinder so its bottom sits at rect top
                    cyl_cz = cz + rect_h * 0.5 + ah * 0.25
                    xf = safe(tree, "GeometryNodeTransform", (base_x + 60, node_y + 30))
                    if xf:
                        tree.links.new(cyl.outputs[0], xf.inputs["Geometry"])
                        ang = (1.57079632679, 0, 0) if facing_y else (0, 1.57079632679, 0)
                        try:
                            xf.inputs["Rotation"].default_value = ang
                        except Exception:
                            pass
                        try:
                            xf.inputs["Translation"].default_value = (cx, cy, cyl_cz)
                        except Exception:
                            pass
                        cyl_xf = xf.outputs["Geometry"]
                        j = safe(tree, "GeometryNodeJoinGeometry", (base_x + 90, node_y))
                        if j:
                            tree.links.new(rect, j.inputs["Geometry"])
                            tree.links.new(cyl_xf, j.inputs["Geometry"])
                            return j.outputs["Geometry"]
            except Exception:
                pass
        # Fallback: enlarge rect height by arch
        return _box(win_w, depth, win_h + arch_h * 0.5, cx, cy, cz + arch_h * 0.25, base_x, node_y)

    return _box(win_w, depth, win_h, cx, cy, cz, base_x, node_y)


def _window_frame_extra_parts(tree, props, win_w, win_h, cx, cy, cz, facing_y, base_x, node_y):
    """Frame / mullion / transom / glazing trim parts to sit inside the opening (not cutters)."""
    ft = getattr(props, "gb_window_frame_thickness", 0.1)
    if ft < 0.02:
        ft = 0.06
    has_mullion = getattr(props, "gb_window_has_mullion", False)
    has_transom = getattr(props, "gb_window_has_transom", False)
    has_glazing = getattr(props, "gb_window_glazing", False)
    shape = getattr(props, "gb_window_shape", "RECT")
    if shape in ("CIRCLE", "ROSETTE"):
        # Circular windows: frame is torus-like; simplified as glazing disc only
        if has_glazing:
            safe = getattr(_M, "_safe_node", None)
            if safe:
                try:
                    disc = safe(tree, "GeometryNodeMeshCylinder", (base_x, node_y))
                    if disc:
                        try:
                            disc.inputs["Radius"].default_value = max(win_w, win_h) * 0.5 - ft
                        except Exception:
                            pass
                        try:
                            disc.inputs["Depth"].default_value = 0.015
                        except Exception:
                            pass
                        xf = safe(tree, "GeometryNodeTransform", (base_x + 50, node_y))
                        if xf:
                            tree.links.new(disc.outputs[0], xf.inputs["Geometry"])
                            ang = (1.57079632679, 0, 0) if facing_y else (0, 1.57079632679, 0)
                            try:
                                xf.inputs["Rotation"].default_value = ang
                            except Exception:
                                pass
                            try:
                                xf.inputs["Translation"].default_value = (cx, cy, cz)
                            except Exception:
                                pass
                            # Tag as glass trim zone via helper if available
                            try:
                                from surreal_arch.trim_color_bake import tag_trim_geometry
                                return [tag_trim_geometry(_M, tree, xf.outputs["Geometry"], win_w, win_h, trim_value=5.0)]
                            except Exception:
                                return [xf.outputs["Geometry"]]
                except Exception:
                    pass
        return []
    parts = []
    # Mullion (vertical centre)
    if has_mullion:
        # vertical bar 40mm thick, full height inside reveal
        bw = max(ft * 0.6, 0.035)
        if facing_y:
            parts.append(_M._gb_box(tree, (bw, ft * 0.5, win_h), (cx, cy, cz), base_x, node_y, "trim"))
        else:
            parts.append(_M._gb_box(tree, (ft * 0.5, bw, win_h), (cx, cy, cz), base_x, node_y, "trim"))
    if has_transom:
        bw = max(ft * 0.6, 0.035)
        if facing_y:
            parts.append(_M._gb_box(tree, (win_w, ft * 0.5, bw), (cx, cy, cz), base_x, node_y + 40, "trim"))
        else:
            parts.append(_M._gb_box(tree, (ft * 0.5, win_w, bw), (cx, cy, cz), base_x, node_y + 40, "trim"))
    if has_glazing:
        # Thin glass plane recessed 10mm
        recess = max(_M._gb_trim_depth(props, getattr(props, "gb_wall_thick", 0.3)) * 0.5, 0.012) if hasattr(_M, "_gb_trim_depth") else 0.012
        gx = cx + (recess if not facing_y else 0)
        gy = cy + (recess if facing_y else 0)
        # push slightly inside wall
        if facing_y:
            gy = cy + (0.01 if True else 0)
        try:
            from surreal_arch.trim_color_bake import tag_trim_geometry
            if facing_y:
                g = _M._gb_box(tree, (win_w - ft, 0.012, win_h - ft), (cx, cy, cz), base_x, node_y + 80, "trim")
            else:
                g = _M._gb_box(tree, (0.012, win_w - ft, win_h - ft), (cx, cy, cz), base_x, node_y + 80, "trim")
            if g is not None:
                parts.append(tag_trim_geometry(_M, tree, g, win_w, win_h, trim_value=5.0))
        except Exception:
            if facing_y:
                g = _M._gb_box(tree, (win_w - ft, 0.012, win_h - ft), (cx, cy, cz), base_x, node_y + 80, "trim")
            else:
                g = _M._gb_box(tree, (0.012, win_w - ft, win_h - ft), (cx, cy, cz), base_x, node_y + 80, "trim")
            if g is not None:
                parts.append(g)
    return [p for p in parts if p is not None]


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
            cutters_ns.append(("N", _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 1500 + i * 10, wx, ry + rd * 0.5, win_z, True)))
            cutters_ns.append(("S", _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 1600 + i * 10, wx, ry - rd * 0.5, win_z, True)))
        for i in range(n_ew):
            frac = (i + 1) / (n_ew + 1)
            wy = ry - rd * 0.5 + frac * rd
            cutters_ew.append(("E", _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 1700 + i * 10, rx + rw * 0.5, wy, win_z, False)))
            cutters_ew.append(("W", _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 1800 + i * 10, rx - rw * 0.5, wy, win_z, False)))
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
                facing_y = wall_dir in ("N", "S")
                if wall_dir in ("N", "S"):
                    wx = rx - rw * 0.5 + wall_len * frac
                    wy = ry + w_dir_y
                    cutters_ns.append((wall_dir, _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 1900 + wi * 10, wx, wy, win_z, True)))
                else:
                    wx = rx + w_dir_x
                    wy = ry - rd * 0.5 + wall_len * frac
                    cutters_ew.append((wall_dir, _window_cutter_geometry(tree, props, win_w, win_h, depth, base_x, node_y + 2000 + wi * 10, wx, wy, win_z, False)))
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

    # Window frame / mullion / glazing extras (sit inside openings, tagged as trim)
    if with_windows and (getattr(props, "gb_window_has_mullion", False) or getattr(props, "gb_window_has_transom", False) or getattr(props, "gb_window_glazing", False)):
        win_w = getattr(props, "gb_window_width", 0.8)
        win_h = getattr(props, "gb_window_height", 0.8)
        sill = getattr(props, "gb_window_sill", 1.0)
        if getattr(props, "gb_windows_enabled", False):
            win_z = t + sill + win_h * 0.5
            n_ns = max(0, getattr(props, "gb_window_count_ns", 0))
            n_ew = max(0, getattr(props, "gb_window_count_ew", 0))
            for i in range(n_ns):
                frac = (i + 1) / (n_ns + 1)
                wx = rx - rw * 0.5 + frac * rw
                parts.extend(_window_frame_extra_parts(tree, props, win_w, win_h, wx, ry + rd * 0.5, win_z, True, base_x + 2500, node_y + 400 + i * 10))
                parts.extend(_window_frame_extra_parts(tree, props, win_w, win_h, wx, ry - rd * 0.5, win_z, True, base_x + 2600, node_y + 400 + i * 10))
            for i in range(n_ew):
                frac = (i + 1) / (n_ew + 1)
                wy = ry - rd * 0.5 + frac * rd
                parts.extend(_window_frame_extra_parts(tree, props, win_w, win_h, rx + rw * 0.5, wy, win_z, False, base_x + 2700, node_y + 400 + i * 10))
                parts.extend(_window_frame_extra_parts(tree, props, win_w, win_h, rx - rw * 0.5, wy, win_z, False, base_x + 2800, node_y + 400 + i * 10))
        else:
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
                facing_y = wall_dir in ("N", "S")
                for wi in range(wn):
                    frac = (wi + 0.5) / wn
                    if facing_y:
                        wx = rx - rw * 0.5 + wall_len * frac
                        wy = ry + w_dir_y
                    else:
                        wx = rx + w_dir_x
                        wy = ry - rd * 0.5 + wall_len * frac
                    parts.extend(_window_frame_extra_parts(tree, props, win_w, win_h, wx, wy, win_z, facing_y, base_x + 2900, node_y + 400 + wi * 10))

    if with_ceiling is None:
        with_ceiling = getattr(props, "gb_ceiling", False)
    if with_ceiling:
        ceil = _M._gb_box(tree, (rw, rd, t), (rx, ry, H + t * 0.5), base_x, node_y + 700, "ceiling")
        if ceil:
            parts.append(ceil)
    return parts


def _ngon_wall_ring(tree, props, radius, H, t, sides, base_x, node_y, cx=0.0, cy=0.0,
                    ellipse_ratio=1.0, super_n=2.0, with_caps=True):
    """Build a polygonal / circular / ellipse / superellipse wall ring + floor + optional ceiling."""
    import math
    # Resolve actual sides & shape params
    shape = getattr(props, "gb_room_shape", "RECTANGLE")
    gb_sides = getattr(props, "gb_room_sides", sides)
    gb_radius = getattr(props, "gb_room_radius", radius)
    gb_ellipse = getattr(props, "gb_room_ellipse_ratio", ellipse_ratio)
    gb_n = getattr(props, "gb_room_super_n", super_n)
    if shape in ("CIRCULAR", "APSIDAL"):
        n = max(16, gb_sides * 2)
    elif shape in ("OCTAGON",):
        n = 8
    elif shape in ("HEX",):
        n = 6
    elif shape in ("ELLIPSE", "SUPERELLIPSE", "FREEFORM"):
        n = max(12, gb_sides)
    else:
        n = max(3, gb_sides)
    r = max(1.0, gb_radius)
    # Build floor as mesh circle via GN: Curve Circle -> Fill -> Extrude
    parts = []
    # Floor: cylinder-like slab
    safe = getattr(_M, "_safe_node", None)
    if safe:
        # Try GN: Curve Circle + Fill + Extrude for organic floors
        try:
            circ = safe(tree, "GeometryNodeCurvePrimitiveCircle", (base_x - 400, node_y))
            if circ:
                try:
                    circ.inputs["Radius"].default_value = r
                except Exception:
                    pass
                try:
                    circ.inputs["Resolution"].default_value = n
                except Exception:
                    pass
                # Scale Y for ellipse
                if shape in ("ELLIPSE", "SUPERELLIPSE") and abs(gb_ellipse - 1.0) > 0.02:
                    # Use Transform to squash Y
                    fill = safe(tree, "GeometryNodeFillCurve", (base_x - 200, node_y))
                    ex = safe(tree, "GeometryNodeExtrudeMesh", (base_x, node_y))
                    xf = safe(tree, "GeometryNodeTransform", (base_x + 200, node_y))
                    if fill and ex and xf:
                        tree.links.new(circ.outputs["Curve"], fill.inputs["Curve"])
                        tree.links.new(fill.outputs["Mesh"], ex.inputs["Mesh"])
                        # extrude by t along Z
                        try:
                            ex.inputs["Offset Scale"].default_value = t
                        except Exception:
                            pass
                        tree.links.new(ex.outputs["Mesh"], xf.inputs["Geometry"])
                        try:
                            xf.inputs["Scale"].default_value = (1.0, gb_ellipse, 1.0)
                        except Exception:
                            pass
                        tree.links.new(xf.outputs["Geometry"], xf.outputs["Geometry"])  # dummy
                        # Use as floor piece
                        parts.append(xf.outputs["Geometry"])
                    else:
                        # fallback to box floor
                        raise RuntimeError("fill path missing")
                else:
                    # circular / ngon floor
                    fill = safe(tree, "GeometryNodeFillCurve", (base_x - 200, node_y))
                    ex = safe(tree, "GeometryNodeExtrudeMesh", (base_x, node_y))
                    if fill and ex:
                        tree.links.new(circ.outputs["Curve"], fill.inputs["Curve"])
                        tree.links.new(fill.outputs["Mesh"], ex.inputs["Mesh"])
                        try:
                            ex.inputs["Offset Scale"].default_value = t
                        except Exception:
                            pass
                        parts.append(ex.outputs["Mesh"])
                    else:
                        raise RuntimeError("fill path missing")
        except Exception:
            pass
    if not parts:
        # Fallback: approximate with box floor (always works)
        floor = _M._gb_box(tree, (r * 2, r * 2, t), (cx, cy, t * 0.5), base_x, node_y)
        if floor:
            parts.append(floor)
    # Walls: segment walls around the ring using boxes placed tangentially
    # For true curve walls we'd need GN Curve->Extrude walls; do segmented approximation for now (boolean-safe)
    import math as _math
    seg_len = 2 * r * _math.sin(_math.pi / n) if n >= 3 else r * 2
    wall_th = t
    wz = t + (H - t) * 0.5
    wh = H - t
    # Collect window cutters mapped angularly - distribute windows evenly around ring
    # Reuse rectangular window logic as angular distribution: windows per ring = gb_window_count_ns + gb_window_count_ew fallback
    win_w = getattr(props, "gb_window_width", 0.8)
    win_h = getattr(props, "gb_window_height", 0.8)
    sill = getattr(props, "gb_window_sill", 1.0)
    win_z = t + sill + win_h * 0.5
    if getattr(props, "gb_windows_enabled", False):
        wn = max(0, getattr(props, "gb_window_count_ns", 0) + getattr(props, "gb_window_count_ew", 0))
        if wn == 0:
            wn = max(1, getattr(props, "gb_window_count", 2))
    else:
        wn = 0
        if getattr(props, "gb_window_n", False) or getattr(props, "gb_window_e", False) or getattr(props, "gb_window_w", False):
            wn = max(1, getattr(props, "gb_window_count", 2))
    for i in range(n):
        ang = 2 * _math.pi * i / n
        # radius including ellipse/superellipse squash
        rr = r
        if shape == "SUPERELLIPSE":
            # superellipse radius factor: |cos|^n + |sin|^n
            c = abs(_math.cos(ang)) ** gb_n
            s = abs(_math.sin(ang) * gb_ellipse) ** gb_n if gb_ellipse != 1.0 else abs(_math.sin(ang)) ** gb_n
            denom = (c + s) ** (1.0 / gb_n) if (c + s) > 1e-6 else 1.0
            rr = r / denom
        elif shape == "ELLIPSE":
            rr = r * (1.0 if abs(_math.cos(ang)) > 0.5 else gb_ellipse)
        x = cx + rr * _math.cos(ang)
        y = cy + rr * _math.sin(ang)
        # Tangent angle = ang + 90deg
        tang = ang + _math.pi * 0.5
        # Wall segment: place box of length seg_len, thickness wall_th
        # Need rotation - _gb_box does not rotate; use Transform node via _M helper if available
        # Fallback: axis-aligned approx (still encloses ring, boolean doors not angular)
        # For now place axis-aligned wall centered at ang position with depth along tangent approx
        # Proper rotation requires GeometryNodeTransform - build via GN if available
        seg = _M._gb_box(tree, (wall_th, seg_len, wh), (x, y, wz), base_x + 300 + i * 20, node_y + i * 8, "wall")
        if seg is None:
            continue
        # Apply rotation via Transform if helper exists
        try:
            if safe:
                xf = safe(tree, "GeometryNodeTransform", (base_x + 500 + i * 20, node_y + 800 + i * 3))
                if xf:
                    tree.links.new(seg, xf.inputs["Geometry"])
                    try:
                        xf.inputs["Rotation"].default_value = (0, 0, tang)
                    except Exception:
                        pass
                    seg = xf.outputs["Geometry"]
        except Exception:
            pass
        # Window cutter for every k-th segment if windows enabled
        if wn > 0 and (i % max(1, n // wn) == 0):
            # Build cutter matching window shape (reuse helper)
            depth = opening_cutter_depth(t)
            # Minimal rectangular cutter rotated to wall tangent
            cutter = _M._gb_box(tree, (depth, win_w, win_h), (x, y, win_z), base_x + 900 + i * 20, node_y + 400 + i, "door")
            if cutter is not None:
                # Rotate cutter similarly
                try:
                    if safe:
                        cxf = safe(tree, "GeometryNodeTransform", (base_x + 1100 + i * 20, node_y + 900 + i))
                        if cxf:
                            tree.links.new(cutter, cxf.inputs["Geometry"])
                            try:
                                cxf.inputs["Rotation"].default_value = (0, 0, tang)
                            except Exception:
                                pass
                            cutter = cxf.outputs["Geometry"]
                except Exception:
                    pass
                cut = _M._gb_bool_diff(tree, seg, [cutter], base_x + 1300 + i * 20, node_y + 500 + i)
                parts.append(cut if cut is not None else seg)
            else:
                parts.append(seg)
        else:
            parts.append(seg)
    # Apse extension: for APSIDAL add rectangular stem
    if shape == "APSIDAL":
        stem_w = getattr(props, "gb_width", r * 1.6)
        stem_d = getattr(props, "gb_depth", r)
        stem_parts = rect_room_shell(tree, props, stem_w, stem_d, H, t, base_x + 800, node_y + 1500, rx=cx, ry=cy - stem_d * 0.5 - r * 0.5, with_ceiling=False, with_doors=False, with_windows=False)
        parts.extend([p for p in stem_parts if p is not None])
    # Ceiling
    if getattr(props, "gb_ceiling", False):
        ceil = None
        if safe and n >= 6:
            try:
                circ2 = safe(tree, "GeometryNodeCurvePrimitiveCircle", (base_x + 600, node_y + 1200))
                fill2 = safe(tree, "GeometryNodeFillCurve", (base_x + 800, node_y + 1200))
                ex2 = safe(tree, "GeometryNodeExtrudeMesh", (base_x + 1000, node_y + 1200))
                if circ2 and fill2 and ex2:
                    try:
                        circ2.inputs["Radius"].default_value = r - t
                    except Exception:
                        pass
                    tree.links.new(circ2.outputs["Curve"], fill2.inputs["Curve"])
                    tree.links.new(fill2.outputs["Mesh"], ex2.inputs["Mesh"])
                    ceil = ex2.outputs["Mesh"]
            except Exception:
                pass
        if ceil is None:
            ceil = _M._gb_box(tree, (r * 1.8, r * 1.8, t), (cx, cy, H + t * 0.5), base_x + 1000, node_y + 1200, "ceiling")
        if ceil is not None:
            parts.append(ceil)
    return parts


def _is_advanced_shape(props):
    shape = getattr(props, "gb_room_shape", "RECTANGLE")
    return shape in ("CIRCULAR", "APSIDAL", "OCTAGON", "HEX", "ELLIPSE", "SUPERELLIPSE", "FREEFORM")


def build_greybox_room(tree, props, base_x=-1400):
    W = getattr(props, "gb_width", 8.0)
    D = getattr(props, "gb_depth", 6.0)
    H = getattr(props, "gb_height", 3.5)
    t = getattr(props, "gb_wall_thick", 0.3)
    if _is_advanced_shape(props):
        parts = _ngon_wall_ring(tree, props, getattr(props, "gb_room_radius", 4.0), H, t, getattr(props, "gb_room_sides", 8), base_x, 0, ellipse_ratio=getattr(props, "gb_room_ellipse_ratio", 0.7), super_n=getattr(props, "gb_room_super_n", 4.0))
        return _M._gb_join(tree, parts, base_x + 1600, 0)
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
    """L-bend inner corner sleeve - quarter floor + return walls (not solid infill)."""
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
    """90deg bent (L-shaped) corridor: Arm A along +Y, Arm B along +X."""
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
