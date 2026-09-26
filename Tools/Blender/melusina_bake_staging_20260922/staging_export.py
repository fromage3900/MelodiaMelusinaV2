# Staging export: UV-verified hair + eye meshes -> OBJ for the Copernicus bake lane.
# Read-only on the staging copy (never saved); writes OBJs + one evidence JSON.
import bpy, json, os

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922"
OUT = os.path.join(LANE, "obj")
os.makedirs(OUT, exist_ok=True)

# (object name, active UV layer for export, clean export stem)
TARGETS = [
    ("Hair Strand.004", "shp_uv_map", "Melusina_HairA_Strand004"),
    ("Hair Strand.007", "shp_uv_map", "Melusina_HairB_Strand007"),
    ("Hair Strand.010", "shp_uv_map", "Melusina_HairC_Strand010"),
    ("R_Iris.001",      "UVMap",      "Melusina_IrisA_R1"),
    ("R_Iris.002",      "UVMap",      "Melusina_IrisB_R2"),
    ("R_Eyelash",       "UVMap",      "Melusina_Eyelash_R"),
]

# Introspect the OBJ exporter once; keep only kwargs it actually accepts
op = bpy.ops.wm.obj_export
valid = {p.identifier for p in op.get_rna_type().properties if not p.identifier.startswith("rna_")}
bpy.ops.object.select_all(action='DESELECT')

results = []
for obj_name, uv_name, stem in TARGETS:
    ob = bpy.data.objects.get(obj_name)
    if ob is None:
        results.append({"object": obj_name, "verdict": "MISSING"})
        continue
    me = ob.data
    uv_names = [l.name for l in me.uv_layers]
    uv_live = {}
    for l in me.uv_layers:
        n = len(l.data)
        if n == 0:
            uv_live[l.name] = "EMPTY"
            continue
        step = max(1, n // 2000)
        nz = sum(1 for i in range(0, n, step)
                 if abs(l.data[i].uv.x) > 1e-6 or abs(l.data[i].uv.y) > 1e-6)
        uv_live[l.name] = "LIVE" if nz / max(1, len(range(0, n, step))) > 0.5 else "ZERO"
    primary = uv_name if uv_name in uv_names else (uv_names[0] if uv_names else None)
    if primary:
        me.uv_layers.active = me.uv_layers[primary]
        me.uv_layers[primary].active_render = True
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    path = os.path.join(OUT, stem + ".obj")
    kwargs = dict(filepath=path, export_selected_objects=True, apply_modifiers=True,
                  export_uv=True, export_normals=True, export_materials=True)
    kwargs = {k: v for k, v in kwargs.items() if k in valid}
    bpy.ops.wm.obj_export(**kwargs)
    ok = os.path.isfile(path) and os.path.getsize(path) > 1000
    ob.select_set(False)
    results.append({
        "object": obj_name, "stem": stem, "obj": path if ok else None,
        "size_bytes": os.path.getsize(path) if ok else 0,
        "verts": len(me.vertices), "polys": len(me.polygons),
        "uv_sets": uv_live, "exported_uv": primary,
        "materials": [ms.material.name if ms.material else "EMPTY_SLOT" for ms in ob.material_slots],
        "verdict": "EXPORTED" if ok else "EXPORT_FAILED",
    })

# Left-eye census: does an L-side iris/cornea mesh exist anywhere in this WIP?
l_eye = [o.name for o in bpy.data.objects
         if o.type == "MESH" and any(k in o.name.lower() for k in ("iris", "cornea", "eyeball"))
         and o.name.lower().startswith(("l", "left"))]
left_missing = {"l_side_eye_meshes_found": l_eye,
                "note": "Only R_Iris.001/.002 + R_Eyelash exist as separate eye meshes in this WIP; "
                        "left iris may be a material region on the body mesh (Melusina_Base / Melusina.001)."}

evidence = {
    "schema": "melodia.bake_staging_export.v1",
    "source_copy": bpy.data.filepath,
    "out_dir": OUT,
    "exports": results,
    "left_eye_census": left_missing,
}
epath = os.path.join(LANE, "staging_export_evidence.json")
with open(epath, "w", encoding="utf-8") as f:
    json.dump(evidence, f, indent=1)
print("STAGING_EXPORT -> " + epath)
for r in results:
    print("  %-24s %-14s size=%-9s uv=%s sets=%s" % (
        r.get("object"), r.get("verdict"), r.get("size_bytes", "-"),
        r.get("exported_uv"), json.dumps(r.get("uv_sets", {}))))
print("  L-side eye meshes:", l_eye or "NONE FOUND")
