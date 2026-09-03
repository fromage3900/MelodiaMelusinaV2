"""Blender-side scene construction for Resonant World Studio."""

import bpy
import math
import mathutils
import os

from . import bridge


COLL_TERRAIN = "RW_Terrain"
COLL_DRESSING = "RW_Dressing"
COLL_RIG = "RW_Rig"


def clear_generated():
    """Remove only what this addon made, so re-running is idempotent."""
    for name in (COLL_DRESSING, COLL_TERRAIN, COLL_RIG):
        coll = bpy.data.collections.get(name)
        if coll is None:
            continue
        for obj in list(coll.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)


def _collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def terrain_from_obj(obj_path):
    """Read `v x y z r g b` OBJ into a mesh carrying AuraColor."""
    verts, faces, colors = [], [], []
    with open(obj_path) as fh:
        for line in fh:
            p = line.split()
            if not p:
                continue
            if p[0] == "v":
                verts.append((float(p[1]), float(p[2]), float(p[3])))
                colors.append((float(p[4]), float(p[5]), float(p[6]), 1.0)
                              if len(p) >= 7 else (0.5, 0.5, 0.5, 1.0))
            elif p[0] == "f":
                faces.append([int(t.split("/")[0]) - 1 for t in p[1:]])
    if not verts:
        return None

    me = bpy.data.meshes.new("RW_Terrain_mesh")
    me.from_pydata(verts, [], faces)
    me.update()

    attr = me.color_attributes.new(name="AuraColor", type='FLOAT_COLOR',
                                   domain='CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            if vi < len(colors):
                attr.data[li].color = colors[vi]

    me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = False

    obj = bpy.data.objects.new("RW_Terrain", me)
    _collection(COLL_TERRAIN).objects.link(obj)
    obj.data.materials.append(aura_material())
    return obj


def aura_material(emission=2.8, name="M_RW_Aura"):
    """Velocity colour drives base colour AND emission.

    The generator bakes note velocity into vertex colour; earlier builders
    computed it and attached no material, so it was discarded.
    """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (400, 0)
    col = nt.nodes.new('ShaderNodeVertexColor'); col.location = (-400, 0)
    col.layer_name = "AuraColor"
    hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.location = (-200, 0)
    hsv.inputs['Saturation'].default_value = 1.25
    lum = nt.nodes.new('ShaderNodeRGBToBW'); lum.location = (-200, -240)
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (0, -240)
    ramp.color_ramp.interpolation = 'EASE'
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[1].position = 0.98
    mul = nt.nodes.new('ShaderNodeMath'); mul.location = (220, -240)
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = emission

    link = nt.links.new
    link(col.outputs['Color'], hsv.inputs['Color'])
    link(hsv.outputs['Color'], bsdf.inputs['Base Color'])
    link(col.outputs['Color'], lum.inputs['Color'])
    link(lum.outputs['Val'], ramp.inputs['Fac'])
    link(ramp.outputs['Color'], mul.inputs[0])
    if 'Emission Color' in bsdf.inputs:
        link(hsv.outputs['Color'], bsdf.inputs['Emission Color'])
    if 'Emission Strength' in bsdf.inputs:
        link(mul.outputs['Value'], bsdf.inputs['Emission Strength'])
    bsdf.inputs['Roughness'].default_value = 0.62
    link(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def prop_material(name, colour, emission, roughness):
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


_PROP_SHAPE = {
    "resonance_crystal": ("cone", 5.0, 0.12),
    "chime_pillar": ("cylinder", 3.5, 0.30),
    "moss_cluster": ("ico", 0.0, 0.85),
    "songstone": ("cube", 0.0, 0.70),
    "note_bloom": ("circle", 4.0, 0.40),
}


def _template(kind, colour):
    name = "RW_TPL_%s" % kind
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    shape, emit, rough = _PROP_SHAPE.get(kind, ("cube", 0.0, 0.6))
    if shape == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.32, depth=1.1)
    elif shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.18, depth=2.0)
    elif shape == "ico":
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34)
    elif shape == "circle":
        bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.26,
                                          fill_type='NGON')
    else:
        bpy.ops.mesh.primitive_cube_add(size=0.42)

    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(
        prop_material("M_RW_%s" % kind, colour, emit, rough))
    obj.hide_render = True
    obj.location = (0, 0, -9999)
    return obj


def instance_props(props):
    """Linked instances, not realized copies -- keeps memory flat."""
    if not props:
        return 0
    coll = _collection(COLL_DRESSING)
    templates = {}
    made = 0
    for spec in props:
        kind = spec["kind"]
        if kind not in templates:
            templates[kind] = _template(kind, tuple(spec["colour"]))
        inst = bpy.data.objects.new("%s_%d" % (kind, made),
                                    templates[kind].data)
        coll.objects.link(inst)
        x, y, z = spec["location"]
        s = spec["scale"]
        inst.location = (x, y, z)
        inst.scale = (s, s, s)
        inst.rotation_euler = (0, 0, spec["rotation_z"])
        made += 1
    return made


def bounds_of(objs):
    mn = [1e18] * 3
    mx = [-1e18] * 3
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return (mathutils.Vector([(mn[i] + mx[i]) / 2 for i in range(3)]),
            mathutils.Vector([mx[i] - mn[i] for i in range(3)]),
            mathutils.Vector(mn), mathutils.Vector(mx))


def build_world(top=(0.10, 0.13, 0.22), bottom=(0.02, 0.03, 0.05)):
    w = bpy.data.worlds.get("RW_World") or bpy.data.worlds.new("RW_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); out.location = (400, 0)
    bg = nt.nodes.new('ShaderNodeBackground'); bg.location = (200, 0)
    bg.inputs['Strength'].default_value = 1.15
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-60, 0)
    ramp.color_ramp.elements[0].color = (*bottom, 1.0)
    ramp.color_ramp.elements[1].color = (*top, 1.0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-280, 0)
    tex = nt.nodes.new('ShaderNodeTexCoord'); tex.location = (-480, 0)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.location = (-170, -200)
    mr.inputs['From Min'].default_value = -0.3
    mr.inputs['From Max'].default_value = 0.55
    mr.clamp = True
    link = nt.links.new
    link(tex.outputs['Generated'], sep.inputs['Vector'])
    link(sep.outputs['Z'], mr.inputs['Value'])
    link(mr.outputs['Result'], ramp.inputs['Fac'])
    link(ramp.outputs['Color'], bg.inputs['Color'])
    link(bg.outputs['Background'], out.inputs['Surface'])


def build_lights(centre, span, rim=(1.0, 0.62, 0.80)):
    """Energy scales with span^2 -- area lights obey inverse square, so a
    fixed wattage that suits a 3-unit prop is invisible on a 16-unit level."""
    coll = _collection(COLL_RIG)
    unit = span * span
    for name, energy, colour, loc in (
        ("RW_Key", unit * 1.9, (1.0, 0.95, 0.88),
         (centre.x + span * 0.55, centre.y - span * 0.7,
          centre.z + span * 0.65)),
        ("RW_Fill", unit * 0.5, (0.65, 0.78, 1.0),
         (centre.x - span * 0.75, centre.y - span * 0.45,
          centre.z + span * 0.3)),
        ("RW_Rim", unit * 1.3, rim,
         (centre.x, centre.y + span * 0.8, centre.z + span * 0.5)),
    ):
        d = bpy.data.lights.new(name, type='AREA')
        d.energy = energy
        d.color = colour
        d.size = span * 0.5
        o = bpy.data.objects.new(name, d)
        o.location = loc
        coll.objects.link(o)
        v = centre - mathutils.Vector(loc)
        o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()

    sd = bpy.data.lights.new("RW_Sun", type='SUN')
    sd.energy = 3.0
    sd.angle = math.radians(2.0)
    so = bpy.data.objects.new("RW_Sun", sd)
    so.location = (centre.x, centre.y - span * 0.4, centre.z + span)
    so.rotation_euler = (math.radians(58), 0, math.radians(40))
    coll.objects.link(so)


def build_camera(centre, size, height_fn=None, eye_level=False, lens=40.0):
    """Frame from real bounds. For eye level, sample the LOCAL column height
    so the camera stands on the ground instead of inside it."""
    coll = _collection(COLL_RIG)
    span = max(size)
    cd = bpy.data.cameras.new("RW_Camera")
    cd.lens = lens
    cd.clip_start = 0.01
    cd.clip_end = span * 40
    cam = bpy.data.objects.new("RW_Camera", cd)
    coll.objects.link(cam)

    fov = 2 * math.atan((cd.sensor_width * 0.5) / lens)
    fit = max(size.x, size.y)
    dist = (fit * 0.5) / math.tan(fov * 0.5) * (0.6 if eye_level else 1.3)

    az = math.radians(-38)
    el = math.radians(4 if eye_level else 26)
    off_x = dist * math.cos(el) * math.sin(az)
    off_y = -dist * math.cos(el) * math.cos(az)

    if eye_level and height_fn is not None:
        cx, cy = centre.x + off_x, centre.y + off_y
        cam.location = (cx, cy, height_fn(cx, cy) + 1.7)
        target = mathutils.Vector(
            (centre.x, centre.y, height_fn(centre.x, centre.y) + 1.3))
    else:
        cam.location = (centre.x + off_x, centre.y + off_y,
                        centre.z + dist * math.sin(el))
        target = centre

    v = target - mathutils.Vector(cam.location)
    cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    cd.dof.use_dof = True
    cd.dof.focus_distance = max(0.1, v.length)
    cd.dof.aperture_fstop = 2.4 if eye_level else 4.0
    bpy.context.scene.camera = cam
    return cam


def melusina_asset_path():
    """Repo path to Melusina_Asset.blend, or None if not exported yet."""
    candidate = os.path.join(bridge.repo_root(), "Tools",
                             "MelodiaProceduralStudio", "Assets",
                             "Melusina_Asset.blend")
    return candidate if os.path.exists(candidate) else None


def add_melusina(field, centre):
    """Append Melusina to the rig collection, standing on the column beneath
    her centre -- NOT the bounding box top. Using global bounds is what made
    her float in earlier versions."""
    import bpy
    asset = melusina_asset_path()
    if asset is None:
        return False, None

    from . import bridge as br
    _ww, td = br.load_modules()

    with bpy.data.libraries.load(asset, link=False) as (src, dst):
        if "Asset_Melusina" not in src.collections:
            return False, None
        dst.collections = ["Asset_Melusina"]
    colls = [c for c in bpy.data.collections
             if c.name.startswith("Asset_Melusina")]
    if not colls:
        return False, None
    coll = colls[-1]
    rig = _collection(COLL_RIG)
    if coll.name not in {c.name for c in bpy.context.scene.collection.children}:
        bpy.context.scene.collection.children.link(coll)

    holder = bpy.data.objects.new("RW_Melusina_Root", None)
    rig.objects.link(holder)
    for o in coll.objects:
        if o.parent is None:
            o.parent = holder

    ground = td.surface_height_at(field, centre.x, centre.y)
    holder.location = (centre.x, centre.y, ground)
    return True, ground


def configure_render(samples=48):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    sc.view_settings.exposure = 0.25
    ee = getattr(sc, "eevee", None)
    if ee:
        for key, val in (("taa_render_samples", samples),
                         ("use_raytracing", True),
                         ("use_shadows", True)):
            if hasattr(ee, key):
                try:
                    setattr(ee, key, val)
                except Exception:
                    pass
