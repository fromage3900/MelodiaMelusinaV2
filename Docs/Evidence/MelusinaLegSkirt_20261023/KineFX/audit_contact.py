"""Bounded offline geometry/skin contact audit; reuses shirt_legal KineFX import."""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
import hou

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FILES = [ROOT / 'SourceExports' / n for n in (
    'SK_Melusina_V2_Body.fbx', 'SK_Melusina_V2_Boots.fbx',
    'SK_Melusina_V2_Skirt_R2_SmoothChains.fbx')]

def bounds(pts):
    return {'min': [round(min(p[a] for p in pts), 8) for a in range(3)],
            'max': [round(max(p[a] for p in pts), 8) for a in range(3)]} if pts else None

def main():
    result = {'schema':'melodia.leg_skirt_offline_contact.v1',
              'units':'KineFX convertunits=1, metres', 'houdini':hou.applicationVersionString(),
              'files':[]}
    for path in FILES:
        hou.hipFile.clear(suppress_save_prompt=True)
        obj = hou.node('/obj').createNode('geo', 'contact_audit')
        imp = obj.createNode('kinefx::fbxcharacterimport','fbx_in')
        imp.parm('fbxfile').set(path.as_posix())
        imp.parm('convertunits').set(1)
        skin, rest = imp.geometry(0), imp.geometry(1)
        names = [str(p.attribValue('name')) for p in rest.points()]
        positions = [list(p.position()) for p in skin.points()]
        joints = {str(p.attribValue('name')):list(p.position()) for p in rest.points()}
        region_paths = skin.stringListAttribValue('boneCapture_pCaptPath') if skin.findGlobalAttrib('boneCapture_pCaptPath') else []
        # Capture indices map to region paths, not necessarily skeleton point order.
        capture_names = [p.rsplit('/',1)[-1] for p in region_paths] if region_paths else names
        weights = []
        for p in skin.points():
            raw = p.attribValue('boneCapture')
            weights.append([(capture_names[int(raw[i])],float(raw[i+1]))
                            for i in range(0,len(raw)-1,2) if raw[i+1] > 1e-6 and raw[i] >= 0])
        prim_attrs = [a.name() for a in skin.primAttribs()]
        attr_counts = {}
        for n in ('name','path','shop_materialpath','material','fbx_material_name'):
            if n in prim_attrs:
                attr_counts[n] = dict(collections.Counter(str(p.attribValue(n)) for p in skin.prims()))
        # Pure topology components, including outlines as separate islands.
        parent = list(range(len(positions)))
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        def union(a,b):
            a,b = find(a),find(b)
            if a != b: parent[b] = a
        for prim in skin.prims():
            ids = [v.point().number() for v in prim.vertices()]
            for v in ids[1:]: union(ids[0],v)
        islands = collections.defaultdict(list)
        for i in range(len(positions)): islands[find(i)].append(i)
        groups = []
        for ids in islands.values():
            tally = collections.Counter()
            for i in ids:
                for n,w in weights[i]: tally[n] += w
            groups.append({'point_count':len(ids),'bounds_m':bounds([positions[i] for i in ids]),
                'sample_ids':ids[:3], 'top_influence_sum':tally.most_common(12)})
        groups.sort(key=lambda x:x['point_count'],reverse=True)
        f = {'path':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'points':len(positions),'primitives':len(skin.prims()),'joints':len(names),
             'point_attributes':[a.name() for a in skin.pointAttribs()],
             'primitive_attributes':prim_attrs,'detail_attributes':[a.name() for a in skin.globalAttribs()],
             'primitive_categories':attr_counts,'bounds_m':bounds(positions),
             'capture_path_count':len(region_paths),'capture_index_is_rest_index':capture_names == names,
             'unweighted_points':sum(not w for w in weights),'weight_sum_bad_points':sum(abs(sum(v for _,v in w)-1)>0.001 for w in weights),
             'joints_m':joints,'island_count':len(groups),'islands':groups}
        data={'positions_m':positions,'weights':weights,'joints_m':joints,'primitive_ids':[[v.point().number() for v in p.vertices()] for p in skin.prims()]}
        (OUT / (path.stem + '_data.json')).write_text(json.dumps(data),encoding='utf-8')
        result['files'].append(f)
        print(path.name,len(positions),'points',len(names),'bones',len(groups),'islands',flush=True)
    (OUT/'contact_geometry.json').write_text(json.dumps(result,indent=1),encoding='utf-8')
    print('WROTE',OUT/'contact_geometry.json',flush=True)

if __name__ == '__main__': main()
