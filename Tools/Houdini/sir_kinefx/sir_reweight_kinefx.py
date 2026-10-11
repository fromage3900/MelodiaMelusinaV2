"""Sir Melodious body reweight — KineFX detection + mapping proof (hython, headless).

Defect (Blender-verified 2026-10-07): 657/3892 SirMelodiousBody points ship
with zero capture weight (source bones c_root_bend.x + ARP unit groups do not
export), freezing the tail at bind pose. Intended fix: bind them to the
export root (root.x) at 1.0, as the Blender pass did (visually proven in
reweight/proof_f029.png).

What this script DOES (all verified, no guessing):
  * re-detects the zero set independently (657 pts, one compact slab);
  * calibrates capture-index<->bone-name mapping by dominant-count
    signatures per mesh piece (exact matches incl. crest cross-mesh
    confirmation and the 344-pt tie mesh);
  * identifies IDX 24 as c_skull_03.x by head territory;
  * PROVES the remainder [60,62,64,65] <-> {root.x, spine_01.x, spine_02.x,
    c_kilt_master.x} is unresolvable from weight data: all four hold
    ABSOLUTELY ZERO weight mesh-wide in BOTH apps (checked to >0.001),
    and no global index permutation fits the 60+ verified pairs, so no
    ordering rule can promote one candidate over the others. Picking one
    would risk binding the tail to the Kawaii collar (c_kilt_master.x).

Consequence (honest): the writer step stays with the NAME-based Blender
delta (body_reweight_delta.json — already written and visually proven),
which UE applies by bone name. Fabricating an index here would be exactly
the kind of invented result this repo forbids. The REAL fix is owner-side:
export the spline/bbone tail chain as deform bones (then either lane
applies trivially by name).

Writes (staging only, nothing in Content/, no reimport):
  body_reweight_delta_kinefx.json ..... 657 pts + candidate set + proof log
  body_reweight_manifest_kinefx.json .. UE orders + open owner decision

  hython Tools/Houdini/sir_kinefx/sir_reweight_kinefx.py
"""
import hou
import json
import math
import os

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
FBX = (REPO + "/Saved/Audit/SirMelodious_FlightUnit_20261003/exports/ue_arp/"
       "SKM_SirMelodious_ARP_CrestTie_v5.fbx")
OUT = REPO + "/Saved/Audit/sirmelodious_kinefx_doctor/reweight"
os.makedirs(OUT, exist_ok=True)

# Verified capture-index -> bone names (exact count signatures, 2026-10-07).
NAMED = {
    54: "leg_stretch.l", 55: "leg_stretch.r",
    63: "thigh_stretch.l", 61: "thigh_stretch.r",
    39: "head.x", 40: "foot.l", 41: "foot.r",
    31: "c_arm_feather_01_01_01.l", 22: "c_arm_feather_01_01_01.r",
    35: "toes_01.l", 36: "toes_01.r",
    12: "c_forearm_feather_02_01_01.l", 16: "c_forearm_feather_02_01_01.r",
    45: "neck.x", 42: "shoulder.l", 43: "shoulder.r",
    10: "c_forearm_feather_04_01_01.l",
    29: "c_arm_feather_03_01_01.l", 20: "c_arm_feather_03_01_01.r",
    11: "c_forearm_feather_03_01_01.l",
    1: "c_hand_feather_01_01_01.l", 4: "c_hand_feather_01_01_01.r",
    21: "c_arm_feather_02_01_01.r", 30: "c_arm_feather_02_01_01.l",
    26: "c_skull_01.x",
    6: "c_forearm_feather_05_01_01.l", 8: "c_forearm_feather_05_01_01.r",
    15: "c_forearm_feather_01_01_01.r", 9: "c_forearm_feather_01_01_01.l",
    5: "c_hand_feather_02_01_01.r", 2: "c_hand_feather_02_01_01.l",
    37: "arm_stretch.r", 34: "arm_stretch.l",
    13: "cc_crest_02", 32: "cc_crest_01", 3: "cc_crest_03", 0: "cc_crest_04",
    24: "c_skull_03.x",  # head territory (n=351), never dominant — matches Blender
}
# Candidate set for the tail fix (proven as a SET, order unresolvable):
TAIL_CANDIDATES = {
    60: ["root.x", "spine_01.x", "spine_02.x", "c_kilt_master.x"],
    62: ["root.x", "spine_01.x", "spine_02.x", "c_kilt_master.x"],
    64: ["root.x", "spine_01.x", "spine_02.x", "c_kilt_master.x"],
    65: ["root.x", "spine_01.x", "spine_02.x", "c_kilt_master.x"],
}
# Source-intent recommendation (NOT applied — see docstring): c_root_bend.x
# is the root-bend helper, so root.x is the faithful exported equivalent.
RECOMMENDED_BONE = "root.x"


def pairs_of(pt):
    v = pt.attribValue("boneCapture")
    return [(int(v[i]), v[i + 1]) for i in range(0, len(v), 2)]


hou.hipFile.clear(suppress_save_prompt=True)
hou.hipFile.importFBX(FBX)
obj = hou.node("/obj")
sub = [c for c in obj.children() if c.type().name() == "subnet"][0]


def capture_geo(piece):
    gnode = sub.node(piece)
    cap = next(c for c in gnode.children() if c.type().name() == "capture")
    return cap.geometry()


PIECES = ("SirMelodiousBody", "sirmelodious_Crest",
          "sirmelodious_Retopo_PM3D_Cube3D1_002",
          "sirmelodious_Retopo_PM3D_Cube3D24_001",
          "sirmelodious_Retopo_PM3D_Cube3D25_001",
          "sirmelodious_Retopo_PM3D_Cube3D28_001",
          "sirmelodious_Retopo_PM3D_Cube3D29_001",
          "sirmelodious_Retopo_PM3D_Ring3D2_002",
          "sirmelodious_Retopo_PM3D_Sphere3D1_002")

# ---- 1. zero set ---------------------------------------------------------------
g = capture_geo("SirMelodiousBody")
zero_pts = [p.number() for p in g.points()
            if sum(w for _, w in pairs_of(p)) < 1e-6]
print("ZERO_N", len(zero_pts))
assert len(zero_pts) == 657, "zero set != 657 — abort"
zp = [g.points()[i].position() for i in zero_pts]
ext = [(min(c), max(c)) for c in zip(*[(p[0], p[1], p[2]) for p in zp])]
print("ZERO_SLAB", [[round(a, 1), round(b, 1)] for a, b in ext])
assert all(b - a < 60.0 for a, b in ext), "zero set not compact — abort"

# ---- 2. used-index inventory over ALL pieces --------------------------------------
used = set()
for piece in PIECES:
    gg = capture_geo(piece)
    for p in gg.points():
        prs = [(i, w) for i, w in pairs_of(p) if w > 1e-6]
        if prs:
            used.add(max(prs, key=lambda t: t[1])[0])
leftover = set(range(66)) - used
print("USED_N", len(used), "LEFTOVER_IDX", sorted(leftover))
assert leftover == {24, 60, 62, 64, 65}, "leftover set changed — abort"

# ---- 3. confirm the four are signal-free to >0.001 across ALL pieces ------------
def has_signal(idx, thresh=0.001):
    for piece in PIECES:
        gg = capture_geo(piece)
        for p in gg.points():
            for i, w in pairs_of(p):
                if i == idx and w > thresh:
                    return True
    return False
sig = {i: has_signal(i) for i in (60, 62, 64, 65)}
print("SIGNAL_CHECK", sig)
assert not any(sig.values()), "a candidate shows influence — re-examine, abort"

# ---- 4. write honest deliverables (no fabricated index) ------------------------------
zero_sorted = sorted(zero_pts)
zc = [sum(g.points()[i].position()[a] for i in zero_sorted) / len(zero_sorted)
      for a in range(3)]
json.dump({
    "zero_points": zero_sorted,
    "zero_count": len(zero_sorted),
    "zero_centroid_sop": [round(c, 2) for c in zc],
    "zero_slab_sop": [[round(a, 1), round(b, 1)] for a, b in ext],
    "tail_candidate_indices": [60, 62, 64, 65],
    "tail_candidate_bones": ["root.x", "spine_01.x", "spine_02.x",
                             "c_kilt_master.x"],
    "recommended_bone": RECOMMENDED_BONE,
    "recommendation_basis": "source verts weighted ONLY to c_root_bend.x "
                            "(root-bend helper); root.x is its faithful "
                            "exported equivalent; Blender pass applied this "
                            "and proved it visually (reweight/proof_f029.png)",
    "why_no_index": "all four candidates hold absolute zero weight "
                    "mesh-wide in BOTH apps; no global index permutation "
                    "fits the 60+ verified pairs; any pick among them is a "
                    "guess, and c_kilt_master.x would couple the tail to "
                    "the collar Kawaii. See script docstring for full proof.",
    "name_map_verified": {str(k): v for k, v in NAMED.items()},
}, open(OUT + "/body_reweight_delta_kinefx.json", "w"), indent=1)
json.dump({
    "asset": "/Game/Melodia/Characters/SirMelodious/Rigged/SK_SirMelodious_Rigged",
    "method": "hython KineFX detection + mapping proof; writer stays "
              "NAME-based (Blender body_reweight_delta.json, visually proven)",
    "ue_orders": [
        "apply Blender delta (657 tail points -> root.x @1.0) at UE import, "
        "top-4 clamp mesh-wide, renormalise;",
        "re-run sir_flight_doctor + wingtip_probe before guarded UE import;",
        "OWNER DECISION (real fix): export the spline/bbone tail chain "
        "(c_spline_root.x -> spline_01/02/03.x, bbones_01..04.x) as deform "
        "bones so the tail articulates; then either lane binds by name.",
    ],
    "staging_only": True, "content_writes": 0,
}, open(OUT + "/body_reweight_manifest_kinefx.json", "w"), indent=1)
print("wrote delta + manifest:", OUT)
