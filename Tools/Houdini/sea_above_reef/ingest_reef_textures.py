"""Ingest verifier for the Sea Above reef texture suite.

Reads every PNG listed in the suite manifests (or all T_SeaAbove_* / _ContactSheet
files) in Saved/Audit/sea_above/houdini_variants/, checks dimensions and modes,
measures the TILEABILITY SEAM METRIC (mean abs level difference between opposite
edges), hashes each file, and writes:

  reef_texture_ingest_manifest.json
    schema: melodia.sea_above_reef_textures.v1
    per-file: sha256, bytes, size, mode, seam_left_right, seam_top_bottom,
              tileable (bool), import contract (sRGB / LOD group / tiling hint)

Import contract follows the flipbook-plan discipline (VFX plan 2026-08-28 §2.3):
colour maps sRGB=true; all masks/height/normal/caustics sRGB=false.

Run (plain Python only):
  python Tools/Houdini/sea_above_reef/ingest_reef_textures.py
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

rc.require_pil()
from PIL import Image  # noqa: E402

# kind -> (sRGB_on_import, ue_lod_group, note)
CONTRACT = {
    "T_SeaAbove_Sand_Albedo": (True, "TEXTUREGROUP_World", "colour; tiling material base"),
    "T_SeaAbove_Sand_Height": (False, "TEXTUREGROUP_World", "data; height/parallax or blend"),
    "T_SeaAbove_Sand_Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+"),
    "T_SeaAbove_Sand_WetMask": (False, "TEXTUREGROUP_World", "data; drives darken/roughness"),
    "T_SeaAbove_Sand_RippleMask": (False, "TEXTUREGROUP_World", "data; ripple breakup"),
    "T_SeaAbove_Caustics": (False, "TEXTUREGROUP_Effects", "data; 2-copy panner blend"),
    "T_SeaAbove_ShellMask_Nautilus": (False, "TEXTUREGROUP_World", "data; material mask"),
    "T_SeaAbove_ShellMask_Scallop": (False, "TEXTUREGROUP_World", "data; material mask"),
    "T_SeaAbove_ShellMask_Conch": (False, "TEXTUREGROUP_World", "data; material mask"),
    "T_SeaAbove_ShellMask_SandDollar": (False, "TEXTUREGROUP_World", "data; material mask"),
    "T_SeaAbove_Clutter_Atlas": (True, "TEXTUREGROUP_Effects", "RGBA decal atlas; straight alpha"),
    "T_SeaAbove_ClutterFloor_Mask": (False, "TEXTUREGROUP_World", "data; debris breakup"),
    "T_SeaAbove_CoralSkin_Albedo": (True, "TEXTUREGROUP_World",
                                    "colour; coral skin, per-PC tint via MI"),
    "T_SeaAbove_CoralSkin_Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+"),
    "T_SeaAbove_CoralSkin_EmissiveMask": (False, "TEXTUREGROUP_Effects",
                                          "data; pore glow, scale by User.SeaAbovePulse"),
    "T_SeaAbove_KelpSway_LUT": (False, "TEXTUREGROUP_Effects",
                                "data; HALF-WRAP: U=time loop, V=height clamps "
                                "(base pinned); WPO=(rgb*2-1)*Amp, "
                                "Amp*=(1+1.5*User.SeaAbovePulse). U-loop verified by "
                                "kelp_vat_textures.py, excluded from 2-axis wrap check"),
    # --- texture suite v2 (R5, texture_suite_v2.py) ---
    "T_SeaAbove_Droplet_Atlas": (False, "TEXTUREGROUP_Effects",
                                 "data mask flipbook; grayscale luminance in RGB, no "
                                 "alpha; 4x4 grid of 512px cells, row-major frames; "
                                 "Niagara flipbook (P0 droplet plan); atlas, no wrap"),
    "T_SeaAbove_Membrane_Reveal": (False, "TEXTUREGROUP_Effects",
                                   "data; centered radial reveal mask "
                                   "(non-wrapping by design)"),
    "T_SeaAbove_Membrane_Ripple_N": (False, "TEXTUREGROUP_Effects",
                                     "normal map, OpenGL Y+; radial ripple membrane "
                                     "(centered, non-wrapping by design)"),
    "T_SeaAbove_WetRock_Albedo": (True, "TEXTUREGROUP_World",
                                  "colour; wet basalt, tiling material base"),
    "T_SeaAbove_WetRock_Normal": (False, "TEXTUREGROUP_World",
                                  "normal map, OpenGL Y+; from wet-rock height"),
    "T_SeaAbove_WetRock_Wetline": (False, "TEXTUREGROUP_World",
                                   "data; crack+lowland darkening ('wet black line')"),
    "T_SeaAbove_BarnacleCrust_Mask": (False, "TEXTUREGROUP_World",
                                      "data; two-scale voronoi cluster rings"),
    "T_SeaAbove_PulseBand_LUT": (True, "TEXTUREGROUP_Effects",
                                 "sRGB ramp strip 1024x64; U=PC00..PC11 pastel bands, "
                                 "V constant; CLAMP U (1D ramp, non-wrapping)"),
    "T_SeaAbove_Foam_Mask": (False, "TEXTUREGROUP_Effects",
                             "data; foam streak breakup, tiling"),
    "T_SeaAbove_Sediment_Ramp": (True, "TEXTUREGROUP_Effects",
                                 "sRGB vertical ramp strip 64x1024; CLAMP V "
                                 "(1D ramp, non-wrapping)"),
    "T_Jelly_ArmLogic_LUT": (False, "TEXTUREGROUP_Effects",
                             "data; HALF-WRAP: U=time loop, V=along-arm clamps; "
                             "WPO=(rgb*2-1)*Amp; U-loop verified by generator"),
    "T_Jelly_Biolum_LUT": (True, "TEXTUREGROUP_Effects",
                           "sRGB emissive ramp; HALF-WRAP: U=time loop, "
                           "V=along-arm clamps"),
    "T_Jelly_Bell_BaseColor": (True, "TEXTUREGROUP_World", "colour; translucent veil"),
    "T_Jelly_Bell_Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+"),
    "T_Jelly_Bell_Opacity": (False, "TEXTUREGROUP_World", "data; gauzy falloff"),
    "T_Jelly_Bell_CanalMask": (False, "TEXTUREGROUP_Effects", "data; canal emissive"),
    "T_Jelly_Bell_Irid_Mottle": (False, "TEXTUREGROUP_World",
                                 "data; film-thickness variation"),
    "T_Jelly_Iridescence_LUT": (True, "TEXTUREGROUP_Effects",
                                "colour ramp; HALF-WRAP: V=film phase wraps, "
                                "U=facing clamps (excluded from 2-axis check)"),
    "T_Jelly_Nematocyst_Glints": (False, "TEXTUREGROUP_Effects", "data; sparkle field"),
    "T_Leviathan_Bone_BaseColor": (True, "TEXTUREGROUP_World", "colour; eroded bone"),
    "T_Leviathan_Bone_Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+"),
    "T_Leviathan_Bone_Roughness": (False, "TEXTUREGROUP_World", "data; roughness"),
    "T_Organ_Pipe_BaseColor": (True, "TEXTUREGROUP_World", "colour; brushed brass + patina"),
    "T_Organ_Pipe_Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+"),
    "T_Organ_Pipe_Emissive": (False, "TEXTUREGROUP_Effects",
                              "data; tilable glow; mouth boost = x smoothstep(0.9,1.0,uv.y); "
                              "tint by T_SeaAbove_PulseBand_LUT (uv.x band)"),
    "T_DressShorewake_ScaleShimmer": (True, "TEXTUREGROUP_World",
                                      "colour; iridescent scale overlay (Nikki layer)"),
    "T_DressShorewake_ScaleMask": (False, "TEXTUREGROUP_World", "data; scale coverage"),
}
SEAM_RATIO_PASS = 1.6   # wrap step may not exceed 1.6x the typical local gradient

# radial-domain bell maps: U (around the bell) wraps; V (apex->margin) is a
# designed gradient and must NOT tile. Checked on the U axis only.
U_ONLY_WRAP = {"T_Jelly_Bell_BaseColor", "T_Jelly_Bell_CanalMask",
               "T_Jelly_Bell_Opacity", "T_Jelly_Bell_Irid_Mottle"}


def _seam_axis(arr, axis):
    """Return (raw_levels, ratio) for the wrap along `axis`.

    A perfectly tilable high-frequency field legitimately shows a one-sample step
    across the wrap; that equals the local gradient, not a seam. So the honest
    metric is: wrap step relative to the mean adjacent-sample gradient.
    """
    a = arr * 255.0
    if a.ndim == 3:
        a = a.mean(axis=2)
    first = np.take(a, 0, axis=axis).astype(np.float32)
    last = np.take(a, a.shape[axis] - 1, axis=axis).astype(np.float32)
    step = float(np.mean(np.abs(first - last)))
    grad = float(np.mean(np.abs(np.diff(a, axis=axis))))
    ratio = step / max(grad, 1e-6)
    return step, ratio


def seam_metrics(arr01):
    a = arr01
    if a.ndim == 3 and a.shape[2] == 4:
        a = a[..., :3]  # alpha edges are not tiling edges
    lr_levels, lr_ratio = _seam_axis(a, axis=1)
    tb_levels, tb_ratio = _seam_axis(a, axis=0)
    return lr_levels, tb_levels, lr_ratio, tb_ratio


def is_tiling_target(name):
    """Sprites, atlases, contact sheets and half-wrap LUTs are not 2-axis wrap targets."""
    if "ContactSheet" in name:
        return False
    if name == "T_SeaAbove_Clutter_Atlas":
        return False
    if name.startswith("T_SeaAbove_Clutter_"):  # individual decal sprites
        return False
    if name == "T_SeaAbove_KelpSway_LUT":        # U-only wrap; checked by its generator
        return False
    if name == "T_SeaAbove_Droplet_Atlas":
        return False  # 4x4 flipbook atlas - cell-local frames, not a wrap texture
    if name in ("T_SeaAbove_Membrane_Reveal", "T_SeaAbove_Membrane_Ripple_N"):
        return False  # centered radial, non-wrapping by design
    if name in ("T_SeaAbove_PulseBand_LUT", "T_SeaAbove_Sediment_Ramp"):
        return False  # 1D ramp strips
    if name in ("T_Jelly_ArmLogic_LUT", "T_Jelly_Biolum_LUT", "T_Jelly_Iridescence_LUT"):
        return False  # half-wrap ramps/LUTs (U-loop checked by their generators)
    if name in U_ONLY_WRAP:
        return "u_only"  # radial-domain bell maps: U wraps, V is a designed gradient
    return True


def inspect(path):
    img = Image.open(str(path))
    img.load()
    size = img.size
    mode = img.mode
    arr = np.asarray(img.convert("RGBA" if mode == "RGBA" else
                                 ("RGB" if mode in ("RGB", "P") else "L")),
                     dtype=np.float32) / 255.0
    if mode == "P":
        arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    if arr.ndim == 3 and arr.shape[2] == 4:
        # seam metric on colour channels only (alpha edges are not tiling edges)
        arr_seam = arr[..., :3]
    else:
        arr_seam = arr
    lr, tb, lr_r, tb_r = seam_metrics(arr_seam)
    name = path.stem
    srgb, lod, note = CONTRACT.get(name, (mode == "RGB", "TEXTUREGROUP_Effects",
                                          "unlisted file - review"))
    target = is_tiling_target(name)
    if target == "u_only":
        tileable = lr_r < SEAM_RATIO_PASS or lr < 2.0
    elif target:
        # ratio rule covers normal fields; sparse/near-flat fields (gradient < 1
        # level) have meaningless ratios, so an absolutely imperceptible step
        # (< 2 levels = <0.8% brightness) also passes.
        tileable = ((lr_r < SEAM_RATIO_PASS and tb_r < SEAM_RATIO_PASS)
                    or (lr < 2.0 and tb < 2.0))
    else:
        tileable = None  # not a wrap target - seam metric not applicable
    return {
        "name": name,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": rc.sha256_of(path),
        "width": size[0],
        "height": size[1],
        "mode": mode,
        "tiling_target": target,
        "seam_left_right_levels": round(lr, 3),
        "seam_top_bottom_levels": round(tb, 3),
        "seam_lr_ratio": round(lr_r, 3),
        "seam_tb_ratio": round(tb_r, 3),
        "tileable": tileable,
        "import": {"sRGB": srgb, "lod_group": lod, "tiling": "wrap" if target else "decal",
                   "note": note},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(rc.OUT_DIR))
    ap.add_argument("--patterns", nargs="*",
                    default=["T_SeaAbove_*.png", "T_Jelly_*.png",
                             "T_Leviathan_*.png", "T_Organ_*.png",
                             "T_DressShorewake_*.png"])
    ap.add_argument("--include-sheets", action="store_true",
                    help="also verify *_ContactSheet.png (not tiling targets)")
    args = ap.parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        raise SystemExit(f"[ingest] missing dir: {root}")
    paths = []
    for pat in args.patterns:
        paths.extend(sorted(root.glob(pat)))
    if not args.include_sheets:
        paths = [p for p in paths if "ContactSheet" not in p.name]
    if not paths:
        raise SystemExit("[ingest] no files matched - run the suite generators first")

    rows = [inspect(p) for p in paths]
    targets = [r for r in rows if r["tiling_target"]]
    n_tile = sum(1 for r in targets if r["tileable"])
    report = {
        "schema": "melodia.sea_above_reef_textures.v1",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_dir": str(root),
        "runtime": "python+PIL",
        "seam_pass_rule": "wrap step <= 1.6x mean adjacent gradient (both axes)",
        "summary": {"files": len(rows), "tiling_targets": len(targets),
                    "tileable_pass": n_tile, "tileable_fail": len(targets) - n_tile,
                    "non_tiling_outputs": len(rows) - len(targets)},
        "files": rows,
    }
    out_path = root / "reef_texture_ingest_manifest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ingest] {len(rows)} files checked -> {out_path.name}")
    print(f"[ingest] tiling targets pass/fail: {n_tile}/{len(targets) - n_tile} "
          f"(+{len(rows) - len(targets)} decal/QA outputs excluded from wrap check)")
    for r in rows:
        if r["tiling_target"] == "u_only":
            flag = "OK " if r["tileable"] else "SEAM"
            print(f"  [{flag}] {r['name']:<38} {r['width']}x{r['height']} {r['mode']:<4} "
                  f"U-only wrap: lr={r['seam_left_right_levels']:>6}L/"
                  f"{r['seam_lr_ratio']:>5}r (V=radial gradient, no wrap) "
                  f"srgb={r['import']['sRGB']}")
            continue
        if not r["tiling_target"]:
            print(f"  [SPRT] {r['name']:<38} {r['width']}x{r['height']} {r['mode']:<4} "
                  f"(decal/QA - no wrap check)")
            continue
        flag = "OK " if r["tileable"] else "SEAM"
        print(f"  [{flag}] {r['name']:<38} {r['width']}x{r['height']} {r['mode']:<4} "
              f"lr={r['seam_left_right_levels']:>6}L/{r['seam_lr_ratio']:>5}r "
              f"tb={r['seam_top_bottom_levels']:>6}L/{r['seam_tb_ratio']:>5}r "
              f"srgb={r['import']['sRGB']}")
    if n_tile != len(targets):
        print("[ingest] WARNING: seam failures above - regenerate or investigate "
              "(a 'SEAM' line means the wrap step exceeds local-gradient tolerance)")
    print("[ingest] NOTE: manifest is an output, not an input - re-derive by rerunning")


if __name__ == "__main__":
    main()
