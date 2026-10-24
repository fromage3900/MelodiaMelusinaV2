"""Largest watertight component -> Sonifold LB eigenpairs + nodal figure."""
import sys, time
from pathlib import Path
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

name, N = sys.argv[1], int(sys.argv[2])
mesh = trimesh.load(Path("data/meshes")/f"{name}.obj", force="mesh")
comps = mesh.split(only_watertight=False)
comps.sort(key=lambda c: len(c.vertices), reverse=True)
mesh = comps[0]
print(f"using largest component: {len(mesh.vertices)}v/{len(mesh.faces)}f watertight={mesh.is_watertight}")

from precompute.eigensolver import compute_eigen
V = np.asarray(mesh.vertices, dtype=np.float64)
F = np.asarray(mesh.faces, dtype=np.int64)
t0 = time.time()
evals, evecs = compute_eigen(V, F, N=N)
print(f"{N} eigenpairs in {time.time()-t0:.1f}s")
print("eigenvalues 0..15:", np.round(evals[:16], 3))

out = Path("data/eigen"); out.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out/f"{name}.npz", eigenvalues=evals, eigenvectors=evecs, vertices=V, faces=F)

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
mode = lambda k: evecs[k] if evecs.shape[0] == len(evals) else evecs[:, k]
modes = [1, 2, 3, 5, 8, 13]
fig = plt.figure(figsize=(18, 10))
for i, k in enumerate(modes):
    ax = fig.add_subplot(2, 3, i+1, projection="3d")
    vals = mode(k)
    s = np.std(vals) + 1e-12
    t = np.clip(vals / (2*s), -1, 1) * 0.5 + 0.5
    fc = plt.cm.RdBu_r(t[F].mean(axis=1))
    pc = Poly3DCollection(V[F], facecolors=fc, edgecolor="none")
    ax.add_collection3d(pc)
    ax.set_box_aspect((np.ptp(V[:,0]), np.ptp(V[:,1]), np.ptp(V[:,2])))
    ax.view_init(elev=12, azim=30)
    ax.set_title(f"mode {k}  lam={evals[k]:.3f}"); ax.set_axis_off()
fig.suptitle(f"Sonifold | Melodia '{name}' — LB eigenmodes")
fig.savefig(f"figures/melodia_{name}_modes.png", dpi=110, bbox_inches="tight")
print(f"saved figures/melodia_{name}_modes.png")
