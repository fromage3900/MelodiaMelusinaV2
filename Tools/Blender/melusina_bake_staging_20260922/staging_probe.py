# Read-only staging probe: hair + eye UV state on the harp WIP copy.
# Never saves. Writes one evidence JSON. Factory-startup (no addons) is intentional.
import bpy, json, sys
from mathutils import Vector

OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922\staging_probe.json"
dg = bpy.context.evaluated_depsgraph_get()

def world_bounds(ob):
    ev = ob.evaluated_get(dg)
    try:
        pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        return {"min": [round(v, 4) for v in lo], "max": [round(v, 4) for v in hi],
                "size": [round(hi[i] - lo[i], 4) for i in range(3)]}
    except Exception as e:
        return {"err": str(e)[:120]}

def uv_state(me):
    layers = [{"name": l.name, "active_render": l.active_render} for l in me.uv_layers]
    detail = []
    for l in me.uv_layers[:4]:
        data = l.data
        n = len(data)
        if n == 0:
            detail.append({"layer": l.name, "loops": 0, "verdict": "EMPTY"})
            continue
        step = max(1, n // 4000)
        nonx = sum(1 for i in range(0, n, step) if abs(data[i].uv.x) > 1e-6)
        nony = sum(1 for i in range(0, n, step) if abs(data[i].uv.y) > 1e-6)
        us = [data[i].uv.x for i in range(0, n, step)]
        vs = [data[i].uv.y for i in range(0, n, step)]
        detail.append({"layer": l.name, "loops": n,
                       "sampled": len(range(0, n, step)),
                       "nonzero_u_frac": round(nonx / max(1, len(us)), 3),
                       "nonzero_v_frac": round(nony / max(1, len(vs)), 3),
                       "u_range": [round(min(us), 3), round(max(us), 3)],
                       "v_range": [round(min(vs), 3), round(max(vs), 3)]})
    return {"uv_layer_count": len(me.uv_layers), "layers": layers, "detail": detail}

hair_re = ("hair", "flip")
eye_re = ("cornea", "iris", "eyeball", "eye")
rows = []
for ob in bpy.data.objects:
    nm = ob.name.lower()
    is_hair = any(k in nm for k in hair_re)
    is_eye = any(k in nm for k in eye_re)
    if not (is_hair or is_eye):
        continue
    row = {"name": ob.name, "type": ob.type,
           "parent": ob.parent.name if ob.parent else None,
           "hide_render": ob.hide_render, "hide_viewport": ob.hide_viewport}
    if ob.type == "MESH":
        row["verts"] = len(ob.data.vertices)
        row["polys"] = len(ob.data.polygons)
        row["materials"] = [ms.material.name if ms.material else None for ms in ob.material_slots]
        row["uv"] = uv_state(ob.data)
        row["modifiers"] = [m.type for m in ob.modifiers]
        row["vg_hair"] = sum(1 for g in ob.vertex_groups if "hair" in g.name.lower())
        row["world_bounds"] = world_bounds(ob)
    elif ob.type == "CURVES":
        try:
            row["curve_points"] = len(ob.data.points) if hasattr(ob.data, "points") else None
        except Exception:
            pass
        row["modifiers"] = [m.type for m in ob.modifiers]
        row["world_bounds"] = world_bounds(ob)
    rows.append(row)

rigs = []
for ob in bpy.data.objects:
    if ob.type == "ARMATURE":
        hb = [b.name for b in ob.data.bones if "hair" in b.name.lower()]
        rigs.append({"name": ob.name, "bones": len(ob.data.bones), "hair_bones": len(hb)})

# eye-adjacent meshes may hide under the body mesh; also list all mesh names carrying 'Melusina'
melusina_meshes = [o.name for o in bpy.data.objects
                   if o.type == "MESH" and "melusina" in o.name.lower()][:40]

report = {"schema": "melodia.bake_staging_probe.v1",
          "source_copy": bpy.data.filepath,
          "n_objects": len(bpy.data.objects),
          "armatures": rigs,
          "hair_eye_rows": rows,
          "melusina_meshes": melusina_meshes}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1)
print("STAGING_PROBE rows=%d armatures=%d -> %s" % (len(rows), len(rigs), OUT))
for r in rows:
    uvs = r.get("uv", {}).get("uv_layer_count", "n/a") if r["type"] == "MESH" else "-"
    print("  %-28s %-7s verts=%-8s uvlayers=%s mods=%s" % (r["name"], r["type"],
          r.get("verts", r.get("curve_points", "-")), uvs, ",".join(r.get("modifiers", []))[:40]))
