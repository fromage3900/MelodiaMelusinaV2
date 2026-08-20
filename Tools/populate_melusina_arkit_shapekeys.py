#!/usr/bin/env python3
"""Give Melusina's empty ARKit shape keys real deltas, copied from their FACS twins.

THE SITUATION
-------------
`simply_coll` carries 121 key blocks (Basis + 120). Unreal imports 68. The 52 that do
not arrive are the entire ARKit block, and they are not being lost in transit -- every
one of them is bit-identical to the Basis (max deviation < 1e-7). They are empty shells:
named, never sculpted. Unreal correctly discards zero-delta morph targets, and no export
or import setting can recover something that was never there.

What DOES have real deltas is the 46-key FACS-style set plus 21 visemes. Those import
fine. So the ARKit names are a naming convention laid over expressions that already
exist under different names.

THE APPROACH
------------
Copy the vertex deltas from each FACS key onto its ARKit equivalent. This is a data
operation on shape key coordinates -- no sculpting, no solver, nothing invented. Where
two FACS keys correspond to one ARKit key (e.g. `innerBrowRaiserL` + `innerBrowRaiserR`
-> `browInnerUp`), the deltas are summed, which is what those combined ARKit shapes mean.

Keys with no FACS source are LEFT EMPTY and reported. They are genuinely unauthored:
the eight `eyeLook*` directions, `eyeSquint*`, `eyeWide*`, `jawForward/Left/Right`,
`mouthRoll*`, `mouthShrug*`, `mouthClose`, `tongueOut`. Those need either sculpting or
Faceit's own generation, and this script will not fake them.

WHY NOT FACEIT
--------------
Faceit 2.3.56 is installed (extensions/user_default/faceit) and can do a richer job,
including generating the missing directional eye shapes from the rig. That is the better
long-term route. This script exists because it is deterministic, headless, reviewable,
and needs no UI -- it closes most of the gap now without committing to a Faceit rebuild.

SAFETY
------
Dry-run by default. Only writes to keys that are currently empty; refuses to overwrite a
key that already has deltas. Never saves over the input.

USAGE
-----
    blender --background --factory-startup <stage>.blend \
        --python Tools/populate_melusina_arkit_shapekeys.py
    blender --background --factory-startup <stage>.blend \
        --python Tools/populate_melusina_arkit_shapekeys.py -- --apply --save-as <out>.blend
"""

from __future__ import annotations

import sys

import bpy

MESH = "simply_coll"
EPS = 1e-6

# ARKit target -> the FACS key(s) that carry the same expression.
# Multiple sources are summed: ARKit's combined shapes (browInnerUp, cheekPuff) have no
# per-side equivalent, so both sides contribute.
MAPPING: dict[str, tuple[str, ...]] = {
    "eyeBlinkLeft":        ("eyesCloseL",),
    "eyeBlinkRight":       ("eyesCloseR",),
    "browDownLeft":        ("browLowerL",),
    "browDownRight":       ("browLowerR",),
    "browInnerUp":         ("innerBrowRaiserL", "innerBrowRaiserR"),
    "browOuterUpLeft":     ("outerBrowRaiserL",),
    "browOuterUpRight":    ("outerBrowRaiserR",),
    "cheekPuff":           ("cheekPuffL", "cheekPuffR"),
    "cheekSquintLeft":     ("cheekRaiserL",),
    "cheekSquintRight":    ("cheekRaiserR",),
    "noseSneerLeft":       ("noseWrinklerL",),
    "noseSneerRight":      ("noseWrinklerR",),
    "jawOpen":             ("jawDrop",),
    "mouthSmileLeft":      ("lipCornerPullerL",),
    "mouthSmileRight":     ("lipCornerPullerR",),
    "mouthFrownLeft":      ("lipCornerDepressorL",),
    "mouthFrownRight":     ("lipCornerDepressorR",),
    "mouthDimpleLeft":     ("dimplerL",),
    "mouthDimpleRight":    ("dimplerR",),
    "mouthStretchLeft":    ("lipStretcherL",),
    "mouthStretchRight":   ("lipStretcherR",),
    "mouthUpperUpLeft":    ("upperLipRaiserL",),
    "mouthUpperUpRight":   ("upperLipRaiserR",),
    "mouthLowerDownLeft":  ("lowerLipDepressorL",),
    "mouthLowerDownRight": ("lowerLipDepressorR",),
    "mouthPucker":         ("pucker",),
    "mouthFunnel":         ("funneler",),
    "mouthShrugUpper":     ("chinRaiser",),
    "mouthPressLeft":      ("lipPressor",),
    "mouthPressRight":     ("lipPressor",),
    "mouthLeft":           ("mouthSlideLeft",),
    "mouthRight":          ("mouthSlideRight",),
    "jawLeft":             ("jawSlideLeft",),
    "jawRight":            ("jawSlideRight",),
    "jawForward":          ("jawThrust",),
}


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    a = args()
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def deltas(key, basis) -> list[float]:
    """Per-coordinate offset of a shape key from the basis."""
    n = len(basis.data) * 3
    a, b = [0.0] * n, [0.0] * n
    key.data.foreach_get("co", a)
    basis.data.foreach_get("co", b)
    return [x - y for x, y in zip(a, b)]


def magnitude(d: list[float]) -> float:
    return max((abs(v) for v in d), default=0.0)


def main() -> int:
    apply = "--apply" in args()
    save_as = opt("--save-as")

    ob = bpy.data.objects.get(MESH)
    if not ob or not ob.data.shape_keys:
        print(f"ABORT: '{MESH}' missing or has no shape keys")
        return 2

    blocks = ob.data.shape_keys.key_blocks
    basis = blocks[0]
    have = {k.name for k in blocks}

    plan, already, no_source, missing_target = [], [], [], []
    for target, sources in MAPPING.items():
        if target not in have:
            missing_target.append(target)
            continue
        if magnitude(deltas(blocks[target], basis)) > EPS:
            already.append(target)
            continue
        live = [s for s in sources if s in have and magnitude(deltas(blocks[s], basis)) > EPS]
        if not live:
            no_source.append(target)
            continue
        plan.append((target, live))

    print(f"mesh            : {MESH} ({len(blocks)} key blocks)")
    print(f"would populate  : {len(plan)}")
    print(f"already authored: {len(already)}")
    print(f"no FACS source  : {len(no_source)}  {sorted(no_source)}")
    if missing_target:
        print(f"target absent   : {sorted(missing_target)}")

    unmapped = sorted(n for n in have
                      if n not in MAPPING and n not in {basis.name}
                      and magnitude(deltas(blocks[n], basis)) <= EPS)
    print(f"\nstill empty after this pass ({len(unmapped)}):")
    for n in unmapped:
        print(f"    {n}")

    if not apply:
        print("\nDRY RUN. Nothing written. Re-run with '-- --apply'.")
        return 0

    for target, sources in plan:
        acc = [0.0] * (len(basis.data) * 3)
        for s in sources:
            for i, v in enumerate(deltas(blocks[s], basis)):
                acc[i] += v
        base = [0.0] * len(acc)
        basis.data.foreach_get("co", base)
        blocks[target].data.foreach_set("co", [b + d for b, d in zip(base, acc)])
        print(f"  {target} <- {'+'.join(sources)}")

    ob.data.update()
    print(f"\npopulated {len(plan)} ARKit shape keys")

    if save_as:
        bpy.ops.wm.save_as_mainfile(filepath=save_as, copy=True, compress=False)
        print(f"saved: {save_as}")
    else:
        print("NOT saved. Pass '--save-as <path>'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
