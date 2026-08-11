"""Greybox tower shells — multi-floor walkable blockouts (v2.72.2)."""

from __future__ import annotations

_M = None


def bind(monolith):
    global _M
    _M = monolith


def _require():
    if _M is None:
        raise RuntimeError("surreal_greybox.towers not bound — call bind(monolith) at register")


def _patch(name, fn):
    _require()
    setattr(_M, name, fn)
    mod = getattr(_M, "__name__", None)
    if mod:
        import sys
        module = sys.modules.get(mod)
        if module is not None:
            setattr(module, name, fn)


def build_greybox_tower(tree, props, base_x=-1400):
    """Multi-floor tower blockout: outer shell + internal floor slabs + window openings."""
    M = _M
    floors = max(1, getattr(props, "gb_floors", 4))
    fh = getattr(props, "gb_height", 3.2)
    W = getattr(props, "gb_width", 6.0)
    D = getattr(props, "gb_depth", 6.0)
    t = getattr(props, "gb_wall_thick", 0.35)
    ww = getattr(props, "gb_door_width", 1.4)
    wh = getattr(props, "gb_door_height", 1.4)
    parts = []
    total_h = floors * fh
    cutters = []
    wall_z_center = total_h * 0.5
    walls = {
        "N": M._gb_box(tree, (W, t, total_h), (0, D * 0.5 - t * 0.5, wall_z_center), base_x, 0),
        "S": M._gb_box(tree, (W, t, total_h), (0, -D * 0.5 + t * 0.5, wall_z_center), base_x, 300),
        "E": M._gb_box(tree, (t, D, total_h), (W * 0.5 - t * 0.5, 0, wall_z_center), base_x, 600),
        "W": M._gb_box(tree, (t, D, total_h), (-W * 0.5 + t * 0.5, 0, wall_z_center), base_x, 900),
    }
    win_cut_n, win_cut_s = [], []
    for f in range(floors):
        cz = f * fh + fh * 0.55
        if f == 0:
            dcut = M._gb_box(
                tree, (ww * 1.3, t * 3, fh * 0.8),
                (0, -D * 0.5, (fh * 0.8) * 0.5), base_x + 500, 300, "door",
            )
            win_cut_s.append(dcut)
        else:
            wcut_n = M._gb_box(tree, (ww, t * 3, wh), (0, D * 0.5, cz), base_x + 500, f * 120, "window")
            wcut_s = M._gb_box(tree, (ww, t * 3, wh), (0, -D * 0.5, cz), base_x + 500, 300 + f * 120, "window")
            win_cut_n.append(wcut_n)
            win_cut_s.append(wcut_s)
    walls["N"] = M._gb_bool_diff(tree, walls["N"], win_cut_n, base_x + 900, 0)
    walls["S"] = M._gb_bool_diff(tree, walls["S"], win_cut_s, base_x + 900, 300)
    for k in walls:
        if walls[k]:
            parts.append(walls[k])
    for f in range(1, floors):
        slab = M._gb_box(
            tree, (W - t * 2, D - t * 2, t),
            (0, 0, f * fh + t * 0.5), base_x, 1200 + f * 120, "level",
        )
        if slab:
            parts.append(slab)
    base_floor = M._gb_box(tree, (W, D, t), (0, 0, t * 0.5), base_x, 1100, "level")
    if base_floor:
        parts.append(base_floor)
    roof = M._gb_box(tree, (W, D, t), (0, 0, total_h + t * 0.5), base_x, 1150, "ceiling")
    if roof:
        parts.append(roof)
    return M._gb_join(tree, parts, base_x + 1600, 0)


def attach_to_monolith(monolith):
    bind(monolith)
    _patch("build_greybox_tower", build_greybox_tower)
