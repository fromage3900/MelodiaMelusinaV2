import unreal, json, math

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_crater.json"
world = unreal.EditorLevelLibrary.get_editor_world()
rep = {"samples": []}
CX, CY = -950.0, 2300.0
pts = [(CX, CY)]
for r in (330.0, 480.0, 650.0):
    for k in range(4):
        a = math.radians(k * 90.0 + r)
        pts.append((CX + math.cos(a) * r, CY + math.sin(a) * r))
for (x, y) in pts:
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world, unreal.Vector(x, y, 3000.0), unreal.Vector(x, y, -3000.0),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True,
            unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
        zs = []
        if hits is not None:
            for h in hits:
                try:
                    d = h.to_dict()
                    if d.get("blocking_hit"):
                        zs.append(round(float(d["impact_point"].z), 1))
                except Exception:
                    continue
        rep["samples"].append({"xy": [round(x, 1), round(y, 1)], "hits": zs})
    except Exception as e:
        rep["samples"].append({"xy": [x, y], "err": str(e)[:120]})
open(OUT, "w").write(json.dumps(rep, indent=1))
print("CRATER_WROTE")
