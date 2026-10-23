#!/usr/bin/env python3
"""
Blender lit-sphere renderer for Choral Sheep wool — simulates how flat/Worley albedos will read under light.

Without needing Houdini UE launch: renders a wool-shaded sphere with Principled + sheen, using the same
base/accent/sheen per PC, under studio HDRI-lite (3 point lights). Great for judging "does clean flat already read as wool?"

Two modes:
  - inside Blender (bpy): builds materials, assigns to UV sphere, renders thumbnails to Saved/Audit/...
  - outside Blender: Pillow fallback — draws sphere normal shading over wool albedos (fake but useful for review)

Usage inside Blender 5.2:
  blender --background --python Tools/Houdini/blender_lit_sphere_render.py -- --size 512 --mode wool --out Saved/Audit/choral_sheep/experiments/lit

Outside Blender (quick):
  python Tools/Houdini/blender_lit_sphere_render.py --size 512 --mode flat --out Saved/Audit/choral_sheep/experiments/lit_fallback
"""
import argparse, colorsys, sys
from pathlib import Path

PITCH_CLASS_HUES = {
    0:  ("C",  0.000), 1:  ("Cs", 0.083), 2:  ("D",  0.167), 3:  ("Ds", 0.250),
    4:  ("E",  0.333), 5:  ("F",  0.417), 6:  ("Fs", 0.500), 7:  ("G",  0.583),
    8:  ("Gs", 0.667), 9:  ("A",  0.750), 10: ("As", 0.833), 11: ("B",  0.917),
}
def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def _fallback_lit_sphere(albedo_path, size, seed=0):
    """Pillow fake-lit sphere: multiply albedo by Lambert from sphere normal"""
    from PIL import Image, ImageDraw, ImageFilter
    import math, random
    rnd = random.Random(seed)
    img = Image.open(albedo_path).convert("RGB").resize((size, size), Image.LANCZOS)
    # Build normal-based shading: simple top-left light
    light = Image.new("L", (size, size), 0)
    ld = ImageDraw.Draw(light)
    # radial gradient approximating N·L for sphere centered at (size/2,size/2) radius size/2
    cx, cy, r = size//2, size//2, size//2 - 4
    # precompute shading via per-pixel loop (slow but 512 is ok)
    # Use small numpy-like via PIL? We'll do python loop with step 2 then blur
    # Faster: create distance-based Lambert via drawing concentric circles
    for rad in range(r, 0, -4):
        t = rad / r  # 1 at edge, 0 center
        # Lambert ~ sqrt(1 - (dist/r)^2) with light from top-left (shift)
        # approximate by varying brightness: center brightest
        bright = int(180 + 75 * (1 - t)**0.7)  # 180 edge, 255 center
        # shift slightly toward light
        ox, oy = int(-r*0.18), int(-r*0.22)
        ld.ellipse([cx - rad + ox, cy - rad + oy, cx + rad + ox, cy + rad + oy], fill=bright)
    light = light.filter(ImageFilter.GaussianBlur(radius=3))
    # apply to albedo: multiply
    shaded = Image.new("RGB", (size, size), (0,0,0))
    # per-pixel multiply via PIL ImageChops multiply with shading
    # Convert light to RGB multiplier
    light_rgb = Image.merge("RGB", [light, light, light])
    from PIL import ImageChops
    # Multiply albedo * light/255 : ImageChops.multiply does (a*b)/255
    lit = ImageChops.multiply(img, light_rgb)
    # Add rim: faint accent rim at opposite side
    rim = Image.new("RGBA", (size, size), (0,0,0,0))
    rd = ImageDraw.Draw(rim)
    rd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255,255,255,22), width=3)
    rim = rim.filter(ImageFilter.GaussianBlur(radius=1.2))
    lit = Image.alpha_composite(lit.convert("RGBA"), rim).convert("RGB")
    # Mask to circle (transparent outside)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    out = Image.new("RGB", (size, size), (26,26,26))
    out.paste(lit, mask=mask)
    return out

def _run_in_blender(out_dir: Path, size=512, albedo_mode="worley12"):
    import bpy, math
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clean scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    # Lights: 3-point
    for name, loc, energy in [
        ("Key", (3.5, -3.5, 4.5), 900),
        ("Fill", (-3.0, -1.2, 2.8), 400),
        ("Rim", (0, 4.0, 2.0), 600),
    ]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = 1.8
    # Camera
    bpy.ops.object.camera_add(location=(0, -3.2, 0.2), rotation=(math.radians(90), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    # Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(0, 0, 0))
    sphere = bpy.context.object
    sphere.name = "WoolSphere"
    # Try to import sheep_shine for chromatic materials
    import importlib.util
    spec = importlib.util.spec_from_file_location("sheep_shine", str(Path(__file__).parent.parent / "BlenderAddons/melodia_studio/sheep_shine.py"))
    sheep_shine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sheep_shine)  # type: ignore
    built = sheep_shine.build_chromatic_materials()
    print(f"[lit] built {len(built)} mats")
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        mat_name = f"ChoralWool_PC_{label}"
        mat = bpy.data.materials.get(mat_name)
        if mat:
            if not sphere.data.materials:
                sphere.data.materials.append(mat)
            else:
                sphere.data.materials[0] = mat
        scene.render.filepath = str(out_dir / f"Lit_PC{pc:02d}_{label}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[lit] rendered {label}")
    # Also sheet
    print(f"[lit] done -> {out_dir}")

def _run_fallback(out_dir: Path, size=512, albedo_mode="worley12"):
    from PIL import Image
    # Use existing Worley12 albedos if present, else flat
    src_root = Path("Saved/Audit/choral_sheep/experiments")
    # fallback to main wool if needed
    search = list(src_root.glob("*"))  # not needed; we just regenerate worley on the fly
    out_dir.mkdir(parents=True, exist_ok=True)
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        base_rgb = tuple(int(c*255) for c in base)
        accent_rgb = tuple(int(c*255) for c in accent)
        # reuse experiment_wool_lab's worley generator if available
        try:
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location("lab", str(Path(__file__).parent / "experiment_wool_lab.py"))
            lab = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lab)
            if albedo_mode == "flat":
                from PIL import Image as _I
                albedo = _I.new("RGB", (size, size), base_rgb)
            else:
                albedo = lab._worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.12 if "12" in albedo_mode else 0.25)
            tmp = out_dir / f"_tmp_{label}.png"
            albedo.save(tmp, "PNG")
            lit = _fallback_lit_sphere(tmp, size, seed=pc)
            lit.save(out_dir / f"Lit_PC{pc:02d}_{label}.png", "PNG")
            tmp.unlink(missing_ok=True)
            print(f"[lit:fallback] {label} -> Lit_PC{pc:02d}_{label}.png")
        except Exception as e:
            print(f"[lit:fallback] {label} failed {e}")
            import traceback; traceback.print_exc()

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--")+1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--out", default="Saved/Audit/choral_sheep/experiments/lit")
    ap.add_argument("--mode", default="worley12", choices=["flat","worley12","worley25"])
    args = ap.parse_args(argv if argv else sys.argv[1:])
    out = Path(args.out)
    if not out.is_absolute():
        out = Path.cwd() / args.out
    try:
        import bpy
        _run_in_blender(out, size=args.size, albedo_mode=args.mode)
    except ImportError:
        print(f"[lit] bpy not available — fallback sphere shading ({args.mode})")
        _run_fallback(out, size=args.size, albedo_mode=args.mode)
    except Exception as e:
        print(f"[lit] blender failed {e} — falling back")
        try: _run_fallback(out, size=args.size, albedo_mode=args.mode)
        except Exception as e2: print(f"fallback also failed {e2}")
