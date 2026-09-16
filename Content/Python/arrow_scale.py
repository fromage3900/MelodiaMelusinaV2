import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/arrow_scale.v1.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ed.get_editor_world()
al = unreal.EditorAssetLibrary
rep = {"spawned": []}

TWIN = "/Game/Cinematics/Shorewake/HERO01/WaveHarp_R08/SM_ME_WaveHarp_Arrow_R08"
STOCK = None
# resolve stock archer arrow mesh from BP_Arrow's Arrow component
bp = al.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Projectiles/BP_Arrow")
cdo = unreal.GameplayStatics.get_actor_of_class if False else None
try:
    dco = al.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Projectiles/BP_Arrow.BP_Arrow_C")
    for p in dco.get_class().get_default_object().get_editor_property("component_templates") or []:
        nm = str(p.get_fname()) if hasattr(p, "get_fname") else str(p)
        if "Arrow" in nm or "Sphere" in nm or "Mesh" in nm:
            try:
                m = p.get_editor_property("static_mesh")
                if m is not None:
                    STOCK = m.get_path_name()
                    break
            except Exception:
                pass
except Exception as e:
    rep["stock_resolve_err"] = str(e)[:150]
rep["stock_mesh"] = STOCK


def trace(x, y):
    h = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, -21.2), unreal.Vector(x, y, -4000.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = h.to_dict() if h is not None else {}
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


def bounds_of(mesh_path):
    m = al.load_asset(mesh_path)
    b = m.get_bounds() if m is not None else None
    return str(b)[:200]


rep["twin_bounds"] = bounds_of(TWIN)
pairs = [("ArrowScale_Twin", TWIN, 1250.0), ("ArrowScale_Stock", STOCK, 1330.0)]
for label, mesh_path, x in pairs:
    if mesh_path is None:
        rep["spawned"].append({"label": label, "skipped": "no_mesh"})
        continue
    m = al.load_asset(mesh_path)
    gz = trace(x, 2200.0)
    loc = unreal.Vector(x, 2200.0, (gz if gz is not None else -590.0) + 60.0)
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(m, loc)
    a.set_actor_label(label)
    a.modify()
    l = a.get_actor_location()
    e = a.get_actor_bounds(False)[1]
    rep["spawned"].append({"label": label, "mesh": mesh_path,
                           "loc": [round(float(l.x), 1), round(float(l.y), 1),
                                   round(float(l.z), 1)],
                           "extent": [round(float(e.x), 1), round(float(e.y), 1),
                                      round(float(e.z), 1)]})
rep["saved"] = bool(unreal.EditorLevelLibrary.save_current_level())
open(OUT, "w").write(json.dumps(rep, indent=1))
print("ARROWSCALE_WROTE " + json.dumps(rep["spawned"])[:400] + " saved=" + str(rep["saved"]))
