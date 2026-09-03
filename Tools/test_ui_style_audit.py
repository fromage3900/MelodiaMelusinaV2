#!/usr/bin/env python3
"""Assertions for ui_style_audit's colour handling. No editor required.

Two bugs were caught here rather than by eye, and both would have quietly
corrupted a polish spec:

  1. Clustering keyed on RGBA while measuring distance on RGB, so #FFFFFF at
     seven different opacities split across clusters instead of being one
     colour used at seven opacities.
  2. to_hex clamped HDR channels, so (0,255,250) and (0,255,255) -- two
     genuinely different glow colours -- both printed #00FFFF and looked like
     a duplicate-cluster bug.

Runs against a captured audit if one exists, otherwise synthetic input.

    python Tools/test_ui_style_audit.py
"""
import importlib.util
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
CAPTURE = os.path.join(PROJECT, "Saved", "Dashboards", "ui_tokens.json")

_spec = importlib.util.spec_from_file_location(
    "ui_style_audit", os.path.join(HERE, "ui_style_audit.py"))
ui = importlib.util.module_from_spec(_spec)
sys.modules["ui_style_audit"] = ui
_spec.loader.exec_module(ui)


def synthetic():
    return Counter({
        (1.0, 1.0, 1.0, 1.0): 10,     # white opaque
        (1.0, 1.0, 1.0, 0.5): 4,      # same white, half alpha
        (0.0, 0.0, 0.0, 1.0): 8,
        (0.02, 0.016, 0.035, 0.8): 3,  # near-black, should join black
        (0.0, 235.0, 255.0, 1.0): 2,   # HDR cyan
        (0.0, 255.0, 250.0, 1.0): 2,   # different HDR cyan, clamps identically
        (0.82, 0.82, 0.82, 1.0): 5,
    })


def main():
    if os.path.exists(CAPTURE):
        data = json.load(open(CAPTURE, encoding="utf-8"))
        colors = Counter({tuple(c["rgba"]): c["count"] for c in data["colors"]})
        source = f"captured audit ({len(colors)} colours)"
    else:
        colors = synthetic()
        source = "synthetic fixture"

    clusters = ui.cluster_colors(colors, 0.06)
    results = []

    labels = [ui.to_hex(c["token"] + (1.0,)) for c in clusters]
    dupes = [h for h, n in Counter(labels).items() if n > 1]
    results.append((not dupes, "no two clusters share a display label",
                    f"dupes={dupes}" if dupes else ""))

    total = sum(c["total"] for c in clusters)
    want = sum(colors.values())
    results.append((total == want, "use counts conserved across clustering",
                    f"{total} vs {want}"))

    # alpha must be a property of a token, never a reason to split one
    for cl in clusters:
        if len(cl["alphas"]) > 1:
            results.append((True, "alpha variants held inside one token",
                            f"{ui.to_hex(cl['token'] + (1.0,))} "
                            f"alphas={sorted(cl['alphas'])}"))
            break
    else:
        results.append((True, "alpha variants held inside one token", "(none present)"))

    # HDR must not be clamped into hex
    hdr = [ui.to_hex((0.0, 235.0, 255.0, 1.0)), ui.to_hex((0.0, 255.0, 250.0, 1.0))]
    results.append((hdr[0] != hdr[1], "HDR colours render distinguishably",
                    " vs ".join(hdr)))
    results.append((ui.to_hex((1.0, 0.0, 0.0, 1.0)) == "#FF0000",
                    "in-range colours still render as plain hex",
                    ui.to_hex((1.0, 0.0, 0.0, 1.0))))

    print(f"ui_style_audit colour assertions - {source}\n")
    failed = 0
    for ok, label, note in results:
        print(f"  {'PASS' if ok else '*** FAIL ***'}  {label}"
              + (f"  [{note}]" if note else ""))
        failed += 0 if ok else 1
    print(f"\n=== {len(results) - failed}/{len(results)} passed ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
