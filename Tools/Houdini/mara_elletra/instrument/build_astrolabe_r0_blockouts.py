#!/usr/bin/env python3
"""Emit coarse Resonance Astrolabe R0 OBJ blockouts from the tracked candidate manifest.

This is deliberately NOT an HDA and NOT final geometry. It exists only to make the
Issue #42 R0 silhouette gate physically testable in Houdini/Blender/UE before detail work.
OBJ coordinates are authored in centimeters.

Examples:
  python Tools/Houdini/mara_elletra/instrument/build_astrolabe_r0_blockouts.py --check
  python Tools/Houdini/mara_elletra/instrument/build_astrolabe_r0_blockouts.py --emit
"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = ROOT / "Docs/Production/Evidence/ResonanceAstrolabe/R0/astrolabe_silhouette_candidates.v1.json"
DEFAULT_OUTPUT = ROOT / "_staging/resonance_astrolabe_r0"

def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "melodia.resonance-astrolabe-r0-candidates.v1":
        raise ValueError("Unexpected manifest schema.")
    candidates = data.get("candidates", [])
    if not 6 <= len(candidates) <= 12:
        raise ValueError(f"R0 requires 6-12 candidates, got {len(candidates)}.")
    ids = [c["id"] for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate IDs must be unique.")
    for c in candidates:
        if c["overall_length_cm"] <= 0 or c["head_width_cm"] <= 0:
            raise ValueError(f"{c['id']}: non-positive authored dimensions.")
        if not 0 < c["head_center_cm_from_base"] < c["overall_length_cm"]:
            raise ValueError(f"{c['id']}: head center must lie inside overall length.")
        if c["ring_count"] != len(c["ring_scale"]) or c["ring_count"] != len(c["ring_tilt_deg"]):
            raise ValueError(f"{c['id']}: ring arrays do not match ring_count.")
    return data

class Obj:
    def __init__(self) -> None:
        self.v = []
        self.f = []
        self.groups = []

    def add_box(self, name, center, size):
        cx,cy,cz=center; sx,sy,sz=(s/2 for s in size)
        pts=[
            (cx-sx,cy-sy,cz-sz),(cx+sx,cy-sy,cz-sz),(cx+sx,cy+sy,cz-sz),(cx-sx,cy+sy,cz-sz),
            (cx-sx,cy-sy,cz+sz),(cx+sx,cy-sy,cz+sz),(cx+sx,cy+sy,cz+sz),(cx-sx,cy+sy,cz+sz)
        ]
        base=len(self.v)
        self.v.extend(pts)
        faces=[(1,2,3,4),(5,8,7,6),(1,5,6,2),(2,6,7,3),(3,7,8,4),(5,1,4,8)]
        self.groups.append((name, len(self.f)))
        self.f.extend(tuple(base+i for i in q) for q in faces)

    def add_torus(self, name, center, major_r, minor_r=1.35, tilt_deg=0.0, arc_deg=360.0, seg=32, tube=8):
        cx,cy,cz=center
        arc=math.radians(arc_deg)
        closed = arc_deg >= 359.9
        u_count=seg if closed else seg+1
        base=len(self.v)
        tilt=math.radians(tilt_deg)
        for i in range(u_count):
            u=arc*(i/(seg if not closed else seg))
            for j in range(tube):
                vv=2*math.pi*j/tube
                x=(major_r+minor_r*math.cos(vv))*math.cos(u)
                y=minor_r*math.sin(vv)
                z=(major_r+minor_r*math.cos(vv))*math.sin(u)
                yt=y*math.cos(tilt)-z*math.sin(tilt)
                zt=y*math.sin(tilt)+z*math.cos(tilt)
                self.v.append((cx+x,cy+yt,cz+zt))
        self.groups.append((name, len(self.f)))
        for i in range(seg):
            ni=(i+1)%u_count
            if not closed and i+1>=u_count:
                break
            for j in range(tube):
                nj=(j+1)%tube
                a=base+i*tube+j+1
                b=base+ni*tube+j+1
                c=base+ni*tube+nj+1
                d=base+i*tube+nj+1
                self.f.append((a,b,c,d))

    def add_spoke(self, name, center, radius, angle_deg, thickness=1.1):
        a=math.radians(angle_deg)
        cx,cy,cz=center
        x1=cx-math.cos(a)*radius; z1=cz-math.sin(a)*radius
        x2=cx+math.cos(a)*radius; z2=cz+math.sin(a)*radius
        mx=(x1+x2)/2; mz=(z1+z2)/2
        length=math.hypot(x2-x1,z2-z1)
        if abs(math.cos(a)) >= abs(math.sin(a)):
            self.add_box(name,(mx,cy,mz),(length,thickness,thickness))
        else:
            self.add_box(name,(mx,cy,mz),(thickness,thickness,length))

    def write(self, path: Path, header: str):
        lines=[f"# {header}","# Units: centimeters"]
        group_map={}
        for name, face_start in self.groups:
            group_map.setdefault(face_start, []).append(name)
        for p in self.v:
            lines.append(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}")
        for fi,face in enumerate(self.f):
            if fi in group_map:
                lines.append("g " + "_".join(group_map[fi]))
            lines.append("f " + " ".join(str(i) for i in face))
        path.write_text("\n".join(lines)+"\n",encoding="utf-8")

def build_candidate(c: dict) -> Obj:
    obj=Obj()
    L=float(c["overall_length_cm"])
    head=float(c["head_width_cm"])
    zc=float(c["head_center_cm_from_base"])
    R=head/2
    shaft_top=max(30.0, zc-R*0.72)
    obj.add_box("grip_and_shaft",(0,0,shaft_top/2),(3.4,3.0,shaft_top))
    obj.add_box("grip_collar",(0,0,34),(8.5,4.0,3.8))

    arc=360.0
    if c["id"]=="AST_R0_04_HANGING_SEXTANT": arc=235.0
    if c["id"]=="AST_R0_08_BROKEN_HALO": arc=300.0

    for i,(scale,tilt) in enumerate(zip(c["ring_scale"],c["ring_tilt_deg"])):
        dx=(float(c["asymmetry_offset_cm"]) if i==0 else 0.0)
        obj.add_torus(f"ring_{i:02d}",(dx,0,zc),R*float(scale),
                      minor_r=max(1.0,head*0.035),tilt_deg=float(tilt),
                      arc_deg=arc if i==0 else 360.0)

    obj.add_torus("resonator",(float(c["asymmetry_offset_cm"])*0.25,0,zc),
                  R*0.22,minor_r=max(0.9,head*0.028),tilt_deg=15)

    pid=c["id"]
    if pid=="AST_R0_02_SPLIT_ORRERY":
        obj.add_torus("side_lens",(R*0.9,0,zc+R*0.1),R*0.18,minor_r=1.0,tilt_deg=-20)
    elif pid=="AST_R0_03_EYE_COMPASS":
        obj.add_spoke("eye_axis",(0,0,zc),R*0.88,0,1.5)
        obj.add_torus("side_lens",(R*0.88,0,zc),R*0.17,minor_r=1.1,tilt_deg=0)
    elif pid=="AST_R0_04_HANGING_SEXTANT":
        obj.add_spoke("quadrant_arm",(0,0,zc),R*0.78,35,1.6)
    elif pid=="AST_R0_05_TIDAL_QUADRANT":
        obj.add_box("asym_lobe",(-R*0.48,0,zc-R*1.08),(R*0.55,4.0,R*0.72))
    elif pid=="AST_R0_06_ROSE_WINDOW":
        for ang in (0,45,90,135):
            obj.add_spoke(f"rose_spoke_{ang}",(0,0,zc),R*0.92,ang,1.15)
    elif pid=="AST_R0_07_ORBIT_CAGE":
        obj.add_spoke("cage_axis_a",(0,0,zc),R*0.92,55,1.0)
        obj.add_spoke("cage_axis_b",(0,0,zc),R*0.92,125,1.0)
    elif pid=="AST_R0_08_BROKEN_HALO":
        obj.add_torus("side_lens",(R*0.92,0,zc+R*0.08),R*0.17,minor_r=1.0,tilt_deg=-15)

    pendx=float(c["pendulum_offset_cm"])
    pendz=max(shaft_top+6,zc-R-14)
    obj.add_box("pendulum",(pendx,0,pendz),(3.4,3.4,16))
    obj.add_box("top_registration",(0,0,L-1.0),(2.0,2.0,2.0))
    return obj

def emit(data: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True,exist_ok=True)
    for c in data["candidates"]:
        obj=build_candidate(c)
        path=out_dir/(c["id"]+".obj")
        obj.write(path,f"{c['id']} — {c['name']} — Issue #42 R0 blockout")
        print(path)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST)
    ap.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    ap.add_argument("--check",action="store_true",help="Validate manifest and exit.")
    ap.add_argument("--emit",action="store_true",help="Emit eight coarse OBJ blockouts.")
    args=ap.parse_args()
    data=load_manifest(args.manifest)
    print(f"OK: {len(data['candidates'])} R0 candidates; schema={data['schema']}")
    if args.emit:
        emit(data,args.output)
    if not args.check and not args.emit:
        ap.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
