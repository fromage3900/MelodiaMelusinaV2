"""Melodia stage collection visibility — soft presets for portfolio cockpit UI.

Policy (soft isolation):
  - Viewport: LayerCollection.hide_viewport (Outliner eye) — never Collection.hide_viewport
  - Render: Collection.hide_render (camera icon)
  - Always clear lc.exclude on touched stage collections
  - Collection.hide_viewport (hard lock) is only cleared, never set (unless hard=True escape hatch)
"""

from __future__ import annotations

import bpy

from .branding import N_PANEL_CATEGORY, PRODUCT_NAME

# Preset → (on collections, off collections)
_STAGE_PRESETS = {
    "solo_melusina": {
        "on": ("Asset_melusina", "Asset_sirmelodious", "Lights_Nikki", "Studio", "Cameras", "Characters", "FX_Hero"),
        "off": (
            "Review_Queue",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Lights_Jewelry",
            "Lights_Silhouette",
            "MusicalOrnaments_Review",
            "MusicalGN_Editable",
            "OrnamentGN_Editable",
            "RenderSubject",
        ),
    },
    "diorama_on": {
        "on": (
            "Asset_melusina",
            "Asset_sirmelodious",
            "Lights_Nikki",
            "Studio",
            "Cameras",
            "Set_Diorama",
            "Characters",
        ),
        "off": ("Surreal_Regen_Starlight", "Melusina_WaterFX", "Review_Queue"),
    },
    "starlight_on": {
        "on": (
            "Asset_melusina",
            "Asset_sirmelodious",
            "Lights_Nikki",
            "Studio",
            "Cameras",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Characters",
        ),
        "off": ("Melusina_WaterFX", "Review_Queue"),
    },
    "beauty_clean": {
        # Lights parent holds L_KeyWarm / L_RimPink / L_GoldKick / L_FillCool.
        # Lights_Nikki is an empty marker — omitting Lights renders unlit.
        "on": ("Asset_melusina", "Asset_sirmelodious", "Lights", "Lights_Nikki", "Studio", "Cameras", "Characters"),
        "off": (
            "Review_Queue",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Melusina_HairDrip",
            "FX_Hero",
            "Lights_Jewelry",
            "Lights_Silhouette",
            "MusicalOrnaments_Review",
            "MusicalGN_Editable",
            "OrnamentGN_Editable",
        ),
    },
    "hair_drip_on": {
        "on": (
            "Asset_melusina",
            "Asset_sirmelodious",
            "Lights_Nikki",
            "Studio",
            "Cameras",
            "Characters",
            "Melusina_HairDrip",
        ),
        "off": (
            "Review_Queue",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "FX_Hero",
        ),
    },
    # Review Queue focus: kitbash subject — Melusina soft-off
    "review_all": {
        "on": (
            "Review_Queue",
            "Lights_Nikki",
            "Studio",
            "Cameras",
            "MusicalGN_Editable",
            "OrnamentGN_Editable",
            "MusicalOrnaments_Review",
            "RenderSubject",
        ),
        "off": (
            "Asset_melusina",
            "Characters",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Melusina_HairDrip",
            "FX_Hero",
            "Lights_Jewelry",
            "Lights_Silhouette",
        ),
    },
    "review_queue_solo": {
        "on": (
            "Review_Queue",
            "Lights_Nikki",
            "Studio",
            "Cameras",
        ),
        "off": (
            "Asset_melusina",
            "Characters",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Melusina_HairDrip",
            "FX_Hero",
            "Lights_Jewelry",
            "Lights_Silhouette",
            "MusicalOrnaments_Review",
            "MusicalGN_Editable",
            "OrnamentGN_Editable",
            "RenderSubject",
        ),
    },
    "editable_gn": {
        "on": (
            "OrnamentGN_Editable",
            "MusicalGN_Editable",
            "Review_Queue",
            "Lights_Nikki",
            "Studio",
            "Cameras",
        ),
        "off": (
            "Asset_melusina",
            "Characters",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Melusina_HairDrip",
            "FX_Hero",
            "Lights_Jewelry",
            "Lights_Silhouette",
            "MusicalOrnaments_Review",
            "RenderSubject",
        ),
    },
    # Sculpt focus: editable GN only (legacy review colls removed from stage workflow)
    "sculpt_monetization": {
        "on": (
            "Studio",
            "Cameras",
            "Lights_Nikki",
            "MusicalGN_Editable",
            "OrnamentGN_Editable",
        ),
        "off": (
            "Review_Queue",
            "Asset_melusina",
            "Set_Diorama",
            "Surreal_Regen_Starlight",
            "Melusina_WaterFX",
            "Characters",
            "FX_Hero",
            "Lights_Jewelry",
            "Lights_Silhouette",
            "MusicalOrnaments_Review",
            "OrnamentFix_Review",
            "RenderSubject",
        ),
    },
}

# Monetization polish targets (stage object names or substrings)
_SCULPT_EXACT = frozenset(
    {
        "SM_Orn_TrebleClef",
        "SM_Orn_MusicalCorner",
        "SM_Orn_MelodyToken_01",
        "SM_Orn_MelodyToken_02",
        "SM_Orn_MelodyToken_03",
        "MelodyToken",
    }
)
_SCULPT_SUBSTRINGS = (
    "torus_knot_SM_Orn_TorusKnot",
    "filigree_ring_SM_Orn_FiligreeRing",
    "crown_molding_SM_Orn_CrownMolding",
    "rose_window_SM_Orn_RoseWindow",
    "vault_ribs_SM_Orn_VaultRibs",
    "oculus_frame_SM_Orn_OculusFrame",
    "spiral_stair_SM_Orn_SpiralStaircase",
    "SM_Orn_TorusKnot",
    "SM_Orn_FiligreeRing",
    "SM_Orn_CrownMolding",
    "SM_Orn_RoseWindow",
    "SM_Orn_VaultRibs",
    "SM_Orn_OculusFrame",
    "SM_Orn_SpiralStaircase",
    "SM_Orn_MelodyToken_",
)

# Core stage names always in allowlist (even if not in a preset yet)
_STATIC_STAGE_NAMES = frozenset(
    {
        "Review_Queue",
        "Asset_melusina",
        "Asset_sirmelodious",
        "Characters",
        "Studio",
        "Cameras",
        "Set_Diorama",
        "Surreal_Regen_Starlight",
        "Melusina_WaterFX",
        "Melusina_HairDrip",
        "FX_Hero",
        "Lights_Nikki",
        "Lights_Jewelry",
        "Lights_Silhouette",
        "MusicalOrnaments_Review",
        "MusicalGN_Editable",
        "OrnamentGN_Editable",
        "OrnamentFix_Review",
        "RenderSubject",
        "Wardrobe_Base",
        "Wardrobe_Accessories",
    }
)


def is_sculpt_monetization_target(obj) -> bool:
    if obj is None or obj.type not in {"MESH", "CURVE", "SURFACE", "FONT"}:
        return False
    name = obj.name
    if name in _SCULPT_EXACT:
        return True
    return any(s in name for s in _SCULPT_SUBSTRINGS)


def walk_layer(lc, fn) -> None:
    fn(lc)
    for ch in lc.children:
        walk_layer(ch, fn)


def find_layer_collection(root, name: str):
    """Return LayerCollection whose .collection.name matches, or None."""
    found = []

    def _hunt(lc):
        coll = getattr(lc, "collection", None)
        if coll is not None and coll.name == name:
            found.append(lc)

    walk_layer(root, _hunt)
    return found[0] if found else None


def review_queue_children() -> list[bpy.types.Collection]:
    parent = bpy.data.collections.get("Review_Queue")
    if parent is None:
        return []
    return list(parent.children)


def _stage_collection_names() -> set[str]:
    names: set[str] = set(_STATIC_STAGE_NAMES)
    for spec in _STAGE_PRESETS.values():
        names.update(spec.get("on") or ())
        names.update(spec.get("off") or ())
    for c in bpy.data.collections:
        if c.name.startswith(("Wardrobe_", "Lights_")):
            names.add(c.name)
        if c.name.startswith("Asset_") and c.name not in names:
            # Review_Queue Asset_* children
            names.add(c.name)
    rq = bpy.data.collections.get("Review_Queue")
    if rq is not None:
        names.add("Review_Queue")
        for ch in rq.children:
            names.add(ch.name)
    return names


def clear_layer_excludes(context=None) -> None:
    """Clear exclude/hide only on known Melodia stage collections (not whole scene)."""
    ctx = context or bpy.context
    root = ctx.view_layer.layer_collection
    allowed = _stage_collection_names()

    def _clear(lc):
        try:
            coll = getattr(lc, "collection", None)
            cname = getattr(coll, "name", "") if coll is not None else ""
            if cname and cname not in allowed:
                return
            lc.exclude = False
            lc.hide_viewport = False
        except Exception:
            pass

    walk_layer(root, _clear)


def clear_collection_hard_locks(context=None) -> int:
    """Clear Collection.hide_viewport (hard Outliner lock) on allowlisted stage cols."""
    allowed = _stage_collection_names()
    cleared = 0
    for name in sorted(allowed):
        coll = bpy.data.collections.get(name)
        if coll is None:
            continue
        try:
            if coll.hide_viewport:
                coll.hide_viewport = False
                cleared += 1
        except Exception:
            continue
    return cleared


def set_collection_flags(
    name: str,
    *,
    viewport: bool,
    render: bool | None = None,
    hard: bool = False,
    context=None,
) -> bool:
    """Soft-set visibility for a named collection.

    viewport → LayerCollection.hide_viewport (current view layer)
    render   → Collection.hide_render
    hard     → escape hatch: also set Collection.hide_viewport (default False — never for stage)
    """
    coll = bpy.data.collections.get(name)
    if not coll:
        return False
    # Never force Sir Melodious off — that greys Asset_sirmelodious in the Outliner.
    if name == "Asset_sirmelodious" and not viewport:
        viewport = True
        if render is False:
            render = True
    # Never hard-lock Review_Queue parent or any of its children
    never_hard = name == "Review_Queue" or name.startswith("Asset_")
    if name in _STATIC_STAGE_NAMES or never_hard:
        hard = False

    ctx = context or bpy.context
    root = ctx.view_layer.layer_collection
    lc = find_layer_collection(root, name)
    if lc is not None:
        try:
            lc.exclude = False
            lc.hide_viewport = not viewport
        except Exception:
            pass

    # Soft path: always clear Collection hard-lock so Outliner eyes work
    try:
        if hard:
            coll.hide_viewport = not viewport
        else:
            coll.hide_viewport = False
    except Exception:
        pass

    if render is not None:
        try:
            coll.hide_render = not render
        except Exception:
            pass

    for o in list(coll.objects):
        try:
            if o is None:
                continue
            if viewport:
                o.hide_viewport = False
                o.hide_set(False)
        except Exception:
            pass
    return True


def clear_object_visibility_overrides() -> int:
    """Clear per-object hide flags so Outliner collection toggles work again.

    Sculpt isolate previously set hide_viewport/hide_set on hundreds of objects,
    which blocks normal collection visibility. Every stage preset should clear this.
    """
    cleared = 0
    for obj in bpy.data.objects:
        try:
            changed = False
            if obj.hide_viewport:
                obj.hide_viewport = False
                changed = True
            if obj.hide_render:
                obj.hide_render = False
                changed = True
            try:
                if obj.hide_get():
                    obj.hide_set(False)
                    changed = True
            except Exception:
                pass
            if changed:
                cleared += 1
        except Exception:
            continue
    return cleared


def ensure_outliner_restrict_columns(
    *,
    viewport: bool = True,
    hide: bool = True,
    render: bool = True,
) -> int:
    """Show Outliner restriction toggles — especially Disable in Viewports (monitor/laptop).

    Soft LayerCollection hides still drive the eye; this only unhides the icon columns
    so the laptop/monitor column stays visible while reviewing stage collections.
    """
    count = 0
    try:
        windows = bpy.context.window_manager.windows
    except Exception:
        return 0
    for window in windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != "OUTLINER":
                continue
            for sp in area.spaces:
                if sp.type != "OUTLINER":
                    continue
                try:
                    sp.show_restrict_column_viewport = viewport
                    sp.show_restrict_column_hide = hide
                    sp.show_restrict_column_render = render
                    count += 1
                except Exception:
                    continue
    return count


def fix_stage_visibility(context=None) -> dict:
    """Unlock residual hard locks + clear object hides + soft layer clears."""
    cleared_objs = clear_object_visibility_overrides()
    cleared_hard = clear_collection_hard_locks(context)
    clear_layer_excludes(context)
    outliners = ensure_outliner_restrict_columns()
    return {
        "cleared_object_hides": cleared_objs,
        "cleared_hard_locks": cleared_hard,
        "outliner_restrict_columns": outliners,
    }


def ensure_ornament_fix_collection() -> bpy.types.Collection | None:
    """Link gothic monetization fix meshes into OrnamentFix_Review for collection toggles."""
    name = "OrnamentFix_Review"
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        try:
            bpy.context.scene.collection.children.link(coll)
        except Exception:
            pass
    targets = (
        "torus_knot_SM_Orn_TorusKnot",
        "filigree_ring_SM_Orn_FiligreeRing",
        "crown_molding_SM_Orn_CrownMolding",
        "rose_window_SM_Orn_RoseWindow_8Petal",
        "vault_ribs_SM_Orn_VaultRibs",
        "oculus_frame_SM_Orn_OculusFrame",
        "spiral_stair_SM_Orn_SpiralStaircase",
        "SM_Orn_TorusKnot",
        "SM_Orn_FiligreeRing",
        "SM_Orn_CrownMolding",
        "SM_Orn_RoseWindow_8Petal",
        "SM_Orn_VaultRibs",
        "SM_Orn_OculusFrame",
        "SM_Orn_SpiralStaircase",
    )
    for oname in targets:
        obj = bpy.data.objects.get(oname)
        if obj is None:
            continue
        if coll not in obj.users_collection:
            try:
                coll.objects.link(obj)
            except Exception:
                pass
    return coll


def isolate_sculpt_monetization_objects() -> dict:
    """Sculpt focus via COLLECTIONS only — never set per-object hide flags."""
    ensure_ornament_fix_collection()
    shown_colls = []
    for cname in (
        "OrnamentGN_Editable",
        "MusicalGN_Editable",
        "OrnamentFix_Review",
        "MusicalOrnaments_Review",
        "Studio",
        "Cameras",
        "Lights_Nikki",
    ):
        if set_collection_flags(cname, viewport=True, render=True):
            shown_colls.append(cname)
    return {"mode": "collections_only", "shown_collections": shown_colls}


def apply_stage_preset(preset_id: str, *, clear_exclude: bool = True) -> dict:
    spec = _STAGE_PRESETS.get(preset_id)
    if not spec:
        return {"ok": False, "error": f"unknown preset {preset_id}"}
    fix = fix_stage_visibility()
    cleared_objs = fix["cleared_object_hides"]
    if not clear_exclude:
        # fix_stage_visibility already cleared excludes; no-op branch for API compat
        pass
    if preset_id == "sculpt_monetization":
        on_names = list(spec["on"]) + [
            "OrnamentGN_Editable",
            "MusicalGN_Editable",
        ]
        off_names = list(spec["off"])
    else:
        on_names = list(spec["on"])
        off_names = list(spec["off"])
    applied_on, applied_off, missing = [], [], []
    for name in on_names:
        if set_collection_flags(name, viewport=True, render=True):
            applied_on.append(name)
        else:
            missing.append(name)
    for name in off_names:
        if set_collection_flags(name, viewport=False, render=False):
            applied_off.append(name)
        elif name not in missing:
            missing.append(name)
    isolate = None
    if preset_id == "sculpt_monetization":
        isolate = isolate_sculpt_monetization_objects()
    return {
        "ok": True,
        "preset": preset_id,
        "on": applied_on,
        "off": applied_off,
        "missing": missing,
        "cleared_object_hides": cleared_objs,
        "cleared_hard_locks": fix["cleared_hard_locks"],
        "isolate": isolate,
    }


def _review_queue_scene_index(scene) -> int:
    return int(getattr(scene, "surreal_arch_review_queue_index", 0) or 0)


def _set_review_queue_scene_index(scene, index: int) -> None:
    try:
        scene.surreal_arch_review_queue_index = int(index)
    except Exception:
        pass


def solo_review_queue_child(index: int | None = None, *, delta: int = 0, context=None) -> dict:
    """Soft-show exactly one Review_Queue child; soft-hide siblings. No hard locks."""
    ctx = context or bpy.context
    children = review_queue_children()
    if not children:
        return {"ok": False, "error": "Review_Queue missing or empty"}

    # Ensure parent soft-on; Melusina soft-off for kitbash focus
    set_collection_flags("Review_Queue", viewport=True, render=True, context=ctx)
    set_collection_flags("Lights_Nikki", viewport=True, render=True, context=ctx)
    set_collection_flags("Studio", viewport=True, render=True, context=ctx)
    set_collection_flags("Cameras", viewport=True, render=True, context=ctx)

    n = len(children)
    scene = ctx.scene
    if index is None:
        cur = _review_queue_scene_index(scene)
        index = (cur + int(delta)) % n
    else:
        index = int(index) % n

    _set_review_queue_scene_index(scene, index)
    shown = None
    for i, child in enumerate(children):
        on = i == index
        set_collection_flags(child.name, viewport=on, render=on, context=ctx)
        if on:
            shown = child

    framed = None
    if shown is not None:
        try:
            bpy.ops.object.select_all(action="DESELECT")
        except Exception:
            pass
        mesh = None
        for o in shown.objects:
            if o.type == "MESH":
                mesh = o
                break
        if mesh is None and shown.objects:
            mesh = next(iter(shown.objects), None)
        if mesh is not None:
            try:
                mesh.select_set(True)
                ctx.view_layer.objects.active = mesh
                framed = mesh.name
                bpy.ops.view3d.view_selected(use_all_regions=False)
            except Exception:
                try:
                    framed = mesh.name
                except Exception:
                    framed = None

    label = shown.name if shown else "?"
    return {
        "ok": True,
        "name": label,
        "index": index,
        "total": n,
        "framed": framed,
        "message": f"{label} ({index + 1}/{n})",
    }


class SURREAL_ARCH_OT_toggle_stage_collection(bpy.types.Operator):
    bl_idname = "surreal_arch.toggle_stage_collection"
    bl_label = "Toggle Stage Collection"
    bl_options = {"REGISTER"}

    collection_name: bpy.props.StringProperty()
    viewport: bpy.props.BoolProperty(default=True)
    render: bpy.props.BoolProperty(default=True)
    clear_exclude: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        if self.clear_exclude:
            clear_layer_excludes(context)
        name = self.collection_name.strip()
        if not name:
            self.report({"ERROR"}, "collection_name required")
            return {"CANCELLED"}
        coll = bpy.data.collections.get(name)
        if not coll:
            self.report({"WARNING"}, f"Collection not found: {name}")
            return {"CANCELLED"}
        # Soft read: prefer LayerCollection eye state
        show = bool(self.viewport)
        ok = set_collection_flags(
            name,
            viewport=show,
            render=bool(self.render) if show else False,
            context=context,
        )
        self.report({"INFO"}, f"{name}: {'ON' if show else 'OFF'}" if ok else f"{name}: failed")
        return {"FINISHED"} if ok else {"CANCELLED"}


class SURREAL_ARCH_OT_set_stage_visibility_preset(bpy.types.Operator):
    bl_idname = "surreal_arch.set_stage_visibility_preset"
    bl_label = "Stage Visibility Preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        items=(
            ("solo_melusina", "Solo Melusina", "Hero + Nikki lights (Review_Queue soft-off)"),
            ("diorama_on", "Diorama", "Solo + Set_Diorama"),
            ("starlight_on", "Starlight", "Diorama + Surreal_Regen_Starlight"),
            ("beauty_clean", "Beauty Clean", "Minimal beauty plate"),
            ("review_all", "Review Queue", "Kitbash focus — Review_Queue on, Melusina soft-off"),
            ("review_queue_solo", "Review Queue Solo", "Only Review_Queue + lights/cameras"),
            (
                "sculpt_monetization",
                "Sculpt Monetization",
                "Only kitbash fix meshes + Melody Tokens",
            ),
            (
                "editable_gn",
                "Editable GN",
                "Soft-isolate OrnamentGN_Editable / MusicalGN_Editable / Review_Queue",
            ),
        ),
        default="solo_melusina",
    )

    def execute(self, context):
        result = apply_stage_preset(self.preset, clear_exclude=True)
        if not result.get("ok"):
            self.report({"ERROR"}, result.get("error", "failed"))
            return {"CANCELLED"}
        miss = result.get("missing") or []
        msg = f"Stage preset: {self.preset} (on={len(result['on'])} off={len(result['off'])})"
        if result.get("cleared_object_hides"):
            msg += f" | cleared {result['cleared_object_hides']} obj hides"
        if result.get("cleared_hard_locks"):
            msg += f" | unlocked {result['cleared_hard_locks']} hard locks"
        if miss:
            msg += f" | missing {len(miss)}"
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SURREAL_ARCH_OT_clear_object_visibility(bpy.types.Operator):
    bl_idname = "surreal_arch.clear_object_visibility"
    bl_label = "Fix Collection Toggles"
    bl_description = (
        "Clear object hides + Collection.hide_viewport hard locks on stage allowlist "
        "so Outliner eyes work again; also shows the Disable in Viewports (laptop) column"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = fix_stage_visibility(context)
        cols = result.get("outliner_restrict_columns", 0)
        self.report(
            {"INFO"},
            f"Fixed: {result['cleared_object_hides']} obj hides, "
            f"{result['cleared_hard_locks']} hard locks cleared"
            + (f", laptop column on ({cols} outliner)" if cols else ""),
        )
        return {"FINISHED"}


class SURREAL_ARCH_OT_show_outliner_restrict(bpy.types.Operator):
    bl_idname = "surreal_arch.show_outliner_restrict"
    bl_label = "Show Outliner Restrict Columns"
    bl_description = (
        "Enable Outliner restriction toggles including Disable in Viewports "
        "(monitor/laptop icon column)"
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        n = ensure_outliner_restrict_columns()
        if n <= 0:
            self.report({"WARNING"}, "No Outliner editor found")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Outliner laptop/eye/camera columns enabled ({n})")
        return {"FINISHED"}


class SURREAL_ARCH_OT_review_queue_cycle(bpy.types.Operator):
    bl_idname = "surreal_arch.review_queue_cycle"
    bl_label = "Review Queue Cycle"
    bl_description = "Soft-solo one Review_Queue child at a time (Prev / Next / Solo Current)"
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.IntProperty(
        name="Direction",
        description="-1 Prev, 0 Solo Current, +1 Next",
        default=0,
        min=-1,
        max=1,
    )

    def execute(self, context):
        delta = int(self.direction)
        index = None
        if delta == 0:
            index = _review_queue_scene_index(context.scene)
        result = solo_review_queue_child(index=index, delta=delta if delta != 0 else 0, context=context)
        if not result.get("ok"):
            self.report({"WARNING"}, result.get("error", "Review Queue cycle failed"))
            return {"CANCELLED"}
        self.report({"INFO"}, result.get("message", "OK"))
        return {"FINISHED"}


class SURREAL_ARCH_OT_isolate_editable_gn(bpy.types.Operator):
    bl_idname = "surreal_arch.isolate_editable_gn"
    bl_label = "Isolate Editable GN"
    bl_description = (
        "Soft-isolate OrnamentGN_Editable, MusicalGN_Editable, and Review_Queue "
        "via LayerCollection.hide_viewport"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = apply_stage_preset("editable_gn", clear_exclude=True)
        if not result.get("ok"):
            self.report({"ERROR"}, result.get("error", "failed"))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            f"Isolated editable GN (on={len(result['on'])} off={len(result['off'])})",
        )
        return {"FINISHED"}


class SURREAL_ARCH_PT_stage_studio(bpy.types.Panel):
    """Stage tools nested under Melodia Studio (closed). Pie owns quick presets."""

    bl_label = "Stage (Solo / Starlight / Beauty)"
    bl_idname = "SURREAL_ARCH_PT_stage_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 6

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Stage visibility (soft)", icon="HIDE_OFF")
        fix = box.row(align=True)
        fix.operator(
            "surreal_arch.clear_object_visibility",
            text="Fix collection toggles",
            icon="CHECKMARK",
        )
        eye = box.row(align=True)
        eye.operator(
            "surreal_arch.show_outliner_restrict",
            text="Show Outliner laptop column",
            icon="RESTRICT_VIEW_OFF",
        )
        sculpt = box.row(align=True)
        sculpt.scale_y = 1.35
        op = sculpt.operator(
            "surreal_arch.set_stage_visibility_preset",
            text="Sculpt Monetization",
            icon="SCULPTMODE_HLT",
        )
        op.preset = "sculpt_monetization"
        iso = box.row(align=True)
        iso.scale_y = 1.2
        iso.operator(
            "surreal_arch.isolate_editable_gn",
            text="Isolate Editable GN",
            icon="RESTRICT_VIEW_OFF",
        )
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for preset, label in (
            ("solo_melusina", "Solo"),
            ("diorama_on", "Diorama"),
            ("starlight_on", "Starlight"),
            ("beauty_clean", "Beauty"),
            ("review_all", "Review Queue"),
            ("review_queue_solo", "RQ Solo"),
        ):
            op = grid.operator("surreal_arch.set_stage_visibility_preset", text=label)
            op.preset = preset

        # Review Queue parent toggle + Prev/Next/Solo
        rq_box = box.box()
        rq_box.label(text="Review Queue", icon="ASSET_MANAGER")
        rq = bpy.data.collections.get("Review_Queue")
        rq_on = False
        if rq is not None:
            lc = find_layer_collection(context.view_layer.layer_collection, "Review_Queue")
            if lc is not None:
                rq_on = not lc.hide_viewport and not lc.exclude
            else:
                rq_on = not rq.hide_viewport
        toggle_row = rq_box.row(align=True)
        op = toggle_row.operator(
            "surreal_arch.toggle_stage_collection",
            text="Queue Parent",
            icon="OUTLINER_COLLECTION",
            depress=rq_on,
        )
        op.collection_name = "Review_Queue"
        op.viewport = not rq_on
        op.render = not rq_on

        cycle = rq_box.row(align=True)
        op = cycle.operator("surreal_arch.review_queue_cycle", text="Prev", icon="TRIA_LEFT")
        op.direction = -1
        op = cycle.operator("surreal_arch.review_queue_cycle", text="Solo", icon="SOLO_ON")
        op.direction = 0
        op = cycle.operator("surreal_arch.review_queue_cycle", text="Next", icon="TRIA_RIGHT")
        op.direction = 1

        children = review_queue_children()
        if children:
            idx = _review_queue_scene_index(context.scene) % len(children)
            rq_box.label(text=f"{children[idx].name} ({idx + 1}/{len(children)})")
        else:
            rq_box.label(text="No Review_Queue children")

        quick = box.row(align=True)
        for cname, label in (
            ("Lights_Nikki", "Nikki"),
            ("Lights_Jewelry", "Jewelry"),
            ("Set_Diorama", "Diorama"),
            ("Surreal_Regen_Starlight", "Regen"),
            ("MusicalGN_Editable", "MusicalGN"),
            ("OrnamentGN_Editable", "GothicGN"),
        ):
            coll = bpy.data.collections.get(cname)
            on = False
            if coll is not None:
                lc = find_layer_collection(context.view_layer.layer_collection, cname)
                if lc is not None:
                    on = not lc.hide_viewport and not lc.exclude
                else:
                    on = not coll.hide_viewport
            op = quick.operator(
                "surreal_arch.toggle_stage_collection",
                text=label,
                depress=on,
            )
            op.collection_name = cname
            op.viewport = not on
            op.render = not on


def _ensure_review_queue_index_prop():
    if not hasattr(bpy.types.Scene, "surreal_arch_review_queue_index"):
        bpy.types.Scene.surreal_arch_review_queue_index = bpy.props.IntProperty(
            name="Review Queue Index",
            description="Soft-solo index into Review_Queue children",
            default=0,
            min=0,
        )


def register_stage_visibility_classes():
    _ensure_review_queue_index_prop()
    try:
        ensure_outliner_restrict_columns()
    except Exception:
        pass
    return [
        SURREAL_ARCH_OT_toggle_stage_collection,
        SURREAL_ARCH_OT_set_stage_visibility_preset,
        SURREAL_ARCH_OT_clear_object_visibility,
        SURREAL_ARCH_OT_show_outliner_restrict,
        SURREAL_ARCH_OT_review_queue_cycle,
        SURREAL_ARCH_OT_isolate_editable_gn,
        SURREAL_ARCH_PT_stage_studio,
    ]
