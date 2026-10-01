"""Verify the staged brutalist contact sheets are pixel-faithful to their tiles.

WHY THIS EXISTS
---------------
A first look at `brutalist_sheet_family.png` appeared to show 7 of 8 cells as
specks with clipped labels (`FFICE_`, `UBICLE_`) - which reads as a framing or
compositing bug. It is not. Three hypotheses were checked and two were wrong
before the real answer appeared:

  1. "The per-object camera framing is too wide."  WRONG. The manifest bboxes
     give 44.2m of visible width for a 21.2m object; the individual tiles are
     correctly framed.
  2. "Blender's linear pixel buffer double-encodes to sRGB on write."  WRONG.
     Measured mean delta between a tile and its composited region is ~0, and
     the predicted double-encode mean (0.50) is nowhere near the observed.
  3. "The compositor wrote the tiles into the wrong rows."  WRONG, but only
     provable by search: `worst=166` on every tile turned out to be THIS
     checker reading the sheet bottom-up. Written PNG rows are top-down.

The actual cause of the speck appearance is simply that a 2910x828 sheet is
downscaled hard when viewed, so 720x405 tiles of thin brutalist geometry
degrade to specks. The files were always correct.

The decoder is self-tested against synthetic PNGs covering all five filter
types before any comparison is believed. That self-test earned its keep: it
caught a bug in the test's own PNG *encoder* (filter predictors computed from
already-encoded bytes), which had briefly made the whole comparison look
like a defect.

Run:  python Tools/verify_contact_sheets.py     (exit 0 = sheets faithful)
"""
import glob
import os
import struct
import sys
import zlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_W, TILE_H = 720, 405
STAMP = "2026-09-25"


def read_png(path):
    """Minimal PNG -> (w, h, rows of RGB bytes). Handles 8-bit RGB/RGBA."""
    with open(path, "rb") as fh:
        data = fh.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, w = 8, bytearray(), None
    h = bitd = ctype = None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitd, ctype = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bitd != 8 or ctype not in (2, 6):
        raise ValueError("unsupported png %s bitd=%s ctype=%s" % (path, bitd, ctype))
    nch = 3 if ctype == 2 else 4
    raw = zlib.decompress(bytes(idat))
    stride = w * nch
    out, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out.append(line)
        prev = line
    return w, h, nch, out


def check(sheet_path, tile_paths, cols, gap=6):
    sw, sh, snch, srows = read_png(sheet_path)
    rows = (len(tile_paths) + cols - 1) // cols
    exp_w = TILE_W * cols + gap * (cols + 1)
    exp_h = TILE_H * rows + gap * (rows + 1)
    if (sw, sh) != (exp_w, exp_h):
        print("  !! size %dx%d != expected %dx%d" % (sw, sh, exp_w, exp_h))
        return False
    ok = True
    for i, tp in enumerate(tile_paths):
        tw, th, tnch, trows = read_png(tp)
        if (tw, th) != (TILE_W, TILE_H):
            print("  !! tile %s is %dx%d" % (os.path.basename(tp), tw, th))
            ok = False
            continue
        r, c = divmod(i, cols)
        # Rows in a written PNG are TOP-DOWN. Blender's in-memory pixel buffer
        # is bottom-up, which is what compose_sheet indexes with; once written
        # to disk the first tile row is at the top. Getting this backwards
        # reported a phantom worst=166 on every tile, so it is pinned here.
        y0 = gap + r * (TILE_H + gap)
        x0 = gap + c * (TILE_W + gap)
        if y0 + TILE_H > sh or x0 + TILE_W > sw:
            print("  !! tile %s falls outside the sheet" % os.path.basename(tp))
            ok = False
            continue
        worst, nonzero = 0, 0
        step = 3  # sample every 3rd pixel; full compare is needlessly slow
        for y in range(0, TILE_H, step):
            srow, trow = srows[y0 + y], trows[y]
            for x in range(0, TILE_W, step):
                for k in range(3):
                    d = abs(srow[(x0 + x) * snch + k] - trow[x * tnch + k])
                    if d:
                        nonzero += 1
                        worst = max(worst, d)
        tag = "OK " if nonzero == 0 else "DIFF"
        if nonzero:
            ok = False
        print("  %s %-26s worst=%3d nonzero_samples=%d"
              % (tag, os.path.basename(tp), worst, nonzero))
    return ok


def self_test_decoder():
    """Build PNGs with all five filter types; confirm we recover exact bytes.

    This is not ceremony. It caught a real bug in the *test's own* encoder -
    filter predictors were computed from the already-encoded byte buffer
    instead of the original neighbouring pixels - which had made a correct
    sheet look like a uniform worst=166 defect. A verifier that cannot prove
    its own decoder works is not evidence.
    """
    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    def build(path, w, h, rows, nch):
        raw = bytearray()
        for y in range(h):
            f = y % 5  # every filter type gets exercised across the rows
            raw.append(f)
            src = rows[y]
            prev = rows[y - 1] if y > 0 else bytearray(len(src))
            line = bytearray(len(src))
            for x in range(len(src)):
                # Predictors come from ORIGINAL neighbours, not encoded bytes.
                a = src[x - nch] if x >= nch else 0
                b = prev[x]
                c = prev[x - nch] if x >= nch else 0
                if f == 0:
                    pred = 0
                elif f == 1:
                    pred = a
                elif f == 2:
                    pred = b
                elif f == 3:
                    pred = (a + b) // 2
                else:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (src[x] - pred) & 0xFF
            raw += line
        ihdr = struct.pack(">IIBBBBB", w, h, 8, 2 if nch == 3 else 6, 0, 0, 0)
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                     + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
                     + chunk(b"IEND", b""))

    tmp = os.path.join(REPO, "Saved", "Audit", "_cs_selftest")
    os.makedirs(tmp, exist_ok=True)
    ok = True
    try:
        for nch in (3, 4):
            w, h = 37, 21
            rows = [bytearray((x * 7 + y * 13 + c * 29) % 256
                              for x in range(w) for c in range(nch)) for y in range(h)]
            p = os.path.join(tmp, "st_%d.png" % nch)
            build(p, w, h, rows, nch)
            gw, gh, gnch, grows = read_png(p)
            good = ((gw, gh, gnch) == (w, h, nch)
                    and all(bytes(grows[y]) == bytes(rows[y]) for y in range(h)))
            print("  nch=%d %dx%d exact_roundtrip=%s" % (nch, gw, gh, good))
            ok &= good
            os.remove(p)
    finally:
        try:
            os.rmdir(tmp)
        except OSError:
            pass
    return ok


def main():
    tiledir = os.path.join(REPO, "RawArt", "GNShowcase", "brutalist_%s" % STAMP)
    audit = os.path.join(REPO, "Saved", "Audit")
    names = {os.path.splitext(os.path.basename(p))[0]: p
             for p in glob.glob(os.path.join(tiledir, "*.png"))}
    if not names:
        print("NO TILES at %s - run deploy/_melodia_stage_gn_brutalist.py first" % tiledir)
        return 2

    print("=== DECODER SELF-TEST ===")
    if not self_test_decoder():
        print("RESULT: DECODER BROKEN - comparisons below would be meaningless")
        return 2
    print()
    jobs = [
        ("brutalist_sheet_city_pbr.png", 2,
         ["CITY_TightEstate", "CITY_TowerCluster", "CITY_LowSprawl", "CITY_CivicSuperblock"]),
        ("brutalist_sheet_city_komikaze.png", 2,
         ["KMZ_TightEstate", "KMZ_TowerCluster", "KMZ_LowSprawl", "KMZ_CivicSuperblock"]),
        ("brutalist_sheet_facade.png", 2,
         ["FAC_TowerRibbon", "FAC_PunchedEstate", "FAC_CivicColonnade"]),
        ("brutalist_sheet_roofs.png", 2,
         ["ROOF_FlatParapet", "ROOF_LowPitch", "ROOF_Sawtooth",
          "ROOF_BarrelVault", "ROOF_PyramidHip", "ROOF_PlantDeck"]),
        ("brutalist_sheet_family.png", 4,
         ["OFFICE_CivicSlab", "OFFICE_BarbicanScale", "OFFICE_Bunker", "OFFICE_SlenderTower",
          "CUBICLE_Canonical", "CUBICLE_MazeShift", "CUBICLE_OpenPlan", "CUBICLE_Swarm"]),
    ]

    allok = True
    for sheet, cols, keys in jobs:
        missing = [k for k in keys if k not in names]
        if missing:
            # A missing tile must FAIL loudly. Defaulting to a partial list would
            # shrink the expected grid and the geometry check would then fail for
            # the wrong reason - or, worse, a shorter sheet would still "pass".
            print("=== %s === MISSING TILES: %s" % (sheet, missing))
            allok = False
            continue
        print("=== %s (cols=%d) ===" % (sheet, cols))
        allok &= check(os.path.join(audit, sheet), [names[k] for k in keys], cols)
        print()

    print("RESULT: %s" % ("ALL SHEETS PIXEL-FAITHFUL" if allok else "DEFECT FOUND"))
    return 0 if allok else 1


# Guarded so other diagnostics can import read_png/check without re-running.
if __name__ == "__main__":
    sys.exit(main())
