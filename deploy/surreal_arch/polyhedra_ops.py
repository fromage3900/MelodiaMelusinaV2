"""Polyhedra spawn operators — registry-backed panel + spawn_polyhedron."""
from __future__ import annotations

import bpy

from .polyhedra import GROUP_LABELS, POLYHEDRA_REGISTRY, spawn_polyhedron


class SURREAL_ARCH_OT_spawn_polyhedron(bpy.types.Operator):
    bl_idname = "surreal_arch.spawn_polyhedron"
    bl_label = "Spawn Polyhedron"
    bl_options = {"REGISTER", "UNDO"}

    kind: bpy.props.EnumProperty(
        items=[(k, f"{v['emoji']} {v['label']}", v["group"]) for k, v in POLYHEDRA_REGISTRY.items()],
        name="Kind",
    )

    def execute(self, context):
        entry = POLYHEDRA_REGISTRY[self.kind]
        obj = spawn_polyhedron(context, self.kind)
        self.report({"INFO"}, f"Spawned {entry['label']}: {obj.name}")
        return {"FINISHED"}


def patch_kepler_panel(monolith):
    """Redraw Kepler panel from POLYHEDRA_REGISTRY; delegate legacy ops to package."""

    def _wrap_kepler(kind: str, obj_name: str):
        def _execute(self, context):
            obj = spawn_polyhedron(context, kind, obj_name)
            self.report({"INFO"}, f"Spawned {obj.name}")
            return {"FINISHED"}
        return _execute

    monolith.SURREAL_ARCH_OT_kepler_ssdc.execute = _wrap_kepler("SSDC", "SmallStellatedDodec")
    monolith.SURREAL_ARCH_OT_kepler_gd.execute = _wrap_kepler("GD", "GreatDodec")
    monolith.SURREAL_ARCH_OT_kepler_gsdc.execute = _wrap_kepler("GSDC", "GreatStellatedDodec")
    monolith.SURREAL_ARCH_OT_kepler_gi.execute = _wrap_kepler("GI", "GreatIcosahedron")

    def _draw(self, context):
        layout = self.layout
        layout.label(text="Polyhedra library (Kepler + Platonic + more):", icon="MESH_ICOSPHERE")
        by_group = {}
        for key, meta in POLYHEDRA_REGISTRY.items():
            by_group.setdefault(meta["group"], []).append((key, meta))
        op_map = {"SSDC": "kepler_ssdc", "GD": "kepler_gd", "GSDC": "kepler_gsdc", "GI": "kepler_gi"}
        for group in ("kepler", "platonic", "archimedean", "compound"):
            items = by_group.get(group)
            if not items:
                continue
            box = layout.box()
            box.label(text=GROUP_LABELS.get(group, group.title()))
            col = box.column(align=True)
            col.scale_y = 1.15
            for key, meta in items:
                if key in op_map:
                    col.operator(f"surreal_arch.{op_map[key]}", text=f"{meta['emoji']} {meta['label']}")
                else:
                    op = col.operator("surreal_arch.spawn_polyhedron", text=f"{meta['emoji']} {meta['label']}")
                    op.kind = key
        layout.label(text="Scale follows active object's base_radius.", icon="INFO")

    monolith.SURREAL_ARCH_PT_kepler.bl_label = "Polyhedra Library"
    monolith.SURREAL_ARCH_PT_kepler.draw = _draw


def register_polyhedra_operators(monolith):
    patch_kepler_panel(monolith)
    registered = []
    try:
        bpy.utils.register_class(SURREAL_ARCH_OT_spawn_polyhedron)
        registered.append(SURREAL_ARCH_OT_spawn_polyhedron)
    except RuntimeError:
        pass
    return registered
