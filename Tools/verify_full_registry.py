"""P0 — full-registry baseline harness (absorption plan §3-P0).

Generates EVERY builder id in the unified registry headlessly, realizes,
records vert count + bbox + error to registry_baseline.json. Also records
the monolith's arch_type generate path per id (via surreal_architecture_gen
dispatch) so absorbed builders get A/B'd against their old path.

Run:  blender --background --python Tools/verify_full_registry.py
Out:  Tools/registry_baseline.json + console PASS/FAIL table.
"""
import bpy, json, os, sys, traceback

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(REPO, "Tools", "registry_baseline.json")
sys.path.insert(0, os.path.join(os.environ.get("APPDATA", ""),
    "Blender Foundation", "Blender", "5.2", "scripts", "addons"))
sys.path.insert(0, os.path.join(REPO, "deploy"))

# Blender autoloads AppData addons before this script runs; drop any cached
# surreal_arch so the harness measures THIS repo's deploy tree, not the stale
# live copy (laptop AppData had the P2 kits; this box's does not).
for _m in [m for m in list(sys.modules) if m == "surreal_arch" or m.startswith("surreal_arch.")]:
    del sys.modules[_m]
import surreal_arch  # noqa: E402
assert surreal_arch.__file__.replace("\\", "/").startswith(REPO.replace("\\", "/")), \
    f"harness must load repo copy, got {surreal_arch.__file__}"

results = {"package": {}, "monolith": {}, "meta": {}}

# ---------------- package registry ----------------
from surreal_arch.melodia_gn import core as pkg_core

ids = sorted(pkg_core.GROUP_BUILDERS.keys())
print(f"=== PACKAGE REGISTRY: {len(ids)} ids ===")
ok = 0
for tid in ids:
    entry = {"ok": False}
    try:
        fn = pkg_core.GROUP_BUILDERS[tid]
        res = fn()
        tree = res[0] if isinstance(res, (tuple, list)) else res
        me = bpy.data.meshes.new("PB")
        ob = bpy.data.objects.new("PB", me)
        bpy.context.scene.collection.objects.link(ob)
        mod = ob.modifiers.new("g", 'NODES')
        mod.node_group = tree
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        m2 = ev.to_mesh()
        if m2 and len(m2.vertices):
            xs = [v.co.x for v in m2.vertices]
            ys = [v.co.y for v in m2.vertices]
            zs = [v.co.z for v in m2.vertices]
            entry.update(ok=True, verts=len(m2.vertices),
                         bbox=[round(max(xs)-min(xs), 3), round(max(ys)-min(ys), 3),
                               round(max(zs)-min(zs), 3)])
            ev.to_mesh_clear()
            ok += 1
        else:
            entry["error"] = "empty geometry"
            if m2:
                ev.to_mesh_clear()
        bpy.data.objects.remove(ob)
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    results["package"][tid] = entry
print(f"package OK {ok}/{len(ids)}")

# ---------------- monolith dispatch ----------------
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "monolith", os.path.join(REPO, "deploy", "surreal_architecture_gen.py"))
    M = importlib.util.module_from_spec(spec)
    sys.modules["monolith"] = M
    spec.loader.exec_module(M)
except Exception as e:
    print("monolith import failed:", e)
    M = None

if M is not None:
    enum_ids = []
    try:
        try:
            bpy.utils.register_class(M.SurrealArchProperties)
        except Exception:
            pass  # already registered in this session
        enum_ids = [i.identifier for i in
                    M.SurrealArchProperties.bl_rna.properties["arch_type"].enum_items
                    if i.identifier not in ("DEFAULT",)]
    except Exception as e:
        print("enum read failed:", e)
    print(f"=== MONOLITH DISPATCH: {len(enum_ids)} arch ids ===")
    mok = 0
    for aid in enum_ids:
        entry = {"ok": False}
        try:
            # real props instance with ALL defaults — the monolith attaches its
            # PointerProperty to Object; create the scratch object FIRST, then
            # use ob.surreal_arch_props
            me = bpy.data.meshes.new("MB_m")
            ob = bpy.data.objects.new("MB", me)
            bpy.context.scene.collection.objects.link(ob)
            try:
                bpy.utils.register_class(M.SurrealArchProperties)
            except Exception:
                pass
            props = getattr(ob, "surreal_arch_props", None)
            if props is None:
                bpy.types.Object.surreal_arch_props = bpy.props.PointerProperty(type=M.SurrealArchProperties)
                props = ob.surreal_arch_props
            props.arch_type = aid
            props.auto_update = False
            M.apply_geometry_nodes_to_object(ob, props, force=True)
            # after apply, the object's GN tree exists — evaluate it
            gn_mod = next((m for m in ob.modifiers if m.name.startswith("SurrealArch")), None)
            if gn_mod and gn_mod.node_group:
                bpy.context.view_layer.update()
                dg = bpy.context.evaluated_depsgraph_get()
                evo = ob.evaluated_get(dg)
                m2 = evo.to_mesh()
                if m2 and len(m2.vertices):
                    xs = [v.co.x for v in m2.vertices]
                    ys = [v.co.y for v in m2.vertices]
                    zs = [v.co.z for v in m2.vertices]
                    entry.update(ok=True, verts=len(m2.vertices),
                                 bbox=[round(max(xs)-min(xs), 3), round(max(ys)-min(ys), 3),
                                       round(max(zs)-min(zs), 3)])
                    evo.to_mesh_clear()
                    mok += 1
                else:
                    entry["error"] = "empty geometry"
                    if m2:
                        evo.to_mesh_clear()
            else:
                entry["error"] = "no GN modifier created"
            bpy.data.objects.remove(ob)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        results["monolith"][aid] = entry
    print(f"monolith OK {mok}/{len(enum_ids)}")

results["meta"] = {
    "blender": bpy.app.version_string,
    "package_count": len(results["package"]),
    "monolith_count": len(results["monolith"]),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=1)
print("WROTE", OUT)
