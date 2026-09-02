#!/usr/bin/env python3
"""
Blender headless preview — builds 12 chromatic Choral Sheep materials and
optionally renders a contact-sheet style look at the sheep.

Runs in two modes:
  1. Inside Blender (bpy available): builds materials, assigns to sheep mesh, renders thumbnails
  2. Outside Blender (CI): no-op, reports what would happen — use sheep_shine.py interactively

Usage (Blender 5.2):
    blender --background --python Tools/BlenderAddons/choral_sheep/preview_choral_flock.py -- --out Saved/Audit/choral_sheep/blender_preview
Or inside existing Blender Python console:
    exec(compile(open("Tools/BlenderAddons/choral_sheep/preview_choral_flock.py").read(),"x","exec"))
"""
import sys
import argparse
from pathlib import Path

OUT_DEFAULT = Path("Saved/Audit/choral_sheep/blender_preview")

def _run_in_blender(out_dir: Path, do_render: bool = False):
    import bpy
    # import the shine toolkit (same folder)
    import importlib.util
    spec = importlib.util.spec_from_file_location("sheep_shine", str(Path(__file__).parent / "sheep_shine.py"))
    sheep_shine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sheep_shine)  # type: ignore

    built = sheep_shine.build_chromatic_materials()
    print(f"[flock] built {len(built)} chromatic materials: {built}")

    # try to find sheep and cycle for proof
    try:
        sheep = sheep_shine._find_sheep_mesh()
        print(f"[flock] target mesh: {sheep.name} verts={len(sheep.data.vertices)}")
    except Exception as e:
        print(f"[flock] no sheep mesh in scene ({e}) — materials built but not assigned")
        sheep = None

    out_dir.mkdir(parents=True, exist_ok=True)
    # Optional contact render: assign each variant and render thumbnail
    if do_render and sheep is not None:
        scene = bpy.context.scene
        scene.render.resolution_x = 512
        scene.render.resolution_y = 512
        scene.render.image_settings.file_format = 'PNG'
        scene.render.film_transparent = True
        for label in list(sheep_shine.chromatic_variations().keys()):
            matname = f"ChoralWool_PC_{label}"
            if not sheep.data.materials:
                sheep.data.materials.append(bpy.data.materials.get(matname))
            else:
                sheep.data.materials[0] = bpy.data.materials.get(matname)
            out_path = str(out_dir / f"Blender_PC_{label}.png")
            scene.render.filepath = out_path
            bpy.ops.render.render(write_still=True)
            print(f"[flock] rendered {out_path}")
    elif sheep is not None:
        # lightweight: assign each and save blend state proof
        for pc in range(12):
            label = sheep_shine.PITCH_CLASS_HUES[pc][0]
            sheep_shine.apply_pitch_class(pc, sheep)
        print(f"[flock] cycled all 12 PCs on {sheep.name} — open viewport to see current (B)")

    # write manifest
    import json
    manifest = {
        "built": built,
        "count": len(built),
        "variants": sheep_shine.chromatic_variations(),
        "note": "Blender materials ChoralWool_PC_{C..B} ready; UE will instance as MI_ChoralSheep_Coat_PC{label}"
    }
    # can't json-dump RGB tuples directly cleanly — convert
    manifest_path = out_dir / "blender_flock_manifest.json"
    # serialize
    def _ser(v):
        if isinstance(v, tuple) and len(v)==3 and isinstance(v[0], float):
            return [round(x,4) for x in v]
        return v
    serializable = {}
    for k,(base,sheen,accent) in sheep_shine.chromatic_variations().items():
        serializable[k] = {"base": [round(c,4) for c in base], "sheen": sheen, "accent": [round(c,4) for c in accent]}
    manifest["variants"] = serializable
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[flock] manifest -> {manifest_path}")

if __name__ == "__main__":
    # parse --out after Blender's -- separator
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--")+1:]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--render", action="store_true", help="render thumbnails (requires scene + camera)")
    args = ap.parse_args(argv)
    out_dir = Path(args.out).resolve() if Path(args.out).is_absolute() else Path(args.out)
    # if relative, resolve against BS_GodFile root
    if not out_dir.is_absolute():
        out_dir = (Path(__file__).resolve().parents[3] / args.out).resolve()
    try:
        import bpy  # type: ignore
        _run_in_blender(out_dir, do_render=args.render)
    except ImportError:
        print("[flock] bpy not available — this script must run inside Blender 5.2")
        print("       To stage without Blender, run Tools/Houdini/generate_choral_variants.py instead")
        print("       Or in Blender Scripting tab: exec(open('Tools/BlenderAddons/melodia_studio/preview_choral_flock.py').read())")
