import unreal, json

MANIFEST = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/greybox_toon_convert.v1.json"
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Architecture/Greybox/"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TEXROOT = "/Game/Greybox_Kit/"
al = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
rep = {"created": [], "repointed": [], "notes": []}

MATS = [
    ("M_arch_02_mat", "Arch_02", "classic_arch_02", False),
    ("M_arch_03_mat", "Arch_03", "classic_arch_03", False),
    ("M_arch_04_mat", "Arch_04", "classic_arch_04", False),
    ("M_arch_05_mat", "Arch_05", "classic_arch_05", False),
    ("M_arch_06_mat", "Arch_06", "classic_arch_06", False),
    ("M_arch_11_mat", "Arch_11", "classic_arch_11", False),
    ("M_classic_arch_13", "Classic_Arch_13", "classic_arch_13", False),
    ("M_classic_arch_18_mat", "Classic_Arch_18", "classic_arch_18", False),
    ("M_classical_arch_20", "Classic_Arch_20", "classic_arch_20", False),
    ("M_column_2_mat", "Column_02", "column_02", True),
    ("M_frieze_01_001", "Frieze_01", "frieze_01", False),
]
NORMAL_SUFFIX = {"column_02": "NormalGL"}


def tex(stem, kind):
    if kind == "normal":
        suf = NORMAL_SUFFIX.get(stem, "Normal_GL")
        return TEXROOT + stem + "_" + suf
    if kind == "metal":
        return TEXROOT + stem + "_Metallic"
    if kind == "rough":
        return TEXROOT + stem + "_Roughness"
    return TEXROOT + stem + "_BaseColor"


parent = al.load_asset(PARENT)
mi_of = {}
for mat, stem, tstem, is_metal in MATS:
    mi_name = "MI_Greybox_" + stem
    mi_path = MI_DIR + mi_name
    try:
        mi = al.load_asset(mi_path)
        if mi is None:
            mi = at.create_asset(mi_name, MI_DIR,
                                 unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", parent)
        routed = {}
        for pname, kind in (("Albedo", "base"), ("NormalMap", "normal"),
                            ("RoughnessMap", "rough")):
            t = al.load_asset(tex(tstem, kind))
            if t is not None:
                mi.set_texture_parameter_value_editor_only(pname, t)
                routed[pname] = True
        if is_metal:
            t = al.load_asset(tex(tstem, "metal"))
            if t is not None:
                mi.set_texture_parameter_value_editor_only("MetallicMap", t)
                routed["MetallicMap"] = True
            mi.set_scalar_parameter_value_editor_only("Metallic", 1.0)
        mi.set_scalar_parameter_value_editor_only("TextureWeight", 1.0)
        mi.set_scalar_parameter_value_editor_only("LayerA_TextureWeight", 1.0)
        mi_of[mat] = mi_path
        rep["created"].append({"mi": mi_name, "from": mat, "routed": routed})
    except Exception as e:
        rep["notes"].append(mi_name + " ERR " + str(e)[:180])

# repoint mesh slots whose material matches one of the 11
meshes = []
for entry in al.list_assets("/Game/Greybox_Kit", recursive=False, include_folder=False):
    if "/Game/Greybox_Kit/SM_" in entry:
        meshes.append(entry.split(".")[0])
for mpath in sorted(set(meshes)):
    try:
        mesh = al.load_asset(mpath)
        if mesh is None:
            continue
        slots = mesh.get_material_slot_names() if hasattr(mesh, "get_material_slot_names") else []
        # fallback: static_materials property
        if not slots:
            try:
                sm = mesh.get_editor_property("static_materials")
                slots = [str(s.get_editor_property("material_slot_name")) for s in sm]
            except Exception:
                continue
        for idx, sname in enumerate(slots):
            base = str(sname).split(".")[-1]
            if base in mi_of:
                mi = al.load_asset(mi_of[base])
                try:
                    mesh.set_material(idx, mi)
                    rep["repointed"].append({"mesh": mpath.split("/")[-1],
                                            "slot": idx, "mi": mi_of[base].split("/")[-1]})
                except Exception as e:
                    rep["notes"].append(mpath.split("/")[-1] + " slot%d ERR " % idx + str(e)[:120])
    except Exception as e:
        rep["notes"].append(mpath + " ERR " + str(e)[:120])

open(MANIFEST, "w").write(json.dumps(rep, indent=1))
print("GREYBOX_WROTE created=%d repointed=%d notes=%d" % (
    len(rep["created"]), len(rep["repointed"]), len(rep["notes"])))
