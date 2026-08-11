"""Headless smoke test for Melodia Kawaii GN generate (Blender 5.1)."""
import importlib
import bpy
import traceback

ADDON = "blender_kawaii_gn"
GENERATORS = ("kawaii_donut_gn", "kawaii_cupcake_gn", "kawaii_table_gn")


def main():
    # Fresh file — no stale node groups
    bpy.ops.wm.read_homefile(use_empty=True)

    # Import addon modules directly (avoid loading all user addons in background)
    import sys
    addon_dir = r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons"
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)

    import blender_kawaii_gn
    importlib.reload(blender_kawaii_gn)
    blender_kawaii_gn.register()

    from blender_kawaii_gn.core.gn_framework import get_generator

    results = []
    for gen_id in GENERATORS:
        gen_cls = get_generator(gen_id)
        if gen_cls is None:
            results.append((gen_id, False, "not in registry"))
            continue
        try:
            obj = gen_cls.create_object()
            mod = obj.modifiers.get("Kawaii GN")
            ng = mod.node_group if mod else None
            has_iface = False
            if ng:
                has_iface = any(
                    getattr(i, "in_out", None) == "OUTPUT" and i.name == "Geometry"
                    for i in ng.interface.items_tree
                )
            ok = obj is not None and ng is not None and has_iface
            results.append((gen_id, ok, obj.name if obj else "no object"))
        except Exception as exc:
            results.append((gen_id, False, traceback.format_exc()))

    failed = [r for r in results if not r[1]]
    print("KAWAII_GN_TEST_RESULTS:")
    for gen_id, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status} {gen_id}:")
        if not ok:
            print(detail)
        else:
            print(f"    {detail}")

    if failed:
        raise SystemExit(1)
    print("KAWAII_GN_TEST_ALL_PASS")


if __name__ == "__main__":
    main()
