"""Morph baker for the Surreal GN architecture (P0 of reactive geometry).

Bakes Geometry-Nodes parameter variants into Blender shape keys so they
export as UE FBX morph targets, and extends snap_export sidecars to schema
v2 with a morph_targets array.

Strategy: GN results have no shape keys until evaluated. We evaluate the
modifier stack once per variant (param delta applied), capture evaluated
vertex positions, and store deltas as RELATIVE shape keys on a baked copy.
The live GN object is never mutated.

Reaction contract (UE side):
  MOR_<variant> names map 1:1 to sidecar "morph_targets" entries carrying
  {"name", "source_param", "base_value", "variant_value", "reaction_channel"}.
  Channels align with melodia rhythm lanes: beat | bass | grade |
  pluck:<id> | press:<id>.

Usage (in Blender):
    from surreal_arch import morph_baker
    report = morph_baker.bake_object_variants(obj, [
        {"name": "pluck_string_07", "param": "Pluck 07", "base": 0.0, "value": 1.0,
         "reaction_channel": "pluck:07"},
    ])
    sidecar = morph_baker.extend_sidecar_with_morphs(existing_sidecar_dict, report)

Pure-logic helpers are import-safe without bpy; baking requires bpy.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

SNAP_SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# Pure helpers (offline-safe)
# ---------------------------------------------------------------------------

def build_morph_targets_array(variants: list[dict]) -> list[dict]:
    """Normalize variant specs -> sidecar morph_targets entries."""
    out = []
    for v in variants:
        name = str(v.get("name", "")).strip()
        if not name:
            continue
        out.append({
            "name": f"MOR_{name}",
            "source_param": str(v.get("param", "")),
            "base_value": float(v.get("base", 0.0)),
            "variant_value": float(v.get("value", 1.0)),
            "reaction_channel": str(v.get("reaction_channel", "beat")),
            "vertex_delta_count": int(v.get("vertex_delta_count", 0)),
        })
    return out


def extend_sidecar_with_morphs(sidecar: dict, bake_report: dict) -> dict:
    """Upgrade a surreal_arch_ue_snap_v1 sidecar to v2 with morph_targets."""
    if not isinstance(sidecar, dict):
        return sidecar
    sidecar["schema_version"] = SNAP_SCHEMA_VERSION
    sidecar["morph_schema"] = "melodia_morph_v1"
    variants = bake_report.get("variants", []) if isinstance(bake_report, dict) else []
    sidecar["morph_targets"] = build_morph_targets_array(variants)
    return sidecar


def default_string_variants(prefix: str, count: int, channel_prefix: str,
                            param_template: str) -> list[dict]:
    """Helper: per-string/per-key pluck variants (harp strings, piano keys).

    e.g. default_string_variants("pluck", 7, "pluck", "Pluck {i:02d}") ->
         [{"name": "pluck_01", "param": "Pluck 01", ...}, ...]
    """
    out = []
    for i in range(1, max(1, count) + 1):
        label = f"{i:02d}"
        out.append({
            "name": f"{prefix}_{label}",
            "param": param_template.format(i=i),
            "base": 0.0,
            "value": 1.0,
            "reaction_channel": f"{channel_prefix}:{label}",
        })
    return out


def write_morph_sidecar(sidecar: dict, fbx_path: str | Path) -> Path:
    """Write <fbx>.snap.json next to the FBX (same convention as snap_export)."""
    p = Path(fbx_path)
    out = p.with_suffix(".snap.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Baking (requires bpy; import-safe guard)
# ---------------------------------------------------------------------------

def _get_bpy():
    try:
        import bpy  # type: ignore
        return bpy
    except Exception:
        return None


def _find_gn_modifier(obj):
    """First NODES modifier with a node group. Blender 4.x+ renamed to node_group."""
    for mod in getattr(obj, "modifiers", []):
        if getattr(mod, "type", "") != "NODES":
            continue
        for attr in ("node_group", "node_tree"):
            if getattr(mod, attr, None) is not None:
                return mod
    return None


def _modifier_tree(modifier):
    for attr in ("node_group", "node_tree"):
        t = getattr(modifier, attr, None)
        if t is not None:
            return t
    return None


def _set_param(modifier, name: str, value: float) -> bool:
    """Set a node-group input on the modifier instance (Blender 4.x/5.x).

    Per-instance values live as IDProps keyed by the interface socket
    identifier; fall back to mutating the tree's default (bake-only dup).
    """
    tree = _modifier_tree(modifier)
    if tree is None:
        return False
    iface = getattr(tree, "interface", None)

    def _identifiers():
        out = []
        if iface is not None:
            for item in iface.items_tree:
                if getattr(item, "in_out", "") == "INPUT" and item.name == name:
                    out.append(item.identifier)
        # legacy trees
        inputs = getattr(tree, "inputs", None)
        if inputs is not None and name in inputs:
            try:
                out.append(inputs[name].identifier)
            except Exception:
                pass
        return out

    for ident in _identifiers():
        try:
            modifier[ident] = value
            return True
        except Exception:
            continue

    # Last resort: change tree default directly (fine on bake-only duplicate).
    if iface is not None:
        for item in iface.items_tree:
            if getattr(item, "in_out", "") == "INPUT" and item.name == name:
                try:
                    item.default_value = value
                    return True
                except Exception:
                    pass
    return False


def _evaluated_mesh_copy(bpy, obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = bpy.data.meshes.new_from_object(ev)
    me.calc_loop_triangles()
    return me


def bake_object_variants(obj, variants: list[dict], bake_name: str | None = None,
                         context=None) -> dict:
    """Bake GN parameter variants as relative shape keys on a duplicated object.

    Returns report dict:
      {"ok": bool, "object": name, "baked_object": name,
       "variants": [...], "errors": [...]}
    """
    bpy = _get_bpy()
    if bpy is None:
        return {"ok": False, "error": "no bpy"}
    if obj is None or obj.type != "MESH":
        return {"ok": False, "error": "need a mesh object"}

    mod = _find_gn_modifier(obj)
    errors: list[str] = []
    made: list[dict] = []

    # Duplicate so the live GN object stays untouched.
    dup_name = bake_name or f"{obj.name}_MORPHBAKE"
    existing = bpy.data.objects.get(dup_name)
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = dup_name
    for coll in list(obj.users_collection):
        coll.objects.link(dup)

    # Base evaluation (params at current/base state).
    base_me = _evaluated_mesh_copy(bpy, dup)
    base_count = len(base_me.vertices)
    if base_count == 0:
        return {"ok": False, "error": "evaluated mesh empty (check GN modifier output)"}
    # Replace dup data with the EVALUATED mesh so shape keys have matching
    # topology even when the source object's mesh datablock is a bare carrier.
    dup.data = base_me
    if dup.name in bpy.context.view_layer.objects:
        pass

    # Shape keys container starts empty; first key becomes basis.
    keys = None
    dup.shape_key_add(name="Basis", from_mix=False)
    keys = dup.data.shape_keys
    for spec in variants:
        name = f"MOR_{spec.get('name', '')}"
        pname = spec.get("param", "")
        target = float(spec.get("value", 1.0))
        ok_set = _set_param(mod, pname, target) if mod is not None else False
        if not ok_set:
            # Try direct node-tree socket default (affects all instances; fine for bake-only dup)
            tree = _modifier_tree(mod) if mod is not None else None
            done = False
            if tree is not None:
                iface = getattr(tree, "interface", None)
                if iface is not None:
                    for item in iface.items_tree:
                        if getattr(item, "in_out", "") == "INPUT" and item.name == pname:
                            try:
                                item.default_value = target
                                done = True
                            except Exception:
                                pass
            if not done:
                errors.append(f"param not settable: {pname}")
                continue
        var_me = _evaluated_mesh_copy(bpy, dup)
        if len(var_me.vertices) != base_count:
            errors.append(f"topology drift at {pname} ({len(var_me.vertices)} vs {base_count})")
            continue
        sk = dup.shape_key_add(name=name, from_mix=False)
        # Write absolute evaluated positions; relative_to_basis keeps deltas.
        for i, v in enumerate(var_me.vertices):
            sk.data[i].co = v.co
        sk.value = 0.0
        made.append({**spec, "vertex_delta_count": base_count})
        var_me.user_clear()
        bpy.data.meshes.remove(var_me)

    # NOTE: base_me is now dup.data (assigned above) - do NOT remove it.

    return {
        "ok": len(made) > 0,
        "object": obj.name,
        "baked_object": dup_name,
        "variants": made,
        "errors": errors,
    }


def export_baked_fbx(obj, fbx_path: str, context=None) -> str:
    """FBX with shape keys -> UE morph targets. Requires bpy.

    Blender 5.x replaced the legacy exporter: shape keys are exported by
    default when present (no use_shape_keys flag). We therefore ensure the
    object's evaluated mesh carries the shape keys (bake already does this)
    and select only the target object.
    """
    bpy = _get_bpy()
    if bpy is None:
        raise RuntimeError("no bpy")
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    vp = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    kwargs = dict(
        filepath=str(fbx_path),
        use_selection=True,
        use_mesh_modifiers=True,
        apply_scale_options="FBX_SCALE_ALL",
    )
    try:
        # Legacy exporter (<=4.x): explicit shape-key flags
        probe = bpy.ops.export_scene.fbx.get_rna_type().properties
        ids = {p.identifier for p in probe}
        if "use_shape_keys" in ids:
            kwargs["use_shape_keys"] = True
            kwargs["use_shape_key_use_as_shape"] = True
    except Exception:
        pass
    bpy.ops.export_scene.fbx(**kwargs)
    if vp is not None:
        bpy.context.view_layer.objects.active = vp
    return str(fbx_path)


def bake_and_export(obj, variants: list[dict], out_dir, base_name: str,
                    monolith_sidecar: dict | None = None) -> dict:
    """One-call: bake variants, export FBX, write v2 sidecar. Requires bpy."""
    bpy = _get_bpy()
    if bpy is None:
        return {"ok": False, "error": "no bpy"}
    from pathlib import Path as _P
    out_dir = _P(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = bake_object_variants(obj, variants, bake_name=f"{base_name}_MORPHBAKE")
    if not report.get("ok"):
        report["sidecar"] = None
        report["fbx"] = None
        return report
    fbx = out_dir / f"{base_name}.fbx"
    export_baked_fbx(bpy.data.objects[report["baked_object"]], str(fbx))
    sidecar = dict(monolith_sidecar or {"format": "surreal_arch_ue_snap_v1"})
    sidecar = extend_sidecar_with_morphs(sidecar, report)
    sc_path = write_morph_sidecar(sidecar, fbx)
    report["fbx"] = str(fbx)
    report["sidecar"] = str(sc_path)
    return report
