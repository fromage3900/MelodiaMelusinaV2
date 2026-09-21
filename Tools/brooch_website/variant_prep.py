# variant_prep.py — runtime silhouette-object prep for website variant renders.
# Chain: blender -b <blend> --python variant_prep.py --python brooch_pres_rig.py \
#        --python brooch_pres_shot.py -- --sky <sky> --silhouette <sil>
# Reads --silhouette from argv, builds the preset object via Tools/brooch_silhouettes
# (runtime-only, NO save). 'flower' builds nothing. Imported AFTER bpy is live.
import bpy
import sys


def _arg(name, default=None):
    a = sys.argv
    return a[a.index(name) + 1] if name in a else default


sil = _arg("--silhouette", "flower")
if sil and sil != "flower":
    sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/Tools")
    import brooch_silhouettes as _bsil
    hero = bpy.data.objects["FlowerBrooch"]
    info = _bsil.build_silhouette(sil, hero=hero)
    info["object"].hide_render = False
    print("[variant] built %s -> %s (scale %.3f, span %.3f)" % (
        sil, info["object"].name, info["scale"], info["span_after"]))
else:
    print("[variant] flower base (no variant object)")
