"""Cascadeur secondary-motion pass for Sir Melodious (runs INSIDE Cascadeur).

Copy this file to a Cascadeur scripts folder, then run it from the Cascadeur
command line / script runner with an empty 24 fps scene open. It imports the
v6 ARP mesh FBX as the scene and each v6 clip FBX as animation takes, using
only documented csc.fbx.FbxLoader calls (import_scene / import_animation).

After import (manual, interactive — physics tuning is an artist call):
  1. Quick Rigging Tool on deform bones only (arm/forearm/hand + feather
     chains, crest cc_crest_01..04, tie cc_tie_01..03, legs). Mirror L/R.
  2. Animation Unbaking on the imported 24 fps takes so the baked ARP keys
     become editable intervals.
  3. AutoPhysics preview, then Secondary Motion slider on feather chains
     (overlap on downstroke), crest tip lag, tie swing. Small values first:
     feathers are 22 light chains, not limbs.
  4. Export FBX per take (Cascadeur cm, 24 fps, -Z forward to match the UE
     route) back to Saved/Audit/.../exports/cascadeur/ for the guarded UE
     animation-only import onto the frozen skeleton.

Scale note: Cascadeur works in centimeters; Blender-meter FBXs arrive x100.
The v6 ARP FBXs are Blender exports — if Sir arrives giant, that is the
documented Blender->Cascadeur unit trap, NOT a new defect. Fix at import
scale, never by re-authoring the rig. (Same trap class as the Houdini
scale_gate HOLD in doctor_report_sir_flight.json.)
"""
import os

# --- edit these two lines to point at the staging exports -------------------
MESH_FBX = (
    "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/"
    "SirMelodious_FlightUnit_20261003/exports/ue_arp/"
    "SKM_SirMelodious_ARP_CrestTie_v5.fbx"
)
CLIP_DIR = (
    "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/"
    "SirMelodious_FlightUnit_20261003/exports/ue_arp"
)
CLIPS = [
    "A_Sir_Fly_Loop_v6_ARP.fbx",
    "A_Sir_Hover_Idle_v6_ARP.fbx",
    "A_Sir_Glide_v6_ARP.fbx",
    "A_Sir_Takeoff_v6_ARP.fbx",
    "A_Sir_Land_v6_ARP.fbx",
]
# -----------------------------------------------------------------------------

import csc  # noqa: E402  (Cascadeur in-app API)


def _loader(scene):
    app = csc.app.get_application()
    tools = app.get_tools_manager()
    tool = tools.get_tool("FbxSceneLoader")
    return tool.get_fbx_loader(scene)


def run(scene):
    loader = _loader(scene)
    mesh = MESH_FBX.replace("\\", "/")
    loader.import_scene(mesh)
    print("[sir] mesh imported: " + mesh)
    for clip in CLIPS:
        path = os.path.join(CLIP_DIR, clip).replace("\\", "/")
        if os.path.exists(path):
            loader.import_animation(path)
            print("[sir] animation imported: " + path)
        else:
            print("[sir] MISSING (skipped): " + path)
    print("[sir] done. Set 24 fps if needed, then Quick Rig -> Unbake -> "
          "AutoPhysics per Docs/Production/SIR_CASCADEUR_LANE_2026-10-07.md")
