"""Generate arch_type EnumProperty items from ARCH_CATALOG (dev stub export)."""

from __future__ import annotations

import bpy

from .catalog import build_catalog, search_index


def generate_enum_items(monolith):
    """Return bpy-compatible enum tuples from catalog metadata."""
    catalog = build_catalog(monolith)
    seen = set()
    items = []
    for ent in search_index(monolith):
        at_id = ent.get("id", "")
        if not at_id or at_id.startswith("_") or at_id in seen:
            continue
        if at_id not in catalog and ent.get("category") == "Research Preset":
            continue
        seen.add(at_id)
        label = ent.get("label", at_id)
        desc = ent.get("description") or ent.get("category", "")
        if ent.get("builder_attr"):
            desc = f"{desc} [builder={ent['builder_attr']}]".strip()
        items.append((at_id, label, desc))
    items.sort(key=lambda row: row[0])
    return items


def format_enum_stub(monolith):
    """Format a Python snippet mirroring arch_type EnumProperty items."""
    lines = [
        "# Auto-generated from ARCH_CATALOG — do not hand-edit; re-export via Level Design panel",
        "CATALOG_ARCH_TYPE_ITEMS = [",
    ]
    for at_id, label, desc in generate_enum_items(monolith):
        safe_label = label.replace('"', '\\"')
        safe_desc = (desc or "").replace('"', '\\"')
        lines.append(f'    ("{at_id}", "{safe_label}", "{safe_desc}"),')
    lines.append("]")
    return "\n".join(lines)


def sync_catalog_enum_cache(monolith):
    items = generate_enum_items(monolith)
    monolith._CATALOG_ENUM_ITEMS = items
    return len(items)


class SURREAL_ARCH_OT_export_catalog_enum(bpy.types.Operator):
    bl_idname = "surreal_arch.export_catalog_enum"
    bl_label = "Export Catalog Enum Stub"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        import surreal_architecture_gen as monolith
        path = bpy.path.abspath(self.filepath or "//catalog_arch_type_items.py")
        text = format_enum_stub(monolith)
        count = sync_catalog_enum_cache(monolith)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        self.report({"INFO"}, f"Wrote {count} enum items to {path}")
        return {"FINISHED"}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "//catalog_arch_type_items.py"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def register_catalog_enum_ops(monolith):
    sync_catalog_enum_cache(monolith)
    return [SURREAL_ARCH_OT_export_catalog_enum]
