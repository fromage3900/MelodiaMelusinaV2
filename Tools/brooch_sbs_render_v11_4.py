"""One-shot v11.4 side-by-side: rebuild canonical v11.4 trees, solve both presets
side-by-side (citadel LEFT, veil RIGHT of the hero flower), render beauty front
+ tq + flat-black silhouette reads. Scene is NOT saved.

Usage:
  blender -b FlowerBrooch.blend --factory-startup --python Tools/brooch_sbs_render_v11_4.py [-- --out <dir>]
"""
import bpy
import pathlib
import sys
import time
from mathutils import Vector

sys.path.insert(0, "P:/MelodiaMelusinaV2-Laptop/Tools")
import brooch_silhouettes as sil


def _arg(name, default=None):
    a = sys.argv
    if name in a:
        i = a.index(name)
        if i + 1 < len(a):
            return a[i + 1]
    return default


OUT = _arg("--out", "P:/MelodiaMelusinaV2-Laptop/Saved/Audit/v114_sbs/")
REPORT = _arg("--report", OUT + "v114_sbs_report.json")
pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)
CANONICAL = "P:/MelodiaMelusinaV2-Laptop/Tools/brooch_silhouettes.py"


def _sha16(path):
    import hashlib
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:16]
    except Exception as exc:
        return "unreadable:%r" % (exc,)


def _stamp(path):
    import os
    try:
        st = os.stat(path)
        return {"bytes": st.st_size,
                "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime))}
    except Exception:
        return {"bytes": 0, "mtime": None}


# The report is written by the harness that produced the frames (evidence standard rule 4)
# and names its own sha256 so the record identifies which harness ran.
report = {
    "schema": "melodia.brooch.sil_evidence",
    "evidence_version": sil.EVIDENCE_VERSION,
    "harness": {"script": __file__, "sha256_16": _sha16(__file__),
                "canonical_builder": CANONICAL,
                "canonical_builder_sha256_16": _sha16(CANONICAL)},
    "blender": bpy.app.version_string,
    "scene_file": bpy.data.filepath or None,
    "scene_mtime": _stamp(bpy.data.filepath)["mtime"] if bpy.data.filepath else None,
    "shot_requested": time.strftime("%Y-%m-%dT%H:%M:%S"),
    # Recorded BEFORE any builder runs: proves whether the blend already carried the
    # silhouette trees (i.e. whether a bake was ever saved) rather than assuming it.
    "sil_trees_preexisting_in_blend": sorted(
        n for n in bpy.data.node_groups.keys() if "BroochSil" in n),
    "sizing": {}, "census": {}, "silhouette": {}, "shots": [], "assertions": [],
}
print("[sbs] sil trees in blend before build:", report["sil_trees_preexisting_in_blend"])

hero = bpy.data.objects.get("FlowerBrooch")
assert hero is not None, "hero FlowerBrooch missing"
ctr, top_z, span = sil.plate_metrics(hero)
print("[sbs] plate center=(%.3f,%.3f) top=%.3f span=%.3f" % (ctr[0], ctr[1], top_z, span))
infos = {}
infos["star_citadel"] = sil.build_silhouette("star_citadel", hero=hero)
infos["lissajous_veil"] = sil.build_silhouette("lissajous_veil", hero=hero)
# Duo spacing. span*1.15 put the pair at ~1595 px wide in the 1600 frame — passing
# separation easily but touching the right edge at 1.45/1.60 distances, while pulling
# the camera back to clear the edge drops the 64 px icon read below its 8 px floor.
# Narrowing the GAP is the one lever that fixes framing without shrinking either
# subject: icon gate and per-subject size are untouched, separation stays ~39 px at
# 128 (gate: >=1). Composition only — no sizing, census, or material authority change.
gap = span * 1.05
infos["star_citadel"]["object"].location.x -= gap
infos["lissajous_veil"]["object"].location.x += gap
bpy.context.view_layer.update()
trio = [hero, infos["star_citadel"]["object"], infos["lissajous_veil"]["object"]]
lo, hi = sil.measured_bbox(trio)
center = (lo + hi) * 0.5
size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
print("[sbs] trio center=(%.3f,%.3f,%.3f) size=%.3f" % (center.x, center.y, center.z, size))
WANT = span * 1.15  # build_silhouette() default span_factor=1.15
for key, info in infos.items():
    print("[sbs] %s scale=%.4f span %.3f -> %.3f" % (key, info["scale"], info["span_before"], info["span_after"]))
    report["sizing"][key] = {
        "scale": round(float(info["scale"]), 6),
        "span_before": round(float(info["span_before"]), 6),
        "span_after": round(float(info["span_after"]), 6),
        "want": round(float(WANT), 6),
        "overshoot_pct": round(100.0 * (float(info["span_after"]) / WANT - 1.0), 4),
        "object": info["object"].name,
    }
report["plate"] = {"center": [round(float(ctr[0]), 6), round(float(ctr[1]), 6)],
                   "top_z": round(float(top_z), 6), "span": round(float(span), 6)}
report["want_span"] = round(float(WANT), 6)
report["trio"] = {"center": [round(float(center.x), 6), round(float(center.y), 6),
                             round(float(center.z), 6)],
                  "size": round(float(size), 6),
                  "gap_x": round(float(gap), 6)}

# Census + in-tree detail, taken while the v11.4 trees are live. Counts come from the
# EVALUATED mesh (sil.mesh_census), so they describe what actually renders, not the
# pre-modifier base mesh.
for key, info in infos.items():
    report["census"][key] = sil.mesh_census(info["object"])
report["census"]["hero"] = sil.mesh_census(hero)
report["trees"] = {}
for tn in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil"):
    t = bpy.data.node_groups.get(tn)
    report["trees"][tn] = sil.tree_detail_nodes(t) if t is not None else None
# Optional-Higgsas path record (set by build_veil). The manual lissajous is canonical;
# this exists so the report states which path produced the wire instead of leaving a bare
# boolean that reads like a build failure.
report["higgsas_probe"] = dict(sil.HIGGSAS_STATUS)

scn = bpy.context.scene
scn.frame_set(1)
scn.render.engine = 'BLENDER_EEVEE'
report["engine_requested"] = 'BLENDER_EEVEE'
report["engine_active"] = scn.render.engine
try:
    scn.eevee.taa_render_samples = 64
except Exception as exc:
    print("  warn samples (%r)" % (exc,))
report["samples_active"] = int(getattr(scn.eevee, "taa_render_samples", 0))
for nm in ("FlowerBrooch", "FlowerBrooch_Dangles", "FlowerBrooch_Petals"):
    o = bpy.data.objects.get(nm)
    if o is None:
        continue
    for m in o.modifiers:
        if m.name.startswith("Outline"):
            m.show_render = False
cam = bpy.data.objects.get("LAB_Cam")
# Lens is set EXPLICITLY for the flat pass instead of inheriting whatever the last beauty
# shot left behind. Silhouette framing must be a pure function of the trio, or reordering
# the shots above silently changes the icon-gate numbers (2026-09-22).
cam.data.lens = 55.0
# Framing distance for the flat pass, derived from MEASURED fill at ink_max=0.02
# (white world; duo fill % of frame width scales ~1/D):
#   D=1.45*size -> duo spans both edges (width >= 1600)
#   D=1.60*size -> duo x 3..1599 = 99.75% fill -> STILL touches right edge (icon minax=10)
#   framing needs fill <= ~95% -> D >= 1.60 * 99.75/95 = 1.68*size
#   icon needs minax >= 8 at 64px -> 10 px at 1.60 with 1/D -> floor at 2.00*size
# 1.70 sits in the [1.68, 2.00] window with margin on both gates. The earlier comment's
# "8 px floor around 1.7" arithmetic was wrong (it did not match its own 11 px@1.45 /
# 10 px@1.60 chain); the measured 1/D floor is 2.00. If either assertion fails again the
# report says which side moved — do NOT widen the window by editing thresholds.
SIL_DIST = size * 1.70

scn.camera = cam
scn.render.resolution_x, scn.render.resolution_y = 1600, 1000
scn.render.resolution_percentage = 100


def aim(loc, tgt):
    cam.location = Vector(loc)
    d = (Vector(tgt) - Vector(loc)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


SZ = size * 1.1
D = SZ * 1.9
for fname, loc, tgt, lens in (
        ("v114_sbs_front.png", (center.x, center.y - D, center.z + SZ * 0.10), center, 55.0),
        ("v114_sbs_tq.png", (center.x - D * 0.55, center.y - D * 0.70, center.z + SZ * 0.40), center, 55.0)):
    cam.data.lens = lens
    aim(loc, tgt)
    scn.render.filepath = OUT + fname
    bpy.ops.render.render(write_still=True)
    print("shot:", scn.render.filepath)
    st = _stamp(scn.render.filepath)
    report["shots"].append({"file": fname, "kind": "beauty",
                            "px": [int(scn.render.resolution_x),
                                   int(scn.render.resolution_y)],
                            "lens_mm": lens, "bytes": st["bytes"], "mtime": st["mtime"]})

flat = bpy.data.materials.get("SIL_Flatten_v114")
if flat is None:
    flat = bpy.data.materials.new("SIL_Flatten_v114")
flat.use_nodes = True
for n in [n for n in flat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
    flat.node_tree.nodes.remove(n)
out = next((n for n in flat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
emi = flat.node_tree.nodes.new('ShaderNodeEmission')
emi.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
emi.inputs['Strength'].default_value = 1.0
flat.node_tree.links.new(emi.outputs['Emission'], out.inputs['Surface'])
saved = []
for tree_name in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil"):
    tree = bpy.data.node_groups.get(tree_name)
    if tree is None:
        continue
    for n in tree.nodes:
        if n.bl_idname == 'GeometryNodeSetMaterial':
            saved.append((n, n.inputs['Material'].default_value))
            n.inputs['Material'].default_value = flat
try:
    scn.view_settings.view_transform = 'Standard'
except Exception:
    pass
# V11 silhouette recipe (BROOCH_V11_SILHOUETTE_PLAN_2026-09-17 §0): black-emission
# flatten + FRESH WHITE WORLD + ALL LIGHTS HIDDEN, flat reads at 1600/256/128.
# The 2026-09-22 run did the flatten but skipped the white world and the light hide, so
# the subjects were black on the stage's grey starry backdrop (modal 0.44, vignetted
# corners 0.196) instead of black on white — those numbers described the set, not the
# silhouette. 64px is added because the §Gate line names 128/64 as the icon gate.
world_prev = scn.world
sil_world = bpy.data.worlds.new("SIL_White_v114")
sil_world.use_nodes = True
_wbg = next((n for n in sil_world.node_tree.nodes if n.type == 'BACKGROUND'), None)
if _wbg is not None:
    _wbg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    _wbg.inputs['Strength'].default_value = 1.0
scn.world = sil_world
lights_hidden = []
for o in bpy.data.objects:
    if o.type == 'LIGHT' and not o.hide_render:
        o.hide_render = True
        lights_hidden.append(o.name)
print("[sbs] sil pass: white world + %d lights hidden" % len(lights_hidden))
# Everything mesh except the two silhouette objects is hidden for the flatten pass.
# The stage floor is hidden too (2026-09-22): a lit floor reads as a bright horizon band
# across a flat-black pass and contaminates an icon-legibility measurement. The
# v114_sbs_stage harness already hid it; this aligns the two instead of leaving them
# divergent. Floor visibility is recorded in the report either way.
hide = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render:
        continue
    if o.name.startswith("FlowerBrooch_Sil"):
        continue
    o.hide_render = True
    hide.append(o.name)
sil_trees = [t for t in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil")
             if bpy.data.node_groups.get(t) is not None]
report["sil_pass"] = {
    "recipe": "BROOCH_V11_SILHOUETTE_PLAN_2026-09-17 section 0",
    "flatten_material": flat.name,
    "white_world": sil_world.name,
    "world_prev": world_prev.name if world_prev else None,
    "lights_hidden": lights_hidden,
    "sil_trees_present": sil_trees,
    "set_material_nodes_rewired": len(saved),
    "non_sil_meshes_hidden": len(hide),
    "hidden_names": hide,
    "floor_hidden": "BroochFloor_Stage" in hide,
    "view_transform": scn.view_settings.view_transform,
}
for px in (1600, 256, 128, 64):
    scn.render.resolution_x, scn.render.resolution_y = px, px
    # SIL_DIST, not a literal: the 1.45 framing fix must actually reach the loop or the
    # icon gate keeps measuring the old 1.9 distance (that is exactly how min_axis_px 7
    # survived a "fixed" comment in the 2026-09-22 run).
    aim((center.x, center.y - SIL_DIST, center.z + size * 0.1), center)
    scn.render.filepath = OUT + ("v114_sbs_sil_%d.png" % px)
    bpy.ops.render.render(write_still=True)
    print("shot:", scn.render.filepath)
    # polarity="dark": the flatten recipe is a BLACK Emission, so the subjects are the
    # dark minority on the white world. Measured, not assumed (see ink_report docstring).
    rec = sil.ink_report(scn.render.filepath, polarity="dark", ink_max=0.02)
    rec["kind"] = "silhouette"
    rec["bytes"] = _stamp(scn.render.filepath)["bytes"]
    rec["mtime"] = _stamp(scn.render.filepath)["mtime"]
    report["silhouette"]["%d" % px] = rec
    report["shots"].append(rec)
for n, m in saved:
    n.inputs['Material'].default_value = m
for nm in ("FlowerBrooch", "FlowerBrooch_Dangles", "FlowerBrooch_Petals"):
    o = bpy.data.objects.get(nm)
    if o is None:
        continue
    for m in o.modifiers:
        if m.name.startswith("Outline"):
            m.show_render = True
# Restore the look-dev state. The scene is never saved (see header), so this only matters
# if the harness is re-run or a human steps in after it in the same session — but leaving
# a white world and hidden lights behind is exactly the kind of residue that makes the
# NEXT run's numbers describe the previous run's set.
scn.world = world_prev
for nm in lights_hidden:
    bpy.data.objects[nm].hide_render = False
report["sil_pass"]["restored"] = {
    "world": world_prev.name if world_prev else None,
    "lights": lights_hidden, "meshes": len(hide)}

# ------------------------------------------------------------- assertions ----
# The report ships next to the frames it describes and carries real pass/fail rows, so a
# later reader can re-check claims from numbers instead of re-reading prose. Thresholds are
# named here, not hidden: 0.5% sizing, 8 px at the 64 px icon read, >=1 px separation gap,
# white (>0.9) backdrop on the flat pass.
RT = sil.report_assert
_sz = report["sizing"]
RT(report, "sizing_within_0p5pct",
   all(abs(_sz[k]["overshoot_pct"]) <= 0.5 for k in _sz) and len(_sz) == 2,
   {k: _sz[k]["overshoot_pct"] for k in _sz})
_th = report["trees"]
RT(report, "both_sil_trees_present",
   all(_th.get(t) is not None for t in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil")),
   {t: (None if _th.get(t) is None else _th[t]["node_count"]) for t in _th})
RT(report, "v114_detail_inline_in_tree",
   all(_th.get(t) and _th[t]["detail_count"] > 0
       for t in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil")),
   {t: (None if _th.get(t) is None else _th[t]["detail_count"]) for t in _th})
_cn = report["census"]
RT(report, "census_closed_manifold",
   all(_cn[k]["boundary_edges"] == 0 and _cn[k]["non_manifold_edges"] == 0
       for k in ("star_citadel", "lissajous_veil")),
   {k: {"boundary": _cn[k]["boundary_edges"],
        "non_manifold": _cn[k]["non_manifold_edges"],
        "loose_verts": _cn[k]["loose_verts"], "loose_edges": _cn[k]["loose_edges"]}
    for k in ("star_citadel", "lissajous_veil")})
RT(report, "sil_setmaterial_resolves",
   all(_th.get(t) and _th[t]["set_material"]
       for t in ("GN_BroochSil_Citadel", "GN_BroochSil_Veil")),
   {t: (None if _th.get(t) is None else _th[t]["set_material"]) for t in _th})
_sil = report["silhouette"]
RT(report, "sil_frames_written",
   all(_sil[k]["bytes"] > 0 for k in _sil) and sorted(_sil, key=int) == ["64", "128", "256", "1600"],
   {k: _sil[k]["bytes"] for k in _sil})
RT(report, "sil_backdrop_white",
   all(_sil[k]["backdrop_modal"] >= 0.9 for k in _sil),
   {k: {"backdrop_modal": _sil[k]["backdrop_modal"], "corner": _sil[k]["corner"]}
    for k in _sil})
RT(report, "sil_framing_inside_frame",
   all(_sil[k]["touch_edge"] is False for k in _sil),
   {k: _sil[k]["touch_edge"] for k in _sil})
RT(report, "icon_legible_at_64px",
   _sil["64"]["min_axis_px"] >= 8,
   {"64": {"min_axis_px": _sil["64"]["min_axis_px"],
           "ink_pct": _sil["64"]["ink_pct"],
           "ink_bbox_px": _sil["64"]["ink_bbox_px"]}})
RT(report, "two_subjects_separated_at_128",
   _sil["128"]["max_column_gap_px"] >= 1,
   {"128": {"max_column_gap_px": _sil["128"]["max_column_gap_px"],
            "ink_pct": _sil["128"]["ink_pct"]}})
report["assertions_summary"] = {
    "total": len(report["assertions"]),
    "passed": sum(1 for a in report["assertions"] if a["pass"]),
    "failed": sum(1 for a in report["assertions"] if not a["pass"]),
    "failed_ids": [a["id"] for a in report["assertions"] if not a["pass"]],
}
report["shot_finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
sil.write_report(REPORT, report)
print("[sbs] assertions %(passed)d/%(total)d pass  failed=%(failed_ids)s"
      % report["assertions_summary"])
print("done v11.4 sbs render (scene NOT saved)")
