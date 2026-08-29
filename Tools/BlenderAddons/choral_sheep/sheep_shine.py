#!/usr/bin/env python3
"""Choral Sheep shader + variation toolkit (run inside live Blender 5.2).

Make the Choral Sheep companion 'shine' with a woolly Principled look and
generate a family of named color variations that fit Melodia's Resonant World
palette. Geometry is never touched -- materials only, so the rig is safe.

How to run (Blender > Scripting workspace > Python console):
    exec(compile(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/BlenderAddons/choral_sheep/sheep_shine.py", encoding="utf-8").read(), "x", "exec"))
Then call the functions interactively, e.g.:
    build_wool_material("ChoralWool_Pearl")        # name one sheep material 'shine'
    apply_variation("ChoralWool_Sakura")           # recolour the sheep in place
    make_variations()                              # build the full palette as materials
    cycle_variations()                             # auto-cycle a few for a look
"""
import bpy
import math
from random import Random

# --- Resonant World palette (matches Melodia terrain/creature colour language) ---
VARIATIONS = {
    # name            : base RGB          sheen   accent(emissive)RGB
    "Pearl":          ((0.94, 0.93, 0.90), 0.55, (0.62, 0.85, 1.00)),
    "Sakura":         ((0.99, 0.82, 0.84), 0.50, (1.00, 0.62, 0.80)),
    "Sage":           ((0.78, 0.86, 0.74), 0.50, (0.55, 0.90, 0.65)),
    "Periwinkle":     ((0.76, 0.79, 0.96), 0.52, (0.70, 0.72, 1.00)),
    "DuskGold":       ((0.95, 0.82, 0.55), 0.60, (1.00, 0.70, 0.35)),
    "Moss":           ((0.58, 0.70, 0.56), 0.45, (0.62, 0.90, 0.55)),
    "Reverie":        ((0.88, 0.80, 0.96), 0.58, (0.85, 0.70, 1.00)),
    "Ember":          ((0.95, 0.62, 0.50), 0.55, (1.00, 0.45, 0.40)),
    "Moonlit":        ((0.82, 0.87, 0.95), 0.62, (0.85, 0.95, 1.00)),
    "Honeydew":       ((0.88, 0.92, 0.72), 0.48, (0.70, 0.95, 0.50)),
}

_ACCENT_EMIT = 1.2          # resonance accent emission strength

# --- Chromatic octave kit (tonight's contract): one coat per pitch class ------
# ChoralSheep 12-variant system -- variant N sings scale-degree N.
# PC label -> hue fraction of the color wheel; base/accent derive as pastel
# (Nikkilike softness) so all 12 read as one flock, twelve notes.
PITCH_CLASS_HUES = {
    0:  ("C",  0.000),
    1:  ("Cs", 0.083),
    2:  ("D",  0.167),
    3:  ("Ds", 0.250),
    4:  ("E",  0.333),
    5:  ("F",  0.417),
    6:  ("Fs", 0.500),
    7:  ("G",  0.583),
    8:  ("Gs", 0.667),
    9:  ("A",  0.750),
    10: ("As", 0.833),
    11: ("B",  0.917),
}


def _pastel_pair(hue, sat=0.38, val=0.92):
    """Pastel body + saturated accent RGB triple from a hue fraction."""
    import colorsys
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent


def chromatic_variations():
    """Build the 12-entry {label: (base, sheen, accent)} chromatic kit."""
    out = {}
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        # sheen rises through the octave: the leading tone shimmers hardest
        sheen = 0.46 + (pc / 12.0) * 0.18
        out[label] = (base, round(sheen, 3), accent)
    return out


def build_chromatic_materials():
    """Create all 12 pitch-class wool materials; returns list of material names."""
    built = []
    for label, (base, sheen, accent) in chromatic_variations().items():
        name = f"ChoralWool_PC_{label}"
        build_wool_material(name, base=base, sheen=sheen, accent=accent)
        built.append(name)
        print(f"[sheep] built chromatic coat {name}")
    return built


def apply_pitch_class(pc, target=None):
    """Apply the chromatic coat for pitch class 0..11 (C..B)."""
    if pc not in PITCH_CLASS_HUES:
        raise KeyError(f"pitch class must be 0..11, got {pc!r}")
    label = PITCH_CLASS_HUES[pc][0]
    base, sheen, accent = chromatic_variations()[label]
    matname = f"ChoralWool_PC_{label}"
    build_wool_material(matname, base=base, sheen=sheen, accent=accent)
    sheep = target or _find_sheep_mesh()
    if not sheep.data.materials:
        sheep.data.materials.append(bpy.data.materials.get(matname))
    else:
        sheep.data.materials[0] = bpy.data.materials.get(matname)
    print(f"[sheep] applied pitch-class coat {matname} (pc={pc})")
    return matname


def _find_sheep_mesh():
    """Return the sheep mesh object by known names, else the largest mesh."""
    for name in ("Skin_Sheep_ZSpheres2", "Skin_Sheep_25Spheres2", "sheep", "Sheep"):
        if name in bpy.data.objects and bpy.data.objects[name].type == "MESH":
            return bpy.data.objects[name]
    # prefer any mesh starting with 'Skin_' (character mesh naming convention)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("Skin_"):
            return o
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh object found")
    return max(meshes, key=lambda o: o.dimensions.x * o.dimensions.y * o.dimensions.z)


def build_wool_material(name="ChoralWool_Pearl", base=(0.94, 0.93, 0.90),
                        sheen=0.55, accent=(0.62, 0.85, 1.00), create=True):
    """Create (or update) a woolly + shiny Principled material for the sheep.

    - subsurface scattering for soft wool translucency
    - moderate roughness + a clearcoat pass for the 'shine'
    - a tiny emissive accent tied to Melodia's resonance-glow language

    NOTE (Blender 5.2): the Principled BSDF renamed several inputs vs 4.x --
      'Subsurface' -> 'Subsurface Weight', 'Sheen' -> 'Sheen Weight',
      'Clearcoat' -> 'Coat Weight', 'Clearcoat Roughness' -> 'Coat Roughness'.
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        if not create:
            return None
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (100, 0)
    principled.inputs["Base Color"].default_value = (*base, 1.0)
    principled.inputs["Subsurface Weight"].default_value = 0.35
    principled.inputs["Subsurface Radius"].default_value = (1.0, 1.0, 1.0)
    principled.inputs["Roughness"].default_value = 0.42
    principled.inputs["Sheen Weight"].default_value = sheen
    principled.inputs["Sheen Tint"].default_value = (0.7, 0.7, 0.7, 1.0)
    principled.inputs["Coat Weight"].default_value = 0.5
    principled.inputs["Coat Roughness"].default_value = 0.2

    # Resonance accent glow (emissive) -- small, classy, on the wool
    emiss = nt.nodes.new("ShaderNodeEmission")
    emiss.location = (100, -220)
    emiss.inputs["Color"].default_value = (*accent, 1.0)
    emiss.inputs["Strength"].default_value = _ACCENT_EMIT
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (300, -100)
    mix.inputs["Fac"].default_value = 0.06
    nt.links.new(principled.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emiss.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def apply_variation(variation_name, target=None):
    """Assign a built variation material to the sheep's first material slot."""
    if variation_name not in VARIATIONS:
        raise KeyError(f"unknown variation {variation_name!r}; have {list(VARIATIONS)}")
    base, sheen, accent = VARIATIONS[variation_name]
    matname = f"ChoralWool_{variation_name}"
    build_wool_material(matname, base=base, sheen=sheen, accent=accent)
    sheep = target or _find_sheep_mesh()
    if not sheep.data.materials:
        sheep.data.materials.append(bpy.data.materials.get(matname))
    else:
        sheep.data.materials[0] = bpy.data.materials.get(matname)
    print(f"[sheep] applied variation '{variation_name}' -> {matname}")
    return matname


def make_variations():
    """Build every named variation as a material (not yet applied)."""
    built = []
    for name, (base, sheen, accent) in VARIATIONS.items():
        matname = f"ChoralWool_{name}"
        build_wool_material(matname, base=base, sheen=sheen, accent=accent)
        built.append(matname)
    print(f"[sheep] built {len(built)} variation materials: {built}")
    return built


def cycle_variations(seconds=2.0, subset=None):
    """Preview-swap the sheep's material across the palette for a look."""
    import bpy
    names = subset or list(VARIATIONS)
    sheep = _find_sheep_mesh()
    for name in names:
        apply_variation(name, sheep)
        print(f"[sheep] preview: {name}")


def shiny_accessories(target=None):
    """Give hooves/nose a glossy dark 'shiny' material (optional polish)."""
    acc = bpy.data.materials.get("ChoralSheep_ShinyAccent")
    if acc is None:
        acc = bpy.data.materials.new("ChoralSheep_ShinyAccent")
    acc.use_nodes = True
    nt = acc.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled"); principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (0.12, 0.10, 0.12, 1.0)
    principled.inputs["Roughness"].default_value = 0.18
    principled.inputs["Clearcoat"].default_value = 1.0
    principled.inputs["Clearcoat Roughness"].default_value = 0.1
    nt.links.new(principled.outputs["BSDF"], out.inputs["Surface"])
    print("[sheep] ShinyAccent material ready (assign to hooves/nose slots)")
    return acc


if __name__ == "__main__":
    # quick non-destructive demo when executed directly
    make_variations()
    apply_variation("Pearl")
    print("[sheep] ready. Variations:", list(VARIATIONS))
