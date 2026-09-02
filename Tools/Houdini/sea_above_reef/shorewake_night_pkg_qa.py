#!/usr/bin/env python
"""QA + package for the Shorewake night bake package.

Verifies every PNG opens, records sha256 + dimensions, asserts:
  - slotted OBJ has 48 distinct usemtl groups
  - ID map has 48 covered panels (census from panel_id_manifest)
  - all kit textures are square, power-of-two
Renders a contact sheet PNG. Writes package manifest + README.

Run: python Tools/Houdini/sea_above_reef/shorewake_night_pkg_qa.py
"""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[3]
PKG = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "bake" / "night_pkg_2026-08-31"

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})


# 1. OBJ usemtl census
obj = PKG / "SM_ShorewakeDress_48MAT_v2_slotted.obj"
usemtl = sorted(set(re.findall(r"^usemtl (\S+)", obj.read_text(encoding="utf-8", errors="ignore"),
                               re.MULTILINE)))
check("obj_48_usemtl", len(usemtl) == 48, f"{len(usemtl)} groups; first={usemtl[:3]} last={usemtl[-3:]}")
check("obj_names_p01_p48", usemtl[:1] == ["SW_Dress_P01"] and usemtl[-1:] == ["SW_Dress_P48"], usemtl[:1] + usemtl[-1:])

# 2. ID map census
pid = json.loads((PKG / "panel_id_manifest.json").read_text())
zero = [k for k, v in pid["coverage"].items() if v["px"] == 0]
check("idmap_48_panels", pid["slot_count"] == 48, f"slot_count={pid['slot_count']}")
check("idmap_no_zero_coverage", not zero, f"zero={zero}")
check("idmap_black_is_padding", 20 <= pid["unassigned_black_pct"] <= 50,
      f"{pid['unassigned_black_pct']}%")

# 3. texture inventory: opens, square, POT
pot = lambda n: n > 0 and (n & (n - 1)) == 0
inv = {}
for png in sorted(PKG.glob("*.png")):
    with Image.open(png) as im:
        w, h = im.size
        im.verify()
    inv[png.name] = {"w": w, "h": h, "bytes": png.stat().st_size}
    nm = png.name.lower()
    dress_space = ("legend" in nm or "contact" in nm
                   or "painterly_drape" in nm or "foamcrest" in nm
                   or "panelid_4k" in nm)
    if not dress_space:
        check(f"pot_{png.name}", pot(w) and pot(h) and w == h, f"{w}x{h}")

# 4. sha256 for every package file
hashes = {}
for f in sorted(PKG.iterdir()):
    if f.is_file() and f.suffix != ".json":
        hashes[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()

# 5. contact sheet
tiles = ["T_Shorewake_PearlWeave_Height.png", "T_Shorewake_PearlWeave_Normal.png",
         "T_Shorewake_PearlWeave_AO.png", "T_Shorewake_PearlWeave_Roughness.png",
         "T_Shorewake_ChladniWeave_N.png", "T_Shorewake_PearlSheen_Iridescence.png",
         "T_Shorewake_PearlSheen_Strength.png", "T_Shorewake_Painterly_BaseColor.png",
         "T_Shorewake_Painterly_Height.png"]
CELL = 512
sheet = Image.new("RGB", (CELL * 4, CELL * 3 + 40), (18, 18, 22))
sd = ImageDraw.Draw(sheet)
try:
    fnt = ImageFont.truetype("arial.ttf", 22)
except Exception:
    fnt = ImageFont.load_default()
labels = ["Weave Height", "Weave Normal", "Weave AO", "Weave Roughness",
          "Chladni n=5,m=7 N", "Pearl Iridescence", "Sheen Strength", "Painterly Base",
          "Painterly Height"]
for i, (t, lab) in enumerate(zip(tiles, labels)):
    im = Image.open(PKG / t).convert("RGB").resize((CELL - 8, CELL - 8))
    x, y = (i % 4) * CELL, (i // 4) * (CELL + 30)
    sheet.paste(im, (x + 4, y + 24))
    sd.text((x + 8, y + 2), lab, fill=(230, 230, 230), font=fnt)
idim = Image.open(PKG / "T_DressShorewake_PanelID_4K.png").resize((CELL - 8, CELL - 8))
sheet.paste(idim, (3 * CELL + 4, 2 * (CELL + 30) + 24))
sd.text((3 * CELL + 8, 2 * (CELL + 30) + 2), "Panel ID 4K (48 slots)",
        fill=(230, 230, 230), font=fnt)
sheet.save(PKG / "NIGHT_PKG_contact_sheet.png")

# 6. package manifest
manifest = {
    "schema": "melodia.shorewake_night_pkg.v1",
    "date": "2026-08-31",
    "purpose": "Slotted (48-material) bake mesh + bake maps + pearl-weave/painterly kit "
               "for Substance hand-paint, then UE import",
    "checks": CHECKS,
    "all_pass": all(c["ok"] for c in CHECKS),
    "texture_inventory": inv,
    "sha256": hashes,
    "inputs": {
        "source_blend": "Saved/Audit/melusina_lookdev/Shorewake_48MAT_frozen_snapshot.blend",
        "bake_of_record": "bake/sbs/ (sbsbaker 4K: AO/Normal/Curv/Thick/Position)",
        "id_map": "T_DressShorewake_PanelID_4K.png (48 flat colors, luminance-ordered)",
    },
    "workflows": {
        "merged_paint": "one texture set + PanelID mask colors == per-panel control "
                        "(fill layer -> black mask -> ID color extract)",
        "per_panel_sets": "import slotted FBX; Substance creates 48 texture sets "
                          "(SW_Dress_P01..P48); UE MIs already exist in "
                          "/Game/Melodia/Characters/Melusina/Textures/Clothes/",
    },
}
(PKG / "night_pkg_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("QA " + json.dumps({"all_pass": manifest["all_pass"],
                          "fails": [c["name"] for c in CHECKS if not c["ok"]],
                          "files": len(hashes)}))
