# -*- coding: utf-8 -*-
"""Unhide Melodia Portfolio Stage collections for review / toggling (SOFT).

Fixes the common "I can't see or toggle most objects" state after solo-Melusina
shots and headless scripts.

Policy (matches Melodia Studio stage_visibility soft isolation):
  - Clear Collection.hide_viewport (hard Outliner lock) — never set it
  - Viewport: LayerCollection.hide_viewport / exclude (soft eye)
  - Render: Collection.hide_render only when requested

Run in the OPEN Blender 5.1 (Scripting → Run Script), or:
  blender Melodia_Portfolio_Stage_v4.blend -b -P Tools/unhide_stage_review_collections.py -- --save

Flags:
  --all          Also show Set_Diorama, SirMelodious, WaterFX, all Wardrobe_*
  --musical      Focus MusicalOrnaments_Review (+ keep Melusina)
  --wardrobe     Focus Wardrobe_fv2_accordion (+ Melusina)
  --save         REFUSED by default (Melusina stage save policy)
"""
from __future__ import annotations

import sys

import bpy


def log(msg: str) -> None:
    print(f"[unhide-stage] {msg}", flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def walk_layer(lc, fn) -> None:
    fn(lc)
    for ch in lc.children:
        walk_layer(ch, fn)


def find_layer_collection(root, name: str):
    found = []

    def _hunt(lc):
        coll = getattr(lc, "collection", None)
        if coll is not None and coll.name == name:
            found.append(lc)

    walk_layer(root, _hunt)
    return found[0] if found else None


def set_collection_flags(name: str, *, viewport: bool, render: bool | None = None) -> None:
    """Soft-set: LayerCollection eye + optional hide_render. Never hard-lock."""
    coll = bpy.data.collections.get(name)
    if not coll:
        return
    # Always unlock hard Outliner lock
    try:
        coll.hide_viewport = False
    except Exception:
        pass
    root = bpy.context.view_layer.layer_collection
    lc = find_layer_collection(root, name)
    if lc is not None:
        try:
            lc.exclude = False
            lc.hide_viewport = not viewport
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
    log(f"  {name}: soft-viewport={'ON' if viewport else 'OFF'}")


def clear_layer_excludes() -> None:
    """Un-exclude / soft-unhide every layer collection so Outliner toggles work."""
    root = bpy.context.view_layer.layer_collection

    def _clear(lc):
        try:
            lc.exclude = False
            lc.hide_viewport = False
            coll = getattr(lc, "collection", None)
            if coll is not None and getattr(coll, "hide_viewport", False):
                coll.hide_viewport = False
        except Exception:
            pass

    walk_layer(root, _clear)
    log("cleared view-layer exclude/hide + Collection.hide_viewport hard locks")


def exit_local_view() -> None:
    for area in bpy.context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D" and getattr(space, "local_view", None):
                try:
                    override = {
                        "area": area,
                        "region": next(r for r in area.regions if r.type == "WINDOW"),
                        "space_data": space,
                    }
                    with bpy.context.temp_override(**override):
                        if space.local_view:
                            bpy.ops.view3d.localview()
                            log("exited local view")
                except Exception as exc:
                    log(f"local view skip: {exc}")


def run(*, show_all: bool, musical: bool, wardrobe: bool) -> None:
    clear_layer_excludes()
    exit_local_view()

    for name in (
        "Asset_melusina",
        "FX_Hero",
        "Lights_Nikki",
        "Review_Queue",
        "MusicalOrnaments_Review",
        "Wardrobe_Base",
        "Wardrobe_Accessories",
        "Wardrobe_fv2_accordion",
        "RenderSubject",
        "Studio",
        "Cameras",
    ):
        set_collection_flags(name, viewport=True, render=None)

    if musical:
        set_collection_flags("MusicalOrnaments_Review", viewport=True, render=True)
        set_collection_flags("Asset_melusina", viewport=True, render=True)

    if wardrobe:
        set_collection_flags("Wardrobe_fv2_accordion", viewport=True, render=True)
        set_collection_flags("Asset_melusina", viewport=True, render=True)

    if show_all:
        for coll in bpy.data.collections:
            n = coll.name
            if n.startswith(
                ("Asset_", "Wardrobe_", "FX_", "Lights_", "Set_", "Look_", "Review")
            ) or n in ("MusicalOrnaments_Review", "Melusina_WaterFX", "RenderSubject"):
                set_collection_flags(n, viewport=True, render=True)
        log("show_all: Asset/Wardrobe/FX/Lights/Set/Look + musical + waterfx")

    log("TIP: Outliner display mode → View Layer. Soft eye toggles always work after Fix.")
    log("TIP: Linked Melusina (library) shows chain icon — editing needs Make Library Override.")
    try:
        bpy.ops.object.select_all(action="DESELECT")
        mel = bpy.data.collections.get("Asset_melusina")
        if mel and mel.objects:
            for o in mel.objects:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            bpy.context.view_layer.objects.active = next(iter(mel.objects), None)
    except Exception:
        pass


def main() -> int:
    args = _argv()
    show_all = "--all" in args
    musical = "--musical" in args
    wardrobe = "--wardrobe" in args
    if not (show_all or musical or wardrobe):
        show_all = True
    run(show_all=show_all, musical=musical, wardrobe=wardrobe)
    if "--save" in args:
        log(
            "REFUSED --save: Melusina stage saves are forbidden after repeated shader stomps. "
            "Save manually in Blender. Set MELODIA_ALLOW_STAGE_SAVE=1 only with artist consent."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
