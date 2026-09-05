#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
seasons_qa.py - QA + contact-sheet verifier for the seasonal and existing
garment / cymatic / water-veil fabric corpora under Saved/Audit/melusina_lookdev/.

What it does
------------
(1) Verifies expected counts and power-of-two sizes for four corpora:
      a) seasonal variants : 4 seasons x 10 layers x 8 maps
      b) garment_refresh  : 10 layers x 8 maps  (80-map set)
      c) cymatic static   : 10 layers x 9 maps  (90-map set)
      d) water veil       : 4 zones x 9 maps + VeilHeight_4K (37-map set)
(2) Assembles a single-season composite contact sheet (4 rows = Spring/Summer/
    Autumn/Winter) from existing SEASON_*_CONTACT.png rows, falling back to
    per-layer BaseColor maps, else emits a manifest-only report.
(3) Reports any missing map or non-power-of-two size as a FAIL with the exact
    absolute path.

Degrades gracefully: independent of any subagent's data being complete; always
reports what exists. Never touches .uasset, the editor, or git.

Report (seed 20260902, per-corpus {expected, found, pass}, sheet path) is written
to Saved/Audit/universal_garment/seasonal_qa_report.json.

Usage:  python Tools/Houdini/sea_above_reef/seasons_qa.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

SEED = 20260902

_WS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
AUDIT = os.path.join(_WS, "Saved", "Audit", "melusina_lookdev")
TOOL = os.path.join(_WS, "Tools", "Houdini", "sea_above_reef")

# ---------------------------------------------------------------------------
# Corpus specs
# ---------------------------------------------------------------------------
GARMENT_LAYERS = [
    "M_Bodice_Torso", "M_Bodice_Front", "M_Bodice_Side", "M_Bodice_Upper",
    "M_Collar", "M_Shoulder_Trim", "M_Shoulder_Ornament", "M_Sleeve",
    "M_Underskirt", "M_Skirt_Full",
]
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]

# seasonal: 8 maps per layer, matching the season_*_manifest.json "files"
SEASON_MAPS = ["AO", "BaseColor", "Height", "Iridescence",
               "Metal", "Normal", "Roughness", "Sheen"]
SEASON_CONTACT = {
    s: os.path.join(AUDIT, "garment_refresh", "seasons",
                    f"SEASON_{s}_CONTACT.png")
    for s in SEASONS
}

# garment_refresh: same 8-map family (T_Shorewake_Garment_<Layer>_<Map>.png)
GARMENT_MAPS = ["AO", "BaseColor", "Height", "Iridescence",
                "Metal", "Normal", "Roughness", "Sheen"]

# cymatic static: 9-map copernicus-contract set
CYMATIC_MAPS = ["BaseColor", "Emissive", "Height", "Iridescence",
                "Metallic", "Normal", "Opacity", "ORM", "Roughness"]

# water veil: 4 zones x 9 maps + the fallback 4K veil height
WATER_ZONES = ["SheetVeil", "SingingFall", "HearthPool", "TideSeam"]
WATER_MAPS = ["BaseColor", "Emissive", "Height", "Iridescence",
              "Metallic", "Normal", "Opacity", "ORM", "Roughness"]


def corpus_specs():
    """Return list of (name, root, expected_files, expected_count)."""
    specs = []

    def seas_add(name, root, prefix, layers, maps):
        root = os.path.normpath(root)
        files = [os.path.join(root, f"{prefix}{l}_{m}.png")
                 for l in layers for m in maps]
        specs.append((name, root, files, len(files)))

    # (a) seasonal : 4 seasons x 10 layers x 8 maps
    # expected names: T_Shorewake_Season_<Season>_<Layer>_<Map>.png
    seas_root = os.path.join(AUDIT, "garment_refresh", "seasons")
    sfiles = [os.path.join(seas_root,
                           f"T_Shorewake_Season_{s}_{l}_{m}.png")
              for s in SEASONS for l in GARMENT_LAYERS for m in SEASON_MAPS]
    specs.append(("seasonal", seas_root, sfiles, len(sfiles)))
    # Contact sheets (SEASON_<S>_CONTACT.png) are handled separately below.

    # (b) garment_refresh: 10 layers x 8 maps = 80
    seas_add(
        "garment_refresh",
        os.path.join(AUDIT, "garment_refresh"),
        "T_Shorewake_Garment_", GARMENT_LAYERS, GARMENT_MAPS,
    )

    # (c) cymatic static: 10 layers x 9 maps = 90
    seas_add(
        "cymatic",
        os.path.join(AUDIT, "garment_refresh", "cymatic"),
        "T_Cymatic_Garment_", GARMENT_LAYERS, CYMATIC_MAPS,
    )

    # (d) water veil: 4 zones x 9 maps + VeilHeight_4K = 37
    water_root = os.path.join(AUDIT, "singing_water", "cymatic")
    wfiles = [os.path.join(water_root, f"T_SingingWater_{z}_{m}.png")
              for z in WATER_ZONES for m in WATER_MAPS]
    wfiles.append(os.path.join(water_root, "T_SingingWater_VeilHeight_4K.png"))
    specs.append(("water_veil", water_root, wfiles, len(wfiles)))

    return specs


def is_pot(n):
    return n > 0 and (n & (n - 1)) == 0


def probe_root(root, expected_files, expected_count):
    """Verify an expected file set. Returns a dict with expected/found/pass. """
    present = []
    missing = []
    non_pot = []
    for exp in expected_files:
        if os.path.isfile(exp):
            present.append(exp)
        else:
            missing.append(exp)
    # power-of-two size check on what IS present (cheap header read)
    try:
        from PIL import Image
    except Exception:
        Image = None
    for p in present:
        w = h = 0
        if Image is not None:
            try:
                with Image.open(p) as im:
                    w, h = im.size
            except Exception:
                w = h = -1
        else:
            # fallback: parse PNG IHDR width/height without PIL
            with open(p, "rb") as fh:
                head = fh.read(24)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w = int.from_bytes(head[16:20], "big")
                h = int.from_bytes(head[20:24], "big")
        if not (is_pot(w) and is_pot(h)):
            non_pot.append({"path": os.path.abspath(p), "size": [w, h]})

    missing_abs = [{"path": os.path.abspath(m)} for m in missing]
    ok = (len(present) == expected_count and not missing and not non_pot)
    return {
        "expected": expected_count,
        "found": len(present),
        "pass": ok,
        "missing": missing_abs,
        "non_pot": non_pot,
        "root": os.path.abspath(root),
    }


# ---------------------------------------------------------------------------
# Contact sheet assembly
# ---------------------------------------------------------------------------
def build_composite_sheet(outdir):
    """Stack the 4 SEASON_*_CONTACT.png rows vertically. Fall back to per-layer
    BaseColor maps, else manifest-only. Returns sheet path or None."""
    rows = []
    for s in SEASONS:
        p = SEASON_CONTACT[s]
        if os.path.isfile(p):
            rows.append((s, p))
        else:
            rows.append((s, None))

    have_any_row = any(r[1] for r in rows)
    if not have_any_row:
        # fall back to BaseColor maps: one row per season, 10 layer columns
        row_imgs = []
        for s in SEASONS:
            cells = []
            for l in GARMENT_LAYERS:
                f = os.path.join(AUDIT, "garment_refresh", "seasons",
                                 f"T_Shorewake_Season_{s}_{l}_BaseColor.png")
                cells.append(f if os.path.isfile(f) else None)
            if any(cells):
                row_imgs.append((s, cells))
        if not row_imgs:
            return None
        try:
            from PIL import Image
        except Exception:
            return None
        thumb = 64
        row_h = thumb + 16
        # width: 10 columns + padding
        sheets = []
        for s, cells in row_imgs:
            row = Image.new("RGB", (thumb * 10 + 20, row_h), (20, 20, 24))
            for ci, f in enumerate(cells):
                if f:
                    try:
                        im = Image.open(f).convert("RGB")
                        im.thumbnail((thumb, thumb))
                        row.paste(im, (10 + ci * thumb, 8))
                    except Exception:
                        pass
            sheets.append(row)
            # label band with season name is omitted for simplicity; manifest
            # records which rows assembled.
        W = max(im.width for im in sheets)
        H = sum(im.height for im in sheets)
        canvas = Image.new("RGB", (W, H), (20, 20, 24))
        y = 0
        for im in sheets:
            canvas.paste(im, (0, y))
            y += im.height
        os.makedirs(outdir, exist_ok=True)
        sp = os.path.join(outdir, "seasonal_composite_contact.png")
        canvas.save(sp)
        return sp

    # primary path: use existing SEASON_*_CONTACT rows
    try:
        from PIL import Image
    except Exception:
        Image = None
    if Image is None:
        return None
    loaded = []
    for s, p in rows:
        if p:
            try:
                loaded.append(Image.open(p).convert("RGB"))
            except Exception:
                loaded.append(None)
        else:
            loaded.append(None)
    if not any(loaded):
        return None
    imgs = [im for im in loaded if im is not None]
    W = max(im.width for im in imgs)
    H = sum(im.height for im in imgs)
    canvas = Image.new("RGB", (W, H), (20, 20, 24))
    y = 0
    for s, im in zip(SEASONS, loaded):
        if im is not None:
            canvas.paste(im, (0, y))
            y += im.height
    os.makedirs(outdir, exist_ok=True)
    sp = os.path.join(outdir, "seasonal_composite_contact.png")
    canvas.save(sp)
    return sp


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    report = {
        "schema": "melodia.seasons_qa.v1",
        "seed": SEED,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": os.path.abspath(__file__),
        "audit_root": os.path.abspath(AUDIT),
        "per_corpus": {},
        "sheet_path": None,
        "sheet_basis": "manifest-only",
        "overall_pass": None,
    }

    for name, root, expected_files, expected_count in corpus_specs():
        res = probe_root(root, expected_files, expected_count)
        report["per_corpus"][name] = res
        if res.get("missing"):
            report.setdefault("corpus_missing", {})[name] = res["missing"]
        if res.get("non_pot"):
            report.setdefault("corpus_non_pot", {})[name] = res["non_pot"]

    # composite sheet
    outdir = os.path.join(_WS, "Saved", "Audit", "universal_garment")
    sheet = build_composite_sheet(outdir)
    if sheet:
        report["sheet_path"] = os.path.abspath(sheet)
        report["sheet_basis"] = "season_contact_rows" \
            if all(os.path.isfile(SEASON_CONTACT[s]) for s in SEASONS) \
            else "basemap_rows"
    else:
        report["sheet_path"] = None
        report["sheet_basis"] = "manifest-only"

    passes = [res["pass"] for res in report["per_corpus"].values()]
    report["overall_pass"] = all(passes) if passes else None

    os.makedirs(os.path.dirname(os.path.join(_WS, "Saved", "Audit",
                                             "universal_garment")), exist_ok=True)
    out_report = os.path.join(outdir, "seasonal_qa_report.json")
    with open(out_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("REPORT:", os.path.abspath(out_report))
    print("SHEET:", report["sheet_path"])
    print(json.dumps(report["per_corpus"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())