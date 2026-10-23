"""Build + gate the house terrain HDA v2 (Hython only; never touches Unreal or Content/HDA).

Extends the vista builder (build_house_garden_vista_hda_v1.py, melodia::house_garden_vista::1.0). Kept from v1: the Unreal
landscape contract (seven Nikki layers + unreal_* attributes), the pond, the promoted controls. New in v2:

  H2  house-aware pad measured from the live House map (footprint + margin, real falloff), a 1 km window (cooks at a
      preview resolution for live editing, final resolution for the Landscape), and a near-field flatten so the DEM's
      +-8 m marsh/island relief does not fight the house.
  H3  horizon: a radial ramp (flat inside horizon_start, full by horizon_full) of ridged-multifractal rises that open
      toward the view azimuth, plus a Rock layer on the ridges.

Run (editor CLOSED is not required, but never cook this inside a shared editor):
  "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/build_house_terrain_hda.py

Output: Saved/Staging/HouseTerrain_20261023/MelodiaHouseTerrain_2.0.hda  (candidate; promote to Content/HDA only after the gate)
        Saved/Audit/HouseTerrain_20261023/terrain_gate.json + hillshade.png + .hip
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
STAGE = ROOT / "Saved" / "Staging" / "HouseTerrain_20261023"
AUDIT = ROOT / "Saved" / "Audit" / "HouseTerrain_20261023"
HDA_PATH = STAGE / "MelodiaHouseTerrain_2.0.hda"
IGN_TIFF = ROOT / "Docs" / "Poitou" / "research" / "dem" / "maillezais_rgealti1m_l93.tif"
sys.path.insert(0, str(ROOT / "Tools" / "Houdini"))
sys.path.insert(0, r"C:\EnvironmentPortfolio\tools\gouache")
import hda_promote_controls as promote

import hou

TYPE_NAME = "melodia::house_terrain::2.0"
LAYERS = ["Grass", "Ground", "Base", "Mud", "Path", "Rock", "Water"]

# Measured from the live L_MelusinaHouse_P0 shell actors, 2026-10-23: x -1182..2570 cm, y -1179..27 cm.
# Houdini heightfields lie in XZ with Y up; Houdini Engine maps UE (x, y, z) = (Hx, Hz, Hy) * 100 (verify with a marker cook).
HOUSE = {"xmin": -11.82, "xmax": 25.70, "zmin": -11.79, "zmax": 0.27}
PAD_MARGIN = 6.0
PAD_FALLOFF = 12.0
HCX = (HOUSE["xmin"] + HOUSE["xmax"]) / 2.0
HCZ = (HOUSE["zmin"] + HOUSE["zmax"]) / 2.0


def make_controls(geo):
    controls = geo.createNode("null", "controls")
    pg = controls.parmTemplateGroup()

    def fl(f, name, label, v, lo=None, hi=None):
        kw = {}
        if lo is not None:
            kw["min"] = lo
        if hi is not None:
            kw["max"] = hi
        f.addParmTemplate(hou.FloatParmTemplate(name, label, 1, default_value=(v,), **kw))

    f = hou.FolderParmTemplate("source", "IGN Source and Window", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.StringParmTemplate("source_filepath", "IGN RGE ALTI GeoTIFF", 1, default_value=(str(IGN_TIFF),), string_type=hou.stringParmType.FileReference))
    fl(f, "source_min", "Source minimum (m NGF)", 1.40, 0.0, 100.0)
    fl(f, "source_range", "Source height range (m)", 16.0033, 0.01, 100.0)
    fl(f, "crop_x", "DEM crop center X (m)", 520.0, -1500.0, 1500.0)
    fl(f, "crop_z", "DEM crop center Z (m)", 580.0, -1500.0, 1500.0)
    fl(f, "reference_elevation", "Local reference elevation (m NGF)", 9.66, -100.0, 100.0)
    fl(f, "amplitude", "DEM amplitude (m across source range)", 16.0033, 0.0, 100.0)
    fl(f, "window_m", "Window size (m)", 500.0, 100.0, 2000.0)
    fl(f, "window_cx", "Window center local X (m)", HCX)
    fl(f, "window_cz", "Window center local Z (m)", HCZ)
    f.addParmTemplate(hou.IntParmTemplate("preview_resolution", "Resolution (samples; 253 live, 1009 final)", 1, default_value=(253,), min=65, max=2017))
    pg.append(f)

    f = hou.FolderParmTemplate("garden", "House Pad and Pond", folder_type=hou.folderType.Tabs)
    fl(f, "pad_elevation", "House pad elevation (m)", -0.10, -10.0, 10.0)
    fl(f, "pad_xmin", "Pad X minimum (m)", round(HOUSE["xmin"] - PAD_MARGIN, 2))
    fl(f, "pad_xmax", "Pad X maximum (m)", round(HOUSE["xmax"] + PAD_MARGIN, 2))
    fl(f, "pad_zmin", "Pad Z minimum (m)", round(HOUSE["zmin"] - PAD_MARGIN, 2))
    fl(f, "pad_zmax", "Pad Z maximum (m)", round(HOUSE["zmax"] + PAD_MARGIN, 2))
    fl(f, "pad_falloff", "Pad falloff (m)", PAD_FALLOFF, 0.5, 60.0)
    for n, label, v in [("pond_x", "Pond center X (m)", 40.0), ("pond_z", "Pond center Z (m)", -6.0), ("pond_radius_x", "Pond radius X (m)", 12.0), ("pond_radius_z", "Pond radius Z (m)", 9.0), ("water_level", "Pond water level (m)", -0.8), ("pond_bed", "Pond bed elevation (m)", -2.2)]:
        fl(f, n, label, v, -100.0, 100.0)
    pg.append(f)

    f = hou.FolderParmTemplate("horizon", "Horizon", folder_type=hou.folderType.Tabs)
    fl(f, "flat_inner", "Near field fully flat to (m)", 45.0, 0.0, 500.0)
    fl(f, "flat_outer", "DEM relief fully back by (m)", 110.0, 1.0, 800.0)
    fl(f, "horizon_start", "Horizon rises start (m)", 55.0, 0.0, 800.0)
    fl(f, "horizon_full", "Horizon rises full by (m)", 190.0, 1.0, 900.0)
    fl(f, "horizon_amp", "Horizon ridge height (m)", 26.0, 0.0, 200.0)
    fl(f, "ridge_freq", "Ridge frequency (1/m)", 0.0065, 0.0005, 0.05)
    fl(f, "ridge_sharp", "Ridge sharpness", 1.3, 0.5, 4.0)
    f.addParmTemplate(hou.IntParmTemplate("ridge_octaves", "Ridge octaves", 1, default_value=(3,), min=1, max=6))
    fl(f, "dem_gain", "DEM micro-relief gain away from the house", 0.5, 0.0, 2.0)
    f.addParmTemplate(hou.IntParmTemplate("ridge_seed", "Ridge seed", 1, default_value=(17,), min=0, max=99999))
    fl(f, "view_azimuth", "View azimuth (deg, 0 = +X)", 0.0, -180.0, 180.0)
    fl(f, "view_open", "View opens within (deg)", 75.0, 5.0, 180.0)
    fl(f, "off_view_gain", "Ridge height outside the view (0..1)", 0.35, 0.0, 1.0)
    fl(f, "rock_start", "Rock starts on ridge crests above (0..1)", 0.80, 0.0, 1.0)
    fl(f, "rock_full", "Rock fully covers crests above (0..1)", 0.95, 0.0, 1.0)
    pg.append(f)

    f = hou.FolderParmTemplate("paths_caves", "Paths and Caves", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.IntParmTemplate("path_count", "Number of paths", 1, default_value=(4,), min=0, max=8))
    f.addParmTemplate(hou.IntParmTemplate("path_seed", "Path seed", 1, default_value=(11,), min=0, max=99999))
    fl(f, "path_spread_deg", "Path fan spread (deg)", 70.0, 0.0, 180.0)
    fl(f, "path_length_m", "Path length (m)", 230.0, 60.0, 900.0)
    fl(f, "path_start_x", "Path start X (m, the porch)", 27.0)
    fl(f, "path_start_z", "Path start Z (m, the porch)", -5.76)
    fl(f, "path_width_m", "Path width (m)", 3.0, 0.5, 20.0)
    fl(f, "path_carve_m", "Path carve depth (m)", 0.25, 0.0, 3.0)
    fl(f, "eye_height_m", "Porch eye height above the pad (m)", 1.6, 0.5, 4.0)
    f.addParmTemplate(hou.IntParmTemplate("cave_count", "Number of caves", 1, default_value=(3,), min=0, max=8))
    f.addParmTemplate(hou.IntParmTemplate("cave_seed", "Cave seed", 1, default_value=(5,), min=0, max=99999))
    fl(f, "cave_radius_m", "Cave bowl radius (m)", 9.0, 2.0, 60.0)
    fl(f, "cave_depth_m", "Cave bowl depth (m)", 4.0, 0.0, 30.0)
    fl(f, "cave_mouth_m", "Cave mouth width (m)", 7.0, 1.0, 40.0)
    pg.append(f)

    f = hou.FolderParmTemplate("landscape", "Landscape and LayerInfo", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.StringParmTemplate("landscape_material", "Landscape material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Landscape_Nikki.MI_Poitou_Landscape_Nikki",)))
    f.addParmTemplate(hou.StringParmTemplate("layerinfo_dir", "LayerInfo folder", 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo",)))
    for layer in LAYERS:
        f.addParmTemplate(hou.StringParmTemplate("layerinfo_" + layer.lower(), "LayerInfo: " + layer, 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo/LI_Poitou_%s.LI_Poitou_%s" % (layer, layer),)))
    pg.append(f)
    controls.setParmTemplateGroup(pg)
    return controls


NAMES = (["source_filepath", "source_min", "source_range", "crop_x", "crop_z", "reference_elevation", "amplitude", "window_m", "window_cx", "window_cz", "preview_resolution",
          "pad_elevation", "pad_xmin", "pad_xmax", "pad_zmin", "pad_zmax", "pad_falloff", "pond_x", "pond_z", "pond_radius_x", "pond_radius_z", "water_level", "pond_bed",
          "flat_inner", "flat_outer", "horizon_start", "horizon_full", "horizon_amp", "ridge_freq", "ridge_sharp", "ridge_octaves", "dem_gain", "ridge_seed", "path_count", "path_seed", "path_spread_deg", "path_length_m", "path_start_x", "path_start_z", "path_width_m", "path_carve_m", "eye_height_m", "cave_count", "cave_seed", "cave_radius_m", "cave_depth_m", "cave_mouth_m", "view_azimuth", "view_open", "off_view_gain", "rock_start", "rock_full",
          "landscape_material", "layerinfo_dir"] + ["layerinfo_" + n.lower() for n in LAYERS])

PATHS_PY = r'''
import math, random
node = hou.pwd(); geo = node.geometry(); hda = node.parent()
src = node.inputs()[0].geometry()
ins = node.inputs()
cav = ins[1].geometry() if len(ins) > 1 and ins[1] else None
cpts = [(p.position()[0], p.position()[2]) for p in cav.points()] if cav is not None else []
geo.clear()
vols = {p.attribValue("name"): p for p in src.prims() if isinstance(p, hou.Volume)}
H = vols["height"]
def h(x, z): return H.sample((float(x), 0.0, float(z)))
def slope(x, z):
    d = 4.0
    return math.hypot((h(x + d, z) - h(x - d, z)) / (2 * d), (h(x, z + d) - h(x, z - d)) / (2 * d))
n = hda.parm("path_count").eval()
va = hda.parm("view_azimuth").eval(); spread = hda.parm("path_spread_deg").eval(); L = hda.parm("path_length_m").eval()
sx, sz = hda.parm("path_start_x").eval(), hda.parm("path_start_z").eval()
wl = hda.parm("water_level").eval()
pond_x, pond_z = hda.parm("pond_x").eval(), hda.parm("pond_z").eval()
pond_rx, pond_rz = max(0.1, hda.parm("pond_radius_x").eval()), max(0.1, hda.parm("pond_radius_z").eval())
hx = (hda.parm("pad_xmin").eval() + hda.parm("pad_xmax").eval()) * 0.5; hz = (hda.parm("pad_zmin").eval() + hda.parm("pad_zmax").eval()) * 0.5
rng = random.Random(hda.parm("path_seed").eval())
geo.addAttrib(hou.attribType.Prim, "path_id", 0)
geo.addAttrib(hou.attribType.Point, "elev", 0.0)
def angdiff(a, b): return abs((a - b + 540.0) % 360.0 - 180.0)
for k in range(n):
    goal = va + (0.0 if n == 1 else spread * (k / float(n - 1) - 0.5))
    target = cpts[k] if k < len(cpts) else None
    if target is not None: goal = math.degrees(math.atan2(target[1] - sz, target[0] - sx))
    x, z, heading = sx, sz, goal
    pts = [(x, z)]
    for step in range(int(L * 1.6 / 6.0)):
        if target is not None:
            if math.hypot(target[0] - x, target[1] - z) < 8.0:
                pts.append(target); break
            goal = math.degrees(math.atan2(target[1] - z, target[0] - x))
        best, bc = None, 1e9
        for dh in (-48, -36, -24, -12, 0, 12, 24, 36, 48):
            hd = heading + dh
            nx, nz = x + 6.0 * math.cos(math.radians(hd)), z + 6.0 * math.sin(math.radians(hd))
            hg = h(nx, nz)
            cost = slope(nx, nz) * 22.0 + abs(dh) * 0.04 + angdiff(hd, goal) * 0.16 + rng.random() * 0.25
            pr = math.hypot((nx - pond_x) / pond_rx, (nz - pond_z) / pond_rz)
            if pr < 1.45: cost += 80.0 * (1.45 - pr)
            if hg < wl + 0.25: cost += 60.0
            if cost < bc: bc, best = cost, (nx, nz, hd)
        x, z, heading = best
        pts.append((x, z))
        if target is None and math.hypot(x - hx, z - hz) > L: break
    for _ in range(3):
        pts = [pts[0]] + [((pts[i - 1][0] + pts[i][0] + pts[i + 1][0]) / 3.0, (pts[i - 1][1] + pts[i][1] + pts[i + 1][1]) / 3.0) for i in range(1, len(pts) - 1)] + [pts[-1]]
    poly = geo.createPolygon(); poly.setIsClosed(False); poly.setAttribValue("path_id", k)
    for (px, pz) in pts:
        pt = geo.createPoint(); pt.setPosition(hou.Vector3(px, 0.0, pz)); pt.setAttribValue("elev", h(px, pz)); poly.addVertex(pt)
'''

CAVES_PY = r'''
import math, random
node = hou.pwd(); geo = node.geometry(); hda = node.parent()
srcs = node.inputs()
src = srcs[0].geometry()
geo.clear()
vols = {p.attribValue("name"): p for p in src.prims() if isinstance(p, hou.Volume)}
H = vols["height"]
def h(x, z): return H.sample((float(x), 0.0, float(z)))
def grad(x, z):
    d = 4.0
    return ((h(x + d, z) - h(x - d, z)) / (2 * d), (h(x, z + d) - h(x, z - d)) / (2 * d))
n = hda.parm("cave_count").eval(); rng = random.Random(hda.parm("cave_seed").eval())
va = hda.parm("view_azimuth").eval(); vo = hda.parm("view_open").eval()
hx = (hda.parm("pad_xmin").eval() + hda.parm("pad_xmax").eval()) * 0.5; hz = (hda.parm("pad_zmin").eval() + hda.parm("pad_zmax").eval()) * 0.5
path_pts = []
ex, ez = hda.parm("path_start_x").eval(), hda.parm("path_start_z").eval()
ey = hda.parm("pad_elevation").eval() + hda.parm("eye_height_m").eval()
def los(tx, ty, tz, step=3.0):
    d = math.hypot(tx - ex, tz - ez)
    n = max(2, int(d / step))
    for i in range(1, n):
        t = i / float(n)
        if h(ex + (tx - ex) * t, ez + (tz - ez) * t) > ey + (ty - ey) * t - 0.3: return False
    return True
cands = []
for r in range(70, 231, 8):
    for ang in range(int(-vo), int(vo) + 1, 3):
        a = math.radians(va + ang); x, z = hx + r * math.cos(a), hz + r * math.sin(a)
        hg = h(x, z); gx, gz = grad(x, z); sl = math.hypot(gx, gz)
        if hg < 8.0 or sl < 0.26: continue
        if path_pts and min(math.hypot(x - px, z - pz) for px, pz in path_pts) < 22.0: continue
        if not los(x, hg + 2.0, z): continue
        # a cave mouth opens HORIZONTALLY: the flank's outward (downslope) direction must point toward the porch within ~60 degrees
        gl = math.hypot(gx, gz); el = math.hypot(ex - x, ez - z)
        if gl < 1e-6 or el < 1e-6: continue
        if ((-gx / gl) * ((ex - x) / el) + (-gz / gl) * ((ez - z) / el)) < 0.5: continue
        cands.append((sl * 1.0 + hg / 40.0 + rng.random() * 0.35, x, z, hg, gx, gz, sl))
cands.sort(reverse=True)
geo.addAttrib(hou.attribType.Point, "N", hou.Vector3(0, 1, 0))
geo.addAttrib(hou.attribType.Point, "pscale", 1.0)
geo.addAttrib(hou.attribType.Point, "cave_id", 0)
geo.addAttrib(hou.attribType.Point, "slope", 0.0)
chosen = []
for c in cands:
    if len(chosen) >= n: break
    if all(math.hypot(c[1] - o[1], c[2] - o[2]) >= 40.0 for o in chosen): chosen.append(c)
mouth = hda.parm("cave_mouth_m").eval()
for i, (sc, x, z, hg, gx, gz, sl) in enumerate(chosen):
    pt = geo.createPoint(); pt.setPosition(hou.Vector3(x, hg, z))
    nrm = hou.Vector3(-gx, 1.0, -gz).normalized()
    pt.setAttribValue("N", nrm); pt.setAttribValue("pscale", mouth); pt.setAttribValue("cave_id", i); pt.setAttribValue("slope", sl)
'''

CARVE_VEX = r'''
vector q = set(@P.x, 0, @P.z);
float pm = 0.0;
if (npoints(1) > 1) {
    int pr; vector uv;
    float d = xyzdist(1, q, pr, uv);
    float w = max(0.1, ch("../controls/path_width_m")) * 0.5;
    pm = 1.0 - smooth(w, w + max(0.8, w), d);
}
float dxp = max(max(ch("../controls/pad_xmin") - @P.x, 0.0), @P.x - ch("../controls/pad_xmax"));
float dzp = max(max(ch("../controls/pad_zmin") - @P.z, 0.0), @P.z - ch("../controls/pad_zmax"));
float padw = 1.0 - smooth(0.0, max(0.1, ch("../controls/pad_falloff")), length(set(dxp, 0, dzp)));
@height -= pm * ch("../controls/path_carve_m") * (1.0 - padw);
float bowl = 0.0;
if (npoints(2) > 0) {
    int np = nearpoint(2, q);
    vector cp = point(2, "P", np);
    float dc = distance(q, set(cp.x, 0, cp.z));
    float R = max(1.0, ch("../controls/cave_radius_m"));
    bowl = 1.0 - smooth(0.0, R, dc);
}
@height -= bowl * ch("../controls/cave_depth_m");
@Rock = clamp(max(@Rock, bowl), 0.0, 1.0);
@Path = clamp(max(@Path, pm), 0.0, 1.0);
@Mud = clamp(max(@Mud, pm * 0.35), 0.0, 1.0);
@Grass = clamp(@Grass * (1.0 - max(pm, bowl)), 0.0, 1.0);
'''

SHAPE_VEX = r'''
float raw = @height;
float lo = ch("../controls/source_min");
float span = max(0.001, ch("../controls/source_range"));
float datum = ch("../controls/reference_elevation");
float amp = ch("../controls/amplitude");
float dem = ((clamp(raw, lo, lo + span) - datum) / span) * amp;
float x = @P.x, z = @P.z;
float hx = (ch("../controls/pad_xmin") + ch("../controls/pad_xmax")) * 0.5;
float hz = (ch("../controls/pad_zmin") + ch("../controls/pad_zmax")) * 0.5;
float r = length(set(x - hx, 0, z - hz));

// ---- H3 horizon: ridged multifractal rises, flat near the house, open toward the view azimuth
float far = smooth(ch("../controls/horizon_start"), ch("../controls/horizon_full"), r);
float az = degrees(atan2(z - hz, x - hx));
float dd = az - ch("../controls/view_azimuth") + 540.0;
dd = dd - 360.0 * floor(dd / 360.0);
float dAz = abs(dd - 180.0);
float open = ch("../controls/view_open");
float inView = 1.0 - smooth(open, open + 60.0, dAz);
float viewGain = lerp(ch("../controls/off_view_gain"), 1.0, inView);
vector pp = set(x, 0.0, z) * ch("../controls/ridge_freq") + set(ch("../controls/ridge_seed") * 1.37, 0.0, ch("../controls/ridge_seed") * 0.71);
float n = 0.0, a = 1.0, f = 1.0, norm = 0.0;
int oct = chi("../controls/ridge_octaves");
for (int i = 0; i < oct; i++) {
    n += a * (1.0 - abs(noise(pp * f) * 2.0 - 1.0));
    norm += a; a *= 0.45; f *= 2.0;
}
n /= norm;
float ridge = pow(clamp(n, 0.0, 1.0), ch("../controls/ridge_sharp"));
float horizon = far * viewGain * ch("../controls/horizon_amp") * ridge;

// ---- DEM relief only returns away from the house; the pad and pond then shape the near field
float demMix = smooth(ch("../controls/flat_inner"), ch("../controls/flat_outer"), r);
float base = dem * demMix * ch("../controls/dem_gain") + horizon;

// ---- H2 house pad: the footprint + margin, with a real falloff
float dx = max(max(ch("../controls/pad_xmin") - x, 0.0), x - ch("../controls/pad_xmax"));
float dz = max(max(ch("../controls/pad_zmin") - z, 0.0), z - ch("../controls/pad_zmax"));
float padDist = length(set(dx, 0, dz));
float pad = 1.0 - smooth(0.0, max(0.1, ch("../controls/pad_falloff")), padDist);

// ---- pond (kept from v1)
float rx = max(0.1, ch("../controls/pond_radius_x"));
float rz = max(0.1, ch("../controls/pond_radius_z"));
float pr = length(set((x - ch("../controls/pond_x")) / rx, 0, (z - ch("../controls/pond_z")) / rz));
float shore = smooth(0.58, 1.0, pr);
float outer = smooth(1.0, 1.16, pr);
float waterLevel = ch("../controls/water_level");
float bed = ch("../controls/pond_bed");
float pondGround = lerp(bed, waterLevel, shore);
float gardenHeight = lerp(pondGround, base, outer);
gardenHeight = lerp(gardenHeight, ch("../controls/pad_elevation"), pad);
@height = gardenHeight;

float rockiness = far * smooth(ch("../controls/rock_start"), max(ch("../controls/rock_start") + 0.01, ch("../controls/rock_full")), ridge);
@Rock = clamp(rockiness * (1.0 - pad), 0.0, 1.0);
@Grass = clamp((1.0 - max(pad, 1.0 - outer)) * (1.0 - @Rock), 0.0, 1.0);
@Ground = 1.0;
@Base = 1.0;
@Mud = max((1.0 - smooth(0.90, 1.12, pr)) * smooth(0.50, 0.78, pr), 0.0);
@Path = pad;
@Water = 1.0 - smooth(0.96, 1.02, pr);
'''

ATTR_VEX = r'''
s@unreal_landscape_layer_name = s@name;
if (s@name == "height") {
    s@unreal_material = chs("../controls/landscape_material");
    s@unreal_landscape_material = chs("../controls/landscape_material");
} else {
    string p = "../controls/layerinfo_" + tolower(s@name);
    s@unreal_landscape_layer_info = chs(p);
}
'''


def build_network(geo):
    controls = make_controls(geo)
    file = geo.createNode("heightfield_file", "IGN_RGE_ALTI_1m")
    file.parm("filename").setExpression('chs("../controls/source_filepath")', hou.exprLanguage.Hscript)
    file.parm("sizemethod").set(0)
    file.parm("size").set(3000.0)
    file.parm("heightscale").set(1.0)
    crop = geo.createNode("heightfield_crop", "crop_window")
    crop.setInput(0, file)
    crop.parm("cropmode").set(2)
    crop.parm("sizex").setExpression('ch("../controls/window_m") - 1', hou.exprLanguage.Hscript)
    crop.parm("sizey").setExpression('ch("../controls/window_m") - 1', hou.exprLanguage.Hscript)
    crop.parm("tx").setExpression('ch("../controls/crop_x")', hou.exprLanguage.Hscript)
    crop.parm("tz").setExpression('ch("../controls/crop_z")', hou.exprLanguage.Hscript)
    rs = geo.createNode("heightfield_resample", "resolution")
    rs.setInput(0, crop)
    rs.parm("fixedresample").set(1)
    rs.parm("gridspacing").setExpression('ch("../controls/window_m")/int(ch("../controls/preview_resolution"))', hou.exprLanguage.Hscript)
    xform = geo.createNode("xform", "local_house_frame")
    xform.setInput(0, rs)
    xform.parm("tx").setExpression('ch("../controls/window_cx")-ch("../controls/crop_x")', hou.exprLanguage.Hscript)
    xform.parm("tz").setExpression('ch("../controls/window_cz")-ch("../controls/crop_z")', hou.exprLanguage.Hscript)
    cp = geo.createNode("heightfield_copylayer", "create_nikki_landscape_layers")
    cp.setInput(0, xform)
    cp.parm("numcopy").set(len(LAYERS))
    for i, layer in enumerate(LAYERS, 1):
        cp.parm("create%d" % i).set(1)
        cp.parm("srcname%d" % i).set("mask")
        cp.parm("dstname%d" % i).set(layer)
    wr = geo.createNode("volumewrangle", "shape_pad_pond_horizon_masks")
    wr.setInput(0, cp)
    wr.parm("snippet").set(SHAPE_VEX)
    caves = geo.createNode("python", "place_caves")
    caves.setInput(0, wr)
    caves.parm("python").set(CAVES_PY)
    paths = geo.createNode("python", "route_paths_to_caves")
    paths.setInput(0, wr)
    paths.setInput(1, caves)
    paths.parm("python").set(PATHS_PY)
    carve = geo.createNode("volumewrangle", "carve_paths_and_caves")
    carve.setInput(0, wr)
    carve.setInput(1, paths)
    carve.setInput(2, caves)
    carve.parm("snippet").set(CARVE_VEX)
    attr = geo.createNode("attribwrangle", "unreal_classic_landscape_attributes")
    attr.setInput(0, carve)
    attr.parm("class").set(1)
    attr.parm("snippet").set(ATTR_VEX)
    clean = geo.createNode("blast", "remove_helper_mask")
    clean.setInput(0, attr)
    clean.parm("group").set("@name=mask")
    clean.parm("grouptype").set(4)
    out = geo.createNode("output", "OUT_HOUSE_TERRAIN_LANDSCAPE")
    out.parm("outputidx").set(0)
    out.setInput(0, clean)
    out_caves = geo.createNode("output", "OUT_CAVE_POINTS")
    out_caves.parm("outputidx").set(1)
    out_caves.setInput(0, caves)
    out_paths = geo.createNode("output", "OUT_PATH_CURVES")
    out_paths.parm("outputidx").set(2)
    out_paths.setInput(0, paths)
    for n in geo.children():
        n.moveToGoodPosition()
    return controls


def heights(hda):
    g = hda.node("remove_helper_mask").geometry()
    if g is None:
        diag = {n.name(): {"errors": list(n.errors()), "warnings": list(n.warnings())} for n in hda.allSubChildren() if n.errors() or n.warnings()}
        raise RuntimeError("no geometry from remove_helper_mask; node diagnostics: " + json.dumps(diag, indent=1))
    vols = {p.attribValue("name"): p for p in g.prims() if isinstance(p, hou.Volume)}
    return g, vols


def grid(vol):
    import numpy as np
    nx, ny, _ = vol.resolution()
    return np.asarray(vol.allVoxels(), dtype=np.float32).reshape((ny, nx))


def oriented(vol, variant=None):
    """Return (arr, xs, zs, residual, variant); arr[j, i] == vol.sample(xs[i], 0, zs[j]).
    The variant (transpose, flip_x, flip_z) is searched on a layer with real signal (height) and then REUSED for sparse layers."""
    import numpy as np
    arr0 = grid(vol)
    bb = vol.boundingBox()

    def build(tr, fl_x, fl_z):
        arr = arr0.T if tr else arr0
        ny, nx = arr.shape
        xs = np.linspace(bb.minvec()[0], bb.maxvec()[0], nx)
        zs = np.linspace(bb.minvec()[2], bb.maxvec()[2], ny)
        return np.ascontiguousarray(arr[::-1 if fl_z else 1, ::-1 if fl_x else 1]), xs, zs

    if variant is not None:
        a, xs, zs = build(*variant)
        return a, xs, zs, 0.0, variant
    best = None
    for tr in (False, True):
        for fl_x in (False, True):
            for fl_z in (False, True):
                a, xs, zs = build(tr, fl_x, fl_z)
                ny, nx = a.shape
                pts = [(int((nx - 1) * fx), int((ny - 1) * fz)) for fx, fz in ((0.2, 0.3), (0.7, 0.4), (0.5, 0.8), (0.35, 0.65), (0.8, 0.15), (0.45, 0.5))]
                err = sum(abs(float(a[j, i]) - vol.sample((float(xs[i]), 0.0, float(zs[j])))) for i, j in pts)
                if best is None or err < best[0]:
                    best = (err, a, xs, zs, (tr, fl_x, fl_z))
    return best[1], best[2], best[3], best[0], best[4]


def gate(hda, report):
    import numpy as np
    t0 = time.time()
    hda.cook(force=True)
    cook_s = time.time() - t0
    errors = [(n.path(), list(n.errors())) for n in hda.allSubChildren() if n.errors()]
    g, vols = heights(hda)
    missing = [n for n in ["height"] + LAYERS if n not in vols]
    h = vols["height"]
    nx, ny, _ = h.resolution()
    arr = grid(h)
    b = h.boundingBox()
    vs = h.voxelSize()
    xmin, xmax = b.minvec()[0] - vs[0] * 0.5, b.maxvec()[0] + vs[0] * 0.5
    zmin, zmax = b.minvec()[2] - vs[2] * 0.5, b.maxvec()[2] + vs[2] * 0.5

    def sample(x, z):
        return h.sample((float(x), 0.0, float(z)))

    pad_e = hda.parm("pad_elevation").eval()
    px = [(hda.parm("pad_xmin").eval() + hda.parm("pad_xmax").eval()) / 2.0, hda.parm("pad_xmin").eval() + 6.0, hda.parm("pad_xmax").eval() - 6.0, HOUSE["xmin"], HOUSE["xmax"]]
    pz = [(hda.parm("pad_zmin").eval() + hda.parm("pad_zmax").eval()) / 2.0, HOUSE["zmin"], HOUSE["zmax"]]
    pad_samples = {"x%.1f_z%.1f" % (x, z): sample(x, z) for x in px for z in pz}
    # radial statistics around the house centre, on an oriented grid (arr[j, i] == sample(xs[i], zs[j]))
    cx, cz = (hda.parm("pad_xmin").eval() + hda.parm("pad_xmax").eval()) / 2.0, (hda.parm("pad_zmin").eval() + hda.parm("pad_zmax").eval()) / 2.0
    arr, xs, zs, orient_err, _variant = oriented(h)
    va = hda.parm("view_azimuth").eval()

    def ring_vals(r0, r1, ang_lo, ang_hi):
        out = []
        for ang in np.arange(ang_lo, ang_hi + 0.1, 5.0):
            for r in np.arange(r0, r1 + 0.1, 5.0):
                out.append(h.sample((float(cx + r * math.cos(math.radians(va + ang))), 0.0, float(cz + r * math.sin(math.radians(va + ang))))))
        return np.asarray(out, dtype=np.float32)

    Rn = hda.parm("flat_inner").eval()
    halfw = hda.parm("window_m").eval() / 2.0
    fr0, fr1 = 0.62 * halfw, 0.92 * halfw
    near = np.asarray([h.sample((float(cx + dx), 0.0, float(cz + dz))) for dx in np.arange(-Rn, Rn + 0.1, 3.0) for dz in np.arange(-Rn, Rn + 0.1, 3.0) if math.hypot(dx, dz) < Rn], dtype=np.float32)
    far_view = ring_vals(fr0, fr1, -40.0, 40.0)
    far_off = np.concatenate([ring_vals(fr0, fr1, 125.0, 180.0), ring_vals(fr0, fr1, -180.0, -125.0)])
    report.update({
        "volume_resolution": [nx, ny], "orientation_residual_m": round(float(orient_err), 4), "cook_seconds": round(cook_s, 3),
        "local_bounds_m": {"x": [round(xmin, 2), round(xmax, 2)], "z": [round(zmin, 2), round(zmax, 2)]},
        "height_min_max_m": [round(float(arr.min()), 3), round(float(arr.max()), 3)],
        "near_field_min_max_m": [round(float(near.min()), 3), round(float(near.max()), 3)],
        "view_horizon_band_max_m": round(float(far_view.max()), 2) if far_view.size else None,
        "offview_horizon_band_max_m": round(float(far_off.max()), 2) if far_off.size else None,
        "pad_samples_m": {k: round(v, 4) for k, v in pad_samples.items()},
        "layers_present": sorted(vols.keys()), "sop_errors": errors,
        "rock_coverage_pct": round(float(grid(vols["Rock"]).mean()) * 100.0, 2),
    })
    a = {
        "no_cook_errors": not errors,
        "all_expected_layers": not missing,
        "unreal_attrs_on_height": bool(h.attribValue("unreal_material")),
        "bounds_match_window": abs((xmax - xmin) - hda.parm("window_m").eval()) < 6.0 and abs((zmax - zmin) - hda.parm("window_m").eval()) < 6.0,
        "house_pad_flat": all(abs(v - pad_e) < 0.03 for k, v in pad_samples.items()),
        "near_field_gentle": float(near.max()) - float(near.min()) < 3.0,
        "view_horizon_ge_14m": bool(far_view.size and float(far_view.max()) >= 14.0),
        "offview_lower_than_view": bool(far_view.size and far_off.size and float(far_off.max()) < float(far_view.max())),
        "preview_cook_under_3s": cook_s < 3.0,
    }
    # ---- H4 paths / H5 caves (read from the extra outputs; world-space)
    pg = hda.node("OUT_PATH_CURVES").geometry()
    cg = hda.node("OUT_CAVE_POINTS").geometry()
    npaths, ncaves = hda.parm("path_count").eval(), hda.parm("cave_count").eval()
    L = hda.parm("path_length_m").eval()
    wl = hda.parm("water_level").eval()
    path_stats = []
    all_slopes, wet = [], 0
    n_cave_pts = len(cg.points())
    for pr in pg.prims():
        pts = [v.point().position() for v in pr.vertices()]
        rmax = max(math.hypot(p[0] - cx, p[2] - cz) for p in pts)
        guided = pr.attribValue("path_id") < n_cave_pts
        endp = pts[-1]
        for p in pts:
            if h.sample((p[0], 0.0, p[2])) < wl + 0.2:
                wet += 1
            if guided and math.hypot(p[0] - endp[0], p[2] - endp[2]) < 40.0:
                continue
            d = 4.0
            gx = (h.sample((p[0] + d, 0.0, p[2])) - h.sample((p[0] - d, 0.0, p[2]))) / (2 * d)
            gz = (h.sample((p[0], 0.0, p[2] + d)) - h.sample((p[0], 0.0, p[2] - d))) / (2 * d)
            all_slopes.append(math.hypot(gx, gz))
        path_stats.append({"id": pr.attribValue("path_id"), "points": len(pts), "start": [round(pts[0][0], 1), round(pts[0][2], 1)], "end": [round(endp[0], 1), round(endp[2], 1)], "guided": guided, "r_max_m": round(rmax, 1)})
    cave_pts = [(p.position()[0], p.position()[2], p.position()[1], p.attribValue("slope")) for p in cg.points()]
    min_sep = min([math.hypot(a1[0] - b1[0], a1[1] - b1[1]) for i, a1 in enumerate(cave_pts) for b1 in cave_pts[i + 1:]] or [999.0])
    report["paths"] = {"count": len(path_stats), "stats": path_stats, "slope_p95": round(float(np.percentile(all_slopes, 95)), 3) if all_slopes else None, "wet_points": wet,
                       "coverage_pct": round(float(grid(vols["Path"]).mean()) * 100.0, 2)}
    report["caves"] = {"count": len(cave_pts), "points_xz_h_slope": [[round(c[0], 1), round(c[1], 1), round(c[2], 1), round(c[3], 3)] for c in cave_pts], "min_separation_m": round(min_sep, 1)}
    a["paths_count_ok"] = len(path_stats) == npaths
    a["free_paths_reach_far"] = all(ps["r_max_m"] >= 0.8 * L for ps in path_stats if not ps["guided"])
    a["paths_gentle_p95_under_0_30"] = (report["paths"]["slope_p95"] or 0.0) <= 0.30
    a["paths_stay_dry"] = wet == 0
    a["paths_start_at_porch"] = all(math.hypot(ps["start"][0] - hda.parm("path_start_x").eval(), ps["start"][1] - hda.parm("path_start_z").eval()) < 2.0 for ps in path_stats)
    a["caves_count_ok"] = len(cave_pts) == ncaves
    a["caves_on_flank_slopes"] = all(c[3] >= 0.26 and c[2] > -50 for c in cave_pts)
    a["caves_spaced_40m"] = min_sep >= 40.0
    # ---- sightlines from the porch eye (guide = paths, release = cave mouths)
    ex_, ez_ = hda.parm("path_start_x").eval(), hda.parm("path_start_z").eval()
    ey_ = hda.parm("pad_elevation").eval() + hda.parm("eye_height_m").eval()

    def visible(tx, ty, tz, step=3.0):
        d = math.hypot(tx - ex_, tz - ez_)
        n = max(2, int(d / step))
        for i in range(1, n):
            t = i / float(n)
            if h.sample((ex_ + (tx - ex_) * t, 0.0, ez_ + (tz - ez_) * t)) > ey_ + (ty - ey_) * t - 0.3:
                return False
        return True

    cave_vis = [visible(c[0], c[2] + 2.0, c[1]) for c in cave_pts]
    path_end_vis, path_vis_frac = [], []
    for pr in pg.prims():
        pts = [v.point().position() for v in pr.vertices()]
        vis = [visible(p[0], h.sample((p[0], 0.0, p[2])) + 1.0, p[2]) for p in pts[2:]]
        path_end_vis.append(bool(vis and vis[-1]))
        path_vis_frac.append(round(sum(vis) / float(max(1, len(vis))), 3))
    report["sightlines"] = {"eye": [ex_, round(ey_, 2), ez_], "caves_visible": cave_vis, "path_end_visible": path_end_vis, "path_visible_fraction": path_vis_frac}
    a["caves_visible_from_porch"] = bool(cave_pts) and all(cave_vis)
    a["path_starts_read_from_porch"] = all(f >= 0.25 for f in path_vis_frac) if path_vis_frac else True
    k_guided = min(len(path_stats), len(cave_pts))
    a["guided_paths_end_at_visible_caves"] = all(math.hypot(path_stats[i]["end"][0] - cave_pts[i][0], path_stats[i]["end"][1] - cave_pts[i][1]) < 12.0 and cave_vis[i] for i in range(k_guided)) if k_guided else True

    report["assertions"] = a
    return arr, a, vols


def drive_probe(hda, report):
    """The live-parameter proof: change a promoted parm on the TYPE and the output must change."""
    import numpy as np
    base = float(grid(heights(hda)[1]["height"]).max())
    old = hda.parm("horizon_amp").eval()
    hda.parm("horizon_amp").set(old * 0.5)
    hda.cook(force=True)
    half = float(grid(heights(hda)[1]["height"]).max())
    hda.parm("horizon_amp").set(old)
    hda.cook(force=True)
    report["parm_drive"] = {"parm": "horizon_amp", "max_height_at_full": round(base, 2), "max_height_at_half": round(half, 2), "differ": abs(base - half) > 1.0}
    report["assertions"]["live_parameter_drive"] = report["parm_drive"]["differ"]


def hillshade(arr, path, cell_m, path_arr=None, caves_ij=None):
    import numpy as np
    import png_io
    gy, gx = np.gradient(arr, cell_m)
    az, alt = math.radians(315.0), math.radians(40.0)
    sx, sy = -gx, -gy
    shade = (np.sin(alt) + np.cos(alt) * (sx * math.cos(az) + sy * math.sin(az)) * 6.0)
    shade = np.clip(shade, 0.0, 1.0)
    rel = (arr - arr.min()) / max(1e-6, arr.max() - arr.min())
    rgb = np.stack([shade * (0.55 + 0.45 * rel), shade * (0.70 + 0.2 * rel), shade * (0.50 + 0.1 * rel)], axis=-1)
    if path_arr is not None:
        m = np.clip(path_arr * 1.5, 0.0, 1.0)[..., None]
        rgb = rgb * (1.0 - m) + np.array([1.0, 0.25, 0.2]) * m
    for (i, j) in (caves_ij or []):
        rgb[max(0, j - 2):j + 3, max(0, i - 2):i + 3] = 1.0
    png_io.save(str(path), (np.clip(rgb, 0, 1) * 255).astype(np.uint8))


def main():
    if not IGN_TIFF.is_file() or IGN_TIFF.stat().st_size < 1000000:
        raise RuntimeError("Full IGN RGE ALTI GeoTIFF is unavailable: %s" % IGN_TIFF)
    STAGE.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "MelodiaHouseTerrain")
    for c in geo.children():
        c.destroy()
    controls = build_network(geo)
    pairs = promote.stage1_promote(controls, geo, NAMES, hou)
    promote.stage1_wire(controls, pairs, hou)
    for inner, promoted in pairs:
        template = controls.parmTemplateGroup().find(inner)
        if isinstance(template, hou.StringParmTemplate):
            controls.parm(inner).setExpression('chs("../%s")' % promoted, hou.exprLanguage.Hscript)
    hda = geo.createDigitalAsset(name=TYPE_NAME, hda_file_name=str(HDA_PATH), description="Melodia House Terrain (pad + horizon)", min_num_inputs=0, max_num_inputs=0, version="2.0")
    promote.stage2_promote_definition(hda, pairs, HDA_PATH, hou)
    hda.matchCurrentDefinition()
    hda.parm("source_filepath").set(str(IGN_TIFF))

    report = {"asset": str(HDA_PATH), "type": TYPE_NAME, "house_footprint_m": HOUSE, "pad_margin_m": PAD_MARGIN, "controls": {k: hda.parm(k).eval() for k in NAMES}}
    arr, a, vols = gate(hda, report)
    drive_probe(hda, report)
    cell = hda.parm("window_m").eval() / hda.parm("preview_resolution").eval()
    try:
        oh, xs, zs, _e, var = oriented(vols["height"])
        op = oriented(vols["Path"], var)[0]
        cg = hda.node("OUT_CAVE_POINTS").geometry()
        ny = oh.shape[0]
        caves_ij = []
        for pt in cg.points():
            ci = int(round((pt.position()[0] - xs[0]) / (xs[-1] - xs[0]) * (len(xs) - 1)))
            cj = int(round((pt.position()[2] - zs[0]) / (zs[-1] - zs[0]) * (len(zs) - 1)))
            caves_ij.append((ci, ny - 1 - cj))
        hillshade(oh[::-1, :], AUDIT / "hillshade.png", cell, path_arr=op[::-1, :], caves_ij=caves_ij)
        report["hillshade"] = str(AUDIT / "hillshade.png")
    except Exception as e:
        report["hillshade_error"] = str(e)
    (AUDIT / "terrain_gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    hou.hipFile.save(str(AUDIT / "MelodiaHouseTerrain.hip"))
    failed = [k for k, v in report["assertions"].items() if not v]
    print("GATE " + json.dumps({"failed": failed, "assertions": report["assertions"], "cook_seconds": report["cook_seconds"], "height_min_max_m": report["height_min_max_m"], "near_field_r70": report["near_field_min_max_m"], "view_max": report["view_horizon_band_max_m"], "offview_max": report["offview_horizon_band_max_m"]}))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
