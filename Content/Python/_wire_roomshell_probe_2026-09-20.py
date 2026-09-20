import unreal
import json

out = {"exists": {}, "hits": [], "bp": {}}

paths = [
    "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell",
    "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex",
]
for p in paths:
    out["exists"][p] = unreal.EditorAssetLibrary.does_asset_exist(p)

keywords = [
    "PCG_MelusinaHouse",
    "PCG_EscherRecursive",
    "PCG_MelusinaRoomShell",
    "_probe_pcgex",
    "MorningDell",
]
for root in ["/Game/EnvSandbox", "/Game/Melodia", "/Game"]:
    try:
        assets = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
    except Exception:
        continue
    for a in assets:
        if any(k in a for k in keywords):
            out["hits"].append(a.split(".")[0])
out["hits"] = sorted(set(out["hits"]))[:100]

bp_path = "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
out["bp"]["type"] = type(bp).__name__ if bp else None
if isinstance(bp, unreal.Blueprint):
    scs = bp.simple_construction_script
    out["bp"]["has_scs"] = scs is not None
    nodes_info = []
    if scs:
        for n in scs.get_all_nodes():
            try:
                tc = n.component_class
                nodes_info.append({
                    "var": str(n.get_variable_name()),
                    "class": tc.get_name() if tc else None,
                })
            except Exception as e:
                nodes_info.append({"err": str(e)})
    out["bp"]["scs_nodes"] = nodes_info
    try:
        gc = bp.generated_class()
        cdo = unreal.get_default_object(gc)
        comps = cdo.get_components_by_class(unreal.ActorComponent)
        out["bp"]["cdo_comps"] = [
            f"{c.get_name()}:{c.get_class().get_name()}" for c in comps
        ]
    except Exception as e:
        out["bp"]["cdo_err"] = str(e)

# PCG component class availability
for cname in ["PCGComponent", "PcgComponent"]:
    try:
        cls = getattr(unreal, cname)
        out[f"cls_{cname}"] = str(cls)
    except Exception as e:
        out[f"cls_{cname}"] = str(e)

print("PROBE_JSON " + json.dumps(out))
