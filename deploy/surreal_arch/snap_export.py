"""UE-oriented snap + trim metadata export for kitbash pipelines."""

from __future__ import annotations

import json


def build_trim_groups(props, monolith=None):
    """Derive trim-sheet face group hints from arch_type + greybox trim props."""
    at = props.arch_type
    mode = getattr(props, "gb_trim_mode", "NONE")
    recess = float(getattr(props, "gb_trim_recess", 0.04))
    groups = []

    def _g(gid, role, ue_slot, snap_bind=None, notes=""):
        entry = {
            "id": gid,
            "role": role,
            "ue_material_slot": ue_slot,
            "trim_mode": mode,
            "recess_depth": recess,
        }
        if snap_bind:
            entry["snap_bind"] = snap_bind
        if notes:
            entry["notes"] = notes
        groups.append(entry)

    if mode == "NONE" and not at.startswith(("GB_SCIFI_", "GB_CORRIDOR_OFFSET", "GB_BRUTALIST_", "GB_ZEN_")):
        return groups

    if at == "GB_CORRIDOR_OFFSET":
        _g("wall_panel_recess", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Side wall offset panels")
        _g("floor_ledge", "TRIM_FLOOR_LEDGE", "M_Trim_Floor", notes="Center runner + side strips")
        _g("ceiling_slab", "TRIM_CEILING", "M_Trim_Ceiling")
    elif at == "GB_ROMANESQUE_ARCADE":
        _g("colonette", "TRIM_COLUMN", "M_Trim_Column")
        _g("impost_block", "TRIM_IMPOST", "M_Trim_Impost")
        _g("arch_ring", "TRIM_ARCH", "M_Trim_Arch", snap_bind="arch_center")
        _g("barrel_vault", "TRIM_VAULT", "M_Trim_Vault")
    elif at == "GB_ROMANESQUE_APSE":
        _g("apse_shell", "TRIM_PANEL_RECESS", "M_Trim_Apse_Shell", snap_bind="apse_center",
           notes="Semicircular choir recess — UE trim sheet apse band")
        _g("barrel_vault", "TRIM_VAULT", "M_Trim_Vault")
        _g("apse_open", "TRIM_FRAME", "M_Trim_Frame", snap_bind="apse_open")
    elif at == "GB_BRUTALIST_PANEL_WALL":
        _g("pilaster", "TRIM_PILASTER", "M_Trim_Pilaster")
        _g("recess_panel", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Between pilasters")
        _g("baseboard", "TRIM_BASEBOARD", "M_Trim_Baseboard")
    elif at == "GB_VENETIAN_LOGGIA":
        _g("bifora_void", "TRIM_OPENING", "M_Trim_Opening")
        _g("colonnette", "TRIM_COLUMN", "M_Trim_Column")
        _g("cornice_shelf", "TRIM_CORNICE", "M_Trim_Cornice", snap_bind="cornice")
        _g("sill_band", "TRIM_SILL", "M_Trim_Sill")
    elif at == "GB_SCIFI_PRESSURE_DOOR":
        _g("gasket_ring", "TRIM_GASKET", "M_Trim_Gasket", snap_bind="gasket",
           notes="Recessed channel around door — UE trim sheet gasket")
        _g("pressure_frame", "TRIM_FRAME", "M_Trim_Frame", snap_bind="door")
        _g("door_void", "TRIM_OPENING", "M_Trim_Door_Void", snap_bind="door")
    elif at == "GB_ZEN_ROJI_STEP":
        _g("path_slab", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor")
        _g("edge_stone", "TRIM_EDGE", "M_Trim_Edge", notes="Raised roji edge stones")
    elif at == "GB_ZEN_TORII_GATE":
        _g("hashira", "TRIM_COLUMN", "M_Trim_Column", snap_bind="gate")
        _g("nuki", "TRIM_BEAM", "M_Trim_Beam")
        _g("kasagi", "TRIM_LINTEL", "M_Trim_Lintel", snap_bind="gate")
    elif at == "GB_ZEN_SAKURA_TORII":
        _g("hashira", "TRIM_COLUMN", "M_Trim_Column", snap_bind="gate")
        _g("nuki", "TRIM_BEAM", "M_Trim_Beam")
        _g("kasagi", "TRIM_LINTEL", "M_Trim_Lintel", snap_bind="gate")
        _g("blossom_band", "TRIM_BLOSSOM", "M_Trim_Blossom", notes="Sakura blossom band on kasagi")
        _g("petal_accent", "TRIM_PETAL", "M_Trim_Petal", notes="Petal accent strips on hashira")
    elif at == "GB_ZEN_TSUKUBAI":
        _g("basin", "TRIM_BASIN", "M_Trim_Basin", snap_bind="basin",
           notes="Recess bowl — UE trim sheet basin band")
        _g("flagstone", "TRIM_FLAGSTONE", "M_Trim_Flagstone")
        _g("pad", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor")
    elif at == "GB_ZEN_ENGAWA":
        _g("deck", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor")
        _g("post", "TRIM_COLUMN", "M_Trim_Column")
        _g("rail", "TRIM_RAIL", "M_Trim_Rail", snap_bind="engawa_edge")
    elif at == "GB_ZEN_BAMBOO_FENCE":
        _g("bamboo_post", "TRIM_COLUMN", "M_Trim_Column")
        _g("bamboo_rail", "TRIM_RAIL", "M_Trim_Rail", notes="Horizontal bamboo rails")
    elif at == "GB_ZEN_TOBIISHI":
        _g("stepping_stone", "TRIM_FLOOR", "M_Trim_Floor", notes="Scattered tobi-ishi stones")
        _g("path_bed", "TRIM_EDGE", "M_Trim_Edge", snap_bind="floor")
    elif at == "GB_ZEN_KARESANSUI":
        _g("sand_bed", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Raked gravel plane")
        _g("border_stone", "TRIM_EDGE", "M_Trim_Edge", notes="Ishigumi border collar")
        _g("rake_groove", "TRIM_PANEL_RECESS", "M_Trim_Rake", notes="Parallel rake grooves")
    elif at == "GB_ZEN_MACHIAI":
        _g("post", "TRIM_COLUMN", "M_Trim_Column")
        _g("roof", "TRIM_BEAM", "M_Trim_Beam", snap_bind="floor")
        _g("bench", "TRIM_FLOOR", "M_Trim_Bench", notes="Machiai waiting bench")
    elif at == "GB_ZEN_STONE_BRIDGE":
        _g("deck", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="deck", notes="Bridge deck slab")
        _g("rail", "TRIM_RAIL", "M_Trim_Rail", notes="Low stone bridge rail")
        _g("abutment", "TRIM_EDGE", "M_Trim_Edge", notes="Bank abutment blocks")
    elif at == "GB_ZEN_CHERRY_ALLEE":
        _g("trunk_base", "TRIM_COLUMN", "M_Trim_Trunk", notes="Cherry trunk bases along path")
        _g("blossom_canopy", "TRIM_PANEL_RECESS", "M_Trim_Blossom", snap_bind="canopy", notes="Canopy blossom trim zone")
        _g("petal_scatter", "TRIM_FLOOR", "M_Trim_Petal", notes="Fallen petal scatter strip")
    elif at == "GB_ZEN_WATER_EDGE":
        _g("stream_bed", "TRIM_BASIN", "M_Trim_Basin", snap_bind="floor", notes="Depressed stream channel")
        _g("stream_bank", "TRIM_EDGE", "M_Trim_Edge", notes="Raised stream banks")
        _g("stepping_stone", "TRIM_FLAGSTONE", "M_Trim_Flagstone", notes="Bridge landing stepping stones")
    elif at == "GB_ZEN_SANDO":
        _g("paving", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Shrine approach paving")
        _g("edge_stone", "TRIM_EDGE", "M_Trim_Edge", notes="Path border stones")
        _g("toro_post", "TRIM_COLUMN", "M_Trim_Column", notes="Stone lantern posts along sando")
        _g("toro_base", "TRIM_FLAGSTONE", "M_Trim_Flagstone", notes="Lantern plinth bases")
    elif at == "GB_ZEN_KAIRO":
        _g("floor", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Cloister walkway slab")
        _g("column", "TRIM_COLUMN", "M_Trim_Column", notes="Courtyard-facing column row")
        _g("beam", "TRIM_BEAM", "M_Trim_Beam", notes="Horizontal tie beam")
        _g("noki_eave", "TRIM_EAVE", "M_Trim_Eave", notes="Roof eave overhang volume")
        _g("wall_panel", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Garden-side low wall")
    elif at == "GB_ZEN_HAIDEN":
        _g("haijo_floor", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Raised worship floor")
        _g("genkan_step", "TRIM_STEP", "M_Trim_Step", notes="Entry genkan steps")
        _g("post", "TRIM_COLUMN", "M_Trim_Column", notes="Haiden corner and front posts")
        _g("ranma", "TRIM_PANEL_RECESS", "M_Trim_Ranma", notes="Transom panel above threshold")
        _g("noki", "TRIM_EAVE", "M_Trim_Eave", notes="Roof eave overhang")
    elif at == "GB_ZEN_GOJU_PAGODA":
        _g("plinth", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Stone plinth base")
        _g("tier_core", "TRIM_COLUMN", "M_Trim_Column", notes="Pagoda story core volume")
        _g("tier_roof", "TRIM_EAVE", "M_Trim_Eave", notes="Flared eave slab per tier")
        _g("sorin", "TRIM_SPIRE", "M_Trim_Sorin", notes="Finial spire (sōrin)")
    elif at == "GB_ZEN_TAHOTO":
        _g("plinth", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Stone plinth")
        _g("mokoshi_base", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Square mokoshi skirt story")
        _g("drum_body", "TRIM_COLUMN", "M_Trim_Column", notes="Round drum body (greybox)")
        _g("roof_lower", "TRIM_EAVE", "M_Trim_Eave", notes="Lower roof slab")
        _g("roof_upper", "TRIM_EAVE", "M_Trim_Eave", notes="Upper roof slab")
        _g("sorin", "TRIM_SPIRE", "M_Trim_Sorin", notes="Finial spire")
    elif at == "GB_ZEN_HONDEN":
        _g("sanctum_floor", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Raised sacred platform")
        _g("sanctuary_wall", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Enclosed moya walls")
        _g("engawa_margin", "TRIM_FLOOR", "M_Trim_Engawa", notes="Veranda margin strip")
        _g("threshold", "TRIM_FRAME", "M_Trim_Frame", notes="Entry threshold from haiden")
        _g("noki_eave", "TRIM_EAVE", "M_Trim_Eave", notes="Deep roof eave")
    elif at == "GB_ZEN_LANTERN":
        _g("kiso", "TRIM_FLOOR", "M_Trim_Floor", snap_bind="floor", notes="Stone plinth base")
        _g("sao", "TRIM_COLUMN", "M_Trim_Column", notes="Lantern shaft post")
        _g("hibukuro", "TRIM_PANEL_RECESS", "M_Trim_Panel_Recess", notes="Fire chamber body")
        _g("kasa", "TRIM_EAVE", "M_Trim_Eave", notes="Roof cap slab")
        _g("hoju", "TRIM_SPIRE", "M_Trim_Sorin", notes="Jewel finial")
    elif at in ("GB_GOTHIC_PORTAL", "GB_GOTHIC_BAY", "GB_CORRIDOR_DOOR_END"):
        _g("door_frame", "TRIM_FRAME", "M_Trim_Frame", snap_bind="door")
        if at == "GB_GOTHIC_BAY":
            _g("window_reveal", "TRIM_REVEAL", "M_Trim_Window")
    elif at.startswith("GREYBOX_") or at.startswith("GB_"):
        if getattr(props, "gb_frame", False) or at in ("GREYBOX_DOORWAY", "GB_CORRIDOR_DOOR_END"):
            _g("door_frame", "TRIM_FRAME", "M_Trim_Frame")
        if getattr(props, "gb_wainscot_height", 0) > 0.01:
            _g("wainscot", "TRIM_WAINSCOT", "M_Trim_Wainscot")
        if getattr(props, "gb_baseboard_height", 0) > 0.01:
            _g("baseboard", "TRIM_BASEBOARD", "M_Trim_Baseboard")

    return groups


def attach_trim_metadata(obj, props, monolith=None):
    groups = build_trim_groups(props, monolith)
    if groups:
        obj["surreal_trim_groups"] = json.dumps(groups)
    elif "surreal_trim_groups" in obj:
        del obj["surreal_trim_groups"]


_SNAP_TYPE_ALIASES = {
    "TRACERY": "TRACERY",
    "ARCH": "ARCH",
    "BUTTRESS": "BUTTRESS",
    "DOOR": "DOOR",
    "WALL": "WALL",
    "FLOOR": "FLOOR",
    "CORNER": "CORNER",
    "GRID": "GRID",
}


def normalize_snap_points(snaps):
    """Normalize snap contract for UE importers (type + rule defaults)."""
    out = []
    for pt in snaps or []:
        st = str(pt.get("type", "WALL")).upper()
        st = _SNAP_TYPE_ALIASES.get(st, st)
        rule = str(pt.get("rule", "OPTIONAL")).upper()
        if rule not in ("OPTIONAL", "MUST_CONNECT"):
            rule = "OPTIONAL"
        out.append({**pt, "type": st, "rule": rule})
    return out


def write_sidecar_json(obj, monolith, fbx_path):
    """Write `<fbx>.snap.json` sidecar next to exported FBX."""
    import os
    base, _ = os.path.splitext(fbx_path)
    path = base + ".snap.json"
    payload = build_ue_export_payload(obj, monolith)
    payload["snap_points"] = normalize_snap_points(payload.get("snap_points"))
    payload["fbx_path"] = fbx_path
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def build_ue_export_payload(obj, monolith):
    props = obj.surreal_arch_props
    raw = obj.get("surreal_snap_points")
    snaps = json.loads(raw) if isinstance(raw, str) else (raw or [])
    raw_trim = obj.get("surreal_trim_groups")
    if raw_trim:
        trim_groups = json.loads(raw_trim) if isinstance(raw_trim, str) else raw_trim
    else:
        trim_groups = build_trim_groups(props, monolith)
    ver = monolith.bl_info.get("version", (0, 0, 0))
    gn_trim_faces = 0
    try:
        from .trim_color_bake import count_eval_trim_zone_faces
        gn_trim_faces = count_eval_trim_zone_faces(obj)
    except Exception:
        pass
    payload = {
        "format": "surreal_arch_ue_snap_v1",
        "addon_version": f"{ver[0]}.{ver[1]}.{ver[2]}",
        "object": obj.name,
        "arch_type": props.arch_type,
        "module_id": obj.name,
        "material_choice": getattr(props, "material_choice", "STONE"),
        "trim_mode": getattr(props, "gb_trim_mode", "NONE"),
        "unit_size": float(getattr(props, "unit_size", 2.0)),
        "snap_points": normalize_snap_points(snaps),
        "trim_groups": trim_groups,
        "ue_export_hints": {
            "assign_trim_by": "vertex_color:SURREAL_TRIM_or_material_slot",
            "recommended_slots": [g["ue_material_slot"] for g in trim_groups],
            "manifold": True,
        },
    }
    if gn_trim_faces > 0:
        payload["gn_trim_zone_faces"] = gn_trim_faces
    trim_layer = obj.get("surreal_trim_color_layer")
    if trim_layer:
        payload["trim_color_layer"] = trim_layer
        payload["ue_export_hints"]["trim_color_layer"] = trim_layer
        if trim_layer == "SURREAL_TRIM":
            payload["trim_bake_mode"] = "per_face_zones"
            payload["ue_export_hints"]["assign_trim_by"] = "vertex_color:SURREAL_TRIM"
    return payload
