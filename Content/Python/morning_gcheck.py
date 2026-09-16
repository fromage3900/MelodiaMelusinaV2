import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_gcheck.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
out = {}
for a in svc.get_all_level_actors():
    if a.get_actor_label() == "PCG_MelodiaOpening_Morning_Dressing":
        isms = a.get_components_by_class(unreal.InstancedStaticMeshComponent)
        recs = []
        for ism in isms:
            try:
                m = ism.static_mesh
                recs.append({
                    "mesh": (str(m.get_path_name()) if m else None),
                    "count": ism.get_instance_count(),
                })
            except Exception as e:
                recs.append({"err": str(e)[:120]})
        out["pcg_isms"] = recs
        try:
            sc = a.get_actor_scale3d()
            out["pcg_scale"] = [sc.x, sc.y, sc.z]
        except Exception:
            pass

al = unreal.EditorAssetLibrary
cands = al.list_assets("/Game/EnvSandbox/PCG", recursive=True, include_folder=False)
out["arp_hits"] = [c for c in cands if "Arpeggio" in c]
for gp in out["arp_hits"][:3] + ["/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden"]:
    g = al.load_asset(gp)
    if g is None:
        out[gp] = "MISSING"
        continue
    try:
        nodes = g.get_editor_property("nodes")
        names = [n.get_class().get_name() for n in nodes]
        import collections
        out[gp] = {
            "nodes": len(nodes),
            "spawners": names.count("PCGSpawnActorNode"),
            "kinds": dict(list(collections.Counter(names).items())[:14]),
        }
    except Exception as e:
        out[gp] = "ERR " + str(e)[:150]

open(OUT, "w").write(json.dumps(out, indent=1))
print("GCHECK_WROTE " + OUT)
