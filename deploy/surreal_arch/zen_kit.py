"""Zen modular kit — roji, torii, tsukubai, engawa, bamboo fence, tobi-ishi, karesansui, machiai, stone bridge, cherry allee, water edge (v2.73)."""

from __future__ import annotations


def build_zen_roji_step(tree, M, props, base_x=-1400):
    """Roji dew-path segment — flat slab + raised edge stones for trim sheets."""
    L = getattr(props, "gb_length", 4.0)
    W = getattr(props, "gb_width", 1.8)
    t = getattr(props, "gb_wall_thick", 0.12)
    edge_h = max(t * 1.8, 0.08)
    parts = []

    slab = M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0)
    if slab:
        parts.append(slab)

    for sx in (-1, 1):
        edge = M._gb_box(
            tree,
            (t * 0.9, L * 0.96, edge_h),
            (sx * (W * 0.5 - t * 0.35), 0, edge_h * 0.5 + t),
            base_x,
            200 + sx * 50,
            "trim:edge_stone",
        )
        if edge:
            parts.append(edge)

    return M._gb_join(tree, parts, base_x + 600, 0)


def build_zen_torii_gate(tree, M, props, base_x=-1400):
    """Modular torii gate greybox — posts, nuki, kasagi lintel; path snaps through opening."""
    W = getattr(props, "torii_width", getattr(props, "gb_width", 3.6))
    H = getattr(props, "torii_height", getattr(props, "gb_height", 4.2))
    pr = getattr(props, "torii_post_radius", max(W * 0.06, 0.14))
    t = getattr(props, "gb_wall_thick", 0.2)
    nuki_z = H * getattr(props, "torii_nuki_height", 0.7)
    parts = []

    for i, sx in enumerate((-1, 1)):
        post = M._gb_box(
            tree,
            (pr * 2.2, pr * 2.2, H),
            (sx * W * 0.5, 0, H * 0.5),
            base_x,
            i * 120,
            "trim:hashira",
        )
        if post:
            parts.append(post)

    nuki = M._gb_box(
        tree,
        (W + pr * 2.5, pr * 1.6, pr * 1.4),
        (0, 0, nuki_z),
        base_x,
        300,
        "trim:nuki",
    )
    if nuki:
        parts.append(nuki)

    kasagi = M._gb_box(
        tree,
        (W + pr * 4.0, pr * 2.0, pr * 1.2),
        (0, 0, H * 0.98),
        base_x,
        450,
        "trim:kasagi",
    )
    if kasagi:
        parts.append(kasagi)

    return M._gb_join(tree, parts, base_x + 800, 0)


def build_zen_sakura_torii(tree, M, props, base_x=-1400):
    """Sakura torii variant — standard torii + blossom band on kasagi + petal accent strips."""
    W = getattr(props, "torii_width", getattr(props, "gb_width", 3.4))
    H = getattr(props, "torii_height", getattr(props, "gb_height", 4.0))
    pr = getattr(props, "torii_post_radius", max(W * 0.06, 0.14))
    t = getattr(props, "gb_wall_thick", 0.2)
    nuki_z = H * getattr(props, "torii_nuki_height", 0.7)
    parts = []

    for i, sx in enumerate((-1, 1)):
        post = M._gb_box(
            tree,
            (pr * 2.2, pr * 2.2, H),
            (sx * W * 0.5, 0, H * 0.5),
            base_x,
            i * 120,
            "trim:hashira",
        )
        if post:
            parts.append(post)
        petal = M._gb_box(
            tree,
            (pr * 1.4, pr * 0.35, H * 0.22),
            (sx * W * 0.5, pr * 0.5, H * 0.62),
            base_x,
            80 + i * 40,
            "trim:petal_accent",
        )
        if petal:
            parts.append(petal)

    nuki = M._gb_box(
        tree,
        (W + pr * 2.5, pr * 1.6, pr * 1.4),
        (0, 0, nuki_z),
        base_x,
        300,
        "trim:nuki",
    )
    if nuki:
        parts.append(nuki)

    kasagi = M._gb_box(
        tree,
        (W + pr * 4.0, pr * 2.0, pr * 1.2),
        (0, 0, H * 0.98),
        base_x,
        450,
        "trim:kasagi",
    )
    if kasagi:
        parts.append(kasagi)

    blossom = M._gb_box(
        tree,
        (W + pr * 3.2, pr * 0.55, pr * 0.9),
        (0, pr * 0.35, H * 0.99),
        base_x,
        520,
        "trim:blossom_band",
    )
    if blossom:
        parts.append(blossom)

    return M._gb_join(tree, parts, base_x + 850, 0)


def build_zen_tsukubai(tree, M, props, base_x=-1400):
    """Tsukubai stone basin pad — recess bowl + surround flagstones."""
    W = getattr(props, "gb_width", 1.6)
    D = getattr(props, "gb_depth", 1.6)
    H = getattr(props, "gb_height", 0.45)
    t = getattr(props, "gb_wall_thick", 0.14)
    recess = M._gb_trim_depth(props, t)
    parts = []

    pad = M._gb_box(tree, (W, D, t), (0, 0, t * 0.5), base_x, 0)
    if pad:
        parts.append(pad)

    bowl_w = W * 0.55
    bowl = M._gb_box(
        tree,
        (bowl_w, bowl_w, max(H - t, t * 2)),
        (0, 0, t + (H - t) * 0.45),
        base_x,
        200,
        "trim:basin",
    )
    if bowl:
        cutter = M._gb_box(
            tree,
            (bowl_w * 0.72, bowl_w * 0.72, (H - t) * 0.9),
            (0, 0, t + (H - t) * 0.5),
            base_x + 300,
            200,
            "void",
        )
        cut = M._gb_bool_diff(tree, bowl, [cutter], base_x + 500, 200) if cutter else bowl
        if cut:
            parts.append(cut)

    for i, (ox, oy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        flag = M._gb_box(
            tree,
            (W * 0.22, D * 0.22, t * 0.65),
            (ox * W * 0.32, oy * D * 0.32, t * 0.35),
            base_x,
            400 + i * 40,
            "trim:flagstone",
        )
        if flag:
            parts.append(flag)

    return M._gb_join(tree, parts, base_x + 900, 0)


def build_zen_engawa(tree, M, props, base_x=-1400):
    """Engawa veranda — raised deck slab, post row, low railing beam along open edge."""
    W = getattr(props, "gb_width", 5.0)
    D = getattr(props, "gb_depth", 2.4)
    H = getattr(props, "gb_height", 0.35)
    t = getattr(props, "gb_wall_thick", 0.12)
    post_h = max(H * 1.6, 0.55)
    parts = []

    deck = M._gb_box(tree, (W, D, t), (0, 0, t * 0.5), base_x, 0, "trim:deck")
    if deck:
        parts.append(deck)

    n_posts = max(3, int(W / 1.4) + 1)
    for i in range(n_posts):
        u = i / max(n_posts - 1, 1)
        px = -W * 0.5 + u * W
        post = M._gb_box(
            tree,
            (t * 1.1, t * 1.1, post_h),
            (px, D * 0.5 - t * 0.6, post_h * 0.5 + t),
            base_x,
            100 + i * 30,
            "trim:post",
        )
        if post:
            parts.append(post)

    rail = M._gb_box(
        tree,
        (W * 0.98, t * 0.85, t * 0.75),
        (0, D * 0.5 - t * 0.35, post_h * 0.82 + t),
        base_x,
        500,
        "trim:rail",
    )
    if rail:
        parts.append(rail)

    return M._gb_join(tree, parts, base_x + 1000, 0)


def build_zen_bamboo_fence(tree, M, props, base_x=-1400):
    """Bamboo fence segment — posts + horizontal rails; tileable along path axis."""
    L = getattr(props, "gb_length", 4.0)
    H = getattr(props, "zen_fence_height", getattr(props, "gb_height", 1.2))
    t = getattr(props, "gb_wall_thick", 0.06)
    post_r = max(t * 1.4, 0.05)
    parts = []

    n_posts = max(2, int(L / 1.1) + 1)
    for i in range(n_posts):
        u = i / max(n_posts - 1, 1)
        py = -L * 0.5 + u * L
        post = M._gb_box(
            tree,
            (post_r * 2, post_r * 2, H),
            (0, py, H * 0.5),
            base_x,
            i * 40,
            "trim:bamboo_post",
        )
        if post:
            parts.append(post)

    for ri, zf in enumerate((0.25, 0.55, 0.82)):
        rail = M._gb_box(
            tree,
            (t * 2.2, L * 0.96, t * 0.9),
            (0, 0, H * zf),
            base_x,
            300 + ri * 50,
            "trim:bamboo_rail",
        )
        if rail:
            parts.append(rail)

    return M._gb_join(tree, parts, base_x + 1100, 0)


def build_zen_tobiishi(tree, M, props, base_x=-1400):
    """Tobi-ishi stepping stones — scattered flat stones along a path strip."""
    L = getattr(props, "gb_length", 5.0)
    W = getattr(props, "gb_width", 1.6)
    t = getattr(props, "gb_wall_thick", 0.1)
    stone_w = max(W * 0.28, 0.35)
    parts = []

    bed = M._gb_box(tree, (W, L, t * 0.35), (0, 0, t * 0.18), base_x, 0)
    if bed:
        parts.append(bed)

    offsets = [
        (-0.22, -0.38), (0.18, -0.12), (-0.08, 0.14), (0.24, 0.32),
        (-0.26, 0.42), (0.06, -0.28), (0.0, 0.0),
    ]
    n_stones = max(4, min(7, int(L / 0.9) + 2))
    for i in range(n_stones):
        ox, oy = offsets[i % len(offsets)]
        py = -L * 0.42 + (i / max(n_stones - 1, 1)) * L * 0.84
        stone = M._gb_box(
            tree,
            (stone_w, stone_w * 0.85, t * 0.55),
            (ox * W, py + oy * 0.25, t * 0.45),
            base_x,
            200 + i * 35,
            "trim:stepping_stone",
        )
        if stone:
            parts.append(stone)

    return M._gb_join(tree, parts, base_x + 1200, 0)


def build_zen_karesansui(tree, M, props, base_x=-1400):
    """Dry rock garden — raked gravel plane, ishigumi border, parallel rake grooves."""
    W = getattr(props, "gb_width", 8.0)
    D = getattr(props, "gb_depth", 6.0)
    t = getattr(props, "gb_wall_thick", 0.12)
    groove_d = max(t * 0.35, 0.04)
    parts = []

    sand = M._gb_box(tree, (W, D, t), (0, 0, t * 0.5), base_x, 0, "trim:sand_bed")
    if sand:
        parts.append(sand)

    for sx in (-1, 1):
        border = M._gb_box(
            tree,
            (t * 1.4, D * 0.96, t * 1.6),
            (sx * (W * 0.5 - t * 0.5), 0, t * 0.85),
            base_x,
            100 + sx,
            "trim:border_stone",
        )
        if border:
            parts.append(border)
    for sy in (-1, 1):
        border = M._gb_box(
            tree,
            (W * 0.96, t * 1.4, t * 1.6),
            (0, sy * (D * 0.5 - t * 0.5), t * 0.85),
            base_x,
            120 + sy,
            "trim:border_stone",
        )
        if border:
            parts.append(border)

    n_grooves = max(4, int(D / 1.1))
    for i in range(n_grooves):
        py = -D * 0.42 + (i / max(n_grooves - 1, 1)) * D * 0.84
        groove = M._gb_box(
            tree,
            (W * 0.75, groove_d, t * 0.25),
            (0, py, t * 0.72),
            base_x,
            300 + i * 25,
            "trim:rake_groove",
        )
        if groove:
            parts.append(groove)

    return M._gb_join(tree, parts, base_x + 1300, 0)


def build_zen_machiai(tree, M, props, base_x=-1400):
    """Machiai waiting pavilion — open posts, shallow roof beam, bench slab."""
    W = getattr(props, "gb_width", 3.2)
    D = getattr(props, "gb_depth", 2.4)
    H = getattr(props, "gb_height", 2.2)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    floor = M._gb_box(tree, (W, D, t), (0, 0, t * 0.5), base_x, 0, "trim:bench")
    if floor:
        parts.append(floor)

    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        col = M._gb_box(
            tree,
            (t * 1.1, t * 1.1, H * 0.85),
            (sx * (W * 0.5 - t * 0.55), sy * (D * 0.5 - t * 0.55), H * 0.43 + t),
            base_x,
            100 + i * 35,
            "trim:post",
        )
        if col:
            parts.append(col)

    roof = M._gb_box(
        tree,
        (W * 1.05, D * 1.05, t * 1.3),
        (0, 0, H - t * 0.4),
        base_x,
        300,
        "trim:roof",
    )
    if roof:
        parts.append(roof)

    bench = M._gb_box(
        tree,
        (W * 0.55, t * 1.2, t * 0.9),
        (0, -D * 0.15, t * 0.95),
        base_x,
        400,
        "trim:bench",
    )
    if bench:
        parts.append(bench)

    return M._gb_join(tree, parts, base_x + 1100, 0)


def build_zen_stone_bridge(tree, M, props, base_x=-1400):
    """Garden stone bridge — deck slab, low rails, bank abutments."""
    span = getattr(props, "zen_bridge_span", 5.0)
    rise = getattr(props, "zen_bridge_rise", 0.55)
    W = getattr(props, "gb_width", 1.8)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    deck = M._gb_box(
        tree,
        (W, span * 0.92, t),
        (0, 0, rise + t * 0.5),
        base_x,
        0,
        "trim:deck",
    )
    if deck:
        parts.append(deck)

    for sx in (-1, 1):
        rail = M._gb_box(
            tree,
            (t * 0.9, span * 0.88, t * 1.1),
            (sx * (W * 0.5 - t * 0.35), 0, rise + t * 1.1),
            base_x,
            100 + sx * 50,
            "trim:rail",
        )
        if rail:
            parts.append(rail)

    for sy in (-1, 1):
        abut = M._gb_box(
            tree,
            (W * 1.15, t * 1.6, rise * 0.85),
            (0, sy * (span * 0.5 - t * 0.4), rise * 0.42),
            base_x,
            200 + sy * 50,
            "trim:abutment",
        )
        if abut:
            parts.append(abut)

    return M._gb_join(tree, parts, base_x + 1200, 0)


def build_zen_cherry_allee(tree, M, props, base_x=-1400):
    """Sakura path segment — walk slab, trunk bases, blossom canopy, petal scatter."""
    L = getattr(props, "gb_length", 6.0)
    W = getattr(props, "gb_width", 2.6)
    H = getattr(props, "gb_height", 0.32)
    t = getattr(props, "gb_wall_thick", 0.1)
    parts = []

    walk = M._gb_box(tree, (W * 0.55, L, t), (0, 0, t * 0.5), base_x, 0, "trim:path_slab")
    if walk:
        parts.append(walk)

    n_trunks = max(3, int(L / 2.2))
    for i in range(n_trunks):
        for sx in (-1, 1):
            py = -L * 0.42 + (i / max(n_trunks - 1, 1)) * L * 0.84
            trunk = M._gb_box(
                tree,
                (t * 2.2, t * 2.2, H * 2.8),
                (sx * (W * 0.42), py, H * 1.5),
                base_x,
                80 + i * 20 + sx,
                "trim:trunk_base",
            )
            if trunk:
                parts.append(trunk)
            canopy = M._gb_box(
                tree,
                (W * 0.28, W * 0.28, t * 1.4),
                (sx * (W * 0.42), py, H * 2.9),
                base_x,
                120 + i * 20 + sx,
                "trim:blossom_canopy",
            )
            if canopy:
                parts.append(canopy)

    petal = M._gb_box(
        tree,
        (W * 0.5, L * 0.35, t * 0.45),
        (W * 0.12, L * 0.22, t * 0.75),
        base_x,
        500,
        "trim:petal_scatter",
    )
    if petal:
        parts.append(petal)

    return M._gb_join(tree, parts, base_x + 1300, 0)


def build_zen_water_edge(tree, M, props, base_x=-1400):
    """Stream bank strip — channel bed, raised banks, stepping stones at bridge landings."""
    L = getattr(props, "gb_length", 2.8)
    W = getattr(props, "gb_width", 2.4)
    depth = getattr(props, "zen_stream_depth", 0.35)
    t = getattr(props, "gb_wall_thick", 0.14)
    t_bank = t * 1.2
    parts = []

    bed = M._gb_box(
        tree,
        (W * 0.55, L, depth),
        (0, 0, -depth * 0.35),
        base_x,
        0,
        "trim:stream_bed",
    )
    if bed:
        parts.append(bed)

    for sx in (-1, 1):
        bank = M._gb_box(
            tree,
            (t_bank, L * 0.98, t_bank * 1.8),
            (sx * (W * 0.5 - t_bank * 0.4), 0, t_bank * 0.55),
            base_x,
            100 + sx * 50,
            "trim:stream_bank",
        )
        if bank:
            parts.append(bank)

    for sy in (-1, 1):
        step = M._gb_box(
            tree,
            (W * 0.22, W * 0.22, t * 0.7),
            (0, sy * (L * 0.5 - 0.15), t_bank * 0.35),
            base_x,
            250 + sy * 40,
            "trim:stepping_stone",
        )
        if step:
            parts.append(step)

    return M._gb_join(tree, parts, base_x + 1100, 0)


def build_zen_sando(tree, M, props, base_x=-1400):
    """Shrine approach — paving slab, border stones, stone lantern rhythm."""
    L = getattr(props, "gb_length", 8.0)
    W = getattr(props, "gb_width", 2.2)
    t = getattr(props, "gb_wall_thick", 0.12)
    parts = []

    paving = M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0, "trim:paving")
    if paving:
        parts.append(paving)

    for sx in (-1, 1):
        edge = M._gb_box(
            tree,
            (t * 1.1, L * 0.96, t * 1.5),
            (sx * (W * 0.5 - t * 0.4), 0, t * 0.85),
            base_x,
            100 + sx * 50,
            "trim:edge_stone",
        )
        if edge:
            parts.append(edge)

    n_toro = max(1, int(L / 6.0))
    for i in range(n_toro):
        py = -L * 0.42 + (i / max(n_toro - 1, 1)) * L * 0.84 if n_toro > 1 else 0
        post = M._gb_box(
            tree,
            (t * 1.4, t * 1.4, t * 5.5),
            (W * 0.38, py, t * 3.2),
            base_x,
            200 + i * 40,
            "trim:toro_post",
        )
        base = M._gb_box(
            tree,
            (t * 2.2, t * 2.2, t * 0.9),
            (W * 0.38, py, t * 0.95),
            base_x,
            210 + i * 40,
            "trim:toro_base",
        )
        if post:
            parts.append(post)
        if base:
            parts.append(base)

    return M._gb_join(tree, parts, base_x + 1300, 0)


def build_zen_kairo(tree, M, props, base_x=-1400):
    """Covered cloister — walkway, column row, tie beam, eave, garden wall."""
    L = getattr(props, "gb_length", 6.0)
    W = getattr(props, "gb_width", 2.4)
    H = getattr(props, "gb_height", 2.8)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    floor = M._gb_box(tree, (W, L, t), (0, 0, t * 0.5), base_x, 0, "trim:floor")
    if floor:
        parts.append(floor)

    n_cols = max(3, int(L / 1.82) + 1)
    for i in range(n_cols):
        py = -L * 0.45 + (i / max(n_cols - 1, 1)) * L * 0.9
        col = M._gb_box(
            tree,
            (t * 1.2, t * 1.2, H * 0.78),
            (W * 0.5 - t * 0.7, py, H * 0.4 + t),
            base_x,
            100 + i * 35,
            "trim:column",
        )
        if col:
            parts.append(col)

    beam = M._gb_box(
        tree,
        (t * 1.1, L * 0.92, t * 0.85),
        (W * 0.5 - t * 0.5, 0, H * 0.72),
        base_x,
        400,
        "trim:beam",
    )
    if beam:
        parts.append(beam)

    eave = M._gb_box(
        tree,
        (W * 1.05, L * 0.98, t * 1.4),
        (0, 0, H - t * 0.5),
        base_x,
        500,
        "trim:noki_eave",
    )
    if eave:
        parts.append(eave)

    wall = M._gb_box(
        tree,
        (t, L * 0.95, H * 0.55),
        (-W * 0.5 + t * 0.5, 0, H * 0.32),
        base_x,
        600,
        "trim:wall_panel",
    )
    if wall:
        parts.append(wall)

    return M._gb_join(tree, parts, base_x + 1400, 0)


def build_zen_haiden(tree, M, props, base_x=-1400):
    """Worship hall (haiden) — genkan steps, raised haijo floor, posts, ranma, noki eave."""
    W = getattr(props, "gb_width", 5.0)
    D = getattr(props, "gb_depth", 4.0)
    H = getattr(props, "gb_height", 3.2)
    step_rise = getattr(props, "zen_genkan_rise", 0.45)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    for i in range(3):
        step_w = W * (0.52 + i * 0.14)
        step_h = step_rise / 3.0
        step_y = -D * 0.5 + t * 0.9 + i * (t * 0.55)
        step_z = step_h * 0.5 + i * step_h
        step = M._gb_box(
            tree,
            (step_w, t * 1.6, step_h),
            (0, step_y, step_z),
            base_x,
            i * 25,
            "trim:genkan_step",
        )
        if step:
            parts.append(step)

    floor_z = step_rise + t * 0.5
    floor = M._gb_box(tree, (W, D, t), (0, 0, floor_z), base_x, 120, "trim:haijo_floor")
    if floor:
        parts.append(floor)

    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1))):
        px = sx * (W * 0.5 - t * 0.55) if sx else 0
        py = sy * (D * 0.5 - t * 0.55) if sy else (-D * 0.5 + t * 0.8 if sy == -1 else D * 0.5 - t * 0.8)
        col = M._gb_box(
            tree,
            (t * 1.15, t * 1.15, H * 0.72),
            (px, py, floor_z + H * 0.38),
            base_x,
            200 + i * 30,
            "trim:post",
        )
        if col:
            parts.append(col)

    ranma = M._gb_box(
        tree,
        (W * 0.72, t * 0.9, H * 0.22),
        (0, -D * 0.5 + t * 1.1, floor_z + H * 0.58),
        base_x,
        450,
        "trim:ranma",
    )
    if ranma:
        parts.append(ranma)

    noki = M._gb_box(
        tree,
        (W * 1.12, D * 1.08, t * 1.5),
        (0, 0, floor_z + H - t * 0.35),
        base_x,
        500,
        "trim:noki",
    )
    if noki:
        parts.append(noki)

    return M._gb_join(tree, parts, base_x + 1500, 0)


def build_zen_goju_pagoda(tree, M, props, base_x=-1400):
    """Five-story pagoda greybox (goju-no-tō) — tapered tier cores, roof slabs, sorin finial."""
    tiers = max(2, min(7, getattr(props, "pagoda_tiers", 5)))
    R = getattr(props, "pagoda_base_radius", 2.0)
    th = getattr(props, "pagoda_tier_height", 1.2)
    taper = getattr(props, "pagoda_taper", 0.82)
    overhang = getattr(props, "pagoda_roof_overhang", 0.4)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    plinth = M._gb_box(tree, (R * 2.2, R * 2.2, t * 1.6), (0, 0, t * 0.8), base_x, 0, "trim:plinth")
    if plinth:
        parts.append(plinth)

    z = t * 1.6
    r = R
    for i in range(tiers):
        core = M._gb_box(
            tree,
            (r * 1.55, r * 1.55, th * 0.62),
            (0, 0, z + th * 0.31),
            base_x,
            100 + i * 70,
            "trim:tier_core",
        )
        if core:
            parts.append(core)
        roof = M._gb_box(
            tree,
            ((r + overhang) * 2.05, (r + overhang) * 2.05, th * 0.38),
            (0, 0, z + th * 0.62 + th * 0.19),
            base_x,
            140 + i * 70,
            "trim:tier_roof",
        )
        if roof:
            parts.append(roof)
        z += th
        r *= taper

    sorin = M._gb_box(tree, (t * 0.9, t * 0.9, th * 0.55), (0, 0, z + th * 0.28), base_x, 900, "trim:sorin")
    if sorin:
        parts.append(sorin)

    return M._gb_join(tree, parts, base_x + 1600, 0)


def build_zen_tahoto(tree, M, props, base_x=-1400):
    """Tahōtō treasure pagoda — square mokoshi base, drum body, double roof, sorin."""
    W = getattr(props, "gb_width", 3.2)
    H = getattr(props, "gb_height", 6.5)
    span = getattr(props, "zen_tahoto_roof_span", 0.35)
    t = getattr(props, "gb_wall_thick", 0.14)
    parts = []

    plinth = M._gb_box(tree, (W * 1.15, W * 1.15, t * 1.5), (0, 0, t * 0.75), base_x, 0, "trim:plinth")
    if plinth:
        parts.append(plinth)

    z = t * 1.5
    mokoshi_h = H * 0.18
    mokoshi = M._gb_box(tree, (W, W, mokoshi_h), (0, 0, z + mokoshi_h * 0.5), base_x, 100, "trim:mokoshi_base")
    if mokoshi:
        parts.append(mokoshi)
    z += mokoshi_h

    drum_h = H * 0.42
    drum_w = W * 0.78
    drum = M._gb_box(tree, (drum_w, drum_w, drum_h), (0, 0, z + drum_h * 0.5), base_x, 200, "trim:drum_body")
    if drum:
        parts.append(drum)
    z += drum_h

    lower_roof = M._gb_box(
        tree,
        (W * (1.0 + span), W * (1.0 + span), H * 0.08),
        (0, 0, z + H * 0.04),
        base_x,
        300,
        "trim:roof_lower",
    )
    if lower_roof:
        parts.append(lower_roof)
    z += H * 0.08

    upper_core = M._gb_box(tree, (drum_w * 0.55, drum_w * 0.55, H * 0.12), (0, 0, z + H * 0.06), base_x, 400, "trim:drum_body")
    if upper_core:
        parts.append(upper_core)
    z += H * 0.12

    upper_roof = M._gb_box(
        tree,
        (W * (0.95 + span * 0.8), W * (0.95 + span * 0.8), H * 0.1),
        (0, 0, z + H * 0.05),
        base_x,
        500,
        "trim:roof_upper",
    )
    if upper_roof:
        parts.append(upper_roof)
    z += H * 0.1

    sorin = M._gb_box(tree, (t * 0.85, t * 0.85, H * 0.08), (0, 0, z + H * 0.04), base_x, 600, "trim:sorin")
    if sorin:
        parts.append(sorin)

    return M._gb_join(tree, parts, base_x + 1700, 0)


def build_zen_lantern(tree, M, props, base_x=-1400):
    """Greybox ishi-dōrō (石灯籠) — kiso, sao, hibukuro, kasa, hōju stack."""
    H = getattr(props, "zen_lantern_height", 1.6)
    R = getattr(props, "zen_lantern_radius", 0.32)
    style = getattr(props, "zen_lantern_style", "KASUGA")
    kasa_mul = {"KASUGA": 1.0, "YUKIMI": 1.35, "ORIBE": 0.9, "MISAKI": 1.5}.get(style, 1.0)
    parts = []
    z = 0.0

    kiso_h = H * 0.12
    kiso = M._gb_box(tree, (R * 2.2, R * 2.2, kiso_h), (0, 0, z + kiso_h * 0.5), base_x, 0, "trim:kiso")
    if kiso:
        parts.append(kiso)
    z += kiso_h

    sao_h = H * 0.38
    sao = M._gb_box(tree, (R * 0.55, R * 0.55, sao_h), (0, 0, z + sao_h * 0.5), base_x, 100, "trim:sao")
    if sao:
        parts.append(sao)
    z += sao_h

    chudai_h = H * 0.07
    chudai = M._gb_box(tree, (R * 1.1, R * 1.1, chudai_h), (0, 0, z + chudai_h * 0.5), base_x, 200, "trim:chudai")
    if chudai:
        parts.append(chudai)
    z += chudai_h

    hib_h = H * 0.22
    hib = M._gb_box(tree, (R * 1.35, R * 1.35, hib_h), (0, 0, z + hib_h * 0.5), base_x, 300, "trim:hibukuro")
    if hib:
        parts.append(hib)
    z += hib_h

    kasa_h = H * 0.14 * kasa_mul
    kasa_w = R * (2.0 + kasa_mul * 0.35)
    kasa = M._gb_box(tree, (kasa_w, kasa_w, kasa_h), (0, 0, z + kasa_h * 0.5), base_x, 400, "trim:kasa")
    if kasa:
        parts.append(kasa)
    z += kasa_h

    hoju_h = H * 0.07
    hoju = M._gb_box(tree, (R * 0.45, R * 0.45, hoju_h), (0, 0, z + hoju_h * 0.5), base_x, 500, "trim:hoju")
    if hoju:
        parts.append(hoju)

    return M._gb_join(tree, parts, base_x + 1200, 0)


def build_zen_honden(tree, M, props, base_x=-1400):
    """Main sanctuary (honden) — raised sanctum, enclosed moya, engawa margin, deep noki."""
    W = getattr(props, "gb_width", 5.5)
    D = getattr(props, "gb_depth", 4.5)
    H = getattr(props, "gb_height", 3.6)
    rise = getattr(props, "zen_honden_platform_rise", 0.55)
    t = getattr(props, "gb_wall_thick", 0.16)
    parts = []

    platform = M._gb_box(tree, (W * 1.08, D * 1.08, t), (0, 0, rise * 0.5), base_x, 0, "trim:sanctum_floor")
    if platform:
        parts.append(platform)

    floor_z = rise + t * 0.5
    moya_w = W * 0.72
    moya_d = D * 0.68
    moya_h = H * 0.62
    for i, (sx, sy) in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1))):
        if sx:
            wall = M._gb_box(
                tree,
                (t, moya_d, moya_h),
                (sx * (moya_w * 0.5 + t * 0.5), 0, floor_z + moya_h * 0.5),
                base_x,
                100 + i * 30,
                "trim:sanctuary_wall",
            )
        else:
            wall = M._gb_box(
                tree,
                (moya_w, t, moya_h),
                (0, sy * (moya_d * 0.5 + t * 0.5), floor_z + moya_h * 0.5),
                base_x,
                100 + i * 30,
                "trim:sanctuary_wall",
            )
        if wall:
            parts.append(wall)

    core = M._gb_box(
        tree,
        (moya_w * 0.55, moya_d * 0.55, moya_h * 0.45),
        (0, 0, floor_z + moya_h * 0.28),
        base_x,
        250,
        "trim:sanctum_floor",
    )
    if core:
        parts.append(core)

    engawa = M._gb_box(
        tree,
        (W, D * 0.22, t * 0.9),
        (0, -D * 0.5 + D * 0.11, floor_z + t * 0.45),
        base_x,
        350,
        "trim:engawa_margin",
    )
    if engawa:
        parts.append(engawa)

    threshold = M._gb_box(
        tree,
        (W * 0.55, t * 1.2, H * 0.18),
        (0, -D * 0.5 + t * 0.6, floor_z + H * 0.12),
        base_x,
        400,
        "trim:threshold",
    )
    if threshold:
        parts.append(threshold)

    noki = M._gb_box(
        tree,
        (W * 1.15, D * 1.12, t * 1.6),
        (0, 0, floor_z + H - t * 0.4),
        base_x,
        500,
        "trim:noki_eave",
    )
    if noki:
        parts.append(noki)

    return M._gb_join(tree, parts, base_x + 1800, 0)


def compute_zen_kit_snaps(M, props, arch_type=None):
    """Snap hooks for GB_ZEN_* modular kits."""
    t = arch_type or props.arch_type
    unit = getattr(props, "unit_size", 2.0)

    if t == "GB_ZEN_ROJI_STEP":
        L = getattr(props, "gb_length", 4.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.1), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.1), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "GB_ZEN_TORII_GATE":
        W = getattr(props, "torii_width", getattr(props, "gb_width", 3.6))
        H = getattr(props, "torii_height", getattr(props, "gb_height", 4.2))
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -1.2, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, 1.2, 0), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("gate", "DOOR", (0, 0, H * 0.35), (0, 1, 0), "MUST_CONNECT"),
        ]
    if t == "GB_ZEN_SAKURA_TORII":
        W = getattr(props, "torii_width", getattr(props, "gb_width", 3.4))
        H = getattr(props, "torii_height", getattr(props, "gb_height", 4.0))
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -1.2, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, 1.2, 0), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("gate", "DOOR", (0, 0, H * 0.35), (0, 1, 0), "MUST_CONNECT"),
            M._gb_snap_point("blossom", "TRIM", (0, 0, H * 0.98), (0, 0, 1)),
        ]
    if t == "GB_ZEN_TSUKUBAI":
        W = getattr(props, "gb_width", 1.6)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("basin", "TRIM", (0, 0, getattr(props, "gb_height", 0.45) * 0.6), (0, 0, 1)),
            M._gb_snap_point("approach_ny", "WALL", (0, -W * 0.6, 0), (0, -1, 0), grid_quantum=unit),
            M._gb_snap_point("approach_py", "WALL", (0, W * 0.6, 0), (0, 1, 0), grid_quantum=unit),
        ]
    if t == "GB_ZEN_ENGAWA":
        D = getattr(props, "gb_depth", 2.4)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("roji", "WALL", (0, -D * 0.5, 0.1), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("garden", "WALL", (0, D * 0.5, 0.1), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("engawa_edge", "TRIM", (0, D * 0.5, getattr(props, "gb_height", 0.35)), (0, 1, 0)),
        ]
    if t == "GB_ZEN_BAMBOO_FENCE":
        L = getattr(props, "gb_length", 4.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("fence_ny", "WALL", (0, -L * 0.5, 0.2), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("fence_py", "WALL", (0, L * 0.5, 0.2), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "GB_ZEN_TOBIISHI":
        L = getattr(props, "gb_length", 5.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.05), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.05), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "GB_ZEN_KARESANSUI":
        D = getattr(props, "gb_depth", 6.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("view_ny", "WALL", (0, -D * 0.5, 0.1), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("view_py", "WALL", (0, D * 0.5, 0.1), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("bench_px", "TRIM", (getattr(props, "gb_width", 8.0) * 0.5, 0, 0.12), (1, 0, 0)),
        ]
    if t == "GB_ZEN_MACHIAI":
        D = getattr(props, "gb_depth", 2.4)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -D * 0.5 - 0.3, 0.1), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("garden_py", "WALL", (0, D * 0.5, 0.1), (0, 1, 0), "OPTIONAL", grid_quantum=unit),
        ]
    if t == "GB_ZEN_STONE_BRIDGE":
        span = getattr(props, "zen_bridge_span", 5.0)
        rise = getattr(props, "zen_bridge_rise", 0.55)
        return [
            M._gb_snap_point("deck", "FLOOR", (0, 0, rise), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("bank_ny", "WALL", (0, -span * 0.5, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("bank_py", "WALL", (0, span * 0.5, 0), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "GB_ZEN_CHERRY_ALLEE":
        L = getattr(props, "gb_length", 6.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.08), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.08), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("canopy", "TRIM", (0, 0, getattr(props, "gb_height", 0.32) * 2.5), (0, 0, 1)),
        ]
    if t == "GB_ZEN_WATER_EDGE":
        L = getattr(props, "gb_length", 2.8)
        t_bank = getattr(props, "gb_wall_thick", 0.14) * 1.2
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.08), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.08), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("landing_ny", "FLOOR", (0, -L * 0.5 + 0.2, t_bank * 0.35), (0, 0, 1), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("landing_py", "FLOOR", (0, L * 0.5 - 0.2, t_bank * 0.35), (0, 0, 1), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("bridge_ny", "WALL", (0, -L * 0.5, 0.05), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("bridge_py", "WALL", (0, L * 0.5, 0.05), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "GB_ZEN_SANDO":
        L = getattr(props, "gb_length", 8.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.08), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.08), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("toro_mid", "TRIM", (0, 0, getattr(props, "gb_wall_thick", 0.12) * 2.5), (0, 0, 1)),
        ]
    if t == "GB_ZEN_KAIRO":
        L = getattr(props, "gb_length", 6.0)
        W = getattr(props, "gb_width", 2.4)
        H = getattr(props, "gb_height", 2.8)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("path_ny", "WALL", (0, -L * 0.5, 0.1), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, L * 0.5, 0.1), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("court_px", "WALL", (W * 0.5, 0, 0.1), (1, 0, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("garden_nx", "WALL", (-W * 0.5, 0, 0.1), (-1, 0, 0), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("engawa_edge", "TRIM", (W * 0.5, 0, H * 0.35), (1, 0, 0)),
        ]
    if t == "GB_ZEN_HAIDEN":
        D = getattr(props, "gb_depth", 4.0)
        rise = getattr(props, "zen_genkan_rise", 0.45)
        H = getattr(props, "gb_height", 3.2)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, rise), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("approach_ny", "WALL", (0, -D * 0.5 - 0.2, rise * 0.5), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("threshold", "DOOR", (0, -D * 0.5 + 0.15, rise + 0.1), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("sacred_py", "WALL", (0, D * 0.5, rise), (0, 1, 0), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("eave", "TRIM", (0, 0, rise + H * 0.9), (0, 0, 1)),
        ]
    if t == "GB_ZEN_GOJU_PAGODA":
        tiers = getattr(props, "pagoda_tiers", 5)
        th = getattr(props, "pagoda_tier_height", 1.2)
        total_h = tiers * th + 0.5
        R = getattr(props, "pagoda_base_radius", 2.0)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("court_anchor", "WALL", (R * 0.9, 0, total_h * 0.35), (1, 0, 0), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("spire", "TRIM", (0, 0, total_h), (0, 0, 1)),
        ]
    if t == "GB_ZEN_TAHOTO":
        H = getattr(props, "gb_height", 6.5)
        W = getattr(props, "gb_width", 3.2)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("sacred_anchor", "WALL", (0, 0, H * 0.85), (0, 0, 1), "OPTIONAL", grid_quantum=unit),
            M._gb_snap_point("spire", "TRIM", (0, 0, H), (0, 0, 1)),
            M._gb_snap_point("court_px", "WALL", (W * 0.55, 0, H * 0.25), (1, 0, 0), "OPTIONAL", grid_quantum=unit),
        ]
    if t == "GB_ZEN_HONDEN":
        D = getattr(props, "gb_depth", 4.5)
        rise = getattr(props, "zen_honden_platform_rise", 0.55)
        H = getattr(props, "gb_height", 3.6)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, rise), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("haiden_ny", "WALL", (0, -D * 0.5 - 0.25, rise), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("sacred_core", "TRIM", (0, 0, rise + H * 0.35), (0, 0, 1)),
            M._gb_snap_point("noki_edge", "TRIM", (0, 0, rise + H * 0.92), (0, 0, 1)),
        ]
    if t == "GB_ZEN_LANTERN":
        H = getattr(props, "zen_lantern_height", 1.6)
        return [
            M._gb_snap_point("floor", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("toro_mid", "TRIM", (0, 0, H * 0.45), (0, 0, 1)),
            M._gb_snap_point("accent", "TRIM", (0, 0, H), (0, 0, 1)),
        ]
    return []


def compute_zen_arch_snaps(M, props, arch_type=None):
    """Snap metadata for procedural ZEN_* architecture types (graph chaining)."""
    t = arch_type or props.arch_type
    unit = getattr(props, "unit_size", 2.0)

    if t == "ZEN_TORII":
        H = getattr(props, "torii_height", 4.2)
        return [
            M._gb_snap_point("path_ny", "WALL", (0, -1.5, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("path_py", "WALL", (0, 1.5, 0), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("gate", "DOOR", (0, 0, H * 0.35), (0, 1, 0), "MUST_CONNECT"),
        ]
    if t == "ZEN_BRIDGE":
        span = getattr(props, "zen_bridge_span", 4.0)
        return [
            M._gb_snap_point("bank_ny", "WALL", (0, -span * 0.5, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("bank_py", "WALL", (0, span * 0.5, 0), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("deck", "FLOOR", (0, 0, getattr(props, "zen_bridge_rise", 0.8)), (0, 0, 1)),
        ]
    if t == "ZEN_LANTERN":
        H = getattr(props, "zen_lantern_height", 1.6)
        return [
            M._gb_snap_point("base", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("accent", "TRIM", (0, 0, H), (0, 0, 1)),
        ]
    if t == "ZEN_TEAHOUSE":
        D = getattr(props, "teahouse_depth", 4.0)
        return [
            M._gb_snap_point("engawa", "WALL", (0, D * 0.5, 0.2), (0, 1, 0), "MUST_CONNECT", grid_quantum=unit),
            M._gb_snap_point("roji", "WALL", (0, -D * 0.5, 0), (0, -1, 0), "MUST_CONNECT", grid_quantum=unit),
        ]
    if t == "ZEN_STONE_GARDEN":
        sz = getattr(props, "stone_garden_size", 6.0)
        return [
            M._gb_snap_point("center", "FLOOR", (0, 0, 0), (0, 0, 1), grid_quantum=unit),
            M._gb_snap_point("edge_ny", "WALL", (0, -sz * 0.5, 0), (0, -1, 0), grid_quantum=unit),
            M._gb_snap_point("edge_py", "WALL", (0, sz * 0.5, 0), (0, 1, 0), grid_quantum=unit),
        ]
    return []


def compute_zen_snaps(M, props, arch_type=None):
    t = arch_type or props.arch_type
    if t.startswith("GB_ZEN_"):
        return compute_zen_kit_snaps(M, props, t)
    if t.startswith("ZEN_"):
        return compute_zen_arch_snaps(M, props, t)
    return []
