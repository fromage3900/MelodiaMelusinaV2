# -*- coding: utf-8 -*-
"""Melodia FX Audit — effective render visibility + indirect-linkage report.

Answers, per object in the scene:
  * Will it actually show up in a render of the active view layer?
    (object hide_render, collection hide_render chain, view-layer exclusion,
    object type, instance collections)
  * Why not, if not — one-line reasons.
  * Is it indirectly linked (drives / is referenced by another object via
    modifiers, constraints, drivers, parents, GN object inputs, FLIP fluid
    roles, instanced collections, GP frames)?
  * Is its animation a clean Nx24-frame loop (for 24fps loop shots)?

Two entry points:
  * N-panel addon: deploy/melodia_fx_audit_panel.py (View3D > Sidebar > Melodia FX)
  * Headless CLI: blender -b <stage.blend> -P Tools/fx_render_audit.py

Writes Saved/Audit/fx_render_audit_<stage>_<timestamp>.json + .md
(and mirrors to the C: workspace copy when reachable).

Read-only: never saves the stage, never changes visibility.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

import bpy

# Collections considered "FX" for focus columns. Everything is audited.
FX_NAME_TOKENS = ("FX_", "Melusina_", "FLIP", "Water", "Pond", "Nikki",
                  "Hair", "GP", "Bokeh", "Lights", "Cameras", "Studio",
                  "Set_", "Asset_", "RenderSubject", "Review_")

RENDERABLE_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT", "GPENCIL",
                    "GREASEPENCIL", "VOLUME", "CURVES", "POINTCLOUD"}
NON_RENDER_TYPES = {"EMPTY", "CAMERA", "LIGHT", "ARMATURE", "LATTICE",
                    "SPEAKER", "LIGHT_PROBE", "HAIR"}

_REF_MODIFIER_MAP = (
    ("BOOLEAN", "object"),
    ("ARRAY", "offset_object"),
    ("CURVE", "object"),
    ("LATTICE", "object"),
    ("SHRINKWRAP", "target"),
    ("MESH_SEQUENCE_CACHE", None),
)


# --------------------------------------------------------------------------
# Visibility model
# --------------------------------------------------------------------------

def _path_map(scene):
    """collection name -> list of ancestor names ending at scene root."""
    paths = {}

    def walk(col, ancestors):
        paths[col.name] = list(ancestors) + [col.name]
        for child in col.children:
            walk(child, list(ancestors) + [col.name])

    walk(scene.collection, [])
    return paths


def _viewlayer_exclusions(view_layer):
    """collection name -> True if excluded in this view layer (inherited)."""
    excluded = {}

    def walk(lc, parent_excluded):
        this = parent_excluded or bool(lc.exclude)
        excluded[lc.collection.name] = this
        for child in lc.children:
            walk(child, this)

    walk(view_layer.layer_collection, False)
    return excluded


def _collection_chain_status(col_name, paths, excluded):
    chain = paths.get(col_name, [col_name])
    hidden_by = [n for n in chain
                 if (bpy.data.collections.get(n) or None) and
                 bpy.data.collections[n].hide_render]
    excluded_by = [n for n in chain if excluded.get(n)]
    return {
        "chain": chain,
        "hidden_by_collection": hidden_by,
        "viewlayer_excluded_by": excluded_by,
    }


def _duplicate_collection_instances(scene):
    """collection data name -> number of times it appears in the scene tree.

    A collection linked in twice renders every object in it twice.
    """
    counts: dict[str, int] = {}

    def walk(col):
        counts[col.name] = counts.get(col.name, 0) + 1
        for child in col.children:
            walk(child)

    walk(scene.collection)
    return {name: n for name, n in counts.items() if n > 1}


def _object_roles(obj):
    """Static classification of what this object IS in the FX stack."""
    roles = []
    flip = None
    try:
        if getattr(obj, "flip_fluid", None) and obj.flip_fluid.is_active:
            flip = str(obj.flip_fluid.object_type).replace("TYPE_", "")
            roles.append(f"FLIP:{flip}")
    except Exception:
        pass
    if obj.instance_collection is not None:
        roles.append(f"INSTANCES:{obj.instance_collection.name}")
    if obj.instance_type in {"VERTS", "FACES", "EDGES"}:
        roles.append(f"DUPLI:{obj.instance_type}")
    if obj.type == "ARMATURE":
        roles.append("SKELETON")
    if obj.type == "CAMERA":
        roles.append("CAMERA")
    if obj.type == "LIGHT":
        roles.append("LIGHT")
    if obj.type == "EMPTY" and obj.parent:
        roles.append("ORGANIZER")
    if obj.type == "GPENCIL":
        frame_nums = sorted({f.frame_number
                             for l in obj.data.layers for f in l.frames})
        if len(frame_nums) <= 1:
            roles.append("GP_STATIC")
        else:
            roles.append(f"GP_ANIMATED:{len(frame_nums)}fr")
    return roles, flip


def _effective_render(obj, paths, excluded, linked_in_scene=True):
    """Returns (renders, reasons, via_collection)."""
    reasons = []
    if not linked_in_scene:
        reasons.append("NOT_LINKED_IN_SCENE")
    if obj.hide_render:
        reasons.append("OBJECT_HIDE_RENDER")
    if obj.type in NON_RENDER_TYPES:
        reasons.append(f"TYPE_NO_RENDER:{obj.type}")
    if obj.instance_collection is not None:
        reasons.append(f"INSTANCE_EMPTY:{obj.instance_collection.name}")

    via = []
    for col in obj.users_collection:
        status = _collection_chain_status(col.name, paths, excluded)
        if status["hidden_by_collection"]:
            reasons.append("COLL_HIDE_RENDER:" + ",".join(status["hidden_by_collection"]))
        if status["viewlayer_excluded_by"]:
            reasons.append("VL_EXCLUDE:" + ",".join(status["viewlayer_excluded_by"]))
        if (linked_in_scene and not status["hidden_by_collection"]
                and not status["viewlayer_excluded_by"]):
            via.append(col.name)

    if not obj.users_collection:
        reasons.append("NOT_IN_ANY_COLLECTION")

    renders = (
        linked_in_scene
        and not obj.hide_render
        and obj.type in RENDERABLE_TYPES
        and bool(via)
        and obj.instance_collection is None
    )
    return renders, sorted(set(reasons)), via


# --------------------------------------------------------------------------
# Indirect linkage
# --------------------------------------------------------------------------

def _collect_references():
    """obj.name -> list of human-readable "X references Y" strings."""
    referenced_by: dict[str, list[str]] = {}

    def ref(target_name, source_label):
        if not target_name or target_name == source_label:
            return
        referenced_by.setdefault(target_name, []).append(source_label)

    for obj in bpy.data.objects:
        source = f"{obj.name} ({obj.type})"
        for mod in obj.modifiers:
            mtype = mod.type
            if mtype == "NODES" and mod.node_group:
                # Light scan: native nodes with an .object/.collection property
                for node in mod.node_group.nodes:
                    try:
                        if getattr(node, "object", None):
                            ref(node.object.name, f"GN {mod.node_group.name}::ObjectInfo")
                        if getattr(node, "collection", None):
                            coll = node.collection
                            for member in coll.all_objects:
                                ref(member.name, f"GN {mod.node_group.name}::CollectionInfo({coll.name})")
                    except Exception:
                        pass
            else:
                for mod_type, attr in _REF_MODIFIER_MAP:
                    if mod.type == mod_type and attr:
                        try:
                            ref(getattr(mod, attr).name, f"modifier {mod.name} ({mod_type})")
                        except Exception:
                            pass
        if obj.type == "ARMATURE":
            for target in bpy.data.objects:
                for arm in target.modifiers:
                    if arm.type == "ARMATURE" and arm.object is obj:
                        ref(obj.name, f"deforms {target.name}")
        for con in obj.constraints:
            try:
                ref(con.target.name, f"constraint {con.name}")
            except Exception:
                pass
        if obj.animation_data:
            for drv in obj.animation_data.drivers:
                for var in drv.driver.variables:
                    for target in var.targets:
                        try:
                            ref(target.id.name, f"driver {drv.data_path}")
                        except Exception:
                            pass
        if obj.parent:
            ref(obj.parent.name, f"parent of {obj.name}")
        if obj.instance_collection:
            for member in obj.instance_collection.all_objects:
                ref(member.name, f"instanced via {obj.name}")
    return referenced_by


# --------------------------------------------------------------------------
# Loop check
# --------------------------------------------------------------------------

def _loop_info(obj):
    if not obj.animation_data:
        return None
    out = []
    if obj.animation_data.action:
        a = obj.animation_data.action
        duration = a.frame_range[1] - a.frame_range[0] + 1
        out.append({
            "action": a.name,
            "start": round(a.frame_range[0], 1),
            "end": round(a.frame_range[1], 1),
            "frames": round(duration, 1),
            "loop24": duration > 0 and abs(duration / 24 - round(duration / 24)) < 1e-6,
        })
    for track in obj.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.action:
                dur = strip.frame_end - strip.frame_start + 1
                out.append({
                    "nla": track.name,
                    "action": strip.action.name,
                    "start": round(strip.frame_start, 1),
                    "end": round(strip.frame_end, 1),
                    "frames": round(dur, 1),
                    "repeat": getattr(strip, "repeat", 1),
                    "loop24": dur > 0 and abs(dur / 24 - round(dur / 24)) < 1e-6,
                })
    return out or None


# --------------------------------------------------------------------------
# Audit
# --------------------------------------------------------------------------

def audit_scene(scene=None):
    scene = scene or bpy.context.scene
    view_layer = scene.view_layers[0]
    paths = _path_map(scene)
    excluded = _viewlayer_exclusions(view_layer)
    referenced_by = _collect_references()
    dup_collections = _duplicate_collection_instances(scene)

    scene_tree_names = set(paths.keys())
    rows = []
    for obj in bpy.data.objects:
        linked = any(c.name in scene_tree_names for c in obj.users_collection)
        renders, reasons, via = _effective_render(obj, paths, excluded,
                                                  linked_in_scene=linked)
        roles, flip = _object_roles(obj)
        loop = _loop_info(obj)
        refs = referenced_by.get(obj.name, [])
        row = {
            "name": obj.name,
            "type": obj.type,
            "collection": ", ".join(c.name for c in obj.users_collection) or "-",
            "linked_in_scene": linked,
            "focus_fx": any(tok in " ".join(c.name for c in obj.users_collection)
                            for tok in FX_NAME_TOKENS),
            "renders": bool(renders),
            "reasons": reasons,
            "via_collection": via,
            "roles": roles,
            "flip_role": flip,
            "hidden_viewport": obj.hide_viewport,
            "materials": [s.material.name for s in obj.material_slots if s.material],
            "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
            "referenced_by": refs,
            "references_count": len(refs),
            "animation": loop,
            "loop_friendly": bool(loop) and all(r["loop24"] for r in loop),
        }
        rows.append(row)

    rows.sort(key=lambda r: (r["collection"].lower(), r["name"].lower()))
    report = {
        "schema": "melodia.fx_render_audit.v1",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stage": bpy.data.filepath,
        "blender": bpy.app.version_string,
        "view_layer": view_layer.name,
        "engine": scene.render.engine,
        "frame_range": [scene.frame_start, scene.frame_end],
        "duplicate_collection_instances": dup_collections,
        "summary": {
            "total": len(rows),
            "renders": sum(1 for r in rows if r["renders"]),
            "not_rendering": sum(1 for r in rows if not r["renders"]),
            "fx_focus": sum(1 for r in rows if r["focus_fx"]),
            "linked_in_scene": sum(1 for r in rows if r["linked_in_scene"]),
            "not_linked": sum(1 for r in rows if not r["linked_in_scene"]),
            "indirect_only": sum(1 for r in rows
                                 if not r["renders"] and r["references_count"]),
            "hidden_in_viewport": sum(1 for r in rows if r["hidden_viewport"]),
            "loop_friendly": sum(1 for r in rows if r["loop_friendly"]),
            "dup_collection_instances": dup_collections,
        },
        "objects": rows,
    }
    return report


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def _out_dir():
    dirs = []
    if bpy.data.filepath:
        blend_dir = Path(bpy.data.filepath).resolve().parent
        dirs.append(blend_dir / "Saved" / "Audit")
    c_mirror = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit")
    if c_mirror.exists():
        dirs.append(c_mirror)
    return dirs


def _md(report):
    lines = []
    s = report["summary"]
    stage = report["stage"] or "<unsaved>"
    lines.append(f"# FX Render Audit — {Path(stage).name}")
    lines.append(f"* {report['generated_at']} · Blender {report['blender']} · "
                 f"view layer `{report['view_layer']}` · engine `{report['engine']}` · "
                 f"frames {report['frame_range'][0]}–{report['frame_range'][1]}`")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| Total objects | {s['total']} |")
    lines.append(f"| **Renders** | **{s['renders']}** |")
    lines.append(f"| Not rendering | {s['not_rendering']} |")
    lines.append(f"| FX-focus objects | {s['fx_focus']} |")
    lines.append(f"| Indirect-only (referenced, not rendered) | {s['indirect_only']} |")
    lines.append(f"| Hidden in viewport | {s['hidden_in_viewport']} |")
    lines.append(f"| Loop-friendly (N×24) | {s['loop_friendly']} |")
    if s.get("dup_collection_instances"):
        lines.append("")
        lines.append("## ⚠ Duplicate collection instances (renders twice)")
        lines.append("")
        lines.append("| Collection | Times linked in scene |")
        lines.append("|---|---|")
        for name, n in sorted(s["dup_collection_instances"].items()):
            lines.append(f"| {name} | {n} |")
    lines.append("")

    def row_line(r):
        why = ", ".join(r["reasons"]) if r["reasons"] else ("✅" if r["renders"] else "?")
        anim = ""
        if r["animation"]:
            anim = "; ".join(f"{a['action']}@{a['start']}-{a['end']}"
                             + ("" if a["loop24"] else " !not-24f")
                             for a in r["animation"][:2])
        refs = f"{r['references_count']} ref" if r["references_count"] else ""
        roles = ", ".join(r["roles"]) if r["roles"] else ""
        return (f"| `{r['name']}` | {r['type']} | {r['collection']} | "
                f"{'YES' if r['renders'] else 'NO'} | {why} | {roles} {refs} | {anim} |")

    lines.append("## All objects")
    lines.append("")
    lines.append("| Object | Type | Collection | Renders? | Why | Roles/Refs | Animation |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in report["objects"]:
        lines.append(row_line(r))
    lines.append("")

    indirect = [r for r in report["objects"] if not r["renders"] and r["references_count"]]
    if indirect:
        lines.append("## Indirectly linked — NOT rendered, but referenced")
        lines.append("")
        for r in indirect:
            lines.append(f"- **{r['name']}** ({r['type']}): "
                         + "; ".join(r["referenced_by"][:6]))
        lines.append("")
    return "\n".join(lines) + "\n"


def run_audit(print_summary=True):
    """Run the audit, write .json + .md, return (report, files)."""
    report = audit_scene()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stage_base = Path(bpy.data.filepath or "unsaved").stem
    files = []
    for out_dir in _out_dir():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            base = out_dir / f"fx_render_audit_{stage_base}_{stamp}"
            (base.with_suffix(".json")).write_text(
                json.dumps(report, indent=2), encoding="utf-8")
            (base.with_suffix(".md")).write_text(_md(report), encoding="utf-8")
            files.append(str(base.with_suffix(".md")))
        except OSError:
            continue
    if print_summary:
        s = report["summary"]
        print(f"[melodia-fx] audit {s['renders']}/{s['total']} render | "
              f"fx={s['fx_focus']} indirect={s['indirect_only']} "
              f"hidden_vp={s['hidden_in_viewport']} loop24={s['loop_friendly']}")
        for f in files:
            print(f"[melodia-fx] wrote {f}")
    return report, files


# --------------------------------------------------------------------------
# N-panel UI
# --------------------------------------------------------------------------

class MELODIA_FX_OT_run_audit(bpy.types.Operator):
    """Run the FX render-visibility audit and write report files."""
    bl_idname = "melodia_fx.run_audit"
    bl_label = "Run FX Render Audit"
    bl_options = {"REGISTER"}

    def execute(self, context):
        report, files = run_audit(print_summary=True)
        context.scene.melodia_fx_last_summary = _summary_text(report)
        self.report({"INFO"}, f"Audit wrote {len(files)} report file(s); "
                              f"{report['summary']['renders']}/{report['summary']['total']} objects render")
        return {"FINISHED"}


class MELODIA_FX_PT_panel(bpy.types.Panel):
    bl_label = "Melodia FX Audit"
    bl_idname = "MELODIA_FX_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia FX"

    def draw(self, context):
        layout = self.layout
        layout.operator("melodia_fx.run_audit", icon="RESTRICT_RENDER_OFF")
        summary = getattr(context.scene, "melodia_fx_last_summary", "")
        if summary:
            box = layout.box()
            for line in summary.splitlines():
                box.label(text=line)
        if bpy.data.filepath:
            box = layout.box()
            box.label(text=f"Stage: {Path(bpy.data.filepath).name}", icon="FILE_BLEND")
        layout.separator()
        layout.label(text="Renders vs indirect linkage per FX object,",
                     icon="INFO")
        layout.label(text="written to Saved/Audit/fx_render_audit_*.md")
        layout.operator(
            "wm.path_open",
            text="Open Saved/Audit folder",
            icon="FILE_FOLDER",
        ).filepath = str(Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit"))


def _summary_text(report):
    s = report["summary"]
    stage = Path(report["stage"] or "<unsaved>").name
    lines = [
        f"Stage: {stage}",
        f"Renders: {s['renders']}/{s['total']}   FX-focus: {s['fx_focus']}",
        f"Not rendering: {s['not_rendering']}   Indirect-only: {s['indirect_only']}",
        f"Hidden in viewport: {s['hidden_in_viewport']}   Loop-friendly (24f): {s['loop_friendly']}",
    ]
    return "\n".join(lines)


classes = (MELODIA_FX_OT_run_audit, MELODIA_FX_PT_panel)


def register():
    bpy.types.Scene.melodia_fx_last_summary = bpy.props.StringProperty(
        name="Last FX Audit Summary", default="")
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.melodia_fx_last_summary


if __name__ == "__main__":
    register()
