"""Native geometry acceptance for explicit room doors; does not claim UE capsule proof."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import hou

FIXTURE = dict(room_w=15.36, room_d=11.52, room_h=7.2, wall_t=.24, panel_w=3.6,
               seed=2, decor=3, interlock=0, door_wall=3, door_w=1.8, door_h=3.2,
               engine_y_up=0, engine_flip=0)


def snapshot(node):
    node.cook(force=True)
    if node.errors():
        raise RuntimeError(str(node.errors()))
    geo = node.geometry()
    collision = geo.findPrimGroup('collision_geo_simple_box_main_geo')
    render_group = geo.findPrimGroup('rendered_main_geo')
    rendered_group_prims=len(render_group.prims()) if render_group else None
    collision_info = None
    if collision:
        vertices=[tuple(v.point().position()) for p in collision.prims() for v in p.vertices()]
        collision_info=dict(prims=len(collision.prims()),
                            bounds=[[min(p[i] for p in vertices) for i in range(3)],
                                    [max(p[i] for p in vertices) for i in range(3)]])
        render=hou.Geometry();render.merge(geo)
        render.deletePrims(render.findPrimGroup(collision.name()).prims(), False)
        geo=render
    payload = json.loads(geo.attribValue("sockets_json"))
    digest = hashlib.sha256()
    digest.update(repr(geo.pointFloatAttribValues("P")).encode())
    digest.update(repr(geo.vertexFloatAttribValues("uv")).encode())
    digest.update(repr([[v.point().number() for v in p.vertices()] for p in geo.prims()]).encode())
    return dict(points=len(geo.points()), prims=len(geo.prims()),
                bbox=[list(geo.boundingBox().minvec()), list(geo.boundingBox().maxvec())],
                vertex_attributes=[a.name() for a in geo.vertexAttribs()],
                geometry_sha256=digest.hexdigest(), sockets=payload,
                gate=json.loads(geo.attribValue("gate_json")), floor_collision=collision_info,
                rendered_group_prims=rendered_group_prims,
                errors=list(node.errors()), warnings=list(node.warnings()))


def portal_rays(node, record):
    """Finite transverse segments sample the full rendered portal aperture.

    These hit all geometry roles, not just plaster; their length spans exterior
    wall plus interior trim. They are geometric rays, NOT a pawn/capsule sweep.
    """
    g = node.geometry(); wall = record['wall']; width = record['width']; height = record['height']; center = record['s']
    W, D = node.evalParm('room_w'), node.evalParm('room_d')
    blocked = []
    for i in range(7):
        s = center + (i/6-.5)*(width-.16)
        for j in range(6):
            z = .08+j/5*(height-.16)
            a = {'S':(s,-.40,z),'N':(s,D+.40,z),'W':(-.40,s,z),'E':(W+.40,s,z)}[wall]
            d = {'S':(0.,1.,0.),'N':(0.,-1.,0.),'W':(1.,0.,0.),'E':(-1.,0.,0.)}[wall]
            pos, normal, uvw = hou.Vector3(), hou.Vector3(), hou.Vector3()
            hit = g.intersect(hou.Vector3(a), hou.Vector3(d), pos, normal, uvw, max_hit=.8)
            if hit >= 0:blocked.append(dict(s=s,z=z,primitive=hit,role=g.prim(hit).attribValue('material_role')))
    return dict(samples=42,blocked=blocked,pass_clear=not blocked)


def main(source, candidate, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    original_sha=hashlib.sha256(Path(source).read_bytes()).hexdigest()
    for path in (source,candidate):hou.hda.installFile(path)
    parent=hou.node('/obj').createNode('geo','room_explicit_verification');parent.deleteItems(parent.children())
    old=parent.createNode('melodia::room_shell','legacy')
    candidate_type=next(d.nodeTypeName() for d in hou.hda.definitionsInFile(candidate)
                        if d.nodeTypeName() in ('melodia::room_shell_explicit::1.0','melodia::room_shell_contact::1.0'))
    new=parent.createNode(candidate_type,'candidate')
    report=dict(version=hou.applicationVersionString(),license=str(hou.licenseCategory()),
                source_hda=source,source_sha256=original_sha,candidate_hda=candidate,
                candidate_sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),checks={})
    report['default_legacy']=snapshot(old);report['default_candidate']=snapshot(new)
    report['checks']['default_geometry_identical']=report['default_legacy']['geometry_sha256']==report['default_candidate']['geometry_sha256']
    for n in (old,new):
        for k,v in FIXTURE.items():n.parm(k).set(v)
    a,b=snapshot(old),snapshot(new)
    report['legacy_fixture']=a;report['candidate_legacy_fixture']=b
    report['checks']['legacy_fixture_identical']=a['geometry_sha256']==b['geometry_sha256'] and a['bbox']==b['bbox']
    if new.parm('simple_floor_collision') and new.evalParm('simple_floor_collision'):
        collision=b['floor_collision']
        expected=[[-FIXTURE['wall_t'],-FIXTURE['wall_t'],-.2],
                  [FIXTURE['room_w']+FIXTURE['wall_t'],FIXTURE['room_d']+FIXTURE['wall_t'],0.]]
        report['checks']['simple_floor_six_faces']=bool(collision) and collision['prims']==6
        report['checks']['explicit_render_group_matches_main_mesh']=b['rendered_group_prims']==b['prims']
        report['checks']['simple_floor_matches_rendered_slab']=bool(collision) and all(
            abs(collision['bounds'][j][i]-expected[j][i])<1e-5 for j in range(2) for i in range(3))
        new.parm('engine_y_up').set(1)
        transformed=snapshot(new)['floor_collision']
        report['engine_y_up_floor_collision']=transformed
        report['checks']['simple_floor_engine_up_axis']=all(
            abs(transformed['bounds'][j][i]-v)<1e-5
            for j,row in enumerate([[-FIXTURE['wall_t'],-.2,-(FIXTURE['room_d']+FIXTURE['wall_t'])],
                                    [FIXTURE['room_w']+FIXTURE['wall_t'],0.,FIXTURE['wall_t']]])
            for i,v in enumerate(row))
        new.parm('engine_y_up').set(0)
    old.parm('room_w').set(16.8);wide=snapshot(old);report['legacy_wide']=wide
    center=lambda q:(q['s0']+q['s1'])/2
    report['legacy_hazard_move_m']=center(wide['sockets']['door'])-center(a['sockets']['door'])
    report['checks']['legacy_hazard_reproduced']=abs(report['legacy_hazard_move_m']-3.84)<1e-6
    doors=[dict(id='salon_entry',wall='W',s=5.76,width=1.8,height=3.2),dict(id='salon_front',wall='S',s=7.68,width=2.4,height=3.2)]
    new.parm('openings_json').set(json.dumps(doors));report['explicit_variants']=[]
    for w in (15.36,16.8):
        new.parm('room_w').set(w);snap=snapshot(new);rays={q['id']:portal_rays(new,q) for q in doors}
        snap.update(room_w=w,aperture_rays=rays);report['explicit_variants'].append(snap)
    first,second=report['explicit_variants']
    report['checks']['explicit_two_real_clear_portals']=all(q['pass_clear'] for snap in (first,second) for q in snap['aperture_rays'].values())
    report['checks']['stable_named_socket_frames']=first['sockets']['opening_sockets']==second['sockets']['opening_sockets']
    report['checks']['explicit_gate_pass']=all(q['gate']['all_pass'] for q in (first,second))
    # Same-wall seam-crossing pair verifies both cuts rather than metadata-only exits.
    same=[dict(id='west_a',wall='W',s=3.84,width=1.8,height=3.2),dict(id='west_b',wall='W',s=8.4,width=1.8,height=3.2)]
    new.parm('openings_json').set(json.dumps(same));report['same_wall']=snapshot(new)
    report['same_wall']['aperture_rays']={q['id']:portal_rays(new,q) for q in same}
    report['checks']['same_wall_seam_crossing_clear']=all(q['pass_clear'] for q in report['same_wall']['aperture_rays'].values())
    import room_shell
    invalid=[None,{},[dict(doors[0],s=-1)],[dict(doors[0],height=8)],[dict(doors[0],width=0)],
             [dict(doors[0],wall='Q')],[dict(doors[0],s=float('nan'))],[doors[0],doors[0]],
             [doors[0],dict(doors[0],id='overlap',s=6)]]
    rejected=[]
    for records in invalid:
        try:room_shell.validate_openings(records,15.36,11.52,7.2)
        except ValueError as exc:rejected.append(str(exc))
    report['invalid_rejections']=rejected;report['checks']['invalid_apertures_rejected']=len(rejected)==len(invalid)
    new.parm('openings_json').set('[{"id":"bad","wall":"W","s":-1,"width":1.8,"height":3.2}]')
    try:new.cook(force=True)
    except hou.OperationFailed:pass
    report['invalid_hda_errors']=list(new.errors());report['checks']['invalid_hda_cook_rejected']=bool(new.errors())
    report['checks']['canonical_hda_unchanged']=original_sha==hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report['all_pass']=all(report['checks'].values())
    report['limits']='Native rendered-geometry ray samples only. UE capsule sweep, actor integration, live look and packaged route remain pending.'
    (out/'room_shell_explicit_verify.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(checks=report['checks'],all_pass=report['all_pass'],legacy_move_m=report['legacy_hazard_move_m'],evidence=str(out/'room_shell_explicit_verify.json')),indent=2))
    return 0 if report['all_pass'] else 1


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-hda',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    sys.exit(main(a.source_hda,a.candidate,a.out))
