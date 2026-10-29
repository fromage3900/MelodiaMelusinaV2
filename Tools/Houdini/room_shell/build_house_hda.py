"""Pack melodia::house::1.0: subnet HDA with arch output, PCG scatter branch,
and the artist parm surface (2.0-lane vocabulary: folders, labeled menus,
help text, ranges, dual profile/artist authoring where it matters).

Run with hython. No Content/ asset is overwritten. Verify cooks the HDA
twice (arch + scatter) and fails closed on every gate.
"""
import argparse
import hashlib
import json
from pathlib import Path

import hou

TYPE = "melodia::house"
LABEL = "Melodia House - Salon First"
HERE = Path(__file__).resolve().parent


def _folder(name, label, templates, kind=hou.folderType.Collapsible):
    f = hou.FolderParmTemplate(name, label, folder_type=kind)
    f.setParmTemplates(templates)
    f.setDefaultValue(1)
    return f


def _float(name, label, default, help_text, low=None, high=None):
    p = hou.FloatParmTemplate(name, label, 1, default_value=(float(default),))
    if low is not None:
        p.setMinValue(float(low))
    if high is not None:
        p.setMaxValue(float(high))
    p.setHelp(help_text)
    return p


def _int(name, label, default, help_text, low=None, high=None):
    p = hou.IntParmTemplate(name, label, 1, default_value=(int(default),))
    if low is not None:
        p.setMinValue(int(low))
    if high is not None:
        p.setMaxValue(int(high))
    p.setHelp(help_text)
    return p


def _menu(name, label, items, labels, default, help_text):
    p = hou.MenuParmTemplate(name, label, tuple(items), menu_labels=tuple(labels),
                             default_value=int(default))
    p.setHelp(help_text)
    return p


def _toggle(name, label, default, help_text):
    p = hou.ToggleParmTemplate(name, label, default_value=bool(default))
    p.setHelp(help_text)
    return p


def artist_parameter_group():
    g = hou.ParmTemplateGroup()
    g.append(_folder("salon", "Salon Footprint", [
        _float("salon_w", "Interior Width (m)", 16.8,
               "Measured salon width. The rounded plan is inscribed inside this footprint.", 1.0, 100.0),
        _float("salon_d", "Interior Depth (m)", 12.0,
               "Measured salon depth in metres.", 1.0, 100.0),
        _float("salon_h", "Clear Wall Height (m)", 7.2,
               "Clear interior height from floor datum to ceiling plane.", 1.0, 40.0),
        _float("salon_roof_rise", "Roof Rise (m)", 1.6,
               "Conical cap rise above the wall head. Pitch is gated 15 to 60 degrees.", 0.2, 12.0),
    ]))
    g.append(_folder("landing", "Landing Wing", [
        _float("landing_w", "Interior Width (m)", 9.6,
               "Landing wing width in metres.", 1.0, 100.0),
        _float("landing_d", "Interior Depth (m)", 4.8,
               "Landing wing depth in metres.", 1.0, 100.0),
        _float("landing_h", "Clear Wall Height (m)", 4.2,
               "Landing clear height. Must clear the 3.2 m portal plus 0.6 m head.", 3.8, 40.0),
        _int("landing_windows", "Long-Wall Windows", 1,
             "Window count on the landing long wall.", 0, 8),
        _float("landing_roof_rise", "Roof Rise (m)", 1.8,
               "Mansard rise above the landing wall head.", 0.2, 12.0),
    ]))
    g.append(_folder("plan_shape", "Salon Plan Shape", [
        _menu("salon_shape", "Footprint Shape", ("ellipse", "superellipse", "polygon"),
              ("Ellipse", "Soft Rounded Rectangle", "Polygon"), 0,
              "Ellipse keeps the measured House footprint. Rounded Rectangle uses Corner Squareness. Polygon uses Side Count."),
        _int("salon_sides", "Polygon Sides", 16,
             "Used only by Polygon. Kept inside the validated rounded-shell limits.", 5, 64),
        _float("salon_exponent", "Corner Squareness", 2.6,
               "Used only by Soft Rounded Rectangle. 2.0 is an ellipse; higher values square the corners.", 2.0, 8.0),
        _int("plan_segments", "Plan Tessellation", 96,
             "Curve segments around the plan. Portal edges stay exact.", 16, 512),
    ]))
    g.append(_folder("portals", "Doors and Portals", [
        _float("portal_w", "Clear Width (m)", 2.4,
               "Standard portal: one 2.4 m bay. The joint validates it.", 1.2, 4.8),
        _float("portal_h", "Clear Height (m)", 3.2,
               "Standard portal height at floor level.", 2.0, 6.0),
    ]))
    g.append(_folder("massing", "Stepped Wall Massing", [
        _float("tier_0", "Ground Tier Scale (locked)", 1.0,
               "Base tier is always 1.0: tiers step the wall band, never the interior volume."),
        _float("tier_1", "Middle Tier Scale", 0.92,
               "Upper wall footprint as a fraction of the tier below.", 0.05, 1.0),
        _float("tier_2", "Crown Tier Scale", 0.84,
               "Top wall footprint as a fraction of the tier below.", 0.05, 1.0),
    ]))
    g.append(_folder("roof", "Roof Dressing", [
        _float("roof_overhang", "Eave Overhang (m)", 0.6,
               "Reserved for the eave pass. Live mansard uses its validated default today.", 0.0, 2.0),
    ]))
    g.append(_folder("stairs", "Porch Stairs", [
        _float("stair_drop", "Drop to Grade (m)", 1.5,
               "Total descent from the landing portal to grade. Risers follow the 0.17 m walkability law.", 0.2, 6.0),
        _float("stair_w", "Stair Width (m)", 2.4,
               "Clear stair width, aligned with the portal.", 0.9, 4.8),
    ]))
    g.append(_folder("pad", "Foundation Pad", [
        _float("pad_margin", "Pad Margin (m)", 1.2,
               "Skirt beyond the union footprint. The pad top ring reads as a terrace.", 0.0, 5.0),
    ]))
    g.append(_folder("finish", "Surface Dressing", [
        _toggle("dressing_medallion", "Chladni Floor Medallion", True,
                "Floor medallion in both rooms."),
        _toggle("dressing_skirting", "Skirting", True,
                "Skirting boards in both rooms."),
        _toggle("dressing_rail", "Chair Rail", True,
                "Chair rail in both rooms."),
    ]))
    g.append(_folder("dress", "PCG Dressing Density", [
        _int("scatter_floor", "Floor Instances", 400,
             "Scatter count on dressable floor.", 0, 20000),
        _int("scatter_wall", "Wall Instances", 600,
             "Scatter count on dressable walls.", 0, 20000),
        _int("scatter_ceiling", "Ceiling Instances", 150,
             "Scatter count on the ceiling (hanging dressing).", 0, 20000),
        _int("scatter_ledge", "Ledge Instances", 120,
             "Scatter count on ledges and trims.", 0, 20000),
        _int("scatter_sill", "Sill Instances", 40,
             "Scatter count on sills.", 0, 20000),
    ]))
    g.append(_folder("engine", "Engine Output", [
        _toggle("engine_y_up", "Y-up Houdini Engine Output", True,
                "Emit in the Engine frame. Off cooks native Z-up metres for review."),
        _toggle("engine_flip", "Flip Winding for Engine", True,
                "Match the Engine Y/Z swap so UE front faces stay outward."),
        hou.StringParmTemplate("material_map_json", "Material Role Overrides (JSON)", 1,
                               default_value=("{}",)),
    ]))
    g.append(_folder("advanced", "Advanced / Pipeline Data", [
        hou.StringParmTemplate("house_plan_json", "Full Plan Override (JSON)", 1,
                               default_value=("",)),
    ]))
    for t in ("material_map_json", "house_plan_json"):
        g.find(t).setHelp("Pipeline authoring. The folders above drive the Salon run; "
                          "JSON overrides full plans or single material roles per actor.")
    return g


def _section_source():
    import base64
    rect_src = (HERE / "room_shell.py").read_text(encoding="utf-8")
    round_src = (HERE / "room_shell_rounded.py").read_text(encoding="utf-8")
    house_src = (HERE / "house.py").read_text(encoding="utf-8")
    # base64 blobs: the HDA round-trip escapes raw quotes, which breaks %r
    # literals. Base64 has no quotes or backslashes, so it survives intact.
    header = ("import base64\n_RectNS = {}\n_RoundedNS = {}\n"
              "_RECT_SRC = base64.b64decode('%s').decode('utf-8')\n"
              "_ROUND_SRC = base64.b64decode('%s').decode('utf-8')\n"
              "exec(compile(_RECT_SRC, 'room_shell', 'exec'), _RectNS)\n"
              "exec(compile(_ROUND_SRC, 'room_shell_rounded', 'exec'), _RoundedNS)\n"
              % (base64.b64encode(rect_src.encode('utf-8')).decode('ascii'),
                 base64.b64encode(round_src.encode('utf-8')).decode('ascii')))
    return header + house_src


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    hda_path = out_dir / "MelodiaHouse_1.0.hda"
    if hda_path.exists():
        hda_path.unlink()

    holder = hou.node("/obj").createNode("geo", "melodia_house_pack")
    holder.deleteItems(holder.children())
    sub = holder.createNode("subnet", "house")
    arch = sub.createNode("python", "arch")
    arch.parm("python").set(_section_source() + "\ncook(hou.pwd())\n")

    groupby = sub.createNode("attribwrangle", "by_surface")
    groupby.setInput(0, arch)
    groupby.parm("class").set(1)
    groupby.parm("snippet").set(
        "string sunames[] = {'surface_floor', 'surface_wall', "
        "'surface_ceiling', 'surface_ledge', 'surface_sill', 'structure'};\n"
        "setprimgroup(0, sunames[i@surf_id], @primnum, 1);")
    promote = sub.createNode("attribpromote", "surf_room_up")
    promote.setInput(0, groupby)
    promote.parm("inclass").set(1)
    promote.parm("outclass").set(2)
    promote.parm("method").set(8)
    promote.parm("inname").set("surface room")

    surfaces = ["surface_floor", "surface_wall", "surface_ceiling",
                "surface_ledge", "surface_sill"]
    scatters = []
    for s in surfaces:
        blast = sub.createNode("blast", "keep_" + s)
        blast.setInput(0, promote)
        blast.parm("group").set(s)
        blast.parm("negate").set(1)
        sc = sub.createNode("scatter", s + "_scatter")
        sc.setInput(0, blast)
        short = s.replace("surface_", "")
        sc.parm("npts").setExpression('ch("../scatter_%s")' % short,
                                      hou.exprLanguage.Hscript)
        scatters.append(sc)
    pcg_merge = sub.createNode("merge", "pcg_merge")
    for i, sc in enumerate(scatters):
        pcg_merge.setInput(i, sc)

    out_arch = sub.createNode("output", "OUT_arch")
    out_arch.setInput(0, arch)
    out_pcg = sub.createNode("output", "OUT_pcg")
    out_pcg.setInput(0, pcg_merge)
    out_arch.parm("outputidx").set(0)
    out_pcg.parm("outputidx").set(1)
    sub.layoutChildren()

    asset = sub.createDigitalAsset(name="melodia::house",
                                   hda_file_name=str(hda_path),
                                   description=LABEL,
                                   min_num_inputs=0, max_num_inputs=0,
                                   version="1.0")
    hou.hda.installFile(str(hda_path))
    definition = next(d for d in hou.hda.definitionsInFile(str(hda_path))
                      if d.nodeTypeName() == TYPE)
    definition.setParmTemplateGroup(artist_parameter_group())
    return dict(hda=str(hda_path),
                sha256=hashlib.sha256(hda_path.read_bytes()).hexdigest(),
                bytes=hda_path.stat().st_size)


def verify(hda_path, out_dir):
    hou.hda.installFile(str(hda_path))
    parent = hou.node("/obj").createNode("geo", "melodia_house_verify")
    parent.deleteItems(parent.children())
    node = parent.createNode(TYPE, "house_SALON_FIRST")
    node.cook(force=True)
    if node.errors():
        raise RuntimeError("arch cook errors: %s" % list(node.errors()))
    inner = node.path() + "/arch"
    arch_geo = hou.node(inner).geometry()
    assert arch_geo is not None
    merge = hou.node(node.path() + "/pcg_merge")
    merge.cook(force=True)
    pcg_geo = merge.geometry()
    roles = {}
    for prim in arch_geo.prims():
        if not prim.attribValue("material_role"):
            continue
        roles[prim.attribValue("material_role")] = \
            roles.get(prim.attribValue("material_role"), 0) + 1
    cgrp = arch_geo.findPrimGroup("collision_geo_house")
    collision_prims = len(cgrp.prims()) if cgrp is not None else 0
    surfaces = {}
    for prim in arch_geo.prims():
        if not prim.attribValue("surface"):
            continue
        s = prim.attribValue("surface")
        surfaces[s] = surfaces.get(s, 0) + 1
    rooms = set()
    for prim in arch_geo.prims():
        if prim.attribValue("room"):
            rooms.add(prim.attribValue("room"))
    report = dict(points=len(arch_geo.points()), prims=len(arch_geo.prims()),
                  roles=roles, surface_prims=surfaces, rooms=sorted(rooms),
                  collision_prims=collision_prims,
                  pcg_points=len(pcg_geo.points()) if pcg_geo else 0,
                  pcg_per_surface={},
                  errors=[str(e) for e in node.errors()],
                  warnings=[str(w) for w in node.warnings()])
    for s in ["surface_floor", "surface_wall", "surface_ceiling",
              "surface_ledge", "surface_sill"]:
        sc = hou.node(node.path() + "/" + s + "_scatter")
        sc.cook(force=True)
        report["pcg_per_surface"][s] = len(sc.geometry().points())
    out = Path(out_dir) / "house_verify.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert report["errors"] == [], report["errors"]
    assert report["pcg_points"] > 0, "PCG branch emitted nothing"
    assert all(v > 0 for v in report["pcg_per_surface"].values()), \
        "empty PCG surface: %s" % report["pcg_per_surface"]
    assert report["collision_prims"] > 0, "collision_geo_house is empty"
    return report


def main(out_dir):
    info = build(out_dir)
    print(json.dumps(info, indent=2))
    verify(info["hda"], out_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
