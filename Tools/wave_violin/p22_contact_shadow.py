# -*- coding: utf-8 -*-
"""p22 — Contact shadow: shadow-catcher ground + tighter key angle.

Review finding ("fluffy contact"): the deploy plate's only base is an OPAQUE
dark ground slab (ME_MAT_Violin_Ground, rough 0.95, base ~(0.16,0.13,0.2)) that
flattens the whole bottom band to ~0.28 lum — the model reads as sitting on a
uniform dark plane with no readable contact. The world is pure black, so the
slab is the sole grounding cue.

Fix (per queue row):
  1. SHADOW-CATCHER GROUND — set me_WaveViolin_Ground.is_shadow_catcher=True and
     render with transparent film, so the slab disappears and ONLY the model's
     real key-light contact shadow remains at the base. EEVEE honors the catcher
     (probe: bottom-band alpha 0.91 transparent, shadow alpha ~0.084).
  2. TIGHTER KEY — key is AREA size 0.6 @ (1.4,-1.8,1.55) e430: a broad soft
     source => wide "fluffy" penumbra. Shrink to 0.22 (crisper shadow edge),
     rake more over-head (x->1.15, z->1.75) so the shadow shortens and tightens
     under the base. Catcher + transparent film make the tightened shadow the
     only grounding.

Numeric evidence (verify by re-reading rendered PNGs from disk):
  - slab_gone: bottom-band % transparent alpha rises to ~0.9, mean alpha drops.
  - contact_shadow_present: bottom band holds a contiguous semi-shadow region.
  - sharpness: 99th-pct luminance gradient in the bottom contact band is HIGHER
    with the tightened key than with the old (soft) key — proven by rendering
    the contact band twice (key_old vs key_final) and diffing the gradient.
"""
import bpy, json, math, os
import numpy as np

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p22] {m}", flush=True)
rep = {"phase": "p22", "ok": True}

scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]

# ---------- 1) shadow-catcher ground + transparent film ----------
ground = bpy.data.objects["ME_WaveViolin_Ground"]
ground.is_shadow_catcher = True
scn.render.film_transparent = True
rep["ground_catcher"] = {
    "object": ground.name,
    "is_shadow_catcher": bool(ground.is_shadow_catcher),
    "film_transparent": True,
    "material": "ME_MAT_Violin_Ground (now pure catcher, opaque slab removed)",
}

# ---------- 2) key light: capture original, tighten ----------
key = bpy.data.objects["ME_WaveViolin_Light_Key"]
KEY_OLD = {"size": 0.6, "loc": (1.4, -1.8, 1.55), "energy": 430.0}   # literal original (disk may already be tightened)
KEY_FINAL = {"size": 0.22, "loc": (1.15, -1.8, 1.75), "energy": 455.0}
key.data.size = KEY_FINAL["size"]
key.location = KEY_FINAL["loc"]
key.data.energy = KEY_FINAL["energy"]
rep["key_old"] = KEY_OLD
rep["key_final"] = KEY_FINAL
log(f"key tightened {KEY_OLD} -> {KEY_FINAL}")

def pop_png(png):
    im = bpy.data.images.load(png); W, H = im.size
    a = np.array(im.pixels[:W*H*4]).reshape(H, W, 4)
    bpy.data.images.remove(im)
    return W, H, a

def shadow_metrics(rgba, band0=0.72):
    H, W = rgba.shape[:2]
    r, g, b, al = rgba[...,0], rgba[...,1], rgba[...,2], rgba[...,3]
    lum = 0.2126*r + 0.7152*g + 0.0722*b
    band = slice(int(band0*H), H)
    blum = lum[band]; bal = al[band]
    gy, gx = np.gradient(blum)
    gmag = np.sqrt(gx**2 + gy**2)
    return {
        "w": W, "h": H,
        "whole_meanlum": round(float(lum.mean()),3),
        "bottom_meanlum": round(float(blum.mean()),3),
        "bottom_alpha_mean": round(float(bal.mean()),3),
        "bottom_alpha_transparent_pct": round(float((bal<0.05).mean()),3),   # slab-gone proxy
        "contact_shadow_px": int(((bal>0.02)&(bal<0.7)).sum()),              # semi-shadow footprint
        "bright_gt05": int((lum>0.5).sum()), "hot_gt09": int((lum>0.9).sum()),
        "max": round(float(lum.max()),3),
        "contact_grad_p99": round(float(np.percentile(gmag, 99)),3),         # shadow-edge crispness
        "contact_grad_mean": round(float(gmag.mean()),3),
    }

# ---------- render contact band with ORIGINAL key (prove tightening matters) ----------
# keep catcher + transparent film so the band measures the shadow, only swap key back
key.data.size = KEY_OLD["size"]; key.location = KEY_OLD["loc"]; key.data.energy = KEY_OLD["energy"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.render.filepath = os.path.join(OUT, "_p22_keyold.png")
bpy.ops.render.render(write_still=True)
old_m = shadow_metrics(pop_png(os.path.join(OUT,"_p22_keyold.png"))[2])
rep["contact_key_old"] = old_m

# ---------- render deploy + macro with tightened key ----------
key.data.size = KEY_FINAL["size"]; key.location = KEY_FINAL["loc"]; key.data.energy = KEY_FINAL["energy"]
bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p22_deploy.png")
bpy.ops.render.render(write_still=True)
deploy_m = shadow_metrics(pop_png(os.path.join(OUT,"p22_deploy.png"))[2])
rep["render_deploy"] = deploy_m
log(f"deploy: whole_lum={deploy_m['whole_meanlum']} bottom_alpha_trans={deploy_m['bottom_alpha_transparent_pct']} "
    f"shadow_px={deploy_m['contact_shadow_px']} grad99={deploy_m['contact_grad_p99']}")

# macro body plate (body-only closeup; ground out of frame)
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
mc.rotation_euler.x = -1.5708; bpy.context.view_layer.update()
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p22_macro.png")
    bpy.ops.render.render(write_still=True)
    mm = shadow_metrics(pop_png(os.path.join(OUT,"p22_macro.png"))[2])
    rep["render_macro"] = {"w":mm["w"],"h":mm["h"],"meanlum":mm["whole_meanlum"],
                           "bright_gt05":mm["bright_gt05"],"hot_gt09":mm["hot_gt09"],"max":mm["max"]}

mc.rotation_euler.x = 0.0
rep["contact_delta"] = {
    "shadow_px_keyold": old_m["contact_shadow_px"],
    "shadow_px_final":  deploy_m["contact_shadow_px"],
    "grad99_keyold":    old_m["contact_grad_p99"],
    "grad99_final":     deploy_m["contact_grad_p99"],
    "slab_gone_final":  deploy_m["bottom_alpha_transparent_pct"],
}
rep["accept"] = bool(
    deploy_m["bottom_alpha_transparent_pct"] > 0.85          # slab gone
    and deploy_m["contact_shadow_px"] > 4000                 # real shadow present (~4.5k)
    and deploy_m["contact_grad_p99"] > old_m["contact_grad_p99"])  # tighter -> crisper
log(f"accept={rep['accept']}")

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p22_report.json"), "w"), indent=1)
# cleanup temp
for t in ("_p22_keyold.png",): 
    p = os.path.join(OUT, t)
    if os.path.exists(p): os.remove(p)
log("p22 DONE")