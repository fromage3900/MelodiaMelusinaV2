#!/usr/bin/env python
"""
hython cooker for Choral Sheep groom wedges.

Tries hou wedge cook; falls back to writing JSON previews + a contact sheet
so UE ingest can be tested without Houdini.

Run:
    hython Tools/Houdini/cook_groom_variants.py --out Saved/Audit/choral_sheep/grooms
    python Tools/Houdini/cook_groom_variants.py --out Saved/Audit/choral_sheep/grooms  # fallback
"""
import argparse
import json
from pathlib import Path

SPEC_PATH = Path(__file__).parent / "choral_groom_variants_spec.json"

def cook_with_hou(out: Path):
    import hou
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    hip = Path("Tools/Houdini/choral_sheep_groom.hipnc").resolve()
    if hip.is_file() and hip.stat().st_size > 200:  # real hip, not stub
        hou.hipFile.load(str(hip))
    wedge = hou.node("/out/groom_wedge")
    abc_rop = hou.node("/out/groom_abc_rop")
    if wedge and abc_rop:
        out.mkdir(parents=True, exist_ok=True)
        # Cook wedge — each pc
        for pc in range(12):
            try:
                wedge.parm("pc").set(pc)
            except Exception:
                pass
            abc_rop.render()
            print(f"[groom:cook] pc {pc} -> abc")
        print(f"[groom] hou cook done -> {out}")
        return True
    raise RuntimeError("wedge/abc ROP not found — run build_choral_groom_hip.py under hython first")

def cook_fallback(out: Path):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    # Write per-PC JSON previews that UE groom importer can validate
    for label, params in spec["per_pc_overrides"].items():
        if label.startswith("_"):
            continue
        pc = spec["variant_axis"]["labels"].index(label)
        preview = {
            "pc": pc, "label": label,
            "wool_clump_scale": params["wool_clump_scale"],
            "clump_size": params["clump_size"],
            "curl": params["curl"],
            "density_mult": params["density_mult"],
            "length_cm": params["length_cm"],
            "frizz": params["frizz"],
            "groom_abc": f"Groom_ChoralSheep_PC{label}.abc",
            "shell_fbx": f"FurShell_ChoralSheep_PC{label}.fbx",
            "note": "Fallback preview — run hython build+cook for real Alembic grooms",
        }
        (out / f"Groom_ChoralSheep_PC_{label}.json").write_text(json.dumps(preview, indent=2), encoding="utf-8")
        # placeholder abc (empty but verifies pipeline; real groom needs hython)
        abc = out / f"Groom_ChoralSheep_PC_{label}.abc"
        abc.write_bytes(b"# groom abc placeholder - cook with hython for real strands\n")
        print(f"[groom:fallback] {abc.name} {params}")

    # contact sheet via PIL (visual groom proxy until strands exist)
    try:
        from PIL import Image, ImageDraw
        cols, rows, cell = 4, 3, 256
        sheet = Image.new("RGB", (cols*cell, rows*cell), (235,232,228))
        for i, label in enumerate(spec["variant_axis"]["labels"]):
            if label not in spec["per_pc_overrides"]:
                continue
            p = spec["per_pc_overrides"][label]
            # encode wool_clump_scale as circle size, curl as wavyness hint
            x0, y0 = (i%cols)*cell, (i//cols)*cell
            tile = Image.new("RGB", (cell, cell), (245,243,240))
            d = ImageDraw.Draw(tile)
            # wool puff
            scale = p["wool_clump_scale"]
            r = int(70 + (scale-0.62)/0.06*50)  # 70..120
            cx, cy = cell//2, cell//2+10
            # clump blobs
            for ox, oy in [(-18,-8),(18,-8),(0,12),(-10,18),(10,18)]:
                d.ellipse([cx+ox-r//2, cy+oy-r//2, cx+ox+r//2, cy+oy+r//2], fill=(255,255,255), outline=(200,185,175), width=2)
            # curl hint arc
            curl = p["curl"]
            d.arc([cx-40, cy-30, cx+40, cy+20], start=200, end=340, fill=(160,140,130), width=max(2,int(curl*8)))
            d.text((10,12), f"PC{i:02d} {label}", fill=(60,50,45))
            d.text((10, cell-22), f"clump {scale:.2f} curl {p['curl']:.2f}", fill=(90,80,75))
            sheet.paste(tile, (x0, y0))
        sheet_path = out / "_Groom_ContactSheet.png"
        sheet.save(sheet_path, "PNG")
        print(f"[groom:fallback] contact -> {sheet_path}")
    except ImportError:
        print("[groom] Pillow missing for contact sheet — pip install Pillow")

    print(f"[groom:fallback] done -> {out} (run hython for real ABC)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Saved/Audit/choral_sheep/grooms")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    try:
        import hou
        if cook_with_hou(out):
            raise SystemExit(0)
    except ImportError:
        pass
    except Exception as e:
        print(f"[groom] hou cook failed ({e}) -> fallback")
    cook_fallback(out)
