"""Melodia Studio N-panel hub — genome carousel parent for nested Studio panels.

Lean replacement for the missing Gate3 carousel: brand header + CTA row so
GN Stack, Stage Studio, bridges, and portrait can nest under a real parent.
"""

from __future__ import annotations

import bpy
from bpy.types import Panel, Operator

from .branding import N_PANEL_CATEGORY, PRODUCT_NAME, PRODUCT_SUBTITLE, product_label


class SURREAL_ARCH_PT_genome_carousel(Panel):
    """Top-level Melodia Studio hub in the 3D View N-panel."""

    bl_label = PRODUCT_NAME
    bl_idname = "SURREAL_ARCH_PT_genome_carousel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon="WORLD_DATA")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text=product_label())
        col.label(text=PRODUCT_SUBTITLE, icon="BLANK1")

        row = layout.row(align=True)
        row.scale_y = 1.2
        if hasattr(bpy.types, "SURREAL_ARCH_OT_generate") or hasattr(
            bpy.ops.surreal_arch, "generate"
        ):
            try:
                row.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")
            except Exception:
                row.label(text="Generate", icon="SHADERFX")
        if hasattr(bpy.types, "SURREAL_ARCH_OT_set_stage_visibility_preset"):
            op = row.operator(
                "surreal_arch.set_stage_visibility_preset",
                text="Starlight",
                icon="LIGHT_SUN",
            )
            op.preset = "starlight_on"
        if hasattr(bpy.types, "SURREAL_ARCH_OT_solo_object"):
            row.operator("surreal_arch.solo_object", text="Solo", icon="SOLO_ON")

        row2 = layout.row(align=True)
        row2.operator(
            "surreal_arch.sync_reload",
            text="Sync & Reload",
            icon="FILE_REFRESH",
        )
        row2.operator(
            "surreal_arch.studio_health",
            text="Studio Health",
            icon="CHECKMARK",
        )


class SURREAL_ARCH_OT_sync_reload(Operator):
    """Reload surreal_arch overhaul modules and re-patch the monolith."""

    bl_idname = "surreal_arch.sync_reload"
    bl_label = "Sync & Reload"
    bl_options = {"REGISTER"}

    def execute(self, context):
        import importlib
        import sys

        try:
            import surreal_architecture_gen as mono
        except Exception as exc:
            self.report({"ERROR"}, f"Monolith not loaded: {exc}")
            return {"CANCELLED"}

        try:
            from . import integration
            integration.unregister_overhaul()
        except Exception:
            pass

        # Reload key overhaul packages so disk edits appear without restart.
        prefixes = (
            "surreal_arch",
            "surreal_greybox",
            "surreal_world",
            "surreal_os",
        )
        to_reload = [
            name
            for name in list(sys.modules)
            if name == "surreal_arch"
            or name.startswith("surreal_arch.")
            or any(name == p or name.startswith(p + ".") for p in prefixes[1:])
        ]
        # Reload leaves first (deepest) then parents — reverse alpha is a decent heuristic.
        for name in sorted(to_reload, key=lambda n: n.count("."), reverse=True):
            mod = sys.modules.get(name)
            if mod is None:
                continue
            try:
                importlib.reload(mod)
            except Exception:
                pass

        try:
            from . import integration
            integration.register_overhaul(mono)
            self.report({"INFO"}, "Melodia Studio reloaded")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Reload failed: {exc}")
            return {"CANCELLED"}


class SURREAL_ARCH_OT_studio_health(Operator):
    """Print Studio health one-liner (builder counts) to the Info log."""

    bl_idname = "surreal_arch.studio_health"
    bl_label = "Studio Health"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from .melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA, CATEGORY_META
            from .melodia_gn.presets import audit_presets, builders_with_presets

            n_build = len(GROUP_BUILDERS)
            n_meta = len(GROUP_METADATA)
            n_cat = len(CATEGORY_META)
            n_presets = len(builders_with_presets())
            audit = audit_presets()
            missing = audit.get("missing_builders") or audit.get("orphans") or []
            msg = (
                f"GN builders={n_build} meta={n_meta} cats={n_cat} "
                f"preset_builders={n_presets} preset_gaps={len(missing)}"
            )
            print(f"[Melodia Studio Health] {msg}")
            if missing:
                print(f"[Melodia Studio Health] preset gaps: {list(missing)[:12]}")
            self.report({"INFO"}, msg)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Health check failed: {exc}")
            return {"CANCELLED"}


CLASSES = (
    SURREAL_ARCH_PT_genome_carousel,
    SURREAL_ARCH_OT_sync_reload,
    SURREAL_ARCH_OT_studio_health,
)
