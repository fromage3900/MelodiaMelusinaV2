# Manual OBJ export v2 (HairA/HairB): Blender-style topology — one "v" per
# unique position, per-corner "vt"/"vn" indices — so Houdini's importer sees
# VERTEX-class uv/N (point-class uv bakes flat in bakegeometrytextures::2.0).
import bpy, json, os, math

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922"
OUT = os.path.join(LANE, "obj")
TARGETS = [("Hair Strand.004", "shp_uv_map", "Melusina_HairA_Strand004"),
           ("Hair Strand.007", "shp_uv_map", "Melusina_HairB_Strand007")]

results = []
for obj_name, uv_name, stem in TARGETS:
    ob = bpy.data.objects[obj_name]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    eme = ev.to_mesh()
    uvl = eme.uv_layers.get(uv_name) or (eme.uv_layers[0] if len(eme.uv_layers) else None)
    uv = uvl.data if uvl else None

    nan_v = nan_uv = 0
    v_lines, vt_index, vn_index, f_lines = {}, {}, {}, []
    uv_i = 0
    for poly in eme.polygons:
        idx = []
        for li in poly.loop_indices:
            vi = eme.loops[li].vertex_index
            co = eme.vertices[vi].co
            if not all(math.isfinite(c) for c in co):
                nan_v += 1
                continue
            if vi + 1 not in v_lines:
                v_lines[vi + 1] = "v %.6f %.6f %.6f" % (co.x, co.y, co.z)
            n = eme.loops[li].normal
            nkey = (round(n.x, 4), round(n.y, 4), round(n.z, 4))
            if nkey not in vn_index:
                vn_index[nkey] = len(vn_index) + 1
            if uv:
                u = uv[li].uv
                if not (math.isfinite(u.x) and math.isfinite(u.y)):
                    nan_uv += 1
                    continue
                ukey = (round(u.x, 5), round(u.y, 5))
            else:
                ukey = (0.0, 0.0)
            if ukey not in vt_index:
                uv_i += 1
                vt_index[ukey] = uv_i
            idx.append("%d/%d/%d" % (vi + 1, vt_index[ukey], vn_index[nkey]))
        if len(idx) >= 3:
            f_lines.append("f " + " ".join(idx))
    ev.to_mesh_clear()

    path = os.path.join(OUT, stem + ".obj")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Melusina bake staging manual export v2 (vertex-class uv/N)\n")
        f.write("# source: %s object: %s\n" % (bpy.data.filepath, obj_name))
        f.write("\n".join(v_lines[k] for k in sorted(v_lines)) + "\n")
        f.write("\n".join("vt %.6f %.6f" % k for k in vt_index) + "\n")
        f.write("\n".join("vn %.5f %.5f %.5f" % k for k in vn_index) + "\n")
        f.write("\n".join(f_lines) + "\n")
    size = os.path.getsize(path)
    results.append({"object": obj_name, "stem": stem, "obj": path, "size_bytes": size,
                    "v": len(v_lines), "vt": len(vt_index), "vn": len(vn_index),
                    "faces": len(f_lines), "nan_positions": nan_v, "nan_uvs": nan_uv,
                    "verdict": "EXPORTED" if size > 10000 and f_lines else "EXPORT_FAILED"})

with open(os.path.join(LANE, "hairAB_manual_v2_evidence.json"), "w", encoding="utf-8") as f:
    json.dump({"schema": "melodia.bake_staging_manual_export.v2", "results": results}, f, indent=1)
print("HAIRAB_V2")
for r in results:
    print("  %-18s %-14s %d B  v=%d vt=%d vn=%d f=%d nan=%d/%d" % (
        r["object"], r["verdict"], r["size_bytes"], r["v"], r["vt"], r["vn"],
        r["faces"], r["nan_positions"], r["nan_uvs"]))
