"""Which declared params are actually wired? Runtime ground truth, in Blender.

A static scan cannot answer this. This codebase wires sockets through loop
variables (paris_wall_detail's `specs` tuples), through dynamically built names
(civic_kit's BUILDER_PARAM_DEFAULTS loop) and through module helpers, so any
string-literal scan reports healthy builders as dead - `_melodia_param_wiring_audit.py`
is kept only as a triage heuristic for that reason and over-reports badly.

The reliable answer is the built tree. A Group Input output socket with NO
outgoing link is connected to nothing: no preset, no slider, and no
`mel_gn.apply_preset` can ever affect geometry through it, while the UI still
shows it and the apply operator still counts it as "applied". That is the
decorative-param class, and it is verified by the fountain (civic_kit builds
from a Python PROPS namespace) and by GN_PARIS_SlabTrim (its BBox sockets are
declared but the geometry derives the box from GeometryNodeBoundBox).

Excludes the geometry passthrough and the universal music params, which are
added by new_geometry_tree for every builder and are not per-builder controls.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_gn_param_wiring.py

Exit 0 only when no builder has an unwired param socket.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")
if os.environ.get("MELODIA_AUDIT_LIVE") == "1":
    sys.path.insert(0, APPDATA_ADDONS)
else:
    sys.path.insert(0, DEPLOY)
    sys.path.append(APPDATA_ADDONS)

from surreal_arch.melodia_gn import core  # noqa: E402

# Not per-builder controls: the passthrough and the universal music params.
SKIP = {"Geometry"} | set(getattr(core, "_MUSIC_PARAMS", set()))

built = 0
errors = []
with_dead = []
dead_total = 0

for bid in sorted(core.GROUP_BUILDERS):
    try:
        res = core.GROUP_BUILDERS[bid]()
    except Exception as exc:
        errors.append(f"{bid}: {type(exc).__name__}: {exc}")
        continue
    tree = res[0] if isinstance(res, (tuple, list)) and res else res
    if tree is None or not hasattr(tree, "nodes"):
        continue
    gin = None
    for node in tree.nodes:
        if node.bl_idname == "NodeGroupInput":
            gin = node
            break
    if gin is None:
        continue
    built += 1
    dead = []
    for sock in gin.outputs:
        if sock.name in SKIP:
            continue
        if not sock.is_linked:
            dead.append(sock.name)
    if dead:
        dead_total += len(dead)
        with_dead.append({"builder": bid, "tree": tree.name, "dead": dead})

print(f"[param-wiring] builders built={built} build_errors={len(errors)}")
for e in errors[:10]:
    print(f"[param-wiring] BUILD ERROR {e}")
print(f"[param-wiring] builders with unwired params: {len(with_dead)}")
print(f"[param-wiring] unwired param sockets total: {dead_total}")
for entry in sorted(with_dead, key=lambda d: -len(d["dead"]))[:40]:
    print(f"[param-wiring]   {entry['builder']}: {len(entry['dead'])} dead "
          f"-> {entry['dead'][:8]}")

if with_dead or errors:
    raise SystemExit(1)
print("[param-wiring] PASS")
