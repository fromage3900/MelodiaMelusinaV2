"""melusina_house_p0_dressing.py â€” dress Melusina's P0 house with the Magician's Library.

The house leg of the Poitou P0 Golden Walk is bounded by the plan to three rooms:
    bedroom  ->  landing/vestibule  ->  oval salon  ->  front doors
(POITOU_P0_GOLDEN_WALK_2026-10-21.md, "HOUSE (one connected showcase route, not every
room)"). The Magician's Library pack supplies the interior props, the Building set
supplies the staircase/landing architecture, and CentreRing supplies the salon's
circular floor medallion.

This script is the single source of truth for that dressing:

    plan    - write specs/p0/melusina_house_p0_dressing.v1.json + a top-down layout
              diagram to Saved/Audit/. Mutates nothing.
    apply   - load /Game/Melodia/Levels/Opening/L_MelusinaHouse_P0, spawn the
              dressing as StaticMeshActors with geometry-correct seating (the mesh
              pivot offset is measured from the asset bounds, so every prop actually
              stands on its surface), save the level, write a receipt.

Every placement carries the plan role it serves. Nothing is placed without a role.

Usage:
    UnrealEditor-Cmd.exe <project> -run=pythonscript -script=<this file> -unattended
    or, in the editor:  exec(open(<this file>).read())
    Modes: MAGICIANS_MODE = plan (default) | apply
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPEC = PROJECT_ROOT / "specs" / "p0" / "melusina_house_p0_dressing.v1.json"
RECEIPT = PROJECT_ROOT / "Saved" / "Audit" / "melusina_house_p0_dressing.json"
DIAGRAM = PROJECT_ROOT / "Saved" / "Audit" / "melusina_house_p0_dressing_layout.svg"

MAP = "/Game/Melodia/Levels/Opening/L_MelusinaHouse_P0"

# The house's two Houdini room shells, measured from their baked meshes
# (world cm). Interior is the shell box minus ~30 cm of wall per side.
ROOMS = {
    "bedroom": {
        "shell_outer_x": [-1179, -425], "shell_outer_y": [-1023, -69], "floor_z": 0,
        "interior_x": [-1150, -450], "interior_y": [-995, -100],
        "note": "HoudiniAssetActor_1 at (-1152,-96,0) -> MelodiaRoomShell_1_0_2C3698E7, 754x954x380 cm shell",
    },
    "landing": {
        "shell_outer_x": [-450, 60], "shell_outer_y": [-1023, -69], "floor_z": 0,
        "interior_x": [-450, 60], "interior_y": [-995, -100],
        "note": "open threshold between the bedroom shell and the salon shell; the story door sits on the salon side at (94,-584,49)",
    },
    "salon": {
        "shell_outer_x": [23, 1381], "shell_outer_y": [-1809, 27], "floor_z": 0,
        "interior_x": [60, 1350], "interior_y": [-1780, 0],
        "note": "HoudiniAssetActor_0 at (50,0,0) -> MelodiaRoomShell_1_0_3_5_0_main_geo_508A1C1F, 1358x1835x563 cm shell",
    },
}

CANON = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
PACK = "/Game/MagicianLabatory/Source"
# Second dressing source: the Kitbash3D Enchanted Interiors pack converted onto
# M_Master_Toon_Universal on 2026-10-21, imported at /Game/EnchantedInteriors.
# Its prop meshes live under Geometries/ and are named <ActorName>_Main.
ECV = "/Game/EnchantedInteriors"

# (mesh_path, x, y, rot_z_deg, surface_z, role, plan_citation)
D = []


def add(mesh, x, y, rot, surface, role, cite, tree="canon", folder=None):
    D.append({"mesh_name": mesh, "tree": tree, "folder": folder, "x": x, "y": y,
              "rot_z": rot, "surface_z": surface, "role": role, "cite": cite})


# ---------------------------------------------------------------- BEDROOM
# "bed + desk/window + companion/perch focal point + resonant object" (P0 score)
# "curved bed alcove, built-in shelf following wall curvature, one big blue dormer
#  window, ribbons, sheet music, jars, shoes and clothes" (rooms doc Â§2)
add("SM_Desk", -900, -935, 0, 0, "writing desk / field-journal worktable",
    "house plan GN_MH_11 interior: center/right writing desk / field-journal worktable; P0 M01 desk inspection")
add("SM_Desk_Drawer", -900, -935, 0, 0, "drawer under the desk",
    "rooms doc SS2 domestic imperfection: the room must feel lived in")
add("SM_Shelf_Prop", -955, -915, 0, 82, "field journal / papers on the desk",
    "house plan: field-journal worktable")
add("SM_Globe", -870, -945, 0, 82, "globe on the desk",
    "rooms doc SS2: scholar's clutter breaking the clean system")
add("SM_Microscope", -880, -920, 0, 82, "microscope on the desk",
    "rooms doc SS2: domestic imperfection")
add("SM_Candle1_L", -910, -930, 0, 82, "candle - P0 M02 resonant-object VISUAL candidate",
    "P0 M02: instrument, small music-box, or window chime (choose one existing compatible actor)")
add("SM_Wick", -910, -930, 0, 95, "wick in the candle",
    "P0 M02")
add("SM_GlassBottle4", -945, -950, 0, 82, "ink jar on the desk",
    "rooms doc SS2: jars")
add("SM_GlassBottle5", -930, -952, 0, 82, "ink jar on the desk",
    "rooms doc SS2: jars")
add("SM_GlassBottle6", -915, -950, 0, 82, "jar on the desk",
    "rooms doc SS2: jars")
add("SM_Bookshelf", -1130, -790, 0, 0, "built-in shelf run, west wall (250 cm)",
    "rooms doc SS2: built-in shelf following wall curvature")
add("SM_Shelf", -640, -145, 0, 0, "built-in shelf, north wall (159 cm)",
    "rooms doc SS2: built-in shelf following wall curvature")
add("SM_Shelf_2", -1010, -140, 0, 0, "built-in shelf, north wall (91 cm)",
    "rooms doc SS2: built-in shelf following wall curvature")
add("SM_GlassBottle2", -625, -145, 0, 186, "jar on the shelf",
    "rooms doc SS2: jars")
add("SM_GlassBottle3", -605, -140, 0, 186, "jar on the shelf",
    "rooms doc SS2: jars")
add("SM_Box", -1130, -700, 0, 250, "small box on the shelf",
    "rooms doc SS2: clutter")
add("SM_Carpet", -720, -760, 90, 0, "rug beside the bed (271x526)",
    "REF_02 board: Floor, mouldings & ornaments; house plan: center entry + sitting / circular rug")
add("SM_Desk3", -880, -250, 0, 0, "bedside table (48x22x77)",
    "P0 M01: one strong visual line from bed to the focal point")
add("SM_Pot_Table", -330, -900, 0, 0, "plant table, south-east (142x173)",
    "REF_02 board: Flowering & floral elements")
add("SM_Pot", -330, -900, 0, 107, "pot on the plant table",
    "REF_02 board: Flowering & floral elements")
add("SM_Kit_Ornament_A", -1140, -420, 0, 0, "wall ornament, west wall",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Kit_Ornament_B", -1140, -520, 0, 0, "wall ornament, west wall (275 cm)",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Kit_Ornament_C", -1100, -140, 0, 0, "wall ornament, west wall",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Deco4", -1145, -330, 0, 0, "wall hanging, west wall (248 cm)",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Deco5", -700, -960, 0, 0, "wall hanging, south wall (236 cm)",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Flag", -1000, -955, 0, 0, "wall banner, south wall (207 cm)",
    "REF_02 board: Fabric, awnings & drapes")
add("SM_Drawer_Box002", -520, -600, 0, 0, "chest by the bed",
    "rooms doc SS2: domestic imperfection")

# ---------------------------------------------------------------- LANDING
add("SM_Hallpillar", -430, -300, 0, 0, "column framing the threshold",
    "rooms doc SS1 Resonant Salon / GN_MH_00 shell; P0 M03 threshold", tree="pack", folder="Building/Pillar")
add("SM_Hallpillar", -350, -800, 0, 0, "column framing the threshold",
    "P0 M03 threshold", tree="pack", folder="Building/Pillar")
add("SM_Wood_Pillar", -200, -250, 0, 0, "timber post by the threshold (1690 cm)",
    "REF_02 board: Columns & pillars", tree="pack", folder="Building/Wood_Pillar")
add("SM_Hallwall", -430, -950, 90, 0, "wall segment closing the passage",
    "P0 M03: the bedroom door opens onto the larger house", tree="canon", folder="Hallwall")
add("SM_HallwallGlass", -430, -300, 90, 0, "glass screen in the passage",
    "REF_01 board: arched window family", tree="canon", folder="HallwallGlass")
add("SM_HallwallGlassBar", -430, -300, 90, 0, "glass screen frame",
    "REF_01 board: arched window family", tree="canon", folder="HallwallGlassBar")
add("SM_HallDeco", -430, -620, 90, 0, "passage ornament",
    "REF_02 board: Floor, mouldings & ornaments", tree="canon", folder="HallDeco")
add("SM_Lantern", -150, -880, 0, 0, "hanging lantern in the passage",
    "P0 M04: the house hums")
add("SM_LanternGlass", -150, -880, 0, 58, "lantern glass",
    "P0 M04: the house hums")

# ---------------------------------------------------------------- SALON
# "two-storey oval volume; slightly sunken center; off-center instrument anchor;
#  upper gallery; tall arched windows; ceiling medallion" (rooms doc SS1)
add("SM_CenterRing4", 700, -900, 0, 0, "salon circular floor medallion (765 cm) - the M04 landmark",
    "rooms doc SS1: slightly sunken center; house plan: center entry + sitting / circular rug; P0 M04 one oval salon",
    tree="pack", folder="Props/CenterRing/CenterRing4")
add("SM_CenterRing9", 700, -900, 0, 3, "concentric ring 2 (558 cm)",
    "house plan ceiling-score logic: 3-5 concentric staff-like rings", tree="pack", folder="Props/CenterRing/CenterRing9")
add("SM_CenterRing10", 700, -900, 0, 6, "concentric ring 3 (558 cm)",
    "house plan ceiling-score logic", tree="pack", folder="Props/CenterRing/CenterRing10")
add("SM_CenterRing13", 700, -900, 0, 9, "concentric ring 4 (397 cm)",
    "house plan ceiling-score logic", tree="pack", folder="Props/CenterRing/CenterRing13")
add("SM_CenterRing5", 700, -900, 0, 12, "central rosette (374 cm)",
    "house plan ceiling-score logic: central rosette", tree="pack", folder="Props/CenterRing/CenterRing5")
add("SM_Platform", 1000, -1300, 0, 0, "off-centre instrument anchor dais",
    "rooms doc SS1: off-center instrument anchor")
add("SM_Carpet3", 250, -780, 0, 0, "entry rug by the story door (245 cm)",
    "P0 M03/M04 transition; house plan: center entry + sitting / circular rug")
add("SM_Desk2", 300, -300, 0, 0, "console table, east wall (165x76x88)",
    "house plan: center/right writing desk / field-journal worktable")
add("SM_Globe2", 300, -300, 0, 88, "globe on the console table",
    "rooms doc SS1: the salon should feel like Melusina's study")
add("SM_Lantern", 380, -1400, 0, 0, "salon lantern",
    "P0 M04: the house hums; REF_01 board: lamps")
add("SM_LanternGlass", 380, -1400, 0, 58, "salon lantern glass",
    "P0 M04")
add("SM_Wall_Lamp", 70, -1200, 90, 0, "sconce on the salon west wall",
    "REF_01 board: porch depth, shell crests, lamps")
add("SM_Wall_Lamp_Glass", 70, -1200, 90, 43, "sconce glass",
    "REF_01 board: lamps")
add("SM_Shelf6", 850, -1700, 0, 0, "long low bench, south wall (194 cm)",
    "rooms doc SS1: gallery / seating edge")
add("SM_Box", 850, -1700, 0, 28, "box on the bench",
    "rooms doc SS1")
add("SM_Kit_Ornament_C", 300, -1750, 0, 0, "salon wall ornament",
    "REF_02 board: Floor, mouldings & ornaments")
add("SM_Entrance", 1320, -1600, 0, 0, "the front doors (143x177x700) - M05 exit",
    "P0 M05 front door; REF_01 board: front door; house plan GN_MH_05 hero door")
add("SM_Floor_Pannel", 300, -1450, 0, 0, "floor inlay panel (520 cm)",
    "house plan: floor inset ring", tree="pack", folder="Building/Floor2F/Floor2F")
add("SM_Floor_Pannel2", 1150, -1450, 0, 0, "floor inlay panel (322 cm)",
    "house plan: floor inset ring", tree="pack", folder="Building/Floor2F/Floor2F2")
add("SM_Floor_Pannel3", 500, -1600, 90, 0, "floor inlay strip, south (281x1057)",
    "house plan: floor inset ring", tree="pack", folder="Building/Floor2F/Floor2F3")

# ---------------------------------------------------------------- STAIRCASE
# P0 M04: "frame the grand staircase without requiring the player to go upstairs"
add("SM_Stair1", 1250, -300, 0, 0, "stair tread 1",
    "P0 M04: frame the grand staircase", tree="pack", folder="Building/Stair1")
add("SM_Stair2", 1250, -560, 0, 0, "stair tread 2",
    "P0 M04", tree="pack", folder="Building/Stair2")
add("SM_Stair3", 1250, -830, 0, 0, "stair tread 3",
    "P0 M04", tree="pack", folder="Building/Stair3")
add("SM_Rail", 950, -560, 0, 0, "balustrade run (945 cm)",
    "REF_02 board: Arches, balustrades & railings", tree="pack", folder="Building/Rail")
add("SM_Rail2", 860, -250, 0, 0, "balustrade return",
    "REF_02 board: Arches, balustrades & railings", tree="pack", folder="Building/Rail2")
add("SM_Stair_Pillar1", 1080, -250, 0, 0, "stair newel",
    "REF_02 board: Arches, balustrades & railings", tree="pack", folder="Building/Stair_Pillar1")
add("SM_Stair_Pillar5", 1250, -900, 0, 0, "stair newel",
    "REF_02 board: Arches, balustrades & railings", tree="pack", folder="Building/Stair_Pillar5")
add("SM_Stair_Pillar11", 1250, -160, 0, 0, "stair newel block",
    "REF_02 board: Arches, balustrades & railings", tree="pack", folder="Building/Stair_Pillar11")
add("SM_Pillar", 120, -1700, 0, 0, "salon column (736 cm)",
    "REF_02 board: Columns & pillars", tree="pack", folder="Building/Pillar")
add("SM_Wood_Pillar", 1330, -1750, 0, 0, "tall timber post (1690 cm)",
    "REF_02 board: Columns & pillars", tree="pack", folder="Building/Wood_Pillar")
add("SM_Wall", 1330, -1100, 90, 0, "salon wall screen (386 cm)",
    "P0 M04: house identity reads with FX disabled", tree="pack", folder="Building/Wall")
add("SM_WoodWall", 700, -1770, 0, 0, "low timber wall, south (969 cm)",
    "REF_02 board: Floor, mouldings & ornaments", tree="pack", folder="Building/WoodWall")


# ---------------------------------------------------------------- ECV LAYER
# Enchanted Interiors (Kitbash3D, UE4.26+) converted onto M_Master_Toon_Universal
# on 2026-10-21, imported at /Game/EnchantedInteriors. This layer sits ON TOP of
# the Magician's Library base dressing: it adds the warmth, the candles and the
# "cute" layer the P0 house leg needs, without touching a single base placement.
# Every entry below is a NEW actor (Jev additive policy 2026-10-21:
# NEW_ASSETS_ONLY_NO_EXISTING_MUTATION).
#
# ECV prop meshes are named <ActorName>_Main under /Game/EnchantedInteriors/Geometries.
# surface_z is the height the prop's LOWEST POINT rests at, so a hanging piece uses
# it as the height of its bottom: the salon's shell is 563 cm tall, so a 335 cm
# chandelier hangs from 200 cm (top at 535 cm) and a 117 cm one from 330 cm.

# --- bedroom: a candle on the bedside table, a bookcase, a second trunk, a bowl
add("KB3D_ECI_PropCandleHolder_A_Main", -880, -250, 0, 77,
    "candle cluster on the bedside table (48x22x77)",
    "rooms doc SS2 domestic imperfection; house plan: ribbons, sheet music, jars - the bedroom is lived in",
    tree="ecv")
add("KB3D_ECI_PropBookShelf_A_Main", -560, -930, 0, 0,
    "free-standing bookcase, south-east of the bedroom",
    "house plan GN_MH_11: built-in shelf following wall curvature - this one is the free-standing companion",
    tree="ecv")
add("KB3D_ECI_PropBookStack_A_Main", -1100, -790, 0, 250,
    "book stack on the west shelf run (top 250 cm)",
    "rooms doc SS2: scholar's clutter breaking the clean system", tree="ecv")
add("KB3D_ECI_PropChest_B_Main", -520, -870, 0, 0,
    "second trunk, south-east corner",
    "rooms doc SS2: the room must feel lived in", tree="ecv")
add("KB3D_ECI_PropAppleBowl_A_Main", -820, -955, 0, 82,
    "small fruit bowl on the writing desk (top 82 cm)",
    "house plan: field-journal worktable; rooms doc SS2 domestic imperfection", tree="ecv")

# --- landing: a lantern by the threshold, a banner pole, a bowl on the pot table
add("KB3D_ECI_PropStandingLantern_A_Main", -400, -450, 0, 0,
    "standing lantern by the threshold (landing side of the shared wall line)",
    "P0 M03 threshold: first reveal of curving pink architecture - a warm pool before the salon",
    tree="ecv")
add("KB3D_ECI_PropBannerPole_A_Main", -240, -700, 0, 0,
    "banner pole in the landing",
    "REF_01 board: porch depth, shell crests, lamps, drapes, flowers", tree="ecv")
add("KB3D_ECI_PropAppleBowl_A_Main", -330, -900, 0, 107,
    "fruit bowl on the plant table pot (top 107 cm)",
    "rooms doc SS2: domestic imperfection in a formal space", tree="ecv")

# --- salon: the chandelier over the M04 landmark, the sitting group, the shelves
add("KB3D_ECI_PropChandelier_A_Main", 700, -900, 0, 200,
    "chandelier hanging over the circular floor medallion (bottom 200 cm, top 535 cm under the 563 cm shell)",
    "P0 M04 landmark: the oval salon's one visual landmark, now lit from above; house plan ceiling-score logic",
    tree="ecv")
add("KB3D_ECI_PropChandelier_C_Main", 1100, -1600, 0, 330,
    "small chandelier by the front doors (bottom 330 cm)",
    "P0 M05: purposeful pause before the exterior reveal - a warm doorway", tree="ecv")
add("KB3D_ECI_PropRoundTable_A_Main", 420, -450, 0, 0,
    "round table, the sitting group in front of the salon entry",
    "house plan: center entry + sitting / circular rug", tree="ecv")
add("KB3D_ECI_PropChair_A_Main", 350, -450, 90, 0,
    "chair at the sitting table",
    "house plan: center entry + sitting / circular rug", tree="ecv")
add("KB3D_ECI_PropAcolyteChair_A_Main", 490, -450, -90, 0,
    "second chair at the sitting table",
    "house plan: center entry + sitting / circular rug", tree="ecv")
add("KB3D_ECI_PropAppleBowl_A_Main", 420, -450, 0, 79,
    "fruit bowl on the sitting table (top 79 cm)",
    "rooms doc SS2: domestic imperfection - a table with something on it", tree="ecv")
add("KB3D_ECI_PropCandleStackLit_A_Main", 330, -300, 0, 88,
    "candle cluster on the console table (top 88 cm)",
    "P0 M04: the house hums - a lit console reads as inhabited", tree="ecv")
add("KB3D_ECI_PropAppleBowl_A_Main", 255, -280, 0, 88,
    "fruit bowl on the console table (top 88 cm)",
    "rooms doc SS2: domestic imperfection", tree="ecv")
add("KB3D_ECI_PropBookShelf_A_Main", 600, -80, 0, 0,
    "bookcase along the salon's north wall",
    "house plan: Melusina's library reaches into the salon; rooms doc SS1 Resonant Salon",
    tree="ecv")
add("KB3D_ECI_PropStandingLantern_A_Main", 980, -1700, 0, 0,
    "standing lantern by the south bench",
    "P0 M04: warm pool at the seated end of the oval salon", tree="ecv")
add("KB3D_ECI_PropBookStack_A_Main", 1060, -1300, 0, 0,
    "book stack on the floor beside the instrument dais",
    "P0 M04: the off-centre instrument dais needs company, not isolation", tree="ecv")


def mesh_bounds(path):
    a = unreal.load_asset(path)
    if a is None:
        return None
    try:
        b = a.get_bounds()
        return {"size": [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)],
                "centre": [round(b.origin.x, 1), round(b.origin.y, 1), round(b.origin.z, 1)]}
    except Exception:
        return None


def actor_z_for(path, surface_z):
    """The mesh pivot is at its local origin; the box centre is `centre`. The mesh
    bottom sits at centre.z - h/2 in local space, so the actor must be lifted by
    -(bottom) to stand the base on `surface_z`."""
    b = mesh_bounds(path)
    if not b:
        return surface_z
    h = b["size"][2]
    bottom = b["centre"][2] - h / 2.0
    return round(surface_z - bottom, 1)


def write_diagram(rows, path):
    """Top-down layout diagram (SVG) - the room footprints plus every placement."""
    W, H = 1700, 1250
    def X(x):
        return 60 + (x + 1250) * 0.60
    def Y(y):
        return 120 + (y + 1900) * 0.60
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
           '<rect width="100%" height="100%" fill="#141018"/>',
           '<text x="30" y="34" fill="#f0e6ff" font-family="Segoe UI" font-size="22">Melusina&#8217;s P0 house &#8212; Magician&#8217;s Library dressing plan (top-down, cm)</text>']
    for name, r in ROOMS.items():
        x0, x1 = r["interior_x"]
        y0, y1 = r["interior_y"]
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#2b2438" stroke="#8f7fb5" stroke-width="2"/>'
                   % (X(x0), Y(y1), (x1 - x0) * 0.60, (y1 - y0) * 0.60))
        out.append('<text x="%.1f" y="%.1f" fill="#b9a8d8" font-family="Segoe UI" font-size="16">%s</text>' % (X(x0) + 8, Y(y1) + 20, name))
    for d in rows:
        cx, cy = X(d["x"]), Y(d["y"])
        col = "#f4b8d0" if d["room"] == "bedroom" else ("#bcd8f4" if d["room"] == "salon" else "#e8d7a8")
        sz = d.get("size") or [60, 60, 60]
        s = max(5.0, min(22.0, (sz[0] or 60) * 0.6 * 0.35))
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="0.75" stroke="#ffffff" stroke-width="1"/>' % (cx, cy, s, col))
        out.append('<text x="%.1f" y="%.1f" fill="#efe6ff" font-family="Segoe UI" font-size="11">%s</text>' % (cx + s + 3, cy + 4, d["mesh_name"]))
    out.append('</svg>')
    path.write_text("\n".join(out), encoding="utf-8")


def room_of(x, y):
    for name, r in ROOMS.items():
        ix, iy = r["interior_x"], r["interior_y"]
        if ix[0] - 40 <= x <= ix[1] + 40 and iy[0] - 40 <= y <= iy[1] + 40:
            return name
    return "threshold"


def build_lookup(root, prefer_prefix=None):
    """mesh name -> object path, for one source tree."""
    out = {}
    for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        sp = str(p).rsplit(".", 1)[0]
        n = sp.rsplit("/", 1)[-1]
        if not n.startswith("SM_"):
            continue
        if prefer_prefix and not sp.startswith(prefer_prefix):
            continue
        out.setdefault(n, sp)
    return out


def layout_ascii(rows, step=100):
    """Coarse ASCII floor plan of the two rooms (git-reviewable, no binary)."""
    lines = []
    for rname in ("bedroom", "salon"):
        r = ROOMS[rname]
        x0, x1 = r["interior_x"]
        y0, y1 = r["interior_y"]
        cells = {}
        for d in rows:
            if d["room"] != rname or not d.get("size"):
                continue
            cx = int((d["x"] - x0) // step)
            cy = int((d["y"] - y0) // step)
            ch = d["mesh_name"].replace("SM_", "")[:1]
            if (cy, cx) in cells:
                cells[(cy, cx)] = "*"
            else:
                cells[(cy, cx)] = ch
        nx = int((x1 - x0) // step) + 1
        ny = int((y1 - y0) // step) + 1
        lines.append("%s  (x %d..%d, y %d..%d, %d cm cells)" % (rname, x0, x1, y0, y1, step))
        for cy in range(ny - 1, -1, -1):
            row = "".join(cells.get((cy, cx), ".") for cx in range(nx))
            lines.append("  y%+5d %s" % (y0 + cy * step, row))
        lines.append("")
    return lines


def main() -> int:
    mode = (os.environ.get("MAGICIANS_MODE") or
            (sys.argv[1].strip().lower() if len(sys.argv) > 1 else "plan"))
    if mode not in ("plan", "apply"):
        mode = "plan"

    canon = build_lookup(CANON)
    pack = build_lookup(PACK)

    rows = []
    for d in D:
        r = dict(d)
        if r["tree"] == "canon":
            r["mesh"] = canon.get(r["mesh_name"])
        elif r["tree"] == "ecv":
            r["mesh"] = "%s/Geometries/%s" % (ECV, r["mesh_name"])
        else:
            r["mesh"] = pack.get(r["mesh_name"])
        if not r["mesh"] and r.get("folder"):
            r["mesh"] = "%s/%s" % (PACK, r["folder"])
        b = mesh_bounds(r["mesh"]) if r["mesh"] else None
        r["size"] = b["size"] if b else None
        r["room"] = room_of(r["x"], r["y"])
        r["actor_z"] = actor_z_for(r["mesh"], r["surface_z"]) if r["mesh"] else r["surface_z"]
        rows.append(r)

    spec = {
        "contract_id": "melodia.melusina_house_p0.dressing.v1",
        "kind": "level_dressing_contract",
        "schema_version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "package": {
            "package_id": "package.melusina_house_p0.dressing",
            "display_name": "Melusina P0 house dressing (Magician's Library)",
            "content_kind": "level_dressing_contract",
            "status": "design_contract_runtime_pending",
        },
        "authority": {
            "level": MAP,
            "route": "POITOU P0 Golden Walk house leg (M00-M05)",
            "authoritative_document": "Docs/Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md (origin/main; absent from some working trees)",
            "house_visual_score": "Docs/References/MelusinasHouse/OriginalDesign/melusinashouseplan_2026-09-02.md",
            "room_plan": "Docs/References/MelusinasHouse/OriginalDesign/MELUSINAS_HOUSE_GN_ROOMS_AND_ACOUSTIC_ARCHITECTURE_2026-09-03.md",
            "reference_boards": "Docs/References/MelusinasHouse/ (REF_01 exterior, REF_02 build sheet, REF_03 cutaway - REF_03 is a corrupt JPEG in git)",
            "prop_source": [
                "Fab 'Magician's Library Environment and VFX Pack' (Coreb Games), imported at /Game/MagicianLabatory - base dressing (tree=canon/pack)",
                "Kitbash3D 'Enchanted Interiors' (UE4.26+), converted onto M_Master_Toon_Universal on 2026-10-21, imported at /Game/EnchantedInteriors - layer on top (tree=ecv)",
            ],
            "note": "Every placement carries the plan role it serves. The house leg is bounded by the P0 score to bedroom -> landing -> oval salon -> front doors; other rooms of the 9-room constellation stay behind closed doors.",
        },
        "layers": {
            "base": {
                "tree": ["canon", "pack"],
                "source": "Magician's Library (canon + Building/CentreRing pack)",
                "role": "the house's architecture and identity: shelves, desk, medallion rings, stair, doors",
            },
            "enchanted_interiors": {
                "tree": ["ecv"],
                "source": "Kitbash3D Enchanted Interiors, converted to M_Master_Toon_Universal",
                "role": "the warm and cute layer on top: chandeliers over the M04 landmark, candle clusters, the sitting group, bookcases, a banner and a lantern",
                "policy": "additive only - no base placement is moved or edited (Jev NEW_ASSETS_ONLY_NO_EXISTING_MUTATION, 2026-10-21)",
            },
        },
        "rooms": ROOMS,
        "placement_rule": "surface_z is the height of the surface the prop's BASE rests on (0 = room floor, 82 = desk top, 186 = shelf top, 107 = pot table top, 95 = candle top). The apply step measures each mesh's bounds and lifts the actor by -(centre.z - height/2) so the base actually sits on that surface.",
        "counts": {
            "placements": len(rows),
            "by_room": {k: sum(1 for r in rows if r["room"] == k) for k in ROOMS},
            "by_layer": {
                "base": sum(1 for r in rows if r.get("tree") in ("canon", "pack")),
                "enchanted_interiors": sum(1 for r in rows if r.get("tree") == "ecv"),
            },
        },
        "layout_ascii": layout_ascii(rows),
        "layout_svg": "Saved/Audit/melusina_house_p0_dressing_layout.svg (local artifact; the repo pre-commit hook refuses .svg, so layout_ascii is the git-reviewable copy)",
        "placements": rows,
        "not_yet_true": [
            "no placement is runtime-proven; this contract certifies nothing until the level is opened in the editor and the route is walked",
            "the house leg's map ownership is still unresolved in the P0 spec (not_yet_true #2): L_MelusinaHouse_P0 is a new, Perforce-open-for-add map with 21 actors, while the convergence plan names /Game/Melodia/Levels/Opening/L_MelusinaMorning as the house path and forbids duplicate Morning maps",
            "the P0 M02 resonant object still needs an EXISTING compatible actor; the candle placed here is the visual candidate, not an interactive",
            "the P0 M04 salon interactable is not supplied by the prop pack; the circular medallion is the landmark, not the interactable",
            "the grand staircase is framed from the Building set but is not a walkable route; P0 M04 only requires it framed",
            "SM_Entrance and the wall-facing ornaments need an orientation check against the room's facing",
            "the Enchanted Interiors layer (tree=ecv) is a DESIGN proposal on top of the base dressing: hanging pieces use surface_z as the HEIGHT OF THEIR LOWEST POINT (the two chandeliers hang at 200 cm and 330 cm so their tops stay under the salon's 563 cm shell), and every ECV mesh still needs a visual check in the editor - the pack was converted onto M_Master_Toon_Universal on 2026-10-21 but has never been lit in this room",
            "KB3D_ECI_PropTableFabric_A_Main was considered for the salon but dropped: it measures 1008 cm long, which is a banquet table, not a companion to the oval salon's instrument dais",
            "the Enchanted Interiors pack does not supply a piano, a music box or a window chime, so P0 M02's resonant object is still open; the candle cluster on the bedside table is the visual candidate, not the interactive",
        ],
    }
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    write_diagram(rows, DIAGRAM)
    print("DRESSING|plan|placements=%d|by_room=%s" % (len(rows), json.dumps(spec["counts"]["by_room"])))
    print("DRESSING|spec=%s|diagram=%s" % (SPEC.name, DIAGRAM.name))

    if mode != "apply":
        return 0

    # ---- apply: place the dressing in the house level
    # SAFETY: never reload the level if it is already open - reloading would
    # discard whatever the owner has unsaved in this session.
    world = unreal.EditorLevelLibrary.get_editor_world()
    cur_name = world.get_path_name() if world else ""
    if not cur_name.startswith(MAP):
        unreal.EditorLevelLibrary.load_level(MAP)
        world = unreal.EditorLevelLibrary.get_editor_world()

    # IDEMPOTENCE: an actor that is already there is MOVED to the corrected
    # position, never duplicated. The level already carries a first pass of this
    # dressing, and a re-apply must correct it in place.
    existing = {}
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            lbl = a.get_actor_label()
        except Exception:
            continue
        if lbl.startswith("Mag_"):
            existing[lbl] = a

    spawned, moved, skipped = [], [], []
    for r in rows:
        mesh = unreal.load_asset(r["mesh"])
        if mesh is None:
            skipped.append({"mesh": r["mesh"], "reason": "asset not found"})
            continue
        loc = unreal.Vector(r["x"], r["y"], r["actor_z"])
        rot = unreal.Rotator(0, 0, r["rot_z"])
        label = "Mag_%s_%s" % (r["room"], r["mesh_name"])
        actor = existing.get(label)
        if actor is not None:
            try:
                actor.set_actor_location(loc, False, True)
                actor.set_actor_rotation(rot, False)
                comp = actor.static_mesh_component
                if comp is not None and comp.static_mesh != mesh:
                    comp.set_static_mesh(mesh)
                moved.append({"mesh": r["mesh"], "label": label,
                              "loc": [r["x"], r["y"], r["actor_z"]], "rot_z": r["rot_z"],
                              "room": r["room"], "role": r["role"]})
                continue
            except Exception as ex:
                skipped.append({"mesh": r["mesh"], "reason": "move failed: %s" % ex})
                continue
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        if actor is None:
            skipped.append({"mesh": r["mesh"], "reason": "spawn failed"})
            continue
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        actor.set_actor_label(label)
        spawned.append({"mesh": r["mesh"], "label": actor.get_actor_label(),
                        "loc": [r["x"], r["y"], r["actor_z"]], "rot_z": r["rot_z"],
                        "room": r["room"], "role": r["role"]})
    saved = False
    try:
        unreal.EditorLevelLibrary.save_current_level()
        saved = True
    except Exception as ex:
        saved = str(ex)[:200]
    out = {"generated": datetime.now(timezone.utc).isoformat(), "mode": mode,
           "level": MAP, "spawned": len(spawned), "moved": len(moved),
           "skipped": skipped, "save": saved, "placements": spawned + moved}
    RECEIPT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("DRESSING|apply|spawned=%d|moved=%d|skipped=%d|save=%s"
          % (len(spawned), len(moved), len(skipped), saved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

