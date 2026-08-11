"""Extended verify for Surreal Architecture v2.75 — kits, bridges, polyhedra, zen expansion.

Launch with --factory-startup for reliable headless runs:
  blender --background --factory-startup --python deploy/_mcp_verify_overhaul.py
"""
import json
import bpy

print("=== SURREAL OVERHAUL VERIFY v2.75 ===")
print("Blender", bpy.app.version_string)

if "surreal_architecture_gen" not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module="surreal_architecture_gen")

import surreal_architecture_gen as s
import importlib
importlib.reload(s)

print("Version:", s.bl_info.get("version"))

# The addon’s register() patches the monolith, but importlib.reload(s) replaces
# those monkey-patches. Re-apply kit/snap/trim hooks for accurate verification.
try:
    import surreal_arch.integration as _integration
    importlib.reload(_integration)
except Exception as e:
    print(f"Integration reload skipped: {e}")

try:
    s.unregister()
except Exception:
    pass
s.register()

obj = bpy.data.objects.new("_VerifyProps", bpy.data.meshes.new("_VerifyMesh"))
print("Search on object props:", hasattr(obj, "surreal_arch_props"))
if hasattr(obj, "surreal_arch_props"):
    print("  arch_search_query:", hasattr(obj.surreal_arch_props, "arch_search_query"))

KIT_TESTS = [
    ("GREYBOX_CORRIDOR", {}),
    ("GB_GOTHIC_PORTAL", {"gb_door_width": 1.4, "gb_door_height": 2.6}),
    ("GB_GOTHIC_BAY", {"gothic_width": 2.4, "gb_windows_enabled": True}),
    ("GB_GOTHIC_BUTTRESS", {"gb_height": 5.0}),
    ("GB_GOTHIC_TRACERY_PANEL", {"gothic_width": 1.8}),
    ("GB_CORRIDOR_OFFSET", {"gb_length": 6.0, "gb_trim_mode": "RECESS", "gb_baseboard_height": 0.12}),
    ("GB_ROMANESQUE_ARCADE", {"gb_width": 3.2, "gb_height": 4.2}),
    ("GB_ROMANESQUE_APSE", {"gb_width": 4.0, "gb_depth": 3.5, "gb_height": 4.5, "gb_trim_mode": "RECESS"}),
    ("GB_BRUTALIST_PANEL_WALL", {"gb_length": 6.0, "gb_height": 3.5, "gb_trim_mode": "RECESS"}),
    ("GB_VENETIAN_LOGGIA", {"gothic_width": 2.8, "gb_height": 4.0}),
    ("GB_SCIFI_PRESSURE_DOOR", {"gb_length": 3.5, "gb_door_width": 1.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ROJI_STEP", {"gb_length": 4.5, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TORII_GATE", {"torii_width": 3.6, "torii_height": 4.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TSUKUBAI", {"gb_width": 1.6, "gb_depth": 1.6, "gb_height": 0.45, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_ENGAWA", {"gb_width": 5.0, "gb_depth": 2.4, "gb_height": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_BAMBOO_FENCE", {"gb_length": 4.0, "zen_fence_height": 1.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TOBIISHI", {"gb_length": 5.0, "gb_width": 1.6, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_KARESANSUI", {"gb_width": 8.0, "gb_depth": 6.0, "gb_trim_mode": "RECESS", "gb_trim_recess": 0.03}),
    ("GB_ZEN_MACHIAI", {"gb_width": 3.2, "gb_depth": 2.4, "gb_height": 2.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_STONE_BRIDGE", {"zen_bridge_span": 5.0, "zen_bridge_rise": 0.55, "gb_width": 1.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_CHERRY_ALLEE", {"gb_length": 6.0, "gb_width": 2.6, "gb_height": 0.32, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_WATER_EDGE", {"gb_length": 2.8, "gb_width": 2.4, "zen_stream_depth": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_SANDO", {"gb_length": 8.0, "gb_width": 2.2, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_KAIRO", {"gb_length": 6.0, "gb_width": 2.4, "gb_height": 2.8, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_HAIDEN", {"gb_width": 5.0, "gb_depth": 4.0, "gb_height": 3.2, "zen_genkan_rise": 0.45, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_GOJU_PAGODA", {"pagoda_tiers": 5, "pagoda_base_radius": 2.0, "pagoda_tier_height": 1.2, "pagoda_taper": 0.82, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_SAKURA_TORII", {"torii_width": 3.4, "torii_height": 4.0, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_TAHOTO", {"gb_width": 3.2, "gb_height": 6.5, "zen_tahoto_roof_span": 0.35, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_HONDEN", {"gb_width": 5.5, "gb_depth": 4.5, "gb_height": 3.6, "zen_honden_platform_rise": 0.55, "gb_trim_mode": "RECESS"}),
    ("GB_ZEN_LANTERN", {"zen_lantern_height": 1.6, "zen_lantern_style": "KASUGA", "gb_trim_mode": "RECESS"}),
]

print("\n--- Kit smoke ---")
all_ok = True
if not getattr(s, "_surreal_patched", False):
    print("  !! FAIL: monolith patch (_surreal_patched) not applied")
    all_ok = False
else:
    print("  patch_applied: OK")
for atype, overrides in KIT_TESTS:
    mesh = bpy.data.meshes.new("VerifyMesh")
    obj = bpy.data.objects.new(f"Verify_{atype}", mesh)
    bpy.context.collection.objects.link(obj)
    p = obj.surreal_arch_props
    p.arch_type = atype
    for k, v in overrides.items():
        setattr(p, k, v)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.surreal_arch.generate()
    snaps = json.loads(obj.get("surreal_snap_points", "[]")) if obj.get("surreal_snap_points") else []
    trim = json.loads(obj.get("surreal_trim_groups", "[]")) if obj.get("surreal_trim_groups") else []
    print(f"  {atype}: snaps={len(snaps)} trim_groups={len(trim)}")
    if atype.startswith(("GB_", "GREYBOX_")) and len(snaps) == 0:
        print(f"  !! FAIL: {atype} wrote 0 snap points")
        all_ok = False
    if atype.startswith("GB_") and atype in ("GB_CORRIDOR_OFFSET", "GB_ROMANESQUE_APSE", "GB_SCIFI_PRESSURE_DOOR", "GB_ZEN_ROJI_STEP", "GB_ZEN_TORII_GATE", "GB_ZEN_TSUKUBAI", "GB_ZEN_ENGAWA", "GB_ZEN_BAMBOO_FENCE", "GB_ZEN_TOBIISHI", "GB_ZEN_KARESANSUI", "GB_ZEN_MACHIAI", "GB_ZEN_STONE_BRIDGE", "GB_ZEN_CHERRY_ALLEE", "GB_ZEN_WATER_EDGE", "GB_ZEN_SANDO", "GB_ZEN_KAIRO", "GB_ZEN_HAIDEN", "GB_ZEN_GOJU_PAGODA", "GB_ZEN_SAKURA_TORII", "GB_ZEN_TAHOTO", "GB_ZEN_HONDEN", "GB_ZEN_LANTERN") and len(trim) == 0:
        print(f"  !! FAIL: {atype} wrote 0 trim_groups")
        all_ok = False

print("\n--- Graph spawners ---")
from surreal_arch.greybox_graph import GRAPH_REGISTRY
for gid in GRAPH_REGISTRY:
    op_name = f"surreal_arch.spawn_graph_{gid.lower()}"
    has_op = hasattr(bpy.ops.surreal_arch, f"spawn_graph_{gid.lower()}")
    print(f"  {gid}: operator={has_op}")

print("\n--- UV modifiers (Tier B) ---")
for op_id in (
    "uv_create_edit_proxy",
    "uv_commit_from_proxy",
    "uv_invoke_miouv",
    "uv_invoke_uvpackmaster",
):
    has_op = hasattr(bpy.ops.surreal_arch, op_id)
    print(f"  {op_id}: operator={has_op}")
    if not has_op:
        all_ok = False
try:
    from surreal_arch.capabilities import is_available
    from surreal_arch.pipeline import uv_pack_hint

    print(f"  miouv_detect: {is_available('miouv')}")
    print(f"  uvpackmaster_detect: {is_available('uvpackmaster')}")
    hint = uv_pack_hint(obj.surreal_arch_props) if hasattr(obj, "surreal_arch_props") else None
    print(f"  uv_pack_hint_trim: {hint is not None}")
except Exception as e:
    print(f"  uv modifier probe skipped: {e}")

print("\n--- Research presets ---")
from surreal_arch.research_presets import RESEARCH_PRESETS
for key in RESEARCH_PRESETS:
    op_id = f"preset_research_{key}"
    print(f"  {key}: {hasattr(bpy.ops.surreal_arch, op_id)}")

print("\n--- Trim zone GN ---")
try:
    import surreal_arch.snap_export as _snap_export
    import surreal_arch.trim_color_bake as _trim_color_bake
    importlib.reload(_trim_color_bake)
    importlib.reload(_snap_export)
    from surreal_arch.trim_color_bake import count_eval_trim_zone_faces, resolve_trim_zone
    from surreal_arch.snap_export import build_ue_export_payload

    mesh = bpy.data.meshes.new("TrimZoneMesh")
    obj = bpy.data.objects.new("Verify_TrimZone", mesh)
    bpy.context.collection.objects.link(obj)
    p = obj.surreal_arch_props
    p.arch_type = "GB_BRUTALIST_PANEL_WALL"
    p.gb_trim_mode = "RECESS"
    p.gb_length = 6.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.surreal_arch.generate()
    n_trim_faces = count_eval_trim_zone_faces(obj)
    print(f"  brutalist_recess trim_zone_faces={n_trim_faces}")
    if n_trim_faces < 2:
        print("  !! FAIL: expected trim-labelled faces with surreal_trim_zone > 0")
        all_ok = False
    payload = build_ue_export_payload(obj, s)
    if payload.get("gn_trim_zone_faces", 0) < 2:
        print("  !! FAIL: export payload missing gn_trim_zone_faces")
        all_ok = False
    z_gasket = resolve_trim_zone(s, "trim:gasket_ring", p)
    z_body = resolve_trim_zone(s, "level", p)
    print(f"  resolve_trim_zone gasket={z_gasket} body={z_body}")
    if z_gasket is None or float(z_gasket) < 1:
        print("  !! FAIL: trim:gasket_ring did not resolve to zone id")
        all_ok = False
    if z_body is not None:
        print("  !! FAIL: non-trim label should not assign trim zone")
        all_ok = False
except Exception as e:
    print(f"  trim_zone_gn error: {e}")
    all_ok = False

print("\n--- Trim bake ---")
try:
    import surreal_arch.trim_color_bake as _trim_color_bake
    import surreal_arch.trim_bake as _trim_bake
    importlib.reload(_trim_color_bake)
    importlib.reload(_trim_bake)
    from surreal_arch.trim_bake import apply_trim_bake, TRIM_COLOR_MAP
    mesh = bpy.data.meshes.new("TrimBakeMesh")
    obj = bpy.data.objects.new("Verify_TrimBake", mesh)
    bpy.context.collection.objects.link(obj)
    p = obj.surreal_arch_props
    p.arch_type = "GB_SCIFI_PRESSURE_DOOR"
    p.gb_trim_mode = "RECESS"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.surreal_arch.generate()
    ok = apply_trim_bake(obj, p, s)
    print(f"  apply_trim_bake: {ok} map_size={len(TRIM_COLOR_MAP)}")
    p.gb_bake_trim_colors = True
    ok_zone = apply_trim_bake(obj, p, s)
    has_layer = "SURREAL_TRIM" in obj.data.color_attributes
    print(f"  apply_trim_bake_zones: {ok_zone} layer={has_layer}")
    if not ok_zone or not has_layer:
        print("  !! FAIL: gb_bake_trim_colors did not write SURREAL_TRIM layer")
        all_ok = False
except Exception as e:
    print(f"  trim_bake error: {e}")
    all_ok = False

print("\n--- ARCH_CATALOG ---")
try:
    from surreal_arch.catalog import build_catalog
    cat = build_catalog(s)
    n = len([k for k in cat if not k.startswith("_")])
    print(f"  entries: {n}")
except Exception as e:
    print(f"  catalog error: {e}")

print("\n--- Catalog enum ---")
try:
    from surreal_arch.catalog_enum import generate_enum_items, format_enum_stub, sync_catalog_enum_cache

    enum_count = sync_catalog_enum_cache(s)
    items = generate_enum_items(s)
    ids = {row[0] for row in items}
    print(f"  enum_items: {enum_count}")
    missing = [aid for aid, _ in KIT_TESTS if aid.startswith("GB_") and aid not in ids]
    if missing:
        print(f"  !! FAIL: catalog enum missing kit ids: {missing}")
        all_ok = False
    stub = format_enum_stub(s)
    assert "CATALOG_ARCH_TYPE_ITEMS" in stub
    assert stub.count('("GB_SCIFI_PRESSURE_DOOR"') == 1
    print("  catalog_enum: OK")
except Exception as e:
    print(f"  catalog_enum error: {e}")
    all_ok = False

print("\n--- Catalog dispatch ---")
try:
    from surreal_arch.catalog_dispatch import catalog_dispatch_summary

    summary = catalog_dispatch_summary(s)
    kit_keys = set(getattr(s, "_KIT_DISPATCH", {}).keys())
    dispatch_keys = set(getattr(s, "_CATALOG_DISPATCH", {}).keys())
    print(f"  dispatch_entries: {summary['dispatch_entries']} param_stubs: {summary['param_stubs']}")
    missing_dispatch = [aid for aid, _ in KIT_TESTS if aid.startswith("GB_") and aid not in dispatch_keys]
    if missing_dispatch:
        print(f"  !! FAIL: catalog dispatch missing kit ids: {missing_dispatch}")
        all_ok = False
    if not kit_keys.issubset(dispatch_keys):
        extra = kit_keys - dispatch_keys
        print(f"  !! FAIL: _KIT_DISPATCH not mirrored in _CATALOG_DISPATCH: {sorted(extra)}")
        all_ok = False
    for aid in sorted(kit_keys):
        attr = s._CATALOG_DISPATCH.get(aid)
        if attr and not hasattr(s, attr):
            print(f"  !! FAIL: dispatch {aid} -> missing builder {attr}")
            all_ok = False
    print("  catalog_dispatch: OK")
except Exception as e:
    print(f"  catalog_dispatch error: {e}")
    all_ok = False

print("\n--- surreal_greybox extract ---")
try:
    import surreal_greybox

    required = ("_gb_box", "_gb_join", "_gb_bool_diff", "_gb_load_snap_points", "_gb_snap_point")
    missing = [name for name in required if not hasattr(s, name)]
    print(f"  bound_helpers: {len(required) - len(missing)}/{len(required)}")
    if missing:
        print(f"  !! FAIL: monolith missing greybox bindings: {missing}")
        all_ok = False
    else:
        print("  surreal_greybox: OK")
except Exception as e:
    print(f"  surreal_greybox error: {e}")
    all_ok = False

print("\n--- Workflow modes ---")
try:
    from surreal_arch.ui import workflow_allows_panel, workflow_allows_style

    class _WF:
        ui_workflow_mode = "BLOCKOUT"

    blockout = _WF()
    assert workflow_allows_panel("level_design", blockout)
    assert not workflow_allows_panel("music", blockout)
    assert not workflow_allows_panel("sverchok", blockout)
    assert workflow_allows_style("GREYBOX", "BLOCKOUT")
    assert not workflow_allows_style("GOTHIC", "BLOCKOUT")

    arch = _WF()
    arch.ui_workflow_mode = "ARCHITECTURE"
    assert not workflow_allows_panel("level_design", arch)
    assert not workflow_allows_panel("style_greybox", arch)
    assert workflow_allows_style("GOTHIC", "ARCHITECTURE")
    print("  workflow_modes: OK")
except Exception as e:
    print(f"  workflow_modes error: {e}")
    all_ok = False

print("\n--- Kit registration ---")
print("  _KIT_DISPATCH:", list(getattr(s, "_KIT_DISPATCH", {}).keys()))

print("\n--- Kit snap hooks ---")
try:
    for aid, overrides in KIT_TESTS:
        if not aid.startswith("GB_"):
            continue
        mesh = bpy.data.meshes.new("SnapHookMesh")
        obj = bpy.data.objects.new(f"SnapHook_{aid}", mesh)
        bpy.context.collection.objects.link(obj)
        p = obj.surreal_arch_props
        p.arch_type = aid
        for k, v in overrides.items():
            setattr(p, k, v)
        pts = s._gb_compute_snap_points(p)
        print(f"  {aid}: hook_snaps={len(pts)}")
        if len(pts) == 0:
            print(f"  !! FAIL: {aid} snap hook returned 0 points")
            all_ok = False
    print("  kit_snap_hooks: OK")
except Exception as e:
    print(f"  kit_snap_hooks error: {e}")
    all_ok = False

print("\n--- Pipeline operators ---")
PIPELINE_OPS = (
    "export_ue5",
    "export_snap_json",
    "bake_trim_attributes",
    "bake_beavel",
    "spawn_polyhedron",
    "export_catalog_enum",
    "validate_assembly",
    "toggle_snap_overlay",
    "publish_greybox_assets",
)
for op_id in PIPELINE_OPS:
    ok = hasattr(bpy.ops.surreal_arch, op_id)
    print(f"  {op_id}: {ok}")
    if not ok:
        all_ok = False

print("\n--- Optional dependency bridges ---")
try:
    import surreal_arch.capabilities as _cap
    import surreal_arch.polyhedra as _poly
    import surreal_arch.higgsas_bridge as _higg
    importlib.reload(_cap)
    importlib.reload(_poly)
    importlib.reload(_higg)
    from surreal_arch.capabilities import is_available
    from surreal_arch.polyhedra import POLYHEDRA_REGISTRY

    print(f"  beavel: {is_available('beavel')}")
    print(f"  synthia: {is_available('synthia')} (skip spawn if missing)")
    print(f"  higgsas: {is_available('higgsas')}")
    if is_available("higgsas"):
        ng = _higg.load_node("NTBricks Grid")
        print(f"  higgsas NTBricks Grid: {ng is not None}")
        if ng is None:
            print("  higgsas NTBricks Grid: WARN (library on disk but group not loaded in factory-startup)")
    else:
        print("  higgsas: SKIP (library not on disk)")

    for key, meta in POLYHEDRA_REGISTRY.items():
        mesh = meta["build"](1.0)
        nv = len(mesh.vertices)
        np = len(mesh.polygons)
        ok_poly = nv >= 4 and np > 0
        print(f"  polyhedron {key}: verts={nv} faces={np}")
        if not ok_poly:
            print(f"  !! FAIL: polyhedron {key} invalid mesh")
            all_ok = False
        bpy.data.meshes.remove(mesh)

    print("\n--- Synthia arch types (fallback mesh) ---")
    from surreal_arch.synthia_bridge import SYNTHIA_ARCH_MAP
    for arch_id in SYNTHIA_ARCH_MAP:
        mesh = bpy.data.meshes.new(f"Verify_{arch_id}")
        obj = bpy.data.objects.new(f"Verify_{arch_id}", mesh)
        bpy.context.collection.objects.link(obj)
        p = obj.surreal_arch_props
        p.arch_type = arch_id
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.surreal_arch.generate()
        nv = len(obj.data.vertices) if obj.data else 0
        print(f"  {arch_id}: verts={nv} tag={obj.get('surreal_synthia_source', '')}")
        if nv < 4:
            print(f"  !! FAIL: {arch_id} produced empty mesh")
            all_ok = False
    print("  bridges: OK")
except Exception as e:
    print(f"  bridges error: {e}")
    all_ok = False

print("\n--- Export contract ---")
try:
    import surreal_arch.snap_export as _snap_export
    importlib.reload(_snap_export)
    from surreal_arch.snap_export import build_ue_export_payload, normalize_snap_points, write_sidecar_json
    import tempfile, os
    mesh = bpy.data.meshes.new("ExportMesh")
    obj = bpy.data.objects.new("Verify_Export", mesh)
    bpy.context.collection.objects.link(obj)
    p = obj.surreal_arch_props
    p.arch_type = "GB_SCIFI_PRESSURE_DOOR"
    p.gb_trim_mode = "RECESS"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.surreal_arch.generate()
    payload = build_ue_export_payload(obj, s)
    assert payload.get("format") == "surreal_arch_ue_snap_v1"
    snaps = payload.get("snap_points", [])
    assert all(str(pt.get("rule", "")).isupper() for pt in snaps)
    assert payload.get("gn_trim_zone_faces", 0) > 0, "RECESS export missing gn_trim_zone_faces"
    norm = normalize_snap_points([{"type": "door", "rule": "must_connect", "id": "x"}])
    assert norm[0]["type"] == "DOOR" and norm[0]["rule"] == "MUST_CONNECT"
    with tempfile.TemporaryDirectory() as td:
        fbx = os.path.join(td, "test_ue5.fbx")
        open(fbx, "w").write("stub")
        sidecar = write_sidecar_json(obj, s, fbx)
        assert os.path.isfile(sidecar)
        with open(sidecar, encoding="utf-8") as f:
            side = json.load(f)
        assert side.get("gn_trim_zone_faces", 0) > 0
    p.gb_bake_trim_colors = True
    from surreal_arch.trim_bake import apply_trim_bake
    apply_trim_bake(obj, p, s)
    payload_zones = build_ue_export_payload(obj, s)
    assert payload_zones.get("trim_color_layer") == "SURREAL_TRIM"
    assert payload_zones.get("trim_bake_mode") == "per_face_zones"
    print("  export_contract: OK")
except Exception as e:
    print(f"  export_contract error: {e}")
    all_ok = False

if not all_ok:
    raise RuntimeError("Verify failed: one or more GB_/GREYBOX_ modules produced no snaps/trim metadata")

print("=== DONE ===")
