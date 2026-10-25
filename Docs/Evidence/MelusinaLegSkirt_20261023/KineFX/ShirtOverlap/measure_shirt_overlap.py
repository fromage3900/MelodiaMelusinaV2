"""Exact unsigned shirt/skirt bind distance; no geometry, skin or UE edits.

The centroid search is conservatively bounded by nearest-vertex distance plus
the largest triangle radius. It therefore includes every possible closer face.
Radial direction is an art-direction diagnostic, not a signed solid distance.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial import cKDTree
from trimesh.triangles import closest_point

HERE=Path(__file__).resolve().parent
KIN=HERE.parent
AUDIT=KIN.parent

def read(path):
    return json.loads(path.read_text())

def main():
    sf=HERE/'SK_Melusina_V2_Shirt_Flared_data.json'
    kf=KIN/'SK_Melusina_V2_Skirt_R2_SmoothChains_data.json'
    shirt,skirt=read(sf),read(kf)
    p=np.asarray(shirt['positions_m']);v=np.asarray(skirt['positions_m'])
    faces=np.asarray(skirt['primitive_ids']);assert faces.shape[1]==3
    tris=v[faces];centres=tris.mean(axis=1)
    min_y=tris[:,:,1].min(axis=1);max_y=tris[:,:,1].max(axis=1)
    max_radius=float(np.linalg.norm(tris-centres[:,None,:],axis=2).max())
    tree=cKDTree(centres);vert_tree=cKDTree(v)
    kilt=np.array([sum(w for n,w in ws if n.startswith('c_kilt_')) for ws in shirt['weights']])
    thigh=np.array([sum(w for n,w in ws if n.startswith('thigh_')) for ws in shirt['weights']])
    ids=np.flatnonzero(kilt>.01)
    centre=np.asarray(shirt['joints_m']['c_root_master_x'])[[0,2]]
    measurements=[]
    for i in ids:
        point=p[i];upper=float(vert_tree.query(point)[0])
        candidates=np.asarray(tree.query_ball_point(point,upper+max_radius+1e-9),dtype=int)
        assert len(candidates)
        nearest=closest_point(tris[candidates],np.repeat(point[None,:],len(candidates),axis=0))
        distances=np.linalg.norm(nearest-point,axis=1);j=int(distances.argmin());near=nearest[j]
        radial=point[[0,2]]-centre;radial/=np.linalg.norm(radial)
        # A horizontal ray measures actual ordering at the same height. Unlike
        # nearest-point direction, this does not confuse sloping cloth with an
        # inside/outside relation. Open/gapped sections can have no intersection.
        section=np.flatnonzero((min_y<=point[1])&(max_y>=point[1]))
        origin=np.array([centre[0],point[1],centre[1]])
        direction=np.array([radial[0],0.,radial[1]])
        ts=tris[section];e1=ts[:,1]-ts[:,0];e2=ts[:,2]-ts[:,0]
        h=np.cross(np.broadcast_to(direction,e2.shape),e2)
        det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-12
        inv=np.zeros_like(det);inv[valid]=1/det[valid]
        delta=origin-ts[:,0];u=inv*np.einsum('ij,ij->i',delta,h)
        q=np.cross(delta,e1);vv=inv*(q@direction)
        t=inv*np.einsum('ij,ij->i',e2,q)
        valid&=(u>=-1e-9)&(vv>=-1e-9)&(u+vv<=1+1e-9)&(t>=0)
        radial_clearance=None;outer=None
        if valid.any():
            outer=float(t[valid].max())
            radial_clearance=float((np.linalg.norm(point[[0,2]]-centre)-outer)*100)
        measurements.append({'shirt_point':int(i),'position_m':point.tolist(),
            'nearest_skirt_point_m':near.tolist(),'nearest_skirt_triangle':int(candidates[j]),
            'unsigned_distance_cm':float(distances[j]*100),
            'radial_difference_cm':float(np.dot((point-near)[[0,2]],radial)*100),
            'vertical_difference_cm':float((point[1]-near[1])*100),
            'same_height_ray_intersections':int(valid.sum()),
            'outermost_skirt_ray_radius_cm':outer*100 if outer is not None else None,
            'same_height_radial_clearance_cm':radial_clearance,
            'kilt_weight':float(kilt[i]),'thigh_weight':float(thigh[i]),
            'candidate_triangles':len(candidates)})
    # Independent brute-force spot checks falsify search-bound/index mistakes.
    spot=[]
    for row in measurements[::max(1,len(measurements)//8)]:
        point=np.asarray(row['position_m'])
        cp=closest_point(tris,np.repeat(point[None,:],len(tris),axis=0))
        distance=float(np.linalg.norm(cp-point,axis=1).min()*100)
        delta=abs(distance-row['unsigned_distance_cm']);assert delta<1e-8
        spot.append({'shirt_point':row['shirt_point'],'brute_force_distance_cm':distance,'delta_cm':delta})
    matched=[r for r in measurements if abs(r['vertical_difference_cm'])<=.5]
    below=[r for r in matched if r['radial_difference_cm']<0]
    sections=[r for r in measurements if r['same_height_radial_clearance_cm'] is not None]
    report={'schema':'melodia.shirt_skirt_bind_overlap.v1','proof':'KineFX bind/source geometry only; not P0 motion or cloth collision',
        'input_hashes':{str(f.relative_to(AUDIT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [sf,kf,AUDIT/'SourceExports/SK_Melusina_V2_Shirt_Flared.fbx']},
        'shirt_points':len(p),'skeleton_joints':len(shirt['joints_m']),
        'shirt_kilt_weight_over_1pct':int((kilt>.01).sum()),'shirt_thigh_weight_over_1pct':int((thigh>.01).sum()),
        'existing_kilt_bones':sorted({n for ws in shirt['weights'] for n,w in ws if n.startswith('c_kilt_') and w>1e-6}),
        'max_triangle_radius_cm':max_radius*100,'measurements':measurements,'brute_force_spot_checks':spot,
        'summary':{'unsigned_distance_cm':dict(zip(['min','p05','median','p95','max'],np.quantile([r['unsigned_distance_cm'] for r in measurements],[0,.05,.5,.95,1]).tolist())),
            'near_same_height_points':len(matched),'radially_inside_of_nearest_surface':len(below),
            'radially_inside_point_ids':[r['shirt_point'] for r in below],
            'same_height_ray_points':len(sections),
            'same_height_radial_clearance_cm':dict(zip(['min','p05','median','p95','max'],np.quantile([r['same_height_radial_clearance_cm'] for r in sections],[0,.05,.5,.95,1]).tolist())),
            'same_height_under_surface_point_ids':[r['shirt_point'] for r in sections if r['same_height_radial_clearance_cm']<0]},
        'limitations':['Unsigned distance cannot establish inside/outside a layered open garment.',
            'Radial difference is relative to the trunk centre and nearest skirt surface; it is not signed collision clearance.',
            'Bind clearance does not prove motion clearance or justify stripping existing kilt/thigh influences.',
            'First-ring positions, rotations and skinned surfaces must be checked in House P0.'],
        'source_geometry_or_weights_changed':False}
    (HERE/'shirt_skirt_overlap.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['shirt_points','shirt_kilt_weight_over_1pct','shirt_thigh_weight_over_1pct','summary']},indent=2))

if __name__=='__main__':main()
