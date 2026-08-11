"""Native PCG implementation of the Relativity Room and Penrose Loop Escher
room generators, translated from deploy/surreal_architecture_gen.py's Blender
GeometryNodes builders (build_gb_escher_relativity, build_gb_escher_penrose_loop).

The Blender addon builds these as real geometry-node trees; this script
reproduces the same transform math as a PCGCreatePointsSettings point set
(each "box" from the original algorithm becomes one point with a matching
location/rotation/scale), feeding a StaticMeshSpawner using a unit cube mesh
non-uniformly scaled per point -- the same CreatePoints+StaticMeshSpawner
pattern proven throughout this session's Escher/Bezier graph fixes, just with
real computed geometry instead of a handful of hand-placed points.

Run inside the editor (Monolith run_python or py console):
  import build_escher_relativity_room as berr
  berr.build_relativity_room()
  berr.build_penrose_loop()
"""
from __future__ import annotations

import math

DEST_FOLDER = "/Game/EnvSandbox/PCG/Styles/Escher"
CUBE_MESH = "/Engine/BasicShapes/Cube.Cube"  # unit 100x100x100 cube; UE cm units


def _make_point(unreal, loc_m, rot_rad, scale_m, density=1.0):
    """loc_m/scale_m in meters (matching the source algorithm's units) ->
    UE point in cm. scale_m is box dimensions in meters -> divided by 1.0m
    (100cm) cube to get the UE non-uniform Scale3D."""
    p = unreal.PCGPoint()
    loc_cm = unreal.Vector(loc_m[0] * 100.0, loc_m[1] * 100.0, loc_m[2] * 100.0)
    rot = unreal.Rotator(math.degrees(rot_rad[1]), math.degrees(rot_rad[2]), math.degrees(rot_rad[0]))
    scale = unreal.Vector(max(scale_m[0], 0.02), max(scale_m[1], 0.02), max(scale_m[2], 0.02))
    t = unreal.Transform(location=loc_cm, rotation=rot, scale=scale)
    p.set_editor_property("transform", t)
    p.set_editor_property("density", density)
    return p


def _relativity_room_points(unreal, S=10.0, t=0.3, n=8):
    """Direct translation of build_gb_escher_relativity's box list into
    (location_m, rotation_rad(x,y,z), scale_m) tuples."""
    H = S
    rise = H * 0.6 / max(1, n)
    run = S * 0.5 / max(1, n)
    boxes = []  # (loc, rot, scale)

    # Outer chamber shell
    boxes.append(((0, 0, t * 0.5), (0, 0, 0), (S, S, t)))                # floor
    boxes.append(((0, 0, H + t * 0.5), (0, 0, 0), (S, S, t)))            # ceiling
    boxes.append(((0, S * 0.5, H * 0.5), (0, 0, 0), (S, t, H)))          # N wall
    boxes.append(((0, -S * 0.5, H * 0.5), (0, 0, 0), (S, t, H)))         # S wall
    boxes.append(((S * 0.5, 0, H * 0.5), (0, 0, 0), (t, S, H)))          # E wall
    boxes.append(((-S * 0.5, 0, H * 0.5), (0, 0, 0), (t, S, H)))         # W wall

    # Central hub
    hub_s = S * 0.25
    boxes.append(((0, 0, H * 0.5), (0, 0, 0), (hub_s, hub_s, t * 2)))

    stair_w = S * 0.28
    # Staircase A: normal gravity, floor, +Y
    ox_a, oy_a = -S * 0.2, -S * 0.3
    for i in range(n):
        sz_top = t + (i + 1) * rise
        sy_c = oy_a + i * run + run * 0.5
        boxes.append(((ox_a, sy_c, sz_top * 0.5), (0, 0, 0), (stair_w, run, sz_top)))

    # Staircase B: E-wall gravity, rotated 90 deg around Y
    for i in range(n):
        step_depth = t + (i + 1) * rise
        sy_b = S * 0.1 + i * run + run * 0.5
        boxes.append((
            (S * 0.5 - step_depth * 0.5, sy_b, H * 0.55 - i * rise),
            (0, math.radians(90), 0),
            (step_depth, stair_w, run),
        ))

    # Staircase C: ceiling gravity, rotated 180 deg around X
    for i in range(n):
        sz_hang = t + (i + 1) * rise
        sy_c2 = S * 0.3 - i * run - run * 0.5
        boxes.append((
            (S * 0.15, sy_c2, H - sz_hang * 0.5),
            (math.pi, 0, 0),
            (stair_w, run, sz_hang),
        ))

    return boxes


def build_relativity_room(name="PCG_EscherRelativityRoom", S=10.0, t=0.3, n=8, force=True):
    """Builds a self-contained PCG graph: PCGCreatePointsSettings (computed
    Relativity Room geometry) -> PCGStaticMeshSpawnerSettings (cube mesh,
    per-point non-uniform scale). Live-generate on a plain PCGVolume to
    verify -- matches this session's established verification standard."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _relativity_room_points(unreal, S=S, t=t, n=n)
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes, saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def _penrose_loop_points(unreal, side=8.0, W_cor=2.5, n=10, rise=0.22, t=0.28,
                          tower_h=6.0, outer_wall_h=1.4):
    """Direct translation of build_gb_escher_penrose_loop's box list."""
    run = (side - W_cor * 2) / n
    boxes = []

    # Rooftop base slab
    boxes.append(((0, 0, t * 0.5), (0, 0, 0), (side, side, t)))

    arm_configs = [
        (0, side * 0.5 - W_cor * 0.5, run, 0, side * 0.5, side * 0.5, 0),
        (side * 0.5 - W_cor * 0.5, 0, 0, -run, side * 0.5, -side * 0.5, math.pi * 0.5),
        (0, -side * 0.5 + W_cor * 0.5, -run, 0, -side * 0.5, -side * 0.5, math.pi),
        (-side * 0.5 + W_cor * 0.5, 0, 0, run, -side * 0.5, side * 0.5, math.pi * 1.5),
    ]
    for ai, (cx, cy, sdx, sdy, crn_x, crn_y, rot_z) in enumerate(arm_configs):
        base_z = ai * n * rise
        for si in range(n):
            step_z_top = base_z + (si + 1) * rise
            if abs(sdx) > 0:
                bw, bd = run, W_cor
                bx_c = cx + sdx * (si + 0.5)
                by_c = cy
            else:
                bw, bd = W_cor, run
                bx_c = cx
                by_c = cy + sdy * (si + 0.5)
            boxes.append(((bx_c, by_c, step_z_top * 0.5), (0, 0, 0), (bw, bd, step_z_top)))

        corner_z = base_z + n * rise + rise
        boxes.append((
            (crn_x - math.copysign(W_cor * 0.5, crn_x), crn_y - math.copysign(W_cor * 0.5, crn_y), corner_z * 0.5),
            (0, 0, 0),
            (W_cor, W_cor, corner_z),
        ))

    total_z = 4 * n * rise
    for (pw, pd, px, py) in [
        (side, t, 0, side * 0.5), (side, t, 0, -side * 0.5),
        (t, side, side * 0.5, 0), (t, side, -side * 0.5, 0),
    ]:
        boxes.append(((px, py, total_z + outer_wall_h * 0.5), (0, 0, 0), (pw, pd, outer_wall_h)))

    for (tw, td, tx, ty) in [
        (side, t, 0, side * 0.5), (side, t, 0, -side * 0.5),
        (t, side, side * 0.5, 0), (t, side, -side * 0.5, 0),
    ]:
        boxes.append(((tx, ty, -tower_h * 0.5), (0, 0, 0), (tw, td, tower_h)))

    return boxes


def build_penrose_loop(name="PCG_EscherPenroseLoop", side=8.0, force=True):
    """Ascending-and-Descending-style impossible staircase loop -- a square
    rooftop ring of 4 staircase arms that paradoxically returns to its own
    starting height. Same CreatePoints+StaticMeshSpawner pattern as
    build_relativity_room()."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _penrose_loop_points(unreal, side=side)
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes, saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def _recursive_room_points(unreal, W0=12.0, H=3.5, t=0.3, dw=1.4, depth=3, twist_deg=15, scale=0.62):
    """Direct translation of build_gb_escher_recursive_room's box list --
    concentric square rooms of decreasing scale, each rotated, connected by
    doorway passages. Based on Escher's 'Smaller and Smaller' / 'Print
    Gallery'. Real recursion (self-similar detail at multiple scales), not
    just repeated modules -- this is the actual "massive scale" lever."""
    twist = math.radians(twist_deg)
    boxes = []

    for di in range(depth):
        W = W0 * (scale ** di)
        rot = twist * di
        wh = H - t
        wz = t + wh * 0.5
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        Wn = W0 * (scale ** (di + 1)) if di + 1 < depth else W * 0.1
        margin = (W - Wn) * 0.5

        for (sw, sd, sx, sy) in [
            (W, margin, 0, (W - margin) * 0.5),
            (W, margin, 0, -(W - margin) * 0.5),
            (margin, Wn, (W - margin) * 0.5, 0),
            (margin, Wn, -(W - margin) * 0.5, 0),
        ]:
            rx = sx * cos_r - sy * sin_r
            ry = sx * sin_r + sy * cos_r
            boxes.append(((rx, ry, t * 0.5), (0, 0, rot), (sw, sd, t)))

        for (bw, bd, bx2, by2, is_door) in [
            (W, t, 0, W * 0.5 - t * 0.5, True),
            (W, t, 0, -W * 0.5 + t * 0.5, False),
            (t, W, W * 0.5 - t * 0.5, 0, False),
            (t, W, -W * 0.5 + t * 0.5, 0, False),
        ]:
            if is_door:
                seg_len = (bw - dw) * 0.5
                for sx2 in (-1, 1):
                    cx2 = sx2 * (seg_len * 0.5 + dw * 0.5)
                    rx2 = cx2 * cos_r - by2 * sin_r
                    ry2 = cx2 * sin_r + by2 * cos_r
                    boxes.append(((rx2, ry2, wz), (0, 0, rot), (seg_len, bd, wh)))
            else:
                rx = bx2 * cos_r - by2 * sin_r
                ry = bx2 * sin_r + by2 * cos_r
                boxes.append(((rx, ry, wz), (0, 0, rot), (bw, bd, wh)))

    W_inner = W0 * (scale ** depth)
    boxes.append(((0, 0, H * 0.4), (0, 0, 0), (W_inner, W_inner, H * 0.8)))

    return boxes


def build_recursive_room(name="PCG_EscherRecursiveRoom", W0=12.0, depth=3, force=True):
    """Concentric, rotated, self-similar rooms with doorway passages between
    scales -- 'Smaller and Smaller' / 'Print Gallery'. Same CreatePoints+
    StaticMeshSpawner pattern as the other two builders."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _recursive_room_points(unreal, W0=W0, depth=depth)
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes ({depth} recursive levels), saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def _gravity_shift_corridor_points(unreal, L=12.0, W=3.0, H=3.0, t=0.25, n_segs=5):
    """Direct translation of build_gb_escher_gravity_shift's box list -- a
    corridor that progressively rotates 90 deg around its own travel axis
    over n_segs sections; floor becomes wall by the exit."""
    seg_l = L / n_segs
    boxes = []

    for si in range(n_segs):
        ang = si * (math.pi / 2) / (n_segs - 1)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        y_ctr = -L * 0.5 + seg_l * (si + 0.5)

        for (role, lx, lz, bw, bh) in [
            ("floor", 0, -H * 0.5, W, t),
            ("ceiling", 0, H * 0.5, W, t),
            ("left", -W * 0.5, 0, t, H),
            ("right", W * 0.5, 0, t, H),
        ]:
            rx = lx * cos_a - lz * sin_a
            rz = lx * sin_a + lz * cos_a + H * 0.5

            if abs(ang - math.pi / 4) < 0.1 or abs(ang - math.pi * 3 / 4) < 0.1:
                box_sz = (max(bw, bh), seg_l, max(bw, bh))
            else:
                box_sz = (bw, seg_l, bh)

            boxes.append(((rx, y_ctr, rz), (0, ang, 0), box_sz))

    boxes.append(((0, -L * 0.5 + seg_l * 0.25, t * 1.05), (0, 0, 0), (W * 0.3, seg_l * 0.4, t * 0.5)))
    return boxes


def build_gravity_shift_corridor(name="PCG_EscherGravityShiftCorridor", L=12.0, force=True):
    """A corridor that progressively rotates 90 deg around its travel axis --
    you enter with the floor underfoot, exit with the original floor as the
    left wall. Same CreatePoints+StaticMeshSpawner pattern."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _gravity_shift_corridor_points(unreal, L=L)
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes, saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def _belvedere_points(W=6.0, D=6.0, H1=3.5, t=0.35):
    """Direct translation of build_gb_escher_belvedere -- a 2-story loggia
    where the upper floor's columns connect to the WRONG (opposite) corners
    of the lower floor, with impossible X-crossing beams at mid-level.
    Escher's 'Belvedere' (1958)."""
    H2 = H1
    col_s = t * 1.5
    boxes = []

    boxes.append(((0, 0, t * 0.5), (0, 0, 0), (W, D, t)))
    boxes.append(((0, 0, H1 + t * 0.5), (0, 0, 0), (W, D, t)))
    boxes.append(((0, 0, H1 + H2 + t * 0.5), (0, 0, 0), (W, D, t)))

    corners = [(-W * 0.5 + col_s * 0.5, -D * 0.5 + col_s * 0.5),
               (W * 0.5 - col_s * 0.5, -D * 0.5 + col_s * 0.5),
               (W * 0.5 - col_s * 0.5, D * 0.5 - col_s * 0.5),
               (-W * 0.5 + col_s * 0.5, D * 0.5 - col_s * 0.5)]
    for (cx, cy) in corners:
        boxes.append(((cx, cy, H1 * 0.5 + t), (0, 0, 0), (col_s, col_s, H1)))

    opp_corners = [corners[2], corners[3], corners[0], corners[1]]
    for (bx_lo, by_lo), (bx_hi, by_hi) in zip(corners, opp_corners):
        mx, my = (bx_lo + bx_hi) * 0.5, (by_lo + by_hi) * 0.5
        mz = H1 + H2 * 0.5 + t
        dx, dy = bx_hi - bx_lo, by_hi - by_lo
        horiz_len = math.sqrt(dx * dx + dy * dy)
        col_len = math.sqrt(horiz_len ** 2 + H2 ** 2)
        tilt_x = math.atan2(H2, horiz_len)
        yaw = math.atan2(dy, dx) if horiz_len > 0.001 else 0
        boxes.append(((mx, my, mz), (tilt_x, 0, yaw), (col_s, col_s, col_len)))

    beam_h = t * 1.8
    for ang in [0, math.pi * 0.5]:
        beam_len = math.sqrt(W ** 2 + D ** 2) * 0.9
        boxes.append(((0, 0, H1 + H2 * 0.5), (0, 0, ang), (beam_len, col_s, beam_h)))

    for (bw, bd, bx2, by2) in [
        (W, t, 0, D * 0.5 - t * 0.5),
        (W, t, 0, -D * 0.5 + t * 0.5),
        (t, D, W * 0.5 - t * 0.5, 0),
        (t, D, -W * 0.5 + t * 0.5, 0),
    ]:
        boxes.append(((bx2, by2, H1 + H2 + t + H2 * 0.15), (0, 0, 0), (bw, bd, H2 * 0.3)))

    return boxes


def build_belvedere(name="PCG_EscherBelvedere", force=True):
    """Escher's 'Belvedere' (1958): a 2-story loggia where the upper columns
    connect to the wrong corners below, with impossible X-crossing beams."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _belvedere_points()
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes, saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def _waterfall_points(span=8.0, W_ch=0.9, rise=0.5, H_col=4.0):
    """Direct translation of build_gb_escher_waterfall -- three elevated
    channel arms 120deg apart, each tilting gently downward, but the loop
    closes back at the top so water appears to flow down and return to its
    source. Escher's 'Waterfall' (1961)."""
    t_ch = 0.25
    boxes = []
    tilt = math.atan2(rise, span)
    ch_len = math.sqrt(span ** 2 + rise ** 2)

    for ai in range(3):
        yaw = ai * math.tau / 3
        cx = math.cos(yaw) * span * 0.5
        cy = math.sin(yaw) * span * 0.5
        cz = H_col + rise * (1 - ai / 3)

        boxes.append(((cx, cy, cz), (tilt, 0, yaw + math.pi * 0.5), (W_ch, ch_len, t_ch)))
        boxes.append(((cx + math.cos(yaw + math.pi * 0.5) * W_ch * 0.5,
                        cy + math.sin(yaw + math.pi * 0.5) * W_ch * 0.5,
                        cz + W_ch * 0.3), (tilt, 0, yaw + math.pi * 0.5), (t_ch, ch_len, W_ch * 0.6)))
        boxes.append(((cx - math.cos(yaw + math.pi * 0.5) * W_ch * 0.5,
                        cy - math.sin(yaw + math.pi * 0.5) * W_ch * 0.5,
                        cz + W_ch * 0.3), (tilt, 0, yaw + math.pi * 0.5), (t_ch, ch_len, W_ch * 0.6)))
        boxes.append(((cx, cy, cz * 0.5), (0, 0, 0), (t_ch * 2.5, t_ch * 2.5, cz)))

    for ai in range(3):
        yaw_a = ai * math.tau / 3
        yaw_b = ((ai + 1) % 3) * math.tau / 3
        jx = math.cos((yaw_a + yaw_b) * 0.5) * span * 0.85
        jy = math.sin((yaw_a + yaw_b) * 0.5) * span * 0.85
        jz = H_col + rise * 0.5 + W_ch * 0.4
        boxes.append(((jx, jy, jz), (0, 0, 0), (W_ch * 1.4, W_ch * 1.4, W_ch * 0.8)))

    boxes.append(((0, 0, t_ch * 0.5), (0, 0, 0), (span * 2.2, span * 2.2, t_ch)))
    return boxes


def build_waterfall(name="PCG_EscherWaterfall", force=True):
    """Escher's 'Waterfall' (1961): three elevated channel arms 120deg apart,
    each tilting down, but the loop closes back at the top."""
    import unreal
    import pcg_graph_builder as gb

    graph, created = gb.load_or_create_graph(f"{DEST_FOLDER}/{name}", DEST_FOLDER, force=force)

    create_node, create_settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
    create_node.set_node_position(-400, 0)

    boxes = _waterfall_points()
    pts = [_make_point(unreal, loc, rot, scale) for (loc, rot, scale) in boxes]
    create_settings.set_editor_property("points_to_create", pts)

    spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    spawn_node.set_node_position(0, 0)

    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(CUBE_MESH))
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    sel = spawn_settings.get_editor_property("mesh_selector_parameters")
    sel.set_editor_property("mesh_entries", [entry])

    graph.add_edge(create_node, "Out", spawn_node, "In")

    unreal.EditorAssetLibrary.save_asset(f"{DEST_FOLDER}/{name}")
    print(f"{name}: built {len(boxes)} boxes, saved")
    return f"{DEST_FOLDER}/{name}", len(boxes)


def build_all():
    r1 = build_relativity_room()
    r2 = build_penrose_loop()
    r3 = build_recursive_room()
    r4 = build_gravity_shift_corridor()
    r5 = build_belvedere()
    r6 = build_waterfall()
    return {"relativity_room": r1, "penrose_loop": r2, "recursive_room": r3, "gravity_shift_corridor": r4,
            "belvedere": r5, "waterfall": r6}


if __name__ == "__main__":
    print(build_all())
