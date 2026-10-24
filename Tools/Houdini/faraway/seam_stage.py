r"""seam_stage.py -- Faraway Mother global F=0 seam + seam-distance field + gate / arch / bridge placement (hython 22.0.368).

Builds on tile_driver.py (global 250 m tile grid, SilkPeak HDA) and g1_stitch_proof.py (marching squares on a
0.5 m global lattice, welded by lattice-edge keys). For a block of tiles it
  1. cooks the tiles and fuses their heights into one lattice heightfield,
  2. extracts the nodal seam F = 0 of chladni_field.F per tile and over the whole block; the two segment sets must be
     identical (tile-by-tile extraction is continuous across borders); junctions (the 8-way crossing at the origin) are
     reported, not hidden,
  3. samples an EXACT seam-distance field on a coarse lattice (every 4th node, 7.8125 m) and checks it against the
     first-order estimate |F|/|grad F| where that estimate is valid,
  4. places ONE Heart Gate, ONE Frill Arch and ONE Lace Bridge on the seam (rules below), cooks each placed HDA and
     checks grounding,
  5. writes seam_graph.json, seam_distance.npz, placements.json, preview_seam.png under
     Saved/Audit/faraway_seam/<tag>/.
Placement rules: the site straddles the seam (piers on opposite F signs), the passage axis is the seam tangent walked
uphill, the footprint is low-relief, curvature over +-15 m is small, >= 80 m from any junction, >= 60 m from the block
edge, and the three assets are >= 50 m apart. The bridge spans a seam slice of 24-40 m whose two ends are within 1.5 m of
each other in height and whose middle dips the most.

Usage: hython Tools/Houdini/faraway/seam_stage.py [--ix0 -2 --iy0 -2 --nx 3 --ny 3] [--tag NAME]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import chladni_field as cf  # noqa: E402
import g1_stitch_proof as g1  # noqa: E402
import tile_driver as td  # noqa: E402

TILE, DIV, DX = cf.TILE_M, cf.TILE_DIVISIONS, cf.LATTICE_M
DS = 0.5                      # marching-squares lattice (m); 250 m tile = 500 cells
DSAMPLE = 4 * DX              # seam-distance field spacing
OUT_ROOT = ROOT / "Saved" / "Audit" / "faraway_seam"
HDAS = {"gate": ("HDA_Faraway_HeartGate", "HDA_Faraway_HeartGate_1.0.hda"),
        "arch": ("HDA_Faraway_FrillArch", "HDA_Faraway_FrillArch_1.0.hda"),
        "bridge": ("HDA_Faraway_LaceBridge", "HDA_Faraway_LaceBridge_1.0.hda")}
SCALES = {"gate": 4.0, "arch": 2.0}
T0 = time.time()


def log(*a):
    print(f"[SEAM {time.time() - T0:6.1f}s]", *a, flush=True)


def bilinear(MH, X0, Y0, x, y):
    fx = (np.asarray(x, float) - X0) / DX
    fy = (np.asarray(y, float) - Y0) / DX
    i = np.clip(np.floor(fx).astype(int), 0, MH.shape[1] - 2)
    j = np.clip(np.floor(fy).astype(int), 0, MH.shape[0] - 2)
    tx, ty = fx - i, fy - j
    return (MH[j, i] * (1 - tx) * (1 - ty) + MH[j, i + 1] * tx * (1 - ty) + MH[j + 1, i] * (1 - tx) * ty + MH[j + 1, i + 1] * tx * ty)


def extract_block_seam(X0, Y0, nx, ny):
    """Per-tile marching squares welded by edge keys vs one whole-block pass."""
    nt = int(round(TILE / DS))
    pos, key_tiles, all_segs = {}, {}, []
    for r in range(ny):
        for c in range(nx):
            I0, J0 = c * nt, r * nt
            ii, jj = I0 + np.arange(nt + 1), J0 + np.arange(nt + 1)
            F = cf.F(X0 + ii[None, :] * DS + 0 * jj[:, None], Y0 + jj[:, None] * DS + 0 * ii[None, :])
            all_segs += g1.ms_segments(F, I0, J0, X0, Y0, DS, (c, r), pos, key_tiles)
    NX, NY = nx * nt, ny * nt
    ii, jj = np.arange(NX + 1), np.arange(NY + 1)
    Fref = cf.F(X0 + ii[None, :] * DS + 0 * jj[:, None], Y0 + jj[:, None] * DS + 0 * ii[None, :])
    pos_ref, kt_ref = {}, {}
    ref_segs = g1.ms_segments(Fref, 0, 0, X0, Y0, DS, "whole", pos_ref, kt_ref)
    identical = {frozenset(s) for s in all_segs} == {frozenset(s) for s in ref_segs}
    weld_disc = max((pos[k][1] for k in pos), default=0.0)
    lines, adj, anomalies = g1.trace_polylines(all_segs)
    internal_x = {c * nt for c in range(1, nx)}
    internal_y = {r * nt for r in range(1, ny)}
    breaks = 0
    polys = []
    for path in lines:
        pts = np.array([pos[k][0] for k in path])
        closed = path[0] == path[-1] and len(path) > 2
        if not closed:
            for k in (path[0], path[-1]):
                if (k[0] == 1 and k[1] in internal_x) or (k[0] == 0 and k[2] in internal_y):
                    breaks += 1
        seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        polys.append(dict(points=pts, closed=bool(closed), length_m=float(seglen.sum())))
    polys.sort(key=lambda p: -p["length_m"])
    junction_xy = [pos[k][0] for k, v in adj.items() if len(v) > 2]
    return dict(polys=polys, identical=identical, breaks=breaks, junction_xy=np.array(junction_xy).reshape(-1, 2),
                junction_keys=len(junction_xy), welded=sum(1 for v in key_tiles.values() if len(v) > 1), weld_disc=weld_disc,
                segments=len(all_segs))


def seam_distance_field(X0, Y0, nx, ny, polys):
    """Exact distance to the seam polylines on a coarse lattice (chunked point-to-segment)."""
    A, B = [], []
    for p in polys:
        P = p["points"]
        A.append(P[:-1])
        B.append(P[1:])
    A, B = np.concatenate(A), np.concatenate(B)
    n = int(round(nx * TILE / DSAMPLE)) + 1
    m = int(round(ny * TILE / DSAMPLE)) + 1
    xs = X0 + np.arange(n) * DSAMPLE
    ys = Y0 + np.arange(m) * DSAMPLE
    XX, YY = np.meshgrid(xs, ys)
    pts = np.stack([XX.ravel(), YY.ravel()], 1)
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    d = np.empty(len(pts))
    for s in range(0, len(pts), 1500):
        q = pts[s:s + 1500][:, None, :]
        t = np.clip(((q - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
        proj = A[None] + t[..., None] * AB[None]
        d[s:s + 1500] = np.sqrt(((q - proj) ** 2).sum(2)).min(1)
    return xs, ys, d.reshape(m, n)


def asset_extent(hou, kind, scale):
    """Local extent of an HDA default cook: half span (x), depth (z, +), bottom (y min)."""
    typ, f = HDAS[kind]
    hou.hda.installFile(str(ROOT / "hda" / f))
    inst = hou.node("/obj").createNode(typ, f"ext_{kind}")
    inst.cook(force=True)
    geo = inst.node("output0").geometry()
    P = np.array(geo.pointFloatAttribValues("P"), float).reshape(-1, 3)
    inst.destroy()
    return dict(half=float(max(abs(P[:, 0].min()), P[:, 0].max())) * scale, depth=float(max(abs(P[:, 2].min()), P[:, 2].max())) * scale,
                bottom=float(P[:, 1].min()) * scale, height=float(np.ptp(P[:, 1])) * scale,
                pier_h=float(np.ptp(P[:, 1])) * scale)


class Site:
    def __init__(self, polys, junctions, X0, Y0, W, H, MH):
        self.polys, self.junctions, self.X0, self.Y0, self.W, self.H, self.MH = polys, junctions, X0, Y0, W, H, MH

    def arc(self, P):
        return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])

    def clear_of_edge(self, c, margin=60.0):
        return (c[0] - self.X0 >= margin and self.X0 + self.W - c[0] >= margin and c[1] - self.Y0 >= margin and self.Y0 + self.H - c[1] >= margin)

    def junction_clear(self, c, r=80.0):
        return len(self.junctions) == 0 or float(np.hypot(*(self.junctions - c).T).min()) >= r

    def frame(self, P, k):
        """Seam point, tangent (walked uphill), lateral, curvature over +-15 m."""
        arc = self.arc(P)
        a, b = int(np.searchsorted(arc, arc[k] - 6)), int(np.searchsorted(arc, arc[k] + 6))
        tg = P[min(b, len(P) - 1)] - P[max(a, 0)]
        n = np.linalg.norm(tg)
        if n < 1e-9:
            return None
        tg = tg / n
        a2, b2 = int(np.searchsorted(arc, arc[k] - 15)), int(np.searchsorted(arc, arc[k] + 15))
        t1 = P[k] - P[max(a2, 0)]
        t2 = P[min(b2, len(P) - 1)] - P[k]
        if np.linalg.norm(t1) < 1e-9 or np.linalg.norm(t2) < 1e-9:
            return None
        cosang = float(np.clip(np.dot(t1, t2) / (np.linalg.norm(t1) * np.linalg.norm(t2)), -1, 1))
        return tg, math.degrees(math.acos(cosang))

    def best_straddle(self, ext, exclude=(), exclude_r=50.0, arc_window=None):
        best = None
        hs, depth = ext["half"], ext["depth"]
        for pid, p in enumerate(self.polys):
            P = p["points"]
            if len(P) < 40 or p["length_m"] < 60:
                continue
            arc = self.arc(P)
            for k in range(10, len(P) - 10, 4):
                c0 = P[k]
                if not (self.clear_of_edge(c0) and self.junction_clear(c0)):
                    continue
                if any(np.hypot(*(c0 - e)) < exclude_r for e in exclude):
                    continue
                fr = self.frame(P, k)
                if fr is None:
                    continue
                tg, turn = fr
                lat = np.array([tg[1], -tg[0]])
                hf, hb = bilinear(self.MH, self.X0, self.Y0, *(c0 + tg * 20)), bilinear(self.MH, self.X0, self.Y0, *(c0 - tg * 20))
                fpts = np.array([c0 + lat * a_ + tg * b_ for a_ in np.linspace(-hs, hs, 13) for b_ in (-depth, 0.0, depth)])
                fh = bilinear(self.MH, self.X0, self.Y0, fpts[:, 0], fpts[:, 1])
                fl, frr = cf.F(*(c0 + lat * hs)), cf.F(*(c0 - lat * hs))
                straddle = bool((fl > 0) != (frr > 0))
                cost = (fh.max() - fh.min()) + 0.5 * abs(hf - hb) + 0.2 * turn + (0 if straddle else 100.0)
                if arc_window is not None and not (arc_window[0] <= arc[k] <= arc_window[1]):
                    cost += 50.0
                if best is None or cost < best["cost"]:
                    best = dict(cost=float(cost), pid=pid, k=k, c0=c0, tg=tg if hf >= hb else -tg, straddle=straddle, turn=float(turn))
        return best


def ground(site, c, tg, ext, scale_bottom_y):
    lat = np.array([tg[1], -tg[0]])
    fx = np.linspace(-ext["half"], ext["half"], 25)
    fz = np.linspace(-ext["depth"], ext["depth"], 5)
    pts = np.array([c + lat * a + tg * b for a in fx for b in fz])
    h = bilinear(site.MH, site.X0, site.Y0, pts[:, 0], pts[:, 1])
    base = float(h.min())
    bottom = base + scale_bottom_y
    return base, float(h.max() - bottom), float(max(0.0, bottom - h.min()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ix0", type=int, default=-2)
    ap.add_argument("--iy0", type=int, default=-2)
    ap.add_argument("--nx", type=int, default=3)
    ap.add_argument("--ny", type=int, default=3)
    ap.add_argument("--tag", default="g3x3_origin")
    a = ap.parse_args()
    import hou

    out = OUT_ROOT / a.tag
    out.mkdir(parents=True, exist_ok=True)
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hda.installFile(str(ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda"))
    X0, Y0 = a.ix0 * TILE, a.iy0 * TILE
    W, H = a.nx * TILE, a.ny * TILE
    gates, tiles = {}, {}
    log(f"block {a.nx}x{a.ny} from tile ({a.ix0},{a.iy0}): X {X0:.0f}..{X0 + W:.0f}, Y {Y0:.0f}..{Y0 + H:.0f} m")

    # 1. tiles -> one lattice heightfield
    n = DIV
    MH = np.full((a.ny * n + 1, a.nx * n + 1), np.nan)
    for r in range(a.ny):
        for c in range(a.nx):
            t, errs = td.cook_tile(hou, g1.SILK_T, a.ix0 + c, a.iy0 + r, {})
            if t is None:
                log("tile cook failed", errs)
                return 1
            MH[r * n:r * n + n + 1, c * n:c * n + n + 1] = t["H"]
            tiles[(a.ix0 + c, a.iy0 + r)] = t
    log(f"heightfield {MH.shape[1]}x{MH.shape[0]}, {np.nanmin(MH):.1f}..{np.nanmax(MH):.1f} m, nan={int(np.isnan(MH).sum())}")

    # 2. seam
    sm = extract_block_seam(X0, Y0, a.nx, a.ny)
    total = sum(p["length_m"] for p in sm["polys"])
    log(f"seam: {len(sm['polys'])} polylines, {total:.0f} m, {sm['segments']} segments, junction keys {sm['junction_keys']}, "
        f"welded border keys {sm['welded']}, unintended breaks {sm['breaks']}, tile==whole {sm['identical']}")
    allpts = np.concatenate([p["points"] for p in sm["polys"]])
    Fv = np.abs(cf.F(allpts[:, 0], allpts[:, 1]))
    gx, gy = cf.grad(allpts[:, 0], allpts[:, 1])
    gm = np.hypot(gx, gy)
    valid = gm > 1e-4
    dev = Fv[valid] / gm[valid]
    # multi-way crossings sit where grad F = 0 on the nodal set (the origin's 8-way crossing); a single marching-squares
    # cell can hold them without any degree-3 edge key, so find them from the field itself
    crit = allpts[gm < 3e-4]
    if len(crit):
        cells = {tuple(np.round(q / 40.0).astype(int)) for q in crit}
        crit_xy = np.array([np.mean([q for q in crit if tuple(np.round(q / 40.0).astype(int)) == c_], axis=0) for c_ in cells])
        sm["junction_xy"] = np.vstack([sm["junction_xy"], crit_xy]) if len(sm["junction_xy"]) else crit_xy
        log(f"critical points on the seam (grad F ~ 0): {len(crit_xy)} cluster(s) at {np.round(crit_xy, 0).tolist()[:4]}")
    gates["S1_seam_continuous"] = dict(status="PASS" if sm["identical"] and sm["breaks"] == 0 and sm["welded"] > 0 else "FAIL",
        polylines=len(sm["polys"]), total_length_m=total, welded_border_keys=sm["welded"], unintended_breaks=sm["breaks"],
        tile_vs_whole_block_segments_identical=sm["identical"], junction_keys=sm["junction_keys"],
        detail="marching squares on a 0.5 m global lattice, per tile, welded by shared edge keys; junction keys are the real "
               "multi-way crossings of the nodal set (8-way at the origin), not breaks")
    gates["S2_seam_on_nodal_set"] = dict(status="PASS" if float(dev.max()) <= 0.1 else "FAIL", points=int(len(allpts)),
        points_with_grad_above_1e4=int(valid.sum()), max_first_order_offset_m=float(dev.max()), limit_m=0.1,
        detail="|F|/|grad F| at every seam vertex (first-order distance to F=0), vertices near grad F = 0 excluded")

    # 3. seam distance field
    xs, ys, D = seam_distance_field(X0, Y0, a.nx, a.ny, sm["polys"])
    XXs, YYs = np.meshgrid(xs, ys)
    Fs = cf.F(XXs, YYs)
    gxs, gys = cf.grad(XXs, YYs)
    gms = np.hypot(gxs, gys)
    est = np.abs(Fs) / np.maximum(gms, 1e-12)
    sel = (gms > 1.5e-3) & (D < 60.0) & (D > 3.0)
    rel = np.abs(est[sel] - D[sel]) / D[sel]
    gates["S3_seam_distance_field"] = dict(status="PASS" if sel.sum() > 50 and float(np.median(rel)) <= 0.10 else "FAIL",
        samples=int(D.size), spacing_m=DSAMPLE, compared=int(sel.sum()), median_rel_err_vs_first_order=float(np.median(rel)) if sel.sum() else None,
        p90_rel_err=float(np.percentile(rel, 90)) if sel.sum() else None, limit_median=0.10,
        detail="exact point-to-polyline distance vs |F|/|grad F| where the first-order estimate is valid (|grad F| > 1.5e-3 /m, 3 m < d < 60 m)")
    np.savez_compressed(out / "seam_distance.npz", x=xs, y=ys, distance_m=D.astype(np.float32), signed_F=Fs.astype(np.float32),
                        spacing_m=DSAMPLE, block_min=[X0, Y0])

    # 4. placement
    site = Site(sm["polys"], sm["junction_xy"], X0, Y0, W, H, MH)
    ext = {k: asset_extent(hou, k, SCALES.get(k, 1.0)) for k in ("gate", "arch")}
    placements, taken = {}, []

    def place(kind, **kw):
        e = ext[kind]
        b = site.best_straddle(e, exclude=taken, **kw)
        if b is None:
            return None
        P = site.polys[b["pid"]]["points"]
        tg, c0 = b["tg"], b["c0"]
        yaw = math.degrees(math.atan2(tg[0], tg[1]))
        base, embed, flt = ground(site, c0, tg, e, e["bottom"] - 0.0)
        lat = np.array([tg[1], -tg[0]])
        arc = site.arc(P)
        # independent tangent (+-2 m) for the alignment check
        a2, b2 = int(np.searchsorted(arc, arc[b["k"]] - 2)), int(np.searchsorted(arc, arc[b["k"]] + 2))
        ti = P[min(b2, len(P) - 1)] - P[a2]
        ti /= np.linalg.norm(ti)
        ang = math.degrees(math.acos(min(1.0, abs(float(np.dot(ti, tg))))))
        taken.append(c0)
        return dict(hda=HDAS[kind][1], node_type=HDAS[kind][0], world_XY=[float(c0[0]), float(c0[1])],
                    houdini_translate=[float(c0[0]), base - e["bottom"] * 0.0, float(c0[1])], houdini_rotate_y_deg=yaw,
                    uniform_scale=SCALES[kind], seam_polyline=int(b["pid"]), seam_arc_m=float(arc[b["k"]]), straddles_seam=b["straddle"],
                    tangent_align_deg=ang, turn_deg_over_30m=b["turn"], base_height_m=base, max_embed_m=embed, float_gap_m=flt,
                    embed_limit_m=e["pier_h"] * 0.25 if kind == "arch" else 3.0 * SCALES[kind], local_extent=e, site_cost=b["cost"])

    placements["gate"] = place("gate")
    g = placements["gate"]
    if g is None:
        log("no gate site")
        return 1
    placements["arch"] = place("arch", arc_window=(g["seam_arc_m"] - 220, g["seam_arc_m"] + 220)) if True else None

    # bridge: slice of a seam polyline with level ends and a dip between
    best_b = None
    for pid, p in enumerate(site.polys):
        P = p["points"]
        if len(P) < 60 or p["length_m"] < 60:
            continue
        arc = site.arc(P)
        for s0 in np.arange(10.0, arc[-1] - 45.0, 5.0):
            for L in (24.0, 32.0, 40.0):
                if s0 + L > arc[-1] - 5:
                    continue
                ss = np.linspace(s0, s0 + L, 17)
                sl = np.stack([np.interp(ss, arc, P[:, 0]), np.interp(ss, arc, P[:, 1])], 1)
                if not all(site.clear_of_edge(q, 40.0) and site.junction_clear(q, 60.0) for q in sl[[0, 8, -1]]):
                    continue
                if any(np.hypot(*(sl[8] - e)) < 50.0 for e in taken):
                    continue
                hh = bilinear(MH, X0, Y0, sl[:, 0], sl[:, 1])
                if abs(hh[0] - hh[-1]) > 1.5:
                    continue
                dip = float(0.5 * (hh[0] + hh[-1]) - hh.min())
                chord = np.linalg.norm(sl[-1] - sl[0])
                if L / max(chord, 1e-6) > 1.05:
                    continue                                              # keep the slice nearly straight (no switchback)
                if best_b is None or dip > best_b["dip"]:
                    best_b = dict(dip=dip, pid=pid, s0=float(s0), L=float(L), pts=sl, h=hh)
    bridge = None
    if best_b is not None:
        sl, hh = best_b["pts"], best_b["h"]
        bridge = dict(hda=HDAS["bridge"][1], node_type=HDAS["bridge"][0], seam_polyline=int(best_b["pid"]), seam_arc_m=best_b["s0"],
                      length_m=best_b["L"], dip_m=best_b["dip"], deck_height_m=float(hh[0]), end_height_delta_m=float(abs(hh[0] - hh[-1])),
                      curve_input_world=[[float(x), float(hh[0]), float(y)] for x, y in sl], houdini_translate=[0.0, 0.0, 0.0],
                      note="curve is in world metres (Houdini x=X, y=deck height, z=Y); the HDA uses X/Z of the curve and the first point's Y")
        taken.append(sl[8])
    placements["bridge"] = bridge

    # 5. cook each placed asset at its placement and check it
    cook_notes = {}
    for kind, pl in placements.items():
        if pl is None:
            cook_notes[kind] = "no site"
            continue
        typ, f = HDAS[kind]
        hou.hda.installFile(str(ROOT / "hda" / f))
        inst = hou.node("/obj").createNode(typ, f"placed_{kind}")
        if kind == "bridge":
            cg = hou.node("/obj").createNode("geo", "bridge_curve")
            for ch in cg.children():
                ch.destroy()
            py = cg.createNode("python", "mk")
            py.parm("python").set("import hou\ng=hou.pwd().geometry()\npts=" + repr([tuple(q) for q in pl["curve_input_world"]]) +
                                  "\nps=[g.createPoint() for _ in pts]\nfor p,q in zip(ps,pts): p.setPosition(hou.Vector3(q))\n"
                                  "pr=g.createPolygon(); pr.setIsClosed(False)\nfor p in ps: pr.addVertex(p)\n")
            py.setDisplayFlag(True)
            py.setRenderFlag(True)
            inst.setInput(0, cg)
        inst.cook(force=True)
        errs = [str(e)[:100] for c in [inst, *inst.allSubChildren()] for e in c.errors()]
        geo = inst.node("output0").geometry()
        if geo is None or errs:
            cook_notes[kind] = f"cook failed {errs}"
            continue
        P = np.array(geo.pointFloatAttribValues("P"), float).reshape(-1, 3)
        info = dict(points=len(P), bbox_min=P.min(0).round(2).tolist(), bbox_max=P.max(0).round(2).tolist())
        if kind == "bridge":
            info["from_input"] = int(geo.intAttribValue("from_input")) if geo.findGlobalAttrib("from_input") else None
            xy = P[:, [0, 2]]
            ends_ok = (np.abs(xy[:, 0] - pl["curve_input_world"][0][0]).min() < 6 and np.abs(xy[:, 0] - pl["curve_input_world"][-1][0]).min() < 6)
            info["spans_slice_ends"] = bool(ends_ok)
        cook_notes[kind] = info
        pl["cook"] = info
        log(f"{kind}: cooked {info['points']} pts bbox {info['bbox_min']} .. {info['bbox_max']}")

    # gates S4 / S5 / S6
    gp = placements["gate"]
    gates["S4_gate_on_seam"] = dict(status="PASS" if gp["straddles_seam"] and gp["tangent_align_deg"] <= 2.0 and gp["float_gap_m"] <= 1e-6
                                    and gp["max_embed_m"] <= gp["embed_limit_m"] else "FAIL",
        straddles_seam=gp["straddles_seam"], tangent_align_deg=gp["tangent_align_deg"], float_gap_m=gp["float_gap_m"],
        max_embed_m=gp["max_embed_m"], embed_limit_m=gp["embed_limit_m"], world_XY=gp["world_XY"], seam_arc_m=gp["seam_arc_m"],
        detail="piers on opposite F signs, passage axis along the seam tangent, base = lowest terrain under the footprint; "
               "embed limit = pier height 3 m x scale (G1 rule)")
    ap_, bp_ = placements.get("arch"), placements.get("bridge")
    arch_ok = ap_ is not None and ap_["straddles_seam"] and ap_["float_gap_m"] <= 1e-6 and ap_["max_embed_m"] <= max(ap_["embed_limit_m"], 1.0)
    bridge_ok = bp_ is not None and bp_["end_height_delta_m"] <= 1.5 and bp_["dip_m"] >= 0.5 and isinstance(bp_.get("cook"), dict) \
        and bp_["cook"].get("from_input") == 1
    dists = []
    pts_pl = [np.array(gp["world_XY"])] + ([np.array(ap_["world_XY"])] if ap_ else []) + (
        [np.array(bp_["curve_input_world"][len(bp_["curve_input_world"]) // 2])[[0, 2]]] if bp_ else [])
    for i in range(len(pts_pl)):
        for j in range(i + 1, len(pts_pl)):
            dists.append(float(np.hypot(*(pts_pl[i] - pts_pl[j]))))
    gates["S5_arch_and_bridge_on_seam"] = dict(status="PASS" if arch_ok and bridge_ok and (not dists or min(dists) >= 50.0) else "FAIL",
        arch=None if ap_ is None else {k: ap_[k] for k in ("world_XY", "seam_arc_m", "straddles_seam", "float_gap_m", "max_embed_m", "embed_limit_m", "tangent_align_deg")},
        bridge=None if bp_ is None else {k: bp_[k] for k in ("seam_arc_m", "length_m", "dip_m", "deck_height_m", "end_height_delta_m")},
        min_separation_m=min(dists) if dists else None, separation_limit_m=50.0)
    gates["S6_placed_hdas_cook"] = dict(status="PASS" if all(isinstance(v, dict) for v in cook_notes.values()) else "FAIL", detail=cook_notes)

    # outputs
    seam_doc = dict(schema="melodia.faraway_seam_graph.v1", block=dict(ix0=a.ix0, iy0=a.iy0, nx=a.nx, ny=a.ny, min=[X0, Y0], size=[W, H]),
                    method="marching squares F=0 on a 0.5 m global lattice, per 250 m tile, welded by edge keys",
                    field="chladni_field.F (3,5), u=(X+4000)/8000", frame="world X,Y metres (Houdini x,z)",
                    polylines=[dict(id=i, closed=p["closed"], length_m=p["length_m"], n_points=int(len(p["points"])),
                                    points=np.round(p["points"], 3).tolist()) for i, p in enumerate(sm["polys"])],
                    junctions_xy=np.round(sm["junction_xy"], 2).tolist())
    (out / "seam_graph.json").write_text(json.dumps(seam_doc))
    (out / "placements.json").write_text(json.dumps(dict(schema="melodia.faraway_placements.v1", source_commit=td.git_head(), frame="Houdini: x=X, y=height, z=Y; yaw about +Y; local +Z = seam tangent",
                                                         placements=placements), indent=1, default=float))

    # preview: relief + seam + placements
    img = td.relief(tiles, a.ix0, a.iy0, a.nx, a.ny)
    Himg = img.shape[0]
    px = lambda X: (X - X0) / DX * 4.0
    py_ = lambda Y: (Himg - 1) - (Y - Y0) / DX * 4.0

    def dot(x, y, r, col):
        x, y = int(round(px(x))), int(round(py_(y)))
        img[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1] = col

    for p in sm["polys"]:
        for q in p["points"][::2]:
            dot(q[0], q[1], 1, (250, 247, 255))
    if bp_:
        for x, _, y in bp_["curve_input_world"]:
            dot(x, y, 3, (90, 140, 220))
    if ap_:
        dot(*ap_["world_XY"], 9, (214, 108, 150))
    dot(*gp["world_XY"], 12, (214, 168, 70))
    td.png(out / "preview_seam.png", img)

    overall = "PASS" if all(g_["status"] == "PASS" for g_ in gates.values()) else "FAIL"
    (out / "seam_stage_report.json").write_text(json.dumps(dict(overall=overall, tag=a.tag, gates=gates, elapsed_s=round(time.time() - T0, 1)), indent=1, default=float))
    for k, g_ in gates.items():
        log(f"{g_['status']:7s} {k}")
    log(f"overall={overall} out={out}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
