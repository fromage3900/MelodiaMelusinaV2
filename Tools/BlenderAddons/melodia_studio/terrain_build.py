"""Terrain mesh / aura material / dressing instancing for Melodia Studio.

Split out of studio_panel.py on 2026-10-04 (monolith split, no logic change).
Everything here builds bpy data from the generator's OBJ output; the primary
panel drives it via operators.generate_from_midi.
"""

import os

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore


# ------------------------------------------------------------- mesh build

def build_terrain_mesh(obj_path, mesh_name="Terrain"):
    """Build a mesh from the generator's OBJ (v x y z r g b) format."""
    if bpy is None:
        return None
    if not os.path.exists(obj_path):
        return None

    verts, faces, colors = [], [], []
    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                if len(parts) >= 7:
                    colors.append((float(parts[4]), float(parts[5]), float(parts[6]), 1.0))
                else:
                    colors.append((0.5, 0.5, 0.5, 1.0))
            elif parts[0] == "f":
                faces.append([int(p.split("/")[0]) - 1 for p in parts[1:]])

    if not verts:
        return None

    mesh = bpy.data.meshes.new(mesh_name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    if colors:
        attr = mesh.color_attributes.new(name="AuraColor", type='FLOAT_COLOR', domain='CORNER')
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                vidx = mesh.loops[loop_idx].vertex_index
                if vidx < len(colors):
                    attr.data[loop_idx].color = colors[vidx]

    if len(mesh.uv_layers) == 0:
        mesh.uv_layers.new(name="UVMap")

    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(build_aura_material())
    return obj


def build_aura_material(name="M_ResonantAura"):
    """Material that actually samples AuraColor for base colour + emission."""
    if bpy is None:
        return None
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    col = nt.nodes.new('ShaderNodeVertexColor')
    col.layer_name = "AuraColor"
    col.location = (-300, 0)
    lum = nt.nodes.new('ShaderNodeRGBToBW')
    lum.location = (-100, -200)
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (60, -200)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.95
    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(col.outputs['Color'], lum.inputs['Color'])
    nt.links.new(lum.outputs['Val'], ramp.inputs['Fac'])
    if 'Emission Color' in bsdf.inputs:
        nt.links.new(col.outputs['Color'], bsdf.inputs['Emission Color'])
    if 'Emission Strength' in bsdf.inputs:
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Strength'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


# ---------------------------------------------------------------- dressing instancing (linked, low memory)
# Reuses the proven pattern from resonant_world_studio/build.py:176 but
# lives here so the primary Melodia Studio panel can instance without
# depending on that sibling addon.

_DRESS_COLL = "MS_Dressing"
_PROP_SHAPE = {
    "resonance_crystal": ("cone", 5.0, 0.12),
    "chime_pillar": ("cylinder", 3.5, 0.30),
    "moss_cluster": ("ico", 0.0, 0.85),
    "songstone": ("cube", 0.0, 0.70),
    "note_bloom": ("circle", 4.0, 0.40),
}

def _dress_collection():
    if bpy is None:
        return None
    coll = bpy.data.collections.get(_DRESS_COLL)
    if coll is None:
        coll = bpy.data.collections.new(_DRESS_COLL)
        bpy.context.scene.collection.children.link(coll)
    return coll

def _clear_dressing():
    if bpy is None:
        return 0
    coll = bpy.data.collections.get(_DRESS_COLL)
    if coll is None:
        # also clear legacy loose objects with MS_Dress prefix
        removed = 0
        for obj in list(bpy.data.objects):
            if obj.name.startswith("MS_Dress_"):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed += 1
                except Exception:
                    pass
        return removed
    for obj in list(coll.all_objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass
    try:
        # keep the collection for next run
        pass
    except Exception:
        pass
    return 1

def _prop_material(name, colour, emission, roughness):
    if bpy is None:
        return None
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (300, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (0, 0)
    b.inputs['Base Color'].default_value = (*colour, 1.0)
    b.inputs['Roughness'].default_value = roughness
    if emission > 0:
        if 'Emission Color' in b.inputs:
            b.inputs['Emission Color'].default_value = (*colour, 1.0)
        if 'Emission Strength' in b.inputs:
            b.inputs['Emission Strength'].default_value = emission
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return mat

def _template_object(kind, colour):
    if bpy is None:
        return None
    name = f"MS_TPL_{kind}"
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return existing
    shape, emit, rough = _PROP_SHAPE.get(kind, ("cube", 0.0, 0.6))
    try:
        if shape == "cone":
            bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.32, depth=1.1)
        elif shape == "cylinder":
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.18, depth=2.0)
        elif shape == "ico":
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34)
        elif shape == "circle":
            bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.26, fill_type='NGON')
        else:
            bpy.ops.mesh.primitive_cube_add(size=0.42)
    except Exception:
        return None
    obj = bpy.context.active_object
    if obj is None:
        return None
    obj.name = name
    try:
        obj.data.materials.append(_prop_material(f"M_MS_{kind}", colour, emit, rough))
    except Exception:
        pass
    obj.hide_render = True
    obj.hide_viewport = True
    # move template far away so it never renders in view
    try:
        obj.location = (0, 0, -9999)
        obj.hide_set(True)
    except Exception:
        pass
    return obj

def _instance_dressing(midi_path: str, style_id: str, seed: int, budget: int) -> int:
    """Build field deterministically and instance dressing props. Returns count."""
    if bpy is None:
        return 0
    _clear_dressing()
    if style_id == "bare":
        return 0
    # Build field using shared core.field.build_field() pipeline
    try:
        from . import terrain_dressing as td
        from .core.field import build_field
        result = build_field(midi_path, "walkable_valley", source="walkable")
        if not result["ok"]:
            return 0
        field = result["field"]
        plan, _stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=budget)
    except Exception:
        return 0
    if not plan:
        return 0
    coll = _dress_collection()
    templates: dict = {}
    made = 0
    for spec in plan:
        kind = spec["kind"]
        if kind not in templates:
            tpl = _template_object(kind, tuple(spec["colour"]))
            if tpl is None:
                continue
            templates[kind] = tpl
        tpl = templates.get(kind)
        if tpl is None or tpl.data is None:
            continue
        try:
            inst = bpy.data.objects.new(f"MS_Dress_{kind}_{made}", tpl.data)
            coll.objects.link(inst)
            x, y, z = spec["location"]
            s = spec["scale"]
            inst.location = (float(x), float(y), float(z))
            inst.scale = (float(s), float(s), float(s))
            inst.rotation_euler = (0, 0, float(spec["rotation_z"]))
            made += 1
        except Exception:
            continue
    return made
