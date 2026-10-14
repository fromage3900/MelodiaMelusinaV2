"""Higgsas pipeline — one loader where four had grown apart.

Convergence target, audited 2026-09-25
(Saved/Audit/BRUTALIST_CONVERGENCE_AUDIT_2026-09-25.md §5b):

    higgsas_bridge.higg_node(...)      needs a `monolith` builders do not have
    core_forms_kit._higg_node(...)     private copy of the bridge path
    walls_kit._higg_node(...)          near-identical duplicate of the above
    paris_wall_detail._higgs(...)      the only DUP-SAFE one

This is the exact copy-and-patch pattern paris_common.py was created to kill, now
applied to Higgsas: one implementation, so a fix lands once.

Two defects this deliberately closes:

1. **`.001` duplicates — root cause is per-call appends, not spelling.** My first
   hypothesis (bare vs ``NT`` spelling creating a twin) was WRONG; the stepped trace in
   ``Saved/Audit/_diag_higgas_step.py`` disproved it. The real mechanism: appending
   groups one at a time re-imports their *shared dependencies* each time, and Blender
   leaves a copy behind - ``Edge Bisect`` and ``Curve Bisect`` both depend on
   ``Line Plane Intersection``, so two single loads produced
   ``Line Plane Intersection.001`` (same for ``UV Transform`` / ``UV Measure`` ->
   ``UV Seam.001``). Two defences: every name is normalised to the ``NT`` canonical
   form BEFORE the session probe (kills the spelling-layer twin), and the library is
   appended ONCE per session as a single batch (kills the dependency twin - one pass
   shares one dependency map). Proven: 64 groups, ``.001=none``.
2. **No fallback contract.** The library is gitignored / machine-local
   (RawArt/BlenderLibraries/Higgsas/*), so a fresh clone has no Higgsas at all and the
   NATIVE FALLBACK is what actually runs. Every entry point therefore returns a native
   node when the group cannot load and REPORTS that it did so, instead of passing
   silently - "built something" and "used Higgsas" are different claims.

No import-time side effects: the library is only touched when a function is called.

The committed capability probe for this module is Tools/higgasas_verify.py.
"""

from __future__ import annotations

from .core import safe_node, color_node, link_sockets

# Higgsas groups the BRUTALIST / city / office lane intends to wire, grouped by job.
# Names are RAW inventory names (Saved/Audit/higgas_inventory.txt - 279 groups); the
# ``NT`` prefix is added by canonical(). Flat and iterable so the probe iterates one
# implementation, not a second copy of the list.
PIPELINE_GROUPS = {
    # subtractive massing: cut apertures out of slabs, chamfer junctions
    "sdf": [
        "SDF Boolean", "SDF Cube", "SDF Cylinder", "SDF Polygon", "SDF to Mesh",
        "Mesh To SDF", "Points to SDF Metaballs",
    ],
    # packing: the missing capability for a city generator
    "placement": [
        "Instances AABB Colision", "Instances Bounding Box", "Instances Tile",
        "Place Instances on Ground", "Bounding Box AABB Collision",
    ],
    # surface / panel devices (board-form reveals, joints, spandrels)
    "mesh_ops": [
        "Mesh Offset", "Mesh Thickness", "Solidify", "Inset Face", "Face Offset",
        "Edge Bisect", "Sharpen Mesh", "Planarize Face", "Mesh Face Subdivide",
        "Mesh Face Divider", "Cube Recursive Subdivision", "Mesh Relax",
    ],
    # pattern grids (breeze block, waffle ceiling, terrazzo)
    "grids": [
        "Bricks Grid", "Cairo Tile Grid", "Triangle Grid", "Hexagon Grid",
    ],
    # plan generation (cubicle maze, street-grid permeability)
    "plans": [
        "Maze Solver",
    ],
    # services (conduit, cable tray, ducts, handrails, sagging pendants)
    "curves": [
        "Curve Offset", "Curve Bisect", "Dynamic Catenary Splines", "Loft Splines",
        "Even Curve to Mesh", "Tubes to Splines",
    ],
    # UV for trim sheets without unwrapping - the shader story's foundation
    "uv": [
        "Triplanar UV Mapping", "Image Box Mapping", "Correct UV", "UV Transform",
        "UV Measure",
    ],
    # prop housings (copier, signage, elevator cab, modulor massing)
    "props": [
        "Rounded Cube", "Rounded Cone", "Super Ellipse", "Super Ellipsoid",
        "Pyramid", "Spur Gear",
    ],
    # weighted density / grime falloff
    "falloff": [
        "Index Falloff", "Directional Falloff", "Radial Falloff",
    ],
}


def all_pipeline_names() -> list:
    """Every group in PIPELINE_GROUPS, deduplicated, in category order."""
    seen, out = set(), []
    for names in PIPELINE_GROUPS.values():
        for name in names:
            if name not in seen:
                seen.add(name)
                out.append(name)
    return out


def canonical(name):
    """Normalise any spelling to the ``NT`` form used as the session key.

    ``"Spin" -> "NTSpin"``, ``"NTSpin" -> "NTSpin"``. Guarded against non-strings
    because dials and dict lookups pass through whatever they resolved to.
    """
    if not isinstance(name, str) or not name:
        return name
    return name if name.startswith("NT") else "NT" + name


def bare(name) -> str:
    """Canonical name with ``NT`` stripped - the library's own (v1.3) spelling."""
    canon = canonical(name)
    return canon[2:] if isinstance(canon, str) and canon.startswith("NT") else canon


def library_path() -> str:
    try:
        from ..capabilities import higgsas_library_path
        return higgsas_library_path() or ""
    except Exception:
        return ""


def available() -> bool:
    """True when the library file resolves OR a group is already in the session."""
    path = library_path()
    if path:
        import os
        if os.path.exists(path):
            return True
    try:
        import bpy
        return any(getattr(g, "name", "").startswith("NT")
                   for g in bpy.data.node_groups)
    except Exception:
        return False


def load(name: str):
    """Resolve (never duplicate) one Higgsas node group. Returns it or None.

    Session probe by canonical name -> session probe by bare name (adopts and renames
    it, which kills a `.001` twin at the spelling layer) -> ONE BATCHED library append.

    The batching is load-bearing. Appending groups one at a time re-imports their
    shared dependencies every time, and Blender leaves a `.001` behind:
    'Edge Bisect' and 'Curve Bisect' both depend on 'Line Plane Intersection', so two
    single loads produced 'Line Plane Intersection.001' (stepped proof:
    Saved/Audit/_diag_higgas_step.py). A single `libraries.load` pass shares one
    dependency map for the whole batch, so it cannot dup. First use warms the whole
    pipeline set at once; later misses warm only what is still missing.
    """
    import bpy
    if not isinstance(name, str) or not name:
        return None
    canon, bare_name = canonical(name), bare(name)
    ng = _session_get(canon, bare_name)
    if ng is not None:
        return ng
    _append_batch(_warm_names(name))
    return _session_get(canon, bare_name)


def _session_get(canon, bare_name=None):
    """Find a group by canonical name, adopting an unprefixed twin if that is all there is."""
    import bpy
    try:
        groups = bpy.data.node_groups
        ng = groups.get(canon)
        if ng is not None:
            return ng
        if bare_name:
            alt = groups.get(bare_name)
            if alt is not None:
                # Adopt it so a later NT lookup cannot append a second copy.
                try:
                    alt.name = canon
                except Exception:
                    pass
                return alt
    except Exception:
        return None
    return None


def _warm_names(extra=()):
    """Everything worth holding in the session, for ONE library pass.

    PIPELINE_GROUPS (what this lane intends to wire) plus the addon bridge's legacy
    HIGGSAS_ARCH_NODES set (what existing builders already call), plus anything the
    caller asked for right now - all in one batch so shared dependencies import once.
    """
    names = set(all_pipeline_names())
    try:
        from ..higgsas_bridge import HIGGSAS_ARCH_NODES
        names.update(HIGGSAS_ARCH_NODES)
    except Exception:
        pass
    if isinstance(extra, str):
        names.add(extra)
    else:
        names.update(extra or ())
    return sorted(names)


def _append_batch(names):
    """Append every still-missing group in a SINGLE library pass. Never raises.

    After the pass, each requested group is adopted to its canonical ``NT`` name so
    the next caller's session probe hits immediately. A group the library does not
    carry is simply absent - the caller's fallback path then runs, by design.
    """
    import os
    import bpy
    path = library_path()
    if not path or not os.path.exists(path):
        return
    want = []
    for name in names:
        canon, bare_name = canonical(name), bare(name)
        if _session_get(canon, bare_name) is None and bare_name:
            want.append((canon, bare_name))
    if not want:
        return
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            available = list(src.node_groups)
            wanted_bares = {b for _, b in want}
            dst.node_groups = [n for n in available if n in wanted_bares]
    except Exception:
        return
    for canon, bare_name in want:
        _session_get(canon, bare_name)



def node(tree, name, loc, fallback_type=None, color_role="ornament"):
    """Add a Higgsas group node, or a native fallback node. Returns node or None.

    The builder-facing replacement for the four private loaders: no `monolith`
    argument (builders do not have one) and the fallback is first-class.
    """
    ng = load(name)
    if ng is None:
        if fallback_type:
            return safe_node(tree, fallback_type, loc)
        return None
    try:
        n = tree.nodes.new("GeometryNodeGroup")
        n.node_tree = ng
        n.location = loc
        if color_role:
            try:
                color_node(n, color_role)
            except Exception:
                pass
        return n
    except Exception:
        if fallback_type:
            return safe_node(tree, fallback_type, loc)
        return None


def _resolve(value, prefer=None):
    """NODE -> its socket, socket -> itself (same idea as paris_common._sock)."""
    if hasattr(value, "outputs"):
        try:
            if prefer:
                s = value.outputs.get(prefer)
                if s is not None:
                    return s
            return value.outputs[0]
        except Exception:
            return None
    return value


def inp(n, name, value) -> bool:
    """Set a named group input. Returns True only when it actually took.

    Never raises: a socket that is not there is a reported False, not a silent pass,
    and not a crash - one bad dial must not kill an 800-node tree.
    """
    if n is None:
        return False
    try:
        s = n.inputs.get(name)
    except Exception:
        s = None
    if s is None:
        return False
    try:
        if hasattr(value, "outputs"):
            link_sockets(n.id_data, _resolve(value), s)
        elif hasattr(value, "bl_idname"):
            link_sockets(n.id_data, value, s)
        else:
            s.default_value = value
        return True
    except Exception:
        return False


def geometry_socket(n, out=False):
    """Best-matching geometry socket NAME on a group node, or None.

    Higgsas groups do not agree on naming, so probe semantic candidates first, then
    fall back to the first socket of a geometry type. Returns the NAME: `in` on a bpy
    collection raises, so callers probe with .get() (house rule).
    """
    if n is None:
        return None
    try:
        pool = n.outputs if out else n.inputs
    except Exception:
        return None
    wanted = ("Geometry", "Mesh", "Curve", "Curves", "Instances", "Points",
              "Result", "Output", "Input")
    for nm in wanted:
        try:
            if pool.get(nm) is not None:
                return nm
        except Exception:
            pass
    for s in pool:
        if getattr(s, "type", "") in ("GEOMETRY", "MESH", "CURVE", "INSTANCES"):
            return s.name
    try:
        return pool[0].name
    except Exception:
        return None


def source_out(value):
    """Resolve a stage source (node or socket) to its geometry output socket."""
    if value is None:
        return None
    if hasattr(value, "outputs"):
        return _resolve(value, geometry_socket(value, out=True))
    return value


def stage(tree, name, x, y, geometry_in=None, inputs=None, fallback_type=None,
          fallback_builder=None):
    """Add one pipeline stage, wiring geometry through it.

    Returns ``(node, used_fallback)`` - a tuple, never a bare truthy node, because
    "built something" and "used Higgsas" are different claims and only the second one
    may appear in a Higgsas-quality report.

    ``fallback_builder(tree, (x, y))`` wins over ``fallback_type`` when both are given:
    a native replacement usually takes more than one node.
    """
    n = node(tree, name, (x, y))
    used_fallback = n is None
    if used_fallback:
        if fallback_builder is not None:
            try:
                n = fallback_builder(tree, (x, y))
            except Exception:
                n = None
        if n is None and fallback_type:
            n = safe_node(tree, fallback_type, (x, y))
        if n is None:
            return None, True

    if geometry_in is not None:
        src = source_out(geometry_in)
        tgt = geometry_socket(n, out=False)
        if src is not None and tgt:
            try:
                link_sockets(tree, src, n.inputs[tgt])
            except Exception:
                pass

    for key, value in (inputs or {}).items():
        inp(n, key, value)
    return n, used_fallback


def stages(tree, specs, x, y, geometry_in=None, gap=320):
    """Run ``(name, inputs, fallback_type)`` specs, threading geometry through them.

    Returns ``(last_node, fallback_names)``. Geometry threads automatically - each
    stage's output feeds the next stage's geometry input - which is what makes a chain
    cheaper to author than the sum of its parts. Every stage that degraded to native is
    NAMED in the second return value, so a caller can surface it rather than claim a
    Higgsas path it never ran.
    """
    fallback_names = []
    current = geometry_in
    last = None
    for i, spec in enumerate(specs or []):
        if isinstance(spec, str):
            name, inputs, fallback_type = spec, {}, None
        else:
            parts = list(spec) + [None] * (3 - len(spec))
            name, inputs, fallback_type = parts[0], parts[1] or {}, parts[2]
        n, used = stage(tree, name, x + i * gap, y, geometry_in=current,
                        inputs=inputs, fallback_type=fallback_type)
        if n is None:
            fallback_names.append(name)
            continue
        if used:
            fallback_names.append(name)
        last = n
        current = n
    return last, fallback_names


def status() -> dict:
    """Probe report: library path, availability, and load state per pipeline group.

    Consumed by Tools/higgasas_verify.py so probe and runtime answer from ONE
    implementation - a probe that re-implements loading tests its own copy, not the
    code that ships.
    """
    import os
    path = library_path()
    report = {
        "library_path": path,
        "library_exists": bool(path) and os.path.exists(path),
        "available": available(),
        "requested": 0,
        "loaded": 0,
        "missing": 0,
        "groups": {},
    }
    for name in all_pipeline_names():
        ok = load(name) is not None
        report["groups"][name] = "loaded" if ok else "missing"
        report["requested"] += 1
        report["loaded" if ok else "missing"] += 1
    return report


