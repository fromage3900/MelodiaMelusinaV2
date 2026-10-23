"""Volumetric dreamscape — VDB volumes for UE Sparse Volume Textures.

Probe-verified 2026-08-28: Apprentice writes .vdb via File SOP (File SOP
"write" mode). UE 5.3+ imports .vdb as Sparse Volume Textures — material maps
the grid as density/mask. Three volumes for the Sea Above reef (metres):

  VOL_GodRays.vdb      3 slanted shafts falling from the sea above (~120 m tall)
  VOL_GhostFog.vdb     the leviathan's ghost-fog, an ellipsoid hugging its
                       ribcage bounds (centred on the SM_Leviathan rest area)
  VOL_NebulaVeil.vdb   a broad soft veil above the jellyfish bell (dream sky)

Run:  hython Tools/Houdini/sea_above_reef/build_volumetrics.py
"""

import json
from pathlib import Path

import hou

OUT_DIR = Path(__file__).resolve().parents[3] / "Saved" / "Audit" / "sea_above" / "volumes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHAFTS_CODE = r"""
import hou, math
node = hou.pwd()
geo = node.geometry()
# three tapered shaft quads (open shells) -> vdbfrompolygons SDF downstream
for k, (x, z, w, tilt) in enumerate(((-30, 8, 7, 0.35), (5, -6, 9, 0.15),
                                     (34, 12, 6, -0.28))):
    top_w, bot_w = w, w * 1.8
    h = 120.0
    top = hou.Vector3(x + tilt * h, 60.0, z)
    for sx in (-1.0, 1.0):
        pass
    pts = []
    for (tx, tz, bw) in ((-top_w, 0, bot_w), (top_w, 0, bot_w)):
        row = []
        for (fx, fz) in ((-bw, 0), (bw, 0)):
            p = geo.createPoint()
            row.append(p)
        row = None
        break
    # build as two triangles-worth of quads: a simple 4-point slanted sheet
    corners = [V(top[0] - top_w, 60.0, top[2]),
               V(top[0] + top_w, 60.0, top[2]),
               V(x + top_w * 1.8 + tilt * h * 0.2, 60.0 - h, z + top_w * 1.8),
               V(x - top_w * 1.8 + tilt * h * 0.2, 60.0 - h, z - top_w * 1.8)]
    f = geo.createPolygon()
    for c in corners:
        p = geo.createPoint()
        p.setPosition(c)
        f.addVertex(p)
    _ = sx
"""

SHAFTS_CODE = r"""
import hou, math
node = hou.pwd()
geo = node.geometry()
V = hou.Vector3
# three slanted shaft sheets (open quads); SDF of thin shells reads as rays
for (x, z, w, tilt) in ((-30, 8, 7, 0.35), (5, -6, 9, 0.15), (34, 12, 6, -0.28)):
    h = 120.0
    tw = w
    bw = w * 1.8
    corners = [V(x - tw, 60.0, z),
               V(x + tw, 60.0, z),
               V(x + bw + tilt * h * 0.2, 60.0 - h, z + bw * 0.6),
               V(x - bw + tilt * h * 0.2, 60.0 - h, z - bw * 0.6)]
    f = geo.createPolygon()
    for c in corners:
        p = geo.createPoint()
        p.setPosition(c)
        f.addVertex(p)
"""


def _write_vdb(obj, geo_name, out_path, parms=None):
    for old in [n for n in obj.children() if n.name() == geo_name]:
        old.destroy()
    g = obj.createNode("geo", geo_name, run_init_scripts=True)
    return g


def main():
    obj = hou.node("/obj")
    results = []

    # --- god rays ---------------------------------------------------------------
    g = _write_vdb(obj, "VOL_GodRays", None)
    py = g.createNode("python", "gen_shafts")
    py.parm("python").set(SHAFTS_CODE)
    py.cook(force=True)
    vdb = g.createNode("vdbfrompolygons", "to_sdf")
    setp_ok = True
    try:
        vdb.parm("voxelsize").set(1.5)
    except Exception:
        pass
    vdb.setInput(0, py)
    vdb.cook(force=True)
    err = " ".join(str(vdb.errors()).split()) if vdb.errors() else ""
    print(f"[volumes] godrays sdf: {err or 'OK'}")
    w = g.createNode("file", "writer")
    w.parm("file").set(str(OUT_DIR / "VOL_GodRays.vdb"))
    w.parm("filemode").set("write")
    w.setInput(0, vdb)
    w.cook(force=True)
    results.append(("VOL_GodRays.vdb", (OUT_DIR / "VOL_GodRays.vdb").exists()))
    g.destroy()

    # --- ghost fog + nebula veil (ellipsoid SDF shells) --------------------------
    ELLIPSOID = r"""
import hou, math
node = hou.pwd()
geo = node.geometry()
V = hou.Vector3
CENTER = __CENTER__
RAD = __RAD__
base = V(*CENTER)
SEG, RINGS = 32, 20
rows = []
for j in range(RINGS + 1):
    phi = j / RINGS * math.pi
    row = []
    for i in range(SEG):
        th = i / SEG * 2.0 * math.pi
        p = geo.createPoint()
        p.setPosition(base + V(RAD[0] * math.sin(phi) * math.cos(th),
                               RAD[1] * math.cos(phi),
                               RAD[2] * math.sin(phi) * math.sin(th)))
        row.append(p)
    rows.append(row)
for j in range(RINGS):
    for i in range(SEG):
        f = geo.createPolygon()
        for q in (rows[j][i], rows[j][(i + 1) % SEG],
                  rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
            f.addVertex(q)
"""

    def ellipsoid_vdb(name, center, rad, voxel):
        for old in [n for n in obj.children() if n.name() == name]:
            old.destroy()
        g = obj.createNode("geo", name, run_init_scripts=True)
        py = g.createNode("python", "gen_ellipsoid")
        code = (ELLIPSOID.replace("__CENTER__", repr(tuple(center)))
                         .replace("__RAD__", repr(tuple(rad))))
        py.parm("python").set(code)
        py.cook(force=True)
        vdb = g.createNode("vdbfrompolygons", "to_sdf")
        try:
            vdb.parm("voxelsize").set(voxel)
        except Exception:
            pass
        vdb.setInput(0, py)
        vdb.cook(force=True)
        err = " ".join(str(vdb.errors()).split()) if vdb.errors() else ""
        print(f"[volumes] {name} sdf: {err or 'OK'}")
        w = g.createNode("file", "writer")
        w.parm("file").set(str(OUT_DIR / f"{name}.vdb"))
        w.parm("filemode").set("write")
        w.setInput(0, vdb)
        w.cook(force=True)
        results.append((f"{name}.vdb", (OUT_DIR / f"{name}.vdb").exists()))
        g.destroy()

    # leviathan rest area: SM_Leviathan spans x -75..+90, y ~ -26..+30, z ~ +-30
    ellipsoid_vdb("VOL_GhostFog", (5, -4, 0), (80.0, 26.0, 30.0), 2.0)
    # jellyfish bell at origin, arms reach ~320 m — a broad veil above
    ellipsoid_vdb("VOL_NebulaVeil", (0, 120, 0), (220.0, 90.0, 220.0), 4.0)

    payload = {"schema": "melodia.sea_above_volumes.v1",
               "voxel_note": "SDF grids; UE SVT import maps grid values as "
                             "density/mask - noise and colour live in the material",
               "volumes": [{"name": n, "path": str(OUT_DIR / n),
                            "bytes": (OUT_DIR / n).stat().st_size if ok else 0,
                            "written": ok} for n, ok in results]}
    (OUT_DIR / "volumes_manifest.json").write_text(json.dumps(payload, indent=2),
                                                   encoding="utf-8")
    print(f"[volumes] manifest -> volumes_manifest.json "
          f"({sum(1 for _, ok in results if ok)}/{len(results)} written)")


if __name__ == "__main__":
    main()
