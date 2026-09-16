import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_brook_fix.json"
rep = {}
al = unreal.EditorAssetLibrary

# --- lake via generated class, dell snap kept ---
try:
    bp = al.load_asset(
        "/Oceanology_Plugin/Design/Lake/Blueprints/Lake/BP_OceanologyLake")
    cls = bp.generated_class() if hasattr(bp, "generated_class") else bp
    lake = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls, unreal.Vector(-950.0, 2300.0, -638.0), unreal.Rotator(0, 0, 0))
    if lake is None:
        rep["lake"] = {"ok": False, "err": "spawn null even via class"}
    else:
        lake.set_actor_label("Morning_SheepDell_Lake")
        try:
            org, ext = lake.get_actor_bounds(False)
            width = max(float(ext.x) * 2.0, 1.0)
            s = max(0.05, min(520.0 / width, 2.0))
        except Exception:
            s = 0.2
        lake.set_actor_scale3d(unreal.Vector(s, s, s))
        rep["lake"] = {"ok": True, "scale": s}
except Exception as e:
    rep["lake"] = {"ok": False, "err": str(e)[:200]}

# --- BellTree + Arpeggio node titles (what do they eat?) ---
for gp, key in [
        ("/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden", "bell"),
        ("/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge", "arp")]:
    g = al.load_asset(gp)
    titles = []
    try:
        for n in g.get_editor_property("nodes"):
            t = ""
            for attr in ("node_title", "get_node_title", "caption"):
                try:
                    v = getattr(n, attr)
                    t = v() if callable(v) else v
                    if t:
                        break
                except Exception:
                    continue
            titles.append(str(t)[:60] or n.get_class().get_name())
    except Exception as e:
        titles = ["ERR " + str(e)[:150]]
    rep[key] = titles

open(OUT, "w").write(json.dumps(rep, indent=1))
print("BROOK_FIX_WROTE " + OUT)
