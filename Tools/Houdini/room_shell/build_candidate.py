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


def build_glass_candidate(source_hda, destination):
    """Clone the installed window and add explicit, overrideable UE bindings."""
    source_hda, destination = Path(source_hda), Path(destination)
    if destination.exists():
        raise FileExistsError(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(source_hda.read_bytes()).hexdigest()
    definition = hou.hda.definitionsInFile(str(source_hda))[0]
    definition.copyToHDAFile(str(destination), 'melodia::stained_glass_bound::0.1', 'Stained Glass Material Candidate')
    hou.hda.installFile(str(destination))
    candidate = hou.hda.definitionsInFile(str(destination))[0]
    module = candidate.sections()['PythonModule'].contents()
    old_pane = 'box(cx, cy, cz, w-inset*2, ht-inset*2, thick, "glass_pane")'
    assert old_pane in module
    module = module.replace(old_pane, 'box(cx, cy, cz, w-inset*2, thick, ht-inset*2, "glass_pane")', 1)
    module = module.replace('M.P[i][1]/ht + 0.5 if ht else 0.5', 'M.P[i][2]/ht + 0.5 if ht else 0.5')
    marker = '    g.addAttrib(hou.attribType.Prim, "material_role", "")'
    assert marker in module
    module = module.replace(marker, marker + '\n    g.addAttrib(hou.attribType.Prim, "unreal_material", "")', 1)
    marker = '        poly.setAttribValue("material_role", role)'
    assert marker in module
    mapping = {"glass_pane": "/Game/_PROJECT/04_Materials/Cathedral/MI_LF_StainedGlass",
               "lead_came": "/Game/Melodia/HoudiniFoundry/RoomShell/MI_RoomShell_trim_gold"}
    injection = "\n        mapping = %r\n        mapping.update(json.loads(h.evalParm('material_map_json') or '{}'))\n        poly.setAttribValue('unreal_material', mapping.get(role, '/Game/Melodia/HoudiniFoundry/RoomShell/MI_RoomShell_trim_gold'))" % mapping
    module = module.replace(marker, marker + injection, 1)
    candidate.addSection('PythonModule', module)
    group = candidate.parmTemplateGroup()
    group.append(hou.StringParmTemplate('material_map_json', 'Material Overrides (JSON)', 1, default_value=('{}',)))
    candidate.setParmTemplateGroup(group)
    assert source_hash == hashlib.sha256(source_hda.read_bytes()).hexdigest()
    return str(destination)


def build_ultimate(destination):
    """Build an isolated house assembly candidate from the existing room cores."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(str(destination))
    root = Path(__file__).parent
    obj = hou.node('/obj').createNode('geo', 'housing_ultimate_candidate')
    for child in obj.children():
        child.destroy()
    sop = obj.createNode('python', 'assemble_house')
    sop.parm('python').set("hou.pwd().parent().hdaModule().cook(hou.pwd())")
    sop.setDisplayFlag(True)
    sop.setRenderFlag(True)
    group = obj.parmTemplateGroup()
    group.append(hou.StringParmTemplate('house_plan_json', 'House Plan (JSON)', 1, default_value=('',)))
    group.append(hou.StringParmTemplate('material_map_json', 'Material Overrides (JSON)', 1, default_value=('{}',)))
    group.append(hou.ToggleParmTemplate('engine_y_up', 'Engine Y Up', default_value=True))
    group.append(hou.ToggleParmTemplate('engine_flip', 'Flip Winding', default_value=True))
    for name, label, value in [
        ('salon_w','Salon Width',16.8), ('salon_d','Salon Depth',12.0), ('salon_h','Salon Height',7.2),
        ('salon_exponent','Salon Curve Exponent',2.6), ('tier_0','Tier 1',1.0), ('tier_1','Tier 2',0.92), ('tier_2','Tier 3',0.84),
        ('portal_w','Portal Width',2.4), ('portal_h','Portal Height',3.2), ('salon_roof_rise','Salon Roof Rise',1.6),
        ('landing_w','Landing Width',9.6), ('landing_d','Landing Depth',4.8), ('landing_h','Landing Height',4.2),
        ('landing_roof_rise','Landing Roof Rise',1.8), ('stair_drop','Stair Drop',1.5), ('stair_w','Stair Width',2.4), ('pad_margin','Foundation Margin',1.2)]:
        group.append(hou.FloatParmTemplate(name,label,1,default_value=(value,)))
    for name,label,value in [('salon_shape','Salon Shape',0),('salon_sides','Salon Sides',16),('plan_segments','Curve Segments',96),('landing_windows','Landing Windows',1)]:
        group.append(hou.IntParmTemplate(name,label,1,default_value=(value,)))
    for name,label in [('dressing_medallion','Floor Medallion'),('dressing_skirting','Skirting'),('dressing_rail','Chair Rail')]:
        group.append(hou.ToggleParmTemplate(name,label,default_value=True))
    group.append(hou.ToggleParmTemplate('walk_collision', 'Experimental Walk Collision', default_value=False))
    group.append(hou.ToggleParmTemplate('portal_frill', 'Portal Frill', default_value=False))
    group.append(hou.IntParmTemplate('frill_layers', 'Frill Layers', 1, default_value=(3,), min=1, max=8, min_is_strict=True, max_is_strict=True))
    obj.setParmTemplateGroup(group)
    asset = obj.createDigitalAsset(name='melodia::housing_ultimate::0.1', hda_file_name=str(destination), description='Melodia Housing Ultimate Candidate', min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    definition.setParmTemplateGroup(group)
    rect = (root / 'room_shell.py').read_text(encoding='utf-8')
    rounded = (root / 'room_shell_rounded.py').read_text(encoding='utf-8')
    house = (root / 'house.py').read_text(encoding='utf-8')
    module = "_RectNS = {}\nexec(%r, _RectNS)\n_RoundedNS = {}\nexec(%r, _RoundedNS)\n" % (rect, rounded) + house
    faraway = root.parent / 'faraway'
    heart = (faraway / 'heart_gate_geometry.py').read_text(encoding='utf-8')
    frill = (faraway / 'frill_arch_geometry.py').read_text(encoding='utf-8')
    module += '\n_FrillNS = {}\nexec(%r, _FrillNS)\nexec(%r, _FrillNS)\n' % (heart, frill)
    definition.addSection('PythonModule', module)
    return str(destination)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-hda")
    ap.add_argument("--ultimate", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--floor-collision", action="store_true")
    args = ap.parse_args()
    if args.ultimate:
        print(json.dumps({"candidate_hda": build_ultimate(args.out)}, indent=2))
    else:
        if not args.source_hda:
            ap.error("--source-hda is required unless --ultimate is used")
        print(json.dumps(build(args.source_hda, args.out, args.floor_collision), indent=2))
