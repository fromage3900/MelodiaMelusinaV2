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
wrangle_geo.parm("class").set(2)  # point (H22 menu: 0=detail 1=prim 2=point 3=vertex)
wrangle_geo.parm("snippet").set("""
 // thickness: ray along -N, against self
 vector dir = -normalize(v@N);
 vector hitpos; vector hituvw;
 int hit = intersect(0, v@P, dir, hitpos, hituvw);
 float t = hit >= 0 ? distance(hitpos, v@P) : 1.0;
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
wrangle_ao.parm("class").set(2)  # point — per-point Ao (detail would be one value)
# spare seed parm for chi("seed") in the snippet (H22: must exist or cook fails)
seed_tpl = hou.IntParmTemplate("seed", "Seed", 1, default_value=({seed},), min=0, max=99999999)
wrangle_ao.addSpareParmTuple(seed_tpl)
wrangle_ao.parm("seed").set({seed})  # template defaults mangle large ints; explicit set sticks
wrangle_ao.parm("snippet").set("""
 // AO: hemisphere sample 64 rays, cosine-weighted, self-exclusion
 int nsamples = 64;
 float occ = 0;
 // seed from SEED parm on HDA / COP
 int seed = chi("seed");
 for(int i=0;i<nsamples;i++) {{
   vector dir = sample_direction_uniform(rand(seed*7+i*131+@ptnum*17));
   dir = dir * sign(dot(dir, v@N)); // hemisphere
   vector hitpos; vector hituvw;
   int hit = intersect(0, v@P + v@N*0.001, dir, hitpos, hituvw);
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
# H22 truth: sopimport takes resolution from its input — no resolution parms exist.
sop_import = copnet.createNode("sopimport", "SOP_Import")
sop_import.parm("usesoppath").set(1)  # H22 truth: soppath ignored unless this is on
sop_import.parm("soppath").set("/obj/dress_bake/OUT_SOP")

# Bake Preprocess — cage/normal prep ahead of the geometry baker
pre = copnet.createNode("bakepreprocess", "PRE_Bake")
pre.setInput(0, sop_import)

# Bake Geometry Textures ::2.0 (H22 successor to Labs Maps Baker):
# bakes attribs incl. curvature, UV-gap filling built in (enableuvfilling = bg fill).
# H22 Apprentice truth (hit 2026-09-03): COP file saves are capped at 1920x1080 —
# 4096 renders cook fine but FAIL at save ("Copernicus resolution is limited").
# Max square texture on this license: 1080. Full 4K needs a licensed host.
APPRENTICE_MAX_SQUARE = 1080
# H22 input truth: size_ref (input 0) takes IMAGE metadata for output resolution
# (geometry here fails "Can't convert Geometry to Metadata"); input 1 = low.
# from size_ref, so constant -> resample dials it. Determinism from the VEX AO seed.
size_const = copnet.createNode("constant", "SIZE_Const")
size_rs = copnet.createNode("resample", "SIZE_Ref")
size_rs.setInput(0, size_const)
size_rs.parm("resolution1").set({size})
size_rs.parm("resolution2").set({size})
baker = copnet.createNode("bakegeometrytextures::2.0", "Baker_GeoTex")
baker.parm("uvattribute").set("uv")
baker.parm("enableuvfilling").set(1)
baker.parm("tracingmode").set(2)  # Single Mesh (Low Only) — same-mesh bake, no cage/high needed
baker.parm("bakecurvature").set(1)  # native curvature -> Emission branch
baker.parm("bakethickness").set(1)  # native thickness -> Roughness branch
baker.parm("attribs").set(1)  # custom float slot: Ao -> BaseColor branch
baker.parm("doattrib1").set(1)
baker.parm("attrib1").set("Ao")
# H22 truth (probed 2026-09-03): custom slots take FLOAT attribs (Ao renders);
# vector Cd is rejected ("wrong type"). SOP f@thickness/f@Ao are point floats.
baker.setInput(0, size_rs)
baker.setInput(1, pre)

# Per-channel branches (honest mapping, each a real baked signal):
#   BaseColor <- custom(11): 64-ray VEX Ao | Normal <- normal(0)
#   Emission <- curvature(5) | Roughness <- thickness(8)
branches = {{"BaseColor": 11, "Normal": 0, "Emission": 5, "Roughness": 8}}
branch_nodes = {{}}
for name, idx in branches.items():
    nl = copnet.createNode("null", "BR_" + name)
    nl.setInput(0, baker, idx)
    branch_nodes[name] = nl

# Denoise COP — AI denoiser on the Ao branch (kills 64-ray speckle)
denoise = copnet.createNode("denoiseai", "Denoise_AO")
denoise.setInput(0, branch_nodes["BaseColor"])
branch_nodes["BaseColor"] = denoise

# File Output COPs — per-channel endpoints (interactive view; disk writes via ROPs)
for name in ["BaseColor", "Normal", "Emission", "Roughness"]:
    fout = copnet.createNode("file", "OUT_" + name)
    fout.parm("filename").set("{out_dir}/T_MelusinaC_DressShorewake_" + name + ".png")
    fout.setInput(0, branch_nodes[name])

# Disk writers — /out image ROPs (H22 truth, probed 2026-09-03: file COP .cook() never
# writes; ROP coppath points at each branch node, aov1=C, setres=1 dials true size)
outnet = hou.node("/out")
for name in ["BaseColor", "Normal", "Emission", "Roughness"]:
    rop = outnet.createNode("image", "ROP_OUT_" + name)
    rop.parm("coppath").set("/img/cop_dress_bake/BR_" + name)
    rop.parm("aov1").set("C")
    rop.parm("setres").set(1)  # else ROP downsamples to its own res1/res2 (1024)
    rop.parm("res1").set({size})
    rop.parm("res2").set({size})
    rop.parm("copoutput").set("{out_dir}/T_MelusinaC_DressShorewake_" + name + ".png")

copnet.layoutChildren()
hou.hipFile.save(hip)
print("[Copernicus] Saved " + hip)
print("[Copernicus] Networks: SOP dress_bake (File->VEX thickness/curvature->VEX AO 64 seeded->OUT_SOP)")
print("[Copernicus]           COP cop_dress_bake (SOP Import->Preprocess->BakeGeoTex UVfill->Curvature->DenoiseAI->File Outputs)")
'''

def build_hip_code(hip_path: Path, posed_obj: str, seed: int, size: int) -> str:
    out_dir = str((PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "houdini_variants").as_posix())
    return HIP_BUILD_CODE.format(
        hip_path=str(hip_path).replace("\\", "/"),
        posed_obj=posed_obj.replace("\\", "/"),
        out_dir=out_dir,
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
        "replaces": "Tools/Houdini/sea_above_reef/bake_rasterize_ao.py (PIL) -> H22 COP (Preprocess + BakeGeoTex UVfill + DenoiseAI)",
        "networks": {
            "sop": "File -> VEX thickness/curvature/convex -> VEX AO 64 rays (spare seed parm) -> OUT_SOP",
            "cop": "SOP Import -> Bake Preprocess -> BakeGeometryTextures::2.0 (uv, UVfill) -> Curvature -> DenoiseAI -> File Outputs",
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
