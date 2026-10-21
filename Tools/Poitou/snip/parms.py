f_live.addParmTemplate(hou.ToggleParmTemplate("real_meshes", "Use project meshes (else BasicShapes)", default_value=True))
f_live.addParmTemplate(hou.StringParmTemplate("landscape_material", "Landscape material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Landscape_Nikki.MI_Poitou_Landscape_Nikki",)))
f_live.addParmTemplate(hou.StringParmTemplate("layerinfo_dir", "LayerInfo folder", 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo",)))
f_iles = F("f_iles", "Iles", folder_type=hou.folderType.Tabs)
f_iles.addParmTemplate(hou.IntParmTemplate("iles_count", "Island count", 1, default_value=(4,), min=0, max=6))
for pn, lab, v in [("iles_seed","Island seed",3.0),("iles_radius","Island radius (m)",70.0),("iles_hmin","Island min height (m)",4.0),("iles_hmax","Island max height (m)",12.0)]:
    f_iles.addParmTemplate(hou.FloatParmTemplate(pn, lab, 1, default_value=(v,)))
f_hz = F("f_hz", "Horizon", folder_type=hou.folderType.Tabs)
f_hz.addParmTemplate(hou.ToggleParmTemplate("horizon_on", "Horizon ring + bands", default_value=False))
for pn, lab, v in [("skirt_extent","Skirt extent (m, square)",6000.0),("swell_amp","Swell max height (m)",10.0),("swell_ramp","Swell ramp distance (m)",1500.0),("swell_freq","Swell noise freq",0.0012),
                   ("band0_dist","Band 0 radius (m)",1300.0),("band1_dist","Band 1 radius (m)",1900.0),("band2_dist","Band 2 radius (m)",2600.0),("band_spacing","Band tree spacing (m)",9.0),("band_gap","Band gap threshold",0.45),
                   ("spire_dist","Far spire radius (m)",2300.0),("spire_angle","Far spire angle (deg)",35.0),("spire_height","Far spire height (m)",40.0),("mist_strength","Mist mask strength",1.0)]:
    f_hz.addParmTemplate(hou.FloatParmTemplate(pn, lab, 1, default_value=(v,)))
f_hz.addParmTemplate(hou.IntParmTemplate("spire_count", "Far spires", 1, default_value=(2,), min=0, max=3))
f_hz.addParmTemplate(hou.StringParmTemplate("skirt_material", "Skirt material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_FarStone.MI_Poitou_FarStone",)))
for f in (f_live, f_ctl, f_rise, f_iles, f_hz): ptg.append(f)
