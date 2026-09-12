#!/usr/bin/env python3
"""Assertions for the Chladni pattern foundry. No editor, no network required.

    python Tools/test_chladni_foundry.py
"""
import importlib.util
import json
import os
import random
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)

_spec = importlib.util.spec_from_file_location(
    "ollama_chladni_foundry_daemon",
    os.path.join(PROJECT, "deploy", "ollama_chladni_foundry_daemon.py"))
cf = importlib.util.module_from_spec(_spec)
sys.modules["ollama_chladni_foundry_daemon"] = cf
_spec.loader.exec_module(cf)


def main():
    results = []

    def check(ok, label, note=""):
        results.append((bool(ok), label, str(note)))

    # Bessel sanity against known zeros of J_n.
    check(abs(cf.bessel_j(0, 2.4048)) < 1e-3, "J0 zero near 2.4048",
          f"J0(2.4048)={cf.bessel_j(0, 2.4048):.5f}")
    check(abs(cf.bessel_j(1, 3.8317)) < 1e-3, "J1 zero near 3.8317",
          f"J1(3.8317)={cf.bessel_j(1, 3.8317):.5f}")
    z01 = cf.bessel_zero(0, 1)
    check(abs(z01 - 2.4048) < 1e-3, "bessel_zero(0,1) brackets correctly", f"{z01:.5f}")

    # Temperament sanity: C4 and A4.
    check(cf.note_hz("C", 4) == 261.63, "C4 == 261.63 Hz", cf.note_hz("C", 4))
    check(cf.note_hz("A" if "A" in cf.PITCH else "G", 4) > 0, "note_hz returns positive", "")

    # Known square mode has real nodal content.
    spec11 = {"id": "t", "family": "C", "geometry": "square",
              "notes": [], "modes": [{"n": 1, "m": 1, "w": 1.0}], "seed": 1}
    segs11 = cf.marching_squares(cf.square_field(spec11))
    check(len(segs11) > 40, "square (1,1)+ mode has nodal segments", f"{len(segs11)} segs")

    # Circular (0,1): one nodal circle, no spokes.
    spec01 = {"id": "t", "family": "C", "geometry": "circular",
              "notes": [], "modes": [{"n": 0, "p": 1, "phase": 0.0}], "seed": 1}
    circles, spokes = cf.circular_analytic(spec01)
    check(circles == [1.0] and spokes == [], "(0,1) exact nodal set",
          f"circles={circles} spokes={spokes}")

    # Circular (2,1): rim circle + 4 spokes.
    spec21 = {"id": "t", "family": "C", "geometry": "circular",
              "notes": [], "modes": [{"n": 2, "p": 1, "phase": 0.0}], "seed": 1}
    circles2, spokes2 = cf.circular_analytic(spec21)
    check(circles2 == [1.0] and len(spokes2) == 4, "(2,1) rim + 4 spokes",
          f"{len(spokes2)} spokes")

    # Determinism: same spec -> identical sheet + SVG bytes.
    rng = random.Random(7)
    got = None
    for _ in range(20):
        spec = cf.sample_candidate(rng)
        sheet, svg = cf.build_sheet(spec, no_ollama=True)
        if sheet is not None:
            got = (spec, sheet, svg)
            break
    check(got is not None, "mintable candidate found within 20 samples", "")
    if got:
        spec, sheet, svg = got
        sheet2, svg2 = cf.build_sheet(spec, no_ollama=True)
        check(sheet2 == sheet and svg2 == svg, "same spec -> byte-identical sheet+SVG", "")

    # Schema completeness.
    if got:
        need = {"schema", "id", "family", "notes", "geometry", "modes", "seed",
                "rank", "nodal_length", "scores", "rank_weights", "display_name",
                "production_note", "name_model", "palette", "palette_provenance", "status"}
        check(set(sheet) >= need, "sheet carries full schema", f"missing={need - set(sheet)}")
        check(sheet["schema"] == cf.SCHEMA, "schema tag matches", sheet["schema"])
        check(0.0 <= sheet["rank"] <= 1.0, "rank in [0,1]", sheet["rank"])

    # SVG well-formed + palette-faithful.
    if got:
        try:
            root = ET.fromstring(svg)
            strokes = {e.get("stroke") for e in root.iter() if e.get("stroke")}
            ok = all(s in set(cf.PALETTE.values()) for s in strokes)
            check(ok, "all stroke colors from locked palette", f"{len(strokes)} colors")
        except ET.ParseError as e:
            check(False, "SVG parses", str(e))
        check(len(svg) < 200000, "SVG stays small", f"{len(svg)} bytes")

    # Ranker rejects empties and fields of pure noise only via None (no crash).
    empty = {"id": "t", "family": "C", "geometry": "square",
             "notes": [], "modes": [{"n": 1, "m": 1, "w": 0.0}], "seed": 1}
    try:
        cf.score_candidate(empty)
        check(True, "ranker never raises on degenerate field", "")
    except Exception as e:
        check(False, "ranker never raises on degenerate field", str(e))

    # Export round-trip: build a sheet in a temp shelf, export, verify files.
    with tempfile.TemporaryDirectory() as td:
        import pathlib
        bak_out = cf.OUT
        cf.OUT = pathlib.Path(td) / "shelf"
        try:
            rngx = random.Random(23)
            specx, sheetx, svgx = None, None, None
            for _ in range(30):
                cand = cf.sample_candidate(rngx)
                built, art = cf.build_sheet(cand, no_ollama=True)
                if built is not None:
                    specx, sheetx, svgx = cand, built, art
                    break
            check(sheetx is not None, "export fixture minted", "")
            if sheetx is not None:
                cf.write_sheet(sheetx, svgx)
                dest = pathlib.Path(td) / "exp"
                n = cf.export_sheets([sheetx["id"]], dest)
                check(n == 1, "export writes one sheet set", f"n={n}")
                idx = (dest / "INDEX.md").read_text(encoding="utf-8")
                check(sheetx["id"] in idx, "INDEX.md lists the sheet id", "")
                html = (dest / "contact_sheet.html").read_text(encoding="utf-8")
                check("<figure>" in html, "contact sheet embeds the SVG preview", "")
                n2 = cf.export_sheets([sheetx["id"]], dest)
                check(n2 == 1, "re-export is stable", f"n2={n2}")
        finally:
            cf.OUT = bak_out

    # Naming batch is a pure offline no-op when no_ollama is set.
    demo2 = {"id": "Demo_Y", "geometry": "square",
             "modes": [{"n": 1, "m": 1, "w": 1.0}], "family": "C"}
    cf.name_sheets_batch([demo2], no_ollama=True)
    check("display_name" not in demo2, "offline naming leaves sheet untouched", "")
    check("C" in cf.fallback_name({"geometry": "square",
                                   "modes": [{"n": 1, "m": 1, "w": 1.0}],
                                   "family": "C"}),
          "fallback naming is deterministic and readable", "")

    # Filters: family/geometry-pinned sampling always honors the pin.
    rngf = random.Random(11)
    pinned = [cf.sample_candidate(rngf, family="C", geometry="circular")
              for _ in range(10)]
    check(all(s["family"] == "C" and s["geometry"] == "circular" for s in pinned),
          "--family/--geometry pins honored", "")

    # Stop marker honored: pre-set marker dir -> loop exits immediately.
    with tempfile.TemporaryDirectory() as td:
        import pathlib
        mark = pathlib.Path(td) / "STOP"
        mark.write_text("", encoding="utf-8")
        args = cf.parse_args(["--once", "5", "--no-ollama"])
        made = cf.run_loop(args, random.Random(1), stops=[mark])
        check(made == 0, "stop marker exits loop before minting", f"made={made}")

    print("chladni foundry assertions\n")
    failed = 0
    for ok, label, note in results:
        print(f"  {'PASS' if ok else '*** FAIL ***'}  {label}" + (f"  [{note}]" if note else ""))
        failed += 0 if ok else 1
    print(f"\n=== {len(results) - failed}/{len(results)} passed ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
