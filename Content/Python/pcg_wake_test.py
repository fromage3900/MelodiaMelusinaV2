import unreal, json

import os

# Repo-relative so the project runs from any drive letter (e.g. G:). Content/Python/<this> -> repo root is two levels up.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(_ROOT, "Saved", "Audit", "pcg_wake_test.json")
rep = {}
al = unreal.EditorAssetLibrary
plots = [
    ("Wake_Mandala", "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_MandalaBloom"),
    ("Wake_Phyllo", "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden"),
    ("Wake_Terrace", "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_TerraceGarden"),
    ("Wake_WallPath", "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_WallGardenPath"),
]
x = 6000.0
for label, gpath in plots:
    rec = {"graph": gpath}
    try:
        vol = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PCGVolume, unreal.Vector(x, 6000.0, 0.0), unreal.Rotator(0, 0, 0))
        vol.set_actor_label(label)
        vol.set_actor_scale3d(unreal.Vector(10.0, 10.0, 4.0))
        comp = vol.get_component_by_class(unreal.PCGComponent)
        g = al.load_asset(gpath)
        comp.set_graph(g)
        comp.generate(True)
        isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
        counts = []
        for ism in isms:
            try:
                m = ism.static_mesh
                counts.append({"mesh": (str(m.get_path_name()).split(".")[-1] if m else None),
                               "count": ism.get_instance_count()})
            except Exception:
                pass
        rec["isms"] = counts
        rec["total"] = sum(c.get("count", 0) for c in counts)
        rec["volume"] = label
    except Exception as e:
        rec["err"] = str(e)[:200]
    rep[label] = rec
    x += 1500.0
open(OUT, "w").write(json.dumps(rep, indent=1))
print("WAKE_WROTE")
