"""Assemble the rounded-plan salon shell HDA from a RoomShell definition.

Copies the source definition into a NEW type (melodia::room_shell_rounded::1.0)
and swaps its PythonModule for room_shell_rounded.py. The source HDA is
read-only here; its sha256 is asserted unchanged so the rectangular shell cannot
drift.

Two source shapes are supported:
  * the canonical Content/HDA/MelodiaRoomShell_1.0.hda (33 parms, no explicit
    openings) - the rounded plan parms are appended;
  * the converged contact-floor definition (openings_json + simple_floor_collision
    already present) - openings_json is reused instead of duplicated.

Type defaults are written with clone()+replace(); mutating the template returned
by ParmTemplateGroup.find() does NOT persist, which silently drops drop-in
defaults.

Run with hython; no Content/ asset is overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json

import hou

CANDIDATE_TYPE = "melodia::room_shell_rounded::1.0"
CANDIDATE_LABEL = "Melodia Round Salon Shell - Curved Plan"


def set_defaults(definition, values):
    """Set TYPE default values. Returns the names that actually landed."""
    group = definition.parmTemplateGroup()
    applied = {}
    missing = []
    for name, value in values.items():
        template = group.find(name)
        if template is None:
            missing.append(name)
            continue
        template = template.clone()
        if isinstance(template, hou.MenuParmTemplate):
            template.setDefaultValue(int(value))
        elif isinstance(template, hou.ToggleParmTemplate):
            template.setDefaultValue(bool(value))
        elif isinstance(template, hou.StringParmTemplate):
            template.setDefaultValue(tuple(value) if isinstance(value, (tuple, list)) else (str(value),))
        else:
            template.setDefaultValue(tuple(value) if isinstance(value, (tuple, list)) else (value,))
        group.replace(name, template)
        applied[name] = value
    definition.setParmTemplateGroup(group)
    return applied, missing


def read_defaults(definition, names):
    group = definition.parmTemplateGroup()
    out = {}
    for name in names:
        template = group.find(name)
        if template is None:
            continue
        value = template.defaultValue()
        out[name] = list(value) if isinstance(value, (tuple, list)) else [value]
    return out


def build(source_hda, destination, salon_defaults=True, tiers=(1.0, 0.92, 0.84)):
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
    appended = []
    if templates.find("openings_json") is None:
        default_openings = "[]"
        if salon_defaults:
            default_openings = json.dumps(
                [
                    {"id": "salon_entry", "theta": 0.25, "width": 2.4, "height": 3.2},
                    {"id": "salon_front", "theta": 0.75, "width": 2.4, "height": 3.2},
                ],
                separators=(",", ":"),
            )
        openings = hou.StringParmTemplate("openings_json", "Explicit Door Openings (JSON)", 1,
                                          default_value=(default_openings,))
        openings.setHelp(
            'Array of named floor-level portals: [{"id":"salon_entry","theta":0.25,"width":2.4,"height":3.2}]. '
            "theta is the perimeter fraction (0..1, counter-clockwise from +X through the room centre); "
            "width is metres of true arc length. Every portal edge becomes a plan vertex, so jambs are exact cuts."
        )
        templates.append(openings)
        appended.append("openings_json")

    for template, name in (
        (hou.MenuParmTemplate("plan_shape", "Plan Shape",
                              ("Ellipse", "Superellipse", "Polygon"),
                              menu_labels=("Ellipse", "Superellipse (rounded rect)", "Polygon"),
                              default_value=0), "plan_shape"),
        (hou.IntParmTemplate("plan_sides", "Plan Sides (polygon)", 1, default_value=(16,)), "plan_sides"),
        (hou.FloatParmTemplate("plan_exponent", "Superellipse Exponent", 1, default_value=(2.6,)), "plan_exponent"),
        (hou.IntParmTemplate("plan_segments", "Plan Tessellation", 1, default_value=(96,)), "plan_segments"),
        (hou.StringParmTemplate("tiers_json", "Tier Setbacks (JSON)", 1,
                                default_value=(json.dumps([float(t) for t in tiers], separators=(",", ":")),)), "tiers_json"),
        (hou.StringParmTemplate("material_map_json", "Material Map Override (JSON)", 1,
                                default_value=("{}",)), "material_map_json"),
    ):
        if templates.find(name) is not None:
            continue
        if name == "plan_sides":
            template.setHelp("Corner count for the Polygon plan. Ignored by Ellipse and Superellipse.")
        elif name == "plan_exponent":
            template.setHelp("2.0 = true ellipse; higher = squarer (a superellipse). Ignored by Ellipse and Polygon.")
        elif name == "plan_segments":
            template.setHelp("Wall segments around the perimeter. Portal edges are inserted exactly, "
                             "so a low value still cuts clean jambs.")
        elif name == "tiers_json":
            template.setHelp('Array of setback ratios per tier, e.g. [1.0, 0.85, 0.70]. 1.0 = full radius (base), '
                             'lower = stepped setback (ziggurat massing). Empty array [] = single volume (no tiers). '
                             'Controls the exterior silhouette from distance. tiers[0] must stay 1.0 so the base '
                             'footprint and the floor slab keep matching the interior.')
        elif name == "material_map_json":
            template.setHelp('Optional JSON object overriding material_role -> UE material path. Every role the '
                             'mesh emits must resolve to an existing /Game/ asset: the cook raises rather than '
                             'cooking an unmapped role. Unlisted roles keep the module default.')
        templates.append(template)
        appended.append(name)
    candidate.setParmTemplateGroup(templates)

    defaults = {
        "plan_shape": 0,
        "plan_sides": 16,
        "plan_exponent": 2.6,
        "plan_segments": 96,
        "tiers_json": json.dumps([float(t) for t in tiers], separators=(",", ":")),
    }
    if salon_defaults:
        # Land at the measured artist salon footprint (L_MelusinaHouse_P0 HDA_House_Salon).
        defaults.update(room_w=15.84, room_d=12.06, room_h=7.6)
        defaults["openings_json"] = json.dumps(
            [
                {"id": "salon_entry", "theta": 0.25, "width": 2.4, "height": 3.2},
                {"id": "salon_front", "theta": 0.75, "width": 2.4, "height": 3.2},
            ],
            separators=(",", ":"),
        )
    applied, missing = set_defaults(candidate, defaults)
    landed = read_defaults(candidate, list(defaults))

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
        "parms_appended": appended,
        "defaults_requested": applied,
        "defaults_missing": missing,
        "defaults_actual": landed,
        "salon_defaults": salon_defaults,
        "tiers": [float(t) for t in tiers],
        "source_unchanged": before == after,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-hda", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-salon-defaults", action="store_true")
    ap.add_argument("--tiers", default="1.0,0.92,0.84",
                    help="Comma separated tier setbacks; tiers[0] must be 1.0")
    args = ap.parse_args()
    tiers = tuple(float(v) for v in args.tiers.split(","))
    print(json.dumps(build(args.source_hda, args.out, salon_defaults=not args.no_salon_defaults,
                          tiers=tiers), indent=2))
