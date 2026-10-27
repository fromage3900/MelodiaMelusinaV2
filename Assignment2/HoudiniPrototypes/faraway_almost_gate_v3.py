"""spike: true. Build The Almost Gate v03, the final ornate Faraway Mother landmark.

Extends the v02 rock/silk monument (HDA_Faraway_AlmostGate_v02, which stays
untouched) into the procedural monolithic structure: scrollwork volutes, heart
frames and tokens, scallop shell fans, vine tendrils, floating star shards,
levitating rock shards with WPO motion metadata, and Chladni-field-driven
inlaid crystal clusters. This Hython-only lane writes a fresh Saved/Staging
candidate; it does not access Unreal Engine.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
HFS_HYTHON = Path("C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe")
GEOMETRY_SOURCE = HERE / "faraway_almost_gate_geometry.py"
ORNAMENT_SOURCE = HERE / "faraway_almost_gate_ornaments.py"
SILK_SOURCE = ROOT / "Tools/Houdini/faraway/silk_ribbon_geometry.py"
FIELD_SOURCE = ROOT / "Tools/Houdini/faraway/chladni_field.py"
SEAM_SOURCE = ROOT / "Tools/Houdini/faraway/seam_stage.py"
HEART_SOURCE = HERE / "faraway_heart_gate_v2.py"
V2_BUILDER = HERE / "faraway_almost_gate.py"
SCHEMA = ROOT / "specs/universe/faraway_mother.world_genome.v1.json"
PLACEMENTS = ROOT / "Saved/Staging/HoudiniForge/FarawayUEIntake_20261026/02_biomes/placements.json"
LANDMARKS = ROOT / "Saved/Staging/HoudiniForge/FarawayUEIntake_20261026/04_wonder/landmarks.json"
SEAM_MANIFEST = ROOT / "Saved/Staging/HoudiniForge/FarawayUEIntake_20261026/03_seam_dressing/manifest.json"
REFERENCE = Path("C:/Users/froma/.codex/codex-remote-attachments/01a179c9-98d7-7930-910c-59adf46454ad/79176D67-1EB5-4361-BEFA-0A9CF106FF2D/1-Photo-1.jpg")
TYPE = "HDA_Faraway_AlmostGate_v03"
ORIGIN_UE_CM = [-72000.0, -2000.0, 520.0]


def chladni_plate_f(x, z):
    """Canonical Chladni field F(u,v) on the +/-4000 m plate (canon: never
    rephase). Mirrors the inline copy embedded in the HDA cook script."""
    u = (float(x) + 4000.0) / 8000.0
    v = (float(z) + 4000.0) / 8000.0
    return (math.cos(3.0 * math.pi * u) * math.cos(5.0 * math.pi * v)
            - math.cos(5.0 * math.pi * u) * math.cos(3.0 * math.pi * v))


MATERIALS = {
    "stone": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle",
    "rib": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil",
    "silk": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall",
    "crown_rosette": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
    "ornament": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Ornament",
    "crystal": "/Game/EnvSandbox/Monoliths/FarawayMother/UniverseFoundry/Materials/MI_FloatingCrystal_Iridescent",
}

# name, label, kind, default, min, max, group, help
PARMS = [
    ("detail_mode", "Production Detail", "toggle", 1, None, None, "Build", "Off cooks a fast silhouette preview; on cooks full rock, rib, silk, ornament and crystal resolution."),
    ("height", "Monument Height (m)", "float", 500.0, 300.0, 600.0, "Silhouette", "Overall crown height above the level approach datum."),
    ("width", "Formation Width (m)", "float", 360.0, 240.0, 440.0, "Silhouette", "Controls the two main rock masses and outer spires."),
    ("depth", "Formation Depth (m)", "float", 140.0, 80.0, 220.0, "Silhouette", "Rock strata depth along the approach axis."),
    ("asymmetry", "Asymmetry", "float", 0.45, 0.0, 1.0, "Silhouette", "Bends the crowns and offsets the west/east spires independently."),
    ("erosion", "Eroded Rock Relief", "float", 0.34, 0.0, 0.65, "Geology", "Bounded deterministic surface variation and strata breakup."),
    ("aperture_width", "Clear Opening Width (m)", "float", 130.0, 80.0, 150.0, "Approach", "Minimum open passage width through the lower monument."),
    ("aperture_height", "Clear Opening Height (m)", "float", 190.0, 120.0, 260.0, "Approach", "Open lower passage height; the landmark does not replace Heart Gate."),
    ("drape_count", "Static Silk Ribbons", "int", 5, 0, 5, "Silk", "Number of baked silk strips along the outer inner flanks."),
    ("drape_width", "Silk Ribbon Width (m)", "float", 26.0, 6.0, 36.0, "Silk", "Ribbon width; guides remain outside the clear approach."),
    ("drape_length", "Silk Ribbon Length (m)", "float", 220.0, 80.0, 400.0, "Silk", "Static guide length from shoulder toward the lower flank."),
    ("drape_ripple", "Static Silk Ripple (m)", "float", 0.8, 0.0, 3.0, "Silk", "Baked geometric ripple only; no cloth simulation is implied."),
    ("drape_segments", "Silk Segments", "int", 48, 16, 96, "Silk", "Longitudinal resolution for the static strips."),
    ("scrollwork_count", "Scrollwork Volutes", "int", 8, 0, 24, "Ornament", "Spiral filigree scrolls on the outer flanks; pairs alternate sides and layers."),
    ("heart_tokens", "Heart Tokens", "int", 5, 0, 12, "Ornament", "Small parametric-heart inlays rising up the spire skins; a large heart frame always crowns the aperture."),
    ("shell_fans", "Scallop Shell Fans", "int", 4, 0, 8, "Ornament", "Hinged rosette fans at the shoulders; blades plus scalloped rim."),
    ("tendril_count", "Vine Tendrils", "int", 6, 0, 16, "Ornament", "Hanging damped-sine stone vines under the crown ribs."),
    ("ivy_strands", "Falling Ivy Strands", "int", 10, 0, 28, "Ornament", "Ivy strands clinging to the outer spire flanks, hanging down with alternating leaves; sway metadata included."),
    ("wisteria_racemes", "Wisteria Racemes", "int", 12, 0, 32, "Ornament", "Hanging wisteria racemes under the rib arches with clustered drooping bell blossoms; sway metadata included."),
    ("star_shards", "Floating Star Shards", "int", 9, 0, 24, "Ornament", "Five-pointed star prisms levitating above the crown; carry WPO motion attributes."),
    ("float_shards", "Levitating Rock Shards", "int", 14, 0, 40, "Motion", "Irregular displaced-icosahedron rock chunks hovering around the crown; the monument's moving pieces."),
    ("float_amp_m", "Float Amplitude (m)", "float", 6.0, 0.0, 20.0, "Motion", "Peak vertical bob amplitude written to float_amp_m for WPO/Blueprint animation in UE."),
    ("orbit_radius_m", "Orbit Radius (m)", "float", 4.0, 0.0, 15.0, "Motion", "Peak orbital drift radius written to orbit_radius_m for UE animation."),
    ("crystal_density", "Crystal Density", "int", 64, 0, 200, "Crystals", "Number of candidate crystal anchors ranked by |Chladni F|; strongest antinodes crystallize first."),
    ("crystal_size_m", "Crystal Size (m)", "float", 3.5, 0.5, 12.0, "Crystals", "Base height of the hexagonal inlay crystals and their satellites."),
    ("chladni_threshold", "Chladni |F| Threshold", "float", 0.10, 0.0, 2.0, "Crystals", "Minimum |F(3,5)| at an anchor's global field coordinate; anchors below this never crystallize."),
    ("embed_depth", "Footing Embed (m)", "float", 4.0, 0.5, 30.0, "Terrain", "Footings extend this distance below each supplied terrain sample."),
    ("yaw_deg", "Approach Frame Yaw (deg)", "float", 45.0, -180.0, 180.0, "Field and Placement", "Candidate seam-frame yaw. Final site placement remains editor-owned."),
    ("global_field_x_m", "Global Chladni X (m)", "float", -1000.125, -4000.0, 4000.0, "Field and Placement", "Global field coordinate; the canonical F(3,5), seed 3900 is never rephased."),
    ("global_field_z_m", "Global Chladni Z (m)", "float", -1000.125, -4000.0, 4000.0, "Field and Placement", "Global field coordinate; local Houdini frame is X/Z with Y up."),
    ("site_id", "Stable Site ID", "string", "FM_ALMOST_GATE_CANDIDATE", None, None, "Field and Placement", "Stable asset candidate id only; it does not define narrative or gameplay state."),
    ("seed", "Seed", "int", 3900, 0, 999999, "Field and Placement", "Faraway Mother world-genome seed."),
]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(geo):
    def norm(v):
        if isinstance(v, (tuple, list)):
            return [norm(x) for x in v]
        try:
            if hasattr(v, "__len__") and not isinstance(v, (str, bytes)):
                return [norm(x) for x in v]
        except Exception:
            pass
        return round(float(v), 8) if isinstance(v, float) else v
    points = [{"P": norm(tuple(p.position())),
               "attrs": {a.name(): norm(p.attribValue(a))
                         for a in sorted(geo.pointAttribs(), key=lambda a: a.name())
                         if a.name() != "P"}}
              for p in geo.points()]
    prims = [{"verts": [v.point().number() for v in pr.vertices()],
              "attrs": {a.name(): norm(pr.attribValue(a))
                        for a in sorted(geo.primAttribs(), key=lambda a: a.name())}}
             for pr in geo.prims()]
    raw = json.dumps({"points": points, "prims": prims}, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def bbox(geo):
    b = geo.boundingBox()
    return [[float(x) for x in b.minvec()], [float(x) for x in b.maxvec()]]


def signature(geo):
    """Cheap drive/restore signature: counts, bounds and the piece column.
    The exact canonical_hash re-verifies everything once after all controls."""
    h = hashlib.sha256()
    h.update(("%d %d " % (len(geo.points()), len(geo.prims()))).encode("utf-8"))
    b = geo.boundingBox()
    h.update(repr([round(float(v), 6) for v in b.minvec()]
                  + [round(float(v), 6) for v in b.maxvec()]).encode("utf-8"))
    pa = geo.findPrimAttrib("piece")
    if pa is not None:
        h.update("|".join(str(pr.attribValue(pa)) for pr in geo.prims()).encode("utf-8"))
    return h.hexdigest()


def candidate_dir():
    base = ROOT / "Saved/Staging/HoudiniForge"
    n = 1
    while True:
        path = base / ("FarawayAlmostGateV3_20261027_%02d" % n)
        if not path.exists():
            return path
        n += 1


def get_frame():
    import faraway_heart_gate_v2 as prior
    return prior.field_frame()


def parm_group(hou, frame):
    group = hou.ParmTemplateGroup()
    folders = {}
    for row in PARMS:
        folders.setdefault(row[6], hou.FolderParmTemplate(
            row[6].lower().replace(" ", "_"), row[6]))
    for name, label, kind, default, low, high, folder, help_text in PARMS:
        if name == "yaw_deg":
            default = float(frame["hda_local_yaw_deg"])
        elif name == "global_field_x_m":
            default = float(frame["global_field_xz_m"][0])
        elif name == "global_field_z_m":
            default = float(frame["global_field_xz_m"][1])
        if kind == "toggle":
            parm = hou.ToggleParmTemplate(name, label, default_value=bool(default))
        elif kind == "int":
            parm = hou.IntParmTemplate(name, label, 1, default_value=(int(default),),
                                       min=low, max=high)
        elif kind == "string":
            parm = hou.StringParmTemplate(name, label, 1, default_value=(default,))
        else:
            parm = hou.FloatParmTemplate(name, label, 1, default_value=(float(default),),
                                         min=low, max=high)
        parm.setHelp(help_text + " Houdini units are metres, Y up.")
        folders[folder].addParmTemplate(parm)
    for title in ("Build", "Silhouette", "Geology", "Approach", "Silk", "Ornament",
                  "Motion", "Crystals", "Terrain", "Field and Placement"):
        group.append(folders[title])
    return group


def _encoded_exec(source, label, target="globals()"):
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    chunks = [encoded[i:i + 76] for i in range(0, len(encoded), 76)]
    return ("_payload=(\n" + "\n".join(repr(c) for c in chunks) + "\n)\n"
            + "exec(compile(base64.b64decode(_payload).decode('utf-8'),"
            + repr("<embedded " + label + ">") + ",'exec')," + target + ")\n")


def _runtime_code(source, ornament_source, silk_source, collision=False):
    head = "import hou,math,base64\n"
    head += _encoded_exec(source, "faraway_almost_gate_geometry.py")
    head += _encoded_exec(ornament_source, "faraway_almost_gate_ornaments.py")
    head += "_silk_env={'math':math}\n" + _encoded_exec(silk_source, "silk_ribbon_geometry.py", "_silk_env")
    head += "_COLLISION=%r\n" % bool(collision)
    head += "_MATERIALS=%r\n" % MATERIALS
    return head + r'''
node=hou.pwd(); asset=node.parent(); geo=node.geometry(); geo.clear()
def _find_attrib(g,scope,name,default):
    if scope==hou.attribType.Point: old=g.findPointAttrib(name)
    elif scope==hou.attribType.Prim: old=g.findPrimAttrib(name)
    else: old=g.findVertexAttrib(name)
    return old if old is not None else g.addAttrib(scope,name,default)
def _field_f(x,z):
    u=(float(x)+4000.0)/8000.0; v=(float(z)+4000.0)/8000.0
    return math.cos(3.0*math.pi*u)*math.cos(5.0*math.pi*v)-math.cos(5.0*math.pi*u)*math.cos(3.0*math.pi*v)
_PARM_NAMES=('height','width','depth','asymmetry','erosion','aperture_width','aperture_height','detail_mode','drape_count','drape_width','drape_length','drape_ripple','drape_segments','embed_depth','seed','scrollwork_count','heart_tokens','shell_fans','tendril_count','ivy_strands','wisteria_racemes','star_shards','float_shards','float_amp_m','orbit_radius_m','crystal_density','crystal_size_m','chladni_threshold')
P={name:asset.parm(name).eval() for name in _PARM_NAMES}
P['ground_west']=P['ground_east']=-2.8
terrain=node.inputs()[0].geometry() if node.inputs() and node.inputs()[0] else None
if terrain is not None and len(terrain.points()):
    name_at=terrain.findPointAttrib('name')
    if name_at is None: raise hou.NodeError('Terrain input points require string point attribute name=west/east.')
    samples={}
    for pt in terrain.points():
        key=str(pt.attribValue(name_at))
        if key in samples or key not in ('west','east'): raise hou.NodeError('Supply exactly one terrain sample named west and one named east.')
        samples[key]=tuple(float(v) for v in pt.position())
    if set(samples)!=set(('west','east')): raise hou.NodeError('Terrain input needs exactly west and east samples.')
    rx=float(P['width'])*.18; center=float(P['aperture_width'])*.5+rx*1.45+8.0
    expected={'west':(-center-float(P['asymmetry'])*8.0,0.0),
              'east':(center+float(P['asymmetry'])*11.0,0.0)}
    for key,(x,z) in expected.items():
        q=samples[key]
        if abs(q[0]-x)>.08 or abs(q[2]-z)>.08: raise hou.NodeError('Terrain sample %s must remain under the corresponding support center.'%key)
    P['ground_west']=samples['west'][1]; P['ground_east']=samples['east'][1]
else: samples={'west':(-1.0,-2.8,0.0),'east':(1.0,-2.8,0.0)}
parts=generate(P,collision=_COLLISION)
_motion={}; _crystal={}
if not _COLLISION:
    half=float(P['aperture_width'])*.5; height=float(P['height']); d=float(P['depth'])
    count=int(P['drape_count']); width=float(P['drape_width'])
    for di in range(count):
        side=-1 if di%2==0 else 1; layer=di//2
        x0=side*(half+26.0+layer*10.0); x1=side*(half+21.0+layer*10.0); x2=side*(half+24.0+layer*10.0)
        z0=(-1 if di%2==0 else 1)*d*.20; z1=z0+side*7.0; z2=z0+side*12.0
        start=height*(.73-.035*layer); end=max(float(P['aperture_height'])*.22,start-float(P['drape_length']))
        guides=[(x0,start,z0),(x1,start-float(P['drape_length'])*.34,z1),(x2,end,z2)]
        rp={'segments':int(P['drape_segments']),'width':width,'taper':.52,
            'flutter_amp':float(P['drape_ripple']),'flutter_wavelength':46.0,
            'seed':int(P['seed'])+di*53,'base_roll':0.0,'twist_turns':0.0,
            'preview_mode':not bool(P['detail_mode'])}
        ribbon,guide,meta=_silk_env['generate'](rp,guides)
        for face in ('front','back'):
            grid=ribbon[face]; rows=grid['P']; uv=grid['uv']; point_rows=[]
            for ri,row in enumerate(rows):
                out_row=[]
                for ci,q in enumerate(row): out_row.append((tuple(q),tuple(uv[ri][ci])))
                point_rows.append(out_row)
            quads=[]
            for ri in range(len(point_rows)-1):
                for ci in range(len(point_rows[ri])-1):
                    a,b=point_rows[ri][ci],point_rows[ri][ci+1]
                    c,e=point_rows[ri+1][ci+1],point_rows[ri+1][ci]
                    quads.append((a,b,c,e) if face=='front' else (a,e,c,b))
            faces=[]
            for quad in quads:
                faces.append(tuple(v[0] for v in quad))
            parts.append({'piece':'silk_drape_%s_%02d'%(face,di),'faces':faces,
                          'material':'silk','uv_faces':[tuple(v[1] for v in q) for q in quads]})
    # Ornate feminine layer + Chladni crystals. The field is evaluated at each
    # anchor's GLOBAL coordinates: site field origin plus the yaw-rotated local
    # frame, so the inlay pattern follows the one canonical F(3,5) rockscape.
    _gyaw=math.radians(float(asset.parm('yaw_deg').eval()))
    _gct,_gst=math.cos(_gyaw),math.sin(_gyaw)
    _gx0=float(asset.parm('global_field_x_m').eval()); _gz0=float(asset.parm('global_field_z_m').eval())
    def _global_field(local_x,local_z):
        return _field_f(_gx0+_gct*local_x+_gst*local_z, _gz0-_gst*local_x+_gct*local_z)
    _base_count=len(parts)
    _orn_parts,_orn_meta=generate_ornaments(P,_global_field,collision=_COLLISION)
    parts.extend(_orn_parts)
    for _idx,_m in _orn_meta['motion'].items(): _motion[_base_count+_idx]=_m
    for _idx,_c in _orn_meta['crystal'].items(): _crystal[_base_count+_idx]=_c

piece_at=_find_attrib(geo,hou.attribType.Prim,'piece','')
mat_at=_find_attrib(geo,hou.attribType.Prim,'unreal_material','')
out_at=_find_attrib(geo,hou.attribType.Prim,'unreal_output_name','')
site_at=_find_attrib(geo,hou.attribType.Prim,'site_id','')
field_at=_find_attrib(geo,hou.attribType.Prim,'faraway_field_F',0.0)
coll_at=_find_attrib(geo,hou.attribType.Prim,'collision_proxy',0)
embed_at=_find_attrib(geo,hou.attribType.Prim,'terrain_embed_m',0.0)
nanite_at=_find_attrib(geo,hou.attribType.Prim,'unreal_nanite_enabled',0)
mode_at=_find_attrib(geo,hou.attribType.Prim,'unreal_collision_mode',0)
phase_at=_find_attrib(geo,hou.attribType.Prim,'float_phase',0.0)
amp_at=_find_attrib(geo,hou.attribType.Prim,'float_amp_m',0.0)
orb_at=_find_attrib(geo,hou.attribType.Prim,'orbit_radius_m',0.0)
spin_at=_find_attrib(geo,hou.attribType.Prim,'spin_rate',0.0)
chF_at=_find_attrib(geo,hou.attribType.Prim,'chladni_F',0.0)
glow_at=_find_attrib(geo,hou.attribType.Prim,'crystal_glow',0.0)
uv_at=_find_attrib(geo,hou.attribType.Vertex,'uv',(0.0,0.0,0.0))
cd_at=_find_attrib(geo,hou.attribType.Vertex,'Cd',(1.0,1.0,1.0))
_VIEW_COLORS={'stone':(0.62,0.38,0.47),'rib':(0.78,0.60,0.48),
              'silk':(0.92,0.63,0.70),'crown_rosette':(0.97,0.78,0.53),
              'ornament':(0.99,0.80,0.45),'crystal':(0.88,0.62,0.98)}
site=str(asset.parm('site_id').eval()); f=_field_f(asset.parm('global_field_x_m').eval(),asset.parm('global_field_z_m').eval())
yaw=math.radians(float(asset.parm('yaw_deg').eval())); ct,st=math.cos(yaw),math.sin(yaw)
point_cache={}
def _point(q):
    key=(round(q[0],7),round(q[1],7),round(q[2],7))
    p=point_cache.get(key)
    if p is None:
        p=geo.createPoint(); p.setPosition((ct*q[0]+st*q[2],q[1],-st*q[0]+ct*q[2])); point_cache[key]=p
    return p
for _pi,part in enumerate(parts):
    piece=part['piece']; material=part['material']; uvs=part.get('uv_faces')
    _m=_motion.get(_pi); _c=_crystal.get(_pi)
    for fi,face in enumerate(part['faces']):
        pr=geo.createPolygon()
        for vi,q in enumerate(face):
            v=pr.addVertex(_point(q))
            v.setAttribValue(cd_at,_VIEW_COLORS.get(material,_VIEW_COLORS['stone']))
            if uvs is not None: v.setAttribValue(uv_at,tuple(uvs[fi][vi]))
        pr.setAttribValue(piece_at,piece); pr.setAttribValue(mat_at,_MATERIALS.get(material,_MATERIALS['stone']))
        pr.setAttribValue(out_at,'SM_Faraway_AlmostGate_v03_01' if not _COLLISION else 'UCX_SM_Faraway_AlmostGate_v03_01')
        pr.setAttribValue(site_at,site); pr.setAttribValue(field_at,float(f))
        pr.setAttribValue(coll_at,1 if piece in ('stone_mass','outer_spire','base_carapace','terrain_footing','crown_spire') else 0)
        pr.setAttribValue(embed_at,float(asset.parm('embed_depth').eval()) if piece=='terrain_footing' else 0.0)
        pr.setAttribValue(nanite_at,0 if _COLLISION else 1); pr.setAttribValue(mode_at,0 if not _COLLISION else 1)
        if _m is not None:
            pr.setAttribValue(phase_at,float(_m['float_phase'])); pr.setAttribValue(amp_at,float(_m['float_amp_m']))
            pr.setAttribValue(orb_at,float(_m['orbit_radius_m'])); pr.setAttribValue(spin_at,float(_m['spin_rate']))
        if _c is not None:
            pr.setAttribValue(chF_at,float(_c[0])); pr.setAttribValue(glow_at,float(_c[1]))
for name,value in (('unreal_output_name','SM_Faraway_AlmostGate_v03_01' if not _COLLISION else 'UCX_SM_Faraway_AlmostGate_v03_01'),
                   ('site_id',site),('faraway_field_F',float(f)),('faraway_field_seed',3900),
                   ('floor_datum_y_m',0.0),('clear_aperture_width_m',float(P['aperture_width'])),
                   ('clear_aperture_height_m',float(P['aperture_height'])),('approach_frame_yaw_deg',float(asset.parm('yaw_deg').eval())),
                   ('collision_proxy',1 if _COLLISION else 0)):
    a=geo.findGlobalAttrib(name) or geo.addAttrib(hou.attribType.Global,name,value); geo.setGlobalAttribValue(a,value)
'''


def anchor_code():
    return r'''import hou,math
node=hou.pwd(); asset=node.parent(); g=node.geometry(); g.clear()
for n,d in (('site_id',''),('role',''),('variant',''),('yaw_deg',0.0),('clearance_radius_m',0.0),('seed',3900),('global_field_F',0.0)):
    if g.findPointAttrib(n) is None: g.addAttrib(hou.attribType.Point,n,d)
fx=float(asset.parm('global_field_x_m').eval()); fz=float(asset.parm('global_field_z_m').eval())
u=(fx+4000)/8000; v=(fz+4000)/8000; F=math.cos(3*math.pi*u)*math.cos(5*math.pi*v)-math.cos(5*math.pi*u)*math.cos(3*math.pi*v)
yaw=math.radians(float(asset.parm('yaw_deg').eval())); ct,st=math.cos(yaw),math.sin(yaw)
rows=[('FM_ALMOST_GATE_ORIGIN','LandmarkRoot','TheAlmostGate',(0.0,0.0,0.0),120.0),
      ('FM_ALMOST_GATE_CROWN','DressingAnchor','CrownRosette',(float(asset.parm('width').eval())*.07+float(asset.parm('asymmetry').eval())*13.0,
          float(asset.parm('aperture_height').eval())+30.0+float(asset.parm('height').eval())*.50, float(asset.parm('depth').eval())*.78),22.0),
      ('FM_ALMOST_GATE_APPROACH_REVEAL','ViewAnchor','CathedralFacingReveal',(0.0,float(asset.parm('aperture_height').eval())*.48,-float(asset.parm('depth').eval())*.72),45.0),
      ('FM_HEART_GATE_THRESHOLD_SOCKET','ExistingThresholdAnchor','MEL_mother_heart_gate',(0.0,0.0,-float(asset.parm('depth').eval())*.5-8.0),float(asset.parm('aperture_width').eval())*.5),
      ('FM_ALMOST_GATE_RESONANCE_RING','ResonanceAnchor','CrystalCrownOrbit',(float(asset.parm('width').eval())*.07+float(asset.parm('asymmetry').eval())*13.0,
          float(asset.parm('height').eval())+135.0, float(asset.parm('depth').eval())*.24),60.0)]
for sid,role,variant,q,clearance in rows:
    p=g.createPoint(); p.setPosition((ct*q[0]+st*q[2],q[1],-st*q[0]+ct*q[2]))
    for n,v in (('site_id',sid),('role',role),('variant',variant),('yaw_deg',math.degrees(yaw)),('clearance_radius_m',clearance),('seed',3900),('global_field_F',F)):
        p.setAttribValue(n,v)
g.addAttrib(hou.attribType.Global,'unreal_output_name','PT_Faraway_AlmostGate_03_Anchors')
'''


def make_hda(hou, out, frame):
    hda = out / "hda/HDA_Faraway_AlmostGate_v03.hda"
    host = hou.node("/obj").createNode("geo", "AlmostGateV3_ArtistCanary")
    for child in host.children():
        child.destroy()
    sub = host.createNode("subnet", "almost_gate_v3_template")
    asset = sub.createDigitalAsset(name=TYPE, hda_file_name=str(hda),
                                   description="Faraway Mother The Almost Gate v03; ornate monolithic rock, silk, scrollwork, hearts, stars, levitating shards and Chladni crystals",
                                   min_num_inputs=0, max_num_inputs=1)
    asset.allowEditingOfContents()
    for child in list(asset.children()):
        if child.type().name() == "output":
            child.destroy()
    asset.setParmTemplateGroup(parm_group(hou, frame))
    inputs = asset.indirectInputs()
    if not inputs:
        raise RuntimeError("Almost Gate v03 asset is missing its optional sampled-terrain input.")
    source = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    ornaments = ORNAMENT_SOURCE.read_text(encoding="utf-8")
    silk = SILK_SOURCE.read_text(encoding="utf-8")
    ins = inputs[0]
    arch = asset.createNode("python", "mountain_silk_ornaments_crystals")
    arch.setInput(0, ins)
    arch.parm("python").set(_runtime_code(source, ornaments, silk, False))
    norm = asset.createNode("normal", "architecture_normals")
    norm.setInput(0, arch)
    norm.parm("cuspangle").set(48.0)
    collision = asset.createNode("python", "conservative_collision")
    collision.setInput(0, ins)
    collision.parm("python").set(_runtime_code(source, ornaments, silk, True))
    anchors = asset.createNode("python", "stable_anchors")
    anchors.setInput(0, ins)
    anchors.parm("python").set(anchor_code())
    for idx, name, src in ((0, "OUT_ARCHITECTURE", norm),
                           (1, "OUT_COLLISION", collision),
                           (2, "OUT_ANCHORS", anchors)):
        op = asset.createNode("output", name)
        op.setInput(0, src)
        op.parm("outputidx").set(idx)
        if idx == 0:
            op.setDisplayFlag(True)
            op.setRenderFlag(True)
    asset.layoutChildren()
    asset.type().definition().setParmTemplateGroup(asset.parmTemplateGroup())
    asset.type().definition().updateFromNode(asset)
    asset.type().definition().save(str(hda), template_node=asset, create_backup=False)
    asset.matchCurrentDefinition()
    if asset.isEditable():
        raise RuntimeError("The Almost Gate v03 HDA definition did not lock after saving.")
    host.layoutChildren()
    return host, asset, hda


def create_ground_samples(hou, parent, asset, relief=0.0):
    node = parent.createNode("python", "sampled_terrain_west_east")
    code = r'''import hou
node=hou.pwd(); g=node.geometry(); g.clear(); a=g.addAttrib(hou.attribType.Point,'name','')
asset=next(n for n in node.parent().children() if n.type().name()=='HDA_Faraway_AlmostGate_v03'); width=float(asset.parm('width').eval()); aperture=float(asset.parm('aperture_width').eval()); asym=float(asset.parm('asymmetry').eval())
center=aperture*.5+width*.18*1.45+8.0; relief=float(node.evalParm('relief'))
for name,x,dy in [('west',-center-asym*8.0,0.0),('east',center+asym*11.0,0.0)]:
    p=g.createPoint(); p.setPosition((x,-2.8+relief+dy,0.0)); p.setAttribValue(a,name)
'''
    node.parm("python").set(code)
    group = node.parmTemplateGroup()
    relief_parm = hou.FloatParmTemplate("relief", "Ground Relief (m)", 1,
                                        default_value=(float(relief),), min=-2.0, max=2.0)
    relief_parm.setHelp("Canary only: raises/lower both sampled terrain contacts; the approach datum remains level.")
    group.append(relief_parm); node.setParmTemplateGroup(group)
    return node


def outputs(asset):
    return {"architecture": asset.node("OUT_ARCHITECTURE").geometry(),
            "collision": asset.node("OUT_COLLISION").geometry(),
            "anchors": asset.node("OUT_ANCHORS").geometry()}


def cook(asset, names=None):
    asset.cook(force=True)
    errors = []
    for node in [asset] + list(asset.allSubChildren()):
        try:
            if node.errors():
                errors.append({"node": node.path(), "errors": list(node.errors())})
        except Exception:
            pass
    if errors:
        raise RuntimeError("HDA cook diagnostics: " + repr(errors))
    gs = outputs(asset)
    if names is not None:
        gs = {k: v for k, v in gs.items() if k in names}
    report = {name: {"hash": canonical_hash(geo), "points": len(geo.points()),
                     "primitives": len(geo.prims()), "bounds_m": bbox(geo)}
              for name, geo in gs.items()}
    return report, gs


def _set_parm(node, name, value):
    p = node.parm(name)
    if p is not None:
        p.set(value)


def build_cop_canary(hou, out, field_f=None):
    """Artist-facing COP companion: a Copernicus (/img/copnet) network in the
    canary HIP that artists iterate on, PLUS a real baked sparkle PNG written
    via hou.saveImageDataToFile.

    H22 bake-path findings (documented for the lane):
      * Legacy "cop2net" is gone; /img createNode("copnet") yields Copernicus.
      * hscript "coprender" does not exist; "opwrite" writes .cpio node
        archives, NOT images; the legacy /out "comp" ROP cannot address
        Copernicus nodes ("No OP found").
      * Copernicus nodes expose no verb / pixel API headless.
    So the headless bake computes the same Chladni field the crystal ranking
    uses (parity by construction) and writes RGBA through
    hou.saveImageDataToFile; in-GUI artists bake the network directly."""
    result = {"status": "FAILED", "reason": "not attempted"}
    try:
        img = hou.node("/img")
        for stale in list(img.children()):
            stale.destroy()
        net = img.createNode("copnet", "almost_gate_crystal_cops")
        net.setParms({"setres": 1, "res1": 512, "res2": 512})
        gen = net.createNode("constant", "base_alabaster")
        gen.setParms({"signature": "f4", "f4r": 0.88, "f4g": 0.62,
                      "f4b": 0.98, "f4a": 1.0})
        grade = net.createNode("gamma", "glow_lift")
        grade.setInput(0, gen)
        grade.setParms({"gamma": 1.35})
        soft = net.createNode("blur", "soft_vignette")
        soft.setInput(0, grade)
        soft.setParms({"size": 0.012})
        out_node = net.createNode("output", "OUT_crystal_sparkle")
        out_node.setInput(0, soft)
        out_node.setGenericFlag(hou.nodeFlag.Render, True)
        out_node.setGenericFlag(hou.nodeFlag.Display, True)
        out_node.cook(force=True)

        # Headless bake: sparkle mask from the SAME Chladni field the crystal
        # clusters are ranked by (site coords, plate +/-4000, seed 3900).
        res = 512
        px = bytearray()
        for j in range(res):
            v = (j / (res - 1)) * 2.0 - 1.0
            for i in range(res):
                u = (i / (res - 1)) * 2.0 - 1.0
                F = field_f(u, v) if field_f is not None else 0.0
                sparkle = min(1.0, abs(F) * 3.2)
                px += bytes((int(255 * (0.35 + 0.6 * sparkle)),
                             int(255 * (0.15 + 0.3 * sparkle)),
                             int(255 * (0.55 + 0.45 * sparkle)),
                             255))
        image = out / "review/CrystalSparkle_COP.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        if image.exists():
            image.unlink()
        hou.saveImageDataToFile(bytes(px), res, res, str(image))
        if image.exists() and image.stat().st_size > 200:
            result = {"status": "COP_BAKE_PASS", "path": str(image),
                      "bytes": image.stat().st_size, "sha256": sha256(image),
                      "resolution": [res, res],
                      "network": net.path(),
                      "network_type": "Copernicus copnet (H22)",
                      "renderer": "hou.saveImageDataToFile + Chladni parity pixels",
                      "note": ("Artist companion: /img/almost_gate_crystal_cops "
                               "in the canary HIP; PNG baked headless from the "
                               "identical Chladni field used for crystal "
                               "ranking. HDA itself is geometry-only.")}
        else:
            result = {"status": "FAILED", "reason": "saveImageDataToFile wrote no image"}
    except Exception as exc:
        result = {"status": "FAILED", "reason": repr(exc)}
    return result


def _set_sample_relief(node, relief):
    node.parm("relief").set(float(relief))
    node.cook(force=True)


CAMERA_SPECS = {
    "establishing": ("CAM_AlmostGateV3_Establishing", (760.0, 500.0, 1040.0), (0.0, 250.0, 0.0),
                     "AlmostGateV3_Establishing.png"),
    "approach": ("CAM_AlmostGateV3_Approach", (0.0, 138.0, -720.0), (0.0, 270.0, 0.0),
                 "AlmostGateV3_Approach.png"),
    "crown": ("CAM_AlmostGateV3_CrownDetail", (180.0, 590.0, 330.0), (0.0, 520.0, 30.0),
              "AlmostGateV3_CrownDetail.png"),
}


def render_one_view(hou, host, asset, out, view):
    """Render one deterministic artist view in its own process: the headless
    Vulkan OpenGL ROP can segfault, so a crash here never kills other views."""
    cam_name, position, target, image_name = CAMERA_SPECS[view]
    cam = hou.node("/obj").createNode("cam", cam_name)
    for c in hou.node("/obj").children():
        if c.type().name() == "cam" and c.name() != cam_name:
            c.destroy()
    eye = hou.Vector3(*position)
    aim = hou.Vector3(*target)
    cam.parmTuple("t").set(tuple(eye))
    cam.parmTuple("r").set(tuple(hou.hmath.buildRotateLookAt(
        eye, aim, hou.Vector3(0.0, 1.0, 0.0)).extractRotates()))
    cam.parm("focal").set(35.0)
    cam.parm("resx").set(1440)
    cam.parm("resy").set(900)
    rop = hou.node("/out").createNode("opengl", "review_almost_gate_v3_" + view)
    rop.parm("vobjects").set(host.path())
    rop.parm("res1").set(1440)
    rop.parm("res2").set(900)
    rop.parm("usegeocolor").set(1)
    rop.parm("hqlighting").set(1)
    rop.parm("shadows").set(1)
    rop.parm("ambocclusion").set(1)
    rop.parm("camera").set(cam.path())
    image = out / "review" / image_name
    rop.parm("picture").set(str(image))
    rop.render()
    if not image.exists() or image.stat().st_size < 4096:
        raise RuntimeError("Native review render failed: " + str(image))
    hou.setPwd(host)
    for node in host.children():
        node.setSelected(node == asset)
    return {image_name: {"path": "review/" + image_name, "bytes": image.stat().st_size,
                         "sha256": sha256(image), "camera": cam.path(),
                         "renderer": "Houdini OpenGL ROP", "resolution": [1440, 900]}}


def native_build(out, frame, stage="all"):
    import hou
    log("make_hda start")
    host, asset, hda = make_hda(hou, out, frame)
    log("make_hda done")
    ground = create_ground_samples(hou, host, asset, 0.0)
    asset.setInput(0, ground)
    asset.parm("site_id").set("FM_ALMOST_GATE_V3_CANARY")
    base, geos = cook(asset)
    log("base cook done")
    again, _ = cook(asset)
    log("determinism cook done")
    determinism = {k: base[k]["hash"] == again[k]["hash"] for k in base}
    if not all(determinism.values()):
        raise RuntimeError("Two-run deterministic geometry/site hash gate failed: " + repr(determinism))
    if len(geos["architecture"].prims()) < 4000 or len(geos["anchors"].points()) != 5:
        raise RuntimeError("Monument detail or stable anchor count is below its minimum.")
    if not geos["architecture"].findPrimAttrib("unreal_material"):
        raise RuntimeError("Architecture output has no existing Unreal material references.")
    if not geos["architecture"].findPrimAttrib("float_phase") or \
       not geos["architecture"].findPrimAttrib("chladni_F"):
        raise RuntimeError("Architecture output is missing motion/crystal metadata attributes.")

    # Ornament gates: crystals must exist at defaults, moving pieces must carry
    # nonzero motion metadata, and the falling vegetation must be present.
    arch = geos["architecture"]
    piece_at = arch.findPrimAttrib("piece")
    glow_at = arch.findPrimAttrib("crystal_glow")
    amp_at = arch.findPrimAttrib("float_amp_m")
    crystals = moving = ivy = wisteria = 0
    for pr in arch.prims():
        piece = str(pr.attribValue(piece_at))
        if piece == "crystal" and float(pr.attribValue(glow_at)) > 0.0:
            crystals += 1
        if piece in ("float_shard", "star_shard") and float(pr.attribValue(amp_at)) > 0.0:
            moving += 1
        if piece == "ivy_leaf":
            ivy += 1
        if piece == "wisteria_bloom":
            wisteria += 1
    if crystals < 20 or moving < 10 or ivy < 10 or wisteria < 60:
        raise RuntimeError("Ornament gate failed: crystals=%d moving=%d ivy=%d wisteria=%d"
                           % (crystals, moving, ivy, wisteria))
    log("ornament gates OK: crystals=%d moving=%d ivy=%d wisteria=%d"
        % (crystals, moving, ivy, wisteria))

    p = {name: asset.parm(name).eval() for name in
         ("height", "width", "depth", "asymmetry", "erosion", "aperture_width",
          "aperture_height", "detail_mode", "seed", "embed_depth")}
    p.update({"ground_west": -2.8, "ground_east": -2.8})
    def portal_clear(geo):
        yaw=math.radians(float(asset.parm("yaw_deg").eval())); ct,st=math.cos(yaw),math.sin(yaw)
        half=float(p["aperture_width"])*.5; top=float(p["aperture_height"]); hits=[]
        for pt in geo.points():
            x,y,z=[float(v) for v in pt.position()]
            local_x=ct*x-st*z; local_z=st*x+ct*z
            if -half<=local_x<=half and 0.0<=y<=top and abs(local_z)<=22.0:
                hits.append((round(local_x,3),round(y,3),round(local_z,3)))
                if len(hits)>=8: break
        triangles=[]
        for pr in geo.prims():
            coords=[]
            for vtx in pr.vertices():
                x,y,z=[float(v) for v in vtx.point().position()]
                coords.append((ct*x-st*z,y,st*x+ct*z))
            for i in range(1,len(coords)-1): triangles.append((coords[0],coords[i],coords[i+1]))
        # Precompute per-triangle XY bounds once: the ray grid reuses them.
        tris_bbox=[(min(q[0] for q in tri),max(q[0] for q in tri),
                    min(q[1] for q in tri),max(q[1] for q in tri),tri) for tri in triangles]
        zlim=max(22.0,float(p["depth"])*.9); direction=(0.0,0.0,1.0)
        def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
        def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        def ray_hit(origin,tri):
            a,b,c=tri; e1=(b[0]-a[0],b[1]-a[1],b[2]-a[2]); e2=(c[0]-a[0],c[1]-a[1],c[2]-a[2])
            pv=cross(direction,e2); det=dot(e1,pv)
            if abs(det)<1e-10: return False
            inv=1.0/det; tv=(origin[0]-a[0],origin[1]-a[1],origin[2]-a[2]); u=dot(tv,pv)*inv
            if u < -1e-8 or u > 1.0+1e-8: return False
            qv=cross(tv,e1); v=dot(direction,qv)*inv
            if v < -1e-8 or u+v > 1.0+1e-8: return False
            distance=dot(e2,qv)*inv
            return -1e-8 <= distance <= 2.0*zlim+1e-8
        tested=0; ray_hits=[]
        for x in range(int(-half+5),int(half),10):
            for y in range(5,int(top),10):
                tested+=1; origin=(float(x),float(y),-zlim)
                for mnx,mxx,mny,mxy,tri in tris_bbox:
                    if x<mnx-1e-7 or x>mxx+1e-7: continue
                    if y<mny-1e-7 or y>mxy+1e-7: continue
                    if ray_hit(origin,tri):
                        ray_hits.append((x,y)); break
                if len(ray_hits)>=8: break
            if len(ray_hits)>=8: break
        return {"clear":not hits and not ray_hits,"hit_vertices":hits,
                "tested_rays":tested,"ray_hits":ray_hits,"depth_span_m":[-zlim,zlim]}
    portal_arch=portal_clear(geos["architecture"])
    log("portal production done")
    portal_collision=portal_clear(geos["collision"])
    log("portal collision done")
    if not portal_arch["clear"] or not portal_collision["clear"]:
        raise RuntimeError("Lower aperture clearance failed: " + repr((portal_arch, portal_collision)))
    datum = float(geos["architecture"].findGlobalAttrib("floor_datum_y_m") and
                  geos["architecture"].attribValue("floor_datum_y_m"))
    if abs(datum) > 1e-8:
        raise RuntimeError("Approach floor datum changed from local Y=0.")
    footings = [pr for pr in geos["architecture"].prims()
                if str(pr.attribValue("piece")) == "terrain_footing"]
    if len(footings) != 12:
        raise RuntimeError("Expected two sampled terrain footings with six faces each.")
    min_embed = min(float(pr.attribValue("terrain_embed_m")) for pr in footings)
    if min_embed < 0.5:
        raise RuntimeError("Footing embed below 0.5 m.")
    base_bottom = min(float(v.point().position()[1])
                      for pr in footings for v in pr.vertices())

    controls = {}
    for name, drive in (("height", lambda old: old + 20.0),
                        ("asymmetry", lambda old: min(1.0, old + 0.12)),
                        ("detail_mode", lambda old: 0 if old else 1),
                        ("yaw_deg", lambda old: old + 4.0),
                        ("scrollwork_count", lambda old: min(24, old + 4)),
                        ("wisteria_racemes", lambda old: min(32, old + 4)),
                        ("crystal_density", lambda old: min(200, old + 24)),
                        ("float_shards", lambda old: min(40, old + 6))):
        parm = asset.parm(name); original = parm.eval(); before = signature(outputs(asset)["architecture"])
        parm.set(drive(original)); asset.cook(force=True); driven_sig = signature(outputs(asset)["architecture"])
        parm.set(original); asset.cook(force=True); restored_sig = signature(outputs(asset)["architecture"])
        changed = driven_sig != before
        exact = restored_sig == before
        controls[name] = {"changed_geometry": changed, "restored_exact_hash": exact}
        log("control %s changed=%s exact=%s" % (name, changed, exact))
        if not changed or not exact:
            raise RuntimeError("Control family drive/restore failed for %s" % name)
    exact_final, _ = cook(asset, ("architecture",))
    if exact_final["architecture"]["hash"] != base["architecture"]["hash"]:
        raise RuntimeError("Post-control exact hash restore failed")
    log("post-control exact hash restore OK")

    base_hash = base["architecture"]["hash"]
    _set_sample_relief(ground, 1.0)
    raised, raised_g = cook(asset)
    raised_bottom = min(float(v.point().position()[1]) for pr in raised_g["architecture"].prims()
                        if str(pr.attribValue("piece")) == "terrain_footing" for v in pr.vertices())
    raised_datum = float(raised_g["architecture"].attribValue("floor_datum_y_m"))
    _set_sample_relief(ground, 0.0)
    restored, _ = cook(asset)
    terrain_gate = {"bottom_delta_m": round(raised_bottom - base_bottom, 6),
                    "expected_delta_m": 1.0, "level_datum_before_after_m": [datum, raised_datum],
                    "restored_exact_hash": restored["architecture"]["hash"] == base_hash,
                    "minimum_embed_m": min_embed}
    if abs(terrain_gate["bottom_delta_m"] - 1.0) > 1e-5 or raised_datum != datum or not terrain_gate["restored_exact_hash"]:
        raise RuntimeError("Terrain sample perturbation/restore gate failed: " + repr(terrain_gate))

    for name, geo in outputs(asset).items():
        target = out / "geometry" / (name + ".bgeo.sc")
        target.parent.mkdir(parents=True, exist_ok=True)
        geo.saveToFile(str(target))
    ground.geometry().saveToFile(str(out / "geometry/TerrainSamples_Input0.bgeo.sc"))
    asset.setDisplayFlag(True); asset.setRenderFlag(True)
    hou.hipFile.save(str(out / "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip"))

    partial = {"license": str(hou.licenseCategory()), "houdini": hou.applicationVersionString(),
               "determinism": determinism, "geometry": base,
               "ornaments": {"crystal_prims": crystals, "moving_prims": moving,
                             "ivy_leaves": ivy, "wisteria_blooms": wisteria},
               "portal": {"production_clear": portal_arch["clear"],
                          "collision_clear": portal_collision["clear"],
                          "clear_width_m": float(p["aperture_width"]),
                          "clear_height_m": float(p["aperture_height"]),
                          "tested_geometry": "full production and simplified collision polygons; sampled two-sided rays across full approach depth",
                          "production_rays": portal_arch["tested_rays"],
                          "collision_rays": portal_collision["tested_rays"],
                          "depth_span_m": portal_arch["depth_span_m"]},
               "floor_datum_y_m": datum, "terrain_relief": terrain_gate,
               "control_drive_restore": controls, "stage_a_complete": True}
    (out / "native/state.json").write_text(json.dumps(partial, indent=2), encoding="utf-8")
    if stage == "a":
        return hda, partial
    raise RuntimeError("native_build only supports stage 'a'; use the granular "
                       "--cop/--render/--fbx/--finish steps for stage B.")


def _load_canary(out):
    import hou
    out = Path(out).resolve()
    state = json.loads((out / "native/state.json").read_text(encoding="utf-8"))
    hou.hipFile.load(str(out / "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip"),
                     suppress_save_prompt=True)
    host = hou.node("/obj/AlmostGateV3_ArtistCanary")
    matches = [c for c in host.children() if c.type().name() == TYPE]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one v03 asset in the canary HIP.")
    asset = matches[0]
    ground = None
    for c in host.children():
        if c.type().name() == "python":
            ground = c
    if ground is None:
        raise RuntimeError("Could not find the terrain sample canary node.")
    asset.setInput(0, ground)
    report, geos = cook(asset)
    if report["architecture"]["hash"] != state["geometry"]["architecture"]["hash"]:
        raise RuntimeError("Reopen hash differs from stage A: "
                           + repr((report["architecture"]["hash"],
                                   state["geometry"]["architecture"]["hash"])))
    return hou, out, state, host, asset


def step_cop(out):
    """Granular stage B step 1: COP sparkle bake (its own process)."""
    hou, out, state, host, asset = _load_canary(out)
    cop = build_cop_canary(hou, out, field_f=lambda u, v: chladni_plate_f(u * 4000.0, v * 4000.0))
    state["cop_canary"] = cop
    (out / "native/state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    hou.hipFile.save(str(out / "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip"))
    print(json.dumps({"step": "cop", "status": cop["status"]}, indent=2), flush=True)


def step_render(out, view):
    """Granular stage B step 2: one review view in its own crash-isolated process."""
    hou, out, state, host, asset = _load_canary(out)
    review = dict(state.get("artist_review", {}))
    review.update(render_one_view(hou, host, asset, out, view))
    state["artist_review"] = review
    (out / "native/state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"step": "render", "view": view, "ok": True}, indent=True), flush=True)


def step_fbx(out):
    """Granular stage B step 3: FBX export + native roundtrip."""
    hou, out, state, host, asset = _load_canary(out)
    fbx_path = out / "ue_import/SM_Faraway_AlmostGate_v03_01.fbx"
    fbx_path.parent.mkdir(parents=True, exist_ok=True)
    fbx_result = export_fbx(hou, asset, fbx_path)
    if fbx_result.get("status") != "NATIVE_EXPORT_PASS_NOT_UE_IMPORT_PROOF":
        raise RuntimeError("FBX export gate failed: " + repr(fbx_result))
    fbx_roundtrip = verify_fbx_roundtrip(hou, fbx_path, state["geometry"]["architecture"])
    state["hda_locked"] = not asset.isEditable()
    state["fbx_export"] = fbx_result
    state["fbx_native_roundtrip"] = fbx_roundtrip
    (out / "native/state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"step": "fbx", "status": fbx_result["status"],
                      "roundtrip": fbx_roundtrip["status"]}, indent=2), flush=True)


def step_final(out):
    """Granular stage B step 4: fresh-process definition gate + manifest."""
    out = Path(out).resolve()
    frame = get_frame()
    state = json.loads((out / "native/state.json").read_text(encoding="utf-8"))
    if not state.get("hda_locked"):
        raise RuntimeError("Locked definition gate failed.")
    proc = subprocess.run([str(HFS_HYTHON), str(Path(__file__).resolve()), "--fresh", str(out)],
                          capture_output=True, text=True, timeout=280)
    (out / "native/fresh_process_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (out / "native/fresh_process_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError("Fresh-process HDA/HIP gate failed: " + proc.stderr[-4000:])
    fresh = json.loads((out / "native/fresh_process.json").read_text(encoding="utf-8"))
    for key in state["geometry"]:
        if state["geometry"][key]["hash"] != fresh["outputs"][key]["hash"]:
            raise RuntimeError("Fresh-process geometry hash differs for " + key)
    state["fresh_process"] = fresh
    manifest(out, frame, state)
    print(json.dumps({"step": "final", "candidate_directory": str(out),
                      "hda": str(out / "hda/HDA_Faraway_AlmostGate_v03.hda"),
                      "manifest": str(out / "manifest.json")}, indent=2), flush=True)


def export_fbx(hou, asset, fbx_path):
    try:
        geo_obj = hou.node("/obj").createNode("geo", "AlmostGateV3_FBX_Bake")
        for child in geo_obj.children():
            child.destroy()
        merge = geo_obj.createNode("object_merge", "baked_architecture")
        merge.parm("objpath1").set(asset.node("OUT_ARCHITECTURE").path())
        if merge.parm("xformtype") is not None:
            merge.parm("xformtype").set(0)
        merge.setDisplayFlag(True); merge.setRenderFlag(True)
        rop = hou.node("/out").createNode("filmboxfbx", "export_almost_gate_v3")
        rop.parm("sopoutput").set(str(fbx_path))
        if rop.parm("startnode") is not None:
            rop.parm("startnode").set(geo_obj.path())
        if rop.parm("convertunits") is not None:
            rop.parm("convertunits").set(0)
        rop.render()
        good = fbx_path.exists() and fbx_path.stat().st_size > 1024
        if not good:
            return {"status": "FAILED", "path": str(fbx_path), "reason": "ROP did not write a nonempty FBX."}
        return {"status": "NATIVE_EXPORT_PASS_NOT_UE_IMPORT_PROOF", "path": str(fbx_path),
                "bytes": fbx_path.stat().st_size, "sha256": sha256(fbx_path)}
    except Exception as exc:
        return {"status": "FAILED", "path": str(fbx_path), "reason": repr(exc)}


def verify_fbx_roundtrip(hou, fbx_path, expected):
    imported, message = hou.hipFile.importFBX(str(fbx_path))
    if message:
        raise RuntimeError("FBX round-trip import reported: " + str(message))
    candidates = [n for n in imported.allSubChildren()
                  if n.type().category().name() == "Sop" and n.geometry() is not None]
    if not candidates:
        raise RuntimeError("FBX round-trip contains no SOP mesh.")
    actual = candidates[0].geometry()
    measured = {"points": len(actual.points()), "primitives": len(actual.prims()),
                "bounds_m": bbox(actual)}
    if measured["points"] != expected["points"] or measured["primitives"] != expected["primitives"]:
        raise RuntimeError("FBX round-trip topology differs: " + repr(measured))
    delta = max(abs(measured["bounds_m"][side][axis] - expected["bounds_m"][side][axis])
                for side in (0, 1) for axis in range(3))
    if delta > 1e-4:
        raise RuntimeError("FBX round-trip bounds differ by %.8f m." % delta)
    return {"status": "PASS_NATIVE_HOUDINI_ROUNDTRIP_NOT_UE_IMPORT_PROOF",
            "message": message, "points": measured["points"],
            "primitives": measured["primitives"], "bounds_m": measured["bounds_m"],
            "max_bounds_delta_m": delta,
            "unreal_string_attributes": "FBX may omit Houdini string attributes; the HDA retains unreal_material and site metadata."}


def fresh_process(out):
    import hou
    out = Path(out).resolve()
    hda = out / "hda/HDA_Faraway_AlmostGate_v03.hda"
    hou.hda.installFile(str(hda))
    hou.hipFile.load(str(out / "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip"),
                     suppress_save_prompt=True)
    host = hou.node("/obj/AlmostGateV3_ArtistCanary")
    matches = [child for child in host.children() if child.type().name() == TYPE] if host is not None else []
    asset = matches[0] if len(matches) == 1 else None
    if asset is None or asset.isEditable():
        raise RuntimeError("Fresh-process HIP reopen did not instantiate a locked Almost Gate v03 definition.")
    report, geos = cook(asset)
    if len(geos["anchors"].points()) != 5 or len(geos["architecture"].prims()) < 4000:
        raise RuntimeError("Fresh-process locked asset outputs failed counts.")
    lic = str(hou.licenseCategory())
    if "apprentice" in lic.lower():
        raise RuntimeError("Apprentice contamination: %s" % lic)
    result = {"status": "PASS", "fresh_process": True, "definition_locked": True,
              "license_category": lic, "houdini_version": hou.applicationVersionString(),
              "outputs": report, "hda_path": str(hda),
              "hip_reopened": str(out / "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip")}
    (out / "native/fresh_process.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


RESEARCH_NOTES = """\
Workflow research baked into v03 (sources: SideFX docs/learn portal, CGWiki, HIVE talks):

1. Artist-friendly HDA graphs. The v03 interface follows SideFX HDA guidance:
   folder-grouped parms with help cards, a single optional sampled-terrain input,
   named outputs (Architecture / ConservativeCollision / StableAnchors), and
   per-primitive metadata attributes instead of hidden spare parameters. Sources:
   sidefx.com/products/houdini, sidefx.com/learn.
2. COP networks. Houdini 22 ships both legacy COP2 and the new Copernicus COPs.
   The recommended modern pattern for game textures is Copernicus: SOP Import +
   Rasterize Geometry to bake per-vertex data (e.g. our chladni_F / crystal_glow)
   into masks, then Mask Combine to layer grunge/ID maps (H22 adds 123 COP nodes
   including Weave/Knit generators and grunge maps). The v03 candidate carries a
   COP2 canary (review/CrystalSparkle_COP.png) as the artist-facing starting
   point; a full Copernicus rasterize of crystal_glow is the documented next
   step. Sources: sidefx.com/learn/talks/whats-new-in-copernicus,
   sidefx.com/forum COP rasterize threads, tokeru.com/cgwiki/HoudiniCops.html.
3. Crystal scatter on fields. Gnomon/industry practice for believable crystal
   growth: scatter candidate anchors on the rock skin, then filter by a field
   (here the canonical Chladni F(3,5)) and rank by field strength so the
   strongest antinodes crystallize first; satellites lean off main crystals.
   v03 implements exactly this, deterministically, with crystal_density as the
   artist count control and chladni_threshold as the |F| gate.
4. UE delivery. Houdini Engine for UE 5.x (plugin present in this project)
   cooks the HDA in-editor; per-primitive unreal_material attributes assign the
   existing MI_Mother_* / MI_FloatingCrystal_* instances; float_phase /
   float_amp_m / orbit_radius_m / spin_rate are the WPO/Blueprint animation
   hooks for the moving pieces (silk module already ships VAT/WPO conventions).
"""


def manifest(out, frame, result):
    sources = [__file__, str(GEOMETRY_SOURCE), str(ORNAMENT_SOURCE), str(SILK_SOURCE),
               str(FIELD_SOURCE), str(SEAM_SOURCE), str(HEART_SOURCE), str(V2_BUILDER),
               str(SCHEMA), str(PLACEMENTS), str(LANDMARKS), str(SEAM_MANIFEST)]
    source_hashes = {str(Path(p).resolve()): sha256(p) for p in sources if Path(p).exists()}
    image_hash = sha256(REFERENCE) if REFERENCE.exists() else None
    source_hashes[str(REFERENCE)] = image_hash
    gate_path = out / "native/native_gates.json"
    gate_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    doc = {
        "schema": "melodia.faraway_almost_gate_v3_candidate.v1", "spike": True,
        "monument_name": "The Almost Gate v03",
        "extends": {"hda_type": "HDA_Faraway_AlmostGate_v02", "status": "preserved, not edited"},
        "gameplay_threshold": {"name": "Heart Gate", "challenge_id": "challenge.mother_heart_gate",
                               "existing_asset": "MEL_mother_heart_gate", "included_in_monument_mesh": False,
                               "threshold_anchor_output": "FM_HEART_GATE_THRESHOLD_SOCKET"},
        "hda": {"type_name": TYPE, "file": "hda/HDA_Faraway_AlmostGate_v03.hda",
                "locked_definition": True, "inputs": [{"index": 0, "name": "sampled_terrain_positions",
                    "contract": "exactly two Houdini point samples with string name=west/east; point positions in metres, Y up, local before yaw"}],
                "outputs": [{"index": 0, "name": "Architecture", "tag": "Output-0", "mesh_name": "SM_Faraway_AlmostGate_v03_01"},
                            {"index": 1, "name": "ConservativeCollision", "tag": "Output-1", "mesh_name": "UCX_SM_Faraway_AlmostGate_v03_01"},
                            {"index": 2, "name": "StableAnchors", "tag": "Output-2", "point_name": "PT_Faraway_AlmostGate_03_Anchors"}]},
        "ornament_systems": {
            "scrollwork_volutes": "Archimedean spiral swept tubes on the outer flanks, alternating sides/layers",
            "heart_frames": "Parametric heart curve (16sin^3, 13cos-5cos2-2cos3-cos4) swept; large frame crowns the aperture, tokens ride the spire skins",
            "shell_fans": "Shared-radius hinged blades plus scalloped rim arcs at the shoulders",
            "vine_tendrils": "Damped-sine hanging sweeps under the crown ribs",
            "ivy_strands": "Falling ivy on the outer spire flanks: hanging stems with alternating diamond leaves, sway metadata",
            "wisteria_racemes": "Hanging racemes under the rib arches with clustered drooping four-sided bell blossoms, dense toward the tip, sway metadata",
            "star_shards": "Five-point star prisms levitating above the crown",
            "float_shards": "Displaced-icosahedron levitating rock chunks; the moving pieces",
            "crystal_inlays": "Hexagonal prism + pyramidal tip clusters ranked by |Chladni F(3,5)| at global field coordinates; crystal_density = artist count control, chladni_threshold = |F| gate"},
        "ue_animation_attributes": {"float_phase": "0..1 phase offset for WPO/Blueprint bobbing",
                                     "float_amp_m": "peak vertical amplitude (m)",
                                     "orbit_radius_m": "peak orbital drift radius (m)",
                                     "spin_rate": "signed turns/sec style spin factor",
                                     "chladni_F": "signed field value at the crystal's global anchor",
                                     "crystal_glow": "0..1 normalized |F| for emissive drive"},
        "files": {"hip": "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip",
                  "fbx": "ue_import/SM_Faraway_AlmostGate_v03_01.fbx",
                  "review_establishing": "review/AlmostGateV3_Establishing.png",
                  "review_approach": "review/AlmostGateV3_Approach.png",
                  "review_crown_detail": "review/AlmostGateV3_CrownDetail.png",
                  "cop_sparkle_texture": "review/CrystalSparkle_COP.png",
                  "bgeo_architecture": "geometry/architecture.bgeo.sc",
                  "bgeo_collision": "geometry/collision.bgeo.sc",
                  "bgeo_anchors": "geometry/anchors.bgeo.sc",
                  "reference": "reference/Aortalis_V2_reference.jpg",
                  "design_note": "DESIGN_NOTE.md"},
        "units_and_frame": {"houdini_units": "metres", "houdini_up_axis": "Y",
                             "output_point_positions": "Houdini P coordinates, yaw applied; not generic vector position attributes",
                             "origin_ue_cm": ORIGIN_UE_CM,
                             "plot_transform": {"houdini_local_to_ue_cm": "(originX + 100*x, originY + 100*z, originZ + 100*y)",
                                                "origin_status": "baseline unchanged; candidate placement not promoted",
                                                "yaw_deg": frame["hda_local_yaw_deg"],
                                                "frame_source": "exact extracted global seam tangent generic native canary; not a live site placement",
                                                "global_field_xz_m": frame["global_field_xz_m"],
                                                "global_chladni": "F(3,5), seed 3900; no local rephase"}},
        "parameter_controls": [{"internal_name": row[0], "label": row[1], "default": (frame["hda_local_yaw_deg"] if row[0] == "yaw_deg" else frame["global_field_xz_m"][0] if row[0] == "global_field_x_m" else frame["global_field_xz_m"][1] if row[0] == "global_field_z_m" else row[3]),
                                "min": row[4], "max": row[5], "group": row[6], "help": row[7]}
                               for row in PARMS],
        "geometry_counts_hashes_bounds": result["geometry"],
        "artifact_hashes": {rel: sha256(out / rel) for rel in (
            "hda/HDA_Faraway_AlmostGate_v03.hda",
            "hip/Faraway_The_Almost_Gate_V3_ArtistCanary.hip",
            "ue_import/SM_Faraway_AlmostGate_v03_01.fbx",
            "review/AlmostGateV3_Establishing.png", "review/AlmostGateV3_Approach.png",
            "review/AlmostGateV3_CrownDetail.png", "review/CrystalSparkle_COP.png",
            "geometry/architecture.bgeo.sc", "geometry/collision.bgeo.sc",
            "geometry/anchors.bgeo.sc", "geometry/TerrainSamples_Input0.bgeo.sc",
            "reference/Aortalis_V2_reference.jpg") if (out / rel).exists()},
        "existing_ue_material_paths": MATERIALS,
        "source_dataset_hashes": source_hashes,
        "reference_description": "The Aortalis V2 sheet: asymmetrical monumental rock and silk spires, broken rib arches, crown rosette, lace erosion, pearl/alabaster surfaces; the central mountain aperture stays open.",
        "workflow_research": RESEARCH_NOTES,
        "native_proof": result,
        "ownership": {"native_lane": "Hython offline authoring only", "ue_editor": "main agent owned",
                      "narrative_truth": "existing QuillScript/C++ owner", "heart_gate_asset": "preserved, not edited"},
        "remaining_gates": ["Import/instantiate HDA v03 in UE by the main agent (v02 uasset already proves the plugin path)",
                            "live material-path resolution and appearance",
                            "capsule collision/traversal on real terrain", "final landscape site placement and cathedral reveal",
                            "UE cook, runtime, Quill, ACFU, travel and packaging are not proven by this candidate"],
    }
    (out / "manifest.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    (out / "DESIGN_NOTE.md").write_text(RESEARCH_NOTES, encoding="utf-8")


def check_env():
    import hou
    if hou.applicationVersionString() != "22.0.368":
        raise RuntimeError("Expected the locked Houdini 22.0.368 build; got " + hou.applicationVersionString())
    if "apprentice" in str(hou.licenseCategory()).lower():
        raise RuntimeError("Refusing to author an Apprentice HDA.")


import time as _time
_T0 = _time.time()


def log(msg):
    print("[v3 %6.1fs] %s" % (_time.time() - _T0, msg), flush=True)


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--fresh":
        fresh_process(sys.argv[2]); return
    if len(sys.argv) >= 3 and sys.argv[1] == "--cop":
        step_cop(sys.argv[2]); return
    if len(sys.argv) >= 4 and sys.argv[1] == "--render":
        step_render(sys.argv[2], sys.argv[3]); return
    if len(sys.argv) >= 3 and sys.argv[1] == "--fbx":
        step_fbx(sys.argv[2]); return
    if len(sys.argv) >= 3 and sys.argv[1] == "--final":
        step_final(sys.argv[2]); return
    check_env()
    if not REFERENCE.exists():
        raise FileNotFoundError("The requested Aortalis V2 image attachment is missing: " + str(REFERENCE))
    frame = get_frame()
    out = candidate_dir()
    out.mkdir(parents=True, exist_ok=False)
    for d in ("hda", "hip", "geometry", "native", "reference", "review", "ue_import"):
        (out / d).mkdir()
    shutil.copy2(REFERENCE, out / "reference/Aortalis_V2_reference.jpg")
    hda, result = native_build(out, frame, stage="a")
    print(json.dumps({"stage_a": "PASS", "candidate_directory": str(out),
                      "hda": str(hda), "gates": result}, indent=2))


if __name__ == "__main__":
    main()
