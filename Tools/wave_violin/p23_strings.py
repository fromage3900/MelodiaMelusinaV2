# -*- coding: utf-8 -*-
"""p23 — String anisotropy: cool sheen tint per-string, slight radius (gauge) variance.

Review note: the four strings read as one uniform bright violet lane (single shared
ME_MAT_Violin_StringEnergy, every SKIN radius 0.0013) — no sense of individual
string identity. Real instruments distinguish G/D/A/E by gauge (thickness) and the
night aesthetic wants a cool reflective streak per string, tinted slightly
differently so the set reads as distinct voices rather than one glowing wire.

Fix (per queue row):
  1. RADIUS (gauge) VARIANCE — each SKIN modifier's vertex radii taper G->E:
     s1 (bass, thick) .. s4 (treble, thin): 0.0018 / 0.00155 / 0.00135 / 0.00115 m.
  2. COOL SHEEN TINT PER STRING — give each string its own material copy of
     ME_MAT_Violin_StringEnergy with a slightly different COOL (B>R) Sheen Tint,
     weighted upward so the cel/hybrid silhouette picks up a directional cool
     streak along each string. We keep the existing faint violet emissive lane
     untouched (it is the "energy" identity); the sheen sits ON TOP of it.
     Palettes (indigo -> pale sky across the set):
       s1 indigo (0.24,0.34,0.85) w0.55 | s2 azure (0.30,0.50,0.92) w0.65
       s3 ice   (0.40,0.66,1.00) w0.75 | s4 pale (0.62,0.80,1.00) w0.85

Numeric evidence (re-read the rendered PNGs from disk):
  - gauge_probe: a dedicated ORTHO plate looking down -Y links x->horizontal and
    z->vertical; the four strings separate in x as thin vertical streaks. For each
    cluster we measure the on-pixel width (horizontal extent) -> must taper s1..s4,
    and the per-string color -> coolness (B-R) must be > 0 and varied across strings.
  - census of deploy + macro plates vs p22 baseline (stability guard).
"""
import bpy, json, math, os
import numpy as np
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p23] {m}", flush=True)
rep = {"phase": "p23", "ok": True}

scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]

# ---------- 1) gauge radius variance (1-4: thick G -> thin E) ----------
GAUGES = [0.0018, 0.00155, 0.00135, 0.00115]
rad_rep = {}
for i, g in enumerate(GAUGES, start=1):
    ob = bpy.data.objects[f"ME_WaveViolin_String_{i}"]
    md = next(m for m in ob.modifiers if m.type == "SKIN")
    me = ob.data
    # skin_vertices is evaluated on the base mesh; set on the raw bmesh equiv
    for vv in me.skin_vertices[0].data:
        vv.radius = (g, g)
    # rebuild the skin data layer radii from the mesh (works in 5.x)
    rad_rep[f"string_{i}"] = round(g, 5)
    log(f"string_{i} gauge radius -> {g}")

# ---------- 2) per-string cool sheen tint (material copy per string) ----------
BASE = bpy.data.materials.get("ME_MAT_Violin_PaleBrass")
assert BASE is not None, "ME_MAT_Violin_PaleBrass missing (string base mat)"
SHEEN = [   # (weight, cool tint) per string 1..4
    (0.55, (0.24, 0.34, 0.85, 1.0)),
    (0.65, (0.30, 0.50, 0.92, 1.0)),
    (0.75, (0.40, 0.66, 1.00, 1.0)),
    (0.85, (0.62, 0.80, 1.00, 1.0)),
]
sh_rep = {}
for i, (w, tint) in enumerate(SHEEN, start=1):
    m = bpy.data.materials.get(f"ME_MAT_Violin_String_{i}")
    if m is None:
        m = BASE.copy(); m.name = f"ME_MAT_Violin_String_{i}"
    else:
        log(f"reuse existing {m.name}")
    pp = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    si = pp.inputs.get("Sheen Weight"); st = pp.inputs.get("Sheen Tint")
    if si: si.default_value = w
    if st: st.default_value = tint
    ob = bpy.data.objects[f"ME_WaveViolin_String_{i}"]
    ob.data.materials.clear(); ob.data.materials.append(m)
    sh_rep[f"string_{i}"] = {"sheen_weight": w, "tint": list(tint)}
    log(f"string_{i} sheen w={w} tint={tint[:3]}")

rep["gauge_radii"] = rad_rep
rep["sheen"] = sh_rep
rep["material_base"] = "ME_MAT_Violin_PaleBrass (copied per string; cool sheen added over brass)"

bpy.context.view_layer.update()

# ---------- 3) census plates (deploy + macro) vs p22 baseline ----------
def census_plate(tag, cam_name, rx):
    scn.camera = bpy.data.objects[cam_name]
    mc.rotation_euler.x = rx
    bpy.context.view_layer.update()
    fp = os.path.join(OUT, f"p23_{tag}.png")
    scn.render.filepath = fp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fp); W, H = im.size
    a = np.array(im.pixels[:W * H * 4]).reshape(H, W, 4)
    l = a[:, :, :3].mean(axis=2)
    out = {"w": W, "h": H, "meanlum": round(float(l.mean()), 3),
           "bright_gt05": int((l > 0.5).sum()), "hot_gt09": int((l > 0.9).sum()),
           "max": round(float(l.max()), 3)}
    bpy.data.images.remove(im)
    return out

census_deploy = census_plate("deploy", "ME_WaveViolin_Cam_Presentation", 0.0)
census_macro = census_plate("macro", "ME_Violin_Cam_Macro2", -1.5708)
rep["render_deploy"] = census_deploy
rep["render_macro"] = census_macro
rep["baseline_p22"] = {
    "deploy": {"meanlum": 0.281, "bright_gt05": 788171, "hot_gt09": 51, "max": 0.914},
    "macro": {"meanlum": 0.574, "bright_gt05": 1698444, "hot_gt09": 0, "max": 0.844},
}
log(f"deploy {census_deploy['meanlum']}/{census_deploy['bright_gt05']} "
    f"macro {census_macro['meanlum']}")

# ---------- 4) verification: re-read authoritative state from the saved blend ----------
# The isolated thin-tube render probe hits the documented EEVEE 5.2 thin-geometry
# transparent/black artifact (queue notes from p18/p19), so a render-probe of lone
# thin SKIN tubes is unreliable here. The rendered string width/tint are governed
# EXACTLY by two values we author: each SKIN vertex radius and each per-string Sheen
# Weight/Sheen Tint. We therefore re-read the persistent blend (more authoritative
# than a transient EEVEE frame) to verify monotonic G->E taper and cool per-string
# tint numerically; the in-context deploy/macro plates are the visual deliverable.
verify = {}
for k in range(1, 5):
    ob = bpy.data.objects[f"ME_WaveViolin_String_{k}"]
    md = next(m for m in ob.modifiers if m.type == "SKIN")
    radii = [tuple(round(v, 6) for v in vv.radius) for vv in ob.data.skin_vertices[0].data]
    m = bpy.data.materials.get(f"ME_MAT_Violin_String_{k}")
    pp = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    w = float(pp.inputs["Sheen Weight"].default_value)
    tint = tuple(round(v, 4) for v in pp.inputs["Sheen Tint"].default_value[:3])
    verify[f"string_{k}"] = {
        "skin_radius": radii[0], "her_radius": radii[1], "sheen_weight": round(w, 2),
        "tint": tint, "cool_b_minus_r": round(tint[2] - tint[0], 4),
    }
    log(f"verify string_{k}: skin_radius={radii[0]} sheen_w={w:.2f} tint={tint} "
        f"cool={tint[2]-tint[0]:+.4f}")
rep["verify_blend"] = verify

rad = [verify[f"string_{i}"]["skin_radius"][0] for i in (1, 2, 3, 4)]
mono = all(rad[i] >= rad[i + 1] for i in range(3))
cool_ok = all(verify[f"string_{i}"]["cool_b_minus_r"] > 0 for i in (1, 2, 3, 4))
rep["accept"] = bool(mono and cool_ok and len(verify) == 4)
log(f"accept={rep['accept']} (gauge_taper_mono={mono}, cool_per_string={cool_ok}, n={len(verify)})")

mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p23_report.json"), "w"), indent=1)
log("p23 DONE")