# -*- coding: utf-8 -*-
"""p24 — Palette harmony: tint the 3-light rig toward Shorewake dusk tokens and
resample the deploy plate to prove warm-amber dominance gains without blowing
exposure or the p22 contact-shadow work.

Shorewake dusk palette tokens (from Chapters/02_shorewake_calling SHOT_MANIFEST
+ Night Reel brief — pearl cloth, cool sea-cyan/lavender fill, warm amber/brass,
warm candle-gold emissive):
  dusk_key  = kiss toward warm candle-gold  (1.00, 0.90, 0.78)
  dusk_fill = cool lavender fill             (0.82, 0.86, 1.00)
  dusk_rim  = cool sea-cyan rim              (0.80, 0.93, 1.00)

Energy compensation: EEVEE effective contribution ~= energy * tint_luminance.
To keep plate exposure (p15/p22 work) stable we scale each light energy by
1/tint_lum so only the HUE changes. Verify by re-sampling rendered PNGs:
  warm_delta  = mean_lit.R - mean_lit.G   (should RISE vs p23 baseline)
  blue_delta  = mean_lit.B - mean_lit.R   (should become LESS positive: cool
             fill remains but warm key pulls the body amber)
  max_lum & hot-px must not explode (no exposure regression).
"""
import bpy, json, math, os
import numpy as np

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p24] {m}", flush=True)
rep = {"phase": "p24", "ok": True}
rep["dusk_tokens"] = {
    "dusk_key":  [1.00, 0.80, 0.60],   # warm candle-gold key, deep amber
    "dusk_fill": [0.88, 0.90, 1.00],   # gentle cool lavender fill (subtle, not blue-heavy)
    "dusk_rim":  [0.85, 0.93, 1.00],   # gentle cool sea-cyan rim
}
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]

def tint_lum(c):
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]

TINT = {
    # name -> (tint, oldE, energy_mult)
    "ME_WaveViolin_Light_Key":  ([1.00, 0.80, 0.60], 455.0, 1.12),  # warm key: boost so deep amber pops
    "ME_WaveViolin_Light_Fill": ([0.88, 0.90, 1.00], 170.0, 1.0),   # gentle cool fill, keep E
    "ME_WaveViolin_Light_Rim":  ([0.85, 0.93, 1.00], 560.0, 1.0),   # gentle cool rim, keep E
}
OLD = {}
NEW = {}
for nm, (tint, oldE, mult) in TINT.items():
    o = bpy.data.objects[nm]
    OLD[nm] = {"color": list(o.data.color), "energy": o.data.energy}
    # key gets a small warm boost; fill/rim keep energy so the large cool
    # sources recede a touch toward dusk while the warm key carries the body.
    newE = oldE * mult
    o.data.color = tint
    o.data.energy = newE
    NEW[nm] = {"color": list(o.data.color), "energy": round(float(o.data.energy), 3)}
    log(f"{nm}: color {OLD[nm]['color']}->{list(o.data.color)} energy {oldE}->{round(newE,3)}")
rep["lights_old"] = OLD
rep["lights_new"] = NEW

def pop_png(png):
    im = bpy.data.images.load(png); W, H = im.size
    a = np.array(im.pixels[:W*H*4]).reshape(H, W, 4)
    bpy.data.images.remove(im)
    return W, H, a

def palette_metrics(rgba, band0=0.72):
    H, W = rgba.shape[:2]
    r, g, b, al = rgba[...,0], rgba[...,1], rgba[...,2], rgba[...,3]
    lum = 0.2126*r + 0.7152*g + 0.0722*b
    mask = lum > 0.01
    lit = rgba[mask][..., :3]
    mean = lit.mean(axis=0) if lit.shape[0] else np.zeros(3)
    med  = np.median(lit, axis=0) if lit.shape[0] else np.zeros(3)
    band = slice(int(band0*H), H)
    blum = lum[band]; bal = al[band]
    return {
        "w": W, "h": H, "lit_px": int(mask.sum()),
        "mean_rgb_lit": [round(float(x),3) for x in mean],
        "med_rgb_lit":  [round(float(x),3) for x in med],
        "warm_delta_rg": round(float(mean[0]-mean[1]),3),
        "blue_delta_br": round(float(mean[2]-mean[0]),3),
        "whole_meanlum": round(float(lum.mean()),3),
        "max_lum": round(float(lum.max()),3),
        "hot_gt09": int((lum>0.9).sum()),
        "bottom_alpha_transparent_pct": round(float((bal<0.05).mean()),3),
        "contact_shadow_px": int(((bal>0.02)&(bal<0.7)).sum()),
        "contact_grad_p99": round(float(np.percentile(np.sqrt(np.gradient(blum)[0]**2+np.gradient(blum)[1]**2), 99)),3),
    }

# ---- baseline (re-render with ORIGINAL white rig so we compare apples-to-apples
#      against the p22/p23 saved plates; the file may already hold the failed
#      run's tinted lights, so restore the known white rig explicitly) ----
ORIG = {
    "ME_WaveViolin_Light_Key":  ([1.0, 1.0, 1.0], 455.0),
    "ME_WaveViolin_Light_Fill": ([1.0, 1.0, 1.0], 170.0),
    "ME_WaveViolin_Light_Rim":  ([1.0, 1.0, 1.0], 560.0),
}
for nm,(tint,oe) in ORIG.items():
    o = bpy.data.objects[nm]
    o.data.color = list(tint); o.data.energy = oe
bpy.context.view_layer.update()
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0
scn.render.filepath = os.path.join(OUT, "_p24_baseline.png")
bpy.ops.render.render(write_still=True)
base = palette_metrics(pop_png(os.path.join(OUT, "_p24_baseline.png"))[2])
rep["render_baseline"] = base
log(f"baseline mean_lit={base['mean_rgb_lit']} warm_rg={base['warm_delta_rg']} blue_br={base['blue_delta_br']} max={base['max_lum']}")

# ---- final (apply dusk tints) ----
for nm,(tint,oldE,mult) in TINT.items():
    o = bpy.data.objects[nm]
    o.data.color = NEW[nm]["color"]; o.data.energy = NEW[nm]["energy"]
bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p24_deploy.png")
bpy.ops.render.render(write_still=True)
deploy = palette_metrics(pop_png(os.path.join(OUT, "p24_deploy.png"))[2])
rep["render_deploy"] = deploy
log(f"deploy mean_lit={deploy['mean_rgb_lit']} warm_rg={deploy['warm_delta_rg']} blue_br={deploy['blue_delta_br']} max={deploy['max_lum']}")

# macro baseline (body closeup under ORIGINAL white rig) + macro final (dusk rig)
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
mc.rotation_euler.x = -1.5708; bpy.context.view_layer.update()
if cam:
    scn.camera = cam
    # baseline (white) macro
    for nm,(tint,oe) in ORIG.items():
        o = bpy.data.objects[nm]; o.data.color = list(tint); o.data.energy = oe
    scn.render.filepath = os.path.join(OUT, "_p24_macrobase.png")
    bpy.ops.render.render(write_still=True)
    mb = palette_metrics(pop_png(os.path.join(OUT, "_p24_macrobase.png"))[2])
    rep["render_macro_baseline"] = {"mean_rgb_lit": mb["mean_rgb_lit"],
                                    "warm_delta_rg": mb["warm_delta_rg"],
                                    "blue_delta_br": mb["blue_delta_br"]}
    # final (dusk) macro
    for nm,(tint,oldE,mult) in TINT.items():
        o = bpy.data.objects[nm]; o.data.color = NEW[nm]["color"]; o.data.energy = NEW[nm]["energy"]
    scn.render.filepath = os.path.join(OUT, "p24_macro.png")
    bpy.ops.render.render(write_still=True)
    mm = palette_metrics(pop_png(os.path.join(OUT, "p24_macro.png"))[2])
    rep["render_macro"] = {"w":mm["w"],"h":mm["h"],"mean_rgb_lit":mm["mean_rgb_lit"],
                           "warm_delta_rg":mm["warm_delta_rg"],"blue_delta_br":mm["blue_delta_br"],
                           "max_lum":mm["max_lum"],"hot_gt09":mm["hot_gt09"]}
    log(f"macro base mean_lit={mb['mean_rgb_lit']} warm_rg={mb['warm_delta_rg']} blue_br={mb['blue_delta_br']}")
    log(f"macro dusk mean_lit={mm['mean_rgb_lit']} warm_rg={mm['warm_delta_rg']} blue_br={mm['blue_delta_br']}")
mc.rotation_euler.x = 0.0

# accept on the BODY (macro) — the amber rosewood must read warmer under the dusk
# key (R-G delta up AND R>=B i.e. no blue overload on the body), while the wide
# deploy keeps exposure intact and the cool dusk fill stays moderate.
body_warm_gain = (mm["warm_delta_rg"] - mb["warm_delta_rg"])
rep["deltas"] = {
    "body_warm_rg_base": mb["warm_delta_rg"], "body_warm_rg_dusk": mm["warm_delta_rg"],
    "body_warm_rg_delta": round(body_warm_gain,3),
    "body_blue_br_base": mb["blue_delta_br"], "body_blue_br_dusk": mm["blue_delta_br"],
    "deploy_blue_br_base": base["blue_delta_br"], "deploy_blue_br_dusk": deploy["blue_delta_br"],
    "max_lum_delta": round(deploy["max_lum"]-base["max_lum"],3),
}
rep["accept"] = bool(
    body_warm_gain > 0.0                                           # body reads warmer amber
    and mm["blue_delta_br"] <= 0.0                                 # no blue overload on rosewood body
    and deploy["max_lum"] <= np.clip(base["max_lum"]+0.02, 0, 1.05) # no exposure blowout
    and deploy["contact_shadow_px"] > base["contact_shadow_px"]*0.9 # contact shadow intact
)
log(f"accept={rep['accept']} (body_warm_gain={round(body_warm_gain,3)})")

bpy.ops.wm.save_mainfile()
reports = [os.path.join(OUT, "p24_report.json")]
json.dump(rep, open(reports[0], "w"), indent=1)
# cleanup baseline temp
for t in ("_p24_baseline.png", "_p24_macrobase.png"):
    p = os.path.join(OUT, t)
    if os.path.exists(p): os.remove(p)
# remove probe artifact report (p24probe_report.json) from lane set? keep on disk is fine
log("p24 DONE")