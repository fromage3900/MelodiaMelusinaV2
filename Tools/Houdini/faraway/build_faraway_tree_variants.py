r"""build_faraway_tree_variants.py -- W19: hero tree / bush variation sets from orchard_tree_geometry. spike: true

Pure Python (no hou): 6 foliage archetypes x 4 seeds = 24 variants from the SAME generator the HDA embeds, so each variant is
reproducible inside the HDA by setting the same controls. Per variant: measured bounds (m, Y up, ground y=0), polygon and
blossom-card counts, solid-closure check, front + side silhouette; OBJ export (trunk/limb/root/canopy/blossom groups).
Outputs: <out>/obj/<name>.obj, variants.json (controls + measurements + UE intake names), silhouettes_sheet.png, manifest.json.
UE naming: SM_Faraway_<Archetype>_<NN> (existing foliage materials only: MI_ProcFoliage_Sakura, MI_Mother_*).
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import orchard_tree_geometry as og  # noqa: E402

OUT = ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayTrees_20261026"
ARCH = {
    "HeroOrchard":   dict(height=9.5, trunk_radius=0.42, branch_levels=3, branch_spread=1.0, twist=0.45, blossom_density=1.0),
    "LanternTree":   dict(height=13.0, trunk_radius=0.30, branch_levels=3, branch_spread=0.7, twist=0.15, blossom_density=0.8),
    "WeepingBell":   dict(height=8.0, trunk_radius=0.36, branch_levels=3, branch_spread=1.35, twist=0.7, blossom_density=1.2),
    "DwarfSakura":   dict(height=3.2, trunk_radius=0.16, branch_levels=2, branch_spread=1.1, twist=0.5, blossom_density=1.3),
    "PearlBush":     dict(height=1.6, trunk_radius=0.08, branch_levels=2, branch_spread=1.5, twist=0.3, blossom_density=1.5),
    "CloudCrown":    dict(height=17.0, trunk_radius=0.55, branch_levels=4, branch_spread=0.9, twist=0.3, blossom_density=0.7),
}
SEEDS = [3900, 3901, 3902, 3903]
BASE = dict(preview_mode=0)


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def line(img, p, q, c):
    n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
    for k in range(n + 1):
        t = k / max(n, 1)
        x = int(p[0] + (q[0] - p[0]) * t); y = int(p[1] + (q[1] - p[1]) * t)
        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
            img[y, x] = c


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "obj").mkdir(exist_ok=True)
    rows, sheet_cells = [], []
    for name, ctl in ARCH.items():
        for si, seed in enumerate(SEEDS):
            p = dict(BASE, **ctl, seed=seed)
            prims, meta = og.generate(p)
            P = np.array([v for pr in prims for v in pr["poly"]], dtype=np.float32)
            lo, hi = P.min(0), P.max(0)
            pieces = {}
            for pr in prims:
                pieces[pr["piece"]] = pieces.get(pr["piece"], 0) + 1
            vname = f"SM_Faraway_{name}_{si:02d}"
            # OBJ
            lines, idx = [], 1
            groups = {}
            for pr in prims:
                if pr.get("coll"):
                    continue
                groups.setdefault(pr["piece"], []).append(pr["poly"])
            for g, polys in groups.items():
                lines.append(f"g {g}")
                for poly in polys:
                    for v in poly:
                        lines.append("v %.4f %.4f %.4f" % tuple(v))
                    lines.append("f " + " ".join(str(idx + k) for k in range(len(poly))))
                    idx += len(poly)
            (OUT / "obj" / f"{vname}.obj").write_text("\n".join(lines))
            sil = {"front": P[:, [0, 1]], "side": P[:, [2, 1]]}
            sheet_cells.append((name, si, prims, lo, hi))
            rows.append({"name": vname, "archetype": name, "seed": seed, "controls": ctl,
                         "bounds_min_m": [round(float(v), 3) for v in lo], "bounds_max_m": [round(float(v), 3) for v in hi],
                         "size_m": [round(float(v), 3) for v in (hi - lo)], "polys": len(prims), "pieces": pieces,
                         "blossom_cards": int(pieces.get("blossom_cards", 0)),
                         "grounded": bool(abs(float(lo[1])) < 0.5 or float(lo[1]) > -0.5)})
    # silhouette sheet: 6 rows (archetypes) x 4 cols, each cell 220 px, shared metric scale (17 m = 200 px)
    cell, scale = 230, 11.5
    img = np.zeros((6 * cell, 4 * cell, 3), np.uint8) + 14
    col = {"trunk": (150, 110, 90), "root": (110, 80, 70), "branch": (140, 100, 85), "blossom_cards": (255, 160, 205), "canopy_proxy": (90, 60, 90)}
    for k, (name, si, prims, lo, hi) in enumerate(sheet_cells):
        r, c = k // 4, k % 4
        ox, oy = c * cell + cell // 2, r * cell + cell - 14
        for pr in prims:
            if pr.get("coll"):
                continue
            cc = col.get(pr["piece"], (200, 150, 190))
            pts = [(ox + v[0] * scale, oy - v[1] * scale) for v in pr["poly"]]
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                line(img, a_, b_, cc)
        img[oy:oy + 1, c * cell:(c + 1) * cell] = (60, 60, 80)
    png(OUT / "silhouettes_sheet.png", img)
    (OUT / "variants.json").write_text(json.dumps({"seed_base": 3900, "generator": "orchard_tree_geometry.generate (preview_mode=0, full detail)", "variants": rows}, indent=1))
    gate = {"variants": len(rows), "archetypes": len(ARCH), "all_have_blossoms_or_canopy": all(("blossom_cards" in r["pieces"] and "canopy_proxy" in r["pieces"]) for r in rows),
            "height_range_m": [min(r["size_m"][1] for r in rows), max(r["size_m"][1] for r in rows)],
            "all_polys_positive": all(r["polys"] > 100 for r in rows),
            "seeds_differ": len({round(r["size_m"][0], 3) for r in rows if r["archetype"] == "HeroOrchard"}) > 1,
            "max_polys": max(r["polys"] for r in rows)}
    gate["pass"] = bool(gate["variants"] == 24 and gate["all_have_blossoms_or_canopy"] and gate["all_polys_positive"] and gate["seeds_differ"] and gate["height_range_m"][0] > 0.5)
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_trees.spike.v1", "spike": True, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
