"""Accessory visibility - wire per-slot wardrobe toggles to real collection hides.

P1 from DEEPSEEK_HANDOFF_TOGGLEABLES: the old NikkiWardrobeProperties vector
was UI-only and spawn ops ignored it. This module owns a scene-level 16-slot
BoolVectorProperty and an apply operator that maps each bit to a wardrobe /
accessory collection by name, setting hide_viewport + hide_render (soft, never
Collection.hide_viewport hard locks).
"""

from __future__ import annotations

import bpy

ACCESSORY_VECTOR_SIZE = 16

# Collection name hints, checked in order; first match wins per slot.
_ACCESSORY_HINTS = (
    "Wardrobe_Accessories",
    "Wardrobe_Base",
    "Nikki_Accessories",
    "Nikki_Outfit",
    "Accessories",
)


def _ensure_accessory_props():
    if not hasattr(bpy.types.Scene, "surreal_arch_accessory_toggles"):
        bpy.types.Scene.surreal_arch_accessory_toggles = bpy.props.BoolVectorProperty(
            name="Accessory Toggles",
            description="Per-slot hide/show for wardrobe accessory collections",
            size=ACCESSORY_VECTOR_SIZE,
            default=tuple([True] * ACCESSORY_VECTOR_SIZE),
        )


def unregister_accessory_props():
    if hasattr(bpy.types.Scene, "surreal_arch_accessory_toggles"):
        try:
            del bpy.types.Scene.surreal_arch_accessory_toggles
        except Exception:
            pass


def accessory_collections() -> list:
    """Ordered accessory target collections (name-driven, robust to absence).

    Slots map 1:1 to a live accessory-ish collection. If the stage uses
    Wardrobe_Accessories children (Seq_* / per-piece), they win; otherwise
    known hint names; otherwise any collection whose name mentions Accessor.
    """
    targets = []
    wa = bpy.data.collections.get("Wardrobe_Accessories")
    if wa is not None:
        targets = [c for c in wa.children] or [wa]
    if not targets:
        seen = set()
        for hint in _ACCESSORY_HINTS:
            coll = bpy.data.collections.get(hint)
            if coll is not None and hint not in seen:
                targets.append(coll)
                seen.add(hint)
    if not targets:
        for c in bpy.data.collections:
            if "accessor" in c.name.lower():
                targets.append(c)
    return targets


def apply_accessory_toggles(context=None) -> dict:
    """Set hide_viewport/hide_render on accessory collections from the vector."""
    ctx = context or bpy.context
    scene = ctx.scene
    vec = list(getattr(scene, "surreal_arch_accessory_toggles", (True,) * ACCESSORY_VECTOR_SIZE))
    targets = accessory_collections()
    shown, hidden, missing = [], [], []
    for i, coll in enumerate(targets):
        on = bool(vec[i]) if i < len(vec) else True
        coll.hide_render = not on
        coll.hide_viewport = False  # never hard-lock; eye stays free
        lc = None
        try:
            root = ctx.view_layer.layer_collection

            def _hunt(lc_node, name):
                if lc_node.collection and lc_node.collection.name == name:
                    return lc_node
                for ch in lc_node.children:
                    r = _hunt(ch, name)
                    if r is not None:
                        return r
                return None

            lc = _hunt(root, coll.name)
        except Exception:
            pass
        if lc is not None:
            lc.hide_viewport = not on
        for obj in coll.objects:
            try:
                obj.hide_viewport = not on
                obj.hide_set(not on)
            except Exception:
                pass
        if on:
            shown.append(coll.name)
        else:
            hidden.append(coll.name)
    for i, coll in enumerate(targets):
        pass
    for i in range(len(vec)):
        if i >= len(targets):
            missing.append(i)
    return {
        "ok": True,
        "shown": shown,
        "hidden": hidden,
        "unmapped_slots": missing,
        "total_collections": len(targets),
    }


class SURREAL_ARCH_OT_apply_accessory_visibility(bpy.types.Operator):
    bl_idname = "surreal_arch.apply_accessory_visibility"
    bl_label = "Apply Accessory Visibility"
    bl_description = (
        "Map the 16 accessory toggle slots onto wardrobe/accessory collections "
        "and apply real hide_viewport/hide_render (soft, no hard locks)"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = apply_accessory_toggles(context)
        msg = f"Accessories: {len(result['shown'])} shown, {len(result['hidden'])} hidden"
        if result["unmapped_slots"]:
            msg += f" | unmapped slots: {result['unmapped_slots']}"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SURREAL_ARCH_OT_show_all_accessories(bpy.types.Operator):
    bl_idname = "surreal_arch.show_all_accessories"
    bl_label = "Show All Accessories"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        scene.surreal_arch_accessory_toggles = tuple([True] * ACCESSORY_VECTOR_SIZE)
        result = apply_accessory_toggles(context)
        self.report({"INFO"}, f"All accessories shown ({len(result['shown'])} collections)")
        return {"FINISHED"}


ACCESSORY_CLASSES = (
    SURREAL_ARCH_OT_apply_accessory_visibility,
    SURREAL_ARCH_OT_show_all_accessories,
)


def register_accessory_classes():
    _ensure_accessory_props()
    return list(ACCESSORY_CLASSES)