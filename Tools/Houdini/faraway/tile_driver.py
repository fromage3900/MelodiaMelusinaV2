r"""tile_driver.py -- Faraway Mother NxM tile driver (hython 22.0.368, Houdini-only, no UE).

Generalises the hard-coded 2x2 of g1_stitch_proof.py into a driver over the GLOBAL tile grid:
  tile (i, j) has its min corner at world (i*250, j*250) m, so every origin sits on the global 1.953125 m lattice
  (250 = 128 * 1.953125) and the 8 km plate (+-4000 m) is exactly 32 x 32 tiles, i = j = -16 .. 15.
Cooks each tile through the SilkPeak HDA (analytic point normals), and per tile writes
  tile_i{i}_j{j}.bgeo.sc, and a manifest row: tile id, origin, size, divisions, HDA sha256 + parms, content hash
  (rounded positions + normals ordered by lattice index, independent of point order), file sha256, counts, height
  range, and a hash for each of the four border edges.
Gates (stop at the first FAIL is the caller's choice; all are reported):
  T1 every tile origin is a multiple of 250 m and every vertex lies on the global lattice
  T2 every tile cooks without errors with (divisions+1)^2 points
  T3 every shared border: positions <= 0.01 m, normal dot >= 0.98 (unchanged limit), edge hashes equal
  T4 determinism: a fresh re-cook of the first tile has the identical content hash
Writes Saved/Audit/faraway_tiles/<tag>/tile_manifest.json, tiles/, preview_relief.png.

Usage: hython Tools/Houdini/faraway/tile_driver.py [--ix0 -2 --iy0 -2 --nx 3 --ny 3] [--tag NAME] [--hda PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import zlib
import struct
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import chladni_field as cf  # noqa: E402
import g1_stitch_proof as g1  # noqa: E402

TILE, DIV, DX = cf.TILE_M, cf.TILE_DIVISIONS, cf.LATTICE_M
SILK_T = g1.SILK_T
POS_LIMIT_M = 0.01
NORMAL_LIMIT = 0.98          # the G1.07 limit, unchanged
OUT_ROOT = ROOT / "Saved" / "Audit" / "faraway_tiles"
T0 = time.time()


def log(*a):
    print(f"[TILES {time.time() - T0:6.1f}s]", *a, flush=True)


def content_hash(H, N, Pg):
    """Identity of a tile's geometry: positions to 0.1 mm and normals to 1e-5, ordered by lattice index."""
    h = hashlib.sha256()
    h.update(np.round(Pg * 1e4).astype(np.int64).tobytes())
    h.update(np.round(N * 1e5).astype(np.int64).tobytes())
    return h.hexdigest()


def edge_hash(Pg_edge, N_edge):
    h = hashlib.sha256()
    h.update(np.round(Pg_edge * 1e4).astype(np.int64).tobytes())
    h.update(np.round(N_edge * 1e5).astype(np.int64).tobytes())
    return h.hexdigest()


def cook_tile(hou, hda_type, i, j, parms):
    tx, ty = i * TILE, j * TILE
    inst = hou.node("/obj").createNode(hda_type, f"tile_i{i}_j{j}")
    inst.parm("tile_x").set(tx)
    inst.parm("tile_y").set(ty)
    inst.parm("tile_size").set(TILE)
    inst.parm("divisions").set(DIV)
    for k, v in parms.items():
        inst.parm(k).set(v)
    inst.cook(force=True)
    errs = list(inst.errors()) + [e for c in inst.allSubChildren() for e in c.errors()]
    geo = inst.node("output0").geometry()
    if geo is None or errs:
        return None, errs
    P, pv, vN, pn = g1.extract(geo)
    Np = g1.point_normals(len(P), pv, vN)
    ix = np.rint((P[:, 0] - tx) / DX).astype(int)
    iz = np.rint((P[:, 2] - ty) / DX).astype(int)
    n = DIV + 1
    H = np.full((n, n), np.nan)
    N = np.zeros((n, n, 3))
    Pg = np.zeros((n, n, 3))
    H[iz, ix] = P[:, 1]
    N[iz, ix] = Np
    Pg[iz, ix] = P
    snap_local = float(max(np.abs(P[:, 0] - (tx + ix * DX)).max(), np.abs(P[:, 2] - (ty + iz * DX)).max()))
    snap_global = float(max(np.abs(P[:, 0] / DX - np.rint(P[:, 0] / DX)).max(),
                            np.abs(P[:, 2] / DX - np.rint(P[:, 2] / DX)).max()) * DX)
    return dict(inst=inst, geo=geo, H=H, N=N, Pg=Pg, tx=tx, ty=ty, npts=len(P), nprims=len(pn),
                snap_local=snap_local, snap_global=snap_global), errs


def png(path, rgb):
    """Minimal PNG writer (no PIL: PIL warnings segfault hython 22.0.368)."""
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def relief(tiles, ix0, iy0, nx, ny, scale=4):
    n = DIV
    Hm = np.zeros((ny * n + 1, nx * n + 1))
    Nm = np.zeros((ny * n + 1, nx * n + 1, 3))
    for (i, j), t in tiles.items():
        c, r = i - ix0, j - iy0
        Hm[r * n:r * n + n + 1, c * n:c * n + n + 1] = t["H"]
        Nm[r * n:r * n + n + 1, c * n:c * n + n + 1] = t["N"]
    L = np.array([-0.5, 0.8, 0.35])
    L /= np.linalg.norm(L)
    shade = np.clip(Nm @ L, 0, 1)
    shade = 0.35 + 0.65 * shade                                   # soft: never black
    t = (Hm - Hm.min()) / max(np.ptp(Hm), 1e-6)
    cream, lilac = np.array([240, 228, 214.0]), np.array([196, 184, 226.0])   # pearl/cream -> lilac
    base = cream[None, None, :] * (1 - t[..., None]) + lilac[None, None, :] * t[..., None]
    img = np.clip(base * shade[..., None], 0, 255)
    img = np.flipud(img)                                          # +Y (world north) up
    img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1).astype(np.uint8)
    for c in range(1, nx):                                        # faint tile borders
        img[:, c * n * scale - 1:c * n * scale + 1] = (img[:, c * n * scale - 1:c * n * scale + 1] * 0.82).astype(np.uint8)
    for r in range(1, ny):
        img[r * n * scale - 1:r * n * scale + 1, :] = (img[r * n * scale - 1:r * n * scale + 1, :] * 0.82).astype(np.uint8)
    return img


def git_head():
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ix0", type=int, default=-2)
    ap.add_argument("--iy0", type=int, default=-2)
    ap.add_argument("--nx", type=int, default=3)
    ap.add_argument("--ny", type=int, default=3)
    ap.add_argument("--tag", default="g3x3_origin")
    ap.add_argument("--hda", type=Path, default=ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda")
    ap.add_argument("--no-bgeo", action="store_true")
    a = ap.parse_args()
    import hou

    out = OUT_ROOT / a.tag
    (out / "tiles").mkdir(parents=True, exist_ok=True)
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hda.installFile(str(a.hda))
    ids = [(a.ix0 + c, a.iy0 + r) for r in range(a.ny) for c in range(a.nx)]
    if any(not (-16 <= i <= 15 and -16 <= j <= 15) for i, j in ids):
        log("tile index outside the 8 km plate (-16..15)")
        return 2
    gates, rows, tiles = {}, [], {}
    log(f"Houdini {hou.applicationVersionString()} licence {hou.licenseCategory()} | grid {a.nx}x{a.ny} from "
        f"({a.ix0},{a.iy0}) = X {a.ix0 * TILE:.0f}..{(a.ix0 + a.nx) * TILE:.0f} m, Y {a.iy0 * TILE:.0f}..{(a.iy0 + a.ny) * TILE:.0f} m")

    cook_fail = []
    hda_parms = None
    for (i, j) in ids:
        t, errs = cook_tile(hou, SILK_T, i, j, {})
        if t is None:
            cook_fail.append((i, j, [str(e)[:120] for e in errs]))
            continue
        if hda_parms is None:
            hda_parms = {p.name(): p.eval() for p in t["inst"].parms() if p.name() not in ("tile_x", "tile_y", "tile_size", "divisions")
                         and not p.name().startswith(("folder", "stdswitcher", "sep"))}
        t["chash"] = content_hash(t["H"], t["N"], t["Pg"])
        t["edges"] = {"W": edge_hash(t["Pg"][:, 0], t["N"][:, 0]), "E": edge_hash(t["Pg"][:, DIV], t["N"][:, DIV]),
                      "S": edge_hash(t["Pg"][0, :], t["N"][0, :]), "N": edge_hash(t["Pg"][DIV, :], t["N"][DIV, :])}
        tiles[(i, j)] = t
        fh, fsize = None, None
        if not a.no_bgeo:
            f = out / "tiles" / f"tile_i{i}_j{j}.bgeo.sc"
            t["geo"].saveToFile(str(f))
            fh, fsize = g1.sha256(f), f.stat().st_size
        rows.append(dict(
            tile=[i, j], id=f"i{i}_j{j}", origin_m=[t["tx"], t["ty"]], size_m=TILE, divisions=DIV, cell_m=DX,
            points=t["npts"], prims=t["nprims"], height_m=[round(float(np.nanmin(t["H"])), 3), round(float(np.nanmax(t["H"])), 3)],
            content_sha256=t["chash"], edge_sha256=t["edges"],
            file=(f"tiles/tile_i{i}_j{j}.bgeo.sc" if fh else None), file_sha256=fh, file_bytes=fsize))
        log(f"tile i{i} j{j}: {t['npts']} pts / {t['nprims']} prims, height {rows[-1]['height_m'][0]}..{rows[-1]['height_m'][1]} m, "
            f"content {t['chash'][:12]}")

    # T1 lattice
    aligned = all(abs(i * TILE / DX - round(i * TILE / DX)) < 1e-9 for i, _ in ids) and all(cf.on_lattice(j * TILE) for _, j in ids)
    worst_snap = max((t["snap_global"] for t in tiles.values()), default=float("nan"))
    gates["T1_lattice_aligned"] = dict(status="PASS" if aligned and worst_snap < 1e-3 else "FAIL",
                                       worst_global_lattice_snap_m=worst_snap, cell_m=DX,
                                       detail="every tile origin = k*250 m and every vertex = integer * 1.953125 m in world metres")
    # T2 cook
    ok_cook = not cook_fail and len(tiles) == len(ids) and all(t["npts"] == (DIV + 1) ** 2 and not np.isnan(t["H"]).any() for t in tiles.values())
    gates["T2_tiles_cook"] = dict(status="PASS" if ok_cook else "FAIL", tiles=len(tiles), expected=len(ids), errors=cook_fail)

    # T3 shared borders
    pairs, worst_pos, min_dot, hash_mismatch = [], 0.0, 1.0, 0
    for (i, j), A in tiles.items():
        for (di, dj, ea, eb) in ((1, 0, "E", "W"), (0, 1, "N", "S")):
            B = tiles.get((i + di, j + dj))
            if B is None:
                continue
            if ea == "E":
                pa, pb, na, nb = A["Pg"][:, DIV], B["Pg"][:, 0], A["N"][:, DIV], B["N"][:, 0]
            else:
                pa, pb, na, nb = A["Pg"][DIV, :], B["Pg"][0, :], A["N"][DIV, :], B["N"][0, :]
            dpos = float(np.abs(pa - pb).max())
            dot = float(np.einsum("ij,ij->i", na, nb).min())
            same = A["edges"][ea] == B["edges"][eb]
            worst_pos, min_dot, hash_mismatch = max(worst_pos, dpos), min(min_dot, dot), hash_mismatch + (0 if same else 1)
            pairs.append(dict(a=f"i{i}_j{j}", b=f"i{i + di}_j{j + dj}", edge=f"{ea}|{eb}", max_dpos_m=dpos, min_normal_dot=dot, edge_hash_equal=same))
    gates["T3_shared_borders"] = dict(
        status="PASS" if pairs and worst_pos <= POS_LIMIT_M and min_dot >= NORMAL_LIMIT and hash_mismatch == 0 else ("BLOCKED" if not pairs else "FAIL"),
        shared_borders=len(pairs), worst_position_delta_m=worst_pos, position_limit_m=POS_LIMIT_M,
        min_normal_dot=min_dot, normal_limit=NORMAL_LIMIT, edge_hash_mismatches=hash_mismatch, pairs=pairs)

    # T4 determinism: a fresh instance of the first tile must give the identical content hash
    if tiles:
        i0, j0 = next(iter(tiles))
        again, _ = cook_tile(hou, SILK_T, i0, j0, {})
        h2 = content_hash(again["H"], again["N"], again["Pg"]) if again else None
        gates["T4_deterministic_recook"] = dict(status="PASS" if h2 == tiles[(i0, j0)]["chash"] else "FAIL",
                                                tile=[i0, j0], first=tiles[(i0, j0)]["chash"][:16], second=(h2 or "none")[:16])

    if tiles:
        png(out / "preview_relief.png", relief(tiles, a.ix0, a.iy0, a.nx, a.ny))
    peak, cur = g1.mem_mb()
    overall = "PASS" if gates and all(g["status"] == "PASS" for g in gates.values()) else "FAIL"
    manifest = dict(
        schema="melodia.faraway_tile_manifest.v1", overall=overall, tag=a.tag, source_commit=git_head(),
        houdini=hou.applicationVersionString(), licence=str(hou.licenseCategory()),
        frame=dict(units="metres", world="X,Y m; Houdini x=X, y=height, z=Y", plate_m=cf.PLATE_M, half_m=cf.HALF_M,
                   uu_per_m=100, uv="u=(X+4000)/8000, v=(Y+4000)/8000"),
        field=dict(mode=[cf.N_MODE, cf.M_MODE], module="Tools/Houdini/faraway/chladni_field.py", seam_threshold=cf.SEAM_THRESHOLD),
        grid=dict(ix0=a.ix0, iy0=a.iy0, nx=a.nx, ny=a.ny, tile_m=TILE, divisions=DIV, cell_m=DX,
                  origin_rule="origin = (i*250, j*250) m", plate_tiles="32x32 (i,j = -16..15)"),
        hda=dict(path=str(a.hda.relative_to(ROOT)).replace("\\", "/"), type=SILK_T, sha256=g1.sha256(a.hda), parms=hda_parms),
        seeds=dict(hda_seed=(hda_parms or {}).get("seed"), note="HDA seed jitters the peak anchors only; the Chladni field is seed-free"),
        gates=gates, tiles=rows, elapsed_s=round(time.time() - T0, 1), peak_working_set_mb=round(peak, 0))
    (out / "tile_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    for k, g in gates.items():
        log(f"{g['status']:7s} {k}")
    log(f"overall={overall} manifest={out / 'tile_manifest.json'} peakWS={peak:.0f} MB")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
