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


def _run_sync_reload():
    """Hot-reload overhaul modules on the main thread after the operator returns.

    Must not run inside SURREAL_ARCH_OT_sync_reload.execute: importlib.reload of
    this module invalidates the live operator RNA and crashes Blender 5.2
    (EXCEPTION_ACCESS_VIOLATION in RNA_property_collection_lookup_string_index).
    """
    import importlib
    import sys

    try:
        import surreal_architecture_gen as mono
    except Exception as exc:
        print(f"[Melodia Studio] Sync & Reload: monolith missing: {exc}")
        return None

    try:
        from surreal_arch import integration
        integration.unregister_overhaul()
    except Exception:
        pass

    prefixes = (
        "surreal_arch",
        "surreal_greybox",
        "surreal_world",
        "surreal_os",
    )
    # Skip this module — reloading it while this timer runs is still unsafe.
    skip = {"surreal_arch.genome_carousel"}
    to_reload = [
        name
        for name in list(sys.modules)
        if name not in skip
        and (
            name == "surreal_arch"
            or name.startswith("surreal_arch.")
            or any(name == p or name.startswith(p + ".") for p in prefixes[1:])
        )
    ]
    for name in sorted(to_reload, key=lambda n: n.count("."), reverse=True):
        mod = sys.modules.get(name)
        if mod is None:
            continue
        try:
            importlib.reload(mod)
        except Exception as exc:
            print(f"[Melodia Studio] reload skip {name}: {exc}")

    try:
        from surreal_arch import integration
        integration.register_overhaul(mono)
        print("[Melodia Studio] reloaded")
    except Exception as exc:
        print(f"[Melodia Studio] Sync & Reload failed: {exc}")
    return None


class SURREAL_ARCH_OT_sync_reload(Operator):
    """Reload surreal_arch overhaul modules and re-patch the monolith."""

    bl_idname = "surreal_arch.sync_reload"
    bl_label = "Sync & Reload"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.app.timers.register(_run_sync_reload, first_interval=0.05)
        self.report({"INFO"}, "Melodia Studio reload queued")
        return {"FINISHED"}


class SURREAL_ARCH_OT_studio_health(Operator):
    """Print Studio health one-liner (builder counts) to the Info log."""

    bl_idname = "surreal_arch.studio_health"
    bl_label = "Studio Health"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from .melodia_gn.core import (
                GROUP_BUILDERS,
                GROUP_METADATA,
                CATEGORY_META,
                TREE_TYPES,
                TREE_CATEGORIES,
                _rebuild_derived_data,
            )
            from .melodia_gn.presets import audit_presets, builders_with_presets

            _rebuild_derived_data()
            n_build = len(GROUP_BUILDERS)
            n_meta = len(GROUP_METADATA)
            n_trees = len(TREE_TYPES)
            n_cat = len(CATEGORY_META)
            section_counts = {
                cid: len(info.get("trees") or [])
                for cid, info in TREE_CATEGORIES.items()
            }
            n_active_sections = sum(1 for n in section_counts.values() if n > 0)
            n_section_trees = sum(section_counts.values())
            n_presets = len(builders_with_presets())
            audit = audit_presets()
            missing = audit.get("missing_builders") or audit.get("orphans") or []
            msg = (
                f"GN builders={n_build} menu={n_trees} "
                f"sections={n_active_sections}/{n_cat} section_trees={n_section_trees} "
                f"preset_builders={n_presets} preset_gaps={len(missing)}"
            )
            print(f"[Melodia Studio Health] {msg}")
            print(f"[Melodia Studio Health] sections: {section_counts}")
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
