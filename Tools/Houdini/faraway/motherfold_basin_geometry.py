r"""motherfold_basin_geometry.py -- pure-Python shoreline + water helpers for the Motherfold Basin HDA.

Embedded verbatim in the HDA's Python SOPs by build_faraway_motherfold_basin_hda.py (no file
dependency at cook time). Needs numpy only (ships with hython).

Shoreline = marching TRIANGLES on the cooked terrain grid (each quad split a-b-c / a-c-d), contour
at the water level. Every segment is emitted with the low (wet) side on its LEFT in the (x, z) frame,
so every closed lake loop has a POSITIVE shoelace area in (x, z), islands come out negative, and a
chain that leaves the tile is an OPEN polyline that ends exactly on the tile border (the crossing on
a border edge depends only on the two border samples, so neighbour tiles meet at the same point).
"""
import math

import numpy as np


def shoreline_chains(P, level):
    """P: (N,3) point positions of a square Grid-SOP tile (any point order). Returns
    [(closed: bool, [(x, y, z), ...]), ...] sorted closed-first then longest-first. For a closed
    chain the first point is NOT repeated at the end."""
    P = np.asarray(P, dtype=np.float64).reshape(-1, 3)
    n = int(round(math.sqrt(len(P)))) - 1
    if n < 1 or (n + 1) * (n + 1) != len(P):
        raise ValueError("input is not a square grid of points (%d pts)" % len(P))
    x0, z0 = P[:, 0].min(), P[:, 2].min()
    cell = (P[:, 0].max() - x0) / n
    ix = np.rint((P[:, 0] - x0) / cell).astype(np.int64)
    iz = np.rint((P[:, 2] - z0) / cell).astype(np.int64)
    H = np.empty((n + 1, n + 1))
    X = np.empty((n + 1, n + 1))
    Z = np.empty((n + 1, n + 1))
    H[iz, ix] = P[:, 1]
    X[iz, ix] = P[:, 0]
    Z[iz, ix] = P[:, 2]
    above = H >= level

    tris = []  # triangles of each cell: (a,b,c) and (a,c,d), a=(r,c) b=(r,c+1) c=(r+1,c+1) d=(r+1,c)
    for tri in (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0))):
        s = sum(above[(slice(o[0], n + o[0]), slice(o[1], n + o[1]))].astype(np.int8) for o in tri)
        for r, cc in zip(*np.nonzero((s == 1) | (s == 2))):
            tris.append(tuple((int(r) + o[0], int(cc) + o[1]) for o in tri))

    def pos(v0, v1):
        h0, h1 = H[v0], H[v1]
        t = (level - h0) / (h1 - h0)
        return (X[v0] + t * (X[v1] - X[v0]), level, Z[v0] + t * (Z[v1] - Z[v0]))

    nxt, where = {}, {}
    for tri in tris:
        side = [bool(above[v]) for v in tri]
        odd = 0 if side[1] == side[2] else (1 if side[0] == side[2] else 2)
        o1, o2 = tri[(odd + 1) % 3], tri[(odd + 2) % 3]
        vo = tri[odd]
        k1 = (vo, o1) if vo < o1 else (o1, vo)
        k2 = (vo, o2) if vo < o2 else (o2, vo)
        p, q = pos(vo, o1), pos(vo, o2)
        low = vo if not above[vo] else o1
        lx, lz = X[low], Z[low]
        cross = (q[0] - p[0]) * (lz - p[2]) - (q[2] - p[2]) * (lx - p[0])
        if cross < 0:
            k1, k2, p, q = k2, k1, q, p
        nxt[k1] = k2
        where[k1] = p
        where[k2] = q

    ends = set(nxt.values())
    chains, seen = [], set()
    for k in sorted(k for k in nxt if k not in ends):  # open chains start where nothing ends
        pts, cur = [], k
        while cur is not None and cur not in seen:
            seen.add(cur)
            pts.append(where[cur])
            cur = nxt.get(cur)
        chains.append((False, pts))
    for k in sorted(nxt):  # what is left are pure cycles
        if k in seen:
            continue
        pts, cur = [], k
        while cur not in seen:
            seen.add(cur)
            pts.append(where[cur])
            cur = nxt[cur]
        chains.append((True, pts))
    chains.sort(key=lambda ch: (not ch[0], -len(ch[1])))
    return chains


def shoelace_xz(pts):
    """Signed area in the (x, z) frame; >0 for the loops emitted by shoreline_chains (lake)."""
    s = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i][0], pts[i][2]
        x2, z2 = pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][2]
        s += x1 * z2 - x2 * z1
    return 0.5 * s


def water_rect(tile_x, tile_y, tile_size, bx, by, radius, margin=1.1):
    """Water plane footprint = tile bounds intersected with the lake's square (centre +- radius*margin).
    Returns (x0, z0, x1, z1) in global metres or None when they do not overlap."""
    rw = radius * margin
    x0, x1 = max(tile_x, bx - rw), min(tile_x + tile_size, bx + rw)
    z0, z1 = max(tile_y, by - rw), min(tile_y + tile_size, by + rw)
    if x1 - x0 < 1e-3 or z1 - z0 < 1e-3:
        return None
    return (x0, z0, x1, z1)
