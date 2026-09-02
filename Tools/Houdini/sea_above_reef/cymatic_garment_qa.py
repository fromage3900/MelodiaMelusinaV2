#!/usr/bin/env python
"""Cymatic garment kit QA + contact sheet (2026-09-02).

Verifies the cymatic garment output corpus against the expected counts and
manifest seed, checks each layer's static 9-map set + 8-frame animated set are
present and power-of-two, then assembles a contact sheet of the static
BaseColor maps (and one animated frame row) for visual inspection.

Run after shorewake_cymatic_garment.py:
  ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/cymatic_garment_qa.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
CY = PROJECT / "Saved/Audit/melusina_lookdev/garment_refresh/cymatic"
ANIM = CY / "animated"
EXPECTED_LAYERS = [
    "M_Bodice_Torso", "M_Bodice_Front", "M_Bodice_Side", "M_Bodice_Upper",
    "M_Collar", "M_Shoulder_Trim", "M_Shoulder_Ornament", "M_Sleeve",
    "M_Underskirt", "M_Skirt_Full",
]
CHANNELS = ["BaseColor", "Normal", "Height", "Roughness", "Metallic",
            "Iridescence", "Emissive", "ORM", "Opacity"]
ANIM_CH = ["BaseColor", "Normal", "Iridescence", "Emissive", "Height"]
FRAMES = 8


def main():
    manifest_p = CY / "cymatic_garment_manifest.json"
    if manifest_p.exists():
        man = json.loads(manifest_p.read_text(encoding="utf-8"))
        params = man.get("params", {})
        print(f"[qa] manifest: seed={man['seed']} files={len(man['files'])}"
              f" modes={params.get('modes')}")
    else:
        params = {}
        print("[qa] WARNING manifest not present yet (cook incomplete?)")

    checks, fail = [], []
    # static: 10 layers x 9 channels
    for layer in EXPECTED_LAYERS:
        for ch in CHANNELS:
            f = CY / f"T_Cymatic_Garment_{layer}_{ch}.png"
            if f.exists():
                im = Image.open(f)
                checks.append(("static", layer, ch, f.name, im.size))
            else:
                fail.append(f"missing static {layer}/{ch}")
    # animated: 10 layers x 8 frames x 5 channels
    for layer in EXPECTED_LAYERS:
        for fr in range(FRAMES):
            for ch in ANIM_CH:
                f = ANIM / f"T_Cymatic_Garment_{layer}_Frame{fr:02d}_{ch}.png"
                if f.exists():
                    im = Image.open(f)
                    checks.append(("anim", layer, f"Frame{fr:02d}", ch, im.size))
                else:
                    fail.append(f"missing anim {layer} Frame{fr:02d}/{ch}")

    static_ok = sum(1 for c in checks if c[0] == "static")
    anim_ok = sum(1 for c in checks if c[0] == "anim")
    expected_static = len(EXPECTED_LAYERS) * len(CHANNELS)
    expected_anim = len(EXPECTED_LAYERS) * FRAMES * len(ANIM_CH)
    print(f"[qa] static {static_ok}/{expected_static}  animated {anim_ok}/{expected_anim}")

    # power-of-two + aspect
    bad_pot = [c for c in checks if c[4][0] not in (1024, 2048, 4096)
               or c[4][0] != c[4][1]]
    if bad_pot:
        fail.append(f"non-POT/aspect: {bad_pot[:3]}")

    # basecolor contact sheet
    if static_ok == expected_static:
        sheets = []
        ims = [Image.open(CY / f"T_Cymatic_Garment_{l}_BaseColor.png").convert("RGB")
               for l in EXPECTED_LAYERS]
        # one row, side by side, labeled
        cell = 256
        rows = 2
        cols = (len(ims) + rows - 1) // rows
        W = cols * cell + 40
        H = rows * cell + 40
        sheet = Image.new("RGB", (W, H), (10, 10, 14))
        draw = ImageDraw.Draw(sheet)
        for i, im in enumerate(ims):
            r, c = divmod(i, cols)
            im = im.resize((cell - 4, cell - 4))
            sheet.paste(im, (40 + c * cell + 2, 40 + r * cell + 2))
            draw.text((40 + c * cell + 4, 40 + r * cell + 2),
                      EXPECTED_LAYERS[i].replace("M_", "M_"), fill=(255, 255, 255))
        cp = CY / "CYMATIC_GARMENT_BASECOLOR_CONTACT.png"
        sheet.save(cp)
        print(f"[qa] contact sheet -> {cp.name}")
    else:
        print("[qa] skipping contact sheet (static incomplete)")

    print(f"[qa] {'PASS' if not fail else 'FAIL'}")
    for f in fail[:20]:
        print(f"   - {f}")
    sys.exit(0 if not fail else 1)


if __name__ == "__main__":
    main()