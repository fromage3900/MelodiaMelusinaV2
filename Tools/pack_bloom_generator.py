"""Pack the musical flower generator as a sellable Blender 5.2 asset pack.

  blender --background --python Tools/pack_bloom_generator.py -- [out_dir]

Writes <out_dir>/ResonantBlooms_v0.1/:
  ResonantBlooms.blend       asset library (Rose, Peony, Vine, Petal node groups + 3 materials, all marked as assets)
  ResonantBlooms_Demo.blend  the same plus a lit demo scene (3 growth stages of each flower, vine)
  previews/*.png             renders of the demo scene
  README.md, LICENSE.txt     usage + parameters; licence is a DRAFT for the owner/legal to approve

Self-contained: loads only deploy/surreal_arch/melodia_gn/blooms.py (no Melodia registry, no third-party code).
"""
import importlib.util
import math
import sys
import types
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
GN_DIR = ROOT / "deploy" / "surreal_arch" / "melodia_gn"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = (Path(args[0]).resolve() if args else ROOT / "Saved" / "Staging" / "MelusinaBlooms" / "release") / "ResonantBlooms_v0.1"
(OUT / "previews").mkdir(parents=True, exist_ok=True)

pkg = types.ModuleType("melodia_gn")
pkg.__path__ = [str(GN_DIR)]
sys.modules["melodia_gn"] = pkg
spec = importlib.util.spec_from_file_location("melodia_gn.blooms", GN_DIR / "blooms.py")
blooms = importlib.util.module_from_spec(spec)
sys.modules["melodia_gn.blooms"] = blooms
spec.loader.exec_module(blooms)

PRODUCT = {
    "Bloom_Rose": (blooms.build_bloom_rose, "Resonant Rose: golden-angle whorls of 3/5/8/13 petals (triad), Growth 0 bud .. 1 bloom."),
    "Bloom_Peony": (blooms.build_bloom_peony, "Cadence Peony: five ruffled layers of 5/8/13/21/21 petals (pentatonic), Growth 0 bud .. 1 bloom."),
    "Bloom_Vine": (blooms.build_vine_melody, "Melody Vine: swaying vine, length driven by Growth, leaves on 'Notes' along its arclength."),
    "Bloom_Petal": (blooms.build_petal, "Single curled petal - for particle petal shed / scattering."),
}


def make_materials():
    def principled(name, base, rough, sss=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = rough
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = sss
        nt.links.new(bsdf.outputs[0], out.inputs[0])
        bsdf.location, out.location = (0, 0), (300, 0)
        return m, nt, bsdf

    petal, nt, bsdf = principled("Bloom_Petal_Mat", None, 0.45, 0.25)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_type, attr.attribute_name = "GEOMETRY", "GrowthCol"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(attr.outputs["Color"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.label = "Petal colour: heart -> edge (edit the stops)"
    ramp.color_ramp.elements[0].color = (0.62, 0.05, 0.16, 1)
    ramp.color_ramp.elements[1].color = (1.0, 0.55, 0.66, 1)
    nt.links.new(sep.outputs["Blue"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    attr.location, sep.location, ramp.location = (-900, 0), (-700, 0), (-450, 0)
    pet2, nt2, bsdf2 = principled("Bloom_PeonyPetal_Mat", None, 0.5, 0.3)
    a2 = nt2.nodes.new("ShaderNodeAttribute")
    a2.attribute_type, a2.attribute_name = "GEOMETRY", "GrowthCol"
    sp2 = nt2.nodes.new("ShaderNodeSeparateColor")
    nt2.links.new(a2.outputs["Color"], sp2.inputs[0])
    rp2 = nt2.nodes.new("ShaderNodeValToRGB")
    rp2.label = "Petal colour: heart -> edge (edit the stops)"
    rp2.color_ramp.elements[0].color = (0.85, 0.30, 0.50, 1)
    rp2.color_ramp.elements[1].color = (1.0, 0.86, 0.90, 1)
    nt2.links.new(sp2.outputs["Blue"], rp2.inputs["Fac"])
    nt2.links.new(rp2.outputs["Color"], bsdf2.inputs["Base Color"])
    a2.location, sp2.location, rp2.location = (-900, 0), (-700, 0), (-450, 0)
    accent, _, ab = principled("Bloom_Accent_Mat", None, 0.3)
    ab.inputs["Base Color"].default_value = (1.0, 0.78, 0.25, 1)
    ab.inputs["Metallic"].default_value = 0.8
    stem, _, sb = principled("Bloom_Stem_Mat", None, 0.55)
    sb.inputs["Base Color"].default_value = (0.16, 0.42, 0.18, 1)
    return [petal, accent, stem, pet2]


def build_groups():
    trees = {}
    for name, (fn, desc) in PRODUCT.items():
        t = fn(name)
        t.name = name
        t.use_fake_user = True
        t.asset_mark()
        t.asset_data.description = desc
        for tag in ("flower", "procedural", "growth", "music", "nature"):
            t.asset_data.tags.new(tag)
        trees[name] = t
    return trees


def put(trees, mats, kind, growth, x, y=0.0, seed=1.0, scale=1.0):
    t = trees[kind].copy()
    for it in t.interface.items_tree:
        if getattr(it, "in_out", "") == "INPUT":
            if it.name == "Growth":
                it.default_value = growth
            elif it.name == "Seed":
                it.default_value = seed
            elif it.name == "Scale" and kind in ("Bloom_Rose", "Bloom_Peony"):
                it.default_value = scale
    me = bpy.data.meshes.new(f"{kind}_{growth}")
    ob = bpy.data.objects.new(f"{kind}_{growth}", me)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new("Bloom", "NODES")
    md.node_group = t
    ob.location = (x, y, 0.0)
    return ob


def demo_scene(trees, mats):
    sc = bpy.context.scene
    ground = bpy.data.objects.new("Ground", bpy.data.meshes.new("Ground"))
    sc.collection.objects.link(ground)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6.0)
    bm.to_mesh(ground.data)
    bm.free()
    gm = bpy.data.materials.new("Demo_Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.56, 0.58, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(gm)
    ground.location = (0, 0, -0.23)
    for i, g in enumerate((0.0, 0.55, 1.0)):
        put(trees, mats, "Bloom_Rose", g, -0.55 + i * 0.4, y=-0.25, seed=3.0)
        put(trees, mats, "Bloom_Peony", g, -0.55 + i * 0.4, y=0.25, seed=5.0)
    put(trees, mats, "Bloom_Vine", 1.0, 0.85, y=0.0, seed=2.0)
    put(trees, mats, "Bloom_Vine", 0.6, 1.0, y=0.2, seed=7.0)
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    sc.collection.objects.link(cam)
    cam.location = (0.25, -2.5, 0.95)
    cam.rotation_euler = (math.radians(71), 0, math.radians(1))
    cam.data.lens = 42
    sc.camera = cam
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(25))
    sc.collection.objects.link(sun)
    sc.world = bpy.data.worlds.new("Demo")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.86, 0.88, 0.98, 1)
    bg.inputs["Strength"].default_value = 1.0
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900


def render(path, engine):
    sc = bpy.context.scene
    try:
        sc.render.engine = engine
        if engine == "CYCLES":
            sc.cycles.device = "CPU"
            sc.cycles.samples = 40
            sc.cycles.use_denoising = True
    except TypeError as exc:
        print("ENGINE-FALLBACK", exc)
        sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.engine, path)


for o in list(bpy.data.objects):            # factory scene ships a default cube/light/camera
    bpy.data.objects.remove(o)
trees = build_groups()
mats = make_materials()
for t in trees.values():
    for it in t.interface.items_tree:
        if getattr(it, "in_out", "") == "INPUT" and it.name.endswith(" Material"):
            it.default_value = {"Petal Material": mats[3] if t.name == "Bloom_Peony" else mats[0], "Accent Material": mats[1], "Stem Material": mats[2]}[it.name]
for m in mats:
    m.use_fake_user = True
    m.asset_mark()
    m.asset_data.description = "Resonant Blooms starter material"
# ---- Lane 2: pack Melodia foliage textures ----
try:
    _spec = importlib.util.spec_from_file_location("pack_textures", ROOT / "Tools" / "foliage_pipeline" / "pack_textures.py")
    _pt = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_pt)
    _copied = _pt.copy_to_release(OUT / "Textures" / "MelodiaFoliage")
    _imgs = _pt.import_and_pack()
    _packed = sum(1 for _i in bpy.data.images if getattr(_i, "packed_file", None) is not None)
    _cards = _pt.dress_cards(OUT)
    print("TEXTURES_COPIED", len(_copied), "TEXTURES_PACKED", len(_imgs), "PACKED_VERIFY", _packed, "CARDS_DRESSED", len(_cards))
except Exception as _e:
    print("TEXTURE_PACK_SKIP", repr(_e))

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "ResonantBlooms.blend"), compress=True)
demo_scene(trees, mats)
render(OUT / "previews" / "demo_hero.png", "CYCLES")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "ResonantBlooms_Demo.blend"), compress=True)
import shutil, zipfile
src = OUT / "source"
src.mkdir(exist_ok=True)
for rel in ("deploy/surreal_arch/melodia_gn/blooms.py", "Tools/pack_bloom_generator.py", "Tools/bloom_preview.py", "Tools/bake_bloom_kit.py"):
    f = ROOT / rel
    if f.exists():
        shutil.copy2(f, src / f.name)
docs = ROOT / "Tools" / "bloom_pack_docs"
if docs.exists():
    for f in docs.iterdir():
        shutil.copy2(f, OUT / f.name)
for stale in OUT.glob("*.blend1"):
    stale.unlink()
zip_path = OUT.parent / (OUT.name + ".zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(OUT.parent))
print("ZIP", zip_path, zip_path.stat().st_size)
print("PACK_DONE", OUT)
