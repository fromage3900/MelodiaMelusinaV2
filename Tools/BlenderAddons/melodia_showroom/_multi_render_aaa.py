import os, sys, traceback
import bpy

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
LOG = os.path.join(REPO, "Saved", "Audit", "world_build_20260824", "multi_render_aaa.log")
PRESETS = [
    "verdant_default",
    "cathedral_wide_crystalline",
    "toccata_spires_toccata",
    "waltz_garden_waltz",
    "ballad_plaza_ballad",
    "fugue_maze_fugue",
    "nocturne_reflection_nocturne",
    "lullaby_cave_lullaby",
    "tarantella_bounce_saltarello",
    "canon_echo_pavane",
    "gavotte_hedges_aria",
    "rhapsody_fold_chaconne",
    "berceuse_overhang_madrigal",
    "ritornello_rings_madrigal",
]

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

try:
    bpy.ops.preferences.addon_enable(module="melodia_showroom")
    log("registered=melodia_showroom")
except Exception:
    log(traceback.format_exc())

scene = bpy.context.scene
props = scene.melodia_showroom

# AAA defaults
props.samples = 512
props.resolution_percent = 200
props.transparent = False

for preset in PRESETS:
    try:
        props.preset = preset
        bpy.ops.melodia_showroom.run_pipeline()
        report = getattr(props, "last_report", "")
        log("%s|%s" % (preset, report))
    except Exception:
        log("%s|FAILED|%s" % (preset, traceback.format_exc()))

log("exit_clean")
os._exit(0)
