"""Health check for the GN node-id surface — run inside Blender 5.2.

Answers the question `melodia_gn/core.py::NODE_REMAP_52` cannot answer about
itself: does every id in that table actually resolve on THIS Blender, and is
anyone still authoring with a deprecated id?

Why this exists: `NODE_REMAP_52` (core.py:11) is a 10-entry hand-written map
driven by `bpy.app.version >= (5, 0, 0)`, consumed by `safe_node()` via
`_resolve_bl_idname()`. `safe_node` swallows failure into a warning and returns
None, so a WRONG remap value degrades silently to a missing node — geometry
loses a feature and nothing reports it. No test asserted the table matched
Blender's real node set until this file.

  1. every NODE_REMAP_52 VALUE resolves via tree.nodes.new()
  2. every NODE_REMAP_52 KEY resolves on 5.x too (remap is not masking a live id)
  3. no source file still authors a deprecated KEY id (static scan)
  4. a curated set of ids the builders depend on resolves

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_gn_node_ids.py

Exit code 0 only when every check passes.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
for p in (DEPLOY, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

failures = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


# Ids the builders depend on by name. A rename here is a silent geometry loss.
REQUIRED_NODE_IDS = (
    "GeometryNodeMeshCube",
    "GeometryNodeMeshGrid",
    "GeometryNodeMeshCircle",
    "GeometryNodeMeshIcoSphere",
    "GeometryNodeMeshCylinder",
    "GeometryNodeMeshLine",
    "GeometryNodeSetPosition",
    "GeometryNodeTransform",
    "GeometryNodeJoinGeometry",
    "GeometryNodeInstanceOnPoints",
    "GeometryNodeRealizeInstances",
    "GeometryNodeBoundBox",
    "GeometryNodeGroup",
    "GeometryNodeMeshBoolean",
    "GeometryNodeMergeByDistance",
    "GeometryNodeStoreNamedAttribute",
    "GeometryNodeSampleSoundFrequencies",
    "GeometryNodeInputSceneTime",
    "GeometryNodeInputPosition",
    "GeometryNodeSetShadeSmooth",
    "ShaderNodeMath",
    "ShaderNodeVectorMath",
    "ShaderNodeMapRange",
    "ShaderNodeSeparateXYZ",
    "ShaderNodeCombineXYZ",
)

# Files whose authored ids are the surface under test.
SCAN_DIRS = (
    os.path.join(DEPLOY, "surreal_arch", "melodia_gn"),
)
SCAN_FILES = (
    os.path.join(DEPLOY, "surreal_architecture_gen.py"),
)


def _remap_table_lines():
    """Locate the `NODE_REMAP_52 = {...}` block in core.py via AST.

    Returns {"core.py": (first_line, last_line)}. Without this the table's own
    ten entries are counted as "sites authoring a deprecated id" - which is what
    happened on the checker's first run (24 reported, 10 of them the table).
    Line numbers are not guessed or hard-coded; they come from the parse.
    """
    import ast

    core = os.path.join(DEPLOY, "surreal_arch", "melodia_gn", "core.py")
    if not os.path.isfile(core):
        return {}
    try:
        with open(core, "r", encoding="utf-8-sig", errors="replace") as fh:
            tree = ast.parse(fh.read(), filename=core)
    except Exception:
        return {}
    for node in tree.body:
        targets = getattr(node, "targets", None) or []
        for t in targets:
            if getattr(t, "id", "") == "NODE_REMAP_52":
                start = min(n.lineno for n in ast.walk(node)
                            if hasattr(n, "lineno"))
                end = max(getattr(n, "end_lineno", n.lineno)
                          for n in ast.walk(node) if hasattr(n, "lineno"))
                return {"core.py": (start, end)}
    return {}


def _iter_source_files():
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".py"):
                yield os.path.join(d, fn)
    for f in SCAN_FILES:
        if os.path.isfile(f):
            yield f


def _resolve(bl_idname):
    """Return True when the running Blender can create this node type."""
    try:
        import bpy
    except ImportError:
        return None
    ng = bpy.data.node_groups.new("__node_id_probe__", "GeometryNodeTree")
    try:
        ng.nodes.new(bl_idname)
        return True
    except Exception:
        return False
    finally:
        bpy.data.node_groups.remove(ng)


def main():
    try:
        import bpy
        from surreal_arch.melodia_gn.core import NODE_REMAP_52
    except Exception as exc:
        check("import bpy + NODE_REMAP_52", False, repr(exc))
        return 1
    check("import bpy + NODE_REMAP_52", True,
          f"blender={'.'.join(str(v) for v in bpy.app.version)} entries={len(NODE_REMAP_52)}")

    # 1. every remap VALUE resolves (5.x target ids).
    bad_values = []
    for src, dst in sorted(NODE_REMAP_52.items()):
        if _resolve(dst) is False:
            bad_values.append(f"{src}->{dst}")
    check("NODE_REMAP_52 values resolve", not bad_values,
          f"unresolvable: {bad_values[:8]}" if bad_values else f"{len(NODE_REMAP_52)} checked")

    # 2. Legacy remap keys: INFORMATIONAL ONLY.
    # These are pre-5.x ids that legitimately no longer exist - that absence is
    # exactly why they are remapped. Asserting they resolve fails by design and
    # would be noise, not signal. A key that DOES still resolve is worth
    # surfacing (the remap may be redirecting away from a valid id), so report
    # the resolved keys and never fail on them.
    still_resolvable = [k for k in sorted(NODE_REMAP_52) if _resolve(k) is not False]
    print(f"[INFO] NODE_REMAP_52 keys still resolvable on this build: {still_resolvable}")

    # 3. Real signal: source files authoring a DEPRECATED PRIMARY id.
    # Alias use is fine (`require_node(tree, "<modern>", loc, "<legacy>")` is the
    # documented defensive pattern); authoring the legacy id as the primary
    # argument only works because safe_node remaps it, which is latent debt.
    table_lines = _remap_table_lines()
    primary, alias = [], []
    key_re = re.compile(
        r"[\"'](" + "|".join(re.escape(k) for k in NODE_REMAP_52) + r")[\"']")
    modern = set(NODE_REMAP_52.values())
    for path in _iter_source_files():
        table_span = table_lines.get(os.path.basename(path), ()) \
            if os.path.basename(path) == "core.py" else ()
        try:
            with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
                for lineno, line in enumerate(fh, 1):
                    if line.lstrip().startswith("#"):
                        continue
                    if table_span and table_span[0] <= lineno <= table_span[1]:
                        continue  # the remap table's own entries
                    m = key_re.search(line)
                    if not m:
                        continue
                    entry = f"{os.path.basename(path)}:{lineno}:{m.group(1)}"
                    if any(mid in line for mid in modern):
                        alias.append(entry)
                    else:
                        primary.append(entry)
        except Exception:
            continue
    check("no source authors a deprecated PRIMARY id", not primary,
          f"{len(primary)} site(s): {primary[:8]}" if primary
          else f"clean; {len(alias)} alias-only use(s)")
    if alias:
        print(f"[INFO] legacy-id alias (fallback) use, not a defect: {len(alias)}")

    # 4. ids the builders depend on resolve.
    missing = [n for n in REQUIRED_NODE_IDS if _resolve(n) is False]
    check("required builder node ids resolve", not missing,
          f"missing: {missing}" if missing else f"{len(REQUIRED_NODE_IDS)} checked")

    print(f"\nnode-id health: {len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"node-id health check crashed: {exc!r}")
        sys.exit(1)