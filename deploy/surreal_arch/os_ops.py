"""Style Genome operators — apply genome, spawn genome graph/plan."""

from __future__ import annotations

import bpy


def _os_genome():
    import sys
    import os

    deploy = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if deploy not in sys.path:
        sys.path.insert(0, deploy)
    from surreal_os import genome as os_genome

    return os_genome


def register_os_operators(monolith):
    classes = []

    class SURREAL_ARCH_OT_apply_style_genome(bpy.types.Operator):
        bl_idname = "surreal_arch.apply_style_genome"
        bl_label = "Apply Style Genome"
        bl_description = "Load surreal_os genome floats and prop defaults onto active object"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")

        def execute(self, context):
            obj = context.active_object
            props = obj.surreal_arch_props
            gid = getattr(props, "style_genome_id", "") or "zen_shrine_v1"
            try:
                genome = _os_genome().apply_genome(props, gid, monolith=monolith)
            except Exception as err:
                self.report({"ERROR"}, str(err))
                return {"CANCELLED"}
            self.report({"INFO"}, f"Applied genome {genome.get('id', gid)}")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_select_style_genome(bpy.types.Operator):
        bl_idname = "surreal_arch.select_style_genome"
        bl_label = "Select Style Genome"
        bl_description = "Set and apply a Style Genome from the OS catalog"
        bl_options = {"REGISTER", "UNDO"}

        genome_id: bpy.props.StringProperty(name="Genome ID", default="")

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")

        def execute(self, context):
            obj = context.active_object
            props = obj.surreal_arch_props
            gid = self.genome_id or "zen_shrine_v1"
            props.style_genome_id = gid
            try:
                genome = _os_genome().apply_genome(props, gid, monolith=monolith)
            except Exception as err:
                self.report({"ERROR"}, str(err))
                return {"CANCELLED"}
            self.report({"INFO"}, f"Selected genome {genome.get('id', gid)}")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_spawn_genome_graph(bpy.types.Operator):
        bl_idname = "surreal_arch.spawn_genome_graph"
        bl_label = "Spawn Genome Graph"
        bl_description = "Apply active genome then spawn its default_graph module chain"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            return context.active_object is not None

        def execute(self, context):
            from .greybox_graph import GRAPH_REGISTRY, spawn_graph, resolve_graph_spacing

            obj = context.active_object
            gid = "zen_shrine_v1"
            if obj and hasattr(obj, "surreal_arch_props"):
                gid = getattr(obj.surreal_arch_props, "style_genome_id", "") or gid
                try:
                    _os_genome().apply_genome(obj.surreal_arch_props, gid, monolith=monolith)
                except Exception as err:
                    self.report({"WARNING"}, f"Genome apply: {err}")
            genome = monolith._active_style_genome
            if not genome:
                try:
                    genome = _os_genome().load_genome(gid)
                    monolith._active_style_genome = genome
                except Exception as err:
                    self.report({"ERROR"}, str(err))
                    return {"CANCELLED"}
            graph_id = genome.get("default_graph", "ZEN_SHRINE_AXIS")
            meta = GRAPH_REGISTRY.get(graph_id)
            if not meta:
                self.report({"ERROR"}, f"Graph {graph_id} not in GRAPH_REGISTRY")
                return {"CANCELLED"}
            spacing = resolve_graph_spacing(context)
            objs = spawn_graph(
                context, monolith, meta["spec"],
                spacing=spacing, graph_id=graph_id,
            )
            self.report({"INFO"}, f"Spawned {len(objs)} modules ({graph_id})")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_spawn_zen_shrine_plan(bpy.types.Operator):
        bl_idname = "surreal_arch.spawn_zen_shrine_plan"
        bl_label = "Spawn Zen Shrine Plan"
        bl_description = "Apply genome and spawn a ZEN_SHRINE compose plan mesh"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            obj = context.active_object
            gid = "zen_shrine_v1"
            if obj and hasattr(obj, "surreal_arch_props"):
                gid = getattr(obj.surreal_arch_props, "style_genome_id", "") or gid
                try:
                    _os_genome().apply_genome(obj.surreal_arch_props, gid, monolith=monolith)
                except Exception:
                    pass
            try:
                bpy.ops.surreal_arch.spawn_castle_plan()
            except Exception:
                try:
                    bpy.ops.surreal_arch.spawn_plan()
                except Exception as err:
                    self.report({"ERROR"}, f"Plan spawn failed: {err}")
                    return {"CANCELLED"}
            self.report({"INFO"}, "Zen shrine plan spawned (compose with ZEN_SHRINE)")
            return {"FINISHED"}

    classes.extend([
        SURREAL_ARCH_OT_apply_style_genome,
        SURREAL_ARCH_OT_select_style_genome,
        SURREAL_ARCH_OT_spawn_genome_graph,
        SURREAL_ARCH_OT_spawn_zen_shrine_plan,
    ])
    return classes
