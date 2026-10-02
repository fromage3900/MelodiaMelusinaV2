"""Jev decision packet - Melusina animation pipeline convergence with outfit mechanics, 2026-10-02.
Closed candidate sets only. Jev selects; Monolith/Claireon/Blender execute; readback proves state."""
import json, os, sys
STATE = {
 "outfit_mechanics": "Wardrobe = material slots on ONE body mesh (Magical Transform dissolves slot opacity) + leader-pose garment slots (Shirt/Skirt/Boots/Accessories) that must share SK_Melusina_Skeleton (465 bones; IsGarmentSkeletonCompatible refuses others). Hat/Hair are separate components.",
 "inventory": "83 AnimSequences under Melusina; 77 on SK_Melusina_Skeleton, 5 on SK_MelusinaRigARP_V2Test, 1 stray MEL_seg_chest. 10 retargeters (4 live Melusina routes: Mocap, Quaternius, Sparrow, UE4Mannequin archived).",
 "gate_measured": "61 production clips: root_x height OK on all except the 2 caster clips I imported (8880 vs 88 - Quaternius retarget unit error, fixed by manual root scale). c_* arm/finger controls are STATIC in every proven clip (parented to root). forearm_twist bones are STATIC in every proven clip. Proven hand-roll peaks: locomotion 10-52deg, bow-draw v2 79deg, Death 105deg. Sparrow clips 85-95deg after I added twist/control rewrites the baseline never had.",
 "glove_facts": "Blender hero blend: glove carries ~36% skin weight on c_* finger controls and 10% forearm_twist. In UE the proven clips keep those static and gloves read fine, so UE-side weights likely differ from the blend; unverified.",
 "owner_ground_truth": "Owner states shoulder/retarget fix exists in the target retarget pose (RTG_UE4Mannequin_To_Melusina) and the months-stable baseline must not be regressed. Sparrow retargeter now carries that target pose.",
 "tools": "Blender 5.2, Houdini 22 hython, Cascadeur installed. Claireon AnimPose evaluation works non-PIE.",
}
Q = {
 "clip_contract": ("What is the runtime clip contract?", ["DEFORM_ONLY_NO_CONTROL_OR_TWIST_REWRITE","DRIVE_CONTROLS_AND_TWIST_ON_EVERY_CLIP","CASE_BY_CASE"]),
 "sparrow_action": ("What happens to the Sparrow clips I modified?", ["RERUN_PURE_RETARGET_WITH_FIXED_TARGET_POSE_NO_REWRITES","KEEP_CURRENT_TWIST_AND_CONTROL_REWRITES","DROP_SPARROW_USE_V2_BOWDRAW"]),
 "caster_action": ("What happens to the two caster clips?", ["KEEP_ROOT_FIX_ONLY_STRIP_CONTROL_REWRITE","KEEP_ALL_CURRENT","REPLACE_WITH_PROVEN_QUATERNIUS_V2FIXED_CLIPS"]),
 "glove_next": ("Next step to find the glove cause?", ["COMPARE_UE_MESH_SKIN_WEIGHTS_VIA_BLENDER_EXPORT_OF_UE_FBX","MORE_CLIP_EDITS","REWEIGHT_GLOVE_NOW"]),
 "gate_lane": ("How is the pipeline locked?", ["COMMIT_UNIFORM_GATE_TOOL_AND_BASELINE_THRESHOLDS","DOCS_ONLY","NO_GATE"]),
}
from typesafe_sdk import TypeSafeClient
from typesafe_sdk._core.questions import Choice
qs = {k: Choice(instructions=v[0], criteria={o: None for o in v[1]}) for k, v in Q.items()}
with TypeSafeClient() as c:
    r = c.system_one(state={"verified_state": STATE}, questions=qs)
out = {"schema":"melodia.jev.converge.v1","source":"jev-live","model":str(getattr(r,"model",None)),
       "answers":{k:{"choice":a.choice,"reason":getattr(a,"reason",None)} for k,a in r.answers.items()}}
d = "Saved/Audit/ArcheryGoalSession_20261001/JevConverge_20261002.json"
json.dump(out, open(d,"w"), indent=2); print(json.dumps(out, indent=1))
