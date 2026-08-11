"""Melodia GN routing ΓÇö default path for new ornament / music / castle arches."""

from __future__ import annotations

import bpy

from .melodia_gn.core import STUDIO_LABELS, label_tree

# arch_type ΓåÆ (builder_callable_import_path_key, node group name)
ARCH_TO_GN = {
    "GAZEBO": ("structures.build_gazebo", "MEL_gazebo"),
    "PORTICO": ("structures.build_portico", "MEL_portico"),
    "ARCH": ("structures.build_arch", "MEL_arch"),
    # Melodia GN natives
    "MELODIA_NOTE_HEAD": ("music.build_music_note_head", "MEL_music_note_head"),
    "MELODIA_TREBLE_CLEF": ("music.build_music_treble_clef", "MEL_music_treble_clef"),
    "MELODIA_STAFF": ("music.build_music_staff", "MEL_music_staff"),
    "MELODIA_HARMONIC": ("music.build_music_harmonic", "MEL_music_harmonic"),
    "MELODIA_PHRASE": ("music.build_music_phrase", "MEL_music_phrase"),
    "ORN_VINE": ("ornament.build_ornament_vine", "MEL_ornament_vine"),
    "ORN_RADIAL": ("ornament.build_ornament_radial", "MEL_ornament_radial"),
    "ORN_FRAME": ("ornament.build_ornament_frame", "MEL_ornament_frame"),
    "ORN_PANEL": ("ornament.build_ornament_panel", "MEL_ornament_panel"),
    "ORN_GRID": ("ornament.build_ornament_grid", "MEL_ornament_grid"),
    # Live musical RNA aliases ΓåÆ Melodia GN (prefer_melodia_gn).
    # FILIGREE_* stays on monolith builders ΓÇö gothic kitbash SPECS need style props.
    "TREBLE_CLEF": ("music.build_music_treble_clef", "MEL_music_treble_clef"),
    "NOTE_HEAD": ("music.build_music_note_head", "MEL_music_note_head"),
    "STAFF": ("music.build_music_staff", "MEL_music_staff"),
    "SHEET_MUSIC_RAIL": ("music.build_music_sheet_rail", "MEL_music_sheet_rail"),
    "CASTLE_TOWER": ("castle.build_castle_tower", "MEL_castle_tower"),
    "CASTLE_GATEHOUSE": ("castle.build_castle_gatehouse", "MEL_castle_gatehouse"),
    "CASTLE_KEEP": ("castle.build_castle_keep", "MEL_castle_keep"),
    "CASTLE_CRENELLATION": ("castle.build_castle_crenellation", "MEL_castle_crenellation"),
    "CASTLE_WALL_SEGMENT": ("castle.build_castle_wall_segment", "MEL_castle_wall_segment"),
    "CASTLE_GOTHIC_WINDOW": ("castle.build_castle_gothic_window", "MEL_castle_gothic_window"),
    "CASTLE_BUTTRESS": ("castle.build_castle_buttress", "MEL_castle_buttress"),
    "CASTLE_CURTAIN_WALL": ("castle.build_castle_curtain_wall", "MEL_castle_curtain_wall"),
    "CASTLE_MACHICOLATIONS": ("castle.build_castle_machicolations", "MEL_castle_machicolations"),
    "CASTLE_SPIRAL_STAIRS": ("castle.build_castle_spiral_stairs", "MEL_castle_spiral_stairs"),
    "CASTLE_ASSEMBLER": ("castle.build_castle_assembler", "MEL_castle_assembler"),
    "NIKKI_FLORA_QUARTER": ("nikki_quarter.build_nikki_quarter", "MEL_nikki_quarter"),
    "ESCHER_BELVEDERE": ("escher_belvedere.build_escher_belvedere", "MEL_escher_belvedere"),
    "ESCHER_PENROSE_STAIRS": ("escher_penrose_stairs.build_escher_penrose_stairs", "MEL_escher_penrose_stairs"),
    "ESCHER_WATERFALL": ("escher_waterfall.build_escher_waterfall", "MEL_escher_waterfall"),
    "SKY_OBSERVATORY": ("sky_observatory.build_sky_observatory", "MEL_sky_observatory"),
}

MELODIA_GN_PREFIXES = ("MELODIA_", "ORN_", "MUSIC_", "CASTLE_", "NIKKI_", "ESCHER_")


def should_use_melodia_gn(arch_type: str, *, prefer: bool = True) -> bool:
    if not prefer or not arch_type:
        return False
    if arch_type in ARCH_TO_GN:
        return True
    return any(arch_type.startswith(p) for p in MELODIA_GN_PREFIXES)


def _resolve_builder(dotted: str):
    mod_name, fn_name = dotted.rsplit(".", 1)
    mod = __import__(f"surreal_arch.melodia_gn.{mod_name}", fromlist=[fn_name])
    return getattr(mod, fn_name)


def _collection_for_arch_type(arch_type: str) -> str | None:
    if arch_type.startswith(("MELODIA_", "MUSIC_")) or arch_type in ("NOTE_HEAD", "TREBLE_CLEF", "SHEET_MUSIC_RAIL"):
        return "MusicalGN_Editable"
    if arch_type.startswith(("NIKKI_", "SKY_")):
        return "NikkiGN_Editable"
    if arch_type.startswith("ESCHER_"):
        return "EscherGN_Editable"
    if arch_type.startswith("ORN_") or arch_type.startswith("CASTLE_") or arch_type in ("ARCH", "GAZEBO", "PORTICO"):
        return "OrnamentGN_Editable"
    return None


def _ensure_in_collection(obj, coll_name: str):
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        try:
            bpy.context.scene.collection.children.link(coll)
        except Exception:
            pass
    for extant in obj.users_collection:
        if extant == coll:
            return
        if extant.name == coll_name:
            return
    try:
        coll.objects.link(obj)
    except Exception:
        pass


def _socket_identifier(mod, label: str) -> str | None:
    ng = getattr(mod, "node_group", None)
    iface = getattr(ng, "interface", None)
    if iface is not None:
        try:
            for item in iface.items_tree:
                if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "in_out", "") == "INPUT":
                    if getattr(item, "name", "") == label:
                        return getattr(item, "identifier", None)
        except Exception:
            pass
    for key in getattr(mod, "keys", lambda: [])():
        if str(key).lower() == label.lower():
            return key
    return None


def _assign_socket(mod, label: str, value):
    ident = _socket_identifier(mod, label)
    if ident:
        try:
            mod[ident] = value
        except Exception:
            pass


def _bind_music_props(mod, props):
    arch = getattr(props, "arch_type", "")
    if arch == "NOTE_HEAD":
        kind = getattr(props, "note_kind", "QUARTER")
        kind_index = {"WHOLE_NOTE": 0, "HALF_NOTE": 1, "QUARTER": 2, "EIGHTH_NOTE": 3}.get(kind, 2)
        _assign_socket(mod, "Note Kind", kind_index)
        _assign_socket(mod, "Scale", getattr(props, "note_size", 0.5))
        _assign_socket(mod, "Has Stem", kind != "WHOLE_NOTE")
        _assign_socket(mod, "Has Flag", kind == "EIGHTH_NOTE")
    elif arch == "TREBLE_CLEF":
        _assign_socket(mod, "Scale", getattr(props, "clef_size", 2.0))
        _assign_socket(mod, "Thickness", getattr(props, "clef_thickness", 0.06))
        _assign_socket(mod, "Spiral Tightness", getattr(props, "clef_curls", 1.5))
    elif arch == "STAFF":
        _assign_socket(mod, "Length", getattr(props, "staff_length", 8.0))
        _assign_socket(mod, "Thickness", getattr(props, "staff_line_thickness", 0.04))
        _assign_socket(mod, "Bar Count", max(1, int(getattr(props, "staff_note_count", 8) / 4) + 1))
    elif arch == "SHEET_MUSIC_RAIL":
        _assign_socket(mod, "Length", getattr(props, "sheet_length", getattr(props, "staff_length", 8.0)))
        _assign_socket(mod, "Height", getattr(props, "sheet_height", 1.0))
        _assign_socket(mod, "Line Thickness", getattr(props, "sheet_line_thickness", 0.025))
        _assign_socket(mod, "Note Count", getattr(props, "sheet_note_count", getattr(props, "staff_note_count", 12)))
        _assign_socket(mod, "Note Size", getattr(props, "sheet_note_size", 0.18))


def try_apply_melodia_gn(obj, props, monolith=None) -> bool:
    """Ensure Melodia GN group exists and attach as modifier. Returns True if handled."""
    arch = getattr(props, "arch_type", "")
    from .quality_props import prefer_melodia_gn

    if not should_use_melodia_gn(
        arch,
        prefer=prefer_melodia_gn(arch) and bool(getattr(props, "prefer_melodia_gn", True)),
    ):
        return False

    entry = ARCH_TO_GN.get(arch)
    if entry is None:
        print(f"[Melodia GN] prefer on for {arch} but no ARCH_TO_GN map ΓÇö fall through")
        return False

    dotted, group_name = entry
    try:
        if group_name not in bpy.data.node_groups:
            builder = _resolve_builder(dotted)
            builder(group_name)
        ng = bpy.data.node_groups.get(group_name)
        if ng is None:
            return False
        label_tree(ng, group_name)
        # Replace prior MelodiaGN mod
        for mod in list(obj.modifiers):
            if mod.name.startswith("MelodiaGN"):
                obj.modifiers.remove(mod)
        mod = obj.modifiers.new(name="MelodiaGN", type="NODES")
        mod.node_group = ng
        _bind_music_props(mod, props)
        label = STUDIO_LABELS.get(arch, {}).get("ui_label", group_name)
        obj["melodia_gn_label"] = label
        obj["melodia_gn_tree"] = group_name
        write_snaps = getattr(monolith, "_gb_write_snap_points", None) if monolith else None
        if write_snaps:
            try:
                write_snaps(obj, props)
            except Exception:
                pass
        print(f"[Melodia GN] attached {group_name} to {obj.name}")
        target_coll = _collection_for_arch_type(arch)
        if target_coll:
            _ensure_in_collection(obj, target_coll)
        return True
    except Exception as exc:
        print(f"[Melodia GN] apply failed for {arch}: {exc}")
        return False
