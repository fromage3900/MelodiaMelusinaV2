r"""build_faraway_seam_dressing.py -- exact F=0 junctions, traced seam polylines, stitch dressing instances. spike: true

numpy only (no hou/UE). Global field of chladni_field.py: F = cos(3 pi u)cos(5 pi v) - cos(5 pi u)cos(3 pi v),
u=(X+4000)/8000, v=(Y+4000)/8000, X/Y in metres. Deterministic (seed 3900).

 1. junctions   Newton on grad F = 0 from a dense seed lattice, kept where |F| < 1e-9 (exact crossings of nodal lines)
 2. seam lines  marching squares of F=0 on a 2048^2 lattice (3.9 m), chained into polylines, resampled every 6 m
                (tangent, curvature, distance-to-nearest-junction)
 3. stitches    Infinity-Nikki-style "sewn ground": instances along each seam, a ladder of cross-stitches every 2.4 m on
                alternating sides, plus a hero running-stitch band; scale/yaw jitter from a hash, 80 m junction clearance

Outputs: <out>/junctions.json, seam_polylines.json, stitches.json (+ stitches.csv for PCG point import), manifest.json
Usage: python Tools/Houdini/faraway/build_faraway_seam_dressing.py [--out DIR] [--grid 2048]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HALF = 4000.0
PI = math.pi


def F(u, v):
    return np.cos(3 * PI * u) * np.cos(5 * PI * v) - np.cos(5 * PI * u) * np.cos(3 * PI * v)


def grad_hess(u, v):
    c3u, c5u, s3u, s5u = np.cos(3 * PI * u), np.cos(5 * PI * u), np.sin(3 * PI * u), np.sin(5 * PI * u)
    c3v, c5v, s3v, s5v = np.cos(3 * PI * v), np.cos(5 * PI * v), np.sin(3 * PI * v), np.sin(5 * PI * v)
    fu = -3 * PI * s3u * c5v + 5 * PI * s5u * c3v
    fv = -5 * PI * c3u * s5v + 3 * PI * c5u * s3v
    fuu = -9 * PI**2 * c3u * c5v + 25 * PI**2 * c5u * c3v
    fvv = -25 * PI**2 * c3u * c5v + 9 * PI**2 * c5u * c3v
    fuv = 15 * PI**2 * s3u * s5v - 15 * PI**2 * s5u * s3v
    return fu, fv, fuu, fuv, fvv


def junctions():
    seeds = np.linspace(0.005, 0.995, 400)
    U, V = np.meshgrid(seeds, seeds)
    u, v = U.ravel().copy(), V.ravel().copy()
    for _ in range(40):
        fu, fv, a, b, d = grad_hess(u, v)
        det = a * d - b * b
        det = np.where(np.abs(det) < 1e-9, 1e-9, det)
        du = (d * fu - b * fv) / det
        dv = (-b * fu + a * fv) / det
        u -= np.clip(du, -0.02, 0.02)
        v -= np.clip(dv, -0.02, 0.02)
    ok = (u > 0) & (u < 1) & (v > 0) & (v < 1)
    fu, fv, *_ = grad_hess(u, v)
    ok &= (np.hypot(fu, fv) < 1e-7) & (np.abs(F(u, v)) < 1e-8)
    uniq = []
    for a_, b_ in sorted(zip(u[ok].tolist(), v[ok].tolist())):
        if all(abs(a_ - q[0]) > 2e-4 or abs(b_ - q[1]) > 2e-4 for q in uniq):
            uniq.append((a_, b_))
    return [(x * 2 * HALF - HALF, y * 2 * HALF - HALF) for x, y in uniq]


def marching(N):
    xs = np.linspace(0, 1, N)
    U, V = np.meshgrid(xs, xs)
    Z = F(U, V)
    segs = []
    for j in range(N - 1):
        z00, z10, z01, z11 = Z[j, :-1], Z[j, 1:], Z[j + 1, :-1], Z[j + 1, 1:]
        sgn = (z00 > 0).astype(int) | ((z10 > 0).astype(int) << 1) | ((z11 > 0).astype(int) << 2) | ((z01 > 0).astype(int) << 3)
        for i in np.nonzero((sgn != 0) & (sgn != 15))[0]:
            def interp(a, b, ia, ib):
                t = a / (a - b) if a != b else 0.5
                return t
            x0, x1, y0, y1 = xs[i], xs[i + 1], xs[j], xs[j + 1]
            e = []
            a, b, c, d = z00[i], z10[i], z11[i], z01[i]
            if (a > 0) != (b > 0): e.append((x0 + (x1 - x0) * a / (a - b), y0))
            if (b > 0) != (c > 0): e.append((x1, y0 + (y1 - y0) * b / (b - c)))
            if (d > 0) != (c > 0): e.append((x0 + (x1 - x0) * d / (d - c), y1))
            if (a > 0) != (d > 0): e.append((x0, y0 + (y1 - y0) * a / (a - d)))
            if len(e) == 2: segs.append((e[0], e[1]))
            elif len(e) == 4: segs += [(e[0], e[1]), (e[2], e[3])]
    return segs


def chain(segs):
    key = lambda p: (round(p[0] * 1e7), round(p[1] * 1e7))
    adj = {}
    for s in segs:
        for p, q in (s, s[::-1]):
            adj.setdefault(key(p), []).append(q)
    seen, lines = set(), []
    pts = {key(p): p for s in segs for p in s}
    for k0 in sorted(adj):
        if k0 in seen or len(adj[k0]) != 1 and False: continue
        if k0 in seen: continue
        # walk both ways from k0
        line = [pts[k0]]; seen.add(k0); cur = k0
        while True:
            nxt = [q for q in adj[cur] if key(q) not in seen]
            if not nxt: break
            q = nxt[0]; seen.add(key(q)); line.append(q); cur = key(q)
        if len(line) > 5: lines.append(line)
    return lines


def resample(line, step_m):
    P = np.array([[x * 2 * HALF - HALF, y * 2 * HALF - HALF] for x, y in line])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    n = max(2, int(d[-1] / step_m))
    s = np.linspace(0, d[-1], n)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], d[-1]


def h32(*a):
    x = 2166136261
    for v in a:
        x = ((x ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 4294967295.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawaySeamDressing_20261026"))
    ap.add_argument("--grid", type=int, default=2048)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    J = junctions()
    segs = marching(a.grid)
    lines = chain(segs)
    seams = []
    stitches = []
    for li, ln in enumerate(lines):
        P, length = resample(ln, 6.0)
        if length < 60: continue
        T = np.gradient(P, axis=0); T /= np.maximum(np.hypot(*T.T)[:, None], 1e-9)
        ang = np.unwrap(np.arctan2(T[:, 1], T[:, 0]))
        curv = np.abs(np.gradient(ang)) / 6.0
        dj = np.min(np.hypot(P[:, None, 0] - np.array([j[0] for j in J])[None], P[:, None, 1] - np.array([j[1] for j in J])[None]), axis=1)
        seams.append({"id": li, "length_m": round(float(length), 1), "points": [[round(float(x), 2), round(float(y), 2)] for x, y in P[::2]],
                      "max_curvature_per_m": round(float(curv.max()), 5), "min_junction_dist_m": round(float(dj.min()), 1)})
        # cross-stitch ladder every 2.4 m, alternating side, offset 0.35 m, 80 m junction clearance
        Q, _ = resample(ln, 2.4)
        TQ = np.gradient(Q, axis=0); TQ /= np.maximum(np.hypot(*TQ.T)[:, None], 1e-9)
        for k, (p, t) in enumerate(zip(Q, TQ)):
            if np.min(np.hypot(p[0] - np.array([j[0] for j in J]), p[1] - np.array([j[1] for j in J]))) < 80: continue
            side = 1 if k % 2 == 0 else -1
            n = np.array([-t[1], t[0]])
            h = h32(li, k, 3900)
            kind = "cross" if k % 5 else "knot"
            stitches.append({"x": round(float(p[0] + n[0] * side * 0.35), 3), "y": round(float(p[1] + n[1] * side * 0.35), 3),
                             "yaw_deg": round(math.degrees(math.atan2(t[1], t[0])) + (90 if kind == "cross" else 0) + (h - 0.5) * 14, 2),
                             "scale": round(0.85 + 0.4 * h, 3), "kind": kind, "seam": li})
    # junction ornament: a "button" at every junction
    buttons = [{"x": round(j[0], 2), "y": round(j[1], 2), "kind": "button", "scale": 2.0, "yaw_deg": 0.0, "seam": -1} for j in J]
    inside = [j for j in J if abs(j[0]) < HALF and abs(j[1]) < HALF]
    gate = {"junction_count": len(J), "seam_lines": len(seams), "stitch_count": len(stitches),
            "total_seam_km": round(sum(s["length_m"] for s in seams) / 1000, 2),
            "min_stitch_junction_clearance_ok": all(min(math.hypot(s["x"] - j[0], s["y"] - j[1]) for j in J) >= 79.0 for s in stitches[::50]),
            "origin_junction": any(abs(j[0]) < 1 and abs(j[1]) < 1 for j in J),
            "heart_gate_580_on_seam": abs(math.cos(3 * PI * (580 + HALF) / 8000) * math.cos(5 * PI * HALF / 8000) - math.cos(5 * PI * (580 + HALF) / 8000) * math.cos(3 * PI * HALF / 8000)) < 1e-9}
    gate["pass"] = bool(gate["junction_count"] >= 3 and gate["seam_lines"] > 0 and gate["stitch_count"] > 1000 and gate["origin_junction"] and gate["min_stitch_junction_clearance_ok"] and gate["heart_gate_580_on_seam"])
    (out / "junctions.json").write_text(json.dumps({"units": "m global X/Y", "count": len(J), "junctions": [[round(x, 2), round(y, 2)] for x, y in J]}))
    (out / "seam_polylines.json").write_text(json.dumps({"seams": seams}))
    (out / "stitches.json").write_text(json.dumps({"seed": 3900, "instances": stitches + buttons}))
    (out / "stitches.csv").write_text("x_m,y_m,yaw_deg,scale,kind,seam\n" + "\n".join(f"{s['x']},{s['y']},{s['yaw_deg']},{s['scale']},{s['kind']},{s['seam']}" for s in stitches + buttons))
    man = {"schema": "melodia.faraway_seam_dressing.spike.v1", "spike": True, "gate": gate,
           "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(out.glob("*")) if p.is_file() and p.name != "manifest.json"}}
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
