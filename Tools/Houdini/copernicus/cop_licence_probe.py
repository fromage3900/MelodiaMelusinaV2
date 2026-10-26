"""Does this Houdini licence enforce the COP resolution cap the copernicus modules assume?

CONTEXT. Every module under Tools/Houdini/copernicus/ that falls back to numpy justifies the
fallback with "Apprentice caps COP writes at 1920x1080". Every receipt generated on 2026-10-25
records licenseCategoryType.Indie, so that sentence has been false about the licence since the
licence changed, and nobody re-tested the cap itself.

WHAT THIS DOES. Builds the minimal COP that the H22 truth requires - a constant COP into a null
into an /out image ROP with setres=1 - writes it at each requested resolution, then reads the PNG
IHDR back so the answer is the size that actually landed on disk, not the size requested. It also
decodes the zlib stream far enough to say whether the image is a flat field; a watermark is the
other way a capped licence limits output, so a size check alone would be a half answer.

HOW TO READ THE RESULT. A CLAMPED row means the software enforces a cap. "NOT capped" means the
software writes the requested size and adds nothing - it does NOT mean the licence *terms* permit
shipping above-HD output. The software not stopping you is not permission. This probe measures the
COP write path only; it says nothing about the geometry baker's texture behaviour.

    hython Tools/Houdini/copernicus/cop_licence_probe.py
    hython Tools/Houdini/copernicus/cop_licence_probe.py --sizes 1024,1920,2048,8192

Exit code is 0 whether or not a cap exists - this reports, it does not gate. It never touches the
Unreal editor, never opens a project .hip and writes only under --out.
"""
import argparse
import collections
import json
import os
import struct
import sys
import zlib

CAP_SENTENCE_SIZE = 1920  # the resolution the modules' justification claims is the ceiling


def png_header_and_flatness(path):
    """Return (width, height, distinct_byte_values, row_filter_types) or None if unreadable."""
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None

    pos, idat, width, height = 8, b"", None, None
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", data[:8])
        elif ctype == b"IDAT":
            idat += data
        elif ctype == b"IEND":
            break
        pos += 12 + length
    if width is None or height is None:
        return None

    distinct = None
    filters = {}
    if idat:
        try:
            pixels = zlib.decompress(idat)
        except zlib.error:
            pixels = b""
        if pixels:
            distinct = len(set(pixels))
            stride = len(pixels) // height if height else 0
            counts = collections.Counter()
            if stride:
                for row in range(height):
                    counts[pixels[row * stride]] += 1
            filters = dict(counts)
    return width, height, distinct, filters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="1024,1920,1921,2048,4096",
                    help="comma separated square resolutions to write")
    ap.add_argument("--out", default=os.path.join(os.path.expanduser("~"),
                                                  "AppData", "Local", "Temp",
                                                  "melodia_cop_licence"))
    args = ap.parse_args()
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    os.makedirs(args.out, exist_ok=True)

    import hou  # imported late so --help works outside hython

    report = {
        "kind": "melodia.cop_licence_probe.v1",
        "license_category": str(hou.licenseCategory()),
        "claimed_cap_px": CAP_SENTENCE_SIZE,
        "note": ("Measures the COP write path only. 'not capped' means the software writes the "
                 "requested size without a watermark; it is not a statement that the licence "
                 "terms permit shipping above-HD output."),
        "sizes": [],
    }
    print("[lic] licenseCategory = %s" % (report["license_category"],))

    hou.hipFile.clear(suppress_save_prompt=True)
    copnet = hou.node("/img").createNode("copnet", "cop_licence_probe")
    const = copnet.createNode("constant", "SRC_Const")
    branch = copnet.createNode("null", "BR_Const")
    branch.setInput(0, const)
    outnet = hou.node("/out")

    for size in sizes:
        rop = outnet.createNode("image", "ROP_%d" % size)
        rop.parm("coppath").set(copnet.path() + "/BR_Const")
        rop.parm("aov1").set("C")
        rop.parm("setres").set(1)          # H22 truth: else the ROP downsamples to its own res
        rop.parm("res1").set(size)
        rop.parm("res2").set(size)
        target = os.path.join(args.out, "const_%d.png" % size)
        rop.parm("copoutput").set(target)

        error = ""
        try:
            rop.render()
        except Exception as exc:  # noqa: BLE001 - one size failing must not abort the sweep
            error = str(exc)

        decoded = png_header_and_flatness(target)
        row = {"requested_px": size, "error": error}
        if decoded is None:
            row.update(written=False, actual_px=None, verdict="NO FILE")
        else:
            width, height, distinct, filters = decoded
            row.update(
                written=True,
                actual_px=[width, height],
                bytes=os.path.getsize(target),
                distinct_byte_values=distinct,
                row_filter_types=filters,
                flat_field=(distinct is not None and distinct <= 6),
                verdict="exact" if (width, height) == (size, size) else "CLAMPED",
            )
        report["sizes"].append(row)
        print("[lic] requested %5d -> actual %s  verdict=%s  error=%s"
              % (size, row.get("actual_px"), row["verdict"], error or "none"))

    written = [r for r in report["sizes"] if r.get("written")]
    report["capped"] = any(r["verdict"] == "CLAMPED" for r in written)
    report["all_flat"] = all(r.get("flat_field") for r in written) if written else None
    report["above_claim_written"] = [r["requested_px"] for r in written
                                     if r["requested_px"] > CAP_SENTENCE_SIZE
                                     and r["verdict"] == "exact"]
    report["all_pass"] = bool(written) and all(r["verdict"] in ("exact", "CLAMPED")
                                               for r in written)

    print("\n[lic] capped=%s  un-watermarked above %d px: %s"
          % (report["capped"], CAP_SENTENCE_SIZE, report["above_claim_written"]))
    print("[lic] " + json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
