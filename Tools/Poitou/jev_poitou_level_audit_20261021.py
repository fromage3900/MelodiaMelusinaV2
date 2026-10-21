"""JEV DECISION PACKET - Poitou level restore + additive policy, 2026-10-21.

Closed candidate sets only. Jev selects; it does not mutate Unreal. Execution
goes through the existing owner lanes and is proved by the headless cook
check, per Docs/Production/JEV_CANONICAL_WORKFLOW.md section 5.

Why this packet exists
----------------------
On 2026-10-21 a session expanded the Poitou HDA (a shared masonry kit, seven
generators, an in-theme repoint of 12,572 instances) and, while doing so,
MUTATED 18 existing Poitou mesh packages in Content/.  The level
L_Poitou_v2 then stopped producing content: its Poitou_Layout_v6 actor's
Houdini cook finishes "with errors" while the other ten Houdini actors cook
clean.  The owner had a working game level before that session.

Everything below is VERIFIED this session, on disk:

  * the level map L_Poitou_v2.umap was NOT modified; the editor session was
    never touched; the Houdini Engine asset
    /Game/EnvSandbox/Poitou/HDA/poitou_layout_live_v6.uasset was NOT modified
    (mtime 2026-10-20 23:20);
  * the Poitou_Layout_v6 actor cooks the EMBEDDED HDA
    "poitou_layout_roomshell_candidate" and that cook finishes "with errors"
    - reproduced headlessly by Tools/Editor/poitou_he_cook_check.py, which
    loads the map (the Houdini Engine plugin cooks on load) and reads the
    result per actor out of the log;
  * the ONLY Content/ changes in the session were: 18 Poitou mesh packages
    re-saved with their slot-0 material rebound; 5 of those 18 grown to two
    material slots; and 8 new material assets created (7 MIs plus
    M_Poitou_Stone_Plinth);
  * a pre-session snapshot taken at 18:34 records the exact prior state of
    all 18 meshes: every one had exactly ONE static material slot, with a
    known original material. It is the restore source of truth;
  * the HDA-side SOURCES changed (Tools/Poitou only): inst.vex repointed off
    the retired Kenney pack onto in-theme assets with re-derived divisors, a
    new shared kit plus seven generators, and the near poplar rows' instance
    removed because their generated replacement is not wired to the level yet;
  * the Houdini Engine plugin's own scratch, Content/HoudiniEngine/Temp/,
    was written by the headless cooks. Content/HoudiniEngine/Bake/ is
    referenced by the level and was NOT touched;
  * the Poitou meshes are open for ADD in Perforce (they were created
    locally on 2026-10-20 and never submitted), so `p4 revert` would DELETE
    them and must not be run. The restore has to be done in Unreal.

The question Jev is asked is not "what is wrong" - that is an evidence
question with a deterministic answer. It is: given the verified state, what
is the correct ORDER of restore, what is the correct proof, and what is the
standing rule for the rest of this programme.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

STATE = {
    "verified_at": "2026-10-21 evening, disk + log evidence",
    "incident": (
        "A session expanded the Poitou HDA and in the same session mutated 18 existing "
        "Poitou mesh packages in Content/ (slot-0 material rebound, five of them grown to "
        "two material slots). The level L_Poitou_v2 stopped producing content: its "
        "Poitou_Layout_v6 Houdini cook finishes 'with errors' and spawns nothing, while "
        "the other ten Houdini actors in the same level cook clean."
    ),
    "untouched": [
        "L_Poitou_v2.umap (not modified)",
        "the owner's editor session (never closed, never reloaded, never written)",
        "poitou_layout_live_v6.uasset, the Houdini Engine asset (mtime 2026-10-20 23:20)",
        "Content/HoudiniEngine/Bake/ (referenced by the level)",
        "the HDA graph itself is intact on disk in the asset",
    ],
    "changed": [
        "18 Poitou mesh packages re-saved with slot 0 rebound to a different material",
        "5 of those 18 grown to two static material slots (crumbled wall, broken arch, buttress stub, bridge parapet, village well)",
        "8 new material assets created (additive; not yet in Perforce)",
        "Tools/Poitou HDA sources: inst.vex repointed, shared kit + 7 generators, near poplar instance removed",
        "Content/HoudiniEngine/Temp/ plugin scratch written by headless cooks",
    ],
    "restore_source_of_truth": (
        "Saved/Audit/PoitouConvergence_20261020/poitou_mesh_slots.json - an 18:34 snapshot "
        "recording every one of the 18 meshes with exactly ONE slot and its original "
        "material. Restoring from it is mechanical and needs no judgement."
    ),
    "verification_tool": (
        "Tools/Editor/poitou_he_cook_check.py - headless; loads the map, which makes the "
        "Houdini Engine plugin cook every Houdini actor, then reads each actor's cook "
        "result out of the log. Current result: Poitou_Layout_v6 = ERROR, "
        "Poitou_RoomShell_07 = OK. It is deterministic and needs no editor."
    ),
    "perforce_hazard": (
        "The Poitou meshes are open for ADD, so `p4 revert` would delete them. Any "
        "restore must be done in Unreal, and the restore must be verified before submit."
    ),
    "owner_state": (
        "The owner had a working game level before the session and does not now. The "
        "owner's standing instruction to agents is that this project is NOT a sandbox "
        "for experimentation and that work must be ADDITIVE."
    ),
}

QUESTIONS: dict[str, dict[str, Any]] = {
    "restore_order": {
        "question": (
            "Given the verified state, which restore action should execute FIRST to bring "
            "the level back to its pre-session content state with the least risk of losing "
            "work?"
        ),
        "criteria": {
            "RESTORE_ALL_18_FROM_SNAPSHOT": 0,
            "TRIM_5_SLOT_COUNT_ONLY": 0,
            "CLEAR_PLUGIN_SCRATCH_ONLY": 0,
            "REIMPORT_EMBEDDED_HDA": 0,
            "HOLD_FOR_OWNER": 0,
        },
    },
    "proof": {
        "question": (
            "What proves the level is intact, given the owner needs certainty this time and "
            "the editor is a live session that must not be disturbed?"
        ),
        "criteria": {
            "HEADLESS_COOK_CHECK_ONLY": 0,
            "OWNER_VISUAL_ONLY": 0,
            "HEADLESS_COOK_CHECK_THEN_OWNER_VISUAL": 0,
        },
    },
    "additive_policy": {
        "question": (
            "What is the standing rule for the rest of this programme when authoring or "
            "rebinding materials and assets on a level that is live and working?"
        ),
        "criteria": {
            "NEW_ASSETS_ONLY_NO_EXISTING_MUTATION": 0,
            "NEW_ASSETS_PLUS_OWNER_APPROVED_BINDING": 0,
            "TOOLING_ONLY_UNTIL_OWNER_SIGN_OFF": 0,
        },
    },
    "scope": {
        "question": (
            "What may proceed on the Poitou HDA programme now, and in what order, given the "
            "level is currently broken?"
        ),
        "criteria": {
            "REPAIR_AND_PROVE_LEVEL_FIRST_THEN_EXPAND": 0,
            "CONTINUE_EXPANDING_GENERATORS_IN_PARALLEL": 0,
            "PAUSE_THE_PROGRAMME_UNTIL_OWNER_VERIFIES": 0,
        },
    },
}

CONSTRAINTS = [
    "The owner's level is the deliverable. The owner's working game level must be intact before anything else is attempted.",
    "This project is not a sandbox for experimentation. Work must be additive: new files and new outputs, never mutations to existing assets a live level depends on.",
    "No p4 revert on the Poitou meshes: they are open for ADD and revert would delete them.",
    "No editor mutation, no closing or reloading the owner's editor session. All execution headless.",
    "Jev selects only; the existing owner lane executes; the headless cook check proves the result independently.",
    "Do not re-import or re-embed an HDA into the Houdini Engine asset as a restore step: the embedded graph is intact and is not the fault.",
    "Every restore step must be recorded and reversible before it is executed.",
    "Do not re-point or re-tune the HDA sources until the level cooks clean again.",
]


def jev_available() -> bool:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return False
    try:
        import typesafe_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    print("=" * 72)
    print("JEV DECISION PACKET - Poitou level restore + additive policy 2026-10-21")
    print("=" * 72)
    if not jev_available():
        print("\n[!] Jev unavailable (TYPESAFE_API_KEY / typesafe_sdk).")
        print("    Fallback would be a COMPOSED GUESS, not Jev evidence.")
        return 2
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.questions import Choice

    questions = {qid: Choice(instructions=spec["question"],
                             criteria={opt: None for opt in spec["criteria"]})
                 for qid, spec in QUESTIONS.items()}
    with TypeSafeClient() as client:
        result = client.system_one(state={"verified_state": STATE,
                                          "constraints": CONSTRAINTS},
                                   questions=questions)
    out = {
        "schema": "melodia.jev.poitou_level_audit.v1",
        "source": "jev-live",
        "state_verified_at": STATE["verified_at"],
        "answers": {qid: {"choice": a.choice, "score": getattr(a, "score", None),
                          "reason": getattr(a, "reason", None)}
                    for qid, a in result.answers.items()},
    }
    dest = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit",
        "PoitouConvergence_20261020", "JevPoitouLevelAudit_20261021.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\n=== JEV ===")
    print(json.dumps(out["answers"], indent=1))
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
