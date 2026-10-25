"""Recover the current RoomShell definition into an additive explicit-door candidate.

Run with hython; no canonical Content or source definition is overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import hou


def build(source_hda, destination, floor_collision=False):
    source_hda, destination = Path(source_hda), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name("room_shell.py")
    before = hashlib.sha256(source_hda.read_bytes()).hexdigest()
    definition = hou.hda.definitionsInFile(str(source_hda))[0]
    candidate_type = "melodia::room_shell_contact::1.0" if floor_collision else "melodia::room_shell_explicit::1.0"
    definition.copyToHDAFile(str(destination), candidate_type, "Melodia Room Shell - Explicit Doors")
    hou.hda.installFile(str(destination))
    candidate = next(d for d in hou.hda.definitionsInFile(str(destination)) if d.nodeTypeName() == candidate_type)
    candidate.addSection("PythonModule", source.read_text(encoding="utf-8"))
    templates = candidate.parmTemplateGroup()
    parameter = hou.StringParmTemplate("openings_json", "Explicit Door Openings (JSON)", 1, default_value=("[]",))
    parameter.setHelp('Optional array: [{"id":"salon_entry","wall":"W","s":5.76,"width":1.8,"height":3.2}]. Metres in the native room frame. Empty retains legacy random door selection. Explicit records replace it and cut real floor-level portals.')
    templates.append(parameter)
    collision = hou.ToggleParmTemplate("simple_floor_collision", "Simple Floor Collision", default_value=floor_collision)
    collision.setHelp("Emit an invisible collision_geo_simple_box_main_geo matching only the floor slab, paired with rendered_main_geo. Walls and door apertures are not included in this convex box. Validate the cooked Unreal BodySetup before promotion.")
    templates.append(collision)
    materials = hou.StringParmTemplate("material_map_json", "Material Map Override (JSON)", 1, default_value=("{}",))
    materials.setHelp('Optional JSON object overriding material_role -> UE material path, e.g. {"pearl_shell":"/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_Nikki_Show_PearlSheen"}. Every role the mesh emits must resolve to an existing /Game/ asset: the cook raises rather than cooking an unmapped role. Unlisted roles keep the module default.')
    templates.append(materials)
    candidate.setParmTemplateGroup(templates)
    assert before == hashlib.sha256(source_hda.read_bytes()).hexdigest(), "Source HDA changed"
    return {"source_hda": str(source_hda), "source_sha256": before, "candidate_hda": str(destination), "candidate_type": candidate_type, "candidate_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "module_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-hda", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--floor-collision", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build(args.source_hda, args.out, args.floor_collision), indent=2))
