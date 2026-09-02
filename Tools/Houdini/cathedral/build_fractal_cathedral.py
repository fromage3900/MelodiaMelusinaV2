"""P4 Fractal Cathedral — Houdini (hython 22.0.368) mesh forge."""
import argparse, json, math
from pathlib import Path
import numpy as np
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "cathedral"
SEED = 20260901

def build_fractal_arch_profile(span, height, depth, tracery):
    pts=[]
    half=span*0.5
    segments=16*(depth+1)
    for i in range(segments+1):
        t=i/segments
        x=-half+t*span
        base=1-pow(abs(x)/half,1.5+depth*0.15) if half>0 else 0
        y=base*height
        wobble=math.cos(8*math.pi*t)*math.cos(6*math.pi*(y/max(height,1)))*tracery*0.08*height
        y+=wobble
        if depth>0 and 0.4<t<0.6:
            sub_h=height*0.35
            sub_x=(t-0.5)/0.1
            sub_y=sub_h*(1-abs(sub_x))*0.5
            y+=sub_y*(depth/3.0)
        pts.append((x,y))
    return pts

def build_nave_mesh(span=6.0,height=12.0,depth=3,tracery=0.6,bays=4):
    verts=[];faces=[];uvs=[]
    bay_len=span*0.75
    nave_len=bay_len*bays
    arch=build_fractal_arch_profile(span,height,depth,tracery)
    arch_n=len(arch)
    base_vert=0
    for bay in range(bays):
        y0=bay*bay_len
        y1=(bay+1)*bay_len
        base=base_vert
        for (x,z) in arch:
            verts.append((x,y0,z)); uvs.append(((x+span*0.5)/span if span>0 else 0, bay/bays))
            verts.append((x,y1,z)); uvs.append(((x+span*0.5)/span if span>0 else 0, (bay+1)/bays))
        for i in range(arch_n-1):
            v0=base+i*2; v1=base+i*2+1; v2=base+(i+1)*2+1; v3=base+(i+1)*2
            faces.append((v0,v1,v2,v3))
        base_vert+=arch_n*2
    fi=len(verts)
    floor_x0=-span*0.5; floor_x1=span*0.5
    verts.extend([(floor_x0,0,0),(floor_x1,0,0),(floor_x1,nave_len,0),(floor_x0,nave_len,0)])
    uvs.extend([(0,0),(1,0),(1,1),(0,1)])
    faces.append((fi,fi+1,fi+2,fi+3))
    rib_w=0.12; apex_z=height
    for bay in range(bays):
        y0=bay*bay_len; y1=(bay+1)*bay_len
        for (x0,ys,x1,ye) in [(-span*0.5,y0,span*0.5,y1),(span*0.5,y0,-span*0.5,y1)]:
            ri=len(verts)
            verts.extend([(x0,ys,apex_z-rib_w),(x0+rib_w,ys,apex_z),(x1+rib_w,ye,apex_z),(x1,ye,apex_z-rib_w)])
            uvs.extend([(0,0),(1,0),(1,1),(0,1)])
            faces.append((ri,ri+1,ri+2,ri+3))
    return np.array(verts,dtype="float32"),faces,np.array(uvs,dtype="float32")

def build_rose_window(span,tracery):
    verts=[(0,0,0)]; uvs=[(0.5,0.5)]; faces=[]
    radius=span*0.42; res=64
    for r in range(1,res//2):
        rad=radius*r/(res//2)
        ring_n=max(8,int(2*math.pi*rad/(radius/8)))
        for a in range(ring_n):
            ang=2*math.pi*a/ring_n
            x=math.cos(ang)*rad; y=math.sin(ang)*rad
            n,m=8,6
            cx=math.cos(n*math.pi*(x/radius*0.5+0.5))*math.cos(m*math.pi*(y/radius*0.5+0.5))
            cy=math.cos(m*math.pi*(x/radius*0.5+0.5))*math.cos(n*math.pi*(y/radius*0.5+0.5))
            tracery_h=(cx-cy)*0.15*radius*tracery
            verts.append((x,y,tracery_h)); uvs.append((x/radius*0.5+0.5,y/radius*0.5+0.5))
    outer_n=int(2*math.pi*radius/(radius/8))
    idx0=len(verts)-outer_n
    for i in range(outer_n):
        a=0; b=idx0+i; c=idx0+((i+1)%outer_n)
        if b < len(verts) and c < len(verts):
            faces.append((a,b,c))
    return np.array(verts,dtype="float32"),faces,np.array(uvs,dtype="float32")

def write_obj(path,verts,faces,uvs=None):
    path=Path(path)
    with open(path,"w") as f:
        f.write(f"# Fractal Cathedral hython {SEED} {path.name}\n")
        for v in verts: f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        if uvs is not None:
            for uv in uvs: f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")
        for face in faces:
            if len(face)==4: f.write(f"f {face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1} {face[3]+1}/{face[3]+1}\n")
            else: f.write(f"f {face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1}\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=3)
    ap.add_argument("--span",type=float,default=6.0)
    ap.add_argument("--height",type=float,default=12.0)
    ap.add_argument("--tracery",type=float,default=0.6)
    ap.add_argument("--bays",type=int,default=4)
    args=ap.parse_args()
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    print(f"[cathedral] depth={args.depth} span={args.span} height={args.height} tracery={args.tracery} bays={args.bays}")
    verts,faces,uvs=build_nave_mesh(args.span,args.height,args.depth,args.tracery,args.bays)
    nave_path=OUT_DIR/"SM_P4_Cathedral_Fractal.obj"
    write_obj(nave_path,verts,faces,uvs)
    print(f"[cathedral] {nave_path} verts={len(verts)} faces={len(faces)} {nave_path.stat().st_size} bytes")
    rverts,rfaces,ruvs=build_rose_window(args.span,args.tracery)
    rose_path=OUT_DIR/"SM_P4_Cathedral_RoseWindow.obj"
    write_obj(rose_path,rverts,rfaces,ruvs)
    print(f"[cathedral] {rose_path} verts={len(rverts)} faces={len(rfaces)} {rose_path.stat().st_size} bytes")
    manifest={"schema":"melodia.cathedral_fractal.v1","seed":SEED,"params":{"recursion_depth":args.depth,"arch_span":args.span,"vault_height":args.height,"tracery_density":args.tracery,"bays":args.bays},"meshes":[{"name":"SM_P4_Cathedral_Fractal","path":"Saved/Audit/cathedral/SM_P4_Cathedral_Fractal.obj","verts":len(verts),"faces":len(faces),"bytes":nave_path.stat().st_size},{"name":"SM_P4_Cathedral_RoseWindow","path":"Saved/Audit/cathedral/SM_P4_Cathedral_RoseWindow.obj","verts":len(rverts),"faces":len(rfaces),"bytes":rose_path.stat().st_size}],"gn_builder":"MEL_p4_fractal_cathedral","copernicus_variant":"FractalCathedral","scale":"meters (UE cm = *100)","nanite":True}
    with open(OUT_DIR/"cathedral_fractal_manifest.json","w") as f: json.dump(manifest,f,indent=2)
    print(f"[manifest] {OUT_DIR/'cathedral_fractal_manifest.json'}")

if __name__=="__main__": main()
