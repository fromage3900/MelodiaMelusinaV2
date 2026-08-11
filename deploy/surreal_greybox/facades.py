"""Facade rhythm builders — pilotis halls and column grids (v2.72.2)."""

from __future__ import annotations

_M = None


def bind(monolith):
    global _M
    _M = monolith


def _require():
    if _M is None:
        raise RuntimeError("surreal_greybox.facades not bound — call bind(monolith) at register")


def _patch(name, fn):
    _require()
    setattr(_M, name, fn)
    mod = getattr(_M, "__name__", None)
    if mod:
        import sys
        module = sys.modules.get(mod)
        if module is not None:
            setattr(module, name, fn)


def build_greybox_pillar_hall(tree, props, base_x=-1400):
    """Hypostyle hall blockout: column grid + floor + roof slab."""
    M = _M
    cols_x = max(2, getattr(props, "gb_cols_x", 4))
    cols_y = max(2, getattr(props, "gb_cols_y", 6))
    spacing = getattr(props, "gb_spacing", 3.0)
    H = getattr(props, "gb_height", 5.0)
    t = getattr(props, "gb_wall_thick", 0.3)
    col_r = getattr(props, "gb_leg_thick", 0.5)
    parts = []
    span_x = (cols_x - 1) * spacing
    span_y = (cols_y - 1) * spacing
    pad = spacing * 0.8
    fw = span_x + pad * 2
    fd = span_y + pad * 2
    floor = M._gb_box(tree, (fw, fd, t), (0, 0, -t * 0.5), base_x, 0)
    if floor:
        parts.append(floor)
    roof = M._gb_box(tree, (fw, fd, t), (0, 0, H - t * 0.5), base_x, 300, "ceiling")
    if roof:
        parts.append(roof)
    idx = 0
    for ix in range(cols_x):
        for iy in range(cols_y):
            cx = -span_x * 0.5 + ix * spacing
            cy = -span_y * 0.5 + iy * spacing
            circ = M._safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (base_x + 600, 600 + idx * 40))
            col_geom = None
            if circ:
                try:
                    circ.inputs["Resolution"].default_value = 8
                    circ.inputs["Radius"].default_value = col_r
                except Exception:
                    pass
                fill = M._safe_node(tree, "GeometryNodeFillCurve", (base_x + 750, 600 + idx * 40))
                if fill:
                    try:
                        fill.mode = "NGONS"
                    except Exception:
                        pass
                    M._link(tree, circ.outputs["Curve"], fill.inputs["Curve"])
                    ext = M._safe_node(tree, "GeometryNodeExtrudeMesh", (base_x + 900, 600 + idx * 40))
                    if ext:
                        ext.mode = "FACES"
                        try:
                            ext.inputs["Offset Scale"].default_value = H
                        except Exception:
                            pass
                        M._link(tree, fill.outputs["Mesh"], ext.inputs["Mesh"])
                        tr = M._safe_node(tree, "GeometryNodeTransform", (base_x + 1100, 600 + idx * 40))
                        if tr:
                            try:
                                tr.inputs["Translation"].default_value = (cx, cy, 0)
                            except Exception:
                                pass
                            M._link(tree, ext.outputs["Mesh"], tr.inputs["Geometry"])
                            M.color_node(tr, "pillar")
                            col_geom = tr.outputs["Geometry"]
            if col_geom is None:
                col_geom = M._gb_box(
                    tree, (col_r * 1.6, col_r * 1.6, H),
                    (cx, cy, H * 0.5), base_x + 600, 600 + idx * 40, "pillar",
                )
            if col_geom:
                parts.append(col_geom)
            idx += 1
    return M._gb_join(tree, parts, base_x + 1600, 0)


def attach_to_monolith(monolith):
    bind(monolith)
    _patch("build_greybox_pillar_hall", build_greybox_pillar_hall)
