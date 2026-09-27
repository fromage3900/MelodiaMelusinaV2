"""regalia v5 motif space (pure python). Units: mm at Melusina's scale, NOMINAL band.
s = along band (0 = front centre for the circlet / top centre for the tiara), u = across band (+ = up/toward face side).
Every motif has a FIXED sample count, so topology never depends on the fit."""
import math
def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def resample(pts, n, closed=False):
    P = list(pts) + ([pts[0]] if closed else [])
    L = [0.0]
    for i in range(1, len(P)): L.append(L[-1] + dist(P[i - 1], P[i]))
    tot = L[-1]; out = []; j = 0
    cnt = n if closed else n - 1
    for k in range(n):
        d = tot * k / cnt
        while j < len(L) - 2 and L[j + 1] < d: j += 1
        seg = max(1e-12, L[j + 1] - L[j]); out.append(lerp(P[j], P[j + 1], (d - L[j]) / seg))
    return out
def length(pts, closed=False):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) + (dist(pts[-1], pts[0]) if closed else 0)
def bezier(p0, p1, p2, p3, n=40):
    out = []
    for k in range(n + 1):
        t = k / n; a = (1 - t) ** 3; b = 3 * t * (1 - t) ** 2; c = 3 * t * t * (1 - t); d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out
def spiral(c, r_start, r_end, a_start, a_end, n=60):
    return [(c[0] + (r_start + (r_end - r_start) * k / n) * math.cos(a_start + (a_end - a_start) * k / n),
             c[1] + (r_start + (r_end - r_start) * k / n) * math.sin(a_start + (a_end - a_start) * k / n)) for k in range(n + 1)]
def ellipse(c, a, b, n=120, a0=0.0):
    return [(c[0] + a * math.cos(a0 + 2 * math.pi * k / n), c[1] + b * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]
def teardrop(big_c, R, tip_c, r, n=64):
    """closed centreline = convex hull of two circles (rounded tip, never a cusp), CCW"""
    dx, dy = tip_c[0] - big_c[0], tip_c[1] - big_c[1]; D = math.hypot(dx, dy); ang = math.atan2(dy, dx)
    beta = math.acos((R - r) / D)             # tangent angle measured from the axis
    pts = []
    for k in range(48):                        # big arc: from +beta to 2pi-beta (the far side)
        a = ang + beta + (2 * math.pi - 2 * beta) * k / 47; pts.append((big_c[0] + R * math.cos(a), big_c[1] + R * math.sin(a)))
    for k in range(16):                        # tip arc: from -beta to +beta
        a = ang - beta + 2 * beta * k / 15; pts.append((tip_c[0] + r * math.cos(a), tip_c[1] + r * math.sin(a)))
    return resample(pts, n, closed=True)
def mirror_s(pts, s0=0.0): return [(2 * s0 - p[0], p[1]) for p in pts]
def smooth(pts, it=2, closed=False):
    P = list(pts)
    for _ in range(it):
        Q = []
        for i in range(len(P)):
            if not closed and (i == 0 or i == len(P) - 1): Q.append(P[i]); continue
            a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]; Q.append(((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4))
        P = Q
    return P

# --------------------------------------------------------------- element records
# kind: "wire" (centreline, closed, width, dome height) | "bead" (centre, radius, height)
def W(pts, closed, w, h, name, spacing=1.1, n=None):
    n = n or max(8, int(round(length(pts, closed) / spacing)))
    return {"kind": "wire", "pts": resample(pts, n, closed), "closed": closed, "w": w, "h": h, "name": name}
def B(c, r, h, name): return {"kind": "bead", "c": c, "r": r, "h": h, "name": name}

# --------------------------------------------------------------- band plate shape (nominal)
def circlet_plate(h_nom=15.0, rim=2.8):
    half = h_nom / 2 - rim            # 4.7
    PK, PW, DIP = 24.0, 52.0, 3.0
    def bump(s): return math.cos(math.pi / 2 * s / PW) ** 2 if abs(s) < PW else 0.0
    return (lambda s: half + PK * bump(s)), (lambda s: -half - DIP * bump(s))
def tiara_plate(h_nom=12.0, rim=2.24):
    half = h_nom / 2 - rim
    return (lambda s: half), (lambda s: -half)

# --------------------------------------------------------------- motifs
WIRE_W, WIRE_H = 1.5, 1.05
def motif_A(sc, k=1.0, tag="A"):
    """paired teardrops, tips facing a centre bead, small end beads"""
    E = []
    for sg in (1, -1):
        E.append(W(teardrop((sc + sg * 9.5 * k, 0), 3.2 * k, (sc + sg * 3.7 * k, 0), 1.0 * k), True, WIRE_W * k, WIRE_H * k, "%s_td%+d" % (tag, sg)))
        E.append(B((sc + sg * 15.2 * k, 0.0), 0.95 * k, 0.8 * k, "%s_bs%+d" % (tag, sg)))
    E.append(B((sc, 0.0), 1.3 * k, 1.1 * k, tag + "_bc"))
    return E
def motif_B(sc, k=1.0, tag="B"):
    """lyre scroll: one continuous wire, round U at the bottom, both ends curling into eyes"""
    rightpart = bezier((sc + 0.0, -3.3 * k), (sc + 1.8 * k, -3.3 * k), (sc + 1.6 * k, 3.4 * k), (sc + 4.4 * k, 3.4 * k), 24)
    eye_c = (sc + 5.6 * k, 0.9 * k)
    sp = spiral(eye_c, 2.5 * k, 1.05 * k, math.radians(118), math.radians(118 - 300), 44)
    right = rightpart + sp[1:]
    left = mirror_s(right, sc)
    pts = list(reversed(left))[:-1] + right
    return [W(smooth(pts, 2), False, WIRE_W * k, WIRE_H * k, tag + "_lyre")]
def circlet_front(ut, ub):
    E = []
    SC, SU = 0.0, 9.5                  # stone centre
    sa, sb = 16.0, 12.0                # stone half axes (32 x 24)
    E.append(W(ellipse((SC, SU), sa + 1.25, sb + 1.25, 132), True, 1.8, 3.2, "F_collet"))
    for i in range(9):                 # crown of beads over the collet
        a = math.radians(22 + 136 * i / 8); E.append(B((SC + (sa + 4.4) * math.cos(a), SU + (sb + 4.4) * math.sin(a)), 0.95, 0.8, "F_bead%d" % i))
    for sg in (1, -1):
        ea, eb = sa + 6.9, sb + 6.9
        arc = [(SC + ea * math.cos(math.radians(a)), SU + eb * math.sin(math.radians(a))) for a in range(-50, -4, 3)]
        up = bezier((SC + ea, SU), (SC + ea + 0.1, SU + 4.4), (SC + ea + 1.2, SU + 6.0), (27.2, ut(27.2) - 2.4), 16)
        top = [(s, ut(s) - 2.4) for s in [27.2 + (37.6 - 27.2) * k / 10 for k in range(1, 11)]]
        eye_c = (40.6, 3.3)
        sp = spiral(eye_c, 2.55, 1.05, math.radians(100), math.radians(100 - 290), 40)
        pts = smooth(arc + up + top + sp[1:], 6)
        if sg < 0: pts = mirror_s(pts)
        E.append(W(pts, False, WIRE_W, WIRE_H, "F_scroll%+d" % sg))
        E.append(B((sg * 9.4, -5.9), 0.8, 0.7, "F_bfoot%+d" % sg))
    return E
def circlet_layout(L_nom):
    ut, ub = circlet_plate()
    E = circlet_front(ut, ub)
    for sg in (1, -1):
        for k in range(7): E += motif_A(sg * (80 + 72 * k), 1.0, "A%+d_%d" % (sg, k))
        for k in range(6):
            E += motif_B(sg * (116 + 72 * k), 1.0, "B%+d_%d" % (sg, k))
            for d in (-15.5, 15.5): E.append(B((sg * (116 + 72 * k) + d, 0.0), 0.7, 0.6, "Bb%+d_%d_%+d" % (sg, k, d)))
    return E, ut, ub
def tiara_layout(L_nom):
    ut, ub = tiara_plate(); E = []
    k = 0.78; half = L_nom / 2
    pos = []; s = 24.0
    while s + 16 * k < half - 10: pos.append(s); s += 30.0
    for i, p in enumerate(pos):
        for sg in (1, -1):
            if i % 2 == 0: E += motif_A(sg * p, k, "tA%+d_%d" % (sg, i))
            else: E += motif_B(sg * p, k, "tB%+d_%d" % (sg, i))
    return E, ut, ub

# --------------------------------------------------------------- validation (outline samples)
def outline_samples(e):
    out = []
    if e["kind"] == "bead":
        for k in range(24): a = 2 * math.pi * k / 24; out.append((e["c"][0] + e["r"] * math.cos(a), e["c"][1] + e["r"] * math.sin(a)))
        return out
    P = e["pts"]; n = len(P); hw = e["w"] / 2
    for i in range(n):
        a = P[i - 1] if (e["closed"] or i > 0) else P[i]; b = P[(i + 1) % n] if (e["closed"] or i < n - 1) else P[i]
        tx, ty = b[0] - a[0], b[1] - a[1]; l = math.hypot(tx, ty) or 1; nx, ny = -ty / l, tx / l
        out += [(P[i][0] + nx * hw, P[i][1] + ny * hw), (P[i][0] - nx * hw, P[i][1] - ny * hw)]
    return out
def validate(E, ut, ub, gap=0.25, margin=0.3):
    issues = []
    for e in E:
        for p in outline_samples(e):
            if p[1] > ut(p[0]) - margin or p[1] < ub(p[0]) + margin: issues.append("%s outside plate at (%.1f,%.1f)" % (e["name"], p[0], p[1])); break
    # pairwise: distance between centre geometry minus half widths
    def cen(e): return [e["c"]] if e["kind"] == "bead" else e["pts"]
    def rad(e): return e["r"] if e["kind"] == "bead" else e["w"] / 2
    for i in range(len(E)):
        for j in range(i + 1, len(E)):
            a, b = E[i], E[j]
            ca, cb = cen(a), cen(b)
            if min(x[0] for x in ca) - 20 > max(x[0] for x in cb) or min(x[0] for x in cb) - 20 > max(x[0] for x in ca): continue
            d = min(dist(p, q) for p in ca for q in cb) - rad(a) - rad(b)
            if d < gap: issues.append("%s ~ %s gap %.2f" % (a["name"], b["name"], d))
    # self-clearance for wires: non-adjacent samples closer than width
    for e in E:
        if e["kind"] != "wire": continue
        P = e["pts"]; n = len(P); step = length(P, e["closed"]) / n; skip = int(math.ceil(e["w"] * 1.6 / step)) + 1
        worst = 1e9
        for i in range(n):
            for j in range(i + skip, n):
                if e["closed"] and (n - (j - i)) <= skip: continue
                worst = min(worst, dist(P[i], P[j]))
        if worst < e["w"] + gap: issues.append("%s self-gap %.2f" % (e["name"], worst - e["w"]))
        # curvature radius >= w/2 (offset validity)
        for i in range(1 if not e["closed"] else 0, n - (1 if not e["closed"] else 0)):
            a, b, c = P[i - 1], P[i], P[(i + 1) % n]
            A = dist(a, b); Bb = dist(b, c); C = dist(a, c); area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
            if area2 > 1e-12:
                R = A * Bb * C / (2 * area2)
                if R < e["w"] * 0.55: issues.append("%s tight curvature R=%.2f at %d" % (e["name"], R, i)); break
    return issues
