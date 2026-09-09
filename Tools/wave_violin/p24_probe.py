# -*- coding: utf-8 -*-
"""p24 probe — dump the 3-light rig + world, and sample the existing deploy plate
mean colors so the palette-harmony nudge can be designed against measured data."""
import bpy, json, os
import numpy as np

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)

rep = {"phase": "p24probe", "ok": True}
scn = bpy.context.scene
print("[p24probe] world name:", scn.world.name if scn.world else "NONE", flush=True)
if scn.world:
    w = scn.world
    rep["world"] = {"name": w.name,
                    "use_nodes": w.use_nodes,
                    "color": list(w.color) if hasattr(w, 'color') else None}
    if w.use_nodes:
        def walk(n, d=0):
            lines = []
            for i in w.node_tree.nodes:
                if i.type == 'BACKGROUND':
                    bg = i.inputs['Color'].default_value[:3] if i.inputs['Color'].default_value else None
                    st = i.inputs['Strength'].default_value if 'Strength' in i.inputs else None
                    lines.append({"node": i.name, "color": list(bg) if bg is not None else None,
                                  "strength": st})
            return lines
        rep["world_bg"] = walk(w)

# lights
lum = []
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        d = o.data
        lum.append({
            "name": o.name, "type": d.type,
            "energy": d.energy, "color": list(d.color),
            "loc": list(o.location), "rot": list(o.rotation_euler),
            "size": getattr(d, "size", None),
            "size_x": getattr(d, "size_x", None), "size_y": getattr(d, "size_y", None),
            "angle": getattr(d, "angle", None),
            "visible": not o.hide_viewport,
        })
rep["lights"] = lum
for L in lum:
    print(f"[p24probe] LIGHT {L['name']} {L['type']} energy={L['energy']} color={L['color']} loc={L['loc']} size={L['size']}", flush=True)

# cameras
cams = [o.name for o in bpy.data.objects if o.type == 'CAMERA']
rep["cams"] = cams
print("[p24probe] cams:", cams, flush=True)

# sample existing deploy plate if present
def pop_png(png):
    im = bpy.data.images.load(png); W, H = im.size
    a = np.array(im.pixels[:W*H*4]).reshape(H, W, 4)
    bpy.data.images.remove(im)
    return W, H, a

for f in ("p23_deploy.png", "p22_deploy.png"):
    p = os.path.join(OUT, f)
    if os.path.exists(p):
        W, H, rgba = pop_png(p)
        r, g, b = rgba[...,0], rgba[...,1], rgba[...,2]
        lumrgb = 0.2126*r+0.7152*g+0.0722*b
        mask = lumrgb > 0.01
        if mask.sum() > 0:
            lit = rgba[mask]
            mean = lit[...,:3].mean(axis=0)
            med = np.median(lit[...,:3], axis=0)
        else:
            mean = med = [0,0,0]
        rep[f] = {"w":W,"h":H,
                  "lit_px": int(mask.sum()),
                  "mean_rgb_lit": [round(float(x),3) for x in mean],
                  "med_rgb_lit":  [round(float(x),3) for x in med],
                  "whole_mean_rgb": [round(float(r.mean()),3),round(float(g.mean()),3),round(float(b.mean()),3)]}
        print(f"[p24probe] {f}: WxH={W}x{H} lit_px={mask.sum()} mean_lit={mean.round(3)} med_lit={med.round(3)}")

json.dump(rep, open(os.path.join(OUT, "p24probe_report.json"), "w"), indent=1)
print("[p24probe] DONE", flush=True)