"""Jev packet - P0 close-out audit, 2026-10-02. Closed candidate sets; Jev selects only; tools execute; readback proves."""
import json
STATE = {
 "landed_today": "Branch integration/merge-origin-main (100 commits ahead, 0 behind origin/main) pushed; PR #404 open into main (direct push to main is blocked by the pre-push hook). 6 merge conflicts resolved (docs->origin, BP/actors->ours). NOT built from scratch after merge.",
 "verified_in_pie_today": "WaveHarp loop: aim stance, tap + charged shots spawn arrows, Sparrow draw reads as archery with harp->bow morph, clean Sparrow/caster retargets (twist/control bones static per baseline, uniform gate tool). Sir + Choral Sheep ABPs had output_connected=false (never animated) - fixed, state machines now live. Eye attach: ambiguity bug fixed; an intermittent detach to socket None is UNEXPLAINED. Owner reports he has done real WASD himself.",
 "doc_vs_asset_drift": "CURRENT_STATE (09-28) claims Sir's ABP driver wired and all 4 states play clips; live audit today found output_connected=false and a frozen Sir. Docs run ahead of assets; claims need a live readback.",
 "owed_from_state_doc": "stock-then-GOOD/PERFECT damage ladder numbers; lock-persistence live probe (Quill InputDisable re-lock); packaged build + 60fps (editor-PIE baseline FAIL on 60 floor) + showcase gates; Sir shoulder perch / BP_SirPerch placement (none placed in any level); P0 dungeon loop with melody slimes (MelodiaDungeonRunCoordinator placed in no map); issue #51 narrative-record atomicity (draft PR #144); automation 97/99 headless (2 known); Morning edits unsubmitted in p4; Perforce server currently down.",
 "constraints": "Git law: origin/main canonical, no direct main pushes, no force; build with closed editor; editor OOM crashes under memory pressure (commit 55/71 GB, 8 GB pagefile); never full property dumps on the live editor; materials = instances of existing masters.",
}
Q = {
 "p0_done_definition": ("What is the P0 definition of done for close-out?", ["PACKAGED_BUILD_PLUS_PLAYED_LOOP_EVIDENCE","EDITOR_PIE_LOOP_EVIDENCE_ONLY","DOCS_AND_GATE_LEDGER_ONLY"]),
 "first_blocker": ("What is the first blocker to clear?", ["BUILD_VERIFY_MERGED_TREE_CLOSED_EDITOR","SIR_SHOULDER_PERCH","DAMAGE_LADDER_NUMBERS","DUNGEON_SLIME_LOOP"]),
 "second_blocker": ("What is second, after the first is cleared?", ["DAMAGE_LADDER_NUMBERS","SIR_SHOULDER_PERCH","PACKAGED_BUILD_AND_60FPS","DUNGEON_SLIME_LOOP"]),
 "docs_drift": ("How are doc/asset drift claims handled from now?", ["EVERY_STATE_CLAIM_GETS_A_LIVE_READBACK_RECEIPT","TRUST_DOCS","REWRITE_ALL_DOCS_NOW"]),
 "eye_detach": ("The intermittent eye detach is unexplained; what now?", ["INSTRUMENT_WITH_A_RUNTIME_ATTACH_LOG_AND_REPRODUCE","SHIP_AS_IS","REATTACH_EVERY_TICK"]),
}
from typesafe_sdk import TypeSafeClient
from typesafe_sdk._core.questions import Choice
qs = {k: Choice(instructions=v[0], criteria={o: None for o in v[1]}) for k, v in Q.items()}
with TypeSafeClient() as c:
    r = c.system_one(state={"verified_state": STATE}, questions=qs)
out = {"schema":"melodia.jev.p0_closeout.v1","source":"jev-live","model":str(getattr(r,"model",None)),"answers":{k:{"choice":a.choice,"reason":getattr(a,"reason",None)} for k,a in r.answers.items()}}
json.dump(out, open("Saved/Audit/ArcheryGoalSession_20261001/JevP0Closeout_20261002.json","w"), indent=2); print(json.dumps(out, indent=1))
