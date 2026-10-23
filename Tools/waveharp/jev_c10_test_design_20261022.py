"""JEV DECISION PACKET - C10 (the WaveHarp form automation test), 2026-10-22.

Closed candidate sets only. Jev selects; it does not mutate Unreal and it does not
write the test. The test is written by the existing owner lane afterwards, and the
result is proved by the test run itself.

Per Docs/Production/JEV_CANONICAL_WORKFLOW.md section 5: Jev adjudicates
implementation/test strategy; the existing owner executes; deterministic tools prove.
"""
from __future__ import annotations

import json
import os
import sys

STATE = {
    "verified_at": "2026-10-22, disk + compiler evidence",
    "situation": (
        "The WaveHarp 3-form system (C1-C6) was implemented today in "
        "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.h/.cpp. "
        "C10 is the NEXT item: the automation test that must make the form system "
        "provable rather than merely compiled."
    ),
    "what_c1_c6_changed": [
        "C1 EMelodiaWaveHarpForm {Harp, Bow, CarillonMelee}; CurrentForm is replicated; "
        "SetForm is the ONLY writer; the ring is HARP -> BOW -> CARILLON -> HARP.",
        "C2 the head swap: the committed form chooses the wand mesh (the caster wand and "
        "the melee wand differ only in the head), swapped at the transition midpoint. "
        "bUseHeadSwap is OFF by default until the Carillon art pass lands.",
        "C3 the transition is driven by the montage's FormAlpha curve when the authored "
        "henshin clip exists, otherwise by a smoothstep timer (defect D3: the old 0.22 s "
        "linear pop).",
        "C4 the melee geometry is MEASURED, not skeletal: blade start (21.9, 0, 17) cm, "
        "mid (37.08, 0, -0.52), tip (32.77, 0, -22.51), head-local, from "
        "Saved/Audit/waveharp/ue_ready/waveharp_wand_bake_manifest.json. That is a ~41 cm "
        "blade on a ~37 cm swing radius (defect D8: the shipped skeleton sockets are "
        "~90-100x too far out and produced a 42 m sweep).",
        "C5 the melee resolves through the sanctioned seam "
        "UMelodiaExternalJRPGBridgeSubsystem::ResolveWorldFlowAttack, and the rhythm is "
        "judged at the ACTION (the swing start), matching the arrow, not at impact.",
        "C6 one deliberate form-select key (R), the transition locks attacks, the flourish "
        "starts on the music clock's beat boundary (GetSecondsToNextBeat), and a pressed "
        "attack is buffered rather than eaten.",
    ],
    "measured_facts_the_test_could_use": {
        "blade_length_cm": 40.92,
        "blade_radius_cm": 37.08,
        "grip_local_cm": [0.0, 0.0, 13.0],
        "head_seat_local_cm": [0.0, 0.0, 105.0],
        "cymatic_projection_local_cm": [0.0, 0.0, 121.0],
        "old_defect_reach_m": 42.0,
        "form_ring": ["Harp", "Bow", "CarillonMelee"],
    },
    "existing_test_pattern": (
        "Source/BS_GodFile/MelodiaIntegration/Tests/ holds 11 files using "
        "IMPLEMENT_SIMPLE_AUTOMATION_TEST (see MelodiaHybridEncounterTests.cpp). "
        "MelodiaHybridEncounterTests.cpp asserts the hybrid single-state-owner contract, "
        "which is the closest precedent for asserting the form single-writer contract."
    ),
    "existing_offline_pattern": (
        "Content/Python/waveharp_hold_fix.py plus "
        "Content/Python/Tests/test_waveharp_hold_fix.py: 19/19 pure-maths assertions, no "
        "Unreal required, run with C:/Python314/python.exe. The hold maths was written this "
        "way on purpose."
    ),
    "constraints": [
        "The module's Tests folder is the existing C++ test surface; do not create a parallel harness.",
        "A test that needs a live world is a flaky gate. The P0 loop requires the committed "
        "harness to be the harness that ran.",
        "The bake manifest is the source of truth for the socket numbers; a test that re-types "
        "those numbers becomes a second source of truth that drifts.",
        "The editor may be occupied by another lane; a test that needs the editor open is not a gate.",
        "Defect D8 (a 42 m melee sweep) was shipped once and survived a compile. A regression "
        "guard for it is worth more than any new feature test.",
    ],
}

QUESTIONS = {
    "c10_scope": {
        "question": (
            "What should the C10 automation test actually be, for the WaveHarp form system?"
        ),
        "criteria": {
            "A": "Pure-maths C++ automation tests only in the module Tests folder: the ring order, "
                 "the eased transition curve, the lock window, the socket composition and the "
                 "blade reach. No editor, no world, no assets loaded.",
            "B": "Pure-maths C++ tests plus a live PIE functional test that drives SetForm and "
                 "asserts the head mesh, the morph weight and the blade sweep in a running level.",
            "C": "A python offline gate under Tools/ that re-derives the contract from the spec and "
                 "the bake manifest, with no C++ at all.",
            "D": "Both lanes, each doing what it is good at: C++ automation tests for the maths "
                 "and the state machine, plus a python offline gate that checks the asset contract "
                 "(the shipped sockets against the bake manifest) and the gate rules.",
        },
    },
    "c10_first_assertion": {
        "question": (
            "If the C10 test suite can only prove ONE thing first, which is the highest-value "
            "regression guard for this build?"
        ),
        "criteria": {
            "A": "D8: the melee blade reach must be the measured ~41 cm and must never be the "
                 "shipped ~42 m sweep. This defect shipped once, through a green compile.",
            "B": "D3: the form transition must be eased (a curve or a smoothstep), never the old "
                 "0.22 s linear pop, and the head must swap at the midpoint.",
            "C": "Single-writer: only SetForm may change CurrentForm or the head; no notify, no "
                 "tick path, no second entry point may write the form.",
            "D": "The beat lock and the input buffer: the flourish must start on a beat boundary "
                 "and a pressed attack must survive the transition.",
        },
    },
    "c10_run_surface": {
        "question": (
            "Where must the C10 test be able to run so that it is actually a gate rather than a "
            "nice-to-have?"
        ),
        "criteria": {
            "A": "Headless, in CI: the module's automation tests run through UnrealEditor-Cmd with "
                 "-ExecCmds=Automation RunTests, on a machine with no editor window open.",
            "B": "In the editor, as a RiderLink focused test, because the form needs a live "
                 "character to be meaningful.",
            "C": "Offline, with no engine at all, so it runs on any machine in seconds.",
            "D": "Both: the headless engine run proves the state machine and the maths, and the "
                 "offline python run proves the asset contract and the gate rules.",
        },
    },
    "c10_failure_mode": {
        "question": (
            "What is the most likely way this test suite becomes worthless within a month, and "
            "what should the design do about it?"
        ),
        "criteria": {
            "A": "It asserts implementation details, so every art or animation change breaks it "
                 "and the team starts ignoring it. Design: assert the CONTRACT (offsets, reach, "
                 "order, ownership) and read the numbers from the bake manifest, never re-type them.",
            "B": "It needs a live world, so it is flaky and gets skipped when the editor is busy. "
                 "Design: keep the world-dependent proof in the PIE receipt and keep C10 "
                 "world-free and deterministic.",
            "C": "It duplicates the spec, so the spec and the test drift apart and both are wrong. "
                 "Design: the test reads the numbers from the bake manifest and the spec's "
                 "machine form, and fails loudly when they disagree.",
            "D": "It is never run, because nothing invokes it. Design: wire it into the same "
                 "command the existing tests already run under, so it cannot be forgotten.",
        },
    },
}


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
    print("JEV DECISION PACKET - C10 (WaveHarp form automation test) 2026-10-22")
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
                                          "constraints": STATE["constraints"]},
                                   questions=questions)
    out = {
        "schema": "melodia.jev.waveharp_c10_test_design.v1",
        "source": "jev-live",
        "state_verified_at": STATE["verified_at"],
        "answers": {qid: {"choice": a.choice, "score": getattr(a, "score", None),
                          "reason": getattr(a, "reason", None)}
                    for qid, a in result.answers.items()},
    }
    dest = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit", "waveharp",
        "JevWaveHarpC10TestDesign_20261022.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\n=== JEV ===")
    print(json.dumps(out["answers"], indent=1))
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
