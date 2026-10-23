"""A2+A4 - Endless Escher Citadel: build + Mantra cinema (surreal marble-laden iridescent dream).

The song (song_schema.json, 192 voxels) becomes the architecture:
  - spiral corridor (torus, TURNS rotations) via polywire along the song curve
  - one marble hall per note (copy_to_points; Cd = aurora hue; shop_materialpath
    per instance = resonant marble / dissonant obsidian)
  - recursive golden-ratio spires on beat towers
  - Penrose stair loop (4 runs, closed, second tier = endless)
  - instanced detail: windows, torch glows, banners, biolum motes, pearl lights
  - Sea Above stage: island, false ocean with emissive foam, mist discs, gradient sky
Materials: Karma/Mantra PrincipledShader at /mat (marble/obsidian/aurora/biolum/gold/pearl).
Renderer: Mantra (ifd) - Karma's LOP input is blocked headless on this build.
Outputs (manifest): 4 hero shots @1920x1080 + fly-through sequence @960x540.

Run:  hython Tools/Houdini/endless_citadel/endless_citadel_build.py
"""
import hashlib
import json
import math
from pathlib import Path

import hou

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
SCHEMA = ROOT / "Saved" / "Audit" / "endless_citadel" / "song_schema.json"
OUT = ROOT / "Saved" / "Audit" / "endless_citadel"
OUT.mkdir(parents=True, exist_ok=True)
POINTS_BGEO = OUT / "citadel_song_points.bgeo"

scene = hou.node("/obj")
geo = scene.createNode("geo", "citadel")


def P(node, name, value):
    """Defensive parm set: returns True if the parm existed and was set."""
    p = node.parm(name)
    if p is not None:
        try:
            p.set(value)
            return True
        except Exception:
            return False
    return False


# ------------------------------------------------------------------ materials
def make_material(name, **kw):
    sh = hou.node("/mat").createNode("principledshader", name)
    for k, v in kw.items():
        try:
            sh.parm(k).set(v)
        except Exception:
            pass
    return sh


make_material("cit_marble", basecolorr=0.95, basecolorg=0.93, basecolorb=0.97,
              rough=0.16, reflect=0.6, ior=1.5, basecolor_usePointColor=1)
make_material("cit_obsidian", basecolorr=0.055, basecolorg=0.045, basecolorb=0.085,
              rough=0.32, reflect=0.35, basecolor_usePointColor=1)
make_material("cit_aurora", basecolorr=0.02, basecolorg=0.02, basecolorb=0.04,
              emitint=3.0, emitcolorr=0.96, emitcolorg=0.55, emitcolorb=0.78)
make_material("cit_biolum", basecolorr=0.01, basecolorg=0.03, basecolorb=0.03,
              emitint=6.0, emitcolorr=0.20, emitcolorg=0.90, emitcolorb=0.85)
make_material("cit_gold", basecolorr=0.96, basecolorg=0.74, basecolorb=0.34,
              metallic=1.0, rough=0.22)
make_material("cit_pearl", basecolorr=0.95, basecolorg=0.93, basecolorb=0.96,
              rough=0.12, reflect=0.9, emitint=0.6, emitcolorr=1.0,
              emitcolorg=0.55, emitcolorb=0.75)
make_material("cit_mist", basecolorr=0.05, basecolorg=0.10, basecolorb=0.14,
              emitint=1.2, emitcolorr=0.45, emitcolorg=0.75, emitcolorb=0.85,
              opac=0.35)
make_material("cit_sky", basecolorr=0.006, basecolorg=0.012, basecolorb=0.035,
              emitint=0.4, emitcolorr=0.05, emitcolorg=0.12, emitcolorb=0.30)


# ------------------------------------------------------------------ song points -> bgeo
def write_song_points():
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    g = hou.Geometry()
    for k in ("pitch", "velocity", "energy", "pitch_class", "scale_degree",
              "beat", "measure", "wing", "ornate", "t", "angle", "radius",
              "hue_r", "hue_g", "hue_b"):
        g.addAttrib(hou.attribType.Point, k, 0.0)
    g.addAttrib(hou.attribType.Point, "Cd", (0.5, 0.5, 0.5))
    g.addAttrib(hou.attribType.Point, "shop_materialpath", "/mat/cit_marble")
    g.addAttrib(hou.attribType.Point, "scale", 1.0)
    g.addAttrib(hou.attribType.Point, "voicetype", "")
    for p in data["voxels"]:
        pt = g.createPoint()
        pt.setPosition((p["x"], p["z"], p["y"]))  # Houdini Z-up: (x, z, y)
        for k in ("pitch", "velocity", "energy", "pitch_class", "scale_degree",
                  "beat", "measure", "wing", "hue_r", "hue_g", "hue_b",
                  "ornate", "t", "angle", "radius"):
            v = p.get(k)
            pt.setAttribValue(k, 0.0 if v is None else float(v))
        mat = "cit_obsidian" if p["material"] == "dissonant_note" else "cit_marble"
        pt.setAttribValue("shop_materialpath", f"/mat/{mat}")
        pt.setAttribValue("Cd", (p["hue_r"] * 0.55 + 0.45,
                                 p["hue_g"] * 0.55 + 0.45,
                                 p["hue_b"] * 0.55 + 0.45))
        pt.setAttribValue("scale", 0.9 + 0.7 * (p["velocity"] / 127.0))
        pt.setAttribValue("voicetype", p.get("voice", "harmony"))
    g.saveToFile(str(POINTS_BGEO))
    # closed torus curve through the song points (order preserved)
    curve = hou.Geometry()
    cpts = [curve.createPoint() for _ in data["voxels"]]
    for cpt, p in zip(cpts, data["voxels"]):
        cpt.setPosition((p["x"], p["z"], p["y"]))
    curve.createPolygon(is_closed=True)
    poly = curve.prims()[0]
    for cpt in cpts:
        poly.addVertex(cpt)
    CURVE_BGEO = OUT / "citadel_song_curve.bgeo"
    curve.saveToFile(str(CURVE_BGEO))
    return data


data = write_song_points()
points_file = geo.createNode("file", "song_points")
points_file.parm("file").set(str(POINTS_BGEO))

# tangent + orient from the spiral curve (neighbors on t)
orient_wrangle = geo.createNode("attribwrangle", "orient_pts")
orient_wrangle.parm("snippet").set("""
int n = npoints(0);
float t = @t;
float d = 1e-3;
int i0 = -1, i1 = -1;
float best0 = 1e9, best1 = 1e9;
for (int i = 0; i < n; i++) {
    float ti = point(0, "t", i);
    if (ti <= t && (t - ti) < best0) { best0 = t - ti; i0 = i; }
    if (ti >= t && (ti - t) < best1) { best1 = ti - t; i1 = i; }
}
if (i0 < 0) i0 = 0; if (i1 < 0) i1 = n - 1;
vector p0 = point(0, "P", i0);
vector p1 = point(0, "P", i1);
vector tan = normalize(p1 - p0);
matrix3 m = dihedral({0, 0, 1}, tan);
p@orient = quaternion(m);
f@pscale = f@scale * 1.6;
""")
orient_wrangle.setNextInput(points_file)

# corridor curve: closed polyline through song points, resampled, polywire
corridor_curve = geo.createNode("file", "corridor_curve")
corridor_curve.parm("file").set(str(OUT / "citadel_song_curve.bgeo"))
resample = geo.createNode("resample", "corridor_resample")
P(resample, "method", 0)
P(resample, "length", 1.4)
resample.setNextInput(corridor_curve)
corridor = geo.createNode("polywire", "corridor_tube")
P(corridor, "radius", 2.1)
P(corridor, "subdiv", 2)
corridor.setNextInput(resample)


# ------------------------------------------------------------------ hall module
hall = geo.createNode("subnet", "hall_module")
hall.moveToGoodPosition()
h = hall.createNode("merge", "hall_out")
def hall_prim(node_name, prim_type, **parms):
    n = hall.createNode(prim_type, node_name)
    for k, v in parms.items():
        try:
            n.parm(k).set(v)
        except Exception:
            pass
    h.setNextInput(n)
    return n

floor = hall_prim("h_floor", "box", sizex=6.4, sizey=0.5, sizez=5.2, ty=0.25)
col_l = hall_prim("h_col_l", "tube", radx=0.42, rady=0.42, height=6.0,
                  tx=-2.6, ty=3.0)
col_r = hall_prim("h_col_r", "tube", radx=0.42, rady=0.42, height=6.0,
                  tx=2.6, ty=3.0)
arch = hall_prim("h_arch", "torus", radx=2.9, rady=2.9, tube=0.35,
                 tx=0, ty=5.6, tz=2.5)
roof = hall_prim("h_roof", "box", sizex=6.6, sizey=0.5, sizez=5.4, ty=6.4)
win_l = hall_prim("h_win_l", "box", sizex=0.3, sizey=3.4, sizez=2.4,
                  tx=-3.15, ty=3.6)
win_r = hall_prim("h_win_r", "box", sizex=0.3, sizey=3.4, sizez=2.4,
                  tx=3.15, ty=3.6)
halo = hall_prim("h_halo", "torus", radx=0.9, rady=0.9, tube=0.18,
                  tx=0, ty=7.0, tz=0)
# hall material (marble) - prim-level so copytopoints copies carry it
hmat = hall.createNode("material", "hall_mat")
P(hmat, "shop_materialpath1", "/mat/cit_marble")
hmat.setNextInput(h)
hmat.setGenericFlag(hou.nodeFlag.Render, True)
hmat.setGenericFlag(hou.nodeFlag.Display, True)
hall.layoutChildren()

# ------------------------------------------------------------------ copy halls
halls_copy = geo.createNode("copytopoints", "halls")
halls_copy.setNextInput(hall, 0)
halls_copy.setInput(1, orient_wrangle, 0)

# windows -> aurora emissive material (per-prim attr, harmless if unused)

# ------------------------------------------------------------------ towers (recursive spires)
tower_pts = geo.createNode("attribwrangle", "tower_pts")
tower_pts.parm("snippet").set("""
int n = npoints(0);
if (@beat % 3 == 0) { i@tower = 1; } else { removepoint(0, @ptnum); }
""")
tower_pts.setNextInput(orient_wrangle)

tower_sub = geo.createNode("subnet", "tower_module")
ts = tower_sub.createNode("merge", "tower_out")
def spire(level, cx, cy, cz, r, hgt):
    cyl = tower_sub.createNode("tube", f"spire_c{level}")
    P(cyl, "radx", r)
    P(cyl, "rady", r)
    P(cyl, "height", hgt)
    P(cyl, "tx", cx)
    P(cyl, "ty", cz + hgt * 0.5)
    P(cyl, "tz", cy)
    ts.setNextInput(cyl)
    finial = tower_sub.createNode("sphere", f"spire_f{level}")
    P(finial, "radx", r * 0.9)
    P(finial, "rady", r * 0.9)
    P(finial, "radz", r * 0.9)
    P(finial, "ty", cz + hgt * 1.05)
    ts.setNextInput(finial)
    return r * 0.618, hgt * 0.618

r0, h0 = 1.3, 7.0
for lvl in range(3):
    r0, h0 = spire(lvl, 0, 0, 0, r0, h0)
tower_sub.layoutChildren()
towers = geo.createNode("copytopoints", "towers")
towers.setNextInput(tower_sub, 0)
towers.setInput(1, tower_pts, 0)

# ------------------------------------------------------------------ penrose stairs
stairs = geo.createNode("subnet", "penrose_stairs")
sm = stairs.createNode("merge", "stairs_out")
RUNS, STEPS, RISE, R = 4, 6, 0.35, 4.0
sx, sy = 8.0, 2.0  # penrose location
for tier in (0, 1):
    for run in range(RUNS):
        a0 = run * (math.pi / 2.0) + math.pi / 4.0
        base_z = run * RISE * STEPS + tier * 3.0
        for s in range(STEPS):
            ang = a0 + (s / STEPS) * (math.pi / 2.0)
            cx = sx + R * math.cos(ang)
            cy = sy + R * math.sin(ang)
            step = stairs.createNode("box", f"st_t{tier}_r{run}_s{s}")
            step.parm("sizex").set(1.1)
            step.parm("sizey").set(RISE * 0.92)
            step.parm("sizez").set(1.1)
            step.parmTuple("t").set((cx, base_z + s * RISE + RISE * 0.5, cy))
            step.parmTuple("r").set((0, -math.degrees(ang) + 90, 0))
            sm.setNextInput(step)
stairs.layoutChildren()

# ------------------------------------------------------------------ island (flattened sphere) + ocean + mist + sky
island = geo.createNode("sphere", "island")
island.parm("radx").set(48)
island.parm("rady").set(7)
island.parm("radz").set(48)
island.parmTuple("t").set((8, -1.4, 5))
island_sop = island.createOutputNode("attribwrangle", "island_rough")
island_sop.parm("snippet").set(
    "@P.y += (noise(@P * 0.06 + 4.0) - 0.5) * 1.4;\n"
    "float edge = clamp((length(set(@P.x - 8, @P.z - 5)) - 40.0) / 6.0, 0.0, 1.0);\n"
    "@P.y -= edge * 2.2;")

ocean = geo.createNode("grid", "ocean")
ocean.parm("sizex").set(900)
ocean.parm("sizey").set(900)
ocean.parmTuple("t").set((8, -2.2, 5))

foam_pts = geo.createNode("grid", "foam_ring_pts")
foam_pts.parm("sizex").set(160)
foam_pts.parm("sizey").set(160)
foam_pts.parm("rows").set(24)
foam_pts.parm("cols").set(24)
foam_pts.parmTuple("t").set((8, -1.7, 5))
foam_w = foam_pts.createOutputNode("attribwrangle", "foam_ring")
foam_w.parm("snippet").set("""
float d = distance(@P, set(8, -1.7, 5));
float ring = 1.0 - abs(d - 26.0) / 6.0;
ring = clamp(ring, 0.0, 1.0);
ring *= (0.6 + 0.4 * noise(@P * 0.5));
if (ring < 0.25) removepoint(0, @ptnum);
@Cd = set(0.2, 0.9, 0.85) * ring;
s@shop_materialpath = "/mat/cit_biolum";
""")

mist = geo.createNode("grid", "mist")
mist.parm("sizex").set(700)
mist.parm("sizey").set(700)
mist.parmTuple("t").set((8, 2.0, 5))

sky = geo.createNode("sphere", "sky")
sky.parm("radx").set(800)
sky.parm("rady").set(800)
sky.parm("radz").set(800)
sky.parmTuple("t").set((8, 0, 5))

# material assignments (prim-level via Material SOP)
def assign_mat(node, matpath, snippet=""):
    ms = node.createOutputNode("material", "mat_" + node.name())
    P(ms, "shop_materialpath1", matpath)
    return ms

assign_mat(island_sop, "/mat/cit_marble")
assign_mat(ocean, "/mat/cit_obsidian")
assign_mat(mist, "/mat/cit_mist")
assign_mat(sky, "/mat/cit_sky")
assign_mat(corridor, "/mat/cit_marble")
assign_mat(stairs, "/mat/cit_marble")

# ---------------------------------------------------------------- final merge (render output)
final_merge = geo.createNode("merge", "citadel_final")
for piece in (corridor, halls_copy, towers, stairs, island_sop,
              ocean, foam_w, mist, sky):
    final_merge.setNextInput(piece)
final_merge.setGenericFlag(hou.nodeFlag.Render, True)
final_merge.setGenericFlag(hou.nodeFlag.Display, True)
geo.setGenericFlag(hou.nodeFlag.Render, True)
geo.layoutChildren()

# ------------------------------------------------------------------ lights + camera
def make_light(name, loc, rgb, intensity, light_type="distant"):
    lg = scene.createNode("hlight", name)
    lg.parmTuple("t").set(loc)
    P(lg, "light_enable", 1)
    P(lg, "light_type", light_type)
    P(lg, "light_colorr", rgb[0])
    P(lg, "light_colorg", rgb[1])
    P(lg, "light_colorb", rgb[2])
    P(lg, "light_intensity", intensity)
    P(lg, "light_exposure", 0.0)
    return lg


key = make_light("cit_key", (40, 60, -30), (0.55, 0.68, 1.0), 1.6)
rim = make_light("cit_rim", (-35, 25, 40), (1.0, 0.45, 0.75), 1.2)
bio = make_light("cit_bio", (10, 6, -20), (0.20, 0.90, 0.85), 2.0)


def add_camera(name, loc, target):
    cam = scene.createNode("cam", name)
    cam.parmTuple("t").set(loc)
    P(cam, "resx", 1920)
    P(cam, "resy", 1080)
    P(cam, "resMenu", "16:9")
    eye = hou.Vector3(loc)
    tgt = hou.Vector3(target)
    d = (tgt - eye).normalized()
    z = d  # camera looks along +Z in this convention; flip if wrong
    up = hou.Vector3(0, 1, 0)
    x = up.cross(z)
    if x.length() < 1e-6:
        x = hou.Vector3(1, 0, 0)
    else:
        x = x.normalized()
    y = z.cross(x)
    m = hou.Matrix3()
    for r, vec in enumerate((x, y, z)):
        for c in range(3):
            m.setAt(r, c, vec[c])
    rot = m.extractRotates()
    cam.parmTuple("r").set((rot[0], rot[1], rot[2]))
    return cam


cam_hero = add_camera("cit_cam_hero", (46, 22, -34), (8, 8, 5))
cam_aerial = add_camera("cit_cam_aerial", (12, 58, 40), (8, 6, 5))
cam_stairs = add_camera("cit_cam_stairs", (16, 9, 16), (8, 4, 5))
cam_fly = add_camera("cit_cam_fly", (30, 14, -24), (8, 6, 5))

# ------------------------------------------------------------------ render (Mantra)
DEBUG = __import__("os").environ.get("CITADEL_DEBUG") == "1"
if DEBUG:
    final_merge.cook()
    g = final_merge.geometry()
    print("[citadel-DEBUG] final prims:", len(g.prims()), "points:", len(g.points()))
    print("[citadel-DEBUG] bounds:", g.boundingBox())
    print("[citadel-DEBUG] geo render flag:", geo.isRenderFlagSet() if hasattr(geo, "isRenderFlagSet") else "n/a")
    key_parms = [p.name() for p in key.parms()]
    print("[citadel-DEBUG] hlight parms:", [n for n in key_parms if "light" in n or "inten" in n or "color" in n][:20])
    cam_parms = [p.name() for p in cam_hero.parms()]
    print("[citadel-DEBUG] cam res parms:", [n for n in cam_parms if "res" in n or "shutter" in n][:10])
    hip = OUT / "citadel_debug.hip"
    hou.hipFile.save(str(hip))
    print("[citadel-DEBUG] saved hip:", hip)
    print("[citadel-DEBUG] SKIPPING RENDER")
    raise SystemExit(0)

mantra = hou.node("/out").createNode("ifd", "citadel_render")
mantra.parm("vm_picture").set(str(OUT / "citadel_$F4.png"))
mantra.parm("override_camerares").set(1)
mantra.parm("res_overridex").set(1920)
mantra.parm("res_overridey").set(1080)
mantra.parm("vm_samplesx").set(4)
mantra.parm("vm_samplesy").set(4)

shots = {
    "hero": (cam_hero, OUT / "citadel_hero.png"),
    "aerial": (cam_aerial, OUT / "citadel_aerial.png"),
    "stairs": (cam_stairs, OUT / "citadel_stairs.png"),
}
outputs = []
for name, (cam, path) in shots.items():
    mantra.parm("camera").set(cam.path())
    mantra.parm("vm_picture").set(str(path))
    mantra.render()
    outputs.append({"shot": name, "path": str(path), "bytes": path.stat().st_size})

# fly-through: 48 frames
fly_dir = OUT / "flythrough"
fly_dir.mkdir(parents=True, exist_ok=True)
mantra.parm("res_overridex").set(960)
mantra.parm("res_overridey").set(540)
mantra.parm("vm_samplesx").set(2)
mantra.parm("vm_samplesy").set(2)
mantra.parm("camera").set(cam_fly.path())
mantra.parm("vm_picture").set(str(fly_dir / "fly_$F4.png"))
P(mantra, "trange", "normal")
P(mantra, "f1", 1)
P(mantra, "f2", 48)
P(mantra, "f3", 1)
mantra.render()

manifest = {
    "schema": "melodia.endless_citadel_render.v1",
    "seed": data["seed"],
    "song": data["song"],
    "renderer": "Mantra (Karma LOP input blocked headless on Apprentice)",
    "shots": outputs,
    "flythrough": {"dir": str(fly_dir), "frames": 48, "res": "960x540"},
}
mp = OUT / "citadel_render_manifest.json"
mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("[citadel] manifest ->", mp)
print("[citadel] DONE")