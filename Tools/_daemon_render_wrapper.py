"""Blender render wrapper for the MIDI World-Gen Daemon.

Reads a job JSON written by the daemon, builds the scene, renders, and exits.
This runs INSIDE Blender (has bpy).

Usage:
  blender --background --factory-startup --python _daemon_render_wrapper.py
"""

import bpy
import os
import sys
import json
import math
import mathutils

from worldgen_tooling_contracts import path_is_within

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
for p in (ADDON,):
    if p not in sys.path:
        sys.path.insert(0, p)


def load_job():
    """Load the unique job passed by the parent daemon."""
    path = os.environ.get("MELODIA_WORLDGEN_JOB")
    if not path:
        raise RuntimeError("MELODIA_WORLDGEN_JOB was not provided")
    if not os.path.exists(path):
        raise FileNotFoundError("World-gen job not found: %s" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_job(job):
    """Reject malformed or path-escaping jobs before Blender reads/writes."""
    required = {"obj", "midi", "preset", "out", "props", "camera"}
    missing = sorted(required.difference(job))
    if missing:
        raise ValueError("World-gen job missing keys: %s" % ", ".join(missing))
    allowed_temp = os.environ.get("MELODIA_WORLDGEN_ALLOWED_TEMP")
    allowed_out = os.environ.get("MELODIA_WORLDGEN_ALLOWED_OUT")
    if not allowed_temp or not allowed_out:
        raise RuntimeError("World-gen path allowlists were not provided")
    if not path_is_within(job["obj"], allowed_temp):
        raise ValueError("OBJ path escapes the allowed temporary directory")
    if not path_is_within(job["out"], allowed_out):
        raise ValueError("Render path escapes the allowed audit directory")


def import_obj(path):
    verts, faces, colors = [], [], []
    with open(path) as f:
        for line in f:
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
    me = bpy.data.meshes.new("DaemonTerrain")
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
    obj = bpy.data.objects.new("DaemonTerrain", me)
    bpy.context.collection.objects.link(obj)
    return obj


def aura_material(emission=2.8):
    mat = bpy.data.materials.new("M_DaemonAura")
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
    L = nt.links.new
    L(col.outputs['Color'], hsv.inputs['Color'])
    L(hsv.outputs['Color'], bsdf.inputs['Base Color'])
    L(col.outputs['Color'], lum.inputs['Color'])
    L(lum.outputs['Val'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], mul.inputs[0])
    if 'Emission Color' in bsdf.inputs:
        L(hsv.outputs['Color'], bsdf.inputs['Emission Color'])
    if 'Emission Strength' in bsdf.inputs:
        L(mul.outputs['Value'], bsdf.inputs['Emission Strength'])
    bsdf.inputs['Roughness'].default_value = 0.62
    L(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def instance_props(props):
    if not props:
        return
    coll = bpy.data.collections.new("DaemonDressing")
    bpy.context.scene.collection.children.link(coll)
    for spec in props:
        kind = spec["kind"]
        if kind == "resonance_crystal":
            bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.32, depth=1.1)
        elif kind == "chime_pillar":
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.18, depth=2.0)
        elif kind == "moss_cluster":
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34)
        elif kind == "songstone":
            bpy.ops.mesh.primitive_cube_add(size=0.42)
        else:
            bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.26,
                                              fill_type='NGON')
        inst = bpy.context.active_object
        coll.objects.link(inst)
        x, y, z = spec["location"]
        s = spec["scale"]
        inst.location = (x, y, z)
        inst.scale = (s, s, s)
        inst.rotation_euler = (0, 0, spec["rotation_z"])


def build_world(top=(0.10, 0.13, 0.22), bottom=(0.02, 0.03, 0.05)):
    w = bpy.data.worlds.new("DaemonWorld")
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
    L = nt.links.new
    L(tex.outputs['Generated'], sep.inputs['Vector'])
    L(sep.outputs['Z'], mr.inputs['Value'])
    L(mr.outputs['Result'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], bg.inputs['Color'])
    L(bg.outputs['Background'], out.inputs['Surface'])


def build_lights(centre, span, rim=(1.0, 0.62, 0.80)):
    unit = span * span
    for name, energy, colour, loc in (
        ("DaemonKey", unit * 1.9, (1.0, 0.95, 0.88),
         (centre.x + span * 0.55, centre.y - span * 0.7,
          centre.z + span * 0.65)),
        ("DaemonFill", unit * 0.5, (0.65, 0.78, 1.0),
         (centre.x - span * 0.75, centre.y - span * 0.45,
          centre.z + span * 0.3)),
        ("DaemonRim", unit * 1.3, rim,
         (centre.x, centre.y + span * 0.8, centre.z + span * 0.5)),
    ):
        d = bpy.data.lights.new(name, type='AREA')
        d.energy = energy
        d.color = colour
        d.size = span * 0.5
        o = bpy.data.objects.new(name, d)
        o.location = loc
        bpy.context.scene.collection.objects.link(o)


def build_camera(centre, size, cam_cfg, field_height_fn=None):
    span = max(size)
    cd = bpy.data.cameras.new("DaemonCam")
    cd.lens = cam_cfg.get("lens", 40)
    cd.clip_start = 0.01
    cd.clip_end = span * 40
    cam = bpy.data.objects.new("DaemonCam", cd)
    bpy.context.scene.collection.objects.link(cam)
    fov = 2 * math.atan((cd.sensor_width * 0.5) / cd.lens)
    fit = max(size.x, size.y)
    dist = (fit * 0.5) / math.tan(fov * 0.5) * cam_cfg.get("dist_mult", 1.3)
    az = math.radians(cam_cfg.get("azimuth", -38))
    el = math.radians(cam_cfg.get("elevation", 26))
    cam.location = (centre.x + dist * math.cos(el) * math.sin(az),
                    centre.y - dist * math.cos(el) * math.cos(az),
                    centre.z + dist * math.sin(el))
    target = centre
    v = target - mathutils.Vector(cam.location)
    cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    cd.dof.use_dof = True
    cd.dof.focus_distance = max(0.1, v.length)
    cd.dof.aperture_fstop = 4.0
    bpy.context.scene.camera = cam


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
            mathutils.Vector([mx[i] - mn[i] for i in range(3)]))


def main():
    job = load_job()
    validate_job(job)

    print("[wrapper] Job: %s / %s" % (job["midi"], job["preset"]), flush=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Terrain
    terrain = import_obj(job["obj"])
    if terrain is None:
        raise RuntimeError("World-gen OBJ produced no vertices")
    terrain.data.materials.append(aura_material())

    # Dressing
    instance_props(job.get("props", []))

    # World + lights
    build_world()
    centre, size = bounds_of([terrain])[:2]
    span = max(size)
    build_lights(centre, span)

    # Camera
    build_camera(centre, size, job.get("camera", {}))

    # Render
    final_path = os.path.abspath(job["out"])
    partial_path = final_path + ".%d.partial.png" % os.getpid()
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = partial_path
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(partial_path):
        raise RuntimeError("Blender reported success without a render artifact")
    os.replace(partial_path, final_path)

    print("[wrapper] Rendered: %s" % final_path, flush=True)


if __name__ == "__main__":
    main()
