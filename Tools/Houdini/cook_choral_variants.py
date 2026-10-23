#!/usr/bin/env python
"""
hython cooker for Choral Sheep COP variants.

Called by deploy/houdini_mcp_server.py::generate_variants when hython is present.
Also runnable directly:
    hython Tools/Houdini/cook_choral_variants.py --out Saved/Audit/choral_sheep/houdini_variants --size 1024
"""
import argparse
import colorsys
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

def cook_with_hou(out: Path, size: int):
    import hou
    hip = Path("Tools/Houdini/choral_sheep_variants.hipnc").resolve()
    if hip.is_file():
        hou.hipFile.load(str(hip))
    copnet_path = "/obj/choral_sheep_variants/copnet1"
    ropnet_path = "/out/choral_variants_rop"
    copnet = hou.node(copnet_path)
    ropnet = hou.node(ropnet_path)
    if copnet is None or ropnet is None:
        raise RuntimeError(f"expected {copnet_path} and {ropnet_path} in HIP")
    out.mkdir(parents=True, exist_ok=True)
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        # drive COP params per variant if nodes exist
        const = hou.node(f"{copnet_path}/const_PC_{label}")
        if const:
            const.parm("colorr").set(base[0]); const.parm("colorg").set(base[1]); const.parm("colorb").set(base[2])
            const.parm("resx").set(size); const.parm("resy").set(size)
        rop = hou.node(f"{ropnet_path}/rop_PC_{label}")
        if rop:
            rop.parm("copoutput").set(str(out / f"ChoralWool_PC_{label}.png"))
            rop.render()
            print(f"[cook] rendered PC {label}")
        else:
            # fallback: cook COP directly
            cop = hou.node(f"{copnet_path}/border_PC_{label}")
            if cop:
                cop.render(str(out / f"ChoralWool_PC_{label}.png"))
    print(f"[cook] done -> {out}")

def cook_with_pil(out: Path, size: int):
    from PIL import Image, ImageDraw
    out.mkdir(parents=True, exist_ok=True)
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        base_rgb = tuple(int(c*255) for c in base)
        accent_rgb = tuple(int(c*255) for c in accent)
        sheen = 0.46 + (pc/12.0)*0.18
        img = Image.new("RGB", (size, size), base_rgb)
        draw = ImageDraw.Draw(img)
        draw.rectangle([size//8, size//8, size-size//8, size-size//8], outline=accent_rgb, width=max(2, size//128))
        overlay = Image.new("RGBA", (size, size), (255,255,255,0))
        od = ImageDraw.Draw(overlay)
        od.rectangle([0,0,size,size//3], fill=(255,255,255, int(sheen*60)))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        try:
            draw = ImageDraw.Draw(img)
            draw.text((12, size-28), f"PC{pc:02d} {label}", fill=(40,40,40))
        except Exception:
            pass
        img.save(out / f"ChoralWool_PC_{label}.png", "PNG")
        print(f"[cook:pil] wrote ChoralWool_PC_{label}.png")
    # contact sheet
    try:
        from PIL import Image
        cols, rows, thumb = 4, 3, size//4
        sheet = Image.new("RGB", (cols*thumb, rows*thumb), (230,230,230))
        for i, (pc,(label,hue)) in enumerate(PITCH_CLASS_HUES.items()):
            base,_ = _pastel_pair(hue); base_rgb = tuple(int(c*255) for c in base)
            tile = Image.new("RGB", (thumb, thumb), base_rgb)
            sheet.paste(tile, ((i%cols)*thumb, (i//cols)*thumb))
        sheet.save(out / "_ChoralSheep_Chromatic_ContactSheet.png", "PNG")
    except Exception:
        pass

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Saved/Audit/choral_sheep/houdini_variants")
    ap.add_argument("--size", type=int, default=1024)
    args = ap.parse_args()
    out = Path(args.out).resolve()
    try:
        import hou
        cook_with_hou(out, args.size)
    except ImportError:
        cook_with_pil(out, args.size)
    except Exception as e:
        print(f"[cook] hou failed ({e}), falling back to PIL")
        cook_with_pil(out, args.size)
