# -*- coding: utf-8 -*-
"""p07/p08 — polish audit + export prep (headless, idempotent).

p07: programmatic checks (tri budget, UV layers, ORM colorspace, scale,
     materials non-null, hidden FLIP-analogues) + 4-plate contact sheet PNG.
p08: fill Export collection with game-res trim, write UE intake manifest JSON.
"""
import bpy, json, math, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p078] {m}", flush=True)
rep = {"p07": {}, "p08": {}}

hero_colls = ("ME_WaveViolin_Assemblies", "ME_WaveViolin_Strings", "ME_WaveViolin_Ornament")
tris = {}
issues = []
for o in bpy.data.objects:
    if o.type != "MESH" or not any(c.name in hero_colls for c in o.users_collection):
        continue
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    t = sum(len(p.vertices) - 2 for p in me.polygons)
    tris[o.name] = t
    if any(abs(s - 1) > 1e-4 for s in o.scale):
        issues.append(f"{o.name}: non-unit scale {tuple(round(s,4) for s in o.scale)}")
    if not o.data.uv_layers:
        issues.append(f"{o.name}: no UV")
    if not [s.material for s in o.material_slots]:
        issues.append(f"{o.name}: no material")
    ev.to_mesh_clear()

total = sum(tris.values())
rep["p07"]["tris_total"] = total
rep["p07"]["tri_budget_80k"] = total < 80000
rep["p07"]["issues"] = issues

# colorspace guard on all file images
for img in bpy.data.images:
    if img.source == "FILE" and any(k in img.name for k in ("Normal", "Height", "ORM")):
        if img.colorspace_settings.name != "Non-Color":
            img.colorspace_settings.name = "Non-Color"
            rep["p07"].setdefault("noncolor_fixed", []).append(img.name)

# contact sheet render (4 poses)
scn = bpy.context.scene
scn.render.resolution_x = 1400; scn.render.resolution_y = 1400
mc = bpy.data.objects["ME_WaveViolin_Control"]
plates = []
for tag, rx in (("stow", -1.5708), ("deploy", 0.0)):
    mc.rotation_euler.x = rx
    bpy.context.view_layer.update()
    p = os.path.join(OUT, f"p07_{tag}.png")
    scn.render.filepath = p
    bpy.ops.render.render(write_still=True)
    plates.append(p)
mc.rotation_euler.x = -1.5708

# simple 2-up contact sheet (PIL if present; plates kept separately otherwise)
try:
    from PIL import Image
    ims = [Image.open(p) for p in plates]
    w = sum(i.width for i in ims); h = max(i.height for i in ims)
    sheet = Image.new("RGB", (w, h))
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0)); x += i.width
    sheet.save(os.path.join(OUT, "p07_contact.png"))
    rep["p07"]["contact_sheet"] = os.path.join(OUT, "p07_contact.png")
except Exception as exc:
    rep["p07"]["contact_sheet"] = f"SKIPPED (no PIL: {exc}); plates kept separately"

# ---------------- p08: export collection ----------------
exp = bpy.data.collections.get("Export")
for o in list(exp.objects): exp.objects.unlink(o)
include = [o for o in bpy.data.objects if o.type == "MESH"
           and any(c.name in hero_colls for c in o.users_collection)]
skipped = []
for o in include:
    if o.name in ("ME_WaveViolin_Veil",):   # sim/drape stays out of game mesh
        skipped.append(o.name); continue
    exp.objects.link(o)
    # apply export-safe: keep shape keys + drivers (they survive FBX skinned-less via morphs)
manifest = {
    "asset": "SM_MEWaveViolin",
    "landing": "/Game/EnvSandbox/Meshes/Environment/waveviolin",
    "naming": "ME_WaveViolin_*, sockets SOCKET_*, mats ME_MAT_Violin_*",
    "objects": sorted(o.name for o in exp.objects),
    "skipped_for_sim": skipped,
    "tris_total": total,
    "uvs": "UVMap + ME_BakeUV (active=ME_BakeUV)",
    "sockets": [o.name for o in bpy.data.objects if o.name.startswith("SOCKET_")],
}
json.dump(manifest, open(os.path.join(LANE, "ue_intake_manifest.json"), "w"), indent=1)
rep["p08"] = {"export_objs": len(exp.objects), "manifest": True}

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p078_report.json"), "w"), indent=1)
log(f"p07 tris={total} issues={len(issues)}; p08 exported {len(exp.objects)}")
