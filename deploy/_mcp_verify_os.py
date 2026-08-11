"""Headless verify for Surreal Architecture OS layer.

Launch with --factory-startup:
  blender --background --factory-startup --python deploy/_mcp_verify_os.py
"""
import json
import os
import sys

import bpy

print("=== SURREAL OS VERIFY ===")

DEPLOY = os.path.dirname(os.path.abspath(__file__))
if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

s = sys.modules.get("surreal_architecture_gen")
if s is None:
    if "surreal_architecture_gen" not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module="surreal_architecture_gen")
    s = sys.modules.get("surreal_architecture_gen")
if s is None:
    print("  !! FAIL: surreal_architecture_gen not loaded")
    raise SystemExit(1)
if not getattr(s, "_surreal_patched", False):
    print("  !! FAIL: monolith patch (_surreal_patched) not applied")
    raise SystemExit(1)
print("  monolith: OK")

all_ok = True

print("\n--- Genome load ---")
from surreal_os import genome as os_genome

for gid in os_genome.list_genomes():
    try:
        g = os_genome.load_genome(gid)
        print(f"  {gid}: verticality={g.get('verticality')} graph={g.get('default_graph')}")
    except Exception as err:
        print(f"  !! FAIL {gid}: {err}")
        all_ok = False

print("\n--- Grammar graphs ---")
from surreal_os.grammar_loader import load_grammar_graph, merge_grammar_into_registry
from surreal_arch.greybox_graph import GRAPH_REGISTRY

merged = merge_grammar_into_registry(GRAPH_REGISTRY)
print(f"  merged_into_registry: {merged}")
for gid in ("ZEN_SHRINE_AXIS", "ZEN_SAKURA_WALK", "ZEN_SHRINE_COURTYARD", "ZEN_ROJI_PATH", "ZEN_KARESANSHUI_WALK", "ZEN_TEA_GARDEN", "ZEN_STREAM_GARDEN", "ZEN_PAGODA_SPIRE", "ZEN_KAIRO_ENCLOSURE", "CLOISTER", "GOTHIC_CHAPTER_HOUSE", "GOTHIC_NAVE_CROSSING", "SCIFI_AIRLOCK", "SCI_FI_DECK", "ROMANESQUE_CLOISTER", "VENETIAN_CANAL", "ROMANESQUE_APSE", "SCI_FI_DECK_EXPANSION", "SCI_FI_INDUSTRIAL_YARD", "ASIAN_CITY", "ASIAN_CITY_RECURSIVE", "BRUTALIST_PLAZA", "ART_NOUVEAU", "ART_DECO", "MOORISH_COURTYARD", "RENAISSANCE_PIAZZA", "BYZANTINE_BASILICA", "BAROQUE_CHURCH"):
    if gid not in GRAPH_REGISTRY:
        print(f"  !! FAIL: {gid} not in GRAPH_REGISTRY")
        all_ok = False
    elif not GRAPH_REGISTRY[gid].get("os_grammar"):
        print(f"  !! FAIL: {gid} missing os_grammar flag")
        all_ok = False
    else:
        spec = GRAPH_REGISTRY[gid]["spec"]
        print(f"  {gid} modules={len(spec)} os_grammar=True")

print("\n--- Atoms + taxonomy ---")
from surreal_os import atoms, taxonomy, critique

kit_dispatch = getattr(s, "_KIT_DISPATCH", {})
missing_tax = taxonomy.validate_kit_dispatch(kit_dispatch)
if missing_tax:
    print(f"  !! FAIL missing taxonomy: {missing_tax}")
    all_ok = False
else:
    print("  taxonomy: all GB_ZEN_* kits registered")

zen_ok, zen_fails = critique.critique_all_zen_kits(kit_dispatch)
if not zen_ok:
    for line in zen_fails:
        print(f"  !! FAIL {line}")
    all_ok = False
else:
    print("  critique: all GB_ZEN_* pass")

print("\n--- Compose roles ---")
from surreal_os.rules_engine import load_compose_styles
from surreal_world.compose import resolve_compose_style

os_styles = load_compose_styles()
if "ZEN_SHRINE" not in os_styles:
    print("  !! FAIL: ZEN_SHRINE missing from compose_roles.json")
    all_ok = False
else:
    style = resolve_compose_style(s, "ZEN_SHRINE")
    print(f"  ZEN_SHRINE roles: {len(style)} keys")
    role_expect = {
        "sacred": "_lib_GB_ZEN_HONDEN",
        "corner_tower": "_lib_GB_ZEN_GOJU_PAGODA",
        "monument": "_lib_GB_ZEN_TAHOTO",
        "small": "_lib_GB_ZEN_LANTERN",
        "gate": "_lib_GB_ZEN_TORII_GATE",
    }
    for role, lib in role_expect.items():
        if style.get(role) != lib:
            print(f"  !! FAIL: {role} expected {lib} got {style.get(role)}")
            all_ok = False

s._active_style_genome = os_genome.load_genome("zen_shrine_sakura")
style_sakura = resolve_compose_style(s, "ZEN_SHRINE")
if style_sakura.get("gate") != "_lib_GB_ZEN_SAKURA_TORII":
    print(f"  !! FAIL: sakura genome gate override got {style_sakura.get('gate')}")
    all_ok = False
else:
    print("  genome compose_roles sakura: OK")
s._active_style_genome = None

print("\n--- Genome apply + graph spawn smoke ---")
mesh = bpy.data.meshes.new("_OSVerifyMesh")
obj = bpy.data.objects.new("_OSVerify", mesh)
bpy.context.collection.objects.link(obj)
props = obj.surreal_arch_props
os_genome.apply_genome(props, "zen_shrine_v1", monolith=s)
if props.style_genome_id != "zen_shrine_v1":
    print("  !! FAIL: style_genome_id not set")
    all_ok = False
else:
    print("  apply_genome: OK")

g = os_genome.load_genome("zen_shrine_v1")
if g.get("surreal_transform") != "axis_compression":
    print(f"  !! FAIL: zen_shrine_v1 surreal_transform={g.get('surreal_transform')}")
    all_ok = False
else:
    print("  zen_shrine_v1 axis_compression: OK")

ga = os_genome.load_genome("zen_shrine_axis")
if ga.get("grammar_id") != "ZEN_SHRINE_AXIS":
    print(f"  !! FAIL: zen_shrine_axis grammar_id={ga.get('grammar_id')}")
    all_ok = False
elif ga.get("surreal_transform") != "vertical_stretch":
    print(f"  !! FAIL: zen_shrine_axis surreal_transform={ga.get('surreal_transform')}")
    all_ok = False
elif len(ga.get("sacred_sequence") or []) < 6:
    print(f"  !! FAIL: zen_shrine_axis sacred_sequence short")
    all_ok = False
else:
    print("  zen_shrine_axis vertical_stretch: OK")

gs = os_genome.load_genome("zen_shrine_sakura")
if gs.get("torii_variant") != "sakura" or gs.get("default_graph") != "ZEN_SAKURA_WALK":
    print(f"  !! FAIL: zen_shrine_sakura variant/graph")
    all_ok = False
else:
    print("  zen_shrine_sakura sakura walk: OK")

gc = os_genome.load_genome("zen_shrine_courtyard")
if gc.get("default_graph") != "ZEN_SHRINE_COURTYARD":
    print(f"  !! FAIL: zen_shrine_courtyard graph={gc.get('default_graph')}")
    all_ok = False
else:
    print("  zen_shrine_courtyard: OK")

gr = os_genome.load_genome("zen_roji_path")
if gr.get("default_graph") != "ZEN_ROJI_PATH" or not gr.get("compose_roles"):
    print(f"  !! FAIL: zen_roji_path genome")
    all_ok = False
else:
    print("  zen_roji_path genome: OK")

gt = os_genome.load_genome("zen_tea_garden")
if gt.get("default_graph") != "ZEN_TEA_GARDEN":
    print(f"  !! FAIL: zen_tea_garden graph={gt.get('default_graph')}")
    all_ok = False
else:
    print("  zen_tea_garden genome: OK")

zk = os_genome.load_genome("zen_karesansui_v1")
if zk.get("grammar_id") != "ZEN_KARESANSHUI_WALK" or zk.get("surreal_transform") != "axis_compression":
    print(f"  !! FAIL: zen_karesansui_v1 grammar/transform")
    all_ok = False
else:
    print("  zen_karesansui_v1: OK")

zs = os_genome.load_genome("zen_stream_garden_v1")
if zs.get("grammar_id") != "ZEN_STREAM_GARDEN" or not zs.get("compose_roles"):
    print(f"  !! FAIL: zen_stream_garden_v1")
    all_ok = False
else:
    print("  zen_stream_garden_v1: OK")

zp = os_genome.load_genome("zen_pagoda_spire_v1")
if zp.get("grammar_id") != "ZEN_PAGODA_SPIRE" or zp.get("surreal_transform") != "vertical_stretch":
    print(f"  !! FAIL: zen_pagoda_spire_v1")
    all_ok = False
else:
    print("  zen_pagoda_spire_v1: OK")

zke = os_genome.load_genome("zen_kairo_enclosure_v1")
if zke.get("grammar_id") != "ZEN_KAIRO_ENCLOSURE" or zke.get("compose_roles", {}).get("sacred") != "_lib_GB_ZEN_HONDEN":
    print(f"  !! FAIL: zen_kairo_enclosure_v1")
    all_ok = False
else:
    print("  zen_kairo_enclosure_v1: OK")

siy = os_genome.load_genome("scifi_industrial_yard_v1")
if siy.get("grammar_id") != "SCI_FI_INDUSTRIAL_YARD" or siy.get("family") != "Sci-Fi":
    print(f"  !! FAIL: scifi_industrial_yard_v1")
    all_ok = False
else:
    print("  scifi_industrial_yard_v1: OK")

genome_ids = os_genome.list_genomes()
if len(genome_ids) < 29:
    print(f"  !! FAIL: expected >=29 genomes got {len(genome_ids)}")
    all_ok = False
else:
    print(f"  genome catalog: {len(genome_ids)} entries")

groups = getattr(s, "_STYLE_GENOME_GROUPS", {}) or {}
if not groups or sum(len(v) for v in groups.values()) < len(genome_ids):
    print(f"  !! FAIL: _STYLE_GENOME_GROUPS incomplete: {groups}")
    all_ok = False
elif groups.get("Zen", []) and len(groups.get("Zen", [])) >= 10 and groups.get("Gothic", []):
    print(f"  _STYLE_GENOME_GROUPS: {', '.join(f'{k}={len(v)}' for k, v in groups.items())}")
else:
    print(f"  !! FAIL: _STYLE_GENOME_GROUPS missing families: {groups}")
    all_ok = False

if not hasattr(s, "_STYLE_GENOMES") or len(s._STYLE_GENOMES) < 21:
    print("  !! FAIL: _STYLE_GENOMES not populated")
    all_ok = False
else:
    print("  _STYLE_GENOMES: OK")

meta = getattr(s, "_STYLE_GENOME_META", {}) or {}
if "zen_tea_garden" not in meta or meta["zen_tea_garden"].get("graph") != "ZEN_TEA_GARDEN":
    print(f"  !! FAIL: _STYLE_GENOME_META missing tea garden: {meta.get('zen_tea_garden')}")
    all_ok = False
else:
    print("  _STYLE_GENOME_META: OK")

from surreal_arch.greybox_graph import spawn_graph

bpy.context.view_layer.objects.active = obj
spec = GRAPH_REGISTRY["ZEN_SHRINE_AXIS"]["spec"]
try:
    objs = spawn_graph(bpy.context, s, spec[:3], spacing=8.0, graph_id="ZEN_SHRINE_AXIS")
    print(f"  spawn_graph partial: {len(objs)} objects")
    for o in objs:
        snaps = json.loads(o.get("surreal_snap_points", "[]")) if o.get("surreal_snap_points") else []
        if len(snaps) == 0:
            print(f"  !! FAIL: {o.name} has 0 snaps")
            all_ok = False
    asian_spec = GRAPH_REGISTRY["ASIAN_CITY"]["spec"]
    asian_objs = spawn_graph(bpy.context, s, asian_spec[:3], spacing=10.0, graph_id="ASIAN_CITY")
    print(f"  spawn_graph ASIAN_CITY partial: {len(asian_objs)} objects")
    if len(asian_objs) < 2:
        print(f"  !! FAIL: ASIAN_CITY spawn got {len(asian_objs)}")
        all_ok = False
    asian_r_spec = GRAPH_REGISTRY["ASIAN_CITY_RECURSIVE"]["spec"]
    asian_r_objs = spawn_graph(bpy.context, s, asian_r_spec[:4], spacing=9.0, graph_id="ASIAN_CITY_RECURSIVE")
    print(f"  spawn_graph ASIAN_CITY_RECURSIVE partial: {len(asian_r_objs)} objects")
    if len(asian_r_objs) < 3:
        print(f"  !! FAIL: ASIAN_CITY_RECURSIVE spawn got {len(asian_r_objs)}")
        all_ok = False
    brutal_spec = GRAPH_REGISTRY["BRUTALIST_PLAZA"]["spec"]
    brutal_objs = spawn_graph(bpy.context, s, brutal_spec[:3], spacing=12.0, graph_id="BRUTALIST_PLAZA")
    print(f"  spawn_graph BRUTALIST_PLAZA partial: {len(brutal_objs)} objects")
    if len(brutal_objs) < 2:
        print(f"  !! FAIL: BRUTALIST_PLAZA spawn got {len(brutal_objs)}")
        all_ok = False
    art_spec = GRAPH_REGISTRY["ART_NOUVEAU"]["spec"]
    art_objs = spawn_graph(bpy.context, s, art_spec[:3], spacing=10.0, graph_id="ART_NOUVEAU")
    print(f"  spawn_graph ART_NOUVEAU partial: {len(art_objs)} objects")
    if len(art_objs) < 2:
        print(f"  !! FAIL: ART_NOUVEAU spawn got {len(art_objs)}")
        all_ok = False
    deco_spec = GRAPH_REGISTRY["ART_DECO"]["spec"]
    deco_objs = spawn_graph(bpy.context, s, deco_spec[:3], spacing=10.0, graph_id="ART_DECO")
    print(f"  spawn_graph ART_DECO partial: {len(deco_objs)} objects")
    if len(deco_objs) < 2:
        print(f"  !! FAIL: ART_DECO spawn got {len(deco_objs)}")
        all_ok = False
    moor_spec = GRAPH_REGISTRY["MOORISH_COURTYARD"]["spec"]
    moor_objs = spawn_graph(bpy.context, s, moor_spec[:3], spacing=10.0, graph_id="MOORISH_COURTYARD")
    print(f"  spawn_graph MOORISH_COURTYARD partial: {len(moor_objs)} objects")
    if len(moor_objs) < 2:
        print(f"  !! FAIL: MOORISH_COURTYARD spawn got {len(moor_objs)}")
        all_ok = False
    ren_spec = GRAPH_REGISTRY["RENAISSANCE_PIAZZA"]["spec"]
    ren_objs = spawn_graph(bpy.context, s, ren_spec[:3], spacing=11.0, graph_id="RENAISSANCE_PIAZZA")
    print(f"  spawn_graph RENAISSANCE_PIAZZA partial: {len(ren_objs)} objects")
    if len(ren_objs) < 2:
        print(f"  !! FAIL: RENAISSANCE_PIAZZA spawn got {len(ren_objs)}")
        all_ok = False
    byz_spec = GRAPH_REGISTRY["BYZANTINE_BASILICA"]["spec"]
    byz_objs = spawn_graph(bpy.context, s, byz_spec[:4], spacing=11.0, graph_id="BYZANTINE_BASILICA")
    print(f"  spawn_graph BYZANTINE_BASILICA partial: {len(byz_objs)} objects")
    if len(byz_objs) < 3:
        print(f"  !! FAIL: BYZANTINE_BASILICA spawn got {len(byz_objs)}")
        all_ok = False
    bar_spec = GRAPH_REGISTRY["BAROQUE_CHURCH"]["spec"]
    bar_objs = spawn_graph(bpy.context, s, bar_spec[:4], spacing=11.0, graph_id="BAROQUE_CHURCH")
    print(f"  spawn_graph BAROQUE_CHURCH partial: {len(bar_objs)} objects")
    if len(bar_objs) < 3:
        print(f"  !! FAIL: BAROQUE_CHURCH spawn got {len(bar_objs)}")
        all_ok = False
    gch_spec = GRAPH_REGISTRY["GOTHIC_CHAPTER_HOUSE"]["spec"]
    gch_objs = spawn_graph(bpy.context, s, gch_spec[:4], spacing=10.0, graph_id="GOTHIC_CHAPTER_HOUSE")
    print(f"  spawn_graph GOTHIC_CHAPTER_HOUSE partial: {len(gch_objs)} objects")
    if len(gch_objs) < 3:
        print(f"  !! FAIL: GOTHIC_CHAPTER_HOUSE spawn got {len(gch_objs)}")
        all_ok = False
    gnc_spec = GRAPH_REGISTRY["GOTHIC_NAVE_CROSSING"]["spec"]
    gnc_objs = spawn_graph(bpy.context, s, gnc_spec[:4], spacing=10.0, graph_id="GOTHIC_NAVE_CROSSING")
    print(f"  spawn_graph GOTHIC_NAVE_CROSSING partial: {len(gnc_objs)} objects")
    if len(gnc_objs) < 3:
        print(f"  !! FAIL: GOTHIC_NAVE_CROSSING spawn got {len(gnc_objs)}")
        all_ok = False
    from surreal_arch.research_presets import run_research_preset
    rp = run_research_preset(bpy.context, "gothic_cloister_graph", monolith=s)
    if rp.get("mode") != "graph" or rp.get("count", 0) < 3:
        print(f"  !! FAIL: research preset graph spawn: {rp}")
        all_ok = False
    else:
        print(f"  research_preset gothic_cloister_graph: {rp['count']} modules")
    rp2 = run_research_preset(bpy.context, "scifi_airlock_graph", monolith=s)
    if rp2.get("mode") != "graph" or rp2.get("count", 0) < 3:
        print(f"  !! FAIL: scifi_airlock_graph spawn: {rp2}")
        all_ok = False
    else:
        print(f"  research_preset scifi_airlock_graph: {rp2['count']} modules")
    rp2b = run_research_preset(bpy.context, "scifi_industrial_yard_graph", monolith=s)
    if rp2b.get("mode") != "graph" or rp2b.get("count", 0) < 4:
        print(f"  !! FAIL: scifi_industrial_yard_graph spawn: {rp2b}")
        all_ok = False
    else:
        print(f"  research_preset scifi_industrial_yard_graph: {rp2b['count']} modules")
    rp3 = run_research_preset(bpy.context, "zen_pagoda_spire_graph", monolith=s)
    if rp3.get("mode") != "graph" or rp3.get("count", 0) < 5:
        print(f"  !! FAIL: zen_pagoda_spire_graph spawn: {rp3}")
        all_ok = False
    else:
        print(f"  research_preset zen_pagoda_spire_graph: {rp3['count']} modules")
    rp4 = run_research_preset(bpy.context, "byzantine_basilica_graph", monolith=s)
    if rp4.get("mode") != "graph" or rp4.get("count", 0) < 4:
        print(f"  !! FAIL: byzantine_basilica_graph spawn: {rp4}")
        all_ok = False
    else:
        print(f"  research_preset byzantine_basilica_graph: {rp4['count']} modules")
    rp5 = run_research_preset(bpy.context, "baroque_church_graph", monolith=s)
    if rp5.get("mode") != "graph" or rp5.get("count", 0) < 4:
        print(f"  !! FAIL: baroque_church_graph spawn: {rp5}")
        all_ok = False
    else:
        print(f"  research_preset baroque_church_graph: {rp5['count']} modules")
    rp6 = run_research_preset(bpy.context, "gothic_chapter_house_graph", monolith=s)
    if rp6.get("mode") != "graph" or rp6.get("count", 0) < 4:
        print(f"  !! FAIL: gothic_chapter_house_graph spawn: {rp6}")
        all_ok = False
    else:
        print(f"  research_preset gothic_chapter_house_graph: {rp6['count']} modules")
    rp7 = run_research_preset(bpy.context, "gothic_nave_crossing_graph", monolith=s)
    if rp7.get("mode") != "graph" or rp7.get("count", 0) < 4:
        print(f"  !! FAIL: gothic_nave_crossing_graph spawn: {rp7}")
        all_ok = False
    else:
        print(f"  research_preset gothic_nave_crossing_graph: {rp7['count']} modules")
    pagoda_spec = GRAPH_REGISTRY["ZEN_PAGODA_SPIRE"]["spec"]
    pagoda_objs = spawn_graph(bpy.context, s, pagoda_spec[:4], spacing=10.0, graph_id="ZEN_PAGODA_SPIRE")
    print(f"  spawn_graph ZEN_PAGODA_SPIRE partial: {len(pagoda_objs)} objects")
    if len(pagoda_objs) < 3:
        print(f"  !! FAIL: ZEN_PAGODA_SPIRE spawn got {len(pagoda_objs)}")
        all_ok = False
except Exception as err:
    print(f"  !! FAIL spawn_graph: {err}")
    all_ok = False

print("\n--- Research preset graph audit ---")
from surreal_arch.research_presets import audit_graph_presets, audit_grammar_enums, RESEARCH_PRESETS

graph_preset_ids = [pid for pid, spec in RESEARCH_PRESETS.items() if spec.get("graph_id")]
audit_errs = audit_graph_presets(GRAPH_REGISTRY)
if audit_errs:
    for line in audit_errs:
        print(f"  !! FAIL {line}")
    all_ok = False
elif len(graph_preset_ids) < 24:
    print(f"  !! FAIL: expected >=24 graph research presets got {len(graph_preset_ids)}")
    all_ok = False
else:
    print(f"  graph_research_presets: {len(graph_preset_ids)} OK")

enum_errs = audit_grammar_enums(GRAPH_REGISTRY)
if enum_errs:
    for line in enum_errs:
        print(f"  !! FAIL {line}")
    all_ok = False
else:
    print("  grammar_enum_audit: OK")

print("\n--- Surreal transform ---")
from surreal_os.rules_engine import get_transform, apply_surreal_transform

xf = get_transform("axis_compression")
if not xf:
    print("  !! FAIL: axis_compression missing")
    all_ok = False
elif "BRUTALIST_PLAZA" not in (xf.get("applies_to") or []):
    print("  !! FAIL: axis_compression missing BRUTALIST_PLAZA")
    all_ok = False
elif "ZEN_STREAM_GARDEN" not in (xf.get("applies_to") or []):
    print("  !! FAIL: axis_compression missing ZEN_STREAM_GARDEN")
    all_ok = False
else:
    print(f"  axis_compression type={xf.get('type')} BRUTALIST_PLAZA: OK")

xf2 = get_transform("vertical_stretch")
if not xf2:
    print("  !! FAIL: vertical_stretch missing")
    all_ok = False
elif "ZEN_PAGODA_SPIRE" not in (xf2.get("applies_to") or []):
    print("  !! FAIL: vertical_stretch missing ZEN_PAGODA_SPIRE")
    all_ok = False
else:
    print(f"  vertical_stretch type={xf2.get('type')} ZEN_PAGODA_SPIRE: OK")

xf3 = get_transform("recursive_interior")
if not xf3 or "CLOISTER" not in (xf3.get("applies_to") or []):
    print(f"  !! FAIL: recursive_interior CLOISTER apply: {xf3}")
    all_ok = False
elif "ASIAN_CITY" not in (xf3.get("applies_to") or []):
    print("  !! FAIL: recursive_interior missing ASIAN_CITY")
    all_ok = False
else:
    print("  recursive_interior CLOISTER + ASIAN_CITY: OK")

gothic = os_genome.load_genome("gothic_cloister_v1")
if os_genome.genome_family(gothic) != "Gothic":
    print(f"  !! FAIL: genome_family gothic={os_genome.genome_family(gothic)}")
    all_ok = False
elif gothic.get("surreal_transform") != "recursive_interior":
    print(f"  !! FAIL: gothic_cloister_v1 transform={gothic.get('surreal_transform')}")
    all_ok = False
elif gothic.get("compose_style") != "GOTHIC_CLOISTER":
    print(f"  !! FAIL: gothic_cloister_v1 compose={gothic.get('compose_style')}")
    all_ok = False
elif os_styles.get("GOTHIC_CLOISTER", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
    print("  !! FAIL: GOTHIC_CLOISTER compose_roles missing")
    all_ok = False
else:
    print("  gothic_cloister_v1 + GOTHIC_CLOISTER compose_roles: OK")

gch = os_genome.load_genome("gothic_chapter_house_v1")
if gch.get("grammar_id") != "GOTHIC_CHAPTER_HOUSE" or gch.get("compose_style") != "GOTHIC_CHAPTER_HOUSE":
    print(f"  !! FAIL: gothic_chapter_house_v1")
    all_ok = False
elif os_styles.get("GOTHIC_CHAPTER_HOUSE", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
    print("  !! FAIL: GOTHIC_CHAPTER_HOUSE compose_roles missing")
    all_ok = False
else:
    print("  gothic_chapter_house_v1 + GOTHIC_CHAPTER_HOUSE compose_roles: OK")

gnc = os_genome.load_genome("gothic_nave_crossing_v1")
if gnc.get("grammar_id") != "GOTHIC_NAVE_CROSSING" or gnc.get("compose_style") != "GOTHIC_NAVE_CROSSING":
    print(f"  !! FAIL: gothic_nave_crossing_v1")
    all_ok = False
elif gnc.get("surreal_transform") != "vertical_stretch":
    print(f"  !! FAIL: gothic nave transform={gnc.get('surreal_transform')}")
    all_ok = False
elif os_styles.get("GOTHIC_NAVE_CROSSING", {}).get("monument") != "_lib_ROSE_WINDOW":
    print("  !! FAIL: GOTHIC_NAVE_CROSSING compose_roles missing")
    all_ok = False
else:
    print("  gothic_nave_crossing_v1 + GOTHIC_NAVE_CROSSING compose_roles: OK")

scifi = os_genome.load_genome("scifi_airlock_v1")
if scifi.get("default_graph") != "SCIFI_AIRLOCK":
    print(f"  !! FAIL: scifi_airlock_v1 graph={scifi.get('default_graph')}")
    all_ok = False
else:
    print("  scifi_airlock_v1: OK")

sdeck = os_genome.load_genome("scifi_deck_v1")
sdspine = os_genome.load_genome("scifi_deck_spine_v1")
if sdeck.get("compose_style") != "SCIFI_DECK" or sdspine.get("compose_style") != "SCIFI_DECK":
    print(f"  !! FAIL: scifi deck compose bleed deck={sdeck.get('compose_style')} spine={sdspine.get('compose_style')}")
    all_ok = False
elif os_styles.get("SCIFI_DECK", {}).get("gate") != "_lib_GB_SCIFI_PRESSURE_DOOR":
    print("  !! FAIL: SCIFI_DECK compose_roles missing")
    all_ok = False
else:
    print("  scifi_deck_v1 + scifi_deck_spine_v1 + SCIFI_DECK compose_roles: OK")

sair = os_genome.load_genome("scifi_airlock_v1")
siy2 = os_genome.load_genome("scifi_industrial_yard_v1")
if sair.get("compose_style") != "SCIFI_DECK" or siy2.get("compose_style") != "SCIFI_DECK":
    print(f"  !! FAIL: scifi compose bleed airlock={sair.get('compose_style')} industrial={siy2.get('compose_style')}")
    all_ok = False
elif siy2.get("compose_roles", {}).get("gate") != "_lib_GB_SCIFI_PRESSURE_DOOR":
    print(f"  !! FAIL: scifi_industrial_yard_v1 gate role={siy2.get('compose_roles')}")
    all_ok = False
else:
    print("  scifi_airlock_v1 + scifi_industrial_yard_v1 SCIFI_DECK retarget: OK")

rom = os_genome.load_genome("romanesque_cloister_v1")
rapp = os_genome.load_genome("romanesque_apse_v1")
if rom.get("grammar_id") != "ROMANESQUE_CLOISTER" or rom.get("compose_style") != "ROMANESQUE_CLOISTER":
    print(f"  !! FAIL: romanesque_cloister_v1 compose/grammar")
    all_ok = False
elif rapp.get("grammar_id") != "ROMANESQUE_APSE" or rapp.get("compose_style") != "ROMANESQUE_APSE":
    print(f"  !! FAIL: romanesque_apse_v1 compose/grammar")
    all_ok = False
elif os_styles.get("ROMANESQUE_CLOISTER", {}).get("medium") != "_lib_GB_ROMANESQUE_ARCADE":
    print("  !! FAIL: ROMANESQUE_CLOISTER compose_roles missing")
    all_ok = False
elif os_styles.get("ROMANESQUE_APSE", {}).get("sacred") != "_lib_GB_ROMANESQUE_APSE":
    print("  !! FAIL: ROMANESQUE_APSE compose_roles missing")
    all_ok = False
else:
    print("  romanesque_cloister_v1 + romanesque_apse_v1 ROMANESQUE compose: OK")

ven = os_genome.load_genome("venetian_canal_v1")
if ven.get("compose_style") != "VENETIAN_CANAL" or os_genome.genome_family(ven) != "Venetian":
    print(f"  !! FAIL: venetian_canal_v1 compose/family")
    all_ok = False
elif ven.get("grammar_id") != "VENETIAN_CANAL":
    print(f"  !! FAIL: venetian_canal_v1 grammar={ven.get('grammar_id')}")
    all_ok = False
elif os_styles.get("VENETIAN_CANAL", {}).get("medium") != "_lib_GB_VENETIAN_LOGGIA":
    print("  !! FAIL: VENETIAN_CANAL compose_roles missing")
    all_ok = False
else:
    print("  venetian_canal_v1 + VENETIAN_CANAL compose_roles: OK")

asian = os_genome.load_genome("asian_city_v1")
if asian.get("compose_style") != "ASIAN_CITY" or os_genome.genome_family(asian) != "Asian":
    print(f"  !! FAIL: asian_city_v1 compose/family={asian.get('compose_style')}")
    all_ok = False
elif asian.get("grammar_id") != "ASIAN_CITY":
    print(f"  !! FAIL: asian_city_v1 grammar={asian.get('grammar_id')}")
    all_ok = False
elif os_styles.get("ASIAN_CITY", {}).get("gate") != "_lib_CN_PAILOU":
    print("  !! FAIL: ASIAN_CITY compose_roles missing")
    all_ok = False
else:
    print("  asian_city_v1 + ASIAN_CITY compose_roles: OK")

asian_r = os_genome.load_genome("asian_city_recursive_v1")
if asian_r.get("compose_style") != "ASIAN_CITY_RECURSIVE" or asian_r.get("grammar_id") != "ASIAN_CITY_RECURSIVE":
    print(f"  !! FAIL: asian_city_recursive_v1 compose/grammar")
    all_ok = False
elif asian_r.get("surreal_transform") != "recursive_interior":
    print(f"  !! FAIL: asian_city_recursive_v1 transform={asian_r.get('surreal_transform')}")
    all_ok = False
elif os_styles.get("ASIAN_CITY_RECURSIVE", {}).get("medium") != "_lib_JP_KURA_STOREHOUSE":
    print("  !! FAIL: ASIAN_CITY_RECURSIVE compose_roles missing")
    all_ok = False
else:
    print("  asian_city_recursive_v1 + ASIAN_CITY_RECURSIVE compose_roles: OK")

brut = os_genome.load_genome("brutalist_plaza_v1")
if brut.get("surreal_transform") != "axis_compression" or os_genome.genome_family(brut) != "Brutalist":
    print(f"  !! FAIL: brutalist_plaza_v1 transform/family")
    all_ok = False
elif brut.get("grammar_id") != "BRUTALIST_PLAZA" or brut.get("compose_style") != "BRUTALIST_PLAZA":
    print(f"  !! FAIL: brutalist_plaza_v1 grammar/compose={brut.get('grammar_id')}/{brut.get('compose_style')}")
    all_ok = False
elif os_styles.get("BRUTALIST_PLAZA", {}).get("medium") != "_lib_GB_BRUTALIST_PANEL_WALL":
    print("  !! FAIL: BRUTALIST_PLAZA compose_roles missing")
    all_ok = False
else:
    print("  brutalist_plaza_v1 + BRUTALIST_PLAZA compose: OK")

wc = os_genome.load_genome("western_castle_v1")
if wc.get("compose_style") != "WESTERN_CASTLE" or os_genome.genome_family(wc) != "Western":
    print(f"  !! FAIL: western_castle_v1 compose/family")
    all_ok = False
elif wc.get("grammar_id") != "CLOISTER":
    print(f"  !! FAIL: western_castle_v1 grammar={wc.get('grammar_id')}")
    all_ok = False
elif wc.get("surreal_transform") != "recursive_interior":
    print(f"  !! FAIL: western_castle_v1 surreal_transform={wc.get('surreal_transform')}")
    all_ok = False
elif wc.get("compose_roles", {}).get("gate") != "_lib_GB_GOTHIC_PORTAL":
    print(f"  !! FAIL: western_castle_v1 gate role={wc.get('compose_roles')}")
    all_ok = False
else:
    print("  western_castle_v1 + recursive_interior compose: OK")

an = os_genome.load_genome("art_nouveau_v1")
if an.get("compose_style") != "ART_NOUVEAU" or os_genome.genome_family(an) != "ArtNouveau":
    print(f"  !! FAIL: art_nouveau_v1 compose/family")
    all_ok = False
elif an.get("grammar_id") != "ART_NOUVEAU":
    print(f"  !! FAIL: art_nouveau_v1 grammar={an.get('grammar_id')}")
    all_ok = False
elif os_styles.get("ART_NOUVEAU", {}).get("gate") != "_lib_OGEE_ARCH":
    print("  !! FAIL: ART_NOUVEAU compose_roles missing")
    all_ok = False
else:
    print("  art_nouveau_v1 + ART_NOUVEAU compose_roles: OK")

ad = os_genome.load_genome("art_deco_lobby_v1")
if ad.get("compose_style") != "ART_DECO" or os_genome.genome_family(ad) != "ArtDeco":
    print(f"  !! FAIL: art_deco_lobby_v1 compose/family")
    all_ok = False
elif ad.get("grammar_id") != "ART_DECO":
    print(f"  !! FAIL: art_deco_lobby_v1 grammar={ad.get('grammar_id')}")
    all_ok = False
elif ad.get("surreal_transform") != "vertical_stretch":
    print(f"  !! FAIL: art_deco_lobby_v1 transform={ad.get('surreal_transform')}")
    all_ok = False
elif os_styles.get("ART_DECO", {}).get("gate") != "_lib_CUSPED_ARCH":
    print("  !! FAIL: ART_DECO compose_roles missing")
    all_ok = False
else:
    print("  art_deco_lobby_v1 + ART_DECO compose_roles: OK")

mc = os_genome.load_genome("moorish_courtyard_v1")
if mc.get("compose_style") != "MOORISH_COURTYARD" or os_genome.genome_family(mc) != "Moorish":
    print(f"  !! FAIL: moorish_courtyard_v1 compose/family")
    all_ok = False
elif mc.get("grammar_id") != "MOORISH_COURTYARD":
    print(f"  !! FAIL: moorish_courtyard_v1 grammar={mc.get('grammar_id')}")
    all_ok = False
elif os_styles.get("MOORISH_COURTYARD", {}).get("gate") != "_lib_ARCHWAY_ADV":
    print("  !! FAIL: MOORISH_COURTYARD compose_roles missing")
    all_ok = False
else:
    print("  moorish_courtyard_v1 + MOORISH_COURTYARD compose_roles: OK")

rp = os_genome.load_genome("renaissance_piazza_v1")
if rp.get("compose_style") != "RENAISSANCE_PIAZZA" or os_genome.genome_family(rp) != "Renaissance":
    print(f"  !! FAIL: renaissance_piazza_v1 compose/family")
    all_ok = False
elif rp.get("grammar_id") != "RENAISSANCE_PIAZZA":
    print(f"  !! FAIL: renaissance_piazza_v1 grammar={rp.get('grammar_id')}")
    all_ok = False
elif os_styles.get("RENAISSANCE_PIAZZA", {}).get("sacred") != "_lib_DOME":
    print("  !! FAIL: RENAISSANCE_PIAZZA compose_roles missing")
    all_ok = False
else:
    print("  renaissance_piazza_v1 + RENAISSANCE_PIAZZA compose_roles: OK")

bb = os_genome.load_genome("byzantine_basilica_v1")
if bb.get("grammar_id") != "BYZANTINE_BASILICA" or bb.get("compose_style") != "BYZANTINE_BASILICA":
    print(f"  !! FAIL: byzantine_basilica_v1")
    all_ok = False
elif bb.get("surreal_transform") != "vertical_stretch":
    print(f"  !! FAIL: byzantine transform={bb.get('surreal_transform')}")
    all_ok = False
elif os_styles.get("BYZANTINE_BASILICA", {}).get("sacred") != "_lib_DOME":
    print("  !! FAIL: BYZANTINE_BASILICA compose_roles missing")
    all_ok = False
else:
    print("  byzantine_basilica_v1 + BYZANTINE_BASILICA compose_roles: OK")

bc = os_genome.load_genome("baroque_church_v1")
if bc.get("grammar_id") != "BAROQUE_CHURCH" or bc.get("compose_style") != "BAROQUE_CHURCH":
    print(f"  !! FAIL: baroque_church_v1")
    all_ok = False
elif bc.get("surreal_transform") != "recursive_interior":
    print(f"  !! FAIL: baroque transform={bc.get('surreal_transform')}")
    all_ok = False
elif os_styles.get("BAROQUE_CHURCH", {}).get("gate") != "_lib_OGEE_ARCH":
    print("  !! FAIL: BAROQUE_CHURCH compose_roles missing")
    all_ok = False
else:
    print("  baroque_church_v1 + BAROQUE_CHURCH compose_roles: OK")

ven = os_genome.load_genome("venetian_canal_v1")
if ven.get("compose_style") != "VENETIAN_CANAL" or os_genome.genome_family(ven) != "Venetian":
    print(f"  !! FAIL: venetian_canal_v1 compose/family")
    all_ok = False
elif ven.get("grammar_id") != "VENETIAN_CANAL":
    print(f"  !! FAIL: venetian_canal_v1 grammar={ven.get('grammar_id')}")
    all_ok = False
elif os_styles.get("VENETIAN_CANAL", {}).get("medium") != "_lib_GB_VENETIAN_LOGGIA":
    print("  !! FAIL: VENETIAN_CANAL compose_roles missing")
    all_ok = False
else:
    print("  venetian_canal_v1 + VENETIAN_CANAL compose_roles: OK")

if all_ok:
    print("\n=== OS VERIFY OK ===")
else:
    print("\n=== OS VERIFY FAILED ===")
    raise SystemExit(1)
