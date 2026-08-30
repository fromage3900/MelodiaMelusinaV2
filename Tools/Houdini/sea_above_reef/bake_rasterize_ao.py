"""PASS H4 — rasterize per-vertex AO into a UV texture (deterministic numpy).

Reads the Houdini AO OBJ (vertex color R = AO) and the UV layout from the v2
prep OBJ, then barycentrically rasterizes vertex AO through each triangle's UV
triangle into a 4096x4096 grayscale PNG. No render engine, no watermark, no
stochastic sampling — exact interpolation of an exact per-vertex field.

Output: bake/T_DressShorewake_AO.png (overwrites the Cycles attempt)
        bake/dress_ao_raster_manifest.json
Run:  python Tools/Houdini/sea_above_reef/bake_rasterize_ao.py
"""

import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

BAKE_DIR = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_lookdev\bake")
AO_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_ao.obj"
UV_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2.obj"
RES = 4096


def load_obj(path):
    verts, uvs, colors, faces, ft_ids = [], [], [], [], []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                c = (float(parts[4]), float(parts[5]), float(parts[6])) if len(parts) >= 7 else None
                verts.append((x, y, z)); colors.append(c)
            elif line.startswith("vt "):
                parts = line.split()
                uvs.append((float(parts[1]), float(parts[2])))
            elif line.startswith("f "):
                idx = []
                for tok in line.split()[1:]:
                    comps = tok.split("/")
                    vi = int(comps[0]) - 1
                    ti = int(comps[1]) - 1 if len(comps) > 1 and comps[1] else vi
                    idx.append((vi, ti))
                faces.append(idx)
    return (np.array(verts, dtype=np.float64), np.array(uvs, dtype=np.float64)
            if uvs else None, colors, faces)


def main():
    ao_v, _, ao_c, ao_f = load_obj(AO_OBJ)
    uv_v, uv_t, _, uv_f = load_obj(UV_OBJ)
    assert len(ao_v) == len(uv_v), "vertex count mismatch between AO and UV OBJs"
    # vertex order matches (same source mesh); carry UV ids from the UV OBJ faces
    ao_vals = np.array([c[0] if c is not None else 1.0 for c in ao_c], dtype=np.float64)

    img = np.ones((RES, RES), dtype=np.float32)
    written = 0
    for tri in uv_f:
        if len(tri) < 3:
            continue
        vids = [t[0] for t in tri]
        tids = [t[1] for t in tri]
        uv0 = np.array(uv_t[tids[0]]); uv1 = np.array(uv_t[tids[1]]); uv2 = np.array(uv_t[tids[2]])
        v0, v1, v2 = ao_vals[vids[0]], ao_vals[vids[1]], ao_vals[vids[2]]
        lo = np.floor(np.min([uv0, uv1, uv2], axis=0) * RES).astype(int)
        hi = np.ceil(np.max([uv0, uv1, uv2], axis=0) * RES).astype(int) + 1
        lo = np.clip(lo, 0, RES); hi = np.clip(hi, 0, RES)
        if hi[0] <= lo[0] or hi[1] <= lo[1]:
            continue
        xs = np.arange(lo[0], hi[0]) + 0.5
        ys = np.arange(lo[1], hi[1]) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        px = gx / RES
        py = gy / RES  # raw UV space (OBJ vt origin bottom-left); flip image at the end
        d = (uv1[1] - uv2[1]) * (uv0[0] - uv2[0]) + (uv2[0] - uv1[0]) * (uv0[1] - uv2[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((uv1[1] - uv2[1]) * (px - uv2[0]) + (uv2[0] - uv1[0]) * (py - uv2[1])) / d
        w1 = ((uv2[1] - uv0[1]) * (px - uv2[0]) + (uv0[0] - uv2[0]) * (py - uv2[1])) / d
        w2 = 1.0 - w0 - w1
        mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not mask.any():
            continue
        vals = w0 * v0 + w1 * v1 + w2 * v2
        img[gy[mask].astype(int), gx[mask].astype(int)] = vals[mask].astype(np.float32)
        written += int(mask.sum())

    # background: white (unoccluded) for untouched texels; flip V for PNG (top-left)
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    out = np.flipud(out)
    Image.fromarray(out, mode="L").save(BAKE_DIR / "T_DressShorewake_AO.png")
    manifest = {
        "schema": "melodia.shorewake_ao_raster.v1",
        "resolution": RES,
        "triangles": len(uv_f),
        "texels_written": written,
        "source_obj": str(AO_OBJ),
        "uv_obj": str(UV_OBJ),
        "note": "exact barycentric interpolation of Houdini VEX vertex AO; background=1.0",
    }
    (BAKE_DIR / "dress_ao_raster_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("RASTER_DONE tris=%d texels=%d" % (len(uv_f), written))


main()
