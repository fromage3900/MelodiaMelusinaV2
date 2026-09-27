import sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, motif2d as M
which = sys.argv[1]; x0, x1 = float(sys.argv[2]), float(sys.argv[3])
E, ut, ub = M.circlet_layout(1240.0) if which == "c" else M.tiara_layout(620.0)
fig, ax = plt.subplots(figsize=(16, 16 * 40 / (x1 - x0) + 1.5))
import numpy as np; S = np.linspace(x0, x1, 600)
ax.plot(S, [ut(s) for s in S], "k-"); ax.plot(S, [ub(s) for s in S], "k-")
for e in E:
    o = M.outline_samples(e)
    if e["kind"] == "bead":
        ax.fill([p[0] for p in o], [p[1] for p in o], color="goldenrod")
    else:
        P = e["pts"]; L = o[0::2]; R = o[1::2]
        if e["closed"]: ax.plot([p[0] for p in L + L[:1]], [p[1] for p in L + L[:1]], "b-", lw=.6); ax.plot([p[0] for p in R + R[:1]], [p[1] for p in R + R[:1]], "b-", lw=.6)
        else: ax.plot([p[0] for p in L], [p[1] for p in L], "b-", lw=.6); ax.plot([p[0] for p in R], [p[1] for p in R], "b-", lw=.6)
        ax.plot([p[0] for p in P], [p[1] for p in P], "r-", lw=.3)
ax.set_xlim(x0, x1); ax.set_aspect("equal"); plt.savefig(sys.argv[4], dpi=80, bbox_inches="tight")
