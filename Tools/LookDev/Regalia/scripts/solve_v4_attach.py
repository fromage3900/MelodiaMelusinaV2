"""Box-side: solve Blender-rest-world (as imported 'blender-cm' space B=(x,-y,z)*100) -> UE body component space similarity
from matching bone heads, then per-piece attach transforms relative to the UE bind pose of the attach bone.
usage: python3 solve_v4_attach.py melusina_pose_dump_v4.json ue_probe_v4.json out.json"""
import json, sys, re, numpy as np
pd, pr, out = sys.argv[1:4]
PD = json.load(open(pd)); PR = json.load(open(pr))
UB = PR["body"]["bones_cs"]
def norm(n): return re.sub(r"[.\-]", "_", n).lower()
un = {norm(k): k for k in UB}
A, B, names = [], [], []
for bn, d in PD["bones"].items():
    k = un.get(norm(bn))
    if not k: continue
    M = np.array(d["rest"]); p = M[:3, 3]
    A.append([p[0] * 100, -p[1] * 100, p[2] * 100]); B.append(UB[k][:3]); names.append((bn, k))
A = np.array(A); B = np.array(B); n = len(A)
print("matched bones", n, "of", len(PD["bones"]), "blender deform /", len(UB), "UE")
def umeyama(X, Y):
    mx, my = X.mean(0), Y.mean(0); Xc, Yc = X - mx, Y - my
    C = Yc.T @ Xc / len(X); U, S, Vt = np.linalg.svd(C); D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0: D[2, 2] = -1
    R = U @ D @ Vt; s = np.trace(np.diag(S) @ D) / ((Xc ** 2).sum() / len(X)); t = my - s * R @ mx
    return s, R, t
s, R, t = umeyama(A, B)
res = np.linalg.norm((s * (R @ A.T)).T + t - B, axis=1)
# robust: drop outliers > 3*median and refit
keep = res < max(0.5, 3 * np.median(res)); s, R, t = umeyama(A[keep], B[keep])
res2 = np.linalg.norm((s * (R @ A.T)).T + t - B, axis=1)
head_names = [k for k in UB if norm(k) in ("head_x", "head")]; neck = [k for k in UB if norm(k) in ("spine_03_x", "spine_03")]
print("scale", s, "\nR\n", np.round(R, 4), "\nt", np.round(t, 3))
print("residual cm: median %.3f max(kept) %.3f n_kept %d" % (np.median(res2[keep]), res2[keep].max(), keep.sum()))
for (bn, k), r in zip(names, res2):
    if norm(k) in ("head_x", "neck_x", "spine_03_x", "root_x") or r > 1.0: print("  ", bn, k, round(float(r), 3))
def q2m(x, y, z, w):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def m2q(M):
    tr = M.trace()
    if tr > 0:
        S = np.sqrt(tr + 1) * 2; w = 0.25 * S; x = (M[2, 1] - M[1, 2]) / S; y = (M[0, 2] - M[2, 0]) / S; z = (M[1, 0] - M[0, 1]) / S
    else:
        i = int(np.argmax(np.diag(M)))
        if i == 0: S = np.sqrt(1 + M[0, 0] - M[1, 1] - M[2, 2]) * 2; w = (M[2, 1] - M[1, 2]) / S; x = 0.25 * S; y = (M[0, 1] + M[1, 0]) / S; z = (M[0, 2] + M[2, 0]) / S
        elif i == 1: S = np.sqrt(1 + M[1, 1] - M[0, 0] - M[2, 2]) * 2; w = (M[0, 2] - M[2, 0]) / S; x = (M[0, 1] + M[1, 0]) / S; y = 0.25 * S; z = (M[1, 2] + M[2, 1]) / S
        else: S = np.sqrt(1 + M[2, 2] - M[0, 0] - M[1, 1]) * 2; w = (M[1, 0] - M[0, 1]) / S; x = (M[0, 2] + M[2, 0]) / S; y = (M[1, 2] + M[2, 1]) / S; z = 0.25 * S
    q = np.array([x, y, z, w]); return (q / np.linalg.norm(q)).tolist()
def rel_to(bone):
    b = UB[bone]; Rb = q2m(*b[3:7]); tb = np.array(b[:3])
    Rr = Rb.T @ R; tr = Rb.T @ (t - tb)
    return {"bone": bone, "loc": tr.tolist(), "quat_xyzw": m2q(Rr), "scale": float(s)}
O = {"scale": float(s), "R": R.tolist(), "t": t.tolist(), "n_matched": int(n), "n_kept": int(keep.sum()),
     "residual_median_cm": float(np.median(res2[keep])), "residual_max_cm": float(res2[keep].max()),
     "head_bone": head_names[0] if head_names else None, "neck_bone": neck[0] if neck else None}
O["attach"] = {"SM_Regalia_v4_Circlet": rel_to(O["head_bone"]), "SM_Regalia_v4_Tiara": rel_to(O["head_bone"]),
               "SM_Regalia_v4_Earrings": rel_to(O["head_bone"]), "SM_Regalia_v4_Necklace": rel_to(O["neck_bone"])}
O["component_space"] = {"loc": t.tolist(), "quat_xyzw": m2q(R), "scale": float(s)}
json.dump(O, open(out, "w"), indent=1); print("wrote", out, json.dumps(O["attach"], indent=0)[:800])
