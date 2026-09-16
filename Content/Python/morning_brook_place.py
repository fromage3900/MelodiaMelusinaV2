import unreal, json
from unreal import EditorActorSubsystem, EditorLevelLibrary, EditorAssetLibrary

REPORT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_brook_apply.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
rep = {"lake": {}, "volumes": []}


def trace_z(x, y, top=3000.0, bottom=-3000.0):
    ign = []
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, top), unreal.Vector(x, y, bottom),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, ign,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = hit.to_dict()
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


# --- 1. Lake at the sheep dell ---
lake_cls = EditorAssetLibrary.load_asset(
    "/Oceanology_Plugin/Design/Lake/Blueprints/Lake/BP_OceanologyLake")
if lake_cls is None:
    rep["lake"] = {"ok": False, "err": "BP load null"}
else:
    lx, ly = -950.0, 2300.0
    gz = trace_z(lx, ly)
    # dell floor expected near -650; fall back if trace misses
    lz = (gz + 12.0) if gz is not None else -638.0
    lake = EditorLevelLibrary.spawn_actor_from_object(
        lake_cls, unreal.Vector(lx, ly, lz), unreal.Rotator(0, 0, 0))
    if lake is None:
        rep["lake"] = {"ok": False, "err": "spawn null"}
    else:
        lake.set_actor_label("Morning_SheepDell_Lake")
        try:
            org, ext = lake.get_actor_bounds(False)
            width = max(float(ext.x) * 2.0, 1.0)
            s = 520.0 / width
            s = max(0.05, min(s, 2.0))
            lake.set_actor_scale3d(unreal.Vector(s, s, s))
        except Exception as e:
            s = 0.2
            lake.set_actor_scale3d(unreal.Vector(s, s, s))
            rep["lake"]["bounds_note"] = str(e)[:120]
        rep["lake"] = {"ok": True, "loc": [lx, ly, lz],
                       "ground_z": gz, "scale": s}

# --- 2 + 3. PCG volumes: banks (BellTree, standalone) + arpeggio ---
plots = [
    ("Morning_Dell_Banks", "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden",
     (-950.0, 2300.0, -500.0), (6.0, 5.0, 2.5)),
    ("Morning_Brook_Arpeggio", "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge",
     (-350.0, 2320.0, -480.0), (6.0, 3.0, 2.5)),
]
for label, gpath, loc, scl in plots:
    rec = {"label": label, "graph": gpath}
    try:
        vol = EditorLevelLibrary.spawn_actor_from_class(
            unreal.PCGVolume, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
        vol.set_actor_label(label)
        vol.set_actor_scale3d(unreal.Vector(*scl))
        comp = vol.get_component_by_class(unreal.PCGComponent)
        g = EditorAssetLibrary.load_asset(gpath)
        if g is None:
            rec["ok"] = False
            rec["err"] = "graph load null"
        else:
            comp.set_graph(g)
            comp.generate(True)
            isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
            counts = []
            for ism in isms:
                try:
                    m = ism.static_mesh
                    counts.append({
                        "mesh": (str(m.get_path_name()) if m else None),
                        "count": ism.get_instance_count()})
                except Exception as e:
                    counts.append({"err": str(e)[:100]})
            rec["ok"] = True
            rec["isms"] = counts
            rec["total"] = sum(c.get("count", 0) for c in counts)
    except Exception as e:
        rec["ok"] = False
        rec["err"] = str(e)[:200]
    rep["volumes"].append(rec)

open(REPORT, "w").write(json.dumps(rep, indent=1))
print("BROOK_APPLY_WROTE " + REPORT)
