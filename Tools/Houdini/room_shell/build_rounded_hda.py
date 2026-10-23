"""Assemble the rounded-plan salon shell HDA from the canonical RoomShell definition.

Copies the current MelodiaRoomShell definition into a NEW type
(melodia::room_shell_rounded::1.0) and swaps its PythonModule for
room_shell_rounded.py. The canonical HDA is read-only here; its sha256 is
asserted unchanged so the rectangular shell cannot drift.

Run with hython; no Content/ asset is overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json

import hou

CANDIDATE_TYPE = "melodia::room_shell_rounded::1.0"
CANDIDATE_LABEL = "Melodia Round Salon Shell - Curved Plan"


def build(source_hda, destination, salon_defaults=True):
    source_hda, destination = Path(source_hda), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    module = Path(__file__).with_name("room_shell_rounded.py")
    before = hashlib.sha256(source_hda.read_bytes()).hexdigest()

    definition = hou.hda.definitionsInFile(str(source_hda))[0]
    definition.copyToHDAFile(str(destination), CANDIDATE_TYPE, CANDIDATE_LABEL)
    hou.hda.installFile(str(destination))
    candidate = next(d for d in hou.hda.definitionsInFile(str(destination))
                     if d.nodeTypeName() == CANDIDATE_TYPE)

    candidate.addSection("PythonModule", module.read_text(encoding="utf-8"))

    templates = candidate.parmTemplateGroup()
    templates.append(
        hou.MenuParmTemplate(
            "plan_shape", "Plan Shape",
            ("Ellipse", "Superellipse", "Polygon"),
            menu_labels=("Ellipse", "Superellipse (rounded rect)", "Polygon"),
            default_value=0,
        )
    )
    sides = hou.IntParmTemplate("plan_sides", "Plan Sides (polygon)", 1, default_value=(16,))
    sides.setHelp("Corner count for the Polygon plan. Ignored by Ellipse and Superellipse.")
    templates.append(sides)
    expo = hou.FloatParmTemplate("plan_exponent", "Superellipse Exponent", 1, default_value=(2.6,))
    expo.setHelp("2.0 = true ellipse; higher = squarer (a superellipse). Ignored by Ellipse and Polygon.")
    templates.append(expo)
    segs = hou.IntParmTemplate("plan_segments", "Plan Tessellation", 1, default_value=(96,))
    segs.setHelp("Wall segments around the perimeter. Portal edges are inserted exactly, so a low value still cuts clean jambs.")
    templates.append(segs)
    default_openings = "[]"
    if salon_defaults:
        default_openings = json.dumps(
            [
                {"id": "salon_entry", "theta": 0.25, "width": 1.8, "height": 3.2},
                {"id": "salon_front", "theta": 0.75, "width": 2.4, "height": 3.2},
            ],
            separators=(",", ":"),
        )
    openings = hou.StringParmTemplate("openings_json", "Explicit Door Openings (JSON)", 1,
                                      default_value=(default_openings,))
    openings.setHelp(
        'Array of named floor-level portals: [{"id":"salon_entry","theta":0.25,"width":1.8,"height":3.2}]. '
        "theta is the perimeter fraction (0..1, counter-clockwise from +X through the room centre); "
        "width is metres of true arc length. Every portal edge becomes a plan vertex, so jambs are exact cuts."
    )
    templates.append(openings)
    tiers = hou.StringParmTemplate("tiers_json", "Tier Setbacks (JSON)", 1,
                                  default_value=("[1.0, 0.85, 0.70]",))
    tiers.setHelp(
        'Array of setback ratios per tier, e.g. [1.0, 0.85, 0.70]. '
        '1.0 = full radius (base), lower = stepped setback (ziggurat massing). '
        'Empty array [] = single volume (no tiers). Controls the exterior silhouette from distance.'
    )
    templates.append(tiers)
    candidate.setParmTemplateGroup(templates)

    if salon_defaults:
        # Land at the measured artist salon footprint (L_MelusinaHouse_P0 HDA_House_Salon).
        params = candidate.parmTemplateGroup()
        for name, value in (("room_w", 15.84), ("room_d", 12.06), ("room_h", 7.6)):
            parm = params.find(name)
            if parm is not None:
                parm.setDefaultValue((value,))
        candidate.setParmTemplateGroup(params)

    after = hashlib.sha256(source_hda.read_bytes()).hexdigest()
    assert before == after, "Source HDA changed during build - aborting"

    return {
        "source_hda": str(source_hda),
        "source_sha256": before,
        "candidate_hda": str(destination),
        "candidate_type": CANDIDATE_TYPE,
        "candidate_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "module": str(module),
        "module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "salon_defaults": salon_defaults,
        "source_unchanged": before == after,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-hda", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-salon-defaults", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build(args.source_hda, args.out, salon_defaults=not args.no_salon_defaults), indent=2))
