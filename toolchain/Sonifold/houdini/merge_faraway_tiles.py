"""merge_faraway_tiles.py -- merge staged g3x3 faraway tiles into one heightfield OBJ.

Tiles are point grids (SilkPeak HDA output0, (div+1)^2 points, P includes height,
analytic N). Merges by global lattice key, triangulates, writes OBJ (normals via
area-weighted accumulation). Pure hython + numpy; no license-gated export.

Usage: hython merge_faraway_tiles.py [tag] [out_obj]
"""
import os
import sys

import hou
import numpy as np

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile"
KIT = r"G:\Melodia_Houdini_Foundry\FarawayCarKit_20261024"
TAG = sys.argv[1] if len(sys.argv) > 1 else "g3x3_origin"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(KIT, "FarawayMountains_3x3.obj")
TILES = os.path.join(ROOT, "Saved", "Audit", "faraway_tiles", TAG, "tiles")

obj = hou.node("/obj")
geo = obj.createNode("geo")
geo.setName("tile_merge")
fs = geo.createNode("file")

pts = {}
for f in sorted(os.listdir(TILES)):
    if not f.endswith(".bgeo.sc"):
        continue
    fs.parm("file").set(os.path.join(TILES, f))
    fs.cook(force=True)
    g = fs.geometry()
    P = np.array([[p.position().x(), p.position().y(), p.position().z()] for p in g.points()])
    for x, y, z in P:
        pts[(round(x, 3), round(y, 3), round(z, 3))] = (x, y, z)
    print(f, len(P), "points; merged so far:", len(pts))

P = np.array(list(pts.values()))
# detect layout: the two plane dims are the ones with lattice-scale unique counts
uniq = [len(np.unique(np.round(P[:, c], 3))) for c in range(3)]
plane = sorted(range(3), key=lambda c: uniq[c])[:2]
plane.sort()
height = [c for c in range(3) if c not in plane][0]
print(f"layout: plane dims {plane}, height dim {height}, uniques {uniq}")

u0 = sorted({k[plane[0]] for k in pts})
u1 = sorted({k[plane[1]] for k in pts})
nx, ny = len(u0), len(u1)
m0 = {v: i for i, v in enumerate(u0)}
m1 = {v: i for i, v in enumerate(u1)}
V = np.zeros((nx * ny, 3))
for k, p in pts.items():
    V[m1[k[plane[1]]] * nx + m0[k[plane[0]]]] = p
print(f"grid {nx} x {ny}, plane extents {u0[0]}..{u0[-1]} / {u1[0]}..{u1[-1]}, "
      f"height range {P[:, height].min():.1f}..{P[:, height].max():.1f}")

# triangulate (two tris per quad), then area-weighted vertex normals (vectorized)
j, i = np.meshgrid(np.arange(ny - 1), np.arange(nx - 1), indexing="ij")
a = (j * nx + i).ravel()
b = a + 1
c = a + nx
d = c + 1
F = np.stack([np.concatenate([a, a]), np.concatenate([b, d]),
              np.concatenate([d, c])], axis=1)
T = V[F]                                    # (ntri, 3, 3)
fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
N = np.zeros_like(V)
np.add.at(N, F.ravel(), np.repeat(fn, 3, axis=0))
ln = np.linalg.norm(N, axis=1, keepdims=True)
N = N / np.where(ln == 0, 1, ln)

with open(OUT, "w") as fh:
    fh.write(f"# Faraway mountains 3x3 tile merge ({TAG}) - {nx}x{ny} grid, {len(F)} tris\n")
    for p, n in zip(V, N):
        fh.write(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")
        fh.write(f"vn {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}\n")
    for a, b, c in F:
        fh.write(f"f {a+1}//{a+1} {b+1}//{b+1} {c+1}//{c+1}\n")
z = V[:, 2]
print(f"wrote {OUT}  {os.path.getsize(OUT)//1024} KB, z range {z.min():.1f}..{z.max():.1f}")
