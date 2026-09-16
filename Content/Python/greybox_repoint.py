import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/greybox_repoint.json"
rep = {"repointed": [], "notes": []}
al = unreal.EditorAssetLibrary
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Architecture/Greybox/"
ALIAS = {"M_classical_arch_20": "MI_Greybox_Classic_Arch_20"}

meshes = []
for entry in al.list_assets("/Game/Greybox_Kit", recursive=False, include_folder=False):
    base = entry.split(".")[0]
    if "/Game/Greybox_Kit/SM_" in base:
        meshes.append(base)
for mpath in sorted(set(meshes)):
    try:
        mesh = al.load_asset(mpath)
        if mesh is None:
            continue
        try:
            sm = mesh.get_editor_property("static_materials")
        except Exception as e:
            rep["notes"].append(mpath.split("/")[-1] + " slots ERR " + str(e)[:100])
            continue
        for idx, s in enumerate(sm):
            try:
                sname = str(s.get_editor_property("material_slot_name"))
            except Exception:
                continue
            base = sname.split(".")[-1]
            mi_name = ALIAS.get(base)
            if mi_name is None and base.startswith("M_"):
                # M_arch_02_mat -> MI_Greybox_Arch_02 ; M_frieze_01_001 -> MI_Greybox_Frieze_01
                core = base[2:]
                for suf in ("_mat", "_001"):
                    if core.endswith(suf):
                        core = core[: -len(suf)]
                mi_name = "MI_Greybox_" + core
            if mi_name is None:
                continue
            mi = al.load_asset(MI_DIR + mi_name)
            if mi is None:
                rep["notes"].append(mpath.split("/")[-1] + " slot%d MI missing %s" % (idx, mi_name))
                continue
            try:
                mesh.set_material(idx, mi)
                rep["repointed"].append({"mesh": mpath.split("/")[-1], "slot": idx, "mi": mi_name})
            except Exception as e:
                rep["notes"].append(mpath.split("/")[-1] + " slot%d ERR " % idx + str(e)[:130])
    except Exception as e:
        rep["notes"].append(mpath + " ERR " + str(e)[:120])

open(OUT, "w").write(json.dumps(rep, indent=1))
print("REPOINT_WROTE repointed=%d notes=%d" % (len(rep["repointed"]), len(rep["notes"])))
