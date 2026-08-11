"""Extended verify for Surreal Architecture procedural world pipeline (v2.68).

Launch with --factory-startup for reliable headless runs (~6s vs 10+ min hang):
  blender --background --factory-startup --python deploy/_mcp_verify_world.py
"""
import importlib
import json
import os
import sys
import tempfile

import bpy

print("=== SURREAL WORLD VERIFY v2.69 ===")
print("Blender", bpy.app.version_string)

DEPLOY = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "5.1", "scripts", "addons")
for p in (DEPLOY, LIVE):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

if "surreal_architecture_gen" in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_disable(module="surreal_architecture_gen")

import surreal_architecture_gen as s

importlib.reload(s)
if not hasattr(bpy.types.Object, "surreal_arch_props"):
    s.register()

try:
    import surreal_arch.integration as _integration

    importlib.reload(_integration)
    _integration.patch_monolith(s)
except Exception as e:
    print(f"Patch monolith skipped: {e}")

from surreal_world import compose, export, library, plans, verify_hooks

all_ok = True
export_root = None
city_export_root = None
asian_recursive_export_root = None
brutalist_export_root = None
castle_root = None
art_nouveau_export_root = None
art_deco_export_root = None
moorish_export_root = None
renaissance_export_root = None
byzantine_export_root = None
baroque_export_root = None
venetian_export_root = None
romanesque_cloister_export_root = None
romanesque_apse_export_root = None
gothic_export_root = None
gothic_chapter_export_root = None
gothic_nave_crossing_export_root = None
scifi_deck_export_root = None
scifi_airlock_export_root = None
scifi_industrial_export_root = None
zen_pagoda_export_root = None

print("\n--- Library init ---")
try:
    stats = library.ensure_verify_library(s)
    n = library.library_piece_count(stats["collection"])
    need = len(library.VERIFY_LIBRARY_TYPES)
    present = sum(1 for at in library.VERIFY_LIBRARY_TYPES if bpy.data.objects.get(f"_lib_{at}"))
    print(f"  verify_set: {present}/{need} baked={stats['baked']} failed={stats['failed']}")
    if stats["failures"]:
        print(f"  failures: {stats['failures']}")
    if present < need - 1:
        print(f"  !! FAIL: verify library set incomplete ({present}/{need})")
        all_ok = False
except Exception as e:
    print(f"  library_init error: {e}")
    all_ok = False

print("\n--- Castle plan ---")
try:
    plan = plans.spawn_castle_plan(location=(0, 0, 0), size=12.0)
    me = plan.data
    vg = [g.name for g in plan.vertex_groups]
    print(f"  faces={len(me.polygons)} verts={len(me.vertices)} groups={vg}")
    if len(me.polygons) < 5 or "is_gate" not in vg:
        print("  !! FAIL: castle plan topology")
        all_ok = False
except Exception as e:
    print(f"  castle plan error: {e}")
    all_ok = False

print("\n--- Compose COLLECTION ---")
try:
    from surreal_os import genome as os_genome
    library.init_library(s, types_only={"GB_GOTHIC_PORTAL", "GREYBOX_CORRIDOR"})
    s._active_style_genome = os_genome.load_genome("western_castle_v1")
    bpy.context.view_layer.objects.active = plan
    plan.select_set(True)
    root, msg = compose.compose_world(s, bpy.context, plan, "WESTERN_CASTLE", 0.8, "COLLECTION")
    s._active_style_genome = None
    castle_root = root
    print(f"  {msg}")
    inst_count = root.get("surreal_instance_count", 0) if root else 0
    print(f"  instance_count={inst_count}")
    if root is None or inst_count < 3:
        print("  !! FAIL: compose produced too few instances")
        all_ok = False
    if root and root.get("surreal_compose_mode") != "COLLECTION":
        print("  !! FAIL: expected COLLECTION mode")
        all_ok = False
except Exception as e:
    print(f"  compose error: {e}")
    all_ok = False

print("\n--- LD compose metrics (castle) ---")
try:
    metrics = verify_hooks.compose_metrics(castle_root)
    ld_fails = verify_hooks.check_castle_ld_metrics(castle_root)
    print(f"  metrics: {metrics}")
    if ld_fails:
        print(f"  !! FAIL: {ld_fails}")
        all_ok = False
    else:
        print("  ld_castle: OK")
except Exception as e:
    print(f"  ld metrics error: {e}")
    all_ok = False

print("\n--- Recompose idempotency ---")
try:
    before = root.get("surreal_instance_count", 0) if root else 0
    root2, msg2 = compose.recompose_world(s, bpy.context, root)
    after = root2.get("surreal_instance_count", 0) if root2 else 0
    print(f"  before={before} after={after} msg={msg2}")
    if abs(before - after) > 2:
        print("  !! FAIL: recompose instance count drift")
        all_ok = False
    export_root = root2
    castle_root = root2
except Exception as e:
    print(f"  recompose error: {e}")
    all_ok = False

print("\n--- Sacred tag dispatch ---")
try:
    zen = plans.spawn_zen_roji_plan(location=(20, 0, 0))
    zroot, zmsg = compose.compose_world(s, bpy.context, zen, "ZEN_SHRINE", 0.9, "COLLECTION")
    sacred_n = verify_hooks.compose_metrics(zroot).get("sacred", 0) if zroot else 0
    if zroot:
        export_root = zroot
    zen_fails = verify_hooks.check_zen_ld_metrics(zroot)
    print(f"  zen_compose: {zmsg} sacred_instances={sacred_n}")
    if sacred_n < 1 or zen_fails:
        print(f"  !! FAIL: zen LD {zen_fails}")
        all_ok = False
    else:
        print("  ld_zen: OK")
except Exception as e:
    print(f"  sacred tag error: {e}")
    all_ok = False

print("\n--- Zen temple plan compose ---")
try:
    temple = plans.spawn_zen_temple_plan(location=(25, 0, 0))
    troot, tmsg = compose.compose_world(s, bpy.context, temple, "ZEN_SHRINE", 0.9, "COLLECTION")
    tfails = verify_hooks.check_zen_temple_ld_metrics(troot)
    print(f"  temple_compose: {tmsg} metrics={verify_hooks.compose_metrics(troot)}")
    if tfails:
        print(f"  !! FAIL: temple LD {tfails}")
        all_ok = False
    else:
        print("  ld_temple: OK")
except Exception as e:
    print(f"  temple compose error: {e}")
    all_ok = False

print("\n--- Village plan compose ---")
try:
    village = plans.spawn_village_plan(location=(40, 0, 0))
    vroot, vmsg = compose.compose_world(s, bpy.context, village, "WESTERN_VILLAGE", 0.85, "COLLECTION")
    vfails = verify_hooks.check_village_ld_metrics(vroot)
    print(f"  village_compose: {vmsg} metrics={verify_hooks.compose_metrics(vroot)}")
    if vfails:
        print(f"  !! FAIL: village LD {vfails}")
        all_ok = False
    else:
        print("  ld_village: OK")
except Exception as e:
    print(f"  village compose error: {e}")
    all_ok = False

print("\n--- Art Nouveau plan compose ---")
try:
    from surreal_os import genome as os_genome
    art_plan = plans.spawn_village_plan(location=(100, 0, 0))
    s._active_style_genome = os_genome.load_genome("art_nouveau_v1")
    aroot, amsg = compose.compose_world(s, bpy.context, art_plan, "ART_NOUVEAU", 0.85, "COLLECTION")
    art_nouveau_export_root = aroot
    s._active_style_genome = None
    print(f"  art_nouveau_compose: {amsg} metrics={verify_hooks.compose_metrics(aroot)}")
    if aroot.get("surreal_style_genome_id") != "art_nouveau_v1":
        print(f"  !! FAIL: art_nouveau genome stamp got {aroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  art_nouveau_compose: OK")
except Exception as e:
    print(f"  art_nouveau compose error: {e}")
    all_ok = False

print("\n--- Art Deco lobby plan compose ---")
try:
    from surreal_os import genome as os_genome
    library.init_library(
        s,
        types_only={
            "TESSELLATION_TOWER",
            "GB_BRUTALIST_PANEL_WALL",
            "FILIGREE_PANEL",
            "CUSPED_ARCH",
            "OBELISK",
        },
    )
    deco_plan = plans.spawn_village_plan(location=(110, 0, 0))
    s._active_style_genome = os_genome.load_genome("art_deco_lobby_v1")
    droot, dmsg = compose.compose_world(s, bpy.context, deco_plan, "ART_DECO", 0.85, "COLLECTION")
    art_deco_export_root = droot
    s._active_style_genome = None
    print(f"  art_deco_compose: {dmsg} metrics={verify_hooks.compose_metrics(droot)}")
    if droot.get("surreal_style_genome_id") != "art_deco_lobby_v1":
        print(f"  !! FAIL: art_deco genome stamp got {droot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  art_deco_compose: OK")
except Exception as e:
    print(f"  art_deco compose error: {e}")
    all_ok = False

print("\n--- Moorish courtyard plan compose ---")
try:
    from surreal_os import genome as os_genome
    moor_plan = plans.spawn_village_plan(location=(120, 0, 0))
    s._active_style_genome = os_genome.load_genome("moorish_courtyard_v1")
    mroot, mmsg = compose.compose_world(s, bpy.context, moor_plan, "MOORISH_COURTYARD", 0.85, "COLLECTION")
    moorish_export_root = mroot
    s._active_style_genome = None
    print(f"  moorish_compose: {mmsg} metrics={verify_hooks.compose_metrics(mroot)}")
    if mroot.get("surreal_style_genome_id") != "moorish_courtyard_v1":
        print(f"  !! FAIL: moorish genome stamp got {mroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  moorish_compose: OK")
except Exception as e:
    print(f"  moorish compose error: {e}")
    all_ok = False

print("\n--- Renaissance piazza plan compose ---")
try:
    from surreal_os import genome as os_genome
    ren_plan = plans.spawn_village_plan(location=(140, 0, 0))
    s._active_style_genome = os_genome.load_genome("renaissance_piazza_v1")
    rroot, rmsg = compose.compose_world(s, bpy.context, ren_plan, "RENAISSANCE_PIAZZA", 0.85, "COLLECTION")
    renaissance_export_root = rroot
    s._active_style_genome = None
    print(f"  renaissance_compose: {rmsg} metrics={verify_hooks.compose_metrics(rroot)}")
    if rroot.get("surreal_style_genome_id") != "renaissance_piazza_v1":
        print(f"  !! FAIL: renaissance genome stamp got {rroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  renaissance_compose: OK")
except Exception as e:
    print(f"  renaissance compose error: {e}")
    all_ok = False

print("\n--- Byzantine basilica plan compose ---")
try:
    from surreal_os import genome as os_genome
    byz_plan = plans.spawn_village_plan(location=(150, 0, 0))
    s._active_style_genome = os_genome.load_genome("byzantine_basilica_v1")
    bzroot, bzmsg = compose.compose_world(s, bpy.context, byz_plan, "BYZANTINE_BASILICA", 0.85, "COLLECTION")
    byzantine_export_root = bzroot
    s._active_style_genome = None
    print(f"  byzantine_compose: {bzmsg} metrics={verify_hooks.compose_metrics(bzroot)}")
    if bzroot.get("surreal_style_genome_id") != "byzantine_basilica_v1":
        print(f"  !! FAIL: byzantine genome stamp got {bzroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  byzantine_compose: OK")
except Exception as e:
    print(f"  byzantine compose error: {e}")
    all_ok = False

print("\n--- Baroque church plan compose ---")
try:
    from surreal_os import genome as os_genome
    bar_plan = plans.spawn_village_plan(location=(155, 0, 0))
    s._active_style_genome = os_genome.load_genome("baroque_church_v1")
    barroot, barmsg = compose.compose_world(s, bpy.context, bar_plan, "BAROQUE_CHURCH", 0.85, "COLLECTION")
    baroque_export_root = barroot
    s._active_style_genome = None
    print(f"  baroque_compose: {barmsg} metrics={verify_hooks.compose_metrics(barroot)}")
    if barroot.get("surreal_style_genome_id") != "baroque_church_v1":
        print(f"  !! FAIL: baroque genome stamp got {barroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  baroque_compose: OK")
except Exception as e:
    print(f"  baroque compose error: {e}")
    all_ok = False

print("\n--- Romanesque cloister plan compose ---")
try:
    from surreal_os import genome as os_genome
    rom_plan = plans.spawn_village_plan(location=(158, 0, 0))
    s._active_style_genome = os_genome.load_genome("romanesque_cloister_v1")
    romroot, rommsg = compose.compose_world(s, bpy.context, rom_plan, "ROMANESQUE_CLOISTER", 0.85, "COLLECTION")
    romanesque_cloister_export_root = romroot
    s._active_style_genome = None
    print(f"  romanesque_cloister_compose: {rommsg} metrics={verify_hooks.compose_metrics(romroot)}")
    if romroot.get("surreal_style_genome_id") != "romanesque_cloister_v1":
        print(f"  !! FAIL: romanesque cloister genome stamp got {romroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  romanesque_cloister_compose: OK")
except Exception as e:
    print(f"  romanesque cloister compose error: {e}")
    all_ok = False

print("\n--- Romanesque apse plan compose ---")
try:
    from surreal_os import genome as os_genome
    rapp_plan = plans.spawn_village_plan(location=(162, 0, 0))
    s._active_style_genome = os_genome.load_genome("romanesque_apse_v1")
    rapproot, rappmsg = compose.compose_world(s, bpy.context, rapp_plan, "ROMANESQUE_APSE", 0.85, "COLLECTION")
    romanesque_apse_export_root = rapproot
    s._active_style_genome = None
    print(f"  romanesque_apse_compose: {rappmsg} metrics={verify_hooks.compose_metrics(rapproot)}")
    if rapproot.get("surreal_style_genome_id") != "romanesque_apse_v1":
        print(f"  !! FAIL: romanesque apse genome stamp got {rapproot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  romanesque_apse_compose: OK")
except Exception as e:
    print(f"  romanesque apse compose error: {e}")
    all_ok = False

print("\n--- Venetian canal plan compose ---")
try:
    from surreal_os import genome as os_genome
    ven_plan = plans.spawn_village_plan(location=(160, 0, 0))
    s._active_style_genome = os_genome.load_genome("venetian_canal_v1")
    vroot, vmsg = compose.compose_world(s, bpy.context, ven_plan, "VENETIAN_CANAL", 0.85, "COLLECTION")
    venetian_export_root = vroot
    s._active_style_genome = None
    print(f"  venetian_compose: {vmsg} metrics={verify_hooks.compose_metrics(vroot)}")
    if vroot.get("surreal_style_genome_id") != "venetian_canal_v1":
        print(f"  !! FAIL: venetian genome stamp got {vroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  venetian_compose: OK")
except Exception as e:
    print(f"  venetian compose error: {e}")
    all_ok = False

print("\n--- Gothic cloister plan compose ---")
try:
    from surreal_os import genome as os_genome
    goth_plan = plans.spawn_village_plan(location=(180, 0, 0))
    s._active_style_genome = os_genome.load_genome("gothic_cloister_v1")
    groot, gmsg = compose.compose_world(s, bpy.context, goth_plan, "GOTHIC_CLOISTER", 0.85, "COLLECTION")
    gothic_export_root = groot
    s._active_style_genome = None
    print(f"  gothic_compose: {gmsg} metrics={verify_hooks.compose_metrics(groot)}")
    if groot.get("surreal_style_genome_id") != "gothic_cloister_v1":
        print(f"  !! FAIL: gothic genome stamp got {groot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  gothic_compose: OK")
except Exception as e:
    print(f"  gothic compose error: {e}")
    all_ok = False

print("\n--- Gothic chapter house plan compose ---")
try:
    from surreal_os import genome as os_genome
    gch_plan = plans.spawn_village_plan(location=(190, 0, 0))
    s._active_style_genome = os_genome.load_genome("gothic_chapter_house_v1")
    gchroot, gchmsg = compose.compose_world(s, bpy.context, gch_plan, "GOTHIC_CHAPTER_HOUSE", 0.85, "COLLECTION")
    gothic_chapter_export_root = gchroot
    s._active_style_genome = None
    print(f"  gothic_chapter_compose: {gchmsg} metrics={verify_hooks.compose_metrics(gchroot)}")
    if gchroot.get("surreal_style_genome_id") != "gothic_chapter_house_v1":
        print(f"  !! FAIL: gothic chapter genome stamp got {gchroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  gothic_chapter_compose: OK")
except Exception as e:
    print(f"  gothic chapter compose error: {e}")
    all_ok = False

print("\n--- Gothic nave crossing plan compose ---")
try:
    from surreal_os import genome as os_genome
    gnc_plan = plans.spawn_village_plan(location=(195, 0, 0))
    s._active_style_genome = os_genome.load_genome("gothic_nave_crossing_v1")
    gncroot, gncmsg = compose.compose_world(s, bpy.context, gnc_plan, "GOTHIC_NAVE_CROSSING", 0.85, "COLLECTION")
    gothic_nave_crossing_export_root = gncroot
    s._active_style_genome = None
    print(f"  gothic_nave_crossing_compose: {gncmsg} metrics={verify_hooks.compose_metrics(gncroot)}")
    if gncroot.get("surreal_style_genome_id") != "gothic_nave_crossing_v1":
        print(f"  !! FAIL: gothic nave crossing genome stamp got {gncroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  gothic_nave_crossing_compose: OK")
except Exception as e:
    print(f"  gothic nave crossing compose error: {e}")
    all_ok = False

print("\n--- Sci-Fi deck plan compose ---")
try:
    from surreal_os import genome as os_genome
    scifi_plan = plans.spawn_village_plan(location=(200, 0, 0))
    s._active_style_genome = os_genome.load_genome("scifi_deck_v1")
    sciroot, scimsg = compose.compose_world(s, bpy.context, scifi_plan, "SCIFI_DECK", 0.85, "COLLECTION")
    scifi_deck_export_root = sciroot
    s._active_style_genome = None
    print(f"  scifi_deck_compose: {scimsg} metrics={verify_hooks.compose_metrics(sciroot)}")
    if sciroot.get("surreal_style_genome_id") != "scifi_deck_v1":
        print(f"  !! FAIL: scifi deck genome stamp got {sciroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  scifi_deck_compose: OK")
except Exception as e:
    print(f"  scifi deck compose error: {e}")
    all_ok = False

print("\n--- Sci-Fi airlock plan compose ---")
try:
    from surreal_os import genome as os_genome
    air_plan = plans.spawn_village_plan(location=(220, 0, 0))
    s._active_style_genome = os_genome.load_genome("scifi_airlock_v1")
    aroot, amsg = compose.compose_world(s, bpy.context, air_plan, "SCIFI_DECK", 0.85, "COLLECTION")
    scifi_airlock_export_root = aroot
    s._active_style_genome = None
    print(f"  scifi_airlock_compose: {amsg} metrics={verify_hooks.compose_metrics(aroot)}")
    if aroot.get("surreal_style_genome_id") != "scifi_airlock_v1":
        print(f"  !! FAIL: scifi airlock genome stamp got {aroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  scifi_airlock_compose: OK")
except Exception as e:
    print(f"  scifi airlock compose error: {e}")
    all_ok = False

print("\n--- Sci-Fi industrial yard plan compose ---")
try:
    from surreal_os import genome as os_genome
    ind_plan = plans.spawn_village_plan(location=(240, 0, 0))
    s._active_style_genome = os_genome.load_genome("scifi_industrial_yard_v1")
    iroot, imsg = compose.compose_world(s, bpy.context, ind_plan, "SCIFI_DECK", 0.85, "COLLECTION")
    scifi_industrial_export_root = iroot
    s._active_style_genome = None
    print(f"  scifi_industrial_compose: {imsg} metrics={verify_hooks.compose_metrics(iroot)}")
    if iroot.get("surreal_style_genome_id") != "scifi_industrial_yard_v1":
        print(f"  !! FAIL: scifi industrial genome stamp got {iroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  scifi_industrial_compose: OK")
except Exception as e:
    print(f"  scifi industrial compose error: {e}")
    all_ok = False

print("\n--- Zen pagoda spire plan compose ---")
try:
    from surreal_os import genome as os_genome
    from surreal_arch.research_presets import run_research_preset
    temple = plans.spawn_zen_temple_plan(location=(200, 0, 0))
    s._active_style_genome = os_genome.load_genome("zen_pagoda_spire_v1")
    zproot, zpmsg = compose.compose_world(s, bpy.context, temple, "ZEN_SHRINE", 0.9, "COLLECTION")
    zen_pagoda_export_root = zproot
    s._active_style_genome = None
    print(f"  zen_pagoda_compose: {zpmsg} metrics={verify_hooks.compose_metrics(zproot)}")
    if zproot.get("surreal_style_genome_id") != "zen_pagoda_spire_v1":
        print(f"  !! FAIL: zen_pagoda genome stamp got {zproot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  zen_pagoda_compose: OK")
    rp = run_research_preset(bpy.context, "zen_pagoda_spire_graph", monolith=s)
    if rp.get("mode") != "graph" or rp.get("count", 0) < 5:
        print(f"  !! FAIL: zen_pagoda_spire_graph spawn: {rp}")
        all_ok = False
    else:
        print(f"  zen_pagoda_spire_graph: {rp['count']} modules")
    s._active_style_genome = None
except Exception as e:
    print(f"  zen_pagoda compose error: {e}")
    all_ok = False

print("\n--- Grid city plan compose ---")
try:
    city = plans.spawn_grid_city_plan(location=(60, 0, 0), grid=4, plot=4.0, street=1.5)
    croot, cmsg = compose.compose_world(s, bpy.context, city, "ASIAN_CITY", 0.85, "COLLECTION")
    city_export_root = croot
    cfails = verify_hooks.check_city_ld_metrics(croot)
    print(f"  city_compose: {cmsg} metrics={verify_hooks.compose_metrics(croot)}")
    if cfails:
        print(f"  !! FAIL: city LD {cfails}")
        all_ok = False
    else:
        print("  ld_city: OK")
except Exception as e:
    print(f"  city compose error: {e}")
    all_ok = False

print("\n--- Asian city recursive plan compose ---")
try:
    from surreal_os import genome as os_genome
    rec_city = plans.spawn_village_plan(location=(70, 0, 0))
    s._active_style_genome = os_genome.load_genome("asian_city_recursive_v1")
    arroot, armsg = compose.compose_world(s, bpy.context, rec_city, "ASIAN_CITY_RECURSIVE", 0.85, "COLLECTION")
    asian_recursive_export_root = arroot
    s._active_style_genome = None
    print(f"  asian_recursive_compose: {armsg} metrics={verify_hooks.compose_metrics(arroot)}")
    if arroot.get("surreal_style_genome_id") != "asian_city_recursive_v1":
        print(f"  !! FAIL: asian recursive genome stamp got {arroot.get('surreal_style_genome_id')}")
        all_ok = False
    else:
        print("  asian_recursive_compose: OK")
except Exception as e:
    print(f"  asian recursive compose error: {e}")
    all_ok = False

print("\n--- Motte/bailey plan compose ---")
try:
    from surreal_os import genome as os_genome
    library.init_library(s, types_only={"GREYBOX_PILLAR_HALL", "GB_BRUTALIST_PANEL_WALL"})
    s._active_style_genome = os_genome.load_genome("brutalist_plaza_v1")
    motte = plans.spawn_motte_bailey_plan(location=(80, 0, 0))
    mroot, mmsg = compose.compose_world(s, bpy.context, motte, "BRUTALIST_PLAZA", 0.85, "COLLECTION")
    brutalist_export_root = mroot
    s._active_style_genome = None
    mfails = verify_hooks.check_motte_ld_metrics(mroot)
    print(f"  motte_compose: {mmsg} metrics={verify_hooks.compose_metrics(mroot)}")
    if mfails:
        print(f"  !! FAIL: motte LD {mfails}")
        all_ok = False
    else:
        print("  ld_motte: OK")
except Exception as e:
    print(f"  motte compose error: {e}")
    all_ok = False

print("\n--- One-click castle (COLLECTION, Layer 2 only) ---")
try:
    result = bpy.ops.surreal_arch.one_click_castle(
        style="WESTERN_CASTLE",
        plan_size=12.0,
        with_terrain=False,
        with_vegetation=False,
        with_lighting=False,
        with_komikaze=False,
    )
    if result != {"FINISHED"}:
        raise RuntimeError(f"one_click_castle returned {result}")
    world = bpy.context.active_object
    if world is None or world.type != "EMPTY" or not world.get("surreal_composed_from"):
        raise RuntimeError(f"expected WorldRoot active object, got {world}")
    if world.get("surreal_compose_mode") != "COLLECTION":
        raise RuntimeError("one_click world not COLLECTION mode")
    oc_fails = verify_hooks.check_castle_ld_metrics(world)
    inst = world.get("surreal_instance_count", 0)
    print(f"  one_click: {world.name} instances={inst} mode=COLLECTION")
    if oc_fails:
        print(f"  !! FAIL: one_click LD {oc_fails}")
        all_ok = False
    else:
        print("  one_click_castle: OK")
except Exception as e:
    print(f"  one_click_castle error: {e}")
    all_ok = False

print("\n--- World export manifest ---")
try:
    if export_root is None:
        raise RuntimeError("no export_root from compose tests")
    manifest = export.build_world_manifest(export_root, monolith=s)
    assert manifest.get("format") == "surreal_arch_world_v1"
    assert manifest.get("schema_version", 0) >= 1
    assert manifest.get("instance_count", 0) >= 3
    assert len(manifest.get("hism_groups", [])) >= 1
    val_errors = export.validate_manifest(manifest)
    if val_errors:
        raise RuntimeError(f"manifest validation: {val_errors}")
    hints = {i["ue_material_hint"] for i in manifest["instances"]}
    if not any("/Game/EnvSandbox/" in h for h in hints):
        raise RuntimeError("ue_material_hint paths missing EnvSandbox prefix")
    if export_root.get("surreal_compose_style") == "ZEN_SHRINE":
        sg = manifest.get("style_genome") or {}
        if sg.get("id") != "zen_shrine_v1":
            raise RuntimeError(f"style_genome missing zen_shrine_v1: {sg}")
        if not sg.get("sacred_sequence"):
            raise RuntimeError("style_genome sacred_sequence empty")
        if not sg.get("resolved_compose_roles"):
            raise RuntimeError("style_genome resolved_compose_roles missing")
        if sg["resolved_compose_roles"].get("sacred") != "_lib_GB_ZEN_HONDEN":
            raise RuntimeError("resolved_compose_roles sacred mismatch")
    city_root = city_export_root
    if city_root is not None:
        cm = export.build_world_manifest(city_root, monolith=s)
        csg = cm.get("style_genome") or {}
        if csg.get("id") != "asian_city_v1":
            raise RuntimeError(f"ASIAN_CITY style_genome expected asian_city_v1: {csg}")
        if csg.get("family") != "Asian":
            raise RuntimeError(f"ASIAN_CITY family mismatch: {csg.get('family')}")
        if csg.get("resolved_compose_roles", {}).get("gate") != "_lib_CN_PAILOU":
            raise RuntimeError("ASIAN_CITY resolved gate mismatch")
        print("  asian_city manifest embed: OK")
    if asian_recursive_export_root is not None:
        arm = export.build_world_manifest(asian_recursive_export_root, monolith=s)
        arsg = arm.get("style_genome") or {}
        if arsg.get("id") != "asian_city_recursive_v1":
            raise RuntimeError(f"ASIAN_CITY_RECURSIVE style_genome expected asian_city_recursive_v1: {arsg}")
        if arsg.get("family") != "Asian":
            raise RuntimeError(f"asian recursive family mismatch: {arsg.get('family')}")
        if arsg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError("asian recursive surreal_transform mismatch")
        if arsg.get("resolved_compose_roles", {}).get("medium") != "_lib_JP_KURA_STOREHOUSE":
            raise RuntimeError("ASIAN_CITY_RECURSIVE resolved medium mismatch")
        print("  asian_city_recursive manifest embed: OK")
    if brutalist_export_root is not None:
        bm = export.build_world_manifest(brutalist_export_root, monolith=s)
        bsg = bm.get("style_genome") or {}
        if bsg.get("id") != "brutalist_plaza_v1":
            raise RuntimeError(f"brutalist style_genome expected brutalist_plaza_v1: {bsg}")
        if bsg.get("family") != "Brutalist":
            raise RuntimeError(f"brutalist family mismatch: {bsg.get('family')}")
        if bsg.get("grammar_id") != "BRUTALIST_PLAZA":
            raise RuntimeError("brutalist grammar_id mismatch")
        if bsg.get("compose_style") != "BRUTALIST_PLAZA":
            raise RuntimeError(f"brutalist compose_style mismatch: {bsg.get('compose_style')}")
        if bsg.get("surreal_transform") != "axis_compression":
            raise RuntimeError("brutalist surreal_transform mismatch")
        if bsg.get("resolved_compose_roles", {}).get("medium") != "_lib_GB_BRUTALIST_PANEL_WALL":
            raise RuntimeError("brutalist resolved medium role mismatch")
        print("  brutalist_plaza manifest embed: OK")
    if castle_root is not None and castle_root.get("surreal_compose_style") == "WESTERN_CASTLE":
        wcm = export.build_world_manifest(castle_root, monolith=s)
        wsg = wcm.get("style_genome") or {}
        if wsg.get("id") != "western_castle_v1":
            raise RuntimeError(f"WESTERN_CASTLE style_genome expected western_castle_v1: {wsg}")
        if wsg.get("family") != "Western":
            raise RuntimeError(f"western family mismatch: {wsg.get('family')}")
        if wsg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError(f"western surreal_transform mismatch: {wsg.get('surreal_transform')}")
        if wsg.get("resolved_compose_roles", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
            raise RuntimeError("WESTERN_CASTLE resolved gate mismatch")
        print("  western_castle manifest embed: OK")
    if art_nouveau_export_root is not None:
        am = export.build_world_manifest(art_nouveau_export_root, monolith=s)
        asg = am.get("style_genome") or {}
        if asg.get("id") != "art_nouveau_v1":
            raise RuntimeError(f"ART_NOUVEAU style_genome expected art_nouveau_v1: {asg}")
        if asg.get("family") != "ArtNouveau":
            raise RuntimeError(f"art_nouveau family mismatch: {asg.get('family')}")
        if asg.get("resolved_compose_roles", {}).get("gate") != "_lib_OGEE_ARCH":
            raise RuntimeError("ART_NOUVEAU resolved gate mismatch")
        print("  art_nouveau manifest embed: OK")
    if art_deco_export_root is not None:
        dm = export.build_world_manifest(art_deco_export_root, monolith=s)
        dsg = dm.get("style_genome") or {}
        if dsg.get("id") != "art_deco_lobby_v1":
            raise RuntimeError(f"ART_DECO style_genome expected art_deco_lobby_v1: {dsg}")
        if dsg.get("family") != "ArtDeco":
            raise RuntimeError(f"art_deco family mismatch: {dsg.get('family')}")
        if dsg.get("surreal_transform") != "vertical_stretch":
            raise RuntimeError("ART_DECO surreal_transform mismatch")
        if dsg.get("resolved_compose_roles", {}).get("gate") != "_lib_CUSPED_ARCH":
            raise RuntimeError("ART_DECO resolved gate mismatch")
        print("  art_deco manifest embed: OK")
    if moorish_export_root is not None:
        mm = export.build_world_manifest(moorish_export_root, monolith=s)
        msg = mm.get("style_genome") or {}
        if msg.get("id") != "moorish_courtyard_v1":
            raise RuntimeError(f"MOORISH_COURTYARD style_genome expected moorish_courtyard_v1: {msg}")
        if msg.get("family") != "Moorish":
            raise RuntimeError(f"moorish family mismatch: {msg.get('family')}")
        if msg.get("resolved_compose_roles", {}).get("gate") != "_lib_ARCHWAY_ADV":
            raise RuntimeError("MOORISH_COURTYARD resolved gate mismatch")
        print("  moorish_courtyard manifest embed: OK")
    if renaissance_export_root is not None:
        rm = export.build_world_manifest(renaissance_export_root, monolith=s)
        rsg = rm.get("style_genome") or {}
        if rsg.get("id") != "renaissance_piazza_v1":
            raise RuntimeError(f"RENAISSANCE_PIAZZA style_genome expected renaissance_piazza_v1: {rsg}")
        if rsg.get("family") != "Renaissance":
            raise RuntimeError(f"renaissance family mismatch: {rsg.get('family')}")
        if rsg.get("resolved_compose_roles", {}).get("sacred") != "_lib_DOME":
            raise RuntimeError("RENAISSANCE_PIAZZA resolved sacred mismatch")
        print("  renaissance_piazza manifest embed: OK")
    if byzantine_export_root is not None:
        bm = export.build_world_manifest(byzantine_export_root, monolith=s)
        bsg = bm.get("style_genome") or {}
        if bsg.get("id") != "byzantine_basilica_v1":
            raise RuntimeError(f"BYZANTINE_BASILICA style_genome expected byzantine_basilica_v1: {bsg}")
        if bsg.get("family") != "Byzantine":
            raise RuntimeError(f"byzantine family mismatch: {bsg.get('family')}")
        if bsg.get("surreal_transform") != "vertical_stretch":
            raise RuntimeError("byzantine surreal_transform mismatch")
        if bsg.get("resolved_compose_roles", {}).get("sacred") != "_lib_DOME":
            raise RuntimeError("BYZANTINE_BASILICA resolved sacred mismatch")
        print("  byzantine_basilica manifest embed: OK")
    if baroque_export_root is not None:
        bcm = export.build_world_manifest(baroque_export_root, monolith=s)
        bcsg = bcm.get("style_genome") or {}
        if bcsg.get("id") != "baroque_church_v1":
            raise RuntimeError(f"BAROQUE_CHURCH style_genome expected baroque_church_v1: {bcsg}")
        if bcsg.get("family") != "Baroque":
            raise RuntimeError(f"baroque family mismatch: {bcsg.get('family')}")
        if bcsg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError("baroque surreal_transform mismatch")
        if bcsg.get("resolved_compose_roles", {}).get("gate") != "_lib_OGEE_ARCH":
            raise RuntimeError("BAROQUE_CHURCH resolved gate mismatch")
        print("  baroque_church manifest embed: OK")
    if romanesque_cloister_export_root is not None:
        rcm = export.build_world_manifest(romanesque_cloister_export_root, monolith=s)
        rcsg = rcm.get("style_genome") or {}
        if rcsg.get("id") != "romanesque_cloister_v1":
            raise RuntimeError(f"ROMANESQUE_CLOISTER style_genome expected romanesque_cloister_v1: {rcsg}")
        if rcsg.get("family") != "Romanesque":
            raise RuntimeError(f"romanesque cloister family mismatch: {rcsg.get('family')}")
        if rcsg.get("resolved_compose_roles", {}).get("medium") != "_lib_GB_ROMANESQUE_ARCADE":
            raise RuntimeError("ROMANESQUE_CLOISTER resolved medium mismatch")
        print("  romanesque_cloister manifest embed: OK")
    if romanesque_apse_export_root is not None:
        ram = export.build_world_manifest(romanesque_apse_export_root, monolith=s)
        rasg = ram.get("style_genome") or {}
        if rasg.get("id") != "romanesque_apse_v1":
            raise RuntimeError(f"ROMANESQUE_APSE style_genome expected romanesque_apse_v1: {rasg}")
        if rasg.get("family") != "Romanesque":
            raise RuntimeError(f"romanesque apse family mismatch: {rasg.get('family')}")
        if rasg.get("resolved_compose_roles", {}).get("sacred") != "_lib_GB_ROMANESQUE_APSE":
            raise RuntimeError("ROMANESQUE_APSE resolved sacred mismatch")
        print("  romanesque_apse manifest embed: OK")
    if venetian_export_root is not None:
        vm = export.build_world_manifest(venetian_export_root, monolith=s)
        vsg = vm.get("style_genome") or {}
        if vsg.get("id") != "venetian_canal_v1":
            raise RuntimeError(f"VENETIAN_CANAL style_genome expected venetian_canal_v1: {vsg}")
        if vsg.get("family") != "Venetian":
            raise RuntimeError(f"venetian family mismatch: {vsg.get('family')}")
        if vsg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError("venetian surreal_transform mismatch")
        if vsg.get("resolved_compose_roles", {}).get("gate") != "_lib_BRIDGE":
            raise RuntimeError("VENETIAN_CANAL resolved gate mismatch")
        print("  venetian_canal manifest embed: OK")
    if gothic_export_root is not None:
        gm = export.build_world_manifest(gothic_export_root, monolith=s)
        gsg = gm.get("style_genome") or {}
        if gsg.get("id") != "gothic_cloister_v1":
            raise RuntimeError(f"GOTHIC_CLOISTER style_genome expected gothic_cloister_v1: {gsg}")
        if gsg.get("family") != "Gothic":
            raise RuntimeError(f"gothic family mismatch: {gsg.get('family')}")
        if gsg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError("gothic surreal_transform mismatch")
        if gsg.get("resolved_compose_roles", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
            raise RuntimeError("GOTHIC_CLOISTER resolved gate mismatch")
        print("  gothic_cloister manifest embed: OK")
    if gothic_chapter_export_root is not None:
        gcm = export.build_world_manifest(gothic_chapter_export_root, monolith=s)
        gcsg = gcm.get("style_genome") or {}
        if gcsg.get("id") != "gothic_chapter_house_v1":
            raise RuntimeError(f"GOTHIC_CHAPTER_HOUSE style_genome expected gothic_chapter_house_v1: {gcsg}")
        if gcsg.get("family") != "Gothic":
            raise RuntimeError(f"gothic chapter family mismatch: {gcsg.get('family')}")
        if gcsg.get("resolved_compose_roles", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
            raise RuntimeError("GOTHIC_CHAPTER_HOUSE resolved gate mismatch")
        print("  gothic_chapter_house manifest embed: OK")
    if gothic_nave_crossing_export_root is not None:
        gnm = export.build_world_manifest(gothic_nave_crossing_export_root, monolith=s)
        gnsg = gnm.get("style_genome") or {}
        if gnsg.get("id") != "gothic_nave_crossing_v1":
            raise RuntimeError(f"GOTHIC_NAVE_CROSSING style_genome expected gothic_nave_crossing_v1: {gnsg}")
        if gnsg.get("family") != "Gothic":
            raise RuntimeError(f"gothic nave crossing family mismatch: {gnsg.get('family')}")
        if gnsg.get("surreal_transform") != "vertical_stretch":
            raise RuntimeError("gothic nave crossing surreal_transform mismatch")
        if gnsg.get("resolved_compose_roles", {}).get("monument") != "_lib_ROSE_WINDOW":
            raise RuntimeError("GOTHIC_NAVE_CROSSING resolved monument mismatch")
        print("  gothic_nave_crossing manifest embed: OK")
    if scifi_deck_export_root is not None:
        sm = export.build_world_manifest(scifi_deck_export_root, monolith=s)
        ssg = sm.get("style_genome") or {}
        if ssg.get("id") != "scifi_deck_v1":
            raise RuntimeError(f"SCIFI_DECK style_genome expected scifi_deck_v1: {ssg}")
        if ssg.get("family") != "Sci-Fi":
            raise RuntimeError(f"scifi family mismatch: {ssg.get('family')}")
        if ssg.get("surreal_transform") != "recursive_interior":
            raise RuntimeError("scifi deck surreal_transform mismatch")
        if ssg.get("resolved_compose_roles", {}).get("gate") != "_lib_GB_SCIFI_PRESSURE_DOOR":
            raise RuntimeError("SCIFI_DECK resolved gate mismatch")
        print("  scifi_deck manifest embed: OK")
    if scifi_airlock_export_root is not None:
        am = export.build_world_manifest(scifi_airlock_export_root, monolith=s)
        asg = am.get("style_genome") or {}
        if asg.get("id") != "scifi_airlock_v1":
            raise RuntimeError(f"SCIFI airlock style_genome expected scifi_airlock_v1: {asg}")
        if asg.get("resolved_compose_roles", {}).get("gate") != "_lib_GB_SCIFI_PRESSURE_DOOR":
            raise RuntimeError("SCIFI airlock resolved gate mismatch")
        print("  scifi_airlock manifest embed: OK")
    if scifi_industrial_export_root is not None:
        im = export.build_world_manifest(scifi_industrial_export_root, monolith=s)
        isg = im.get("style_genome") or {}
        if isg.get("id") != "scifi_industrial_yard_v1":
            raise RuntimeError(f"SCIFI industrial style_genome expected scifi_industrial_yard_v1: {isg}")
        if isg.get("resolved_compose_roles", {}).get("large") != "_lib_GREYBOX_PILLAR_HALL":
            raise RuntimeError("SCIFI industrial resolved large mismatch")
        print("  scifi_industrial_yard manifest embed: OK")
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "test.world.json")
        export.write_world_manifest(export_root, path, monolith=s)
        with open(path, encoding="utf-8") as f:
            side = json.load(f)
        assert side.get("format") == "surreal_arch_world_v1"
    print(f"  manifest instances={manifest.get('instance_count')} hism_groups={len(manifest.get('hism_groups', []))}")
    print("  export_contract: OK")
except Exception as e:
    print(f"  export_contract error: {e}")
    all_ok = False

print("\n--- Per-role FBX export ---")
try:
    if export_root is None:
        raise RuntimeError("no export_root for FBX tier")
    with tempfile.TemporaryDirectory() as td:
        fbx_paths = export.export_role_fbx_batches(bpy.context, export_root, out_dir=td)
        print(f"  fbx_batches={len(fbx_paths)} paths={[os.path.basename(p) for p in fbx_paths]}")
        if len(fbx_paths) < 2:
            print("  !! FAIL: expected at least 2 role FBX batches")
            all_ok = False
        else:
            for p in fbx_paths:
                if not os.path.isfile(p) or os.path.getsize(p) < 64:
                    print(f"  !! FAIL: invalid FBX {p}")
                    all_ok = False
                    break
            else:
                print("  fbx_export: OK")
except Exception as e:
    print(f"  fbx_export error: {e}")
    all_ok = False

print("\n--- World operators ---")
for op_id in ("plan_spawn_zen_roji", "export_world_ue"):
    ok = hasattr(bpy.ops.surreal_arch, op_id)
    print(f"  {op_id}: {ok}")
    if not ok:
        all_ok = False

if not all_ok:
    raise RuntimeError("World verify failed")

print("\n=== WORLD VERIFY OK ===")
