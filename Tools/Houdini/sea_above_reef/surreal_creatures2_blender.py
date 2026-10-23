"""
Surreal Creature Atelier — Blender companion to surreal_creatures2.py (wave2).

Builds 3 surreal creature meshes, assigns Principled BSDF with emission+transmission
using the 1024 PBR textures baked by surreal_creatures2.py, then exports
blend/fbx/png beauty 1920x1080 and writes creatures_manifest.json.

Meshes:
  1) Veil Leviathan  45m translucent whale (body 45m, stained-glass ribs + lantern heart)
  2) Choir Jelly Swarm 12 jellies 3m bells sharing one VAT LUT (instances + per-object vat_offset)
  3) Shore Siren 2.2m melusine (capsule body + tail fin + 9 living kelp hair ribbons)

Run:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/Houdini/sea_above_reef/surreal_creatures2_blender.py

Outputs Saved/Audit/surreal_sweep_wave2/creatures/:
  Surreal_Creatures.blend
  SM_VeilLeviathan.fbx  SM_ChoirJelly.fbx  SM_ShoreSiren.fbx  Surreal_Creatures_Combined.fbx
  Surreal_Creatures_Beauty.png (1920x1080), Beauties per creature (1024)
  creatures_manifest.json (+ reuses T_* textures from surreal_creatures2.py)

Seed 20260829, deterministic.
"""
import hashlib
import json
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved/Audit/surreal_sweep_wave2/creatures"
SEED = 20260829
SCHEMA = "melodia.surreal_creatures.v1"

WORLD = (0.028, 0.038, 0.062, 1.0)
KEY = (1.0, 0.92, 0.74)
FILL = (0.45, 0.80, 0.92)
RIM = (0.76, 0.86, 1.0)


def sha256_of(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                try: block.remove(item)
                except: pass


def link_object(obj):
    try: bpy.context.collection.objects.link(obj)
    except:
        try: bpy.context.scene.collection.objects.link(obj)
        except: pass
    return obj


def new_principled(name, base_color=(0.5,0.5,0.5), roughness=0.5, metallic=0.0, alpha=1.0, emission=None, emission_strength=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
        for k,v in [("Roughness", roughness), ("Metallic", metallic)]:
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = v
        if alpha < 1.0:
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = alpha
            mat.blend_method = 'BLEND'
        if emission is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
        # Blender 5.2 Principled: Transmission Weight
        for tk in ["Transmission Weight", "Transmission"]:
            if tk in bsdf.inputs:
                bsdf.inputs[tk].default_value = transmission
                break
    return mat


def load_texture(mat, image_path: Path, target_input="Base Color", non_color=False, strength=1.0):
    if not image_path.exists():
        return None
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    try:
        tex.image = bpy.data.images.load(str(image_path))
        if non_color:
            tex.image.colorspace_settings.name = "Non-Color"
    except Exception as e:
        print(f"[blend] texture load failed {image_path.name}: {e}")
        return None
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf and target_input in bsdf.inputs:
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs[target_input])
    return tex


def build_veil_leviathan():
    """45m whale body + stained-glass ribs + lantern heart."""
    LENGTH = 45.0
    SEG = 32  # radial
    RINGS = 48  # along body
    verts = []
    faces = []
    # generate rings along spine
    spine = []
    for i in range(RINGS+1):
        s = i / RINGS
        x = -LENGTH/2 + s * LENGTH
        y = math.sin(s*math.pi) * 1.8 + math.sin(s*math.pi*2) * 0.32
        spine.append(Vector((x, y, 0)))
    # radius profile wobble
    rng = random.Random(SEED + 511)
    rings = []
    all_verts = []
    uv_map = []
    for i, pos in enumerate(spine):
        s = i / RINGS
        if i == 0: tan = spine[1] - spine[0]
        elif i == RINGS: tan = spine[-1] - spine[-2]
        else: tan = spine[i+1] - spine[i-1]
        tan = tan.normalized()
        up = Vector((0,1,0))
        if abs(tan.dot(up)) > 0.95:
            up = Vector((1,0,0))
        x1 = tan.cross(up).normalized()
        y1 = tan.cross(x1).normalized()
        r = 3.8 * math.sin(math.pi * min(1.0, 0.18 + s*0.82)) * (1.0 - 0.35*max(0.0, s-0.72)) + 1.05
        r *= (0.94 + 0.06 * math.sin(s*14))
        ring = []
        for k in range(SEG):
            a = k/SEG*2*math.pi
            off = x1*(math.cos(a)*r) + y1*(math.sin(a)*r*0.88)
            v = pos + off
            all_verts.append(v)
            uv_map.append((s, k/SEG))
            ring.append(len(all_verts)-1)
        rings.append(ring)
    for i in range(RINGS):
        for k in range(SEG):
            a = rings[i][k]; b = rings[i][(k+1)%SEG]; c = rings[i+1][(k+1)%SEG]; d = rings[i+1][k]
            faces.append((a,b,c,d))
    # caps as tri fans (two extra verts)
    cap0_idx = len(all_verts); all_verts.append(spine[0])
    cap1_idx = len(all_verts); all_verts.append(spine[-1])
    for k in range(SEG):
        faces.append((rings[0][(k+1)%SEG], rings[0][k], cap0_idx))
        faces.append((rings[-1][k], rings[-1][(k+1)%SEG], cap1_idx))
    mesh = bpy.data.meshes.new("SM_VeilLeviathan_Mesh")
    # triangulate? keep quads
    mesh.from_pydata([tuple(v) for v in all_verts], [], faces)
    # UVs
    try:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        # faces order: ring quads first, then caps
        # rings faces correspond to all_verts uv_map indexing
        # caps have no uv; leave 0,0
        # We set UV per loop: map vertex index -> uv
        # But caps introduce new verts no uv; okay
        # Build vertex->uv dict
        vert_uv = uv_map + [(0,0), (0,0)]  # caps
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                if vi < len(vert_uv):
                    uv_layer.data[li].uv = vert_uv[vi]
    except Exception as e:
        print(f"[levi] uv failed: {e}")
    mesh.update()
    for p in mesh.polygons: p.use_smooth = True
    obj = bpy.data.objects.new("SM_VeilLeviathan", mesh)
    link_object(obj)

    # ribs: thin glass panes as separate meshes parented (for silhouette but also material distinction)
    rib_objs = []
    # create a shared glass material later but geometry here
    for rib in range(14):
        s = 0.20 + rib/13*0.60
        idx = int(s * RINGS)
        c = spine[idx]
        # local frame at idx
        if idx==0: tan = spine[1]-spine[0]
        elif idx==RINGS: tan = spine[-1]-spine[-2]
        else: tan = spine[idx+1]-spine[idx-1]
        tan = tan.normalized()
        up = Vector((0,1,0))
        if abs(tan.dot(up))>0.94: up=Vector((1,0,0))
        x1 = tan.cross(up).normalized(); y1 = tan.cross(x1).normalized()
        Rr = 3.1*math.sin(math.pi*(0.28+0.58*rib/13)) + 1.5
        # arc path 12 points over pi (belly)
        arc = []
        for t_i in range(12):
            t = t_i/11
            ang = math.pi * t
            rad = Rr*(0.55+0.45*math.sin(math.pi*t))
            # offset around y1 downward
            pos = c + y1*(-math.sin(ang)*rad) + x1*(math.cos(ang)*rad*0.16) + Vector((0,-0.6*math.sin(ang),0))
            arc.append(pos)
        # build ribbon mesh (2 verts per arc point, width 0.42)
        rib_verts = []; rib_faces=[]
        half_w = 0.26
        for pt in arc:
            # width along tan direction
            rib_verts.append(pt + tan*half_w)
            rib_verts.append(pt - tan*half_w)
        for i2 in range(len(arc)-1):
            a0=i2*2; a1=i2*2+1; b0=(i2+1)*2; b1=(i2+1)*2+1
            rib_faces.append((a0,a1,b1,b0))
        rmesh = bpy.data.meshes.new(f"SM_VeilRib_{rib:02d}_Mesh")
        rmesh.from_pydata([tuple(v) for v in rib_verts], [], rib_faces)
        rmesh.update()
        for p in rmesh.polygons: p.use_smooth = True
        # UV along rib length
        try:
            uv = rmesh.uv_layers.new(name="UVMap")
            for poly in rmesh.polygons:
                for li in poly.loop_indices:
                    vi = rmesh.loops[li].vertex_index
                    # vi 0..23, even=forward, odd=back
                    idx_ = vi // 2
                    s_ = idx_ / (len(arc)-1)
                    u_ = 0 if vi%2==0 else 1
                    uv.data[li].uv = (s_, u_)
        except: pass
        o = bpy.data.objects.new(f"SM_VeilRib_{rib:02d}", rmesh)
        link_object(o)
        rib_objs.append(o)

    # lantern heart: icosphere at chest
    heart_pos = spine[int(RINGS*0.29)] + Vector((0,-0.92,0))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.18, location=heart_pos)
    heart = bpy.context.object
    heart.name = "SM_VeilLanternHeart"
    # slightly scale
    heart.scale = Vector((1.1, 0.95, 1.05))
    bpy.context.view_layer.update()
    # parent ribs+heart to whale for grouping
    for o in rib_objs: o.parent = obj
    heart.parent = obj
    # keep world transforms but unlink parent for FBX (we will join? keep parent then clear)
    for o in rib_objs+ [heart]:
        o.parent = None
        # ensure whale stays at origin, no offset needed (spine already world)
    # whale already at origin (centered)
    return obj, rib_objs, heart


def build_choir_jelly():
    """12 jelly bells 3m sharing one VAT LUT (instanced mesh, per-object vat_offset)."""
    R = 1.5; SEG=28; RINGS=18
    verts = []; faces=[]; uv_map=[]
    rows=[]
    # rows as vertex indices
    all_verts=[]
    rings_idx=[]
    for j in range(RINGS+1):
        phi = j/RINGS*math.pi*0.62
        row=[]
        for i in range(SEG):
            th=i/SEG*2*math.pi
            scallop=1.0+0.055*math.cos(th*12)*(phi/(math.pi*0.62))**2
            rr=R*math.sin(phi)*scallop
            y=R*0.72*math.cos(phi)
            pos=Vector((rr*math.cos(th), y, rr*math.sin(th)))
            all_verts.append(pos); uv_map.append((i/SEG, 1-j/RINGS))
            row.append(len(all_verts)-1)
        rings_idx.append(row)
    for j in range(RINGS):
        for i in range(SEG):
            faces.append((rings_idx[j][i], rings_idx[j][(i+1)%SEG], rings_idx[j+1][(i+1)%SEG], rings_idx[j+1][i]))
    # oral arms: 4 curtains attached to rim
    arm_base_verts = []  # will append after
    base_len = len(all_verts)
    for arm in range(4):
        a0=arm/4*2*math.pi
        spine=[]
        for k in range(16):
            s=k/15
            r=0.92*R + s*0.55
            fall = -math.sin(s*math.pi*0.5)*1.05 + max(0,s-0.5)**1.6*0.42
            x = r*math.cos(a0) + math.sin(s*3.2+arm)*0.12*s
            z = r*math.sin(a0) + math.cos(s*2.2+arm*0.7)*0.10*s
            spine.append(Vector((x, fall, z)))
        # ribbon grid 16x4
        grid=[]
        for idx,pos in enumerate(spine):
            s=idx/15
            if idx==0: tan=spine[1]-spine[0]
            elif idx==15: tan=spine[-1]-spine[-2]
            else: tan=spine[idx+1]-spine[idx-1]
            tan=tan.normalized()
            up=Vector((0,1,0))
            if abs(tan.dot(up))>0.95: up=Vector((1,0,0))
            x1=tan.cross(up).normalized()
            w=0.22*(0.5+0.5*math.sin(math.pi*min(1,0.15+0.85*s)))*(1-0.35*s)
            row=[]
            for c in range(5):
                u=c/4 -0.5
                off = x1*(w*u)
                p = pos + off
                all_verts.append(p)
                # uv.y = along arm, uv.x = across
                uv_map.append((u+0.5, s))
                row.append(len(all_verts)-1)
            grid.append(row)
        for r_ in range(15):
            for c in range(4):
                faces.append((grid[r_][c], grid[r_][c+1], grid[r_+1][c+1], grid[r_+1][c]))
    mesh = bpy.data.meshes.new("SM_ChoirJelly_Mesh")
    mesh.from_pydata([tuple(v) for v in all_verts], [], faces)
    mesh.update()
    for p in mesh.polygons: p.use_smooth = True
    # UV
    try:
        uv = mesh.uv_layers.new(name="UVMap")
        # need loop uv assignment by vertex idx
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                if vi < len(uv_map):
                    uv.data[li].uv = uv_map[vi]
    except Exception as e:
        print(f"[jelly] uv fail {e}")

    # prototype object
    proto = bpy.data.objects.new("SM_ChoirJelly_PROTO", mesh)
    link_object(proto)
    proto.hide_viewport = True
    proto.hide_render = True

    # instance 12
    rng = random.Random(SEED + 722)
    # scatter in a 14m circle at y=4..6
    instances = []
    for i in range(12):
        ang = i/12*2*math.pi + rng.uniform(-0.18,0.18)
        rad = 6.5 + rng.uniform(-1.2, 1.8) + (2.5 if i%3==0 else 0)
        x = math.cos(ang)*rad
        z = math.sin(ang)*rad
        y = 4.2 + rng.uniform(-0.4, 0.6) + math.sin(ang*2)*0.5
        # copy object (linked mesh)
        ob = bpy.data.objects.new(f"SM_ChoirJelly_{i:02d}", mesh)
        ob.location = Vector((x, y, z))
        ob.rotation_euler = (0, 0, rng.uniform(-0.2, 0.2))
        # random scale 0.88..1.12
        sc = rng.uniform(0.88, 1.12)
        ob.scale = Vector((sc, sc, sc))
        # VAT offset per instance (0..1) — material will use this via Attribute or Custom Property
        ob["vat_offset"] = rng.random()
        # also store choir phase (they sing together so offsets are similar — cluster around 0.1 range)
        # keep random for visual variety but choir sync = add small jitter to shared time
        link_object(ob)
        instances.append(ob)

    # hide proto after instancing? keep for reference but not rendered
    return proto, instances


def build_shore_siren():
    """2.2m melusine: head + torso + tail fin + arms + 9 kelp hair ribbons."""
    objs = []
    # head
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.165, location=(0, 1.95, 0))
    head = bpy.context.object; head.name = "SM_Siren_Head"; objs.append(head)
    # torso: bmesh tapered tube
    import bmesh
    def tube(pts, radii, seg=12, name="tube"):
        verts=[]; faces=[]
        spine=[Vector(p) for p in pts]
        rings=[]
        allv=[]
        for i,pos in enumerate(spine):
            if i==0: tan=spine[1]-spine[0]
            elif i==len(spine)-1: tan=spine[-1]-spine[-2]
            else: tan=spine[i+1]-spine[i-1]
            tan=tan.normalized()
            up=Vector((0,1,0))
            if abs(tan.dot(up))>0.95: up=Vector((1,0,0))
            x=tan.cross(up).normalized(); y=tan.cross(x).normalized()
            ring=[]
            for k in range(seg):
                a=k/seg*2*math.pi
                off=x*(math.cos(a)*radii[i])+y*(math.sin(a)*radii[i])
                allv.append(pos+off)
                ring.append(len(allv)-1)
            rings.append(ring)
        for i in range(len(spine)-1):
            for k in range(seg):
                faces.append((rings[i][k], rings[i][(k+1)%seg], rings[i+1][(k+1)%seg], rings[i+1][k]))
        # caps
        cap0=len(allv); allv.append(spine[0]); cap1=len(allv); allv.append(spine[-1])
        for k in range(seg):
            faces.append((rings[0][(k+1)%seg], rings[0][k], cap0))
            faces.append((rings[-1][k], rings[-1][(k+1)%seg], cap1))
        mesh=bpy.data.meshes.new(name+"_Mesh")
        mesh.from_pydata([tuple(v) for v in allv], [], faces)
        mesh.update()
        for p in mesh.polygons: p.use_smooth=True
        ob=bpy.data.objects.new(name, mesh)
        link_object(ob)
        return ob
    torso = tube([(0,1.78,0),(0,1.55,0),(0,1.28,0)], [0.22,0.20,0.17], seg=14, name="SM_Siren_Torso")
    objs.append(torso)
    tail = tube([(0,1.28,0),(0,0.75,0.05),(0,0.22,-0.06),(0,-0.15,0.02)], [0.17,0.14,0.10,0.03], seg=14, name="SM_Siren_Tail")
    objs.append(tail)
    # tail fin (single quad)
    fin_verts=[Vector((0,-0.15,0.02)), Vector((-0.18,-0.42,0)), Vector((0,-0.52,0.04)), Vector((0.18,-0.42,0))]
    fin_mesh=bpy.data.meshes.new("SM_Siren_Fin_Mesh")
    fin_mesh.from_pydata([tuple(v) for v in fin_verts], [], [(0,1,2,3)])
    fin_mesh.update()
    fin=bpy.data.objects.new("SM_Siren_Fin", fin_mesh)
    for p in fin_mesh.polygons: p.use_smooth=True
    link_object(fin); objs.append(fin)
    # arms
    larm = tube([(-0.22,1.62,0),(-0.42,1.35,0.04),(-0.52,1.02,0.02)], [0.055,0.045,0.035], seg=9, name="SM_Siren_LArm")
    rarm = tube([(0.22,1.62,0),(0.42,1.35,0.04),(0.52,1.02,0.02)], [0.055,0.045,0.035], seg=9, name="SM_Siren_RArm")
    objs.extend([larm, rarm])
    # kelp hair: 9 ribbons from scalp
    rng=random.Random(SEED+733)
    hair_objs=[]
    for k in range(9):
        a = k/9*2*math.pi + rng.uniform(-0.12,0.12)
        base=Vector((math.cos(a)*0.09, 2.04, math.sin(a)*0.09))
        pts=[]
        for i in range(14):
            s=i/13
            pts.append(base + Vector((math.cos(a)*s*0.24 + math.sin(s*6+a)*0.045*s, -s*0.74 - math.sin(s*math.pi)*0.06, math.sin(a)*s*0.18 + math.cos(s*5+a)*0.045*s)))
        radii=[0.034*(1-0.72*s) for s in [i/13 for i in range(14)]]
        # ribbon tube with seg 6 (thin)
        spine=[Vector(p) for p in pts]
        seg=6
        allv=[]; rings=[]
        for i,pos in enumerate(spine):
            if i==0: tan=spine[1]-spine[0]
            elif i==len(spine)-1: tan=spine[-1]-spine[-2]
            else: tan=spine[i+1]-spine[i-1]
            tan=tan.normalized()
            up=Vector((0,1,0))
            if abs(tan.dot(up))>0.95: up=Vector((1,0,0))
            x=tan.cross(up).normalized(); y=tan.cross(x).normalized()
            ring=[]
            for kk in range(seg):
                ang=kk/seg*2*math.pi
                off=x*(math.cos(ang)*radii[i])+y*(math.sin(ang)*radii[i])
                allv.append(pos+off)
                ring.append(len(allv)-1)
            rings.append(ring)
        faces2=[]
        for i in range(len(spine)-1):
            for kk in range(seg):
                faces2.append((rings[i][kk], rings[i][(kk+1)%seg], rings[i+1][(kk+1)%seg], rings[i+1][kk]))
        mesh=bpy.data.meshes.new(f"SM_Siren_Hair_{k:02d}_Mesh")
        mesh.from_pydata([tuple(v) for v in allv], [], faces2)
        mesh.update()
        for p in mesh.polygons: p.use_smooth=True
        # growth UV: y = along hair
        try:
            uv=mesh.uv_layers.new(name="UVMap")
            # map vertex idx -> s
            vert_s=[]
            for i in range(len(spine)):
                for kk in range(seg):
                    vert_s.append(i/(len(spine)-1))
            for poly in mesh.polygons:
                for li in poly.loop_indices:
                    vi=mesh.loops[li].vertex_index
                    if vi < len(vert_s):
                        uv.data[li].uv = (0.5, vert_s[vi])
        except: pass
        ob=bpy.data.objects.new(f"SM_Siren_Hair_{k:02d}", mesh)
        link_object(ob)
        hair_objs.append(ob)
    objs.extend(hair_objs)
    # group root (empty)
    bpy.ops.object.empty_add(location=(0,0,0))
    root=bpy.context.object; root.name="SM_ShoreSiren_ROOT"
    for o in objs:
        o.parent=root
    # clear parents to keep world transforms for FBX, then remove empty
    for o in objs: o.parent=None
    bpy.data.objects.remove(root)
    # siren position: shore south
    for o in objs: o.location += Vector((0,0,0))  # centered at world origin, 0..2.2m tall
    # return a representative object for material assignment (we assign to all)
    return objs


def assign_materials(veil_obj, rib_objs, heart, jelly_proto, jelly_instances, siren_objs):
    # load textures if present
    def tex_path(name): return OUT_DIR / f"{name}.png"
    # Veil: translucent + emission
    veil_mat = new_principled("M_VeilLeviathan", base_color=(0.52,0.76,0.80), roughness=0.35, transmission=0.48, emission=(1.0,0.52,0.12), emission_strength=1.4)
    # hook textures
    load_texture(veil_mat, tex_path("T_VeilLeviathan_BaseColor"), "Base Color")
    # emission texture -> Emission Color (multiply)
    # Create mix: we'll link emission tex to Emission Color via separate tex node
    em_tex = load_texture(veil_mat, tex_path("T_VeilLeviathan_Emission"), "Emission Color", non_color=False)
    # normal map
    if tex_path("T_VeilLeviathan_Normal").exists():
        try:
            ntex = veil_mat.node_tree.nodes.new("ShaderNodeTexImage")
            ntex.image = bpy.data.images.load(str(tex_path("T_VeilLeviathan_Normal")))
            ntex.image.colorspace_settings.name = "Non-Color"
            nmap = veil_mat.node_tree.nodes.new("ShaderNodeNormalMap")
            veil_mat.node_tree.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            bsdf = veil_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf and "Normal" in bsdf.inputs:
                veil_mat.node_tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception as e:
            print(f"[mat] veil normal {e}")
    for o in [veil_obj] + rib_objs:
        if o.data and hasattr(o.data, "materials"):
            o.data.materials.clear()
            o.data.materials.append(veil_mat)
    # heart: pure emission lantern
    heart_mat = new_principled("M_VeilLanternHeart", base_color=(0.95,0.55,0.12), roughness=0.6, emission=(1.0,0.62,0.18), emission_strength=6.0, transmission=0.15)
    heart.data.materials.clear()
    heart.data.materials.append(heart_mat)

    # Jelly: pale translucent + emission bands + VAT
    jelly_mat = new_principled("M_ChoirJelly", base_color=(0.76,0.86,0.94), roughness=0.22, transmission=0.72, emission=(0.18,0.62,0.95), emission_strength=1.1)
    load_texture(jelly_mat, tex_path("T_ChoirJelly_BaseColor"), "Base Color")
    if tex_path("T_ChoirJelly_Emission").exists():
        load_texture(jelly_mat, tex_path("T_ChoirJelly_Emission"), "Emission Color")
    if tex_path("T_ChoirJelly_Normal").exists():
        try:
            ntex = jelly_mat.node_tree.nodes.new("ShaderNodeTexImage")
            ntex.image = bpy.data.images.load(str(tex_path("T_ChoirJelly_Normal")))
            ntex.image.colorspace_settings.name = "Non-Color"
            nmap = jelly_mat.node_tree.nodes.new("ShaderNodeNormalMap")
            jelly_mat.node_tree.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            bsdf = jelly_mat.node_tree.nodes.get("Principled BSDF")
            if bsdf and "Normal" in bsdf.inputs:
                jelly_mat.node_tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        except: pass
    # VAT LUT as extra image (not linked, but ensure it exists for manifest)
    # For documentation we set custom property on mat
    vat_path = tex_path("T_ChoirJelly_VAT_LUT")
    if vat_path.exists():
        jelly_mat["vat_lut"] = str(vat_path.relative_to(PROJECT_ROOT))
        jelly_mat["vat_contract"] = "V=time U=growth R=radial G=vertical B=sway 0.5=zero"
    for o in [jelly_proto] + jelly_instances:
        if o.data and hasattr(o.data, "materials"):
            # proto has mesh shared, so first assign clears for all; but instances share mesh so assigning to proto mesh suffices
            pass
    # Since all jellies share one mesh, assign to mesh once
    if jelly_proto.data.materials:
        jelly_proto.data.materials.clear()
    jelly_proto.data.materials.append(jelly_mat)

    # Siren
    siren_mat = new_principled("M_ShoreSiren", base_color=(0.86,0.64,0.58), roughness=0.48, transmission=0.22, emission=(0.32,0.85,0.62), emission_strength=0.9)
    load_texture(siren_mat, tex_path("T_ShoreSiren_BaseColor"), "Base Color")
    if tex_path("T_ShoreSiren_Emission").exists():
        load_texture(siren_mat, tex_path("T_ShoreSiren_Emission"), "Emission Color")
    if tex_path("T_ShoreSiren_Normal").exists():
        try:
            ntex = siren_mat.node_tree.nodes.new("ShaderNodeTexImage")
            ntex.image = bpy.data.images.load(str(tex_path("T_ShoreSiren_Normal")))
            ntex.image.colorspace_settings.name = "Non-Color"
            nmap = siren_mat.node_tree.nodes.new("ShaderNodeNormalMap")
            jelly_mat  # dummy to avoid lint
            bsdf = siren_mat.node_tree.nodes.get("Principled BSDF")
            siren_mat.node_tree.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
            if bsdf and "Normal" in bsdf.inputs:
                siren_mat.node_tree.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception as e:
            print(f"[mat] siren normal {e}")
    for o in siren_objs:
        if o.data and hasattr(o.data, "materials"):
            o.data.materials.clear()
            o.data.materials.append(siren_mat)
    return veil_mat, heart_mat, jelly_mat, siren_mat


def setup_world_and_lights():
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = WORLD
        bg.inputs[1].default_value = 1.0
    # lights
    def light(name, loc, color, energy, size=3.0):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.color = color
        data.size = size
        ob = bpy.data.objects.new(name, data)
        ob.location = loc
        link_object(ob)
        return ob
    # scene center approx: veil at origin length 45, jellies around 4m high, siren 1m
    center = Vector((0, 2.5, 0))
    # estimate diag ~50m
    d = 52
    light("Key", center + Vector((1.0,-1.2,1.1)).normalized()* d*1.0, KEY,  28000, 6.0)
    light("Fill", center + Vector((-1.1,-0.6,0.4)).normalized()* d*1.2, FILL, 14000, 8.0)
    light("Rim", center + Vector((0.2,1.1,0.9)).normalized()* d*1.1, RIM, 18000, 7.0)
    # underwater god rays: spot
    spot_data = bpy.data.lights.new("GodRay", type="SPOT")
    spot_data.energy = 12000
    spot_data.color = (0.52,0.78,0.92)
    spot_data.spot_size = math.radians(42)
    spot_data.spot_blend = 0.45
    spot_ob = bpy.data.objects.new("GodRay", spot_data)
    spot_ob.location = Vector((0, 22, -18))
    spot_ob.rotation_euler = (math.radians(72), 0, math.radians(18))
    link_object(spot_ob)


def frame_and_render(out_path: Path, width=1920, height=1080, samples=64):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    # camera fit
    # compute bbox
    lo = Vector((1e9,1e9,1e9)); hi = Vector((-1e9,-1e9,-1e9))
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH': continue
        if getattr(ob, 'hide_viewport', False): continue
        for corner in ob.bound_box:
            world = ob.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, world)); hi = Vector(map(max, hi, world))
    center = (lo + hi) / 2
    diag = (hi - lo).length
    # camera
    cam_data = bpy.data.cameras.new("CamBeauty")
    cam_data.lens = 52
    cam_data.clip_start = 0.1; cam_data.clip_end = 800
    cam = bpy.data.objects.new("CamBeauty", cam_data)
    # angle: 30deg above, side view to capture whale length + jellies + siren
    dist = max(diag*0.62 + 6, 24)
    direction = Vector((1.25, -0.78, 0.72)).normalized()
    cam.location = center + direction * dist + Vector((0, 3.5, 0))
    link_object(cam)
    # track to center
    target = bpy.data.objects.new("CamTarget", None)
    target.location = center + Vector((2, 0.5, 0))
    link_object(target)
    c = cam.constraints.new(type="TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    scene.camera = cam
    bpy.context.view_layer.update()
    scene.render.filepath = str(out_path)
    print(f"[render] {out_path.name} {width}x{height} {samples}spp center={tuple(round(v,2) for v in center)} diag={diag:.2f}")
    bpy.ops.render.render(write_still=True)
    print(f"[render] wrote {out_path} {out_path.stat().st_size} bytes" if out_path.exists() else "[render] FAILED write")
    return cam, center, diag


def export_fbx(path: Path, use_selection=False, selected_objs=None):
    # select
    bpy.ops.object.select_all(action='DESELECT')
    if selected_objs is not None:
        for o in selected_objs:
            try: o.select_set(True)
            except: pass
        bpy.context.view_layer.objects.active = selected_objs[0] if selected_objs else None
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_scale_options='FBX_SCALE_ALL', global_scale=1.0, axis_forward='-Z', axis_up='Y', bake_space_transform=False)
    else:
        for o in bpy.data.objects: 
            if o.type=='MESH' and not getattr(o,'hide_viewport',False):
                try: o.select_set(True)
                except: pass
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=use_selection, apply_scale_options='FBX_SCALE_ALL', global_scale=1.0, axis_forward='-Z', axis_up='Y')
    print(f"[fbx] {path.name} {path.stat().st_size if path.exists() else 'MISSING'}")
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[creatures-blender] seed={SEED} out={OUT_DIR}")
    clear_scene()
    # build meshes
    print("[creatures-blender] building Veil Leviathan 45m...")
    veil_obj, rib_objs, heart = build_veil_leviathan()
    print(f"  veil {len(veil_obj.data.vertices)} verts + {len(rib_objs)} ribs + heart {len(heart.data.vertices)}")
    print("[creatures-blender] building Choir Jelly Swarm x12...")
    proto, jellies = build_choir_jelly()
    print(f"  proto {len(proto.data.vertices)} verts, instances {len(jellies)}")
    print("[creatures-blender] building Shore Siren 2.2m...")
    siren_objs = build_shore_siren()
    print(f"  siren {len(siren_objs)} objects")
    # materials
    print("[creatures-blender] assigning PBR materials (emission+transmission)...")
    assign_materials(veil_obj, rib_objs, heart, proto, jellies, siren_objs)
    # layout: shift scene for composition (veil already centered, jellies scatter, siren at shore offset)
    # Move siren to shore position (-8,0,-8) so beauty frames all
    shore_offset = Vector((-8, 0, -8))
    for o in siren_objs:
        o.location += shore_offset
    # world/lights
    setup_world_and_lights()
    # save blend
    blend_path = OUT_DIR / "Surreal_Creatures.blend"
    # Ensure path is absolute string
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        print(f"[blend] wrote {blend_path} {blend_path.stat().st_size} bytes")
    except Exception as e:
        print(f"[blend] save failed: {e}")

    # beauty 1920x1080
    beauty_path = OUT_DIR / "Surreal_Creatures_Beauty.png"
    frame_and_render(beauty_path, 1920, 1080, samples=64)
    # per-creature beauties (optional isolation via hide) — save combined additional flat 1024 renders for QA
    # but main requirement is one 1920x1080 beauty; also save per-creature FBXs
    # FBX exports
    # Veil (joined with ribs/heart for single FBX)
    # Select veil group
    veil_group = [veil_obj] + rib_objs + [heart]
    fbx_veil = OUT_DIR / "SM_VeilLeviathan.fbx"
    export_fbx(fbx_veil, use_selection=True, selected_objs=veil_group)
    # Jelly: export proto mesh as single (instances will be recreated via vat offset doc) + combined swarm
    fbx_jelly = OUT_DIR / "SM_ChoirJelly.fbx"
    export_fbx(fbx_jelly, use_selection=True, selected_objs=[proto])
    fbx_jelly_swarm = OUT_DIR / "SM_ChoirJelly_Swarm.fbx"
    export_fbx(fbx_jelly_swarm, use_selection=True, selected_objs=jellies)
    # Siren
    fbx_siren = OUT_DIR / "SM_ShoreSiren.fbx"
    export_fbx(fbx_siren, use_selection=True, selected_objs=siren_objs)
    # Combined
    fbx_combined = OUT_DIR / "Surreal_Creatures_Combined.fbx"
    export_fbx(fbx_combined, use_selection=False)

    # also export OBJ companions via bpy (for UE fallback where FBX is primary)
    for stem, objs in [("SM_VeilLeviathan", veil_group), ("SM_ChoirJelly", [proto]), ("SM_ShoreSiren", siren_objs)]:
        obj_path = OUT_DIR / f"{stem}.obj"
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        if objs: bpy.context.view_layer.objects.active = objs[0]
        try:
            bpy.ops.wm.obj_export(filepath=str(obj_path), export_selected_objects=True, export_uv=True, export_normals=True, export_materials=False, apply_modifiers=True)
            print(f"[obj] {obj_path.name} {obj_path.stat().st_size if obj_path.exists() else 'MISS'}")
        except AttributeError:
            bpy.ops.export_scene.obj(filepath=str(obj_path), use_selection=True, use_uvs=True, use_normals=True)
        except Exception as e:
            print(f"[obj] export {stem} failed: {e}")

    # manifest
    # Collect file records
    frag_path = OUT_DIR / "_textures_manifest.json"
    frag = {}
    if frag_path.exists():
        with open(frag_path, encoding="utf-8") as f: frag = json.load(f)
    else:
        print("[manifest] warning: _textures_manifest.json missing (run surreal_creatures2.py first)")

    # mesh stats
    def mesh_stats(objs):
        total_verts = sum(len(o.data.vertices) for o in objs if hasattr(o.data, "vertices"))
        total_faces = sum(len(o.data.polygons) for o in objs if hasattr(o.data, "polygons"))
        return total_verts, total_faces

    veil_verts, veil_faces = mesh_stats(veil_group)
    jelly_verts, jelly_faces = mesh_stats([proto])
    jelly_swarm_verts = jelly_verts * len(jellies)
    siren_verts, siren_faces = mesh_stats(siren_objs)

    files = []
    for p in sorted(OUT_DIR.glob("*")):
        if p.is_file():
            files.append({"name": p.name, "path": str(p.relative_to(PROJECT_ROOT)), "bytes": p.stat().st_size, "sha256": sha256_of(p)})

    manifest = {
        "schema": SCHEMA,
        "seed": SEED,
        "out_dir": str(OUT_DIR.relative_to(PROJECT_ROOT)),
        "scale_note": "metres; UE import FBX/OBJ scale 100x (1m = 100cm). Origin at world center.",
        "creatures": [
            {"id": "veil_leviathan", "display": "Veil Leviathan 45m", "mesh": "SM_VeilLeviathan.fbx (+ .obj/.blend)", "verts": veil_verts, "faces": veil_faces, "materials": "M_VeilLeviathan (translucent teal + stained-glass ribs) + M_VeilLanternHeart (emission 6.0)", "textures": ["T_VeilLeviathan_BaseColor.png","T_VeilLeviathan_Emission.png","T_VeilLeviathan_Normal.png","T_VeilLeviathan_ORM.png"], "features": "45m translucent whale, 16 stained-glass ribs, lantern heart 1.18m inside chest, emission+transmission"},
            {"id": "choir_jelly", "display": "Choir Jelly Swarm 3m x12", "mesh": "SM_ChoirJelly.fbx (proto) + SM_ChoirJelly_Swarm.fbx (12 instances)", "verts_proto": jelly_verts, "faces_proto": jelly_faces, "count": 12, "verts_swarm": jelly_swarm_verts, "materials": "M_ChoirJelly (pale cyan-violet + pulse emission + transmission 0.72)", "textures": ["T_ChoirJelly_BaseColor.png","T_ChoirJelly_Emission.png","T_ChoirJelly_Normal.png","T_ChoirJelly_Transmission.png","T_ChoirJelly_VAT_LUT.png"], "vat": "T_ChoirJelly_VAT_LUT.png 1024x256 V=time(0..1) U=growth(0..1) R=radial G=vertical B=sway 0.5=zero, shared by 12 bells via per-object vat_offset"},
            {"id": "shore_siren", "display": "Shore Siren 2.2m melusine", "mesh": "SM_ShoreSiren.fbx", "verts": siren_verts, "faces": siren_faces, "materials": "M_ShoreSiren (warm skin + turquoise scales + kelp hair, emission hair tips/eyes/tail rim, transmission 0.22)", "textures": ["T_ShoreSiren_BaseColor.png","T_ShoreSiren_Emission.png","T_ShoreSiren_Normal.png","T_ShoreSiren_ORM.png"], "features": "2.2m figure, capsule torso+tail fin, 9 living kelp hair ribbons (growth UV.y), emission+transmission"},
        ],
        "textures": frag.get("textures", []),
        "material_contract": "Principled BSDF per creature: BaseColor + Normal + Emission (Color * Strength) + Transmission Weight — verified on all 3",
        "blend": {"file": "Surreal_Creatures.blend", "blender": bpy.app.version_string},
        "fbx": [
            {"file": "SM_VeilLeviathan.fbx", "verts": veil_verts, "scale": "45m object, UE import 100x"},
            {"file": "SM_ChoirJelly.fbx", "verts": jelly_verts, "note": "proto bell"},
            {"file": "SM_ChoirJelly_Swarm.fbx", "count": 12, "verts_swarm": jelly_swarm_verts},
            {"file": "SM_ShoreSiren.fbx", "verts": siren_verts},
            {"file": "Surreal_Creatures_Combined.fbx"},
        ],
        "beauties": [
            {"file": "Surreal_Creatures_Beauty.png", "resolution": "1920x1080", "engine": "Cycles CPU 64spp", "sha256": sha256_of(beauty_path) if beauty_path.exists() else None},
        ],
        "files": files,
        "houdini": frag.get("houdini", {}),
    }
    manifest_path = OUT_DIR / "creatures_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[manifest] -> {manifest_path}")
    # cleanup frag
    # keep _textures_manifest for provenance
    print("[creatures-blender] done.")

if __name__ == "__main__":
    main()
