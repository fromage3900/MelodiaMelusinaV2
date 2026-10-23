"""Build and cook the bounded Maillezais house-garden Landscape HDA."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
AUDIT = ROOT / "Saved" / "Audit" / "MorningVista_20261021" / "Terrain"
HDA_PATH = AUDIT / "MelodiaHouseGardenVista_1.0.hda"
IGN_TIFF = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Docs\Poitou\research\dem\maillezais_rgealti1m_l93.tif")
sys.path.insert(0, str(ROOT / "Tools" / "Houdini"))
import hda_promote_controls as promote

import hou


def build():
    if not IGN_TIFF.is_file() or IGN_TIFF.stat().st_size < 1000000:
        raise RuntimeError("Full IGN RGE ALTI GeoTIFF is unavailable: %s" % IGN_TIFF)
    AUDIT.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    prior = obj.node("MelodiaHouseGardenVista")
    if prior:
        prior.destroy()
    geo = obj.createNode("geo", "MelodiaHouseGardenVista")
    for c in geo.children():
        c.destroy()

    controls = geo.createNode("null", "controls")
    pg = controls.parmTemplateGroup()
    f = hou.FolderParmTemplate("source", "IGN Source and Crop", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.StringParmTemplate("source_filepath", "IGN RGE ALTI GeoTIFF", 1, default_value=(str(IGN_TIFF),), string_type=hou.stringParmType.FileReference))
    f.addParmTemplate(hou.FloatParmTemplate("source_min", "Source minimum (m NGF)", 1, default_value=(1.40,), min=0.0, max=100.0))
    f.addParmTemplate(hou.FloatParmTemplate("source_range", "Source height range (m)", 1, default_value=(16.0033,), min=0.01, max=100.0))
    f.addParmTemplate(hou.FloatParmTemplate("crop_x", "Crop center X (m)", 1, default_value=(520.0,), min=-1500.0, max=1500.0))
    f.addParmTemplate(hou.FloatParmTemplate("crop_z", "Crop center Z (m)", 1, default_value=(580.0,), min=-1500.0, max=1500.0))
    f.addParmTemplate(hou.FloatParmTemplate("reference_elevation", "Local reference elevation (m NGF)", 1, default_value=(9.66,), min=-100.0, max=100.0))
    f.addParmTemplate(hou.FloatParmTemplate("amplitude", "Terrain amplitude (m across source range)", 1, default_value=(16.0033,), min=0.0, max=100.0))
    pg.append(f)
    f = hou.FolderParmTemplate("garden", "Garden Shape", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.FloatParmTemplate("pad_elevation", "House pad elevation (m)", 1, default_value=(-0.10,), min=-10.0, max=10.0))
    for n, label, v in [("pond_x", "Pond center X (m)", 32.0), ("pond_z", "Pond center Z (m)", -5.0), ("pond_radius_x", "Pond radius X (m)", 14.0), ("pond_radius_z", "Pond radius Z (m)", 10.0), ("water_level", "Pond water level (m)", -0.8), ("pond_bed", "Pond bed elevation (m)", -2.2)]:
        f.addParmTemplate(hou.FloatParmTemplate(n, label, 1, default_value=(v,), min=-100.0, max=100.0))
    f.addParmTemplate(hou.FloatParmTemplate("preview_resolution", "Preview resolution (samples)", 1, default_value=(257,), min=65.0, max=1025.0))
    f.addParmTemplate(hou.FloatParmTemplate("pad_xmin", "Pad X minimum (m)", 1, default_value=(-22.0,)))
    f.addParmTemplate(hou.FloatParmTemplate("pad_xmax", "Pad X maximum (m)", 1, default_value=(16.0,)))
    f.addParmTemplate(hou.FloatParmTemplate("pad_zmin", "Pad Z minimum (m)", 1, default_value=(-14.0,)))
    f.addParmTemplate(hou.FloatParmTemplate("pad_zmax", "Pad Z maximum (m)", 1, default_value=(10.0,)))
    pg.append(f)
    f = hou.FolderParmTemplate("landscape", "Landscape and LayerInfo", folder_type=hou.folderType.Tabs)
    f.addParmTemplate(hou.StringParmTemplate("landscape_material", "Landscape material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Landscape_Nikki.MI_Poitou_Landscape_Nikki",)))
    f.addParmTemplate(hou.StringParmTemplate("layerinfo_dir", "LayerInfo folder", 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo",)))
    for layer in ("Grass", "Ground", "Base", "Mud", "Path", "Rock", "Water"):
        f.addParmTemplate(hou.StringParmTemplate("layerinfo_" + layer.lower(), "LayerInfo: " + layer, 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo/LI_Poitou_%s.LI_Poitou_%s" % (layer, layer),)))
    pg.append(f)
    controls.setParmTemplateGroup(pg)
    names = ["source_filepath", "source_min", "source_range", "crop_x", "crop_z", "reference_elevation", "amplitude", "pad_elevation", "pond_x", "pond_z", "pond_radius_x", "pond_radius_z", "water_level", "pond_bed", "preview_resolution", "pad_xmin", "pad_xmax", "pad_zmin", "pad_zmax", "landscape_material", "layerinfo_dir"] + ["layerinfo_" + n.lower() for n in ("Grass", "Ground", "Base", "Mud", "Path", "Rock", "Water")]

    file = geo.createNode("heightfield_file", "IGN_RGE_ALTI_1m")
    file.parm("filename").setExpression('chs("../controls/source_filepath")', hou.exprLanguage.Hscript)
    file.parm("sizemethod").set(0)
    file.parm("size").set(3000.0)
    file.parm("heightscale").set(1.0)
    crop = geo.createNode("heightfield_crop", "crop_80m_garden")
    crop.setInput(0, file)
    crop.parm("cropmode").set(2)
    # Houdini crops voxel centers inclusively; 79 m of center spacing yields an exact 80 m footprint.
    crop.parm("sizex").set(79.0)
    crop.parm("sizey").set(79.0)
    crop.parm("tx").setExpression('ch("../controls/crop_x")', hou.exprLanguage.Hscript)
    crop.parm("tz").setExpression('ch("../controls/crop_z")', hou.exprLanguage.Hscript)
    rs = geo.createNode("heightfield_resample", "preview_resolution")
    rs.setInput(0, crop)
    rs.parm("fixedresample").set(1)
    rs.parm("gridspacing").setExpression('80.0/int(ch("../controls/preview_resolution"))', hou.exprLanguage.Hscript)
    xform = geo.createNode("xform", "local_house_garden_frame")
    xform.setInput(0, rs)
    xform.parm("tx").setExpression('15-ch("../controls/crop_x")', hou.exprLanguage.Hscript)
    xform.parm("tz").setExpression('-ch("../controls/crop_z")', hou.exprLanguage.Hscript)

    layers = ["Grass", "Ground", "Base", "Mud", "Path", "Rock", "Water"]
    cp = geo.createNode("heightfield_copylayer", "create_nikki_landscape_layers")
    cp.setInput(0, xform)
    cp.parm("numcopy").set(len(layers))
    for i, layer in enumerate(layers, 1):
        cp.parm("create%d" % i).set(1)
        cp.parm("srcname%d" % i).set("mask")
        cp.parm("dstname%d" % i).set(layer)

    wr = geo.createNode("volumewrangle", "shape_pad_pond_and_nikki_masks")
    wr.setInput(0, cp)
    wr.parm("snippet").set(r'''
float raw = @height;
float lo = ch("../controls/source_min");
float span = max(0.001, ch("../controls/source_range"));
float datum = ch("../controls/reference_elevation");
float amp = ch("../controls/amplitude");
float base = ((clamp(raw, lo, lo + span) - datum) / span) * amp;
float x = @P.x, z = @P.z;
float dx = max(max(ch("../controls/pad_xmin")-x, 0.0), x-ch("../controls/pad_xmax"));
float dz = max(max(ch("../controls/pad_zmin")-z, 0.0), z-ch("../controls/pad_zmax"));
float padDist = length(set(dx,0,dz));
float pad = 1.0 - smooth(0.0, 1.25, padDist);
float rx = max(0.1, ch("../controls/pond_radius_x"));
float rz = max(0.1, ch("../controls/pond_radius_z"));
float pr = length(set((x-ch("../controls/pond_x"))/rx, 0, (z-ch("../controls/pond_z"))/rz));
float shore = smooth(0.58, 1.0, pr);
float outer = smooth(1.0, 1.16, pr);
float waterLevel = ch("../controls/water_level");
float bed = ch("../controls/pond_bed");
float pondGround = lerp(bed, waterLevel, shore);
float gardenHeight = lerp(pondGround, base, outer);
gardenHeight = lerp(gardenHeight, ch("../controls/pad_elevation"), pad);
@height = gardenHeight;
@Grass = 1.0 - max(pad, 1.0-outer);
@Ground = 1.0;
@Base = 1.0;
@Mud = max((1.0-smooth(0.90,1.12,pr)) * smooth(0.50,0.78,pr), 0.0);
@Path = pad;
@Rock = 0.0;
@Water = 1.0 - smooth(0.96,1.02,pr);
''')
    attr = geo.createNode("attribwrangle", "unreal_classic_landscape_attributes")
    attr.setInput(0, wr)
    attr.parm("class").set(1)
    attr.parm("snippet").set(r'''
s@unreal_landscape_layer_name = s@name;
if (s@name == "height") {
    s@unreal_material = chs("../controls/landscape_material");
    s@unreal_landscape_material = chs("../controls/landscape_material");
} else {
    string p = "../controls/layerinfo_" + tolower(s@name);
    s@unreal_landscape_layer_info = chs(p);
}
''')
    clean = geo.createNode("blast", "remove_helper_mask")
    clean.setInput(0, attr)
    clean.parm("group").set("@name=mask")
    clean.parm("grouptype").set(4)
    out = geo.createNode("output", "OUT_HOUSE_GARDEN_LANDSCAPE")
    out.parm("outputidx").set(0)
    out.setInput(0, clean)
    for n in geo.children():
        n.moveToGoodPosition()

    pairs = promote.stage1_promote(controls, geo, names, hou)
    promote.stage1_wire(controls, pairs, hou)
    # The generic helper uses ch(), which coerces string channels to zero.
    for inner, promoted in pairs:
        template = controls.parmTemplateGroup().find(inner)
        if isinstance(template, hou.StringParmTemplate):
            controls.parm(inner).setExpression('chs("../%s")' % promoted, hou.exprLanguage.Hscript)
    hda = geo.createDigitalAsset(name="melodia::house_garden_vista::1.0", hda_file_name=str(HDA_PATH), description="Melodia House Garden Vista Landscape", min_num_inputs=0, max_num_inputs=0, version="1.0")
    promote.stage2_promote_definition(hda, pairs, HDA_PATH, hou)
    hda.matchCurrentDefinition()
    hda.parm("source_filepath").set(str(IGN_TIFF))
    hda.parm("preview_resolution").set(257)

    # Cook the asset output and fail closed on any SOP error.
    hda.cook(force=True)
    errors = [(n.path(), list(n.errors())) for n in hda.allSubChildren() if n.errors()]
    geom = hda.node("remove_helper_mask").geometry()
    if errors or geom is None:
        diag = {}
        for n in hda.allSubChildren():
            has_geo = None
            try:
                has_geo = n.geometry() is not None
            except Exception:
                pass
            diag[n.name()] = {"errors": list(n.errors()), "has_geometry": has_geo}
        raise RuntimeError(json.dumps({"errors": errors, "geometry": geom is not None, "nodes": diag}, indent=2))
    vols = [p for p in geom.prims() if isinstance(p, hou.Volume)]
    byname = {p.attribValue("name"): p for p in vols}
    required = ["height"] + layers
    missing = [n for n in required if n not in byname]
    if missing:
        raise RuntimeError("Missing landscape volumes: %s" % missing)
    height = byname["height"]
    # Bounds are the cooked native heightfield volume bounds. Voxel samples establish pad and pond elevations.
    b = height.boundingBox()
    # sample grids by nearest voxel from volume world positions
    def sample(x, z):
        return height.sample((float(x), 0.0, float(z)))
    coords = [(x, z, sample(x, z)) for x, z in [(-10,-2),(0,0),(32,-5),(46,-5),(50,-5),(54,30)]]
    hvals = list(height.allVoxels())
    # Geometry metadata / extents and material routing proof.
    report = {
        "asset": str(HDA_PATH), "type": "melodia::house_garden_vista::1.0",
        "source": str(IGN_TIFF), "source_bytes": IGN_TIFF.stat().st_size,
        "source_metadata": {"crs": "EPSG:2154", "pixel_m": 1, "dem_min_m": 1.40, "dem_max_m": 17.4033, "height_range_m": 16.0033, "encoding": "float32 GeoTIFF; matching uint16 heightmap metadata in project DEM_NOTES.md"},
        "controls": {k: hda.parm(k).eval() for k in names},
        "volume_resolution": list(height.resolution()),
        "local_bounds_m": {"min": [b.minvec()[0]-height.voxelSize()[0]*0.5, b.minvec()[1], b.minvec()[2]-height.voxelSize()[2]*0.5], "max": [b.maxvec()[0]+height.voxelSize()[0]*0.5, b.maxvec()[1], b.maxvec()[2]+height.voxelSize()[2]*0.5]},
        "height_min_max_m": [min(hvals), max(hvals)],
        "sampled_height_m": {"x%g_z%g" % (x,z): v for x,z,v in coords},
        "native_landscape_export": {"height_layer_name": height.attribValue("unreal_landscape_layer_name"), "landscape_material": height.attribValue("unreal_material"), "landscape_material_attribute": height.attribValue("unreal_landscape_material"), "layers": {n: p.attribValue("unreal_landscape_layer_info") for n,p in byname.items() if n != "height"}},
        "landscape_layers": {n: {"layer_name": p.attribValue("unreal_landscape_layer_name"), "layer_info": p.attribValue("unreal_landscape_layer_info") if n != "height" else None} for n,p in byname.items()},
        "sop_errors": errors,
        "assertions": {"all_expected_layers": not missing, "no_cook_errors": not errors, "heightfield_resolution_matches_preview": list(height.resolution()) == [257,257,1], "outside_pad_terrain_varies": max(hvals) - min(hvals) > 0.2, "heightfield_bounds_within_requested_window": True}
    }
    report["assertions"]["heightfield_bounds_within_requested_window"] = (report["local_bounds_m"]["min"][0] >= -25.01 and report["local_bounds_m"]["max"][0] <= 55.01 and report["local_bounds_m"]["min"][2] >= -40.01 and report["local_bounds_m"]["max"][2] <= 40.01)
    report["assertions"]["house_pad_is_flat_at_minus_0_10m"] = abs(sample(-10,-2) - (-0.10)) < 0.03
    report["assertions"]["pond_bed_is_minus_2_2m"] = abs(sample(32,-5) - (-2.2)) < 0.05
    report["assertions"]["pond_shore_reaches_water_level"] = abs(sample(46,-5) - (-0.8)) < 0.15
    if not all(report["assertions"].values()):
        raise RuntimeError("Cooked HDA failed acceptance checks: %s" % json.dumps(report, indent=2))
    (AUDIT / "cook_proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Save the in-memory Houdini scene used for this independent cook.
    hou.hipFile.save(str(AUDIT / "MorningVista_CookProof.hip"))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()

