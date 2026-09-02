"""Crystal Cathedral — houdini mesh (hython 22.0.368).

Extends build_fractal_cathedral.py — same nave (1364 verts, 8 bays) but vault ribs grow crystal shards,
rose window becomes faceted crystal rosette, buttresses terminate in crystal pinnacles.
Palette from GlitterCrystal/DancingCrystals: crystal facets + iridescence.

Run:
  hython Tools/Houdini/cathedral/build_crystal_cathedral.py --crystal 0.7 --facets 8
  hython Tools/Houdini/cathedral/build_crystal_cathedral.py --crystal 0.9 --facets 12 --bays 8
"""
import argparse, json, math, random
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "cathedral"
SEED = 20260901

# import base cathedral builders
import importlib.util, sys
spec = importlib.util.spec_from_file_location("build_fractal", str(PROJECT_ROOT / "Tools/Houdini/cathedral/build_fractal_cathedral.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def crystal_prism(center, height, radius, facets, rot=0):
    """Return verts/faces for a hexagonal prism crystal."""
    verts = []
    faces = []
    # base center
    # bottom ring
    bottom = []
    top = []
    for i in range(facets):
        ang = 2*math.pi*i/facets + rot
        x = center[0] + math.cos(ang)*radius
        y = center[1] + math.sin(ang)*radius
        verts.append((x, y, center[2]))
        bottom.append(len(verts)-1)
    # top ring (tapered)
    for i in range(facets):
        ang = 2*math.pi*i/facets + rot
        r2 = radius*0.6
        x = center[0] + math.cos(ang)*r2
        y = center[1] + math.sin(ang)*r2
        verts.append((x, y, center[2]+height))
        top.append(len(verts)-1)
    # tip
    verts.append((center[0], center[1], center[2]+height*1.25))
    tip = len(verts)-1
    # side quads
    for i in range(facets):
        a = bottom[i]; b = bottom[(i+1)%facets]; c = top[(i+1)%facets]; d = top[i]
        faces.append((a,b,c,d))
    # top fan
    for i in range(facets):
        a = tip; b = top[i]; c = top[(i+1)%facets]
        faces.append((a,b,c))
    uvs = [(0,0)]*len(verts)
    return np.array(verts, dtype="float32"), faces, np.array(uvs, dtype="float32")

def build_crystal_cathedral(span=10, height=20, depth=4, tracery=0.85, bays=8, crystal=0.7, facets=8):
    # base nave
    verts, faces, uvs = mod.build_nave_mesh(span, height, depth, tracery, bays)
    verts = verts.tolist()
    faces = list(faces)
    uvs = uvs.tolist()
    print(f"[crystal] base nave verts={len(verts)} faces={len(faces)}")

    # crystal shards on vault ribs — each rib gets 3-5 prisms
    rng = random.Random(SEED)
    bay_len = span*0.75
    for bay in range(bays):
        y0 = bay*bay_len
        y1 = (bay+1)*bay_len
        # rib centers (diagonal)
        for (x0, ys, x1, ye) in [(-span*0.5, y0, span*0.5, y1), (span*0.5, y0, -span*0.5, y1)]:
            # shard positions along rib
            shards = int(3 + crystal*3)
            for s in range(shards):
                t = (s+0.5)/shards
                cx = x0 + (x1-x0)*t + rng.uniform(-0.3, 0.3)
                cy = ys + (ye-ys)*t + rng.uniform(-0.3, 0.3)
                cz = height + rng.uniform(-0.5, 0.5)
                # height driven by Chladni + random
                n,m = 8,6
                chlad = abs(math.cos(n*math.pi*(cx/span*0.5+0.5))*math.cos(m*math.pi*(cy/(bay_len*bays)*0.5+0.5)))
                h = (0.8 + chlad*1.2) * crystal * 2.5
                r = 0.18 + rng.uniform(0, 0.12)
                cverts, cfaces, cuvs = crystal_prism((cx, cy, cz), h, r, facets, rot=rng.uniform(0, 6.28))
                base = len(verts)
                verts.extend(cverts.tolist())
                uvs.extend(cuvs.tolist())
                for f in cfaces:
                    faces.append(tuple(v+base for v in f))

    # crystal pinnacles on buttresses (scale 0.5 recursion like PCG but crystal)
    for bay in range(bays+1):
        y = bay*bay_len
        for x in (-span*0.5-0.8, span*0.5+0.8):
            h = (1.2 + rng.uniform(0, 0.8)) * crystal * 2.0
            r = 0.22
            cverts, cfaces, cuvs = crystal_prism((x, y, height*0.9), h, r, 6, rot=rng.uniform(0,6.28))
            base = len(verts)
            verts.extend(cverts.tolist())
            uvs.extend(cuvs.tolist())
            for f in cfaces:
                faces.append(tuple(v+base for v in f))

    return np.array(verts, dtype="float32"), faces, np.array(uvs, dtype="float32")

def build_crystal_rose(span, tracery, crystal, facets):
    verts, faces, uvs = mod.build_rose_window(span, tracery)
    verts = verts.tolist(); faces=list(faces); uvs=uvs.tolist()
    # faceted crystal overlay on rose — hex tiling
    rng = random.Random(SEED+1)
    radius = span*0.42
    # add crystal shards on rose disc
    for _ in range(int(12*crystal)):
        ang = rng.uniform(0, 2*math.pi)
        rad = rng.uniform(radius*0.1, radius*0.85)
        cx = math.cos(ang)*rad
        cy = math.sin(ang)*rad
        n,m=8,6
        chlad = abs(math.cos(n*math.pi*(cx/radius*0.5+0.5))*math.cos(m*math.pi*(cy/radius*0.5+0.5)))
        h = (0.5+chlad)*crystal*1.2
        r = 0.12
        cverts, cfaces, cuvs = crystal_prism((cx, cy, 0), h, r, facets, rot=rng.uniform(0,6.28))
        base=len(verts)
        verts.extend(cverts.tolist()); uvs.extend(cuvs.tolist())
        for f in cfaces:
            faces.append(tuple(v+base for v in f))
    return np.array(verts, dtype="float32"), faces, np.array(uvs, dtype="float32")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=4)
    ap.add_argument("--span",type=float,default=10)
    ap.add_argument("--height",type=float,default=20)
    ap.add_argument("--tracery",type=float,default=0.85)
    ap.add_argument("--bays",type=int,default=8)
    ap.add_argument("--crystal",type=float,default=0.7)
    ap.add_argument("--facets",type=int,default=8)
    args=ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[crystal] depth={args.depth} span={args.span} height={args.height} bays={args.bays} crystal={args.crystal} facets={args.facets}")
    verts, faces, uvs = build_crystal_cathedral(args.span, args.height, args.depth, args.tracery, args.bays, args.crystal, args.facets)
    path = OUT_DIR/"SM_P4_Cathedral_Crystal.obj"
    mod.write_obj(path, verts, faces, uvs)
    print(f"[crystal] {path} verts={len(verts)} faces={len(faces)} {path.stat().st_size} bytes")
    rverts, rfaces, ruvs = build_crystal_rose(args.span, args.tracery, args.crystal, args.facets)
    rpath = OUT_DIR/"SM_P4_Cathedral_Crystal_Rose.obj"
    mod.write_obj(rpath, rverts, rfaces, ruvs)
    print(f"[crystal] {rpath} verts={len(rverts)} faces={len(rfaces)} {rpath.stat().st_size} bytes")
    manifest={"schema":"melodia.cathedral_crystal.v1","seed":SEED,"params":{"recursion_depth":args.depth,"arch_span":args.span,"vault_height":args.height,"tracery_density":args.tracery,"bays":args.bays,"crystal_density":args.crystal,"facet_count":args.facets},"meshes":[{"name":"SM_P4_Cathedral_Crystal","path":"Saved/Audit/cathedral/SM_P4_Cathedral_Crystal.obj","verts":len(verts),"faces":len(faces),"bytes":path.stat().st_size},{"name":"SM_P4_Cathedral_Crystal_Rose","path":"Saved/Audit/cathedral/SM_P4_Cathedral_Crystal_Rose.obj","verts":len(rverts),"faces":len(rfaces),"bytes":rpath.stat().st_size}],"gn_builder":"MEL_p4_crystal_cathedral","copernicus_variants":["FractalCathedral","GlitterCrystal","DancingCrystals"],"scale":"meters (UE cm = *100)","nanite":True}
    with open(OUT_DIR/"crystal_cathedral_manifest.json","w") as f: json.dump(manifest,f,indent=2)
    print(f"[manifest] {OUT_DIR/'crystal_cathedral_manifest.json'}")

if __name__=="__main__": main()
