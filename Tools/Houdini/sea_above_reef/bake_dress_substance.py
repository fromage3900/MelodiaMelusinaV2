"""Headless Substance bake for the Shorewake dress — sbsbaker (Automation ToolKit).

Uses the Designer install's sbsbaker.exe (licensed, no watermark, GPU raytracing).
Runs OUTSIDE any GUI. Outputs to bake/sbs/ at 4096.

CRITICAL GOTCHA (cost an hour of flat-white maps): sbsbaker --output-size takes
the BASE-2 EXPONENTS, not pixels: '--output-size 12,12' = 4096x4096.

Naming convention required by sbsbaker:
  <name>_low.obj   = bake target (has the UVs)
  <name>_high.obj  = occluder/detail source (same mesh, or subdivided detail mesh)

Run:  python Tools/Houdini/sea_above_reef/bake_dress_substance.py
Needs: bake/SM_ShorewakeDress_48MAT_v2_low.obj, ..._high.obj (any occluder copy),
       ..._high_subdiv.obj (detail source for normals; from Blender simple-subdiv x2)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SBSBAKER = Path(r"C:\Program Files\Adobe\Adobe Substance 3D Designer\sbsbaker.exe")
BAKE_DIR = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_lookdev\bake")
OUT_DIR = BAKE_DIR / "sbs"
LOW = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_low.obj"
HIGH_SUBDIV = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high_subdiv.obj"
RES_EXP = 12  # 2^12 = 4096
QUALITY = 3
SEED = 20260830


def run(args, out_png=None):
    if out_png is not None and out_png.exists():
        print("SKIP (exists)", out_png.name)
        return
    cmd = [str(SBSBAKER)] + args
    print("RUN", " ".join(cmd[1:5]), "...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    tail = (r.stdout + r.stderr).strip().splitlines()[-2:]
    print("   ", " | ".join(tail))
    if r.returncode != 0:
        print("FAILED:", r.returncode)
        print(r.stdout[-2000:], r.stderr[-2000:])
        sys.exit(1)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in (LOW,):
        if not p.exists():
            raise SystemExit("missing %s — run shorewake_bake_prep.py first" % p)

    # sbsbaker matches detail sources by NAME SUFFIX (_high), not by flag:
    # the subdivided detail mesh must be the file ending in _high.obj.
    if HIGH_SUBDIV.exists():
        shutil.copyfile(HIGH_SUBDIV, BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high.obj")

    common = ["--output-path", str(OUT_DIR), "--output-format", "png",
              "--output-size", f"{RES_EXP},{RES_EXP}"]

    # --- AO: low as target, _high as occluder (self + inter-panel) ---
    run(["ambient-occlusion", *common, "--quality", str(QUALITY),
         str(LOW), BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high.obj"],
        out_png=OUT_DIR / "SM_ShorewakeDress_48MAT_v2_low_ambient-occlusion.png")

    # --- Normal: tangent space from the subdivided detail mesh, DirectX (UE) ---
    run(["normal-from-mesh", *common,
         "--highdef-mesh", str(HIGH_SUBDIV),
         "--normal-format", "1",  # 1 = DirectX green for UE
         "--antialiasing", "2",   # 4x4 subsampling
         "--max-frontal", "0.02", "--max-rear", "0.02",  # 2% of bbox each way
         str(LOW)],
        out_png=OUT_DIR / "SM_ShorewakeDress_48MAT_v2_low_normal-from-mesh.png")

    # --- Position (object space) ---
    run(["position", *common, str(LOW)],
        out_png=OUT_DIR / "SM_ShorewakeDress_48MAT_v2_low_position.png")

    # --- Curvature (no --quality option on this baker) ---
    run(["curvature", *common,
         str(LOW), BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high.obj"],
        out_png=OUT_DIR / "SM_ShorewakeDress_48MAT_v2_low_curvature.png")

    # --- Thickness ---
    run(["thickness-from-mesh", *common,
         str(LOW), BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high.obj"],
        out_png=OUT_DIR / "SM_ShorewakeDress_48MAT_v2_low_thickness.png")

    manifest = {
        "schema": "melodia.shorewake_sbs_bake.v1",
        "seed": SEED,
        "sbsbaker": str(SBSBAKER),
        "resolution": 2 ** RES_EXP,
        "output_size_note": "sbsbaker --output-size takes base-2 EXPONENTS (12,12 = 4096)",
        "inputs": {"low": str(LOW),
                   "high": str(BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_high.obj")},
        "normal_convention": "directx (UE), mikktspace tangent plugin (default)",
        "outputs_dir": str(OUT_DIR),
    }
    (OUT_DIR / "sbs_bake_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("SBS_BAKE_DONE", sorted(p.name for p in OUT_DIR.glob("*.png")))


if __name__ == "__main__":
    main()
