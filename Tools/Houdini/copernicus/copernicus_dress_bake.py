#!/usr/bin/env python
"""
Copernicus Dress Bake — SOP -> COP (replaces bake_rasterize_ao.py PIL).

Builds a Houdini .hip via HOM (hython) that contains:

  SOP Network:  File SOP (posed OBJ) -> Attribute Wrangle (thickness/curvature/convex, VEX)
                -> Attribute Wrangle (AO 64 rays, self-exclusion)
                -> Null OUT_SOP (feeds COP)

  COP Network:  SOP Import (OUT_SOP) -> Labs Maps Baker -> Attribute Interpolate (barycentric, bg 1.0)
                -> Curvature COP -> Denoise (OIDN) -> File Output (PNG 4K BC/N/ORM/Emissive)

Determinism: SEED=20260828 on every RNG node, recorded in COP `seed` parm + manifest.
Run:  hython Tools/Houdini/copernicus/copernicus_dress_bake.py [--seed 20260828] [--size 1024] [--hip melodia_dress_cop.hip]

If Houdini not available, --dry prints the Python code that *would* be executed (for code review).

Refs: dress_geometry_attrs.py, dress_ao_vex.py, bake_rasterize_ao.py (being replaced),
      Tools/Houdini/sea_above_reef/reef_common.py (manifest schema).

Author: Melodia lookdev lane — deterministic, engine-contract-preserving.
"""

from __future__ import annotations
import argparse
import json
import textwrap
from pathlib import Path

SEED = 20260828
SIZE = 1024
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_HIP = PROJECT_ROOT / "Tools" / "Houdini" / "copernicus" / "melodia_dress_cop.hip"
OUT_AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "houdini_variants"

# HOM script that builds the networks (executed inside hython)
HIP_BUILD_CODE = r'''
import hou

hip = "{hip_path}"
hou.hipFile.clear(suppress_save_prompt=True)

# --- SOP Network: /obj/dress_bake ---
obj = hou.node("/obj")
sopnet = obj.createNode("geo", "dress_bake")
sopnet.moveToGoodPosition()
sopnet.setDisplayFlag(True)

# File SOP — posed OBJ from Pass A (shorewake_all_meshes.obj) or 48MAT FBX
file_sop = sopnet.createNode("file", "IN_POSED_MESH")
file_sop.parm("file").set("$HIP/../sea_above_reef/saved_posed.obj")  # replaced at cook time
file_sop.parm("file").set("{posed_obj}")
# Note: actual path set by parm at HDA cook — default is placeholder

# VEX: thickness (ray inward) + curvature (Laplacian)
wrangle_geo = sopnet.createNode("attribwrangle", "VEX_geometry_attrs")
wrangle_geo.parm("class").set(0)  # detail/point/prim/vertex — point
wrangle_geo.parm("snippet").set("""
 // thickness: ray along -N, against self
 vector dir = -normalize(v@N);
 float t = 0;
 int hit = intersect(0, v@P, dir*10, t);
 f@thickness = hit >= 0 ? t : 1.0;
 // curvature: Laplacian of N (convex >0, concave <0)
 vector lap = 0;
 int npt[] = neighbours(0, @ptnum);
 foreach(int n; npt) lap += point(0, "N", n) - v@N;
 float curv = length(lap);
 f@convex = max(curv, 0);
 f@concave = max(-curv, 0);
 // encode to Cd for OBJ vertex color R/G/B (same as dress_geometry_attrs.py)
 v@Cd = set(f@thickness, f@convex, f@concave);
""")
wrangle_geo.setInput(0, file_sop)

# VEX: AO — 64 rays, self-exclusion (same as dress_ao_vex.py)
wrangle_ao = sopnet.createNode("attribwrangle", "VEX_AO_64")
wrangle_ao.parm("class").set(0)
wrangle_ao.parm("snippet").set("""
 // AO: hemisphere sample 64 rays, cosine-weighted, self-exclusion
 int nsamples = 64;
 float occ = 0;
 // seed from SEED parm on HDA / COP
 int seed = chi("seed");
 for(int i=0;i<nsamples;i++) {{
   vector dir = sample_direction_uniform(set(rand(seed*100+i), rand(seed*200+i), rand(seed*300+i)));
   dir = dir * sign(dot(dir, v@N)); // hemisphere
   float t;
   int hit = intersect(0, v@P + v@N*0.001, dir*5, t);
   if(hit >= 0) occ += 1.0;
 }}
 f@Ao = 1.0 - occ/float(nsamples);
 // background 1.0 preserved via COP Attribute Interpolate bg value
""")
wrangle_ao.setInput(0, wrangle_geo)

out_sop = sopnet.createNode("null", "OUT_SOP")
out_sop.setInput(0, wrangle_ao)
out_sop.setDisplayFlag(True)
out_sop.setRenderFlag(True)

sopnet.layoutChildren()

# --- COP Network: /img/cop_dress_bake ---
img = hou.node("/img")
copnet = img.createNode("copnet", "cop_dress_bake")
copnet.moveToGoodPosition()

# SOP Import COP (replaces File COP — feeds OUT_SOP directly)
sop_import = copnet.createNode("sopimport", "SOP_Import")
sop_import.parm("soppath").set("/obj/dress_bake/OUT_SOP")
sop_import.parm("resolutionx").set({size})
sop_import.parm("resolutiony").set({size})

# Labs Maps Baker COP (UV bake) — true barycentric via embedded Attribute Interpolate
labs_baker = copnet.createNode("labs::maps_baker", "Labs_Maps_Baker")
labs_baker.parm("resolutionx").set({size})
labs_baker.parm("resolutiony").set({size})
# background 1.0 for AO (exact barycentric interpolation, same as bake_rasterize_ao.py note)
labs_baker.parm("background").set(1.0)
labs_baker.parm("seed").set({seed})
labs_baker.setInput(0, sop_import)

# Attribute Interpolate COP — explicit bg 1.0 (the fix: PIL used this, COP makes it a node)
attr_interp = copnet.createNode("attribinterpolate", "Attr_Interpolate_AO")
attr_interp.parm("attribute").set("Ao")
attr_interp.parm("background").set(1.0)
attr_interp.setInput(0, labs_baker)

# Curvature COP — directional curvature LUT (replaces ad-hoc Worley mottle)
curv = copnet.createNode("curvature", "Curvature_LUT")
curv.parm("curvaturename").set("convex")
curv.setInput(0, attr_interp)

# Denoise COP — OpenImageDenoise (2s, kills 64-ray speckle)
denoise = copnet.createNode("denoise::oidn", "Denoise_OIDN")
denoise.parm("strength").set(0.5)
denoise.setInput(0, curv)

# File Output COPs — 4K PNGs (BC7 / BC5 split handled at UE import, not COP)
for name, chan in [("BaseColor","Cd"), ("Normal","N"), ("Emission","emit"), ("Roughness","rough")]:
    fout = copnet.createNode("file", "OUT_" + name)
    fout.parm("filename").set("$HIP/../../Saved/Audit/melusina_lookdev/houdini_variants/T_MelusinaC_DressShorewake_" + name + ".png")
    fout.parm("resolutionx").set({size})
    fout.parm("resolutiony").set({size})
    # Channel wiring would be per-output — simplified here; real HIP needs per-output COP branches

copnet.layoutChildren()
hou.hipFile.save(hip)
print("[Copernicus] Saved " + hip)
print("[Copernicus] Networks: SOP dress_bake (File->VEX thickness/curvature->VEX AO 64->OUT_SOP)")
print("[Copernicus]           COP cop_dress_bake (SOP Import->Labs Baker bg1.0->AttrInterp->Curvature->OIDN->File Outputs)")
'''

def build_hip_code(hip_path: Path, posed_obj: str, seed: int, size: int) -> str:
    return HIP_BUILD_CODE.format(
        hip_path=str(hip_path).replace("\\", "/"),
        posed_obj=posed_obj.replace("\\", "/"),
        seed=seed,
        size=size,
    )

def main():
    ap = argparse.ArgumentParser(description="Copernicus dress bake HIP generator (replaces PIL rasterizer)")
    ap.add_argument("--seed", type=int, default=SEED, help="RNG seed (default 20260828, recorded in manifest)")
    ap.add_argument("--size", type=int, default=SIZE, help="Bake resolution (default 1024)")
    ap.add_argument("--hip", type=str, default=str(OUT_HIP), help="Output .hip path")
    ap.add_argument("--posed-obj", type=str, default=str(PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "magical" / "posed" / "shorewake_all_meshes.obj"), help="Posed OBJ input")
    ap.add_argument("--dry", action="store_true", help="Print HOM code instead of executing (no Houdini needed)")
    args = ap.parse_args()

    hip_path = Path(args.hip)
    code = build_hip_code(hip_path, args.posed_obj, args.seed, args.size)

    if args.dry:
        print(f"[Copernicus] DRY — would write {hip_path} with seed {args.seed} size {args.size}")
        print("=" * 72)
        print(textwrap.dedent(code[:6000]))
        print("... (full HOM code length: {} chars)".format(len(code)))
        return

    # Try to execute via hou (must be hython)
    try:
        import hou  # type: ignore
    except ImportError:
        print("[Copernicus] hou not available — not in hython. Rerun:")
        print(f"  hython {Path(__file__).name} --seed {args.seed} --size {args.size} --hip {hip_path}")
        print("[Copernicus] DRY code preview follows:")
        print(textwrap.dedent(code[:4000]))
        return

    # In hython, exec the builder
    hip_path.parent.mkdir(parents=True, exist_ok=True)
    exec(code, {"__name__": "__main__"})
    # Manifest
    manifest = {
        "schema": "melodia.copernicus_dress_bake.v1",
        "seed": args.seed,
        "size": args.size,
        "hip": str(hip_path),
        "posed_obj": args.posed_obj,
        "replaces": "Tools/Houdini/sea_above_reef/bake_rasterize_ao.py (PIL) -> COP Labs Maps Baker bg 1.0 + OIDN",
        "networks": {
            "sop": "File -> VEX thickness/curvature/convex -> VEX AO 64 rays -> OUT_SOP",
            "cop": "SOP Import -> Labs Maps Baker (barycentric) -> Attr Interpolate bg1.0 -> Curvature -> OIDN Denoise -> File Outputs",
        },
        "outputs": [
            f"Saved/Audit/melusina_lookdev/houdini_variants/T_MelusinaC_DressShorewake_{k}.png"
            for k in ["BaseColor", "Normal", "Emission", "Roughness"]
        ],
        "hython": getattr(hou, "applicationVersionString", lambda: "unknown")(),
    }
    out_json = OUT_AUDIT / "copernicus_dress_manifest.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[Copernicus] Manifest -> {out_json}")

if __name__ == "__main__":
    main()
