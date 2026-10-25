"""Read-only comparison of native body mesh ref-pose axes and chain direction."""
from pathlib import Path
import json,math,hashlib
HERE=Path(__file__).resolve().parent
p=HERE/'native_body_tip_reference.json';source=json.loads(p.read_text())
assert source['source_type']=='SkeletalMesh' and source['bone_count']==465
by={b['name']:b for b in source['bones']};rows=[]
for side in ['l','r']:
 for i in range(1,9):
  name=f'c_kilt_{i:02d}_04_{side}';b=by[name];parent=by[b['parent_name']]
  assert parent['name']==f'c_kilt_{i:02d}_03_{side}'
  point=lambda bone:[bone['component']['location'][a] for a in ['x','y','z']]
  delta=[x-y for x,y in zip(point(b),point(parent))];length=math.sqrt(sum(x*x for x in delta));direction=[x/length for x in delta]
  r=b['component']['rotation'];pitch,yaw,roll=[math.radians(r[k]) for k in ['pitch','yaw','roll']]
  cp,sp,cy,sy,cr,sr=math.cos(pitch),math.sin(pitch),math.cos(yaw),math.sin(yaw),math.cos(roll),math.sin(roll)
  axes={'X_Positive':[cp*cy,cp*sy,sp],
        'Y_Positive':[sr*sp*cy-cr*sy,sr*sp*sy+cr*cy,-sr*cp],
        'Z_Positive':[-(cr*sp*cy+sr*sy),cy*sr-cr*sp*sy,cr*cp]}
  for a,v in list(axes.items()):axes[a.replace('Positive','Negative')]=[-x for x in v]
  dots={a:sum(x*y for x,y in zip(v,direction)) for a,v in axes.items()}
  angles={a:math.degrees(math.acos(max(-1,min(1,d)))) for a,d in dots.items()}
  rows.append({'name':name,'parent':parent['name'],'component_head_cm':point(b),'parent_component_head_cm':point(parent),
               'chain_direction':direction,'component_axes':axes,'axis_dot_chain':dots,'axis_angle_degrees':angles,
               'best_axis':max(dots,key=dots.get)})
gates={'all16_resolved':len(rows)==16,'all16_native_minus_y_align':all(r['best_axis']=='Y_Negative' and r['axis_dot_chain']['Y_Negative']>.999 for r in rows),
       'current_native_x_is_transverse':all(abs(r['axis_dot_chain']['X_Positive'])<.01 for r in rows)}
report={'schema':'melodia.native_skirt_axis.v1','asset_path':source['asset_path'],'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'source_api':'animation.get_bone_ref_pose / USkeletalMesh.GetRefSkeleton',
 'rotation_formula':'UE FRotationMatrix component rotator; row axes; unit scale axis directions',
 'production_baseline_axis':'X_Positive','measured_terminal_axis':'Y_Negative','gates':gates,'passed':all(gates.values()),
 'native_x_angle_range_degrees':[min(r['axis_angle_degrees']['X_Positive'] for r in rows),max(r['axis_angle_degrees']['X_Positive'] for r in rows)],
 'native_minus_y_angle_max_degrees':max(r['axis_angle_degrees']['Y_Negative'] for r in rows),
 'scope':'native mesh reference pose only; no runtime dynamics or property mutation certified','terminals':rows}
(HERE/'native_tip_axis_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='terminals'},indent=2))
assert report['passed'],gates
