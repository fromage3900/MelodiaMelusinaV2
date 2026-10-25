"""Exact KineFX hierarchy/matrix check for the assigned FBX exports."""
import json
from pathlib import Path
import hou
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
results=[]
for filename in ['SK_Melusina_V2_Body.fbx','SK_Melusina_V2_Boots.fbx','SK_Melusina_V2_Skirt_R2_SmoothChains.fbx']:
    hou.hipFile.clear(suppress_save_prompt=True)
    g=hou.node('/obj').createNode('geo','audit')
    n=g.createNode('kinefx::fbxcharacterimport','fbx_in')
    n.parm('fbxfile').set((ROOT/'SourceExports'/filename).as_posix());n.parm('convertunits').set(1)
    skel=n.geometry(1)
    names=[p.attribValue('name') for p in skel.points()]
    parents={name:None for name in names}
    for prim in skel.prims():
        ids=[v.point().number() for v in prim.vertices()]
        for a,b in zip(ids,ids[1:]): parents[names[b]]=names[a]
    rows={p.attribValue('name'):{'p':list(p.position()),'parent':parents[p.attribValue('name')],
                               'transform':list(p.attribValue('transform'))} for p in skel.points()}
    results.append({'file':filename,'joints':rows,'rest_point_attributes':[a.name() for a in skel.pointAttribs()],
                    'skin_capture_attributes':[a.name() for a in n.geometry(0).pointAttribs()]})
(OUT/'skeleton_hierarchy.json').write_text(json.dumps(results,indent=1),encoding='utf-8')
print('WROTE',OUT/'skeleton_hierarchy.json')
