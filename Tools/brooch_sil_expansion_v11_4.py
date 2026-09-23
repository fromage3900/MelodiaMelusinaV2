"""brooch_sil_expansion_v11_4.py — v11.4 bake driver (elegant-mechanical).

v11.4 = in-tree detail pass only (facet language + rim step + groove rails +
arch-void markers + veil echo rail). No new objects, no material authority change,
no sizing change.

AUTHORITY: that detail is authored ONCE, inline in the canonical builders
`brooch_silhouettes.build_citadel` / `build_veil`. This module only drops stale
trees, calls those builders, and attaches the SetMaterial. Scene is NOT saved here
(caller saves via the builder path with auto-backup).
"""
import sys

sys.path.insert(0, "P:/MelodiaMelusinaV2-Laptop/Tools")
import brooch_silhouettes as sil

DETAIL_TAG = "v11.4 elegant-mechanical"


# v11.4 detail lives INLINE in the canonical builder (brooch_silhouettes.build_citadel /
# build_veil). This module is now only the BAKE driver: drop any stale tree, rebuild it
# from the canonical builder, attach the SetMaterial. The previous detail_citadel /
# detail_veil re-application was removed 2026-09-22 — with the detail inline in the
# builder it would have doubled the step rim, both groove rails, all 8 arch markers and
# the veil echo rail, so the baked asset would not have matched the rendered evidence.


def _arg(name, default=None):
    import sys as _s
    a = _s.argv
    if name in a:
        i = a.index(name)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main():
    import bpy
    preset = _arg("--preset", "both")
    want = {"both": ("star_citadel", "lissajous_veil"),
            "citadel": ("star_citadel",),
            "veil": ("lissajous_veil",),
            "star_citadel": ("star_citadel",),
            "lissajous_veil": ("lissajous_veil",)}.get(preset, ("star_citadel", "lissajous_veil"))
    for p in want:
        builder = sil.PRESETS[p]
        old_name = "GN_BroochSil_Citadel" if p == "star_citadel" else "GN_BroochSil_Veil"
        old = bpy.data.node_groups.get(old_name)
        if old is not None:
            bpy.data.node_groups.remove(old)
            print("[v11.4] removed stale tree:", old_name)
        tree = builder()  # canonical builder already carries the v11.4 detail inline
        sil.add_set_material(tree, sil.mat_simple(sil.SIL_GOLD, (1.0, 0.766, 0.336), metallic=1.0, rough=0.22))
        print("[v11.4] rebuilt %s -> %s (%d nodes)" % (p, tree.name, len(tree.nodes)))
    print("done v11.4 expansion (scene NOT saved)")


main()