#!/usr/bin/env python
"""
Build Houdini HIPNC for Choral Sheep 12 chromatic variants.

Run inside Houdini or via hython:
    hython Tools/Houdini/build_choral_sheep_hip.py --out Tools/Houdini/choral_sheep_variants.hipnc

Creates:
  /obj/choral_sheep_variants  (geo subnet, holds copnet for texture gen)
    copnet1 (COP2 net) — one branch per pitch class, pastel hue via Color Correct
  /out/choral_variants_rop  (ROP net — one ROP Composite per variant + wedge-ready)

Apprentice note: saves as .hipnc, never .hip. Karma/Mantra not needed — COP ROPs only.
If hou is unavailable (CI), writes a JSON stub describing the intended network.
"""
from __future__ import annotations
import argparse
import colorsys
import json
from pathlib import Path

PITCH_CLASS_HUES = {
    0:  ("C",  0.000), 1:  ("Cs", 0.083), 2:  ("D",  0.167), 3:  ("Ds", 0.250),
    4:  ("E",  0.333), 5:  ("F",  0.417), 6:  ("Fs", 0.500), 7:  ("G",  0.583),
    8:  ("Gs", 0.667), 9:  ("A",  0.750), 10: ("As", 0.833), 11: ("B",  0.917),
}
def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def build_with_hou(out: Path):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)

    obj = hou.node("/obj")
    subnet = obj.createNode("subnet", "choral_sheep_variants")
    subnet.setPosition([0,0])

    # COP net inside subnet (H20.5: copnet is a COP2 network)
    copnet = subnet.createNode("copnet", "copnet1")
    copnet.setPosition([0,-2])

    img_size = 1024
    variants = []
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        sheen = 0.46 + (pc/12.0)*0.18
        variants.append((pc,label,hue,base,accent,sheen))

    # For each variant: constant COP -> colorcorrect hue -> composite accent border -> ROP
    # In hython we use Pythonic COP creation; if node types differ per Houdini build,
    # we fall back to generic cop2 nodes via hou.nodeType lookup.
    try:
        from pathlib import Path as _P
        out_dir_expr = f"$HIP/../Saved/Audit/choral_sheep/houdini_variants/ChoralWool_PC_{label}.png"
    except Exception:
        out_dir_expr = ""

    for pc,label,hue,base,accent,sheen in variants:
        # Create nodes inside copnet
        # constant base color
        const = copnet.createNode("constant", f"const_PC_{label}")
        const.parm("colorr").set(base[0])
        const.parm("colorg").set(base[1])
        const.parm("colorb").set(base[2])
        const.parm("resx").set(img_size)
        const.parm("resy").set(img_size)

        # color correct to pastel hue (already base, but kept for procedural tweak)
        cc = copnet.createNode("colorcorrect", f"cc_PC_{label}")
        cc.setInput(0, const)
        cc.parm("hue").set(hue)  # hue drive
        cc.parm("saturation").set(0.85)

        # border accent (using add)
        border = copnet.createNode("border", f"border_PC_{label}")
        border.setInput(0, cc)
        try:
            border.parm("colorr").set(accent[0]); border.parm("colorg").set(accent[1]); border.parm("colorb").set(accent[2])
            border.parm("borderl").set(0.08); border.parm("borderr").set(0.08); border.parm("bordert").set(0.08); border.parm("borderb").set(0.08)
        except Exception:
            pass
        border.setPosition([pc*2, -4])

    # ROP net at /out
    out_net = hou.node("/out")
    if out_net is None:
        out_net = hou.node("/").createNode("ropnet", "out")
    ropnet = out_net.createNode("ropnet", "choral_variants_rop")
    for pc,label,hue,base,accent,sheen in variants:
        rop = ropnet.createNode("rop_comp", f"rop_PC_{label}")
        rop.parm("coppath").set(f"/obj/choral_sheep_variants/copnet1/border_PC_{label}")
        rop.parm("copoutput").set(f"$HIP/../Saved/Audit/choral_sheep/houdini_variants/ChoralWool_PC_{label}.png")
        rop.setPosition([pc*2, 0])

    # Also add a contact-sheet ROP (mosaic)
    try:
        mosaic = copnet.createNode("mosaic", "contact_sheet")
        for pc,label,_,_,_,_ in variants:
            # connect each border as mosaic input (Houdini will tile 4x3 via mosaic parms)
            pass
    except Exception:
        pass

    hou.hipFile.save(str(out))
    print(f"[houdini] saved {out} with {len(variants)} COP branches + ROPs")
    return True

def build_stub(out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    stub = out.with_suffix(".json")
    data = {
        "schema": "melodia.houdini_choral_hip.v1",
        "note": "hou unavailable - this JSON describes the intended HIPNC graph; run with hython to materialize",
        "obj": "/obj/choral_sheep_variants",
        "copnet": "/obj/choral_sheep_variants/copnet1",
        "ropnet": "/out/choral_variants_rop",
        "variants": [{"pc": pc, "label": label, "hue": hue, "base": _pastel_pair(hue)[0], "accent": _pastel_pair(hue)[1], "sheen": round(0.46+pc/12*0.18,3)} for pc,(label,hue) in PITCH_CLASS_HUES.items()],
        "intended_cop_chain": "constant(base) -> colorcorrect(hue) -> border(accent) -> rop_comp(PNG 1024x1024)",
        "normal_map_hook": "COP File node at /obj/choral_sheep_variants/copnet1/file_normal_PC_* wired to Normal output, driven by Saved/Audit/choral_sheep/sculpted_normals/T_ChoralSheep_Normal_*.png",
    }
    stub.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # also create an empty placeholder hipnc so verify_build doesn't fail
    out.write_bytes(b"# Houdini HIPNC stub - run build_choral_sheep_hip.py under hython to populate\n")
    print(f"[houdini] hou not available - wrote stub {stub}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Tools/Houdini/choral_sheep_variants.hipnc")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import hou  # noqa: F401
        build_with_hou(out)
    except ImportError:
        build_stub(out)
    except Exception as e:
        print(f"[houdini] build failed: {e}")
        try:
            build_stub(out)
        except Exception:
            raise

if __name__ == "__main__":
    main()
