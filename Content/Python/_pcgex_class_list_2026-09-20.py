# read-only: list unreal classes with PCGEx in name
import unreal, json
from pathlib import Path
from datetime import datetime, timezone

names = []
# dir(unreal) filter
for n in dir(unreal):
    if "pcgex" in n.lower() or n.startswith("PCGEx"):
        names.append(n)
# also try asset registry for PCG settings classes via known factories
extra = []
for n in sorted(names):
    try:
        cls = getattr(unreal, n)
        extra.append({"name": n, "type": type(cls).__name__})
    except Exception as e:
        extra.append({"name": n, "err": str(e)[:80]})

# filter to likely node/settings
nodeish = [e for e in extra if any(k in e["name"].lower() for k in [
    "settings", "node", "path", "shape", "spawn", "filter", "create", "points", "spline", "wall", "grid"
])]

report = {
    "schema": "melodia.pcgex_class_list.v1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "count": len(extra),
    "all": [e["name"] for e in extra],
    "nodeish_sample": nodeish[:120],
}
out = Path(unreal.Paths.project_saved_dir()) / "Audit" / "pcgex_class_list_2026-09-20.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("PCGEX_CLASSES " + json.dumps({"count": len(extra), "nodeish": len(nodeish), "sample": [e["name"] for e in nodeish[:40]]}))
